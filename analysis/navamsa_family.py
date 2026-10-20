#!/usr/bin/env python3
"""D9 navamsa family: does the navamsa (alone or paired) play a role?

New parameters at the 19:00 MYT draw (sidereal, Lahiri, from the positions in
continuous_astro_positions.npz):
  <body>_navamsa     D9 sign of Sun, Moon, Mars, Mercury, Jupiter, Venus,
                     Saturn, Rahu, Lagna (floor(longitude * 9 / 30) mod 12)
  <body>_vargottama  same sign in D1 (rashi) and D9 (navamsa)
Tests (1,557): the 18 alone, all 153 pairs within the family, and each with the
77 other Vedic / Chinese parameters. The analyses done before, on this family:
  A  digit mix given the value(s): learned before 2012, log-likelihood gain on
     2012-2026 (as continuous_astro.py)
  B  same 4D number again when the value(s) recur: Straight / Reverse / i-Box,
     (a) any later / (b) next same-value day (as recurrence_perm.py)
  C  digit-position picks from earlier same-value days, (a) all / (b) previous
     day: S1 (2 hottest), S2 (2 coldest), S3 and rank pairs 1+10, 2+9, 3+8,
     4+7, 5+6; Straight / Reverse / i-Box (as recurrence_s12.py, _s3, _rankpairs)
  D  whole-number hot / cold from all earlier same-value days (as
     whole_number_test.py)
Each is compared with the same scan on circularly shifted parameter calendars;
C and D also with the forward check (top 5 chosen before 2012, scored 2012-2026).

Run from the repo root:  python3 analysis/navamsa_family.py [n_shifts]
"""

import itertools
import json
import math
import multiprocessing as mp
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am  # noqa: E402
import recurrence_perm as rperm  # noqa: E402
import recurrence_rankpairs as rpair  # noqa: E402
import recurrence_s12 as r  # noqa: E402
import recurrence_s12_k as rk  # noqa: E402
import whole_number_test as wn  # noqa: E402

BODIES = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Lagna"]
RASHIS = ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya", "Tula", "Vrischika",
          "Dhanu", "Makara", "Kumbha", "Meena"]
NAVF = [f"{b.lower()}_navamsa" for b in BODIES] + [f"{b.lower()}_vargottama" for b in BODIES]
SPLIT = 2012
RULES = ("straight", "reverse", "ibox")
PICKERS = ["S1", "S2", (0, 9), (1, 8), (2, 7), (3, 6), (4, 5)]
C_COLS = [(p, v, rule) for p in PICKERS for v in "ab" for rule in RULES]


def pname(p):
    return p if isinstance(p, str) else f"{p[0] + 1}+{p[1] + 1}"


def nav_codes(dates):
    z = np.load(os.path.join(am.ROOT, "analysis", "continuous_astro_positions.npz"), allow_pickle=True)
    assert list(z["dates"]) == list(dates), "positions cache is out of date: run continuous_astro.py"
    lon = z["lon"]                                                        # (dates, 9) in BODIES order
    codes, labels = {}, {}
    for j, b in enumerate(BODIES):
        nav = (np.floor(lon[:, j] * 9 / 30) % 12).astype(int)
        rash = (lon[:, j] // 30).astype(int)
        codes[f"{b.lower()}_navamsa"] = nav
        labels[f"{b.lower()}_navamsa"] = RASHIS
        codes[f"{b.lower()}_vargottama"] = (nav == rash).astype(int)
        labels[f"{b.lower()}_vargottama"] = ["no", "yes"]
    return codes, labels


def inject(D, codes, labels):
    for k in codes:
        D.codes[k] = codes[k]
        D.labels[k] = labels[k]


def cells(D, test, shift=0):
    c = np.zeros(len(D.dates), np.int64)
    for f in test:
        c = c * (int(D.codes[f].max()) + 1) + D.codes[f]
    return np.roll(c, shift) if shift else c


# ---------- A: digit mix given the value(s)
def eval_A(cl):
    D = r.G["D"]
    yr = r.G["yr"]
    rd, dig = D.rd, D.rdig
    code = np.unique(cl, return_inverse=True)[1][rd]
    train = yr[rd] < SPLIT
    test = ~train
    base = np.stack([np.bincount(dig[train, p], minlength=10) for p in range(4)]).astype(float)
    base /= base.sum(1, keepdims=True)
    n = int(code.max()) + 1
    cnt = np.zeros((n, 4, 10))
    for p in range(4):
        np.add.at(cnt[:, p], (code[train], dig[train, p]), 1)
    q = (cnt + 500 * base[None]) / (cnt.sum(2, keepdims=True) + 500)
    ct = code[test]
    ll = sum(np.log(q[ct, p, dig[test, p]] / base[p, dig[test, p]]) for p in range(4))
    return np.array([1000 * ll.sum() / (4 * len(ll))])


# ---------- C: digit-position pickers with before / after split
def eval_C(cl):
    G = r.G
    dday = G["dday"]
    order = np.lexsort((np.arange(len(cl)), cl))
    sc = cl[order]
    newgrp = np.r_[True, sc[1:] != sc[:-1]]
    hp = ~newgrp
    days = order[hp]
    late = G["yr"][days] >= SPLIT
    cs = np.cumsum(dday[order], axis=0)
    start = np.maximum.accumulate(np.where(newgrp, np.arange(len(sc)), 0))
    base = np.where((start > 0)[:, None, None], cs[np.maximum(start - 1, 0)], 0)
    src = {"a": (cs - dday[order] - base)[hp], "b": dday[order[:-1]][hp[1:]]}
    ranked = {v: np.argsort(-C, axis=2, kind="stable") for v, C in src.items()}
    res = {}
    for p in PICKERS:
        for v in "ab":
            if p == "S1":
                P = r.picks(src[v], True)
            elif p == "S2":
                P = r.picks(src[v], False)
            else:
                P = rpair.pair_picks(ranked[v], p)
            sd = rk.score_days(days, P)
            for rule in RULES:
                h, e = sd[rule][0][:, -1].astype(float), sd[rule][1][:, -1]
                res[(p, v, rule)] = (h[~late].sum(), e[~late].sum(), h[late].sum(), e[late].sum())
    return np.array([res[c] for c in C_COLS])


def task(args):
    mode, test, shift = args
    if mode == "A":
        return eval_A(cells(r.G["D"], test, shift))
    if mode == "B":
        o = rperm.evaluate(cells(rperm.G["D"], test, shift))
        return np.array([x for t in RULES for x in o[t]])                 # obs_a, exp_a, obs_b, exp_b per rule
    if mode == "C":
        return eval_C(cells(r.G["D"], test, shift))
    return wn.evaluate(cells(r.G["D"], test, shift))


def zz(o, e):
    return (o - e) / np.sqrt(np.maximum(e, 1e-9))


def fwd_stats(A):
    zb, za = zz(A[:, :, 0], A[:, :, 1]), zz(A[:, :, 2], A[:, :, 3])
    zall = zz(A[:, :, 0] + A[:, :, 2], A[:, :, 1] + A[:, :, 3])
    top = np.argsort(-zb, axis=0)[:5]
    return zb, za, zall, top, np.take_along_axis(za, top, 0).mean(0)


def setup_all(extra_codes, extra_labels):
    """Load data for all analyses and add extra parameters to both data copies."""
    wn.setup()                                                            # also runs recurrence_s12.setup()
    rperm.setup()
    for D in (r.G["D"], rperm.G["D"]):
        inject(D, extra_codes, extra_labels)


def run_suite(tests, n_shifts, out_name, seed=41):
    """Analyses A-D on the given tests; prints the summary and writes analysis/<out_name>."""
    t0 = time.time()
    names = [" x ".join(t) for t in tests]
    print(f"{len(tests)} tests", flush=True)
    rng = np.random.default_rng(seed)
    shifts = [int(s) for s in rng.integers(170, r.G["nd"] - 170, n_shifts)]
    out = {"tests": len(tests), "n_shifts": n_shifts}
    with mp.get_context("fork").Pool(4) as pool:
        def scan(mode, sh):
            return np.array(pool.map(task, [(mode, t, sh) for t in tests], chunksize=8))

        # A
        a_real = scan("A", 0)[:, 0]
        a_null = np.array([scan("A", s)[:, 0] for s in shifts])
        print(f"\nA. digit mix given the value(s), log-likelihood gain on 2012-2026 (milli-nats per digit; 0 = no information)")
        print(f"   tests with gain > 0: {int((a_real > 0).sum())} (shifted calendars {np.mean((a_null > 0).sum(1)):.1f})")
        print(f"   best {a_real.max():+.3f} [{names[int(a_real.argmax())]}] vs shifted best {a_null.max(1).mean():+.3f} "
              f"({int((a_null.max(1) >= a_real.max()).sum())}/{n_shifts} as high); singles: " +
              ", ".join(f"{t[0]} {a_real[i]:+.3f}" for i, t in enumerate(tests[:18])), flush=True)
        out["A"] = {"gain": dict(zip(names, a_real.tolist())), "null_best": a_null.max(1).tolist(),
                    "null_n_pos": (a_null > 0).sum(1).tolist()}

        # B
        b_real = scan("B", 0)
        b_null = [scan("B", s) for s in shifts]
        print(f"\nB. same 4D number when the value(s) recur ({time.time() - t0:.0f}s)")
        out["B"] = {}
        for k, rule in enumerate(RULES):
            for v, (oi, ei) in (("a any later day", (4 * k, 4 * k + 1)), ("b next day", (4 * k + 2, 4 * k + 3))):
                z = zz(b_real[:, oi], b_real[:, ei])
                zn = np.array([zz(x[:, oi], x[:, ei]) for x in b_null])
                q = int(np.argmax(z))
                print(f"   {rule:<9} ({v:<15}) z>2 {int((z > 2).sum()):>3} (shifted {np.mean((zn > 2).sum(1)):.0f}) | best {z[q]:+.2f} "
                      f"[{names[q]}] x{b_real[q, oi] / b_real[q, ei]:.3f} | shifted best {zn.max(1).mean():+.2f} "
                      f"({int((zn.max(1) >= z[q]).sum())}/{n_shifts} as high)", flush=True)
                out["B"][f"{rule} {v}"] = {"z_gt_2": int((z > 2).sum()), "null_z_gt_2": (zn > 2).sum(1).tolist(),
                                          "best": float(z[q]), "best_test": names[q], "null_best": zn.max(1).tolist()}

        # C
        c_real = scan("C", 0)
        c_null = [fwd_stats(scan("C", s)) for s in shifts]
        zb, za, zall, top, fwd = fwd_stats(c_real)
        nf = np.array([x[4] for x in c_null])
        nb = np.array([x[2].max(0) for x in c_null])
        ng = np.array([(x[2] > 2).sum(0) for x in c_null])
        print(f"\nC. digit-position picks ({time.time() - t0:.0f}s): z>2 real (shifted) | best z (shifted, as high) | "
              f"forward real (shifted, as high)")
        out["C"] = []
        for ci, (p, v, rule) in enumerate(C_COLS):
            best = float(zall[:, ci].max())
            print(f"   {pname(p):<5} ({v}) {rule:<9} {int((zall[:, ci] > 2).sum()):>4} ({ng[:, ci].mean():>4.0f}) | {best:+.2f} "
                  f"({nb[:, ci].mean():+.2f}, {int((nb[:, ci] >= best).sum())}/{n_shifts}) | {fwd[ci]:+.2f} "
                  f"({nf[:, ci].mean():+.2f}, {int((nf[:, ci] >= fwd[ci]).sum())}/{n_shifts})")
            out["C"].append({"picks": pname(p), "version": v, "rule": rule, "z_gt_2": int((zall[:, ci] > 2).sum()),
                             "null_z_gt_2": ng[:, ci].tolist(), "best_z": best,
                             "best_test": names[int(np.argmax(zall[:, ci]))], "null_best": nb[:, ci].tolist(),
                             "forward": float(fwd[ci]), "null_forward": nf[:, ci].tolist(),
                             "forward_tests": [{"test": names[q], "z_before": float(zb[q, ci]),
                                                "hits_after": float(c_real[q, ci, 2]), "exp_after": float(c_real[q, ci, 3]),
                                                "z_after": float(za[q, ci])} for q in top[:, ci]]})
        beat = np.array([(nf[:, ci] < fwd[ci]).mean() for ci in range(len(C_COLS))])
        print(f"   forward mean over all {len(C_COLS)} columns: real {fwd.mean():+.3f} vs shifted {nf.mean():+.3f}; "
              f"columns beating every shift: {int((beat == 1).sum())} (about {len(C_COLS) / (n_shifts + 1):.1f} by chance)")
        for ci in np.flatnonzero(beat == 1):
            p, v, rule = C_COLS[ci]
            x = out["C"][ci]["forward_tests"][0]
            print(f"      {pname(p)} ({v}) {rule}: forward {fwd[ci]:+.2f} vs {nf[:, ci].mean():+.2f}; top pick {x['test']} "
                  f"before z {x['z_before']:+.2f} -> after x{x['hits_after'] / x['exp_after']:.3f} (z {x['z_after']:+.2f})")
        sys.stdout.flush()

        # D
        nd_shift = shifts[:max(2, n_shifts // 2)]
        d_real = scan("D", 0)
        d_null = [fwd_stats(scan("D", s)) for s in nd_shift]
        zb, za, zall, top, fwd = fwd_stats(d_real)
        nf = np.array([x[4] for x in d_null])
        print(f"\nD. whole-number hot / cold ({time.time() - t0:.0f}s): forward real (shifted, as high) | best z all years")
        out["D"] = []
        for ci, (s, rule) in enumerate(wn.COLS):
            q = int(np.argmax(zall[:, ci]))
            print(f"   {s:<4} {rule:<9} forward {fwd[ci]:+.2f} ({nf[:, ci].mean():+.2f}, {int((nf[:, ci] >= fwd[ci]).sum())}/{len(nd_shift)}) | "
                  f"best {zall[q, ci]:+.2f} [{names[q]}]")
            out["D"].append({"strategy": s, "rule": rule, "forward": float(fwd[ci]), "null_forward": nf[:, ci].tolist(),
                             "best_z": float(zall[q, ci]), "best_test": names[q]})
    json.dump(out, open(os.path.join(am.ROOT, "analysis", out_name), "w"), indent=1)
    print(f"done in {time.time() - t0:.0f}s")
    return out


def main():
    n_shifts = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    wn.setup()
    codes, labels = nav_codes(r.G["D"].dates)
    rperm.setup()
    for D in (r.G["D"], rperm.G["D"]):
        inject(D, codes, labels)
    D = r.G["D"]
    same = len(set(zip(D.codes["moon_navamsa"], codes["moon_navamsa"]))) == 12
    print(f"check: moon_navamsa from positions matches the almanac's moon_navamsa: {same}")
    other = [f for f in r.FACT if f != "moon_navamsa"]
    tests = [(f,) for f in NAVF] + list(itertools.combinations(NAVF, 2)) + [(a, b) for a in NAVF for b in other]
    run_suite(tests, n_shifts, "navamsa_family_results.json")


if __name__ == "__main__":
    main()
