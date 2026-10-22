#!/usr/bin/env python3
"""Recurrence test for the S1 (hot) / S2 (cold) positional-digit picks, for all
78 single parameters and 3,003 pairs, scored as Straight, Reverse and i-Box.

For a draw day whose parameter value (or pair of values) occurred before:
  (a) source = ALL earlier draw days with the same value
  (b) source = only the PREVIOUS draw day with the same value
Count each digit in each position over the source days' winners (any prize,
any operator, each number once per date); S1 = the 2 most frequent digits per
position, S2 = the 2 least frequent (ties -> lower digit), 2^4 = 16 numbers.
Hits on the later day:
  Straight  a winner equals one of the 16
  Reverse   a winner's reversed digits equal one of the 16 (palindromes excluded)
  i-Box     a winner is any arrangement of one of the 16
Chance level for each day = winners that day x probability a random number
hits, using that year's digit mix per position (so a parameter must beat the
plain year-level digit bias, not just uniform chance).
The whole scan is repeated on circularly shifted parameter calendars (one
shift for all parameters, at least about a year of draw days) to get the best
z and number of z > 2 that the scan reaches by chance.

Run from the repo root:  python3 analysis/recurrence_s12.py [n_shifts]
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
import astro_model as am  # noqa: E402
import digit_models as dm  # noqa: E402

ROOT = am.ROOT
FACT = am.VEDIC + am.CHINESE
DIG = am.DIG
POW = np.array([1000, 100, 10, 1])
BITS = np.array([[(k >> (3 - p)) & 1 for p in range(4)] for k in range(16)])     # (16, 4)
RULES = ("straight", "reverse", "ibox")
COLS = [f"{s}_{v}_{r}" for s in ("S1", "S2") for v in "ab" for r in RULES]
G = {}


def norm_sf(z):
    return 0.5 * math.erfc(z / math.sqrt(2))


def setup():
    D = dm.Data()
    nd = len(D.dates)
    key = np.unique(D.rd.astype(np.int64) * 10000 + D.rn)
    wd, wn = key // 10000, key % 10000
    nwin = np.bincount(wd, minlength=nd).astype(float)
    W = np.zeros((nd, 10000), bool)
    W[wd, wn] = True
    dday = np.zeros((nd, 4, 10))
    for p in range(4):
        np.add.at(dday, (wd, p, DIG[wn, p]), 1)
    num = np.arange(10000)
    rev = (DIG[:, ::-1] * POW).sum(1)
    box = np.unique(np.sort(DIG, axis=1) @ POW, return_inverse=True)[1]
    nbox = int(box.max()) + 1
    Cb = np.zeros((nd, nbox), np.float32)
    np.add.at(Cb, (wd, box[wn]), 1)
    yr = np.array([int(d[:4]) for d in D.dates])
    yix = yr - yr.min()
    q = np.zeros((yix.max() + 1, 4, 10))
    np.add.at(q, yix, dday)
    with np.errstate(invalid="ignore"):
        q /= q.sum(2, keepdims=True)
    q = np.nan_to_num(q, nan=0.1)                                         # years with no draws (operator not yet running)
    Py = q[:, 0, DIG[:, 0]] * q[:, 1, DIG[:, 1]] * q[:, 2, DIG[:, 2]] * q[:, 3, DIG[:, 3]]     # (years, 10000)
    Pbox = np.stack([np.bincount(box, weights=Py[y], minlength=nbox) for y in range(len(Py))])
    G.update(D=D, nd=nd, nwin=nwin, W=W, dday=dday, rev=rev, pal=rev == num, box=box, Cb=Cb, yix=yix, Py=Py, Pbox=Pbox)


def cells_of(test, shift=0):
    D = G["D"]
    c = np.zeros(G["nd"], np.int64)
    for f in test:
        c = c * (int(D.codes[f].max()) + 1) + D.codes[f]
    return np.roll(c, shift) if shift else c


def picks(C, hot):
    """(n, 4, 10) digit counts -> (n, 16) numbers."""
    top2 = np.argsort(-C if hot else C, axis=2, kind="stable")[:, :, :2]
    dig = np.take_along_axis(top2, BITS.T[None, :, :], 2)                   # (n, 4, 16)
    return (dig * POW[None, :, None]).sum(1)


def score(days, P):
    """obs / exp per rule for picks P (n, 16) on the given days."""
    W, rev, pal, box, Cb, Py, Pbox, nwin = (G[k] for k in ("W", "rev", "pal", "box", "Cb", "Py", "Pbox", "nwin"))
    y = G["yix"][days]
    out = {}
    out["straight"] = (float(W[days[:, None], P].sum()), float((nwin[days] * Py[y[:, None], P].sum(1)).sum()))
    R = rev[P]
    ok = ~pal[P]
    out["reverse"] = (float((W[days[:, None], R] & ok).sum()), float((nwin[days] * (Py[y[:, None], R] * ok).sum(1)).sum()))
    B = np.sort(box[P], axis=1)
    first = np.ones_like(B, bool)
    first[:, 1:] = B[:, 1:] != B[:, :-1]
    out["ibox"] = (float((Cb[days[:, None], B] * first).sum()), float((nwin[days] * (Pbox[y[:, None], B] * first).sum(1)).sum()))
    return out


def evaluate(cells):
    dday = G["dday"]
    order = np.lexsort((np.arange(len(cells)), cells))
    sc = cells[order]
    newgrp = np.r_[True, sc[1:] != sc[:-1]]
    has_prev = ~newgrp
    days = order[has_prev]
    # (a) all earlier same-value days: exclusive cumulative sum within each group
    cs = np.cumsum(dday[order], axis=0)
    start = np.maximum.accumulate(np.where(newgrp, np.arange(len(sc)), 0))
    base = np.where((start > 0)[:, None, None], cs[np.maximum(start - 1, 0)], 0)
    excl = cs - dday[order] - base
    Ca = excl[has_prev]
    # (b) previous same-value day only
    Cbsrc = dday[order[:-1]][has_prev[1:]]
    res = {}
    for s, hot in (("S1", True), ("S2", False)):
        for v, C in (("a", Ca), ("b", Cbsrc)):
            for r, oe in score(days, picks(C, hot)).items():
                res[f"{s}_{v}_{r}"] = oe
    return res


def task(args):
    test, shift = args
    return evaluate(cells_of(test, shift))


def z_of(r):
    return [(r[c][0] - r[c][1]) / math.sqrt(r[c][1]) for c in COLS]


def main():
    n_shifts = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    t0 = time.time()
    setup()
    tests = [(f,) for f in FACT] + list(itertools.combinations(FACT, 2))
    n = len(tests)
    # reference: no parameter (one cell) -> (a) all earlier days, (b) the previous draw day
    ref = evaluate(np.zeros(G["nd"], np.int64))
    print("No parameter (reference): " + "; ".join(f"{c} x{ref[c][0] / ref[c][1]:.3f}" for c in COLS), flush=True)
    with mp.get_context("fork").Pool(4) as pool:
        real = pool.map(task, [(t, 0) for t in tests], chunksize=16)
        print(f"{n} tests evaluated ({time.time() - t0:.0f}s)", flush=True)
        Z = np.array([z_of(r) for r in real])
        rng = np.random.default_rng(3)
        null = []
        for k in range(n_shifts):
            sh = int(rng.integers(170, G["nd"] - 170))
            Zs = np.array([z_of(r) for r in pool.map(task, [(t, sh) for t in tests], chunksize=16)])
            null.append({"shift": sh, "max_z": Zs.max(0).tolist(), "z_gt_2": (Zs > 2).sum(0).tolist()})
            print(f"shift {k + 1}/{n_shifts} done ({time.time() - t0:.0f}s)", flush=True)
    names = [" x ".join(t) for t in tests]
    report = {"tests": n, "n_shifts": n_shifts, "reference_no_parameter": ref, "null": null, "by_column": {}}
    print("\ncolumn                    z>2 real | shifted mean (range)   best z real | shifted mean (range) | shifts as high")
    for ci, col in enumerate(COLS):
        nm = np.array([x["max_z"][ci] for x in null])
        ng = np.array([x["z_gt_2"][ci] for x in null])
        q = int(np.argmax(Z[:, ci]))
        print(f"{col:<24} {int((Z[:, ci] > 2).sum()):>5} | {ng.mean():>5.0f} ({ng.min()}-{ng.max()})      "
              f"{Z[q, ci]:+.2f} | {nm.mean():+.2f} ({nm.min():+.2f} to {nm.max():+.2f}) | {int((nm >= Z[q, ci]).sum())}/{len(nm)}")
        top = np.argsort(-Z[:, ci])[:5]
        rows = []
        for t in top:
            o, e = real[t][col]
            rows.append({"test": names[t], "hits": o, "expected": e, "ratio": o / e, "z": float(Z[t, ci]),
                         "p_bonf": min(1.0, n * norm_sf(Z[t, ci])), "shift_scans_as_high": int((nm >= Z[t, ci]).sum())})
        report["by_column"][col] = {"z_gt_2": int((Z[:, ci] > 2).sum()), "null_z_gt_2": ng.tolist(),
                                    "null_max_z": nm.tolist(), "top": rows}
    print("\nTop 3 per column:")
    for col in COLS:
        print(f"  {col}")
        for x in report["by_column"][col]["top"][:3]:
            print(f"     {x['test']:<44} {x['hits']:>6.0f} hits vs {x['expected']:>8.1f} (x{x['ratio']:.3f}, z={x['z']:+.2f}, "
                  f"corrected p={x['p_bonf']:.2f}, shifted scans' best >= this {x['shift_scans_as_high']}/{n_shifts})")
    json.dump(report, open(os.path.join(ROOT, "analysis", "recurrence_s12_results.json"), "w"), indent=1)
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
