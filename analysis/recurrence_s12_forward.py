#!/usr/bin/env python3
"""Walk-forward check for recurrence_s12.py: pick the top 5 single/pair
parameters per column (S1/S2 x a/b x Straight/Reverse/i-Box) using draw days in
1985-2011 only, then score those same picks on 2012-2026 draw days.
(For version (a) the later days still use all earlier same-value days as the
source, as one would in practice.)

Run from the repo root:  python3 analysis/recurrence_s12_forward.py
"""

import itertools
import json
import math
import multiprocessing as mp
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recurrence_s12 as r  # noqa: E402

SPLIT = 2012
ORIG = r.score


def period_score(late):
    yr = r.G["yr"]

    def sc(days, P):
        m = (yr[days] >= SPLIT) if late else (yr[days] < SPLIT)
        return ORIG(days[m], P[m])
    return sc


def task(args):
    test, late = args
    r.score = period_score(late)
    return r.evaluate(r.cells_of(test))


def main():
    r.setup()
    r.G["yr"] = np.array([int(d[:4]) for d in r.G["D"].dates])
    tests = [(f,) for f in r.FACT] + list(itertools.combinations(r.FACT, 2))
    with mp.get_context("fork").Pool(4) as pool:
        early = pool.map(task, [(t, False) for t in tests], chunksize=16)
        late = pool.map(task, [(t, True) for t in tests], chunksize=16)
    z = lambda oe: (oe[0] - oe[1]) / math.sqrt(oe[1])
    out = {}
    tot = []
    print(f"Top 5 per column chosen on draw days before {SPLIT}, scored on {SPLIT}-2026")
    for col in r.COLS:
        ze = np.array([z(x[col]) for x in early])
        zl = np.array([z(x[col]) for x in late])
        top = np.argsort(-ze)[:5]
        print(f"  {col:<16} all tests' later z: mean {zl.mean():+.2f}")
        rows = []
        for q in top:
            o, e = late[q][col]
            print(f"     {' x '.join(tests[q]):<44} before: z {ze[q]:+.2f} | after: {o:.0f} vs {e:.1f} (x{o / e:.3f}, z {zl[q]:+.2f})")
            rows.append({"test": " x ".join(tests[q]), "z_before": float(ze[q]), "hits_after": o, "exp_after": e,
                         "z_after": float(zl[q])})
            tot.append(zl[q])
        out[col] = rows
    tot = np.array(tot)
    print(f"\nAll 60 chosen formulas after {SPLIT}: mean z {tot.mean():+.2f} (0 = chance), "
          f"{int((tot > 0).sum())}/60 above chance, {int((tot > 2).sum())} with z > 2")
    json.dump({"split": SPLIT, "columns": out, "mean_z_after": float(tot.mean())},
              open(os.path.join(r.ROOT, "analysis", "recurrence_s12_forward_results.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
