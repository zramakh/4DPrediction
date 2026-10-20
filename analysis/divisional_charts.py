#!/usr/bin/env python3
"""Other divisional charts (vargas) besides D9, run through the same analyses
A-D as navamsa_family.py.

Varga sign of Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Lagna at
19:00 MYT (sidereal positions from continuous_astro_positions.npz), standard
Parashara rules (sign s = 0 Aries .. 11 Pisces, d = degree in sign):
  D2  Hora           odd signs: 0-15 Leo, 15-30 Cancer; even signs reversed
  D3  Drekkana       s + 4k              (k = 10-degree part)
  D4  Chaturthamsa   s + 3k
  D7  Saptamsa       odd: s + k, even: s + 6 + k
  D10 Dasamsa        odd: s + k, even: s + 8 + k
  D12 Dwadasamsa     s + k
  D16 Shodasamsa     from Aries / Leo / Sagittarius (movable / fixed / dual) + k
  D20 Vimsamsa       from Aries / Sagittarius / Leo + k
  D24 Chaturvimsamsa odd: from Leo, even: from Cancer + k
  D27 Bhamsa         from Aries / Cancer / Libra / Capricorn (fire/earth/air/water) + k
  D30 Trimsamsa      odd: 5 Aries, 5 Aquarius, 8 Sagittarius, 7 Gemini, 5 Libra;
                     even: 5 Taurus, 7 Virgo, 8 Pisces, 5 Capricorn, 5 Scorpio
  D40 Khavedamsa     odd: from Aries, even: from Libra + k
  D45 Akshavedamsa   from Aries / Leo / Sagittarius + k
  D60 Shashtiamsa    s + k
Tests: each of the 126 alone and all 36 pairs within each chart (630 tests).
Note: the Lagna moves about 1 degree every 4 minutes, so its finer charts (D30
and up) are uncertain within the 19:00-19:30 draw window.

Run from the repo root:  python3 analysis/divisional_charts.py [n_shifts]
"""

import itertools
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am  # noqa: E402
import navamsa_family as nf  # noqa: E402

BODIES = nf.BODIES
RASHIS = nf.RASHIS
CHARTS = [2, 3, 4, 7, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]


def varga(lon, n):
    s = (lon // 30).astype(int) % 12
    d = lon % 30
    odd = s % 2 == 0                                                      # Aries, Gemini, ... are odd signs
    k = np.minimum((d * n / 30).astype(int), n - 1)
    mod, elem = s % 3, s % 4
    if n == 2:
        return np.where(odd == (d < 15), 4, 3)                           # Leo or Cancer
    if n == 3:
        return (s + 4 * k) % 12
    if n == 4:
        return (s + 3 * k) % 12
    if n == 7:
        return (s + np.where(odd, 0, 6) + k) % 12
    if n == 10:
        return (s + np.where(odd, 0, 8) + k) % 12
    if n in (12, 60):
        return (s + k) % 12
    if n == 16:
        return (np.array([0, 4, 8])[mod] + k) % 12
    if n == 20:
        return (np.array([0, 8, 4])[mod] + k) % 12
    if n == 24:
        return (np.where(odd, 4, 3) + k) % 12
    if n == 27:
        return (np.array([0, 3, 6, 9])[elem] + k) % 12
    if n == 30:
        odd_e, odd_s = np.array([5, 10, 18, 25, 30]), np.array([0, 10, 8, 2, 6])
        evn_e, evn_s = np.array([5, 12, 20, 25, 30]), np.array([1, 5, 11, 9, 7])
        io = np.searchsorted(odd_e, d, side="right").clip(0, 4)
        ie = np.searchsorted(evn_e, d, side="right").clip(0, 4)
        return np.where(odd, odd_s[io], evn_s[ie])
    if n == 40:
        return (np.where(odd, 0, 6) + k) % 12
    if n == 45:
        return (np.array([0, 4, 8])[mod] + k) % 12
    raise ValueError(n)


def chart_codes(dates):
    z = np.load(os.path.join(am.ROOT, "analysis", "continuous_astro_positions.npz"), allow_pickle=True)
    assert list(z["dates"]) == list(dates), "positions cache is out of date: run continuous_astro.py"
    lon = z["lon"]
    codes, labels = {}, {}
    for n in CHARTS:
        for j, b in enumerate(BODIES):
            k = f"{b.lower()}_d{n}"
            codes[k] = varga(lon[:, j], n)
            labels[k] = RASHIS
    return codes, labels


def main():
    n_shifts = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    nf.wn.setup()
    codes, labels = chart_codes(nf.r.G["D"].dates)
    nf.rperm.setup()
    for D in (nf.r.G["D"], nf.rperm.G["D"]):
        nf.inject(D, codes, labels)
    # sanity: D9 rule reproduces the navamsa; D1-equivalent checks
    tests = []
    for n in CHARTS:
        fam = [f"{b.lower()}_d{n}" for b in BODIES]
        tests += [(f,) for f in fam] + list(itertools.combinations(fam, 2))
    out = nf.run_suite(tests, n_shifts, "divisional_charts_results.json", seed=43)
    # per chart: forward mean of C over its own tests is not separable from the column summary,
    # so report each chart's best A gain and best C test
    names = [" x ".join(t) for t in tests]
    print("\nBy chart: best digit-mix gain (A) among its tests")
    for n in CHARTS:
        g = [out["A"]["gain"][nm] for nm in names if all(p.endswith(f"_d{n}") for p in nm.split(" x "))]
        print(f"   D{n:<3} best {max(g):+.3f}, mean {np.mean(g):+.3f} ({len(g)} tests)")


if __name__ == "__main__":
    main()
