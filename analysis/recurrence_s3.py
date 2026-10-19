#!/usr/bin/env python3
"""S3 = the hottest AND the coldest digit in each position, combined: 2^4 = 16
numbers (e.g. hottest 7/3/4/7 and coldest 2/8/0/9 -> 7347, 7349, ..., 2809).

Tested like S1 / S2 in recurrence_s12.py: 78 single parameters and 3,003 pairs;
(a) digit counts from ALL earlier draw days with the same value(s), (b) from the
PREVIOUS same-value day only; Straight / Reverse / i-Box hits on all 3
operators; chance from that year's digit mix per position.
Checks per column (version x rule):
  scan     tests with z > 2 and best z over all years
  forward  the 5 tests with the best z before 2012, scored 2012-2026
both against the same procedure on circularly shifted parameter calendars.
Reference: S3 with no parameter.

Run from the repo root:  python3 analysis/recurrence_s3.py [n_shifts]
"""

import itertools
import json
import math
import multiprocessing as mp
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recurrence_s12 as r  # noqa: E402
import recurrence_s12_k as rk  # noqa: E402

SPLIT = 2012
RULES = ("straight", "reverse", "ibox")
COLS = [(v, rule) for v in "ab" for rule in RULES]
POW = np.array([1000, 100, 10, 1])
BITS = r.BITS


def s3_picks(C):
    """C (n, 4, 10) -> (n, 16): hottest and coldest digit per position (ties -> lower digit;
    if the two coincide, the next coldest is used)."""
    hot = np.argsort(-C, axis=2, kind="stable")[:, :, 0]
    asc = np.argsort(C, axis=2, kind="stable")
    cold = np.where(asc[:, :, 0] == hot, asc[:, :, 1], asc[:, :, 0])
    two = np.stack([hot, cold], axis=2)                                    # (n, 4, 2): bit 0 = hot, 1 = cold
    dig = np.take_along_axis(two, BITS.T[None, :, :], 2)                  # (n, 4, 16)
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
    out = []
    for v in "ab":
        res = rk.score_days(days, s3_picks(src[v]))
        for rule in RULES:
            h, e = res[rule][0][:, -1].astype(float), res[rule][1][:, -1]
            out.append((h[~late].sum(), e[~late].sum(), h[late].sum(), e[late].sum()))
    return np.array(out)


def task(args):
    test, shift = args
    return evaluate(r.cells_of(test, shift))


def zz(o, e):
    return (o - e) / np.sqrt(np.maximum(e, 1e-9))


def summary(A):
    zb, za = zz(A[:, :, 0], A[:, :, 1]), zz(A[:, :, 2], A[:, :, 3])
    zall = zz(A[:, :, 0] + A[:, :, 2], A[:, :, 1] + A[:, :, 3])
    top = np.argsort(-zb, axis=0)[:5]
    return zb, za, zall, top, np.take_along_axis(za, top, 0).mean(0)


def main():
    n_shifts = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    t0 = time.time()
    r.setup()
    r.G["yr"] = np.array([int(d[:4]) for d in r.G["D"].dates])
    tests = [(f,) for f in r.FACT] + list(itertools.combinations(r.FACT, 2))
    names = [" x ".join(t) for t in tests]
    ref = evaluate(np.zeros(r.G["nd"], np.int64))
    print("S3 with no parameter:")
    for ci, (v, rule) in enumerate(COLS):
        o = ref[ci]
        print(f"   ({v}) {rule:<9} before 2012 x{o[0] / o[1]:.3f} (z {zz(o[0], o[1]):+.2f}) | 2012-2026 x{o[2] / o[3]:.3f} (z {zz(o[2], o[3]):+.2f})")
    with mp.get_context("fork").Pool(4) as pool:
        A = np.array(pool.map(task, [(t, 0) for t in tests], chunksize=16))
        print(f"{len(tests)} tests ({time.time() - t0:.0f}s)", flush=True)
        rng = np.random.default_rng(21)
        null = []
        for k in range(n_shifts):
            sh = int(rng.integers(170, r.G["nd"] - 170))
            B = np.array(pool.map(task, [(t, sh) for t in tests], chunksize=16))
            _, _, zallB, _, fwdB = summary(B)
            null.append({"z_gt_2": (zallB > 2).sum(0).tolist(), "best": zallB.max(0).tolist(), "forward": fwdB.tolist()})
            print(f"shift {k + 1}/{n_shifts} ({time.time() - t0:.0f}s)", flush=True)
    zb, za, zall, top, fwd = summary(A)
    ng = np.array([x["z_gt_2"] for x in null])
    nb = np.array([x["best"] for x in null])
    nf = np.array([x["forward"] for x in null])
    report = {"tests": len(tests), "n_shifts": n_shifts, "reference_no_parameter": ref.tolist(), "columns": []}
    print("\ncolumn          z>2 real | shifted mean (range)  best z real | shifted mean, shifts as high  "
          "forward real | shifted mean, shifts as high")
    for ci, (v, rule) in enumerate(COLS):
        cnt, best = int((zall[:, ci] > 2).sum()), float(zall[:, ci].max())
        print(f"({v}) {rule:<10} {cnt:>5} | {ng[:, ci].mean():>5.0f} ({ng[:, ci].min()}-{ng[:, ci].max()})   "
              f"{best:+.2f} | {nb[:, ci].mean():+.2f}, {int((nb[:, ci] >= best).sum())}/{n_shifts}   "
              f"{fwd[ci]:+.2f} | {nf[:, ci].mean():+.2f}, {int((nf[:, ci] >= fwd[ci]).sum())}/{n_shifts}")
        rows = []
        for q in top[:, ci]:
            o = A[q, ci]
            rows.append({"test": names[q], "z_before": float(zb[q, ci]), "hits_after": float(o[2]),
                         "exp_after": float(o[3]), "z_after": float(za[q, ci])})
        best_q = int(np.argmax(zall[:, ci]))
        report["columns"].append({"version": v, "rule": rule, "z_gt_2": cnt, "null_z_gt_2": ng[:, ci].tolist(),
                                  "best_z": best, "best_test": names[best_q], "null_best": nb[:, ci].tolist(),
                                  "forward_mean_z": float(fwd[ci]), "null_forward": nf[:, ci].tolist(),
                                  "forward_tests": rows})
    print("\nForward detail (top 5 chosen on draws before 2012 -> 2012-2026):")
    for c in report["columns"]:
        print(f"  ({c['version']}) {c['rule']}   best over all years: {c['best_test']} (z {c['best_z']:+.2f})")
        for x in c["forward_tests"]:
            print(f"     {x['test']:<44} before z {x['z_before']:+.2f} -> after {x['hits_after']:.0f}/{x['exp_after']:.1f} "
                  f"(x{x['hits_after'] / x['exp_after']:.3f}, z {x['z_after']:+.2f})")
    json.dump(report, open(os.path.join(r.ROOT, "analysis", "recurrence_s3_results.json"), "w"), indent=1)
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
