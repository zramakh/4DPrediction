#!/usr/bin/env python3
"""Whole-number hot / cold picks from earlier days with the same parameter value(s).

For each draw day whose value (single parameter) or pair of values occurred
before: count how many times each 4D number won (any prize, any operator, once
per date) on ALL earlier same-value days.
  hot   16 numbers with the highest count (ties -> more wins overall before
        that day, then lower number)
  cold  16 numbers with the lowest count (ties -> fewer wins overall, then
        lower number)
Scored as Straight / Reverse / i-Box with chance from that year's digit mix
(as recurrence_s12.py). (The "previous same-value day only" version is the
number-recurrence test already done in recurrence_perm.py.)

Checks per column (hot/cold x rule): the 5 tests with the best z before 2012,
scored 2012-2026, against the same procedure on shifted parameter calendars.
References: hot / cold with no parameter.

Run from the repo root:  python3 analysis/whole_number_test.py [n_shifts]
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
COLS = [(s, rule) for s in ("hot", "cold") for rule in ("straight", "reverse", "ibox")]
NUM = np.arange(10000)


def setup():
    r.setup()
    G = r.G
    G["yr"] = np.array([int(d[:4]) for d in G["D"].dates])
    W = G["W"]
    # wins of each number on all days before day t
    G["Gc"] = np.vstack([np.zeros((1, 10000), np.int16), np.cumsum(W, 0, dtype=np.int16)[:-1]])
    # per day: numbers by overall wins before that day, hottest first / coldest first (ties -> lower number)
    G["ghot"] = np.array([np.lexsort((NUM, -g))[:64] for g in G["Gc"]])
    G["gcold"] = np.array([np.lexsort((NUM, g))[:300] for g in G["Gc"]])


def evaluate(cells):
    """(len(COLS), 4): hits before, expected before, hits after, expected after."""
    G = r.G
    W, Gc = G["W"], G["Gc"]
    order = np.lexsort((np.arange(len(cells)), cells))
    sc = cells[order]
    bounds = np.r_[0, np.flatnonzero(np.diff(sc)) + 1, len(sc)]
    days, hot, cold = [], [], []
    ghot, gcold = G["ghot"], G["gcold"]
    for a, b in zip(bounds[:-1], bounds[1:]):
        cnt = np.zeros(10000, np.int32)
        for k, t in enumerate(order[a:b]):
            if k:
                nz = np.flatnonzero(cnt)
                cand = np.union1d(nz, ghot[t]) if len(nz) < 16 else nz
                g = Gc[t, cand].astype(np.float64)
                kh = cnt[cand] * 1e4 + g - cand * 1e-5
                hot.append(cand[np.argsort(-kh)[:16]])
                c = gcold[t][cnt[gcold[t]] == 0][:16]
                cold.append(c)
                days.append(t)
            cnt += W[t]
    days = np.array(days)
    late = G["yr"][days] >= SPLIT
    out = []
    for s, P in (("hot", np.array(hot)), ("cold", np.array(cold))):
        res = rk.score_days(days, P)
        for rule in ("straight", "reverse", "ibox"):
            h, e = res[rule][0][:, -1].astype(float), res[rule][1][:, -1]
            out.append((h[~late].sum(), e[~late].sum(), h[late].sum(), e[late].sum()))
    return np.array(out)


def task(args):
    test, shift = args
    return evaluate(r.cells_of(test, shift))


def zz(o, e):
    return (o - e) / np.sqrt(np.maximum(e, 1e-9))


def main():
    n_shifts = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    t0 = time.time()
    setup()
    tests = [(f,) for f in r.FACT] + list(itertools.combinations(r.FACT, 2))
    names = [" x ".join(t) for t in tests]
    ref = evaluate(np.zeros(r.G["nd"], np.int64))
    print("No parameter (all earlier days):")
    for ci, (s, rule) in enumerate(COLS):
        o = ref[ci]
        print(f"   {s:<5} {rule:<9} before 2012 x{o[0] / o[1]:.3f} (z {zz(o[0], o[1]):+.2f}) | "
              f"2012-2026 x{o[2] / o[3]:.3f} (z {zz(o[2], o[3]):+.2f})", flush=True)
    with mp.get_context("fork").Pool(4) as pool:
        A = np.array(pool.map(task, [(t, 0) for t in tests], chunksize=8))
        print(f"{len(tests)} tests ({time.time() - t0:.0f}s)", flush=True)
        rng = np.random.default_rng(9)
        null = []
        for k in range(n_shifts):
            sh = int(rng.integers(170, r.G["nd"] - 170))
            B = np.array(pool.map(task, [(t, sh) for t in tests], chunksize=8))
            zb, za = zz(B[:, :, 0], B[:, :, 1]), zz(B[:, :, 2], B[:, :, 3])
            top = np.argsort(-zb, axis=0)[:5]
            null.append({"forward": np.take_along_axis(za, top, 0).mean(0).tolist(),
                         "best_all": zz(B[:, :, 0] + B[:, :, 2], B[:, :, 1] + B[:, :, 3]).max(0).tolist()})
            print(f"shift {k + 1}/{n_shifts} ({time.time() - t0:.0f}s)", flush=True)
    zb, za = zz(A[:, :, 0], A[:, :, 1]), zz(A[:, :, 2], A[:, :, 3])
    zall = zz(A[:, :, 0] + A[:, :, 2], A[:, :, 1] + A[:, :, 3])
    top = np.argsort(-zb, axis=0)[:5]
    fwd = np.take_along_axis(za, top, 0).mean(0)
    nf = np.array([x["forward"] for x in null])
    nb = np.array([x["best_all"] for x in null])
    report = {"reference_no_parameter": ref.tolist(), "columns": []}
    print("\nPer column: forward = top 5 tests chosen on draws before 2012, mean z on 2012-2026")
    for ci, (s, rule) in enumerate(COLS):
        print(f"\n{s} {rule}: forward {fwd[ci]:+.2f} (shifted {nf[:, ci].mean():+.2f}, {int((nf[:, ci] >= fwd[ci]).sum())}/{n_shifts} as high) | "
              f"best z all years {zall[:, ci].max():+.2f} [{names[int(np.argmax(zall[:, ci]))]}] "
              f"(shifted best {nb[:, ci].mean():+.2f}, {int((nb[:, ci] >= zall[:, ci].max()).sum())}/{n_shifts} as high)")
        rows = []
        for q in top[:, ci]:
            o = A[q, ci]
            print(f"   {names[q]:<44} before z {zb[q, ci]:+.2f} -> after {o[2]:.0f}/{o[3]:.1f} (x{o[2] / o[3]:.3f}, z {za[q, ci]:+.2f})")
            rows.append({"test": names[q], "z_before": float(zb[q, ci]), "hits_after": float(o[2]),
                         "exp_after": float(o[3]), "z_after": float(za[q, ci])})
        report["columns"].append({"strategy": s, "rule": rule, "forward_mean_z": float(fwd[ci]),
                                  "null_forward": nf[:, ci].tolist(), "best_z_all": float(zall[:, ci].max()),
                                  "best_test": names[int(np.argmax(zall[:, ci]))], "null_best": nb[:, ci].tolist(),
                                  "forward_tests": rows})
    json.dump(report, open(os.path.join(r.ROOT, "analysis", "whole_number_results.json"), "w"), indent=1)
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
