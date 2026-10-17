#!/usr/bin/env python3
"""Deeper look at the best recurrence lead: Mercury nakshatra x Venus rashi,
S1 built from all earlier same-value days, scored as Straight
(see recurrence_s12.py / recurrence_s12_forward.py).

  1. the lead in all 12 versions (S1/S2 x a/b x Straight/Reverse/i-Box),
     before 2012 / 2012-2026 / all, and its two halves on their own
  2. chance check of the lead: 200 circular shifts of the parameter calendar
  3. split by operator (hits counted on one operator's winners) and by period
  4. families: do relatives show the same thing?
       Mercury nakshatra x any other parameter
       any parameter x Venus rashi
       each body's nakshatra x another body's rashi (Moon, Sun, Mars, Mercury,
         Venus, Jupiter, Saturn, Rahu, Lagna)
       Mercury {rashi, nakshatra, retrograde, combust} x Venus {same}
     each family's average z before and after 2012, against the average over
     all 3,081 tests and against 20 shifted calendars.

Run from the repo root:  python3 analysis/s12_family.py
"""

import itertools
import json
import math
import multiprocessing as mp
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recurrence_s12 as r  # noqa: E402

LEAD = ("mercury_nakshatra", "venus_rashi")
COL = "S1_a_straight"
SPLIT = 2012
ORIG = r.score
BODIES = {"moon": ("nakshatra", "moon_rashi"), "sun": ("sun_nakshatra", "sun_rashi"),
          "mars": ("mars_nakshatra", "mars_rashi"), "mercury": ("mercury_nakshatra", "mercury_rashi"),
          "venus": ("venus_nakshatra", "venus_rashi"), "jupiter": ("jupiter_nakshatra", "jupiter_rashi"),
          "saturn": ("saturn_nakshatra", "saturn_rashi"), "rahu": ("rahu_nakshatra", "rahu_rashi"),
          "lagna": ("lagna_nakshatra", "lagna_rashi")}


def z(oe):
    return (oe[0] - oe[1]) / math.sqrt(oe[1]) if oe[1] > 0 else 0.0


def norm(t):
    return tuple(sorted(t, key=r.FACT.index))


def restricted(lo, hi):
    yr = r.G["yr"]

    def sc(days, P):
        m = (yr[days] >= lo) & (yr[days] < hi)
        return ORIG(days[m], P[m])
    return sc


PERIODS = {"before 2012": (0, SPLIT), "2012-2026": (SPLIT, 9999), "all": (0, 9999)}


def task(args):
    test, shift, period = args
    r.score = restricted(*PERIODS[period])
    return r.evaluate(r.cells_of(test, shift))


def main():
    r.setup()
    G = r.G
    G["yr"] = np.array([int(d[:4]) for d in G["D"].dates])
    out = {}
    pool = mp.get_context("fork").Pool(4)

    # 1. the lead in all versions, and its halves
    print("1. Mercury nakshatra x Venus rashi in every version (z; x ratio)")
    print(f"   {'version':<16}" + "".join(f"{p:>22}" for p in PERIODS))
    rows = {}
    res = {p: task((LEAD, 0, p)) for p in PERIODS}
    for c in r.COLS:
        rows[c] = {p: {"hits": res[p][c][0], "exp": res[p][c][1], "z": z(res[p][c])} for p in PERIODS}
        print(f"   {c:<16}" + "".join(f"{z(res[p][c]):>+12.2f} (x{res[p][c][0] / res[p][c][1]:.3f})" for p in PERIODS))
    out["lead_versions"] = rows
    for t in ((LEAD[0],), (LEAD[1],)):
        rr = {p: task((t, 0, p))[COL] for p in PERIODS}
        print(f"   {t[0]} alone ({COL}): " + ", ".join(f"{p} z {z(v):+.2f} (x{v[0] / v[1]:.3f})" for p, v in rr.items()))
        out[f"{t[0]}_alone"] = {p: z(v) for p, v in rr.items()}

    # 2. chance check with 200 shifts
    rng = np.random.default_rng(7)
    shifts = [int(s) for s in rng.integers(170, G["nd"] - 170, 200)]
    print("\n2. Lead vs 200 shifted calendars (same rule, parameters slid in time):")
    out["shift_check"] = {}
    for p in ("2012-2026", "all"):
        real = z(res[p][COL])
        sims = np.array([z(x[COL]) for x in pool.map(task, [(LEAD, s, p) for s in shifts], chunksize=8)])
        share = float(np.mean(sims >= real))
        print(f"   {p:<10} real z {real:+.2f}; shifted mean {sims.mean():+.2f} sd {sims.std():.2f}; "
              f"share of shifts as high {share:.3f}")
        out["shift_check"][p] = {"real_z": real, "shift_mean": float(sims.mean()), "shift_sd": float(sims.std()),
                                 "share_as_high": share}

    # 3. by operator and by period
    print("\n3. By operator (hits on that operator's winners only) and by period:")
    D = G["D"]
    keep = {k: G[k] for k in ("W", "Cb", "nwin")}
    out["by_operator"] = {}
    for o, name in enumerate(r.am.OPS):
        m = D.ro == o
        key = np.unique(D.rd[m].astype(np.int64) * 10000 + D.rn[m])
        wd, wn = key // 10000, key % 10000
        W = np.zeros_like(keep["W"])
        W[wd, wn] = True
        Cb = np.zeros_like(keep["Cb"])
        np.add.at(Cb, (wd, G["box"][wn]), 1)
        G.update(W=W, Cb=Cb, nwin=np.bincount(wd, minlength=G["nd"]).astype(float))
        rr = {p: task((LEAD, 0, p))[COL] for p in PERIODS}
        print(f"   {name:<12} " + ", ".join(f"{p} {v[0]:.0f} vs {v[1]:.1f} (x{v[0] / v[1]:.3f}, z {z(v):+.2f})"
                                          for p, v in rr.items()))
        out["by_operator"][name] = {p: {"hits": v[0], "exp": v[1], "z": z(v)} for p, v in rr.items()}
    G.update(keep)
    out["by_period"] = {}
    for lo, hi in ((1985, 1995), (1995, 2005), (2005, 2012), (2012, 2019), (2019, 2027)):
        r.score = restricted(lo, hi)
        v = r.evaluate(r.cells_of(LEAD))[COL]
        print(f"   {lo}-{hi - 1}: {v[0]:.0f} hits vs {v[1]:.1f} (x{v[0] / v[1]:.3f}, z {z(v):+.2f})")
        out["by_period"][f"{lo}-{hi - 1}"] = {"hits": v[0], "exp": v[1], "z": z(v)}

    # 4. families
    others = [f for f in r.FACT if f not in LEAD]
    nak = [b[0] for b in BODIES.values()]
    ras = [b[1] for b in BODIES.values()]
    fam = {
        "Mercury nakshatra x any": [norm((LEAD[0], f)) for f in r.FACT if f != LEAD[0]],
        "any x Venus rashi": [norm((f, LEAD[1])) for f in r.FACT if f != LEAD[1]],
        "body nakshatra x other body rashi": [norm((a, b)) for (pa, (a, _)), (pb, (_, b)) in
                                              itertools.product(BODIES.items(), BODIES.items()) if pa != pb],
        "Mercury x Venus (rashi/nakshatra/retro/combust)": [norm((a, b)) for a, b in itertools.product(
            ["mercury_rashi", "mercury_nakshatra", "mercury_retrograde", "mercury_combust"],
            ["venus_rashi", "venus_nakshatra", "venus_retrograde", "venus_combust"])],
    }
    # leave the lead itself out of every family
    fam = {k: [t for t in v if t != norm(LEAD)] for k, v in fam.items()}
    all_tests = [(f,) for f in r.FACT] + list(itertools.combinations(r.FACT, 2))
    zall = {p: np.array([z(x[COL]) for x in pool.map(task, [(t, 0, p) for t in all_tests], chunksize=16)])
            for p in ("before 2012", "2012-2026")}
    idx = {t: i for i, t in enumerate(all_tests)}
    print(f"\n4. Families ({COL}; the lead itself left out). All 3,081 tests: mean z before 2012 "
          f"{zall['before 2012'].mean():+.2f}, after {zall['2012-2026'].mean():+.2f}")
    sh20 = shifts[:20]
    out["families"] = {}
    for name, tests in fam.items():
        ii = [idx[t] for t in tests]
        zb, za = zall["before 2012"][ii], zall["2012-2026"][ii]
        null = []
        for s in sh20:
            null.append(np.mean([z(x[COL]) for x in pool.map(task, [(t, s, "2012-2026") for t in tests], chunksize=4)]))
        null = np.array(null)
        print(f"   {name:<48} {len(tests):>3} tests | before 2012 mean z {zb.mean():+.2f} | 2012-2026 mean z "
              f"{za.mean():+.2f}, {int((za > 0).sum())}/{len(tests)} above 0, {int((za > 2).sum())} with z>2 | "
              f"shifted calendars' family mean {null.mean():+.2f} (sd {null.std():.2f}; {int((null >= za.mean()).sum())}/20 as high)")
        top = sorted(zip(tests, za, zb), key=lambda x: -x[1])[:3]
        print("      best after 2012: " + "; ".join(f"{' x '.join(t)} {a:+.2f} (before {b:+.2f})" for t, a, b in top))
        out["families"][name] = {"n": len(tests), "mean_z_before": float(zb.mean()), "mean_z_after": float(za.mean()),
                                 "above0_after": int((za > 0).sum()), "z_gt_2_after": int((za > 2).sum()),
                                 "null_mean": float(null.mean()), "null_sd": float(null.std()),
                                 "null_as_high": int((null >= za.mean()).sum()),
                                 "members": {" x ".join(t): {"before": float(b), "after": float(a)} for t, a, b in zip(tests, za, zb)}}
    pool.close()
    json.dump(out, open(os.path.join(r.ROOT, "analysis", "s12_family_results.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
