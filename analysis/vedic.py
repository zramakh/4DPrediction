"""Vedic (sidereal) astrology quantities for a moment in time.

Builds on ephemeris.py (Meeus Sun/Moon) and adds:
  * Lahiri (Chitrapaksha) ayanamsa -> sidereal longitudes
  * Mercury..Saturn from the JPL approximate Keplerian elements
    (Standish, valid 1800-2050, accuracy well under 1 deg), and the mean
    lunar node for Rahu/Ketu
  * Panchanga: tithi, paksha, nakshatra (+pada), yoga, karana, vara
  * Hora lord at a given time, from sunrise/sunset at Kuala Lumpur

Run directly for a self-check against published events.
"""

import datetime as dt
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ephemeris as eph  # noqa: E402

RASHIS = ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya", "Tula", "Vrischika",
          "Dhanu", "Makara", "Kumbha", "Meena"]
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu",
              "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta",
              "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
              "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
              "Uttara Bhadrapada", "Revati"]
# Vimshottari lords of the nakshatras, repeating every 9.
NAKSHATRA_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
# Vara (weekday) lords, Monday=0 as in datetime.weekday().
VARA_LORDS = ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun"]
# Hora sequence (Chaldean order, descending orbital period).
HORA_ORDER = ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"]
# Planet numbers used in Vedic numerology (Ank Jyotish).
PLANET_NUMBER = {"Sun": 1, "Moon": 2, "Jupiter": 3, "Rahu": 4, "Mercury": 5, "Venus": 6,
                 "Ketu": 7, "Saturn": 8, "Mars": 9}
KARANAS_MOVABLE = ["Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija", "Vishti"]

KL_LAT, KL_LON = 3.139, 101.687

# a, e, I, L, long.peri, long.node (J2000 values and rates per century)
_ELEMENTS = {
    "Mercury": ((0.38709927, 0.20563593, 7.00497902, 252.25032350, 77.45779628, 48.33076593),
                (0.00000037, 0.00001906, -0.00594749, 149472.67411175, 0.16047689, -0.12534081)),
    "Venus": ((0.72333566, 0.00677672, 3.39467605, 181.97909950, 131.60246718, 76.67984255),
              (0.00000390, -0.00004107, -0.00078890, 58517.81538729, 0.00268329, -0.27769418)),
    "Earth": ((1.00000261, 0.01671123, -0.00001531, 100.46457166, 102.93768193, 0.0),
              (0.00000562, -0.00004392, -0.01294668, 35999.37244981, 0.32327364, 0.0)),
    "Mars": ((1.52371034, 0.09339410, 1.84969142, -4.55343205, -23.94362959, 49.55953891),
             (0.00001847, 0.00007882, -0.00813131, 19140.30268499, 0.44441088, -0.29257343)),
    "Jupiter": ((5.20288700, 0.04838624, 1.30439695, 34.39644051, 14.72847983, 100.47390909),
                (-0.00011607, -0.00013253, -0.00183714, 3034.74612775, 0.21252668, 0.20469106)),
    "Saturn": ((9.53667594, 0.05386179, 2.48599187, 49.95424423, 92.59887831, 113.66242448),
               (-0.00125060, -0.00050991, 0.00193609, 1222.49362201, -0.41897216, -0.28867794)),
}


def ayanamsa(jd):
    """Lahiri ayanamsa in degrees (23 deg 51' at J2000, precessing 50.29"/yr)."""
    return 23.85306 + 1.396971 * (jd - 2451545.0) / 36525


def _helio(name, T):
    el0, rate = _ELEMENTS[name]
    a, e, I, L, wbar, node = (x + r * T for x, r in zip(el0, rate))
    M = math.radians((L - wbar) % 360)
    E = M + e * math.sin(M)
    for _ in range(10):
        E -= (E - e * math.sin(E) - M) / (1 - e * math.cos(E))
    xp = a * (math.cos(E) - e)
    yp = a * math.sqrt(1 - e * e) * math.sin(E)
    w = math.radians(wbar - node)
    O, inc = math.radians(node), math.radians(I)
    x = ((math.cos(w) * math.cos(O) - math.sin(w) * math.sin(O) * math.cos(inc)) * xp
         + (-math.sin(w) * math.cos(O) - math.cos(w) * math.sin(O) * math.cos(inc)) * yp)
    y = ((math.cos(w) * math.sin(O) + math.sin(w) * math.cos(O) * math.cos(inc)) * xp
         + (-math.sin(w) * math.sin(O) + math.cos(w) * math.cos(O) * math.cos(inc)) * yp)
    return x, y


def planet_longitude(name, jd):
    """Geocentric tropical ecliptic longitude of date."""
    T = (jd - 2451545.0) / 36525
    if name == "Sun":
        return eph.sun_longitude(jd)
    if name == "Moon":
        return eph.moon_longitude(jd)
    if name in ("Rahu", "Ketu"):
        node = (125.04452 - 1934.136261 * T) % 360  # mean node
        return node if name == "Rahu" else (node + 180) % 360
    px, py = _helio(name, T)
    ex, ey = _helio("Earth", T)
    lon_j2000 = math.degrees(math.atan2(py - ey, px - ex))
    return (lon_j2000 + 1.396971 * T) % 360  # precess J2000 -> of date


def sidereal(name, jd):
    return (planet_longitude(name, jd) - ayanamsa(jd)) % 360


def is_retrograde(name, jd):
    if name in ("Sun", "Moon", "Rahu", "Ketu"):
        return name in ("Rahu", "Ketu")  # nodes always move backwards
    d = (planet_longitude(name, jd + 0.5) - planet_longitude(name, jd - 0.5) + 180) % 360 - 180
    return d < 0


def sun_rise_set(day, lat=KL_LAT, lon=KL_LON):
    """UTC datetimes of sunrise and sunset (upper limb, refraction) on `day`."""
    def event(rising):
        t = dt.datetime.combine(day, dt.time(12)) - dt.timedelta(hours=lon / 15)
        for _ in range(4):
            jd = eph.julian_day(t)
            T = (jd - 2451545.0) / 36525
            lam = math.radians(eph.sun_longitude(jd))
            eps = math.radians(23.439291 - 0.0130042 * T)
            ra = math.atan2(math.cos(eps) * math.sin(lam), math.cos(lam))
            dec = math.asin(math.sin(eps) * math.sin(lam))
            gmst = (280.46061837 + 360.98564736629 * (jd - 2451545.0)) % 360
            ha_now = math.radians(gmst + lon) - ra
            cos_h0 = ((math.sin(math.radians(-0.833)) - math.sin(math.radians(lat)) * math.sin(dec))
                      / (math.cos(math.radians(lat)) * math.cos(dec)))
            h0 = math.acos(cos_h0) * (-1 if rising else 1)
            diff = (h0 - ha_now + math.pi) % (2 * math.pi) - math.pi
            t += dt.timedelta(hours=math.degrees(diff) / 15 / 1.0027379)
        return t
    return event(True), event(False)


def hora_lord(t_utc, local_day):
    """Planetary hour lord at t_utc. Day horas split sunrise..sunset into 12,
    night horas split sunset..next sunrise into 12; the first day hora belongs
    to the weekday lord, then the Chaldean sequence continues."""
    rise, sset = sun_rise_set(local_day)
    next_rise, _ = sun_rise_set(local_day + dt.timedelta(days=1))
    vara = VARA_LORDS[local_day.weekday()]
    start = HORA_ORDER.index(vara)
    if t_utc < rise:
        raise ValueError("before sunrise: belongs to the previous vara")
    if t_utc < sset:
        k = int((t_utc - rise) / ((sset - rise) / 12))
    else:
        k = 12 + int((t_utc - sset) / ((next_rise - sset) / 12))
    return HORA_ORDER[(start + k) % 7]


def panchanga(t_utc, local_day):
    jd = eph.julian_day(t_utc)
    sun, moon = sidereal("Sun", jd), sidereal("Moon", jd)
    elong = (moon - sun) % 360
    tithi = int(elong // 12) + 1  # 1..30
    half = int(elong // 6)  # 0..59 karana index
    if half == 0:
        karana = "Kimstughna"
    elif half >= 57:
        karana = ["Shakuni", "Chatushpada", "Naga"][half - 57]
    else:
        karana = KARANAS_MOVABLE[(half - 1) % 7]
    nak = int(moon // (360 / 27))
    out = {
        "tithi": tithi,
        "paksha": "Shukla" if tithi <= 15 else "Krishna",
        "nakshatra": NAKSHATRAS[nak],
        "nakshatra_lord": NAKSHATRA_LORDS[nak % 9],
        "pada": int(moon % (360 / 27) // (360 / 108)) + 1,
        "yoga": int(((sun + moon) % 360) // (360 / 27)) + 1,
        "karana": karana,
        "vara_lord": VARA_LORDS[local_day.weekday()],
        "hora_lord": hora_lord(t_utc, local_day),
        "moon_rashi": RASHIS[int(moon // 30)],
        "sun_rashi": RASHIS[int(sun // 30)],
    }
    for p in ("Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu"):
        out[f"{p.lower()}_rashi"] = RASHIS[int(sidereal(p, jd) // 30)]
    out["mercury_retrograde"] = is_retrograde("Mercury", jd)
    return out


if __name__ == "__main__":
    def ingress(name, start, end, rashi):
        """First day in [start, end] the planet is in `rashi` (sidereal)."""
        d = start
        while d <= end:
            if RASHIS[int(sidereal(name, eph.julian_day(dt.datetime.combine(d, dt.time(12)))) // 30)] == rashi:
                return d
            d += dt.timedelta(days=1)

    # Published sidereal (Lahiri) ingresses and retrogrades.
    checks = [
        ("Jupiter enters Vrishabha", ingress("Jupiter", dt.date(2024, 4, 1), dt.date(2024, 6, 1), "Vrishabha"), "2024-05-01"),
        ("Saturn enters Meena", ingress("Saturn", dt.date(2025, 2, 1), dt.date(2025, 5, 1), "Meena"), "2025-03-29"),
        ("Saturn enters Kumbha", ingress("Saturn", dt.date(2022, 4, 1), dt.date(2022, 5, 30), "Kumbha"), "2022-04-29"),
        ("Rahu enters Meena (mean)", ingress("Rahu", dt.date(2023, 9, 1), dt.date(2023, 12, 1), "Meena"), "2023-10-30"),
        ("Mars enters Karka", ingress("Mars", dt.date(2024, 9, 1), dt.date(2024, 11, 1), "Karka"), "2024-10-20"),
        ("Venus enters Makara", ingress("Venus", dt.date(2024, 12, 1), dt.date(2025, 1, 1), "Makara"), "2024-12-02"),
    ]
    for name, got, want in checks:
        print(f"{name:<26} computed {got}  published {want}")
    rx = [d for d in (dt.date(2024, 1, 1) + dt.timedelta(days=i) for i in range(366))
          if is_retrograde("Mercury", eph.julian_day(dt.datetime.combine(d, dt.time(12))))]
    spans, s = [], rx[0]
    for a, b in zip(rx, rx[1:] + [None]):
        if b is None or (b - a).days > 1:
            spans.append((str(s), str(a)))
            s = b
    print("Mercury retrograde 2024:", spans, "(published Apr 1-25, Aug 5-28, Nov 26-Dec 15)")
    rise, sset = sun_rise_set(dt.date(2024, 6, 21))
    print("KL 2024-06-21 sunrise/sunset MYT:", (rise + dt.timedelta(hours=8)).time(),
          (sset + dt.timedelta(hours=8)).time(), "(published 07:05 / 19:24)")
    p = panchanga(dt.datetime(2024, 1, 22, 7), dt.date(2024, 1, 22))
    print("2024-01-22 12:30 IST nakshatra:", p["nakshatra"], "(published Mrigashira), tithi", p["tithi"], "(Shukla Dwadashi = 12)")
    p = panchanga(dt.datetime(2023, 11, 12, 13), dt.date(2023, 11, 12))
    print("2023-11-12 evening (Diwali):", p["tithi"], p["nakshatra"], "(published Amavasya = 30, Swati)")
