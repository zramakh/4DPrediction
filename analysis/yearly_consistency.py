#!/usr/bin/env python3
"""Year-by-year consistency of the forward picks, pooled and per operator.

Candidates = every test chosen on 1985-2011 draws only (the top 5 per column of
analysis C: S1, S2, rank pairs; (a) / (b); Straight / Reverse / i-Box):
  pooled      recurrence_s12_forward_results.json + recurrence_rankpairs_results.json
  operator    per_operator_<op>_results.json (picks built from and scored on that operator)
For each candidate, with picks rebuilt before every draw from earlier results,
count the years 2012-2026 in which it beat chance (hits > expected). Because the
candidates were chosen before 2012, these years are out of sample.
Chance: the same candidates on 20 circularly shifted parameter calendars (best
count among all candidates, and how many candidates reach 12+ good years);
the 5 most consistent candidates also get 50 shifts each and a no-parameter
control (same picks without any parameter).

Run from the repo root:  python3 analysis/yearly_consistency.py pooled | Magnum | "Sports Toto" | "Da Ma Cai"
"""

import json
import multiprocessing as mp
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am  # noqa: E402
import per_operator as po  # noqa: E402

YEARS = list(range(2012, 2027))
G = {}


def parse_kind(p):
    if p in ("S1", "S2"):
        return p
    a, b = p.split("+")
    return (int(a) - 1, int(b) - 1)


def candidates(which):
    out = []
    if which == "pooled":
        f = json.load(open(os.path.join(am.ROOT, "analysis", "recurrence_s12_forward_results.json")))
        for col, rows in f["columns"].items():
            s, v, rule = col.split("_")
            out += [(tuple(x["test"].split(" x ")), s, v, rule) for x in rows]
        f = json.load(open(os.path.join(am.ROOT, "analysis", "recurrence_rankpairs_results.json")))
        for c in f["columns"]:
            out += [(tuple(x["test"].split(" x ")), c["ranks"], c["version"], c["rule"]) for x in c["forward_tests"]]
    else:
        tag = which.lower().replace(" ", "")
        f = json.load(open(os.path.join(am.ROOT, "analysis", f"per_operator_{tag}_results.json")))
        for c in f["C"]:
            out += [(tuple(x["test"].split(" x ")), c["picks"], c["version"], c["rule"]) for x in c["forward_tests"]]
    return list(dict.fromkeys(out))


def series(test, p, v, rule, shift=0):
    """Hits and chance per year 2012-2026 for one candidate."""
    r, rk, rp = G["r"], G["rk"], G["rp"]
    g = r.G
    cells = r.cells_of(test, shift) if test else np.zeros(g["nd"], np.int64)
    order = np.lexsort((np.arange(len(cells)), cells))
    sc = cells[order]
    newgrp = np.r_[True, sc[1:] != sc[:-1]]
    hp = ~newgrp
    days = order[hp]
    if v == "a":
        cs = np.cumsum(g["dday"][order], 0)
        st = np.maximum.accumulate(np.where(newgrp, np.arange(len(sc)), 0))
        base = np.where((st > 0)[:, None, None], cs[np.maximum(st - 1, 0)], 0)
        C = (cs - g["dday"][order] - base)[hp]
    else:
        C = g["dday"][order[:-1]][hp[1:]]
    kind = parse_kind(p)
    if kind == "S1":
        P = r.picks(C, True)
    elif kind == "S2":
        P = r.picks(C, False)
    else:
        P = rp.pair_picks(np.argsort(-C, axis=2, kind="stable"), kind)
    sd = rk.score_days(days, P)
    h, e = sd[rule][0][:, -1].astype(float), sd[rule][1][:, -1]
    y = g["yr"][days]
    H = np.array([h[y == Y].sum() for Y in YEARS])
    E = np.array([e[y == Y].sum() for Y in YEARS])
    return H, E


def good_years(H, E):
    return int(((H > E) & (E > 0)).sum())


def task(args):
    cand, shift = args
    H, E = series(*cand, shift=shift)
    return good_years(H, E), H.sum(), E.sum(), H.tolist(), E.tolist()


def main():
    which = sys.argv[1]
    if which != "pooled":
        po.restrict_to(am.OPS.index(which))
    import recurrence_rankpairs as rp
    import recurrence_s12 as r
    import recurrence_s12_k as rk
    G.update(r=r, rk=rk, rp=rp)
    r.setup()
    r.G["yr"] = np.array([int(d[:4]) for d in r.G["D"].dates])
    cands = candidates(which)
    rng = np.random.default_rng(71)
    shifts = [int(s) for s in rng.integers(170, r.G["nd"] - 170, 20)]
    with mp.get_context("fork").Pool(4) as pool:
        real = pool.map(task, [(c, 0) for c in cands], chunksize=4)
        null = [pool.map(task, [(c, s) for c in cands], chunksize=4) for s in shifts]
        order = sorted(range(len(cands)), key=lambda i: (-real[i][0], -real[i][1] / max(real[i][2], 1e-9)))
        top = order[:5]
        sh50 = [int(s) for s in rng.integers(170, r.G["nd"] - 170, 50)]
        per = {i: pool.map(task, [(cands[i], s) for s in sh50], chunksize=4) for i in top}
    gy = np.array([x[0] for x in real])
    ngy = np.array([[x[0] for x in n] for n in null])
    print(f"=== {which}: {len(cands)} candidates chosen before 2012; good years out of {len(YEARS)} (2012-2026) ===")
    print(f"   average good years: real {gy.mean():.2f} | shifted calendars {ngy.mean():.2f}")
    print(f"   candidates with 12+ good years: real {int((gy >= 12).sum())} | shifted {np.mean((ngy >= 12).sum(1)):.2f} "
          f"(range {(ngy >= 12).sum(1).min()}-{(ngy >= 12).sum(1).max()})")
    print(f"   best count: real {gy.max()} | shifted best {ngy.max(1).mean():.1f} (range {ngy.max(1).min()}-{ngy.max(1).max()}; "
          f"{int((ngy.max(1) >= gy.max()).sum())}/{len(shifts)} as high)")
    out = {"which": which, "n_candidates": len(cands), "real_mean": float(gy.mean()), "null_mean": float(ngy.mean()),
           "real_12plus": int((gy >= 12).sum()), "null_12plus": (ngy >= 12).sum(1).tolist(),
           "real_best": int(gy.max()), "null_best": ngy.max(1).tolist(), "top": []}
    print("   most consistent candidates:")
    for i in top:
        test, p, v, rule = cands[i]
        g, h, e, H, E = real[i]
        s50 = np.array([x[0] for x in per[i]])
        Hn, En = series(None, p, v, rule)
        nop = good_years(Hn, En)
        yrs = " ".join(f"{Y % 100:02d}:{a / b:.2f}" for Y, a, b in zip(YEARS, H, E) if b > 0)
        print(f"   {' x '.join(test)} | {p} ({v}) {rule} | {g}/15 years, x{h / e:.3f} | 50 shifts: mean {s50.mean():.1f}, "
              f">= {g} in {int((s50 >= g).sum())}/50 | no parameter {nop}/15 (x{Hn.sum() / En.sum():.3f})")
        print(f"      {yrs}")
        out["top"].append({"test": " x ".join(test), "method": f"{p} ({v}) {rule}", "good_years": g, "ratio": h / e,
                           "shift50_mean": float(s50.mean()), "shift50_as_high": int((s50 >= g).sum()),
                           "no_param_good_years": nop, "per_year": {str(Y): [a, b] for Y, a, b in zip(YEARS, H, E)}})
    tag = which.lower().replace(" ", "")
    json.dump(out, open(os.path.join(am.ROOT, "analysis", f"yearly_consistency_{tag}.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
