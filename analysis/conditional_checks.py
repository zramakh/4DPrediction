#!/usr/bin/env python3
"""Follow-up checks for conditional_extended.py.

1. Replication baseline. "Learn a cell's top numbers before 2012, test them in
   the same cell afterwards" can beat random just because some numbers or
   i-Box groups are a little more common overall (e.g. the Magnum digit
   bias), whatever the condition. The same test is therefore repeated with
   the draw dates shuffled (same machinery, meaningless conditions). Only a
   lift above the shuffled one would point to a real condition effect.
2. The 200 strongest associations found before 2012, in full, with how much
   of their later success comes from a few numbers that are common overall.

Run from the repo root:  python3 analysis/conditional_checks.py   (~10 min on 4 cores)
"""

import itertools
import json
import math
import multiprocessing as mp
import os
import sys
import time
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import conditional_extended as ce  # noqa: E402
import conditional_numbers as cn  # noqa: E402

N_NULL = 3
G = {}


def task(args):
    scope, fsets = args
    data, codes, labels, perms = G["data"], G["codes"], G["labels"], G["perms"]
    sel = data["op"] == scope if scope != "All operators" else np.ones(len(data["num"]), bool)
    num, years = data["num"][sel], data["year"][sel]
    out = {"rep": [], "found": {u: [] for u in cn.UNITS}}
    for fset in fsets:
        cell, sizes = cn.cell_codes(sel, data["date"], codes, data["prize"], fset)
        null_cells = [cn.cell_codes(sel, p[data["date"]], codes, data["prize"], fset)[0] for p in perms]
        for u, (n_units, share, fmt) in cn.UNITS.items():
            ux = num if u == "number" else cn.GROUP_OF[num]
            k1 = cn.once_per_draw(data["date"][sel], ux, n_units)
            ux, uc, uy = ux[k1], cell[k1], years[k1]
            tr, te = uy < cn.SPLIT_YEAR, uy >= cn.SPLIT_YEAR
            real = cn.replicate(uc, ux, n_units, share, tr, te)
            null = [cn.replicate(nc[k1], ux, n_units, share, tr, te) for nc in null_cells]
            if real and all(null):
                out["rep"].append((scope, u, " x ".join(fset), real["hits"], real["expected"],
                                   [x["hits"] for x in null], [x["expected"] for x in null]))
            if "era_5yr" in fset:
                continue
            _, dc, du, dcnt, dexp, _ = cn.scan(uc[tr], ux[tr], n_units, share)
            n_te = np.bincount(uc[te], minlength=uc.max() + 1)
            ok = n_te[dc] > 0
            dc, du, dcnt, dexp = dc[ok], du[ok], dcnt[ok], dexp[ok]
            p = cn.poisson_sf(dcnt, dexp)
            tk, tcount = np.unique(uc[te] * n_units + ux[te], return_counts=True)
            for i in np.argsort(p)[:5]:
                key = dc[i] * n_units + du[i]
                pos = min(np.searchsorted(tk, key), len(tk) - 1)
                out["found"][u].append((float(p[i]), scope, " x ".join(fset),
                                        cn.decode(int(dc[i]), list(fset), sizes, labels), fmt(int(du[i])),
                                        int(dcnt[i]), float(dexp[i]), int(tcount[pos]) if tk[pos] == key else 0,
                                        float(n_te[dc[i]] * share[du[i]])))
    return out


def main():
    t0 = time.time()
    data, codes, labels, factors, n_dates = ce.load()
    G.update(data=data, codes=codes, labels=labels,
             perms=cn.stratified_perms(data, n_dates, N_NULL, np.random.default_rng(99)))
    fsets = [(f,) for f in factors] + list(itertools.combinations(factors, 2))
    scopes = list(cn.OPERATORS) + ["All operators"]
    chunks = [(s, fsets[i:i + 40]) for s in scopes for i in range(0, len(fsets), 40)]
    rep, found = [], {u: [] for u in cn.UNITS}
    with mp.Pool() as pool:
        for k, out in enumerate(pool.imap_unordered(task, chunks), 1):
            rep += out["rep"]
            for u in cn.UNITS:
                found[u] += out["found"][u]
            if k % 40 == 0:
                print(f"  {k}/{len(chunks)} chunks ({time.time() - t0:.0f}s)", flush=True)

    res = {"replication_vs_shuffled": {}, "discoveries": {}}
    print("\nReplication (learn before 2012, test from 2012): real conditions vs shuffled conditions")
    for scope in scopes:
        for u in cn.UNITS:
            rows = [r for r in rep if r[0] == scope and r[1] == u]
            h, e = sum(r[3] for r in rows), sum(r[4] for r in rows)
            nh = sum(sum(r[5]) for r in rows) / N_NULL
            ne = sum(sum(r[6]) for r in rows) / N_NULL
            # per-set z against the shuffled versions of the same set
            z = [(r[3] - r[4]) / math.sqrt(r[4]) for r in rows]
            zn = [(r[5][0] - r[6][0]) / math.sqrt(r[6][0]) for r in rows]
            res["replication_vs_shuffled"][f"{scope} | {u}"] = {
                "sets": len(rows), "lift_real": round(h / e, 4), "lift_shuffled": round(nh / ne, 4),
                "sets_z_gt_3_real": sum(x > 3 for x in z), "sets_z_gt_3_shuffled": sum(x > 3 for x in zn)}
            v = res["replication_vs_shuffled"][f"{scope} | {u}"]
            print(f"  {scope:<13} {u:<10} lift real {v['lift_real']:.3f} vs shuffled {v['lift_shuffled']:.3f}; "
                  f"sets z>3: {v['sets_z_gt_3_real']} real vs {v['sets_z_gt_3_shuffled']} shuffled (of {len(rows)})")

    print("\nTop 200 associations found before 2012: results from 2012 on")
    for u in cn.UNITS:
        f = sorted(found[u])[:200]
        h, e = sum(x[7] for x in f), sum(x[8] for x in f)
        by_value = Counter()
        exp_value = Counter()
        for x in f:
            by_value[x[4]] += x[7]
            exp_value[x[4]] += x[8]
        top = sorted(by_value, key=lambda v: by_value[v] - exp_value[v], reverse=True)[:5]
        n_values = len({x[4] for x in f})
        res["discoveries"][u] = {
            "wins_from_2012": h, "expected": round(e, 1), "lift": round(h / e, 3), "z": round((h - e) / math.sqrt(e), 2),
            "distinct_values": n_values,
            "largest_contributors": [{"value": v, "entries": sum(x[4] == v for x in f), "wins_from_2012": by_value[v],
                                      "expected": round(exp_value[v], 2)} for v in top],
            "list": [{"scope": x[1], "cell": x[3], "value": x[4], "wins_before_2012": x[5],
                      "expected_before": round(x[6], 3), "wins_from_2012": x[7],
                      "expected_from_2012": round(x[8], 3)} for x in f]}
        d = res["discoveries"][u]
        print(f"  {u}: {h} wins vs {e:.1f} expected (z={d['z']:+.2f}); {n_values} distinct values; "
              f"largest contributors {[(c['value'], c['entries'], c['wins_from_2012'], c['expected']) for c in d['largest_contributors']]}")
        rest = [x for x in f if x[4] not in top[:1]]
        h2, e2 = sum(x[7] for x in rest), sum(x[8] for x in rest)
        print(f"    without {top[0]}: {h2} vs {e2:.1f} (z={(h2 - e2) / math.sqrt(e2):+.2f})")
        d["without_top_contributor"] = {"value": top[0], "wins_from_2012": h2, "expected": round(e2, 1),
                                        "z": round((h2 - e2) / math.sqrt(e2), 2)}
    with open(os.path.join(cn.ROOT, "analysis", "conditional_checks_results.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    print(f"\ndone in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
