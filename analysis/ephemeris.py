"""Low-precision Sun and Moon ephemeris (Meeus, Astronomical Algorithms, ch. 25 & 47).

Accuracy is ~0.01 deg for the Sun and ~0.05 deg for the Moon over 1985-2030,
i.e. moon phases to within ~10 minutes, which is far finer than anything the
4D analysis needs. Longitudes are tropical, ecliptic of date (as in Western
astrology).

Run directly to self-check against published events.
"""

import datetime as dt
import functools
import math

ZODIAC = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
          "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
CHINESE_ZODIAC = ["Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake", "Horse", "Goat",
                  "Monkey", "Rooster", "Dog", "Pig"]
PHASES = ["New", "Waxing crescent", "First quarter", "Waxing gibbous",
          "Full", "Waning gibbous", "Last quarter", "Waning crescent"]

# (D, M, M', F, coefficient in 1e-6 deg) - largest terms of Meeus table 47.A
_MOON_TERMS = [
    (0, 0, 1, 0, 6288774), (2, 0, -1, 0, 1274027), (2, 0, 0, 0, 658314), (0, 0, 2, 0, 213618),
    (0, 1, 0, 0, -185116), (0, 0, 0, 2, -114332), (2, 0, -2, 0, 58793), (2, -1, -1, 0, 57066),
    (2, 0, 1, 0, 53322), (2, -1, 0, 0, 45758), (0, 1, -1, 0, -40923), (1, 0, 0, 0, -34720),
    (0, 1, 1, 0, -30383), (2, 0, 0, -2, 15327), (0, 0, 1, 2, -12528), (0, 0, 1, -2, 10980),
    (4, 0, -1, 0, 10675), (0, 0, 3, 0, 10034), (4, 0, -2, 0, 8548), (2, 1, -1, 0, -7888),
    (2, 1, 0, 0, -6766), (1, 0, -1, 0, -5163), (1, 1, 0, 0, 4987), (2, -1, 1, 0, 4036),
    (2, 0, 2, 0, 3994), (4, 0, 0, 0, 3861), (2, 0, -3, 0, 3665), (0, 1, -2, 0, -2689),
    (2, 0, -1, 2, -2602), (2, -1, -2, 0, 2390), (1, 0, 1, 0, -2348), (2, -2, 0, 0, 2236),
    (0, 1, 2, 0, -2120), (0, 2, 0, 0, -2069), (2, -2, -1, 0, 2048), (2, 0, 1, -2, -1773),
    (2, 0, 0, 2, -1595), (4, -1, -1, 0, 1215), (0, 0, 2, 2, -1110), (3, 0, -1, 0, -892),
    (2, 1, 1, 0, -810), (4, -1, -2, 0, 759), (0, 2, -1, 0, -713), (2, 2, -1, 0, -700),
]


def julian_day(t):
    """datetime (naive = UTC) -> Julian Day."""
    if t.tzinfo is not None:
        t = t.astimezone(dt.timezone.utc).replace(tzinfo=None)
    return (t - dt.datetime(2000, 1, 1, 12)).total_seconds() / 86400 + 2451545.0


def sun_longitude(jd):
    T = (jd - 2451545.0) / 36525
    L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T
    M = math.radians(357.52911 + 35999.05029 * T - 0.0001537 * T * T)
    C = ((1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(M)
         + (0.019993 - 0.000101 * T) * math.sin(2 * M) + 0.000289 * math.sin(3 * M))
    omega = math.radians(125.04 - 1934.136 * T)
    return (L0 + C - 0.00569 - 0.00478 * math.sin(omega)) % 360


def moon_longitude(jd):
    T = (jd - 2451545.0) / 36525
    Lp = 218.3164477 + 481267.88123421 * T - 0.0015786 * T ** 2 + T ** 3 / 538841 - T ** 4 / 65194000
    D = 297.8501921 + 445267.1114034 * T - 0.0018819 * T ** 2 + T ** 3 / 545868 - T ** 4 / 113065000
    M = 357.5291092 + 35999.0502909 * T - 0.0001536 * T ** 2 + T ** 3 / 24490000
    Mp = 134.9633964 + 477198.8675055 * T + 0.0087414 * T ** 2 + T ** 3 / 69699 - T ** 4 / 14712000
    F = 93.2720950 + 483202.0175233 * T - 0.0036539 * T ** 2 - T ** 3 / 3526000 + T ** 4 / 863310000
    E = 1 - 0.002516 * T - 0.0000074 * T * T
    s = 0.0
    for d, m, mp, f, c in _MOON_TERMS:
        arg = math.radians(d * D + m * M + mp * Mp + f * F)
        s += c * (E ** abs(m)) * math.sin(arg)
    A1 = math.radians(119.75 + 131.849 * T)
    A2 = math.radians(53.09 + 479264.290 * T)
    s += 3958 * math.sin(A1) + 1962 * math.sin(math.radians(Lp - F)) + 318 * math.sin(A2)
    omega = math.radians(125.04452 - 1934.136261 * T)
    return (Lp + s / 1e6 - 0.00478 * math.sin(omega)) % 360


def elongation(jd):
    """Moon minus Sun longitude: 0 = new moon, 180 = full moon."""
    return (moon_longitude(jd) - sun_longitude(jd)) % 360


def new_moon_before(jd):
    """JD of the last new moon at or before jd."""
    t = jd - elongation(jd) / 12.19  # mean motion ~12.19 deg/day
    for _ in range(6):
        e = (elongation(t) + 180) % 360 - 180
        t -= e / 12.19
    if t > jd + 1e-6:
        t = new_moon_before(t - 25)
    return t


@functools.lru_cache(maxsize=None)
def chinese_new_year(year):
    """Gregorian date of Chinese New Year: the second new moon (in China,
    UTC+8) after the December solstice of the previous year. Correct for every
    year 1985-2030 (no leap 11th/12th month falls in that range)."""
    jd = julian_day(dt.datetime(year - 1, 12, 15))
    while abs(((sun_longitude(jd) - 270) + 180) % 360 - 180) > 1e-5:  # solstice
        jd -= (((sun_longitude(jd) - 270) + 180) % 360 - 180) / 0.9856
    # Walk forward new moon by new moon (each is 29.5 days apart, so the last
    # new moon before nm + 35 days is the next one), comparing China dates.
    solstice_day = _china_date(jd)
    nm = new_moon_before(jd)
    moons = []
    while len(moons) < 2:
        nm = new_moon_before(nm + 35)
        if _china_date(nm) > solstice_day:
            moons.append(_china_date(nm))
    return moons[1]


def _china_midnight_jd(day):
    return julian_day(dt.datetime.combine(day, dt.time())) - 8 / 24


def _has_major_term(start, end):
    """True if the Sun crosses a multiple of 30 deg (a zhongqi) between China
    midnights of `start` and `end` (the next month's first day)."""
    a = sun_longitude(_china_midnight_jd(start))
    b = sun_longitude(_china_midnight_jd(end))
    return int(a // 30) != int(b // 30)


def lunar_date(day):
    """Chinese lunar (month, day, is_leap) for a Gregorian date. A month with no
    major solar term is the leap month and repeats the previous month number
    (the standard rule; exact for 1985-2030)."""
    cny = chinese_new_year(day.year)
    if day < cny:
        cny = chinese_new_year(day.year - 1)
    start, month, leap = cny, 1, False
    while True:
        nxt = _china_date(new_moon_before(_china_midnight_jd(start) + 35))
        if nxt > day:
            return month, (day - start).days + 1, leap
        start = nxt
        leap = not _has_major_term(start, _china_date(new_moon_before(_china_midnight_jd(start) + 35)))
        if not leap:
            month += 1


def _china_date(jd):
    return (dt.datetime(2000, 1, 1, 12) + dt.timedelta(days=jd - 2451545.0, hours=8)).date()


def describe(t):
    """Astronomical / astrological context for a UTC datetime."""
    jd = julian_day(t)
    sun, moon = sun_longitude(jd), moon_longitude(jd)
    elong = (moon - sun) % 360
    return {
        "sun_sign": ZODIAC[int(sun // 30)],
        "moon_sign": ZODIAC[int(moon // 30)],
        "elongation": elong,
        "phase": PHASES[int(((elong + 22.5) % 360) // 45)],
        "illumination": (1 - math.cos(math.radians(elong))) / 2,
        "moon_age_days": jd - new_moon_before(jd),
    }


if __name__ == "__main__":
    # Published events (UTC), e.g. timeanddate.com / USNO.
    checks = [
        ("new moon", dt.datetime(2025, 1, 29, 12, 36), 0),
        ("full moon", dt.datetime(2024, 1, 25, 17, 54), 180),
        ("new moon", dt.datetime(2000, 1, 6, 18, 14), 0),
        ("full moon", dt.datetime(1990, 1, 11, 4, 57), 180),
        ("first quarter", dt.datetime(2026, 1, 26, 4, 47), 90),
    ]
    for name, t, target in checks:
        err = (elongation(julian_day(t)) - target + 180) % 360 - 180
        print(f"{name:<14} {t}  error {err:+.3f} deg (~{err / 12.19 * 24 * 60:+.0f} min)")
    for t, target in ((dt.datetime(2025, 3, 20, 9, 1), 0), (dt.datetime(2024, 7, 22, 8, 44), 120)):
        print(f"sun ingress    {t}  error {(sun_longitude(julian_day(t)) - target + 180) % 360 - 180:+.4f} deg")
    known_cny = {1985: "02-20", 1990: "01-27", 1996: "02-19", 2000: "02-05", 2004: "01-22",
                 2010: "02-14", 2015: "02-19", 2020: "01-25", 2021: "02-12", 2023: "01-22",
                 2024: "02-10", 2025: "01-29", 2026: "02-17"}
    bad = {y: (str(chinese_new_year(y)), d) for y, d in known_cny.items() if str(chinese_new_year(y))[5:] != d}
    print("Chinese New Year check:", "all correct" if not bad else bad)
