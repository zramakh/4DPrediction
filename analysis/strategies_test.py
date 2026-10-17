#!/usr/bin/env python3
"""Four number-building strategies, for every Vedic / Chinese parameter and pair.

S1 hot positional   for the draw's parameter value(s) and operator, the most
                    frequent digit in each of the 4 positions -> 1 number; the
                    top-2 digits per position -> 2^4 = 16 numbers (incl. the 1)
S2 cold positional  the same with the least frequent digits (reversion)
S3 recurrence       replay the winners of the last earlier draw (same operator)
                    with the same parameter value(s): its 1st prize -> 1 pick,
                    its first 16 winners in prize order -> 16 picks
S4 folk transforms  no parameters: the same operator's previous draw, 1st-3rd
                    prizes as-is / mirrored (digit + 5) / reversed, and the
                    first 16 permutations of its 1st prize

S1-S3 run for all 78 parameters and all 3,003 pairs (joint values). Counts for a
year come only from earlier years (2012-2017 = validation, 2018-2026 = test).
The last 5 known draws are also predicted with everything frozen before the
first of them, and compared with random picks of the same size.

Run from the repo root:  python3 analysis/strategies_test.py
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
FACT = am.VEDIC + am.CHINESE
Y0, Y1, Y2 = 2012, 2018, 2027
POW = np.array([1000, 100, 10, 1])
BITS = np.array(list(itertools.product((0, 1), repeat=4)))            # (16, 4); row 0 = all best


def all_dates():
    return sorted({r["date"] for op, stem in am.cn.OPERATORS.items()
                   for r in csv.DictReader(open(os.path.join(ROOT, "data", f"{stem}.csv")))
                   if (op, r["date"]) not in am.cn.EXCLUDE})


def setup():
    data, codes, labels, rows, draws, year_of = am.load()
    keys = sorted(draws)                                               # (date_ix, op) in time order
    n = len(keys)
    Wm = np.full((n, 23), -1)
    Pm = np.zeros((n, 23))
    R16 = np.full((n, 16), -1)                                        # winners in prize order
    for j, k in enumerate(keys):
        seen = []
        for p, num in draws[k][1]:
            if num not in seen:
                seen.append(num)
                Pm[j, len(seen) - 1] = am.BIG[p]
        Wm[j, :len(seen)] = seen
        R16[j, :min(16, len(seen))] = seen[:16]
    dj = np.array([k[0] for k in keys])
    oj = np.array([k[1] for k in keys])
    yj = year_of[dj]
    return codes, rows, draws, keys, dj, oj, yj, Wm, Pm, R16


def score_picks(P, Wm, Pm):
    """P (n, k) picks -> per-draw hits and Big payout (straight)."""
    eq = P[:, :, None] == Wm[:, None, :]
    eq &= (P >= 0)[:, :, None]
    return eq.any(2).sum(1), (eq * Pm[:, None, :]).sum((1, 2))


class Acc:
    def __init__(self):
        self.d = {}

    def add(self, name, period, k, hits, pay, nwin):
        t = self.d.setdefault((name, period, k), [0, 0.0, 0.0, 0])
        t[0] += int(hits.sum())
        t[1] += float(pay.sum())
        t[2] += float((k * nwin / 10000).sum())
        t[3] += len(hits)

    def get(self, name, period, k):
        h, p, e, n = self.d.get((name, period, k), (0, 0.0, 0.0, 0))
        return {"hits": h, "expected": round(e, 2), "lift": round(h / e, 3) if e else None,
                "z": round((h - e) / math.sqrt(e), 2) if e else None,
                "big_per_RM1": round(p / (k * n), 3) if n else None, "draws": n}


def main():
    t0 = time.time()
    codes, rows, draws, keys, dj, oj, yj, Wm, Pm, R16 = setup()
    dates = all_dates()
    held = dates[-5:]
    cut = dates.index(held[0])
    hmask = dj >= cut
    nwin = (Wm >= 0).sum(1)
    acc = Acc()
    last5 = {}
    rd, ro, rn, ry = rows["date"], rows["op_ix"], rows["num"], rows["year"]
    overall = np.stack([np.stack([np.bincount(DIG[rn[ro == o], p], minlength=10) for p in range(4)])
                        for o in range(3)]).astype(float)               # (3, 4, 10) tie-break
    overall /= overall.sum(2, keepdims=True)
    formulas = [(f,) for f in FACT] + list(itertools.combinations(FACT, 2))

    def cell_of(fs):
        c = np.zeros(len(codes[FACT[0]]), np.int64)
        for f in fs:
            c = c * (int(codes[f].max()) + 1) + codes[f]
        return c

    for i, fs in enumerate(formulas):
        name = " x ".join(fs)
        cd = cell_of(fs)
        U = int(cd.max()) + 1
        rc = cd[rd] * 3 + ro                                          # training-row cells (per operator)
        jc = cd[dj] * 3 + oj
        # ---- S1 / S2 positional, yearly refresh ----
        flat = rc * 40
        cnt = np.zeros(U * 3 * 40)
        m0 = ry < Y0
        for p in range(4):
            cnt += np.bincount(flat[m0] + p * 10 + DIG[rn[m0], p], minlength=U * 120)
        for y in range(Y0, Y2):
            sel = yj == y
            if sel.any():
                C = cnt.reshape(U * 3, 4, 10)[jc[sel]] + 1e-6 * overall[oj[sel]]
                period = "validation" if y < Y1 else "test"
                for strat, sign in (("S1", -1), ("S2", 1)):
                    top2 = np.argsort(sign * C, axis=2)[:, :, :2]                     # (n, 4, 2)
                    dig = np.take_along_axis(top2, BITS.T[None, :, :], 2)            # (n, 4, 16)
                    P = (dig * POW[None, :, None]).sum(1)                           # (n, 16)
                    for k in (1, 16):
                        h, pay = score_picks(P[:, :k], Wm[sel], Pm[sel])
                        acc.add(f"{strat} {name}", period, k, h, pay, nwin[sel])
            my = ry == y
            for p in range(4):
                cnt += np.bincount(flat[my] + p * 10 + DIG[rn[my], p], minlength=U * 120)
        # frozen counts for the last 5 draws
        mc = rd < cut
        cf = np.zeros(U * 120)
        for p in range(4):
            cf += np.bincount(flat[mc] + p * 10 + DIG[rn[mc], p], minlength=U * 120)
        C = cf.reshape(U * 3, 4, 10)[jc[hmask]] + 1e-6 * overall[oj[hmask]]
        for strat, sign in (("S1", -1), ("S2", 1)):
            top2 = np.argsort(sign * C, axis=2)[:, :, :2]
            P = (np.take_along_axis(top2, BITS.T[None, :, :], 2) * POW[None, :, None]).sum(1)
            for k in (1, 16):
                h, pay = score_picks(P[:, :k], Wm[hmask], Pm[hmask])
                last5[(f"{strat} {name}", k)] = (int(h.sum()), float(pay.sum()))
        # ---- S3 recurrence ----
        order = np.lexsort((np.arange(len(jc)), jc))
        prev = np.full(len(jc), -1)
        same = jc[order][1:] == jc[order][:-1]
        prev[order[1:][same]] = order[:-1][same]
        ok = (prev >= 0) & (yj >= Y0)
        for y in range(Y0, Y2):
            sel = ok & (yj == y)
            if sel.any():
                P = R16[prev[sel]]
                period = "validation" if y < Y1 else "test"
                for k in (1, 16):
                    h, pay = score_picks(P[:, :k], Wm[sel], Pm[sel])
                    acc.add(f"S3 {name}", period, k, h, pay, nwin[sel])
        # last 5: the previous same-value draw must be before the cut
        before = np.flatnonzero(dj < cut)                              # keys are already in time order
        rb_ = before[::-1]
        u, first = np.unique(jc[rb_], return_index=True)                # last earlier draw per cell
        lastj = rb_[first]
        hc = jc[hmask]
        pos = np.minimum(np.searchsorted(u, hc), len(u) - 1)
        found = u[pos] == hc
        P = np.where(found[:, None], R16[lastj[pos]], -1)
        for k in (1, 16):
            h, pay = score_picks(P[:, :k], Wm[hmask], Pm[hmask])
            last5[(f"S3 {name}", k)] = (int(h.sum()), float(pay.sum()))
        if (i + 1) % 500 == 0:
            print(f"  {i + 1}/{len(formulas)} parameter sets ({time.time() - t0:.0f}s)", flush=True)

    # ---- S4 folk transforms of the previous draw (same operator) ----
    prev_same_op = np.full(len(keys), -1)
    last = {}
    for j in range(len(keys)):
        prev_same_op[j] = last.get(oj[j], -1)
        last[oj[j]] = j
    top3 = Wm[:, :3]
    mirror = ((DIG[top3] + 5) % 10 * POW).sum(-1)
    rev = (DIG[top3][:, :, ::-1] * POW).sum(-1)
    def perms16(n):
        ps = sorted({int("".join(q)) for q in itertools.permutations(f"{n:04d}")}, key=lambda x: (x != n, x))[:16]
        return ps + [-1] * (16 - len(ps))
    perms = np.array([perms16(int(n)) for n in Wm[:, 0]])
    s4 = {"S4 repeat 1st-3rd": top3, "S4 mirror 1st-3rd": mirror, "S4 reverse 1st-3rd": rev,
          "S4 permutations of 1st": perms}
    ok = (prev_same_op >= 0) & (yj >= Y0)
    for name, M in s4.items():
        for y in range(Y0, Y2):
            sel = ok & (yj == y)
            P = M[prev_same_op[sel]]
            k = P.shape[1]
            period = "validation" if y < Y1 else "test"
            h, pay = score_picks(P, Wm[sel], Pm[sel])
            acc.add(name, period, k, h, pay, nwin[sel])
        sel = hmask & (prev_same_op >= 0)
        h, pay = score_picks(M[prev_same_op[sel]], Wm[sel], Pm[sel])
        last5[(name, M.shape[1])] = (int(h.sum()), float(pay.sum()))

    # ---- random baseline for the last 5 draws ----
    rng = np.random.default_rng(16)
    rb = {}
    for k in (1, 3, 16):
        hits = [score_picks(rng.integers(0, 10000, (hmask.sum(), k)), Wm[hmask], Pm[hmask])[0].sum() for _ in range(5000)]
        rb[k] = {"mean": float(np.mean(hits)), "p_at_least_1": float(np.mean(np.array(hits) >= 1)),
                 "p_at_least_2": float(np.mean(np.array(hits) >= 2))}

    # ---- report ----
    out = {"held_out": held, "random_last5": rb, "strategies": {}}
    print(f"\nLast 5 draws ({', '.join(held)}), 15 operator-draws; random picks: " +
          "; ".join(f"{k} pick(s): mean {v['mean']:.3f} hits, P(>=1) {v['p_at_least_1']:.0%}, P(>=2) {v['p_at_least_2']:.1%}"
                    for k, v in rb.items()))
    names = sorted({n for n, _, _ in acc.d})
    for strat in ("S1", "S2", "S3", "S4"):
        sn = [n for n in names if n.startswith(strat)]
        for k in ((1, 16) if strat != "S4" else (3, 16)):
            rows_ = [(n, acc.get(n, "validation", k), acc.get(n, "test", k), last5.get((n, k))) for n in sn
                     if acc.get(n, "validation", k)["draws"]]
            if not rows_:
                continue
            zt = np.array([r[2]["z"] for r in rows_ if r[2]["z"] is not None])
            l5 = np.array([r[3][0] for r in rows_ if r[3] is not None])
            best = sorted(rows_, key=lambda r: -(r[1]["z"] or -9))[:3]
            summary = {"formulas": len(rows_), "test_z_gt_2": int((zt > 2).sum()), "test_z_lt_-2": int((zt < -2).sum()),
                       "test_mean_lift": float(np.mean([r[2]["lift"] for r in rows_ if r[2]["lift"]])),
                       "last5_share_with_hit": float(np.mean(l5 >= 1)) if len(l5) else None,
                       "last5_mean_hits": float(l5.mean()) if len(l5) else None,
                       "best_by_validation": [{"formula": r[0], "validation": r[1], "test": r[2],
                                               "last5_hits": r[3][0] if r[3] else None,
                                               "last5_big": r[3][1] if r[3] else None} for r in best]}
            out["strategies"][f"{strat} top{k}"] = summary
            print(f"\n{strat}, {k} pick(s) per operator-draw: {len(rows_)} formulas. 2018-2026: mean lift x{summary['test_mean_lift']:.3f}, "
                  f"z>2 {summary['test_z_gt_2']} / z<-2 {summary['test_z_lt_-2']} (about {0.023 * len(rows_):.0f} each by chance). "
                  f"Last 5: {summary['last5_share_with_hit']:.0%} of formulas hit, mean {summary['last5_mean_hits']:.3f} hits")
            for b in summary["best_by_validation"]:
                v, t = b["validation"], b["test"]
                print(f"   best on 2012-2017: {b['formula']:<44} valid x{v['lift']} (z={v['z']:+.1f}) -> test x{t['lift']} "
                      f"(z={t['z']:+.1f}, Big RM{t['big_per_RM1']}) | last 5: {b['last5_hits']} hits RM{b['last5_big']:.0f}")
    top_l5 = sorted(((n, k, v) for (n, k), v in last5.items()), key=lambda x: (-x[2][0], -x[2][1]))[:10]
    print("\nMost hits on the last 5 draws (chosen after the fact, for reference):")
    for n, k, (h, p) in top_l5:
        t = acc.get(n, "test", k)
        print(f"   {n:<46} top{k}: {h} hits RM{p:.0f}  | its 2018-2026 test: x{t['lift']} (z={t['z']:+.1f})")
    out["most_hits_last5_after_the_fact"] = [{"formula": n, "k": k, "hits": h, "big": p} for n, k, (h, p) in top_l5]
    json.dump(out, open(os.path.join(ROOT, "analysis", "strategies_results.json"), "w"), indent=1, default=float)
    print(f"\ndone in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
