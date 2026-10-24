# Handoff for AI agents (read this first)

This repo asks one question: can Vedic, KP or Chinese almanac parameters
predict Malaysian 4D results (Magnum, Sports Toto, Da Ma Cai)? It holds the data,
every analysis script and its results, the live forward log and the full
conversation that produced them. Pick up from here; don't redo finished work.

## Where things are

| What | Where |
|---|---|
| Conclusions, ranked leads, every test and its result | `analysis/FINDINGS.md` (start here), older detail in `analysis/REPORT.md` |
| Every question asked and answer given (16-24 Oct 2026) | `docs/conversation.md` |
| Every inline one-off command run during the work | `analysis/adhoc/inline_snippets.md` (+ scratch scripts in `analysis/adhoc/`) |
| Data | `data/magnum.csv`, `data/sportstoto.csv`, `data/damacai.csv` (1985 to 21 Oct 2026); `data/singapore4d.csv` (Singapore 4D 1986 to 12 Jul 2026, for out-of-sample tests) |
| Picks logged before each draw | `analysis/forward_log.csv` |
| Result of each script | `analysis/<script>_results.json` and `analysis/<script>_output.txt` |

## Rules (the work's method; keep it)

1. **Picks only from `analysis/predict_all.py`** (plus `ml_model.py predict --before`
   for `ml_*`). Never re-implement pick logic; a re-implementation produced wrong
   lead1 / lead2 / lead6 picks for 24 Oct. Before accepting any picks file, run
   `python3 analysis/predict_all.py --check <last logged date>`; it must report no
   DIFFERENT row.
2. **No leakage:** a pick for date D uses only results of draws before D.
   Sets without suffix are frozen at their original cutoff; `_upd` sets use all
   results before D.
3. **Walk-forward:** choose on 1985-2011, score on 2012-2026. A lead chosen with
   hindsight is not a lead.
4. **Chance level:** winners that day x probability under that year's positional
   digit mix (`recurrence_s12.setup`: `Py`, `Pbox`).
5. **Multiple testing:** compare the best of N tests with the same scan on circularly
   shifted parameter calendars (shift at least 170 draw days). Report "k of n shifts
   as high".
6. **i-Box counting:** count distinct winning numbers (one winner matching several
   same-digit picks counts once), or AABB / AAAB z values are inflated.
7. **Small samples:** ignore huge z from tests with only a handful of scored days
   (e.g. ayana at lag +1: 12 days).
8. Parameters are computed at 19:00 MYT (11:00 UTC), sidereal Lahiri;
   `almanac.factors(date)` for any date, `astro_model.date_codes` for a future date.
9. Commit and push results with each step; write conclusions into `FINDINGS.md`
   and the Q&A into `docs/conversation.md`.

## Status on 24 Oct 2026

- **Bottom line:** nothing has beaten chance out of sample once selection is
  allowed for. Best leads return about 64-72% of stakes (random numbers about 64%).
- **Top lead:** Karana x Day pillar, S1 from the previous same-value day, i-Box.
  It is steady in Malaysia (z +2.52 before 2012, +2.72 after, 14/15 good years) but
  works only in its exact form, and it fails on Singapore 4D (z -1.60, rank 2,958 of
  3,081). Its two-pair Small i-Box subset is break-even, from 8 wins.
- **Checked and found at chance:** conditional frequencies, astro formulas, ML,
  S1 / S2 / S3 / rank pairs, recurrence (Straight, Reverse, i-Box), whole-number
  hot/cold, navamsa and D2-D60, Mei Hua / Da Liu Ren / Tai Yi, per operator, i-Box
  patterns, yearly consistency, the 75-formula list, offset and lunar-date rules,
  Shadbala and Ashtakavarga (stages A-C). See the "What was tried" table in `FINDINGS.md`.
- **Live:** picks are logged for 17, 18 and 21 Oct (and 24 Oct by the other agent's
  file, which matches `predict_all.py`). Data stops at 21 Oct 2026.

## Open items (continue here)

1. Add the 24 Oct 2026 results (and later draws) to `data/*.csv`. Direct curl to
   result sites is blocked by the proxy; use TinyFish `fetch_content` (check4d.org,
   4dkingdom.com) and `tinyfish_import.py`. Then score with
   `python3 analysis/score_leads.py` / `score_live.py`.
2. Shadbala / Ashtakavarga stage D (whole-number hot/cold) was cut off by a
   container restart: rerun `python3 analysis/shadbala_ashtakavarga.py 6` (about 3 h)
   or a D-only run.
3. Other games for out-of-sample checks: Singapore done. Sabah 88, Sandakan STC,
   Sarawak CashSweep and Grand Dragon have no bulk history found yet.
4. Not yet tried: full Shadbala (Kala, Drik, Ayana bala); Ashtakavarga kakshya
   (1/8-sign) transits; hora or choghadiya at the exact draw minute; Toto 5D/6D or
   jackpot games; testing any surviving lead on Singapore before betting on it.

## Script index

| Script | What it does |
|---|---|
| `analysis/almanac.py` | Every Chinese almanac and Vedic/KP parameter of a 4D draw date that can be computed from the date and the 19:00 Malaysia draw time. |
| `analysis/analyze.py` | Look for exploitable structure in Malaysian 4D results. |
| `analysis/astro_model.py` | 4D prediction formulas built only from Vedic and/or Chinese parameters, tuned on 2012-2017 and forward-tested draw by draw on 2018-2026. |
| `analysis/build_manual_workbook.py` | Build analysis/manual_formula.xlsx from analysis/manual_formula.json. |
| `analysis/chinese_divination.py` | Mei Hua Yi Shu, Da Liu Ren and Tai Yi (day cycles) at the 19:00 MYT draw, run through analyses A-D (navamsa_family.py) plus a direct digit test. |
| `analysis/conditional_checks.py` | Follow-up checks for conditional_extended.py. |
| `analysis/conditional_extended.py` | conditional_numbers.py extended to every Chinese almanac and Vedic/KP parameter in almanac.py (~80 parameters, every single one and every pair). |
| `analysis/conditional_numbers.py` | Do particular 4D numbers win more often under particular conditions? |
| `analysis/consistent_leads_live.py` | Score the most consistent leads (yearly_consistency.py) on given draws. Pooled leads: 16 numbers on all 3 operators (RM48 per draw), picks from all operators' earlier results. Operator leads: 16 numbers on that operator only (RM16 per draw), picks from that operator's earlier results. Scored as Straight and i-Box (approximate i-Box payout = Big prize / arrangements). |
| `analysis/continuous_astro.py` | Exact (continuous) planetary positions at the 19:00 MYT draw vs 4D digits. |
| `analysis/day_pillar_triples.py` | Day pillar combined with every pair of the other 77 parameters (A x B x Day pillar, 2,926 triples), scored with the Karana x Day pillar method (S1 from the previous same-value day, i-Box), against Karana x Day pillar itself. |
| `analysis/digit_models.py` | Trainable digit-position models for 4D, built on the S1/S2 idea. |
| `analysis/divisional_charts.py` | Other divisional charts (vargas) besides D9, run through the same analyses A-D as navamsa_family.py. |
| `analysis/ephemeris.py` | Low-precision Sun and Moon ephemeris (Meeus, Astronomical Algorithms, ch. 25 & 47). |
| `analysis/first_prize_test.py` | Are 1st prizes drawn from a different digit mix than the other prizes? |
| `analysis/formula_list_test.py` | Test a given list of parameter-pair formulas against chance and our leads. |
| `analysis/karana_family.py` | Karana x Day pillar (S1 from the previous same-value day, i-Box): does its family behave the same, and does any relative do better? |
| `analysis/karana_patterns.py` | A lead's picks by i-Box pattern (default: Karana x Day pillar, S1 from the previous same-value day). Pattern of the pick: ABCD (24 arrangements), AABC (12), AABB two pairs (6), AAAB triplet (4), AAAA (1). Each pick is bet on all 3 operators; evidence is counted by distinct winning numbers per draw and operator (one winner matching several same-digit picks counts once), money by bet (every matching pick pays). Big i-Box pays the Big prize / arrangements; Small i-Box the Small prize (1st 3500, 2nd 2000, 3rd 1000) / arrangements. |
| `analysis/karana_profit.py` | Can Karana x Day pillar (S1 from the previous same-value day, i-Box) be made profitable? Breaks its i-Box matches down by operator, by which of the 16 picks (grid position: which of the 2 top digits in each position), by number type (arrangements 24 / 12 / 6 / 4) and by prize tier, before 2012 and 2012-2026, and the money returned as Big i-Box, Small i-Box and Big Straight. |
| `analysis/karana_singapore.py` | Test 1 for the lead Karana x Day pillar (S1 from the previous same-value day, i-Box) on a game it was never fitted to: Singapore Pools 4D (23 winners per draw: 3 top prizes, 10 Starters, 10 Consolations; 1986-05-31 to 2026-07-12, data/singapore4d.csv from github.com/foooooooooooooooooooooooooootw/Singapore-Pools-Dataset). |
| `analysis/karana_tests.py` | Eight checks of the lead Karana x Day pillar (S1 from the previous same-value day, i-Box). Hits = winners that are an arrangement of one of the 16 picks (distinct boxes), chance = winners x that year's box probability, as in recurrence_s12.py. |
| `analysis/kp.py` | Krishnamurti Paddhati (KP) positions: the 249 sub-divisions, sign/star/sub lords, and the Ascendant. |
| `analysis/kp_analysis.py` | KP (Krishnamurti Paddhati) numbers vs 4D results. |
| `analysis/lag_rule.py` | Offset ("lag") rule: does the source draw work better a few days away from the matched day? |
| `analysis/last_draws_test.py` | Hold out the last N known draw dates and predict each one from the draws before it. |
| `analysis/magnum_bias.py` | Deep dive into the Magnum digit bias seen from ~2019 to late 2025. |
| `analysis/manual_formula.py` | A hand-usable 4D formula from a few Vedic / Chinese parameters. |
| `analysis/mh_lr_leads.py` | Leads from Mei Hua Yi Shu and Da Liu Ren (chinese_divination.py) and their performance on recent draws. |
| `analysis/ml_model.py` | Non-linear 4D prediction models, walk-forward tested. |
| `analysis/nakshatra_test.py` | Every nakshatra-type parameter, at three draw times (19:00, 19:15, 19:30 MYT). |
| `analysis/navamsa_family.py` | D9 navamsa family: does the navamsa (alone or paired) play a role? |
| `analysis/new_models.py` | Five further predictive models for 4D, walk-forward tested. |
| `analysis/pairs_test.py` | Do some Vedic / Chinese parameters promote wins and others suppress them, and do pairs of parameters predict better than single ones? |
| `analysis/pattern_ibox.py` | Do some leads favour one i-Box number pattern? |
| `analysis/per_operator.py` | All analyses on singles and pairs of the 78 Vedic / Chinese parameters, separately for each operator. |
| `analysis/per_operator_leads.py` | Score the best per-operator leads (per_operator.py, chosen on 1985-2011) on given draw dates. Picks are rebuilt for each date from that operator's earlier results only and scored on that operator's draw only, as Straight and i-Box (approximate i-Box payout = Big prize / arrangements). RM1 per number, 16 numbers = RM16 per draw. |
| `analysis/predict_all.py` | One command for every pick set logged in forward_log.csv, for any draw date (including a future one), from the results before a cutoff. |
| `analysis/predictive_model.py` | A predictive formula for 4D numbers from date parameters and history, tuned on one period and tested on draws it has never seen. |
| `analysis/recurrence_pairs.py` | recurrence_test.py for all 3,003 PAIRS of Vedic / Chinese parameters. |
| `analysis/recurrence_pairs_null.py` | Null for recurrence_pairs.py: rerun the full 3,003-pair scan with the whole parameter calendar circularly shifted (one shift for all parameters, at least about a year of draw days). Gives the best z and the count of z > 2 that the scan produces when parameters and results are unrelated. |
| `analysis/recurrence_perm.py` | Recurrence test (recurrence_test.py / recurrence_pairs.py) for Straight, Reverse and i-Box matches, over all 78 single parameters and 3,003 pairs. |
| `analysis/recurrence_rankpairs.py` | S3-style picks for every hot/cold rank pair. In each position the digits are ranked 1 (hottest) .. 10 (coldest) from earlier same-value days; a pair takes the digit of rank k and rank 11-k in each position, 2^4 = 16 numbers: 1+10 (= S3), 2+9, 3+8, 4+7, 5+6 Same tests and checks as recurrence_s3.py: 78 single parameters and 3,003 pairs, (a) all earlier / (b) previous same-value day, Straight / Reverse / i-Box, forward (top 5 before 2012 -> 2012-2026) and shifted parameter calendars. Ranks use counts with ties to the lower digit. |
| `analysis/recurrence_s12.py` | Recurrence test for the S1 (hot) / S2 (cold) positional-digit picks, for all 78 single parameters and 3,003 pairs, scored as Straight, Reverse and i-Box. |
| `analysis/recurrence_s12_forward.py` | Walk-forward check for recurrence_s12.py: pick the top 5 single/pair parameters per column (S1/S2 x a/b x Straight/Reverse/i-Box) using draw days in 1985-2011 only, then score those same picks on 2012-2026 draw days. (For version (a) the later days still use all earlier same-value days as the source, as one would in practice.) |
| `analysis/recurrence_s12_k.py` | recurrence_s12.py with the number of picks varied, for all 78 single parameters and 3,003 pairs, S1 (hot) / S2 (cold), (a) all earlier / (b) previous same-value day, scored as Straight / Reverse / i-Box. |
| `analysis/recurrence_s3.py` | S3 = the hottest AND the coldest digit in each position, combined: 2^4 = 16 numbers (e.g. hottest 7/3/4/7 and coldest 2/8/0/9 -> 7347, 7349, ..., 2809). |
| `analysis/recurrence_test.py` | When a Vedic / Chinese parameter value comes back on a later draw day, does that day repeat a 4D number from the earlier day more often than chance? |
| `analysis/rescan_live.py` | Re-run the full S1/S2 recurrence scan (78 single parameters + 3,003 pairs; S1 hot / S2 cold; (a) all earlier / (b) previous same-value day; Straight / Reverse / i-Box, as in recurrence_s12.py) using only results BEFORE a draw date, take the top 5 tests per column, build their 16 picks for that date from earlier results, and score them on that date's winners (all 3 operators). |
| `analysis/s12_combos.py` | S1 (hot) and S2 (cold) positional-digit strategies for single parameters, pairs and triples, keeping only formulas that beat random in BOTH periods. |
| `analysis/s12_family.py` | Deeper look at the best recurrence lead: Mercury nakshatra x Venus rashi, S1 built from all earlier same-value days, scored as Straight (see recurrence_s12.py / recurrence_s12_forward.py). |
| `analysis/s12_lead_cells.py` | Mercury nakshatra x Venus rashi S1 lead (all earlier same-value days, Straight hits; see s12_family.py) broken down by value: each Mercury nakshatra, each Venus rashi and each combined cell, before 2012 and 2012-2026, plus a check whether the cells that were best before 2012 stay best afterwards. |
| `analysis/s12_lead_k.py` | How many numbers to take for the Mercury nakshatra x Venus rashi lead? |
| `analysis/score_leads.py` | Score the ranked leads on given draw dates. Each lead's picks are rebuilt for every date from the results before that date only, then scored as Straight and i-Box (approximate i-Box payout = Big prize / arrangements). |
| `analysis/score_live.py` | Score the picks logged in forward_log.csv (before each draw) against the results in data/*.csv, plus two no-formula leads computed from earlier draws: the cold number (each position's least frequent digit per operator) and 1024 on Magnum. RM1 Big per pick; payouts 1st 2500, 2nd 1000, 3rd 500, Special 180, Consolation 60. Reverse and i-Box matches (other arrangements) are listed too. |
| `analysis/search_single_draw.py` | Try every single-parameter Vedic / Chinese formula (468) on one past draw, compare with random picks, then test the best one on 2018-2026. Shows how a formula that 'predicts' one draw does on others. |
| `analysis/seasonal_astro.py` | Do 4D numbers recur around the same date each year, or follow the Moon or the zodiac? |
| `analysis/shadbala_ashtakavarga.py` | Ashtakavarga and (simplified) Shadbala as parameters, run through the same suite as the Navamsa / divisional-chart families (navamsa_family.run_suite: A digit mix, B same-number recurrence, C S1 / S2 / rank-pair digit picks (a / b, Straight / Reverse / i-Box, walk-forward), D whole-number hot / cold), each against shifted calendars. |
| `analysis/strategies_test.py` | Four number-building strategies, for every Vedic / Chinese parameter and pair. |
| `analysis/update_picks.py` | Rebuild the leads' picks for a draw date from all results before a cutoff, so each new draw's results feed into the next draw's picks. |
| `analysis/vedic.py` | Vedic (sidereal) astrology quantities for a moment in time. |
| `analysis/vedic_analysis.py` | Vedic astrology vs 4D results. |
| `analysis/whole_number_test.py` | Whole-number hot / cold picks from earlier days with the same parameter value(s). |
| `analysis/yearly_consistency.py` | Year-by-year consistency of the forward picks, pooled and per operator. |
| `scraper.py` | Scrape past 4D results (Magnum, Sports Toto, Da Ma Cai) from www.4dmoon.com. |
| `tinyfish_import.py` | Import 4dmoon.com past-results pages fetched through TinyFish into data/*.csv. |
