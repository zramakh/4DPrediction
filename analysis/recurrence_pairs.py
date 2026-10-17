#!/usr/bin/env python3
"""recurrence_test.py for all 3,003 PAIRS of Vedic / Chinese parameters.

The pair value is the combination (f1 = v1 and f2 = v2). For each pair:
  (a) all pairs of draw days with the same combined value
  (b) each draw day with the NEXT draw day that has the same combined value
Repeats = numbers that won (any prize, any operator) on both days. Chance
level per day pair = n_i * n_j / 10000 * c(gap), as in recurrence_test.py.
The top pairs are re-checked with circular time shifts of the parameter
calendar (offsets of at least a year), which keeps all natural rhythms.

Run from the repo root:  python3 analysis/recurrence_pairs.py
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
import astro_model as am  # noqa: E402
import digit_models as dm  # noqa: E402

ROOT = am.ROOT
FACT = am.VEDIC + am.CHINESE
G = {}
POP = np.array([bin(i).count("1") for i in range(256)], np.uint8)


def norm_sf(z):
    return 0.5 * math.erfc(z / math.sqrt(2))


def setup():
    D = dm.Data()
    nd = len(D.dates)
    day = np.array([(dt.date.fromisoformat(d) - dt.date(1985, 1, 1)).days for d in D.dates])
    T = int(day.max()) + 1
    L = 1 << int(np.ceil(np.log2(2 * T)))
    key = np.unique(D.rd.astype(np.int64) * 10000 + D.rn)
    wd, wn = key // 10000, key % 10000
    nwin = np.bincount(wd, minlength=nd).astype(float)
    W = np.zeros((nd, 10000), bool)
    W[wd, wn] = True
    Wp = np.packbits(W, axis=1)
    # gap correction c(g), as in recurrence_test.py
    sz = np.zeros(T)
    sz[day] = nwin
    Fs = np.fft.rfft(sz, L)
    size_g = np.fft.irfft(Fs * np.conj(Fs), L)[:T] / 10000
    coin_g = np.zeros(T)
    order = np.argsort(wn, kind="stable")
    wn_s, wd_s = wn[order], wd[order]
    bounds = np.r_[0, np.flatnonzero(np.diff(wn_s)) + 1, len(wn_s)]
    groups = [day[wd_s[a:b]] for a, b in zip(bounds[:-1], bounds[1:]) if b - a >= 2]
    for s0 in range(0, len(groups), 512):
        M = np.zeros((len(groups[s0:s0 + 512]), T))
        for i, dd in enumerate(groups[s0:s0 + 512]):
            M[i, dd] = 1
        F = np.fft.rfft(M, L, axis=1)
        coin_g += np.rint(np.fft.irfft((F * np.conj(F)).sum(0), L)[:T])
    edges = np.unique(np.round(np.logspace(0, np.log10(T), 60)).astype(int))
    gb = np.searchsorted(edges, np.arange(T), side="right")
    cb = np.bincount(gb[1:], weights=coin_g[1:], minlength=len(edges) + 2)
    sb = np.bincount(gb[1:], weights=size_g[1:], minlength=len(edges) + 2)
    cg = np.where(sb > 0, cb / np.maximum(sb, 1e-12), 1.0)[gb]
    cg[0] = 0
    G.update(D=D, nd=nd, day=day, T=T, L=L, wd=wd, wn=wn, nwin=nwin, Wp=Wp, cg=cg)


def joint(f1, f2, shift=0):
    D = G["D"]
    c1 = D.codes[f1]
    c2 = D.codes[f2]
    c = c1.astype(np.int64) * (int(c2.max()) + 1) + c2
    return np.roll(c, shift) if shift else c


def overlap(i, j):
    return POP[G["Wp"][i] & G["Wp"][j]].sum(1).astype(float)


def evaluate(cells):
    """(obs_a, exp_a, obs_b, exp_b) for one array of per-date cell codes."""
    day, T, L, wd, wn, nwin, cg = G["day"], G["T"], G["L"], G["wd"], G["wn"], G["nwin"], G["cg"]
    _, cc = np.unique(cells, return_inverse=True)
    k = np.bincount(cc[wd].astype(np.int64) * 10000 + wn)
    obs_a = float((k * (k - 1) / 2).sum())
    exp_a = 0.0
    order = np.lexsort((np.arange(len(cc)), cc))
    sc = cc[order]
    bounds = np.r_[0, np.flatnonzero(np.diff(sc)) + 1, len(sc)]
    for a, b in zip(bounds[:-1], bounds[1:]):
        m = b - a
        if m < 2:
            continue
        idx = order[a:b]
        if m <= 80:
            ii, jj = np.triu_indices(m, 1)
            gi, gj = idx[ii], idx[jj]
            exp_a += float((nwin[gi] * nwin[gj] * cg[np.abs(day[gj] - day[gi])]).sum() / 10000)
        else:
            ind = np.zeros(T)
            ind[day[idx]] = nwin[idx]
            Fi = np.fft.rfft(ind, L)
            exp_a += float((np.fft.irfft(Fi * np.conj(Fi), L)[1:T] * cg[1:]).sum() / 10000)
    # (b) next same-value day
    same = sc[1:] == sc[:-1]
    i = order[1:][same]
    j = order[:-1][same]
    obs_b = float(overlap(i, j).sum())
    exp_b = float((nwin[i] * nwin[j] * cg[np.abs(day[i] - day[j])]).sum() / 10000)
    return obs_a, exp_a, obs_b, exp_b


def task(pair):
    f1, f2 = pair
    oa, ea, ob, eb = evaluate(joint(f1, f2))
    return {"pair": f"{f1} x {f2}", "a_obs": oa, "a_exp": ea, "a_ratio": oa / ea if ea else None,
            "a_z": (oa - ea) / math.sqrt(ea) if ea else 0.0,
            "b_obs": ob, "b_exp": eb, "b_ratio": ob / eb if eb else None,
            "b_z": (ob - eb) / math.sqrt(eb) if eb else 0.0}


def shift_check(pair, n=40, seed=0):
    f1, f2 = pair.split(" x ")
    rng = np.random.default_rng(seed)
    real = evaluate(joint(f1, f2))
    nd = G["nd"]
    sims = []
    for _ in range(n):
        s = int(rng.integers(170, nd - 170))                   # about 1 year of draw days or more
        sims.append(evaluate(joint(f1, f2, s)))
    sims = np.array(sims)
    out = {}
    for name, (oi, ei) in {"a": (0, 1), "b": (2, 3)}.items():
        ex_real = real[oi] - real[ei]
        ex_sim = sims[:, oi] - sims[:, ei]
        out[name] = {"excess": ex_real, "shift_mean": float(ex_sim.mean()), "shift_sd": float(ex_sim.std(ddof=1)),
                     "z_vs_shifts": float((ex_real - ex_sim.mean()) / ex_sim.std(ddof=1)),
                     "share_shifts_as_high": float(np.mean(ex_sim >= ex_real))}
    return out


def main():
    t0 = time.time()
    setup()
    pairs = list(itertools.combinations(FACT, 2))
    with mp.get_context("fork").Pool(4) as pool:
        res = list(pool.imap_unordered(task, pairs, chunksize=16))
    print(f"{len(res)} pairs evaluated ({time.time() - t0:.0f}s)", flush=True)
    n = len(res)
    for x in res:
        x["a_p_bonf"] = min(1.0, n * norm_sf(x["a_z"]))
        x["b_p_bonf"] = min(1.0, n * norm_sf(x["b_z"]))
    report = {"pairs": n}
    for label, k in (("(a) any later day with the same pair of values", "a"),
                     ("(b) the NEXT day with the same pair of values", "b")):
        zs = np.array([x[f"{k}_z"] for x in res])
        print(f"\n{label}: z > 2 for {int((zs > 2).sum())} (about {0.0228 * n:.0f} by chance), "
              f"z > 3 for {int((zs > 3).sum())} (about {0.00135 * n:.0f}), z < -2 for {int((zs < -2).sum())}")
        top = sorted(res, key=lambda x: -x[f"{k}_z"])[:10]
        for x in top:
            print(f"   {x['pair']:<44} {x[f'{k}_obs']:>9.0f} repeats vs {x[f'{k}_exp']:>10.1f} expected "
                  f"(x{x[f'{k}_ratio']:.3f}, z={x[f'{k}_z']:+.2f}, corrected p={x[f'{k}_p_bonf']:.2f})")
        report[k] = {"z_gt_2": int((zs > 2).sum()), "z_gt_3": int((zs > 3).sum()), "top": top}
    print("\nTime-shift check of the top 3 pairs in each version (40 shifts of the parameter calendar):", flush=True)
    report["shift_checks"] = {}
    for k in ("a", "b"):
        for x in report[k]["top"][:3]:
            sc = shift_check(x["pair"])
            report["shift_checks"][f"{k}: {x['pair']}"] = sc
            s = sc[k]
            print(f"   ({k}) {x['pair']:<44} excess {s['excess']:+.1f} vs shifted {s['shift_mean']:+.1f} "
                  f"+/- {s['shift_sd']:.1f} -> z {s['z_vs_shifts']:+.2f}; {s['share_shifts_as_high']:.0%} of shifts as high",
                  flush=True)
    json.dump(report, open(os.path.join(ROOT, "analysis", "recurrence_pairs_results.json"), "w"), indent=1, default=float)
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
