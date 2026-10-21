#!/usr/bin/env python3
"""Score the ranked leads on given draw dates. Each lead's picks are rebuilt
for every date from the results before that date only, then scored as
Straight and i-Box (approximate i-Box payout = Big prize / arrangements).

Run from the repo root:  python3 analysis/score_leads.py 2026-10-17 2026-10-18 2026-10-21
"""

import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import navamsa_family as nf  # noqa: E402
import recurrence_rankpairs as rp  # noqa: E402
import recurrence_s12 as r  # noqa: E402
import score_live as sl  # noqa: E402
import update_picks as up  # noqa: E402

LEADS = [
    ("1 Karana x Day pillar, S1 (b), i-Box", ("karana", "day_pillar"), "S1", "b"),
    ("2 KP Moon number x Year element, 2+9 (b), Straight", ("kp_moon_number", "year_element"), (1, 8), "b"),
    ("3 Tithi x Sun nakshatra, 2+9 (b), Straight", ("tithi", "sun_nakshatra"), (1, 8), "b"),
    ("4 KP Asc number x Year pillar, 5+6 (b), i-Box", ("kp_asc_number", "year_pillar"), (4, 5), "b"),
    ("5 Mercury nakshatra x Venus rashi, S1 (a), Straight", ("mercury_nakshatra", "venus_rashi"), "S1", "a"),
    ("6 Jupiter nakshatra x Mercury combust, S2 (a), i-Box", ("jupiter_nakshatra", "mercury_combust"), "S2", "a"),
    ("8 Mercury navamsa x Venus rashi, S2 (b), Straight", ("mercury_navamsa", "venus_rashi"), "S2", "b"),
]


def perms(n):
    return math.factorial(4) // math.prod(math.factorial(n.count(d)) for d in set(n))


def picks(t, test, kind, v):
    G = r.G
    cells = r.cells_of(test)
    e = np.flatnonzero((cells == cells[t]) & (np.arange(G["nd"]) < t))
    if len(e) == 0:
        return None
    C = G["dday"][e if v == "a" else e[-1:]].sum(0, keepdims=True)
    if kind == "S1":
        P = r.picks(C, True)
    elif kind == "S2":
        P = r.picks(C, False)
    else:
        P = rp.pair_picks(np.argsort(-C, axis=2, kind="stable"), kind)
    return [f"{n:04d}" for n in P[0]]


def score(byop, win):
    s, b, sp, bp = [], [], 0, 0.0
    for op, nums in byop.items():
        for x in nums:
            if x in win[op]:
                s.append(f"{x} {op} {win[op][x]}")
                sp += sl.BIG[win[op][x]]
            for m, p in win[op].items():
                if sorted(m) == sorted(x):
                    b.append(f"{x}->{m} {op} {p}")
                    bp += sl.BIG[p] / perms(x)
    return s, sp, b, bp


def main():
    r.setup()
    D = r.G["D"]
    up.D = D
    codes, labels = nf.nav_codes(D.dates)
    nf.inject(D, codes, labels)
    rows, _ = sl.load()
    tot = {}
    for d in sys.argv[1:]:
        t = D.dates.index(d)
        win = {op: {x["4d_number"]: x["prize"] for x in rows[op] if x["date"] == d} for op in sl.OPS}
        sets = {}
        for name, test, kind, v in LEADS:
            p = picks(t, test, kind, v)
            sets[name] = {op: p for op in sl.OPS} if p else None
        mars, _ = up.picks_for(d, d)
        for s in ("S2", "S1"):
            sets[f"7 {s} Mars triple, Straight"] = {op: [f"{n:04d}" for n in v]
                                                    for op, v in mars[f"{s}_marsnak_marsrashi_mercombust"].items()}
        sets["9 Cold number"] = sl.cold_numbers(rows, d)
        print(f"\n=== {d} ===")
        for name, byop in sets.items():
            T = tot.setdefault(name, [0, 0, 0, 0.0, 0])
            if byop is None:
                print(f"{name}|no earlier same-value day, no picks")
                continue
            s, sp, b, bp = score(byop, win)
            k = sum(len(v) for v in byop.values())
            T[0] += len(s); T[1] += sp; T[2] += len(b); T[3] += bp; T[4] += k
            print(f"{name}|{k}|straight {len(s)} {'; '.join(s) or '-'} RM{sp}|i-Box {len(b)} {'; '.join(b) or '-'} ~RM{bp:.2f}")
    print("\n=== totals ===")
    for name, (s, sp, b, bp, k) in tot.items():
        print(f"{name}|staked RM{k}|straight {s} hits RM{sp}|i-Box {b} matches ~RM{bp:.2f}")


if __name__ == "__main__":
    main()
