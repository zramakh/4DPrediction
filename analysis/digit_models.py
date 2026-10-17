#!/usr/bin/env python3
"""Trainable digit-position models for 4D, built on the S1/S2 idea.

Every model outputs, for one draw (date + operator), a probability for each
digit 0-9 in each of the 4 positions, learned only from earlier draws. Numbers
are then built two ways:
  hot  (S1): best digit per position -> 1 number; top-2 per position -> 16
  cold (S2): least likely digit per position -> 1; bottom-2 -> 16

Models
  global          each operator's overall digit frequencies (no parameters)
  match           exact match on 1-3 parameters, counts smoothed toward the
                  operator's overall frequencies with strength alpha (tuned)
  backoff         triple -> pair -> single -> overall, smoothed at each level
  knn             every past draw weighted by exp(beta * number of the 78 Vedic +
                  Chinese parameter values it shares with the target date)
  softmax         L2-regularised multinomial regression per position on one-hot
                  parameter values + operator (learns promoters / suppressors)
  ensemble        average log-probability of the N best match formulas

Protocol
  validation 2012-2017 and test 2018 .. day before the last 5 known draws:
  refit every January on all earlier draws (softmax: refit in 2012 and 2018)
  last 5 known draws: everything frozen before the first of them
  selection: the best validation digit log-likelihood (all 92 digits of a draw
  count, so it is far less noisy than hits)

Usage (repo root):
  python3 analysis/digit_models.py                 tune, test, write digit_models_results.json
  python3 analysis/digit_models.py predict --date 2026-10-18 [--model NAME]
"""

import argparse
import csv
import datetime as dt
import itertools
import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am  # noqa: E402
import conditional_extended as ce  # noqa: E402

ROOT = am.ROOT
DIG = am.DIG
FACT = am.VEDIC + am.CHINESE
POW = np.array([1000, 100, 10, 1])
BITS = np.array(list(itertools.product((0, 1), repeat=4)))
VALID, TEST = (2012, 2018), 2018
OUT = os.path.join(ROOT, "analysis", "digit_models_results.json")


# ---------------------------------------------------------------- data
class Data:
    def __init__(self):
        _, self.codes, self.labels, rows, draws, self.year_of = am.load()
        self.dates = sorted({r["date"] for op, stem in am.cn.OPERATORS.items()
                             for r in csv.DictReader(open(os.path.join(ROOT, "data", f"{stem}.csv")))
                             if (op, r["date"]) not in am.cn.EXCLUDE})
        self.rd, self.ro, self.rn, self.ry = rows["date"], rows["op_ix"], rows["num"], rows["year"]
        self.rdig = DIG[self.rn]                                          # (R, 4)
        keys = sorted(draws)
        self.dj = np.array([k[0] for k in keys])
        self.oj = np.array([k[1] for k in keys])
        self.yj = self.year_of[self.dj]
        n = len(keys)
        self.Wm = np.full((n, 23), -1)
        self.Pm = np.zeros((n, 23))
        for j, k in enumerate(keys):
            seen = []
            for p, num in draws[k][1]:
                if num not in seen:
                    seen.append(num)
                    self.Pm[j, len(seen) - 1] = am.BIG[p]
            self.Wm[j, :len(seen)] = seen
        jix = {k: j for j, k in enumerate(keys)}
        self.rj = np.array([jix[(int(d), int(o))] for d, o in zip(self.rd, self.ro)])  # row -> draw
        self.held = self.dates[-5:]
        self.cut = self.dates.index(self.held[0])
        self.M = np.column_stack([self.codes[f] for f in FACT])            # (dates, 78)

    def cell(self, fs):
        c = np.zeros(len(self.dates), np.int64)
        for f in fs:
            c = c * (int(self.codes[f].max()) + 1) + self.codes[f]
        return c


def counts(D, mask, key_rows, n_keys):
    """Digit counts (n_keys, 4, 10) of training rows grouped by key."""
    k = key_rows[mask]
    d = D.rdig[mask]
    out = np.zeros((n_keys, 4, 10))
    for p in range(4):
        out[:, p, :] = np.bincount(k * 10 + d[:, p], minlength=n_keys * 10).reshape(n_keys, 10)
    return out


def smooth(c, prior, alpha):
    """Dirichlet smoothing of counts c (n,4,10) toward prior (n,4,10) with strength alpha."""
    return (c + alpha * prior) / (c.sum(2, keepdims=True) + alpha)


# ---------------------------------------------------------------- models
class Global:
    name = "global"

    def __init__(self, D):
        self.D = D

    def fit(self, mask):
        self.p = smooth(counts(self.D, mask, self.D.ro, 3), np.full((3, 4, 10), 0.1), 10)
        return self

    def predict(self, J):
        return self.p[self.D.oj[J]]


class Match:
    def __init__(self, D, fs, alpha):
        self.D, self.fs, self.alpha = D, tuple(fs), alpha
        self.name = f"match[{' x '.join(fs)}] a={alpha}"
        self.c = D.cell(fs)
        self.U = int(self.c.max()) + 1

    def fit(self, mask, base=None):
        D = self.D
        self.base = base or Global(D).fit(mask)
        self.cnt = counts(D, mask, self.c[D.rd] * 3 + D.ro, self.U * 3)
        return self

    def predict(self, J):
        D = self.D
        prior = self.base.predict(J)
        return smooth(self.cnt[self.c[D.dj[J]] * 3 + D.oj[J]], prior, self.alpha)


class Backoff:
    def __init__(self, D, fs, alpha):
        self.D, self.fs, self.alpha = D, tuple(fs), alpha
        self.name = f"backoff[{' x '.join(fs)}] a={alpha}"
        self.levels = [Match(D, fs[:k], alpha) for k in range(1, len(fs) + 1)]

    def fit(self, mask):
        prev = Global(self.D).fit(mask)
        for lv in self.levels:
            lv.fit(mask, base=prev)
            prev = lv
        return self

    def predict(self, J):
        return self.levels[-1].predict(J)


class KNN:
    def __init__(self, D, factors, beta, alpha=200.0):
        self.D, self.beta, self.alpha = D, beta, alpha
        self.idx = [FACT.index(f) for f in factors]
        self.name = f"knn[{len(factors)} params] beta={beta}"

    def fit(self, mask):
        self.mask = mask
        self.g = Global(self.D).fit(mask)
        return self

    def predict(self, J):
        D = self.D
        M = D.M[:, self.idx]
        out = np.zeros((len(J), 4, 10))
        m = self.mask
        rd, ro, dg = D.rd[m], D.ro[m], D.rdig[m]
        prior = self.g.predict(J)
        for date in np.unique(D.dj[J]):
            sim = (M == M[date]).sum(1).astype(float)
            w = np.exp(self.beta * (sim - sim.max()))
            wr = w[rd]
            sel = np.flatnonzero(D.dj[J] == date)
            for i in sel:
                o = D.oj[J[i]]
                mo = ro == o
                c = np.stack([np.bincount(dg[mo, p], weights=wr[mo], minlength=10) for p in range(4)])
                c *= 1000.0 / max(c.sum(1).mean(), 1e-9)              # effective sample of 1000 rows
                out[i] = (c + self.alpha * prior[i]) / (c.sum(1, keepdims=True) + self.alpha)
        return out


class Softmax:
    refit_years = {2012, 2018}

    def __init__(self, D, factors, C):
        self.D, self.factors, self.C = D, factors, C
        self.name = f"softmax[{len(factors)} params] C={C}"
        from sklearn.preprocessing import OneHotEncoder
        self.enc = OneHotEncoder(handle_unknown="ignore")
        self.enc.fit(np.column_stack([np.arange(len(D.dates)) % 3] + [D.codes[f] for f in factors]))

    def X(self, dates, ops):
        return self.enc.transform(np.column_stack([ops] + [self.D.codes[f][dates] for f in self.factors]))

    def fit(self, mask):
        from sklearn.linear_model import LogisticRegression
        D = self.D
        X = self.X(D.rd[mask], D.ro[mask])
        self.models = [LogisticRegression(C=self.C, max_iter=200).fit(X, D.rdig[mask, p]) for p in range(4)]
        return self

    def predict(self, J):
        X = self.X(self.D.dj[J], self.D.oj[J])
        return np.stack([m.predict_proba(X) for m in self.models], 1)


class Ensemble:
    def __init__(self, D, members):
        self.D, self.members = D, members
        self.name = f"ensemble[{len(members)} match formulas]"

    def fit(self, mask):
        g = Global(self.D).fit(mask)
        for m in self.members:
            m.fit(mask, base=g)
        return self

    def predict(self, J):
        lp = np.mean([np.log(m.predict(J)) for m in self.members], 0)
        p = np.exp(lp)
        return p / p.sum(2, keepdims=True)


# ---------------------------------------------------------------- evaluation
def numbers(P, cold=False):
    order = np.argsort(P if cold else -P, axis=2, kind="stable")[:, :, :2]
    return (np.take_along_axis(order, BITS.T[None, :, :], 2) * POW[None, :, None]).sum(1)      # (n, 16)


def score(D, J, P):
    """Digit log-likelihood gain (nats, total) and hits / payout for hot and cold numbers."""
    rows = np.flatnonzero(np.isin(D.rj, J))
    pos = np.searchsorted(J, D.rj[rows])
    ll = float(sum(np.log(P[pos, p, D.rdig[rows, p]] / 0.1).sum() for p in range(4)))
    res = {"ll": ll, "digits": 4 * len(rows), "draws": len(J), "winners": int((D.Wm[J] >= 0).sum())}
    for name, cold in (("hot", False), ("cold", True)):
        N = numbers(P, cold)
        for k in (1, 16):
            eq = (N[:, :k, None] == D.Wm[J][:, None, :])
            res[f"{name}{k}_hits"] = int(eq.any(2).sum())
            res[f"{name}{k}_pay"] = float((eq * D.Pm[J][:, None, :]).sum())
    return res


def merge(a, b):
    return {k: a.get(k, 0) + b[k] for k in b}


def run_model(D, make, yearly=True):
    """Walk forward: validation + test with refits, then the frozen last-5 prediction."""
    tot = {"validation": {}, "test": {}}
    model = None
    for y in range(VALID[0], int(D.yj.max()) + 1):
        J = np.flatnonzero((D.yj == y) & (D.dj < D.cut))
        if not len(J):
            continue
        if model is None or yearly or y in getattr(make(), "refit_years", ()):
            model = make().fit((D.ry < y) & (D.rd < D.cut))
        per = "validation" if y < TEST else "test"
        tot[per] = merge(tot[per], score(D, J, model.predict(J)))
    J = np.flatnonzero(D.dj >= D.cut)
    final = make().fit(D.rd < D.cut)
    P = final.predict(J)
    tot["last5"] = score(D, J, P)
    hits = []
    for name, cold in (("hot", False), ("cold", True)):
        N = numbers(P, cold)
        for i, j in enumerate(J):
            for n in N[i]:
                if n in D.Wm[j]:
                    hits.append(f"{name} {D.dates[D.dj[j]][5:]} {am.OPS[D.oj[j]]} {n:04d}")
    tot["last5"]["detail"] = hits
    return tot


def describe(name, r):
    def gain(x):
        return 1000 * x["ll"] / x["digits"]

    def lift(x, key, k):
        e = k * x["winners"] / 10000
        return x[key] / e if e else 0

    v, t, l5 = r["validation"], r["test"], r["last5"]
    return (f"{name:<52} digit ll (milli-nats/digit) valid {gain(v):+.2f} test {gain(t):+.2f} | "
            f"test lift hot1 x{lift(t, 'hot1_hits', 1):.2f} hot16 x{lift(t, 'hot16_hits', 16):.2f} "
            f"cold1 x{lift(t, 'cold1_hits', 1):.2f} cold16 x{lift(t, 'cold16_hits', 16):.2f} | last5 hits "
            f"hot1 {l5['hot1_hits']} hot16 {l5['hot16_hits']} cold1 {l5['cold1_hits']} cold16 {l5['cold16_hits']}")


# ---------------------------------------------------------------- main
def main():
    t0 = time.time()
    D = Data()
    results = {}

    def go(make, yearly=True):
        name = make().name
        results[name] = run_model(D, make, yearly)
        print(describe(name, results[name]), f"({time.time() - t0:.0f}s)", flush=True)

    go(lambda: Global(D))
    prev = json.load(open(os.path.join(ROOT, "analysis", "s12_combos_results.json")))
    combos = []
    for key, v in prev.items():
        if "|" in key:
            combos += [tuple(b["formula"].split(" x ")) for b in v["best"]]
    combos = list(dict.fromkeys(combos))
    print(f"{len(combos)} parameter combinations from the earlier consistency search", flush=True)
    # 1. smoothing strength for exact match, chosen on validation
    for a in (50, 200, 1000):
        for fs in combos[:6]:
            go(lambda fs=fs, a=a: Match(D, fs, a))
    best_alpha = max((50, 200, 1000), key=lambda a: np.mean(
        [results[k]["validation"]["ll"] for k in results if k.endswith(f"a={a}") and k.startswith("match")]))
    print("best smoothing alpha on validation:", best_alpha, flush=True)
    for fs in combos[6:]:
        go(lambda fs=fs: Match(D, fs, best_alpha))
    # 2. backoff for triples
    for fs in [c for c in combos if len(c) == 3]:
        go(lambda fs=fs: Backoff(D, fs, best_alpha))
    # 3. similar days
    for fam_name, fam in (("vedic", am.VEDIC), ("chinese", am.CHINESE), ("both", FACT)):
        for beta in (0.1, 0.3):
            go(lambda fam=fam, beta=beta: KNN(D, fam, beta))
    # 4. softmax regression (refit 2012, 2018, last-5 cut)
    for C in (0.001, 0.01):
        go(lambda C=C: Softmax(D, FACT, C), yearly=False)
    # 5. ensemble of the best match formulas by validation log-likelihood
    ranked = sorted((k for k in results if k.startswith("match")), key=lambda k: -results[k]["validation"]["ll"])
    for N in (5, 20):
        fsN = [tuple(k[len("match["):k.index("]")].split(" x ")) for k in ranked[:N]]
        go(lambda fsN=fsN: Ensemble(D, [Match(D, fs, best_alpha) for fs in fsN]))
    sel = max(results, key=lambda k: results[k]["validation"]["ll"] / results[k]["validation"]["digits"])
    print(f"\nselected by validation digit log-likelihood: {sel}")
    print(describe(sel, results[sel]))
    json.dump({"selected": sel, "best_alpha": best_alpha, "held_out": D.held, "models": results},
              open(OUT, "w"), indent=1, default=float)
    print(f"done in {time.time() - t0:.0f}s")


def predict(date, model_name):
    D = Data()
    res = json.load(open(OUT))
    name = model_name or res["selected"]
    a = res["best_alpha"]
    # rebuild the model from its name
    if name.startswith("match["):
        fs = name[6:name.index("]")].split(" x ")
        make = lambda: Match(D, fs, a)  # noqa: E731
    elif name.startswith("backoff["):
        fs = name[8:name.index("]")].split(" x ")
        make = lambda: Backoff(D, fs, a)  # noqa: E731
    elif name == "global":
        make = lambda: Global(D)  # noqa: E731
    else:
        sys.exit(f"predict supports global / match / backoff models; got {name}")
    ix, codes2, ctx = am.date_codes(date, D.codes, D.labels, FACT)
    for f in FACT:
        D.codes[f] = codes2[f]
    D.dates.append(date)
    D.M = np.column_stack([D.codes[f] for f in FACT])
    model = make().fit(np.ones(len(D.rd), bool))
    D.dj = np.append(D.dj, [ix] * 3)
    D.oj = np.append(D.oj, [0, 1, 2])
    J = np.arange(len(D.dj) - 3, len(D.dj))
    P = model.predict(J)
    print(f"{name} for {date}:")
    for i, op in enumerate(am.OPS):
        for lab, cold in (("hot", False), ("cold", True)):
            N = numbers(P[i:i + 1], cold)[0]
            print(f"  {op:<12} {lab:<4} #1 {N[0]:04d} | 16: " + " ".join(f"{n:04d}" for n in N))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", nargs="?", default="evaluate", choices=["evaluate", "predict"])
    ap.add_argument("--date")
    ap.add_argument("--model")
    a = ap.parse_args()
    if a.mode == "predict":
        predict(a.date, a.model)
    else:
        main()
