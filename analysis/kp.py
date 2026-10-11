"""Krishnamurti Paddhati (KP) positions: the 249 sub-divisions, sign/star/sub
lords, and the Ascendant.

The zodiac is split into 27 nakshatras of 13 deg 20'; each is divided into 9
subs proportional to the Vimshottari dasha years, starting from the
nakshatra's own lord. Subs that straddle a sign boundary are split in two,
giving the 249 KP numbers (1 = Aries 0 deg 00' - 0 deg 46' 40").

Longitudes use the KP ayanamsa, taken as Lahiri minus 5' 20" (0.0889 deg); the
difference only matters within a few arc-minutes of a sub boundary.

Run directly for a self-check.
"""

import datetime as dt
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ephemeris as eph  # noqa: E402
import vedic  # noqa: E402

DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7, "Rahu": 18,
               "Jupiter": 16, "Saturn": 19, "Mercury": 17}
SIGN_LORDS = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars",
              "Jupiter", "Saturn", "Saturn", "Jupiter"]
KP_OFFSET = 0.0889
BODIES = ["Ascendant", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu"]
NAK = 360 / 27


def _build_table():
    """List of (start_deg, end_deg, sign_lord, star_lord, sub_lord), KP no. = index + 1."""
    table = []
    for n in range(27):
        star = DASHA_ORDER[n % 9]
        start = n * NAK
        first = DASHA_ORDER.index(star)
        for k in range(9):
            sub = DASHA_ORDER[(first + k) % 9]
            end = start + NAK * DASHA_YEARS[sub] / 120
            boundary = (math.floor(start / 30 + 1e-9) + 1) * 30
            if start < boundary - 1e-9 < end - 2e-9:
                table.append((start, boundary, star, sub))
                start = boundary
            table.append((start, end, star, sub))
            start = end
    return [(s, e, SIGN_LORDS[int(s // 30)], star, sub) for s, e, star, sub in table]


TABLE = _build_table()
_STARTS = [row[0] for row in TABLE]


def kp_ayanamsa(jd):
    return vedic.ayanamsa(jd) - KP_OFFSET


def ascendant_tropical(jd, lat=vedic.KL_LAT, lon=vedic.KL_LON):
    T = (jd - 2451545.0) / 36525
    eps = math.radians(23.439291 - 0.0130042 * T)
    ramc = math.radians((280.46061837 + 360.98564736629 * (jd - 2451545.0) + lon) % 360)
    asc = math.degrees(math.atan2(math.cos(ramc),
                                  -(math.sin(ramc) * math.cos(eps) + math.tan(math.radians(lat)) * math.sin(eps))))
    return asc % 360


def kp_position(longitude_sidereal):
    """KP number (1-249) and lords for a sidereal longitude."""
    import bisect
    i = bisect.bisect_right(_STARTS, longitude_sidereal % 360) - 1
    s, e, sign_lord, star, sub = TABLE[i]
    return {"kp": i + 1, "sign_lord": sign_lord, "star_lord": star, "sub_lord": sub}


def chart(t_utc):
    """KP number and lords for every body at t_utc (Kuala Lumpur for the Ascendant)."""
    jd = eph.julian_day(t_utc)
    ay = kp_ayanamsa(jd)
    out = {}
    for b in BODIES:
        trop = ascendant_tropical(jd) if b == "Ascendant" else vedic.planet_longitude(b, jd)
        out[b] = kp_position(trop - ay)
    return out


if __name__ == "__main__":
    print("subs:", len(TABLE), "(expect 249); last ends at", round(TABLE[-1][1], 6))
    for i in (0, 1, 8, 9, 248):
        s, e, sl, st, sb = TABLE[i]
        print(f"  KP {i + 1:>3}: {s:8.4f} - {e:8.4f} deg  sign {sl:<7} star {st:<7} sub {sb}")
    # Ascendant sanity: at sunrise the Ascendant equals the Sun's longitude.
    for day in (dt.date(2024, 3, 20), dt.date(2024, 6, 21), dt.date(2024, 12, 21)):
        rise, _ = vedic.sun_rise_set(day)
        jd = eph.julian_day(rise)
        diff = (ascendant_tropical(jd) - eph.sun_longitude(jd) + 180) % 360 - 180
        print(f"  {day} sunrise: Ascendant - Sun = {diff:+.2f} deg (expect ~0, refraction/limb ~0.5 deg)")
    print("  2026-10-10 19:00 MYT:", {b: v["kp"] for b, v in chart(dt.datetime(2026, 10, 10, 11)).items()})
