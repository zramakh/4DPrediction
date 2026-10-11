#!/usr/bin/env python3
"""Do 4D numbers recur around the same date each year, or follow the Moon or
the zodiac?

1. Anniversary recurrence: is a number that won on a given calendar date (or
   Chinese lunar date) more likely to win again within +-3 days of that date
   in other years? Tested against an exact null that keeps the real draw
   calendar, and as a walk-forward prediction.
2. Moon phase, Moon sign, Sun sign, Chinese lunar month / day and Chinese
   zodiac year: do digit frequencies differ between groups, and do the numbers
   that were "hot" for a group before 2010 stay hot for that group afterwards?

Draws are taken at 19:00 Malaysia time (11:00 UTC). Positions come from the
Meeus ephemeris in ephemeris.py.

Run from the repo root:  python3 analysis/seasonal_astro.py
"""

import csv
import datetime as dt
import json
import math
import os
import sys
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ephemeris as eph  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPERATORS = {"Magnum": "magnum", "Sports Toto": "sportstoto", "Da Ma Cai": "damacai"}
WINDOW = 3          # +- days counted as "about the same date"
SPLIT = "2010-01-01"  # walk-forward tests: learn before, test from here
TESTS = []


def norm_sf(z):
    return 0.5 * math.erfc(z / math.sqrt(2))


def chi2_sf(x, df):
    z = ((x / df) ** (1 / 3) - (1 - 2 / (9 * df))) / math.sqrt(2 / (9 * df))
    return norm_sf(z)


def record(test, operator, p, detail):
    TESTS.append({"test": test, "operator": operator, "p": p, "detail": detail})


# ------------------------------------------------------------------ data
def load(stem):
    by = defaultdict(list)
    with open(os.path.join(ROOT, "data", f"{stem}.csv"), newline="") as f:
        for r in csv.DictReader(f):
            by[r["date"]].append(int(r["4d_number"]))
    return {d: by[d] for d in sorted(by)}


CONTEXT = {}


def context(date):
    """Calendar, lunar and astrological attributes of one draw date."""
    if date not in CONTEXT:
        day = dt.date.fromisoformat(date)
        a = eph.describe(dt.datetime.combine(day, dt.time(11)))
        cny = eph.chinese_new_year(day.year)
        lunar_year = day.year if day >= cny else day.year - 1
        lm, ld, leap = eph.lunar_date(day)
        CONTEXT[date] = {
            "year": day.year,
            "doy": day.timetuple().tm_yday - 1,
            "lunar_year": lunar_year,
            "lunar_doy": (day - eph.chinese_new_year(lunar_year)).days,
            "lunar_month": lm,
            "lunar_day": ld,
            "phase": a["phase"],
            "moon_sign": a["moon_sign"],
            "sun_sign": a["sun_sign"],
            "chinese_zodiac": eph.CHINESE_ZODIAC[(lunar_year - 4) % 12],
            "full_moon_window": abs(a["elongation"] - 180) <= 12.19 * 1.5,  # within ~1.5 days
            "new_moon_window": min(a["elongation"], 360 - a["elongation"]) <= 12.19 * 1.5,
        }
    return CONTEXT[date]


# ------------------------------------------------------------------ 1. anniversaries
def anniversary_pairs(draws, key):
    """All pairs of wins of the same number in different years, as arrays of
    (number, year_i, pos_i, year_j, pos_j); pos is day-of-year (solar or lunar)."""
    occ = defaultdict(list)
    for date, nums in draws.items():
        c = context(date)
        y = c["lunar_year"] if key == "lunar_doy" else c["year"]
        for n in set(nums):
            occ[n].append((y, c[key]))
    cols = [[], [], [], [], []]
    for n, lst in occ.items():
        a = np.array(lst)
        i, j = np.triu_indices(len(a), 1)
        keep = a[i, 0] != a[j, 0]
        i, j = i[keep], j[keep]
        for col, v in zip(cols, (np.full(len(i), n), a[i, 0], a[i, 1], a[j, 0], a[j, 1])):
            col.append(v)
    return [np.concatenate(c) for c in cols]


def circ_close(a, b, period):
    d = np.abs(a - b) % period
    return np.minimum(d, period - d) <= WINDOW


def anniversary_test(op, draws, key, period, label):
    """Count pairs of wins of the same number in different years within
    +-WINDOW days (solar or lunar day-of-year). The null keeps every real draw
    date and its number of winners and only assumes the numbers are random:
    each such pair of draws then shares a number with probability 1/10000 per
    pair of winners. (Shifting whole years instead would misalign the draw
    calendar itself - e.g. the Chinese New Year break - and inflate the result.)"""
    num, yi, pi, yj, pj = anniversary_pairs(draws, key)
    close = circ_close(pi, pj, period)
    observed = int(close.sum())

    years = sorted({context(d)["lunar_year" if key == "lunar_doy" else "year"] for d in draws})
    M = np.zeros((len(years), period))
    for d, nums in draws.items():
        c = context(d)
        y = c["lunar_year"] if key == "lunar_doy" else c["year"]
        M[years.index(y), c[key] % period] += len(set(nums))
    def near(a):  # sum of a over +-WINDOW days, circularly
        return sum(np.roll(a, k, axis=-1) for k in range(-WINDOW, WINDOW + 1))
    S = M.sum(0)
    all_pairs = float((S * near(S)).sum())
    same_year = float((M * near(M)).sum())
    expected = (all_pairs - same_year) / 2 / 10000
    z = (observed - expected) / math.sqrt(expected)
    p = 2 * norm_sf(abs(z))
    record(f"{label} recurrence (+-{WINDOW} days, other years)", op, p,
           f"{observed} recurring pairs vs {expected:.0f} expected (z={z:+.2f})")
    per_number = Counter(num[close].tolist())
    return {"observed_pairs": observed, "expected": round(expected, 1), "z": round(z, 2), "p": p,
            "top_numbers": [(f"{n:04d}", c) for n, c in per_number.most_common(5)]}


def anniversary_prediction(op, draws, key, period, label):
    """Walk forward: before each draw from SPLIT on, collect every number that
    won within +-WINDOW days of this date in earlier years; count how many of
    them win now versus what a random set of the same size would catch."""
    seen = np.zeros((period + 31, 10000), bool)  # seen[day-of-year, number]
    hits = expected = picked = 0
    n_test = 0
    for date, nums in draws.items():
        pos = context(date)[key]
        if date >= SPLIT:
            rows = [(pos + k) % period for k in range(-WINDOW, WINDOW + 1)]
            cand = seen[rows].any(0)
            win = np.unique(nums)
            hits += int(cand[win].sum())
            expected += cand.sum() * len(win) / 10000
            picked += int(cand.sum())
            n_test += 1
        seen[pos % period, nums] = True
    z = (hits - expected) / math.sqrt(expected)
    record(f"{label} 'same date last years' prediction", op, norm_sf(z),
           f"{hits} hits vs {expected:.1f} expected (x{hits / expected:.3f})")
    return {"hits": hits, "expected": round(expected, 1), "lift": round(hits / expected, 3),
            "z": round(z, 2), "avg_numbers_picked_per_draw": round(picked / n_test)}


# ------------------------------------------------------------------ 2. moon & zodiac
FACTORS = {
    "moon phase (8)": "phase",
    "moon sign (12)": "moon_sign",
    "sun sign (12)": "sun_sign",
    "Chinese zodiac year (12)": "chinese_zodiac",
    "Chinese lunar month (12)": "lunar_month",
    "Chinese lunar day (1-30)": "lunar_day",
}


def digit_contingency(op, draws, factor, key):
    groups = sorted({context(d)[key] for d in draws}, key=str)
    gi = {g: i for i, g in enumerate(groups)}
    worst = 1.0
    for pos in range(4):
        t = np.zeros((len(groups), 10))
        for d, nums in draws.items():
            for n in nums:
                t[gi[context(d)[key]], n // 10 ** (3 - pos) % 10] += 1
        t = t[t.sum(1) > 0]
        exp = np.outer(t.sum(1), t.sum(0)) / t.sum()
        stat = float(((t - exp) ** 2 / exp).sum())
        df = (t.shape[0] - 1) * 9
        p = chi2_sf(stat, df)
        record(f"{factor} vs digit, position {pos + 1}", op, p, f"chi2={stat:.1f}, df={df}")
        worst = min(worst, p)
    return worst


def hot_numbers_by_group(op, draws, factor, key, k=100):
    """Learn each group's 100 most frequent numbers before SPLIT; check whether
    those numbers win more often than chance in the same group afterwards."""
    train = defaultdict(Counter)
    for d, nums in draws.items():
        if d < SPLIT:
            train[context(d)[key]].update(nums)
    tops = {g: {n for n, _ in c.most_common(k)} for g, c in train.items()}
    hits = expected = 0
    for d, nums in draws.items():
        if d >= SPLIT:
            g = context(d)[key]
            if g in tops:
                hits += len(set(nums) & tops[g])
                expected += len(set(nums)) * len(tops[g]) / 10000
    z = (hits - expected) / math.sqrt(expected)
    record(f"{factor}: group's hot numbers stay hot", op, norm_sf(z),
           f"{hits} hits vs {expected:.1f} expected (x{hits / expected:.3f})")
    return {"hits": hits, "expected": round(expected, 1), "lift": round(hits / expected, 3), "z": round(z, 2)}


def moon_window_rate(op, draws, flag):
    """Do repeats of recent numbers, or particular digits, cluster at full/new moon?
    Here: share of 7s, of repeated digits (e.g. 1123), and of numbers that also
    won in the previous 10 draws, inside vs outside the window."""
    rows = {True: Counter(), False: Counter()}
    recent = []
    for d, nums in draws.items():
        inside = context(d)[flag]
        prev = set().union(*recent) if recent else set()
        for n in nums:
            s = f"{n:04d}"
            rows[inside]["numbers"] += 1
            rows[inside]["has_repeated_digit"] += len(set(s)) < 4
            rows[inside]["recent_repeat"] += n in prev
        recent = (recent + [set(nums)])[-10:]
    out = {}
    for metric in ("has_repeated_digit", "recent_repeat"):
        a, n1 = rows[True][metric], rows[True]["numbers"]
        b, n2 = rows[False][metric], rows[False]["numbers"]
        p1, p2 = a / n1, b / n2
        pp = (a + b) / (n1 + n2)
        z = (p1 - p2) / math.sqrt(pp * (1 - pp) * (1 / n1 + 1 / n2))
        record(f"{flag.replace('_', ' ')}: {metric.replace('_', ' ')}", op, 2 * norm_sf(abs(z)),
               f"{p1 * 100:.2f}% inside vs {p2 * 100:.2f}% outside (z={z:+.2f})")
        out[metric] = {"inside": round(p1, 4), "outside": round(p2, 4), "z": round(z, 2)}
    return out


# ------------------------------------------------------------------ main
def main():
    data = {op: load(stem) for op, stem in OPERATORS.items()}
    pooled = defaultdict(list)
    for draws in data.values():
        for d, nums in draws.items():
            pooled[d].extend(nums)
    data_all = dict(data, **{"All three pooled": dict(sorted(pooled.items()))})

    results = {"anniversary": {}, "astro": {}, "moon_windows": {}}
    for op, draws in data_all.items():
        print(f"== {op}: {len(draws)} draw dates")
        r = {}
        r["solar"] = anniversary_test(op, draws, "doy", 365, "Same calendar date")
        r["lunar"] = anniversary_test(op, draws, "lunar_doy", 354, "Same Chinese lunar date")
        r["solar_prediction"] = anniversary_prediction(op, draws, "doy", 365, "Calendar")
        r["lunar_prediction"] = anniversary_prediction(op, draws, "lunar_doy", 354, "Lunar")
        results["anniversary"][op] = r
        if op == "All three pooled":
            continue
        results["astro"][op] = {}
        for factor, key in FACTORS.items():
            results["astro"][op][factor] = {
                "min_digit_p": digit_contingency(op, draws, factor, key),
                "hot_numbers": hot_numbers_by_group(op, draws, factor, key),
            }
        results["moon_windows"][op] = {f: moon_window_rate(op, draws, f)
                                       for f in ("full_moon_window", "new_moon_window")}

    m = len(TESTS)
    for t in TESTS:
        t["p_bonferroni"] = min(1.0, t["p"] * m)
    results["tests"] = TESTS
    with open(os.path.join(ROOT, "analysis", "seasonal_astro_results.json"), "w") as f:
        json.dump(results, f, indent=1, default=float)

    print("\nAnniversary recurrence (+-3 days, different years)")
    for op, r in results["anniversary"].items():
        s, l = r["solar"], r["lunar"]
        print(f"  {op:<17} calendar: {s['observed_pairs']} pairs vs {s['expected']} expected (z={s['z']:+.2f})"
              f" | lunar: {l['observed_pairs']} vs {l['expected']} (z={l['z']:+.2f})")
        print(f"  {'':<17} most-recurring numbers (calendar): {s['top_numbers']}")
        sp, lp = r["solar_prediction"], r["lunar_prediction"]
        print(f"  {'':<17} predict from same date in past years: calendar x{sp['lift']} (z={sp['z']:+.2f}, "
              f"~{sp['avg_numbers_picked_per_draw']} numbers/draw), lunar x{lp['lift']} (z={lp['z']:+.2f})")
    print("\nMoon / zodiac: smallest digit-test p and whether group 'hot numbers' persist after 2010")
    for op, fs in results["astro"].items():
        for factor, r in fs.items():
            h = r["hot_numbers"]
            print(f"  {op:<12} {factor:<26} min p={r['min_digit_p']:.3f}  hot-100 lift x{h['lift']} (z={h['z']:+.2f})")
    print("\nFull/new moon windows")
    for op, fs in results["moon_windows"].items():
        print(f"  {op}: {fs}")
    print(f"\n{m} tests; {sum(t['p'] < 0.05 for t in TESTS)} with raw p<0.05 (~{m * 0.05:.0f} by chance); "
          f"{sum(t['p_bonferroni'] < 0.05 for t in TESTS)} significant after Bonferroni")
    for t in sorted(TESTS, key=lambda t: t["p"])[:8]:
        print(f"  p={t['p']:.4f} p_adj={t['p_bonferroni']:.2f} {t['operator']:<17} {t['test']}: {t['detail']}")


if __name__ == "__main__":
    main()
