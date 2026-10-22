#!/usr/bin/env python3
"""Day pillar combined with every pair of the other 77 parameters (A x B x Day
pillar, 2,926 triples), scored with the Karana x Day pillar method (S1 from the
previous same-value day, i-Box), against Karana x Day pillar itself.

For each triple: z before 2012, z 2012-2026, good years 2012-2026, ratio after.
Fair choice: the triples with the best z before 2012, scored 2012-2026. Chance:
the same on 10 circularly shifted parameter calendars.

Run from the repo root:  python3 analysis/day_pillar_triples.py
"""

import itertools
import json
import multiprocessing as mp
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am  # noqa: E402
import karana_family as kf  # noqa: E402
import navamsa_family as nf  # noqa: E402

# parameters fixed by the day pillar add nothing to it
SAME_AS_PILLAR = {"day_stem", "day_branch", "nayin", "nayin_element", "day_element", "hour_stem_19h"}


def task(args):
    return kf.summary(*args)


def main():
    nf.r.setup()
    G = nf.r.G
    G["yr"] = np.array([int(d[:4]) for d in G["D"].dates])
    others = [f for f in nf.r.FACT if f != "day_pillar" and f not in SAME_AS_PILLAR]
    triples = [tuple(sorted((a, b, "day_pillar"), key=nf.r.FACT.index)) for a, b in itertools.combinations(others, 2)]
    lead = kf.summary(("karana", "day_pillar"))
    rng = np.random.default_rng(97)
    shifts = [int(s) for s in rng.integers(170, G["nd"] - 170, 10)]
    with mp.get_context("fork").Pool(4) as pool:
        R = np.array(pool.map(task, [(t, 0) for t in triples], chunksize=16))
        N = [np.array(pool.map(task, [(t, s) for t in triples], chunksize=16)) for s in shifts]
    names = [" x ".join(t) for t in triples]
    print(f"{len(triples)} triples (Day pillar x A x B; {len(others)} other parameters, excluding the 6 fixed by the day pillar)")
    print(f"Karana x Day pillar: z before {lead[0]:+.2f}, after {lead[1]:+.2f}, {lead[2]}/15 good years, x{lead[3]:.3f}\n")

    def block(X):
        X = X[np.isfinite(X).all(1)]                                       # drop triples with no history in a period
        top = np.argsort(-X[:, 0])[:20]
        return X[:, 1].mean(), X[:, 2].mean(), X[top, 1].mean(), X[top, 2].mean(), int((X[:, 1] > lead[1]).sum()), \
            int(((X[:, 2] >= lead[2])).sum()), int(((X[:, 0] > 2) & (X[:, 1] > 2)).sum())
    real = block(R)
    nulls = np.array([block(n) for n in N])
    labels = ["mean z after (all triples)", "mean good years (all triples)", "top 20 chosen before 2012: mean z after",
              "top 20 chosen before 2012: mean good years", f"triples with z after > the lead's {lead[1]:+.2f}",
              f"triples with {lead[2]}+ good years", "triples with z > 2 in both periods"]
    print("measure | real | shifted calendars mean (range)")
    for i, lab in enumerate(labels):
        print(f"   {lab:<44} {real[i]:+.2f} | {nulls[:, i].mean():+.2f} ({nulls[:, i].min():+.2f} to {nulls[:, i].max():+.2f})")
    print("\nTop 10 chosen before 2012 -> 2012-2026:")
    R = np.where(np.isfinite(R), R, -99.0)                                  # no-history triples sort last
    for q in np.argsort(-R[:, 0])[:10]:
        print(f"   {names[q]:<55} before {R[q, 0]:+.2f} | after {R[q, 1]:+.2f} (x{R[q, 3]:.3f}) | {int(R[q, 2])}/15")
    print("\nPositive in both periods, best combined (z before + z after):")
    both = [q for q in range(len(triples)) if R[q, 0] > 0 and R[q, 1] > 0]
    for q in sorted(both, key=lambda q: -(R[q, 0] + R[q, 1]))[:10]:
        print(f"   {names[q]:<55} before {R[q, 0]:+.2f} | after {R[q, 1]:+.2f} (x{R[q, 3]:.3f}) | {int(R[q, 2])}/15")
    print("\nBest after 2012 (hindsight):")
    for q in np.argsort(-R[:, 1])[:10]:
        print(f"   {names[q]:<55} before {R[q, 0]:+.2f} | after {R[q, 1]:+.2f} (x{R[q, 3]:.3f}) | {int(R[q, 2])}/15")
    kar = [q for q, t in enumerate(triples) if "karana" in t]
    K = R[kar]
    K = K[(K > -99).all(1)]
    print(f"\nKarana x Day pillar x a third parameter ({len(kar)} triples): mean z before {K[:, 0].mean():+.2f}, after {K[:, 1].mean():+.2f}, "
          f"good years {K[:, 2].mean():.2f}; {int((K[:, 1] > lead[1]).sum())} beat the lead after 2012")
    for q in sorted(kar, key=lambda q: -R[q, 1])[:5]:
        print(f"   {names[q]:<55} before {R[q, 0]:+.2f} | after {R[q, 1]:+.2f} (x{R[q, 3]:.3f}) | {int(R[q, 2])}/15")
    json.dump({"lead": list(map(float, lead)), "triples": {n: list(map(float, x)) for n, x in zip(names, R)},
               "real": list(map(float, real)), "null": nulls.tolist()},
              open(os.path.join(am.ROOT, "analysis", "day_pillar_triples_results.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
