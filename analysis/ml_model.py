#!/usr/bin/env python3
"""Non-linear 4D prediction models, walk-forward tested.

Five model families, all fed only with information available before each
draw:

  A_all     LightGBM (gradient-boosted trees) over (draw, number) pairs. Features:
            the number's digits and pattern; its own history (all-time and
            recent win counts, draws since last win, i-Box group counts, wins
            at any operator on the previous draw date, recent digit bias);
            aggregated Vedic and Chinese conditional lifts (section 8); and the
            raw Vedic / Chinese parameters of the date, so the trees can learn
            interactions such as "digit 7 in position 1 under nakshatra X".
  A_astro   the same trees with only digits/pattern, the Vedic and Chinese lifts
            and the raw parameters (no number history)
  A_hist    the same trees with only digits/pattern and number history (control)
  C_digit   four LightGBM multiclass models, one per digit position, predicting
            the winning digit from the date's Vedic / Chinese parameters,
            operator and recent digit frequencies; P(n) = product of positions
  B_kernel  "similar days": every past draw date is weighted by
            exp(beta * number of Vedic + Chinese parameters it shares with the
            target date); numbers whose i-Box group won on similar days score
            higher. beta = 0.1, 0.3, 1.0.
  E_ens     average of the log-probabilities of A_all, A_astro, C_digit and
            B_kernel(beta=0.3)

Protocol. Features start in 1995 (earlier draws only feed the history).
Models are retrained at the start of every year from 2012 on, using only
draws of earlier years. 2012-2017 is the validation period, 2018-2026 the
test period. The selection rule is fixed in advance: the model with the
best validation log-likelihood is "selected"; its test result is the
headline. Every model's test result is reported too.

Usage (repo root):
  python3 analysis/ml_model.py                       walk-forward evaluation (~40 min)
  python3 analysis/ml_model.py predict --date 2026-10-18 [--k 10]
"""

import argparse
import datetime as dt
import json
import math
import os
import sys
import time
from collections import deque

import lightgbm as lgb
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am  # noqa: E402
import conditional_numbers as cn  # noqa: E402

ROOT = cn.ROOT
OPS = am.OPS
BIG = am.BIG
DIG = am.DIG
FEAT_START, VALID_START, TEST_START = 1995, 2012, 2018
NEG_PER_DRAW = 100
KS = (1, 5, 10, 23, 100)
ASTRO = am.VEDIC + am.CHINESE
RAW_CATS = ["nakshatra", "tithi", "moon_rashi", "lagna_rashi", "hora_lord", "weekday", "masa", "yoga",
            "day_stem", "day_branch", "mansion_28", "day_officer", "nine_star_month", "year_animal", "solar_term"]
BETAS = (0.1, 0.3, 1.0)
LGB_PARAMS = dict(objective="binary", learning_rate=0.05, num_leaves=31, min_data_in_leaf=500,
                  feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1, lambda_l2=1.0,
                  num_threads=4, verbose=-1, seed=7)
N_TREES = 250

# ---------------------------------------------------------------- static number features
_s = np.array([sorted(f"{n:04d}") for n in range(10000)])
NDISTINCT = np.array([len(set(f"{n:04d}")) for n in range(10000)])
_runs = np.array([sorted(np.unique(list(f"{n:04d}"), return_counts=True)[1].tolist()) for n in range(10000)],
                 dtype=object)
PATTERN = np.array([{(4,): 0, (1, 3): 1, (2, 2): 2, (1, 1, 2): 3, (1, 1, 1, 1): 4}[tuple(r)] for r in _runs])
PERMS = np.array([24 // math.prod(math.factorial(c) for c in r) for r in _runs])
DSUM = DIG.sum(1)
STATIC = np.column_stack([DIG, DSUM, NDISTINCT, PATTERN, PERMS]).astype(np.float32)
STATIC_NAMES = ["d1", "d2", "d3", "d4", "digit_sum", "n_distinct", "pattern", "ibox_perms"]
HIST_NAMES = ["wins_op_norm", "wins_op_last200", "wins_op_last1000", "gap_op", "wins_all_norm", "gap_all_dates",
              "box_op_norm", "box_all_norm", "digit_recent_op", "won_prev_date_any", "won_last_draw_op"]
LIFT_NAMES = ["vedic_num", "vedic_box", "vedic_dig", "chinese_num", "chinese_box", "chinese_dig"]
CAT_NAMES = ["operator"] + [f"raw_{f}" for f in RAW_CATS]
ALL_NAMES = STATIC_NAMES + HIST_NAMES + LIFT_NAMES + CAT_NAMES
FEATURE_SETS = {
    "A_all": ALL_NAMES,
    "A_astro": STATIC_NAMES + LIFT_NAMES + CAT_NAMES,
    "A_hist": STATIC_NAMES + HIST_NAMES + ["operator"],
}
CATEGORICAL = {"d1", "d2", "d3", "d4", "pattern", *CAT_NAMES}


# ---------------------------------------------------------------- history state
class History:
    def __init__(self, codes):
        self.cnt = np.zeros((3, 10000))
        self.last = np.full((3, 10000), -10 ** 6)
        self.ndraw = np.zeros(3, int)
        self.recent = {K: np.zeros((3, 10000)) for K in (200, 1000)}
        self.queue = [deque() for _ in range(3)]
        self.box = np.zeros((3, len(cn.GROUP_IDS)))
        self.all = np.zeros(10000)
        self.last_date = np.full(10000, -10 ** 6)
        self.ndates = 0
        self.dig = np.full((3, 4, 10), 1.0)              # decayed digit counts, half-life 300 draws
        self.prev_date_win = np.zeros(10000, bool)
        self.counts = am.Counts(ASTRO, codes)

    def update(self, date_ix, by_op):
        """by_op: {op_i: winners array}; also feeds the astro Counts."""
        self.ndates += 1
        prev = np.zeros(10000, bool)
        allrows_d, allrows_o, allrows_n = [], [], []
        for o, win in by_op.items():
            self.cnt[o, win] += 1
            self.ndraw[o] += 1
            self.last[o, win] = self.ndraw[o]
            q = self.queue[o]
            q.append(win)
            for K in (200, 1000):
                self.recent[K][o, win] += 1
                if len(q) > K:
                    self.recent[K][o, q[-K - 1]] -= 1
            if len(q) > 1000:
                q.popleft()
            np.add.at(self.box[o], cn.GROUP_OF[win], 1)
            self.dig[o] *= 0.5 ** (1 / 300)
            for p in range(4):
                np.add.at(self.dig[o, p], DIG[win, p], 1)
            self.all[win] += 1
            self.last_date[win] = self.ndates
            prev[win] = True
            allrows_d.append(np.full(len(win), date_ix))
            allrows_o.append(np.full(len(win), o))
            allrows_n.append(win)
        self.prev_date_win = prev
        self.counts.add(np.concatenate(allrows_d), np.concatenate(allrows_o), np.concatenate(allrows_n))

    def lifts(self, date_ix):
        """(10000, 6) mean Vedic / Chinese conditional lifts, pooled over operators."""
        out = []
        for fam in (am.VEDIC, am.CHINESE):
            for kind in ("num", "box", "dig"):
                s = np.zeros(10000)
                for f in fam:
                    s += self.counts.term(f, int(self.counts.codes[f][date_ix]), kind, 0)
                out.append(s / len(fam))
        return np.column_stack(out).astype(np.float32)

    def features(self, o, date_ix, lifts, codes):
        nd = max(self.ndraw[o], 1)
        exp_op = nd * 23 / 10000
        exp_all = max(self.all.sum(), 1) / 10000
        gbox = cn.GROUP_OF
        box_exp_op = max(self.box[o].sum(), 1) * cn.GROUP_SHARE
        box_all = self.box.sum(0)
        box_exp_all = max(box_all.sum(), 1) * cn.GROUP_SHARE
        dfreq = self.dig[o] / self.dig[o].sum(1, keepdims=True)
        dscore = sum(np.log(dfreq[p][DIG[:, p]] / 0.1) for p in range(4))
        hist = np.column_stack([
            self.cnt[o] / exp_op, self.recent[200][o], self.recent[1000][o],
            np.minimum(self.ndraw[o] - self.last[o], 3000), self.all / exp_all,
            np.minimum(self.ndates - self.last_date, 3000),
            (self.box[o] / box_exp_op)[gbox], (box_all / box_exp_all)[gbox], dscore,
            self.prev_date_win, self.ndraw[o] - self.last[o] == 0]).astype(np.float32)
        cats = np.array([o] + [codes[f][date_ix] for f in RAW_CATS], np.float32)
        return np.hstack([STATIC, hist, lifts, np.broadcast_to(cats, (10000, len(cats)))])

    def digit_freq(self, o):
        return (self.dig[o] / self.dig[o].sum(1, keepdims=True)).astype(np.float32)   # (4, 10)


# ---------------------------------------------------------------- models
def train_number_model(X, y, names):
    cols = [ALL_NAMES.index(n) for n in names]
    ds = lgb.Dataset(X[:, cols], y, feature_name=names,
                     categorical_feature=[n for n in names if n in CATEGORICAL], free_raw_data=True)
    return lgb.train(LGB_PARAMS, ds, N_TREES), cols


def number_logp(model, cols, X):
    p = model.predict(X[:, cols])
    p = np.clip(p, 1e-9, 1 - 1e-9)
    s = np.log(p / (1 - p))                         # odds (negative subsampling only shifts them)
    return s - logsumexp(s)


def train_digit_models(D):
    """D: list of (cats(1+len(RAW_CATS)), digit_freq(4,10), winner number)."""
    cats = np.array([d[0] for d in D], np.float32)
    freq = np.array([d[1] for d in D], np.float32)
    num = np.array([d[2] for d in D])
    models = []
    for p in range(4):
        X = np.hstack([cats, freq[:, p, :]])
        names = CAT_NAMES + [f"recent_freq_{k}" for k in range(10)]
        ds = lgb.Dataset(X, DIG[num, p], feature_name=names, categorical_feature=CAT_NAMES)
        params = dict(LGB_PARAMS, objective="multiclass", num_class=10, min_data_in_leaf=200)
        models.append(lgb.train(params, ds, 150))
    return models


def digit_logp(models, cats, freq):
    lp = np.zeros(10000)
    for p, m in enumerate(models):
        pr = m.predict(np.hstack([cats, freq[p]])[None, :])[0]
        lp += np.log(np.clip(pr, 1e-9, 1))[DIG[:, p]]
    return lp - logsumexp(lp)


class Kernel:
    """Similar-days model on i-Box groups."""

    def __init__(self, codes, rows):
        self.M = np.column_stack([codes[f] for f in ASTRO])           # (n_dates, F)
        order = np.argsort(rows["date"], kind="stable")
        self.rd = rows["date"][order]
        self.rg = cn.GROUP_OF[rows["num"][order]]

    def logp(self, date_ix):
        upto = np.searchsorted(self.rd, date_ix)                      # rows strictly before date
        if upto == 0:
            return {b: np.full(10000, -math.log(10000)) for b in BETAS}
        sim = (self.M[:date_ix] == self.M[date_ix]).sum(1).astype(float)
        out = {}
        for b in BETAS:
            w = np.exp(b * (sim - sim.max()))
            wr = w[self.rd[:upto]]
            A = np.bincount(self.rg[:upto], weights=wr, minlength=len(cn.GROUP_IDS))
            W = wr.sum()
            pg = (A + W * cn.GROUP_SHARE) / (2 * W)                    # equal-weight prior
            lp = np.log(pg[cn.GROUP_OF] / PERMS)
            out[b] = lp - logsumexp(lp)
        return out


def logsumexp(s):
    m = s.max()
    return m + math.log(np.exp(s - m).sum())


# ---------------------------------------------------------------- metrics
class Tally:
    def __init__(self):
        self.d = {}

    def add(self, model, period, op, logp, win, prize_rows, rng):
        top = np.argsort(-(logp + rng.random(10000) * 1e-12))[:max(KS)]
        for key in (op, "All"):
            t = self.d.setdefault((model, period, key), {"draws": 0, "winners": 0, "ll": 0.0,
                                                         **{f"h{K}": 0 for K in KS}, **{f"e{K}": 0.0 for K in KS},
                                                         **{f"p{K}": 0.0 for K in (1, 5, 10)}})
            t["draws"] += 1
            t["winners"] += len(win)
            t["ll"] += float((logp[win] + math.log(10000)).sum())
            for K in KS:
                t[f"h{K}"] += int(np.isin(win, top[:K]).sum())
                t[f"e{K}"] += K * len(win) / 10000
            for K in (1, 5, 10):
                picks = set(top[:K].tolist())
                t[f"p{K}"] += sum(BIG[p] for p, n in prize_rows if n in picks)

    def summary(self):
        out = {}
        for (m, per, key), t in self.d.items():
            r = {"draws": t["draws"], "loglik_millinats_per_winner": round(1000 * t["ll"] / t["winners"], 3)}
            for K in KS:
                h, e = t[f"h{K}"], t[f"e{K}"]
                r[f"top{K}"] = {"hits": h, "expected": round(e, 1), "lift": round(h / e, 3),
                                "z": round((h - e) / math.sqrt(e), 2)}
            for K in (1, 5, 10):
                r[f"big_top{K}_per_RM1"] = round(t[f"p{K}"] / (K * t["draws"]), 3)
            out.setdefault(m, {}).setdefault(per, {})[key] = r
        return out


# ---------------------------------------------------------------- walk-forward
def walk(predict_dates=None, k=10):
    t0 = time.time()
    data, codes, labels, rows, draws, year_of = am.load()
    if predict_dates:   # append target dates' parameters as extra date indices
        extra = []
        for d in predict_dates:
            ix, codes, _ = am.date_codes(d, codes, labels, ASTRO + [f for f in RAW_CATS if f not in ASTRO])
            extra.append(ix)
    hist = History(codes)
    kern = Kernel(codes, rows)
    rng = np.random.default_rng(11)
    by_date = {}
    for (d, o), (win, prize_rows) in draws.items():
        by_date.setdefault(d, {})[o] = (np.array(win), prize_rows)
    Xs, ys, yrs, D, Dyr = [], [], [], [], []
    models, tally, trained_for = {}, Tally(), None
    for d in sorted(by_date):
        y = int(year_of[d])
        if y >= FEAT_START:
            if not predict_dates and y >= VALID_START and trained_for != y:
                models = fit_all(Xs, ys, yrs, D, Dyr, y)
                trained_for = y
                print(f"  models for {y} trained on {sum(int(v < y) for v in yrs)} rows "
                      f"({time.time() - t0:.0f}s)", flush=True)
            lifts = hist.lifts(d)
            kern_lp = kern.logp(d) if (not predict_dates and y >= VALID_START) else None
            for o, (win, prize_rows) in by_date[d].items():
                X = hist.features(o, d, lifts, codes)
                neg = rng.choice(np.setdiff1d(np.arange(10000), win), NEG_PER_DRAW, replace=False)
                idx = np.concatenate([win, neg])
                Xs.append(X[idx])
                ys.append(np.r_[np.ones(len(win)), np.zeros(NEG_PER_DRAW)])
                yrs.append(np.full(len(idx), y))
                cats = X[0, len(ALL_NAMES) - len(CAT_NAMES):]
                freq = hist.digit_freq(o)
                for n in win:
                    D.append((cats, freq, n))
                    Dyr.append(y)
                if models:
                    period = "validation" if y < TEST_START else "test"
                    lps = predict_all(models, X, cats, freq, kern_lp)
                    for name, lp in lps.items():
                        tally.add(name, period, OPS[o], lp, win, prize_rows, rng)
        hist.update(d, {o: v[0] for o, v in by_date[d].items()})
    if predict_dates:
        models = fit_all(Xs, ys, yrs, D, Dyr, 10 ** 6)
        out = {}
        for d, ix in zip(predict_dates, extra):
            lifts = hist.lifts(ix)
            kern_lp = kern.logp(ix)
            for o in range(3):
                X = hist.features(o, ix, lifts, codes)
                cats = X[0, len(ALL_NAMES) - len(CAT_NAMES):]
                lps = predict_all(models, X, cats, hist.digit_freq(o), kern_lp)
                for name, lp in lps.items():
                    out.setdefault(d, {}).setdefault(name, {})[OPS[o]] = [int(n) for n in np.argsort(-lp)[:k]]
        return out
    return tally.summary(), time.time() - t0


def fit_all(Xs, ys, yrs, D, Dyr, year):
    X = np.concatenate(Xs)
    yv = np.concatenate(ys)
    m = np.concatenate(yrs) < year
    X, yv = X[m], yv[m]
    models = {name: train_number_model(X, yv, names) for name, names in FEATURE_SETS.items()}
    Dm = [x for x, yy in zip(D, Dyr) if yy < year]
    models["C_digit"] = train_digit_models(Dm)
    return models


def predict_all(models, X, cats, freq, kern_lp):
    out = {}
    for name in FEATURE_SETS:
        mdl, cols = models[name]
        out[name] = number_logp(mdl, cols, X)
    out["C_digit"] = digit_logp(models["C_digit"], cats, freq)
    if kern_lp is not None:
        for b, lp in kern_lp.items():
            out[f"B_kernel_b{b}"] = lp
        ens = (out["A_all"] + out["A_astro"] + out["C_digit"] + kern_lp[0.3]) / 4
        out["E_ens"] = ens - logsumexp(ens)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", nargs="?", default="evaluate", choices=["evaluate", "predict"])
    ap.add_argument("--date", action="append")
    ap.add_argument("--k", type=int, default=10)
    a = ap.parse_args()
    if a.mode == "predict":
        res = walk(predict_dates=a.date or [dt.date.today().isoformat()], k=a.k)
        for d, by_model in res.items():
            print(f"Picks for {d} (top {a.k}):")
            for name, by_op in by_model.items():
                for op, nums in by_op.items():
                    print(f"  {name:<14} {op:<12} " + " ".join(f"{n:04d}" for n in nums))
        return
    summary, secs = walk()
    val = {m: r["validation"]["All"]["loglik_millinats_per_winner"] for m, r in summary.items()}
    selected = max(val, key=val.get)
    out = {"selection_rule": "best validation (2012-2017) log-likelihood", "selected": selected,
           "models": summary}
    with open(os.path.join(ROOT, "analysis", "ml_model_results.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print("\n=== Walk-forward results (all operators) ===")
    for m in sorted(summary, key=lambda m: -val[m]):
        v, t = summary[m]["validation"]["All"], summary[m]["test"]["All"]
        print(f"{m:<14} valid ll {v['loglik_millinats_per_winner']:+8.3f}  top10 x{v['top10']['lift']:<5}"
              f" | TEST ll {t['loglik_millinats_per_winner']:+8.3f}  " +
              "  ".join(f"top{K} {t[f'top{K}']['hits']}/{t[f'top{K}']['expected']} x{t[f'top{K}']['lift']} "
                        f"(z={t[f'top{K}']['z']:+.1f})" for K in (5, 10, 23, 100)) +
              f"  Big top10 RM{t['big_top10_per_RM1']}")
    print(f"\nselected by validation: {selected}")
    print(f"done in {secs:.0f}s")


if __name__ == "__main__":
    main()
