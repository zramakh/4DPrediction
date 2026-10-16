# Is there a predictable pattern in Malaysian 4D results?

**Short answer: no usable one.** 18,038 draws (414,871 winning numbers) from
Magnum (1985–2026), Sports Toto (1992–2026) and Da Ma Cai (1992–2026) behave like
independent uniform draws in every way that could be bet on. The one real
anomaly, a digit bias in Magnum's draws, improves odds by roughly 5–12%. That is far short of
the ~56% improvement needed just to overcome the house edge, and no strategy
we backtested made money.

Reproduce with `python3 analysis/analyze.py` (numpy only; ~40 s). Full numbers
are in `analysis/results.json`.

## 1. Tests against "every number is an independent, uniform pick"

105 hypothesis tests were run. With that many tests, about 5 would come out at
p < 0.05 by pure chance; 12 did, and 4 survive Bonferroni correction. **All 4
are the same Magnum digit bias** (section 2).

| Question | Result |
|---|---|
| Are all 10,000 numbers equally likely? | Yes. Spread of hit counts per number matches pure chance almost exactly (SD 3.94 vs 3.96 expected for Magnum; 3.54 vs 3.55 Toto; 3.64 vs 3.63 Da Ma Cai). "Hot" and "cold" numbers are what randomness produces. |
| Are digits 0–9 equally likely in each position? | Toto and Da Ma Cai: yes. Magnum: no in some eras (section 2). |
| Digit sums, patterns (AABB, ABCD, …), number ranges | Match theory for all operators. |
| Does the day of week matter? | Only Magnum, and only because days are confounded with era (Mon/Thu/Fri draws were mostly in the biased 1985–94 period). |
| Month, day of month, numbers built from the date (DDMM, MMDD, YYYY) | No effect. |
| Do numbers repeat from the last 1, 2, 5 or 10 draws more or less than chance? | No. |
| Does the previous 1st prize predict the next (digit transitions, autocorrelation)? | No. One Toto lag-3 autocorrelation (r = +0.04) has raw p = 0.004 but p = 0.42 after correction. |
| Are the 23 numbers within one draw related to each other? | No. |
| Do operators' same-day results overlap, or does one predict another's next draw? | No. |

## 2. The one real signal: Magnum digit bias

Digit frequencies by position in Magnum are measurably uneven in two periods:

* **1985–1994:** strongly biased (e.g. digit 6 appeared 12–15% less than
  expected as the first digit). The bias was stable year to year (correlation
  between one year's deviations and the previous three years': r ≈ 0.6–0.8).
* **1995–2019:** no bias.
* **2020–2026:** a mild bias returns (per-year chi-square around 13 vs 9
  expected; year-to-year persistence r ≈ 0.4–0.7 for 2022–2025).

The most plausible cause is the physical draw equipment (balls or drums
changed over time). Sports Toto and Da Ma Cai show nothing comparable.

### How much is it worth?

A walk-forward model scores each number by the frequency of its four digits
over the previous 300 draws, using only past data:

| Magnum era | Top 100 picks | Top 1,000 picks | RM1 Big on top 10, each draw |
|---|---|---|---|
| 1985–1994 | 1.21× chance (z = 3.5) | 1.12× (z = 6.5) | returns RM0.87 |
| 1995–2019 | 0.95× | 0.99× | returns RM0.57 |
| 2020–2026 | 1.10× (z = 1.6) | 1.05× (z = 2.3) | returns RM0.54 |

Big Forecast pays about RM0.64 per RM1 for a random number, so a number has to
win ~1.56× as often as chance to break even. The real effect is 1.05–1.2× at
best, and even the most favourable historical period lost money.

### Deep dive: Magnum, 2019–2025 (`python3 analysis/magnum_bias.py`)

* **It is mainly a shortage of 7s.** Digit 7 was 6–9% under-represented in
  *every* position (overall 9.23% instead of 10%, z = −8.0), in all three
  prize tiers. 6, 8 and 9 ran slightly hot; 2 and 3 slightly cold. A
  same-digit effect across all four positions is the signature of the balls
  (e.g. the 7 balls in every drum differing slightly), not of chance.
* **It had a clear start and end.** A change-point analysis puts it at
  **2019-01-29 to 2025-11-05** (1,055 draws). Before and after, the draws are
  fair: 7 share 10.23% before, 10.18% after; after-period chi-square 41.6 vs ~36
  expected; the after-period pattern is unrelated to the old one (r = −0.05).
  That points to the equipment being replaced around November 2025. *The bias
  no longer exists.*
* **It was stable while it lasted** (pattern correlation r = 0.49 between the first
  and second halves), so it was genuinely predictable:

| Digit model fitted on 2019–2022, frozen | Top 100 | Top 1,000 | RM1 Big on top 10 |
|---|---|---|---|
| Tested on 2023 – Nov 2025 (bias active) | 1.07× | 1.10× (z = 3.4) | RM0.78 |
| Tested after Nov 2025 (bias gone) | 0.94× | 1.07× | RM0.12 |
| Hindsight, in-sample 2019–2025 (best case) | 1.17× | 1.13× | RM0.70 |

  Even with perfect hindsight, the best single number was only **1.20×** as
  likely as average (top-ranked: 8806, 6806, 1806, 9806, …), against the
  **1.56×** needed to break even. Avoiding every number containing a 7 raised the
  hit rate by 5% (68.96% of winners vs 65.61% of numbers) while the bias lasted,
  and by nothing afterwards.

## 3. Same date every year, moon phase and astrology

`python3 analysis/seasonal_astro.py` (~25 s). Sun and Moon positions come from
`analysis/ephemeris.py`, an implementation of Meeus' *Astronomical Algorithms*
validated against published moon phases (within ~2 minutes), solar ingresses,
Chinese New Year dates and leap-month festival dates. Draws are evaluated at
19:00 Malaysia time. 118 tests were run; 5 had raw p < 0.05 (about 6 expected
by chance) and **none survives correction**.

**Numbers recurring near the same date in different years.** For every number,
each pair of wins in different years within ±3 days of the same date was
counted, both on the Gregorian calendar and on the Chinese lunar calendar,
and compared with the count expected if numbers were random, given the real
draw dates.

| | Same calendar date | Same Chinese lunar date |
|---|---|---|
| Magnum | 22,963 vs 23,043 expected (z = −0.5) | 23,988 vs 24,035 (z = −0.3) |
| Sports Toto | 14,856 vs 14,763 (z = +0.8) | 15,490 vs 15,449 (z = +0.3) |
| Da Ma Cai | 16,061 vs 16,195 (z = −1.1) | 17,219 vs 16,902 (z = +2.4) |
| All three pooled | 160,166 vs 159,986 (z = +0.5) | 167,369 vs 167,055 (z = +0.8) |

The numbers that recur most (1024, 8231, 1841, 7748 and 3553, each with ~50
near-date repeats across all operators) are what the luckiest of 10,000 numbers
looks like by chance. Da Ma Cai's lunar z = +2.4 does not hold up: it fades
with wider windows (+0.3 at ±10 days), is absent in 1992–2005 (z = −0.1), and
is one of 118 tests. Predicting each draw from the numbers that won within ±3
days of the same date in earlier years gave 0.99–1.02× random for every
operator.

*Method note:* a first version used a "shift each year randomly" null and
showed a lunar effect at z = +6.9. That turned out to be the draw calendar
itself (e.g. draw breaks around Chinese New Year line up in lunar time every
year), not the numbers; the exact null above removes it.

**Moon phase, Moon sign, Sun sign, Chinese lunar month/day and Chinese
zodiac year.** For each grouping we tested whether digit frequencies differ
between groups (4 positions each), and whether the 100 numbers most frequent
in a group before 2010 stay frequent in that group from 2010 on:

* Moon phase, Moon sign, Sun sign, lunar month, lunar day: no digit effect for
  any operator (smallest p = 0.17), and group "hot numbers" won 0.95–1.04× as
  often as random afterwards (all |z| < 1.4).
* Chinese zodiac year: Magnum p = 0.006 on the first digit (0.67 after
  correction). This is the Magnum digit bias of section 2 showing through
  (zodiac years are year-level groups, and the bias changed by era), not an
  effect of the zodiac itself; its hot numbers did not carry over (1.05×,
  z = 1.2).
* Draws within ±1.5 days of a full or new moon show the same rates of
  repeated-digit numbers (e.g. 1123) and of recent repeats as other draws.

## 4. Vedic astrology

`python3 analysis/vedic_analysis.py` (~20 s), using `analysis/vedic.py`:
sidereal positions with the Lahiri ayanamsa, Mercury–Saturn from JPL's
approximate Keplerian elements, mean-node Rahu/Ketu, the panchanga (tithi,
paksha, nakshatra, yoga, karana, vara) and the hora lord from Kuala Lumpur
sunrise/sunset. Validated against published data: sidereal ingresses of Jupiter,
Saturn, Rahu, Mars and Venus (2022–2025) to within a day, Mercury's 2024
retrogrades, KL sunrise/sunset to the minute, and the nakshatra/tithi of
2024-01-22 (Mrigashira, Shukla Dwadashi) and Diwali 2023 (Amavasya, Swati).
Draws are evaluated at 19:00 MYT; since that is close to sunset, the hora lord
is mostly fixed by the weekday.

16 factors were tested (tithi, paksha, nakshatra, yoga, karana, vara lord, hora
lord, Moon and Sun rashi, rashis of Mars, Mercury, Venus, Jupiter, Saturn and
Rahu, Mercury retrograde), plus Vedic numerology. Magnum was also analysed
with its biased eras removed (section 2). 348 tests in total.

| Question | Result |
|---|---|
| Do digit frequencies differ by tithi, nakshatra, yoga, karana, paksha, Moon rashi or Mercury retrograde? | No: 3 of 84 tests below p = 0.05 for the other operators (4.2 expected by chance). |
| Do the 100 numbers most frequent in a group (e.g. Rohini nakshatra) before 2010 stay frequent in that group after 2010? | No: 0.90–1.12× random across all 16 factors and four datasets; the largest positive result (Mercury retrograde, Magnum fair periods, 1.12×, z = 2.4) is about the size expected for the best of 64 tries. |
| Numerology: does the ruling planet's number (Sun 1, Moon 2, Jupiter 3, Rahu 4, Mercury 5, Venus 6, Ketu 7, Saturn 8, Mars 9) appear more on days ruled by that planet? | No: for vara, hora and nakshatra lords it appears as a digit 9.93–10.06% of the time (10% expected) and as the digital root 11.03–11.26% (11.11% expected); all \|z\| ≤ 1.7. |
| Combined panchanga model (digit frequencies by nakshatra, tithi, hora and Moon rashi, learned before 2010) | Top 100 picks per draw: Magnum 0.99×, Sports Toto 1.06×, Da Ma Cai 1.04×, Magnum fair periods 1.03× random; none significant. |

Only 2 tests survive correction: Magnum's vara lord against the 1st and 3rd
digits. The vara lord is just the weekday, and this is the weekday/era
confound from section 1 (Monday and Thursday draws were almost all in Magnum's
biased 1985–94 era). With the biased eras removed it drops to p = 0.02 (not
significant).

Digit tests for slow-moving planets (Jupiter, Saturn, Rahu) come out below
p = 0.05 a little more often than 5% (5 of 36). That is not astrology: the
same tests on **arbitrary time blocks** of the same lengths (1–2.5 years) give
p < 0.05 in 10–12.5% of cases, because the draws drift slightly from year to
year as equipment changes. Short blocks (~30 days) give the nominal 3–6%.
Planet signs behave exactly like arbitrary calendar blocks, and their hot
numbers do not carry over (0 of 21 tests).

### KP (Krishnamurti Paddhati) numbers

`python3 analysis/kp_analysis.py` (~20 s), using `analysis/kp.py`: the
standard 249-sub table (nakshatras divided by Vimshottari proportions, split
at sign boundaries; self-checked to give 249 subs, #1 = Ketu/Ketu
0°00'–0°46'40"), the KP ayanamsa, and the Ascendant for Kuala Lumpur at 19:00
MYT (checked: at sunrise the Ascendant coincides with the Sun to within the
expected ~0.8°). For the Ascendant, Moon, Sun, Mercury, Venus, Mars, Jupiter,
Saturn, Rahu and Ketu we tested:

* **The KP number inside the winning numbers** (e.g. Moon at KP 119 → do
  numbers containing "119", or ending in 119, win more?): all 40
  body/operator combinations within chance (substring z from −2.5 to +2.3;
  last-3-digits z from −1.3 to +2.0).
* **Sign, star and sub lords' planet numbers as digits:** 9.9–10.1% for every
  body (10% expected). The one large value, Magnum's Saturn sign lord at
  z = +3.4, is the Magnum equipment bias again: during the 2019–2025 bias
  Saturn sat in its own signs and digit 8 ran hot. With those years removed it
  is z = +0.8.
* **Digit frequencies by star lord, sub lord, and Ascendant/Moon KP number:**
  no consistent effect.
* **Hot numbers per Ascendant / Moon KP number** (learned before 2010):
  Sports Toto 1.09–1.10× (z ≈ 2.4), but Magnum fair periods 0.85× (z = −3.1)
  and Da Ma Cai 0.92–1.08×. Effects that change sign between operators are
  noise.

560 tests: 30 with raw p < 0.05 (28 expected by chance), none significant
after correction.

## 5. Predictive models (walk-forward backtest)

Each strategy picked 23 numbers per draw using only earlier draws, over the
last 40% of each operator's history (2,191–2,731 draws). Hits are compared
with what random picking expects.

| Strategy | Magnum | Sports Toto | Da Ma Cai |
|---|---|---|---|
| Random picks | 1.05× | 0.99× | 1.10× |
| Hot numbers (all-time) | 1.04× | 1.05× | 1.00× |
| Hot numbers (last 100 draws) | 1.05× | 1.05× | 1.04× |
| Cold / overdue numbers | 0.99× | 0.87× | 0.97× |
| Repeat the last draw | 1.04× | 1.04× | 0.96× |
| Day-of-week hot numbers | 1.02× | 1.04× | 1.02× |
| Digit-frequency model | 1.01× | 1.07× | 0.87× |
| Digit Markov model (previous 1st prize) | 1.09× | 0.82× | 0.97× |
| Logistic regression (frequency, recency, gap features) | 1.08× | 1.01× | 0.94× |

None differs from random by more than |z| ≈ 2; random picking itself
landed between 0.99× and 1.10× from noise alone. Guessing each digit of the
next 1st prize: every method scored 9.7–10.4% against 10% for blind guessing.

## 6. Specific numbers under specific conditions (single and paired parameters)

Is there a condition, or a pair of conditions, under which a particular number
(e.g. 7345) or i-Box group (e.g. any order of 4458) wins unusually often?

* `analysis/almanac.py` computes **84 parameters** for every draw date at
  19:00 MYT. Its rules were checked against published almanac values
  (2024-02-10: Jia Chen day, Di mansion, "Full" officer, Bing Yin month;
  2000-01-01: Wu Wu day; Nine Star 2024 = 3 and Feb 2019 month = 2; 2024
  samvatsara Krodhi; 2023 Adhika Shravana). The Yellow/Black path day gods follow
  the standard Green Dragon rule but were not checked against an almanac.
  * *Chinese:* year animal, stem, element, yin/yang and 60-year pillar;
    lunar month, day and leap month; 24 solar terms; Ba Zi month branch, stem
    and pillar; day stem, branch, element and 60-day pillar; Na Yin (30) and
    its element; 19:00 hour stem; 12 Day Officers; 12 day gods and
    Yellow/Black path; 28 mansions; day-vs-year branch (Tai Sui) relation;
    year and month Nine Star.
  * *Vedic/KP:* tithi, paksha, nakshatra, pada, nakshatra lord, yoga,
    karana, hora lord; rashi and nakshatra of the Sun, Moon, Mars, Mercury,
    Venus, Jupiter, Saturn and Rahu; lagna rashi and nakshatra; Moon navamsa;
    retrograde and combust flags for Mercury to Saturn; planets in the Moon's
    sign; masa, adhika masa, ritu, ayana, samvatsara; KP star and sub lord
    and KP number of the Moon, Ascendant and Sun.
  * *Other:* weekday, month, day of month, 5-year era, tropical Moon and Sun
    sign, moon phase, prize tier.
  * Not included: choghadiya, Rahu kalam, gulika and vara lord (at 19:00
    these are fixed by the weekday or fall outside their periods), and the
    daily Nine Star.
* `analysis/conditional_extended.py` (~30 min on 4 cores) scans all 85
  parameters and all 3,570 pairs, for each operator and pooled. That is
  **4.2 million cells** (e.g. "Sports Toto, Rahu in Pushya & top-3 prizes"),
  each with 10,000 numbers and 715 i-Box groups. `analysis/conditional_numbers.py`
  is the same scan over 13 parameters. `analysis/conditional_checks.py` runs
  the follow-up checks below.

**Method.** Each number counts at most once per draw (published draws
occasionally repeat a number in two prize slots). The Magnum 2015-01-09
result, which repeats 22 of the 23 numbers of 2015-01-07 on the source site,
is excluded. The comparison is always with **shuffled dates**: every draw
keeps its numbers but gets the parameters of another date on which the same
operators drew. That keeps every real property of the draws (number and
digit biases, era drift) and only breaks the link to the conditions.
(Two earlier versions of this scan showed apparent clustering. Both were
artefacts: repeated numbers within one draw counting as recurrence, and
shuffles mixing dates with three operators' results and dates with one.)

**1. The strongest associations are what chance produces.**

| Operator | Condition | Value | Wins | Expected |
|---|---|---|---|---|
| Magnum | nakshatra lord Mercury & Rahu in Shatabhisha | 4835 | 6 | 0.09 |
| Sports Toto | Ren year & nakshatra lord Jupiter | 2444 | 7 | 0.17 |
| Da Ma Cai | Shatabhisha pada 2 & Venus not combust | 0924 | 6 | 0.10 |
| Sports Toto | Rahu in Pushya & top-3 prize | 3458 (any order) | 14 | 1.69 |
| Magnum | Geng month & Di mansion | 0558 (any order) | 12 | 1.46 |

Corrected for the search, every one is at p = 1.00. The shuffled-date data
gave an equally or more extreme best association in 6 of 10 shuffles for
numbers and 1 of 10 for i-Box groups.

**2. No parameter set makes winners cluster.** For each set we counted how
often the same number won in two different draws of the same cell, against
shuffled dates. Across 3,654 sets per operator, 27–73 sets reached z > 3 (a
shuffled copy of the data scored the same way gave 15–31). These sets
overlap heavily (most pairs share a parameter) and none carries over to later
years (point 3), so the difference is not a usable effect.

**3. Nothing replicates.** Each cell's top 10 numbers or groups were learned
from draws before 2012 and checked in the same cell from 2012 on, for every
set, against the same test with shuffled conditions:

| | Real conditions | Shuffled conditions |
|---|---|---|
| Single numbers (per operator / pooled) | 0.997–1.012× random | 0.985–1.006× |
| i-Box groups (per operator / pooled) | 1.000–1.046× | 1.005–1.039× |

Real and shuffled conditions give the same lift, so whatever small lift
exists comes from some groups being slightly common overall (largely the
Magnum digit bias), not from any condition. The 200 strongest number
associations found before 2012 won 69 times from 2012 on against 51.3
expected, but 53 of those wins come from a single number, 1024, which appears
in 13 of the 200 entries; without it, 16 vs 19.9. The 200 strongest i-Box
associations: 525 vs 531. Almost every headline association scored **zero**
afterwards (Sports Toto 2222 in any order with the Sun in Vishakha: 4 wins
before 2012, 0 after; Da Ma Cai 9732 with Hasta pada 1 and Mercury in Kanya:
4 before, 0 after).

**One genuine outlier, not tied to any condition: 1024.** It is the most
frequent number in the whole dataset: 79 wins against 41.5 expected, raised
for all three operators and in both halves of the data:

| | Before 2012 | From 2012 |
|---|---|---|
| Magnum | 22 (10.0 expected) | 13 (5.7) |
| Sports Toto | 12 (6.9) | 7 (5.7) |
| Da Ma Cai | 16 (7.5) | 9 (5.6) |

Even as the best of 10,000 numbers this is unlikely by chance (p ≈ 0.0014),
and it is the only one: the other nine most frequent numbers before 2012 won
135 times afterwards against 153 expected. Most of its wins are Special or
Consolation prizes (70 of 79). Two explanations are open: a fault in the
source data (4dmoon.com could not be reached from this environment to check
the original pages), or a real but unexplained effect. Either way it is about
one number, not about dates, weekdays or astrological conditions, and it
should be checked against the operators' official results before anything
is read into it.

## Conclusion

The draws are fair for practical purposes. Frequency, recency, "overdue",
date, weekday, sequence and cross-operator patterns carry no information about
future results. The Magnum digit bias is statistically real but tiny, and is
swamped by the ~36% house edge. A model built on this data cannot be expected
to win money; any picking method, including random, has the same expected
return.

### Method notes

* p-values use the Wilson–Hilferty chi-square approximation and normal
  approximations for counts; correction is Bonferroni over all 105 tests.
* Special slots shown as `----` on the source are excluded, so draws have
  20–23 numbers.
* Backtests are strictly walk-forward: the logistic model is fitted only on
  the first 60% of draws and every feature uses only earlier draws.
* Betting returns use the Big Forecast table (1st 2,500, 2nd 1,000, 3rd 500,
  Special 180, Consolation 60 per RM1). With only a few thousand draws per era,
  the returns are dominated by rare top-prize hits and are noisy.
