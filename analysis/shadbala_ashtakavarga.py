#!/usr/bin/env python3
"""Ashtakavarga and (simplified) Shadbala as parameters, run through the same
suite as the Navamsa / divisional-chart families (navamsa_family.run_suite:
A digit mix, B same-number recurrence, C S1 / S2 / rank-pair digit picks (a / b,
Straight / Reverse / i-Box, walk-forward), D whole-number hot / cold), each
against shifted calendars.

Chart: sidereal (Lahiri) positions at 19:00 MYT (continuous_astro_positions.npz).

Ashtakavarga (Parashara's bindu tables, 7 planets + Lagna as contributors)
  {planet}_bav       bindus (0-8) in the planet's own Bhinna Ashtakavarga for
                     the sign it occupies
  sav_{point}        Sarvashtakavarga bindus of the sign of Sun, Moon, ...,
                     Saturn, Lagna, and of the 11th house from Lagna; 5 bins
                     (<=22, 23-25, 26-28, 29-31, >=32)
Shadbala, simplified (no Kala / Drik / Ayana bala, which need birth-time
details or are near-constant across a few hours)
  sthana: uccha bala (distance from debilitation) + rashi dignity
  dig bala (distance from the planet's strong house: Jupiter / Mercury 1st,
  Sun / Mars 10th, Saturn 7th, Moon / Venus 4th)
  chesta bala (slow / retrograde motion; Mars - Saturn)
  paksha bala (Moon-Sun elongation: benefics gain with it, malefics lose)
  {planet}_strength  tercile of that sum (weak / medium / strong)
  strongest_planet, weakest_planet
  {planet}_dignity   exalted / own / friend / neutral / enemy / debilitated sign

Run from the repo root:  python3 analysis/shadbala_ashtakavarga.py [n_shifts]
"""

import datetime as dt
import itertools
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am  # noqa: E402
import ephemeris as eph  # noqa: E402
import navamsa_family as nf  # noqa: E402
import vedic  # noqa: E402

PL = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
REF = PL + ["Lagna"]
# BAV[planet][reference] = houses (from the reference's sign) that give a bindu
BAV = {
    "Sun": [[1, 2, 4, 7, 8, 9, 10, 11], [3, 6, 10, 11], [1, 2, 4, 7, 8, 9, 10, 11], [3, 5, 6, 9, 10, 11, 12],
            [5, 6, 9, 11], [6, 7, 12], [1, 2, 4, 7, 8, 9, 10, 11], [3, 4, 6, 10, 11, 12]],
    "Moon": [[3, 6, 7, 8, 10, 11], [1, 3, 6, 7, 10, 11], [2, 3, 5, 6, 9, 10, 11], [1, 3, 4, 5, 7, 8, 10, 11],
             [1, 4, 7, 8, 10, 11, 12], [3, 4, 5, 7, 9, 10, 11], [3, 5, 6, 11], [3, 6, 10, 11]],
    "Mars": [[3, 5, 6, 10, 11], [3, 6, 11], [1, 2, 4, 7, 8, 10, 11], [3, 5, 6, 11], [6, 10, 11, 12],
             [6, 8, 11, 12], [1, 4, 7, 8, 9, 10, 11], [1, 3, 6, 10, 11]],
    "Mercury": [[5, 6, 9, 11, 12], [2, 4, 6, 8, 10, 11], [1, 2, 4, 7, 8, 9, 10, 11], [1, 3, 5, 6, 9, 10, 11, 12],
                [6, 8, 11, 12], [1, 2, 3, 4, 5, 8, 9, 11], [1, 2, 4, 7, 8, 9, 10, 11], [1, 2, 4, 6, 8, 10, 11]],
    "Jupiter": [[1, 2, 3, 4, 7, 8, 9, 10, 11], [2, 5, 7, 9, 11], [1, 2, 4, 7, 8, 10, 11], [1, 2, 4, 5, 6, 9, 10, 11],
                [1, 2, 3, 4, 7, 8, 10, 11], [2, 5, 6, 9, 10, 11], [3, 5, 6, 12], [1, 2, 4, 5, 6, 7, 9, 10, 11]],
    "Venus": [[8, 11, 12], [1, 2, 3, 4, 5, 8, 9, 11, 12], [3, 5, 6, 9, 11, 12], [3, 5, 6, 9, 11], [5, 8, 9, 10, 11],
              [1, 2, 3, 4, 5, 8, 9, 10, 11], [3, 4, 5, 8, 9, 10, 11], [1, 2, 3, 4, 5, 8, 9, 11]],
    "Saturn": [[1, 2, 4, 7, 8, 10, 11], [3, 6, 11], [3, 5, 6, 10, 11, 12], [6, 8, 9, 10, 11, 12], [5, 6, 11, 12],
               [6, 11, 12], [3, 5, 6, 11], [1, 3, 4, 6, 10, 11]],
}
assert sum(len(h) for v in BAV.values() for h in v) == 337
LORD = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
EXALT = {"Sun": 10, "Moon": 33, "Mars": 298, "Mercury": 165, "Jupiter": 95, "Venus": 357, "Saturn": 200}
FRIEND = {"Sun": ({"Moon", "Mars", "Jupiter"}, {"Venus", "Saturn"}), "Moon": ({"Sun", "Mercury"}, set()),
          "Mars": ({"Sun", "Moon", "Jupiter"}, {"Mercury"}), "Mercury": ({"Sun", "Venus"}, {"Moon"}),
          "Jupiter": ({"Sun", "Moon", "Mars"}, {"Mercury", "Venus"}), "Venus": ({"Mercury", "Saturn"}, {"Sun", "Moon"}),
          "Saturn": ({"Mercury", "Venus"}, {"Sun", "Moon", "Mars"})}
DIGNITY = ["exalted", "own", "friend", "neutral", "enemy", "debilitated"]
DIG_HOUSE = {"Sun": 10, "Mars": 10, "Jupiter": 1, "Mercury": 1, "Saturn": 7, "Moon": 4, "Venus": 4}
MEAN_SPEED = {"Mars": 0.524, "Mercury": 0.986, "Jupiter": 0.083, "Venus": 0.986, "Saturn": 0.033}
BENEFIC = {"Moon", "Mercury", "Jupiter", "Venus"}
SAV_BINS = [23, 26, 29, 32]


def angdist(a, b):
    d = np.abs(a - b) % 360
    return np.minimum(d, 360 - d)


def speeds(dates):
    cache = os.path.join(am.ROOT, "analysis", "shadbala_speeds.npz")
    if os.path.exists(cache):
        z = np.load(cache, allow_pickle=True)
        if list(z["dates"]) == list(dates):
            return z["v"]
    v = np.zeros((len(dates), len(MEAN_SPEED)))
    for i, d in enumerate(dates):
        jd = eph.julian_day(dt.datetime.combine(dt.date.fromisoformat(d), dt.time(11)))
        for j, p in enumerate(MEAN_SPEED):
            v[i, j] = (vedic.planet_longitude(p, jd + 0.5) - vedic.planet_longitude(p, jd - 0.5) + 180) % 360 - 180
    np.savez(cache, dates=np.array(dates), v=v)
    return v


def codes_for(dates):
    z = np.load(os.path.join(am.ROOT, "analysis", "continuous_astro_positions.npz"), allow_pickle=True)
    assert list(z["dates"]) == list(dates), "positions cache is out of date: run continuous_astro.py"
    lon = z["lon"]                                                       # Sun Moon Mars Mercury Jupiter Venus Saturn Rahu Lagna
    col = {p: lon[:, nf.BODIES.index(p)] for p in REF}
    sign = {p: (col[p] // 30).astype(int) for p in REF}
    n = len(dates)
    codes, labels = {}, {}
    # Ashtakavarga
    bav = {}
    for p in PL:
        b = np.zeros((n, 12), int)
        for ri, ref in enumerate(REF):
            for h in BAV[p][ri]:
                b[np.arange(n), (sign[ref] + h - 1) % 12] += 1
        bav[p] = b
        codes[f"{p.lower()}_bav"] = b[np.arange(n), sign[p]]
        labels[f"{p.lower()}_bav"] = [str(k) for k in range(9)]
    sav = sum(bav.values())
    for p in REF:
        codes[f"sav_{p.lower()}"] = np.digitize(sav[np.arange(n), sign[p]], SAV_BINS)
    codes["sav_11th"] = np.digitize(sav[np.arange(n), (sign["Lagna"] + 10) % 12], SAV_BINS)
    for k in [k for k in codes if k.startswith("sav_")]:
        labels[k] = ["<=22", "23-25", "26-28", "29-31", ">=32"]
    # Shadbala (simplified)
    v = speeds(dates)
    elong = (col["Moon"] - col["Sun"]) % 360
    paksha = angdist(elong, 0) / 3                                       # 0 at new Moon, 60 at full Moon
    total = np.zeros((n, len(PL)))
    for j, p in enumerate(PL):
        uccha = angdist(col[p], EXALT[p] + 180) / 3
        dignity = np.full(n, 3)                                          # neutral
        fr, en = FRIEND[p]
        lords = np.array(LORD)[sign[p]]
        dignity[np.isin(lords, list(fr))] = 2
        dignity[np.isin(lords, list(en))] = 4
        dignity[lords == p] = 1
        dignity[sign[p] == EXALT[p] // 30] = 0
        dignity[sign[p] == (EXALT[p] // 30 + 6) % 12] = 5
        codes[f"{p.lower()}_dignity"] = dignity
        labels[f"{p.lower()}_dignity"] = DIGNITY
        rashi_pts = np.array([30, 30, 15, 7.5, 3.75, 1.875])[dignity]
        strong_pt = col["Lagna"] + (DIG_HOUSE[p] - 1) * 30
        dig = 60 * (1 - angdist(col[p], strong_pt) / 180)
        chesta = np.zeros(n)
        if p in MEAN_SPEED:
            s = v[:, list(MEAN_SPEED).index(p)]
            chesta = np.clip(30 * (1 - s / MEAN_SPEED[p]) + 30 * (s < 0), 0, 60)
        pk = paksha if p in BENEFIC else 60 - paksha
        total[:, j] = uccha + rashi_pts + dig + chesta + pk
        q = np.quantile(total[:, j], [1 / 3, 2 / 3])
        codes[f"{p.lower()}_strength"] = np.digitize(total[:, j], q)
        labels[f"{p.lower()}_strength"] = ["weak", "medium", "strong"]
    codes["strongest_planet"] = total.argmax(1)
    codes["weakest_planet"] = total.argmin(1)
    labels["strongest_planet"] = labels["weakest_planet"] = PL
    return codes, labels


def main():
    n_shifts = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    nf.wn.setup()
    codes, labels = codes_for(nf.r.G["D"].dates)
    nf.rperm.setup()
    for D in (nf.r.G["D"], nf.rperm.G["D"]):
        nf.inject(D, codes, labels)
    new = list(codes)
    for k in new:
        c = np.bincount(codes[k], minlength=len(labels[k]))
        print(f"   {k:<18} " + " ".join(f"{labels[k][i]}:{c[i]}" for i in range(len(c)) if c[i]))
    tests = [(f,) for f in new] + list(itertools.combinations(new, 2)) + [(a, b) for a in new for b in nf.r.FACT]
    out = nf.run_suite(tests, n_shifts, "shadbala_ashtakavarga_results.json", seed=47)
    names = [" x ".join(t) for t in tests]
    print("\nBy group: best digit-mix gain (A) and best S1 (b) i-Box z all years (C)")
    for grp, pred in (("Ashtakavarga", lambda f: f.endswith("_bav") or f.startswith("sav_")),
                      ("Shadbala", lambda f: f.endswith(("_strength", "_planet", "_dignity")))):
        idx = [i for i, t in enumerate(tests) if any(pred(f) for f in t)]
        g = max(idx, key=lambda i: out["A"]["gain"][names[i]])
        print(f"   {grp:<13} {len(idx)} tests; best A {out['A']['gain'][names[g]]:+.3f} [{names[g]}]")


if __name__ == "__main__":
    main()
