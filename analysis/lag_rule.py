#!/usr/bin/env python3
"""Offset ("lag") rule: does the source draw work better a few days away from
the matched day?

For every single parameter (78) and pair (3,003): the source for a draw day is
the previous same-value day moved by k calendar days (k = -7 .. +7, +-14,
+-28, +-30; k = 0 is the usual rule (b)). The source must be an actual draw
date before the target. S1 / S2 picks (16 numbers) scored Straight / Reverse /
i-Box against that year's digit mix, as in recurrence_s12.py.

  lunar date rule  cell = lunar month x lunar day (the same lunar date in an
                   earlier year) with the same offsets
  plain lags       no parameter: source = the draw exactly L days before
                   (L = 1-10, 14, 21, 28-30, 59, 60, 354, 355, 364, 365, 384)

Per offset and column: the 5 tests with the best z before 2012 scored 2012-2026
(walk-forward), and the best z over all years, against 10 shifted calendars.

Run from the repo root:  python3 analysis/lag_rule.py [n_shifts]
"""

import datetime as dt
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

OFFS = list(range(-7, 8)) + [-14, 14, -28, 28, -30, 30]
LAGS = list(range(1, 11)) + [14, 21, 28, 29, 30, 59, 60, 354, 355, 364, 365, 384]
COLS = [(s, rule) for s in ("S1", "S2") for rule in ("straight", "reverse", "ibox")]
SPLIT = 2012


def setup():
    r.setup()
    G = r.G
    G["yr"] = np.array([int(d[:4]) for d in G["D"].dates])
    o = np.array([dt.date.fromisoformat(d).toordinal() for d in G["D"].dates])
    G["ord"] = o
    ix = np.full(o.max() - o.min() + 400, -1)
    ix[o - o.min()] = np.arange(len(o))
    G["ix"], G["o0"] = ix, o.min()


def at(day_ix, k):
    """Draw index k calendar days from day_ix (or -1)."""
    G = r.G
    q = G["ord"][day_ix] + k - G["o0"]
    ok = (q >= 0) & (q < len(G["ix"]))
    out = np.full(len(day_ix), -1)
    out[ok] = G["ix"][q[ok]]
    return out


def score(days, src):
    """(len(COLS), 4): hits / expected before 2012, hits / expected 2012-2026."""
    G = r.G
    ok = (src >= 0) & (src < days)
    days, src = days[ok], src[ok]
    late = G["yr"][days] >= SPLIT
    out = []
    for s, hot in (("S1", True), ("S2", False)):
        res = rk.score_days(days, r.picks(G["dday"][src], hot))
        for rule in ("straight", "reverse", "ibox"):
            h, e = res[rule][0][:, -1].astype(float), res[rule][1][:, -1]
            out.append((h[~late].sum(), e[~late].sum(), h[late].sum(), e[late].sum()))
    return np.array(out)


def evaluate(cells):
    order = np.lexsort((np.arange(len(cells)), cells))
    sc = cells[order]
    hp = np.r_[False, sc[1:] == sc[:-1]]
    days, prev = order[hp], order[:-1][hp[1:]]
    return np.stack([score(days, at(prev, k)) for k in OFFS])          # (offsets, cols, 4)


def task(args):
    test, shift = args
    return evaluate(r.cells_of(test, shift))


def zz(o, e):
    return (o - e) / np.sqrt(np.maximum(e, 1e-9))


def summarize(A):
    zb, za = zz(A[..., 0], A[..., 1]), zz(A[..., 2], A[..., 3])
    zall = zz(A[..., 0] + A[..., 2], A[..., 1] + A[..., 3])
    top = np.argsort(-zb, axis=0)[:5]
    return np.take_along_axis(za, top, 0).mean(0), zall.max(0), top, zb, za      # fwd (offs, cols)


def main():
    n_shifts = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    t0 = time.time()
    setup()
    G = r.G
    out = {"offsets": OFFS, "columns": [f"{s} {rule}" for s, rule in COLS]}
    # plain lags
    print("Plain lags (no parameter): source = the draw exactly L days before; 2012-2026 ratio (z)")
    days = np.arange(G["nd"])
    out["lags"] = {}
    for L in LAGS:
        A = score(days, at(days, -L))
        za = zz(A[:, 2], A[:, 3])
        print(f"   L={L:>3}: " + " | ".join(f"{s} {rule} x{A[c, 2] / A[c, 3]:.3f} ({za[c]:+.2f})" for c, (s, rule) in enumerate(COLS)), flush=True)
        out["lags"][L] = A.tolist()
    # lunar date rule
    lunar = ("lunar_month", "lunar_day")
    A = evaluate(r.cells_of(lunar))
    print("\nLunar date rule (previous same lunar month + day, moved k days): z before | z 2012-2026")
    for i, k in enumerate(OFFS):
        zb, za = zz(A[i, :, 0], A[i, :, 1]), zz(A[i, :, 2], A[i, :, 3])
        print(f"   k={k:+3d}: " + " | ".join(f"{s} {rule} {zb[c]:+.2f}/{za[c]:+.2f}" for c, (s, rule) in enumerate(COLS)))
    out["lunar_date"] = A.tolist()
    # all tests
    tests = [(f,) for f in r.FACT] + list(itertools.combinations(r.FACT, 2))
    names = [" x ".join(t) for t in tests]
    with mp.get_context("fork").Pool(4) as pool:
        R = np.array(pool.map(task, [(t, 0) for t in tests], chunksize=16))        # (tests, offs, cols, 4)
        print(f"\n{len(tests)} tests ({time.time() - t0:.0f}s)", flush=True)
        rng = np.random.default_rng(17)
        NF, NB = [], []
        for j in range(n_shifts):
            sh = int(rng.integers(170, G["nd"] - 170))
            B = np.array(pool.map(task, [(t, sh) for t in tests], chunksize=16))
            f, b, *_ = summarize(B)
            NF.append(f), NB.append(b)
            print(f"shift {j + 1}/{n_shifts} ({time.time() - t0:.0f}s)", flush=True)
    NF, NB = np.array(NF), np.array(NB)
    fwd, best, top, zb, za = summarize(R)
    zall = zz(R[..., 0] + R[..., 2], R[..., 1] + R[..., 3])
    print("\nWalk-forward: mean z 2012-2026 of the 5 tests best before 2012 (shifted calendars mean; shifts as high)")
    print("   k     " + " | ".join(f"{s} {rule:<8}" for s, rule in COLS))
    for i, k in enumerate(OFFS):
        print(f"   {k:+3d}  " + " | ".join(f"{fwd[i, c]:+.2f} ({NF[:, i, c].mean():+.2f};{int((NF[:, i, c] >= fwd[i, c]).sum())})" for c in range(len(COLS))))
    print("\nBest z all years (shifted best mean; shifts as high)")
    for i, k in enumerate(OFFS):
        print(f"   {k:+3d}  " + " | ".join(f"{best[i, c]:+.2f} ({NB[:, i, c].mean():+.2f};{int((NB[:, i, c] >= best[i, c]).sum())})" for c in range(len(COLS))))
    print("\nForward picks per offset (S1 i-Box column):")
    c = COLS.index(("S1", "ibox"))
    out["forward"] = {}
    for i, k in enumerate(OFFS):
        rows = [(names[q], float(zb[q, i, c]), float(za[q, i, c])) for q in top[:, i, c]]
        out["forward"][k] = {"mean_z_after": fwd[i].tolist(), "null": NF[:, i].tolist(), "best_all": best[i].tolist(),
                             "null_best": NB[:, i].tolist(),
                             "top_by_column": {f"{s} {rule}": [(names[q], float(zb[q, i, cc]), float(za[q, i, cc]))
                                                               for q in top[:, i, cc]] for cc, (s, rule) in enumerate(COLS)}}
        print(f"   {k:+3d}: " + "; ".join(f"{n} {b:+.2f}->{a:+.2f}" for n, b, a in rows[:3]))
    # leads: tests positive before and after at the same offset, best combined
    print("\nStrongest single tests at an offset other than 0 (z before > 2 and z after > 2):")
    hits = [(zall[q, i, cc], names[q], OFFS[i], COLS[cc], zb[q, i, cc], za[q, i, cc])
            for q, i, cc in zip(*np.nonzero((zb > 2) & (za > 2))) if OFFS[i] != 0]
    hits.sort(reverse=True)
    n0 = int(((zb > 2) & (za > 2))[:, OFFS.index(0)].sum())
    print(f"   count per offset: " + ", ".join(f"{k:+d}:{int(((zb > 2) & (za > 2))[:, i].sum())}" for i, k in enumerate(OFFS)))
    for z, n, k, (s, rule), b, a in hits[:12]:
        print(f"   k={k:+3d} {n:<42} {s} {rule:<8} before {b:+.2f} after {a:+.2f}")
    out["both_gt2"] = [{"test": n, "k": k, "col": f"{s} {rule}", "z_before": float(b), "z_after": float(a)}
                       for z, n, k, (s, rule), b, a in hits[:50]]
    json.dump(out, open(os.path.join(r.ROOT, "analysis", "lag_rule_results.json"), "w"), indent=1, default=float)
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
