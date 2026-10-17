#!/usr/bin/env python3
"""A hand-usable 4D formula from a few Vedic / Chinese parameters.

    Points(position p, digit d) = sum over the chosen parameters f of
                                  TABLE_f[ value of f on the draw date ][p][d]

    TABLE_f[v][p][d] = round( 10000 * w_f * log[ p(d at p | f = v) / p(d at p) ] )
    (digit frequencies among past winning numbers, all operators, smoothed with
    50 pseudo-draws so that rarely seen values stay close to 0)

    Number #1 = the best-scoring digit in each of the 4 positions.
    Numbers #2-#5 = the next best of the 16 combinations of each position's
    best and second-best digit, ranked by total points.

Parameters and weights are chosen on 2012-2017 (counts from earlier draws), then
frozen. The exact manual procedure is then tested on 2018-2026, with the tables
refreshed every January from all earlier draws (as a user would do once a year).
Finally tables from all draws and a parameter calendar are exported for the
workbook (analysis/manual_formula.xlsx, built by build_manual_workbook.py).

Run from the repo root:  python3 analysis/manual_formula.py
"""

import datetime as dt
import itertools
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am  # noqa: E402
import conditional_extended as ce  # noqa: E402

ROOT = am.ROOT
DIG = am.DIG
BETA = 50.0
N_PARAMS = 6
SCALE = 10000   # points per unit of weighted log-lift; 100 rounded most cells to 0 (see REPORT section 10)
OUT = os.path.join(ROOT, "analysis", "manual_formula.json")


def digit_tables(codes, rows, factors, before_year):
    """log-lift tables (V, 4, 10) per factor from winners of years < before_year (pooled)."""
    m = rows["year"] < before_year
    d, n = rows["date"][m], rows["num"][m]
    base = np.stack([np.bincount(DIG[n, p], minlength=10) for p in range(4)]) / len(n)
    out = {}
    for f in factors:
        V = int(codes[f].max()) + 1
        v = codes[f][d]
        nv = np.bincount(v, minlength=V).astype(float)
        c = np.stack([np.bincount(v * 10 + DIG[n, p], minlength=V * 10).reshape(V, 10) for p in range(4)], 1)
        pc = (c + BETA * base[None]) / (nv[:, None, None] + BETA)
        out[f] = np.log(pc / base[None])
    return out


def points(tables, weights, codes, date_ix):
    P = np.zeros((4, 10))
    for f, w in weights.items():
        P += np.round(SCALE * w * tables[f][codes[f][date_ix]])
    return P


def top_numbers(P, k=5):
    """Number #1 = best digit per position; then the best of the 16 best/second-best combinations."""
    order = np.argsort(-(P + np.arange(10) * 1e-6), 1)       # tie-break: higher digit first
    combos = []
    for bits in itertools.product((0, 1), repeat=4):
        digits = [order[p, b] for p, b in enumerate(bits)]
        combos.append((sum(P[p, d] for p, d in enumerate(digits)) - sum(bits) * 1e-9,
                       digits[0] * 1000 + digits[1] * 100 + digits[2] * 10 + digits[3]))
    combos.sort(key=lambda x: -x[0])
    return [n for _, n in combos[:k]]


def choose(codes, rows, draws, year_of):
    """Rank every Vedic / Chinese parameter by validation log-likelihood of its digit term alone."""
    tab = digit_tables(codes, rows, am.VEDIC + am.CHINESE, am.TRAIN_END)
    val = [(d, np.array(w)) for (d, o), (w, _) in draws.items() if am.TRAIN_END <= year_of[d] < am.VALID_END]
    n_win = sum(len(w) for _, w in val)
    scores = []
    for f in am.VEDIC + am.CHINESE:
        best = (0.0, None)
        for w in (0.1, 0.3, 1.0):
            g = 0.0
            for d, win in val:
                s = w * sum(tab[f][codes[f][d], p][DIG[:, p]] for p in range(4))
                m = s.max()
                g += float((s[win] - m - math.log(np.exp(s - m).sum()) + math.log(10000)).sum())
            if g > best[0]:
                best = (g, w)
        scores.append((best[0] * 1000 / n_win, f, best[1]))
    scores.sort(reverse=True)
    chosen = {f: w for g, f, w in scores[:N_PARAMS] if w is not None}
    return chosen, scores


def test(codes, rows, draws, year_of, weights):
    tally = {k: {"hits": 0, "expected": 0.0, "payout": 0.0, "draws": 0} for k in (1, 5)}
    by_op = {}
    for y in range(am.VALID_END, int(year_of.max()) + 1):
        tab = digit_tables(codes, rows, list(weights), y)
        for (d, o), (win, prize_rows) in draws.items():
            if year_of[d] != y:
                continue
            picks = top_numbers(points(tab, weights, codes, d), 5)
            for k in (1, 5):
                t = tally[k]
                pk = set(picks[:k])
                t["hits"] += sum(n in pk for n in win)
                t["expected"] += k * len(win) / 10000
                t["payout"] += sum(am.BIG[p] for p, n in prize_rows if n in pk)
                t["draws"] += 1
            b = by_op.setdefault(am.OPS[o], [0, 0.0])
            b[0] += sum(n in set(picks) for n in win)
            b[1] += 5 * len(win) / 10000
    out = {}
    for k, t in tally.items():
        out[f"top{k}"] = {"hits": t["hits"], "expected": round(t["expected"], 1),
                          "lift": round(t["hits"] / t["expected"], 3),
                          "z": round((t["hits"] - t["expected"]) / math.sqrt(t["expected"]), 2),
                          "big_return_per_RM1": round(t["payout"] / (k * t["draws"]), 3), "draws": t["draws"]}
    out["top5_by_operator"] = {op: {"hits": h, "expected": round(e, 1), "lift": round(h / e, 3)}
                               for op, (h, e) in by_op.items()}
    return out


def main():
    data, codes, labels, rows, draws, year_of = am.load()
    weights, ranking = choose(codes, rows, draws, year_of)
    print("chosen parameters (validation 2012-2017):")
    for g, f, w in ranking[:10]:
        print(f"  {f:<20} w={w}  gain {g:+.4f} millinats/winner {'<- chosen' if f in weights else ''}")
    res = test(codes, rows, draws, year_of, weights)
    print("\nforward test 2018-2026 (tables refreshed yearly):", json.dumps(res, indent=1))
    # tables from all draws, for manual use
    tab = digit_tables(codes, rows, list(weights), 10 ** 6)
    tables = {f: {str(labels[f][v]): np.round(SCALE * w * tab[f][v]).astype(int).tolist()
                  for v in range(len(labels[f]))} for f, w in weights.items()}
    # calendar of parameter values for upcoming dates
    cal = []
    for i in range(0, 440):
        day = dt.date(2026, 10, 15) + dt.timedelta(days=i)
        ctx = ce.date_context(day.isoformat())
        cal.append({"date": day.isoformat(), "weekday": day.strftime("%a"),
                    **{f: str(ctx[f]) for f in weights}})
    with open(OUT, "w") as fh:
        json.dump({"formula": "Points(p,d) = sum_f TABLE_f[value of f on date][p][d]; number = best digit per position",
                   "weights": weights, "validation_ranking": [[f, w, g] for g, f, w in ranking],
                   "forward_test_2018_2026": res, "tables_all_draws_to": "2026-10-14",
                   "tables": tables, "calendar": cal}, fh, indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
