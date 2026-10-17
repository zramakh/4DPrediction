#!/usr/bin/env python3
"""Do some Vedic / Chinese parameters promote wins and others suppress them,
and do pairs of parameters predict better than single ones?

Stage A (signed singles): every parameter x kind (468 terms) is scored on
  2012-2017 (counts from draws before 2012) with a weight that may be positive
  ("promotes": its hot numbers win more) or negative ("suppresses": its hot
  numbers win less).
Stage B (additive pairs): every pair of the 30 strongest signed singles,
  score = w1 * L1 + w2 * L2 with both weights fitted (so one can promote while
  the other suppresses).
Stage C (joint pairs): for all 3,003 parameter pairs, the cell "f1 = v1 AND
  f2 = v2" is treated as one condition (i-Box and digit kinds), so a value of
  one parameter can boost or cancel a value of the other.

Validation score = log-likelihood gain of the real winners, using the
second-order expansion  gain(w) ~ w * A - w^2 * B / 2  (A = sum over winners
of t - mean t, B = sum of n_winners * var t), maximised over the weights and
penalised by 0.5 nats per fitted weight. The 10 best pair formulas are frozen
in pairs_formulas.json, then tested:
  * walk-forward 2018-2026 (every draw predicted from earlier draws only)
  * the last 5 known draws (counts from draws before the first of them)
and compared with every earlier lead.

Run from the repo root:  python3 analysis/pairs_test.py
"""

import csv
import itertools
import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am  # noqa: E402

ROOT = am.ROOT
DIG = am.DIG
NG = am.NG
GOF = am.cn.GROUP_OF
SHARE = am.cn.GROUP_SHARE
FACT = am.VEDIC + am.CHINESE
PEN = 0.5          # nats per fitted weight
N_SELECT = 10
OUT = os.path.join(ROOT, "analysis", "pairs_formulas.json")


def all_dates():
    return sorted({r["date"] for op, stem in am.cn.OPERATORS.items()
                   for r in csv.DictReader(open(os.path.join(ROOT, "data", f"{stem}.csv")))
                   if (op, r["date"]) not in am.cn.EXCLUDE})


def moments(t):
    return t.mean(), t.var()


# ---------------------------------------------------------------- screening on 2012-2017
def screen(codes, rows, draws, year_of):
    t0 = time.time()
    c0 = am.counts_before(FACT, codes, rows, am.TRAIN_END)
    val = [(d, o, np.array(w)) for (d, o), (w, _) in sorted(draws.items())
           if am.TRAIN_END <= year_of[d] < am.VALID_END]
    val = val[::3]                                     # every 3rd validation draw keeps this fast
    n_win = sum(len(w) for _, _, w in val)

    # A. signed singles
    singles = []
    cache = {}
    for f in FACT:
        for kind in am.KINDS:
            A = B = 0.0
            for d, o, win in val:
                key = (f, kind, int(codes[f][d]), o if kind.endswith("_op") else -1)
                if key not in cache:
                    t = c0.term(f, key[2], kind, max(o, 0))
                    cache[key] = (t, *moments(t))
                t, m, v = cache[key]
                A += float(t[win].sum() - len(win) * m)
                B += len(win) * v
            w = A / B if B > 0 else 0.0
            singles.append({"terms": [(f, kind, w)], "gain": A * A / (2 * B) - PEN if B > 0 else -PEN,
                            "A": A, "B": B})
        cache = {k: v for k, v in cache.items() if k[0] != f}       # keep memory bounded
    singles.sort(key=lambda x: -x["gain"])
    print(f"A. 468 signed single terms scored on {len(val)} validation draws ({time.time() - t0:.0f}s)", flush=True)

    # B. additive pairs among the 30 strongest singles
    top = singles[:30]
    tv = {}
    for s in top:
        f, kind, _ = s["terms"][0]
        for d, o, _w in val:
            key = (f, kind, int(codes[f][d]), o if kind.endswith("_op") else -1)
            if key not in tv:
                tv[key] = c0.term(f, key[2], kind, max(o, 0)).astype(np.float32)
    additive = []
    for a_, b_ in itertools.combinations(range(len(top)), 2):
        (f1, k1, _), (f2, k2, _) = top[a_]["terms"][0], top[b_]["terms"][0]
        if f1 == f2:
            continue
        A = np.zeros(2)
        B = np.zeros((2, 2))
        for d, o, win in val:
            t1 = tv[(f1, k1, int(codes[f1][d]), o if k1.endswith("_op") else -1)]
            t2 = tv[(f2, k2, int(codes[f2][d]), o if k2.endswith("_op") else -1)]
            m1, m2 = t1.mean(), t2.mean()
            A += [t1[win].sum() - len(win) * m1, t2[win].sum() - len(win) * m2]
            c12 = float(np.mean((t1 - m1) * (t2 - m2)))
            B += len(win) * np.array([[t1.var(), c12], [c12, t2.var()]])
        try:
            w = np.linalg.solve(B, A)
        except np.linalg.LinAlgError:
            continue
        additive.append({"type": "additive", "terms": [(f1, k1, float(w[0])), (f2, k2, float(w[1]))],
                         "gain": float(0.5 * A @ w) - 2 * PEN})
    additive.sort(key=lambda x: -x["gain"])
    print(f"B. {len(additive)} additive pairs scored ({time.time() - t0:.0f}s)", flush=True)

    # C. joint pairs (i-Box and digit kinds, pooled over operators)
    m_tr = rows["year"] < am.TRAIN_END
    d_tr, n_tr = rows["date"][m_tr], rows["num"][m_tr]
    g_tr = GOF[n_tr]
    T = len(n_tr)
    qg = (np.bincount(g_tr, minlength=NG) + 200 * SHARE) / (T + 200)
    base = np.stack([np.bincount(DIG[n_tr, p], minlength=10) for p in range(4)]) / T       # (4, 10)
    vd = np.array([d for d, _, _ in val])
    w_draw = np.concatenate([np.full(len(w), j) for j, (_, _, w) in enumerate(val)])
    w_num = np.concatenate([w for _, _, w in val])
    nwin = np.array([len(w) for _, _, w in val])
    joint = []
    for f1, f2 in itertools.combinations(FACT, 2):
        V2 = int(codes[f2].max()) + 1
        cell_all = codes[f1].astype(np.int64) * V2 + codes[f2]
        vc = cell_all[vd]
        uniq, uj = np.unique(vc, return_inverse=True)
        ct = cell_all[d_tr]
        mask = np.isin(ct, uniq)
        idx = np.searchsorted(uniq, ct[mask])
        nv = np.bincount(idx, minlength=len(uniq)).astype(float)
        # box
        cg = np.bincount(idx * NG + g_tr[mask], minlength=len(uniq) * NG).reshape(len(uniq), NG)
        L = np.log((cg + 50) / (nv[:, None] * qg[None, :] + 50))                  # (U, NG)
        m = L @ SHARE
        v = (L ** 2) @ SHARE - m ** 2
        A = float(L[uj[w_draw], GOF[w_num]].sum() - (nwin * m[uj]).sum())
        B = float((nwin * v[uj]).sum())
        if B > 0:
            joint.append({"type": "joint", "pair": (f1, f2), "kind": "box", "w": A / B, "gain": A * A / (2 * B) - PEN})
        # digits
        cd = np.stack([np.bincount(idx * 10 + DIG[n_tr[mask], p], minlength=len(uniq) * 10).reshape(len(uniq), 10)
                       for p in range(4)], 1)                                      # (U, 4, 10)
        pc = (cd + 50 * base[None]) / (nv[:, None, None] + 50)
        lr = np.log(pc / base[None])
        m = lr.mean(2).sum(1)
        v = lr.var(2).sum(1)
        tw = sum(lr[uj[w_draw], p, DIG[w_num, p]] for p in range(4))
        A = float(tw.sum() - (nwin * m[uj]).sum())
        B = float((nwin * v[uj]).sum())
        if B > 0:
            joint.append({"type": "joint", "pair": (f1, f2), "kind": "dig", "w": A / B, "gain": A * A / (2 * B) - PEN})
    joint.sort(key=lambda x: -x["gain"])
    print(f"C. {len(joint)} joint-pair formulas scored ({time.time() - t0:.0f}s)", flush=True)
    return singles, additive, joint, n_win, len(val)


def joint_key(codes, f1, f2):
    key = f"{f1}*{f2}"
    if key not in codes:
        V2 = int(codes[f2].max()) + 1
        codes[key] = codes[f1].astype(np.int64) * V2 + codes[f2]
    return key


def formula_of(x, codes):
    if x["type"] == "joint":
        return [(joint_key(codes, *x["pair"]), x["kind"], x["w"])]
    return [tuple(t) for t in x["terms"]]


def results(date):
    win = {op: {} for op in am.OPS}
    for op, stem in am.cn.OPERATORS.items():
        for r in csv.DictReader(open(os.path.join(ROOT, "data", f"{stem}.csv"))):
            if r["date"] == date:
                win[op].setdefault(int(r["4d_number"]), r["prize"])
    return win


def last5(formula, codes, rows, dates, held, wins):
    cut = dates.index(held[0])
    m = rows["date"] < cut
    factors = sorted({f for f, _, _ in formula})
    c = am.Counts(factors, codes, [f for f, k, _ in formula if k.split("_")[0] == "num"])
    c.add(rows["date"][m], rows["op_ix"][m], rows["num"][m])
    out = {}
    for D in held:
        di = dates.index(D)
        hits, pay = [], 0
        for o, op in enumerate(am.OPS):
            s = am.score(c, formula, di, o) + np.arange(10000) * 1e-12
            for n in np.argsort(-s)[:10]:
                if n in wins[D][op]:
                    hits.append(f"{op} {n:04d} {wins[D][op][n]}")
                    pay += am.BIG[wins[D][op][n]]
        out[D] = {"hits": hits, "payout": pay}
    return out


def main():
    data, codes, labels, rows, draws, year_of = am.load()
    am._YEAR = year_of
    dates = all_dates()
    singles, additive, joint, n_win, n_val = screen(codes, rows, draws, year_of)
    pos = [s for s in singles if s["gain"] > 0 and s["terms"][0][2] > 0]
    neg = [s for s in singles if s["gain"] > 0 and s["terms"][0][2] < 0]
    print(f"\nSigned singles helping on validation: {len(pos)} promote (w > 0), {len(neg)} suppress (w < 0) "
          f"of 468 (after the {PEN}-nat penalty)")
    for s in singles[:8]:
        f, k, w = s["terms"][0]
        print(f"    {f:<22} {k:<7} w={w:+.3f} gain {s['gain']:+.2f} nats")
    print(f"Best additive pairs: " + "; ".join(
        f"{a['terms'][0][0]}/{a['terms'][0][1]} {a['terms'][0][2]:+.2f} & {a['terms'][1][0]}/{a['terms'][1][1]} "
        f"{a['terms'][1][2]:+.2f} ({a['gain']:+.2f})" for a in additive[:3]))
    print(f"Best joint pairs: " + "; ".join(f"{j['pair'][0]}*{j['pair'][1]}/{j['kind']} w={j['w']:+.2f} ({j['gain']:+.2f})"
                                           for j in joint[:3]))
    best_single = singles[0]["gain"]
    pairs = sorted(additive + joint, key=lambda x: -x["gain"])
    chosen = [p for p in pairs if p["gain"] > 0][:N_SELECT]
    print(f"\n{sum(p['gain'] > 0 for p in additive)} additive and {sum(p['gain'] > 0 for p in joint)} joint pairs "
          f"beat 'no formula' after the penalty; {sum(p['gain'] > best_single for p in pairs)} beat the best single. "
          f"Frozen: {len(chosen)} pair formulas -> {OUT}", flush=True)
    json.dump({"validation_draws": n_val, "validation_winners": n_win, "penalty_nats_per_weight": PEN,
               "selected": chosen, "best_single": singles[0], "top_singles": singles[:20],
               "signed_single_counts": {"promote": len(pos), "suppress": len(neg)}},
              open(OUT, "w"), indent=1, default=float)

    # tests
    held = dates[-5:]
    wins = {D: results(D) for D in held}
    print(f"\nTests of the {len(chosen)} frozen pair formulas")
    report = []
    for p in chosen:
        formula = formula_of(p, codes)
        out, _ = am.forward_test("pair", formula, codes, rows, draws)
        a = out["All"]
        l5 = last5(formula, codes, rows, dates, held, wins)
        name = (f"{p['pair'][0]} x {p['pair'][1]} (joint {p['kind']}, w {p['w']:+.2f})" if p["type"] == "joint" else
                " + ".join(f"{f}/{k} ({w:+.2f})" for f, k, w in p["terms"]))
        report.append({"formula": name, "validation_gain": p["gain"], "wf_top10_lift": a["top10"]["lift"],
                       "wf_z": a["top10"]["z"], "wf_big": a["big_return_top10"]["per_RM1"], "last5": l5})
        print(f"  {name}\n      2018-2026 top10 {a['top10']['hits']}/{a['top10']['expected']} x{a['top10']['lift']} "
              f"z={a['top10']['z']:+.1f}, Big RM{a['big_return_top10']['per_RM1']}; last 5: " +
              " | ".join(f"{D[5:]}: {', '.join(l5[D]['hits']) or '-'}" for D in held), flush=True)
    json.dump({"held_out": held, "pairs": report}, open(os.path.join(ROOT, "analysis", "pairs_results.json"), "w"),
              indent=1, default=float)


if __name__ == "__main__":
    main()
