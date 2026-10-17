#!/usr/bin/env python3
"""Every nakshatra-type parameter, at three draw times (19:00, 19:15, 19:30 MYT).

Parameters: the nakshatra of the Moon, Sun, Mars, Mercury, Venus, Jupiter,
Saturn, Rahu and the Lagna; the Moon's pada; the Moon's nakshatra lord; the
KP star lords of the Moon, Ascendant and Sun. The fast-moving ones (Lagna,
Ascendant star lord, Moon nakshatra / pada / lord / KP star lord) are
recomputed at 19:15 and 19:30, since draws run 19:00-19:30.

Each parameter x 6 kinds (num, box, dig and their per-operator versions) is a
formula that picks the top 10 numbers per operator. Tested:
  1. frozen on the last 5 known draws (counts from draws before the first one)
  2. walk-forward on 2018-2026, every draw predicted from earlier draws only
Plus one combined nakshatra formula whose terms are chosen on 2012-2017 only
(astro_model.tune), then frozen.

Run from the repo root:  python3 analysis/nakshatra_test.py
"""

import csv
import datetime as dt
import json
import math
import multiprocessing as mp
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import almanac  # noqa: E402
import astro_model as am  # noqa: E402
import ephemeris as eph  # noqa: E402

ROOT = am.ROOT
BASE = ["nakshatra", "nakshatra_pada", "nakshatra_lord", "sun_nakshatra", "mars_nakshatra", "mercury_nakshatra",
        "venus_nakshatra", "jupiter_nakshatra", "saturn_nakshatra", "rahu_nakshatra", "lagna_nakshatra",
        "kp_moon_star_lord", "kp_asc_star_lord", "kp_sun_star_lord"]
FAST = ["nakshatra", "nakshatra_pada", "nakshatra_lord", "lagna_nakshatra", "kp_moon_star_lord", "kp_asc_star_lord"]
TIMES = {"19:15": dt.time(11, 15), "19:30": dt.time(11, 30)}       # UTC = MYT - 8h


def ctx_at(args):
    date, t = args
    day = dt.date.fromisoformat(date)
    tu = dt.datetime.combine(day, t)
    v = almanac.vedic_factors(tu, day, eph.sun_longitude(eph.julian_day(tu)))
    return {f: v[f] for f in FAST}


def all_dates():
    return sorted({r["date"] for op, stem in am.cn.OPERATORS.items()
                   for r in csv.DictReader(open(os.path.join(ROOT, "data", f"{stem}.csv")))
                   if (op, r["date"]) not in am.cn.EXCLUDE})


def add_time_variants(codes, labels, dates):
    names = []
    with mp.Pool() as pool:
        for tag, t in TIMES.items():
            ctx = pool.map(ctx_at, [(d, t) for d in dates], chunksize=128)
            for f in FAST:
                key = f"{f}@{tag}"
                lab = sorted({c[f] for c in ctx}, key=str)
                codes[key] = np.array([lab.index(c[f]) for c in ctx])
                labels[key] = lab
                names.append(key)
    return names


def picks_for(c, f, kind, di):
    return {op: np.argsort(-(c.term(f, int(c.codes[f][di]), kind, o) + np.arange(10000) * 1e-12))[:10].tolist()
            for o, op in enumerate(am.OPS)}


def results(date):
    win = {op: {} for op in am.OPS}
    for op, stem in am.cn.OPERATORS.items():
        for r in csv.DictReader(open(os.path.join(ROOT, "data", f"{stem}.csv"))):
            if r["date"] == date:
                win[op].setdefault(int(r["4d_number"]), r["prize"])
    return win


def score(picks, win):
    hits, pay = [], 0
    for op, ps in picks.items():
        for n in ps:
            if n in win[op]:
                hits.append(f"{op} {n:04d} {win[op][n]}")
                pay += am.BIG[win[op][n]]
    return hits, pay


def main():
    data, codes, labels, rows, draws, year_of = am.load()
    am._YEAR = year_of
    dates = all_dates()
    assert len(dates) == len(codes["nakshatra"])
    factors = BASE + add_time_variants(codes, labels, dates)
    changed = {k: float(np.mean([labels[k][codes[k][i]] != labels[k.split("@")[0]][codes[k.split("@")[0]][i]]
                                 for i in range(len(dates))])) for k in factors if "@" in k}
    print("share of draw dates whose value differs from 19:00:",
          {k: f"{100 * v:.0f}%" for k, v in changed.items()}, flush=True)
    formulas = [(f, kind) for f in factors for kind in am.KINDS]

    # 1. frozen test on the last 5 draws
    held = dates[-5:]
    cut = dates.index(held[0])
    m = rows["date"] < cut
    c = am.Counts(factors, codes)
    c.add(rows["date"][m], rows["op_ix"][m], rows["num"][m])
    wins = {D: results(D) for D in held}
    frozen = {}
    for f, kind in formulas:
        r = {D: score(picks_for(c, f, kind, dates.index(D)), wins[D]) for D in held}
        frozen[f"{f} / {kind}"] = r
    rng = np.random.default_rng(5)
    rand = []
    for _ in range(len(formulas)):
        rand.append(sum(len(score({op: rng.choice(10000, 10, replace=False).tolist() for op in am.OPS}, wins[D])[0])
                        for D in held))
    tot = {k: (sum(len(v[D][0]) for D in held), sum(v[D][1] for D in held)) for k, v in frozen.items()}
    print(f"\nFrozen test on {', '.join(held)} (counts from draws before {held[0]}), {len(formulas)} formulas x 30 picks per draw")
    for D in held:
        print(f"  {D}: formulas with a hit {sum(bool(v[D][0]) for v in frozen.values())}/{len(formulas)}")
    print(f"  total hits per formula: formulas {np.mean([t[0] for t in tot.values()]):.2f} on average, "
          f"random sets {np.mean(rand):.2f}; with 2+ hits: formulas {sum(t[0] >= 2 for t in tot.values())}, "
          f"random {sum(r >= 2 for r in rand)}")
    best = sorted(tot, key=lambda k: (-tot[k][0], -tot[k][1]))[:12]
    for k in best:
        print(f"    {k:<36} {tot[k][0]} hits RM{tot[k][1]}/RM150  " +
              " | ".join(f"{D[5:]}: {', '.join(frozen[k][D][0]) or '-'}" for D in held))

    # 2. walk-forward 2018-2026 for every formula
    print("\nWalk-forward 2018-2026, top 10 per operator (lift vs random, z, Big return per RM1):", flush=True)
    wf = {}
    for f, kind in formulas:
        out, _ = am.forward_test(f"{f}/{kind}", [(f, kind, 1.0)], codes, rows, draws)
        a = out["All"]
        wf[f"{f} / {kind}"] = {"lift": a["top10"]["lift"], "z": a["top10"]["z"], "hits": a["top10"]["hits"],
                               "expected": a["top10"]["expected"], "big": a["big_return_top10"]["per_RM1"]}
    zs = np.array([v["z"] for v in wf.values()])
    print(f"  {len(wf)} formulas: z > 2 for {int((zs > 2).sum())} (about {0.023 * len(wf):.1f} expected by chance), "
          f"z < -2 for {int((zs < -2).sum())}; best Big return RM{max(v['big'] for v in wf.values())}")
    for k in sorted(wf, key=lambda k: -wf[k]["z"])[:10]:
        v = wf[k]
        print(f"    {k:<36} {v['hits']}/{v['expected']} x{v['lift']} z={v['z']:+.1f} Big RM{v['big']}")
    by_time = {}
    for k, v in wf.items():
        tag = k.split(" / ")[0].split("@")[1] if "@" in k else "19:00"
        if k.split(" / ")[0].split("@")[0] in FAST:
            by_time.setdefault(tag, []).append(v["lift"])
    print("  fast-moving parameters, mean lift by draw time: " +
          ", ".join(f"{t}: x{np.mean(v):.3f}" for t, v in sorted(by_time.items())))

    # 3. combined nakshatra formula chosen on 2012-2017
    am.VARIANTS["nakshatra_all"] = factors
    comb = am.tune("nakshatra_all", codes, rows, draws)
    formula = [tuple(t) for t in comb["terms"]]
    out, _ = am.forward_test("nakshatra_all", formula, codes, rows, draws)
    a = out["All"]
    cf = am.Counts(sorted({f for f, _, _ in formula}), codes)
    cf.add(rows["date"][m], rows["op_ix"][m], rows["num"][m])
    comb_frozen = {}
    for D in held:
        di = dates.index(D)
        picks = {op: np.argsort(-am.score(cf, formula, di, o))[:10].tolist() for o, op in enumerate(am.OPS)}
        comb_frozen[D] = score(picks, wins[D])
    print(f"\nCombined nakshatra formula ({len(formula)} terms, chosen on 2012-2017): 2018-2026 top10 "
          f"{a['top10']['hits']}/{a['top10']['expected']} x{a['top10']['lift']} z={a['top10']['z']:+.1f}, "
          f"Big RM{a['big_return_top10']['per_RM1']}; last 5 draws: " +
          " | ".join(f"{D[5:]}: {', '.join(comb_frozen[D][0]) or '-'}" for D in held))
    print("  terms:", ", ".join(f"{f}/{k}x{w}" for f, k, w in formula[:10]), "...")
    json.dump({"time_variant_change_share": changed, "frozen_last5": {k: {D: v[D] for D in held} for k, v in frozen.items()},
               "random_last5_mean_hits": float(np.mean(rand)), "walk_forward_2018_2026": wf,
               "combined": {"formula": formula, "walk_forward": a, "last5": comb_frozen}},
              open(os.path.join(ROOT, "analysis", "nakshatra_results.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
