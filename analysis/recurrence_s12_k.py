#!/usr/bin/env python3
"""recurrence_s12.py with the number of picks varied, for all 78 single
parameters and 3,003 pairs, S1 (hot) / S2 (cold), (a) all earlier / (b)
previous same-value day, scored as Straight / Reverse / i-Box.

Picks per draw day from the source days' digit counts per position:
  top K   numbers ranked by sum over positions of log(count + 1) (S1: highest,
          S2: lowest; ties -> lower number), K = 1, 2, 4, 8, 16, 32, 64
  grid    top-2 / top-3 digits per position: 16 / 81 numbers (grid 16 = S1/S2
          as in recurrence_s12.py)
Chance per day uses that year's digit mix per position (as before).
Every test is scored before 2012 and 2012-2026. Two checks per column
(strategy x version x rule x pick amount):
  scan     number of tests with z > 2 and best z over all years
  forward  the 5 tests with the best z before 2012, scored 2012-2026
Both are repeated on circularly shifted parameter calendars (one shift for all
parameters, at least about a year of draw days) for the chance level.

Run from the repo root:  python3 analysis/recurrence_s12_k.py [n_shifts]
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

KS = [1, 2, 4, 8, 16, 32, 64]
PICKS = [f"top{k}" for k in KS] + ["grid16", "grid81"]
RULES = ("straight", "reverse", "ibox")
COLS = [(s, v, rule, p) for s in ("S1", "S2") for v in "ab" for rule in RULES for p in PICKS]
SPLIT = 2012
POW = np.array([1000, 100, 10, 1])
KMAX = KS[-1]
H2 = np.array(list(itertools.product(range(10), repeat=2)))                 # digit-rank pairs for half a number
# (i, j) = ranks within the two halves; (i, j) is beaten by (i + 1)(j + 1) - 1 numbers, so only these can be top-64
IJ = np.array([(i, j) for i in range(KMAX) for j in range(KMAX) if (i + 1) * (j + 1) <= KMAX])
G3 = np.array(list(itertools.product(range(3), repeat=4)))
G16 = np.flatnonzero(G3.max(1) < 2)


def half(order, L, p):
    """Top-64 two-digit halves for positions p, p+1: (score, number 0-99) sorted best first."""
    d0 = order[:, p, H2[:, 0]]
    d1 = order[:, p + 1, H2[:, 1]]
    sc = np.take_along_axis(L[:, p], d0, 1) + np.take_along_axis(L[:, p + 1], d1, 1)
    hn = d0 * 10 + d1
    key = -np.round(sc * 1e6).astype(np.int64) * 100 + hn
    o = np.argsort(key, axis=1)[:, :KMAX]
    return np.take_along_axis(sc, o, 1), np.take_along_axis(hn, o, 1)


def pick_sets(C, hot):
    """C (n, 4, 10) -> (ranked top-64 numbers in rank order (n, 64), grid16 (n, 16), grid81 (n, 81))."""
    order = np.argsort(-C if hot else C, axis=2, kind="stable")             # digit at each rank (ties -> lower digit)
    L = np.log(C + 1) * (1 if hot else -1)
    s1, n1 = half(order, L, 0)
    s2, n2 = half(order, L, 2)
    sc = s1[:, IJ[:, 0]] + s2[:, IJ[:, 1]]
    num = n1[:, IJ[:, 0]] * 100 + n2[:, IJ[:, 1]]
    key = -np.round(sc * 1e6).astype(np.int64) * 10000 + num
    part = np.argpartition(key, KMAX, axis=1)[:, :KMAX]
    part = np.take_along_axis(part, np.argsort(np.take_along_axis(key, part, 1), axis=1), 1)
    g = sum(order[:, q, G3[:, q]] * POW[q] for q in range(4))                  # (n, 81) grid numbers
    return np.take_along_axis(num, part, 1), g[:, G16], g


def first_in_row(B):
    """Mask of the first occurrence of each value along each row, in the given order."""
    o = np.argsort(B, axis=1, kind="stable")
    sb = np.take_along_axis(B, o, 1)
    f = np.ones_like(sb, bool)
    f[:, 1:] = sb[:, 1:] != sb[:, :-1]
    out = np.empty_like(f)
    np.put_along_axis(out, o, f, 1)
    return out


def score_days(days, P):
    """Per-day cumulative (hits, expected) along the columns of P for each rule: rule -> ((n, K), (n, K))."""
    G = r.G
    W, rev, pal, box, Cb, Py, Pbox, nwin = (G[k] for k in ("W", "rev", "pal", "box", "Cb", "Py", "Pbox", "nwin"))
    y = G["yix"][days][:, None]
    nw = nwin[days][:, None]
    d = days[:, None]
    out = {"straight": (np.cumsum(W[d, P], 1), nw * np.cumsum(Py[y, P], 1))}
    R = rev[P]
    ok = ~pal[P]
    out["reverse"] = (np.cumsum(W[d, R] & ok, 1), nw * np.cumsum(Py[y, R] * ok, 1))
    B = box[P]
    f = first_in_row(B)
    out["ibox"] = (np.cumsum(Cb[d, B] * f, 1), nw * np.cumsum(Pbox[y, B] * f, 1))
    return out


def evaluate(cells):
    """(len(COLS), 4) array: hits before, expected before, hits after, expected after."""
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
    res = {}
    for s, hot in (("S1", True), ("S2", False)):
        for v in "ab":
            ranked, g16, g81 = pick_sets(src[v], hot)
            for P, cols in ((ranked, {f"top{k}": k for k in KS}), (g16, {"grid16": 16}), (g81, {"grid81": 81})):
                for rule, (h, e) in score_days(days, P).items():
                    hb, eb, ha, ea = h[~late].sum(0), e[~late].sum(0), h[late].sum(0), e[late].sum(0)
                    for pname, kk in cols.items():
                        res[(s, v, rule, pname)] = (hb[kk - 1], eb[kk - 1], ha[kk - 1], ea[kk - 1])
    return np.array([res[c] for c in COLS], float)


def task(args):
    test, shift = args
    return evaluate(r.cells_of(test, shift))


def zz(o, e):
    return (o - e) / np.sqrt(np.maximum(e, 1e-9))


def stats(A):
    """A (tests, cols, 4) -> per column: z>2 count, best z (all years), forward mean z of top-5-before."""
    z_all = zz(A[:, :, 0] + A[:, :, 2], A[:, :, 1] + A[:, :, 3])
    z_b = zz(A[:, :, 0], A[:, :, 1])
    z_a = zz(A[:, :, 2], A[:, :, 3])
    top = np.argsort(-z_b, axis=0)[:5]                                       # (5, cols)
    fwd = np.take_along_axis(z_a, top, 0).mean(0)
    return (z_all > 2).sum(0), z_all.max(0), fwd, z_all, z_b, z_a, top


def main():
    n_shifts = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    t0 = time.time()
    r.setup()
    r.G["yr"] = np.array([int(d[:4]) for d in r.G["D"].dates])
    tests = [(f,) for f in r.FACT] + list(itertools.combinations(r.FACT, 2))
    names = [" x ".join(t) for t in tests]
    with mp.get_context("fork").Pool(4) as pool:
        A = np.array(pool.map(task, [(t, 0) for t in tests], chunksize=8))
        print(f"{len(tests)} tests x {len(COLS)} columns ({time.time() - t0:.0f}s)", flush=True)
        rng = np.random.default_rng(5)
        nulls = []
        for k in range(n_shifts):
            sh = int(rng.integers(170, r.G["nd"] - 170))
            nulls.append(stats(np.array(pool.map(task, [(t, sh) for t in tests], chunksize=8)))[:3])
            print(f"shift {k + 1}/{n_shifts} ({time.time() - t0:.0f}s)", flush=True)
    cnt, best, fwd, z_all, z_b, z_a, top = stats(A)
    ncnt = np.array([x[0] for x in nulls])
    nbest = np.array([x[1] for x in nulls])
    nfwd = np.array([x[2] for x in nulls])
    report = {"tests": len(tests), "n_shifts": n_shifts, "columns": []}
    print("\nPer column: z>2 count real (shifted mean) | best z real (shifted mean, shifts as high) | "
          "forward: top 5 chosen before 2012, mean z 2012-2026 real (shifted mean, shifts as high)")
    for ci, (s, v, rule, p) in enumerate(COLS):
        if p == PICKS[0]:
            print(f"\n{s} ({v}) {rule}")
        fb = int((nfwd[:, ci] >= fwd[ci]).sum())
        bb = int((nbest[:, ci] >= best[ci]).sum())
        print(f"   {p:<7} z>2 {cnt[ci]:>4} ({ncnt[:, ci].mean():>5.0f}) | best {best[ci]:+.2f} ({nbest[:, ci].mean():+.2f}, {bb}/{n_shifts}) | "
              f"forward {fwd[ci]:+.2f} ({nfwd[:, ci].mean():+.2f}, {fb}/{n_shifts})  [{names[int(np.argmax(z_all[:, ci]))]}]")
        report["columns"].append({
            "strategy": s, "version": v, "rule": rule, "picks": p, "z_gt_2": int(cnt[ci]),
            "null_z_gt_2": ncnt[:, ci].tolist(), "best_z": float(best[ci]), "null_best_z": nbest[:, ci].tolist(),
            "best_test": names[int(np.argmax(z_all[:, ci]))], "forward_mean_z": float(fwd[ci]),
            "null_forward_mean_z": nfwd[:, ci].tolist(),
            "forward_tests": [{"test": names[int(q)], "z_before": float(z_b[q, ci]), "z_after": float(z_a[q, ci]),
                               "hits_after": float(A[q, ci, 2]), "exp_after": float(A[q, ci, 3])} for q in top[:, ci]]})
    # overall: how often does the real forward beat its shifted versions, across all columns?
    beat = np.array([(nfwd[:, ci] < fwd[ci]).mean() for ci in range(len(COLS))])
    print(f"\nAcross all {len(COLS)} columns: forward mean z real {fwd.mean():+.3f} vs shifted {nfwd.mean():+.3f}; "
          f"real forward beats all {n_shifts} shifts in {int((beat == 1).sum())} columns "
          f"(about {len(COLS) / (n_shifts + 1):.0f} expected by chance)")
    best_cols = sorted(range(len(COLS)), key=lambda c: -(fwd[c] - nfwd[:, c].mean()) / max(nfwd[:, c].std(), 1e-9))[:8]
    print("\nColumns whose forward result stands out most from their shifted versions:")
    for c in best_cols:
        s, v, rule, p = COLS[c]
        print(f"   {s} ({v}) {rule} {p}: forward {fwd[c]:+.2f} vs shifted {nfwd[:, c].mean():+.2f} +/- {nfwd[:, c].std():.2f}")
        for q in top[:, c][:3]:
            print(f"      {names[q]:<44} before z {z_b[q, c]:+.2f} -> after {A[q, c, 2]:.0f}/{A[q, c, 3]:.1f} "
                  f"(x{A[q, c, 2] / A[q, c, 3]:.3f}, z {z_a[q, c]:+.2f})")
    report["overall"] = {"forward_real_mean": float(fwd.mean()), "forward_null_mean": float(nfwd.mean()),
                         "columns_beating_all_shifts": int((beat == 1).sum())}
    json.dump(report, open(os.path.join(r.ROOT, "analysis", "recurrence_s12_k_results.json"), "w"), indent=1)
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
