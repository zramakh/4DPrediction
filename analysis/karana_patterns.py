#!/usr/bin/env python3
"""A lead's picks by i-Box pattern (default: Karana x Day pillar, S1 from the
previous same-value day). Pattern of the pick: ABCD (24 arrangements), AABC (12), AABB two pairs (6), AAAB triplet
(4), AAAA (1). Each pick is bet on all 3 operators; evidence is counted by
distinct winning numbers per draw and operator (one winner matching several
same-digit picks counts once), money by bet (every matching pick pays).
Big i-Box pays the Big prize / arrangements; Small i-Box the Small prize
(1st 3500, 2nd 2000, 3rd 1000) / arrangements.

Run from the repo root:  python3 analysis/karana_patterns.py [param1 param2 picks version]
   e.g. python3 analysis/karana_patterns.py mars_nakshatra kp_asc_number 5+6 b
"""

import math
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am  # noqa: E402
import recurrence_rankpairs as rp  # noqa: E402
import recurrence_s12 as r  # noqa: E402

BIG = {"1st": 2500, "2nd": 1000, "3rd": 500, "Special": 180, "Consolation": 60}
SMALL = {"1st": 3500, "2nd": 2000, "3rd": 1000, "Special": 0, "Consolation": 0}
PAT = {24: "ABCD", 12: "AABC", 6: "AABB (two pairs)", 4: "AAAB (triplet)", 1: "AAAA"}
LAST5 = ["2026-10-11", "2026-10-14", "2026-10-17", "2026-10-18", "2026-10-21"]


def perms(n):
    s = f"{n:04d}"
    return math.factorial(4) // math.prod(math.factorial(s.count(c)) for c in set(s))


def make_picks(C, kind):
    if kind == "S1":
        return r.picks(C, True)[0]
    if kind == "S2":
        return r.picks(C, False)[0]
    a, b = (int(x) - 1 for x in kind.split("+"))
    return rp.pair_picks(np.argsort(-C, axis=2, kind="stable"), (a, b))[0]


def main():
    args = sys.argv[1:]
    test = tuple(args[:2]) if len(args) >= 2 else ("karana", "day_pillar")
    kind = args[2] if len(args) > 2 else "S1"
    version = args[3] if len(args) > 3 else "b"
    print(f"Lead: {' x '.join(test)}, {kind} ({version})")
    r.setup()
    G = r.G
    D = G["D"]
    yr = np.array([int(d[:4]) for d in D.dates])
    _, _, _, _, draws, _ = am.load()
    cells = r.cells_of(test)
    cum = {}
    recs = []                                       # (t, op, pattern, n_bets, distinct, exp_distinct, big, small, top3, details)
    last = {}
    for t in range(G["nd"]):
        c = cells[t]
        if c in last:
            C = (cum[c] if version == "a" else G["dday"][last[c]])[None]
            P = [int(n) for n in make_picks(C, kind)]
            for o in range(3):
                if (t, o) not in draws:
                    continue
                win = draws[(t, o)][1]
                nw = len(win)
                for k in PAT:
                    picks = [n for n in P if perms(n) == k]
                    if not picks:
                        continue
                    boxes = defaultdict(int)
                    for n in picks:
                        boxes[G["box"][n]] += 1
                    distinct = exp = big = small = top3 = 0.0
                    det = []
                    for b, cnt in boxes.items():
                        exp += nw * G["Pbox"][G["yix"][t], b]
                        for p, w in win:
                            if G["box"][w] == b:
                                p = str(p)
                                distinct += 1
                                big += cnt * BIG[p] / k
                                small += cnt * SMALL[p] / k
                                top3 += p in ("1st", "2nd", "3rd")
                                det.append(f"{w:04d} {p}")
                    recs.append((t, o, k, len(picks), distinct, exp, big, small, top3, det))
        last[c] = t
        cum[c] = cum.get(c, 0) + G["dday"][t]

    def summ(sel):
        bets = sum(x[3] for x in sel)
        o = sum(x[4] for x in sel)
        e = sum(x[5] for x in sel)
        return bets, o, e, sum(x[6] for x in sel), sum(x[7] for x in sel), int(sum(x[8] for x in sel))

    def line(label, sel):
        bets, o, e, big, small, t3 = summ(sel)
        if not bets:
            return f"   {label:<26} no bets"
        z = (o - e) / math.sqrt(e) if e else 0
        return (f"   {label:<26} bets {bets:>6} | distinct winners {o:>4.0f} vs {e:>6.1f} (x{o / e if e else 0:.2f}, z {z:+.2f}) | "
                f"top-3 {t3:>3} | Big i-Box {100 * big / bets:5.1f}% | Small i-Box {100 * small / bets:5.1f}%")

    for name, cond in (("before 2012", lambda x: yr[x[0]] < 2012), ("2012-2026", lambda x: yr[x[0]] >= 2012)):
        print(f"\n== {name}: by pattern (all 3 operators) ==")
        for k, nm in PAT.items():
            print(line(nm, [x for x in recs if cond(x) and x[2] == k]))
    for k in (6, 4):
        print(f"\n== {PAT[k]} by operator ==")
        for o in range(3):
            for name, cond in (("before 2012", lambda x: yr[x[0]] < 2012), ("2012-2026", lambda x: yr[x[0]] >= 2012)):
                print(line(f"{am.OPS[o]} {name}", [x for x in recs if cond(x) and x[2] == k and x[1] == o]))
        print(f"\n== {PAT[k]} year by year (2012-2026; distinct winners / expected; top-3 wins) ==")
        rowstr = []
        for Y in range(2012, 2027):
            bets, o, e, big, small, t3 = summ([x for x in recs if yr[x[0]] == Y and x[2] == k])
            rowstr.append(f"{Y}: {o:.0f}/{e:.1f}" + (f" ({t3} top-3)" if t3 else ""))
        print("   " + " | ".join(rowstr))
        good = sum(1 for Y in range(2012, 2027) if summ([x for x in recs if yr[x[0]] == Y and x[2] == k])[1] >
                   summ([x for x in recs if yr[x[0]] == Y and x[2] == k])[2])
        print(f"   years above chance: {good} of 15")
        print("   top-3 i-Box wins 2012-2026:")
        for x in recs:
            if yr[x[0]] >= 2012 and x[2] == k and x[8]:
                print(f"      {D.dates[x[0]]} {am.OPS[x[1]]}: {', '.join(d for d in x[9] if d.split()[1] in ('1st', '2nd', '3rd'))}")
    print("\n== last 5 draws ==")
    for d in LAST5:
        t = D.dates.index(d)
        c = cells[t]
        e = np.flatnonzero((cells == c) & (np.arange(G["nd"]) < t))
        if len(e) == 0:
            print(f"   {d}: no earlier same-value day")
            continue
        P = [int(n) for n in make_picks(G["dday"][e if version == "a" else e[-1:]].sum(0, keepdims=True), kind)]
        by = {PAT[k]: [f"{n:04d}" for n in P if perms(n) == k] for k in PAT}
        hits = [(PAT[x[2]], am.OPS[x[1]], x[9]) for x in recs if x[0] == t and x[9]]
        print(f"   {d}: " + "; ".join(f"{k} {len(v)}" + (f" {v}" if k.startswith(("AABB", "AAAB", "AAAA")) and v else "") for k, v in by.items() if v))
        for h in hits:
            print(f"      match: {h[0]} {h[1]} {h[2]}")
    for k, nm in PAT.items():
        print(line(f"last 5, {nm}", [x for x in recs if D.dates[x[0]] in LAST5 and x[2] == k]))


if __name__ == "__main__":
    main()
