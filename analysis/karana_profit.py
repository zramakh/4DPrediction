#!/usr/bin/env python3
"""Can Karana x Day pillar (S1 from the previous same-value day, i-Box) be made
profitable? Breaks its i-Box matches down by operator, by which of the 16 picks
(grid position: which of the 2 top digits in each position), by number type
(arrangements 24 / 12 / 6 / 4) and by prize tier, before 2012 and 2012-2026,
and the money returned as Big i-Box, Small i-Box and Big Straight.

Big i-Box pays the Big prize / arrangements; Small i-Box pays the Small prize
(1st 3500, 2nd 2000, 3rd 1000, no Special / Consolation) / arrangements.
Chance: each winner falls in a pick's box with that year's digit mix probability.
Any narrower rule (operators, grid positions, number types) is chosen on draws
before 2012 and then scored on 2012-2026.

Run from the repo root:  python3 analysis/karana_profit.py
"""

import itertools
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am  # noqa: E402
import recurrence_s12 as r  # noqa: E402

BIG = {"1st": 2500, "2nd": 1000, "3rd": 500, "Special": 180, "Consolation": 60}
SMALL = {"1st": 3500, "2nd": 2000, "3rd": 1000, "Special": 0, "Consolation": 0}
TIERS = list(BIG)
TEST = ("karana", "day_pillar")
SPLIT = 2012
LAST5 = ["2026-10-11", "2026-10-14", "2026-10-17", "2026-10-18", "2026-10-21"]


def perms_of(n):
    s = f"{n:04d}"
    return math.factorial(4) // math.prod(math.factorial(s.count(c)) for c in set(s))


def main():
    r.setup()
    G = r.G
    D = G["D"]
    yr = np.array([int(d[:4]) for d in D.dates])
    _, _, _, _, draws, _ = am.load()
    box, Pbox, yix = G["box"], G["Pbox"], G["yix"]
    cells = r.cells_of(TEST)
    # picks for every draw day from the previous same-value day
    rec = []          # per (day, op, grid): obs per tier, expected per tier
    last = {}
    for t in range(G["nd"]):
        c = cells[t]
        if c in last:
            C = G["dday"][last[c]][None]
            P = r.picks(C, True)[0]                                       # (16,), grid order = BITS
            for o in range(3):
                key = (t, o)
                if key not in draws:
                    continue
                win = draws[key][1]
                ntier = {k: sum(1 for p, _ in win if p == k) for k in TIERS}
                for gi, n in enumerate(P):
                    b = box[n]
                    obs = {k: 0 for k in TIERS}
                    for p, w in win:
                        if box[w] == b:
                            obs[str(p)] += 1
                    pb = Pbox[yix[t], b]
                    exp = {k: ntier[k] * pb for k in TIERS}
                    rec.append((t, o, gi, int(n), perms_of(int(n)), obs, exp))
        last[c] = t
    print(f"{len(rec)} pick-operator-draw records")

    def summarize(sel, label):
        o = sum(sum(x[5].values()) for x in sel)
        e = sum(sum(x[6].values()) for x in sel)
        big = sum(sum(x[5][k] * BIG[k] for k in TIERS) / x[4] for x in sel)
        small = sum(sum(x[5][k] * SMALL[k] for k in TIERS) / x[4] for x in sel)
        ebig = sum(sum(x[6][k] * BIG[k] for k in TIERS) / x[4] for x in sel)
        stake = len(sel)
        return {"label": label, "bets": stake, "matches": o, "expected": e, "ratio": o / e if e else 0,
                "big_return": big / stake if stake else 0, "small_return": small / stake if stake else 0,
                "chance_big_return": ebig / stake if stake else 0}

    def show(rows):
        for s in rows:
            print(f"   {s['label']:<34} bets {s['bets']:>6} | matches {s['matches']:>5} vs {s['expected']:>7.1f} (x{s['ratio']:.3f}) | "
                  f"Big i-Box return {100 * s['big_return']:5.1f}% (chance {100 * s['chance_big_return']:.1f}%) | "
                  f"Small i-Box {100 * s['small_return']:5.1f}%")

    early = [x for x in rec if yr[x[0]] < SPLIT]
    late = [x for x in rec if yr[x[0]] >= SPLIT]
    for name, part in (("before 2012", early), ("2012-2026", late)):
        print(f"\n== {name} ==")
        show([summarize(part, "all 16 picks, 3 operators")])
        print("  by operator:")
        show([summarize([x for x in part if x[1] == o], am.OPS[o]) for o in range(3)])
        print("  by number type (arrangements):")
        show([summarize([x for x in part if x[4] == k], f"{k} arrangements") for k in (24, 12, 6, 4, 1)])
        print("  by prize tier (matches vs chance):")
        for k in TIERS:
            o = sum(x[5][k] for x in part)
            e = sum(x[6][k] for x in part)
            print(f"   {k:<12} {o:>5} vs {e:>7.1f} (x{o / e:.3f})")
    print("\n== by grid position (bit pattern = which of the 2 hottest digits per position; 0 = hottest) ==")
    for gi in range(16):
        b = "".join(str(v) for v in r.BITS[gi])
        se = summarize([x for x in early if x[2] == gi], f"grid {b}")
        sl_ = summarize([x for x in late if x[2] == gi], f"grid {b}")
        print(f"   {b}: before x{se['ratio']:.3f} ({se['matches']}) | after x{sl_['ratio']:.3f} ({sl_['matches']}), "
              f"Big i-Box return after {100 * sl_['big_return']:.1f}%")

    # rules chosen before 2012
    print("\n== narrower rules chosen on draws before 2012, scored on 2012-2026 ==")
    ops_good = [o for o in range(3) if summarize([x for x in early if x[1] == o], "")["ratio"] > 1]
    grid_good = [g for g in range(16) if summarize([x for x in early if x[2] == g], "")["ratio"] > 1]
    type_good = [k for k in (24, 12, 6, 4) if summarize([x for x in early if x[4] == k], "")["ratio"] > 1]
    print(f"   operators above chance before 2012: {[am.OPS[o] for o in ops_good]}; grid positions: {len(grid_good)} of 16; "
          f"number types: {type_good}")
    rules = {
        "operators chosen before 2012": lambda x: x[1] in ops_good,
        "grid positions chosen before 2012": lambda x: x[2] in grid_good,
        "number types chosen before 2012": lambda x: x[4] in type_good,
        "all three filters": lambda x: x[1] in ops_good and x[2] in grid_good and x[4] in type_good,
    }
    show([summarize([x for x in late if f(x)], k) for k, f in rules.items()])
    print("\n== last 5 draws: every i-Box match ==")
    for x in rec:
        d = D.dates[x[0]]
        if d in LAST5 and sum(x[5].values()):
            b = "".join(str(v) for v in r.BITS[x[2]])
            tiers = [k for k in TIERS for _ in range(x[5][k])]
            print(f"   {d} {am.OPS[x[1]]:<12} pick {x[3]:04d} (grid {b}, {x[4]} arrangements): {', '.join(tiers)}")
    l5 = [x for x in rec if D.dates[x[0]] in LAST5]
    show([summarize(l5, "last 5 draws, all"), *[summarize([x for x in l5 if x[1] == o], f"last 5, {am.OPS[o]}") for o in range(3)]])


if __name__ == "__main__":
    main()
