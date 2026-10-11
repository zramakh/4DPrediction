#!/usr/bin/env python3
"""Deep dive into the Magnum digit bias seen from ~2019 to late 2025.

Run from the repo root:  python3 analysis/magnum_bias.py
"""

import csv
import math
import os
from collections import defaultdict

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIG = np.array([[n // 1000, n // 100 % 10, n // 10 % 10, n % 10] for n in range(10000)])
BIG_PAYOUT = {"1st": 2500, "2nd": 1000, "3rd": 500, "Special": 180, "Consolation": 60}

by = defaultdict(lambda: defaultdict(list))  # date -> prize -> [numbers]
with open(os.path.join(ROOT, "data", "magnum.csv"), newline="") as f:
    for r in csv.DictReader(f):
        by[r["date"]][r["prize"]].append(int(r["4d_number"]))
dates = sorted(by)


def nums(d):
    return [n for v in by[d].values() for n in v]


def digit_matrix(ds):
    m = np.zeros((4, 10))
    for d in ds:
        for n in nums(d):
            m[np.arange(4), DIG[n]] += 1
    return m


def chi2(m):
    e = m.sum(1, keepdims=True) / 10
    return float(((m - e) ** 2 / e).sum())


def deviation_table(ds, label):
    m = digit_matrix(ds)
    n = m[0].sum()
    print(f"\n{label}: {int(n)} numbers, 1 SE = {100 * math.sqrt(0.09 / n) / 0.1:.1f}%, "
          f"chi2 = {chi2(m):.1f} (df 36, ~36 if fair)")
    print("       " + "".join(f"{d:>6}" for d in range(10)))
    for p in range(4):
        print(f"pos{p + 1}  " + "".join(f"{(m[p, d] / n * 10 - 1) * 100:+6.1f}" for d in range(10)))


def digit7_share(ds):
    k = sum(f"{n:04d}".count("7") for d in ds for n in nums(d))
    t = 4 * sum(len(nums(d)) for d in ds)
    return k / t, (k - 0.1 * t) / math.sqrt(0.09 * t)


def evaluate(order, ds, label):
    parts = []
    for k in (10, 100, 1000, 5000):
        pick = set(order[:k].tolist())
        h = sum(len(pick & set(nums(d))) for d in ds)
        e = sum(len(nums(d)) for d in ds) * k / 10000
        parts.append(f"top{k} x{h / e:.3f} (z={(h - e) / math.sqrt(e):+.1f})")
    top10 = set(order[:10].tolist())
    won = sum(BIG_PAYOUT[p] * len(top10 & set(v)) for d in ds for p, v in by[d].items())
    print(f"  {label}: " + "  ".join(parts) + f"  | RM1 Big on top 10 returns RM{won / (10 * len(ds)):.2f}")


def rank(ds):
    f = digit_matrix(ds) + 1
    f /= f.sum(1, keepdims=True)
    score = sum(np.log(f[p][DIG[:, p]] * 10) for p in range(4))
    return np.argsort(-score), np.sort(score)[::-1]


# 1. Digit-7 share by half-year
print("Digit 7 share by half-year (expected 10%)")
halves = defaultdict(list)
for d in dates:
    if d >= "2015":
        halves[d[:4] + ("H1" if d[5:7] <= "06" else "H2")].append(d)
for h, ds in sorted(halves.items()):
    s, z = digit7_share(ds)
    print(f"  {h}  {s * 100:5.2f}%  z={z:+.2f}  {'#' * int(max(0, -z) * 4)}")

# 2. Change points from the CUSUM of excess 7s per draw
recent = [d for d in dates if d >= "2017"]
cs = np.cumsum([sum(f"{n:04d}".count("7") for n in nums(d)) - 0.4 * len(nums(d)) for d in recent])
j = int(np.argmin(cs))
i = int(np.argmax(cs[:j]))
start, end = recent[i + 1], recent[j]
before = [d for d in recent if d < start]
during = [d for d in dates if start <= d <= end]
after = [d for d in dates if d > end]
print(f"\nBiased period (CUSUM change points): {start} .. {end}, {len(during)} draws")
for label, ds in (("before", before), ("during", during), ("after", after)):
    s, z = digit7_share(ds)
    print(f"  {label:<7} digit-7 share {s * 100:.2f}% (z={z:+.2f}), chi2={chi2(digit_matrix(ds)):.1f}")

deviation_table(during, f"Deviation % by position and digit, {start} .. {end}")
for tier in (("1st", "2nd", "3rd"), ("Special",), ("Consolation",)):
    m = np.zeros((4, 10))
    for d in during:
        for p in tier:
            for n in by[d][p]:
                m[np.arange(4), DIG[n]] += 1
    print(f"  {'/'.join(tier):<12} chi2={chi2(m):.1f}  digit-7 deviation by position: "
          + " ".join(f"{(m[p, 7] / m[p].sum() * 10 - 1) * 100:+.1f}%" for p in range(4)))
deviation_table(after, f"After {end}")

def dev(ds):
    m = digit_matrix(ds)
    return (m / m.sum(1, keepdims=True) - 0.1).ravel()
mid = len(during) // 2
print(f"\nPattern stability: corr(first half, second half of biased period) = "
      f"{np.corrcoef(dev(during[:mid]), dev(during[mid:]))[0, 1]:.2f}; "
      f"corr(biased period, after) = {np.corrcoef(dev(during), dev(after))[0, 1]:.2f}")

# 3. What the bias is worth
print("\nModel fitted on biased draws before 2023, frozen, applied to later draws:")
order, _ = rank([d for d in during if d < "2023"])
evaluate(order, [d for d in during if d >= "2023"], "2023 .. end of bias")
evaluate(order, after, "after the bias ended")
print("Hindsight upper bound (fitted and scored on the whole biased period):")
order, score = rank(during)
evaluate(order, during, "in-sample")
print(f"  model lift of the single best number x{math.exp(score[0]):.3f}, 100th best "
      f"x{math.exp(score[99]):.3f}; Big Forecast needs ~x1.56 to break even")
print("  top-ranked numbers:", " ".join(f"{n:04d}" for n in order[:10]))
