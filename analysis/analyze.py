#!/usr/bin/env python3
"""Look for exploitable structure in Malaysian 4D results.

Part 1 tests the draws against the "fair draw" hypothesis: every winning number
is an independent, uniform pick from 0000-9999, unrelated to the date, the day,
the previous draw or the other operators.

Part 2 backtests prediction strategies walk-forward (each draw is predicted
using only earlier draws) and compares their hit rate with random picking.

Run from the repo root:  python3 analysis/analyze.py
Writes analysis/results.json and prints a summary.
"""

import csv
import json
import math
import os
from collections import Counter, defaultdict

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPERATORS = {"Magnum": "magnum", "Sports Toto": "sportstoto", "Da Ma Cai": "damacai"}
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
RNG = np.random.default_rng(4)
TESTS = []  # every hypothesis test, for multiple-comparison correction


# ---------------------------------------------------------------- statistics
def chi2_sf(x, df):
    """Upper tail of the chi-square distribution (Wilson-Hilferty approximation;
    accurate to ~1e-3 for df >= 3, which is all we use)."""
    if x <= 0:
        return 1.0
    z = ((x / df) ** (1 / 3) - (1 - 2 / (9 * df))) / math.sqrt(2 / (9 * df))
    return 0.5 * math.erfc(z / math.sqrt(2))


def norm_sf(z):
    return 0.5 * math.erfc(z / math.sqrt(2))


def record(name, operator, stat, p, detail=""):
    TESTS.append({"test": name, "operator": operator, "stat": round(stat, 3), "p": p, "detail": detail})


def chi2_uniform(counts, label, op):
    counts = np.asarray(counts, float)
    exp = counts.sum() / counts.size
    stat = float(((counts - exp) ** 2 / exp).sum())
    df = counts.size - 1
    record(label, op, stat, chi2_sf(stat, df), f"chi2={stat:.1f}, df={df}")


def chi2_contingency(table, label, op):
    t = np.asarray(table, float)
    t = t[t.sum(1) > 0][:, t.sum(0) > 0]
    exp = np.outer(t.sum(1), t.sum(0)) / t.sum()
    stat = float(((t - exp) ** 2 / exp).sum())
    df = (t.shape[0] - 1) * (t.shape[1] - 1)
    record(label, op, stat, chi2_sf(stat, df), f"chi2={stat:.1f}, df={df}")


# ---------------------------------------------------------------- data
def load(stem):
    draws = defaultdict(lambda: {"day": None, "top": [], "all": [], "by_prize": defaultdict(list)})
    with open(os.path.join(ROOT, "data", f"{stem}.csv"), newline="") as f:
        for r in csv.DictReader(f):
            d = draws[r["date"]]
            d["day"] = r["day"]
            n = int(r["4d_number"])
            d["all"].append(n)
            d["by_prize"][r["prize"]].append(n)
            if r["prize"] in ("1st", "2nd", "3rd"):
                d["top"].append(n)
            if r["prize"] == "1st":
                d["first"] = n
    out = []
    for date in sorted(draws):
        d = draws[date]
        out.append({"date": date, "day": d["day"], "first": d.get("first"), "top": d["top"],
                    "all": d["all"], "set": set(d["all"]), "by_prize": d["by_prize"]})
    return out


def digits(n):
    return (n // 1000, n // 100 % 10, n // 10 % 10, n % 10)


# ---------------------------------------------------------------- part 1
def test_uniformity(op, draws):
    nums = [n for d in draws for n in d["all"]]
    firsts = [d["first"] for d in draws]
    # Digit frequency in each of the 4 positions.
    for pos in range(4):
        chi2_uniform(np.bincount([digits(n)[pos] for n in nums], minlength=10),
                     f"digit uniformity, position {pos + 1} (all prizes)", op)
        chi2_uniform(np.bincount([digits(n)[pos] for n in firsts], minlength=10),
                     f"digit uniformity, position {pos + 1} (1st prize)", op)
    # Every one of the 10,000 numbers equally likely.
    counts = np.bincount(nums, minlength=10000)
    chi2_uniform(counts, "number frequency uniformity (10,000 numbers)", op)
    # Leading digit pair 00-99 (catches clustering in ranges).
    chi2_uniform(np.bincount([n // 100 for n in nums], minlength=100), "first-two-digit uniformity", op)
    # Digit-sum distribution vs the exact theoretical distribution.
    theo = np.zeros(37)
    for n in range(10000):
        theo[sum(digits(n))] += 1
    obs = np.bincount([sum(digits(n)) for n in nums], minlength=37)
    exp = theo / 10000 * len(nums)
    m = exp >= 5
    stat = float(((obs[m] - exp[m]) ** 2 / exp[m]).sum())
    record("digit-sum distribution", op, stat, chi2_sf(stat, int(m.sum()) - 1))
    # Pattern classes (all different / one pair / two pairs / triple / quad).
    def pattern(n):
        return tuple(sorted(Counter(digits(n)).values()))
    theo_p = Counter(pattern(n) for n in range(10000))
    obs_p = Counter(pattern(n) for n in nums)
    keys = sorted(theo_p)
    o = np.array([obs_p[k] for k in keys], float)
    e = np.array([theo_p[k] / 10000 * len(nums) for k in keys])
    stat = float(((o - e) ** 2 / e).sum())
    record("digit-pattern classes (aabb, abcd, ...)", op, stat, chi2_sf(stat, len(keys) - 1))
    return {
        "numbers_drawn": len(nums),
        "hottest": [(int(n), int(c)) for n, c in sorted(enumerate(counts), key=lambda x: -x[1])[:5]],
        "coldest": [(int(n), int(c)) for n, c in sorted(enumerate(counts), key=lambda x: x[1])[:5]],
        "expected_per_number": round(len(nums) / 10000, 2),
        "count_sd": round(float(counts.std()), 2),
        "poisson_sd": round(math.sqrt(len(nums) / 10000), 2),
    }


def test_time_effects(op, draws):
    # Does the day of the week change which digits come up?
    for pos in range(4):
        t = np.zeros((7, 10))
        for d in draws:
            for n in d["all"]:
                t[DAYS.index(d["day"]), digits(n)[pos]] += 1
        chi2_contingency(t, f"day-of-week vs digit, position {pos + 1}", op)
    # Month of year.
    t = np.zeros((12, 10))
    for d in draws:
        for n in d["all"]:
            t[int(d["date"][5:7]) - 1, digits(n)[0]] += 1
    chi2_contingency(t, "month vs first digit", op)
    # Day of month (1-31) vs number's last two digits mod 10.
    t = np.zeros((31, 10))
    for d in draws:
        for n in d["all"]:
            t[int(d["date"][8:]) - 1, n % 10] += 1
    chi2_contingency(t, "day-of-month vs last digit", op)
    # Drift across eras (5-year bins).
    t = np.zeros((10, 10))
    for d in draws:
        for n in d["all"]:
            t[(int(d["date"][:4]) - 1985) // 5, digits(n)[0]] += 1
    chi2_contingency(t, "era (5-year bins) vs first digit", op)
    # Is the number related to the date itself (e.g. DDMM, MMDD, YYYY)?
    hits, possible = 0, 0
    for d in draws:
        y, mo, dd = d["date"].split("-")
        cands = {int(dd + mo), int(mo + dd), int(y), int(y[2:] + mo), int(y[2:] + dd)}
        hits += len(cands & d["set"])
        possible += len(cands) * len(d["set"])
    exp = possible / 10000
    z = (hits - exp) / math.sqrt(exp)
    record("date-derived numbers (DDMM, MMDD, YYYY...)", op, z, norm_sf(z), f"{hits} hits vs {exp:.1f} expected")


def test_serial(op, draws):
    # Overlap between consecutive draws' winning sets.
    overlap = sum(len(a["set"] & b["set"]) for a, b in zip(draws, draws[1:]))
    exp = sum(len(a["set"]) * len(b["set"]) / 10000 for a, b in zip(draws, draws[1:]))
    z = (overlap - exp) / math.sqrt(exp)
    record("repeat of previous draw's numbers", op, z, 2 * norm_sf(abs(z)), f"{overlap} vs {exp:.1f} expected")
    # Same number reappearing within k draws, for k = 2..10.
    for k in (2, 5, 10):
        obs = sum(len(draws[i]["set"] & set().union(*(draws[j]["set"] for j in range(i - k, i))))
                  for i in range(k, len(draws)))
        # P(a given number is in the union of k previous sets) ~= 1-(1-23/10000)^k
        exp = sum(len(draws[i]["set"]) * (1 - (1 - 23 / 10000) ** k) for i in range(k, len(draws)))
        z = (obs - exp) / math.sqrt(exp)
        record(f"repeat within last {k} draws", op, z, 2 * norm_sf(abs(z)), f"{obs} vs {exp:.1f} expected")
    # Digit-to-digit transition: does position p's digit in the previous 1st prize
    # predict position p's digit in the next 1st prize?
    for pos in range(4):
        t = np.zeros((10, 10))
        for a, b in zip(draws, draws[1:]):
            t[digits(a["first"])[pos], digits(b["first"])[pos]] += 1
        chi2_contingency(t, f"1st-prize digit transition, position {pos + 1}", op)
    # Lag-1..5 autocorrelation of the 1st-prize number as a value.
    x = np.array([d["first"] for d in draws], float)
    x = (x - x.mean()) / x.std()
    for lag in (1, 2, 3, 5):
        r = float((x[:-lag] * x[lag:]).mean())
        z = r * math.sqrt(len(x) - lag)
        record(f"1st-prize autocorrelation, lag {lag}", op, z, 2 * norm_sf(abs(z)), f"r={r:+.4f}")
    # Within one draw: are the 23 numbers related (e.g. share digits beyond chance)?
    shared, pairs = 0, 0
    for d in draws:
        a = d["all"]
        for i in range(len(a)):
            for j in range(i + 1, len(a)):
                shared += a[i] % 10 == a[j] % 10
                pairs += 1
    z = (shared - pairs / 10) / math.sqrt(pairs * 0.09)
    record("within-draw: numbers sharing last digit", op, z, 2 * norm_sf(abs(z)), f"{shared} vs {pairs / 10:.0f}")


def test_cross_operator(data):
    names = list(data)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a = {d["date"]: d["set"] for d in data[names[i]]}
            b = {d["date"]: d["set"] for d in data[names[j]]}
            common = sorted(set(a) & set(b))
            obs = sum(len(a[k] & b[k]) for k in common)
            exp = sum(len(a[k]) * len(b[k]) / 10000 for k in common)
            z = (obs - exp) / math.sqrt(exp)
            record("same-day overlap between operators", f"{names[i]} / {names[j]}", z,
                   2 * norm_sf(abs(z)), f"{obs} vs {exp:.1f} expected over {len(common)} days")
            # Does one operator's draw predict the other's NEXT draw?
            bd = sorted(b)
            obs = exp = 0
            for k in common:
                nxt = next((x for x in bd if x > k), None)
                if nxt:
                    obs += len(a[k] & b[nxt])
                    exp += len(a[k]) * len(b[nxt]) / 10000
            z = (obs - exp) / math.sqrt(exp)
            record("operator A today -> operator B next draw", f"{names[i]} -> {names[j]}", z,
                   2 * norm_sf(abs(z)), f"{obs} vs {exp:.1f} expected")


# ---------------------------------------------------------------- part 2
def features(counts, recent, last_seen, t, n_draws):
    """Per-number feature matrix (10000 x F) using only history before draw t."""
    gap = np.where(last_seen >= 0, t - last_seen, t + 1).astype(float)
    total = counts / max(n_draws, 1)
    return np.column_stack([
        (total - total.mean()) / (total.std() + 1e-9),
        (recent - recent.mean()) / (recent.std() + 1e-9),
        (gap - gap.mean()) / (gap.std() + 1e-9),
        np.log1p(gap),
        (last_seen == t - 1).astype(float),
    ])


def backtest(op, draws, test_from=0.6, K=23, window=100):
    """Walk forward through every draw. Each strategy picks K numbers using only
    earlier draws; we count how many of the actual winning numbers it caught."""
    sets = [np.array(sorted(d["set"])) for d in draws]
    counts = np.zeros(10000)
    last_seen = np.full(10000, -1)
    recent = np.zeros(10000)
    dow_counts = {day: np.zeros(10000) for day in DAYS}
    pos_digit = np.ones((4, 10))
    trans = np.ones((4, 10, 10))
    allnums = np.arange(10000)
    dig = np.array([digits(n) for n in allnums])

    start = int(len(draws) * test_from)
    strategies = ["random", "hot (all-time)", "hot (last 100 draws)", "cold / overdue",
                  "repeat last draw", "day-of-week hot", "digit-frequency model",
                  "digit Markov model", "logistic regression"]
    hits = {s: 0 for s in strategies}
    picks = 0
    caught = 0
    X_train, y_train = [], []
    w = None

    for t, d in enumerate(draws):
        actual = sets[t]
        if t >= start and t > window:
            if w is None:  # fit logistic regression once, on the training period only
                X = np.vstack(X_train)
                y = np.concatenate(y_train)
                w = fit_logistic(X, y)
            pred = {}
            pred["random"] = RNG.choice(10000, K, replace=False)
            pred["hot (all-time)"] = topk(counts, K)
            pred["hot (last 100 draws)"] = topk(recent, K)
            pred["cold / overdue"] = topk(np.where(last_seen >= 0, t - last_seen, 10 ** 6), K)
            prev = sets[t - 1]
            pred["repeat last draw"] = prev[:K]
            pred["day-of-week hot"] = topk(dow_counts[d["day"]], K)
            lp = sum(np.log(pos_digit[p][dig[:, p]] / pos_digit[p].sum()) for p in range(4))
            pred["digit-frequency model"] = topk(lp, K)
            pf = digits(draws[t - 1]["first"])
            lm = sum(np.log(trans[p, pf[p]][dig[:, p]] / trans[p, pf[p]].sum()) for p in range(4))
            pred["digit Markov model"] = topk(lm, K)
            Xf = features(counts, recent, last_seen, t, t)
            pred["logistic regression"] = topk(Xf @ w[1:] + w[0], K)
            for s in strategies:
                hits[s] += len(np.intersect1d(pred[s][:K], actual))
            picks += K
            caught += len(actual)
        elif t > window:
            # Training rows: every winner plus 300 random non-winners. Negative
            # subsampling only shifts the intercept, not the ranking we use.
            Xf = features(counts, recent, last_seen, t, t)
            neg = np.setdiff1d(RNG.choice(10000, 300, replace=False), actual)
            rows = np.concatenate([actual, neg])
            X_train.append(Xf[rows])
            y_train.append(np.concatenate([np.ones(len(actual)), np.zeros(len(neg))]))

        # update history with draw t
        counts[actual] += 1
        last_seen[actual] = t
        recent[actual] += 1
        if t >= window:
            recent[sets[t - window]] -= 1
        dow_counts[d["day"]][actual] += 1
        for n in d["all"]:
            for p, v in enumerate(digits(n)):
                pos_digit[p][v] += 1
        if t > 0:
            a, b = digits(draws[t - 1]["first"]), digits(d["first"])
            for p in range(4):
                trans[p, a[p], b[p]] += 1

    n_test = len(draws) - max(start, window + 1)
    # Expected hits for K random picks against ~23 winners out of 10,000.
    exp = K * caught / 10000
    out = {"test_draws": n_test, "picks_per_draw": K, "expected_hits_random": round(exp, 1), "strategies": {}}
    for s in strategies:
        z = (hits[s] - exp) / math.sqrt(exp)
        out["strategies"][s] = {"hits": hits[s], "hit_rate_per_pick": hits[s] / picks,
                                "vs_random": round(hits[s] / exp, 3), "z": round(z, 2),
                                "p_one_sided": norm_sf(z)}
    return out


def topk(score, k):
    return np.argpartition(-score, k)[:k]


def fit_logistic(X, y, iters=300, lr=0.5):
    Xb = np.column_stack([np.ones(len(X)), X])
    w = np.zeros(Xb.shape[1])
    w[0] = math.log(y.mean() / (1 - y.mean()))
    for _ in range(iters):
        p = 1 / (1 + np.exp(-(Xb @ w)))
        w -= lr * Xb.T @ (p - y) / len(y)
    return w


def predict_first_prize_digits(op, draws, test_from=0.6):
    """Can anything beat 10% at guessing each digit of the next 1st prize?"""
    start = int(len(draws) * test_from)
    freq = np.ones((4, 10))
    trans = np.ones((4, 10, 10))
    correct = {"most frequent digit": 0, "Markov (previous digit)": 0, "random": 0}
    n = 0
    for t, d in enumerate(draws):
        actual = digits(d["first"])
        if t >= start:
            prev = digits(draws[t - 1]["first"])
            for p in range(4):
                correct["most frequent digit"] += int(np.argmax(freq[p]) == actual[p])
                correct["Markov (previous digit)"] += int(np.argmax(trans[p, prev[p]]) == actual[p])
                correct["random"] += int(RNG.integers(10) == actual[p])
                n += 1
        for p in range(4):
            freq[p, actual[p]] += 1
            if t > 0:
                trans[p, digits(draws[t - 1]["first"])[p], actual[p]] += 1
    return {k: {"accuracy": round(v / n, 4),
                "z": round((v - n / 10) / math.sqrt(n * 0.09), 2)} for k, v in correct.items()}


# ---------------------------------------------------------------- part 3: Magnum digit bias
ERAS = (("1985-1994", "1985", "1995"), ("1995-2019", "1995", "2020"), ("2020-2026", "2020", "2027"))
# Big Forecast payout per RM1 (Magnum / Toto / Da Ma Cai all use this table).
BIG_PAYOUT = {"1st": 2500, "2nd": 1000, "3rd": 500, "Special": 180, "Consolation": 60}
DIG = np.array([digits(n) for n in range(10000)])


def era_of(date):
    return next(name for name, lo, hi in ERAS if lo <= date < hi)


def digit_bias_by_year(op, draws):
    """Chi-square of each digit position per calendar year, and whether one
    period's bias predicts the next (correlation of the previous 3 years'
    digit deviations with this year's)."""
    by = defaultdict(lambda: np.zeros((4, 10)))
    for d in draws:
        for n in d["all"]:
            for p, v in enumerate(digits(n)):
                by[int(d["date"][:4])][p, v] += 1
    yearly = {}
    for y in sorted(by):
        m = by[y]
        e = m.sum(1, keepdims=True) / 10
        yearly[y] = [round(float(((m[p] - e[p]) ** 2 / e[p]).sum()), 1) for p in range(4)]
    persistence = {}
    for y in sorted(by):
        if all(y - k in by for k in (1, 2, 3)):
            prev = sum(by[y - k] for k in (1, 2, 3))
            a = (prev / prev.sum(1, keepdims=True) - 0.1).ravel()
            b = (by[y] / by[y].sum(1, keepdims=True) - 0.1).ravel()
            persistence[y] = round(float(np.corrcoef(a, b)[0, 1]), 2)
    return {"chi2_by_year": yearly, "persistence_r": persistence}


def digit_model_betting(op, draws, window=300, ks=(1, 10, 100, 1000)):
    """Walk-forward: score every number by the product of its digit frequencies
    over the previous `window` draws. Report realised hits of the top-K numbers
    per era, and the cash return of betting RM1 Big on the top 10 every draw."""
    cnt = np.zeros((4, 10))
    hits = {e[0]: {k: 0 for k in ks} for e in ERAS}
    winners = {e[0]: 0 for e in ERAS}
    stake = {e[0]: 0 for e in ERAS}
    payout = {e[0]: 0 for e in ERAS}
    for t, d in enumerate(draws):
        arr = np.array(d["all"])
        if t >= window:
            era = era_of(d["date"])
            score = sum(np.log(cnt[p] / cnt[p].sum())[DIG[:, p]] for p in range(4))
            order = np.argsort(-score)
            for k in ks:
                hits[era][k] += len(d["set"] & set(order[:k].tolist()))
            winners[era] += len(arr)
            picks = set(order[:10].tolist())
            stake[era] += 10
            for prize, nums in d["by_prize"].items():
                payout[era] += BIG_PAYOUT[prize] * len(picks & set(nums))
        for p in range(4):
            np.add.at(cnt[p], DIG[arr, p], 1)
        if t >= window:
            for p in range(4):
                np.subtract.at(cnt[p], DIG[np.array(draws[t - window]["all"]), p], 1)
    out = {}
    for era in hits:
        if not winners[era]:
            continue
        row = {}
        for k in ks:
            exp = winners[era] * k / 10000
            row[f"top{k}"] = {"hits": hits[era][k], "expected": round(exp, 1),
                              "lift": round(hits[era][k] / exp, 3),
                              "z": round((hits[era][k] - exp) / math.sqrt(exp), 2)}
        row["bet_top10_big"] = {"staked": stake[era], "won": payout[era],
                                "return_per_rm1": round(payout[era] / stake[era], 3)}
        out[era] = row
    return out


# ---------------------------------------------------------------- main
def main():
    data = {op: load(stem) for op, stem in OPERATORS.items()}
    results = {"summary": {}, "backtest": {}, "first_prize_digits": {}, "digit_bias": {}, "digit_model": {}}
    for op, draws in data.items():
        print(f"== {op}: {len(draws)} draws {draws[0]['date']} .. {draws[-1]['date']}")
        results["summary"][op] = test_uniformity(op, draws)
        test_time_effects(op, draws)
        test_serial(op, draws)
    test_cross_operator(data)

    for op, draws in data.items():
        print(f"   backtesting {op} ...")
        results["backtest"][op] = backtest(op, draws)
        results["first_prize_digits"][op] = predict_first_prize_digits(op, draws)
        results["digit_bias"][op] = digit_bias_by_year(op, draws)
        results["digit_model"][op] = digit_model_betting(op, draws)

    m = len(TESTS)
    for t in TESTS:
        t["p_bonferroni"] = min(1.0, t["p"] * m)
    results["tests"] = TESTS
    results["n_tests"] = m
    results["n_p_below_0.05"] = sum(t["p"] < 0.05 for t in TESTS)
    results["n_significant_after_correction"] = sum(t["p_bonferroni"] < 0.05 for t in TESTS)

    with open(os.path.join(ROOT, "analysis", "results.json"), "w") as f:
        json.dump(results, f, indent=1, default=float)

    print(f"\n{m} hypothesis tests; {results['n_p_below_0.05']} with raw p<0.05 "
          f"(~{m * 0.05:.0f} expected by chance); "
          f"{results['n_significant_after_correction']} significant after Bonferroni.")
    for t in sorted(TESTS, key=lambda t: t["p"])[:12]:
        print(f"  p={t['p']:.2e}  p_adj={t['p_bonferroni']:.2f}  {t['operator']:<26} {t['test']}  {t['detail']}")
    for op, bt in results["backtest"].items():
        print(f"\nBacktest {op}: {bt['test_draws']} draws, {bt['picks_per_draw']} picks/draw, "
              f"random expects {bt['expected_hits_random']} hits")
        for s, r in bt["strategies"].items():
            print(f"  {s:<24} hits={r['hits']:<4} x{r['vs_random']:<6} z={r['z']:+.2f}")
        print("  1st-prize digit accuracy:", results["first_prize_digits"][op])
    for op, s in results["summary"].items():
        print(op, s)
    for op, eras in results["digit_model"].items():
        print(f"\nDigit-bias model, {op} (walk-forward, 300-draw window)")
        for era, row in eras.items():
            tops = "  ".join(f"{k}: x{v['lift']} (z={v['z']:+.1f})" for k, v in row.items() if k.startswith("top"))
            print(f"  {era}: {tops}  | RM1 Big on top 10 returns RM{row['bet_top10_big']['return_per_rm1']}")


if __name__ == "__main__":
    main()
