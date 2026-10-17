#!/usr/bin/env python3
"""How many numbers to take for the Mercury nakshatra x Venus rashi lead?

For each draw day, digit counts per position come from all earlier draw days
with the same Mercury nakshatra and Venus rashi (as in s12_lead_cells.py).
Two ways to make K picks:
  ranked  every number scored by sum over positions of log(count + 1); top K
          for K = 1, 2, 4, ... 1024 (ties -> lower number)
  grid    top-m digits per position -> m^4 numbers (m = 1..5: 1, 16, 81, 256, 625)
Hits = Straight hits on that day's winners (all 3 operators). Chance uses that
year's digit mix (as before). The same is done with no parameter (all earlier
days) for comparison. K is chosen on draw days before 2012 and scored on
2012-2026; 100 shifted calendars give how often a meaningless calendar does as
well after choosing its own best K.

Run from the repo root:  python3 analysis/s12_lead_k.py
"""

import json
import math
import multiprocessing as mp
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recurrence_s12 as r  # noqa: E402

LEAD = ("mercury_nakshatra", "venus_rashi")
KS = [2 ** i for i in range(11)]
MS = [1, 2, 3, 4, 5]
SPLIT = 2012
DIG = r.DIG


def sources(cells):
    G = r.G
    order = np.lexsort((np.arange(len(cells)), cells))
    sc = cells[order]
    ng = np.r_[True, sc[1:] != sc[:-1]]
    cs = np.cumsum(G["dday"][order], 0)
    st = np.maximum.accumulate(np.where(ng, np.arange(len(sc)), 0))
    base = np.where((st > 0)[:, None, None], cs[np.maximum(st - 1, 0)], 0)
    return order[~ng], (cs - G["dday"][order] - base)[~ng]


def curves(cells):
    """Per day (days, hits[day, k], exp[day, k]) for ranked K and grid m."""
    G = r.G
    days, C = sources(cells)
    y = G["yix"][days]
    n = len(days)
    kmax = KS[-1]
    H = np.zeros((n, len(KS) + len(MS)))
    E = np.zeros_like(H)
    L = np.log(C + 1)                                                       # (n, 4, 10)
    for a in range(0, n, 512):
        b = min(n, a + 512)
        s = (L[a:b, 0][:, DIG[:, 0]] + L[a:b, 1][:, DIG[:, 1]] + L[a:b, 2][:, DIG[:, 2]] + L[a:b, 3][:, DIG[:, 3]])
        s = s - np.arange(10000) * 1e-9                                     # ties -> lower number
        top = np.argpartition(-s, kmax, axis=1)[:, :kmax]
        top = np.take_along_axis(top, np.argsort(-np.take_along_axis(s, top, 1), axis=1, kind="stable"), 1)
        hc = np.cumsum(G["W"][days[a:b, None], top], 1)
        ec = np.cumsum(G["Py"][y[a:b, None], top], 1) * G["nwin"][days[a:b], None]
        H[a:b, :len(KS)] = hc[:, np.array(KS) - 1]
        E[a:b, :len(KS)] = ec[:, np.array(KS) - 1]
    rank = np.argsort(np.argsort(-(C - np.arange(10) * 1e-9), axis=2), axis=2)     # 0 = hottest digit
    for j, m in enumerate(MS):
        ok = (rank < m)                                                     # (n, 4, 10)
        sel = ok[:, 0][:, DIG[:, 0]] & ok[:, 1][:, DIG[:, 1]] & ok[:, 2][:, DIG[:, 2]] & ok[:, 3][:, DIG[:, 3]]
        H[:, len(KS) + j] = (G["W"][days] & sel).sum(1)
        E[:, len(KS) + j] = (G["Py"][y] * sel).sum(1) * G["nwin"][days]
    return days, H, E


def zcol(H, E, m):
    o, e = H[m].sum(0), E[m].sum(0)
    return (o - e) / np.sqrt(e), o, e


def summary(cells):
    days, H, E = curves(cells)
    late = r.G["yr"][days] >= SPLIT
    zb, ob, eb = zcol(H, E, ~late)
    za, oa, ea = zcol(H, E, late)
    return {"zb": zb, "za": za, "ob": ob, "eb": eb, "oa": oa, "ea": ea, "nb": int((~late).sum()), "na": int(late.sum())}


def task(shift):
    s = summary(r.cells_of(LEAD, shift))
    kb = int(np.argmax(s["zb"][:len(KS)]))
    return float(s["za"][kb]), float(s["za"].max()), float(s["zb"].max())


def main():
    r.setup()
    r.G["yr"] = np.array([int(d[:4]) for d in r.G["D"].dates])
    labels = [f"top {k}" for k in KS] + [f"grid {m}^4={m ** 4}" for m in MS]
    res = {"lead": summary(r.cells_of(LEAD)), "no parameter": summary(np.zeros(r.G["nd"], np.int64))}
    out = {}
    for name, s in res.items():
        print(f"\n{name}: hits vs expected per {s['nb']} draw days before {SPLIT} | {s['na']} draw days {SPLIT}-2026")
        rows = []
        for i, lab in enumerate(labels):
            print(f"   {lab:<15} {s['ob'][i]:>6.0f}/{s['eb'][i]:>8.1f} (x{s['ob'][i] / s['eb'][i]:.3f}, z {s['zb'][i]:+.2f}) | "
                  f"{s['oa'][i]:>6.0f}/{s['ea'][i]:>8.1f} (x{s['oa'][i] / s['ea'][i]:.3f}, z {s['za'][i]:+.2f}) | "
                  f"hits per day after {s['oa'][i] / s['na']:.3f}")
            rows.append({"picks": lab, "hits_before": s["ob"][i], "exp_before": s["eb"][i], "z_before": s["zb"][i],
                         "hits_after": s["oa"][i], "exp_after": s["ea"][i], "z_after": s["za"][i],
                         "hits_per_day_after": s["oa"][i] / s["na"]})
        out[name] = rows
    s = res["lead"]
    kb = int(np.argmax(s["zb"][:len(KS)]))
    real = float(s["za"][kb])
    rng = np.random.default_rng(11)
    shifts = [int(x) for x in rng.integers(170, r.G["nd"] - 170, 100)]
    with mp.get_context("fork").Pool(4) as pool:
        sims = np.array(pool.map(task, shifts))
    print(f"\nRanked K chosen on draw days before {SPLIT}: {labels[kb]} (z before {s['zb'][kb]:+.2f}) -> "
          f"after {SPLIT}: x{s['oa'][kb] / s['ea'][kb]:.3f}, z {real:+.2f}")
    print(f"   100 shifted calendars doing the same (choose own best K before {SPLIT}, score after): "
          f"mean z {sims[:, 0].mean():+.2f}, sd {sims[:, 0].std():.2f}, {int((sims[:, 0] >= real).sum())}/100 as high")
    print(f"   best K after {SPLIT} picked with hindsight: real z {s['za'].max():+.2f} vs shifted "
          f"{sims[:, 1].mean():+.2f} ({int((sims[:, 1] >= s['za'].max()).sum())}/100 as high)")
    out["chosen_k"] = {"picks": labels[kb], "z_after": real, "shift_mean": float(sims[:, 0].mean()),
                       "shift_sd": float(sims[:, 0].std()), "shifts_as_high": int((sims[:, 0] >= real).sum()),
                       "hindsight_best_z_after": float(s["za"].max()),
                       "hindsight_shifts_as_high": int((sims[:, 1] >= s["za"].max()).sum())}
    json.dump(out, open(os.path.join(r.ROOT, "analysis", "s12_lead_k_results.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
