#!/usr/bin/env python3
"""Karana x Day pillar (S1 from the previous same-value day, i-Box): does its
family behave the same, and does any relative do better?

  1. the lead in all 42 versions (S1, S2, rank pairs; a / b; Straight / Reverse / i-Box)
  2. its halves: Karana alone, Day pillar alone
  3. families, all scored with the lead's method (S1 (b) i-Box):
       Karana x any other parameter; Day pillar x any other parameter;
       Karana x the parts of the day pillar; Panchanga element x Chinese day element
     each family's average z before 2012 / 2012-2026 and good years, against the
     average over all 3,081 tests and against 20 shifted calendars
  4. the best member of each family chosen on draws before 2012, scored 2012-2026
  5. which karana / day pillar values carry the edge (before vs after correlation)

Run from the repo root:  python3 analysis/karana_family.py
"""

import itertools
import json
import math
import multiprocessing as mp
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am  # noqa: E402
import navamsa_family as nf  # noqa: E402

LEAD = ("karana", "day_pillar")
YEARS = list(range(1985, 2027))
PANCHANGA = ["tithi", "karana", "yoga", "nakshatra", "weekday"]
CHINESE_DAY = ["day_pillar", "day_stem", "day_branch", "nayin", "day_element", "day_officer", "day_god"]
CI = nf.C_COLS.index(("S1", "b", "ibox"))


def norm(t):
    return tuple(sorted(t, key=nf.r.FACT.index))


def per_year(test, shift=0):
    """(hits, expected) per year for the lead's method (S1 (b) i-Box)."""
    r = nf.r
    G = r.G
    cells = r.cells_of(test, shift)
    order = np.lexsort((np.arange(len(cells)), cells))
    sc = cells[order]
    hp = np.r_[False, sc[1:] == sc[:-1]]
    days = order[hp]
    C = G["dday"][order[:-1]][hp[1:]]
    P = r.picks(C, True)
    sd = nf.rk.score_days(days, P)
    h, e = sd["ibox"][0][:, -1].astype(float), sd["ibox"][1][:, -1]
    y = G["yr"][days]
    return np.array([h[y == Y].sum() for Y in YEARS]), np.array([e[y == Y].sum() for Y in YEARS])


def summary(test, shift=0):
    H, E = per_year(test, shift)
    yrs = np.array(YEARS)
    b, a = yrs < 2012, yrs >= 2012
    zb = (H[b].sum() - E[b].sum()) / math.sqrt(E[b].sum())
    za = (H[a].sum() - E[a].sum()) / math.sqrt(E[a].sum())
    good = int(((H > E) & a & (E > 0)).sum())
    return zb, za, good, H[a].sum() / E[a].sum()


def task(args):
    return summary(*args)


def main():
    nf.r.setup()
    G = nf.r.G
    G["yr"] = np.array([int(d[:4]) for d in G["D"].dates])
    F = nf.r.FACT
    out = {}

    # 1. the lead in every version
    A = nf.eval_C(nf.cells(G["D"], LEAD))
    zb, za = nf.zz(A[:, 0], A[:, 1]), nf.zz(A[:, 2], A[:, 3])
    print("1. Karana x Day pillar in every version: z before 2012 | z 2012-2026 (x ratio)")
    rows = []
    for ci, (p, v, rule) in enumerate(nf.C_COLS):
        rows.append((za[ci], f"{nf.pname(p)} ({v}) {rule}", zb[ci], A[ci, 2] / A[ci, 3]))
    for z, name, b, rr in sorted(rows, key=lambda x: -x[0])[:8]:
        print(f"   {name:<20} {b:+.2f} | {z:+.2f} (x{rr:.3f})")
    print(f"   ... all 42 versions: mean z before {zb.mean():+.2f}, after {za.mean():+.2f}; "
          f"{int(((zb > 0) & (za > 0)).sum())} positive in both")
    out["versions"] = [{"version": n, "z_before": float(b), "z_after": float(z), "ratio_after": float(rr)} for z, n, b, rr in rows]

    # 2. halves
    print("\n2. Halves (S1 (b) i-Box): z before | z after | good years 2012-2026 | ratio after")
    for t in (("karana",), ("day_pillar",), LEAD):
        b, a, g, rr = summary(t)
        print(f"   {' x '.join(t):<22} {b:+.2f} | {a:+.2f} | {g}/15 | x{rr:.3f}")

    # 3. families
    fam = {
        "Karana x any other": [norm(("karana", f)) for f in F if f != "karana"],
        "Day pillar x any other": [norm(("day_pillar", f)) for f in F if f != "day_pillar"],
        "Karana x parts of the day pillar": [norm(("karana", f)) for f in ("day_stem", "day_branch", "nayin", "day_element")],
        "Panchanga x Chinese day": [norm((a, b)) for a in PANCHANGA for b in CHINESE_DAY],
    }
    fam = {k: [t for t in v if t != norm(LEAD)] for k, v in fam.items()}
    allt = [(f,) for f in F] + list(itertools.combinations(F, 2))
    rng = np.random.default_rng(91)
    shifts = [int(s) for s in rng.integers(170, G["nd"] - 170, 20)]
    members = sorted({t for v in fam.values() for t in v})
    with mp.get_context("fork").Pool(4) as pool:
        base = np.array(pool.map(task, [(t, 0) for t in allt], chunksize=16))
        real = dict(zip(members, pool.map(task, [(t, 0) for t in members], chunksize=4)))
        null = [dict(zip(members, pool.map(task, [(t, s) for t in members], chunksize=4))) for s in shifts]
    print(f"\n3. Families (S1 (b) i-Box; the lead left out). All 3,081 tests: z before {base[:, 0].mean():+.2f}, "
          f"after {base[:, 1].mean():+.2f}, good years {base[:, 2].mean():.2f}/15")
    out["families"] = {}
    for name, tests in fam.items():
        R = np.array([real[t] for t in tests])
        Nz = np.array([[n[t][1] for t in tests] for n in null]).mean(1)
        Ng = np.array([[n[t][2] for t in tests] for n in null]).mean(1)
        # 4. best member chosen before 2012
        q = int(np.argmax(R[:, 0]))
        print(f"   {name:<34} {len(tests):>3} tests | z before {R[:, 0].mean():+.2f} | z after {R[:, 1].mean():+.2f} "
              f"(shifted {Nz.mean():+.2f}, {int((Nz >= R[:, 1].mean()).sum())}/20 as high) | good years {R[:, 2].mean():.2f} "
              f"(shifted {Ng.mean():.2f}) | {int((R[:, 1] > 0).sum())}/{len(tests)} above chance after")
        print(f"      best chosen before 2012: {' x '.join(tests[q])} (z before {R[q, 0]:+.2f}) -> after z {R[q, 1]:+.2f}, "
              f"x{R[q, 3]:.3f}, {int(R[q, 2])}/15 good years")
        top = sorted(range(len(tests)), key=lambda i: -R[i, 1])[:3]
        print("      best after 2012 (hindsight): " + "; ".join(
            f"{' x '.join(tests[i])} z {R[i, 1]:+.2f} ({int(R[i, 2])}/15, before {R[i, 0]:+.2f})" for i in top))
        out["families"][name] = {"n": len(tests), "mean_z_before": float(R[:, 0].mean()), "mean_z_after": float(R[:, 1].mean()),
                                 "null_mean_z_after": Nz.tolist(), "mean_good_years": float(R[:, 2].mean()),
                                 "null_good_years": Ng.tolist(),
                                 "members": {" x ".join(t): {"z_before": float(x[0]), "z_after": float(x[1]),
                                                             "good_years": int(x[2]), "ratio_after": float(x[3])}
                                             for t, x in zip(tests, R)}}
    b, a, g, rr = summary(LEAD)
    print(f"   (the lead itself: z before {b:+.2f}, after {a:+.2f}, {g}/15 good years, x{rr:.3f})")

    # 5. which values carry it
    D = G["D"]
    cells = nf.r.cells_of(LEAD)
    order = np.lexsort((np.arange(len(cells)), cells))
    sc = cells[order]
    hp = np.r_[False, sc[1:] == sc[:-1]]
    days = order[hp]
    P = nf.r.picks(G["dday"][order[:-1]][hp[1:]], True)
    sd = nf.rk.score_days(days, P)
    h, e = sd["ibox"][0][:, -1].astype(float), sd["ibox"][1][:, -1]
    late = G["yr"][days] >= 2012
    print("\n5. Which values carry the edge (i-Box matches / expected)")
    for f in LEAD:
        codes = D.codes[f][days]
        res = []
        for v in np.unique(codes):
            m = codes == v
            ob, eb = h[m & ~late].sum(), e[m & ~late].sum()
            oa, ea = h[m & late].sum(), e[m & late].sum()
            res.append((D.labels[f][v], ob / eb if eb else 0, oa / ea if ea else 0, (oa - ea) / math.sqrt(ea) if ea else 0,
                        (ob - eb) / math.sqrt(eb) if eb else 0))
        zb_, za_ = np.array([x[4] for x in res]), np.array([x[3] for x in res])
        rho = np.corrcoef(zb_, za_)[0, 1]
        both = sum(1 for x in res if x[1] > 1 and x[2] > 1)
        print(f"   {f}: {len(res)} values; above chance after 2012 {sum(1 for x in res if x[2] > 1)}; in both periods {both}; "
              f"before-vs-after correlation {rho:+.2f}")
        best = sorted(res, key=lambda x: -(x[3] + x[4]))[:5]
        print("      most consistent: " + "; ".join(f"{x[0]} x{x[1]:.2f} -> x{x[2]:.2f}" for x in best))
        out[f"values_{f}"] = [{"value": x[0], "ratio_before": x[1], "ratio_after": x[2]} for x in res]
    json.dump(out, open(os.path.join(am.ROOT, "analysis", "karana_family_results.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
