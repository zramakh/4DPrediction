#!/usr/bin/env python3
"""Eight checks of the lead Karana x Day pillar (S1 from the previous same-value
day, i-Box). Hits = winners that are an arrangement of one of the 16 picks
(distinct boxes), chance = winners x that year's box probability, as in
recurrence_s12.py.

  2  shuffle Karana within each Day pillar (200 permutations): does Karana add
     anything beyond the Day pillar groups?
  3  edge over time: excess hits per year, cumulative, and a bootstrap over
     years (2012-2026) for the ratio's confidence range
  4  source age: result by calendar days back to the source draw
  5  distance-matched control: source = a draw 1-3 draw days next to the true
     source (similar age, different Karana x Day pillar)
  6  Karana at other times: sunrise (07:00 MYT) and 19:30 MYT vs 19:00
  7  which numbers of the source day matter: top-3 only, Specials only,
     Consolations only, one operator only
  8  pick construction: top-3 digits per position (81), ranked top 8 / 16 / 32,
     grid 16 (the lead)
  9  bankroll 2012-2026: RM1 per pick per operator, Big i-Box on all 16 and
     Big / Small i-Box on two-pair picks only; return, longest losing run,
     worst drawdown, against random picks of the same patterns

Run from the repo root:  python3 analysis/karana_tests.py
"""

import datetime as dt
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am  # noqa: E402
import recurrence_s12 as r  # noqa: E402
import recurrence_s12_k as rk  # noqa: E402
import vedic  # noqa: E402

LEAD = ("karana", "day_pillar")
SPLIT = 2012
YEARS = np.arange(SPLIT, 2027)
BIG = {"1st": 2500, "2nd": 1000, "3rd": 500, "Special": 180, "Consolation": 60}
SMALL = {"1st": 3500, "2nd": 2000, "3rd": 1000, "Special": 0, "Consolation": 0}
TOP3 = ("1st", "2nd", "3rd")
OUT = {}


def pairs(cells):
    """(scored days, source day) with source = previous day with the same cell."""
    order = np.lexsort((np.arange(len(cells)), cells))
    sc = cells[order]
    hp = np.r_[False, sc[1:] == sc[:-1]]
    return order[hp], order[:-1][hp[1:]]


def ibox(days, P):
    """Per-day (hits, expected) for i-Box picks P (n, K)."""
    G = r.G
    B = G["box"][P]
    f = rk.first_in_row(B)
    h = (G["Cb"][days[:, None], B] * f).sum(1)
    e = G["nwin"][days] * (G["Pbox"][G["yix"][days][:, None], B] * f).sum(1)
    return h.astype(float), e


def stats(days, h, e):
    late = G["yr"][days] >= SPLIT
    hb, eb, ha, ea = h[~late].sum(), e[~late].sum(), h[late].sum(), e[late].sum()
    good = sum(1 for Y in YEARS if h[G["yr"][days] == Y].sum() > e[G["yr"][days] == Y].sum())
    return {"z_before": (hb - eb) / math.sqrt(eb), "z_after": (ha - ea) / math.sqrt(ea), "ratio_before": hb / eb,
            "ratio_after": ha / ea, "good_years": good, "hits_after": ha, "exp_after": ea}


def lead(cells, src_counts=None, hot=True):
    days, src = pairs(cells)
    C = (G["dday"] if src_counts is None else src_counts)[src]
    return days, src, ibox(days, r.picks(C, hot))


def fmt(s):
    return (f"before x{s['ratio_before']:.3f} (z {s['z_before']:+.2f}) | 2012-2026 x{s['ratio_after']:.3f} "
            f"(z {s['z_after']:+.2f}) | {s['good_years']}/15 good years")


# ------------------------------------------------------------------ tests
def t2_shuffle(cells, n=200):
    D = G["D"]
    k, p = D.codes["karana"], D.codes["day_pillar"]
    days, _, (h, e) = lead(cells)
    real = stats(days, h, e)
    rng = np.random.default_rng(2)
    res = []
    for _ in range(n):
        ks = k.copy()
        for v in np.unique(p):
            m = np.flatnonzero(p == v)
            ks[m] = ks[rng.permutation(m)]
        c = ks.astype(np.int64) * (int(p.max()) + 1) + p
        dd, _, (hh, ee) = lead(c)
        res.append(stats(dd, hh, ee))
    zb = np.array([x["z_before"] for x in res])
    za = np.array([x["z_after"] for x in res])
    gy = np.array([x["good_years"] for x in res])
    print("\n2. Karana shuffled within each Day pillar (200 permutations)")
    print(f"   real lead:  {fmt(real)}")
    print(f"   shuffled:   z before mean {zb.mean():+.2f} (as high {int((zb >= real['z_before']).sum())}/{n}) | "
          f"z after mean {za.mean():+.2f} (as high {int((za >= real['z_after']).sum())}/{n}) | "
          f"good years mean {gy.mean():.1f} (as many {int((gy >= real['good_years']).sum())}/{n})")
    both = int(((zb >= real["z_before"]) & (za >= real["z_after"])).sum())
    print(f"   shuffles at least as good in both periods: {both}/{n}")
    OUT["2_shuffle"] = {"real": real, "z_before": zb.tolist(), "z_after": za.tolist(), "good_years": gy.tolist()}


def t3_time(cells):
    days, _, (h, e) = lead(cells)
    yr = G["yr"][days]
    print("\n3. Edge over time (excess = hits - expected)")
    rows, cum = [], 0.0
    allY = np.arange(1986, 2027)
    for Y in allY:
        m = yr == Y
        x = h[m].sum() - e[m].sum()
        cum += x
        rows.append((int(Y), float(h[m].sum()), float(e[m].sum()), float(x), float(cum)))
    for i in range(0, len(rows), 7):
        print("   " + " | ".join(f"{Y}: {hh:.0f}/{ee:.0f} ({x:+.0f}, cum {c:+.0f})" for Y, hh, ee, x, c in rows[i:i + 7]))
    late = [x for x in rows if x[0] >= SPLIT]
    H = np.array([x[1] for x in late])
    E = np.array([x[2] for x in late])
    rng = np.random.default_rng(3)
    bs = []
    for _ in range(10000):
        s = rng.integers(0, len(H), len(H))
        bs.append(H[s].sum() / E[s].sum())
    lo, hi = np.percentile(bs, [2.5, 97.5])
    rat = H / E
    slope = np.polyfit(YEARS, rat, 1)[0]
    early = H[:7].sum() / E[:7].sum()
    later = H[7:].sum() / E[7:].sum()
    print(f"   2012-2026 ratio x{H.sum() / E.sum():.3f}, 95% range by resampling years x{lo:.3f} to x{hi:.3f}; "
          f"share of resamples above x1: {np.mean(np.array(bs) > 1):.3f}")
    print(f"   trend of the yearly ratio: {slope * 10:+.3f} per decade | 2012-2018 x{early:.3f}, 2019-2026 x{later:.3f}")
    E5 = [x for x in rows if x[0] < SPLIT]
    print(f"   1986-2011 ratio x{sum(x[1] for x in E5) / sum(x[2] for x in E5):.3f}")
    OUT["3_time"] = {"years": rows, "ci95": [lo, hi], "slope_per_year": slope, "ratio_2012_18": early, "ratio_2019_26": later}


def t4_age(cells):
    days, src, (h, e) = lead(cells)
    D = G["D"]
    dd = np.array([dt.date.fromisoformat(d).toordinal() for d in D.dates])
    gap = dd[days] - dd[src]
    print("\n4. Source age (calendar days back to the previous same Karana x Day pillar draw)")
    print(f"   gap: median {np.median(gap):.0f} days, 25%-75% {np.percentile(gap, 25):.0f}-{np.percentile(gap, 75):.0f}")
    edges = [0, 120, 240, 420, 720, 1200, 100000]
    late = G["yr"][days] >= SPLIT
    rows = []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (gap >= a) & (gap < b)
        res = []
        for sel in (m & ~late, m & late, m):
            o, x = h[sel].sum(), e[sel].sum()
            res.append((o / x if x else 0, (o - x) / math.sqrt(x) if x else 0, int(sel.sum())))
        rows.append({"from": a, "to": b, "before": res[0], "after": res[1], "all": res[2]})
        print(f"   {a:>5}-{b if b < 100000 else '':<5} days: {res[2][2]:>4} days scored | before x{res[0][0]:.3f} "
              f"(z {res[0][1]:+.2f}) | 2012-2026 x{res[1][0]:.3f} (z {res[1][1]:+.2f}) | all x{res[2][0]:.3f} (z {res[2][1]:+.2f})")
    OUT["4_age"] = rows


def t5_control(cells):
    days, src, (h, e) = lead(cells)
    real = stats(days, h, e)
    print("\n5. Distance-matched control: source moved 1-3 draw days from the true source "
          "(about the same age, different Karana x Day pillar)")
    print(f"   true source:          {fmt(real)}")
    OUT["5_control"] = {"real": real}
    allh, alle, alld = [], [], []
    for off in (-3, -2, -1, 1, 2, 3):
        s2 = src + off
        ok = (s2 >= 0) & (s2 < days) & (cells[np.clip(s2, 0, None)] != cells[days])
        P = r.picks(G["dday"][s2[ok]], True)
        hh, ee = ibox(days[ok], P)
        s = stats(days[ok], hh, ee)
        allh.append(hh), alle.append(ee), alld.append(days[ok])
        print(f"   source {off:+d} draw day{'s' if abs(off) > 1 else ' '}:   {fmt(s)}")
        OUT["5_control"][str(off)] = s
    s = stats(np.concatenate(alld), np.concatenate(allh), np.concatenate(alle))
    print(f"   all 6 controls pooled: {fmt(s)}")
    OUT["5_control"]["pooled"] = s


def karana_at(hour, minute):
    D = G["D"]
    lab = D.labels["karana"]
    out = np.zeros(G["nd"], np.int64)
    for i, d in enumerate(D.dates):
        day = dt.date.fromisoformat(d)
        t = dt.datetime.combine(day, dt.time(0)) + dt.timedelta(hours=hour - 8, minutes=minute)   # MYT -> UTC
        jd = vedic.eph.julian_day(t)
        half = int(((vedic.sidereal("Moon", jd) - vedic.sidereal("Sun", jd)) % 360) // 6)     # as vedic.panchanga
        k = ("Kimstughna" if half == 0 else ["Shakuni", "Chatushpada", "Naga"][half - 57] if half >= 57
             else vedic.KARANAS_MOVABLE[(half - 1) % 7])
        out[i] = lab.index(k)
    return out


def t6_timing():
    D = G["D"]
    p = D.codes["day_pillar"].astype(np.int64)
    print("\n6. Karana taken at other times of the draw day (Day pillar unchanged)")
    OUT["6_timing"] = {}
    for name, (hh, mm) in (("sunrise 07:00", (7, 0)), ("19:00 (lead)", (19, 0)), ("19:30", (19, 30))):
        k = karana_at(hh, mm)
        same = np.mean(k == D.codes["karana"])
        c = k * (int(p.max()) + 1) + p
        days, _, (h, e) = lead(c)
        s = stats(days, h, e)
        print(f"   {name:<14} (same Karana as 19:00 on {100 * same:.0f}% of days): {fmt(s)}")
        OUT["6_timing"][name] = {**s, "same_as_1900": float(same)}


def subset_counts(keep):
    """Digit counts per day (nd, 4, 10) from the winners whose (prize, operator) pass keep()."""
    out = np.zeros((G["nd"], 4, 10))
    for (t, o), (_, prizes) in DRAWS.items():
        seen = {n for p, n in prizes if keep(str(p), o)}
        for n in seen:
            for q in range(4):
                out[t, q, am.DIG[n, q]] += 1
    return out


def t7_sources(cells):
    print("\n7. Which numbers of the source day are used to build the 16 picks")
    sets = {"all 69 (lead)": None,
            "top-3 prizes only": lambda p, o: p in TOP3,
            "Specials only": lambda p, o: p == "Special",
            "Consolations only": lambda p, o: p == "Consolation"}
    for o, name in enumerate(am.OPS):
        sets[f"{name} only"] = (lambda oo: lambda p, o: o == oo)(o)
    OUT["7_sources"] = {}
    for name, keep in sets.items():
        days, _, (h, e) = lead(cells, None if keep is None else subset_counts(keep))
        s = stats(days, h, e)
        print(f"   {name:<20} {fmt(s)}")
        OUT["7_sources"][name] = s


def t8_picks(cells):
    days, src = pairs(cells)
    ranked, g16, g81 = rk.pick_sets(G["dday"][src], True)
    print("\n8. Pick construction (S1 from the previous same-value day, i-Box)")
    OUT["8_picks"] = {}
    for name, P in (("grid 16 (lead)", g16), ("top-3 digits per position (81)", g81), ("ranked top 8", ranked[:, :8]),
                    ("ranked top 16", ranked[:, :16]), ("ranked top 32", ranked[:, :32]), ("ranked top 4", ranked[:, :4])):
        h, e = ibox(days, P)
        s = stats(days, h, e)
        print(f"   {name:<32} {fmt(s)}")
        OUT["8_picks"][name] = s


def perms(n):
    s = f"{n:04d}"
    return math.factorial(4) // math.prod(math.factorial(s.count(c)) for c in set(s))


PERMS = np.array([perms(n) for n in range(10000)])


def pay_tables():
    """Per day: Big / Small i-Box payout per RM1 bet on each box, summed over operators; operators drawing."""
    nb = int(G["box"].max()) + 1
    big = np.zeros((G["nd"], nb), np.float32)
    small = np.zeros((G["nd"], nb), np.float32)
    nops = np.zeros(G["nd"], int)
    for (t, o), (_, prizes) in DRAWS.items():
        nops[t] += 1
        for p, n in prizes:
            p = str(p)
            big[t, G["box"][n]] += BIG[p] / PERMS[n]
            small[t, G["box"][n]] += SMALL[p] / PERMS[n]
    return big, small, nops


def bankroll(days, P, mask, pay, nops):
    """Day-by-day stake and return for picks P (n, 16) where mask (n, 16) marks the picks bet."""
    B = G["box"][P]
    stake = mask.sum(1) * nops[days]
    ret = (pay[days[:, None], B] * mask).sum(1)
    return stake.astype(float), ret.astype(float)


def run_stats(stake, ret):
    bet = stake > 0
    s, x = stake[bet], ret[bet]
    pnl = np.cumsum(x - s)
    dd = (np.maximum.accumulate(np.r_[0, pnl])[1:] - pnl).max()
    lose = x < s
    run = best = 0
    for v in lose:
        run = run + 1 if v else 0
        best = max(best, run)
    return {"days_bet": int(bet.sum()), "stake": float(s.sum()), "return": float(x.sum()),
            "return_pct": float(100 * x.sum() / s.sum()), "net": float(x.sum() - s.sum()),
            "longest_losing_run": int(best), "worst_drawdown": float(dd), "winning_days": int((x > 0).sum())}


def t9_bankroll(cells):
    days, src = pairs(cells)
    late = G["yr"][days] >= SPLIT
    days, src = days[late], src[late]
    P = r.picks(G["dday"][src], True)
    big, small, nops = pay_tables()
    aabb = PERMS[P] == 6
    full = np.ones_like(P, bool)
    print("\n9. Bankroll 2012-2026 (RM1 per pick per operator, every draw day with an earlier same-value day)")
    OUT["9_bankroll"] = {}
    rng = np.random.default_rng(9)
    pool = {k: np.flatnonzero(PERMS == k) for k in (1, 4, 6, 12, 24)}
    for name, mask, pay in (("all 16, Big i-Box", full, big), ("two-pair picks, Big i-Box", aabb, big),
                            ("two-pair picks, Small i-Box", aabb, small)):
        st = run_stats(*bankroll(days, P, mask, pay, nops))
        # random picks with the same pattern of each pick, 200 times
        rnd = []
        for _ in range(200):
            R = np.zeros_like(P)
            for k, ids in pool.items():
                m = PERMS[P] == k
                R[m] = rng.choice(ids, m.sum())
            rnd.append(run_stats(*bankroll(days, R, mask, pay, nops)))
        rp = np.array([x["return_pct"] for x in rnd])
        rd = np.array([x["worst_drawdown"] for x in rnd])
        print(f"   {name:<28} {st['days_bet']} days bet, stake RM{st['stake']:,.0f}, returned RM{st['return']:,.0f} "
              f"({st['return_pct']:.1f}%), net RM{st['net']:+,.0f}")
        print(f"   {'':<28} winning days {st['winning_days']}, longest losing run {st['longest_losing_run']} draw days, "
              f"worst drawdown RM{st['worst_drawdown']:,.0f}")
        print(f"   {'':<28} random picks (same patterns, 200 runs): return {np.median(rp):.1f}% median "
              f"({np.percentile(rp, 5):.1f}-{np.percentile(rp, 95):.1f}%), lead beats {int((rp < st['return_pct']).sum())}/200; "
              f"drawdown median RM{np.median(rd):,.0f}")
        OUT["9_bankroll"][name] = {**st, "random_return_pct": rp.tolist()}


def main():
    global G, DRAWS
    r.setup()
    G = r.G
    G["yr"] = np.array([int(d[:4]) for d in G["D"].dates])
    _, _, _, _, DRAWS, _ = am.load()
    cells = r.cells_of(LEAD)
    days, _, (h, e) = lead(cells)
    print("Lead Karana x Day pillar, S1 (b) i-Box: " + fmt(stats(days, h, e)))
    tests = sys.argv[1:] or ["2", "3", "4", "5", "6", "7", "8", "9"]
    for t in tests:
        {"2": t2_shuffle, "3": t3_time, "4": t4_age, "5": t5_control, "6": lambda c: t6_timing(), "7": t7_sources,
         "8": t8_picks, "9": t9_bankroll}[t](cells)
        sys.stdout.flush()
    path = os.path.join(am.ROOT, "analysis", "karana_tests_results.json")
    old = json.load(open(path)) if os.path.exists(path) and len(tests) < 8 else {}
    json.dump({**old, **OUT}, open(path, "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
