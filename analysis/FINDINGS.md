# Findings: can Vedic / Chinese almanac parameters predict Malaysian 4D?

Data: Magnum (from 1985), Sports Toto and Da Ma Cai (from 1992), all 23 prizes per
draw, up to 17 Oct 2026. Parameters: 78 Vedic, KP and Chinese almanac values per
draw date at 19:00 MYT (`almanac.py`, `astro_model.py`).

**Short answer: no parameter, pair of parameters, or model has shown an edge that
holds up on draws it was not chosen on.** Everything tested lands at chance once
selection is accounted for. Even the best lead would return about 72% of stakes.

## How things were tested

- Train on earlier draws, test on later ones (validation 2012-2017, test
  2018-2026; the last 5 draws, 4-14 Oct 2026, held out completely).
- Chance levels matched to the number of winners per day and the gap between days.
- Multiple testing: Bonferroni correction, and the whole scan rerun on circularly
  shifted parameter calendars (shifted by at least a year). That keeps every natural
  rhythm but breaks any real link, so it shows what the best of thousands of tests
  looks like by luck.
- Walk-forward: choose on 1985-2011, score on 2012-2026.

## What was tried (all at chance)

| Approach | Scripts |
|---|---|
| Number frequency given a parameter value (single / pair / triple) | `conditional_numbers.py`, `conditional_extended.py`, `pairs_test.py` |
| Vedic-only / Chinese-only / combined formulas, frozen and forward-tested | `predictive_model.py`, `astro_model.py`, `forward_log.csv` |
| Manual formula (spreadsheet) | `manual_formula.py`, `manual_formula.xlsx` (1.02x, chance) |
| Non-linear models: gradient boosting, digit models, kNN of similar days, softmax, ensembles | `ml_model.py`, `digit_models.py` |
| Change-point, autoregression, hazard, neural net, number shape | `new_models.py` |
| S1 (hot) / S2 (cold) positional digits, 16 numbers, single / pair / triple parameters | `strategies_test.py`, `s12_combos.py` |
| 1st prize vs cold digits | `first_prize_test.py` |
| Same number repeating when a parameter value recurs (single, pair) | `recurrence_test.py`, `recurrence_pairs.py`, `recurrence_pairs_null.py` |
| Same, as Straight / Reverse / i-Box | `recurrence_perm.py` |
| S1 / S2 picks from earlier same-value days, Straight / Reverse / i-Box | `recurrence_s12.py`, `recurrence_s12_forward.py` |
| S3: hottest + coldest digit per position, 16 numbers, single / pair parameters | `recurrence_s3.py` |
| Rank pairs: 2nd hottest + 2nd coldest, 3rd + 3rd, 4th + 4th, 5th + 6th (and S3 again) | `recurrence_rankpairs.py` |
| D9 navamsa family: navamsa sign and vargottama of 9 bodies, alone, in pairs and with all other parameters; tests A-D above | `navamsa_family.py` |
| Other divisional charts D2-D60 (14 charts x 9 bodies), alone and in pairs within each chart; tests A-D | `divisional_charts.py` |
| Mei Hua Yi Shu (time casting), Da Liu Ren (7 pm plate, transmissions, generals), Tai Yi day cycles (72/24/18/360); tests A-D plus direct number test | `chinese_divination.py` |
| Every analysis (A-D) on singles and pairs, separately for Magnum, Sports Toto, Da Ma Cai | `per_operator.py` |
| i-Box by pick pattern (ABCD / AABC / AABB / AAAB / AAAA), all picks columns, pooled and per operator | `pattern_ibox.py` |
| Whole-number hot / cold (16 numbers that won most / least on earlier same-value days) | `whole_number_test.py` |
| Exact positions: longitudes, angles between planets, aspects, position within sign | `continuous_astro.py` |
| Same, with 1-81 picks | `recurrence_s12_k.py` |

Key recurrence results:
- Single parameters: best Day element x1.002 (corrected p 0.89).
- Pairs (3,003): best z +3.26, same as shifted calendars (+3.12 average); "next
  same-value day" version below chance.
- Straight / Reverse / i-Box: only Reverse, Hora lord or Weekday x Month stem, beat
  9 of 10 shifted scans, at x1.009 (too small to use).
- S1/S2 picks, all 108 combinations of strategy, version, match type and pick
  amount: forward mean z -0.03 vs shifted +0.02; 14 combinations beat all shifts
  against about 18 expected by chance.

## Ranked leads (17 Oct 2026)

| Rank | Lead | Evidence | Problem |
|---|---|---|---|
| 1 | Mercury nakshatra x Venus rashi, S1 from all earlier same-value days, Straight, 16 numbers | #1 pick on 1985-2011, then x1.13 (z +2.12) on 2012-2026; beat 98.5% of 200 shifted calendars | Best of 12 columns, so about 1-in-5 luck; mostly Magnum; faded since 2019 (x1.03); related parameters show nothing (`s12_family.py`); no specific nakshatra or rashi drives it (`s12_lead_cells.py`); other pick counts don't confirm it (`s12_lead_k.py`) |
| 2 | Karana x Day pillar, S1 from previous same-value day, i-Box | Chosen before 2012, x1.04 (z +2.67) after | Was 4th, small gain |
| 3 | S1/S2 pairs and triples positive in both 2012-17 and 2018-26 (e.g. Mars nakshatra x Mars rashi x Mercury combust) | Positive in two periods | Chosen out of thousands using both periods; 0 hits in held-out 5 draws |
| 4 | Cold number, no parameters | 5 first prizes 2012-2026 vs 0.74 expected | 0 in 1995-2011; no digit-level mechanism |
| 5 | 1024 Magnum Big | RM1.64 per RM1 since 2012 | One number picked after the fact |
| - | Magnum digit bias 2019-2025 | The only clearly real deviation | It ended |

Expected performance of lead 1 if its 2012-2026 rate held: about 0.12 hits per day
(all 3 operators combined, so about 1 hit every 8 days), against 0.11 by chance. At
RM1 Big on 16 numbers x 3 operators (RM48 per draw) that returns about 72% of
stakes, against 64% for random numbers.

## Most consistent leads (picks rebuilt before every draw; `yearly_consistency.py`)

Candidates = the ~210 tests per run chosen on 1985-2011 draws only; count of years
2012-2026 above chance. Correction: earlier this file gave Karana x Day pillar about a
3% chance of luck; allowing properly for the 210 candidates searched it is about 20%.

| Run | Average good years real / shifted | 12+ good years real / shifted | Best real / shifted calendars as high | Most consistent |
|---|---|---|---|---|
| Pooled | 7.34 / 7.26 | 2 / 3.3 | 14 / 4 of 20 | Karana x Day pillar, S1 (b) i-Box: 14/15, x1.04 |
| Magnum | 7.45 / 7.25 | 5 / 2.5 | 13 / 7 of 20 | Jupiter retrograde x KP Asc sub lord, 4+7 (b) Straight: 13/15, x1.36 |
| Sports Toto | 7.25 / 7.18 | 2 / 2.7 | 12 / 20 of 20 | Lunar month x Day element, S2 (b) i-Box: 12/15, x1.07 |
| Da Ma Cai | 7.19 / 7.16 | 4 / 2.7 | 12 / 19 of 20 | Ayana x KP Asc star lord, 1+10 (a) Reverse: 12/15, x1.21 |

No run is more consistent than chance as a whole. Magnum has the most candidates with
12+ good years (5 vs 2.5) and the strongest single candidate (x1.36), still within the
range of the shifted calendars.

## Lead: Karana x Day pillar, two-pair picks only, Small i-Box (`karana_profit.py`)

From Karana x Day pillar's 16 picks (S1 from the previous same-value day), bet only the
numbers with two pairs (6 arrangements, e.g. 3311, 7744) as Small i-Box on all 3
operators. i-Box matches x1.42 before 2012 and x1.26 in 2012-2026; Small i-Box return
105% and 103%. Caveat: it rests on 8 top-3 matches in 2012-2026 against ~5.7 by chance
(about a 1-in-4 chance by luck), and such picks are rare (about 0.6 per draw).
Last 5 draws: two-pair picks only on 11 Oct (6116) and 18 Oct (9696), no matches.
24 Oct: no two-pair picks (Garaja x Xin Wei, from 23 Jan 2021).

## Karana x Day pillar family (`karana_family.py`)

Scored with the lead's method (S1 from the previous same-value day, i-Box). The Day
pillar side carries it: Day pillar x any other parameter averages z +0.43 after 2012
(shifted calendars -0.17, 1 of 20 as high; 53 of 76 above chance; 8.3 good years vs 7.2),
Panchanga x Chinese day +0.30 (0 of 20 as high). Karana x any other does not (-0.31 vs
-0.21). Halves alone: Day pillar +0.71, Karana -0.87. No relative chosen before 2012 beat
the lead after 2012 (best: Yoga x Day pillar, z +1.09). Only the lead's own method works
well; across its 42 versions the mean z after 2012 is -0.18.

## Karana x Day pillar: nine further checks (`karana_tests.py`, `karana_singapore.py`)

| # | Check | Result | Reading |
|---|---|---|---|
| 1 | Other game: Singapore 4D, 5,508 draws 1986-2026 (`data/singapore4d.csv`) | z before 2012 -0.57, 2012-2026 -1.60 (x0.956), 6/15 good years; 194 of 200 shifted calendars as high; rank 2,958 of 3,081 tests | **Fails.** The Malaysian top 20 average -0.33 on Singapore, the same as all tests (-0.31). Sabah 88, Sandakan, CashSweep and Grand Dragon: no bulk history found |
| 2 | Karana shuffled within each Day pillar, 200 times | shuffles: z before +0.18, after +0.09; 0/200 as good before, 1/200 after, 0/200 as many good years | The exact Karana split matters in Malaysia, but a lead picked as one of the best of 3,081 tests will beat random splits anyway |
| 3 | Edge over time | excess grows steadily from 1987 (+376 hits by 2026); 2012-2026 x1.040, 95% range x1.025-x1.059 resampling years; 2012-18 x1.046, 2019-26 x1.035 | Steady, slightly fading; no single lucky year |
| 4 | Source age | median 660 days back; 2012-2026 x1.07 (0-120 days), x1.07 (120-240), x1.05 (240-420), x1.08 (420-720), x1.03 (720-1200), x1.01 (1200+) | Older sources are a little weaker; the counts are small |
| 5 | Source moved 1-3 draw days (same age, other cell) | pooled x1.010 before and after (z +1.85 / +1.61), 10/15 years; true source x1.033 / x1.040 | Recent draws help a little in general; the same-cell source does 3-4 times better |
| 6 | Karana at sunrise 07:00 / 19:30 | sunrise z +1.81 / +2.27, 10/15; 19:30 +1.92 / +2.44, 11/15; 19:00 +2.52 / +2.72, 14/15 | 19:00 (draw time) is best; sunrise Karana is the previous Karana on most days, so it splits the days almost the same way |
| 7 | Source subsets | top-3 only +0.39 / +1.06; Specials -0.30 after; Consolations -0.08 after; Magnum only +1.41 after (12/15); Toto +0.23; DMC -0.52 | Needs all 69 numbers; no tier or operator carries it |
| 8 | Pick construction | grid 16 (lead) best; 81 grid -0.59 after; ranked top 4/8/16/32 +0.44 / +0.93 / +0.68 / +0.18 | Only the 16-number grid works, a sign the lead is fitted to its exact form |
| 9 | Bankroll 2012-2026, RM1 per pick per operator | all 16 Big i-Box: stake RM117,168, return 68.2% (random 63.7%, lead beats 196/200), worst drawdown RM37,524, longest losing run 35 draws. Two-pair only: Big 97.2% (beats 174/200), Small 102.9% (+RM93 on RM3,157; 8 winning days in 883; losing run 350 draws; beats 169/200) | Loses money on all 16. Two-pair Small i-Box is break-even and comes from 8 wins |

Overall: in Malaysia the lead is steady, but it is tied to one exact form (Karana at 19:00,
grid 16, all 69 numbers, same-cell source). It does not carry over to Singapore 4D, where
it ranks near the bottom. That points to a Malaysian-data fit and not a real astrological
effect. Bet on it only as entertainment.

## Offset ("lag") and lunar-date rules (`lag_rule.py`)

Source = the previous same-value day moved by k calendar days (k = -7..+7, +-14, +-28,
+-30), for all 3,081 single / pair tests, S1 / S2 x Straight / Reverse / i-Box, against 6
shifted calendars. Also the lunar date rule (same lunar month + day in an earlier year,
with the same offsets) and plain lags with no parameter (source = the draw exactly 1-10,
14, 21, 28-30, 59, 60, 354, 355, 364, 365, 384 days before).

- Walk-forward (top 5 tests chosen before 2012, scored 2012-2026): mean z +0.12 vs +-0.02
  shifted; 22 of 126 offset x column cells beat every shift, about 18 expected by chance.
  No offset stands out once you allow for having tried 21 of them (best: k = +1, +0.71
  above the shifts).
- Plain lags and the lunar date rule: all within chance (|z| < 2.7, mixed signs).
- The largest single z values (e.g. ayana x year_pillar at k = +1, S2 Straight, z +6.6)
  come from very few scored days (ayana at k = +1: 12 days, 7 hits vs well under 1
  expected) and are not leads.

## i-Box by number pattern (`pattern_ibox.py`)

No pattern beats chance in general (average over all tests equals the shifted calendars,
pooled and per operator). Pooled two-pair (AABB) forward picks lean positive (+0.29 vs
+0.19, 5 of 14 columns beat every shift vs ~2). Single-test z values for AABB / AAAB are
inflated because one winning number can match several same-digit picks (e.g. 7227 matches
7227, 7272, 7722): Da Ma Cai KP Moon number x KP Asc star lord (z +5.2) is 46 matches but
only 21 distinct winners vs 21.7 expected, i.e. chance. The Karana x Day pillar AABB lead
holds up when counted by distinct winners (81 vs 52 before 2012, 53 vs 42 after).

## Per operator (`per_operator.py`)

Picks built from and scored on one operator only. Magnum: weekday changes the digit mix
slightly (best of all tests, beats all shifted calendars) and analysis C is a little above
chance (forward +0.10 vs -0.04; 10 of 42 columns beat every shift vs ~6). Sports Toto and
Da Ma Cai: at chance (forward -0.00 vs -0.06 and +0.05 vs +0.06). Effects too small to bet on.

## Live checks (picks logged before each draw in `forward_log.csv`)

| Draw | Lead | Result |
|---|---|---|
| 17 Oct 2026 | 1. Mercury nakshatra x Venus rashi S1 (6335 6337 6345 6347 6535 6537 6545 6547 7335 7337 7345 7347 7535 7537 7545 7547) | 0 hits |
| 17 Oct 2026 | 2. Karana x Day pillar S1 i-Box | 0 straight; 2 i-Box Consolations (7819 Toto, 2980 Da Ma Cai) |
| 17 Oct 2026 | 3. S1 Mars nakshatra x Mars rashi x Mercury combust | 0 hits |
| 17 Oct 2026 | 3. S2 Mars nakshatra x Mars rashi x Mercury combust | 1 straight: 8426 Toto Consolation (RM60 on RM48); i-Box matches on Da Ma Cai 6342 (2nd) and 1624 |
| 17 Oct 2026 | 4. Cold number, 5. 1024 | 0 hits |

| 18 Oct 2026 | 1. Mercury nakshatra x Venus rashi S1 (same 16 numbers) | 0 straight; i-Box matches 5375 Toto Special, 4557 Toto Consolation, 5673 Da Ma Cai Special |
| 18 Oct 2026 | 2. Karana x Day pillar S1 i-Box | 0 straight; 5 i-Box Specials (9569 and 4960 Magnum, 4950 Toto, 5619 and 9406 Da Ma Cai) |
| 18 Oct 2026 | 3. S1 / S2 Mars triple | 0 straight; i-Box 5304, 4950, 8628 (Toto) |
| 18 Oct 2026 | 4. Cold number, 5. 1024 | 0 hits |
| 18 Oct 2026 | All 29 logged formulas | 0 straight hits, RM0 on RM832 |

| 21 Oct 2026 | 5. Mercury nakshatra x Venus rashi S1 (logged before the draw) | **6537 Magnum 2nd prize (Straight, RM1,000 on RM48)** |
| 21 Oct 2026 | 1. Karana x Day pillar S1 i-Box | 0 straight; i-Box 4036 Magnum Special, 4409 Toto Special, 4246 Toto 3rd |
| 21 Oct 2026 | 6. Jupiter nakshatra x Mercury combust S2 i-Box | i-Box 5840 -> 8450 Magnum 1st |
| 21 Oct 2026 | Others | 0 straight hits |

Score the ranked leads on any dates with `python3 analysis/score_leads.py DATE [DATE ...]`.

The 18 Oct picks were made before the 17 Oct draw. Rebuilt with 17 Oct included
(`update_picks.py`), only the Mars-triple picks change, and they also have 0
straight hits on 18 Oct. Picks for 21 Oct were rebuilt from all results through
18 Oct and logged before the draw (variants ending `_upd`).

Full rescan before each draw (`rescan_live.py`: all singles and pairs, S1/S2, a/b,
Straight/Reverse/i-Box, using only earlier results): the top tests barely move
(z changes of about 0.01) and their picks score at chance: Straight 1 hit vs 2.2
expected on 17 Oct and 1 vs 2.0 on 18 Oct; i-Box (distinct pick sets) 27 vs 28.7
and 33 vs 30.6.

Score any date with `python3 analysis/score_live.py YYYY-MM-DD`; rebuild the leads'
picks for the next draw with `python3 analysis/update_picks.py YYYY-MM-DD --log`
after adding the latest results.

## Updating

Results come from 4dmoon.com (`scraper.py`, or `tinyfish_import.py` when the site is
reached through TinyFish); 4dkingdom.com and check4d.org were used to cross-check
17 Oct. Re-run any script from the repo root, e.g. `python3 analysis/recurrence_s12.py`.
