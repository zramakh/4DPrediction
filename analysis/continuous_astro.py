#!/usr/bin/env python3
"""Exact (continuous) planetary positions at the 19:00 MYT draw vs 4D digits.

Features per draw date (sidereal, Lahiri, as in almanac.py):
  lon_X        longitude of Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn,
               Rahu, Lagna (Ascendant at Kuala Lumpur)
  sep_X_Y      angle between each pair (36 pairs), 0-360
  aspect_X_Y   aspect class of each pair: conjunction 0, sextile 60, square 90,
               trine 120, opposition 180 (orb 6 deg) or none
  moon_in_nakshatra, moon_in_rashi, lagna_in_rashi   how far through the sign
Model: angle features in 24 bins of 15 deg; for each bin (or aspect class) and
digit position, the digit distribution learned on draws before 2012 (smoothed
toward the overall mix). Score on 2012-2026 draws: log-likelihood gain over the
overall digit mix, in milli-nats per digit (0 = no information; positive =
the feature predicts digits). Chance: 30 circular shifts of the feature
calendar (one shift for all features, at least about a year of draw days).

Run from the repo root:  python3 analysis/continuous_astro.py
"""

import datetime as dt
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am  # noqa: E402
import digit_models as dm  # noqa: E402
import ephemeris as eph  # noqa: E402
import kp  # noqa: E402
import vedic  # noqa: E402

BODIES = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu"]
SPLIT = 2012
NBIN = 24
ALPHA = 500.0
ASPECTS = np.array([0, 60, 90, 120, 180])
ORB = 6.0
CACHE = os.path.join(am.ROOT, "analysis", "continuous_astro_positions.npz")


def positions(dates):
    if os.path.exists(CACHE):
        z = np.load(CACHE, allow_pickle=True)
        if list(z["dates"]) == list(dates):
            return z["lon"]
    lon = np.zeros((len(dates), len(BODIES) + 1))
    for i, d in enumerate(dates):
        t = dt.datetime.combine(dt.date.fromisoformat(d), dt.time(11))      # 19:00 MYT = 11:00 UTC
        jd = eph.julian_day(t)
        for j, b in enumerate(BODIES):
            lon[i, j] = vedic.sidereal(b, jd)
        lon[i, -1] = (kp.ascendant_tropical(jd) - vedic.ayanamsa(jd)) % 360
    np.savez(CACHE, dates=np.array(dates), lon=lon)
    return lon


def features(lon):
    names = BODIES + ["Lagna"]
    ang, cat = {}, {}
    for j, n in enumerate(names):
        ang[f"lon_{n}"] = lon[:, j]
    for a in range(len(names)):
        for b in range(a + 1, len(names)):
            s = (lon[:, a] - lon[:, b]) % 360
            ang[f"sep_{names[a]}_{names[b]}"] = s
            fold = np.minimum(s, 360 - s)
            dist = np.abs(fold[:, None] - ASPECTS[None, :])
            c = np.where(dist.min(1) <= ORB, dist.argmin(1) + 1, 0)
            cat[f"aspect_{names[a]}_{names[b]}"] = c
    nak = 360 / 27
    ang["moon_in_nakshatra"] = (lon[:, 1] % nak) / nak * 360
    ang["moon_in_rashi"] = (lon[:, 1] % 30) * 12
    ang["lagna_in_rashi"] = (lon[:, -1] % 30) * 12
    codes = {k: (v // (360 / NBIN)).astype(int) % NBIN for k, v in ang.items()}
    codes.update(cat)
    return codes


def gain(code_row, dig, train, test, ncat, rd):
    """Mean log-likelihood gain per digit on test rows (milli-nats) and its z (per-date blocks)."""
    base = np.stack([np.bincount(dig[train, p], minlength=10) for p in range(4)]).astype(float)
    base /= base.sum(1, keepdims=True)
    cnt = np.zeros((ncat, 4, 10))
    for p in range(4):
        np.add.at(cnt[:, p], (code_row[train], dig[train, p]), 1)
    q = (cnt + ALPHA * base[None]) / (cnt.sum(2, keepdims=True) + ALPHA)
    ct = code_row[test]
    ll = sum(np.log(q[ct, p, dig[test, p]] / base[p, dig[test, p]]) for p in range(4))
    per_date = np.bincount(rd[test], weights=ll)
    n_date = np.bincount(rd[test])
    ok = n_date > 0
    m = ll.sum() / (4 * len(ll))
    se = per_date[ok].std(ddof=1) * np.sqrt(ok.sum()) / (4 * len(ll))
    return 1000 * m, m / se


def main():
    D = dm.Data()
    lon = positions(D.dates)
    F = features(lon)
    yr = np.array([int(d[:4]) for d in D.dates])
    rd = D.rd
    dig = D.rdig
    train = yr[rd] < SPLIT
    test = ~train
    names = list(F)
    real = {}
    for k in names:
        c = F[k]
        real[k] = gain(c[rd], dig, train, test, int(c.max()) + 1, rd)
    rng = np.random.default_rng(13)
    nd = len(D.dates)
    shifts = rng.integers(170, nd - 170, 30)
    null = np.zeros((len(shifts), len(names)))
    for i, s in enumerate(shifts):
        for j, k in enumerate(names):
            c = np.roll(F[k], int(s))
            null[i, j] = gain(c[rd], dig, train, test, int(F[k].max()) + 1, rd)[0]
    g = np.array([real[k][0] for k in names])
    zs = np.array([real[k][1] for k in names])
    print(f"{len(names)} features; learned on draws before {SPLIT}, scored on {SPLIT}-2026 "
          f"({int(test.sum())} winning numbers)")
    print(f"   features with gain > 0: {int((g > 0).sum())} (shifted calendars: {np.mean((null > 0).sum(1)):.1f} on average, "
          f"range {(null > 0).sum(1).min()}-{(null > 0).sum(1).max()})")
    print(f"   best gain {g.max():+.3f} milli-nats/digit [{names[int(g.argmax())]}]; shifted calendars' best "
          f"{null.max(1).mean():+.3f} (range {null.max(1).min():+.3f} to {null.max(1).max():+.3f}); "
          f"{int((null.max(1) >= g.max()).sum())}/30 as high")
    print(f"   mean gain over all features {g.mean():+.3f} vs shifted {null.mean():+.3f}")
    print("\nTop 10 features (gain in milli-nats per digit on 2012-2026; z from per-draw variation; share of shifts with this feature as high):")
    out = []
    for j in np.argsort(-g)[:10]:
        share = float(np.mean(null[:, j] >= g[j]))
        print(f"   {names[j]:<28} {g[j]:+.3f}  z {zs[j]:+.2f}  shifts as high {share:.2f}")
    for j, k in enumerate(names):
        out.append({"feature": k, "gain_mnats": float(g[j]), "z": float(zs[j]),
                    "null_mean": float(null[:, j].mean()), "null_share_as_high": float(np.mean(null[:, j] >= g[j]))})
    print("\nBy group (mean gain): " + ", ".join(
        f"{grp} {np.mean([g[j] for j, k in enumerate(names) if k.startswith(grp)]):+.3f}"
        for grp in ("lon_", "sep_", "aspect_", "moon_in", "lagna_in")))
    json.dump({"features": out, "null_best": null.max(1).tolist(), "null_n_positive": (null > 0).sum(1).tolist()},
              open(os.path.join(am.ROOT, "analysis", "continuous_astro_results.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
