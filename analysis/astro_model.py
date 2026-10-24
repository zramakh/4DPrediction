#!/usr/bin/env python3
"""4D prediction formulas built only from Vedic and/or Chinese parameters,
tuned on 2012-2017 and forward-tested draw by draw on 2018-2026.

Three formulas, one per parameter family:
  vedic    tithi, paksha, nakshatra (+pada, lord), yoga, karana, vara (weekday
           lord), hora lord, rashi and nakshatra of every graha, lagna,
           navamsa, retrograde / combust, planets with the Moon, masa, adhika
           masa, ritu, ayana, samvatsara, KP star / sub lords and numbers
  chinese  year animal / stem / element / yin-yang / pillar, lunar month / day /
           leap, solar term, month and day pillars (stem, branch, element),
           Na Yin, hour stem, 12 officers, 12 day gods, Yellow / Black path,
           28 mansions, Tai Sui relation, Nine Star year / month
  both     the union

Nothing else enters the score: no hot numbers, no digit bias, no Western
calendar or astrology. Each term is a ratio "how often X won on dates with this
parameter value" / "how often X won overall", so a number that is simply common
gains nothing.

For a draw on date t (operator op), with v_f = value of parameter f on t:

  score(n) = sum over the formula's terms (f, kind, w) of  w * L_kind(f, v_f, n)

  L_num (f,v,n) = log[(wins of n on dates with f=v + a) / (expected + a)]                 a = 10
  L_box (f,v,n) = log[(wins of n's i-Box group on dates with f=v + a) / (expected + a)]   a = 50
  L_dig (f,v,n) = sum_pos log[p(digit_pos(n) | f=v) / p(digit_pos(n))]                    50 pseudo-draws
  (and *_op variants that count only operator op's draws)

Tuning (draws before 2012 counted, 2012-2017 scored, by the likelihood of the
real winners): every (parameter, kind) term is scored on its own; the useful
ones are ranked and the best prefix and scale are kept. The formula is then
frozen and written to astro_model_formulas.json.

Forward test: from 2018-01-01 every draw is predicted using all draws strictly
before its date; after the date's results are known they are added to the
counts and the next date is predicted.

Usage (repo root):
  python3 analysis/astro_model.py                    tune + forward test (~10 min)
  python3 analysis/astro_model.py predict --date 2026-10-21 [--variant both] [--k 10]
  python3 analysis/astro_model.py log --date 2026-10-21      append picks to forward_log.csv before the draw
  python3 analysis/astro_model.py score                       score forward_log.csv against data/*.csv
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
import predictive_model as pm  # noqa: E402

ROOT = cn.ROOT
OPS = pm.OPS
BIG = pm.BIG
DIG = pm.DIG
NG = len(cn.GROUP_IDS)
TRAIN_END, VALID_END = 2012, 2018
ALPHA = {"num": 10.0, "box": 50.0}
BETA = 50.0
KS = (1, 5, 10, 23, 100)
FORMULAS = os.path.join(ROOT, "analysis", "astro_model_formulas.json")
LOG = os.path.join(ROOT, "analysis", "forward_log.csv")

VEDIC = ["tithi", "paksha", "nakshatra", "nakshatra_lord", "nakshatra_pada", "yoga", "karana", "weekday",
         "hora_lord", "moon_rashi", "sun_rashi", "sun_nakshatra", "mars_rashi", "mars_nakshatra",
         "mercury_rashi", "mercury_nakshatra", "venus_rashi", "venus_nakshatra", "jupiter_rashi",
         "jupiter_nakshatra", "saturn_rashi", "saturn_nakshatra", "rahu_rashi", "rahu_nakshatra",
         "lagna_rashi", "lagna_nakshatra", "moon_navamsa", "mercury_retrograde", "venus_retrograde",
         "mars_retrograde", "jupiter_retrograde", "saturn_retrograde", "mercury_combust", "venus_combust",
         "mars_combust", "jupiter_combust", "saturn_combust", "planets_with_moon", "masa", "adhika_masa",
         "ritu", "ayana", "samvatsara", "kp_moon_star_lord", "kp_moon_sub_lord", "kp_moon_number",
         "kp_asc_star_lord", "kp_asc_sub_lord", "kp_asc_number", "kp_sun_star_lord", "kp_sun_sub_lord",
         "kp_sun_number"]
CHINESE = ["year_animal", "year_stem", "year_element", "year_yinyang", "year_pillar", "lunar_month",
           "lunar_day", "lunar_leap_month", "solar_term", "month_branch", "month_stem", "month_pillar",
           "day_stem", "day_branch", "day_element", "day_pillar", "nayin", "nayin_element", "hour_stem_19h",
           "day_officer", "day_god", "yellow_black_path", "mansion_28", "day_vs_year_branch",
           "nine_star_year", "nine_star_month"]
VARIANTS = {"vedic": VEDIC, "chinese": CHINESE, "both": VEDIC + CHINESE}
KINDS = ["num", "box", "dig", "num_op", "box_op", "dig_op"]


# ------------------------------------------------------------------ counts
class Counts:
    """Win counts by parameter value, pooled and per operator, updatable draw by draw."""

    def __init__(self, factors, codes, num_factors=None):
        """num_factors: factors that need number-level tables (default: all). Leaving large
        joint-pair factors out saves V x 10000 floats per factor."""
        self.factors, self.codes = factors, codes
        self.V = {f: int(codes[f].max()) + 2 for f in factors}       # +1 spare row for unseen values
        z = np.zeros
        nf = set(factors if num_factors is None else num_factors)
        self.num = {f: z((4, self.V[f], 10000), np.float32) if f in nf else None
                    for f in factors}                                  # [pooled, op0, op1, op2]
        self.box = {f: z((4, self.V[f], NG), np.float32) for f in factors}
        self.dig = {f: z((4, self.V[f], 4, 10)) for f in factors}
        self.nv = {f: z((4, self.V[f])) for f in factors}
        self.all = z((4, 10000))
        self.gall = z((4, NG))
        self.dall = z((4, 4, 10))
        self.T = z(4)

    def add(self, date_ix, op_ix, num):
        """Add winning rows (already once-per-draw). Bulk loads use bincount, single dates np.add.at."""
        grp = cn.GROUP_OF[num]
        bulk = len(num) > 5000
        for s, m in ((0, np.ones(len(num), bool)), *((i + 1, op_ix == i) for i in range(3))):
            if not m.any():
                continue
            d, n, g = date_ix[m], num[m], grp[m]
            self.T[s] += len(n)
            self.all[s] += np.bincount(n, minlength=10000)
            self.gall[s] += np.bincount(g, minlength=NG)
            for p in range(4):
                self.dall[s, p] += np.bincount(DIG[n, p], minlength=10)
            for f in self.factors:
                v = self.codes[f][d]
                V = self.V[f]
                if bulk:
                    if self.num[f] is not None:
                        self.num[f][s] += np.bincount(v * 10000 + n, minlength=V * 10000).reshape(V, 10000)
                    self.box[f][s] += np.bincount(v * NG + g, minlength=V * NG).reshape(V, NG)
                    self.nv[f][s] += np.bincount(v, minlength=V)
                    for p in range(4):
                        self.dig[f][s][:, p, :] += np.bincount(v * 10 + DIG[n, p], minlength=V * 10).reshape(V, 10)
                else:
                    if self.num[f] is not None:
                        np.add.at(self.num[f][s], (v, n), 1)
                    np.add.at(self.box[f][s], (v, g), 1)
                    np.add.at(self.nv[f][s], v, 1)
                    for p in range(4):
                        np.add.at(self.dig[f][s], (v, p, DIG[n, p]), 1)

    def term(self, f, v, kind, op_i):
        """L_kind(f, v, n) for all 10,000 numbers."""
        s = op_i + 1 if kind.endswith("_op") else 0
        k = kind.split("_")[0]
        nv = self.nv[f][s, v]
        if k == "num":
            q = (self.all[s] + 20) / (self.T[s] + 20 * 10000)
            return np.log((self.num[f][s, v] + ALPHA["num"]) / (nv * q + ALPHA["num"]))
        if k == "box":
            qg = (self.gall[s] + 200 * cn.GROUP_SHARE) / (self.T[s] + 200)
            return np.log((self.box[f][s, v] + ALPHA["box"]) / (nv * qg + ALPHA["box"]))[cn.GROUP_OF]
        base = self.dall[s] / max(self.T[s], 1)
        pc = (self.dig[f][s, v] + BETA * base) / (nv + BETA)
        lr = np.log(pc / base)                                        # (4, 10)
        return lr[0][DIG[:, 0]] + lr[1][DIG[:, 1]] + lr[2][DIG[:, 2]] + lr[3][DIG[:, 3]]


def score(counts, formula, date_ix, op_i):
    s = np.zeros(10000)
    for f, kind, w in formula:
        s += w * counts.term(f, int(counts.codes[f][date_ix]), kind, op_i)
    return s


def gain(s, winners):
    """Sum over winners of log(10000 * softmax(s)[winner]); 0 = no better than uniform."""
    m = s.max()
    lse = m + math.log(np.exp(s - m).sum())
    return float((s[winners] - lse + math.log(10000)).sum())


# ------------------------------------------------------------------ data
def load():
    data, codes, labels, factors, _ = pm.load()
    sel = data["once"]
    rows = {k: data[k][sel] for k in ("date", "op_ix", "num", "year")}
    # draws: (date_ix, op_i) -> deduped winners and prize rows
    draws = {}
    for d, o, n in zip(rows["date"], rows["op_ix"], rows["num"]):
        draws.setdefault((int(d), int(o)), [[], []])[0].append(int(n))
    for d, o, n, p in zip(data["date"], data["op_ix"], data["num"], data["raw_prize"]):
        draws[(int(d), int(o))][1].append((p, int(n)))
    date_year = np.zeros(len(codes[factors[0]]), int)
    date_year[rows["date"]] = rows["year"]
    return data, codes, labels, rows, draws, date_year


def counts_before(factors, codes, rows, year, num_factors=None):
    c = Counts(factors, codes, num_factors)
    m = rows["year"] < year
    c.add(rows["date"][m], rows["op_ix"][m], rows["num"][m])
    return c


# ------------------------------------------------------------------ tuning
def tune(variant, codes, rows, draws):
    t0 = time.time()
    factors = VARIANTS[variant]
    c = counts_before(factors, codes, rows, TRAIN_END)
    val = [(d, o, np.array(w)) for (d, o), (w, _) in draws.items()
           if TRAIN_END <= rows_year(d) < VALID_END]
    n_win = sum(len(x[2]) for x in val)
    # 1. each (parameter, kind) on its own, three weights
    W = (0.1, 0.3, 1.0)
    single = []
    for f in factors:
        for kind in KINDS:
            groups = {}
            for d, o, win in val:
                key = (int(codes[f][d]), o if kind.endswith("_op") else -1)
                groups.setdefault(key, []).append(win)
            g = dict.fromkeys(W, 0.0)
            for (v, o), wins in groups.items():
                t = c.term(f, v, kind, max(o, 0))
                tw = sum(t[w_].sum() for w_ in wins)
                nw = sum(len(w_) for w_ in wins)
                for w in W:
                    m = (w * t).max()
                    lse = m + math.log(np.exp(w * t - m).sum())
                    g[w] += w * tw - nw * lse + nw * math.log(10000)
            w, best = max(g.items(), key=lambda x: x[1])
            single.append((best, f, kind, w))
    single.sort(reverse=True)
    useful = [x for x in single if x[0] > 0]
    print(f"[{variant}] {len(single)} terms scored alone; {len(useful)} help on validation "
          f"({time.time() - t0:.0f}s)", flush=True)
    for g_, f, kind, w in single[:8]:
        print(f"    {f:<22} {kind:<7} w={w:<4} gain {1000 * g_ / n_win:+.4f} millinats/winner")
    # 2. best prefix of the ranked useful terms, and a joint scale
    cands = (useful if useful else single[:1])[:30]
    prefixes = sorted(k for k in {1, 2, 3, 5, 8, 12, 20, 30} if k <= len(cands)) or [len(cands)]
    scales = (0.25, 0.5, 1.0)
    tot = {(k, sc): 0.0 for k in prefixes for sc in scales}
    for d, o, win in val:
        acc = np.zeros(10000)
        j = 0
        for k in prefixes:
            while j < k:
                _, f, kind, w = cands[j]
                acc += w * c.term(f, int(codes[f][d]), kind, o)
                j += 1
            for sc in scales:
                tot[(k, sc)] += gain(sc * acc, win)
    (k, scale), g = max(tot.items(), key=lambda x: x[1])
    best = (g, k, scale)
    g, k, scale = best
    formula = [(f, kind, round(w * scale, 4)) for _, f, kind, w in cands[:k]]
    print(f"[{variant}] chosen: {k} terms x scale {scale}, validation gain {1000 * g / n_win:+.4f} millinats/winner "
          f"({time.time() - t0:.0f}s)", flush=True)
    return {"terms": formula, "validation_gain_millinats_per_winner": 1000 * g / n_win,
            "validation_winners": n_win,
            "single_terms_top20": [{"parameter": f, "kind": kd, "weight": w, "gain_millinats": 1000 * g_ / n_win}
                                   for g_, f, kd, w in single[:20]]}


_YEAR = None


def rows_year(d):
    return _YEAR[d]


# ------------------------------------------------------------------ forward test
def forward_test(variant, formula, codes, rows, draws, seed=0):
    t0 = time.time()
    factors = sorted({f for f, _, _ in formula})
    num_f = sorted({f for f, k, _ in formula if k.split("_")[0] == "num"})
    c = counts_before(factors, codes, rows, VALID_END, num_f)
    rng = np.random.default_rng(seed)
    test_dates = sorted({d for (d, _) in draws if rows_year(d) >= VALID_END})
    st = {k: {"draws": 0, "winners": 0, "gain": 0.0, **{f"h{K}": 0 for K in KS}, **{f"r{K}": 0 for K in KS},
              **{f"e{K}": 0.0 for K in KS}, **{f"p{K}": 0.0 for K in (1, 5, 10)}, **{f"rp{K}": 0.0 for K in (1, 5, 10)}}
          for k in OPS + ["All"]}
    yearly = {}
    by_date_rows = {}
    for i, d in enumerate(rows["date"]):
        if rows_year(d) >= VALID_END:
            by_date_rows.setdefault(int(d), []).append(i)
    for d in test_dates:
        for o in range(3):
            if (d, o) not in draws:
                continue
            win, prize_rows = draws[(d, o)]
            win = np.array(win)
            s = score(c, formula, d, o) + rng.random(10000) * 1e-9
            top = np.argsort(-s)[:max(KS)]
            rnd = rng.choice(10000, max(KS), replace=False)
            y = rows_year(d)
            yr = yearly.setdefault(y, [0, 0.0])
            yr[0] += int(np.isin(win, top[:10]).sum())
            yr[1] += 10 * len(win) / 10000
            for key in (OPS[o], "All"):
                x = st[key]
                x["draws"] += 1
                x["winners"] += len(win)
                x["gain"] += gain(s, win)
                for K in KS:
                    x[f"h{K}"] += int(np.isin(win, top[:K]).sum())
                    x[f"r{K}"] += int(np.isin(win, rnd[:K]).sum())
                    x[f"e{K}"] += K * len(win) / 10000
                for K in (1, 5, 10):
                    a, b = set(top[:K].tolist()), set(rnd[:K].tolist())
                    x[f"p{K}"] += sum(BIG[p] for p, n in prize_rows if n in a)
                    x[f"rp{K}"] += sum(BIG[p] for p, n in prize_rows if n in b)
        ix = by_date_rows.get(d, [])
        if ix:  # results of date d become known, then the next date is predicted
            c.add(rows["date"][ix], rows["op_ix"][ix], rows["num"][ix])
    out = {}
    for key, x in st.items():
        if not x["draws"]:
            continue
        r = {"draws": x["draws"], "loglik_gain_millinats_per_winner": round(1000 * x["gain"] / x["winners"], 4)}
        for K in KS:
            h, e = x[f"h{K}"], x[f"e{K}"]
            r[f"top{K}"] = {"hits": h, "expected": round(e, 1), "lift": round(h / e, 3),
                            "z": round((h - e) / math.sqrt(e), 2), "random_picks_hits": x[f"r{K}"]}
        for K in (1, 5, 10):
            r[f"big_return_top{K}"] = {"per_RM1": round(x[f"p{K}"] / (K * x["draws"]), 3),
                                       "random_picks_per_RM1": round(x[f"rp{K}"] / (K * x["draws"]), 3)}
        out[key] = r
    print(f"[{variant}] forward test: {len(test_dates)} draw dates in {time.time() - t0:.0f}s", flush=True)
    return out, {int(y): {"hits@10": h, "expected@10": round(e, 1)} for y, (h, e) in sorted(yearly.items())}


# ------------------------------------------------------------------ live use
def date_codes(date, codes, labels, factors):
    """Codes of a (possibly future) date; unseen values map to the spare row."""
    ctx = ce.date_context(date)
    ix = len(codes[factors[0]])
    codes2 = {}
    for f in factors:
        code = labels[f].index(ctx[f]) if ctx[f] in labels[f] else int(codes[f].max()) + 1
        codes2[f] = np.append(codes[f], code)
    return ix, codes2, ctx


def picks_for(date, variants, k, before=None):
    """Top-k picks per operator from the results of draws before `before` (default: `date`)."""
    with open(FORMULAS) as fh:
        formulas = json.load(fh)
    data, codes, labels, rows, draws, _ = load()
    dates = sorted({r["date"] for op, stem in cn.OPERATORS.items()
                    for r in csv.DictReader(open(os.path.join(ROOT, "data", f"{stem}.csv")))
                    if (op, r["date"]) not in cn.EXCLUDE})
    ok = np.array([d < (before or date) for d in dates])[rows["date"]]
    rows = {key: v[ok] for key, v in rows.items()}
    out = {}
    for v in variants:
        formula = [tuple(t) for t in formulas[v]["terms"]]
        factors = sorted({f for f, _, _ in formula})
        ix, codes2, ctx = date_codes(date, codes, labels, factors)
        c = Counts(factors, codes2)
        c.add(rows["date"], rows["op_ix"], rows["num"])
        out[v] = {OPS[o]: [int(n) for n in np.argsort(-score(c, formula, ix, o))[:k]] for o in range(3)}
    return out


def cmd_predict(a):
    variants = [a.variant] if a.variant else list(VARIANTS)
    res = picks_for(a.date, variants, a.k, a.before)
    print(f"Picks for draws on {a.date} (top {a.k}, results before {a.before or a.date}):")
    for v, by_op in res.items():
        for op, nums in by_op.items():
            print(f"  {v:<8} {op:<12} " + " ".join(f"{n:04d}" for n in nums))


def cmd_log(a):
    res = picks_for(a.date, list(VARIANTS), a.k, a.before)
    new = not os.path.exists(LOG)
    with open(LOG, "a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["logged_at_utc", "draw_date", "variant", "operator", "rank", "4d_number"])
        now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
        for v, by_op in res.items():
            for op, nums in by_op.items():
                for r, n in enumerate(nums, 1):
                    w.writerow([now, a.date, v, op, r, f"{n:04d}"])
    print(f"logged top {a.k} picks for {a.date} to {LOG}")


def cmd_score(a):
    results = {}
    for op, stem in cn.OPERATORS.items():
        with open(os.path.join(ROOT, "data", f"{stem}.csv"), newline="") as fh:
            for r in csv.DictReader(fh):
                results.setdefault((op, r["date"]), []).append((r["prize"], r["4d_number"]))
    tally = {}
    with open(LOG, newline="") as fh:
        for r in csv.DictReader(fh):
            if r["logged_at_utc"][:10] > r["draw_date"]:
                continue  # logged after the draw: not a forward prediction
            res = results.get((r["operator"], r["draw_date"]))
            if res is None:
                continue
            t = tally.setdefault(r["variant"], {"picks": 0, "hits": 0, "expected": 0.0, "payout": 0.0, "draws": set()})
            t["picks"] += 1
            t["draws"].add((r["operator"], r["draw_date"]))
            t["expected"] += len({n for _, n in res}) / 10000
            won = [p for p, n in res if n == r["4d_number"]]
            t["hits"] += bool(won)
            t["payout"] += sum(BIG[p] for p in won)
            for p in won:
                print(f"  HIT {r['variant']:<8} {r['operator']:<12} {r['draw_date']} {r['4d_number']} ({p})")
    if not tally:
        print("no logged draws have results yet (update data/ with scraper.py first)")
    for v, t in tally.items():
        print(f"  {v:<8} {len(t['draws'])} draws, {t['picks']} picks: {t['hits']} hits vs {t['expected']:.2f} expected; "
              f"Big return RM{t['payout'] / t['picks']:.2f} per RM1")


def main():
    global _YEAR
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", nargs="?", default="evaluate", choices=["evaluate", "predict", "log", "score"])
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--variant", choices=list(VARIANTS))
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--before", help="use only results of draws before this date (default: --date)")
    ap.add_argument("--retune", action="store_true")
    a = ap.parse_args()
    if a.mode == "predict":
        return cmd_predict(a)
    if a.mode == "log":
        return cmd_log(a)
    if a.mode == "score":
        return cmd_score(a)
    t0 = time.time()
    data, codes, labels, rows, draws, _YEAR = load()
    results = {}
    if os.path.exists(FORMULAS) and not a.retune:
        with open(FORMULAS) as fh:
            formulas = json.load(fh)
        print("using the frozen formulas in", FORMULAS, "(--retune to tune again)", flush=True)
    else:
        formulas = {v: tune(v, codes, rows, draws) for v in VARIANTS}
        with open(FORMULAS, "w") as fh:
            json.dump(formulas, fh, indent=1)
        print("formulas frozen ->", FORMULAS, flush=True)
    for v in VARIANTS:
        formula = [tuple(t) for t in formulas[v]["terms"]]
        res, yearly = forward_test(v, formula, codes, rows, draws)
        results[v] = {"test": res, "by_year": yearly}
    with open(os.path.join(ROOT, "analysis", "astro_model_results.json"), "w") as fh:
        json.dump({"formulas": formulas, "forward_test": results}, fh, indent=1)
    print("\n=== Forward test, draw by draw, 2018-01-01 to the last draw in data/ ===")
    for v, r in results.items():
        print(f"[{v}] {len(formulas[v]['terms'])} terms: " +
              ", ".join(f"{f}/{k}x{w}" for f, k, w in formulas[v]["terms"][:6]) +
              (" ..." if len(formulas[v]["terms"]) > 6 else ""))
        for key, x in r["test"].items():
            print(f"  {key:<12} draws {x['draws']:>5}  " + "  ".join(
                f"top{K}: {x[f'top{K}']['hits']}/{x[f'top{K}']['expected']} (x{x[f'top{K}']['lift']}, z={x[f'top{K}']['z']:+.1f})"
                for K in (5, 10, 23, 100)))
            print(f"  {'':<12} loglik {x['loglik_gain_millinats_per_winner']:+.4f} mnats; Big RM1: " + "  ".join(
                f"top{K} {x[f'big_return_top{K}']['per_RM1']} (random {x[f'big_return_top{K}']['random_picks_per_RM1']})"
                for K in (1, 5, 10)))
        print(f"  top-10 hits by year: " + ", ".join(f"{y}: {h['hits@10']}/{h['expected@10']}" for y, h in r["by_year"].items()))
    print(f"\ndone in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
