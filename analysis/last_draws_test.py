#!/usr/bin/env python3
"""Hold out the last N known draw dates and predict each one from the draws before it.

For every held-out date D (all three operators), each formula is rebuilt from
draws strictly before D, predicts D, and is scored against D's real results:
  * the 468 single-parameter Vedic / Chinese formulas (parameter x kind, top 10 per operator)
  * the section-7 digit formula (top 10), the frozen section-8 Vedic / Chinese / combined
    formulas (top 10), the corrected manual formula (top 5)
  * the section-9 ML models, if their logs from
      ml_model.py predict --date D --before D --k 10
    are given with --ml DATE=LOGFILE
  * 468 sets of random picks as the luck baseline

Usage (repo root):
  python3 analysis/last_draws_test.py [--n 3] [--ml 2026-10-14=path.log ...]
"""

import argparse
import csv
import json
import os
import re
import sys
from itertools import permutations

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am  # noqa: E402
import manual_formula as mf  # noqa: E402
import predictive_model as pm  # noqa: E402

ROOT = am.ROOT
BIG = am.BIG
OPS = am.OPS


def all_dates():
    return sorted({r["date"] for op, stem in am.cn.OPERATORS.items()
                   for r in csv.DictReader(open(os.path.join(ROOT, "data", f"{stem}.csv")))
                   if (op, r["date"]) not in am.cn.EXCLUDE})


def results(date):
    win = {op: {} for op in OPS}
    for op, stem in am.cn.OPERATORS.items():
        for r in csv.DictReader(open(os.path.join(ROOT, "data", f"{stem}.csv"))):
            if r["date"] == date:
                win[op].setdefault(int(r["4d_number"]), r["prize"])
    return win


def score(picks_by_op, win):
    st = ib = pay = 0
    hits = []
    for op, picks in picks_by_op.items():
        w = win[op]
        groups = {"".join(sorted(f"{n:04d}")): n for n in w}
        for n in picks:
            if n in w:
                st += 1
                pay += BIG[w[n]]
                hits.append(f"{op} {n:04d} {w[n]}")
            elif "".join(sorted(f"{n:04d}")) in groups:
                ib += 1
    return {"straight": st, "ibox": ib, "payout": pay, "picks": sum(len(p) for p in picks_by_op.values()),
            "hits": hits}


def ml_picks_multi(path):
    """{date: {model: {op: picks}}} from a multi-date ml_model.py predict log."""
    out, cur = {}, None
    for line in open(path):
        m = re.match(r"Picks for (\d{4}-\d{2}-\d{2})", line)
        if m:
            cur = out.setdefault(m.group(1), {})
            continue
        m = re.match(r"\s+(\S+)\s+(Magnum|Sports Toto|Da Ma Cai)\s+([\d ]+)$", line.rstrip())
        if m and cur is not None:
            cur.setdefault(f"ML {m.group(1)}", {})[m.group(2)] = [int(x) for x in m.group(3).split()]
    return out


SELECTED = ["single jupiter_nakshatra / num_op", "single yellow_black_path / num_op", "single month_branch / dig_op"]


def ml_picks(path):
    out = {}
    for line in open(path):
        m = re.match(r"\s+(\S+)\s+(Magnum|Sports Toto|Da Ma Cai)\s+([\d ]+)$", line.rstrip())
        if m:
            out.setdefault(f"ML {m.group(1)}", {})[m.group(2)] = [int(x) for x in m.group(3).split()]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--ml", action="append", default=[])
    ap.add_argument("--ml-multi", help="one ml_model.py predict log holding several dates")
    ap.add_argument("--frozen", action="store_true",
                    help="train once on draws before the first held-out date (no updating between held-out draws)")
    a = ap.parse_args()
    ml_logs = dict(x.split("=", 1) for x in a.ml)
    ml_multi = ml_picks_multi(a.ml_multi) if a.ml_multi else {}

    data, codes, labels, rows, draws, year_of = am.load()
    am._YEAR = year_of
    pdata, pcodes, _, pfactors, _ = pm.load()
    pweights = json.load(open(pm.CONFIG_PATH))["weights"]
    astro = json.load(open(am.FORMULAS))
    mweights = json.load(open(mf.OUT))["weights"]
    dates = all_dates()
    held = dates[-a.n:]
    rng = np.random.default_rng(2026)
    table = {}          # formula -> {date: score}
    random_scores = {}
    cache = {}
    for D in held:
        di = dates.index(D)
        win = results(D)
        cut = dates.index(held[0]) if a.frozen else di      # training uses draws before `cut` only
        m = rows["date"] < cut
        if cut not in cache:
            c = am.Counts(am.VEDIC + am.CHINESE, codes)
            c.add(rows["date"][m], rows["op_ix"][m], rows["num"][m])
            cache = {cut: c}
        c = cache[cut]
        # 468 single-parameter formulas
        for f in am.VEDIC + am.CHINESE:
            for kind in am.KINDS:
                picks = {}
                for o, op in enumerate(OPS):
                    t = c.term(f, int(codes[f][di]), kind, o)
                    picks[op] = np.argsort(-(t + np.arange(10000) * 1e-12))[:10].tolist()
                table.setdefault(f"single {f} / {kind}", {})[D] = score(picks, win)
        # frozen section-8 formulas
        for v in am.VARIANTS:
            formula = [tuple(t) for t in astro[v]["terms"]]
            picks = {op: np.argsort(-am.score(c, formula, di, o))[:10].tolist() for o, op in enumerate(OPS)}
            table.setdefault(f"S8 {v} formula", {})[D] = score(picks, win)
        # section-7 digit formula
        tab7 = pm.Tables(pdata, pcodes, pfactors, pdata["date"] < cut,
                         alphas=sorted({int(k.split("_a")[1]) for k in pweights if "_a" in k}) or [10],
                         betas=sorted({int(k.split("_b")[1]) for k in pweights if "_b" in k}) or [50],
                         half_lives=sorted({int(k.split("_h")[1]) for k in pweights if "_h" in k}) or [0])
        picks = {}
        for o, op in enumerate(OPS):
            s = pm.combine(tab7.components(o, np.array([di]), pcodes), pweights)[0]
            picks[op] = np.argsort(-s)[:10].tolist()
        table.setdefault("S7 digit formula", {})[D] = score(picks, win)
        # corrected manual formula
        sub = {k: v[m] for k, v in rows.items()}
        sub["year"] = np.zeros(m.sum(), int)
        mt = mf.digit_tables(codes, sub, list(mweights), 1)
        top5 = mf.top_numbers(mf.points(mt, mweights, codes, di), 5)
        table.setdefault("S10 manual formula (top 5)", {})[D] = score({op: top5 for op in OPS}, win)
        # ML models
        if D in ml_logs:
            for name, picks in ml_picks(ml_logs[D]).items():
                table.setdefault(name, {})[D] = score(picks, win)
        for name, picks in ml_multi.get(D, {}).items():
            table.setdefault(name, {})[D] = score(picks, win)
        # random baseline: 468 sets of 30 picks
        random_scores[D] = [score({op: rng.choice(10000, 10, replace=False).tolist() for op in OPS}, win)
                            for _ in range(468)]
        print(f"{D}: scored {sum(D in v for v in table.values())} formulas", flush=True)

    # summary
    def tot(sc):
        return (sum(x["straight"] for x in sc.values()), sum(x["payout"] for x in sc.values()),
                sum(x["ibox"] for x in sc.values()), sum(x["picks"] for x in sc.values()))
    singles = {k: v for k, v in table.items() if k.startswith("single")}
    mode = f"trained once on draws before {held[0]}" if a.frozen else "each predicted from all earlier draws"
    print(f"\nHeld-out draws: {', '.join(held)} ({mode})")
    for D in held:
        fs = [v[D]["straight"] for v in singles.values()]
        rs = [x["straight"] for x in random_scores[D]]
        print(f"  {D}: single-parameter formulas with a straight hit {sum(x > 0 for x in fs)}/468; "
              f"random sets {sum(x > 0 for x in rs)}/468")
    multi = [k for k, v in singles.items() if sum(v[D]["straight"] > 0 for D in held) >= 2]
    rmulti = sum(1 for i in range(468) if sum(random_scores[D][i]["straight"] > 0 for D in held) >= 2)
    print(f"  single formulas that hit on 2+ of the {len(held)} draws: {len(multi)} (random sets: {rmulti})")
    print("\nNamed formulas (straight hits / Big RM back / RM staked, per draw and total):")
    for k, v in table.items():
        if k.startswith("single"):
            continue
        st, pay, ib, npk = tot(v)
        per = "  ".join(f"{D[5:]}: {v[D]['straight']}" + (f" {v[D]['hits']}" if v[D]['hits'] else "") for D in held if D in v)
        print(f"  {k:<28} total {st} hits, RM{pay} / RM{npk}  | {per}")
    print("\nBest single-parameter formulas over the held-out draws:")
    best = sorted(singles.items(), key=lambda kv: (-tot(kv[1])[0], -tot(kv[1])[1]))[:10]
    for k, v in best:
        st, pay, ib, npk = tot(v)
        print(f"  {k:<36} {st} hits, RM{pay} / RM{npk}  " +
              "; ".join(h for D in held for h in v[D]["hits"]))
    print("\nSelected formulas, draw by draw:")
    for k in SELECTED:
        st, pay, ib, npk = tot(table[k])
        print(f"  {k}: total {st} straight hits, {ib} i-Box, Big RM{pay} back on RM{npk}")
        for D in held:
            x = table[k][D]
            print(f"    {D}: {x['straight']} hit(s) {x['hits'] or ''}  i-Box {x['ibox']}  RM{x['payout']} / RM{x['picks']}")
    rs_tot = [sum(random_scores[D][i]["straight"] for D in held) for i in range(468)]
    rp_tot = [sum(random_scores[D][i]["payout"] for D in held) for i in range(468)]
    print(f"\nRandom baseline over these draws (468 sets of 30 picks per draw): straight hits per set "
          f"mean {np.mean(rs_tot):.2f}, {np.mean(np.array(rs_tot) >= 1):.0%} of sets got at least one, "
          f"{np.mean(np.array(rs_tot) >= 2):.0%} got two or more; mean Big return RM{np.mean(rp_tot):.0f} on RM{30 * len(held)}")
    out = {"held_out": held, "frozen": a.frozen, "formulas": table,
           "random_baseline": {D: {"sets_with_hit": sum(x["straight"] > 0 for x in random_scores[D]),
                                   "sets": 468} for D in held}}
    name = f"last{len(held)}_{'frozen' if a.frozen else 'rolling'}_results.json"
    with open(os.path.join(ROOT, "analysis", name), "w") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()
