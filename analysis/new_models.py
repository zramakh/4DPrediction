#!/usr/bin/env python3
"""Five further predictive models for 4D, walk-forward tested.

M1 change-point   Bayesian online change-point detection (Adams & MacKay) on
                  the digit mix of each operator x position: the predictive
                  distribution mixes over "how long the current regime has run"
M2 autoregression ridge regression of the next draw's digit shares on the
                  digit shares of the last 1 / 5 / 20 / 100 draws of the same
                  operator and the latest draw of the other two operators
M3 hazard         P(number wins) as a learned function of the draws since it
                  last won (log-binned hazard curve), per operator
M4 neural net     MLP (sklearn) per digit position on the M2 features + the
                  date's main Vedic / Chinese parameters + operator
M5 shape          probability of each number "shape" class (repeat pattern x
                  digit-sum band x number of odd digits) from exponentially
                  weighted recent winners; numbers share their class probability

Digit models (M1, M2, M4) are scored by digit log-likelihood, number models
(M3, M5) by number log-likelihood; all by hits of their top 1 / top 16 numbers.
Validation 2012-2017 picks each model's settings; test 2018 .. day before the
last 5 known draws; last 5 draws with fitted settings frozen before them
(online models still read the previous draw's result, as in real use).

Run from the repo root:  python3 analysis/new_models.py
"""

import json
import math
import os
import sys
import time
from scipy.special import gammaln

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import digit_models as dm  # noqa: E402

ROOT = dm.ROOT
DIG = dm.DIG
OUT = os.path.join(ROOT, "analysis", "new_models_results.json")
D = None


def period_of(j):
    if D.dj[j] >= D.cut:
        return "last5"
    y = D.yj[j]
    if 2012 <= y < 2018:
        return "validation"
    if y >= 2018:
        return "test"
    return None


class Tally:
    def __init__(self, level):
        self.level = level
        self.t = {p: {"ll": 0.0, "n": 0, "draws": 0, "winners": 0, "hot1": 0, "hot16": 0, "cold1": 0, "cold16": 0,
                      "pay16": 0.0, "detail": []} for p in ("validation", "test", "last5")}

    def digits(self, j, P):
        per = period_of(j)
        if per is None:
            return
        t = self.t[per]
        w = D.Wm[j][D.Wm[j] >= 0]
        t["ll"] += float(sum(np.log(P[p, DIG[w, p]] / 0.1).sum() for p in range(4)))
        t["n"] += 4 * len(w)
        self._hits(t, j, dm.numbers(P[None], False)[0], dm.numbers(P[None], True)[0])

    def numbers(self, j, logp, rng):
        per = period_of(j)
        if per is None:
            return
        t = self.t[per]
        w = D.Wm[j][D.Wm[j] >= 0]
        t["ll"] += float((logp[w] + math.log(10000)).sum())
        t["n"] += len(w)
        s = logp + rng.random(10000) * 1e-9
        order = np.argsort(-s)
        self._hits(t, j, order[:16], order[::-1][:16])

    def _hits(self, t, j, hot, cold):
        w = list(D.Wm[j])
        t["draws"] += 1
        t["winners"] += int((D.Wm[j] >= 0).sum())
        for name, N in (("hot", hot), ("cold", cold)):
            t[f"{name}1"] += int(N[0] in w)
            h = [n for n in N if n in w]
            t[f"{name}16"] += len(h)
            if name == "hot":
                t["pay16"] += sum(D.Pm[j][w.index(n)] for n in h)
            if D.dj[j] >= D.cut:
                t["detail"] += [f"{name} {D.dates[D.dj[j]][5:]} {dm.am.OPS[D.oj[j]]} {n:04d}" for n in h]

    def summary(self):
        out = {}
        for p, t in self.t.items():
            e1 = t["winners"] / 10000
            out[p] = {"ll_milli_per_unit": 1000 * t["ll"] / max(t["n"], 1), "draws": t["draws"],
                      "hot1": t["hot1"], "hot16": t["hot16"], "cold1": t["cold1"], "cold16": t["cold16"],
                      "exp1": round(e1, 2), "exp16": round(16 * e1, 2),
                      "lift_hot16": t["hot16"] / (16 * e1) if e1 else None,
                      "lift_cold16": t["cold16"] / (16 * e1) if e1 else None,
                      "big16_per_RM1": t["pay16"] / (16 * t["draws"]) if t["draws"] else None,
                      "detail": t["detail"]}
        return out


def op_sequences():
    seqs = {}
    for o in range(3):
        seqs[o] = np.flatnonzero(D.oj == o)            # already in time order
    return seqs


def shares(j):
    w = D.Wm[j][D.Wm[j] >= 0]
    S = np.zeros((4, 10))
    for p in range(4):
        S[p] = np.bincount(DIG[w, p], minlength=10)
    return S / len(w), S


# ---------------------------------------------------------------- M1 change-point
def m1(H, a0, R=200):
    tal = Tally("digit")
    a = a0 / 10
    lh, l1h = math.log(1 / H), math.log(1 - 1 / H)
    for o, seq in op_sequences().items():
        C = [np.zeros((1, 10)) for _ in range(4)]
        L = [np.zeros(1) for _ in range(4)]
        for j in seq:
            P = np.zeros((4, 10))
            for p in range(4):
                w = np.exp(L[p] - L[p].max())
                w /= w.sum()
                P[p] = (w[:, None] * (C[p] + a) / (C[p].sum(1, keepdims=True) + a0)).sum(0)
            tal.digits(j, P)
            _, X = shares(j)
            for p in range(4):
                x = X[p]
                A = C[p] + a
                As = A.sum(1)
                ll = gammaln(As) - gammaln(As + x.sum()) + (gammaln(A + x) - gammaln(A)).sum(1)
                grow = L[p] + ll + l1h
                cp = np.logaddexp.reduce(L[p] + ll + lh)
                L[p] = np.concatenate([[cp], grow])
                C[p] = np.vstack([np.zeros((1, 10)), C[p] + x])
                if len(L[p]) > R:
                    keep = np.argsort(-L[p])[:R]
                    keep.sort()
                    L[p], C[p] = L[p][keep], C[p][keep]
                L[p] -= np.logaddexp.reduce(L[p])
    return tal


# ---------------------------------------------------------------- M2 / M4 features
def ar_features():
    n = len(D.dj)
    S = np.zeros((n, 40))
    for j in range(n):
        S[j] = shares(j)[0].ravel()
    base = S.mean(0)
    X = np.zeros((n, 240))
    for o, seq in op_sequences().items():
        cs = np.vstack([np.zeros(40), np.cumsum(S[seq], 0)])
        for i, j in enumerate(seq):
            for b, k in enumerate((1, 5, 20, 100)):
                lo = max(0, i - k)
                X[j, 40 * b:40 * (b + 1)] = (cs[i] - cs[lo]) / (i - lo) if i > lo else base
    # latest earlier-dated draw of each other operator
    for o in range(3):
        others = [q for q in range(3) if q != o]
        for slot, q in enumerate(others):
            sq = op_sequences()[q]
            dq = D.dj[sq]
            for j in op_sequences()[o]:
                k = np.searchsorted(dq, D.dj[j]) - 1
                X[j, 160 + 40 * slot:200 + 40 * slot] = S[sq[k]] if k >= 0 else base
    return X, S


def m2(lam, X, S):
    tal = Tally("digit")
    mu, sd = X.mean(0), X.std(0) + 1e-9
    Z = (X - mu) / sd
    fitted = {}
    for j in range(len(D.dj)):
        per = period_of(j)
        if per is None:
            continue
        key = 2012 if per == "validation" else (2018 if per == "test" else "cut")
        if key not in fitted:
            tr = (D.yj < key) if key != "cut" else (D.dj < D.cut)
            tr &= D.yj >= 1987
            A = np.hstack([Z[tr], np.ones((tr.sum(), 1))])
            W = np.linalg.solve(A.T @ A + lam * np.eye(A.shape[1]), A.T @ S[tr])
            fitted[key] = W
        pred = (np.append(Z[j], 1) @ fitted[key]).reshape(4, 10)
        P = np.clip(pred, 1e-3, None)
        tal.digits(j, P / P.sum(1, keepdims=True))
    return tal


def m4(hidden, alpha, X, S):
    from sklearn.neural_network import MLPClassifier
    from sklearn.preprocessing import OneHotEncoder
    tal = Tally("digit")
    cats = ["nakshatra", "tithi", "day_stem", "day_branch", "lunar_month", "weekday", "moon_rashi"]
    enc = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    C = np.column_stack([D.oj] + [D.codes[f][D.dj] for f in cats])
    enc.fit(C)
    mu, sd = X.mean(0), X.std(0) + 1e-9
    F = np.hstack([(X - mu) / sd, enc.transform(C)])
    rng = np.random.default_rng(4)
    fitted = {}
    for j in range(len(D.dj)):
        per = period_of(j)
        if per is None:
            continue
        key = 2012 if per == "validation" else (2018 if per == "test" else "cut")
        if key not in fitted:
            tr = np.flatnonzero(((D.yj < key) if key != "cut" else (D.dj < D.cut)) & (D.yj >= 1987))
            tr = rng.choice(tr, min(len(tr), 6000), replace=False)
            rows_j, rows_d = [], []
            for jj in tr:
                w = D.Wm[jj][D.Wm[jj] >= 0]
                rows_j += [jj] * len(w)
                rows_d.append(DIG[w])
            Xtr = F[np.array(rows_j)]
            Ytr = np.vstack(rows_d)
            fitted[key] = [MLPClassifier(hidden_layer_sizes=hidden, alpha=alpha, max_iter=60, early_stopping=True,
                                         random_state=p).fit(Xtr, Ytr[:, p]) for p in range(4)]
        P = np.stack([m.predict_proba(F[j:j + 1])[0] for m in fitted[key]])
        tal.digits(j, P)
    return tal


# ---------------------------------------------------------------- M3 hazard
def m3(nbins):
    tal = Tally("number")
    rng = np.random.default_rng(3)
    edges = np.unique(np.round(np.logspace(0, np.log10(4000), nbins)).astype(int))
    nb = len(edges) + 1
    win_c = np.zeros(nb)
    exp_c = np.zeros(nb)
    pending = {}                                       # year -> (wins, exposures) added at year start
    # gaps must be tracked per operator in time order, but the hazard is pooled; process draws by date
    last = np.full((3, 10000), -1)
    count = np.zeros(3, int)
    hz = {}
    cur_key = None
    order = np.argsort(D.dj, kind="stable")
    acc_w = {}
    acc_e = {}
    for j in order:
        o = D.oj[j]
        gap = np.where(last[o] >= 0, count[o] - last[o], 4000)
        b = np.searchsorted(edges, gap)
        y = D.yj[j]
        per = period_of(j)
        if per is not None:
            key = y if per != "last5" else "cut"
            if key not in hz:
                # hazard from all draws before the year (or before the cut)
                we = np.zeros(nb)
                ee = np.zeros(nb)
                for k, v in acc_w.items():
                    if (key == "cut") or k < key:
                        we += v
                        ee += acc_e[k]
                hz[key] = np.log((we + 1) / (ee + 1e4))
            lp = hz[key][b]
            lp = lp - np.logaddexp.reduce(lp)
            tal.numbers(j, lp, rng)
        w = D.Wm[j][D.Wm[j] >= 0]
        acc_w[y] = acc_w.get(y, np.zeros(nb)) + np.bincount(b[w], minlength=nb)
        acc_e[y] = acc_e.get(y, np.zeros(nb)) + np.bincount(b, minlength=nb)
        count[o] += 1
        last[o, w] = count[o]
    return tal


# ---------------------------------------------------------------- M5 shape
def shape_classes():
    s = np.array([f"{n:04d}" for n in range(10000)])
    runs = [tuple(sorted(np.unique(list(x), return_counts=True)[1])) for x in s]
    pat = np.array([{(4,): 0, (1, 3): 1, (2, 2): 2, (1, 1, 2): 3, (1, 1, 1, 1): 4}[r] for r in runs])
    dsum = DIG.sum(1)
    band = np.digitize(dsum, [10, 15, 19, 23, 28])
    odd = (DIG % 2).sum(1)
    cls = pat * 30 + band * 5 + odd
    size = np.bincount(cls, minlength=150)
    return cls, size


def m5(H, kappa):
    tal = Tally("number")
    rng = np.random.default_rng(5)
    cls, size = shape_classes()
    base = size / 10000
    decay = 0.5 ** (1 / H)
    ew = np.zeros((3, 150))
    for j in np.argsort(D.dj, kind="stable"):
        o = D.oj[j]
        pc = (ew[o] + kappa * base) / (ew[o].sum() + kappa)
        lp = np.log(pc[cls] / np.maximum(size[cls], 1))
        tal.numbers(j, lp - np.logaddexp.reduce(lp), rng)
        w = D.Wm[j][D.Wm[j] >= 0]
        ew[o] = ew[o] * decay + np.bincount(cls[w], minlength=150)
    return tal


# ---------------------------------------------------------------- main
def main():
    global D
    t0 = time.time()
    D = dm.Data()
    res = {}

    def run(name, fn):
        s = fn().summary()
        res[name] = s
        v, t, l = s["validation"], s["test"], s["last5"]
        print(f"{name:<34} ll valid {v['ll_milli_per_unit']:+7.2f} test {t['ll_milli_per_unit']:+7.2f} | "
              f"test hot1 {t['hot1']}/{t['exp1']} hot16 x{t['lift_hot16']:.2f} cold16 x{t['lift_cold16']:.2f} "
              f"Big16 RM{t['big16_per_RM1']:.2f} | last5 hot1 {l['hot1']} hot16 {l['hot16']} cold16 {l['cold16']} "
              f"({time.time() - t0:.0f}s)", flush=True)

    for H in (300, 2000):
        for a0 in (50, 500):
            run(f"M1 change-point H={H} a0={a0}", lambda H=H, a0=a0: m1(H, a0))
    X, S = ar_features()
    for lam in (1e2, 1e4, 1e6):
        run(f"M2 autoregression lambda={lam:g}", lambda lam=lam: m2(lam, X, S))
    for nb in (12, 30):
        run(f"M3 hazard bins={nb}", lambda nb=nb: m3(nb))
    for H in (50, 500, 5000):
        for kappa in (500, 5000):
            run(f"M5 shape H={H} kappa={kappa}", lambda H=H, kappa=kappa: m5(H, kappa))
    for hidden, alpha in (((32,), 1e-2), ((64, 32), 1e-3)):
        run(f"M4 neural net {hidden} alpha={alpha:g}", lambda hidden=hidden, alpha=alpha: m4(hidden, alpha, X, S))
    best = {}
    for fam in ("M1", "M2", "M3", "M4", "M5"):
        ks = [k for k in res if k.startswith(fam)]
        best[fam] = max(ks, key=lambda k: res[k]["validation"]["ll_milli_per_unit"])
    print("\nBest setting per model (chosen on 2012-2017):")
    for fam, k in best.items():
        v, t, l = res[k]["validation"], res[k]["test"], res[k]["last5"]
        print(f"  {k:<34} valid {v['ll_milli_per_unit']:+.2f} test {t['ll_milli_per_unit']:+.2f}; test hits top16 "
              f"{t['hot16']}/{t['exp16']} (x{t['lift_hot16']:.2f}); last 5: {l['hot16']} hits {l['detail'][:4]}")
    json.dump({"best": best, "models": res}, open(OUT, "w"), indent=1, default=float)
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
