#!/usr/bin/env python3
"""Vedic astrology vs 4D results.

For every draw (19:00 Malaysia time, Kuala Lumpur) we compute the panchanga
(tithi, paksha, nakshatra, yoga, karana, vara, hora) and sidereal (Lahiri)
rashis of the Sun, Moon, Mars, Mercury, Venus, Jupiter, Saturn and Rahu, and
ask three questions:

1. Do digit frequencies differ between groups (e.g. nakshatras)?
2. Do numbers that were frequent for a group before 2010 stay frequent for that
   group afterwards?
3. Vedic numerology: on draws ruled by a planet (vara, hora or nakshatra lord),
   does that planet's number (Sun 1, Moon 2, Jupiter 3, Rahu 4, Mercury 5,
   Venus 6, Ketu 7, Saturn 8, Mars 9) appear more as a digit, or as the
   number's digital root?

Then a combined walk-forward model learns digit frequencies per position for
the nakshatra, tithi, hora and Moon rashi of each draw before 2010 and
predicts later draws.

Magnum is analysed twice: in full, and with its known equipment-bias periods
(before 1995 and 2019-01-29..2025-11-05) removed, because a bias that changes
by era would otherwise show up as a false effect of any slow-moving planet.

Run from the repo root:  python3 analysis/vedic_analysis.py
"""

import datetime as dt
import json
import math
import os
import sys
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vedic  # noqa: E402
from seasonal_astro import chi2_sf, load, norm_sf  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPLIT = "2010-01-01"
TESTS = []
FACTORS = ["tithi", "paksha", "nakshatra", "yoga", "karana", "vara_lord", "hora_lord",
           "moon_rashi", "sun_rashi", "mars_rashi", "mercury_rashi", "venus_rashi",
           "jupiter_rashi", "saturn_rashi", "rahu_rashi", "mercury_retrograde"]
RULERS = ["vara_lord", "hora_lord", "nakshatra_lord"]
MODEL_FACTORS = ["nakshatra", "tithi", "hora_lord", "moon_rashi"]
DIG = np.array([[n // 1000, n // 100 % 10, n // 10 % 10, n % 10] for n in range(10000)])

_CTX = {}


def ctx(date):
    if date not in _CTX:
        day = dt.date.fromisoformat(date)
        _CTX[date] = vedic.panchanga(dt.datetime.combine(day, dt.time(11)), day)
    return _CTX[date]


def record(test, op, p, detail):
    TESTS.append({"test": test, "operator": op, "p": p, "detail": detail})


def digit_tests(op, draws, factor):
    groups = sorted({str(ctx(d)[factor]) for d in draws})
    gi = {g: i for i, g in enumerate(groups)}
    ps = []
    for pos in range(4):
        t = np.zeros((len(groups), 10))
        for d, nums in draws.items():
            g = gi[str(ctx(d)[factor])]
            np.add.at(t[g], DIG[nums, pos], 1)
        t = t[t.sum(1) > 0]
        if len(t) < 2:
            continue
        exp = np.outer(t.sum(1), t.sum(0)) / t.sum()
        stat = float(((t - exp) ** 2 / exp).sum())
        df = (len(t) - 1) * 9
        p = chi2_sf(stat, df)
        record(f"{factor} vs digit, position {pos + 1}", op, p, f"chi2={stat:.1f}, df={df}")
        ps.append(p)
    return min(ps) if ps else None


def hot_numbers(op, draws, factor, k=100):
    train = defaultdict(Counter)
    for d, nums in draws.items():
        if d < SPLIT:
            train[str(ctx(d)[factor])].update(nums)
    tops = {g: {n for n, _ in c.most_common(k)} for g, c in train.items()}
    hits = expected = 0
    for d, nums in draws.items():
        g = str(ctx(d)[factor])
        if d >= SPLIT and g in tops:
            hits += len(set(nums) & tops[g])
            expected += len(set(nums)) * len(tops[g]) / 10000
    if not expected:
        return None
    z = (hits - expected) / math.sqrt(expected)
    record(f"{factor}: group's hot numbers stay hot", op, norm_sf(z),
           f"{hits} hits vs {expected:.1f} expected (x{hits / expected:.3f})")
    return {"lift": round(hits / expected, 3), "z": round(z, 2)}


def numerology(op, draws, ruler):
    """Share of the ruling planet's digit among all digits (expect 10%), and
    share of numbers whose digital root equals it (expect 1/9, 0000 excluded)."""
    dig_hits = dig_tot = root_hits = root_tot = 0
    for d, nums in draws.items():
        k = vedic.PLANET_NUMBER[ctx(d)[ruler]]
        a = np.array(nums)
        dig_hits += int((DIG[a] == k).sum())
        dig_tot += 4 * len(a)
        a = a[a > 0]
        root_hits += int((1 + (a - 1) % 9 == k).sum())
        root_tot += len(a)
    z1 = (dig_hits - dig_tot * 0.1) / math.sqrt(dig_tot * 0.09)
    z2 = (root_hits - root_tot / 9) / math.sqrt(root_tot * (1 / 9) * (8 / 9))
    record(f"numerology: {ruler}'s number as a digit", op, norm_sf(z1),
           f"{dig_hits / dig_tot * 100:.2f}% vs 10% (z={z1:+.2f})")
    record(f"numerology: {ruler}'s number as digital root", op, norm_sf(z2),
           f"{root_hits / root_tot * 100:.2f}% vs 11.11% (z={z2:+.2f})")
    return {"digit_share": round(dig_hits / dig_tot, 4), "digit_z": round(z1, 2),
            "root_share": round(root_hits / root_tot, 4), "root_z": round(z2, 2)}


def combined_model(op, draws, k=100):
    """Naive-Bayes digit model: P(digit at position | each factor's value),
    learned on draws before SPLIT; each later draw gets the top-k numbers."""
    counts = {f: defaultdict(lambda: np.ones((4, 10))) for f in MODEL_FACTORS}
    for d, nums in draws.items():
        if d < SPLIT:
            c = ctx(d)
            for f in MODEL_FACTORS:
                m = counts[f][str(c[f])]
                for pos in range(4):
                    np.add.at(m[pos], DIG[nums, pos], 1)
    hits = expected = 0
    for d, nums in draws.items():
        if d < SPLIT:
            continue
        c = ctx(d)
        score = np.zeros(10000)
        for f in MODEL_FACTORS:
            m = counts[f][str(c[f])]
            p = np.log(m / m.sum(1, keepdims=True) * 10)
            score += sum(p[pos][DIG[:, pos]] for pos in range(4))
        top = set(np.argpartition(-score, k)[:k].tolist())
        hits += len(top & set(nums))
        expected += k * len(set(nums)) / 10000
    z = (hits - expected) / math.sqrt(expected)
    record("combined panchanga digit model (top 100)", op, norm_sf(z),
           f"{hits} hits vs {expected:.1f} expected (x{hits / expected:.3f})")
    return {"hits": hits, "expected": round(expected, 1), "lift": round(hits / expected, 3), "z": round(z, 2)}


def main():
    data = {op: load(stem) for op, stem in
            (("Magnum", "magnum"), ("Sports Toto", "sportstoto"), ("Da Ma Cai", "damacai"))}
    data["Magnum (fair periods)"] = {d: v for d, v in data["Magnum"].items()
                                     if d >= "1995" and not ("2019-01-29" <= d <= "2025-11-05")}
    print("computing panchanga for", len({d for v in data.values() for d in v}), "dates ...")
    results = {}
    for op, draws in data.items():
        r = {"factors": {}, "numerology": {}}
        for f in FACTORS:
            r["factors"][f] = {"min_digit_p": digit_tests(op, draws, f), "hot_numbers": hot_numbers(op, draws, f)}
        for ruler in RULERS:
            r["numerology"][ruler] = numerology(op, draws, ruler)
        r["combined_model"] = combined_model(op, draws)
        results[op] = r

    m = len(TESTS)
    for t in TESTS:
        t["p_bonferroni"] = min(1.0, t["p"] * m)
    with open(os.path.join(ROOT, "analysis", "vedic_results.json"), "w") as f:
        json.dump({"results": results, "tests": TESTS}, f, indent=1, default=float)

    for op, r in results.items():
        print(f"\n== {op}")
        for f, v in r["factors"].items():
            h = v["hot_numbers"]
            print(f"  {f:<19} min digit p={v['min_digit_p']:.3f}  hot-100 "
                  + (f"x{h['lift']} (z={h['z']:+.2f})" if h else "n/a"))
        for ruler, v in r["numerology"].items():
            print(f"  numerology {ruler:<15} digit {v['digit_share'] * 100:.2f}% (z={v['digit_z']:+.2f})  "
                  f"digital root {v['root_share'] * 100:.2f}% (z={v['root_z']:+.2f})")
        c = r["combined_model"]
        print(f"  combined model: {c['hits']} hits vs {c['expected']} expected (x{c['lift']}, z={c['z']:+.2f})")
    print(f"\n{m} tests; {sum(t['p'] < 0.05 for t in TESTS)} with raw p<0.05 (~{m * 0.05:.0f} by chance); "
          f"{sum(t['p_bonferroni'] < 0.05 for t in TESTS)} significant after Bonferroni")
    for t in sorted(TESTS, key=lambda t: t["p"])[:10]:
        print(f"  p={t['p']:.2e} p_adj={t['p_bonferroni']:.2f} {t['operator']:<22} {t['test']}: {t['detail']}")


if __name__ == "__main__":
    main()
