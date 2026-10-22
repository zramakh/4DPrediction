#!/usr/bin/env python3
"""Leads from Mei Hua Yi Shu and Da Liu Ren (chinese_divination.py) and their
performance on recent draws.

For every test containing a Mei Hua (mh_) or Da Liu Ren (lr_) parameter, alone
or paired with any other parameter, the digit-position picks of analysis C
(S1, S2, rank pairs; (a) all / (b) previous same-value day; Straight /
Reverse / i-Box) are scored before 2012 and 2012-2026. In each of the 42
columns the test with the best z before 2012 is that column's pick; the 3
picks per family with the best 2012-2026 result are listed as its leads (that
last ranking uses 2012-2026, so it flatters them). Their picks are then
rebuilt for each given draw from earlier results only and scored as Straight
and i-Box.

Run from the repo root:  python3 analysis/mh_lr_leads.py 2026-10-17 2026-10-18 2026-10-21
"""

import itertools
import math
import multiprocessing as mp
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chinese_divination as cd  # noqa: E402
import navamsa_family as nf  # noqa: E402
import score_leads as sc  # noqa: E402
import score_live as sl  # noqa: E402


def task(test):
    return nf.eval_C(nf.cells(nf.r.G["D"], test))


def main():
    dates = sys.argv[1:]
    nf.r.setup()
    G = nf.r.G
    G["yr"] = np.array([int(d[:4]) for d in G["D"].dates])
    D = G["D"]
    codes, labels, _ = cd.compute(D.dates)
    nf.inject(D, codes, labels)
    new = list(codes)
    out = {}
    for fam, pre in (("Mei Hua Yi Shu", "mh_"), ("Da Liu Ren", "lr_")):
        mine = [f for f in new if f.startswith(pre)]
        tests = [(f,) for f in mine] + list(itertools.combinations(mine, 2)) + \
                [(a, b) for a in mine for b in nf.r.FACT]
        with mp.get_context("fork").Pool(4) as pool:
            A = np.array(pool.map(task, tests, chunksize=8))
        zb, za, zall, top, fwd = nf.fwd_stats(A)
        best = np.argmax(zb, axis=0)
        picks = []
        for ci, (p, v, rule) in enumerate(nf.C_COLS):
            q = int(best[ci])
            picks.append((float(za[q, ci]), tests[q], p, v, rule, float(zb[q, ci]), A[q, ci]))
        picks.sort(key=lambda x: -x[0])
        out[fam] = picks[:3]
        print(f"\n{fam}: {len(tests)} tests; per-column best-before-2012 picks, mean z after 2012 {np.mean([x[0] for x in picks]):+.2f}")
    rows, _ = sl.load()
    for fam, leads in out.items():
        print(f"\n===== {fam} leads =====")
        tot = []
        for k, (z_after, test, p, v, rule, z_before, a) in enumerate(leads, 1):
            name = f"{' x '.join(test)}, {nf.pname(p)} ({v}), {rule}"
            print(f"{k}. {name}: before 2012 z {z_before:+.2f}; 2012-2026 {a[2]:.0f} hits vs {a[3]:.1f} (x{a[2] / a[3]:.3f}, z {z_after:+.2f})")
            kind = p
            T = [0, 0, 0, 0.0, 0]
            for d in dates:
                t = D.dates.index(d)
                win = {op: {x["4d_number"]: x["prize"] for x in rows[op] if x["date"] == d} for op in sl.OPS}
                pk = sc.picks(t, test, kind, v)
                if pk is None:
                    print(f"     {d}: no earlier same-value day")
                    continue
                s, sp, b, bp = sc.score({op: pk for op in sl.OPS}, win)
                T[0] += len(s); T[1] += sp; T[2] += len(b); T[3] += bp; T[4] += 48
                print(f"     {d}: {' '.join(pk)}")
                print(f"        straight {len(s)} {'; '.join(s) or '-'} RM{sp} | i-Box {len(b)} {'; '.join(b) or '-'} ~RM{bp:.2f}")
            print(f"     total: staked RM{T[4]}, straight {T[0]} hits RM{T[1]}, i-Box {T[2]} matches ~RM{T[3]:.2f}")


if __name__ == "__main__":
    main()
