#!/usr/bin/env python3
"""Recurrence test (recurrence_test.py / recurrence_pairs.py) for Straight,
Reverse and i-Box matches, over all 78 single parameters and 3,003 pairs.

When a parameter value (or pair of values) comes back on a later draw day,
does that day repeat a winner from the earlier day more often than chance as
  Straight  the same number (1234 -> 1234)
  Reverse   the digits reversed (1234 -> 4321; palindromes excluded)
  i-Box     any arrangement of the same digits (1234 -> 3412, incl. straight)?
Versions: (a) all pairs of same-value draw days, (b) each day with the NEXT
same-value day. Chance level per day pair = n_i * n_j * s * c(gap), where s is
the chance two random numbers match under that rule and c(gap) is the observed
/ expected match rate over ALL pairs of draw days that far apart.

Because many tests share parameters (and i-Box counts are lumpy), the whole
scan is repeated on circularly shifted parameter calendars (one shift for all
parameters, at least about a year of draw days): a real effect must beat the
best z and the number of z > 2 the scan reaches on those meaningless calendars.

Run from the repo root:  python3 analysis/recurrence_perm.py [n_shifts]
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
TYPES = ("straight", "reverse", "ibox")
G = {}
POP = np.array([bin(i).count("1") for i in range(256)], np.uint8)


def norm_sf(z):
    return 0.5 * math.erfc(z / math.sqrt(2))


def autocorr(M, L, T):
    F = np.fft.rfft(M, L, axis=-1)
    return np.fft.irfft(F * np.conj(F), L, axis=-1)[..., :T]


def setup():
    D = dm.Data()
    nd = len(D.dates)
    day = np.array([(dt.date.fromisoformat(d) - dt.date(1985, 1, 1)).days for d in D.dates])
    T = int(day.max()) + 1
    L = 1 << int(np.ceil(np.log2(2 * T)))
    key = np.unique(D.rd.astype(np.int64) * 10000 + D.rn)
    wd, wn = key // 10000, key % 10000
    nwin = np.bincount(wd, minlength=nd).astype(float)
    num = np.arange(10000)
    rev = np.array([int(f"{n:04d}"[::-1]) for n in num])
    box_lab = np.unique(np.sort(am.DIG, axis=1) @ [1000, 100, 10, 1],
                        return_inverse=True)[1]
    box_size = np.bincount(box_lab)
    sr_lab = np.unique(np.minimum(num, rev), return_inverse=True)[1]
    sr_size = np.bincount(sr_lab)
    # packed winner sets (straight) and reversed sets without palindromes (reverse)
    W = np.zeros((nd, 10000), bool)
    W[wd, wn] = True
    WR = np.zeros((nd, 10000), bool)
    keep = rev[wn] != wn
    WR[wd[keep], rev[wn][keep]] = True
    Cb = np.zeros((nd, len(box_size)), np.float32)
    np.add.at(Cb, (wd, box_lab[wn]), 1)
    # (day, key, count) entries per match rule; straight-or-reverse is used to get reverse = SR - straight
    ent = {}
    for t, lab, K in (("straight", num, 10000), ("sr", sr_lab, len(sr_size)), ("ibox", box_lab, len(box_size))):
        u, c = np.unique(wd * K + lab[wn], return_counts=True)
        ent[t] = (u // K, u % K, c.astype(float), K)
    s = {"straight": 1e-4, "sr": float((sr_size.astype(float) ** 2).sum() / 1e8),
         "ibox": float((box_size.astype(float) ** 2).sum() / 1e8)}
    # gap correction per rule
    sz = np.zeros(T)
    sz[day] = nwin
    size_g = autocorr(sz, L, T)
    edges = np.unique(np.round(np.logspace(0, np.log10(T), 60)).astype(int))
    gb = np.searchsorted(edges, np.arange(T), side="right")
    cg = {}
    for t, (ed, ek, ec, K) in ent.items():
        order = np.argsort(ek, kind="stable")
        ek_s, ed_s, ec_s = ek[order], ed[order], ec[order]
        bounds = np.r_[0, np.flatnonzero(np.diff(ek_s)) + 1, len(ek_s)]
        groups = [(day[ed_s[a:b]], ec_s[a:b]) for a, b in zip(bounds[:-1], bounds[1:]) if b - a >= 2]
        coin = np.zeros(T)
        for s0 in range(0, len(groups), 512):
            M = np.zeros((len(groups[s0:s0 + 512]), T))
            for i, (dd, cc) in enumerate(groups[s0:s0 + 512]):
                M[i, dd] = cc
            coin += np.rint(autocorr(M, L, T).sum(0))
        cb = np.bincount(gb[1:], weights=coin[1:], minlength=len(edges) + 2)
        sb = np.bincount(gb[1:], weights=s[t] * size_g[1:], minlength=len(edges) + 2)
        c = np.where(sb > 0, cb / np.maximum(sb, 1e-12), 1.0)[gb]
        c[0] = 0
        cg[t] = c
        print(f"{t}: matches between any two draw days x{coin[1:].sum() / (s[t] * size_g[1:].sum()):.3f} of size-based chance",
              flush=True)
    G.update(D=D, nd=nd, day=day, T=T, L=L, nwin=nwin, Wp=np.packbits(W, axis=1), WRp=np.packbits(WR, axis=1),
             Cb=Cb, ent=ent, s=s, cg=cg)


def cells_of(test, shift=0):
    D = G["D"]
    c = np.zeros(G["nd"], np.int64)
    for f in test:
        c = c * (int(D.codes[f].max()) + 1) + D.codes[f]
    return np.roll(c, shift) if shift else c


def evaluate(cells):
    """{rule: (obs_a, exp_a, obs_b, exp_b)}"""
    day, T, L, nwin, cg, s, ent = G["day"], G["T"], G["L"], G["nwin"], G["cg"], G["s"], G["ent"]
    _, cc = np.unique(cells, return_inverse=True)
    obs_a = {}
    for t, (ed, ek, ec, K) in ent.items():
        idx = cc[ed].astype(np.int64) * K + ek
        if t == "straight":
            k = np.bincount(idx)
            obs_a[t] = float((k * (k - 1) / 2).sum())
        else:
            s1 = np.bincount(idx, weights=ec)
            s2 = np.bincount(idx, weights=ec * ec)
            obs_a[t] = float((s1 * s1 - s2).sum() / 2)
    base_a = {t: 0.0 for t in cg}
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
            w = nwin[gi] * nwin[gj]
            g = np.abs(day[gj] - day[gi])
            for t in cg:
                base_a[t] += float((w * cg[t][g]).sum())
        else:
            ind = np.zeros(T)
            ind[day[idx]] = nwin[idx]
            sv = autocorr(ind, L, T)[1:]
            for t in cg:
                base_a[t] += float((sv * cg[t][1:]).sum())
    same = sc[1:] == sc[:-1]
    i, j = order[1:][same], order[:-1][same]
    Wp, WRp, Cb = G["Wp"], G["WRp"], G["Cb"]
    ob = {"straight": float(POP[Wp[i] & Wp[j]].sum()),
          "reverse": float(POP[Wp[i] & WRp[j]].sum()),
          "ibox": float((Cb[i] * Cb[j]).sum())}
    w = nwin[i] * nwin[j]
    g = np.abs(day[i] - day[j])
    eb = {t: float((w * cg[t][g]).sum() * s[t]) for t in cg}
    ea = {t: base_a[t] * s[t] for t in cg}
    return {"straight": (obs_a["straight"], ea["straight"], ob["straight"], eb["straight"]),
            "reverse": (obs_a["sr"] - obs_a["straight"], ea["sr"] - ea["straight"], ob["reverse"], eb["sr"] - eb["straight"]),
            "ibox": (obs_a["ibox"], ea["ibox"], ob["ibox"], eb["ibox"])}


def zscores(r):
    return [(o - e) / math.sqrt(e) if e > 0 else 0.0 for t in TYPES for o, e in (r[t][:2], r[t][2:])]


def task(args):
    test, shift = args
    r = evaluate(cells_of(test, shift))
    return test, r


def scan(pool, tests, shift):
    res = pool.map(task, [(t, shift) for t in tests], chunksize=8)
    return res


def main():
    n_shifts = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    t0 = time.time()
    setup()
    tests = [(f,) for f in FACT] + list(itertools.combinations(FACT, 2))
    n = len(tests)
    cols = [f"{t}_{v}" for t in TYPES for v in "ab"]
    with mp.get_context("fork").Pool(4) as pool:
        real = scan(pool, tests, 0)
        print(f"{n} tests evaluated ({time.time() - t0:.0f}s)", flush=True)
        Z = np.array([zscores(r) for _, r in real])
        rng = np.random.default_rng(2)
        null = []
        for k in range(n_shifts):
            sh = int(rng.integers(170, G["nd"] - 170))
            Zs = np.array([zscores(r) for _, r in scan(pool, tests, sh)])
            null.append({"shift": sh, "max_z": Zs.max(0).tolist(), "z_gt_2": (Zs > 2).sum(0).tolist()})
            print(f"shift {k + 1}/{n_shifts} ({sh}) best z " + " ".join(f"{c} {v:+.2f}" for c, v in zip(cols, Zs.max(0))),
                  flush=True)
    report = {"tests": n, "n_shifts": n_shifts, "null": null, "by_rule": {}}
    names = [" x ".join(t) for t, _ in real]
    for ci, col in enumerate(cols):
        t, v = col.rsplit("_", 1)
        nm = np.array([x["max_z"][ci] for x in null])
        ng = np.array([x["z_gt_2"][ci] for x in null])
        top = np.argsort(-Z[:, ci])[:8]
        label = {"a": "any later same-value day", "b": "NEXT same-value day"}[v]
        print(f"\n{t.upper()} - ({v}) {label}: z > 2 for {int((Z[:, ci] > 2).sum())} tests "
              f"(shifted calendars {ng.mean():.0f}, range {ng.min()}-{ng.max()}); best z {Z[top[0], ci]:+.2f} "
              f"(shifted best {nm.mean():+.2f}, range {nm.min():+.2f} to {nm.max():+.2f}; "
              f"{int((nm >= Z[top[0], ci]).sum())}/{len(nm)} shifts as high)")
        rows = []
        for q in top:
            o, e = real[q][1][t][:2] if v == "a" else real[q][1][t][2:]
            p = min(1.0, n * norm_sf(Z[q, ci]))
            beat = int((nm >= Z[q, ci]).sum())
            print(f"   {names[q]:<44} {o:>9.0f} vs {e:>10.1f} expected (x{o / e:.3f}, z={Z[q, ci]:+.2f}, "
                  f"corrected p={p:.2f}, shifted scans' best >= this: {beat}/{len(nm)})")
            rows.append({"test": names[q], "obs": o, "exp": e, "ratio": o / e, "z": float(Z[q, ci]), "p_bonf": p,
                         "shift_scans_as_high": beat})
        report["by_rule"][col] = {"z_gt_2": int((Z[:, ci] > 2).sum()), "null_z_gt_2": ng.tolist(),
                                  "null_max_z": nm.tolist(), "top": rows}
    json.dump(report, open(os.path.join(ROOT, "analysis", "recurrence_perm_results.json"), "w"), indent=1)
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
