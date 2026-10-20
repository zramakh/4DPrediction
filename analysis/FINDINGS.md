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

## Most consistent lead (picks rebuilt before every draw)

Karana x Day pillar, S1 from the previous same-value day, i-Box: chosen among the
top 5 of its column on 1985-2011, then above chance in 14 of 15 years 2012-2026
(x1.04 overall, x1.035 in 2019-2026). None of 50 shifted calendars got 14 years
(their average is 7.7), and the same picks without a parameter got 6 of 15 (x0.995).
Allowing for the ~60 picks checked forward, the chance of this by luck is about 3%.
The gain is small: as i-Box it would return about 67% of stakes instead of about 64%.

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
