#!/usr/bin/env python3
"""Score the best per-operator leads (per_operator.py, chosen on 1985-2011)
on given draw dates. Picks are rebuilt for each date from that operator's
earlier results only and scored on that operator's draw only, as Straight and
i-Box (approximate i-Box payout = Big prize / arrangements). RM1 per number,
16 numbers = RM16 per draw.

Run from the repo root:  python3 analysis/per_operator_leads.py OPERATOR DATE [DATE ...]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am  # noqa: E402
import per_operator as po  # noqa: E402

LEADS = {
    "Magnum": [("Hour stem 19h", ("hour_stem_19h",), (3, 6), "a", "Straight"),
               ("KP Asc number x Nine star year", ("kp_asc_number", "nine_star_year"), (1, 8), "b", "Straight"),
               ("KP Moon number x Day officer", ("kp_moon_number", "day_officer"), (3, 6), "b", "Straight")],
    "Sports Toto": [("Mercury rashi x Moon navamsa", ("mercury_rashi", "moon_navamsa"), (2, 7), "b", "i-Box"),
                    ("Mercury combust x KP Moon star lord", ("mercury_combust", "kp_moon_star_lord"), (3, 6), "b", "Reverse")],
    "Da Ma Cai": [("KP Moon sub lord x Nine star month", ("kp_moon_sub_lord", "nine_star_month"), (4, 5), "a", "Straight"),
                  ("Month branch x Hour stem 19h", ("month_branch", "hour_stem_19h"), (0, 9), "a", "Reverse")],
}


def main():
    op, dates = sys.argv[1], sys.argv[2:]
    po.restrict_to(am.OPS.index(op))
    import recurrence_s12 as r
    import score_leads as sc
    import score_live as sl
    r.setup()
    D = r.G["D"]
    rows, _ = sl.load()
    for name, test, kind, v, bet in LEADS[op]:
        print(f"\n{op} | {name} | {kind[0] + 1}+{kind[1] + 1} ({v}) | {bet}")
        tot = [0, 0, 0, 0.0, 0]
        for d in dates:
            t = D.dates.index(d)
            win = {op: {x["4d_number"]: x["prize"] for x in rows[op] if x["date"] == d}}
            pk = sc.picks(t, test, kind, v)
            if pk is None:
                print(f"  {d}: no earlier same-value day")
                continue
            s, sp, b, bp = sc.score({op: pk}, win)
            tot[0] += len(s); tot[1] += sp; tot[2] += len(b); tot[3] += bp; tot[4] += 16
            print(f"  {d}: {' '.join(pk)}")
            print(f"     straight {len(s)} {'; '.join(s) or '-'} RM{sp} | i-Box {len(b)} {'; '.join(b) or '-'} ~RM{bp:.2f}")
        print(f"  TOTAL staked RM{tot[4]} | straight {tot[0]} RM{tot[1]} | i-Box {tot[2]} ~RM{tot[3]:.2f}")


if __name__ == "__main__":
    main()
