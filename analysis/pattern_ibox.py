#!/usr/bin/env python3
"""Do some leads favour one i-Box number pattern?

i-Box patterns of a pick: ABCD (24 arrangements), AABC (12), AABB (6), AAAB (4),
AAAA (1). For every single parameter and pair, the digit-position picks of
analysis C (S1, S2, rank pairs 1+10 .. 5+6; (a) all / (b) previous same-value
day) are scored as i-Box per pick (each pick a separate bet), split by the
pick's pattern, before 2012 and 2012-2026. Chance per pick = winners x the
probability of a number in its box under that year's digit mix.
Per pattern:
  forward   the 5 tests with the best z before 2012 in each picks column, z on 2012-2026
  overall   average z on 2012-2026 over all tests (does the pattern beat chance in general?)
both against the same on circularly shifted parameter calendars.

Run from the repo root:  python3 analysis/pattern_ibox.py pooled|Magnum|"Sports Toto"|"Da Ma Cai" [n_shifts]
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
import per_operator as po  # noqa: E402

PATTERNS = [24, 12, 6, 4, 1]
PNAME = {24: "ABCD", 12: "AABC", 6: "AABB", 4: "AAAB", 1: "AAAA"}
PICKERS = ["S1", "S2", (0, 9), (1, 8), (2, 7), (3, 6), (4, 5)]
COLS = [(p, v, k) for p in PICKERS for v in "ab" for k in PATTERNS]
SPLIT = 2012
M = {}


def pname(p):
    return p if isinstance(p, str) else f"{p[0] + 1}+{p[1] + 1}"


def setup():
    import recurrence_rankpairs as rp
    import recurrence_s12 as r
    r.setup()
    G = r.G
    G["yr"] = np.array([int(d[:4]) for d in G["D"].dates])
    D = G["D"]
    perms = np.array([math.factorial(4) // math.prod(math.factorial(f"{n:04d}".count(c)) for c in set(f"{n:04d}"))
                      for n in range(10000)])
    M.update(r=r, rp=rp, perms=perms)


def evaluate(cells):
    r, rp = M["r"], M["rp"]
    G = r.G
    dday = G["dday"]
    order = np.lexsort((np.arange(len(cells)), cells))
    sc = cells[order]
    newgrp = np.r_[True, sc[1:] != sc[:-1]]
    hp = ~newgrp
    days = order[hp]
    late = G["yr"][days] >= SPLIT
    cs = np.cumsum(dday[order], axis=0)
    st = np.maximum.accumulate(np.where(newgrp, np.arange(len(sc)), 0))
    base = np.where((st > 0)[:, None, None], cs[np.maximum(st - 1, 0)], 0)
    src = {"a": (cs - dday[order] - base)[hp], "b": dday[order[:-1]][hp[1:]]}
    y = G["yix"][days][:, None]
    nw = G["nwin"][days][:, None]
    res = {}
    for p in PICKERS:
        for v in "ab":
            if p == "S1":
                P = r.picks(src[v], True)
            elif p == "S2":
                P = r.picks(src[v], False)
            else:
                P = rp.pair_picks(np.argsort(-src[v], axis=2, kind="stable"), p)
            B = G["box"][P]
            h = G["Cb"][days[:, None], B]                                  # i-Box matches per pick
            e = nw * G["Pbox"][y, B]
            k = M["perms"][P]
            for pat in PATTERNS:
                m = k == pat
                hb, eb = (h * m)[~late].sum(), (e * m)[~late].sum()
                ha, ea = (h * m)[late].sum(), (e * m)[late].sum()
                res[(p, v, pat)] = (hb, eb, ha, ea)
    return np.array([res[c] for c in COLS], float)


def task(args):
    test, shift = args
    return evaluate(M["r"].cells_of(test, shift))


def zz(o, e):
    return np.where(e > 0, (o - e) / np.sqrt(np.maximum(e, 1e-9)), 0.0)


def stats(A):
    zb, za = zz(A[:, :, 0], A[:, :, 1]), zz(A[:, :, 2], A[:, :, 3])
    top = np.argsort(-zb, axis=0)[:5]
    fwd = np.take_along_axis(za, top, 0).mean(0)
    return zb, za, top, fwd, za.mean(0)


def main():
    which = sys.argv[1]
    n_shifts = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    if which != "pooled":
        po.restrict_to(am.OPS.index(which))
    t0 = time.time()
    setup()
    r = M["r"]
    tests = [(f,) for f in r.FACT] + list(itertools.combinations(r.FACT, 2))
    names = [" x ".join(t) for t in tests]
    rng = np.random.default_rng(83)
    shifts = [int(s) for s in rng.integers(170, r.G["nd"] - 170, n_shifts)]
    with mp.get_context("fork").Pool(4) as pool:
        A = np.array(pool.map(task, [(t, 0) for t in tests], chunksize=16))
        print(f"{which}: {len(tests)} tests ({time.time() - t0:.0f}s)", flush=True)
        null = [stats(np.array(pool.map(task, [(t, s) for t in tests], chunksize=16))) for s in shifts]
    zb, za, top, fwd, allz = stats(A)
    nf = np.array([x[3] for x in null])
    na = np.array([x[4] for x in null])
    out = {"which": which, "patterns": {}}
    print(f"\n=== {which}: i-Box by pick pattern (z on 2012-2026; 0 = chance) ===")
    print("pattern | share of picks | no-parameter ratio after | overall mean z real (shifted) | forward mean z real (shifted) | columns beating every shift")
    for pat in PATTERNS:
        idx = [ci for ci, c in enumerate(COLS) if c[2] == pat]
        share = A[:, idx, 3].sum() / A[:, :, 3].sum()
        beat = sum(1 for ci in idx if (nf[:, ci] < fwd[ci]).all())
        print(f"{PNAME[pat]} ({pat}) | {100 * share:.1f}% of expected matches | | {allz[idx].mean():+.3f} ({na[:, idx].mean():+.3f}) | "
              f"{fwd[idx].mean():+.3f} ({nf[:, idx].mean():+.3f}) | {beat} of {len(idx)} (~{len(idx) / (n_shifts + 1):.1f} by chance)")
        cols = []
        for ci in idx:
            p, v, _ = COLS[ci]
            q = top[0, ci]
            cols.append({"picks": pname(p), "version": v, "forward": float(fwd[ci]), "null_forward": nf[:, ci].tolist(),
                         "overall": float(allz[ci]), "null_overall": na[:, ci].tolist(),
                         "top_tests": [{"test": names[t], "z_before": float(zb[t, ci]), "hits_after": float(A[t, ci, 2]),
                                        "exp_after": float(A[t, ci, 3]), "z_after": float(za[t, ci])} for t in top[:, ci]]})
        out["patterns"][PNAME[pat]] = cols
    print("\nBest forward picks per pattern (chosen before 2012, scored 2012-2026):")
    for pat in PATTERNS:
        best = []
        for ci, c in enumerate(COLS):
            if c[2] != pat:
                continue
            for t in top[:, ci]:
                best.append((za[t, ci], names[t], c, zb[t, ci], A[t, ci, 2], A[t, ci, 3]))
        best.sort(key=lambda x: -x[0])
        print(f"  {PNAME[pat]}:")
        for z, n, c, b, h, e in best[:3]:
            print(f"     {n:<42} {pname(c[0])} ({c[1]}) | before z {b:+.2f} | after {h:.0f}/{e:.1f} (x{h / e if e else 0:.3f}, z {z:+.2f})")
    tag = which.lower().replace(" ", "")
    json.dump(out, open(os.path.join(am.ROOT, "analysis", f"pattern_ibox_{tag}.json"), "w"), indent=1)
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
