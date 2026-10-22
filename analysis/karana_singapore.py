#!/usr/bin/env python3
"""Test 1 for the lead Karana x Day pillar (S1 from the previous same-value day,
i-Box) on a game it was never fitted to: Singapore Pools 4D (23 winners per
draw: 3 top prizes, 10 Starters, 10 Consolations; 1986-05-31 to 2026-07-12,
data/singapore4d.csv from github.com/foooooooooooooooooooooooooootw/Singapore-Pools-Dataset).

Same method as the Malaysian lead: parameters at 19:00 local time (Singapore
draws at 18:30; Karana at 18:30 shown as well), chance from that year's digit
mix per position. Also: the lead against 200 shifted calendars, its rank among
all 3,081 single / pair tests on Singapore, and Malaysian top-20 leads chosen
before 2012 scored on Singapore.

Run from the repo root:  python3 analysis/karana_singapore.py
"""

import csv
import datetime as dt
import itertools
import json
import math
import multiprocessing as mp
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import almanac  # noqa: E402
import astro_model as am  # noqa: E402
import karana_family as kf  # noqa: E402
import recurrence_s12 as r  # noqa: E402
import vedic  # noqa: E402

LEAD = ("karana", "day_pillar")
FACT = r.FACT
DIG, POW = r.DIG, r.POW


class SG:
    def __init__(self):
        win = {}
        for row in csv.DictReader(open(os.path.join(am.ROOT, "data", "singapore4d.csv"))):
            win.setdefault(row["date"].replace("/", "-"), set()).add(int(row["number"]))
        self.dates = sorted(win)
        self.win = [sorted(win[d]) for d in self.dates]
        vals = {f: [] for f in FACT}
        k1830 = []
        for d in self.dates:
            day = dt.date.fromisoformat(d)
            f = almanac.factors(d)
            f["weekday"] = day.weekday()
            for x in FACT:
                vals[x].append(str(f[x]))
            k1830.append(vedic.panchanga(dt.datetime.combine(day, dt.time(10, 30)), day)["karana"])
        vals["karana_1830"] = k1830
        self.codes, self.labels = {}, {}
        for x, v in vals.items():
            lab = sorted(set(v))
            self.labels[x] = lab
            self.codes[x] = np.array([lab.index(s) for s in v])


def setup():
    D = SG()
    nd = len(D.dates)
    wd = np.concatenate([[t] * len(w) for t, w in enumerate(D.win)])
    wn = np.concatenate(D.win)
    nwin = np.bincount(wd, minlength=nd).astype(float)
    W = np.zeros((nd, 10000), bool)
    W[wd, wn] = True
    dday = np.zeros((nd, 4, 10))
    for p in range(4):
        np.add.at(dday, (wd, p, DIG[wn, p]), 1)
    num = np.arange(10000)
    rev = (DIG[:, ::-1] * POW).sum(1)
    box = np.unique(np.sort(DIG, axis=1) @ POW, return_inverse=True)[1]
    nbox = int(box.max()) + 1
    Cb = np.zeros((nd, nbox), np.float32)
    np.add.at(Cb, (wd, box[wn]), 1)
    yr = np.array([int(d[:4]) for d in D.dates])
    yix = yr - yr.min()
    q = np.zeros((yix.max() + 1, 4, 10))
    np.add.at(q, yix, dday)
    q /= q.sum(2, keepdims=True)
    Py = q[:, 0, DIG[:, 0]] * q[:, 1, DIG[:, 1]] * q[:, 2, DIG[:, 2]] * q[:, 3, DIG[:, 3]]
    Pbox = np.stack([np.bincount(box, weights=Py[y], minlength=nbox) for y in range(len(Py))])
    r.G.clear()
    r.G.update(D=D, nd=nd, nwin=nwin, W=W, dday=dday, rev=rev, pal=rev == num, box=box, Cb=Cb, yix=yix, Py=Py,
               Pbox=Pbox, yr=yr)


def task(args):
    return kf.summary(*args)


def line(name, s):
    zb, za, g, ra = s
    return f"   {name:<46} z before 2012 {zb:+.2f} | z 2012-2026 {za:+.2f} (x{ra:.3f}) | {g}/15 good years"


def main():
    # Malaysian results first (for the top-20 list chosen before 2012)
    r.setup()
    r.G["yr"] = np.array([int(d[:4]) for d in r.G["D"].dates])
    tests = [(f,) for f in FACT] + list(itertools.combinations(FACT, 2))
    with mp.get_context("fork").Pool(4) as pool:
        my = np.array(pool.map(task, [(t, 0) for t in tests], chunksize=16))
    my_top = np.argsort(-my[:, 0])[:20]
    setup()
    G = r.G
    print(f"Singapore 4D: {G['nd']} draws {G['D'].dates[0]} to {G['D'].dates[-1]}, {int(G['nwin'].sum())} winners")
    out = {}
    lead = kf.summary(LEAD)
    print("\nLead on Singapore (S1 from the previous same-value day, i-Box):")
    print(line("Karana x Day pillar (19:00)", lead))
    print(line("Karana at 18:30 (draw time) x Day pillar", kf.summary(("karana_1830", "day_pillar"))))
    print(line("Karana alone", kf.summary(("karana",))))
    print(line("Day pillar alone", kf.summary(("day_pillar",))))
    rng = np.random.default_rng(11)
    shifts = [int(s) for s in rng.integers(170, G["nd"] - 170, 200)]
    with mp.get_context("fork").Pool(4) as pool:
        null = np.array(pool.map(task, [(LEAD, s) for s in shifts], chunksize=8))
        sg = np.array(pool.map(task, [(t, 0) for t in tests], chunksize=16))
    zall_lead = None
    print(f"\n200 shifted calendars: z 2012-2026 as high {int((null[:, 1] >= lead[1]).sum())}/200; "
          f"z before as high {int((null[:, 0] >= lead[0]).sum())}/200; good years as many {int((null[:, 2] >= lead[2]).sum())}/200")
    li = tests.index(LEAD)
    za = sg[:, 1]
    print(f"Rank of the lead among all {len(tests)} tests on Singapore (z 2012-2026): {int((za > za[li]).sum()) + 1}; "
          f"mean z 2012-2026 of all tests {za.mean():+.2f}")
    print("\nMalaysian top 20 (chosen on Malaysian draws before 2012) scored on Singapore 2012-2026:")
    rows = []
    for q in my_top:
        rows.append({"test": " x ".join(tests[q]), "my_z_before": float(my[q, 0]), "sg_z_before": float(sg[q, 0]),
                     "sg_z_after": float(sg[q, 1]), "sg_good_years": int(sg[q, 2])})
    for x in rows[:10]:
        print(f"   {x['test']:<44} MY before {x['my_z_before']:+.2f} -> SG before {x['sg_z_before']:+.2f}, after {x['sg_z_after']:+.2f}")
    mz = np.array([x["sg_z_after"] for x in rows]).mean()
    print(f"   mean SG z 2012-2026 of the 20: {mz:+.2f} (all tests {za.mean():+.2f})")
    best = np.argsort(-sg[:, 0])[:5]
    print("\nSingapore's own top 5 chosen before 2012 -> 2012-2026: " + "; ".join(
        f"{' x '.join(tests[q])} {sg[q, 0]:+.2f} -> {sg[q, 1]:+.2f}" for q in best))
    out = {"lead": lead, "null": null.tolist(), "rank": int((za > za[li]).sum()) + 1, "my_top20_on_sg": rows,
           "all_mean_z_after": float(za.mean())}
    json.dump(out, open(os.path.join(am.ROOT, "analysis", "karana_singapore_results.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
