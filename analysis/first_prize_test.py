#!/usr/bin/env python3
"""Are 1st prizes drawn from a different digit mix than the other prizes?

Motivation: the "cold number" (each operator's least frequent digit in each
position, from its earlier results) won six 1st prizes in 2012-2026 against
about 0.7 expected. If 1st prizes favour historically cold digits, that would
be a mechanism; otherwise it is most likely a lucky streak.

For every draw, the operator's digit counts from all earlier draws (all
prizes) rank the digits 0 (hottest) .. 9 (coldest) in each position. Then:
  A. digit level: share of 1st-prize digits equal to the cold digit, and their
     mean rank, against the other 22 prizes of the same draws (built-in control)
  B. number level: how often the cold number fills each prize slot
  C. chi-square: 1st-prize digit distribution vs the rest, per operator x position
Periods: 1995-2011 (before the lead was found) and 2012-2026 (where it was found).

Run from the repo root:  python3 analysis/first_prize_test.py
"""

import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am  # noqa: E402

ROOT = am.ROOT
DIG = am.DIG
POW = np.array([1000, 100, 10, 1])
PERIODS = {"1995-2011 (independent)": (1995, 2012), "2012-2026 (lead found here)": (2012, 2027)}


def chi2_sf(x, df):
    z = ((x / df) ** (1 / 3) - (1 - 2 / (9 * df))) / math.sqrt(2 / (9 * df))
    return 0.5 * math.erfc(z / math.sqrt(2))


def main():
    _, codes, labels, rows, draws, year_of = am.load()
    keys = sorted(draws)
    cnt = np.zeros((3, 4, 10))                  # digit counts of all earlier draws, per operator
    A = {p: {"first": [0, 0, 0.0], "rest": [0, 0, 0.0]} for p in PERIODS}     # [cold matches, digits, rank sum]
    B = {p: {s: [0, 0] for s in ("1st", "2nd", "3rd", "Special", "Consolation")} for p in PERIODS}
    H = {p: {s: [0, 0] for s in ("1st", "2nd", "3rd", "Special", "Consolation")} for p in PERIODS}
    C = {p: np.zeros((3, 4, 2, 10)) for p in PERIODS}                     # [op, pos, first/rest, digit]
    first_hits = []
    for d, o in keys:
        prize_rows = draws[(d, o)][1]
        y = int(year_of[d])
        per = next((p for p, (a, b) in PERIODS.items() if a <= y < b), None)
        if per is not None and cnt[o].sum() > 0:
            # ties broken by digit value, as in the strategies
            rank = np.argsort(np.argsort(-(cnt[o] - np.arange(10) * 1e-9), axis=1), axis=1)   # 0 = hottest
            cold = np.argmax(rank, axis=1)
            hot = np.argmin(rank, axis=1)
            cold_n, hot_n = int((cold * POW).sum()), int((hot * POW).sum())
            for prize, n in prize_rows:
                dg = DIG[n]
                grp = "first" if prize == "1st" else "rest"
                a = A[per][grp]
                a[0] += int((dg == cold).sum())
                a[1] += 4
                a[2] += float(rank[np.arange(4), dg].sum())
                C[per][o, np.arange(4), 0 if prize == "1st" else 1, dg] += 1
            slots = {}
            for prize, n in prize_rows:
                slots.setdefault(prize, []).append(n)
            for s in B[per]:
                ns = slots.get(s, [])
                B[per][s][0] += int(cold_n in ns)
                B[per][s][1] += len(ns)
                H[per][s][0] += int(hot_n in ns)
                H[per][s][1] += len(ns)
            if "1st" in slots and cold_n in slots["1st"]:
                first_hits.append(f"{y} {am.OPS[o]} {cold_n:04d}")
        for _, n in prize_rows:
            cnt[o, np.arange(4), DIG[n]] += 1

    out = {"A_digit_level": {}, "B_number_level": {}, "C_chi_square": {}, "cold_number_first_prizes": first_hits}
    print("A. Digit level: share of digits that are the operator's historically coldest digit in that position")
    for per in PERIODS:
        f, r = A[per]["first"], A[per]["rest"]
        pf, pr = f[0] / f[1], r[0] / r[1]
        se = math.sqrt(pr * (1 - pr) / f[1])
        z = (pf - pr) / se
        mf, mr = f[2] / f[1], r[2] / r[1]
        se_rank = math.sqrt(8.25 / f[1])                      # variance of a uniform rank 0..9
        print(f"  {per:<30} 1st prize {100 * pf:.2f}% vs other prizes {100 * pr:.2f}% (z={z:+.2f}); "
              f"mean rank 1st {mf:.3f} vs others {mr:.3f} (z={(mf - mr) / se_rank:+.2f}; 9 = coldest)")
        out["A_digit_level"][per] = {"first_cold_share": pf, "rest_cold_share": pr, "z": z,
                                     "first_mean_rank": mf, "rest_mean_rank": mr, "rank_z": (mf - mr) / se_rank,
                                     "first_digits": f[1], "rest_digits": r[1]}
    print("\nB. Number level: how often the cold (and hot) number filled each prize slot")
    for per in PERIODS:
        print(f"  {per}")
        out["B_number_level"][per] = {}
        for s in B[per]:
            h, n = B[per][s]
            hh, _ = H[per][s]
            e = n / 10000
            p = 1 - sum(math.exp(-e) * e ** k / math.factorial(k) for k in range(h)) if h else 1.0
            print(f"    {s:<12} cold number {h:>2} times in {n:>6} slots (expected {e:.2f}, P(>= this) {p:.4f}); "
                  f"hot number {hh}")
            out["B_number_level"][per][s] = {"cold_hits": h, "hot_hits": hh, "slots": n, "expected": e, "p": p}
    print("\nC. Chi-square: 1st-prize digit distribution vs the other prizes (9 df each)")
    for per in PERIODS:
        stats = []
        for o in range(3):
            for p in range(4):
                t = C[per][o, p]
                rowt, colt = t.sum(1, keepdims=True), t.sum(0, keepdims=True)
                e = rowt * colt / t.sum()
                x2 = float(((t - e) ** 2 / np.where(e > 0, e, 1)).sum())
                stats.append((am.OPS[o], p + 1, x2, chi2_sf(x2, 9)))
        tot = sum(s[2] for s in stats)
        print(f"  {per:<30} sum over 12 tests {tot:.1f} (expected 108, p={chi2_sf(tot, 108):.3f}); "
              f"smallest p {min(s[3] for s in stats):.3f} ({[s[:2] for s in stats if s[3] == min(x[3] for x in stats)][0]})")
        out["C_chi_square"][per] = {"sum": tot, "p_sum": chi2_sf(tot, 108),
                                    "tests": [{"operator": a, "position": b, "chi2": c, "p": d} for a, b, c, d in stats]}
    print("\ncold-number 1st prizes:", first_hits)
    json.dump(out, open(os.path.join(ROOT, "analysis", "first_prize_results.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
