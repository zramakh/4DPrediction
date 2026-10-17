#!/usr/bin/env python3
"""When a Vedic / Chinese parameter value comes back on a later draw day, does
that day repeat a 4D number from the earlier day more often than chance?

For each of the 78 parameters, two versions:
  (a) all pairs of draw days with the same value
  (b) each draw day paired with the NEXT draw day that has the same value
A "repeat" = a number that won (any prize, any of the three operators) on
both days. The chance level is time-matched: r(g) = average number of shared
winners between any two draw days g days apart, so slow parameters (whose
same-value days are close together in time) are compared fairly.
z = (observed - expected) / sqrt(expected); Bonferroni over 78 parameters.

Run from the repo root:  python3 analysis/recurrence_test.py
"""

import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am  # noqa: E402
import digit_models as dm  # noqa: E402

ROOT = am.ROOT
FACT = am.VEDIC + am.CHINESE


def norm_sf(z):
    return 0.5 * math.erfc(z / math.sqrt(2))


def main():
    D = dm.Data()
    nd = len(D.dates)
    import datetime as dt
    day = np.array([(dt.date.fromisoformat(d) - dt.date(1985, 1, 1)).days for d in D.dates])
    T = int(day.max()) + 1
    L = 1 << int(np.ceil(np.log2(2 * T)))
    # winners per date (union over operators, each number once per date)
    key = np.unique(D.rd.astype(np.int64) * 10000 + D.rn)
    wd, wn = key // 10000, key % 10000
    # ---- chance level: E[shared] for two draw days = n_i * n_j / 10000 * c(g), where n = winners that day and
    #      c(g) = observed / size-expected over ALL pairs of draw days g days apart (log-binned gaps)
    nwin = np.bincount(wd, minlength=nd).astype(float)
    sz = np.zeros(T)
    sz[day] = nwin
    Fs = np.fft.rfft(sz, L)
    size_g = np.fft.irfft(Fs * np.conj(Fs), L)[:T] / 10000          # sum of n_i n_j / 10000 at gap g
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
    print(f"shared numbers vs size-based chance, over all pairs of draw days: "
          f"x{coin_g[1:].sum() / size_g[1:].sum():.3f} (1-7 days apart x{coin_g[1:8].sum() / size_g[1:8].sum():.3f})", flush=True)

    res = []
    win_sets = {}
    for d, n in zip(wd, wn):
        win_sets.setdefault(int(d), set()).add(int(n))
    for f in FACT:
        c = D.codes[f]
        # (a) all same-value pairs: observed via counts per (value, number); expected via per-value autocorrelation
        k = np.bincount(c[wd].astype(np.int64) * 10000 + wn)
        obs_a = float((k * (k - 1) / 2).sum())
        exp_a = 0.0
        for v in np.unique(c):
            ind = np.zeros(T)
            ind[day[c == v]] = nwin[c == v]
            Fi = np.fft.rfft(ind, L)
            sv = np.fft.irfft(Fi * np.conj(Fi), L)[:T] / 10000      # each unordered pair once for g >= 1
            exp_a += float((sv[1:] * cg[1:]).sum())
        # (b) next same-value draw day
        obs_b = exp_b = 0.0
        last = {}
        for i in range(nd):
            v = c[i]
            if v in last:
                j = last[v]
                obs_b += len(win_sets.get(i, set()) & win_sets.get(j, set()))
                exp_b += nwin[i] * nwin[j] / 10000 * cg[day[i] - day[j]]
            last[v] = i
        za = (obs_a - exp_a) / math.sqrt(exp_a)
        zb = (obs_b - exp_b) / math.sqrt(exp_b)
        res.append({"parameter": f, "all_pairs_obs": obs_a, "all_pairs_exp": exp_a, "all_pairs_ratio": obs_a / exp_a,
                    "all_pairs_z": za, "next_obs": obs_b, "next_exp": exp_b, "next_ratio": obs_b / exp_b, "next_z": zb})
    for x in res:
        x["all_pairs_p_bonf"] = min(1.0, 78 * norm_sf(x["all_pairs_z"]))
        x["next_p_bonf"] = min(1.0, 78 * norm_sf(x["next_z"]))
    for label, kz in (("(a) any later day with the same value", "all_pairs"), ("(b) the NEXT day with the same value", "next")):
        zs = np.array([x[f"{kz}_z"] for x in res])
        print(f"\n{label}: z > 2 for {int((zs > 2).sum())} of 78 (about 1.8 by chance), z < -2 for {int((zs < -2).sum())}")
        for x in sorted(res, key=lambda x: -x[f"{kz}_z"])[:8]:
            print(f"   {x['parameter']:<22} {x[f'{kz}_obs']:>9.0f} repeats vs {x[f'{kz}_exp']:>9.1f} expected "
                  f"(x{x[f'{kz}_ratio']:.3f}, z={x[f'{kz}_z']:+.2f}, corrected p={x[f'{kz}_p_bonf']:.2f})")
    # per-value detail for the most significant parameter (next-occurrence version)
    top = max(res, key=lambda x: x["next_z"])
    f = top["parameter"]
    c = D.codes[f]
    per = {}
    last = {}
    for i in range(nd):
        v = int(c[i])
        if v in last:
            j = last[v]
            o = len(win_sets.get(i, set()) & win_sets.get(j, set()))
            e = nwin[i] * nwin[j] / 10000 * cg[day[i] - day[j]]
            a = per.setdefault(v, [0, 0.0, []])
            a[0] += o
            a[1] += e
            if o:
                a[2] += [f"{D.dates[j]}->{D.dates[i]}: " + ",".join(f"{n:04d}" for n in sorted(win_sets[i] & win_sets[j]))]
        last[v] = i
    print(f"\nMost significant (next-occurrence): {f}. By value:")
    for v, (o, e, ex) in sorted(per.items(), key=lambda kv: -(kv[1][0] - kv[1][1]) / math.sqrt(max(kv[1][1], 1e-9)))[:6]:
        print(f"   {f} = {D.labels[f][v]:<18} {o} repeats vs {e:.1f} expected (z={(o - e) / math.sqrt(e):+.2f}); latest: {ex[-2:]}")
    json.dump({"results": res, "top_parameter": f,
               "top_by_value": {D.labels[f][v]: {"repeats": o, "expected": e, "examples": ex[-10:]}
                                for v, (o, e, ex) in per.items()}},
              open(os.path.join(ROOT, "analysis", "recurrence_results.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
