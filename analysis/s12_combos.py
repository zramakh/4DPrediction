#!/usr/bin/env python3
"""S1 (hot) and S2 (cold) positional-digit strategies for single parameters,
pairs and triples, keeping only formulas that beat random in BOTH periods.

Periods (counts for each year from earlier draws only):
  validation 2012-2017, test 2018-01-01 .. the day before the last 5 known draws.
The last 5 draws are held out completely: counts frozen before the first of them.

Triples are built from the 20 parameters that occur most often among the
pairs that are positive in both periods.

Run from the repo root:  python3 analysis/s12_combos.py
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
import strategies_test as st  # noqa: E402

ROOT = st.ROOT
DIG, POW, BITS = st.DIG, st.POW, st.BITS
G = {}


def init():
    codes, rows, draws, keys, dj, oj, yj, Wm, Pm, R16 = st.setup()
    dates = st.all_dates()
    held = dates[-5:]
    cut = dates.index(held[0])
    rn, ro, rd, ry = rows["num"], rows["op_ix"], rows["date"], rows["year"]
    overall = np.stack([np.stack([np.bincount(DIG[rn[ro == o], p], minlength=10) for p in range(4)])
                        for o in range(3)]).astype(float)
    overall /= overall.sum(2, keepdims=True)
    G.update(codes=codes, dj=dj, oj=oj, yj=yj, Wm=Wm, Pm=Pm, rn=rn, ro=ro, rd=rd, ry=ry, cut=cut,
             overall=overall, nwin=(Wm >= 0).sum(1), held=held, dates=dates)


def picks(C, sign):
    top2 = np.argsort(sign * C, axis=2)[:, :, :2]
    return (np.take_along_axis(top2, BITS.T[None, :, :], 2) * POW[None, :, None]).sum(1)   # (n, 16)


def evaluate(fs):
    g = G
    codes, dj, oj, yj, Wm, Pm = g["codes"], g["dj"], g["oj"], g["yj"], g["Wm"], g["Pm"]
    rn, ro, rd, ry, cut, nwin = g["rn"], g["ro"], g["rd"], g["ry"], g["cut"], g["nwin"]
    c = np.zeros(len(codes[fs[0]]), np.int64)
    for f in fs:
        c = c * (int(codes[f].max()) + 1) + codes[f]
    U = int(c.max()) + 1
    rc = (c[rd] * 3 + ro) * 40
    jc = c[dj] * 3 + oj
    cnt = np.zeros(U * 120)

    def add(mask):
        for p in range(4):
            cnt[:] += np.bincount(rc[mask] + p * 10 + DIG[rn[mask], p], minlength=U * 120)

    out = {s: {k: {"validation": [0, 0.0], "test": [0, 0.0], "last5": [0, 0.0, []]} for k in (1, 16)}
           for s in ("S1", "S2")}
    add(ry < 2012)
    for y in range(2012, 2027):
        sel = (yj == y) & (dj < cut)
        if sel.any():
            C = cnt.reshape(U * 3, 4, 10)[jc[sel]] + 1e-6 * g["overall"][oj[sel]]
            per = "validation" if y < 2018 else "test"
            for s, sign in (("S1", -1), ("S2", 1)):
                P = picks(C, sign)
                for k in (1, 16):
                    h, _ = st.score_picks(P[:, :k], Wm[sel], Pm[sel])
                    o = out[s][k][per]
                    o[0] += int(h.sum())
                    o[1] += float((k * nwin[sel] / 10000).sum())
        add((ry == y) & (rd < cut))
    # held-out last 5: counts now hold exactly the draws before the cut
    sel = dj >= cut
    C = cnt.reshape(U * 3, 4, 10)[jc[sel]] + 1e-6 * g["overall"][oj[sel]]
    for s, sign in (("S1", -1), ("S2", 1)):
        P = picks(C, sign)
        for k in (1, 16):
            eq = (P[:, :k, None] == Wm[sel][:, None, :])
            o = out[s][k]["last5"]
            o[0] = int(eq.any(2).sum())
            o[1] = float((eq * Pm[sel][:, None, :]).sum())
            ii = np.flatnonzero(sel)
            o[2] = [f"{g['dates'][dj[ii[i]]][5:]} {st.am.OPS[oj[ii[i]]]} {P[i, a]:04d}" for i, a, _ in zip(*np.nonzero(eq))]
    return fs, out


def stats(o):
    h, e = o
    return (h / e if e else 0.0), ((h - e) / math.sqrt(e) if e else 0.0)


def run(formulas, pool):
    res = {}
    for fs, out in pool.imap_unordered(evaluate, formulas, chunksize=8):
        res[fs] = out
    return res


def summarise(res, label, s, k, top=10):
    rows = []
    for fs, out in res.items():
        o = out[s][k]
        lv, zv = stats(o["validation"])
        lt, zt = stats(o["test"])
        h = o["validation"][0] + o["test"][0]
        e = o["validation"][1] + o["test"][1]
        rows.append((fs, lv, zv, lt, zt, (h - e) / math.sqrt(e), o["last5"]))
    both = [r for r in rows if r[1] > 1 and r[3] > 1]
    strong = [r for r in rows if r[2] > 1 and r[4] > 1]
    best = sorted(both, key=lambda r: -min(r[2], r[4]))[:top]
    l5 = np.array([r[6][0] for r in best]) if best else np.array([])
    print(f"\n{s}, {k} pick(s), {label}: {len(rows)} formulas; above random in both periods {len(both)} "
          f"({len(both) / len(rows):.0%}; ~25% expected by chance); z>1 in both {len(strong)} (~2.5% by chance = {0.025 * len(rows):.0f})")
    for fs, lv, zv, lt, zt, zc, l5r in best:
        print(f"   {' x '.join(fs):<58} valid x{lv:.2f} (z={zv:+.1f}) test x{lt:.2f} (z={zt:+.1f}) | last 5: "
              f"{l5r[0]} hit(s), RM{l5r[1]:.0f}" + (f" {l5r[2]}" if l5r[2] else ""))
    return {"formulas": len(rows), "both_positive": len(both), "both_z_gt_1": len(strong),
            "best": [{"formula": " x ".join(r[0]), "valid_lift": r[1], "valid_z": r[2], "test_lift": r[3],
                      "test_z": r[4], "last5_hits": r[6][0], "last5_big": r[6][1], "last5_detail": r[6][2]}
                     for r in best],
            "best_last5_hits_total": int(l5.sum()) if len(l5) else 0}


def main():
    t0 = time.time()
    init()
    F = st.FACT
    report = {"held_out": G["held"]}
    with mp.get_context("fork").Pool(4) as pool:          # workers inherit the data loaded above
        r1 = run([(f,) for f in F], pool)
        r2 = run(list(itertools.combinations(F, 2)), pool)
        print(f"singles and pairs evaluated ({time.time() - t0:.0f}s)", flush=True)
        # parameters most common among pairs positive in both periods (S1 and S2, 16 picks)
        freq = {}
        for fs, out in r2.items():
            for s in ("S1", "S2"):
                lv, zv = stats(out[s][16]["validation"])
                lt, zt = stats(out[s][16]["test"])
                if lv > 1 and lt > 1:
                    for f in fs:
                        freq[f] = freq.get(f, 0) + min(zv, zt)
        top20 = sorted(freq, key=lambda f: -freq[f])[:20]
        print("parameters used for triples:", ", ".join(top20), flush=True)
        r3 = run(list(itertools.combinations(top20, 3)), pool)
        print(f"triples evaluated ({time.time() - t0:.0f}s)", flush=True)
    report["triple_parameters"] = top20
    random_last5 = {1: 0.034, 16: 0.544}
    for s in ("S1", "S2"):
        for k in (1, 16):
            for label, res in (("single", r1), ("pairs", r2), ("triples", r3)):
                report[f"{s}|{k}|{label}"] = summarise(res, label, s, k)
            print(f"   (random picks on the last 5 draws: mean {random_last5[k]} hits per formula)")
    json.dump(report, open(os.path.join(ROOT, "analysis", "s12_combos_results.json"), "w"), indent=1, default=float)
    print(f"\ndone in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
