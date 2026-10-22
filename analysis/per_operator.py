#!/usr/bin/env python3
"""All analyses on singles and pairs of the 78 Vedic / Chinese parameters,
separately for each operator.

Until now winners of Magnum, Sports Toto and Da Ma Cai were pooled. Here only
one operator's winning numbers are kept, both as the source of the picks (digit
counts, earlier winners) and as the hits scored, and the chance level uses that
operator's own digit mix per year. The same suite as navamsa_family.py:
  A  digit mix given the value(s), learned before 2012, scored 2012-2026
  B  same 4D number again when the value(s) recur (Straight / Reverse / i-Box,
     any later / next same-value day)
  C  digit-position picks: S1, S2, rank pairs 1+10 .. 5+6; (a) all / (b)
     previous same-value day; Straight / Reverse / i-Box; forward check
  D  whole-number hot / cold, forward check
each against circularly shifted parameter calendars.

Run from the repo root:  python3 analysis/per_operator.py OPERATOR [n_shifts]
   OPERATOR = Magnum | "Sports Toto" | "Da Ma Cai"
"""

import itertools
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am  # noqa: E402
import digit_models as dm  # noqa: E402

ROW_FIELDS = ("rd", "ro", "rn", "ry", "rdig", "rj")


def restrict_to(op_ix):
    """Make every Data() keep only one operator's winning-number rows."""
    orig = dm.Data.__init__

    def init(self, *a, **k):
        orig(self, *a, **k)
        m = self.ro == op_ix
        for f in ROW_FIELDS:
            setattr(self, f, getattr(self, f)[m])
    dm.Data.__init__ = init


def main():
    op = sys.argv[1]
    n_shifts = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    op_ix = am.OPS.index(op)
    restrict_to(op_ix)
    import navamsa_family as nf                                          # imported after the patch
    nf.wn.setup()
    nf.rperm.setup()
    D = nf.r.G["D"]
    assert set(np.unique(D.ro)) == {op_ix}
    print(f"=== {op}: {len(D.rn)} winning numbers on {len(np.unique(D.rd))} draw days ===")
    tests = [(f,) for f in nf.r.FACT] + list(itertools.combinations(nf.r.FACT, 2))
    tag = op.lower().replace(" ", "")
    nf.run_suite(tests, n_shifts, f"per_operator_{tag}_results.json", seed=61 + op_ix)


if __name__ == "__main__":
    main()
