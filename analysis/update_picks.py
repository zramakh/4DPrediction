#!/usr/bin/env python3
"""Rebuild the leads' picks for a draw date from all results before a cutoff,
so each new draw's results feed into the next draw's picks.

Leads:
  recur_S1a_mercurynak_venusrashi   S1 grid from all earlier days with the same
                                    Mercury nakshatra x Venus rashi (all operators)
  recur_S1b_karana_daypillar_ibox   S1 grid from the previous day with the same
                                    Karana x Day pillar (all operators)
  S1/S2_marsnak_marsrashi_mercombust per operator, S1 / S2 grid from all earlier
                                    days with the same Mars nakshatra x Mars rashi
                                    x Mercury combust (as in s12_combos.py)
The cold number and 1024 are handled in score_live.py.

Run from the repo root:
  python3 analysis/update_picks.py DRAW_DATE [CUTOFF]     (CUTOFF = DRAW_DATE by default;
                                                           only results dated before it are used)
  add --log to append the picks to forward_log.csv
"""

import datetime as dt
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am  # noqa: E402
import digit_models as dm  # noqa: E402

DIG = am.DIG
POW = np.array([1000, 100, 10, 1])
BITS = np.array([[(k >> (3 - p)) & 1 for p in range(4)] for k in range(16)])
D = None


def grid(top2):
    return sorted(int((top2[np.arange(4), BITS[k]] * POW).sum()) for k in range(16))


def same_days(date, factors, cutoff):
    ix, c2, ctx = am.date_codes(date, D.codes, D.labels, factors)
    m = np.ones(len(D.dates), bool)
    for f in factors:
        m &= D.codes[f] == c2[f][-1]
    m &= np.array([d < cutoff for d in D.dates])
    return np.flatnonzero(m), {f: ctx[f] for f in factors}


def counts(day_idx, op=None):
    sel = np.isin(D.rd, day_idx) & ((D.ro == op) if op is not None else True)
    if op is None:                                    # each number once per date over all operators
        key = np.unique(D.rd[sel].astype(np.int64) * 10000 + D.rn[sel])
        nums = key % 10000
    else:
        nums = D.rn[sel]
    C = np.zeros((4, 10))
    for p in range(4):
        C[p] = np.bincount(DIG[nums, p], minlength=10)
    return C


def picks_for(date, cutoff):
    out, info = {}, {}
    idx, v = same_days(date, ["mercury_nakshatra", "venus_rashi"], cutoff)
    C = counts(idx)
    out["recur_S1a_mercurynak_venusrashi"] = {"All": grid(np.argsort(-C, axis=1, kind="stable")[:, :2])}
    info["recur_S1a_mercurynak_venusrashi"] = f"{v}, {len(idx)} earlier days"
    idx, v = same_days(date, ["karana", "day_pillar"], cutoff)
    C = counts(idx[-1:])
    out["recur_S1b_karana_daypillar_ibox"] = {"All": grid(np.argsort(-C, axis=1, kind="stable")[:, :2])}
    info["recur_S1b_karana_daypillar_ibox"] = f"{v}, previous day {D.dates[idx[-1]]}"
    trip = ["mars_nakshatra", "mars_rashi", "mercury_combust"]
    idx, v = same_days(date, trip, cutoff)
    before = np.flatnonzero(np.array([d < cutoff for d in D.dates]))
    for s, sign in (("S1", -1), ("S2", 1)):
        name = f"{s}_marsnak_marsrashi_mercombust"
        out[name] = {}
        for o, op in enumerate(am.OPS):
            overall = counts(before, o)
            overall /= overall.sum(1, keepdims=True)
            C = counts(idx, o) + 1e-6 * overall
            out[name][op] = grid(np.argsort(sign * C, axis=1, kind="stable")[:, :2])
        info[name] = f"{v}, {len(idx)} earlier days"
    return out, info


def main():
    global D
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    date = args[0]
    cutoff = args[1] if len(args) > 1 else date
    D = dm.Data()
    out, info = picks_for(date, cutoff)
    print(f"Picks for {date} from results before {cutoff}:")
    for name, by_op in out.items():
        print(f"  {name} ({info[name]})")
        for op, nums in by_op.items():
            print(f"     {op:<12} " + " ".join(f"{n:04d}" for n in nums))
    if "--log" in sys.argv:
        now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
        with open(os.path.join(am.ROOT, "analysis", "forward_log.csv"), "a") as fh:
            for name, by_op in out.items():
                for op, nums in by_op.items():
                    for k, n in enumerate(nums, 1):
                        fh.write(f"{now},{date},{name}_upd,{op},{k},{n:04d}\n")
        print("logged to forward_log.csv with variant suffix _upd")


if __name__ == "__main__":
    main()
