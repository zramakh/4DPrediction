#!/usr/bin/env python3
"""KP (Krishnamurti Paddhati) numbers vs 4D results.

For each draw (19:00 Malaysia time, Ascendant for Kuala Lumpur) and for each of
Ascendant, Moon, Sun, Mercury, Venus, Mars, Jupiter, Saturn, Rahu and Ketu we
compute the KP number (1-249) and its sign, star and sub lords, then test:

1. KP number inside the winning numbers: does the body's KP number (e.g. 119)
   appear in the 4D numbers (as a substring, or as the last 3 digits) more
   often than chance?
2. Lords as digits: does the planet number (Sun 1, Moon 2, Jupiter 3, Rahu 4,
   Mercury 5, Venus 6, Ketu 7, Saturn 8, Mars 9) of the sign, star or sub lord
   appear as a digit more than 10% of the time?
3. Digit frequencies by star lord and by sub lord (9 groups each), and by KP
   number for the fast-moving Ascendant and Moon.
4. Do the 100 most frequent numbers for each Ascendant / Moon KP number before
   2010 stay frequent for that KP number afterwards?

Magnum is also analysed without its known equipment-bias eras.

Run from the repo root:  python3 analysis/kp_analysis.py
"""

import datetime as dt
import json
import math
import os
import sys
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kp  # noqa: E402
from seasonal_astro import chi2_sf, load, norm_sf  # noqa: E402
from vedic import PLANET_NUMBER  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPLIT = "2010-01-01"
DIG = np.array([[n // 1000, n // 100 % 10, n // 10 % 10, n % 10] for n in range(10000)])
STR4 = [f"{n:04d}" for n in range(10000)]
TESTS = []
_CHART = {}


def chart(date):
    if date not in _CHART:
        day = dt.date.fromisoformat(date)
        _CHART[date] = kp.chart(dt.datetime.combine(day, dt.time(11)))
    return _CHART[date]


def record(test, op, p, detail):
    TESTS.append({"test": test, "operator": op, "p": p, "detail": detail})


# Fraction of all 10,000 numbers containing str(k) as a substring, k = 1..249.
SUBSTR_FRAC = {k: sum(str(k) in s for s in STR4) / 10000 for k in range(1, 250)}


def kp_number_in_winners(op, draws, body):
    sub_hits = sub_exp = last3_hits = last3_exp = 0.0
    for d, nums in draws.items():
        k = chart(d)[body]["kp"]
        ks = str(k)
        sub_hits += sum(ks in STR4[n] for n in nums)
        sub_exp += len(nums) * SUBSTR_FRAC[k]
        last3_hits += sum(n % 1000 == k for n in nums)
        last3_exp += len(nums) / 1000
    z1 = (sub_hits - sub_exp) / math.sqrt(sub_exp)
    z2 = (last3_hits - last3_exp) / math.sqrt(last3_exp)
    record(f"{body} KP number inside winners", op, norm_sf(z1), f"{sub_hits:.0f} vs {sub_exp:.1f} (z={z1:+.2f})")
    record(f"{body} KP number = last 3 digits", op, norm_sf(z2), f"{last3_hits:.0f} vs {last3_exp:.1f} (z={z2:+.2f})")
    return {"substring": [int(sub_hits), round(sub_exp, 1), round(z1, 2)],
            "last3": [int(last3_hits), round(last3_exp, 1), round(z2, 2)]}


def lords_as_digits(op, draws, body):
    out = {}
    for lord in ("sign_lord", "star_lord", "sub_lord"):
        hits = tot = 0
        for d, nums in draws.items():
            k = PLANET_NUMBER[chart(d)[body][lord]]
            hits += int((DIG[nums] == k).sum())
            tot += 4 * len(nums)
        z = (hits - 0.1 * tot) / math.sqrt(0.09 * tot)
        record(f"{body} {lord.replace('_', ' ')} number as digit", op, norm_sf(z),
               f"{hits / tot * 100:.2f}% vs 10% (z={z:+.2f})")
        out[lord] = [round(hits / tot, 4), round(z, 2)]
    return out


def digit_contingency(op, draws, label, name):
    groups = sorted({label(d) for d in draws})
    gi = {g: i for i, g in enumerate(groups)}
    ps = []
    for pos in range(4):
        t = np.zeros((len(groups), 10))
        for d, nums in draws.items():
            np.add.at(t[gi[label(d)]], DIG[nums, pos], 1)
        t = t[t.sum(1) > 0]
        exp = np.outer(t.sum(1), t.sum(0)) / t.sum()
        stat = float(((t - exp) ** 2 / exp).sum())
        df = (len(t) - 1) * 9
        p = chi2_sf(stat, df)
        record(f"{name} vs digit, position {pos + 1}", op, p, f"chi2={stat:.1f}, df={df}")
        ps.append(p)
    return min(ps)


def hot_numbers(op, draws, body, k=100):
    train = defaultdict(Counter)
    for d, nums in draws.items():
        if d < SPLIT:
            train[chart(d)[body]["kp"]].update(nums)
    tops = {g: {n for n, _ in c.most_common(k)} for g, c in train.items()}
    hits = expected = 0
    for d, nums in draws.items():
        g = chart(d)[body]["kp"]
        if d >= SPLIT and g in tops:
            hits += len(set(nums) & tops[g])
            expected += len(set(nums)) * len(tops[g]) / 10000
    z = (hits - expected) / math.sqrt(expected)
    record(f"{body} KP number: hot numbers stay hot", op, norm_sf(z),
           f"{hits} vs {expected:.1f} (x{hits / expected:.3f})")
    return [hits, round(expected, 1), round(hits / expected, 3), round(z, 2)]


def main():
    data = {op: load(stem) for op, stem in
            (("Magnum", "magnum"), ("Sports Toto", "sportstoto"), ("Da Ma Cai", "damacai"))}
    data["Magnum (fair periods)"] = {d: v for d, v in data["Magnum"].items()
                                     if d >= "1995" and not ("2019-01-29" <= d <= "2025-11-05")}
    results = {}
    for op, draws in data.items():
        r = {}
        for b in kp.BODIES:
            rb = {"kp_in_winners": kp_number_in_winners(op, draws, b),
                  "lords_as_digits": lords_as_digits(op, draws, b),
                  "star_lord_digits_min_p": digit_contingency(op, draws, lambda d: chart(d)[b]["star_lord"], f"{b} star lord"),
                  "sub_lord_digits_min_p": digit_contingency(op, draws, lambda d: chart(d)[b]["sub_lord"], f"{b} sub lord")}
            if b in ("Ascendant", "Moon"):
                rb["kp_number_digits_min_p"] = digit_contingency(op, draws, lambda d: chart(d)[b]["kp"], f"{b} KP number")
                rb["hot_numbers"] = hot_numbers(op, draws, b)
            r[b] = rb
        results[op] = r

    m = len(TESTS)
    for t in TESTS:
        t["p_bonferroni"] = min(1.0, t["p"] * m)
    with open(os.path.join(ROOT, "analysis", "kp_results.json"), "w") as f:
        json.dump({"results": results, "tests": TESTS}, f, indent=1, default=float)

    for op, r in results.items():
        print(f"\n== {op}")
        print(f"  {'body':<10} {'KP no. in winners':<22} {'KP no.=last 3':<18} {'sign/star/sub lord as digit (z)':<34} digit-test min p (star, sub)")
        for b, v in r.items():
            s, l3 = v["kp_in_winners"]["substring"], v["kp_in_winners"]["last3"]
            lz = " ".join(f"{x[1]:+.2f}" for x in v["lords_as_digits"].values())
            print(f"  {b:<10} {s[0]:>6} vs {s[1]:>8} z={s[2]:+.2f}  {l3[0]:>4} vs {l3[1]:>6} z={l3[2]:+.2f}  {lz:<34} "
                  f"{v['star_lord_digits_min_p']:.3f}, {v['sub_lord_digits_min_p']:.3f}"
                  + (f" | KP-number digit p={v['kp_number_digits_min_p']:.3f}, hot-100 x{v['hot_numbers'][2]} "
                     f"(z={v['hot_numbers'][3]:+.2f})" if "hot_numbers" in v else ""))
    print(f"\n{m} tests; {sum(t['p'] < 0.05 for t in TESTS)} with raw p<0.05 (~{m * 0.05:.0f} by chance); "
          f"{sum(t['p_bonferroni'] < 0.05 for t in TESTS)} significant after Bonferroni")
    for t in sorted(TESTS, key=lambda t: t["p"])[:10]:
        print(f"  p={t['p']:.2e} p_adj={t['p_bonferroni']:.2f} {t['operator']:<22} {t['test']}: {t['detail']}")


if __name__ == "__main__":
    main()
