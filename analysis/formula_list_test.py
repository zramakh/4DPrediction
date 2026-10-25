#!/usr/bin/env python3
"""Test a given list of parameter-pair formulas against chance and our leads.

New parameters (19:00 MYT; sidereal Lahiri positions from
continuous_astro_positions.npz unless stated):
  day_of_month, month          Gregorian date
  aspect_<a>_<b>               conjunction / sextile / square / trine / opposition (orb 6 deg) or none
  aspects_hard, aspects_soft   number of square+opposition / sextile+trine pairs among Sun, Moon,
                               Mars, Mercury, Jupiter, Venus, Saturn
  sun_sign_tropical, moon_sign_tropical   tropical sign (sidereal + Lahiri ayanamsa)
  moon_phase                   8 phases of Moon - Sun (45 deg each)
  pof_rashi, pof_sign          Part of Fortune = Asc + Moon - Sun: sidereal / tropical sign
  lagna_navamsa_lord, moon_d27_lord   lord of the Lagna's D9 sign / the Moon's D27 sign
  plum_trigrams                Mei Hua upper / lower trigram pair (chinese_divination.py)
  vargottama_count, vargottama_d10_count, vargottama_d24_count
                               how many of the 9 bodies have the same sign in D1 and D9 / D10 / D24
  universal_day                digit sum of the full date reduced to 1-9
  kp_ruling_planets            set of: weekday lord, Moon sign lord, Moon star lord, Asc sign lord,
                               Asc star lord
  <body>_navamsa, <body>_dN    as in navamsa_family.py / divisional_charts.py
Each formula (and 500 random pairs of the 78 base parameters for comparison):
digit-position picks of analysis C (navamsa_family.py, 42 columns: S1, S2, rank
pairs; a / b; Straight / Reverse / i-Box) scored before 2012 and 2012-2026.
Its method = the column with the best z before 2012 (no later data used);
score = that column's z on 2012-2026. Then the formula's picks are rebuilt for
the given draw dates from earlier results only and scored.

Run from the repo root:  python3 analysis/formula_list_test.py formulas.txt DATE [DATE ...]
"""

import datetime as dt
import itertools
import json
import math
import multiprocessing as mp
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am  # noqa: E402
import chinese_divination as cd  # noqa: E402
import divisional_charts as dcm  # noqa: E402
import ephemeris as eph  # noqa: E402
import navamsa_family as nf  # noqa: E402
import score_leads as sc  # noqa: E402
import score_live as sl  # noqa: E402
import vedic  # noqa: E402

SIGNS = nf.RASHIS
LORD = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
WEEK_LORD = {"Monday": "Moon", "Tuesday": "Mars", "Wednesday": "Mercury", "Thursday": "Jupiter",
             "Friday": "Venus", "Saturday": "Saturn", "Sunday": "Sun"}
PLANETS7 = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
COL = {b: j for j, b in enumerate(nf.BODIES)}                              # columns in the positions file
ASPECTS = np.array([0, 60, 90, 120, 180])
ASPECT_NAMES = ["none", "conjunction", "sextile", "square", "trine", "opposition"]


def aspect(a, b):
    s = (a - b) % 360
    f = np.minimum(s, 360 - s)
    d = np.abs(f[:, None] - ASPECTS[None, :])
    return np.where(d.min(1) <= 6, d.argmin(1) + 1, 0)


def build(D):
    lon = __import__("continuous_astro").positions(D.dates)          # cached; recomputed when dates change
    days = [dt.date.fromisoformat(d) for d in D.dates]
    ayan = np.array([vedic.ayanamsa(eph.julian_day(dt.datetime.combine(d, dt.time(11)))) for d in days])
    codes, labels = {}, {}

    def add(name, values):
        labs = sorted(set(values.tolist() if hasattr(values, "tolist") else values), key=str)
        ix = {v: i for i, v in enumerate(labs)}
        codes[name] = np.array([ix[v] for v in (values.tolist() if hasattr(values, "tolist") else values)])
        labels[name] = [str(v) for v in labs]

    add("day_of_month", np.array([d.day for d in days]))
    add("month", np.array([d.month for d in days]))
    for a, b in itertools.combinations(PLANETS7 + ["Rahu", "Lagna"], 2):
        add(f"aspect_{a.lower()}_{b.lower()}", aspect(lon[:, COL[a]], lon[:, COL[b]]))
        codes[f"aspect_{b.lower()}_{a.lower()}"] = codes[f"aspect_{a.lower()}_{b.lower()}"]   # either order
        labels[f"aspect_{b.lower()}_{a.lower()}"] = labels[f"aspect_{a.lower()}_{b.lower()}"]
    hard = np.zeros(len(days), int)
    soft = np.zeros(len(days), int)
    for a, b in itertools.combinations(PLANETS7, 2):
        k = aspect(lon[:, COL[a]], lon[:, COL[b]])
        hard += np.isin(k, (3, 5))
        soft += np.isin(k, (2, 4))
    add("aspects_hard", hard)
    add("aspects_soft", soft)
    trop = (lon + ayan[:, None]) % 360
    add("sun_sign_tropical", (trop[:, COL["Sun"]] // 30).astype(int))
    add("moon_sign_tropical", (trop[:, COL["Moon"]] // 30).astype(int))
    add("moon_phase", (((lon[:, COL["Moon"]] - lon[:, COL["Sun"]]) % 360) // 45).astype(int))
    pof = (lon[:, COL["Lagna"]] + lon[:, COL["Moon"]] - lon[:, COL["Sun"]]) % 360
    add("pof_rashi", (pof // 30).astype(int))
    add("pof_sign", (((pof + ayan) % 360) // 30).astype(int))
    nav = lambda L: (np.floor(L * 9 / 30) % 12).astype(int)                # noqa: E731
    add("lagna_navamsa_lord", [LORD[i] for i in nav(lon[:, COL["Lagna"]])])
    add("moon_d27_lord", [LORD[i] for i in dcm.varga(lon[:, COL["Moon"]], 27)])
    rash = (lon // 30).astype(int)
    for name, n in (("vargottama_count", 9), ("vargottama_d10_count", 10), ("vargottama_d24_count", 24)):
        cnt = sum((dcm.varga(lon[:, j], n) if n != 9 else nav(lon[:, j])) == rash[:, j] for j in range(len(nf.BODIES)))
        add(name, cnt)
    add("universal_day", np.array([1 + (sum(int(c) for c in d.strftime("%Y%m%d")) - 1) % 9 for d in days]))
    lab = lambda f: [D.labels[f][c] for c in D.codes[f]]                    # noqa: E731
    wk, ms, al = lab("weekday"), lab("kp_moon_star_lord"), lab("kp_asc_star_lord")
    add("kp_ruling_planets", ["+".join(sorted({WEEK_LORD.get(w, w), LORD[rash[i, COL["Moon"]]], ms[i],
                                               LORD[rash[i, COL["Lagna"]]], al[i]})) for i, w in enumerate(wk)])
    c2, l2, _ = cd.compute(D.dates)
    codes["plum_trigrams"], labels["plum_trigrams"] = c2["mh_hexagram"], l2["mh_hexagram"]
    c3, l3 = nf.nav_codes(D.dates)
    codes.update({k: v for k, v in c3.items() if k.endswith("_navamsa")})
    labels.update({k: v for k, v in l3.items() if k.endswith("_navamsa")})
    c4, l4 = dcm.chart_codes(D.dates)
    codes.update(c4)
    labels.update(l4)
    return codes, labels


def task(test):
    return nf.eval_C(nf.cells(nf.r.G["D"], test))


def main():
    path, dates = sys.argv[1], sys.argv[2:]
    nf.r.setup()
    G = nf.r.G
    G["yr"] = np.array([int(d[:4]) for d in G["D"].dates])
    D = G["D"]
    codes, labels = build(D)
    nf.inject(D, codes, labels)
    raw = [ln.strip() for ln in open(path) if ln.strip()]
    formulas = list(dict.fromkeys(tuple(p.strip() for p in re.split(r"\s*[x×]\s*", ln)) for ln in raw))
    missing = sorted({p for f in formulas for p in f if p not in D.codes})
    if missing:
        print("unknown parameters:", missing)
        formulas = [f for f in formulas if all(p in D.codes for p in f)]
    print(f"{len(raw)} lines, {len(formulas)} distinct formulas")
    rng = np.random.default_rng(53)
    pool_params = sorted(set(nf.r.FACT) | {p for p in codes if not re.match(r"aspect_(\w+)_(\w+)$", p) or
                                           p in {f"aspect_{a.lower()}_{b.lower()}" for a, b in
                                                 itertools.combinations(PLANETS7 + ["Rahu", "Lagna"], 2)}})
    rand = []
    while len(rand) < 500:                                                 # random pairs from the same pool of parameters
        a, b = rng.choice(len(pool_params), 2, replace=False)
        t = (pool_params[a], pool_params[b])
        if t not in rand and t not in formulas:
            rand.append(t)
    with mp.get_context("fork").Pool(4) as pool:
        A = np.array(pool.map(task, formulas, chunksize=4))
        B = np.array(pool.map(task, rand, chunksize=8))

    def choose(X):
        zb, za = nf.zz(X[:, :, 0], X[:, :, 1]), nf.zz(X[:, :, 2], X[:, :, 3])
        c = np.argmax(zb, axis=1)
        i = np.arange(len(X))
        return c, zb[i, c], za[i, c], X[i, c, 2] / X[i, c, 3], za.mean(1)
    ca, zba, zaa, ra, ma = choose(A)
    cb, zbb, zab, rb, mb = choose(B)
    sims = np.array([zab[rng.choice(len(zab), len(formulas), replace=False)].mean() for _ in range(5000)])
    print(f"\nChosen method per formula (best before 2012) -> score on 2012-2026:")
    print(f"   your list: mean z {zaa.mean():+.3f}, {int((zaa > 0).sum())}/{len(zaa)} above chance, {int((zaa > 2).sum())} with z > 2")
    print(f"   (random pairs drawn from the same {len(pool_params)} parameters as the list, base and new)")
    print(f"   500 random pairs: mean z {zab.mean():+.3f}, {np.mean(zab > 0):.0%} above chance, {np.mean(zab > 2):.1%} with z > 2")
    print(f"   share of random sets of {len(formulas)} pairs with a mean at least as high: {np.mean(sims >= zaa.mean()):.2f}")
    print(f"   all 42 methods averaged, 2012-2026: your list {ma.mean():+.3f} vs random {mb.mean():+.3f}")
    order = np.argsort(-zaa)
    rows, _ = sl.load()
    out = []
    print("\nformula | method chosen before 2012 | before z | 2012-2026 | last draws (straight / i-Box)")
    for q in order:
        f = formulas[q]
        p, v, rule = nf.C_COLS[ca[q]]
        tot = [0, 0, 0, 0.0, 0]
        per = {}
        for d in dates:
            t = D.dates.index(d)
            win = {op: {x["4d_number"]: x["prize"] for x in rows[op] if x["date"] == d} for op in sl.OPS}
            pk = sc.picks(t, f, p, v)
            if pk is None:
                continue
            s, sp, b, bp = sc.score({op: pk for op in sl.OPS}, win)
            tot[0] += len(s); tot[1] += sp; tot[2] += len(b); tot[3] += bp; tot[4] += 48
            per[d] = {"straight": s, "straight_rm": sp, "ibox": len(b), "ibox_rm": bp}
        print(f"{' x '.join(f)} | {nf.pname(p)} ({v}) {rule} | {zba[q]:+.2f} | x{ra[q]:.3f} z {zaa[q]:+.2f} | "
              f"RM{tot[4]}: straight {tot[0]} RM{tot[1]}, i-Box {tot[2]} ~RM{tot[3]:.0f}")
        out.append({"formula": " x ".join(f), "method": f"{nf.pname(p)} ({v}) {rule}", "z_before": float(zba[q]),
                    "ratio_after": float(ra[q]), "z_after": float(zaa[q]), "mean_z_all_methods": float(ma[q]),
                    "recent": {"staked": tot[4], "straight_hits": tot[0], "straight_rm": tot[1],
                               "ibox": tot[2], "ibox_rm": tot[3]}, "per_draw": per})
    json.dump({"formulas": out, "random_mean_z_after": float(zab.mean()), "list_mean_z_after": float(zaa.mean()),
               "share_random_sets_as_high": float(np.mean(sims >= zaa.mean())), "dates": dates},
              open(os.path.join(am.ROOT, "analysis", "formula_list_results.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
