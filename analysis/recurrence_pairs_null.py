#!/usr/bin/env python3
"""Null for recurrence_pairs.py: rerun the full 3,003-pair scan with the whole
parameter calendar circularly shifted (one shift for all parameters, at least
about a year of draw days). Gives the best z and the count of z > 2 that the
scan produces when parameters and results are unrelated.

Run from the repo root:  python3 analysis/recurrence_pairs_null.py
"""

import itertools
import json
import math
import multiprocessing as mp
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recurrence_pairs as rp  # noqa: E402

N_SHIFTS = 10


def task(args):
    f1, f2, s = args
    oa, ea, ob, eb = rp.evaluate(rp.joint(f1, f2, s))
    return (oa - ea) / math.sqrt(ea), (ob - eb) / math.sqrt(eb)


def main():
    rp.setup()
    pairs = list(itertools.combinations(rp.FACT, 2))
    rng = np.random.default_rng(1)
    nd = rp.G["nd"]
    real = json.load(open(os.path.join(rp.ROOT, "analysis", "recurrence_pairs_results.json")))
    out = []
    with mp.get_context("fork").Pool(4) as pool:
        for _ in range(N_SHIFTS):
            s = int(rng.integers(170, nd - 170))
            z = np.array(pool.map(task, [(a, b, s) for a, b in pairs], chunksize=16))
            r = {"shift": s, "a_max_z": float(z[:, 0].max()), "a_z_gt_2": int((z[:, 0] > 2).sum()),
                 "b_max_z": float(z[:, 1].max()), "b_z_gt_2": int((z[:, 1] > 2).sum())}
            out.append(r)
            print(r, flush=True)
    for k in ("a", "b"):
        mx = [r[f"{k}_max_z"] for r in out]
        cnt = [r[f"{k}_z_gt_2"] for r in out]
        print(f"({k}) real best z {real[k]['top'][0][f'{k}_z']:+.2f}, z>2 count {real[k]['z_gt_2']} | "
              f"shifted: best z {np.mean(mx):+.2f} (range {min(mx):+.2f}..{max(mx):+.2f}), "
              f"z>2 count {np.mean(cnt):.0f} (range {min(cnt)}..{max(cnt)})")
    json.dump(out, open(os.path.join(rp.ROOT, "analysis", "recurrence_pairs_null.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
