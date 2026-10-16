"""Every Chinese almanac and Vedic/KP parameter of a 4D draw date that can be
computed from the date and the 19:00 Malaysia draw time.

Chinese (Tong Shu / Ba Zi)
  * year: animal, heavenly stem, element, yin/yang, 60-year pillar (from
    Chinese New Year); Ba Zi year pillar from Li Chun for the month pillar
  * lunar month, lunar day, leap month
  * 24 solar terms; Ba Zi month branch, stem and pillar
  * day stem, branch, element and 60-day pillar; Na Yin (30) and its element
  * 19:00 hour (Xu) stem
  * 12 Day Officers (Jian Chu), 12 day gods and Yellow/Black path day,
    28 lunar mansions, day branch vs year branch (Tai Sui) relation
  * Nine Star (flying star) of the year and the month
Vedic
  * panchanga: tithi, paksha, nakshatra, pada, nakshatra lord, yoga, karana,
    hora lord (vara lord equals the weekday)
  * rashi of Sun, Moon, Mars, Mercury, Venus, Jupiter, Saturn, Rahu (Ketu is
    always opposite Rahu) and nakshatra of each
  * Lagna (Ascendant at Kuala Lumpur) rashi and nakshatra, Moon navamsa
  * retrograde and combust flags for Mercury..Saturn, planets sharing the
    Moon's rashi
  * amanta lunar month (masa) and adhika masa, ritu, ayana, samvatsara
KP: star and sub lords and KP number (1-249) of the Moon, Ascendant and Sun

Self-check against published almanac values: python3 analysis/almanac.py
"""

import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ephemeris as eph  # noqa: E402
import kp  # noqa: E402
import vedic  # noqa: E402

STEMS = ["Jia", "Yi", "Bing", "Ding", "Wu", "Ji", "Geng", "Xin", "Ren", "Gui"]
BRANCHES = ["Zi", "Chou", "Yin", "Mao", "Chen", "Si", "Wu", "Wei", "Shen", "You", "Xu", "Hai"]
STEM_ELEMENT = ["Wood", "Wood", "Fire", "Fire", "Earth", "Earth", "Metal", "Metal", "Water", "Water"]
NAYIN_ELEMENT = ["Metal", "Fire", "Wood", "Earth", "Metal", "Fire", "Water", "Earth", "Metal", "Wood",
                 "Water", "Earth", "Fire", "Wood", "Water", "Metal", "Fire", "Wood", "Earth", "Metal",
                 "Fire", "Water", "Earth", "Metal", "Wood", "Water", "Earth", "Fire", "Wood", "Water"]
OFFICERS = ["Establish", "Remove", "Full", "Balance", "Stable", "Initiate", "Destruction",
            "Danger", "Success", "Receive", "Open", "Close"]
DAY_GODS = ["Green Dragon", "Bright Hall", "Heavenly Punishment", "Vermilion Bird", "Golden Coffer",
            "Heavenly Virtue", "White Tiger", "Jade Hall", "Heavenly Prison", "Black Tortoise",
            "Life Governor", "Grappling Hook"]
YELLOW_PATH = {0, 1, 4, 5, 7, 10}
MANSIONS = ["Jiao", "Kang", "Di", "Fang", "Xin", "Wei", "Ji", "Dou", "Niu", "Nu", "Xu", "Wei2",
            "Shi", "Bi", "Kui", "Lou", "Wei3", "Mao", "Bi2", "Zi", "Shen", "Jing", "Gui", "Liu",
            "Xing", "Zhang", "Yi", "Zhen"]
SOLAR_TERMS = ["Chunfen", "Qingming", "Guyu", "Lixia", "Xiaoman", "Mangzhong", "Xiazhi", "Xiaoshu",
               "Dashu", "Liqiu", "Chushu", "Bailu", "Qiufen", "Hanlu", "Shuangjiang", "Lidong",
               "Xiaoxue", "Daxue", "Dongzhi", "Xiaohan", "Dahan", "Lichun", "Yushui", "Jingzhe"]
MASAS = ["Chaitra", "Vaishakha", "Jyeshtha", "Ashadha", "Shravana", "Bhadrapada", "Ashvin",
         "Kartika", "Margashirsha", "Pausha", "Magha", "Phalguna"]
RITUS = ["Vasanta", "Grishma", "Varsha", "Sharad", "Hemanta", "Shishira"]
PLANETS = ["Sun", "Mars", "Mercury", "Venus", "Jupiter", "Saturn", "Rahu"]
COMBUST_ORB = {"Mercury": 14, "Venus": 10, "Mars": 17, "Jupiter": 11, "Saturn": 15}
NAK = 360 / 27
# 2024-02-10 is a Di mansion day (published almanacs); its Julian Day Number
MANSION_REF_JDN, MANSION_REF = 2460351, 2


def jdn(day):
    return day.toordinal() + 1721425


def branch_relation(d, y):
    if d == y:
        return "same"
    if (d - y) % 12 == 6:
        return "clash"
    if (d + y) % 12 == 1:
        return "six harmony"
    if (d + y) % 12 == 7:
        return "harm"
    if (d - y) % 12 in (4, 8):
        return "trine"
    return "other"


def chinese(day, sun_tropical):
    cny = eph.chinese_new_year(day.year)
    ly = day.year if day >= cny else day.year - 1
    lm, ld, leap = eph.lunar_date(day)
    # Ba Zi: months start at the jie terms, the first (Yin) month at Li Chun (Sun 315 deg)
    m = int(((sun_tropical - 315) % 360) // 30)
    by = day.year - (1 if (day.month <= 2 and m >= 10) else 0)
    y_stem = (by - 4) % 10
    m_branch = (m + 2) % 12
    m_stem = ((y_stem % 5) * 2 + 2 + m) % 10
    d_ix = (jdn(day) - 11) % 60
    d_stem, d_branch = d_ix % 10, d_ix % 12
    god = (d_branch - ((m_branch - 2) % 6) * 2) % 12
    year_group = {0: 8, 3: 8, 6: 8, 9: 8, 4: 5, 10: 5, 1: 5, 7: 5}.get((by - 4) % 12, 2)
    lunar_year_ix = (ly - 4) % 60
    return {
        "year_animal": eph.CHINESE_ZODIAC[lunar_year_ix % 12],
        "year_stem": STEMS[lunar_year_ix % 10],
        "year_element": STEM_ELEMENT[lunar_year_ix % 10],
        "year_yinyang": "Yang" if lunar_year_ix % 2 == 0 else "Yin",
        "year_pillar": STEMS[lunar_year_ix % 10] + " " + BRANCHES[lunar_year_ix % 12],
        "lunar_month": lm,
        "lunar_day": ld,
        "lunar_leap_month": leap,
        "solar_term": SOLAR_TERMS[int(sun_tropical // 15)],
        "month_branch": BRANCHES[m_branch],
        "month_stem": STEMS[m_stem],
        "month_pillar": STEMS[m_stem] + " " + BRANCHES[m_branch],
        "day_stem": STEMS[d_stem],
        "day_branch": BRANCHES[d_branch],
        "day_element": STEM_ELEMENT[d_stem],
        "day_pillar": STEMS[d_stem] + " " + BRANCHES[d_branch],
        "nayin": d_ix // 2,
        "nayin_element": NAYIN_ELEMENT[d_ix // 2],
        "hour_stem_19h": STEMS[((d_stem % 5) * 2 + 10) % 10],
        "day_officer": OFFICERS[(d_branch - m_branch) % 12],
        "day_god": DAY_GODS[god],
        "yellow_black_path": "Yellow" if god in YELLOW_PATH else "Black",
        "mansion_28": MANSIONS[(jdn(day) - MANSION_REF_JDN + MANSION_REF) % 28],
        "day_vs_year_branch": branch_relation(d_branch, lunar_year_ix % 12),
        "nine_star_year": 1 + (2026 - by) % 9,
        "nine_star_month": 1 + (year_group - 1 - m) % 9,
    }


def vedic_factors(t_utc, day, sun_tropical):
    jd = eph.julian_day(t_utc)
    p = vedic.panchanga(t_utc, day)
    sid = {b: vedic.sidereal(b, jd) for b in ["Moon"] + PLANETS}
    out = {k: p[k] for k in ("tithi", "paksha", "nakshatra", "nakshatra_lord", "yoga", "karana",
                             "hora_lord", "moon_rashi")}
    out["nakshatra_pada"] = f"{p['nakshatra']} {p['pada']}"
    for b in PLANETS:
        out[f"{b.lower()}_rashi"] = vedic.RASHIS[int(sid[b] // 30)]
        out[f"{b.lower()}_nakshatra"] = vedic.NAKSHATRAS[int(sid[b] // NAK)]
    lagna = (kp.ascendant_tropical(jd) - vedic.ayanamsa(jd)) % 360
    out["lagna_rashi"] = vedic.RASHIS[int(lagna // 30)]
    out["lagna_nakshatra"] = vedic.NAKSHATRAS[int(lagna // NAK)]
    out["moon_navamsa"] = vedic.RASHIS[int(sid["Moon"] * 9 // 30) % 12]
    for b, orb in COMBUST_ORB.items():
        out[f"{b.lower()}_retrograde"] = vedic.is_retrograde(b, jd)
        out[f"{b.lower()}_combust"] = abs((sid[b] - sid["Sun"] + 180) % 360 - 180) < orb
    moon_r = int(sid["Moon"] // 30)
    out["planets_with_moon"] = sum(int(sid[b] // 30) == moon_r for b in PLANETS) + \
        (int(((sid["Rahu"] + 180) % 360) // 30) == moon_r)
    nm = eph.new_moon_before(jd)
    nxt = eph.new_moon_before(nm + 35)
    r0, r1 = int(vedic.sidereal("Sun", nm) // 30), int(vedic.sidereal("Sun", nxt) // 30)
    masa = (r0 + 1) % 12
    out["masa"] = MASAS[masa]
    out["adhika_masa"] = r0 == r1
    out["ritu"] = RITUS[masa // 2]
    out["ayana"] = "Uttarayana" if (sun_tropical >= 270 or sun_tropical < 90) else "Dakshinayana"
    vy = day.year - (1 if (masa >= 9 and day.month <= 5) else 0)
    out["samvatsara"] = 1 + (vy - 1987) % 60  # 1987-88 = Prabhava (1)
    c = kp.chart(t_utc)
    for b in ("Moon", "Ascendant", "Sun"):
        tag = "asc" if b == "Ascendant" else b.lower()
        out[f"kp_{tag}_star_lord"] = c[b]["star_lord"]
        out[f"kp_{tag}_sub_lord"] = c[b]["sub_lord"]
        out[f"kp_{tag}_number"] = c[b]["kp"]
    return out


def factors(date):
    """All Chinese and Vedic/KP parameters for a draw on `date` (YYYY-MM-DD) at 19:00 MYT."""
    day = dt.date.fromisoformat(date)
    t = dt.datetime.combine(day, dt.time(11))
    sun = eph.sun_longitude(eph.julian_day(t))
    return {**chinese(day, sun), **vedic_factors(t, day, sun)}


if __name__ == "__main__":
    f = factors("2024-02-10")
    print("2024-02-10:", f["day_pillar"], f["mansion_28"], f["day_officer"], f["year_pillar"],
          f["month_pillar"], "(published: Jia Chen day, Di mansion, Full day, Jia Chen year, Bing Yin month)")
    print("2019-02-10 month star:", factors("2019-02-10")["nine_star_month"], "(published 2)",
          "| 2024 year star:", factors("2024-06-01")["nine_star_year"], "(published 3)",
          "| 2000-01-01 day pillar:", factors("2000-01-01")["day_pillar"], "(published Wu Wu)")
    print("2024-04-15 masa/samvatsara:", factors("2024-04-15")["masa"], factors("2024-04-15")["samvatsara"],
          "(published Chaitra, Krodhi = 38)")
    print("2023-08-01 adhika masa:", factors("2023-08-01")["adhika_masa"], "(published: Adhika Shravana 2023)")
    print({k: v for k, v in factors("2026-10-16").items()})
