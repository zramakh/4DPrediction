#!/usr/bin/env python3
"""Score the picks logged in forward_log.csv (before each draw) against the
results in data/*.csv, plus two no-formula leads computed from earlier draws:
the cold number (each position's least frequent digit per operator) and 1024 on
Magnum. RM1 Big per pick; payouts 1st 2500, 2nd 1000, 3rd 500, Special 180,
Consolation 60. Reverse and i-Box matches (other arrangements) are listed too.

Run from the repo root:  python3 analysis/score_live.py 2026-10-17 [2026-10-18 ...]
"""

import collections
import csv
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPS = ["Magnum", "Sports Toto", "Da Ma Cai"]
FILES = {"Magnum": "magnum.csv", "Sports Toto": "sportstoto.csv", "Da Ma Cai": "damacai.csv"}
BIG = {"1st": 2500, "2nd": 1000, "3rd": 500, "Special": 180, "Consolation": 60}


def load():
    rows = {op: list(csv.DictReader(open(os.path.join(ROOT, "data", f)))) for op, f in FILES.items()}
    log = list(csv.DictReader(open(os.path.join(ROOT, "analysis", "forward_log.csv"))))
    return rows, log


def picks_for(log, date):
    out = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in log:
        if r["draw_date"] == date:
            ops = OPS if r["operator"] in ("All", "all") else [r["operator"]]
            for o in ops:
                out[r["variant"]][o].append(r["4d_number"])
    return out


def cold_numbers(rows, date):
    out = {}
    for op in OPS:
        D = np.array([[int(c) for c in r["4d_number"]] for r in rows[op] if r["date"] < date])
        cnt = np.stack([np.bincount(D[:, p], minlength=10) for p in range(4)])
        out[op] = ["".join(str(int(np.argmin(cnt[p] + np.arange(10) * 1e-9))) for p in range(4))]
    return out


def score(nums_by_op, win):
    stake = pay = 0
    straight, reverse, ibox = [], [], []
    for op, nums in nums_by_op.items():
        w = win.get(op, {})
        for n in dict.fromkeys(nums):
            stake += 1
            if n in w:
                straight.append(f"{n} {op} {w[n]}")
                pay += BIG[w[n]]
            if n[::-1] != n and n[::-1] in w:
                reverse.append(f"{n}->{n[::-1]} {op} {w[n[::-1]]}")
            for m, p in w.items():
                if m != n and sorted(m) == sorted(n):
                    ibox.append(f"{n}~{m} {op} {p}")
    return stake, pay, straight, reverse, ibox


def main():
    rows, log = load()
    for date in sys.argv[1:]:
        win = {op: {r["4d_number"]: r["prize"] for r in rows[op] if r["date"] == date} for op in OPS}
        if not any(win.values()):
            print(f"{date}: no results in data/ yet")
            continue
        print(f"\n=== {date} ===")
        sets = dict(picks_for(log, date))
        sets["cold_number_noparam"] = cold_numbers(rows, date)
        sets["1024_magnum"] = {"Magnum": ["1024"]}
        tot_s = tot_p = 0
        for v in sorted(sets):
            stake, pay, s, rv, b = score(sets[v], win)
            tot_s += stake
            tot_p += pay
            extra = (f"; reverse {rv}" if rv else "") + (f"; i-Box {b}" if b else "")
            print(f"  {v:<36} {stake:>3} bets  straight {len(s)} {s if s else ''} RM{pay}{extra}")
        print(f"  all formulas together: RM{tot_p} back on RM{tot_s} staked")


if __name__ == "__main__":
    main()
