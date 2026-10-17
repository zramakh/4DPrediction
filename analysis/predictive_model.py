#!/usr/bin/env python3
"""A predictive formula for 4D numbers from date parameters and history,
tuned on one period and tested on draws it has never seen.

Score of number n for a draw of operator `op` on date `t` (all counts from
draws before the period being predicted, each number counted once per draw):

  score(n) = w_hot  * log[(wins_op(n) + a) / (expected_op + a)]              overall hot number
           + w_pool * log[(wins_all(n) + a) / (expected_all + a)]            same, all operators
           + w_dig  * sum_pos log[p_op(pos, digit_pos(n)) / 0.1]             recency-weighted digit bias
           + w_cdig / F * sum_f sum_pos log[p(pos, digit | f = f(t)) / p(pos, digit)]
           + w_cnum / F * sum_f log[(wins(n | f = f(t)) + a) / (expected + a)]
           + w_cbox / F * sum_f log[(wins(ibox(n) | f = f(t)) + a) / (expected + a)]

f runs over the F = 84 date parameters of almanac.py / conditional_extended.py
(weekday, month, moon, Chinese almanac, Vedic, KP, ...). The picks are the K
highest-scoring numbers.

Protocol (no peeking):
  * tune: learn from draws before 2012, choose the weights and smoothing on
    2012-2017 by the average log-likelihood of the real winners;
  * freeze the formula;
  * test on 2018-2026: for each year, re-learn the counts from all draws
    before that year, then predict every draw of that year. Report hit rates
    and Big Forecast returns against random picks.

Usage (repo root):
  python3 analysis/predictive_model.py                 # tune + test (~15 min)
  python3 analysis/predictive_model.py predict --date 2026-10-17 [--operator Magnum] [--k 5]
"""

import argparse
import csv
import datetime as dt
import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import conditional_extended as ce  # noqa: E402
import conditional_numbers as cn  # noqa: E402

ROOT = cn.ROOT
OPS = list(cn.OPERATORS)
TRAIN_END, VALID_END = 2012, 2018          # tune on [2012, 2018), test on [2018, ...)
BIG = {"1st": 2500, "2nd": 1000, "3rd": 500, "Special": 180, "Consolation": 60}
DIG = np.array([[n // 1000, n // 100 % 10, n // 10 % 10, n % 10] for n in range(10000)])
KS = (1, 5, 10, 23, 100)
CONFIG_PATH = os.path.join(ROOT, "analysis", "predictive_model_config.json")


# ------------------------------------------------------------------ data
def load():
    data, codes, labels, factors, n_dates = ce.load()
    factors = [f for f in factors if f != "prize"]
    raw_prize = []
    for op, stem in cn.OPERATORS.items():
        with open(os.path.join(ROOT, "data", f"{stem}.csv"), newline="") as fh:
            for r in csv.DictReader(fh):
                if (op, r["date"]) not in cn.EXCLUDE:
                    raw_prize.append(r["prize"])
    data["raw_prize"] = np.array(raw_prize)
    data["op_ix"] = np.array([OPS.index(o) for o in data["op"]])
    data["once"] = cn.once_per_draw(data["op_ix"] * n_dates + data["date"], data["num"], 10000)
    dates = sorted({r["date"] for s in cn.OPERATORS.values()
                    for r in csv.DictReader(open(os.path.join(ROOT, "data", f"{s}.csv")))})
    return data, codes, labels, factors, dates


def draws_of(data, op_i, mask):
    """List of (date_ix, deduped numbers, [(prize, number)]) for one operator."""
    sel = (data["op_ix"] == op_i) & mask
    out = {}
    for di, n, p, o in zip(data["date"][sel], data["num"][sel], data["raw_prize"][sel], data["once"][sel]):
        e = out.setdefault(di, ([], []))
        if o:
            e[0].append(n)
        e[1].append((p, n))
    return [(d, np.array(v[0]), v[1]) for d, v in sorted(out.items())]


# ------------------------------------------------------------------ learned tables
class Tables:
    """Every count the formula needs, from the training rows only."""

    def __init__(self, data, codes, factors, train_mask, alphas=(2, 10, 50), betas=(50, 500), half_lives=(300, 0)):
        self.factors = factors
        r = train_mask & data["once"]
        num, op, date = data["num"][r], data["op_ix"][r], data["date"][r]
        self.T = len(num)
        self.count_all = np.bincount(num, minlength=10000).astype(float)
        self.count_op = np.stack([np.bincount(num[op == i], minlength=10000) for i in range(3)]).astype(float)
        self.T_op = self.count_op.sum(1)
        q = (self.count_all + 20) / (self.T + 20 * 10000)          # shrunk overall rate of each number
        grp = cn.GROUP_OF[num]
        gcount = np.bincount(grp, minlength=len(cn.GROUP_IDS)).astype(float)
        qg = (gcount + 200 * cn.GROUP_SHARE) / (self.T + 200)
        base_dig = np.stack([np.bincount(DIG[num, p], minlength=10) for p in range(4)]) / self.T  # (4, 10)
        self.alphas, self.betas = alphas, betas
        # recency-weighted digit frequencies per operator
        self.dig = {}
        for h in half_lives:
            m = np.zeros((3, 4, 10))
            for i in range(3):
                s = op == i
                d_i = date[s]
                if h:
                    order = np.unique(d_i, return_inverse=True)[1]
                    w = 0.5 ** ((order.max() - order) / h)
                else:
                    w = np.ones(s.sum())
                for p in range(4):
                    m[i, p] = np.bincount(DIG[num[s], p], weights=w, minlength=10)
            p_ = (m + 200 * 0.1) / (m.sum(2, keepdims=True) + 200)
            self.dig[h] = np.log(p_ / 0.1)                              # (3, 4, 10)
        # conditional tables per factor
        self.cnum = {a: [] for a in alphas}
        self.cbox = {a: [] for a in alphas}
        self.cdig = {b: [] for b in betas}
        for f in factors:
            v = codes[f][date]
            V = int(codes[f].max()) + 1
            n_v = np.bincount(v, minlength=V).astype(float)
            c = np.bincount(v * 10000 + num, minlength=V * 10000).reshape(V, 10000)
            e = n_v[:, None] * q[None, :]
            cg = np.bincount(v * len(cn.GROUP_IDS) + grp, minlength=V * len(cn.GROUP_IDS)).reshape(V, -1)
            eg = n_v[:, None] * qg[None, :]
            for a in alphas:
                self.cnum[a].append(np.log((c + a) / (e + a)).astype(np.float32))
                self.cbox[a].append(np.log((cg + a) / (eg + a)).astype(np.float32))
            cd = np.stack([np.bincount(v * 10 + DIG[num, p], minlength=V * 10).reshape(V, 10)
                           for p in range(4)], 1)                          # (V, 4, 10)
            for b in betas:
                pd = (cd + b * base_dig[None]) / (n_v[:, None, None] + b)
                self.cdig[b].append(np.log(pd / base_dig[None]))

    def components(self, op_i, date_ixs, codes):
        """Dict of component name -> (n_draws, 10000) score arrays."""
        n = len(date_ixs)
        out = {}
        for a in self.alphas:
            hot = np.log((self.count_op[op_i] + a) / (self.T_op[op_i] / 10000 + a))
            pool = np.log((self.count_all + a) / (self.T / 10000 + a))
            out[f"hot_a{a}"] = np.broadcast_to(hot, (n, 10000))
            out[f"pool_a{a}"] = np.broadcast_to(pool, (n, 10000))
        for h, t in self.dig.items():
            s = sum(t[op_i, p][DIG[:, p]] for p in range(4))
            out[f"dig_h{h}"] = np.broadcast_to(s, (n, 10000))
        F = len(self.factors)
        for a in self.alphas:
            sn = np.zeros((n, 10000), np.float32)
            sb = np.zeros((n, len(cn.GROUP_IDS)), np.float32)
            for k, f in enumerate(self.factors):
                v = codes[f][date_ixs]
                sn += self.cnum[a][k][v]
                sb += self.cbox[a][k][v]
            out[f"cnum_a{a}"] = sn / F
            out[f"cbox_a{a}"] = sb[:, cn.GROUP_OF] / F
        for b in self.betas:
            m = np.zeros((n, 4, 10))
            for k, f in enumerate(self.factors):
                m += self.cdig[b][k][codes[f][date_ixs]]
            out[f"cdig_b{b}"] = sum(m[:, p, :][:, DIG[:, p]] for p in range(4)) / F
        return out


def combine(comps, weights):
    s = np.zeros(next(iter(comps.values())).shape, np.float64)
    for k, w in weights.items():
        if w:
            s += w * comps[k]
    return s


def loglik_gain(score, winners):
    """Sum over winners of log(10000 * p(winner)), p = softmax(score)."""
    m = score.max(1, keepdims=True)
    lse = (m[:, 0] + np.log(np.exp(score - m).sum(1)))
    tot = 0.0
    for i, w in enumerate(winners):
        tot += (score[i, w] - lse[i] + math.log(10000)).sum()
    return tot


# ------------------------------------------------------------------ tuning
def tune(data, codes, factors):
    t0 = time.time()
    years = data["year"]
    tab = Tables(data, codes, factors, years < TRAIN_END)
    print(f"tables for tuning built in {time.time() - t0:.0f}s", flush=True)
    grid = (0.25, 0.5, 1, 2, 4)
    single, n_win = {}, 0
    cache = []
    for op_i in range(3):
        draws = draws_of(data, op_i, (years >= TRAIN_END) & (years < VALID_END))
        for s in range(0, len(draws), 200):
            chunk = draws[s:s + 200]
            comps = tab.components(op_i, np.array([d[0] for d in chunk]), codes)
            winners = [d[1] for d in chunk]
            n_win += sum(len(w) for w in winners)
            for k in comps:
                for w in grid:
                    single[(k, w)] = single.get((k, w), 0) + loglik_gain(w * comps[k], winners)
            cache.append((op_i, [d[0] for d in chunk], winners))
    print(f"single-component search done ({time.time() - t0:.0f}s), {n_win} validation winners", flush=True)
    best = {}
    for (k, w), g in single.items():
        if g > best.get(k, (None, 0.0))[1]:
            best[k] = (w, g)
    for k in sorted({k for k, _ in single}):
        b = best.get(k)
        print(f"  {k:<12} best weight {b[0] if b else '-':<5} gain {1000 * (b[1] if b else 0) / n_win:+.3f} milli-nats/winner")
    # one component per family (the best smoothing), then a joint scale
    fam = {}
    for k, (w, g) in best.items():
        f = k.split("_")[0]
        if g > 0 and g > fam.get(f, ("", 0, 0))[2]:
            fam[f] = (k, w, g)
    chosen = {k: w for k, w, _ in fam.values()}
    joint = {}
    for scale in (0, 0.25, 0.5, 0.75, 1.0):
        weights = {k: w * scale for k, w in chosen.items()}
        g = 0.0
        for op_i, dix, winners in cache:
            g += loglik_gain(combine(tab.components(op_i, np.array(dix), codes), weights), winners)
        joint[scale] = g
        print(f"  joint scale {scale}: gain {1000 * g / n_win:+.3f} milli-nats/winner", flush=True)
    scale = max(joint, key=joint.get)
    weights = {k: w * scale for k, w in chosen.items()}
    cfg = {"weights": weights, "validation_gain_millinats_per_winner": 1000 * joint[scale] / n_win,
           "single_component": {k: {"weight": w, "gain_millinats": 1000 * g / n_win} for k, (w, g) in best.items()},
           "train_before": TRAIN_END, "validate": [TRAIN_END, VALID_END - 1]}
    print(f"chosen formula: {weights}")
    return cfg


# ------------------------------------------------------------------ testing
def evaluate(data, codes, factors, weights, years_test, seed=0):
    rng = np.random.default_rng(seed)
    stats = {op: {"draws": 0, "winners": 0, "gain": 0.0,
                  **{f"hits@{k}": 0 for k in KS}, **{f"exp@{k}": 0.0 for k in KS},
                  **{f"rand_hits@{k}": 0 for k in KS},
                  **{f"payout@{k}": 0.0 for k in (1, 5, 10)}, **{f"rand_payout@{k}": 0.0 for k in (1, 5, 10)}}
             for op in OPS + ["All"]}
    by_year = {}
    for y in years_test:
        t = time.time()
        tab = Tables(data, codes, factors, data["year"] < y,
                     alphas=sorted({int(k.split("_a")[1]) for k in weights if "_a" in k}) or [10],
                     betas=sorted({int(k.split("_b")[1]) for k in weights if "_b" in k}) or [50],
                     half_lives=sorted({int(k.split("_h")[1]) for k in weights if "_h" in k}) or [0])
        yh = ye = 0.0
        for op_i, op in enumerate(OPS):
            draws = draws_of(data, op_i, data["year"] == y)
            if not draws:
                continue
            for s in range(0, len(draws), 200):
                chunk = draws[s:s + 200]
                comps = tab.components(op_i, np.array([d[0] for d in chunk]), codes)
                score = combine(comps, weights) + rng.random((len(chunk), 10000)) * 1e-9
                winners = [d[1] for d in chunk]
                g = loglik_gain(score, winners)
                order = np.argsort(-score, 1)[:, :max(KS)]
                for i, (_, win, prize_rows) in enumerate(chunk):
                    rand = rng.choice(10000, max(KS), replace=False)
                    for key in (op, "All"):
                        st = stats[key]
                        for k in KS:
                            st[f"hits@{k}"] += np.isin(win, order[i, :k]).sum()
                            st[f"rand_hits@{k}"] += np.isin(win, rand[:k]).sum()
                            st[f"exp@{k}"] += k * len(win) / 10000
                        for k in (1, 5, 10):
                            picks, rpicks = set(order[i, :k].tolist()), set(rand[:k].tolist())
                            st[f"payout@{k}"] += sum(BIG[p] for p, n in prize_rows if n in picks)
                            st[f"rand_payout@{k}"] += sum(BIG[p] for p, n in prize_rows if n in rpicks)
                    yh += np.isin(win, order[i, :10]).sum()
                    ye += 10 * len(win) / 10000
                for key in (op, "All"):
                    stats[key]["draws"] += len(chunk)
                    stats[key]["winners"] += sum(len(w) for w in winners)
                    stats[key]["gain"] += g
        by_year[y] = {"hits@10": int(yh), "expected@10": round(ye, 1)}
        print(f"  test year {y}: top-10 hits {int(yh)} vs {ye:.1f} expected ({time.time() - t:.0f}s)", flush=True)
    out = {}
    for key, st in stats.items():
        if not st["draws"]:
            continue
        r = {"draws": st["draws"], "loglik_gain_millinats_per_winner": round(1000 * st["gain"] / st["winners"], 3)}
        for k in KS:
            h, e = st[f"hits@{k}"], st[f"exp@{k}"]
            r[f"top{k}"] = {"hits": int(h), "expected": round(e, 1), "lift": round(h / e, 3),
                            "z": round((h - e) / math.sqrt(e), 2), "random_picks_hits": int(st[f"rand_hits@{k}"])}
        for k in (1, 5, 10):
            stake = k * st["draws"]
            r[f"big_return_top{k}"] = {"per_RM1": round(st[f"payout@{k}"] / stake, 3),
                                       "random_picks_per_RM1": round(st[f"rand_payout@{k}"] / stake, 3)}
        out[key] = r
    return out, by_year


# ------------------------------------------------------------------ prediction
def predict(date, operators, k):
    with open(CONFIG_PATH) as fh:
        weights = json.load(fh)["weights"]
    data, codes, labels, factors, dates = load()
    ctx = ce.date_context(date)
    # append the target date as a new date index
    new = len(dates)
    codes2 = {}
    for f in factors:
        lab = ctx[f]
        code = labels[f].index(lab) if lab in labels[f] else -1
        arr = np.append(codes[f], max(code, 0))
        codes2[f] = arr
    tab = Tables(data, codes, factors, data["date"] >= 0,
                 alphas=sorted({int(x.split("_a")[1]) for x in weights if "_a" in x}) or [10],
                 betas=sorted({int(x.split("_b")[1]) for x in weights if "_b" in x}) or [50],
                 half_lives=sorted({int(x.split("_h")[1]) for x in weights if "_h" in x}) or [0])
    unseen = [f for f in factors if ctx[f] not in labels[f]]
    for f in unseen:  # a value never seen in history carries no information
        for a in tab.cnum:
            tab.cnum[a][factors.index(f)] = np.vstack([tab.cnum[a][factors.index(f)], np.zeros((1, 10000), np.float32)])
            tab.cbox[a][factors.index(f)] = np.vstack([tab.cbox[a][factors.index(f)],
                                                       np.zeros((1, len(cn.GROUP_IDS)), np.float32)])
        for b in tab.cdig:
            tab.cdig[b][factors.index(f)] = np.concatenate([tab.cdig[b][factors.index(f)], np.zeros((1, 4, 10))])
        codes2[f][new] = len(labels[f])
    print(f"Draw date {date}: " + ", ".join(f"{f}={ctx[f]}" for f in
          ("weekday", "moon_phase", "lunar_month", "lunar_day", "day_pillar", "nakshatra", "tithi")))
    for op in operators:
        score = combine(tab.components(OPS.index(op), np.array([new]), codes2), weights)[0]
        top = np.argsort(-score)[:k]
        print(f"  {op:<12} " + "  ".join(f"{n:04d}" for n in top))


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", nargs="?", default="evaluate", choices=["evaluate", "predict"])
    ap.add_argument("--date")
    ap.add_argument("--operator", choices=OPS)
    ap.add_argument("--k", type=int, default=5)
    a = ap.parse_args()
    if a.mode == "predict":
        predict(a.date or dt.date.today().isoformat(), [a.operator] if a.operator else OPS, a.k)
        return
    t0 = time.time()
    data, codes, labels, factors, dates = load()
    cfg = tune(data, codes, factors)
    with open(CONFIG_PATH, "w") as fh:
        json.dump(cfg, fh, indent=1)
    print("\nTesting on unseen draws (formula frozen; counts re-learned each year from earlier draws only)")
    test_years = list(range(VALID_END, int(data["year"].max()) + 1))
    res, by_year = evaluate(data, codes, factors, cfg["weights"], test_years)
    # baseline: the same machinery with only the overall-hot component
    hot_only = {k: w for k, w in cfg["weights"].items() if k.startswith(("hot", "pool"))} or {"pool_a10": 1.0}
    print("\nBaseline: overall hot numbers only")
    res_hot, _ = evaluate(data, codes, factors, hot_only, test_years, seed=1)
    out = {"formula": cfg, "test_years": [test_years[0], test_years[-1]], "test": res, "test_by_year": by_year,
           "baseline_hot_only": {"weights": hot_only, "test": res_hot}}
    with open(os.path.join(ROOT, "analysis", "predictive_model_results.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print("\n=== Unseen test draws", test_years[0], "-", test_years[-1], "===")
    for name, r_ in (("formula", res), ("hot-only baseline", res_hot)):
        print(f"[{name}]")
        for key, r in r_.items():
            print(f"  {key:<12} draws {r['draws']:>5}  loglik gain {r['loglik_gain_millinats_per_winner']:+.3f} mnats  " +
                  "  ".join(f"top{k}: {r[f'top{k}']['hits']}/{r[f'top{k}']['expected']} (x{r[f'top{k}']['lift']}, z={r[f'top{k}']['z']:+.1f}; random {r[f'top{k}']['random_picks_hits']})"
                            for k in (5, 10, 23, 100)))
            print(f"  {'':<12} Big RM1 return: " + "  ".join(
                f"top{k} {r[f'big_return_top{k}']['per_RM1']} (random {r[f'big_return_top{k}']['random_picks_per_RM1']})" for k in (1, 5, 10)))
    print(f"\ndone in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
