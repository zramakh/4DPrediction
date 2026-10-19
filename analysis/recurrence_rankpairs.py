#!/usr/bin/env python3
"""S3-style picks for every hot/cold rank pair. In each position the digits are
ranked 1 (hottest) .. 10 (coldest) from earlier same-value days; a pair takes
the digit of rank k and rank 11-k in each position, 2^4 = 16 numbers:
  1+10 (= S3), 2+9, 3+8, 4+7, 5+6
Same tests and checks as recurrence_s3.py: 78 single parameters and 3,003 pairs,
(a) all earlier / (b) previous same-value day, Straight / Reverse / i-Box,
forward (top 5 before 2012 -> 2012-2026) and shifted parameter calendars.
Ranks use counts with ties to the lower digit.

Run from the repo root:  python3 analysis/recurrence_rankpairs.py [n_shifts]
"""

import itertools
import json
import os
import sys
import time
import multiprocessing as mp

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recurrence_s12 as r  # noqa: E402
import recurrence_s12_k as rk  # noqa: E402
import recurrence_s3 as s3  # noqa: E402

PAIRS = [(0, 9), (1, 8), (2, 7), (3, 6), (4, 5)]
RULES = s3.RULES
COLS = [(pr, v, rule) for pr in PAIRS for v in "ab" for rule in RULES]
POW = s3.POW
BITS = r.BITS
SPLIT = s3.SPLIT


def label(pr):
    return f"{pr[0] + 1}+{pr[1] + 1}"


def pair_picks(order, pr):
    two = order[:, :, list(pr)]                                           # (n, 4, 2)
    dig = np.take_along_axis(two, BITS.T[None, :, :], 2)
    return (dig * POW[None, :, None]).sum(1)


def evaluate(cells):
    G = r.G
    dday = G["dday"]
    order = np.lexsort((np.arange(len(cells)), cells))
    sc = cells[order]
    newgrp = np.r_[True, sc[1:] != sc[:-1]]
    has_prev = ~newgrp
    days = order[has_prev]
    late = G["yr"][days] >= SPLIT
    cs = np.cumsum(dday[order], axis=0)
    start = np.maximum.accumulate(np.where(newgrp, np.arange(len(sc)), 0))
    base = np.where((start > 0)[:, None, None], cs[np.maximum(start - 1, 0)], 0)
    src = {"a": (cs - dday[order] - base)[has_prev], "b": dday[order[:-1]][has_prev[1:]]}
    ranked = {v: np.argsort(-C, axis=2, kind="stable") for v, C in src.items()}   # digit at each rank
    res = {}
    for pr in PAIRS:
        for v in "ab":
            sd = rk.score_days(days, pair_picks(ranked[v], pr))
            for rule in RULES:
                h, e = sd[rule][0][:, -1].astype(float), sd[rule][1][:, -1]
                res[(pr, v, rule)] = (h[~late].sum(), e[~late].sum(), h[late].sum(), e[late].sum())
    return np.array([res[c] for c in COLS])


def task(args):
    test, shift = args
    return evaluate(r.cells_of(test, shift))


def main():
    n_shifts = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    t0 = time.time()
    r.setup()
    r.G["yr"] = np.array([int(d[:4]) for d in r.G["D"].dates])
    tests = [(f,) for f in r.FACT] + list(itertools.combinations(r.FACT, 2))
    names = [" x ".join(t) for t in tests]
    zz = s3.zz
    ref = evaluate(np.zeros(r.G["nd"], np.int64))
    with mp.get_context("fork").Pool(4) as pool:
        A = np.array(pool.map(task, [(t, 0) for t in tests], chunksize=16))
        print(f"{len(tests)} tests x {len(COLS)} columns ({time.time() - t0:.0f}s)", flush=True)
        rng = np.random.default_rng(31)
        null = []
        for k in range(n_shifts):
            sh = int(rng.integers(170, r.G["nd"] - 170))
            B = np.array(pool.map(task, [(t, sh) for t in tests], chunksize=16))
            _, _, zallB, _, fwdB = s3.summary(B)
            null.append({"z_gt_2": (zallB > 2).sum(0).tolist(), "best": zallB.max(0).tolist(), "forward": fwdB.tolist()})
            print(f"shift {k + 1}/{n_shifts} ({time.time() - t0:.0f}s)", flush=True)
    zb, za, zall, top, fwd = s3.summary(A)
    ng = np.array([x["z_gt_2"] for x in null])
    nb = np.array([x["best"] for x in null])
    nf = np.array([x["forward"] for x in null])
    report = {"tests": len(tests), "n_shifts": n_shifts, "columns": []}
    print(f"\nranks  ver rule      | no param 2012-26 | z>2 real (shifted) | best z real (shifted, as high) | forward real (shifted, as high)")
    for ci, (pr, v, rule) in enumerate(COLS):
        o = ref[ci]
        cnt, best = int((zall[:, ci] > 2).sum()), float(zall[:, ci].max())
        print(f"{label(pr):<6} ({v}) {rule:<9} | x{o[2] / o[3]:.3f} ({zz(o[2], o[3]):+.2f}) | {cnt:>4} ({ng[:, ci].mean():>4.0f}) | "
              f"{best:+.2f} ({nb[:, ci].mean():+.2f}, {int((nb[:, ci] >= best).sum())}/{n_shifts}) | "
              f"{fwd[ci]:+.2f} ({nf[:, ci].mean():+.2f}, {int((nf[:, ci] >= fwd[ci]).sum())}/{n_shifts})")
        report["columns"].append({
            "ranks": label(pr), "version": v, "rule": rule,
            "no_param_after": {"hits": float(o[2]), "exp": float(o[3])},
            "z_gt_2": cnt, "null_z_gt_2": ng[:, ci].tolist(), "best_z": best,
            "best_test": names[int(np.argmax(zall[:, ci]))], "null_best": nb[:, ci].tolist(),
            "forward_mean_z": float(fwd[ci]), "null_forward": nf[:, ci].tolist(),
            "forward_tests": [{"test": names[q], "z_before": float(zb[q, ci]), "hits_after": float(A[q, ci, 2]),
                               "exp_after": float(A[q, ci, 3]), "z_after": float(za[q, ci])} for q in top[:, ci]]})
    print("\nBy rank pair (averaged over versions and rules): forward real vs shifted; no-parameter ratio after 2012")
    for pr in PAIRS:
        idx = [ci for ci, c in enumerate(COLS) if c[0] == pr]
        nr = np.mean([ref[ci, 2] / ref[ci, 3] for ci in idx])
        print(f"   {label(pr):<5} forward {fwd[idx].mean():+.2f} vs shifted {nf[:, idx].mean():+.2f} "
              f"(real beats {np.mean([(nf[:, ci] < fwd[ci]).mean() for ci in idx]):.0%} of shifts); no-parameter x{nr:.3f}")
    beat = np.array([(nf[:, ci] < fwd[ci]).mean() for ci in range(len(COLS))])
    print(f"\nColumns where the real forward beats every shifted calendar: {int((beat == 1).sum())} of {len(COLS)} "
          f"(about {len(COLS) / (n_shifts + 1):.1f} expected by chance)")
    for ci in np.flatnonzero(beat == 1):
        pr, v, rule = COLS[ci]
        print(f"   {label(pr)} ({v}) {rule}: forward {fwd[ci]:+.2f} vs shifted {nf[:, ci].mean():+.2f}")
        for x in report["columns"][ci]["forward_tests"][:3]:
            print(f"      {x['test']:<44} before z {x['z_before']:+.2f} -> after {x['hits_after']:.0f}/{x['exp_after']:.1f} "
                  f"(x{x['hits_after'] / x['exp_after']:.3f}, z {x['z_after']:+.2f})")
    json.dump(report, open(os.path.join(r.ROOT, "analysis", "recurrence_rankpairs_results.json"), "w"), indent=1)
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
