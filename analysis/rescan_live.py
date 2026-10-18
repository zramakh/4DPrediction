#!/usr/bin/env python3
"""Re-run the full S1/S2 recurrence scan (78 single parameters + 3,003 pairs;
S1 hot / S2 cold; (a) all earlier / (b) previous same-value day; Straight /
Reverse / i-Box, as in recurrence_s12.py) using only results BEFORE a draw date,
take the top 5 tests per column, build their 16 picks for that date from
earlier results, and score them on that date's winners (all 3 operators).

Also scored: S1 / S2 with no parameter (all earlier days = plain hot / cold
positional digits) and the previous draw day only.

Run from the repo root:  python3 analysis/rescan_live.py 2026-10-17 2026-10-18
"""

import itertools
import json
import math
import multiprocessing as mp
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am  # noqa: E402
import recurrence_s12 as r  # noqa: E402

ORIG = r.score
TOP = 5


def task(args):
    test, cut = args
    yr_ok = r.G["before"]

    def sc(days, P):
        m = yr_ok[days]
        return ORIG(days[m], P[m])
    r.score = sc
    res = r.evaluate(r.cells_of(test))
    return [(res[c][0] - res[c][1]) / math.sqrt(res[c][1]) if res[c][1] > 0 else 0.0 for c in r.COLS]


def picks_on(t, test, strategy, version):
    """16 picks for draw-day index t from earlier days with the same values."""
    G = r.G
    cells = r.cells_of(test) if test else np.zeros(G["nd"], np.int64)
    earlier = np.flatnonzero((cells == cells[t]) & (np.arange(G["nd"]) < t))
    if len(earlier) == 0:
        return None
    src = earlier if version == "a" else earlier[-1:]
    C = G["dday"][src].sum(0, keepdims=True)
    return r.picks(C, strategy == "S1")


def hits(t, P):
    """Straight / reverse / i-Box hits and chance expectations on day t."""
    o = r.score(np.array([t]), P)
    return {k: (int(v[0]), float(v[1])) for k, v in o.items()}


def main():
    dates = sys.argv[1:]
    r.setup()
    G = r.G
    D = G["D"]
    tests = [(f,) for f in r.FACT] + list(itertools.combinations(r.FACT, 2))
    report = {}
    for date in dates:
        t = D.dates.index(date)
        G["before"] = np.arange(G["nd"]) < t
        r.score = ORIG
        with mp.get_context("fork").Pool(4) as pool:
            Z = np.array(pool.map(task, [(x, date) for x in tests], chunksize=16))
        r.score = ORIG
        print(f"\n=== {date}: scan on results before {date}; top {TOP} tests per column, their picks scored on {date} ===")
        tot = {k: [0, 0.0] for k in r.RULES}
        rows = []
        for ci, col in enumerate(r.COLS):
            s, v, rule = col.split("_")
            top = np.argsort(-Z[:, ci])[:TOP]
            line = []
            for q in top:
                P = picks_on(t, tests[q], s, v)
                if P is None:
                    continue
                h = hits(t, P)[rule]
                tot[rule][0] += h[0]
                tot[rule][1] += h[1]
                line.append(f"{' x '.join(tests[q])} (z {Z[q, ci]:+.2f}): {h[0]}")
                rows.append({"column": col, "test": " x ".join(tests[q]), "z_before": float(Z[q, ci]),
                             "picks": [int(x) for x in P[0]], "hits": h[0], "expected": h[1]})
            print(f"  {col:<16} " + "; ".join(line))
        print("  Total over all columns' top-5 picks (each scored with its own column's rule):")
        for k, (o, e) in tot.items():
            print(f"     {k:<9} {o} hits vs {e:.1f} expected by chance (x{o / e if e else 0:.2f})")
        print("  Reference, no parameter:")
        ref = {}
        for name, s, v in (("S1 hot, all earlier days", "S1", "a"), ("S2 cold, all earlier days", "S2", "a"),
                           ("S1 hot, previous draw day", "S1", "b"), ("S2 cold, previous draw day", "S2", "b")):
            P = picks_on(t, None, s, v)
            h = hits(t, P)
            ref[name] = {"picks": [int(x) for x in P[0]], **{k: list(x) for k, x in h.items()}}
            print(f"     {name:<28} " + ", ".join(f"{k} {o} (exp {e:.2f})" for k, (o, e) in h.items()))
        top1 = {}
        for ci, col in enumerate(r.COLS):
            q = int(np.argmax(Z[:, ci]))
            top1[col] = " x ".join(tests[q])
        report[date] = {"top_tests": rows, "totals": tot, "reference": ref, "top1": top1}
    json.dump(report, open(os.path.join(am.ROOT, "analysis", "rescan_live_results.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
