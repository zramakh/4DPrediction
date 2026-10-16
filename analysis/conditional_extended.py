#!/usr/bin/env python3
"""conditional_numbers.py extended to every Chinese almanac and Vedic/KP
parameter in almanac.py (~80 parameters, every single one and every pair).

Same three questions per parameter set (see conditional_numbers.py):
strongest number / i-Box group associations against shuffled dates, overall
unevenness against shuffled dates, and replication on later / other years.
To calibrate the unevenness z-scores, one extra shuffled copy of the data is
scored exactly like the real data, so "how many sets reach z > 3" can be
compared with what shuffled data gives.

Run from the repo root:  python3 analysis/conditional_extended.py   (~30 min on 4 cores)
"""

import csv
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
import almanac  # noqa: E402
import conditional_numbers as cn  # noqa: E402
import ephemeris as eph  # noqa: E402

ROOT = cn.ROOT
N_SHUFFLES = 10
SPLIT_YEAR = cn.SPLIT_YEAR
G = {}  # shared with forked workers


def date_context(date):
    day = dt.date.fromisoformat(date)
    a = eph.describe(dt.datetime.combine(day, dt.time(11)))
    out = {"weekday": day.strftime("%a"), "month": day.strftime("%b"), "day_of_month": day.day,
           "era_5yr": f"{day.year - (day.year - 1985) % 5}-{day.year - (day.year - 1985) % 5 + 4}",
           "moon_phase": a["phase"], "moon_sign_tropical": a["moon_sign"], "sun_sign_tropical": a["sun_sign"]}
    out.update(almanac.factors(date))
    return out


def load():
    rows = []
    for op, stem in cn.OPERATORS.items():
        with open(os.path.join(ROOT, "data", f"{stem}.csv"), newline="") as f:
            for r in csv.DictReader(f):
                rows.append((op, r["date"], r["prize"], int(r["4d_number"])))
    dates = sorted({r[1] for r in rows})
    t = time.time()
    with mp.Pool() as pool:
        ctx = pool.map(date_context, dates, chunksize=64)
    print(f"computed {len(ctx[0])} parameters for {len(dates)} draw dates in {time.time() - t:.0f}s", flush=True)
    factors = list(ctx[0])
    labels = {f: sorted({c[f] for c in ctx}, key=str) for f in factors}
    codes = {f: np.array([labels[f].index(c[f]) for c in ctx]) for f in factors}
    labels["prize"] = ["Top 3", "Special", "Consolation"]
    date_ix = {d: i for i, d in enumerate(dates)}
    data = {"op": np.array([r[0] for r in rows]), "date": np.array([date_ix[r[1]] for r in rows]),
            "year": np.array([int(r[1][:4]) for r in rows]),
            "prize": np.array([labels["prize"].index(cn.PRIZE_GROUP[r[2]]) for r in rows]),
            "num": np.array([r[3] for r in rows])}
    return data, codes, labels, factors + ["prize"], len(dates)


def task(args):
    """Scan a chunk of parameter sets in one scope."""
    scope, fsets = args
    data, codes, labels, perms, calib = G["data"], G["codes"], G["labels"], G["perms"], G["calib"]
    sel = data["op"] == scope if scope != "All operators" else np.ones(len(data["num"]), bool)
    num, years = data["num"][sel], data["year"][sel]
    splits = {"before_vs_after_2012": (years < SPLIT_YEAR, years >= SPLIT_YEAR),
              "even_vs_odd_years": (years % 2 == 0, years % 2 == 1)}
    out = {"sets": {}, "assoc": {u: [] for u in cn.UNITS}, "found": {u: [] for u in cn.UNITS},
           "null_best": {u: np.ones(N_SHUFFLES) for u in cn.UNITS}, "cells": {u: 0 for u in cn.UNITS}}
    for fset in fsets:
        name = " x ".join(fset)
        cell, sizes = cn.cell_codes(sel, data["date"], codes, data["prize"], fset)
        shuffled = [cn.cell_codes(sel, p[data["date"]], codes, data["prize"], fset)[0] for p in perms]
        ccal = cn.cell_codes(sel, calib[data["date"]], codes, data["prize"], fset)[0]
        entry = {}
        for u, (n_units, share, fmt) in cn.UNITS.items():
            ux = num if u == "number" else cn.GROUP_OF[num]
            overall = np.bincount(ux, minlength=n_units) / len(ux)
            chi, cc, cu, ccnt, cexp, cp = cn.scan(cell, ux, n_units, share, overall)
            out["cells"][u] += len(cc)
            for i in np.argsort(cp)[:3]:
                out["assoc"][u].append({"scope": scope, "factors": name,
                                        "cell": cn.decode(int(cc[i]), list(fset), sizes, labels),
                                        "value": fmt(int(cu[i])), "wins": int(ccnt[i]),
                                        "expected": round(float(cexp[i]), 2), "p_best_in_cell": float(cp[i])})
            z = zc = None
            if fset != ("prize",):
                null = []
                for s, pc in enumerate(shuffled):
                    c0, *_, p0 = cn.scan(pc, ux, n_units, share, overall)
                    null.append(c0)
                    out["null_best"][u][s] = min(out["null_best"][u][s], p0.min())
                m, sd = np.mean(null), np.std(null, ddof=1)
                z = round(float((chi - m) / sd), 2)
                zc = round(float((cn.scan(ccal, ux, n_units, share, overall)[0] - m) / sd), 2)
            entry[u] = {"cells": len(cc), "z": z, "z_shuffled_copy": zc,
                        "replication": {k: cn.replicate(cell, ux, n_units, share, tr, te)
                                        for k, (tr, te) in splits.items()}}
            # discovery on draws before 2012 only, outcome from 2012 on
            if "era_5yr" not in fset:
                tr, te = splits["before_vs_after_2012"]
                _, dc, du, dcnt, dexp, _ = cn.scan(cell[tr], ux[tr], n_units, share, np.full(n_units, 1 / n_units))
                n_te = np.bincount(cell[te], minlength=cell.max() + 1)
                ok = n_te[dc] > 0
                dc, du, dcnt, dexp = dc[ok], du[ok], dcnt[ok], dexp[ok]
                p = cn.poisson_sf(dcnt, dexp)
                tk, tcount = np.unique(cell[te] * n_units + ux[te], return_counts=True)
                for i in np.argsort(p)[:5]:
                    key = dc[i] * n_units + du[i]
                    pos = min(np.searchsorted(tk, key), len(tk) - 1)
                    out["found"][u].append({
                        "p": float(p[i]), "scope": scope, "factors": name,
                        "cell": cn.decode(int(dc[i]), list(fset), sizes, labels), "value": fmt(int(du[i])),
                        "wins_before_2012": int(dcnt[i]), "expected_before": round(float(dexp[i]), 3),
                        "wins_from_2012": int(tcount[pos]) if tk[pos] == key else 0,
                        "expected_from_2012": float(n_te[dc[i]] * share[du[i]])})
        out["sets"][name] = entry
    return scope, out


def main():
    t0 = time.time()
    data, codes, labels, factors, n_dates = load()
    rng = np.random.default_rng(20261017)
    G.update(data=data, codes=codes, labels=labels,
             perms=[rng.permutation(n_dates) for _ in range(N_SHUFFLES)], calib=rng.permutation(n_dates))
    fsets = [(f,) for f in factors] + list(itertools.combinations(factors, 2))
    scopes = list(cn.OPERATORS) + ["All operators"]
    chunks = [(s, fsets[i:i + 40]) for s in scopes for i in range(0, len(fsets), 40)]
    print(f"{len(factors)} parameters -> {len(fsets)} parameter sets x {len(scopes)} scopes "
          f"= {len(chunks)} chunks", flush=True)
    res = {"settings": {"factors": factors, "factor_sets": len(fsets), "shuffles": N_SHUFFLES,
                        "split_year": SPLIT_YEAR, "top_k": cn.TOP_K, "labels": labels},
           "scopes": {s: {} for s in scopes}}
    assoc = {u: [] for u in cn.UNITS}
    found = {u: [] for u in cn.UNITS}
    null_best = {u: np.ones(N_SHUFFLES) for u in cn.UNITS}
    cells = {u: 0 for u in cn.UNITS}
    with mp.Pool() as pool:
        for k, (scope, out) in enumerate(pool.imap_unordered(task, chunks), 1):
            res["scopes"][scope].update(out["sets"])
            for u in cn.UNITS:
                assoc[u] += out["assoc"][u]
                found[u] += out["found"][u]
                null_best[u] = np.minimum(null_best[u], out["null_best"][u])
                cells[u] += out["cells"][u]
            if k % 20 == 0 or k == len(chunks):
                print(f"  {k}/{len(chunks)} chunks done ({time.time() - t0:.0f}s)", flush=True)

    for u in cn.UNITS:
        a = sorted(assoc[u], key=lambda x: x["p_best_in_cell"])
        for x in a:
            x["p_all_cells"] = float(cn.best_of(x["p_best_in_cell"], cells[u]))
        res[f"top_{u}_associations"] = a[:30]
        res[f"shuffle_{u}"] = {"real_best_p_in_cell": a[0]["p_best_in_cell"],
                               "shuffled_best_p_in_cell": sorted(float(v) for v in null_best[u]),
                               "share_of_shuffles_at_least_as_extreme":
                                   float(np.mean(null_best[u] <= a[0]["p_best_in_cell"])),
                               "cells_searched": cells[u]}
        f = sorted(found[u], key=lambda x: x["p"])
        top = f[:200]
        h, e = sum(x["wins_from_2012"] for x in top), sum(x["expected_from_2012"] for x in top)
        res[f"discover_before_2012_{u}"] = {
            "summary_top200": {"wins_from_2012": h, "expected_if_random": round(e, 1),
                               "lift": round(h / e, 3), "z": round((h - e) / math.sqrt(e), 2)},
            "top30": f[:30]}
    res["summary"] = summarise(res)
    with open(os.path.join(ROOT, "analysis", "conditional_extended_results.json"), "w") as fh:
        json.dump(res, fh, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    report(res)
    print(f"\ndone in {time.time() - t0:.0f}s")


def summarise(res):
    s = {}
    for scope, sets in res["scopes"].items():
        for u in cn.UNITS:
            v = [x[u] for x in sets.values() if x[u]["z"] is not None]
            z = np.array([x["z"] for x in v])
            zc = np.array([x["z_shuffled_copy"] for x in v])
            rep = {}
            for k in ("before_vs_after_2012", "even_vs_odd_years"):
                r = [x[u]["replication"][k] for x in sets.values() if x[u]["replication"][k]]
                h, e = sum(x["hits"] for x in r), sum(x["expected"] for x in r)
                rz = np.array([x["z"] for x in r])
                rep[k] = {"lift": round(h / e, 4), "sets_z_gt_3": int((rz > 3).sum()),
                          "sets_z_lt_-3": int((rz < -3).sum()), "sets": len(r)}
            top = sorted(((x[u]["z"], k) for k, x in sets.items() if x[u]["z"] is not None), reverse=True)[:5]
            s[f"{scope} | {u}"] = {
                "sets": len(v), "median_z": round(float(np.median(z)), 2),
                "z_gt_3_real": int((z > 3).sum()), "z_gt_3_shuffled_copy": int((zc > 3).sum()),
                "z_gt_4_real": int((z > 4).sum()), "z_gt_4_shuffled_copy": int((zc > 4).sum()),
                "most_uneven_sets": top, "replication": rep}
    return s


def report(res):
    for u in cn.UNITS:
        print(f"\n=== strongest {u} associations ===")
        for x in res[f"top_{u}_associations"][:15]:
            print(f"  {x['scope']:<13} {x['cell']:<62} {x['value']:<16} {x['wins']:>3} vs {x['expected']:>5}  "
                  f"p_cell={x['p_best_in_cell']:.2g} p_all={x['p_all_cells']:.2f}")
        sh = res[f"shuffle_{u}"]
        print(f"  real best {sh['real_best_p_in_cell']:.2g}; shuffled bests {[f'{v:.2g}' for v in sh['shuffled_best_p_in_cell']]}"
              f" -> {sh['share_of_shuffles_at_least_as_extreme']:.0%} as extreme; {sh['cells_searched']} cells")
        d = res[f"discover_before_2012_{u}"]
        print(f"  discovered <2012, tested >=2012, top 200: {d['summary_top200']}")
        for x in d["top30"][:6]:
            print(f"    {x['scope']:<13} {x['cell']:<55} {x['value']:<16} before {x['wins_before_2012']} "
                  f"(exp {x['expected_before']}) after {x['wins_from_2012']} (exp {x['expected_from_2012']:.2f})")
    print("\n=== unevenness (z vs shuffled dates) and replication ===")
    for k, v in res["summary"].items():
        print(f"  {k:<26} sets {v['sets']}, median z {v['median_z']:+.2f}, z>3 real {v['z_gt_3_real']} vs shuffled "
              f"{v['z_gt_3_shuffled_copy']}, z>4 {v['z_gt_4_real']} vs {v['z_gt_4_shuffled_copy']}")
        print(f"  {'':<26} most uneven {[(n, z) for z, n in v['most_uneven_sets'][:3]]}")
        print(f"  {'':<26} replication {v['replication']}")


if __name__ == "__main__":
    main()
