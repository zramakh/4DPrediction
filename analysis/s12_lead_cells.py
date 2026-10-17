#!/usr/bin/env python3
"""Mercury nakshatra x Venus rashi S1 lead (all earlier same-value days,
Straight hits; see s12_family.py) broken down by value: each Mercury
nakshatra, each Venus rashi and each combined cell, before 2012 and
2012-2026, plus a check whether the cells that were best before 2012 stay
best afterwards.

Run from the repo root:  python3 analysis/s12_lead_cells.py
"""

import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recurrence_s12 as r  # noqa: E402

F1, F2 = "mercury_nakshatra", "venus_rashi"
SPLIT = 2012


def per_day():
    """Per draw day with an earlier same-value day: (day, hits, expected) for S1 / all earlier days / Straight."""
    G = r.G
    cells = r.cells_of((F1, F2))
    order = np.lexsort((np.arange(len(cells)), cells))
    sc = cells[order]
    newgrp = np.r_[True, sc[1:] != sc[:-1]]
    cs = np.cumsum(G["dday"][order], axis=0)
    start = np.maximum.accumulate(np.where(newgrp, np.arange(len(sc)), 0))
    base = np.where((start > 0)[:, None, None], cs[np.maximum(start - 1, 0)], 0)
    C = (cs - G["dday"][order] - base)[~newgrp]
    days = order[~newgrp]
    P = r.picks(C, True)
    y = G["yix"][days]
    hits = G["W"][days[:, None], P].sum(1).astype(float)
    exp = G["nwin"][days] * G["Py"][y[:, None], P].sum(1)
    return days, hits, exp


def zz(o, e):
    return (o - e) / math.sqrt(e) if e > 0 else 0.0


def table(name, labels, key, hits, exp, late, min_exp=0.0):
    print(f"\n{name}: hits vs expected (ratio, z) before {SPLIT} | {SPLIT}-2026 | all")
    rows = []
    for v in np.unique(key):
        m = key == v
        b, a = m & ~late, m & late
        ob, eb, oa, ea = hits[b].sum(), exp[b].sum(), hits[a].sum(), exp[a].sum()
        rows.append((labels(v), ob, eb, oa, ea))
    rows.sort(key=lambda x: -zz(x[1] + x[3], x[2] + x[4]))
    out = []
    for lab, ob, eb, oa, ea in rows:
        if eb + ea < min_exp:
            continue
        print(f"   {lab:<28} {ob:>4.0f}/{eb:>6.1f} (x{ob / eb if eb else 0:.2f}, {zz(ob, eb):+.2f}) | "
              f"{oa:>4.0f}/{ea:>6.1f} (x{oa / ea if ea else 0:.2f}, {zz(oa, ea):+.2f}) | "
              f"x{(ob + oa) / (eb + ea):.2f}, z {zz(ob + oa, eb + ea):+.2f}")
        out.append({"value": lab, "hits_before": ob, "exp_before": eb, "hits_after": oa, "exp_after": ea})
    zb = np.array([zz(x[1], x[2]) for x in rows if x[2] + x[4] >= min_exp])
    za = np.array([zz(x[3], x[4]) for x in rows if x[2] + x[4] >= min_exp])
    ok = np.isfinite(zb) & np.isfinite(za)
    rho = np.corrcoef(zb[ok], za[ok])[0, 1]
    chi = float((za ** 2).sum())
    print(f"   -> {len(zb)} values; before-vs-after correlation of z {rho:+.2f}; "
          f"{int(((zb > 0) & (za > 0)).sum())} positive in both, {int(((zb > 0) & (za <= 0)).sum())} positive only before; "
          f"spread after {SPLIT}: chi2 {chi:.1f} on {len(za)} (chance ~{len(za)})")
    return {"rows": out, "corr_before_after": float(rho), "chi2_after": chi, "n": len(za)}


def main():
    r.setup()
    G = r.G
    D = G["D"]
    yr = np.array([int(d[:4]) for d in D.dates])
    days, hits, exp = per_day()
    late = yr[days] >= SPLIT
    c1, c2 = D.codes[F1][days], D.codes[F2][days]
    print(f"Lead overall: before {hits[~late].sum():.0f}/{exp[~late].sum():.1f}, after {hits[late].sum():.0f}/{exp[late].sum():.1f}")
    out = {}
    out["mercury_nakshatra"] = table("By Mercury nakshatra", lambda v: D.labels[F1][v], c1, hits, exp, late)
    out["venus_rashi"] = table("By Venus rashi", lambda v: D.labels[F2][v], c2, hits, exp, late)
    cell = c1 * 100 + c2
    out["cells"] = table("By combined cell (expected >= 6 hits over all years)",
                         lambda v: f"{D.labels[F1][v // 100]} + {D.labels[F2][v % 100]}", cell, hits, exp, late, min_exp=6)
    # forward: cells with positive excess before 2012 vs the rest, scored after 2012
    pos = set()
    for v in np.unique(cell):
        m = (cell == v) & ~late
        if hits[m].sum() > exp[m].sum():
            pos.add(v)
    mp_ = np.isin(cell, list(pos)) & late
    mn = ~np.isin(cell, list(pos)) & late
    print(f"\nForward: cells above chance before {SPLIT} -> after: {hits[mp_].sum():.0f}/{exp[mp_].sum():.1f} "
          f"(x{hits[mp_].sum() / exp[mp_].sum():.3f}, z {zz(hits[mp_].sum(), exp[mp_].sum()):+.2f}); "
          f"other cells -> {hits[mn].sum():.0f}/{exp[mn].sum():.1f} (x{hits[mn].sum() / exp[mn].sum():.3f}, "
          f"z {zz(hits[mn].sum(), exp[mn].sum()):+.2f})")
    out["forward_positive_cells"] = {"n_cells": len(pos), "hits": hits[mp_].sum(), "exp": exp[mp_].sum(),
                                     "other_hits": hits[mn].sum(), "other_exp": exp[mn].sum()}
    today = [c for c in out["cells"]["rows"] if c["value"] == "Vishakha + Tula"]
    print("Today's cell (Vishakha + Tula):", today)
    json.dump(out, open(os.path.join(r.ROOT, "analysis", "s12_lead_cells_results.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
