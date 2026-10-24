#!/usr/bin/env python3
"""One command for every pick set logged in forward_log.csv, for any draw date
(including a future one), from the results before a cutoff.

  python3 analysis/predict_all.py DATE                 print all pick sets for DATE
  python3 analysis/predict_all.py DATE --log           also append them to forward_log.csv
  python3 analysis/predict_all.py --check DATE         rebuild a date already logged and compare
                                                       each set with the log (same numbers)

Variants (names as in forward_log.csv):
  lead1 ... lead8                      ranked leads (score_leads.LEADS): picks from earlier draw
                                       days with the same parameter values, results before DATE
  recur_* / S1_ / S2_marsnak_...       update_picks.picks_for; frozen = results before 2026-10-17,
                                       _upd = results before DATE
  single_<param>/<kind>                the six selected single-parameter formulas (astro_model Counts)
  positional_hot / cold_noparam        S1 / S2 grid from all earlier results of each operator
                                       (both: frozen = results before 2026-10-17, _upd = before DATE)
  manual_v2                            manual_formula.json (fixed tables, top 5)
  vedic / chinese / both               astro_model.py frozen formulas (results before 2026-10-11; _upd before DATE)
  ml_*                                 ml_model.py (needs lightgbm; separate process)
The old "manual" set (before the formula fix of 17 Oct) is not rebuilt.
Same parameter values, same data, same code as the analysis scripts: do not
re-implement these elsewhere.
"""

import argparse
import csv
import datetime as dt
import itertools
import json
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am  # noqa: E402
import ephemeris as eph  # noqa: E402
import manual_formula as mf  # noqa: E402
import navamsa_family as nf  # noqa: E402
import recurrence_rankpairs as rp  # noqa: E402
import recurrence_s12 as r  # noqa: E402
import score_leads as sl  # noqa: E402
import update_picks as up  # noqa: E402
import vedic  # noqa: E402

ROOT = am.ROOT
LOG = os.path.join(ROOT, "analysis", "forward_log.csv")
FROZEN = "2026-10-17"
ASTRO_FROZEN = "2026-10-11"          # vedic / chinese / both were logged before the 11 and 14 Oct results were added
SIX = [("jupiter_nakshatra", "num_op"), ("yellow_black_path", "num_op"), ("month_branch", "dig_op"),
       ("saturn_combust", "num_op"), ("mercury_nakshatra", "box"), ("mars_retrograde", "box_op")]
LEAD_TAG = {"S1": "S1", "S2": "S2", (1, 8): "2+9", (4, 5): "5+6"}


def lead_name(rank, test, kind, v):
    return f"lead{rank}_{'_'.join(test)}_{LEAD_TAG[kind]}{v}"


def leads(date):
    """{variant: {"All": [numbers]}} for the ranked leads, from draw days before date."""
    G, D = r.G, r.G["D"]
    jd = eph.julian_day(dt.datetime.combine(dt.date.fromisoformat(date), dt.time(11)))
    before = np.array([d < date for d in D.dates])
    out, info = {}, {}
    for name, test, kind, v in sl.LEADS:
        m = before.copy()
        vals = []
        for f in test:
            if f == "mercury_navamsa":
                code = int(vedic.sidereal("Mercury", jd) * 9 / 30) % 12
                lab = nf.RASHIS[code]
            else:
                _, c2, ctx = am.date_codes(date, D.codes, D.labels, [f])
                code, lab = int(c2[f][-1]), ctx[f]
            m &= D.codes[f] == code
            vals.append(f"{f}={lab}")
        e = np.flatnonzero(m)
        key = lead_name(name.split()[0], test, kind, v)
        if len(e) == 0:
            info[key] = ", ".join(vals) + "; no earlier draw day with these values"
            continue
        C = G["dday"][e if v == "a" else e[-1:]].sum(0, keepdims=True)
        if kind in ("S1", "S2"):
            P = r.picks(C, kind == "S1")
        else:
            P = rp.pair_picks(np.argsort(-C, axis=2, kind="stable"), kind)
        out[key] = {"All": sorted(int(n) for n in P[0])}
        info[key] = ", ".join(vals) + "; " + (f"{len(e)} earlier days" if v == "a" else f"previous day {D.dates[e[-1]]}")
    return out, info


def singles(date, cutoff):
    data, codes, labels, rows, draws, _ = am.load()
    D = r.G["D"]
    ok = np.array([d < cutoff for d in D.dates])[rows["date"]]
    facs = sorted({f for f, _ in SIX})
    ix, codes2, ctx = am.date_codes(date, codes, labels, facs)
    c = am.Counts(facs, codes2)
    c.add(rows["date"][ok], rows["op_ix"][ok], rows["num"][ok])
    out = {}
    for f, kind in SIX:
        out[f"single_{f}/{kind}"] = {op: [int(n) for n in np.argsort(-(c.term(f, int(codes2[f][ix]), kind, o) + np.arange(10000) * 1e-12))[:10]]
                                     for o, op in enumerate(am.OPS)}
    return out


def positional(cutoff):
    D = r.G["D"]
    ok = np.array([d < cutoff for d in D.dates])[D.rd]
    out = {}
    for strat, sign in (("hot", -1), ("cold", 1)):
        out[f"positional_{strat}_noparam"] = {}
        for o, op in enumerate(am.OPS):
            m = ok & (D.ro == o)
            C = np.stack([np.bincount(am.DIG[D.rn[m], p], minlength=10) for p in range(4)]).astype(float)
            top2 = np.argsort(sign * C, 1)[:, :2]
            out[f"positional_{strat}_noparam"][op] = [int((np.array([top2[p, b] for p, b in enumerate(bits)]) * r.POW).sum())
                                                      for bits in itertools.product((0, 1), repeat=4)]
    return out


def manual_v2(date):
    J = json.load(open(os.path.join(ROOT, "analysis", "manual_formula.json")))
    row = next((x for x in J["calendar"] if x["date"] == date), None)
    if row is None:
        return {}
    P = np.zeros((4, 10))
    for f in J["weights"]:
        P += np.array(J["tables"][f][row[f]])
    return {"manual_v2": {op: [int(n) for n in mf.top_numbers(P, 5)] for op in am.OPS}}


def build(date, cutoff=None):
    """All in-process pick sets for date: {variant: {operator or "All": [numbers]}}, plus notes."""
    cutoff = cutoff or date
    r.setup()
    up.D = r.G["D"]
    nf.inject(r.G["D"], *nf.nav_codes(r.G["D"].dates))
    out, info = leads(date)
    for cut, suffix in ((FROZEN, ""), (cutoff, "_upd")):
        p, inf = up.picks_for(date, min(cut, cutoff))
        for k, v in p.items():
            out[k + suffix] = {op: [int(n) for n in nums] for op, nums in v.items()}
            info[k + suffix] = inf[k] + f" (results before {min(cut, cutoff)})"
    for cut, suffix in ((min(FROZEN, cutoff), ""), (cutoff, "_upd")):
        for k, v in {**singles(date, cut), **positional(cut)}.items():
            out[k + suffix] = v
    out.update(manual_v2(date))
    for cut, suffix in ((min(FROZEN, cutoff), ""), (cutoff, "_upd")):
        cut = min(ASTRO_FROZEN, cutoff) if suffix == "" else cut
        for k, v in am.picks_for(date, list(am.VARIANTS), 10, cut).items():
            out[k + suffix] = v
    return out, info


def logged(date):
    sets = {}
    for row in csv.DictReader(open(LOG)):
        if row["draw_date"] == date:
            sets.setdefault(row["variant"], {}).setdefault(row["operator"], set()).add(int(row["4d_number"]))
    return sets


def check(date):
    out, _ = build(date)
    log = logged(date)
    bad = 0
    for k, v in sorted(out.items()):
        if k not in log:
            print(f"   {k:<48} not logged for {date}")
            continue
        same = all(set(nums) == log[k].get(op, set()) for op, nums in v.items())
        bad += not same
        print(f"   {k:<48} {'MATCH' if same else 'DIFFERENT'}")
        if not same:
            for op, nums in v.items():
                if set(nums) != log[k].get(op, set()):
                    print(f"      {op}: rebuilt {' '.join(f'{n:04d}' for n in sorted(nums))}")
                    print(f"      {'':<{len(op)}}  logged  {' '.join(f'{n:04d}' for n in sorted(log[k].get(op, [])))}")
    others = sorted(set(log) - set(out))
    print(f"   logged but rebuilt by other scripts (ml_model.py) or not reproducible: {', '.join(others)}")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("date", nargs="?")
    ap.add_argument("--cutoff")
    ap.add_argument("--log", action="store_true")
    ap.add_argument("--check")
    a = ap.parse_args()
    if a.check:
        sys.exit(1 if check(a.check) else 0)
    out, info = build(a.date, a.cutoff)
    print(f"Pick sets for {a.date} (results before {a.cutoff or a.date}; frozen sets before {FROZEN})")
    for k, v in out.items():
        print(f"\n{k}" + (f"  [{info[k]}]" if k in info else ""))
        for op, nums in v.items():
            print(f"   {op:<12} {' '.join(f'{n:04d}' for n in nums)}")
    for k in info:
        if k not in out:
            print(f"\n{k}  [{info[k]}]")
    if a.log:
        now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
        with open(LOG, "a", newline="") as fh:
            w = csv.writer(fh)
            for k, v in out.items():
                for op, nums in v.items():
                    for i, n in enumerate(nums, 1):
                        w.writerow([now, a.date, k, op, i, f"{n:04d}"])
        print(f"\nlogged {len(out)} sets at {now} UTC")
    print("\nAlso run:  python3 analysis/ml_model.py predict --date DATE --before DATE   (ml_*; needs lightgbm)")


if __name__ == "__main__":
    main()
