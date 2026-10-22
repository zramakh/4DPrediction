#!/usr/bin/env python3
"""Score the most consistent leads (yearly_consistency.py) on given draws.
Pooled leads: 16 numbers on all 3 operators (RM48 per draw), picks from all
operators' earlier results. Operator leads: 16 numbers on that operator only
(RM16 per draw), picks from that operator's earlier results. Scored as Straight
and i-Box (approximate i-Box payout = Big prize / arrangements).

Run from the repo root:  python3 analysis/consistent_leads_live.py pooled|Magnum|"Sports Toto"|"Da Ma Cai" DATE [DATE ...]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am  # noqa: E402
import per_operator as po  # noqa: E402

LEADS = {
    "pooled": [("Karana x Day pillar", ("karana", "day_pillar"), "S1", "b", "i-Box"),
               ("Mars nakshatra x KP Asc number", ("mars_nakshatra", "kp_asc_number"), (4, 5), "b", "i-Box")],
    "Magnum": [("Jupiter retrograde x KP Asc sub lord", ("jupiter_retrograde", "kp_asc_sub_lord"), (3, 6), "b", "Straight"),
               ("Nakshatra lord x Day stem", ("nakshatra_lord", "day_stem"), (1, 8), "b", "Reverse"),
               ("Moon rashi x Day god", ("moon_rashi", "day_god"), (0, 9), "b", "i-Box")],
    "Sports Toto": [("Lunar month x Day element", ("lunar_month", "day_element"), "S2", "b", "i-Box"),
                    ("Mercury rashi x Moon navamsa", ("mercury_rashi", "moon_navamsa"), (2, 7), "b", "i-Box")],
    "Da Ma Cai": [("Ayana x KP Asc star lord", ("ayana", "kp_asc_star_lord"), (0, 9), "a", "Reverse"),
                  ("Ritu x Day stem", ("ritu", "day_stem"), (4, 5), "a", "i-Box")],
}


def main():
    which, dates = sys.argv[1], sys.argv[2:]
    if which != "pooled":
        po.restrict_to(am.OPS.index(which))
    import recurrence_s12 as r
    import score_leads as sc
    import score_live as sl
    r.setup()
    D = r.G["D"]
    rows, _ = sl.load()
    ops = sl.OPS if which == "pooled" else [which]
    for name, test, kind, v, bet in LEADS[which]:
        tot = [0, 0, 0, 0.0, 0]
        cells = []
        for d in dates:
            pk = sc.picks(D.dates.index(d), test, kind, v)
            win = {op: {x["4d_number"]: x["prize"] for x in rows[op] if x["date"] == d} for op in ops}
            if pk is None:
                cells.append(f"{d}: no picks")
                continue
            s, sp, b, bp = sc.score({op: pk for op in ops}, win)
            tot[0] += len(s); tot[1] += sp; tot[2] += len(b); tot[3] += bp; tot[4] += 16 * len(ops)
            cells.append(f"{d}: straight {'; '.join(s) or '-'} | i-Box {len(b)} {'; '.join(b) or ''} ~RM{bp:.1f}")
        print(f"\n{which} | {name} | {bet}")
        for c in cells:
            print("   " + c)
        print(f"   TOTAL staked RM{tot[4]} | straight {tot[0]} RM{tot[1]} | i-Box {tot[2]} ~RM{tot[3]:.1f}")


if __name__ == "__main__":
    main()
