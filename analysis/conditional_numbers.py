#!/usr/bin/env python3
"""Do particular 4D numbers win more often under particular conditions?

For every single parameter, and every pair of parameters, the draws are split
into groups ("cells"), e.g. weekday=Sun, or moon phase=Full x month=Feb. Within
each cell we count how often each of the 10,000 numbers won, and how often
each permutation group won (the sorted digits, as in an i-Box bet: 1234 and
4321 are the same group). Then:

1. Strongest associations: the number (or permutation group) most
   over-represented in each cell, with a Poisson p-value corrected for picking
   the best of 10,000 numbers in that cell.
2. Is any of this beyond chance? The same search is repeated with the draw
   dates shuffled (each draw keeps its numbers but gets another date's
   parameters). If real number/condition links existed, the real data would
   give stronger "best associations" and more uneven cells than the shuffles.
3. Do they repeat? The top numbers of each cell are learned on draws before
   2012 and checked on the same cell from 2012 on (and, separately, learned on
   even years and checked on odd years).

Run from the repo root:  python3 analysis/conditional_numbers.py
"""

import csv
import datetime as dt
import itertools
import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seasonal_astro as sa  # noqa: E402
import vedic  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPERATORS = {"Magnum": "magnum", "Sports Toto": "sportstoto", "Da Ma Cai": "damacai"}
SPLIT_YEAR = 2012
TOP_K = 10           # numbers learned per cell for the replication test
N_SHUFFLES = 20
RNG = np.random.default_rng(20261016)
# 2015-01-09 repeats 22 of the 23 numbers of 2015-01-07 on the source site; a copy, not a draw
EXCLUDE = {("Magnum", "2015-01-09")}

DATE_FACTORS = ["weekday", "month", "day_of_month", "era_5yr", "moon_phase", "moon_sign",
                "sun_sign", "lunar_month", "lunar_day", "chinese_zodiac", "nakshatra", "tithi"]
FACTORS = DATE_FACTORS + ["prize"]
PRIZE_GROUP = {"1st": "Top 3", "2nd": "Top 3", "3rd": "Top 3",
               "Special": "Special", "Consolation": "Consolation"}

# permutation group of each number and the share of all numbers in each group
SORTED_KEY = np.array([int("".join(sorted(f"{n:04d}"))) for n in range(10000)])
GROUP_IDS, GROUP_OF = np.unique(SORTED_KEY, return_inverse=True)
GROUP_SHARE = np.bincount(GROUP_OF, minlength=len(GROUP_IDS)) / 10000
UNITS = {
    "number": (10000, np.full(10000, 1e-4), lambda i: f"{i:04d}"),
    "perm_group": (len(GROUP_IDS), GROUP_SHARE, lambda i: f"{GROUP_IDS[i]:04d} (any order)"),
}


# ------------------------------------------------------------------ data
def date_context(date):
    day = dt.date.fromisoformat(date)
    c = sa.context(date)
    p = vedic.panchanga(dt.datetime.combine(day, dt.time(11)), day)
    return {
        "weekday": day.strftime("%a"),
        "month": day.strftime("%b"),
        "day_of_month": day.day,
        "era_5yr": f"{day.year - (day.year - 1985) % 5}-{day.year - (day.year - 1985) % 5 + 4}",
        "moon_phase": c["phase"],
        "moon_sign": c["moon_sign"],
        "sun_sign": c["sun_sign"],
        "lunar_month": c["lunar_month"],
        "lunar_day": c["lunar_day"],
        "chinese_zodiac": c["chinese_zodiac"],
        "nakshatra": p["nakshatra"],
        "tithi": p["tithi"],
    }


def load_rows():
    """One record per winning number, with operator, date index and prize."""
    rows = []
    for op, stem in OPERATORS.items():
        with open(os.path.join(ROOT, "data", f"{stem}.csv"), newline="") as f:
            for r in csv.DictReader(f):
                if (op, r["date"]) not in EXCLUDE:
                    rows.append((op, r["date"], r["prize"], int(r["4d_number"])))
    dates = sorted({r[1] for r in rows})
    t = time.time()
    ctx = [date_context(d) for d in dates]
    print(f"computed parameters for {len(dates)} draw dates in {time.time() - t:.0f}s")
    labels = {f: sorted({c[f] for c in ctx}, key=str) for f in DATE_FACTORS}
    codes = {f: np.array([labels[f].index(c[f]) for c in ctx]) for f in DATE_FACTORS}
    labels["prize"] = ["Top 3", "Special", "Consolation"]
    date_ix = {d: i for i, d in enumerate(dates)}
    data = {
        "op": np.array([r[0] for r in rows]),
        "date": np.array([date_ix[r[1]] for r in rows]),
        "year": np.array([int(r[1][:4]) for r in rows]),
        "prize": np.array([labels["prize"].index(PRIZE_GROUP[r[2]]) for r in rows]),
        "num": np.array([r[3] for r in rows]),
    }
    return data, codes, labels, len(dates)


# ------------------------------------------------------------------ statistics
LGAMMA = np.array([math.lgamma(j + 1) for j in range(2000)])
TAIL = np.arange(80)


def poisson_sf(k, lam):
    """P(X >= k) for X ~ Poisson(lam), vectorised and accurate in the far tail."""
    k, lam = np.atleast_1d(k).astype(int), np.atleast_1d(lam).astype(float)
    j = k[:, None] + TAIL[None, :]
    p = np.exp(j * np.log(lam)[:, None] - lam[:, None] - LGAMMA[j]).sum(1)
    return np.where(k <= 0, 1.0, np.minimum(p, 1.0))


def best_of(p, n):
    """Chance that the best of n independent tries is at least this extreme."""
    p = np.minimum(np.asarray(p, float), 1 - 1e-16)
    return -np.expm1(n * np.log1p(-p))


def cell_codes(sel, rows_date, codes, prize, fset):
    """Cell index of each selected row for a factor set, and the size of each factor."""
    cell = np.zeros(sel.sum(), dtype=np.int64)
    sizes = []
    for f in fset:
        col = prize[sel] if f == "prize" else codes[f][rows_date[sel]]
        k = 3 if f == "prize" else int(codes[f].max()) + 1
        cell = cell * k + col
        sizes.append(k)
    return cell, sizes


def decode(c, fset, sizes, labels):
    parts = []
    for f, k in zip(reversed(fset), reversed(sizes)):
        parts.append(f"{f}={labels[f][c % k]}")
        c //= k
    return " & ".join(reversed(parts))


def sparse_counts(cell, unit_ix, n_units):
    """Non-zero (cell, unit) counts, sorted by cell."""
    key, cnt = np.unique(cell * n_units + unit_ix, return_counts=True)
    return key // n_units, key % n_units, cnt


def once_per_draw(date_ix, unit_ix, n_units):
    """Mask keeping each number (or permutation group) once per draw.

    Published draws occasionally repeat a number across prize slots; counted
    twice, a single draw would look like a number "recurring" under its
    conditions.
    """
    _, first = np.unique(date_ix * n_units + unit_ix, return_index=True)
    keep = np.zeros(len(unit_ix), bool)
    keep[first] = True
    return keep


def scan(cell, unit_ix, n_units, share):
    """Unevenness statistic and the most over-represented unit of every cell.

    Rows must already be once-per-draw (see once_per_draw). Unevenness is
    sum over cells and units of c(c-1) / (cell size x share): the number of
    times the same number won in two different draws of the same cell,
    weighted by how unlikely that is. Comparing it with shuffled dates (same
    draws, parameters reassigned) shows whether numbers cluster under
    particular conditions. Overall number/digit bias is the same in the
    shuffles, so it cancels out.
    """
    c, u, cnt = sparse_counts(cell, unit_ix, n_units)
    n_cell = np.bincount(cell)
    chi = float((cnt * (cnt - 1) / (n_cell[c] * share[u])).sum())
    exp = n_cell[c] * share[u]
    z = (cnt - exp) / np.sqrt(exp)
    order = np.lexsort((-z, c))               # by cell, most over-represented first
    first = order[np.r_[True, c[order][1:] != c[order][:-1]]]
    p = best_of(poisson_sf(cnt[first], exp[first]), n_units)
    return chi, c[first], u[first], cnt[first], exp[first], p


def replicate(cell, unit_ix, n_units, share, train, test):
    """Learn the TOP_K most over-represented units of each cell on `train`, then
    count their wins in the same cell on `test` against the random expectation."""
    c, u, cnt = sparse_counts(cell[train], unit_ix[train], n_units)
    score = cnt / share[u] + RNG.random(len(cnt)) * 1e-3   # random tie-break
    order = np.lexsort((-score, c))
    c, u = c[order], u[order]
    start = np.r_[0, np.flatnonzero(c[1:] != c[:-1]) + 1]
    rank = np.arange(len(c)) - np.repeat(start, np.diff(np.r_[start, len(c)]))
    keep = rank < TOP_K
    c, u = c[keep], u[keep]
    te_cell, te_unit = cell[test], unit_ix[test]
    n_te = np.bincount(te_cell, minlength=cell.max() + 1)
    tk, tc = np.unique(te_cell * n_units + te_unit, return_counts=True)
    pos = np.searchsorted(tk, c * n_units + u)
    pos = np.minimum(pos, len(tk) - 1)
    hits = int(np.where(tk[pos] == c * n_units + u, tc[pos], 0).sum())
    exp = float((n_te[c] * share[u]).sum())
    if exp == 0:
        return None
    return {"hits": hits, "expected": round(exp, 1), "lift": round(hits / exp, 3),
            "z": round((hits - exp) / math.sqrt(exp), 2)}


# ------------------------------------------------------------------ analysis
def scopes_of(data):
    s = {op: data["op"] == op for op in OPERATORS}
    s["All operators"] = np.ones(len(data["num"]), bool)
    return s


def analyse(data, codes, labels, n_dates):
    fsets = [(f,) for f in FACTORS] + list(itertools.combinations(FACTORS, 2))
    perms = [RNG.permutation(n_dates) for _ in range(N_SHUFFLES)]
    results = {"settings": {"split_year": SPLIT_YEAR, "top_k": TOP_K, "shuffles": N_SHUFFLES,
                            "factors": FACTORS, "factor_sets": len(fsets)}, "scopes": {}}
    assoc = {u: [] for u in UNITS}
    null_best = {u: np.ones(N_SHUFFLES) for u in UNITS}
    total_cells = {u: 0 for u in UNITS}
    for scope, sel in scopes_of(data).items():
        t = time.time()
        num, years = data["num"][sel], data["year"][sel]
        splits = {"before_vs_after_2012": (years < SPLIT_YEAR, years >= SPLIT_YEAR),
                  "even_vs_odd_years": (years % 2 == 0, years % 2 == 1)}
        sr = {}
        for fset in fsets:
            cell, sizes = cell_codes(sel, data["date"], codes, data["prize"], fset)
            entry = {}
            for u, (n_units, share, fmt) in UNITS.items():
                ux = num if u == "number" else GROUP_OF[num]
                k1 = once_per_draw(data["date"][sel], ux, n_units)
                ux, ucell = ux[k1], cell[k1]
                chi, cc, cu, ccnt, cexp, cp = scan(ucell, ux, n_units, share)
                total_cells[u] += len(cc)
                for i in np.argsort(cp)[:3]:
                    assoc[u].append({"scope": scope, "factors": " x ".join(fset),
                                     "cell": decode(int(cc[i]), list(fset), sizes, labels),
                                     "value": fmt(int(cu[i])), "wins": int(ccnt[i]),
                                     "expected": round(float(cexp[i]), 2), "p_best_in_cell": float(cp[i])})
                null_chi = []
                if fset != ("prize",):  # prize is per row, shuffling dates does not move it
                    for s, perm in enumerate(perms):
                        pcell, _ = cell_codes(sel, perm[data["date"]], codes, data["prize"], fset)
                        chi0, *_, p0 = scan(pcell[k1], ux, n_units, share)
                        null_chi.append(chi0)
                        null_best[u][s] = min(null_best[u][s], p0.min())
                z = None
                if null_chi:
                    z = round(float((chi - np.mean(null_chi)) / np.std(null_chi, ddof=1)), 2)
                entry[u] = {"cells": len(cc), "unevenness_z_vs_shuffled": z,
                            "replication": {k: replicate(ucell, ux, n_units, share, tr[k1], te[k1])
                                            for k, (tr, te) in splits.items()}}
            sr[" x ".join(fset)] = entry
        results["scopes"][scope] = sr
        print(f"{scope}: {len(fsets)} parameter sets scanned in {time.time() - t:.0f}s", flush=True)

    for u in UNITS:
        a = sorted(assoc[u], key=lambda x: x["p_best_in_cell"])
        for x in a:
            x["p_all_cells"] = float(best_of(x["p_best_in_cell"], total_cells[u]))
        results[f"top_{u}_associations"] = a[:25]
        results[f"shuffle_{u}"] = {
            "real_best_p_in_cell": a[0]["p_best_in_cell"],
            "shuffled_best_p_in_cell": sorted(float(v) for v in null_best[u]),
            "share_of_shuffles_at_least_as_extreme": float(np.mean(null_best[u] <= a[0]["p_best_in_cell"])),
            "cells_searched": total_cells[u]}
    return results


def discover_then_test(data, codes, labels):
    """Find the strongest associations using draws before 2012 only, then see what they did after."""
    fsets = [(f,) for f in FACTORS if f != "era_5yr"] + \
        [p for p in itertools.combinations(FACTORS, 2) if "era_5yr" not in p]
    out = {}
    for u, (n_units, share, fmt) in UNITS.items():
        found = []
        for scope, sel in scopes_of(data).items():
            num, years = data["num"][sel], data["year"][sel]
            ux = num if u == "number" else GROUP_OF[num]
            k1 = once_per_draw(data["date"][sel], ux, n_units)
            ux, years = ux[k1], years[k1]
            tr, te = years < SPLIT_YEAR, years >= SPLIT_YEAR
            for fset in fsets:
                cell, sizes = cell_codes(sel, data["date"], codes, data["prize"], fset)
                cell = cell[k1]
                _, cc, cu, ccnt, cexp, _ = scan(cell[tr], ux[tr], n_units, share)
                p = poisson_sf(ccnt, cexp)
                n_te = np.bincount(cell[te], minlength=cell.max() + 1)
                tk, tc = np.unique(cell[te] * n_units + ux[te], return_counts=True)
                key = cc * n_units + cu
                pos = np.minimum(np.searchsorted(tk, key), len(tk) - 1)
                after = np.where(tk[pos] == key, tc[pos], 0)
                for i in np.flatnonzero(n_te[cc] > 0):
                    found.append((float(p[i]), scope, " x ".join(fset), decode(int(cc[i]), list(fset), sizes, labels),
                                  fmt(int(cu[i])), int(ccnt[i]), float(cexp[i]), int(after[i]),
                                  float(n_te[cc[i]] * share[cu[i]])))
        found.sort(key=lambda x: x[0])
        top = found[:200]
        hits, exp = sum(x[7] for x in top), sum(x[8] for x in top)
        out[u] = {
            "summary_top200": {"wins_from_2012": hits, "expected_if_random": round(exp, 1),
                               "lift": round(hits / exp, 3), "z": round((hits - exp) / math.sqrt(exp), 2)},
            "top20": [{"scope": x[1], "factors": x[2], "cell": x[3], "value": x[4],
                       "wins_before_2012": x[5], "expected_before": round(x[6], 2),
                       "wins_from_2012": x[7], "expected_from_2012": round(x[8], 2)} for x in found[:20]],
        }
    return out


def main():
    t0 = time.time()
    data, codes, labels, n_dates = load_rows()
    results = analyse(data, codes, labels, n_dates)
    results["discover_before_2012_test_after"] = discover_then_test(data, codes, labels)
    with open(os.path.join(ROOT, "analysis", "conditional_results.json"), "w") as f:
        json.dump(results, f, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    report(results)
    print(f"\ndone in {time.time() - t0:.0f}s")


def report(r):
    for u in UNITS:
        print(f"\n=== strongest {u} associations (all draws) ===")
        for x in r[f"top_{u}_associations"][:12]:
            print(f"  {x['scope']:<13} {x['cell']:<55} {x['value']:<16} {x['wins']:>3} wins vs {x['expected']:>5} exp  "
                  f"p(best in cell)={x['p_best_in_cell']:.2g}  p(all cells)={x['p_all_cells']:.2f}")
        s = r[f"shuffle_{u}"]
        print(f"  real best p={s['real_best_p_in_cell']:.2g}; shuffled-date bests: "
              f"{', '.join(f'{v:.2g}' for v in s['shuffled_best_p_in_cell'][:5])} ... "
              f"-> {s['share_of_shuffles_at_least_as_extreme']:.0%} of shuffles as extreme ({s['cells_searched']} cells)")
    print("\n=== unevenness vs shuffled dates (z) and replication (lift, z) ===")
    for scope, sets in r["scopes"].items():
        for u in UNITS:
            zs = [v[u]["unevenness_z_vs_shuffled"] for v in sets.values() if v[u]["unevenness_z_vs_shuffled"] is not None]
            reps = [v[u]["replication"]["before_vs_after_2012"] for v in sets.values() if v[u]["replication"]["before_vs_after_2012"]]
            h, e = sum(x["hits"] for x in reps), sum(x["expected"] for x in reps)
            big = sorted(((v[u]["unevenness_z_vs_shuffled"] or 0, k) for k, v in sets.items()), reverse=True)[:3]
            print(f"  {scope:<13} {u:<10} unevenness z: median {np.median(zs):+.2f}, max {max(zs):+.2f}; "
                  f"#z>3: {sum(z > 3 for z in zs)}/{len(zs)}; top {[(k, round(z, 1)) for z, k in big]}")
            print(f"  {'':<13} {'':<10} learned<2012 -> tested>=2012 over all sets: lift {h / e:.3f}")
    print("\n=== discovered before 2012, tested from 2012 ===")
    for u, d in r["discover_before_2012_test_after"].items():
        print(f"  {u}: top-200 associations: {d['summary_top200']}")
        for x in d["top20"][:8]:
            print(f"    {x['scope']:<13} {x['cell']:<50} {x['value']:<16} before {x['wins_before_2012']} (exp {x['expected_before']}), "
                  f"after {x['wins_from_2012']} (exp {x['expected_from_2012']})")


if __name__ == "__main__":
    main()
