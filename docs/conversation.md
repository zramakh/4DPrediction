# Conversation log

The questions asked and the answers given while building this analysis (16-24 Oct 2026, times in UTC).
Tool calls, automated notices and raw command output are left out; the scripts and result files in `analysis/` hold those,
and `analysis/adhoc/inline_snippets.md` has every inline command. Conclusions: [analysis/FINDINGS.md](../analysis/FINDINGS.md).

---

## 1. Question (2026-10-16 16:28)

> Can you check during which parameter either single or combination where certain 4d number tend to appear more often

**Answer** (2026-10-16 16:31)

The first draft would be too slow (dense 10,000-column matrices in every shuffle), so I'm switching it to sparse counting.

Running; I'll wait for progress events.

I've pushed the script; the analysis is still running, and I'll add the results and a report section once it finishes.

Magnum is done in 50s; the other scopes should take a few more minutes.

Waiting for the remaining scopes.

Da Ma Cai finished; only the pooled scope and the replication step remain.

All scans are done; the step that finds associations in pre-2012 draws and tests them on 2012+ draws is running now.

Results are in. I'll add a section to REPORT.md and commit.

No parameter or pair of parameters makes particular 4D numbers win more often in a way that holds up. A search this large always finds some numbers that look "hot" under a condition, but those disappear when you test them on other years.

I tested 13 parameters on their own and in all 78 pairs: weekday, month, day of month, 5‑year era, moon phase, moon sign, sun sign, Chinese lunar month, lunar day, Chinese zodiac year, nakshatra, tithi and prize tier. I ran this for Magnum, Sports Toto, Da Ma Cai and all three combined, which gave 66,656 condition groups. In each group I looked at the 10,000 exact numbers and at the 715 i‑Box groups (same digits in any order).

**The most striking matches all came from chance:**

| Operator | Condition | Number | Wins | Expected if random |
|---|---|---|---|---|
| Magnum | 2nd of the month & tithi 16 | 7345 | 4 | 0.02 |
| Sports Toto | Horse year & tithi 3 | 7380 | 4 | 0.03 |
| Da Ma Cai | 22nd of the month & Horse year | 6174 | 4 | 0.03 |
| Magnum | October & lunar day 9 | 4458 (any order) | 8 | 0.47 |
| Da Ma Cai | First-quarter moon & Snake year | 0456 (any order) | 18 | 3.75 |

- **Why these don't count:** each is the best of 10,000 numbers in its group, and each group is one of 66,656. Once you allow for that much searching, none is significant.
- **Shuffled-date check:** I gave every draw another draw's date and re-ran the whole search 20 times, so no real link could exist. The shuffled data produced equally or more extreme "hot numbers" 65% of the time for exact numbers and 50% for i‑Box groups.
- **Testing on later years:** for each condition, I took the top numbers from draws before 2012 and checked them from 2012 onward. They won 1.00–1.05× as often as random numbers. I also learned on even years and tested on odd years, which gave 1.00–1.01×. Almost every headline match scored zero wins afterwards. For example, Sports Toto 9586 on the 17th under a waning gibbous moon won 4 times before 2012 and 0 times after.
- **The only deviations are Magnum's:** a few Magnum combinations, mostly involving the 5‑year era, are less even than chance would give. That is the equipment-related digit bias already described in the report, not a number-and-condition link, and it doesn't carry over to later years either.

I added the script (`analysis/conditional_numbers.py`, about 5 minutes to run), the full results (`analysis/conditional_results.json`) and a new section 6 in `analysis/REPORT.md`, and pushed them to `claude/4d-results-scraper-9ptbd5`.

---

## 2. Question (2026-10-16 16:38)

> I think you didn’t try all the Vedic and Chinese parameters completely as there’s quite a lot of them

**Answer** (2026-10-16 16:39)

You're right, the first pass used only a few of them. I'll list every Vedic and Chinese calendar parameter I can compute from the draw date and time, check the reference formulas, then rerun the full single + pair scan.

Before using them, I'm checking the less standard Chinese almanac rules (28 mansions, Nine Star, Yellow/Black path days) against published references.

Works, at about 1 s per parameter set. Starting the full run (85 parameters → 3,655 sets × 4 scopes, ~40 min).

The full run has started; I'll report when it finishes.

I've pushed the new code. The scan is running (368 chunks), and I'll write up the results when it finishes.

At about 4 s per chunk, the full run should take roughly 25 minutes.

Still running (40/368 chunks).

60/368 chunks done.

80/368 chunks done.

100/368 chunks done.

120/368 chunks done.

140/368 chunks done.

160/368 chunks done.

180/368 chunks done.

200/368 chunks done.

220/368 chunks done.

240/368 chunks done.

260/368 chunks done.

280/368 chunks done; the last part is the larger all-operators scope.

300/368 chunks done.

That was the old monitor; the current one is still watching.

320/368 chunks done.

340/368 chunks done.

Almost done (360/368).

All chunks are done; it's writing the summary now.

Neither explains it either. I'll look at exactly which cells and numbers produce Da Ma Cai's z = 19.

Rerunning both scans now (about 35 minutes in total).

That was the previous monitor expiring; the rerun is being watched by the new one.

I've pushed the fixes. The results file still holds the old numbers and gets overwritten when the rerun finishes, so I'll commit it then.

The run is stopped. Now applying the patch:

Both scans are running again (about 35 minutes).

I've pushed the fix; I'll wait for the rerun to finish.

The first scan is clean now: no parameter set reaches z > 3 except a handful for Magnum, consistent with its known equipment drift. The extended scan (85 parameters) is still running.

I've committed the updated results. The extended results file is mid-rerun, so I'll commit it when the run finishes.

100/368 chunks done.

I moved the stale extended results file out of the repo; the rerun will write a new one.

200/368 chunks done.

The monitor that expired was the old one. The current monitor is still running.

300/368 chunks done.

The last chunks are still running.

The checks are running (~10 min); I'll report when they finish.

A division by zero at the summary step, on parameter sets whose expected count rounds to 0. Fixing and rerunning:

The checks are rerunning with the fix.

I've pushed the fix; the checks are still running.

The search didn't turn up those draws. I'll check the pages saved by the scraper instead, to see how 1024 appears in the source HTML:

The network policy blocks direct downloads, so I'll use the web fetcher instead:

I can't reach the source site from this environment, so I can't check 1024 against the original pages. One last check: is 1024's post‑2012 excess consistent across operators?

Writing it up: I'm replacing section 6 of the report with the corrected first scan, the extended scan, the checks, and the 1024 finding.

You were right. I've rerun the scan with 85 Vedic and Chinese parameters, every single one and every pair (3,655 sets, about 4.2 million condition groups across the three operators and pooled). The answer is still no: no parameter or pair makes particular numbers or i‑Box groups come up more often.

**What's now covered:**
- **Chinese:** year animal, stem, element, yin/yang and pillar; lunar month, day and leap month; 24 solar terms; month and day pillars with their stems, branches and elements; Na Yin; the 7pm hour stem; the 12 Day Officers; the 12 day gods and Yellow/Black path days; the 28 mansions; day‑vs‑year branch (Tai Sui) relation; year and month Nine Star.
- **Vedic/KP:** tithi, paksha, nakshatra and pada, nakshatra lord, yoga, karana, hora lord; sign and nakshatra of every planet including Rahu; lagna; Moon navamsa; retrograde and combust flags; masa, adhika masa, ritu, ayana, samvatsara; KP star lord, sub lord and number for the Moon, Ascendant and Sun.
- **Not included:** choghadiya, Rahu kalam, gulika and vara lord, which at the 7pm draw time are fixed by the weekday or don't apply, and the daily Nine Star.

I checked the Chinese and Vedic calculations against published almanac values. They match for:
- day pillar, mansion and Day Officer;
- month pillar;
- Nine Star year and month;
- samvatsara and adhika masa.

The Yellow/Black path days use the standard rule but I couldn't confirm them against a published almanac.

**Results:**
- **Top matches are chance.** Examples are Magnum 4835 with nakshatra lord Mercury and Rahu in Shatabhisha (6 wins vs 0.09 expected), and Sports Toto 3458 in any order with Rahu in Pushya, top‑3 prizes (14 vs 1.7). I also gave every draw another date's parameters and repeated the whole search 10 times. That shuffled data produced equally extreme matches 60% of the time for exact numbers and 10% for i‑Box groups.
- **Nothing carries over to later years.** Each condition's top numbers, learned from draws before 2012, did no better after 2012 than numbers learned from shuffled conditions: 1.00–1.01× random for exact numbers, about 1.0–1.05× for i‑Box groups. Most headline matches scored zero wins after 2012.

**Two problems in my first scan, now fixed:**
- **Repeated numbers.** A number repeated within one draw was counted as recurring.
- **Mismatched dates.** The shuffle mixed dates where all three operators drew with dates where only one did.

Both created clustering that wasn't real. I also excluded the Magnum 2015‑01‑09 result, which repeats 22 of 2015‑01‑07's 23 numbers and is almost certainly a copy on the source site.

**One real outlier, not tied to any condition: 1024.** It is the most frequent number in the whole dataset, 79 wins vs 41.5 expected, and it is high for all three operators. After 2012 it was still high (29 vs 17), while the other "hot" numbers from before 2012 were not. Chance would produce a number this extreme only about 1 time in 700. I couldn't reach 4dmoon.com from here to rule out an error in the source data, so check those 1024 wins against the operators' official results before reading anything into it.

The new scripts are `analysis/almanac.py`, `analysis/conditional_extended.py` and `analysis/conditional_checks.py`, with results in the matching JSON files. Section 6 of `analysis/REPORT.md` is rewritten, and everything is pushed to `claude/4d-results-scraper-9ptbd5`.

Sources used to check the almanac rules:
- [skillon almanac, 2024‑02‑10](https://www.skillon.com/almanac.cfm/date/2024-02-10)
- [Master Sean Chan, 2019 flying star chart](https://www.masterseanchan.com/fengshui-2019-flying-star-chart/)
- [Master Sean Chan, Feb–Mar 2029](https://www.masterseanchan.com/fengshui-2029-february-march/)

---

## 3. Question (2026-10-16 23:48)

> So far what are the best lead?

**Answer** (2026-10-16 23:49)

The only lead worth following up is the number **1024**. The equipment bias in Magnum's draws was real but too weak to beat the house edge and seems to have stopped. Nothing calendar-based or astrological held up.

**1. 1024: the only number that stays hot**
- **Overall:** it has won 79 times in all draws against 41.5 expected. It is the most frequent number in the whole dataset, and it is high for all three operators.
- **After 2012:** it kept winning at about 1.7× the expected rate (29 vs 17). The other numbers that were hottest before 2012 went back to normal afterwards (135 vs 153 expected).
- **Odds of chance:** even allowing that it is the best of 10,000 numbers, chance gives this about 1 time in 700.
- **What it would be worth:** a number needs to win about 1.56× as often as average just to break even on Big Forecast. 1024's 1.7× since 2012 is above that on paper, but it rests on only 29 wins, so the true rate could be well below or above.
- **Why to be careful:**
  - I couldn't reach the source site from here to check that those wins are genuine and not a data error.
  - It is a single number, found by searching through all 10,000.
  - 70 of its 79 wins are Special or Consolation prizes, the lowest payouts.

**2. Magnum's digit bias: real, but it didn't pay**
- **What it was:** probably from the draw equipment, Magnum's draws ran short of 7s in 1985–94 and again from January 2019 to about November 2025.
- **What it was worth:** it improved the odds by only 1.05–1.2×, below the 1.56× break-even. Even the best stretch lost money in backtests.
- **Now:** it seems to have stopped around November 2025, which suggests the equipment was replaced.

**3. Calendar and astrology: no lead**
- **What was tested:** weekday, date, moon, the Chinese almanac parameters, and Vedic and KP astrology, each alone and in every pair, about 4.2 million condition groups.
- **Result:** nothing beat chance, and nothing carried over to later years.
- **Picking methods:** hot, cold/overdue, repeat-last-draw and machine-learning picks all matched random picking.

**Next steps for 1024:**
1. Check its 79 wins against the operators' official result archives. If many of them aren't there, the lead is a data error.
2. If they check out, track 1024 on draws from now on without betting, for a few hundred draws per operator. The past data has been searched so thoroughly that only new draws can show whether the effect is real.

I can write a short script that lists all 79 dates and prize slots for 1024 as a checklist, and later keeps a running forward test.

---

## 4. Question (2026-10-16 23:57)

> Ok now I want you to create a formula using any of those parameters which is able to provide a few 4d numbers at any of the races using the parameters based on the history. And then you test them for the races that it has not seen and create a predictive model

**Answer** (2026-10-16 23:58)

I'll build a model that, for any draw (operator + date), scores all 10,000 numbers using that date's parameters and the full past history, then returns the top few. It will be trained on old draws, tuned on a middle period, and then tested on later draws it has never seen. Checking the data range first:

The model is now tuning on 2012–2017, then it tests on 2018–2026. I'll report when it finishes.

The script is committed. The model run is still going.

The tuning search finished quickly (about 74,000 winning numbers in the tuning period); the combined-weights step and the test are next.

The joint-weight step is running.

The joint-weight search is still running.

The joint-weight search is still running.

The joint-weight search is still running.

The rerun is going, with finer weights.

The fix is pushed and the run is still in progress.

The single-signal search finished; the joint search and the test are running.

The config file is written mid-run; I'll commit it together with the results once the test finishes.

The tuned formula is frozen: a small recent digit-bias weight, plus conditional i‑Box and digit signals. Testing on 2018–2026 is starting.

Test results are in. Running the frozen formula on the next draws (today, Sat 17 Oct, and Sun 18 Oct) to make sure the prediction tool works:

A small bug in the prediction tool: it counts dates differently from the data loader. Fixing it:

The tool works. As expected from a digit-based formula, the picks are clusters of similar numbers. Adding a report section and committing:

I built the formula and tested it on 2018–2026 draws it had never seen. It produces numbers for any draw, but it doesn't predict winners better than random picks.

**How the formula works.** For a given operator and date, it scores all 10,000 numbers and returns the top few. The score adds up these signals from earlier draws:
- how often each number has won overall;
- recent digit bias;
- how often each digit, number and i‑Box group won under that date's values of all 84 parameters (weekday, moon, Chinese almanac, Vedic, KP).

**How I tested it:**
1. Learned the counts from draws before 2012.
2. Tuned the weights on 2012–2017.
3. Froze the formula.
4. Tested it on the 4,180 draws from 2018 to October 2026, re-learning each year only from earlier draws.

**What tuning showed:** most signals, including hot numbers and 1024, made predictions worse. Only tiny weights on the digit and i‑Box signals survived, and they improved the tuning score by essentially nothing.

**Test on unseen draws:**

| Picks per draw | Wins (any prize) | Random would give | Lift | Significance (z) |
|---|---|---|---|---|
| Top 5 | 54 | 48 | 1.13× | +0.9 |
| Top 10 | 111 | 96 | 1.16× | +1.5 |
| Top 23 | 243 | 221 | 1.10× | +1.5 |
| Top 100 | 963 | 960 | 1.00× | +0.1 |

- **Not a real edge:** none of these lifts is statistically significant. Year by year, the top‑10 picks swung from 2 to 22 wins against about 10 expected.
- **Money:** the top‑1 pick returned RM1.09 per RM1 on Big Forecast, but that came from one lucky top-prize hit. Random picks run alongside returned anywhere from RM0.16 to RM2.89 by luck alone. Breaking even needs about 1.56× random, kept up over many draws; the formula reached 1.0–1.16×.

**Picks for this weekend (top 5).** These are not more likely to win than any other numbers. The digit signal drives the picks, so they come out as near-duplicates. The data also stops at 10 Oct, so the last two draws are missing.

| Draw | Magnum | Sports Toto | Da Ma Cai |
|---|---|---|---|
| Sat 17 Oct | 1599, 1099, 6599, 1549, 9599 | 9092, 9762, 9962, 9062, 9562 | 6092, 6090, 6592, 6091, 6792 |
| Sun 18 Oct | 6599, 1599, 6590, 1099, 6090 | 7597, 7590, 7097, 7797, 6597 | 6090, 6590, 6095, 6595, 6790 |

To get picks for any date, run `python3 analysis/predictive_model.py predict --date 2026-10-21 --k 5`.

The only test this formula hasn't faced is draws that happen after today. If you want that, I can log its picks before each draw and score them afterwards. A few hundred draws would be needed before the result means anything.

Everything is in `analysis/predictive_model.py`, the frozen formula is in `predictive_model_config.json`, and section 7 of `analysis/REPORT.md` has the full write-up. All of it is pushed.

That was just the old progress monitor expiring. The run had already finished, and nothing has changed since.

That's the second monitor expiring. Both runs had already finished, so there's nothing new.

---

## 5. Question (2026-10-17 00:37)

> Use the model that you created for 14/10/2026

**Answer** (2026-10-17 00:38)

The 14 Oct draw has already happened, and the model's data stops on 10 Oct, so it has never seen this draw. I'll try to find the actual results to check the picks:

The top 3 prizes are confirmed by several sites, and none of the picks match them. Fetching the full Special and Consolation lists so I can check all 23 numbers:

Here are the model's top 10 picks for **Wednesday 14 Oct 2026**. That draw has already happened, and the model's data ends on 10 Oct, so it had never seen it.

| Operator | Model's top 10 picks |
|---|---|
| Magnum | 6599, 9599, 5599, 1599, 6899, 0599, 6596, 9596, 6549, 5899 |
| Sports Toto | 7597, 5524, 7594, 0597, 5527, 5594, 0594, 7524, 5597, 5994 |
| Da Ma Cai | 5591, 5594, 5592, 5097, 6594, 6591, 5094, 5597, 5091, 5092 |

For that date the model used: weekday Wed, waxing crescent moon, lunar 9th month day 5, day pillar Xin You, nakshatra Anuradha, tithi 4.

**Actual results (top 3 prizes), confirmed by several result sites:**

| Operator | 1st | 2nd | 3rd | Any pick matched? |
|---|---|---|---|---|
| Magnum | 3872 | 3175 | 1274 | No |
| Sports Toto | 9332 | 0305 | 0606 | No |
| Da Ma Cai | 6906 | 7100 | 6516 | No |

None of the 30 picks won a top‑3 prize. I couldn't get the full Special and Consolation lists: the search summaries said the sites disagree on them, and the result sites can't be reached from this environment. So I can't say yet whether any pick won a smaller prize.

That's the expected outcome. Ten picks per operator against 23 winning numbers would catch one winner of any prize in about 2% of draws, and the formula did no better than random in testing. One draw tells us nothing either way.

If you paste the full 14 Oct results (Special and Consolation included), I'll score all 30 picks. To build up a real forward test, I can also start a log that records picks before each draw and scores them afterwards.

Sources: [4dnumber.net](https://4dnumber.net/), [check4d.co](https://check4d.co/), [check4dresult.com](https://www.check4dresult.com/), [ilove4d.com](https://ilove4d.com/), [4dkingdom.com](https://www.4dkingdom.com/)

---

## 6. Question (2026-10-17 00:40)

> What formula does the predictive model use?

**Answer** (2026-10-17 00:40)

The model gives every 4D number a score, adds up three weighted parts, and picks the highest-scoring numbers. The three parts and their weights were tuned on 2012–2017 draws and then frozen (`analysis/predictive_model_config.json`):

```
score(n) = 0.05 × RecentDigit(n)  +  0.25 × DateDigit(n)  +  0.02 × DateIBox(n)
```

Each part compares how often something actually happened in past draws with how often pure chance would give it. All counts come from past draws only, and a number counts once per draw even if it appears in two prize slots.

**1. RecentDigit: the operator's recent digit bias (weight 0.05)**
- For each of the 4 digit positions, it counts how often each digit 0–9 has appeared in that operator's winning numbers.
- Recent draws count more: a draw 300 draws ago counts half as much as the latest one.
- RecentDigit(n) = Σ over the 4 positions of log( p(digit in that position) / 0.1 ), where p is that frequency, smoothed toward 10%.
- In effect, numbers made of digits that have been coming up lately score higher. This is what picks up equipment bias like Magnum's shortage of 7s.

**2. DateDigit: digit frequencies on similar dates (weight 0.25)**
- For each of the 84 date parameters, it takes all past winners on dates with the same value as the target date, pooled across all three operators. For example, every past draw on a tithi‑4 day, or every past draw on a Xin You day.
- For each position it compares the digit frequency on those dates with the overall digit frequency. The comparison is smoothed, as if 50 extra average draws were added, so thinly supported values have little effect.
- DateDigit(n) = (1/84) × Σ over the 84 parameters, Σ over the 4 positions, of log( p(digit | same parameter value) / p(digit overall) ).

**3. DateIBox: i‑Box group frequencies on similar dates (weight 0.02)**
- It works the same way as DateDigit, but for the number's digit combination in any order (for example, 6599 counts as {5,6,9,9}).
- DateIBox(n) = (1/84) × Σ over the 84 parameters of log( (wins of that group on same-value dates + 50) / (expected wins + 50) ).

The model takes the K highest scores as its picks.

**Signals left out:** tuning also tried hot numbers per operator, hot numbers pooled across operators, and how often each exact number won on similar dates. Each one made predictions worse on the 2012–2017 tuning draws, so their weights are zero.

**What this means in practice:**
- **Similar picks:** only digit-level signals survived, so the picks share digits, as in 6599, 1599 and 9599.
- **Weak effects:** the weights are small because the effects are tiny. Even the best combination improved the tuning score by essentially nothing.
- **No edge:** on 2018–2026 draws it had never seen, it did no better than random (top‑10 picks 1.16×, z = +1.5, not significant).

So it is a fully specified, reproducible formula built from the parameters you asked about, but its picks are no more likely to win than any other numbers. The code is in `analysis/predictive_model.py`: the `Tables` class builds the counts and `components()` computes the parts.

---

## 7. Question (2026-10-17 00:41)

> I want your formula to use the parameters of either the Vedic ones or the Chinese ones or the combination of both, and then, test them in forward test. You didn’t follow my previous order

**Answer** (2026-10-17 00:42)

You're right. My previous formula mixed in signals that are neither Vedic nor Chinese: hot numbers, the operators' recent digit bias, weekday/month, Western moon phase and tropical signs. It also only re-learned once a year rather than draw by draw. I'll rebuild it so that:

- **Only Vedic and/or Chinese parameters** feed the formula, in three versions: Vedic only, Chinese only, and both combined.
- **Tuning chooses the parameters:** it picks which ones to use and how much weight each gets, on 2012–2017 draws. Then the formula is frozen.
- **True forward test:** draws from 2018 to Oct 2026 are predicted one at a time, in date order, using only the draws before each one. After each draw its results are added, then the next draw is predicted.
- **Live forward log:** picks for upcoming draws are recorded before they happen, so they can be scored when results come in.

Before running, I'm making two speed fixes: bulk counting with `bincount`, and reusing shared calculations during tuning.

Tuning the Vedic, Chinese and combined formulas now; the forward test follows.

Of the 312 Vedic terms, 61 helped on the tuning draws when scored alone; those are being combined now.

The Vedic formula is frozen: 30 terms, at half the weights each had when tested alone. The Chinese and combined formulas are tuning next.

36 of the 156 Chinese terms helped on their own. Tuning continues.

The Chinese formula is frozen at 30 terms. The combined formula is next, then the forward tests.

97 of the 468 combined terms helped on their own.

All three formulas are frozen. I'm committing them now, before any forward-test result exists, so the git history shows they were fixed in advance:

The frozen formulas are committed. The draw-by-draw forward test on 2018–2026 is running.

The Vedic forward test finished (1,400 draw dates). The Chinese and combined tests are running.

The Chinese forward test is done too. The combined formula's test is running.

The tests ran, but saving the results crashed on a type error. I'll fix it and make the rerun reuse the frozen formulas exactly as committed rather than re-tuning:

Now adding the write-up to the report and committing everything (results, the forward log and the report):

You were right: my earlier formula mixed in hot numbers, digit bias, weekday/month and Western astrology. I rebuilt it to use **only Vedic and/or Chinese parameters**, as three formulas (Vedic, Chinese, combined), and forward-tested each one draw by draw. None of them beat random picking on draws they hadn't seen.

**How it was built:**
1. Each formula gives a number a higher score when it, its digits or its i‑Box group came up more often on past dates with the same parameter value, compared with how often it comes up overall.
2. I tried every parameter on its own on 2012–2017, counting from draws before 2012. That was 312 terms for Vedic, 156 for Chinese and 468 combined. I kept the best 30 for each.
3. I froze the three formulas and committed them before running any test.

The strongest Vedic terms were Mars's nakshatra, Jupiter's nakshatra and rashi, ayana and ritu. The strongest Chinese ones were day element, day stem, day officer, year stem and Nine Star.

**Forward test:** 4,180 draws from 2018 to Oct 2026. Each draw was predicted only from the draws before it; then its results were added and the next draw was predicted.

| Formula | Top 10 wins vs random | Top 23 | Big return (top 10) |
|---|---|---|---|
| Vedic | 87 vs 96 (0.91×) | 0.95× | RM0.58 |
| Chinese | 99 vs 96 (1.03×) | 1.06× | RM0.65 |
| Vedic + Chinese | 75 vs 96 (0.78×) | 0.85× | RM0.47 |

A random number returns about RM0.64 per RM1. All three formulas looked better than random on 2012–2017 and then did no better, or worse, on the draws they hadn't seen. With hundreds of terms tried, about half look helpful by chance, so the tuning was fitting noise.

**Live forward test:** I logged each formula's top 10 picks for **Sun 18 Oct** and **Wed 21 Oct**, made on 17 Oct at 00:47 UTC. They are in `analysis/forward_log.csv`.

| Formula | Magnum (18 Oct) | Sports Toto (18 Oct) | Da Ma Cai (18 Oct) |
|---|---|---|---|
| Vedic | 7592 5792 7295 9572 5297 … | 0536 6503 3506 6530 0563 … | 6788 8786 8768 2794 2795 … |
| Chinese | 0300 7121 2277 0003 2171 … | 4112 1142 1236 4192 2136 … | 2992 4192 2491 0721 7097 … |
| Both | 9527 7592 9752 5792 9725 … | 7213 0213 0312 2103 2713 … | 2795 2792 9835 9722 8593 … |

To score them after the draws:
1. Run `python3 scraper.py` to add the new results. The results site is blocked from this environment, so this has to run on your computer.
2. Run `python3 analysis/astro_model.py score`.
3. Before each later draw, log new picks with `python3 analysis/astro_model.py log --date YYYY-MM-DD`.

Expect it to take a few hundred draws before the live result means anything.

Everything is in `analysis/astro_model.py`, the frozen formulas are in `astro_model_formulas.json`, and section 8 of `analysis/REPORT.md` has the full write-up. All of it is pushed.

---

## 8. Question (2026-10-17 00:54)

> Do the test for 14/10

**Answer** (2026-10-17 00:54)

None of the 90 picks match the top 3 prizes confirmed earlier. I'll try again to find the Special and Consolation lists so I can check all 23 winning numbers:

I ran the three Vedic/Chinese formulas for **Wed 14 Oct 2026**. That draw is not in the model's data (it ends on 10 Oct), so it's a genuine unseen test. **No pick won a prize.**

**Picks (top 10 per operator)**

| Formula | Magnum | Sports Toto | Da Ma Cai |
|---|---|---|---|
| Vedic | 5265 7492 7294 7429 5228 5526 5256 5562 7249 6166 | 7206 6207 7996 9796 0726 0267 6997 6799 2706 9697 | 6704 0764 6720 6740 6702 6799 6834 8795 0726 2794 |
| Chinese | 0992 0403 2834 3824 8607 4823 0929 9029 2909 0867 | 8142 0826 8726 8421 1494 2394 1824 7862 0403 5723 | 9091 1891 8840 0992 2941 9029 0991 2777 7727 5758 |
| Both | 3044 4043 3440 6798 7997 0799 0443 5526 7909 6793 | 9796 8807 7206 8708 0788 7260 7808 0627 6207 9967 | 2093 0799 0293 9032 3092 6395 7895 0791 0392 2390 |

**Actual results (from result sites):**
- **Magnum:** 3872 / 3175 / 1274. Special: 9432 0504 7685 3683 0877 0164 8480 5730 9152 1613. I couldn't confirm the Consolation list: the one site that gave it listed exactly Da Ma Cai's consolation numbers, so it is probably a copying error.
- **Sports Toto:** 9332 / 0305 / 0606. Special: 3342 8253 0014 5484 2858 7445 6147 8346 8435 5213. Consolation: 2212 6901 8649 8189 3036 3226 2131 1480 4381 2363.
- **Da Ma Cai:** 6906 / 7100 / 6516. Special: 8626 2888 1164 7150 6415 2016 4406 1710 7120 1777. Consolation: 0779 4696 4454 7436 8259 6972 1294 7155 6467 4482.

**Score**

| Formula | Straight hits (any prize) | i‑Box (any order) matches |
|---|---|---|
| Vedic | 0 / 30 picks | 0 |
| Chinese | 0 / 30 picks | 1: **2941** vs Da Ma Cai consolation **1294** |
| Both | 0 / 30 picks | 0 |

**What to expect by chance:**
- **Straight hits:** with 90 picks against 23 winning numbers per operator, random picks would land about 0.2 straight hits. Zero is the most likely result.
- **i‑Box matches:** random picks would get about 3, so 1 is slightly below average.
- **Payout:** the 2941/1294 match would only pay if bet as an i‑Box (24 combinations), and even then roughly RM2.50 on a RM1 i‑Box bet. It is a lucky small match, not a sign the formula works.

One draw can't show whether the formulas work; it takes hundreds. The 4,180‑draw forward test already showed them performing at or below random.

Sources: [4dkingdom.com](https://www.4dkingdom.com/), [4dgm.com](https://4dgm.com/), [keputusan4d.com](https://keputusan4d.com/), [check4dresult.com](https://www.check4dresult.com/), [dato4d.com](https://www.dato4d.com/), [4dpick.co](https://4dpick.co/), [mobile.fast4dking.com](https://mobile.fast4dking.com/v2/live-4d-results-magnum-damacai-toto)

---

## 9. Question (2026-10-17 00:56)

> You can use tiny fish to scrap it from 4dmoon.com

**Answer** (2026-10-17 00:57)

I pulled the official 14 Oct results from 4dmoon.com through TinyFish and scored every set of picks. **None of the 120 picks won a prize.**

**Official results, 14 Oct 2026 (4dmoon.com)**

| | Magnum (#435/26) | Sports Toto (#6198/26) | Da Ma Cai (#6145/26) |
|---|---|---|---|
| 1st / 2nd / 3rd | 3872 / 3175 / 1274 | 9332 / 0305 / 0606 | 6906 / 7100 / 6516 |
| Special | 9432 0504 7685 3683 0877 0164 8480 5730 9152 1613 | 3342 8253 0014 5484 2858 7445 6147 8346 8435 5213 | 8626 2888 1164 7150 6415 2016 4406 1710 7120 1777 |
| Consolation | 4661 2995 3368 3934 2300 3039 9686 6307 7484 4904 | 2212 6901 8649 8189 3036 3226 2131 1480 4381 2363 | 0779 4696 4454 7436 8259 6972 1294 7155 6467 4482 |

The Magnum consolation list differs from what the search summary gave last time. That one had copied Da Ma Cai's numbers by mistake.

**Score (10 picks per operator, 30 per formula)**

| Formula | Straight wins | i‑Box (any order) | Big return on RM30 |
|---|---|---|---|
| Vedic | 0 | 0 | RM0 |
| Chinese | 0 | 1: 2941 ↔ DMC consolation 1294 | RM0 |
| Vedic + Chinese | 0 | 0 | RM0 |
| First model (section 7) | 0 | 0 | RM0 |

Random picks would average about 0.3 straight wins across all 120 picks, so zero is the most likely result. The one i‑Box match is luck at about the expected rate. One draw can't confirm or rule out a formula, but this is consistent with the 4,180‑draw forward test, where all three Vedic/Chinese formulas did no better than random.

**Data update:** I also added the 11 Oct and 14 Oct draws to `data/*.csv` and pushed them. TinyFish strips the HTML classes that `scraper.py` relies on, so the repo's scraper can't read these pages directly. I can add a TinyFish-based importer so new draws can be pulled in here before scoring the logged picks for 18 and 21 Oct.

---

## 10. Question (2026-10-17 00:59)

> yes add the TinyFish importer and also looks like you have failed to create a predictive model, please retry to find for a better formula using the model, maybe you can include different types of equations and it doesn’t have to be linear, and combine few other parameters

**Answer** (2026-10-17 00:59)

Both, then. Plan:

1. **TinyFish importer:** a parser that turns 4dmoon pages fetched through TinyFish into rows in `data/*.csv`.
2. **New predictive model**, non-linear and using more types of signal. I'll try several model families:
   - gradient-boosted trees over (draw, number) pairs, mixing astro parameters with each number's own history (frequency, recency, gaps, digit patterns, cross-operator wins);
   - a non-linear digit-position model;
   - a "similar days" kernel model that weights past draws by how alike their full Vedic/Chinese configuration is.
   
   They'll use the same rules as before: tune on old draws, freeze, then test on 2018–2026.

Checking which ML libraries are available:

All 4 tests pass, and the parser's 14 Oct output exactly matches the rows I added by hand. Checking that running the importer on data already present leaves the files unchanged:

The importer is pushed. **Part 2 is the new predictive model.** Checking available memory first, since the training set will be large:

15 GB and 4 cores is enough. Writing the model script:

One fix before running: right after a draw is recorded, the "draws since last win" for that draw's winners is 0, not 1. So the "won in the last draw" flag must test for 0.

The fix is in place and the walk-forward run has started. The first models train when it reaches 2012, in about 5–10 minutes.

The script is committed. The evaluation is still running.

The run stopped after loading the data, without an error message. I'll rerun it in the foreground so the exit code shows:

It's running again with the memory fix.

I've pushed the memory fix. The evaluation is running.

An old monitor from the earlier astro run just expired. The ML evaluation is still running under its own monitor.

A crash in a progress-print line: `yrs` is a list of arrays, not numbers. That's only cosmetic, but it ended the run. Fixing and restarting:

It's restarted. I'll report each yearly retrain as it happens.

The 2012 models are trained (on 1.0 million rows). The validation and test years follow, with a retrain each year.

Still running; that notice was a duplicate from the older monitor.

Still running; that was another duplicate notice.

The 2013 models are trained. Each year takes about 100 seconds, so about 25 minutes remain.

Still running (2013 is done).

Still running.

2014 is done.

Still running (the 2014 retrain is done).

Still running; 2014 is done.

2015 is done.

Still running (2015 is done).

Three monitors are watching the same log, so every notice arrives three times. I'll stop the two old ones:

Now only one monitor is watching. The run has reached 2015, with 2016–2026 still to go.

2016 is done.

2017 is done. The test years (2018 onward) start next.

The 2018 models are trained. The test period has started.

2019 is done.

2020 is done.

2021 is done.

2022 is done.

2023 is done.

2024 is done. Two more years to go.

2025 is done.

The final-year (2026) models are trained; it's now scoring the 2026 draws.

All models are in. Before interpreting, I'll check where the selected model's apparent test lift comes from:

While the predictions run (about 15 minutes, since they replay the full history), I'll write up the results as section 9 of the report:

One bullet I just wrote is wrong: RM0.86 is *above* the random average of RM0.64, not below it. Correcting it:

I've pushed the report and results. The `ml_model.py` logging change gets committed along with the picks once the prediction run finishes.

The logging option is committed. The prediction run for 18 and 21 Oct is still going.

I added the TinyFish importer and built eight new non-linear models. None of them reliably beats random picking on draws they haven't seen.

**1. TinyFish importer.** `tinyfish_import.py` reads 4dmoon pages fetched through TinyFish and adds them to `data/*.csv`, skipping dates already there. Its 4 tests pass, and its output for 14 Oct matches the data exactly. The README explains how to use it.

**2. New models.** Each was retrained every year from 2012 using only earlier draws, validated on 2012–2017, and tested on 4,180 unseen draws from 2018 to Oct 2026.

| Model | What it is | Test top 10 | Test top 23 |
|---|---|---|---|
| A_all: boosted trees, everything | Digits plus number history plus Vedic and Chinese parameters; can learn interactions such as digit × nakshatra | 1.13× | 1.14× (z = +2.1) |
| A_astro: trees, Vedic and Chinese only | Digits plus Vedic and Chinese parameters | 1.03× | 1.08× |
| A_hist: trees, history only | Control model | 1.04× | 0.96× |
| C_digit | Separate tree model per digit position | 0.97× | 0.98× |
| **B_kernel β=0.1 (chosen in advance by the fixed rule)** | "Similar days": weights past dates by how many of 78 Vedic and Chinese parameters they share with the target date | **1.20× (z = +1.9)** | **1.13× (z = +2.0)** |
| B_kernel β=0.3 / 1.0 | Same, giving more weight to the most similar days | 1.06× / 1.18× | 1.08× / 1.09× |
| E_ens | Average of four of the models | 1.18× | 1.12× |

**Why I don't count the best results as a real edge:**
- **Multiple tries:** with 8 models and 4 pick sizes, a couple of results near z = 2 are expected by chance.
- **Failed validation:** the chosen kernel model was below random on 2012–2017 (0.91×).
- **Inconsistent:** the gains show up for different operators in different models: Da Ma Cai for the kernel, Sports Toto and Magnum for the trees.
- **Poorly calibrated:** every model assigns the actual winners lower probability than simply treating all numbers as equally likely.
- **Money:** the best Big Forecast return was RM0.86 per RM1. It still loses money, and a result that good is within what random picks can reach by luck alone.

**A quirk of the chosen model:** it mostly picks repeated-digit numbers (0000, 6666, 8808…) and gives the same picks for all three operators, because it pools all operators' results. Rare i‑Box groups such as AAAA get their whole group's score on a single number, so a few past wins on "similar days" push them up.

**Live test.** Picks from all new models for **Sun 18 Oct** and **Wed 21 Oct** were saved in `analysis/forward_log.csv` before those draws, alongside the earlier Vedic/Chinese formulas. After each draw I can fetch the results with TinyFish, import them, and run `python3 analysis/astro_model.py score`. Those draws are the only test none of the models has seen. For the 1.1–1.2× lifts to mean anything, they need hundreds of draws.

The code is in `analysis/ml_model.py`, results in `ml_model_results.json`, and section 9 of `analysis/REPORT.md` has the full write-up. Everything is pushed.

---

## 11. Question (2026-10-17 02:47)

> What is the top 5 formula that performed the best?

**Answer** (2026-10-17 02:48)

I ranked every formula I built on the same unseen test: 4,180 draws from 2018 to Oct 2026, all three operators, scored by how often the top 10 picks won any prize compared with random picks. None of the five is a proven edge; the reasons are below the table.

| Rank | Formula | Top 10 wins (vs 96 random) | Top 23 | Big return, top 10 (per RM1) | Validation 2012–17 (top 10) |
|---|---|---|---|---|---|
| 1 | **Similar-days kernel, β = 0.1** | 115 (1.20×, z = +1.9) | 1.13× (z = +2.0) | RM0.71 | 0.91× ✗ |
| 2 | **Ensemble (E_ens)** | 113 (1.18×, z = +1.7) | 1.12× | RM0.71 | 0.95× ✗ |
| 2 | **Similar-days kernel, β = 1.0** | 113 (1.18×, z = +1.7) | 1.09× | RM0.86 | 0.97× ✗ |
| 4 | **Digit formula (section 7)** | 111 (1.16×, z = +1.5) | 1.10× | RM0.63 | tuned there |
| 5 | **Gradient-boosted trees, all inputs (A_all)** | 109 (1.13×, z = +1.3) | 1.14× (z = +2.1) | RM0.57 | 1.03× |

**What each formula is:**

1. **Similar-days kernel (β = 0.1):**
   - Every past draw date gets a weight of e^(0.1 × number of the 78 Vedic and Chinese parameters it shares with the target date).
   - A number's score is its i‑Box group's weighted past wins, smoothed toward the group's normal share, then divided by the number of orderings in that group.
   - It uses Vedic and Chinese parameters only.
2. **Ensemble:** the average of four models' log-probabilities: A_all, A_astro (trees on Vedic/Chinese inputs only), the digit-position trees, and the kernel with β = 0.3.
3. **Similar-days kernel (β = 1.0):** the same as #1, with much more weight on the most similar days.
4. **Digit formula:** score = 0.05 × recent digit bias + 0.25 × digit frequencies on dates with matching parameters + 0.02 × i‑Box frequencies on matching dates.
5. **A_all:** 250 boosted trees over 33 inputs: the number's digits and pattern, its own win history, Vedic and Chinese lift scores, and 15 raw Vedic/Chinese parameters.

**Why none of these is a proven edge:**
- **Selection by luck:** about 15 formulas were tested, and the best of 15 random pickers would typically land around z = 1.7–2 by luck alone. All five sit in that range.
- **Validation failed:** the top three were at or below random on 2012–2017. A real effect should show up in both periods.
- **Inconsistent operators:** the gains come from different operators in different formulas.
- **Money:** every formula still loses on Big Forecast. Breaking even needs about 1.56× the random hit rate, kept up over many draws.

The live forward log (`analysis/forward_log.csv`) now holds picks from all of these for 18 and 21 Oct, saved before the draws. If one of them keeps around 1.2× over the next few hundred draws, that would be the first real evidence it works.

---

## 12. Question (2026-10-17 02:48)

> You still didn’t give me the formula for me to manually input

**Answer** (2026-10-17 02:53)

There are no formula errors. Now I'll check that the workbook gives the same top 5 as the Python formula, for 18 Oct and for a second date:

Here is a formula you can work out yourself. It uses six Vedic and Chinese parameters plus points tables, and I've put it in a workbook (`manual_formula.xlsx`, attached) that does the lookups when you type a date.

**The formula:**

```
Points(position p, digit d) = T1[Chinese year yin/yang] + T2[Venus combust?] + T3[Jupiter combust?]
                            + T4[Masa] + T5[Chinese year stem] + T6[Chinese lunar day]
```

Each T is a points table with 40 numbers per value: digits 0–9 for each of the 4 positions. The tables are on the **Tables** sheet.

- **Number 1:** take the digit with the most points in each position.
- **Numbers 2–5:** for each position, take the best and second-best digit. That gives 16 combinations; rank them by total points and take the next four.
- The same numbers apply to Magnum, Sports Toto and Da Ma Cai, because the tables pool all three operators.

A table entry is `round(100 × weight × log(share of digit d at position p on past dates with this value ÷ its overall share))`, built from every draw from 1985 to 14 Oct 2026. The six parameters and their weights were chosen on 2012–2017 draws and then frozen.

**Using it:**
1. Open the **Predict** sheet and type the draw date in the yellow cell B3.
2. The six parameter values come up automatically from the Calendar sheet (15 Oct 2026 to 28 Dec 2027).
3. The top 5 appear in column Q, with every step shown underneath.
4. To do it fully by hand: find the six values for your date in the Calendar, take each value's row from the Tables sheet, add the six rows together, and take the highest digit in each position.

**Example, Sun 18 Oct 2026:** Yang year, Venus combust, Jupiter not combust, masa Ashvin, year stem Bing, lunar day 9. Result: **9509, 9507, 9599, 9909, 8509**. I checked the workbook against the Python version on five dates and they match exactly. These picks are now also in the live forward log.

**How it performed on 2018–2026 draws it had never seen** (tables rebuilt each January from earlier draws only):

| | Wins of any prize | Random would give | Big Forecast per RM1 |
|---|---|---|---|
| Top 5 numbers | **66** | 48.1 (1.37×, z = +2.6) | **RM1.05** |
| Top 1 number | 13 | 9.6 (1.35×) | RM0.42 |

By operator, the top 5 did 1.30× on Magnum, 1.12× on Sports Toto and 1.70× on Da Ma Cai. It is the best result of everything tested, and it passed a check where the same pick schedule with random numbers swapped in matched it only 0.7% of the time. Playing the same five 9‑heavy numbers every draw gave only 1.04×, so the date parameters are doing the work, not just a liking for 9s.

**Before you bet:**
- **Possibly luck:** this was about the 16th formula tested. Allowing for that, a result this good could come from luck about 1 time in 10.
- **Same numbers for weeks:** the picks are mostly 9‑heavy and change slowly, because most of the six parameters change only monthly or yearly.
- **Few big prizes:** the RM1.05 return comes from a handful of prizes (2 first, 9 second, 2 third in 4,186 draws) and could disappear within a few draws.

The live forward log is the real test. After each draw, I can fetch the result with TinyFish and score the manual formula alongside the others. The workbook and its build scripts are pushed in `analysis/`.

---

## 13. Question (2026-10-17 02:55)

> How did it perform for the last Wednesday draw 14/10?

**Answer** (2026-10-17 02:55)

To keep the test fair, I'll rebuild the points tables from draws before 14 Oct only, since the published tables already include that draw, then score the picks against the official 4dmoon results:

The date index was off by one: my date list included an excluded duplicate date. I'll take the index from the loaded data instead:

The formula won nothing on Wednesday 14 Oct, and checking it showed that the workbook I sent you had a bug. The corrected formula is no better than random picking, so please don't rely on the earlier 1.37× result.

**14 Oct results.** Both versions are scored against the official 4dmoon results, with the tables built only from draws up to 11 Oct.

| Version | Top 5 picks | Straight wins | i‑Box matches |
|---|---|---|---|
| Version I sent you (has the bug) | 9999, 9989, 9899, 8999, 9889 | 0 | 0 |
| Corrected formula | 8796, 8726, 8799, 0796, 8729 | 0 | 0 |

**The bug.** I rounded each points-table cell to a whole number at too small a scale (×100), which turned most cells into 0. Three of the six tables were entirely zero. In 71% of digit positions the "best" digit was really a tie, and my tie-break rule chose the higher digit. That's why the picks were all 9s. The 1.37× result and the RM1.05 return came from that tie-break, not from the Vedic/Chinese parameters.

**Corrected formula (tables at ×10,000), tested on 2018–2026:** top 5 won 49 times against 48.1 expected (1.02×), returning RM0.63 per RM1. That is the same as random picking.

**What I fixed and updated:**
- **Workbook:** `manual_formula.xlsx` (re-sent) now has correctly scaled tables and honest test figures. It matches the Python formula exactly.
- **New picks:** 18 Oct is 9505, 9705, 9506, 9706, 9595; 21 Oct is 9746, 0746, 9706, 0706, 9745. Both versions' picks are in the forward log, labelled `manual` and `manual_v2`.
- **Report:** section 10 of `REPORT.md` records the correction. Everything is pushed.

**Where this leaves the project.** After every formula and model tried, simple and complex, Vedic, Chinese and combined, none beats random picking on draws it hasn't seen. The workbook is still a reproducible way to choose numbers from the parameters, but its picks are no more likely to win than any others.

---

## 14. Question (2026-10-17 03:02)

> Use other formulas that you have chosen and compare which one correctly predicted 14/10

**Answer** (2026-10-17 03:02)

I'll score every formula's picks for 14 Oct against the official results. For a fair test, each formula may only use draws before 14 Oct.

- **Already leak-free:** the section 7 formula, the three Vedic/Chinese formulas and both manual versions. Their 14 Oct picks were made when the data ended on 10 Oct.
- **Need a rerun:** the eight non-linear models from section 9 (trees, digit model, kernels, ensemble) must be rerun with 14 Oct's own results removed. I'm adding a `--before` cutoff for that:

While that runs (about 15 minutes), I'll prepare the scoring script with the picks I already have:

The scoring script is ready. I'll run it as soon as the leak-free picks from the eight models finish.

The cutoff option is pushed; the 14 Oct model run is still in progress.

**No formula predicted 14 Oct.** All 14 formulas, 420 picks in total, missed every prize as straight numbers. A few matched a winning number's digits in a different order, which would only pay if bet as i‑Box.

Every formula used only draws before 14 Oct, and all picks were checked against the official 4dmoon results for that day.

| Formula | Picks | Straight wins | i‑Box matches (expected by chance) | Matches |
|---|---|---|---|---|
| S9 boosted trees, all inputs (A_all) | 30 | 0 | **3** (1.0) | Magnum 6614 ~ 4661 (consolation); Toto 3184 ~ 4381 (consolation); DMC 5751 ~ 7155 (consolation) |
| S9 trees, Vedic/Chinese only (A_astro) | 30 | 0 | **2** (1.0) | Magnum 2493 and 4293 ~ 9432 (special) |
| S8 Chinese formula | 30 | 0 | 1 (1.0) | DMC 2941 ~ 1294 (consolation) |
| S9 trees, history only (A_hist) | 30 | 0 | 1 (1.0) | Toto 1898 ~ 8189 (consolation) |
| S9 digit-position model (C_digit) | 30 | 0 | 1 (1.0) | Toto 5382 ~ 8253 (special) |
| S7 digit formula | 30 | 0 | 0 (1.0) | – |
| S8 Vedic formula | 30 | 0 | 0 (1.0) | – |
| S8 Vedic + Chinese | 30 | 0 | 0 (1.0) | – |
| S9 similar-days kernels (β 0.1 / 0.3 / 1.0) | 30 each | 0 | 0 (1.0) | – |
| S9 ensemble | 30 | 0 | 0 (1.0) | – |
| S10 manual formula, buggy v1 | 15 | 0 | 0 (0.5) | – |
| S10 manual formula, corrected v2 | 15 | 0 | 0 (0.5) | – |

**What these numbers mean:**
- **Straight wins:** random picks would get about 0.07 per formula, so zero everywhere is the normal outcome.
- **i‑Box matches:** random picks would get about 1 per formula. The total across all formulas was 8, against about 13 expected.
- **Best on this draw:** A_all, with 3 matches. With 14 formulas, one of them getting 3 is ordinary luck: random picks reach 3 or more about 8% of the time.
- **Money:** as straight Big bets, every formula returned RM0. Had A_all's three numbers been bet as RM1 i‑Box, they would have paid about RM2.50 + RM2.50 + RM5.00 on RM3 staked. Under the same scheme, A_astro's two hits on special 9432 would have paid about RM7.50 each.

One draw can't separate the formulas. On the 4,180-draw forward test, all of them performed like random picking. The picks for 18 and 21 Oct are saved in advance in `analysis/forward_log.csv`; I can fetch those results with TinyFish after the draws and score every formula the same way.

---

## 15. Question (2026-10-17 03:12)

> Since you have a lot more of the formulas discovered try them all until one of them show high amount of predictions for 14/10

**Answer** (2026-10-17 03:13)

I'll run it, but first a warning about what this kind of search can and can't show. If you try enough formulas on one draw, some will "predict" it by luck alone. The real question is whether the winner keeps working on draws it wasn't picked for. So I'll do three things:

1. **Run every single-parameter formula on 14 Oct:** 468 formulas, one for each Vedic/Chinese parameter × 6 scoring types, each picking its top 10 per operator using only draws before 14 Oct.
2. **Run 468 sets of random picks the same way,** to show how many hits pure luck produces.
3. **Take the formula that scores best on 14 Oct and test it** on the 4,180 earlier draws from 2018–2026.

I'll save the search as a reusable script that reads the official results straight from `data/` (not a scratch file), so it can be rerun for any draw, then commit it:

I tried all 468 single-parameter formulas on 14 Oct (30 picks each, using only earlier draws). **36 of them hit one winning number. Random picks did exactly as well**, with 35 of 468 random sets hitting one.

| | Formulas (468) | Random picks (468 sets) |
|---|---|---|
| 0 straight hits | 432 | 433 |
| 1 straight hit | 36 | 35 |
| 2 or more | 0 | 0 |

**Best on 14 Oct: "Yellow/Black path, per operator".** It takes each operator's numbers that won most often on past Yellow-path days (14 Oct was Yellow path, Heavenly Virtue day). It caught **Sports Toto 2nd prize 0305**, which pays RM1,000 on RM30 of RM1 Big bets.

| Operator | Its 10 picks for 14 Oct |
|---|---|
| Magnum | 4554 0744 5501 4960 4580 8127 1527 4709 1024 3184 |
| Sports Toto | 6702 5949 0502 0019 **0305** ✓ 4891 1419 8827 7174 8726 |
| Da Ma Cai | 5124 0399 7136 0408 5452 9451 5686 7217 2289 6925 |

The runners-up each hit one number: Sports Toto 3rd prize 0606 (month branch, digits), and specials 9432, 1710, 0504 and 8480 (nakshatra, karana, ayana, year animal, day stem).

**Tested on the other 4,186 draws (2018–2026), predicting draw by draw from earlier data only:**

| Formula | Top 10 wins vs random | Big Forecast per RM1 |
|---|---|---|
| Yellow/Black path (winner on 14 Oct) | 1.17× (z = +1.6, not significant) | RM0.70 (loses) |
| Month branch | 0.99× | RM0.68 |
| Nakshatra | 0.96× | RM0.55 |
| Karana | 0.74× | RM0.51 |

So the formulas that "predicted" 14 Oct do no better than random on other draws, and all of them lose money. With 468 attempts, a few were bound to land on that day's numbers by luck, and random picks showed the same hit rate.

One quirk in the i‑Box column: some formulas show 9–10 i‑Box matches. That isn't skill. The i‑Box-type formulas pick all orderings of the same digits, so when one group matches, many picks match together.

If you want to keep testing Yellow/Black path, the fair way is to fix it now and score it only on future draws. I can add it to the forward log for 18 and 21 Oct; it hasn't been tried on those draws. `analysis/search_single_draw.py` reruns this search for any past draw date.

---

## 16. Question (2026-10-17 03:17)

> No no no I thought your suppose to find formula that learnt from previous draws and then test on 14/10 to see which one got a hit. Why did you do it in reverse

**Answer** (2026-10-17 03:17)

What I ran is what you described. Every formula learned only from earlier draws and then predicted 14 Oct; it never saw that day's results. The extra step afterwards may have made it look reversed.

**Step 1: learn from the past, predict 14 Oct (your test)**
1. Each of the 468 formulas built its tables from all draws up to 11 Oct only. The 14 Oct results were removed.
2. From those tables it picked its top 10 numbers per operator for 14 Oct.
3. Only then did I compare the picks with the actual 14 Oct results.

**Results for 14 Oct:**

| | Formulas that got a hit | Hit |
|---|---|---|
| Yellow/Black path (Chinese), per operator | 1 | **Sports Toto 2nd prize 0305** (RM1,000 on a RM30 Big stake) |
| Month branch (Chinese), digits | 1 | Sports Toto 3rd prize 0606 |
| Nakshatra, karana, ayana, year animal, day stem | 1 each | Specials 9432, 1710, 0504, 8480 |
| All 468 formulas | 36 got one hit; none got two | |

**Step 2: an extra check, not a reversal**

I added one more question: was the winner good, or lucky that day? Two checks:
- **Random comparison:** 468 sets of random picks for 14 Oct got 35 hits, against the formulas' 36.
- **Earlier draws:** I ran the winning formula forward the same way on every draw from 2018 to 2026. Each draw was predicted only from draws before it, and the formula scored 1.17× random, which is not significant, and still lost money.

So 14 Oct's best formula is Yellow/Black path, with Sports Toto 0305. The check says that hit was most likely luck, because random picks hit just as often.

To give it a real chance, I can fix Yellow/Black path now and log its picks for **Sun 18 Oct and Wed 21 Oct** before those draws, then score them when the results come out.

---

## 17. Question (2026-10-17 03:23)

> Ok for all those formulas redo but don’t train the last 3 draws and repeat the same to see how they perform for the rest of the last 3 know draws until 14/10

**Answer** (2026-10-17 03:24)

Yes. The last 3 known draws are **Sat 10 Oct, Sun 11 Oct and Wed 14 Oct**. For each one, every formula learns only from the draws before it, predicts that draw, and is then scored against its actual results. The formulas:
- the 468 single-parameter formulas;
- the S7 digit formula;
- the three S8 Vedic/Chinese formulas;
- the corrected manual formula;
- the 8 machine-learning models;
- 468 sets of random picks for comparison.

The 8 ML models need about 15 minutes per draw, so I'll start them in the background first:

While that runs, I'll write the test for everything else:

Two fixes before running: the S7 formula needs its own smoothing settings (read from its weights), and choosing the held-out dates shouldn't re-read the data files for every date:

That confirms it: on 14 Oct, the 36 "hits" were really only 18 different winning numbers, some caught by up to 8 formulas at once. I'll wait for the ML models to finish, then add them to the table:

The ML runs are still going. I'll put together the full comparison once they finish.

The hold-out test is committed. The ML runs for the three draws are still going.

I re-ran every formula on the last three draws — **10, 11 and 14 Oct** — this time without training on them. For each draw, each formula used only the results before it, predicted that draw, and then I checked its picks against the actual results. None of the named formulas won anything, and the single-parameter formulas hit at about the rate random picks would.

**Named formulas (10 picks per operator per draw, 5 for the manual one):**

| Formula | 10 Oct | 11 Oct | 14 Oct | Big return on stake |
|---|---|---|---|---|
| S7 digit formula | 0 | 0 | 0 | RM0 / RM90 |
| S8 Vedic / Chinese / combined | 0 | 0 | 0 | RM0 / RM90 each |
| S10 manual formula (corrected) | 0 | 0 | 0 | RM0 / RM45 |
| ML: A_all, A_astro, A_hist, C_digit | 0 | 0 | 0 | RM0 / RM90 each |
| ML: three similar-days kernels, ensemble | 0 | 0 | 0 | RM0 / RM90 each |

Random picks would average about 0.2 straight hits per formula over these three draws, so all zeros is the normal result.

**The 468 single-parameter formulas (30 picks each per draw):**

| Draw | Formulas with a straight hit | Random sets with a hit |
|---|---|---|
| 10 Oct | 42 | 21 |
| 11 Oct | 29 | 32 |
| 14 Oct | 36 | 32 |
| Hit on 2 or more of the 3 draws | 11 | 4 |

The formulas look ahead on 10 Oct and in the "2 or more" row, but that overstates them. Many formulas pick almost the same numbers, so one lucky number counts several times. On 14 Oct the 36 hits were only 18 different winning numbers, and one number was caught by 8 formulas at once. Random sets don't overlap like that.

**Best single-parameter formulas over the three draws:**

| Formula | Hits | Big return | What it caught |
|---|---|---|---|
| Jupiter nakshatra (Vedic), per operator | 2 | **RM2,680 / RM90** | Sports Toto **1st prize 1236** (10 Oct), Da Ma Cai special 9424 (11 Oct) |
| Yellow/Black path (Chinese), per operator | 2 | RM1,060 / RM90 | Sports Toto consolation 6702 (10 Oct), Sports Toto 2nd prize 0305 (14 Oct) |
| Month branch (Chinese), digits | 2 | RM680 / RM90 | Magnum special 6709, Sports Toto 3rd prize 0606 |
| Saturn combust (Vedic), per operator | 3 | RM180 / RM90 | three consolation numbers |

The Jupiter nakshatra formula's 1st-prize hit is what you'd expect from luck when you check 468 formulas: one of them will usually land a big hit somewhere. Earlier, when the Yellow/Black path formula was tested on 4,186 draws from 2018–2026, it scored 1.17× random and lost money overall.

If you want to give these a fair chance, I can lock in Jupiter nakshatra, Yellow/Black path and Month branch now and log their picks for **18 and 21 Oct** before those draws happen. That would be a genuine test. The full per-draw results are in `analysis/last_draws_results.json`, and `analysis/last_draws_test.py --n 3` re-runs the whole check.

---

## 18. Question (2026-10-17 03:47)

> How does those formula work? Explain it to me step by step

**Answer** (2026-10-17 03:48)

I'll pull the actual numbers behind each hit, so the explanation uses real values rather than a made-up example:

All three are the same simple recipe: find past draws that share one Vedic or Chinese value with today's draw, see which numbers (or digits) won more often than usual on those draws, and pick the top 10. Below are the steps, with the real numbers behind each hit.

## Formula 1: Jupiter nakshatra, per operator (caught Sports Toto 1st prize 1236 on 10 Oct)

1. **Find today's value.** On 10 Oct, Jupiter was in the nakshatra **Ashlesha**. Jupiter stays in one nakshatra for about 5 months, roughly once every 12 years.
2. **Collect matching past draws.** Take every earlier Sports Toto draw where Jupiter was also in Ashlesha: **280 draws**, with 6,432 winning numbers between them.
3. **Count each number's wins on those draws.** 1236 won **6 times**.
4. **Work out how many wins to expect** from the number's overall record. 1236 won 16 times out of 125,808 winning numbers overall, so in a sample of 6,432 you'd expect **0.71**.
5. **Score it:**
   `score = log( (wins on matching draws + 10) / (expected + 10) ) = log(16 / 10.71) = 0.401`
   The +10 is a damping cushion. It stops a number from jumping to the top after only one or two lucky wins.
6. **Rank all 10,000 numbers by score and take the top 10.** 1236 ranked **#1 of 10,000**, and it won 1st prize.

## Formula 2: Yellow/Black path, per operator (caught Sports Toto 2nd prize 0305 on 14 Oct)

The steps are the same, with a different parameter:
1. 14 Oct was a **Yellow path** day (day god: Heavenly Virtue) in the Chinese almanac.
2. Past Sports Toto draws on Yellow-path days: **2,731 draws**, 62,745 winning numbers. That's about half of all draws, because roughly half of all days are Yellow.
3. 0305 won **16 times** on those days, against **7.89** expected.
4. Score = log((16 + 10) / (7.89 + 10)) = **0.374**, which ranked **#5**, so it made the top 10 and won 2nd prize.

Because Yellow days are half of all days, this formula is mostly just "Sports Toto's all-time hottest numbers". 0305 won 16 of its 21 lifetime wins on Yellow days.

## Formula 3: Month branch, digits, per operator (caught Sports Toto 3rd prize 0606 on 14 Oct)

This one scores digits in each position rather than whole numbers:
1. 14 Oct falls in the Chinese solar month **Xu** (the Dog month).
2. Past Sports Toto draws in Xu months: **460 draws**, 10,565 winning numbers.
3. For each position, compare how often each digit appeared there in those draws with its usual share:

| Position | Digit in 0606 | Share in Xu months | Usual share | Points: log(share ÷ usual) |
|---|---|---|---|---|
| 1st | 0 | 10.55% | 10.04% | +0.050 |
| 2nd | 6 | 10.33% | 9.94% | +0.039 |
| 3rd | 0 | 10.39% | 9.97% | +0.041 |
| 4th | 6 | 10.16% | 9.98% | +0.019 |

4. Add the four positions: 0606 scores **+0.150**, which ranked **#10**. It just made the top 10 and won 3rd prize.

The shares are lightly smoothed toward normal (equivalent to adding 50 average draws), so rarely seen values have little effect.

## Why these hits don't mean the formulas work

- **The scores are tiny.** In formula 3 the digit edges are 0.2–0.5 percentage points above the normal 10%, which is the size of ordinary random wobble.
- **Some number always looks hot.** Among 10,000 numbers, the luckiest one in any 280-draw slice will win several times more than expected. 1236's 6 wins against 0.71 expected is about what the luckiest one looks like by chance.
- **Many formulas were tried.** These three were the best of 468 formulas on three draws. With that many attempts, a few big hits are almost guaranteed, and random picks reached about the same hit counts.
- **They don't hold up over many draws.** Tested across 2018–2026, the Yellow/Black path formula scored 1.17× random and lost money. The other two scored about random.

So each formula is a simple, repeatable recipe: "numbers or digits that won more than expected when today's parameter last had this value". The hits on these three draws are consistent with luck. I can log their picks for 18 and 21 Oct now, before the draws, so we can see whether they hit again on draws they haven't seen.

---

## 19. Question (2026-10-17 03:51)

> Ok now do the same analysis but this time train before the last 5 draws, and then test for the last 5 draws and tell me how they perform for the selected formula

**Answer** (2026-10-17 03:51)

I'll freeze all training at the cutoff this time. Each formula learns once from the draws before the 5th-to-last draw, then predicts all 5 held-out draws with no updates in between. I'll report the three selected formulas (Jupiter nakshatra, Yellow/Black path, Month branch) in detail, plus the other formulas and the random baseline for context. First, which are the last 5 draws:

The ML run is still going; I'll add its results when it's done.

The hold-out changes are committed and pushed. The ML run for the 5 draws is still going.

All formulas were trained once on draws before 4 Oct, then predicted the last five draws (4, 7, 10, 11 and 14 Oct) with no retraining in between. On the two draws that are a real test for the three selected formulas, 4 and 7 Oct, all three scored 0.

**The three selected formulas (10 picks per operator, 30 per draw):**

| Formula | 4 Oct | 7 Oct | 10 Oct | 11 Oct | 14 Oct | Total | Big Forecast return |
|---|---|---|---|---|---|---|---|
| Jupiter nakshatra (Vedic) | 0 | 0 | ✓ Sports Toto **1236, 1st** | ✓ Da Ma Cai 9424, special | 0 | 2 hits | RM2,680 on RM150 |
| Yellow/Black path (Chinese) | 0 | 0 | ✓ Sports Toto 6702, consolation | 0 | ✓ Sports Toto **0305, 2nd** | 2 hits | RM1,060 on RM150 |
| Month branch (Chinese) | 0 | 0 | 0 | ✓ Magnum 6709, special | ✓ Sports Toto **0606, 3rd** | 2 hits | RM680 on RM150 |

**These numbers flatter the formulas.** I picked these three *because* they hit on 10, 11 and 14 Oct in the last round, so hits on those dates were guaranteed to appear in this test. The only new evidence is 4 and 7 Oct, and there all three scored **0 out of 60 picks each**.

**Everything else:**
- **Named formulas:** the S7 digit formula, the three S8 Vedic/Chinese formulas, the corrected manual formula and all 8 ML models got **0 hits on all 5 draws**, so RM0 back on each stake.
- **468 single-parameter formulas:** they hit about as often as random picks on each draw:

| Draw | Formulas with a hit (of 468) | Random sets with a hit (of 468) |
|---|---|---|
| 4 Oct | 33 | 33 |
| 7 Oct | 32 | 35 |
| 10 Oct | 41 | 29 |
| 11 Oct | 28 | 28 |
| 14 Oct | 38 | 39 |

- **Random comparison:** 31% of random 30-pick sets hit at least once over these 5 draws, and 4% hit twice or more. The average random set returned **RM111 on RM150**.
- **Other two-hit formulas:** with 468 formulas, about 4% (around 19) should reach two hits by luck, and 29 did. These overlap heavily: several picked the same numbers, so one lucky number counts several times.
- **Big returns:** a few, like Jupiter retrograde and Nine Star year, caught a 1st prize. That is what you'd expect when one formula out of hundreds catches one.

Over these five draws, nothing does better than random once the selection bias is taken out. The fair way to check the three selected formulas is to lock them in now and score them on draws they have never seen: Sun 18 Oct and Wed 21 Oct. I can log their picks before those draws if you want.

---

## 20. Question (2026-10-17 03:58)

> Ok since we have only tested 3 formulas, try the top 6 formulas, the other 3 best performing that we have not tested

**Answer** (2026-10-17 03:58)

The next three best formulas from the 3-draw test are:
- **Saturn combust (per operator):** 3 hits;
- **Mercury nakshatra (i‑Box)** and **Mars retrograde (i‑Box, per operator):** 2 hits each, both with RM560 Big return.

KP Ascendant star lord tied with those two, but it hit the same numbers.

I'll score these three on the same frozen 5-draw test. Then I'll run all six selected formulas over the 4,186 draws from 2018–2026, each draw predicted only from the draws before it, as a proper long test:

The next three best formulas — Saturn combust, Mercury nakshatra and Mars retrograde — did no better than the first three. All six missed both draws they weren't chosen on (4 and 7 Oct), and none beats random over 2018–2026.

**Last 5 draws.** Every formula was trained once on draws before 4 Oct.

| Formula | 4 Oct | 7 Oct | 10 Oct | 11 Oct | 14 Oct | Big return on RM150 |
|---|---|---|---|---|---|---|
| Jupiter nakshatra (per operator) | 0 | 0 | Toto 1236 **1st** | DMC 9424 special | 0 | RM2,680 |
| Yellow/Black path (per operator) | 0 | 0 | Toto 6702 consolation | 0 | Toto 0305 **2nd** | RM1,060 |
| Month branch (digits) | 0 | 0 | 0 | Magnum 6709 special | Toto 0606 **3rd** | RM680 |
| **Saturn combust (per operator)** | 0 | 0 | Toto 7078 + 6702 consolation | 0 | DMC 4482 consolation | RM180 |
| **Mercury nakshatra (i‑Box)** | 0 | 0 | DMC 7972 consolation | DMC 9772 **3rd** | 0 | RM560 |
| **Mars retrograde (i‑Box, per operator)** | 0 | 0 | DMC 7972 consolation | DMC 9772 **3rd** | 0 | RM560 |

All six were chosen for their hits on 10, 11 and 14 Oct, so only 4 and 7 Oct are a real test, and there every formula scored 0. Mercury nakshatra and Mars retrograde also caught exactly the same two numbers. That is one result counted twice, not two formulas agreeing.

**Long test, 2018–2026.** Each of 4,186 draws was predicted using only the draws before it. A real edge would need about 1.56× random just to break even on Big Forecast.

| Formula | Top 10 vs random | Big return per RM1 |
|---|---|---|
| Yellow/Black path | 1.17× (z = +1.6) | RM0.70 |
| Jupiter nakshatra | 1.07× (z = +0.7) | RM0.79 |
| Saturn combust | 1.06× (z = +0.6) | RM0.77 |
| Mars retrograde | 1.04× (z = +0.4) | RM0.57 |
| Month branch | 0.99× (z = −0.1) | RM0.68 |
| Mercury nakshatra | 0.94× (z = −0.6) | RM0.66 |

All six fall within random variation, and all six lost money. The results also swing between operators: for example, Yellow/Black path is 1.24× on Magnum but 1.00× on Sports Toto.

**Unseen test.** I've logged all six formulas' picks for **Sun 18 Oct and Wed 21 Oct** in `analysis/forward_log.csv`, recorded before those draws. Most of these parameters change slowly, so the picks barely change between draws. Some even repeat their recent hits, like Toto 1236 and DMC 9424. Example picks for 18 Oct:
- **Jupiter nakshatra:** Toto 1236 8305 5677 6113 0947 …
- **Saturn combust:** DMC 0399 5025 9655 4482 9632 …
- **Mercury nakshatra:** 9773 and its rearrangements, for all operators.

After each draw I can fetch the results with TinyFish, import them, and score all six.

---

## 21. Question (2026-10-17 04:09)

> It’s weird how only those 2 days where 4/10 and 7/10 has no hits. Try to use the same theory of the top formulas such as the nakshatra, you ask to choose the top 10 best for that, rather than focusing on Jupiter Nakshatra, try for the Nakshatra itself. And also do note that, the draw time is at 7pm to 7:30pm everyday. Maybe this can help

**Answer** (2026-10-17 04:09)

Two good ideas, and I'll test both.

1. **The whole nakshatra family, not just Jupiter's.** I'll test every nakshatra-type parameter:
   - the nakshatra of the Moon (the standard nakshatra), Sun, Mars, Mercury, Venus, Jupiter, Saturn, Rahu and the Lagna (Ascendant);
   - the Moon's nakshatra pada;
   - the nakshatra lords: the Moon's, plus the KP star lords of the Moon, Ascendant and Sun.

   Each one is tested with all 6 scoring types, and each formula picks its top 10 numbers. I'll also build one **combined nakshatra formula**: its terms are chosen on 2012–2017 only, then frozen.
2. **Draw time 7:00–7:30 pm.** So far every parameter was computed at exactly 7:00 pm. Most don't change within 30 minutes. The ones that can are the **Lagna**, which moves about 7° in half an hour and often changes nakshatra, the Ascendant's KP star lord, and occasionally the Moon's nakshatra or pada. So I'll recompute those at **7:15 pm and 7:30 pm** and test each timing separately.

Each will get the same two tests: the frozen last-5-draw test (trained before 4 Oct), and 2018–2026 draw by draw. On 4 and 7 Oct, the last round's top formulas had all been chosen for their hits on the other three draws. That selection is why those two days looked empty.

The test is running: 156 formulas, made up of 26 nakshatra-type parameters (including the 7:15 and 7:30 pm versions) × 6 scoring types. The draw-by-draw 2018–2026 test takes about 15 minutes.

As expected, the draw time matters mainly for the Lagna. Its nakshatra at 7:30 pm differs from the 7:00 pm value on **56%** of draw dates, and at 7:15 pm on 28%. The Moon's nakshatra almost never changes in that half hour (1–2% of dates). The tests are continuing.

The frozen 5-draw test is done, and the 2018–2026 test for all 156 formulas is running now.

Looking at all nakshatras at three draw times did produce hits on 4 and 7 Oct, but overall the nakshatra formulas still score no better than random picks. Testing at 7:15 or 7:30 pm instead of 7:00 pm didn't help either.

**1. Last 5 draws.** I tested 156 formulas: 26 nakshatra-type parameters × 6 scoring types, each trained once on draws before 4 Oct.

| Formula | 4 Oct | 7 Oct | 10 Oct | 11 Oct | 14 Oct | Big return on RM150 |
|---|---|---|---|---|---|---|
| Sun nakshatra (i‑Box) | Magnum 6301 **2nd** | DMC 3106 **3rd** | – | – | – | RM1,500 |
| Lagna nakshatra at 7:15 / 7:30 pm (i‑Box) | Magnum 6301 **2nd** | DMC 3106 **3rd** | – | – | – | RM1,500 |
| Jupiter nakshatra (per operator) | – | – | Toto 1236 **1st** | DMC 9424 special | – | RM2,680 |
| KP Ascendant star lord at 7:15 pm (digits) | Magnum 2306 special | – | Toto 4164 **2nd** | – | – | RM1,180 |
| Sun nakshatra (digits) | Magnum 9852 special | – | Magnum 9856 special | – | – | RM360 |

- The Sun nakshatra and the 7:15/7:30 pm Lagna nakshatra picked exactly the same numbers. At a fixed clock time the Lagna is set by where the Sun is, so both are really measuring the time of year. That's one result, not three.
- Across all 156 formulas, the average was **0.31 hits per formula against 0.29 for random picks**. Thirteen formulas got 2 or more hits against 4 random sets, but many of them pick the same numbers, as above.

**2. Draw by draw, 2018–2026 (4,186 draws, each predicted only from earlier draws):**
- **z above 2:** 3 of the 156 formulas did better than random by z > 2. Pure chance would produce about 3.6, so this is exactly what luck looks like.
- **Best by hit rate:** Saturn nakshatra (per operator), 1.30× random (z = +2.9), and KP Ascendant star lord at 7:30 pm, 1.30× (z = +2.9). Both still lost money: RM0.96 and RM0.85 back per RM1.
- **Best by return:** Moon nakshatra pada at 7:15 pm, RM1.04 per RM1. The same formula at 7:00 pm returned RM0.87, and at 7:30 pm RM0.94 with exactly random hits. A real effect wouldn't swing like that across 15 minutes.
- **Combined nakshatra formula:** 8 terms chosen on 2012–2017, then frozen. It scored 0.96× random over 2018–2026 and got 0 hits in the last 5 draws.

**3. Draw time.** The Lagna nakshatra at 7:30 pm differs from 7:00 pm on 56% of draw dates, and at 7:15 pm on 28%. The Moon's nakshatra barely changes in that half hour (1–2% of dates). Even so, the average lift of the time-sensitive formulas was 1.036× at 7:00 pm, 1.013× at 7:15 pm and 1.016× at 7:30 pm, so timing makes no measurable difference.

The only way to know whether Saturn nakshatra or KP Ascendant star lord is more than luck is to fix them now and score them on future draws. I can add them to the forward log for 18 and 21 Oct alongside the six already there. The full results are in `analysis/nakshatra_results.json`, and `analysis/nakshatra_test.py` reruns everything.

---

## 22. Question (2026-10-17 04:29)

> Ok since all this are single parameter, I have a theory that certain parameter promotes win and brings down the win. Do investigate that for pairs parameter. And redo all the analysis and tell me how it perform for the last 5 draws compared to all other leads

**Answer** (2026-10-17 04:30)

Good theory, and it can be tested directly. If some parameters push wins up and others push them down, two things should show:
- **Single parameters work in both directions.** Some should help with a **positive** weight (their "hot" numbers win more) and others with a **negative** weight (their "hot" numbers win *less*, so they bring a number down). So far I only allowed positive weights.
- **Pairs beat singles.** Either an **additive pair** (one parameter's score plus or minus another's) or a **joint pair** (numbers that win when *both* values occur together, such as nakshatra Rohini on a Yellow-path day) should do better than either parameter alone.

To keep it honest, I'll use the same protocol as before:
1. **Score on 2012–2017** (counting from draws before 2012): every single parameter with positive and negative weights, all additive pairs among the strongest 30 single terms, and all 3,003 joint pairs.
2. **Freeze the 10 best pairs** and commit them before testing.
3. **Test them** on 2018–2026 draw by draw, and on the last 5 draws (trained before 4 Oct), then compare with every earlier lead.

First, a change so joint pairs fit in memory:

Next, the forward-test helper also needs to skip those tables for joint-pair formulas:

The pair screening is running. Stage A scores the single parameters with positive and negative weights, stage B the additive pairs, and stage C the 3,003 joint pairs. After that, the 10 frozen pair formulas get the 2018–2026 and last-5-draw tests.

The code is committed and pushed. The screening is still running.

Stage A is done (468 single terms scored on 1,074 validation draws). The pair stages are running now.

The additive pairs are scored (428). The 3,003 joint pairs are next.

The screening is done, and the formulas are frozen. Before the tests run, I'm committing the frozen pairs as a record that they were chosen first:

Stage A already says something about your theory. Of the 468 single terms:
- **65** help with a positive weight ("promote");
- **127** help with a negative weight ("suppress").

So "suppressing" looks twice as common. There's a statistical reason to expect exactly that, though, which I'll explain with the final results. The 2018–2026 and last-5-draw tests of the 10 frozen pairs are running now.

Your theory is partly right in form but not in practice. Pairs that combine one "promoting" parameter with one "suppressing" parameter do come out on top during tuning, but on unseen draws they still predict no better than random. The best one, Day stem (promote) + Sun rashi (suppress), scored 1.10× random over 2018–2026, which isn't significant, and still lost money.

**1. Single parameters can push either way.** I allowed each of the 468 single terms a positive or negative weight and scored them on 2012–2017.
- **Count:** 65 helped as promoters (their "hot" numbers won more) and 127 as suppressors (their "hot" numbers won *less*).
- **Strongest promoters:** day stem and day element (Chinese, i‑Box) and month Nine Star.
- **Strongest suppressors:** Mercury rashi, Sun rashi and Venus nakshatra.
- **Why suppressors outnumber promoters:** numbers that looked hot under some condition in old data tend to cool off later (regression to the mean). So a negative weight usually wins by a little.
- **Chance level:** about 150 of the 468 would look helpful by chance anyway; 192 did.

**2. Pairs, chosen on 2012–2017 and frozen before testing.** I scored all 428 additive pairs (one parameter plus or minus another) and 6,005 joint pairs (both values together, such as Venus retrograde *and* a Fire day).
- The 10 strongest pairs were all additive, and most were "promoter + suppressor": Day stem with Mercury rashi, Sun rashi, Venus nakshatra or Sun nakshatra. That matches the shape of your theory.
- In a joint pair a specific *combination* of values (for example Venus retrograde on a Fire day) gets its own table. Joint pairs scored lower; I tested the top 3 anyway.

**3. How they performed on unseen draws:**

| Pair formula | 2018–2026 top 10 vs random | Big return per RM1 | Last 5 draws (4–14 Oct) |
|---|---|---|---|
| Day stem (+) & Sun rashi (−) | 1.10× (z = +1.0) | RM0.78 | 0 hits |
| Day stem (+) & Mercury rashi (−) | 1.08× | RM0.64 | 0 |
| Mercury rashi (−) & Day element (+) | 1.06× | RM0.64 | 0 |
| Day stem (+) & Nine Star month (+) | 1.04× | RM0.73 | Magnum 9432 special (14 Oct) |
| Mercury rashi (−) & Nine Star month (+) | **0.74× (z = −2.6)** | RM0.51 | DMC 8926 consolation (10 Oct) |
| Other 5 additive pairs | 0.93–1.03× | RM0.42–0.71 | 0 |
| Joint: Venus retrograde × Day element | 1.04× | RM0.37 | Toto 9184 special (4 Oct) |
| Joint: Venus retrograde × Day stem | 0.99× | RM0.53 | Magnum 9152 special (14 Oct) |
| Joint: Day stem × Day element | 1.04× | RM0.63 | Magnum 9432 special (14 Oct) |

**4. Last 5 draws, pairs against every earlier lead.** Each pick set has 30 numbers per draw (10 per operator), trained once before 4 Oct.

| Lead | How it was chosen | Average hits over the 5 draws | Best return on RM150 |
|---|---|---|---|
| **13 pair formulas** | on 2012–2017 (fair) | 0.38 | RM180 |
| Saturn nakshatra, KP Ascendant star lord (×2) | on 2018–2026 (fair) | 0 | RM0 |
| S7/S8/manual formulas, 8 ML models | on earlier years (fair) | 0 | RM0 |
| Six singles (Jupiter nakshatra, Yellow/Black path, …) | on their 10/11/14 Oct hits (biased) | 2–3, but **0 on 4 and 7 Oct** | RM2,680 |
| Sun nakshatra (i‑Box) | on these same 5 draws (biased) | 2 | RM1,500 |
| **Random picks** | – | **0.36** (31% of sets hit at least once) | RM111 on average |

Among leads chosen fairly, the pair formulas average 0.38 hits against random's 0.36, so they are the same as random. The only leads with big returns were picked *after* seeing these draws, so their hits were counted in their own favour.

**Bottom line.** Promoter-plus-suppressor pairs are the best-structured idea so far, but none holds up on unseen draws.

The cleanest next step is to lock the best pair (Day stem + Sun rashi) and the top joint pair into the forward log for **18 and 21 Oct**, alongside the earlier leads.

Everything is saved in `analysis/pairs_formulas.json` (committed before any testing) and `analysis/pairs_results.json`, and `analysis/pairs_test.py` reruns the whole search.

That notice was only the old nakshatra-test monitor timing out. That test had already finished, and nothing has changed.

---

## 23. Question (2026-10-17 05:00)

> The performance are still bad, so far you choose the best performing numbers from the history of the parameters and then, reuse them in the future. Rather than doing that, try to find 3 other strategy that might work, I give you one. Maybe choose the top performing numbers for each position and then you’ll get 1 number from there, and then the second best number 2^4=16 + 1. Check all those variations to see if it is able to predict based on single parameter and also pairs. Find 3 other strategy. And check the performance for the last 5 draws

**Answer** (2026-10-17 05:01)

Your idea is a genuinely different kind of strategy: build numbers digit by digit instead of reusing whole past winners. I'll test it alongside three other strategies of my own:

| # | Strategy | How it picks for a draw |
|---|---|---|
| **S1 (yours)** | **Hot digits per position** | For the date's parameter value(s), find which digit came up most often in each of the 4 positions → **1 number**. Use the top-2 digits per position → **2⁴ = 16 numbers** (the 16 already include the 1 number). |
| **S2** | **Cold digits per position (reversion)** | The same construction, but using the *least* frequent digits. The pair test found far more parameters acting as "suppressors" than as "promoters", so this checks whether that pattern can be turned into wins. |
| **S3** | **Return of the parameter** | When a parameter value comes back (for example the next Rohini day), replay the winners from the last time it occurred, in prize order: the previous 1st prize = 1 pick, the top 16 = 16 picks. |
| **S4** | **Previous-draw transforms** (popular folk systems, no parameters) | Take the same operator's previous draw and use its 1st–3rd prizes repeated as-is, mirrored (each digit +5), reversed, or the permutations of the 1st prize. |

S1–S3 run for **all 78 single parameters and all 3,003 pairs** (each per operator). I'll check them three ways:
- **Tuning:** pick the best formulas on 2012–2017.
- **Long test:** score them on 2018–2026, with each year predicted only from earlier draws.
- **Last 5 draws:** train only on draws before 4 Oct, then score all 5 against random picks of the same size.

Two fixes before running: the "last time this value occurred" lookup needs vectorising (as written it would take about 25 minutes), and the permutation list needs tidying:

The combination logic checks out: combo #1 is the best digit in every position. Running the full test:

The test is running across 3,081 parameter sets (78 single parameters and 3,003 pairs) for S1–S3, plus the S4 folk systems. I'll report the results when it finishes.

The test script is committed and pushed; the test itself is still running.

It has finished 500 of 3,081 parameter sets, which puts it about 7 minutes from done.

1,000 of 3,081 parameter sets are done.

1,500 of 3,081 are done, roughly halfway.

2,000 of 3,081 are done.

2,500 of 3,081 are done.

Nearly done: 3,000 of 3,081 parameter sets are finished.

None of the four strategies predicts better than random, whether driven by a single parameter or a pair. Your positional-digit method (S1) matched random picking almost exactly on the last 5 draws. The one interesting result came from a version that uses no parameters at all.

I ran each strategy for all 78 single parameters and all 3,003 pairs, per operator. Every year from 2012 to 2026 was predicted only from earlier years; the last 5 draws (4–14 Oct) were predicted with training frozen before 4 Oct. A random-pick baseline was scored on those same draws.

**Last 5 draws (5 draws × 3 operators):**

| Strategy | Picks per operator-draw | Formulas that got at least 1 hit | Random picks: chance of at least 1 hit |
|---|---|---|---|
| S1 hot digits per position (yours) | 1 | 4% | 3% |
| S1 hot digits per position (yours) | 16 | 42% (0.55 hits on average) | 41% (0.55 hits) |
| S2 cold digits per position | 1 / 16 | 3% / 39% | 3% / 41% |
| S3 replay last same-value draw | 1 / 16 | 6% / 26% | 3% / 41% |
| S4 repeat / mirror / reverse previous 1st–3rd | 3 | 0% | 10% |
| S4 permutations of previous 1st prize | 16 | 0% | 41% |

**Best formula per strategy, chosen on 2012–2017 and then tested:**

| Strategy | Best on 2012–2017 | 2012–2017 | 2018–2026 | Last 5 draws |
|---|---|---|---|---|
| S1, 1 number | KP Moon star lord × KP Sun number | 2.43× | 1.04× | 0 |
| S1, 16 numbers | Jupiter combust × KP Ascendant star lord | 1.31× | 0.96× | 0 |
| S2, 16 numbers | Jupiter retrograde × Day element | 1.36× | 0.96× | 1 special (RM180) |
| S3, 1 number | KP Moon star lord × KP Sun number | 2.62× | 1.23× (z = +0.7) | 0 |
| S3, 16 numbers | Day pillar × Tai Sui relation | 1.30× | 1.01× | 1 consolation |
| S4 | Mirror of previous 1st–3rd | 1.26× | 1.18× (z = +1.0) | 0 |

Every winner from 2012–2017 fell back to about 1.0× afterwards. Across the 3,081 formulas in each strategy, the number with z above 2 on 2018–2026 was about what chance produces, apart from S1/S2 with 1 pick, explained next.

**The one interesting result has no parameters in it.** S1 and S2 with 1 pick showed more z‑above‑2 formulas than chance (140 and 158 against about 71). I traced that to a version with no parameters at all: each operator's overall most-frequent (hot) or least-frequent (cold) digit in each position.

| No-parameter version (1 number per operator) | 2012–2017 | 2018–2026 |
|---|---|---|
| Hot digits | 0.54× | 1.56× (15 hits vs 9.6) |
| Cold digits | 1.49× | **2.18× (21 hits vs 9.6)** |

These picks barely change from year to year, and a few numbers carry the hits. Magnum's cold pick was **6666**, which won 12 times from 2013 to 2026 against about 5 expected. Sports Toto's were 5668 / 8568 and Da Ma Cai's were 512x. So the parameter formulas looked good mainly when their picks fell back to these same numbers.

It's the same kind of lead as 1024: real-looking, but found after the fact by searching. On the last 5 draws, the hot version caught one consolation prize (Magnum 7484, 14 Oct) and the cold version caught nothing.

**On the after-the-fact last-5 winners.** If I pick formulas by their last-5 results, Cold × Year element × Day stem tops the list with 7 hits and RM2,660 back on RM240. Its 2018–2026 result is only 1.02×. Ranking formulas on the very draws they're scored on always produces winners like this.

**What's queued for a fresh test.** The no-parameter hot and cold picks are now in the forward log for **18 and 21 Oct**, recorded before the draws:

| Operator | Hot, 1 number | Cold, 1 number | Cold, 16 numbers |
|---|---|---|---|
| Magnum | 8884 | 6665 | 6665, 6666, 6635, 6636, 6265, 6266, … |
| Sports Toto | 1191 | 5568 | 5568, 5569, 5578, 5579, 5668, … |
| Da Ma Cai | 4090 | 3122 | 3122, 3126, 3112, 3116, 3522, … |

The code is in `analysis/strategies_test.py` and the full results are in `analysis/strategies_results.json`, both committed and pushed. If you'd like, I can fetch the 18 Oct results with TinyFish after the draw and score every logged strategy.

---

## 24. Question (2026-10-17 05:18)

> he one interesting result has no parameters in it. S1 and S2 with 1 pick showed more z‑above‑2 formulas than chance (140 and 158 against about 71). I traced that to a version with no parameters at all: each operator's overall most-frequent (hot) or least-frequent (cold) digit in each position. For this how did it perform for the last 5 draws?

**Answer** (2026-10-17 05:18)

I already have the scores from the earlier run, but I'll recompute to show the exact numbers each version picked, counting only draws before 4 Oct:

On the last 5 draws (4, 7, 10, 11 and 14 Oct) it did badly. The **hot** version caught one consolation prize, and the **cold** version, the stronger one over 2018–2026, caught nothing. Both versions counted digits only from draws before 4 Oct, then kept the same picks for all 5 draws.

**Hot version (most frequent digit per position)**

| Operator | #1 number | All 16 numbers | Hits on the last 5 draws |
|---|---|---|---|
| Magnum | 8884 | 8884 8888 8874 8878 8484 8488 8474 8478 7884 7888 7874 7878 7484 7488 7474 7478 | **7484 consolation on 14 Oct** |
| Sports Toto | 1191 | 1191 1194 1131 1134 1391 1394 1331 1334 3191 3194 3131 3134 3391 3394 3331 3334 | none |
| Da Ma Cai | 4090 | 4090 4095 4000 4005 4890 4895 4800 4805 9090 9095 9000 9005 9890 9895 9800 9805 | none |

- **1 number per operator:** 0 hits in 15 operator-draws.
- **16 numbers per operator:** 1 hit, which pays RM60 back on RM240 staked.

**Cold version (least frequent digit per position)**

| Operator | #1 number | All 16 numbers | Hits on the last 5 draws |
|---|---|---|---|
| Magnum | 6665 | 6665 6666 6635 6636 6265 6266 6235 6236 0665 0666 0635 0636 0265 0266 0235 0236 | none |
| Sports Toto | 8568 | 8568 8569 8578 8579 8668 8669 8678 8679 5568 5569 5578 5579 5668 5669 5678 5679 | none |
| Da Ma Cai | 3122 | 3122 3126 3112 3116 3722 3726 3712 3716 5122 5126 5112 5116 5722 5726 5712 5716 | none |

- **1 number per operator:** 0 hits.
- **16 numbers per operator:** 0 hits, so RM0 back on RM240.

**Compared with random picks on the same 15 operator-draws:**
- **1 number per operator-draw:** random picks average 0.03 hits, so both versions' 0 is normal.
- **16 numbers per operator-draw:** random picks average 0.55 hits, and 41% of random sets hit at least once. Hot's 1 hit is about average; cold's 0 is slightly below.

**Why 5 draws can't settle it.** Over 2018–2026, the cold version's 1 number per operator won 21 times in about 4,200 operator-draws, roughly one hit every 200 operator-draws. At that rate, 0 hits in 15 operator-draws is the expected result even if the 2.18× edge were real. To tell a real 2.18× edge from luck, you'd need several hundred future draws.

These exact picks are already in the forward log for **18 and 21 Oct**, recorded before those draws. If you'd like, I can fetch the 18 Oct results with TinyFish after the draw and score them.

---

## 25. Question (2026-10-17 05:21)

> How about the one with single parameter and double parameter for S1 and S2? For the last 5 draw?

**Answer** (2026-10-17 05:21)

I'll recompute the last-5 results for S1 and S2, split into single-parameter and pair formulas, with training frozen before 4 Oct as before:

Over the last 5 draws (4–14 Oct), the S1 and S2 formulas performed about the same as random picks, whether built on one parameter or a pair. All were trained once on draws before 4 Oct; each pick count is per operator per draw, so 15 operator-draws in total.

**All formulas compared with random picks:**

| Strategy | Formulas | Picks | Formulas with ≥1 hit | Random picks with ≥1 hit | Average hits (random) |
|---|---|---|---|---|---|
| S1 hot, single parameter | 78 | 1 | **8%** | 3% | 0.077 (0.034) |
| S1 hot, single parameter | 78 | 16 | 41% | 42% | 0.47 (0.54) |
| S1 hot, pair | 3,003 | 1 | 4% | 3% | 0.038 (0.034) |
| S1 hot, pair | 3,003 | 16 | 42% | 42% | 0.55 (0.54) |
| S2 cold, single parameter | 78 | 1 | 1% | 3% | 0.013 (0.034) |
| S2 cold, single parameter | 78 | 16 | 45% | 42% | 0.60 (0.54) |
| S2 cold, pair | 3,003 | 1 | 3% | 3% | 0.028 (0.034) |
| S2 cold, pair | 3,003 | 16 | 39% | 42% | 0.53 (0.54) |

The only row above random is **S1 hot, single parameter, 1 pick: 8% against 3%**. That's 6 hits from 78 formulas where about 3 were expected. Several of those formulas picked the same number, though. For example, Sun nakshatra and Solar term both picked Magnum **9852** on 4 Oct, a special prize, because both depend on the Sun's position. Counted as distinct picks, it's within luck.

**Best performers on these 5 draws.** These are ranked after the fact, so they flatter themselves:

| Strategy | Formula | Hits | Big Forecast return (staked) |
|---|---|---|---|
| S1, 1 pick, pair | Weekday × Ayana | Magnum **5087 1st** (7 Oct) | RM2,500 (RM15) |
| S1, 1 pick, pair | Moon rashi × Day god | Toto **2723 1st** (7 Oct) | RM2,500 (RM15) |
| S1, 16 picks, pair | Mercury nakshatra × Venus rashi | 4 hits incl. Toto **1236 1st** | RM2,920 (RM240) |
| S1, 16 picks, pair | Day stem × Day god | 4 hits incl. Magnum **5471 1st** | RM2,800 (RM240) |
| S2, 16 picks, pair | Year element × Day stem | **7 hits** incl. Toto 0857 2nd, DMC 1233 2nd | RM2,660 (RM240) |
| S2, 16 picks, pair | Saturn rashi × KP Ascendant number | 4 hits incl. DMC **1293 1st** | RM2,800 (RM240) |
| S2, 1 pick, pair | Saturn rashi × Solar term | DMC 4925 2nd + Toto 8418 special | RM1,180 (RM15) |
| S1, 16 picks, single | Mars rashi / Month stem | 2 hits each | RM240 (RM240) |
| S2, 16 picks, single | Lunar month | 3 hits incl. DMC 3106 3rd | RM740 (RM240) |

**Why these big wins don't point to a working formula:**
- **Many formulas were tried.** With 3,003 pairs, about 3% (around 100) will catch at least one prize with a single pick by luck, and some of those prizes will be 1st prizes. Each of these winners is one lucky pick out of many.
- **They didn't hold up over time.** For example, Year element × Day stem (7 hits) scored 1.02× random over 2018–2026, and Day stem × Day god scored 1.10×.
- **The picks that held up earlier didn't win here.** The best formulas from 2012–2017 for each strategy got 0–1 hits on these 5 draws.

The full per-formula detail is in `analysis/strategies_last5_detail.json`. If you want to give the top performers a fair test, I can lock them in now and log their picks for **18 and 21 Oct** before those draws, then score them with TinyFish afterwards.

---

## 26. Question (2026-10-17 05:30)

> Ok do more analysis on S1 and S2 for parameters focus on the one that is able to hit more commonly. This time try different combinations of parameters or maybe 3 different parameters combined and tell me how they perform with the last 5 draws after training. You need to make sure it predicts the training and testing both in a positive manner

**Answer** (2026-10-17 05:30)

This round looks for formulas that are positive in **both** periods, so it needs care. Requiring good results on 2018–2026 makes 2018–2026 part of the selection, so it no longer counts as an independent test. That leaves the last 5 draws as the only clean check. Here's the plan:

1. **Periods.**
   - Training check (validation): 2012–2017.
   - Second check: 2018 to **3 Oct 2026**. It now stops before the last 5 draws, so they stay unseen.
   - Final check: the last 5 draws (4–14 Oct), with everything frozen before 4 Oct.
2. **What gets scored.**
   - **Combinations:** every single parameter and all 3,003 pairs.
   - **Triples:** three-parameter combinations built from the 20 parameters that turn up most often among the consistent pairs (1,140 triples).
   - **Strategies:** S1 (hot) and S2 (cold), each with 1 and 16 picks.
3. **Consistency filter.** A formula must beat random in **both** periods. I'll also count how many would pass by luck: with no real effect, about 1 in 4 formulas clears "above random in both" by chance.
4. **Final scoring.** The 10 most consistent formulas per strategy are then scored on the last 5 draws.

It's running across 4 cores: singles and pairs first, then the 1,140 triples.

The old monitor is still replaying the previous run's errors. I'll stop it and check that only the new run is going:

The cleanup command also stopped the new run, because its pattern matched that command's own text. Nothing is running now, so I'll start it again cleanly:

The run is going again, with a new monitor that only reports progress and real errors.

The same error came back, so my earlier fix probably wasn't saved. Checking the file:

Confirmed: the earlier fix never reached the file, because that whole command was stopped before it ran. Applying it with the editor this time:

The fix is in and the run has started over. I'll report when the singles and pairs are done.

The pool fix is committed and pushed. The S1/S2 combos run is still going.

An old monitor expired; that test finished earlier. The combos run is still going under its own monitor.

The singles and pairs are done. The 20 parameters chosen for the triples include day element, the 7 pm hour stem, masa, Mars nakshatra, Moon rashi and the Yellow/Black path. The 1,140 triples are running now.

I searched S1 (hot digits) and S2 (cold digits) over single parameters, pairs and triples, and kept only formulas that beat random in both checks. On the 5 unseen draws (4–14 Oct), those shortlisted formulas did no better than random overall. A few individual formulas did catch big prizes, including one Magnum 1st prize.

How I tested:
- **Formulas tried:** 78 single parameters, 3,003 pairs, and 1,140 triples. The triples were built from the 20 parameters that appeared most often among pairs that were consistent across both checks.
- **Two checks:** each formula had to beat random on 2012–2017 and again on 2018 to 3 Oct 2026, with each year counted only from earlier draws.
- **Final test:** the 10 most consistent formulas in each group were frozen and scored on the 5 unseen draws. Picks are per operator per draw, over 15 operator-draws.

**1. How many formulas passed both checks:**

| | Above random in both | By chance | z > 1 in both | By chance |
|---|---|---|---|---|
| S1, 1 pick: single / pairs / triples | 33% / 31% / 28% | ~25% | 4 / 133 / 41 | 2 / 75 / 28 |
| S1, 16 picks | 33% / 25% / 33% | ~25% | 2 / 66 / 43 | 2 / 75 / 28 |
| S2, 1 pick | 35% / 26% / 30% | ~25% | 6 / 73 / 30 | 2 / 75 / 28 |
| S2, 16 picks | 31% / 24% / 33% | ~25% | 4 / 79 / 56 | 2 / 75 / 28 |

The pass rate is only slightly above chance, for two reasons:
- **S1 1-pick pairs:** its excess comes from the no-parameter digit picks noted last time. Many formulas end up picking the same few numbers, so their hits overlap.
- **Triples:** they look better partly because their 20 parameters were already chosen using both checks, so they had a head start.

**2. Last 5 draws: total hits for the 10 shortlisted formulas in each group:**

| Group | Single | Pairs | Triples | 10 random pick-sets would get |
|---|---|---|---|---|
| S1 hot, 1 pick | **2** | 0 | 0 | 0.34 |
| S1 hot, 16 picks | 4 | 3 | 3 | 5.4 |
| S2 cold, 1 pick | 0 | 0 | **1** | 0.34 |
| S2 cold, 16 picks | 5 | 5 | 5 | 5.4 |

Across all 60 shortlisted formulas:
- **1 pick:** 3 hits, against about 2 for random picks.
- **16 picks:** 25 hits, against about 33 for random picks.

Passing both checks did not carry over to unseen draws.

**3. Shortlisted formulas that hit on the last 5 draws:**

| Formula (all chosen before these draws) | Picks | Hit | Big return |
|---|---|---|---|
| **S2: Mars nakshatra × Mars rashi × Mercury combust** | 16 | Magnum **3872 1st prize** (14 Oct) | **RM2,500 on RM240** |
| S2: Lunar leap month × Venus combust × Mercury combust | 1 | Toto **9069 3rd** (10 Oct) | RM500 on RM15 |
| S2: KP Ascendant star lord × Day god | 16 | Toto 7078 + DMC 7208 consolation | RM240 on RM240 |
| S1: Nayin × Yellow/Black path × Nakshatra pada | 16 | Toto 2485 + Magnum 7484 consolation | RM240 on RM240 |
| S1: Mercury combust | 16 | Toto 1311 + Magnum 7484 consolation | RM120 on RM240 |
| S1: Month pillar | 1 | Magnum 6709 special (11 Oct) | RM180 on RM15 |

The Magnum 1st prize, 3872 on 14 Oct, was predicted by a formula fixed before that draw. With 60 shortlisted formulas each making 16 picks a draw, though, one of them hitting a top prize somewhere in 5 draws is fairly likely by chance. A single big hit can't show the formula works.

The two standouts are **Mars nakshatra × Mars rashi × Mercury combust (S2, 16 picks)** and **Lunar leap month × Venus combust × Mercury combust (S2, 1 pick)**. The proper next step is to lock them in now and log their picks for **18 and 21 Oct** before those draws, as with the other leads. All results are in `analysis/s12_combos_results.json`, and `analysis/s12_combos.py` reruns the search.

---

## 27. Question (2026-10-17 05:36)

> Ok wait just so that you and I are in the same page, the analysis is suppose to be like this. You need to know the parameter for today’s draw to be predicted and then compare the parameter that is similar to today’s draw to see and analyse S1 and S2, you seems to compile everything regardless of the parameters

**Answer** (2026-10-17 05:37)

We are on the same page. The tests already did that, draw by draw, so "everything regardless of the parameters" only describes the no-parameter baseline. For each draw being predicted, every S1/S2 formula:

1. computes that draw's own parameter values, e.g. 14 Oct: Mars in a given nakshatra, Mars in a given rashi, Mercury combust yes/no;
2. keeps only the past draws (same operator) with exactly the same value(s);
3. counts digits by position in those matching draws only;
4. takes the top 1 or top 2 digits per position, giving 1 or 16 numbers.

So each draw gets its own matching set of past draws. The one exception is the no-parameter baseline (S1/S2 "no parameter"), which deliberately ignores parameters as a control.

Here is the actual working for 14 Oct, using the formula that caught the Magnum 1st prize:

Yes, this is what the analysis does: every prediction uses only past draws whose parameters match the draw being predicted. Here is that working for 14 Oct, Magnum.

**Step 1: the draw's parameters.** Wed 14 Oct, 7 pm: Mars in **Pushya** nakshatra, Mars in **Karka** rashi, Mercury **not combust**.

**Step 2: keep only past draws with the same values.** There were **189 past Magnum draws** (before 4 Oct) with all three values the same, containing 4,341 winning numbers. These come in clusters whenever Mars passes through Pushya, most recently 26 Sep – 3 Oct 2026 and May 2025. All other draws are ignored for this prediction.

**Step 3: count digits per position in those 189 draws only.**

| Position | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1st | 446 | 440 | 426 | 418 | **404** | 437 | 444 | 421 | **482** | 423 |
| 2nd | **474** | 429 | 423 | 427 | 432 | 448 | **399** | 467 | 413 | 429 |
| 3rd | 424 | **415** | 445 | 427 | 426 | 423 | 423 | 422 | 444 | **492** |
| 4th | **460** | 420 | **414** | 445 | 443 | 421 | 416 | 439 | 433 | 450 |

**Step 4: build the numbers.**
- **S1 (hot):** best digits 8‑0‑9‑0 → number #1 is **8090**. Adding the second-best digits (0‑7‑2‑9) gives 16 numbers: 8090 8099 8020 8029 8790 … 0729.
- **S2 (cold):** least frequent digits 4‑6‑1‑2 → number #1 is **4612**. Adding the second-least (3‑8‑7‑6) gives 16 numbers: 4612 4616 4672 … **3872** 3876.
- **Result:** Magnum's 1st prize that day was **3872**, one of the 16 S2 numbers.

The important caveat is in the table itself. Each digit appears about 434 times on average, and random variation alone moves counts by about ±20. Here they range from 399 to 492, which is mostly that ordinary randomness. So the "hot" and "cold" digits for a given set of parameters are close to random, and that's why the method hits at about the random rate overall.

One other reading of your idea would be a real change. Instead of matching **exactly** on 1–3 parameters, I could take the past draws that are **most similar overall** to the draw being predicted. For example: the 200 past draws that share the most of the 78 Vedic/Chinese parameter values with that day, then S1/S2 on those. Do you want me to run that version, and test it the same way on the last 5 draws?

---

## 28. Question (2026-10-17 05:38)

> So for 17 Oct, we can’t use this Mars thingy right? Since it would have changed, the parameters for 17 Oct is different

**Answer** (2026-10-17 05:38)

Partly right. The **formula** stays the same: always "Mars nakshatra × Mars rashi × Mercury combust". The **values** are worked out fresh for each draw date, though, so on 17 Oct it automatically uses 17 Oct's Mars and Mercury positions and matches against past draws with those values.

Whether the values have changed by 17 Oct depends on the planets. Mars moves slowly and stays in one nakshatra for about 3–4 weeks, so its values may still be the same. I'll check the actual values for the next draws and work out the picks, using all results up to 14 Oct:

You're right that the values change. Mars has moved from **Pushya to Ashlesha** nakshatra since 14 Oct, so the formula now matches a different set of past draws and gives different numbers. The formula itself stays the same: "Mars nakshatra × Mars rashi × Mercury combust".

| Draw | Mars nakshatra | Mars rashi | Mercury combust |
|---|---|---|---|
| Wed 14 Oct | Pushya | Karka | No |
| **Sat 17 Oct** | **Ashlesha** | Karka | No |
| Sun 18 Oct | Ashlesha | Karka | No |
| Wed 21 Oct | Ashlesha | Karka | No |

For 17, 18 and 21 Oct it uses only past draws from when Mars was last in Ashlesha in Karka with Mercury not combust. That's 165 past Magnum draws, 144 Sports Toto and 150 Da Ma Cai. All three dates have the same values, so they get the same numbers, built from all results up to 14 Oct:

| Operator | S1 hot #1 | S2 cold #1 | S2 cold, 16 numbers |
|---|---|---|---|
| Magnum | 9340 | 4666 | 4666 4667 4616 4617 4066 4067 4016 4017 6666 6667 6616 6617 6066 6067 6016 6017 |
| Sports Toto | 1315 | 0428 | 0428 0426 0438 0436 0828 0826 0838 0836 8428 8426 8438 8436 8828 8826 8838 8836 |
| Da Ma Cai | 1999 | 4366 | 4366 4362 4346 4342 4166 4162 4146 4142 2366 2362 2346 2342 2166 2162 2146 2142 |

All these picks, including S1's 16 numbers, are in `analysis/forward_log.csv`. They were logged at 05:38 UTC on 17 Oct, before tonight's 7 pm draw (11:00 UTC), and pushed.

This formula caught Magnum's 1st prize on 14 Oct, but its digit counts sit within normal random variation, so its odds for 17 Oct are about the same as random picks. Mars stays in Ashlesha until about early November, so the numbers will stay the same until then.

After tonight's draw I can fetch the 17 Oct results with TinyFish and score these picks along with all the other logged leads.

That monitor timed out after its run had already finished, so nothing is lost. The 17 Oct picks are logged and pushed, ready to be scored after tonight's draw.

---

## 29. Question (2026-10-17 06:10)

> I think there is a better performing one than this, please create a python code and start analysing them on other ways to train those data to make this a predictive model

**Answer** (2026-10-17 06:11)

I'll build a proper training framework for the parameter-matched digit approach, with several ways to train it. All of them follow the same protocol:

- **Fitting:** each model is fitted only on draws before the period it predicts.
- **Tuning:** settings are tuned on 2012–2017.
- **Testing:** models are tested on 2018 to 3 Oct 2026.
- **Final check:** the last 5 draws, with everything frozen before 4 Oct.

The new training methods:

| Model | How it learns digit probabilities for the draw being predicted |
|---|---|
| **Global** | Each operator's overall digit frequencies, with no parameters (baseline) |
| **Match + smoothing** | S1/S2 as now, but counts from matching past draws are blended with the operator's overall frequencies, with the blend strength tuned. Cells with few matching draws are no longer pure noise. |
| **Backoff** | For a triple: triple-match counts, falling back to the pair, then the single parameter, then overall, each step smoothed |
| **Similar-days (kNN)** | All past draws weighted by how many of the 78 Vedic/Chinese parameter values they share with the draw being predicted (your "compare to similar days" idea, using every parameter at once) |
| **Softmax regression** | A regularised model per digit position that learns which parameter values push each digit up or down (promoters and suppressors) |
| **Ensemble** | Averages the probabilities of the N formulas that scored best on 2012–2017 |

On scoring:
- **Model selection:** besides hits, every model is scored by **how much probability it gave the actual digits** that came out. That uses all 92 digits per draw instead of a handful of hits, so it is far less noisy, and it decides which model is best.
- **Building numbers:** each model then builds numbers the S1 way (most likely digits) and the S2 way (least likely digits), as 1 or 16 per operator.

The models are training now. Of the six model types, the softmax regression is the slowest, so the full run may take 30–60 minutes. I'll report results as each one finishes.

The code is committed and pushed. The first result is the **global** baseline (no parameters):
- **Digit probabilities:** its digit log-likelihood is slightly *negative* in both periods. Each operator's overall digit frequencies predict the next draw's digits a little worse than assuming every digit is equally likely.
- **Hits:** it repeats the earlier odd result: cold digits with 1 pick per operator gave 2.19× random over 2018–2026.

Next, 114 parameter combinations from the earlier search are being trained with smoothing.

The tuning picked the **strongest smoothing (1000)**, which pulls the parameter-matched counts strongly back toward the operator's overall digit frequencies. That is an early sign the parameters add very little. Training continues.

The first similar-days model, using the 52 Vedic parameters, has finished:
- **Digit probabilities:** slightly negative in both periods, the same as the global baseline.
- **Test period:** close to random.
- **Last 5 draws:** 2 hits with the cold 16 numbers.

The other similar-days models are still running.

With β = 0.3, which leans harder on the most similar days, the Vedic similar-days model got clearly worse at predicting digits (−0.87 / −1.18). The more weight it puts on similar days, the worse it predicts. The Chinese and combined versions are next.

The Chinese similar-days model (26 parameters, β = 0.1) came out about the same as the global baseline. Still running.

Chinese similar-days with β = 0.3 is slightly worse again. Still running.

Similar-days on all 78 parameters (β = 0.1) also lands at about the same level as the global baseline. One more similar-days setting is left, then the softmax regression.

All six similar-days models are done. The more closely each one matches days, the worse it predicts: with all 78 parameters at β = 0.3, digit log-likelihood falls to −3.3 / −3.6. The softmax regression is training next; it's the slowest part.

The first softmax regression (strongly regularised, C = 0.001) is also worse than assuming all digits are equally likely (−3.8 / −3.4). It's learning patterns from the training years that don't carry forward. The second softmax setting and the ensembles are next.

Softmax with weaker regularisation (C = 0.01) overfits even more: −15 / −13. The ensembles are the last step.

The 5-formula ensemble is also at the global-baseline level. It caught 3 hits with the hot 16 numbers on the last 5 draws. The 20-formula ensemble is the last one.

All models are done. Here's a summary of the match and backoff formulas, which were too many to print one by one:

I built and tested six new ways of training the digit-position (S1/S2) approach. **None of them predicts the actual digits better than assuming every digit is equally likely (10% each)**, either on the tuning years or on the test years. The more a model relies on the parameters, the worse it gets, so there's no "better one" hiding in these methods.

**How each model was scored:**
- **Main score:** how much probability the model gave the digits that actually came out. That uses all 92 digits per draw, not just a handful of hits, so it's far less noisy. A positive score means better than 10% per digit; a negative score means worse.
- **Hits:** each model also built the hot (S1) and cold (S2) numbers, 1 or 16 per operator, scored as before.
- **Periods:** tuned on 2012–2017, tested on 2018 to 3 Oct 2026, then the last 5 draws with everything frozen before 4 Oct.

| Model | Digit score, 2012–17 / 2018–26 (milli-nats per digit) | Test hits vs random (hot 16 / cold 16) | Last 5 hits (hot 16 / cold 16) |
|---|---|---|---|
| Global (no parameters) | −0.11 / −0.13 | 1.02× / 1.09× | 1 / 0 |
| **Similar-days, 52 Vedic parameters, β = 0.1 (selected)** | **−0.10 / −0.14** | 1.00× / 1.10× | 0 / 2 |
| Similar-days, Chinese / all 78, β = 0.1 | −0.11 / −0.14 to −0.15 | 1.05× / 1.04–1.06× | 1 / 1 |
| Similar-days, β = 0.3 (closer matching) | −0.17 to −3.3 / −0.19 to −3.6 | 0.94–1.06× / 1.00–1.13× | 0–1 / 1 |
| Exact match + smoothing (126 formulas) | best −0.11, typical −0.57 | about 1.0× | average 0.47 (random 0.54) |
| Backoff triple → pair → single (39 formulas) | best −0.30, typical −1.4 | about 1.0× | average 0.56 (random 0.54) |
| Softmax regression (learns promoters/suppressors) | −3.8 / −3.4, and −15 / −13 with less regularisation | 0.87–0.93× / 1.00–1.06× | 0–1 / 0–1 |
| Ensemble of the best 5 / 20 formulas | −0.11 / −0.14 | 0.93–0.95× / 1.11–1.13× | 3 / 0 and 2 / 0 |

**What these results show:**
- **No positive scores.** Not one of the 165 match and backoff formulas scored positive in both periods, and none of the other models did either. The score never went above zero.
- **Parameters made it worse.** Tuning chose the strongest smoothing setting, which pulls predictions back toward each operator's overall digit frequencies. The best models were simply the ones that relied on the parameters least.
- **Flexible models overfit.** Closer similar-day matching and the softmax regression scored worst. They learn patterns from the training years that don't repeat.
- **Last 5 draws: random.** Every model landed at about random: 0.47–0.56 hits per 16-number set, against 0.54 for random picks.

**The cold 1-pick result** (one number per operator from the least frequent digits) still shows about 2× random in test hits: 2.19× for the global model and 2.30× for the 20-formula ensemble. But the digit scores say these models don't predict digits at all. So that result comes from a few specific numbers that happened to win several times, such as Magnum 6666, not from a pattern the model learned. It's already in the forward log as an after-the-fact lead.

I ran one more test for completeness: the earlier gradient-boosted trees using the same digit scoring. Together with everything before, the conclusion is the same: after this many approaches, the digit-by-position frequencies under Vedic and Chinese parameters don't carry information you can learn and use to predict.

The code is in `analysis/digit_models.py`, with results in `analysis/digit_models_results.json`, both pushed. To get picks for a date from any match or backoff model, run `python3 analysis/digit_models.py predict --date 2026-10-18 --model "match[...] a=1000"`.

---

## 30. Question (2026-10-17 06:35)

> OK so far which is the best performing leads?

**Answer** (2026-10-17 06:35)

I'll pull the Big Forecast returns for the top two leads, so they can be compared on money as well as hits:

Over 2018–2026, the cold one-number pick returned RM3.46 per RM1, which can only come from a few big prizes. Checking which ones:

The searches didn't find those draws, so I'll try TinyFish's search for an independent results archive:

Confirmed: **Magnum 1st prize 6666 on 25 Dec 2018** appears on two independent sites (4dkingdom.com and 4dinsingapore.com), so it isn't a data error. Checking two more from that list on 4dkingdom:

Two leads stand out. Everything else performs like random picking.

## 1. The cold-digit number, with no parameters

**The rule:** for each operator, take the **least frequent digit in each position** across all its past results to build one number. For example, Magnum's least-common digits over its history give 6666, and later 6665.

| | Hits | Random expectation | **1st prizes** | Big Forecast return |
|---|---|---|---|---|
| 2012–2017 | 11 | 7.4 | – | RM1.15 per RM1 |
| 2018 – Oct 2026 | 21 | 9.6 | – | **RM3.46 per RM1** |
| **2012–2026 total** | **32** | **17** | **6 (≈0.7 expected)** | profitable in both periods |

The 6 first prizes were Magnum **6666** (26 Oct 2014 and 25 Dec 2018), Sports Toto **5668** (6 Jul 2019), **5568** (17 Apr 2022) and **8568** (17 Jul 2024), and Da Ma Cai **5122** (11 Aug 2024).
- **Data checked against an independent site:** I confirmed three of them on 4dkingdom.com, which isn't the 4dmoon source behind my data: Magnum 6666 on 25 Dec 2018, Toto 5668 on 6 Jul 2019 and DMC 5122 on 11 Aug 2024. A second site, 4dinsingapore.com, also shows the 6666. So these are real results, not data errors.
- **Hard to explain by luck alone:** one number per operator per draw should win a 1st prize about 0.7 times in 15 years. Six or more happens by chance roughly 1 time in 8,000.
- **But I found it after the fact.** It began as a control I added to a much larger search, so the odds above overstate how surprising it is. Allowing for all the rules I've looked at, it is still unusual, but not proof.
- **Last 5 draws:** 0 hits. That's normal, since a single number hits less than once every 200 operator-draws even at twice the random rate.
- **Next draws:** its picks are already in the forward log: **Magnum 6665, Sports Toto 5568, Da Ma Cai 3122**.

## 2. 1024

- **Overall:** it's the most frequent number in the whole dataset, 79 wins against 41.5 expected, and it stayed above average after 2012 (29 wins against 17).
- **On Magnum since 2012:** 13 wins in 2,483 draws, returning **RM1.64 per RM1** on Big Forecast.
- **On Sports Toto and Da Ma Cai:** it loses, at RM0.46 and RM0.42 per RM1.
- **Caveat:** like lead 1, it's a single number found by looking through the data.

## Everything else is at random level

| Lead | Best result on unseen draws | Verdict |
|---|---|---|
| Saturn nakshatra; KP Ascendant star lord at 7:30 pm | 1.30× (z = +2.9) but loses money | About what chance gives across 156 formulas |
| Yellow/Black path, Jupiter nakshatra and the other single-parameter formulas | 0.94–1.17× | Random |
| Pairs and triples, S1/S2 parameter formulas, similar-days, softmax, ensembles | 0.9–1.1×, digit probabilities worse than random | Random |
| Mars nakshatra × Mars rashi × Mercury combust (Magnum 1st prize on 14 Oct) | 1.13× | One lucky hit |
| Magnum's digit bias, 7s under-drawn in 2019–2025 | Real, but too small to profit from and ended Nov 2025 | Historical only |

**What would test lead 1 properly.** The striking part is the 1st prizes. One clear question would sharpen it: **do 1st-prize numbers come from a different digit mix than the other 22 prizes?** For example, are an operator's overall "cold" digits more common in 1st prizes? If they are, there's a mechanism, and lead 1 becomes a real candidate. If not, it was most likely a lucky streak. I can run that test next if you want.

Sources used to check the first prizes: [4dkingdom 25 Dec 2018](https://www.4dkingdom.com/past-results/2018-12-25), [4dinsingapore 25 Dec 2018](https://4dinsingapore.com/4d-results/magnum-4d-25-12-2018/), [4dkingdom 6 Jul 2019](https://www.4dkingdom.com/past-results/2019-07-06), [4dkingdom 11 Aug 2024](https://www.4dkingdom.com/past-results/2024-08-11).

---

## 31. Question (2026-10-17 06:41)

> ok carryout the test

**Answer** (2026-10-17 06:41)

I'll test it from three directions. Each cold or hot digit is worked out only from that operator's results **before** each draw:

1. **Digit level:** in each position, is the 1st-prize digit the operator's historically *cold* digit more often than the digits of the other 22 prizes in the same draw? The other prizes act as a built-in control. I'll also compare the average "hotness rank" of 1st-prize digits against the rest.
2. **Number level:** how often does the cold number land in each prize slot (1st, 2nd, 3rd, special, consolation)? Every slot should get the same rate if nothing special is going on.
3. **Overall digit mix:** chi-square tests of whether 1st-prize digits are distributed differently from the other prizes, per operator and per position.

The lead was found in **2012–2026** data, so **1995–2011** serves as an independent check.

The test found nothing that makes 1st prizes different. They don't favour cold digits, and in the period that played no part in finding this lead (1995–2011), the cold number never won a 1st prize. The 1st-prize streak looks like luck.

**1. Digit level: is the 1st-prize digit the cold digit more often than the other prizes' digits in the same draw?**

| Period | 1st-prize digits that were the cold digit | Other 22 prizes | Difference |
|---|---|---|---|
| 1995–2011 (independent check) | 10.01% | 9.97% | z = +0.3, none |
| 2012–2026 (where the lead was found) | 10.33% | 10.09% | z = +1.4, not significant |

The average "hotness rank" of the digits (0 = hottest, 9 = coldest) was also the same: 4.49 against 4.49, and 4.51 against 4.51. 1st prizes are not drawn from colder digits.

**2. Number level: how often the cold number landed in each prize slot**

| Slot | 1995–2011: hits (expected) | 2012–2026: hits (expected) |
|---|---|---|
| **1st** | **0 (0.82)** | **5 (0.74)**, p = 0.001 |
| 2nd | 0 (0.82) | 0 (0.74) |
| 3rd | 0 (0.82) | 0 (0.74) |
| Special | 9 (8.2) | 12 (7.4) |
| Consolation | 9 (8.2) | 11 (7.4) |

The excess appears only in 2012–2026, the period where I found the lead. In the independent earlier period the same rule won no 1st prize at all.

**3. Overall digit mix of 1st prizes against the other prizes.** I ran 12 chi-square tests, one per operator and digit position.
- **1995–2011:** total 104.7 against 108 expected, p = 0.57.
- **2012–2026:** total 100.9 against 108 expected, p = 0.67.

The digit mix of 1st prizes is indistinguishable from the rest.

**The streak also depends on the exact rule.** Here I updated the cold digits after every draw, where earlier I refreshed them once a year. That small change turns the 6 first prizes into 5, and some of them are different numbers: Toto 9568 in 2012 shows up, while 5668 (2019) and 5568 (2022) drop out. A real effect wouldn't move around like that. A lucky run does.

**Updated verdict on the top lead:**
- **Mechanism:** none found. 1st prizes aren't colder.
- **Independent check:** failed, with 0 first prizes in 1995–2011.
- **Whole period:** 5 first prizes against about 1.6 expected over 1995–2026 (p ≈ 0.02). That's no longer remarkable once you allow for the hundreds of rules tested.

So the cold-number lead is best explained as a lucky streak in 2012–2026, like 1024. Its picks stay in the forward log, but there's no reason to expect them to beat random.

After everything tested (single parameters, pairs, triples, positional digits, similar days, trees, regressions and ensembles), I haven't found anything that reliably predicts 4D results. The draws behave like fair random draws. The scripts and results are in `analysis/first_prize_test.py` and `analysis/first_prize_results.json`, both pushed.

---

## 32. Question (2026-10-17 06:45)

> what are other way to create a predictive model try 5 other ways

**Answer** (2026-10-17 06:47)

I'll try five approaches that haven't been used yet in this project. Each one rests on a different theory of how a pattern could exist:

| # | Model | Idea | Kind of model |
|---|---|---|---|
| **M1** | **Change-point detector** | Draw machines get replaced or wear out, so digit biases may switch on and off (as Magnum's did in 2019–2025). It detects regime changes as they happen and uses only the current regime. | Bayesian online change-point detection |
| **M2** | **Draw-to-draw autoregression** | Do the digits in the last 1, 5, 20 or 100 draws (same operator and the other two operators) predict the next draw's digits? | Ridge vector autoregression |
| **M3** | **"Overdue" hazard curve** | Formally fits how a number's chance of winning depends on how long since it last won ("due" or "repeat" behaviour), as a flexible curve learned from history. | Survival / hazard model |
| **M4** | **Neural network** | A multi-layer perceptron combining recent digit history, the other operators' latest results, the date's Vedic/Chinese parameters and operator, able to learn non-linear interactions. | MLP neural network |
| **M5** | **Number-shape model** | Predicts the *type* of number rather than the number itself (repeated-digit pattern × digit-sum range × count of odd digits, 150 classes), using recent trends. | Structural class model |

**Testing protocol:**
- **Tuning:** each model's settings are tuned on 2012–2017.
- **Test period:** 2018 to 3 Oct 2026.
- **Last 5 draws:** each model's fitted settings are frozen before 4 Oct. The models that work draw by draw (M1, M2, M3, M5) may still use the previous draw's results as input, as they would in real use.
- **Scoring:** by how much probability each model gives the actual results (digits, or numbers for M3/M5), plus hits for the top 1 and top 16 numbers.

One problem before it gets far: M1 calls Python's `lgamma` about 250 million times, which would take hours. sklearn has installed SciPy, so I'll switch to SciPy's vectorised version and restart:

The kill matched its own command line again (it contained the file name), so the patch didn't run. The model run is stopped. Applying the patch on its own now:

The patch is in. One old process still seems to be running, so I'll find it by its process ID and stop it:

Nothing was left running; the earlier count was just the check matching itself. Starting the run:

The five models are running, starting with the change-point detector (M1).

The new models' code is committed and pushed. The run is still going.

The first change-point setting scores slightly below random at predicting digits in both periods. Its hits are at random level, and Big returns RM0.64 per RM1, the same as random picks. Three more M1 settings are running.

The second M1 setting is again slightly below random. Still running.

With the longer H = 2000 setting, the change-point model edges closer to random (−0.09 / −0.12), with 1.16× hits for its top 16 in the test period, but it's still below zero. Still running.

All four change-point settings are done. The best (H = 2000, a0 = 500) is the closest to random so far, −0.08 / −0.07, but still not positive. Next up is the autoregression (M2).

With light regularisation (λ = 100), the autoregression overfits badly (−5.2 / −3.7). It's learning short-term "patterns" that don't repeat. Stronger settings are next.

That result is wrong, and the fault is in my code, not the model idea. Stronger regularisation should move predictions toward the plain average, but my ridge also shrinks the intercept, which distorts the probabilities. I'll fix it and rerun M2 once this run finishes.

M2's last setting is done. Its #1 pick did hit once on the last 5 draws, but these M2 numbers are affected by the intercept bug, so I'll rerun M2 once the fix is in. The hazard model (M3) is next.

The overdue hazard model (12 gap bands) scores −0.13 / −0.04: still slightly below random, though the test period is close to it. The time since a number last won tells you essentially nothing about its next win. The 30-band version is running.

The 30-band hazard model gives the same result. M5, the number-shape model, is next.

The shape model with a short memory (H = 50) chases recent shape trends and scores −9.0 / −8.4, clearly worse than random. Longer memories are next.

Stronger smoothing toward each shape's natural share helps (−0.95 / −0.66), but it's still below random. Still running.

This shape setting (H = 500) still predicts below random (−1.42 / −1.26), even though it had 3 hits in its top 16 on the last 5 draws. Still running.

Still running.

The longest memory (H = 5000) is the best shape setting so far, −0.61 / −0.35, but still below random. One more shape setting, then the neural nets.

All six shape-model settings are done; none beats random (best: −0.54 / −0.31). The two neural-network settings (M4) are training now, and they're the slowest part.

The first neural network overfits heavily (−24 / −37). It learned noise from the training years that didn't carry over. The larger network is running now.

I built and tested five new kinds of predictive model, each based on a different theory. None predicts better than random: every one scored below zero on the main test in both the tuning and test periods. With every model, the less it reacted to the data, the closer it got to random; none ever beat it.

**How they were tested:**
- Settings were tuned on 2012–2017.
- They were then tested on 2018 to 3 Oct 2026.
- Finally they were checked on the last 5 draws (4–14 Oct), with the fitted settings frozen before 4 Oct.
- The main score is how much probability a model gave the actual results. **0 = no better than random; positive = better.**

| Model | Theory it tests | Best setting (chosen on 2012–17) | Score 2012–17 / 2018–26 | Test hits, top 16 vs random | Big return per RM1 (top 16) | Last 5 draws |
|---|---|---|---|---|---|---|
| **M1 Change-point detector** | Draw machines switch between biased "regimes" | long regimes (H = 2000) | −0.08 / −0.07 | 1.12× | RM0.60 | 0 hits (cold 16: Magnum 1235 consolation) |
| **M2 Draw-to-draw autoregression** | Recent draws, including other operators', predict the next | very strong regularisation | −0.11 / −0.04 | 0.93× | RM0.63 | 0 (cold 16: 1) |
| **M3 "Overdue" hazard curve** | A number's chance depends on time since it last won | 12 gap bands | −0.13 / −0.04 | 1.02× | RM0.77 | 0 (cold 16: 1) |
| **M4 Neural network** | Non-linear mix of recent digits, other operators, Vedic/Chinese parameters | 64-32 network | −10.0 / −28.7 | 1.02× | RM0.63 | 0 (cold 16: 1) |
| **M5 Number-shape model** | The *type* of number (pattern, digit-sum range, odd digits) is predictable | longest memory | −0.54 / −0.31 | 0.94× | RM0.75 | 1 (Toto 1311 consolation) |

**What the pattern means:**
- **Change-point (M1):** the best setting assumes regimes last thousands of draws, which in practice means barely changing at all. Detecting machine changes as they happen gives no usable warning.
- **Autoregression (M2):** I found and fixed a bug in my first version (the regression was shrinking its own baseline), then reran it. The best setting is so heavily regularised that it simply predicts the training-period average. Recent draws, from the same operator or the other two, add nothing.
- **Hazard (M3):** the time since a number last won carries no information. Its hit-rate curve is flat, so "overdue" and "repeat" don't help.
- **Neural network (M4):** it learned training-period noise and was far worse than random on new draws.
- **Shape (M5):** the mix of number types matches what random draws produce. Following recent trends in it only hurts.

**Last 5 draws.** Over five draws the best settings hit about as often as random picks, which average 0.55 hits per 16-number set. None of the 1-pick numbers won.

**Where this leaves the project.** Across everything tried, the result is the same: Malaysian 4D draws behave like fair random draws. That includes:
- frequency, hot/cold and overdue picks;
- every Vedic and Chinese parameter, alone and in pairs and triples;
- positional digit building (S1/S2), similar-days matching and replaying past values;
- gradient-boosted trees, softmax regression, neural networks and ensembles;
- change-point detection, autoregression, hazard curves and shape models.

The only real deviation found was Magnum's 2019–2025 digit bias, which was too small to profit from and is gone now. The remaining leads (the cold number, 1024, and the logged formulas) look like streaks found after the fact. The forward log for 17, 18 and 21 Oct is the fair test of them.

The code is in `analysis/new_models.py`, with results in `analysis/new_models_results.json`, both pushed. If you'd like, I can fetch tonight's 17 Oct results with TinyFish after the draw and score every logged lead.

That notice was the monitor for the first M-model run, which I stopped before it produced output. Nothing was lost: the rerun finished, and its results are committed and pushed.

That monitor was for the completed new-models run, so nothing further is pending.

---

## 33. Question (2026-10-17 07:27)

> ok now check which parameter that appears on any of the draw day, which then appear on the next draw day, produces same 4d number

---

## 34. Question (2026-10-17 07:28)

> ok now check which parameter that appears on any of the draw day, which then appear on any of the next draw day, produces same 4d number, list the one that is most significant

**Answer** (2026-10-17 07:28)

You're asking, for each parameter: when a parameter value such as nakshatra = Rohini comes back on a later draw day, does that later day repeat a **4D number** from the earlier day more often than chance? Here's how I'll test it:

1. **Count real repeats.** For each of the 78 Vedic and Chinese parameters, take every pair of draw days that share the same value (including the next time it comes back). Count how many winning numbers the two days have in common, across all three operators.
2. **Compute the chance level, adjusted for time gaps.** Many parameters stay the same for weeks or months: Jupiter's nakshatra lasts about a year, the masa a month. So same-value days are often close together in time. If numbers repeat more over short gaps anyway, slow parameters would look significant for that reason alone. The expected count therefore comes from how often *any* two draw days that far apart share a number.
3. **Two versions:**
   - **(a)** every later day with the same value;
   - **(b)** only the *next* day the value returns, which is your first wording.
4. **Rank by significance.** Parameters are ranked by z-score, with a correction for testing 78 parameters. For the top one, I'll also list which values repeat most.

No parameter makes the same 4D number come back more often than chance when its value recurs. Even the "most significant" ones are only 0.2–2% above chance, which is what luck alone produces when testing 78 parameters.

**What I measured.** For each of the 78 Vedic and Chinese parameters, I found pairs of draw days that share the same value, for example two Rohini days. I then counted the winning numbers the two days have in common (any prize, any of the three operators). The expected count is based on how many winners each day had and how far apart the days are, so fast- and slow-changing parameters are compared fairly.

My first run was wrong. It showed large excesses because my chance level ignored that a day with all three operators drawing has about 69 winning numbers, while a special one-operator draw has about 23. After the fix, two checks confirm the chance level is right: all pairs of draw days share numbers at exactly the expected rate (0.999×), and neighbouring draw days do too (0.997×).

**(a) The same value on any later draw day:**

| Rank | Parameter | Shared numbers | Expected | Ratio | z | p after allowing for 78 tests |
|---|---|---|---|---|---|---|
| 1 | Day element (Chinese) | 1,711,983 | 1,709,008 | 1.002× | +2.3 | 0.89 |
| 2 | KP Moon number | 40,408 | 39,973 | 1.011× | +2.2 | 1.00 |
| 3 | Day stem | 855,622 | 853,881 | 1.002× | +1.9 | 1.00 |
| 4 | Moon rashi | 713,055 | 711,630 | 1.002× | +1.7 | 1.00 |
| 5 | Nakshatra pada | 78,909 | 78,445 | 1.006× | +1.7 | 1.00 |

Only 2 parameters reached z > 2, and about 1.8 would by chance.

**(b) The value's next return only:**

| Rank | Parameter | Shared numbers | Expected | Ratio | z |
|---|---|---|---|---|---|
| 1 | Moon navamsa | 2,588 | 2,530 | 1.023× | +1.2 |
| 2 | Mercury nakshatra | 2,564 | 2,508 | 1.022× | +1.1 |
| 3 | Nakshatra lord | 2,579 | 2,530 | 1.019× | +1.0 |
| 4 | KP Moon star lord | 2,578 | 2,530 | 1.019× | +1.0 |
| 5 | Nayin | 2,573 | 2,528 | 1.018× | +0.9 |

None reached z > 2.

Within the top parameter, the strongest single value was **Moon navamsa = Vrishabha**: 244 repeated numbers against 210 expected (z = +2.3). Some recent examples:
- 2026-07-11 → 2026-07-26: 2031 won both times.
- 2026-07-26 → 2026-08-19: 7311 and 9649 won both times.

That's the best of 12 values, though, and z = +2.3 is about what the best of 12 reaches by chance.

**So, answering your question directly:** the most significant parameter is **Day element** (any later same-value day, 1.002×) or **Moon navamsa** (next return, 1.023×). Neither is significant. A parameter value coming back does not bring back its numbers.

The script is `analysis/recurrence_test.py` and the full per-parameter and per-value results are in `analysis/recurrence_results.json`, both pushed. I can run the same check for parameter pairs, or for i‑Box matches (same digits in any order), if you want.

---

## 35. Question (2026-10-17 07:37)

> OK now do the same analysis but this time for pair parameters for a,b

**Answer** (2026-10-17 07:38)

The same test, now for all **3,003 pairs** of parameters. The pair "value" is the combination, for example nakshatra = Rohini **and** day element = Fire, and the two versions are as before: (a) any later day with the same pair of values, (b) only the next such day.

Two changes, because 3,003 is a lot of tests:
1. **Correction for multiple testing.** Results are corrected for 3,003 tests. About 69 pairs would reach z > 2 and about 4 would reach z > 3 by chance alone.
2. **Robustness check on the top pairs.** The best pairs get an extra time-shift check. I slide the whole parameter calendar against the results by random offsets of a year or more and re-measure. This keeps every natural rhythm of the calendar and of the results, so it shows whether the top pairs only look good by luck.

The run is still going. It started under a minute ago: the parameters are loaded and 4 worker processes are working through the 3,003 pairs. I'll report back once it finishes.

I've committed and pushed the pair-recurrence script, so the working tree is clean again. The test itself is still running: the 4 worker processes are going through the 3,003 parameter pairs. When it finishes, I'll commit the results file and report the most significant pairs for both versions (any later day with the same pair of values, and the next such day), each with its time-shift check.

The pair-recurrence results are committed and pushed. I've started a fairness check that reruns the whole 3,003-pair scan 10 times on time-shifted calendars, which takes about 17 minutes. Here is what the real scan found.

**(a) Any later draw day with the same pair of values**
- 80 pairs have z > 2. About 68 would get there by luck alone, and 38 pairs fall the other way (z < −2).
- Only 2 pairs have z > 3. About 4 would by chance.
- Top 3:
  1. Saturn retrograde × KP Moon number: 21,979 repeats vs 21,501 expected (1.022×, z +3.26)
  2. KP Ascendant star lord × Day-vs-Year branch: 1.006×, z +3.25
  3. Nakshatra pada × Mercury nakshatra: 1.055×, z +2.86
- After correcting for testing 3,003 pairs, every one has p = 1.00.

**(b) The next draw day with the same pair of values**
- Only 21 pairs have z > 2, below the ~68 you'd expect by chance, and none have z > 3.
- Top 3:
  1. Nayin × Day-vs-Year branch: 1.052×, z +2.62
  2. Nakshatra pada × Mercury nakshatra: 1.066×, z +2.61
  3. Yoga × Mars nakshatra: 1.051×, z +2.47
- After correction, every one has p = 1.00.

**Time-shift check of the top pairs.** Each top pair beat all 40 shifted calendars, with z between +2.9 and +4.6. That doesn't make them real: they were picked as the best of 3,003, and that check doesn't account for the picking. The running check repeats the whole scan, picking included, on shifted calendars to measure how high the best pair gets by chance.

**Bottom line so far:** pairs behave like the single parameters did. The number of high-scoring pairs is about what luck produces, the effects are tiny (0.6–6.6% more repeats), and nothing survives the correction for testing 3,003 pairs. The one pair that shows up in both versions is Nakshatra pada × Mercury nakshatra, but even there the gain is about 1 extra repeat per 15 matching day pairs. That would not make a usable pick.

The new null script, `analysis/recurrence_pairs_null.py`, isn't committed yet. I'll report the shifted-scan numbers and commit it once the run finishes.

I've committed and pushed `analysis/recurrence_pairs_null.py`, so the working tree is clean. That's the script running the fairness check: it repeats the full 3,003-pair scan 10 times on time-shifted calendars. When it finishes (about 17 minutes), I'll tell you whether the real top pairs beat what shifted calendars produce by chance, and commit its results file.

Pairs of parameters don't predict repeat numbers either. Rerunning the whole 3,003-pair scan on time-shifted calendars produced the same kind of "best pairs".

I shifted all parameters together by a random amount, at least a year's worth of draws, and redid the full scan 10 times. That keeps the parameters' natural rhythms but breaks any real link between parameters and results, so whatever the shifted scans find is what chance looks like.

| | Real calendar | 10 shifted calendars (chance) |
|---|---|---|
| (a) best pair's z | +3.26 | +3.12 average (range +2.78 to +3.35) |
| (a) pairs with z > 2 | 80 | 46 average (range 23–73) |
| (b) best pair's z | +2.62 | +3.21 average (range +2.79 to +4.42) |
| (b) pairs with z > 2 | 21 | 34 average (range 12–95) |

- **(a) Any later same-value day:** the top pair, Saturn retrograde × KP Moon number, scores no higher than the best pair of a scan on a meaningless calendar. The count of 80 high-scoring pairs is above all 10 shifted runs. That's about a 1-in-11 result, not significant: many pairs share a parameter, so the count swings a lot (12 to 95 across the shifted runs).
- **(b) Next same-value day:** the real calendar does worse than the shifted ones. Its best pair is below the weakest shifted best, and it has fewer high-scoring pairs than average.

**Verdict:** like the single parameters, pairs of Vedic/Chinese parameters don't make the same 4D number come back. The "top pairs" in my last report are the strongest by luck out of 3,003. That includes Nakshatra pada × Mercury nakshatra, the one pair in both top lists, so I wouldn't build picks on any of them.

The scan script, its results, the shifted-calendar check (`analysis/recurrence_pairs_null.py`) and its results are all committed and pushed.

---

## 36. Question (2026-10-17 08:07)

> OK now for all the a,b can you see if the singles or the pairs, rather than focusing only on the straight, find for the one that is able to find straights,reverse or i-box that is significant

**Answer** (2026-10-17 08:10)

The Straight numbers match the earlier test exactly. Each full scan takes about 2.5 minutes, so I'm running the real scan plus 10 shifted-calendar scans in the background.

The new test is running. It covers all 78 single parameters and all 3,003 pairs, for both (a) any later day with the same value and (b) the next such day. It counts three ways a number can come back:

- **Straight:** the same number, e.g. 1234 → 1234.
- **Reverse:** the digits reversed, e.g. 1234 → 4321. Palindromes like 1221 are left out, since their reverse is the same number.
- **i-Box:** any arrangement of the same digits, e.g. 1234 → 3412. This includes the straight number.

**How "significant" is judged:**
- **Chance level:** I worked out how often two random sets of that day's winners would match under each rule, adjusted for how far apart the two days are.
- **Shifted-calendar check:** the whole 3,081-test scan is repeated on 10 shifted calendars that have no real link to the results. A real effect has to beat what those meaningless scans reach.

**Checks so far:** the Straight counts reproduce the earlier single-parameter test exactly. Across all pairs of draw days, Reverse and i-Box matches come out at 0.999× and 1.000× of chance, so the chance levels are calibrated.

The run should take about 30 minutes. The script is committed and pushed, and I'll report the results when it finishes.

---

## 37. Question (2026-10-17 08:11)

> OK and also do analysis for a,b for single,pair, straught, reverse and ibox for the S1 and S2 types as well

**Answer** (2026-10-17 08:13)

Each scan takes about a minute. I'll start this run now, alongside the first one.

Both tests are now running in the background. I'll report when they finish, which should be in about 30–45 minutes since they share the 4 CPUs.

**First run: number recurrence.** This is the Straight, Reverse and i-Box test from before, still running with 10 shifted-calendar checks.

**Second run: the S1/S2 version you asked for (`analysis/recurrence_s12.py`).** For every draw day whose parameter value, or pair of values, has occurred before:
- **(a)** S1 and S2 are built from all earlier draw days with that same value.
- **(b)** They are built from only the previous day with that value.
- **S1** takes the 2 most frequent digits in each position, giving 16 numbers. **S2** takes the 2 least frequent.
- Each pick is scored against that day's winners as Straight, Reverse or i-Box.
- This covers 78 single parameters and 3,003 pairs, so 3,081 tests across 12 combinations of strategy, version and match type.

**How significance is judged:**
- Chance level uses each year's own digit mix per position. A parameter therefore has to beat the ordinary year-level digit bias, not just pure random chance.
- The whole scan is repeated on 20 shifted calendars that have no real link to the results. A real effect has to beat the best z and the number of z > 2 that those meaningless scans reach.

**No-parameter baseline:** without any parameter, S1/S2 picks land between 0.96× and 1.07× of the year-adjusted chance. The parameter versions will be compared against that range.

Both scripts are committed and pushed.

Both scans are done. I'm committing the last results file, then I'll summarise.

Neither test turned up a reliable signal. Across the 78 single parameters and 3,003 pairs, nothing clearly beats chance as Straight, Reverse or i-Box, for plain repeats or for S1/S2. One S1 pick held up on later draws, which makes it a weak lead to watch, not something to bet on.

**How I judged significance:** I reran each whole scan on calendars shifted by a year or more, which keeps the parameters' rhythms but breaks any real link to the results. Those scans give the best score that pure luck reaches. A real effect has to beat that consistently, not just look high on its own.

**1. Same number coming back (10 shifted calendars)**

| Match type | Best test | Gain | Shifted scans scoring as high |
|---|---|---|---|
| Straight (a) | Saturn retrograde × KP Moon number | ×1.022 | 4 of 10 |
| Straight (b) | Nayin × Day-vs-Year branch | ×1.052 | 10 of 10 |
| Reverse (a) | Hora lord × Month stem | ×1.009 | 1 of 10 |
| Reverse (b) | Tithi × Month pillar | ×1.071 | 7 of 10 |
| i-Box (a) | Jupiter retrograde × Saturn retrograde | ×1.001 | 9 of 10 |
| i-Box (b) | Yoga × Mars nakshatra | ×1.018 | 2 of 10 |

- The strongest is Reverse (a), Hora lord or Weekday × Month stem. Only about 1 in 10 shifted scans did as well, but the gain is under 1%, too small to use.
- The i-Box (a) z-scores of +5 to +7 look dramatic but aren't real. i-Box counts are very lumpy, and the meaningless shifted calendars reached up to +14.

**2. S1/S2 picks (20 shifted calendars, then a forward test)**

On all the data, only two of the 12 combinations had a best pick that 19 of the 20 shifted scans failed to reach. With 12 combinations tested, that is about what luck produces.

The fairer test was to choose the top 5 per combination using only 1985–2011, then score them on 2012–2026:

- Across all 60 chosen picks, the average result after 2012 was z +0.17, so essentially chance. 33 of 60 came out above chance and 3 had z > 2.
- **Mercury nakshatra × Venus rashi, S1 (version a, Straight)** was the top pick before 2012 (z +3.47) and stayed above chance afterwards: 307 hits vs 272 expected, ×1.13, z +2.12. It is the only one-time top pick that held up.
- Karana × Day pillar, S1 (version b, i-Box), was 4th before 2012 and also held up: ×1.04, z +2.67.

These are weak leads, not confirmed edges. Three of 60 holding up is close to what chance gives. Even a real ×1.13 hit rate on 16 Straight numbers would still lose money against the payout odds.

**Upcoming picks, logged in `forward_log.csv`** (I logged them on 17 Oct at 09:08 UTC, before that evening's draw):

- **Mercury nakshatra × Venus rashi S1 (17, 18 and 21 Oct):** today it's Vishakha × Tula, the same as the last draw, so the picks are the same all three days: 6335 6337 6345 6347 6535 6537 6545 6547 7335 7337 7345 7347 7535 7537 7545 7547
- **Karana × Day pillar S1, i-Box:**
  - **17 Oct:** 1210 1217 1290 1297 1910 1917 1990 1997 8210 8217 8290 8297 8910 8917 8990 8997
  - **18 Oct:** 1540 1546 1590 1596 1640 1646 1690 1696 9540 9546 9590 9596 9640 9646 9690 9696
  - **21 Oct:** 6340 6342 6370 6372 6440 6442 6470 6472 9340 9342 9370 9372 9440 9442 9470 9472

The scripts and results are committed and pushed. The main ones are `recurrence_perm.py`, `recurrence_s12.py` and `recurrence_s12_forward.py` in `analysis/`. After the draws, I can fetch the results with TinyFish and score these picks along with the others already logged.

---

## 38. Question (2026-10-17 09:19)

> so from all the leads that you have so far rank all of them

**Answer** (2026-10-17 09:20)

I'd rank these leads by how well each held up against chance and on draws it wasn't chosen from, not by raw hit counts. None of them is a proven edge: even the best would still lose money at 4D payout odds.

| Rank | Lead | Best evidence | Weak point | Verdict |
|---|---|---|---|---|
| 1 | **Mercury nakshatra × Venus rashi, S1 (all earlier same-value days, Straight)** | It was the #1 pick using only 1985–2011, then beat chance on 2012–2026, which it was never chosen on: ×1.13, 307 hits vs 272 expected, z +2.12 | Only 3 of the 60 picks chosen this way held up like this, close to what luck gives | **Best lead available today**, logged for 17/18/21 Oct |
| 2 | **Karana × Day pillar, S1 (previous same-value day, i-Box)** | Also chosen on 1985–2011 only; after 2012 ×1.04, z +2.67 | It was only 4th before 2012 and the gain is small | Weak lead, also logged |
| 3 | **S1/S2 pairs and triples positive in both 2012–17 and 2018–26** (e.g. Hour stem 19h × KP Moon star lord × Lunar leap month, S2: ×1.19 then ×1.22; Lunar leap month × Nayin, S1: ×1.23 then ×1.19) | Above chance in two separate periods | Chosen out of 1,140 to 3,003 combinations using both periods. Combinations with z > 1 in both periods ran only about 1.5× what luck gives. 0 hits in the last 5 draws | Weak, possibly luck |
| 4 | **Cold number, no parameters** (each position's least frequent digit so far) | 5 first prizes in 2012–2026 vs 0.74 expected (p ≈ 0.001) | Found after the fact. 0 first prizes in 1995–2011 vs 0.82 expected, and no digit-level pattern explains it | Probably a lucky streak |
| 5 | **1024 on Magnum Big** | Paid RM1.64 per RM1 since 2012 | One number picked after looking at the results | Luck, not a pattern |
| 6 | **Reverse repeats: Hora lord or Weekday × Month stem** | Only 1 in 10 shifted calendars scored as high | Gain under 1% (×1.009) | Too small to use |
| 7 | **Magnum digit bias 2019–2025** | The only deviation that is clearly real | It ended after 2025 | Real but expired, so no use now |
| – | Everything else: hot/cold frequency, single/pair/triple parameter tables, the manual formula (1.02×), ML models, kNN, softmax, hazard, autoregression, ensembles, number recurrence | – | All came out at chance | No lead |

Leads 1 and 2 matter most because they're the only ones chosen on old draws and then checked on newer ones. The rest were picked after seeing the data they're judged on.

The cleanest test now is live draws. Leads 1 and 2 are logged in `forward_log.csv` for 17, 18 and 21 Oct, along with the earlier formulas. After those draws I can fetch the results with TinyFish and score every lead on draws none of them have seen.

---

## 39. Question (2026-10-17 09:21)

> Rank	Lead	Best evidence	Weak point	Verdict
> 1	Mercury nakshatra × Venus rashi, S1 (all earlier same-value days, Straight)	It was the #1 pick using only 1985–2011, then beat chance on 2012–2026, which it was never chosen on: ×1.13, 307 hits vs 272 expected, z +2.12	Only 3 of the 60 picks chosen this way held up like this, close to what luck gives	Best lead available today, logged for 17/18/21 Oct do more analysis on this to see if its family has the same result

**Answer** (2026-10-17 09:26)

No, its family doesn't show the same result. The lead stands alone, and digging deeper weakened it.

**1. Only the exact version works.** Of the 12 ways to build the picks from this pair, only the original holds up: S1 (hottest digits), all earlier same-value days, Straight.

| Version | Before 2012 | 2012–2026 |
|---|---|---|
| **S1, all earlier days, Straight (the lead)** | **×1.18, z +3.47** | **×1.13, z +2.12** |
| S1, all earlier days, Reverse | ×1.02 | ×1.12 |
| S1, all earlier days, i-Box | ×1.03 | ×0.99 |
| S1, previous day only, all three match types | about chance | about chance |
| All 6 S2 (cold digits) versions | about chance, mixed signs | about chance, mixed signs |

On their own, the two halves are weaker:
- **Mercury nakshatra alone:** ×1.06 after 2012, z +1.06.
- **Venus rashi alone:** ×1.05 after 2012, z +0.88.

**2. Chance check.** Its 2012–2026 result beat 98.5% of 200 shifted calendars, so about 1.5% luck odds for this one pick. But it was the best of 12 column winners I checked forward, so the honest odds of it being luck are about 1 in 5.

**3. It comes mostly from Magnum, and it has faded recently.**

| Split | Result |
|---|---|
| Magnum | ×1.25 before 2012, ×1.24 after |
| Sports Toto | ×1.12 before, ×1.16 after |
| Da Ma Cai | ×1.12 before, ×1.02 after |
| 1985–2018, in four blocks | ×1.15 to ×1.23, each z ≈ +2 |
| **2019–2026** | **×1.03, z +0.31** |

The fade since 2019 is the worst sign for using it now.

**4. Families: none share the effect.** Each family's average z after 2012 is close to what the shifted calendars give.

| Family | Tests | Average z after 2012 | Shifted calendars |
|---|---|---|---|
| Mercury nakshatra × any parameter | 76 | −0.06 | −0.07 |
| Any parameter × Venus rashi | 76 | −0.16 | −0.10 |
| Each body's nakshatra × another body's rashi | 71 | −0.18 | −0.19 |
| Mercury × Venus (rashi, nakshatra, retrograde, combust) | 15 | +0.21 (11 of 15 above 0) | −0.05 (3 of 20 shifts as high) |

Only the Mercury × Venus family leans slightly positive, and that isn't significant. The few family members with z > 2 after 2012 were near zero or negative before 2012, so they're luck. One example is Mercury nakshatra × Saturn combust: +3.03 after, +0.31 before.

**Updated verdict:** I'm downgrading this from "best lead" to an isolated result that is probably luck. If it were a real astrological effect, the same planets in nearby forms (Mercury rashi, Venus nakshatra, Reverse or i-Box matches) should show at least some of it, and they don't. It also comes mostly from one operator and has faded since 2019.

It's still logged for 17, 18 and 21 Oct, so those draws will give an independent check. The analysis is in `analysis/s12_family.py` and `analysis/s12_family_results.json`, both committed and pushed.

---

## 40. Question (2026-10-17 09:28)

> ok specifically for mercury nakshatra and venus rashi, can you check how different rashi and nakshatra within performs?

**Answer** (2026-10-17 09:29)

No particular nakshatra, rashi or combination stands out. Whether a value did well before 2012 tells you nothing about how it did after.

Throughout, I count hits per draw day: whether that day's winners included the S1 numbers built from all earlier days with the same Mercury nakshatra and Venus rashi.

**By Mercury nakshatra (27 values)**
- Best overall: Purva Phalguni ×1.64, Ashlesha ×1.54, Pushya ×1.43.
- Worst: Chitra ×0.63, Uttara Phalguni ×0.82.
- Before vs after 2012, correlation **−0.05**. Vishakha was ×1.67 before but ×0.69 after. Uttara Ashadha went the other way, ×0.88 before and ×1.59 after.
- The spread across values after 2012 is what chance gives: chi² 27.0 on 27 values.

**By Venus rashi (12 values)**
- Best: Karka ×1.29, Kumbha ×1.28, Tula ×1.26. Worst: Meena ×0.96, Simha ×0.99.
- 8 of 12 were above chance in both periods, but the before-vs-after correlation is only **+0.12**. Spread after 2012: chi² 11.3 on 12, again chance.

**By combined value (42 combinations with enough history)**

| Combination | Before 2012 | 2012–2026 |
|---|---|---|
| Purva Phalguni + Karka | 7 hits vs 2.9 expected | 8 vs 4.0 |
| Shravana + Makara | 8 vs 3.9 | 6 vs 2.6 |
| Purva Ashadha + Dhanu | 8 vs 4.0 | 6 vs 3.3 |

These look strong, but each rests on only 6–8 hits over 14+ years. With 42 combinations, a few will look like this by luck. The correlation before vs after is **+0.09**, and 17 combinations were positive only before 2012.

**Forward check:** I took the combinations that were above chance before 2012 and scored them after 2012. They came out at ×1.10. The other combinations did **better**, at ×1.16. If certain combinations were favourable, the earlier winners would have stayed ahead.

**Today's combination is Vishakha + Tula.** It had 10 hits vs 5.8 expected before 2012, but only 3 vs 3.4 after, which is chance level.

**What this means:** the lead's small edge, about ×1.13, is spread thinly across almost all values rather than coming from particular nakshatras or rashis. No individual value gives a dependable signal, and choosing values by how they did in the past doesn't help. Together with the earlier finding that the edge faded after 2019 and its family doesn't share it, this points to a statistical fluke, not a real astrological effect.

The analysis is in `analysis/s12_lead_cells.py` and its results file, committed and pushed.

---

## 41. Question (2026-10-17 09:31)

> average per race how many hits are expected? if the same performance is held, for all 3 races combined?

**Answer** (2026-10-17 09:32)

If its 2012–2026 rate holds, expect about **0.12 hits per draw day** across all 3 operators combined: roughly **1 hit every 8 draws**. Chance alone gives about 0.11, or 1 hit every 9 draws.

A "hit" is one of the 16 S1 numbers appearing among that operator's 23 winning numbers, in any prize tier.

**All 3 operators combined, per draw day**

| Period | Hits per draw | One hit every | Chance level | Draws with at least 1 hit |
|---|---|---|---|---|
| 1985–2011 | 0.099 | 10 draws | 0.084 (12 draws) | 9.4% |
| **2012–2026** | **0.124** | **8 draws** | **0.110 (9 draws)** | **11.5%** |
| 2019–2026 (latest) | 0.113 | 9 draws | 0.110 (9 draws) | 10.5% |

The chance level rose after 2012 because there are more winning numbers per day: about 68, against about 52 before.

**Per operator, 2012–2026** (chance is about 0.037 per draw for each)

| Operator | Hits per draw | One hit every |
|---|---|---|
| Magnum | 0.046 | 22 draws |
| Sports Toto | 0.043 | 23 draws |
| Da Ma Cai | 0.038 | 27 draws |

**In money terms:** say you bet RM1 Big on all 16 numbers with each of the 3 operators, which costs RM48 per draw. I'm assuming hits land in the prize tiers in the usual proportions, at about RM278 average per RM1 Big hit.

| Scenario | Return per draw (RM48 staked) | Return rate |
|---|---|---|
| Random numbers | about RM30.60 | 64% |
| This lead at its 2012–2026 rate | about RM34.50 | 72% |
| This lead at its 2019–2026 rate | about RM31.40 | 65% |

So even if the edge is real and held at its best, you'd lose about RM13–14 per draw on average. At its recent rate it is barely different from random. Most draws produce nothing; a hit comes about once every 8–9 draws, and nearly all of those land in the smaller Special and Consolation prizes.

---

## 42. Question (2026-10-17 09:34)

> in one day you have 3 draws so? its 0.36 hits per day?

**Answer** (2026-10-17 09:34)

No. The 0.12 is already per day with all 3 draws combined, so it's about 0.12 hits per day, not 0.36.

It is the sum of the three operators:

| Operator | Hits per draw (2012–2026) |
|---|---|
| Magnum | 0.046 |
| Sports Toto | 0.043 |
| Da Ma Cai | 0.038 |
| **All 3 draws on one day** | **0.125** |

The table I gave first was per draw day, all operators combined. The per-operator table shows each draw's share.

So with the same 16 numbers on all 3 operators, you'd average about 1 hit every 8 days. Chance gives 1 every 9 days. That's about 11 to 12 hits a year at roughly 100 draw days a year.

---

## 43. Question (2026-10-17 09:36)

> since you used 16 top numbers of s1, try to optimize the numbers and check which amount of numbers taken is the most significant?

**Answer** (2026-10-17 09:36)

I'll vary how many numbers are taken: top 1 up to top 1,000, ranked by how hot each number's digits are, plus the top-m digits per position grid (1, 16, 81, 256, 625 numbers). The amount gets chosen on draws before 2012 and checked on 2012–2026, with a shifted-calendar check for the advantage of having picked the best amount.

No amount of numbers makes this lead reliably better than chance. The original 16 is the only setup that held up in both periods, and only in its exact original form.

I built the picks two ways from the same digit counts, using all earlier days with the same Mercury nakshatra and Venus rashi:
- **Grid:** the top m digits in each position, giving m⁴ numbers (1, 16, 81, 256, 625). The original S1 is the 2⁴ = 16 grid.
- **Ranked:** every number scored by how hot its four digits are, then the top 1, 2, 4 … up to 1,024 taken.

| Picks | 1985–2011 | 2012–2026 | Hits per day after 2012 (3 draws) |
|---|---|---|---|
| Top 1 (hottest single number) | ×1.19, z +0.92 | **×1.65, z +2.67** | 0.011 (28 hits in 2,477 days) |
| Top 2 | ×1.12 | ×1.24 | 0.017 |
| Top 4 | ×1.09 | ×1.18 | 0.032 |
| Top 8 | ×1.14, z +1.89 | ×0.97 | 0.053 |
| Ranked top 16 | ×1.07 | ×0.98 | 0.108 |
| **Grid 16 (the original)** | **×1.18, z +3.47** | **×1.13, z +2.12** | **0.124** |
| Top 32 to 64 | ×1.04 | ×1.01 | 0.22–0.44 |
| 81 or more | ×1.00–1.04 | ×0.99–1.01 | 0.56 or more |

- **Chosen fairly, the best amount was 8 numbers.** Picking on 1985–2011 only, top 8 looked best (z +1.89), then did slightly worse than chance after 2012 (×0.97). 56 of 100 shifted calendars did as well with the same procedure.
- **The top 1 result is hindsight.** It was the best after 2012 (×1.65), but it wasn't special before 2012 (z +0.92), and 4 of 100 shifted calendars matched it. One hottest number also hits only about once every 90 days.
- **A different 16 numbers built from the same counts shows nothing.** The ranked top 16 came out at ×1.07 then ×0.98. A real effect from these counts should show in both versions, so the grid's result looks like a coincidence of its exact construction.
- **Without the parameters, every amount is at chance:** ×0.82 to ×1.04 after 2012.

**Verdict:** the edge doesn't grow or stabilise at any number of picks. Larger sets fall to chance, smaller ones are noisy and only look good with hindsight. I'd treat this lead as a fluke. If you still want to follow it, keep the original 16-number grid already logged for 17, 18 and 21 Oct, so the coming draws stay a clean test.

The analysis is in `analysis/s12_lead_k.py`, committed and pushed.

---

## 44. Question (2026-10-17 10:02)

> OK and also do analysis for a,b for single,pair, straught, reverse and ibox for the S1 and S2 types as well do this same analysis for the optimized numbers

**Answer** (2026-10-17 10:02)

This is the full scan again (78 single parameters and 3,003 pairs; S1 and S2; versions a and b; Straight, Reverse and i-Box), but with the number of picks varied instead of fixed at 16. The amounts are ranked top 1, 2, 4, 8, 16, 32 and 64, plus the 16 and 81 grids. Each is chosen on draws before 2012 and checked on 2012–2026, with shifted-calendar checks.

Results are identical and it now takes 1.9 seconds per test, about 25 minutes per full scan. I'm starting the real scan plus 5 shifted-calendar scans, about 2.5 hours in total.

The background slot stops at 2 hours, so I'll relaunch the run detached so it can finish.

The scan with varied pick amounts is running in the background and should take about 2.5 hours. I relaunched it detached so it isn't cut off at the 2-hour background limit. Before launching I checked it against the earlier results: the original 16-number S1 counts match exactly.

It covers 78 single parameters and 3,003 pairs, for S1 and S2, versions (a) and (b), and Straight, Reverse and i-Box. Each is tried with 9 pick amounts: top 1, 2, 4, 8, 16, 32 and 64 ranked numbers, plus the 16- and 81-number digit grids. That makes 108 combinations of strategy, version, match type and amount.

For each combination I'll report:
- how many tests reach z > 2, and the best z, compared with the 5 shifted calendars;
- a forward check: the 5 best tests chosen on draws before 2012, scored on 2012–2026, again compared with the same procedure on shifted calendars;
- which combinations, if any, stand out from their shifted versions.

I'll report as soon as it finishes.

The Broken pipe errors came from the leftover worker processes of the run I'd stopped, which were still writing into the same log file. The current run is healthy: 4 workers at about 87% CPU each, with plenty of free memory, and no new errors since. It should take about 2.5 hours. I'm watching the log and will report the results when it finishes.

The scan is still running, about 30 minutes in out of roughly 2.5 hours. I've set a watcher that will notify me when it finishes, and I'll report the results then.

Changing the number of picks doesn't produce a usable edge in any combination of S1/S2, version (a)/(b) and match type. All 108 combinations of strategy, version, match type and pick amount behave like chance.

**Overall forward check:** for each combination I took the 5 best tests chosen on draws before 2012 and scored them on 2012–2026.

| | Real calendar | Shifted calendars (chance) |
|---|---|---|
| Average z after 2012, all 108 combinations | −0.03 | +0.02 |
| Combinations beating all 5 shifted calendars | 14 | about 18 |

The real parameter calendar did no better than calendars with no real link to the results.

**By pick amount:** the count of tests with z > 2 and the best z per combination sat inside the shifted-calendar range at every amount. No amount, from the single top number up to 81 numbers, was consistently better than chance for any strategy or match type.

**Combinations that stood out most from their shifted versions:**

| Combination | Forward z | Shifted mean |
|---|---|---|
| S2 (a) Reverse, grid 16 | +1.01 | −0.03 |
| S1 (a) Reverse, top 64 | +0.76 | −0.42 |
| S2 (a) i-Box, grid 16 | +0.72 | −0.01 |
| S2 (a) i-Box, top 32 | +0.68 | −0.27 |

With 108 combinations, a few stand out like this by luck. The individual tests inside them also have tiny effects after 2012:
- **Sun rashi × Mars retrograde:** ×1.10, z +1.59.
- **Jupiter nakshatra × Mercury combust (i-Box):** ×1.03, z +2.07.
- **Jupiter retrograde × KP Ascendant number (Reverse, top 64):** ×1.07, z +2.31.

**Large z values that aren't real:** the biggest was S2 (a) Straight, top 64, at z +5.71 for Year pillar × Lunar leap month. The shifted calendars reached about +5.0 too, and their forward score (+1.47) was nearly as high as the real one (+2.04). That points to a slow, year-to-year drift in which digits run cold, not to the parameters.

**The original lead:** in this scan Mercury nakshatra × Venus rashi was still the best test in its own combination, S1 (a) Straight grid 16, at z +4.02. But that combination's forward result was 0.00, against −0.16 on shifted calendars, so it isn't confirmed.

**Conclusion:** across single parameters and pairs, S1/S2, versions (a) and (b), Straight, Reverse and i-Box, and every pick amount from 1 to 81, nothing works better than chance once you check it on draws it wasn't chosen on. That matches every other approach so far. The live picks for 17, 18 and 21 Oct remain the cleanest test.

The scan is in `analysis/recurrence_s12_k.py`, with results in `analysis/recurrence_s12_k_results.json`, both committed and pushed.

---

## 45. Question (2026-10-17 12:23)

> So for today, what is the prediction for the top lead?

**Answer** (2026-10-17 12:24)

Today, Saturday 17 Oct 2026, Mercury is in Vishakha and Venus is in Tula. The lead takes the 2 most frequent digits in each position from the 102 earlier draw days (1986–2026) with that same combination.

| Position | 1st | 2nd | Next |
|---|---|---|---|
| 1st digit | 7 (605) | 6 (601) | 9 (581) |
| 2nd digit | 3 (598) | 5 (595) | 7 (591) |
| 3rd digit | 4 (619) | 3 (617) | 7 (585) |
| 4th digit | 7 (630) | 5 (594) | 4 (583) |

**The 16 numbers, to play on all 3 operators:**

6335 6337 6345 6347 6535 6537 6545 6547
7335 7337 7345 7347 7535 7537 7545 7547

**The single hottest number is 7347.**

Before you use these:
- **About 1 in 9 chance of any hit today.** At its best rate (2012–2026), the lead averages about 0.12 hits per day across all 3 operators. A hit is most likely a Special or Consolation prize.
- **The digit choices are on a knife edge.** In position 1, 7 beats 6 by only 605 to 601, and in position 3, 4 beats 3 by 619 to 617. A couple of draws either way would change the set.
- **It's probably a fluke.** Everything since we found it has weakened it. It faded after 2019, its related parameters don't share it, no individual nakshatra or rashi drives it, and changing the number of picks doesn't confirm it. At its best rate it would still return only about 72% of stakes.

These are the numbers already logged for today's draw in `forward_log.csv`, so tonight's results will be a fair test.

---

## 46. Question (2026-10-17 13:18)

> ok now check the latest result of 4d for today and then tell how the leads perform

**Answer** (2026-10-17 13:18)

It's 9:18 pm in Malaysia, so tonight's 7 pm draw is done. I'll fetch the results from 4dmoon.com with TinyFish.

That page is empty for today so far. I'll try the live results page.

4dmoon hasn't posted tonight's results yet: the live page fills its numbers in with JavaScript, and the past-results page for 17 Oct is still empty. I'll try other results sites.

Two sites (4dkingdom.com and check4d.org) show the same results for tonight. I'll add them to the data and score every pick logged for 17 Oct.

The top lead, Mercury nakshatra × Venus rashi, had no hits tonight. Only one lead won a straight prize: the S2 Mars triple, with a Sports Toto Consolation (RM60 on its RM48 stake). I took the results from 4dkingdom.com and check4d.org, which agree; 4dmoon.com hadn't posted tonight's draw yet.

**Tonight's results (Saturday 17 Oct)**

| | Magnum | Sports Toto | Da Ma Cai |
|---|---|---|---|
| 1st | 1294 | 1508 | 5434 |
| 2nd | 8044 | 5241 | 6342 |
| 3rd | 5541 | 6336 | 7652 |

**How each lead did** (each line is RM1 Big on every pick)

| Rank | Lead | Bets | Straight hits | Won | Other arrangements of the same digits |
|---|---|---|---|---|---|
| 1 | Mercury nakshatra × Venus rashi S1 (6335 … 7547) | 48 | 0 | RM0 | none |
| 2 | Karana × Day pillar S1, i-Box | 48 | 0 | RM0 | 8917 → **7819** Toto Consolation; 8290 → **2980** Da Ma Cai Consolation |
| 3 | S1 Mars nakshatra × Mars rashi × Mercury combust | 48 | 0 | RM0 | none |
| 3 | S2 Mars nakshatra × Mars rashi × Mercury combust | 48 | **1: 8426 Toto Consolation** | **RM60** | 4362/2346 → **6342** Da Ma Cai 2nd; 4162/2146 → **1624** Da Ma Cai Consolation |
| 4 | Cold number (6665 / 8668 / 5122) | 3 | 0 | RM0 | none |
| 5 | 1024 Magnum | 1 | 0 | RM0 | – |

- **Top lead:** no hit, which is what you'd usually expect. It averages about 0.12 hits per day at best, so most days are empty.
- **Karana × Day pillar (i-Box lead):** 2 i-Box matches, both Consolation. A 24-way i-Box Consolation pays only about RM2.50 per RM1. Two matches is about what chance gives for 16 numbers across 3 operators.
- **S2 Mars triple:** the only straight win, a Consolation, so RM60 back on the RM48 stake. It also had near-misses on the Da Ma Cai 2nd prize (6342) and a Consolation (1624). Had it been bet as i-Box, those would have paid a share of those prizes. One night like this is still within chance.

Tonight's results are added to the data files, committed and pushed. The next logged checks are Sunday 18 Oct and Wednesday 21 Oct. The top two leads are logged for both days, along with other earlier formulas, and I can score them the same way after each draw.

---

## 47. Question (2026-10-17 13:25)

> all this convo analysis and everything have you posted them into the repo?

**Answer** (2026-10-17 13:25)

The code, result files, data and logged picks are all pushed, but the written conclusions only exist in this chat. I'll add a findings summary to the repo now.

Yes, it's all in the repo now on branch `claude/4d-results-scraper-9ptbd5` of `zramakh/4dprediction`, and the local copy matches GitHub.

**Already pushed during the work:**
- **Analysis scripts:** all of them in `analysis/`, from the conditional and almanac tests through the ML models, S1/S2, recurrence, family, value and pick-count analyses.
- **Result files:** a JSON file for each analysis.
- **Logged picks:** `analysis/forward_log.csv`, with picks saved before each draw for 17, 18 and 21 Oct.
- **Data:** updated through tonight's 17 Oct draw for Magnum, Sports Toto and Da Ma Cai.
- **TinyFish importer:** `tinyfish_import.py`, with its tests.

**Just added:** the written conclusions had only been in this chat. They're now in `analysis/FINDINGS.md`, linked from the README. It covers:
- how everything was tested (train on earlier draws and test on later ones, shifted calendars, correcting for testing thousands of formulas);
- every approach tried, with the script for each;
- the ranked leads, with their evidence and weak points;
- expected hits and returns for the top lead;
- tonight's live check of each lead.

When the 18 and 21 Oct results come in, I can add them to the data and to the live-check table in `FINDINGS.md`.

---

## 48. Question (2026-10-17 13:26)

> what about all our conversations? can you add that too?

**Answer** (2026-10-17 13:27)

I've written the log; now I'm linking it from the README and pushing.

Yes. The conversation is now in the repo as `docs/conversation.md`, linked from the README, and pushed.

It has all 49 of your questions with my answers, in order and timestamped, from your first question on 16 Oct to the live results check tonight. I left out tool calls and raw command output, since the scripts and result files in `analysis/` already hold those. This latest exchange isn't in it yet; I can add it the next time I update the log, for example after the 18 and 21 Oct results.

**The repo `zramakh/4DPrediction` is public**, so anyone can read this log along with the analysis. I checked: it contains no email address or account details, only the questions, answers and numbers. If you'd rather keep it private, you can make the repo private in GitHub settings, or I can remove the file. It would stay in the git history unless that's rewritten.

---

## 49. Question (2026-10-18 12:02)

> Ok now you can scarp the latest result for today and then tell me how the leads perform yesterday and today

**Answer** (2026-10-18 12:02)

Both sites agree on today's results. I'll add them to the data, then score every logged pick for 17 and 18 Oct with a reusable script.

Over the two days, the leads won RM60 in total on RM1,028 staked. That one prize was a Consolation for the S2 Mars triple yesterday; nothing hit straight today. I took today's results from check4d.org and 4dkingdom.com, which agree.

**Today's results (Sunday 18 Oct)**

| | Magnum | Sports Toto | Da Ma Cai |
|---|---|---|---|
| 1st | 3196 | 3166 | 2454 |
| 2nd | 3806 | 6640 | 1240 |
| 3rd | 0127 | 4937 | 6521 |

**How the leads performed** (each pick is RM1 Big on Straight)

| Lead | 17 Oct (Sat) | 18 Oct (Sun) |
|---|---|---|
| 1. Mercury nakshatra × Venus rashi S1 | 0 hits | 0 straight; i-Box matches 5375 Toto Special, 4557 Toto Consolation, 5673 Da Ma Cai Special |
| 2. Karana × Day pillar S1 (i-Box lead) | 0 straight; 2 i-Box Consolations | 0 straight; 5 i-Box Specials: 9569 and 4960 Magnum, 4950 Toto, 5619 and 9406 Da Ma Cai |
| 3. S1 Mars triple | 0 hits | 0 straight; i-Box 5304 Toto Consolation, 4950 Toto Special |
| 3. S2 Mars triple | **8426 Toto Consolation, RM60** | 0 straight; i-Box 8628 Toto Consolation |
| 4. Cold number | 0 hits | 0 hits |
| 5. 1024 on Magnum | 0 hits | 0 hits (1240 came 2nd at Da Ma Cai, but that isn't a Straight match) |
| All formulas logged for 18 Oct (29) | – | **0 straight hits: RM0 on RM832** |

Running total: **RM60 back on RM1,028 staked**. That's RM196 staked on 17 Oct and RM832 on 18 Oct, when all the earlier formulas were also logged.

- **Top lead:** 0 hits in 2 days. At its best rate you'd expect about 0.24 hits over two days, so this is normal.
- **Karana × Day pillar** is designed for i-Box and got 7 i-Box matches in two days, all Special or Consolation. Each pays only about RM7.50 (Special) or RM2.50 (Consolation) per RM1. Its 16 numbers average about 1.8 i-Box matches per day by chance, so 2 and 5 is ordinary.
- **Near-misses:** the Saturn combust formula's 9316 is an arrangement of Magnum's 1st prize 3196. That would have paid about RM104 per RM1 as i-Box, but it lost as a straight bet. Several formulas also had 1024, an arrangement of Da Ma Cai's 2nd prize 1240.

Two draws are far too few to judge any lead. So far the results match what the testing found: nothing beats chance.

Today's results are added to the data. The new `analysis/score_live.py` scores any draw date against the logged picks, for example `python3 analysis/score_live.py 2026-10-21`. The live-check table in `FINDINGS.md` is updated, and everything is pushed. The next logged draw is Wednesday 21 Oct.

---

## 50. Question (2026-10-18 12:05)

> Ok I’m just curious doesn’t the leads needs to be always updated from the history? So the 17th and before needs to be updated before the S1, S2 is calculated for the new ones? Try again and test if there’s a hit after update?

**Answer** (2026-10-18 12:06)

The code reproduces all the logged picks exactly. Now I'll rebuild them with the 17 Oct results included and score them against today's draw.

Even with the 17 Oct results included, none of the leads would have had a straight hit on 18 Oct.

Only the 18 Oct picks were affected. The 17 Oct picks already used everything available, because the last draw before 17 Oct was 14 Oct. I rebuilt the 18 Oct picks from all results up to 17 Oct. The rebuild code reproduces the originally logged picks exactly when given only results up to 14 Oct, so the only difference is the extra day of data.

| Lead | Change with 17 Oct included | Straight hits on 18 Oct |
|---|---|---|
| 1. Mercury nakshatra × Venus rashi | Counts now cover 103 earlier days instead of 102, but the top 2 digits in each position stayed the same, so it's the same 16 numbers | 0 |
| 2. Karana × Day pillar | No change. It uses the previous day with the same Karana and Day pillar (26 Apr 2025), and 17 Oct had different values | 0 |
| 3. S1 Mars triple | 17 Oct had the same Mars values, so Da Ma Cai's picks changed (…7 became …4, e.g. 1517 became 1514) | 0 |
| 3. S2 Mars triple | Magnum's and Da Ma Cai's picks changed (Magnum 4016… became 1226…) | 0 (new i-Box near-miss: 1267/1627 for Magnum Consolation 2176) |
| 4. Cold number | Already used the latest results | 0 |

The update only shifts digits that were close to a tie, and for most leads one extra day changes nothing at all. It doesn't change the conclusion: no straight hit on 18 Oct either way.

From now on each draw's results go in before the next picks are made. I've rebuilt Wednesday 21 Oct's picks from all results through today (18 Oct) and logged them before the draw, marked `_upd`:

| Lead | 21 Oct picks |
|---|---|
| 1. Mercury nakshatra × Venus rashi (still Vishakha + Tula, 104 earlier days) | 6335 6337 6345 6347 6535 6537 6545 6547 7335 7337 7345 7347 7535 7537 7545 7547 |
| 2. Karana × Day pillar (Vanija × Wu Chen) | 6340 6342 6370 6372 6440 6442 6470 6472 9340 9342 9370 9372 9440 9442 9470 9472 |
| 3. Mars triple S1/S2 | 16 numbers per operator, in `forward_log.csv` |
| 4. Cold number | 6665 (Magnum), 8668 (Toto), 5122 (Da Ma Cai) |

The new script `analysis/update_picks.py` does this rebuild. After adding a draw's results, `python3 analysis/update_picks.py 2026-10-24 --log` makes the next set of picks. `FINDINGS.md` is updated and everything is pushed.

---

## 51. Question (2026-10-18 12:08)

> Wait what about 17th have that been updated from previous rounds or did it stop at the 10 that I ask to test? Send me the hit results for straight and ibox as well

**Answer** (2026-10-18 12:08)

I'll check what data the 17 Oct picks were built from by rebuilding them with two cutoffs: results up to 3 Oct (before the 5 test draws) and up to 14 Oct.

The 17 Oct picks didn't stop at the 5-draw test: they included every result up to 14 Oct. That makes no difference, though. If I freeze the data before 4 Oct instead, I get exactly the same picks.

| Lead | Results before 4 Oct | Results up to 14 Oct | Same 17 Oct picks? |
|---|---|---|---|
| 1. Mercury nakshatra × Venus rashi | 101 earlier days | 102 earlier days | Yes |
| 2. Karana × Day pillar | previous day 11 May 2022 | same | Yes |
| 3. Mars triple, S1 and S2 | 174 earlier days | 174 | Yes |

So the 17 Oct picks were fully up to date. Only the 18 Oct picks were missing a draw (17 Oct), and that's now fixed.

**Straight and i-Box results, using fully updated picks** (RM1 per number on all 3 operators, 48 bets per lead per day). i-Box payouts are approximate: the Big prize divided by the number of possible arrangements.

**17 Oct (Saturday)**

| Lead | Straight | Straight RM | i-Box matches | i-Box RM |
|---|---|---|---|---|
| 1. Mercury nakshatra × Venus rashi | 0 | 0 | 0 | 0 |
| 2. Karana × Day pillar | 0 | 0 | 2: 8917 → 7819 Toto Consolation; 8290 → 2980 DMC Consolation | about 5 |
| 3. S1 Mars triple | 0 | 0 | 0 | 0 |
| 3. S2 Mars triple | **1: 8426 Toto Consolation** | **60** | **5:** 8426 Toto Consolation; 2346 and 4362 → **6342 DMC 2nd**; 2146 and 4162 → 1624 DMC Consolation | **about 91** |
| 4. Cold number (3 bets) | 0 | 0 | 0 | 0 |
| 5. 1024 Magnum (1 bet) | 0 | 0 | 0 | 0 |

**18 Oct (Sunday), rebuilt with 17 Oct included**

| Lead | Straight | i-Box matches | i-Box RM |
|---|---|---|---|
| 1. Mercury nakshatra × Venus rashi | 0 | 3: 7535 → 5375 Toto Special; 7545 → 4557 Toto Consolation; 6537 → 5673 DMC Special | about 27.50 |
| 2. Karana × Day pillar | 0 | 5: 9596 → 9569 Magnum Special; 9640 → 4960 Magnum Special; 9540 → 4950 Toto Special; 1596 → 5619 DMC Special; 9640 → 9406 DMC Special | about 45 |
| 3. S1 Mars triple | 0 | 2: 4305 → 5304 Toto Consolation; 4905 → 4950 Toto Special | about 10 |
| 3. S2 Mars triple | 0 | 3: 1267 and 1627 → 2176 Magnum Consolation; 8826 → 8628 Toto Consolation | about 10 |
| 4. Cold number | 0 | 0 | 0 |
| 5. 1024 Magnum | 0 | 0 | 0 |

**Two-day totals** (RM96 staked per lead, 48 numbers × 2 days):

| Lead | Straight | i-Box |
|---|---|---|
| 1. Mercury nakshatra × Venus rashi | RM0 | about RM27.50 |
| 2. Karana × Day pillar | RM0 | about RM50 |
| 3. S1 Mars triple | RM0 | about RM10 |
| 3. S2 Mars triple | RM60 | **about RM101**, roughly break-even |

- **i-Box always produces more matches**, because each number covers up to 24 arrangements, but each match pays only a fraction of the prize. Getting 2 to 5 matches a day on 48 numbers is what chance gives.
- **S2 Mars triple:** its i-Box result comes almost entirely from two numbers matching Da Ma Cai's 2nd prize, 6342, on 17 Oct. That's one lucky draw, not a pattern.
- **The rebuilt 18 Oct picks were made today.** They use only results up to 17 Oct, but they weren't logged before the draw. With the picks that were logged, the S2 Mars triple had only 1 i-Box match on 18 Oct, about RM2.50.

Wednesday 21 Oct is the next clean test: those picks are rebuilt from all results through today and already logged.

---

## 52. Question (2026-10-18 12:11)

> Ok now recheck the analysis again for all parameters single and pairs and for S1, S2, hot,cold etc and check again if it changes the result for 17th and 18th and if it did perform better

**Answer** (2026-10-18 12:11)

I'll rerun the full scan (78 singles and 3,003 pairs; S1 and S2; versions a and b; Straight, Reverse and i-Box) separately for each draw day. For 17 Oct it uses only results before 17 Oct, and for 18 Oct only results before 18 Oct, so the draw being tested never helps choose the leads. Then I'll score the new top leads' picks on that day against chance.

I reran the full analysis separately for each draw, using only the results before it: 78 single parameters and 3,003 pairs, for S1 (hot) and S2 (cold), versions (a) and (b), and Straight, Reverse and i-Box. Neither the results nor the performance changed.

**The ranking didn't change.** The top tests are the same before 17 Oct and before 18 Oct, and each z-score moved by only about 0.01. Mercury nakshatra × Venus rashi is still #1 for S1 Straight (z +4.02, then +4.01), and Karana × Day pillar is still #1 for S1 (b) i-Box. One or two extra draws can't shift rankings built on 40 years of data.

**How the new top picks did** (the top 5 tests in each of the 12 combinations, 16 picks each):

| | 17 Oct | 18 Oct |
|---|---|---|
| Straight hits | 1 (expected 2.2) | 1 (expected 2.0) |
| The hit | 4510, Magnum Consolation (Nayin element × Yellow/black path, S2 b) | 5656, Da Ma Cai Special (Jupiter rashi × Jupiter combust, S2 a) |
| Reverse hits | 1 (expected 2.2) | 0 (expected 2.2) |
| i-Box hits, distinct pick sets | 27 (expected 28.7) | 33 (expected 30.6) |

The raw i-Box totals look a little better (39 and 46). That's double counting: several top tests produce identical picks, for example Weekday × Year stem, × Year animal and × Year yin-yang. Counting each distinct set of picks once, i-Box is at chance both days.

**Without any parameter**, plain hot or cold digits had no Straight hits on either day. Each was expected to get about 0.11 a day. They had 0–2 i-Box matches, also about chance.

**Did updating help?** No. The picks with up-to-date data did about the same as before, at chance on both days. Updating is still the right practice, and from now on each draw's results go in before the next picks are made.

The new script is `analysis/rescan_live.py`, with results in `rescan_live_results.json`. To repeat this for a future draw, run `python3 analysis/rescan_live.py YYYY-MM-DD` after adding the results. `FINDINGS.md` is updated and everything is pushed.

---

## 53. Question (2026-10-18 12:16)

> Ok list out the leads and their performance for this 2 days 17 and 18

**Answer** (2026-10-18 12:17)

Across 17 and 18 Oct the leads won RM60 in total, from one Straight Consolation, against RM394 staked. Each lead's picks were built from all results up to the night before (for 18 Oct, rebuilt with the 17 Oct results). Stakes are RM1 per number on each operator, and i-Box payouts are approximate.

**Ranked leads**

| Rank | Lead | Bets per day | 17 Oct Straight | 17 Oct i-Box | 18 Oct Straight | 18 Oct i-Box | 2-day Straight | 2-day i-Box |
|---|---|---|---|---|---|---|---|---|
| 1 | Mercury nakshatra × Venus rashi S1 | 48 | 0 | 0 | 0 | 3 (5375 Toto Special, 4557 Toto Consolation, 5673 DMC Special) | RM0 | ~RM27.50 |
| 2 | Karana × Day pillar S1 (i-Box lead) | 48 | 0 | 2 (7819 Toto Consolation, 2980 DMC Consolation) | 0 | 5 (9569 and 4960 Magnum Special, 4950 Toto Special, 5619 and 9406 DMC Special) | RM0 | ~RM50 |
| 3 | S1 Mars nakshatra × Mars rashi × Mercury combust | 48 | 0 | 0 | 0 | 2 (5304 Toto Consolation, 4950 Toto Special) | RM0 | ~RM10 |
| 3 | S2 Mars nakshatra × Mars rashi × Mercury combust | 48 | **1: 8426 Toto Consolation (RM60)** | 5 (8426 Toto Consolation, 6342 DMC 2nd ×2, 1624 DMC Consolation ×2) | 0 | 3 (2176 Magnum Consolation ×2, 8628 Toto Consolation) | **RM60** | ~RM101 |
| 4 | Cold number (6665 / 8668 / 5122) | 3 | 0 | 0 | 0 | 0 | RM0 | RM0 |
| 5 | 1024 Magnum | 1 | 0 | 0 | 0 | 0 | RM0 | RM0 |

**Two-day totals across the 6 leads:** RM394 staked (197 numbers a day). Straight returned RM60 (15%) and i-Box about RM188 (48%).

**The full rescan before each draw** (top 5 tests in all 12 combinations):

| | 17 Oct | 18 Oct |
|---|---|---|
| Straight | 1 hit vs 2.2 expected (4510 Magnum Consolation) | 1 hit vs 2.0 expected (5656 DMC Special) |
| Reverse | 1 vs 2.2 | 0 vs 2.2 |
| i-Box, distinct pick sets | 27 vs 28.7 | 33 vs 30.6 |

**No-parameter reference** (plain hot or cold digits): 0 Straight hits either day, against about 0.11 expected per day.

**Summary**
- **Straight:** only 1 hit in 2 days, and all the leads together did no better than random numbers.
- **i-Box:** many small matches but low payouts. S2 Mars roughly broke even on i-Box only because two of its numbers matched Da Ma Cai's 2nd prize, 6342, on 17 Oct.
- **Lead 1** (Mercury nakshatra × Venus rashi) has had no Straight hit yet. That's normal for its rate of about 1 hit every 8 days.

Two draws are too few to judge anything. The next test is Wednesday 21 Oct, and those picks are already logged.

---

## 54. Question (2026-10-18 13:30)

> I’m wondering if all your analysis only include hot but no cold?

**Answer** (2026-10-18 13:31)

No, cold was included throughout. Every S1/S2 analysis tested both: S1 is the hot version (the 2 most frequent digits in each position) and S2 is the cold version (the 2 least frequent). Cold was tested in these analyses:

| Analysis | Where cold appears |
|---|---|
| Positional strategies (`strategies_test.py`, `s12_combos.py`) | S2 alongside S1 for single parameters, pairs and triples; the Mars triple lead has an S2 version |
| Recurrence scans (`recurrence_s12.py`) | 6 of the 12 combinations are S2 |
| Pick-count scan (`recurrence_s12_k.py`) | S2 ranks numbers coldest first for top 1 to 64, plus cold grids of 16 and 81 numbers |
| Cold number lead (`first_prize_test.py`) | each position's coldest digit, e.g. 6665, 8668, 5122 |
| No-parameter cold picks | logged in `forward_log.csv` as `positional_cold_noparam` |
| Live rescan (`rescan_live.py`) | S2 columns plus a plain-cold reference |

**What cold showed:**
- **Recurrence scan:** S2 version (a) Straight had the most tests with z > 2, 181 of them. Shifted calendars with no real link gave 109–204, so that's within chance.
- **Pick-count scan:** the single biggest score was S2 (a) Straight, top 64, at z +5.71. The shifted calendars reached about +5.0 too, which points to a slow drift in which digits run cold, not to the parameters.
- **Forward checks:** the S2 picks chosen before 2012 came out at about chance after 2012, the same as S1.
- **Cold number:** 5 first prizes in 2012–2026 against 0.74 expected, but none in 1995–2011.

**Live draws:** all three Straight hits in the last two days came from cold picks.

| Draw | Cold pick that hit | Prize |
|---|---|---|
| 17 Oct | S2 Mars triple: 8426 | Toto Consolation, RM60 |
| 17 Oct | S2 Nayin element × Yellow/black path: 4510 | Magnum Consolation |
| 18 Oct | S2 Jupiter rashi × Jupiter combust: 5656 | Da Ma Cai Special |

That sounds good for cold, but roughly half the picks scored were cold. Cold picks would be expected to get about 1 Straight hit per day by chance, and they got 1.5. Three hits over two draws can't tell cold from hot.

If you want, I can keep a separate hot vs cold tally in the live scoring from 21 Oct onward.

---

## 55. Question (2026-10-18 13:32)

> Are the numbers picked from how hot or cold their positions are or the 4d number itself?

**Answer** (2026-10-18 13:32)

S1 and S2 are built from how hot or cold each digit position is, not from how often a whole 4D number has come up.

**How S1 and S2 work.** Take all the winning numbers from the earlier days with the same parameter values, for example every earlier day with Mercury in Vishakha and Venus in Tula. Count how often each digit appears in each of the four positions. For 17 Oct that gave:

| Position | Most frequent | 2nd |
|---|---|---|
| 1st digit | 7 (605) | 6 (601) |
| 2nd digit | 3 (598) | 5 (595) |
| 3rd digit | 4 (619) | 3 (617) |
| 4th digit | 7 (630) | 5 (594) |

S1 combines the top 2 digits in each position: 2 × 2 × 2 × 2 = 16 numbers, 6335 to 7547. S2 does the same with the 2 least frequent digits. The cold number lead (e.g. 6665) is the single coldest digit in each position.

**Why positions rather than whole numbers?** Each 4D number has won only about 50 times in 40 years across all three operators. Split by a parameter value, a number may have won 0, 1 or 2 times in that group, which is too few to call it hot or cold. Each digit position, by contrast, has hundreds or thousands of counts per group, so there's far more data per estimate.

**Whole numbers were tested too, in other analyses:**

| Analysis | What it checked |
|---|---|
| Conditional number tests (`conditional_numbers.py`, `conditional_extended.py`, `pairs_test.py`) | whether specific 4D numbers win more often under a parameter value, a pair or a triple |
| Frequency / hot-number picks in the early models (`predictive_model.py`, `ml_model.py`) | numbers that came up most often before |
| Recurrence tests (`recurrence_test.py`, `recurrence_pairs.py`, `recurrence_perm.py`) | whether the same whole number (or its reverse, or any arrangement of its digits) comes back when a parameter value recurs |
| 1024 lead | one specific number that did well on Magnum |

All of these came out at chance as well.

One thing not yet tried is whole-number hot/cold picks in the S1/S2 format: the 16 numbers that won most often, or least often, on earlier days with the same parameter values, scored with the same chance and shifted-calendar checks. I can run that across all singles and pairs if you'd like.

---

## 56. Question (2026-10-18 13:48)

> Don’t you think whole number hot and cold is already inside S1/S2? Anyways, I thought maybe we can try some new ways of analysis that we have not tried yet. Give me 5 suggestions

**Answer** (2026-10-18 13:49)

Partly. The 16 S1 numbers are always made of hot digits, so a whole number that's hot usually has hot digits too, and in that sense it's covered. But it doesn't work the other way. S1 assumes the four positions are independent and treats each digit separately, so it can't see a specific whole number that keeps repeating. A number that came up 4 times can still have average digits and never make the S1 set. The whole-number repeat tests (`recurrence_test.py` and the pair version) looked at exactly that case, and found nothing.

Here are five approaches we haven't tried yet:

**1. Use the Singapore 4D result, drawn about 30 minutes earlier.** Singapore Pools draws at around 6:30 pm on Wednesday, Saturday and Sunday, before the Malaysian 7 pm draws. Test whether its numbers, digits or digit patterns turn up in Magnum, Toto or Da Ma Cai the same evening more than chance. Do the same with Sabah 88, Sandakan and CashSweep on the same day. If there were any shared influence, this is where it would show, and the information is available before you'd buy a ticket.

**2. Links within a draw and across operators.** We combined the three operators and treated every number separately. Instead, test whether numbers within one draw share digits more than chance, whether the 1st prize's digits hint at the 2nd and 3rd, and whether Magnum's result tonight says anything about Toto's or Da Ma Cai's tonight or at their next draw. These tests look for leftover patterns from how each machine draws its balls.

**3. Exact astrology instead of categories.** So far we used named values such as "Mars in Ashlesha". Use the exact degrees at 7:00 pm instead: the Moon's position, the angles between planets (conjunction 0°, opposition 180°, trine 120°, square 90°), how far into a nakshatra or tithi the Moon is, and the exact planetary hour. Then test whether digits follow these continuous values, for example whether the 1st digit tracks the Moon's degree.

**4. Numerology from the date and draw number.** Turn the date (day, month, year, digit sums), the lunar date and the draw number (e.g. Magnum #436) into 4D numbers by common methods, plus the 4D dream-dictionary mappings. Check whether those numbers win more than random ones. Many players use these, so it's worth a clean test.

**5. A full randomness check of each operator.** Run standard randomness tests on each operator's digits, era by era: frequency, runs, serial correlation, gaps between repeats, and patterns of digit pairs and triples. This answers the underlying question directly: is there any detectable pattern at all? If an operator passes everything, no method can predict it. If one fails a test (as Magnum did in 2019–2025), it shows exactly where to look.

**My recommendation:** start with 5, because it shows whether anything is worth chasing, then 1, since Singapore's result arrives before the Malaysian draw. Each would get the same honest testing as before: train on earlier draws, test on later ones, and compare with shifted or shuffled versions.

Which ones would you like me to run?

---

## 57. Question (2026-10-18 13:51)

> Let’s try the whole number and number 3

**Answer** (2026-10-18 13:51)

I'll check what the almanac code can give for exact planetary positions before writing the two analyses.

I'll write both analyses. The whole-number one is a long scan, so it runs in the background while I do the exact-astrology one.

At 9 seconds per test, one full scan would take about 2 hours. I'll speed it up by precomputing each day's globally hottest and coldest numbers, so each day only needs a small candidate set.

The results are identical and it now takes 0.8 seconds per test. I'm starting the full scan (real calendar plus 4 shifted ones, about 50 minutes) in the background.

The exact-astrology test (number 3) is done: no exact planetary position, angle or aspect predicts the digits. The whole-number test was restarted after a bug fix and is running in the background, about 50 minutes; I'll report it when it finishes.

On whether whole-number hot/cold is already inside S1/S2: the first test of the restarted scan supports your point. With no parameter, whole-number hot picks scored about the same as S1 and cold about the same as S2, all near chance. The full scan will show whether that holds with parameters.

**What I tested:** 84 exact features at 7:00 pm on each draw date.
- **Longitudes:** where the Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu and the Ascendant are, to the degree.
- **Angles:** the angle between every pair of those, 36 pairs.
- **Aspects:** for each pair, whether it is in conjunction (0°), sextile (60°), square (90°), trine (120°) or opposition (180°), within 6°.
- **Position within the sign:** how far the Moon is through its nakshatra and its rashi, and how far the Ascendant is through its rashi.

**How:** each feature split into 15° slices (or aspect types). From the 1985–2011 draws I learned which digits tend to come up in each position for each slice. Then I measured on 2012–2026, over 170,285 winning numbers, whether knowing the feature predicts the digits better than the overall digit mix. The same was repeated on 30 calendars shifted by a year or more, to see what chance looks like.

**Results:**

| | Real calendar | Shifted calendars (chance) |
|---|---|---|
| Features that predict digits better than the overall mix | **0 of 84** | 0 |
| Best feature (Sun–Mercury aspect) | −0.002 | best around −0.009 (range −0.015 to −0.001) |
| Average over all features | −0.253 | −0.243 |

Scores are in thousandths of a unit of information per digit: 0 means the feature tells you nothing, positive would mean it predicts.

- **No feature beat the plain overall digit mix.** Every score is slightly negative, which is what happens when there is no real pattern: the patterns learned before 2012 were just noise and made predictions a little worse after 2012.
- **By group, all at chance:** exact longitudes −0.50, angles between planets −0.36, aspects −0.08, position within nakshatra or rashi −0.39 to −0.41. Aspects score closest to zero only because they are coarser (5 types plus none), so there is less noise to overfit. They aren't predicting anything.

So, like the named categories, the exact planetary positions and aspects show no link to the digits. The script, results and cached planet positions are committed and pushed.

I've committed and pushed the bug fix to the whole-number test, so the repo has no uncommitted changes. The whole-number scan itself is still running, about 50 minutes in total. I'll commit its results and report when it finishes.

Whole-number hot and cold picks also come out at chance, so you were right that they add nothing beyond S1/S2.

**What I tested:** for each of the 78 single parameters and 3,003 pairs, I took all earlier draw days with the same value. Hot is the 16 numbers that won most often on those days, and cold is the 16 that won least often. Each was scored as Straight, Reverse and i-Box. The 5 best tests were chosen on 1985–2011 and checked on 2012–2026, then the whole procedure was repeated on 4 shifted calendars to see what chance gives.

**Results after 2012** (average z of the 5 tests chosen before 2012; 0 means chance):

| Picks | Real calendar | Shifted calendars (chance) |
|---|---|---|
| Hot, Straight | −0.16 | +0.13 |
| Hot, Reverse | −0.63 | −0.03 |
| Hot, i-Box | +0.12 | −0.05 |
| Cold, Straight | +0.61 | +0.91 |
| Cold, Reverse | −1.65 | −1.28 |
| Cold, i-Box | −0.18 | −0.15 |

- **Nothing carried forward.** The tests that looked best before 2012 averaged about chance afterwards, and the real calendar didn't beat the shifted ones in any combination.
- **Hot, Straight** had the strongest single test over all years: KP Moon number × Year element, z +4.31, which no shifted calendar matched. But the 5 tests chosen fairly, before 2012, all fell to about ×1.00 after 2012. One test standing out over all the data isn't evidence when the ones chosen in advance don't hold up.
- **Cold, Straight** looks positive (+0.61), but the shifted calendars did even better (+0.91), so it comes from cold numbers generally, not the parameters.

**Without parameters**, hot and cold whole numbers scored ×0.88 to ×1.06 after 2012, all within chance.

**Today's two tests together:**

| Test | Result |
|---|---|
| Exact planetary positions and aspects (84 features) | None predicts digits; all slightly below the plain overall mix |
| Whole-number hot / cold (3,081 tests) | At chance; no carry-over from before 2012 to after |

Both scripts and their results are committed and pushed, and both tests are listed in `FINDINGS.md`. Of the five suggestions, the remaining ones are the randomness check of each operator (5), the Singapore draw that comes about 30 minutes earlier (1), links within a draw and across operators (2), and date/draw-number numerology (4).

---

## 58. Question (2026-10-19 01:53)

> Ok now let’s test S3- mixture of hot and cold digits where you take the extreme cold and hot and combine them, test this just like how you tested S1 and S2 for all astrological parameters single and pairs

**Answer** (2026-10-19 01:53)

S3 takes the single hottest and single coldest digit in each position and combines them, 2 × 2 × 2 × 2 = 16 numbers. I'll run it the same way as S1 and S2: all 78 single parameters and 3,003 pairs, versions (a) and (b), and Straight, Reverse and i-Box. It gets the same walk-forward check (choose on 1985–2011, test on 2012–2026) and shifted-calendar checks.

The picks come out right, with the hottest and coldest digit combined in each position, and each test takes 0.07 seconds. I'm starting the real scan plus 20 shifted calendars, about 25 minutes.

The S3 scan is running in the background and should take about 25 minutes. The script is committed and pushed.

**S3 picks:** in each position, take the single hottest digit and the single coldest digit from the earlier draw days with the same value(s), and combine them: 2 × 2 × 2 × 2 = 16 numbers. For example, hottest 7-3-4-7 and coldest 2-8-0-9 give 7347, 7349, … 2809.

It covers 78 single parameters and 3,003 pairs, for versions (a) all earlier same-value days and (b) the previous same-value day only, scored as Straight, Reverse and i-Box on all 3 operators.

As with S1 and S2, I'll report:
- the number of tests with z > 2 and the best z, compared with 20 shifted calendars;
- a forward check: the 5 best tests chosen on draws before 2012, scored on 2012–2026, also compared with the shifted calendars;
- a no-parameter S3 for reference.

I'll report back when it finishes.

S3 (the hottest and coldest digit in each position, combined into 16 numbers) didn't beat chance either, and it came out slightly weaker than S1 and S2.

**Main results, compared with 20 shifted calendars:**

| Version | Tests with z > 2, real (chance) | Best z, real (chance) | Forward after 2012, real (chance) |
|---|---|---|---|
| (a) all earlier days, Straight | 46 (64) | +3.08 (+3.55) | −0.34 (+0.16) |
| (a) Reverse | 71 (71) | +3.84 (+3.60) | −0.48 (+0.03) |
| (a) i-Box | 71 (61) | +3.18 (+3.48) | −0.18 (+0.05) |
| (b) previous day, Straight | 15 (41) | +2.78 (+3.28) | −0.64 (−0.18) |
| (b) Reverse | 43 (58) | +3.06 (+3.27) | −0.10 (−0.10) |
| (b) i-Box | 22 (23) | +3.35 (+2.93) | +0.21 (−0.09) |

"Forward" is the average z on 2012–2026 of the 5 tests chosen on 1985–2011; 0 means chance.

- **Counts and best scores are within chance.** The number of tests with z > 2 is at or below the shifted calendars in every version, and the best z stays inside their range. The S3 (a) Straight best is lower than all 20 shifted calendars.
- **Picks chosen fairly don't hold up.** The tests that looked best before 2012 averaged slightly below chance afterwards in 5 of 6 versions. For example, Mars nakshatra × Solar term was z +3.28 before 2012 and ×0.97 after; Lunar day × Month stem was z +4.02 before and ×0.995 after.
- **The best forward result was (b) i-Box,** at +0.21 against −0.09 for chance, but 6 of 20 shifted calendars did as well, so it isn't significant. Its strongest single test was Mercury nakshatra × Day element (×1.03 after 2012), a gain too small to make money with i-Box.
- **Without a parameter,** S3 scored ×0.91 to ×1.05 after 2012, all chance.

**Comparison of all three:**

| Strategy | Best forward result | Verdict |
|---|---|---|
| S1 (two hottest digits) | Mercury nakshatra × Venus rashi, ×1.13 after 2012 (later looked like a fluke) | chance |
| S2 (two coldest digits) | no consistent edge | chance |
| S3 (hottest + coldest) | slightly below chance in 5 of 6 versions | chance |

Mixing hot and cold digits doesn't create an edge where neither hot nor cold had one.

The script and results are committed and pushed (`analysis/recurrence_s3.py`), and S3 is listed in `FINDINGS.md`. The remaining untested ideas are the randomness check of each operator, the earlier Singapore draw, links within a draw and across operators, and date/draw-number numerology.

---

## 59. Question (2026-10-19 06:56)

> Ok we have tried the hottest and the coldest extreme, now I want you to try similarly but for the second hottest and the second coldest, and then the third and so on

**Answer** (2026-10-19 06:57)

The digits in each position can be ranked from hottest (1st) to coldest (10th), and S3 combined the 1st with the 10th. The next pairs are 2nd + 9th, 3rd + 8th, 4th + 7th and 5th + 6th, which ends at the middle. I'll run all of them, plus S3 again for comparison, in one scan with the same checks as before.

The picks come out right for every rank pair, and each test takes 0.24 seconds. I'm starting the real scan plus 10 shifted calendars, about 35 minutes.

The scan is running in the background and should take about 35 minutes. The script is committed and pushed.

In each position the digits are ranked from 1 (hottest) to 10 (coldest), using the earlier draw days with the same parameter value(s). Each rank pair takes one digit from each end, giving 16 numbers:

| Pair | Digits used in each position |
|---|---|
| 1+10 | hottest + coldest (S3, rerun for comparison) |
| 2+9 | 2nd hottest + 2nd coldest |
| 3+8 | 3rd hottest + 3rd coldest |
| 4+7 | 4th hottest + 4th coldest |
| 5+6 | the two middle digits |

Each pair covers 78 single parameters and 3,003 pairs, for versions (a) all earlier same-value days and (b) the previous same-value day only, scored as Straight, Reverse and i-Box. That makes 30 combinations of rank pair, version and match type. Each gets:
- the number of tests with z > 2 and the best z, compared with 10 shifted calendars;
- a forward check: the 5 best tests chosen on 1985–2011, scored on 2012–2026, also compared with the shifted calendars;
- the same picks with no parameter, for reference.

At the end I'll compare the five rank pairs side by side, to see whether any position on the hot–cold scale does better than the others.

No rank pair beats chance. Of the 30 combinations, 3 beat all 10 shifted calendars, about what chance gives (2.7).

Each pair takes the k-th hottest and k-th coldest digit in each position, from the earlier draw days with the same parameter value(s), and combines them into 16 numbers. It was run for 78 single parameters and 3,003 pairs, versions (a) and (b), and Straight, Reverse and i-Box. "Forward" is the average z on 2012–2026 of the 5 tests chosen on 1985–2011; 0 means chance.

**By rank pair** (averaged over versions and match types):

| Rank pair | Forward z, real | Forward z, shifted (chance) | Real beats % of shifts | No parameter, after 2012 |
|---|---|---|---|---|
| 1st + 10th (S3) | −0.08 | −0.17 | 55% | ×0.98 |
| 2nd + 9th | −0.28 | −0.35 | 52% | ×0.96 |
| 3rd + 8th | −0.09 | −0.04 | 47% | ×1.01 |
| 4th + 7th | +0.03 | +0.04 | 52% | ×0.97 |
| 5th + 6th (middle) | +0.28 | −0.16 | 77% | ×1.02 |

- All five are close to their shifted-calendar level. The middle digits (5th + 6th) come out highest, but 77% of shifts falls short of significance (that needs about 95%).

**The 3 combinations that beat every shifted calendar:**

| Combination | Forward z (shifted) | Its best tests after 2012 |
|---|---|---|
| 5+6 (b) i-Box | +1.54 (−0.04) | KP Ascendant number × Year pillar ×1.11; × Month stem ×1.01 |
| 2+9 (b) Straight | +1.08 (−0.26) | KP Moon number × Year element ×1.16; Tithi × Sun nakshatra ×1.11 |
| 1+10 (b) Reverse | +0.68 (−0.44) | KP Moon number × Lunar leap month ×1.06 |

- With 30 combinations checked, about 3 are expected to look like this by luck. Several of those tests also return identical picks (Month stem and Month pillar give the same result), so there's less independent evidence than the count suggests.

**S3 is unstable.** I reran it here with one small change: when two digits tie for coldest, it now takes the higher digit instead of the lower one. That alone moved S3 (a) Straight's forward result from −0.34 to +0.35. A real pattern wouldn't flip sign over a tie-break, so these small differences are noise.

**Across all the digit-ranking strategies so far:**

| Strategy | Result |
|---|---|
| S1 (2 hottest) | chance |
| S2 (2 coldest) | chance |
| S3 (hottest + coldest) | chance |
| 2nd + 9th, 3rd + 8th, 4th + 7th, 5th + 6th | chance |
| Whole-number hot / cold | chance |

No position on the hot-to-cold scale predicts better than another, with or without astrological parameters. That's what you'd expect if each digit is drawn independently with equal chances, whatever happened before.

The script (`analysis/recurrence_rankpairs.py`) and results are committed and pushed, and the test is listed in `FINDINGS.md`.

---

## 60. Question (2026-10-19 10:20)

> But among all this which is the top lead so far? Which performed well all the time especially when it is being updated before every draw?

**Answer** (2026-10-19 10:20)

Every walk-forward result in these tests already rebuilds the picks before each draw: version (a) recounts from all earlier same-value days and version (b) uses the latest one. So the 2012–2026 numbers measure performance when the picks are updated before every draw. I'll check year by year which leads were above chance most consistently.

Karana × Day pillar stands out: above chance in 14 of 15 years. Before calling it the top lead I'll check that against chance, using the same test on 50 shifted calendars and a no-parameter version.

The most consistent lead is **Karana × Day pillar, S1, i-Box**. Its edge is small, though, and it would still lose money.

All the year-by-year figures below already rebuild the picks before every draw, using only the results before it.

**How it works:** take the most recent earlier draw day with the same Karana and Day pillar as today. Use the 2 most frequent digits in each position of that day's winning numbers, giving 16 numbers, and bet them as i-Box.

**Year-by-year results, 2012–2026** (hits relative to chance; above 1.00 means better than chance):

| Lead | Years above chance | 2012–2026 | 2019–2026 |
|---|---|---|---|
| **Karana × Day pillar, S1 (b) i-Box** | **14 of 15** | ×1.04 | ×1.035 |
| KP Moon number × Year element, 2+9 (b) Straight | 11 of 15 | ×1.16 | ×1.16 |
| Jupiter nakshatra × Mercury combust, S2 (a) i-Box | 11 of 15 | ×1.03 | ×1.02 |
| Mercury nakshatra × Venus rashi, S1 (a) Straight | 10 of 15 | ×1.13 | ×1.03 (faded) |
| Tithi × Sun nakshatra, 2+9 (b) Straight | 10 of 15 | ×1.11 | ×1.15 |
| KP Ascendant number × Year pillar, 5+6 (b) i-Box | 10 of 15 | ×1.11 | ×1.05 |

**Karana × Day pillar** was between ×0.99 and ×1.13 in every year, and only 2016 was just below chance.

**Checks against chance:**
- **50 shifted calendars:** none reached 14 good years; they averaged 7.7 of 15. None reached ×1.04 either; their average was ×1.002.
- **Same picks without the parameter:** 6 of 15 years, ×0.995. The Karana × Day pillar condition is what makes the difference.
- **Selection:** it was chosen from the 1985–2011 draws only, as one of about 60 picks checked forward. Allowing for that, the chance of a result this consistent by luck is about 3%.

This is the only lead that has held up in every way I tested it.

**Why it still isn't a money-maker:**
- **The gain is small.** ×1.04 means about 4% more i-Box matches than chance. As i-Box, that returns about 67% of stakes instead of about 64%, so you would still lose about a third of what you bet over time.
- **Live so far:** 2 i-Box Consolation matches on 17 Oct and 5 i-Box Specials on 18 Oct. Chance gives about 1.8 a day, so that's above average, but two days is too few to count.

**The other leads:**
- **KP Moon number × Year element** has the biggest gain (×1.16), but it's a Straight bet and above chance in only 11 of 15 years.
- **Mercury nakshatra × Venus rashi**, the old top lead, has faded since 2019 and is no longer first.

The picks for Wednesday 21 Oct are already logged, built from all results through 18 Oct, and will update before each draw from now on. Karana × Day pillar's picks are 6340 6342 6370 6372 6440 6442 6470 6472 9340 9342 9370 9372 9440 9442 9470 9472, for i-Box. I've added this result to `FINDINGS.md` and pushed it.

---

## 61. Question (2026-10-19 10:23)

> How did all this leads perform from the last 3 draws?

**Answer** (2026-10-19 10:24)

I'll rebuild each lead's picks for the last 3 draws (14, 17 and 18 Oct), using only the results before each draw, and score them as Straight and i-Box.

The S2 Mars triple's Magnum 1st prize hit on 14 Oct (3872) stands out. Before reporting it I'll check how that lead was chosen, since 14 Oct was one of the 5 draws in the earlier last-5 test.

Over the last 3 draws (14, 17 and 18 Oct), the S2 Mars triple did best by far, mainly because it hit Magnum's 1st prize, 3872, on 14 Oct. That's most likely luck: the many formulas checked together would be expected to land about one big prize like this.

Each lead's picks were rebuilt before each draw from only the results before it. Every lead had 48 numbers per draw (16 on each operator), so RM144 staked over the 3 draws; the cold number (3 per draw) and 1024 (1 per draw) are the exceptions.

**Totals over the 3 draws:**

| Lead | Straight hits | Straight won | i-Box matches | i-Box won (approx.) |
|---|---|---|---|---|
| **S2 Mars triple** | **2** (3872 Magnum **1st**; 8426 Toto Consolation) | **RM2,560** | 10 | ~RM220 |
| Tithi × Sun nakshatra, 2+9 (b) | 2 (1613 Magnum Special; 2533 Magnum Special) | RM360 | 5 | ~RM55 |
| KP Ascendant number × Year pillar, 5+6 (b) | 2 (4454 DMC Consolation; 5304 Toto Consolation) | RM120 | 11 | ~RM102.50 |
| KP Moon number × Year element, 2+9 (b) | 1 (4974 DMC Consolation) | RM60 | 6 | ~RM51 |
| **Karana × Day pillar, S1 (b)** (most consistent lead) | 0 | RM0 | 9 | ~RM55 |
| Jupiter nakshatra × Mercury combust, S2 (a) | 0 | RM0 | 4 | ~RM40 |
| Mercury nakshatra × Venus rashi, S1 (a) | 0 | RM0 | 4 | ~RM30 |
| S1 Mars triple | 0 | RM0 | 2 | ~RM10 |
| Cold number (RM9) | 0 | RM0 | 0 | RM0 |
| 1024 Magnum (RM3) | 0 | RM0 | 0 | RM0 |

**By draw:**

| Lead | 14 Oct | 17 Oct | 18 Oct |
|---|---|---|---|
| S2 Mars triple | **3872 Magnum 1st** | 8426 Toto Consolation | i-Box only |
| Tithi × Sun nakshatra | 1613 Magnum Special | 2533 Magnum Special | 0 |
| KP Ascendant number × Year pillar | 4454 DMC Consolation | 0 | 5304 Toto Consolation; 7 i-Box |
| KP Moon number × Year element | 4 i-Box near-misses... 0 Straight | 0 Straight | 4974 DMC Consolation; also 4973, an i-Box match for Toto's 3rd prize 4937 |
| Karana × Day pillar | 2 i-Box | 2 i-Box | 5 i-Box |

**About the 3872 1st prize:**
- **The formula was chosen fairly.** It was picked in the earlier S1/S2 search because it was above chance in both 2012–2017 and 2018–2026. That search held out the last 5 draws (4–14 Oct), and the 14 Oct picks used no results from those draws. So the hit wasn't fitted to that draw.
- **But I then logged it for 17, 18 and 21 Oct partly because of that 3872 hit.** That isn't evidence it works.
- **Luck is the likely explanation.** About 60 sixteen-number formulas were scored on those 5 held-out draws. Together they'd be expected to land about 1.4 big hits (1st, 2nd or 3rd prize) by chance. One 1st prize among them is ordinary.

**Overall:** 4 of the 8 sixteen-number leads were in profit on Straight over these 3 draws, but that rests on 7 Straight hits in total. At the leads' rates, 3 draws are far too few to tell skill from luck.

**Karana × Day pillar,** the most consistent lead over 15 years, had no Straight hits but 9 i-Box matches. Chance gives about 5 to 6 over 3 draws, so it was above average, but that's still worth only about RM55 on RM144 staked.

The next fair test is Wednesday 21 Oct. All these picks are already logged and were built only from results up to 18 Oct.

---

## 62. Question (2026-10-19 10:33)

> Explain what is a and b for S1 and S2

**Answer** (2026-10-19 10:34)

**(a)** and **(b)** say which earlier draws the digits are counted from. Both start the same way:

1. Look up the parameter value(s) for the coming draw, for example Mercury in Vishakha and Venus in Tula.
2. Find the earlier draw days that had the same value(s).
3. Count the digits in each position of those days' winning numbers (all 23 prizes from each of the 3 operators).
4. S1 takes the 2 most frequent digits in each position and S2 the 2 least frequent, giving 2 × 2 × 2 × 2 = 16 numbers.

They differ in step 3.

**(a) All earlier same-value days.** Every earlier draw day with the same value(s) is counted, back to 1985.
- Example: Mercury nakshatra × Venus rashi on 17 Oct (Vishakha + Tula) used 102 earlier draw days from 1986 to 2026, about 7,000 winning numbers.
- With so much data the counts are stable and the picks change slowly. One new draw barely moves them, which is why the 17 and 18 Oct picks came out identical.

**(b) Only the most recent earlier same-value day.** Only the last draw day before this one with the same value(s) is counted.
- Example: Karana × Day pillar on 21 Oct (Vanija + Wu Chen) uses only 28 Jun 2025, the last earlier draw with that combination. That's about 69 winning numbers.
- With so little data the picks change completely from one occurrence to the next. It assumes the most recent matching day matters most.

| | (a) All earlier days | (b) Most recent day |
|---|---|---|
| Days counted | all matching days since 1985 (often 50–200) | 1 |
| Numbers counted | thousands | about 69 |
| Picks | stable, change slowly | change completely each time |
| Assumes | the pattern builds up over all of history | the latest matching day carries the signal |
| Example lead | Mercury nakshatra × Venus rashi, S1 (a) | Karana × Day pillar, S1 (b) |

Both versions use only draws before the one being predicted, so they update themselves after every draw.

---

## 63. Question (2026-10-20 00:07)

> Check if d9 navamsa plays a role single or as pair, redo all the analysis that we have already done specifically on this family.

**Answer** (2026-10-20 00:07)

I'll build the D9 navamsa family from the exact planet positions already computed: the navamsa sign of the Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu and the Ascendant, plus vargottama for each body (the same sign in D1 and D9). That's 18 parameters. So far only the Moon's navamsa had been tested.

Then I'll rerun the main analyses on this family: the 18 single parameters, all pairs within the family, and each navamsa parameter paired with the 78 existing parameters, 1,575 tests in total.

The D9 navamsa analysis is running in the background and should take about an hour. The script (`analysis/navamsa_family.py`) is committed and pushed.

Until now only the Moon's navamsa had been tested. This run adds 18 navamsa parameters:
- **Navamsa sign (D9)** of the Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu and the Ascendant.
- **Vargottama** for each of those 9: the body is in the same sign in D1 and D9, which happens on about 1 draw day in 9.

That gives 1,557 tests: the 18 alone, all 153 pairs within the family, and each one paired with the other 77 Vedic and Chinese parameters.

These are the earlier analyses, rerun on this family:

| | Analysis | Same as before |
|---|---|---|
| A | Digit mix for each value: learned on 1985–2011, tested on 2012–2026 | as in the exact-astrology test |
| B | Same 4D number coming back when the value recurs: Straight, Reverse, i-Box; any later day and next day | as in the number-recurrence tests |
| C | Digit-position picks from earlier same-value days, versions (a) and (b): S1, S2, S3, and rank pairs 2+9, 3+8, 4+7, 5+6; Straight, Reverse, i-Box | as in the S1/S2, S3 and rank-pair tests |
| D | Whole-number hot and cold picks | as in the whole-number test |

Each analysis is compared with the same scan on shifted calendars. C and D also get the forward check: the 5 best tests chosen before 2012, scored on 2012–2026. I'll report the results when it finishes.

The D9 navamsa family doesn't play a role. Across 1,557 tests (navamsa and vargottama for 9 bodies, alone and in pairs), every analysis lands within the range chance gives.

**A. Digit mix for each navamsa value** (learned on 1985–2011, tested on 2012–2026):
- No navamsa or vargottama value predicts the digits. All 18 single parameters score slightly below zero, from −0.006 to −0.26, against 0 for no information.
- Only 1 of the 1,557 tests scored above zero, Mercury vargottama × Year pillar, at +0.000. Shifted calendars had 0 such tests, so this is just rounding.

**B. Same 4D number coming back when the value recurs:**

| Match | Best z (shifted calendars' best) |
|---|---|
| Straight, any later day | +2.77 (+2.93) |
| Straight, next day | +2.30 (+2.68) |
| Reverse, any later day | +3.03 (+3.14) |
| Reverse, next day | +2.94 (+3.00) |
| i-Box, any later day | +12.37 (+11.10) |
| i-Box, next day | +3.27 (+2.86) |

All within chance. The i-Box "any later day" scores are always huge because i-Box matches are very lumpy; the shifted calendars reach the same level.

**C. Digit-position picks** (S1, S2, S3 and rank pairs 2+9 to 5+6; versions a and b; Straight, Reverse, i-Box; 42 combinations):

| | Real calendar | Shifted calendars (chance) |
|---|---|---|
| Average forward z after 2012 | −0.02 | −0.06 |
| Combinations beating every shifted calendar | 6 | about 4.7 |

One combination stood out on two counts: **S2 (b) Straight**, the 2 coldest digits from the previous same-value day.
- **Many high-scoring tests:** 54 tests with z > 2, against 15 on average for the shifted calendars.
- **Held up forward:** +0.93 against −0.09, beating all 8 shifted calendars.
- **Best test:** Mercury navamsa × Venus rashi, z +3.11 before 2012, then ×1.10 after (z +1.70).
- **But it's 1 of 42 combinations,** and on its own that edge is too small and too uncertain to use. Mercury and Venus showing up again is interesting, since the old top lead was Mercury nakshatra × Venus rashi.

**D. Whole-number hot and cold:** forward results at or below the shifted calendars in all 6 combinations.

**Verdict:** navamsa and vargottama behave like every other parameter family: no measurable effect on the results. The only thing worth noting is S2 (b) Straight with Mercury navamsa × Venus rashi. I can log its picks as a live test from 21 Oct if you'd like, but I wouldn't count it as a lead yet.

The script and results are committed and pushed, and the test is listed in `FINDINGS.md`.

---

## 64. Question (2026-10-20 05:14)

> Check how the other D does than

**Answer** (2026-10-20 05:14)

By "the other D" I take it you mean the other divisional charts (vargas). I'll test 13 of them for all 9 bodies, using the standard Parashara rules:

| Chart | Name |
|---|---|
| D2 | Hora |
| D3 | Drekkana |
| D4 | Chaturthamsa |
| D7 | Saptamsa |
| D10 | Dasamsa |
| D12 | Dwadasamsa |
| D16 | Shodasamsa |
| D20 | Vimsamsa |
| D24 | Chaturvimsamsa |
| D27 | Bhamsa |
| D30 | Trimsamsa |
| D40 | Khavedamsa |
| D45 | Akshavedamsa |
| D60 | Shashtiamsa |

That's 14 charts, 126 parameters. I'll run the same suite as for D9 (tests A–D). First I'll make the D9 script reusable.

The divisional-charts test is running in the background and should take about 25 minutes. The script (`analysis/divisional_charts.py`) is committed and pushed.

It works out the sign of the Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu and the Ascendant in 14 divisional charts at 7:00 pm on each draw date, using the standard Parashara rules:
- **Charts:** D2, D3, D4, D7, D10, D12, D16, D20, D24, D27, D30, D40, D45 and D60.
- **Tests:** the 126 resulting parameters alone, plus all 36 pairs within each chart, 630 tests in total.
- **Analyses:** the same four as for D9.
  - A: digit mix for each value.
  - B: the same number coming back.
  - C: S1, S2, S3 and the rank-pair picks.
  - D: whole-number hot and cold.
- **Checks:** each analysis is compared with 8 shifted calendars, and the forward check uses picks chosen on 1985–2011 and scored on 2012–2026.

**Ascendant in the finer charts:** it moves about 1° every 4 minutes. The draw runs from 7:00 to 7:30 pm, so its sign in D30 and above is uncertain. I calculated it at 7:00 pm, so those results for the Ascendant are less reliable.

I'll report the results by chart when it finishes.

The per-chart summary at the end has a bug: matching "_d2" also picks up D20, D24 and D27, and "_d4" picks up D40 and D45. I'll recompute it from the saved results with exact chart matching.

None of the other divisional charts play a role either. Across 630 tests (14 charts × 9 bodies, alone and in pairs within each chart), every analysis is at chance.

**A. Digit mix for each chart's values** (learned on 1985–2011, tested on 2012–2026; 0 means no information):

| Chart | Best test | Average |
|---|---|---|
| D2 Hora | −0.010 | −0.05 |
| D3 Drekkana | −0.140 | −1.22 |
| D4 | −0.155 | −1.27 |
| D7 | −0.145 | −1.26 |
| D10 Dasamsa | −0.162 | −1.31 |
| D12 | −0.157 | −1.29 |
| D16 | −0.149 | −1.29 |
| D20 | −0.143 | −1.29 |
| D24 | −0.166 | −1.33 |
| D27 | −0.153 | −1.29 |
| D30 Trimsamsa | −0.125 | −1.01 |
| D40 | −0.175 | −1.32 |
| D45 | −0.133 | −1.28 |
| D60 Shashtiamsa | −0.135 | −1.33 |

- **No test in any chart beat the plain overall digit mix** (0 of 630; shifted calendars also had 0).
- The finer charts score worse, but that's expected: more values means more to learn from noise. D2 scores closest to zero only because it has just two values (Leo or Cancer).

**B. Same number coming back:** the best result in every match type and version is inside the shifted-calendar range. For example, Straight on any later day had a best z of +2.92 against +3.10 by chance.

**C. Digit-position picks** (S1, S2, S3 and rank pairs, 42 combinations):

| | Real calendar | Shifted calendars (chance) |
|---|---|---|
| Average forward z after 2012 | −0.11 | −0.05 |
| Combinations beating every shifted calendar | 4 | about 4.7 |

The best forward picks were tiny after 2012: Sun D3 × Lagna D3 at ×1.09, and Mercury D12 at ×1.01.

**D. Whole-number hot and cold:**
- **Hot, Straight** beat all 4 shifted calendars, at +0.81 against −0.14.
- That's 1 of 6 combinations, with only 4 calendars to compare against, so it isn't strong evidence.
- **The others** were at or below chance; for example Cold, Reverse was −1.55 against −1.16.

**Divisional charts so far:**

| Charts | Tests | Result |
|---|---|---|
| D1 (rashi, nakshatra and the other main parameters) | thousands | chance |
| D9 navamsa and vargottama | 1,557 | chance |
| D2 to D60 (14 charts) | 630 | chance |

None of the divisional charts shows a link to the 4D results.

The script and results are committed and pushed. I also fixed the per-chart summary in the script, and the test is listed in `FINDINGS.md`.

---

## 65. Question (2026-10-21 08:10)

> Ok now rank all the leads and give me their numbers to test for today

**Answer** (2026-10-21 08:10)

I'll check the time and data first, then build each lead's picks for tonight's draw (Wednesday 21 Oct) from all results through 18 Oct, the last draw.

It's 4:10 pm in Malaysia, before tonight's 7 pm draw, and the data runs through 18 Oct. Now the picks:

Lead 4 has no earlier draw with tonight's combination, because the Year pillar has been the same only since this Chinese year began. So it has no picks tonight. I'll skip it and continue.

These are the ranked leads with their numbers for tonight's draw (Wednesday 21 Oct). All picks are built from every result through 18 Oct, the last draw. I've logged them in `forward_log.csv` at 4:11 pm Malaysia time, before the 7 pm draw, and pushed the log.

**1. Karana × Day pillar, S1 (b), bet as i-Box.** The most consistent lead: above chance in 14 of 15 years since 2012 (×1.04).
Tonight: Vanija × Wu Chen, from the last matching draw on 28 Jun 2025.
6340 6342 6370 6372 6440 6442 6470 6472 9340 9342 9370 9372 9440 9442 9470 9472

**2. KP Moon number × Year element, 2nd + 9th digits (b), bet as Straight.** ×1.16 since 2012, above chance in 11 of 15 years.
Tonight: KP Moon number 211 × Fire, from 12 Oct 2016.
0562 0565 0572 0575 0962 0965 0972 0975 5562 5565 5572 5575 5962 5965 5972 5975

**3. Tithi × Sun nakshatra, 2nd + 9th digits (b), bet as Straight.** ×1.11 since 2012, 10 of 15 years; won 2 Magnum Specials in the last 3 draws.
Tonight: Tithi 11 × Chitra, from 13 Oct 2024.
5343 5348 5393 5398 5743 5748 5793 5798 9343 9348 9393 9398 9743 9748 9793 9798

**4. KP Ascendant number × Year pillar, 5th + 6th digits (b), i-Box: no picks tonight.** No earlier draw has tonight's combination (KP Ascendant number 5 in a Bing Wu year).

**5. Mercury nakshatra × Venus rashi, S1 (a), bet as Straight.** The former top lead: ×1.13 since 2012, but faded since 2019.
Tonight: Vishakha × Tula, from 104 earlier draw days.
6335 6337 6345 6347 6535 6537 6545 6547 7335 7337 7345 7347 7535 7537 7545 7547

**6. Jupiter nakshatra × Mercury combust, S2 (a), bet as i-Box.** ×1.03 since 2012, 11 of 15 years.
Tonight: Ashlesha × not combust, from 210 earlier days.
2640 2643 2650 2653 2840 2843 2850 2853 5640 5643 5650 5653 5840 5843 5850 5853

**7. S2 Mars triple (separate numbers for each operator), bet as Straight.** Hit Magnum's 1st prize, 3872, on 14 Oct, most likely luck.
- **Magnum:** 4226 4227 4266 4267 4626 4627 4666 4667 6226 6227 6266 6267 6626 6627 6666 6667
- **Sports Toto:** 0426 0428 0436 0438 0826 0828 0836 0838 8426 8428 8436 8438 8826 8828 8836 8838
- **Da Ma Cai:** 2342 2346 2362 2366 2742 2746 2762 2766 4342 4346 4362 4366 4742 4746 4762 4766

**8. Mercury navamsa × Venus rashi, S2 (b), bet as Straight.** New from the D9 test, not yet a proven lead.
Tonight: Vrishabha × Tula, from 18 Oct 2026.
5123 5129 5173 5179 5223 5229 5273 5279 7123 7129 7173 7179 7223 7229 7273 7279

**9. Cold number:** 6665 (Magnum), 8668 (Sports Toto), 5122 (Da Ma Cai).

Unless shown per operator, each set of 16 is meant for all 3 operators.

Even the best of these is only a few percent above chance, and as Straight or i-Box bets they would all still lose about a third of stakes over time. After tonight's draw I can fetch the results and score every lead.

---

## 66. Question (2026-10-21 11:46)

> Ok now check the latest result for today in google and tell me how they perform today and also for the last 3 days

**Answer** (2026-10-21 11:53)

Lead 5 hit Magnum's 2nd prize tonight: Mercury nakshatra × Venus rashi had 6537 in its 16 numbers. These picks were logged at 4:11 pm, before the draw. Bet RM1 Big on its 16 numbers with each of the 3 operators, that's **RM1,000 back on RM48 staked**. I took the results from check4d.org and 4dkingdom.com, which agree.

**Tonight's results (Wednesday 21 Oct)**

| | Magnum | Sports Toto | Da Ma Cai |
|---|---|---|---|
| 1st | 8450 | 5915 | 3145 |
| 2nd | **6537** | 4831 | 4268 |
| 3rd | 8694 | 4246 | 4566 |

**Tonight's results by lead**

| Lead | Straight | i-Box matches |
|---|---|---|
| 1 Karana × Day pillar | 0 | 3: 4036 Magnum Special, 4409 Toto Special, 4246 **Toto 3rd** (~RM64) |
| 2 KP Moon number × Year element | 0 | 1 |
| 3 Tithi × Sun nakshatra | 0 | 1 |
| 4 KP Ascendant number × Year pillar | no picks (no earlier matching day) | – |
| **5 Mercury nakshatra × Venus rashi** | **6537 Magnum 2nd, RM1,000** | 2 |
| 6 Jupiter nakshatra × Mercury combust | 0 | 2: 5840 matches **8450 Magnum 1st** (~RM104) |
| 7 S2 Mars triple | 0 | 0 |
| 7 S1 Mars triple | 0 | 1: 5480 matches **8450 Magnum 1st** (~RM104) |
| 8 Mercury navamsa × Venus rashi | 0 | 0 |
| 9 Cold number | 0 | 0 |

**Last 3 draws (17, 18 and 21 Oct)**, with each lead's picks rebuilt before every draw:

| Lead | Staked | Straight hits | Straight won | i-Box matches | i-Box won (approx.) |
|---|---|---|---|---|---|
| **5 Mercury nakshatra × Venus rashi** | RM144 | 1 (6537 Magnum 2nd) | **RM1,000** | 5 | ~RM77 |
| 3 Tithi × Sun nakshatra | RM144 | 1 (2533 Magnum Special) | RM180 | 3 | ~RM28 |
| 2 KP Moon number × Year element | RM144 | 1 (4974 DMC Consolation) | RM60 | 7 | ~RM53 |
| 4 KP Ascendant number × Year pillar | RM48 (picks on 1 day only) | 1 (5304 Toto Consolation) | RM60 | 7 | ~RM43 |
| 7 S2 Mars triple | RM144 | 1 (8426 Toto Consolation) | RM60 | 8 | ~RM101 |
| 1 Karana × Day pillar | RM144 | 0 | RM0 | 10 | ~RM114 |
| 6 Jupiter nakshatra × Mercury combust | RM144 | 0 | RM0 | 5 | ~RM134 |
| 7 S1 Mars triple | RM144 | 0 | RM0 | 3 | ~RM114 |
| 8 Mercury navamsa × Venus rashi | RM144 | 0 | RM0 | 2 | ~RM18 |
| 9 Cold number | RM9 | 0 | RM0 | 0 | RM0 |

- **Lead 5** is the only one in profit on Straight over these 3 draws: RM1,000 back on RM144.
- **Lead 1** (Karana × Day pillar), the most consistent lead over 15 years, had no Straight hits but the most i-Box matches (10). As i-Box it returned about RM114 on RM144, less than it cost.
- **Leads 6 and 7 (S1 Mars)** each had an i-Box match on Magnum's 1st prize tonight, worth about RM104 per RM1 as i-Box. They'd have paid nothing as Straight.

**Is lead 5 working?** Across all 10 leads, 5 Straight hits in 3 draws is about what chance gives (around 3). One 2nd prize among them is a lucky landing, not evidence the method works. Lead 5's long-run edge was about ×1.13, and it had faded since 2019. Still, this hit came on picks logged before the draw, so it's a real live result.

Tonight's results are added to the data. The new `analysis/score_leads.py` scores all the leads for any dates, and `FINDINGS.md` is updated with tonight's live results. Everything is pushed. The next draw is Saturday 24 Oct; the special draw on Tuesday 27 Oct follows. I can build and log fresh picks before each draw.

---

## 67. Question (2026-10-22 03:06)

> da liu ren, Tai Yi Shen Shu,Mei Hua Yi Shu ok and what about this 3? Have analysis on this done before?

**Answer** (2026-10-22 03:07)

No, none of these three has been tested yet. The nearest we've come is their building blocks: day pillar, hour stem at 7 pm, lunar day and month, year animal and solar term. Each method combines those in its own way, so they would be genuinely new tests.

**1. Da Liu Ren (大六壬)**
- **Inputs:** the day pillar, the hour branch (7 pm falls in the Xu 戌 hour) and the monthly general (月将), which follows the Sun's position.
- **What it produces:** a heaven plate rotated over the earth plate, the four lessons (四课), the three transmissions (三传) and the 12 heavenly generals.
- **Can it be computed?** Yes, it's fully determined by those inputs. The rules for the three transmissions have many special cases (贼克, 比用, 涉害, 遥克, 昴星, 别责, 八专, 伏吟, 返吟), but they're well documented and can be coded.
- **Parameters to test:** the first, middle and last transmission branches, the general on each, the day's lesson pattern, and the 伏吟/返吟 types.

**2. Tai Yi Shen Shu (太乙神数)**
- **Inputs:** the number of years and days counted from a starting epoch (太乙积年).
- **What it produces:** the Tai Yi palace and the host, guest and fixed counts (主算, 客算, 定算).
- **Interesting for 4D:** those counts are actual numbers (roughly 1 to 40), so they could be mapped straight to digits.
- **The catch:** schools use different starting epochs and counting rules, so I'd need to pick one standard convention, most likely the 太乙统宗 version, and state it clearly. Results would only apply to that convention.

**3. Mei Hua Yi Shu (梅花易数)**
- **Time casting:**
  - upper trigram = (year-branch number + lunar month + lunar day) mod 8
  - lower trigram = the same plus the hour-branch number, mod 8
  - moving line = the total, mod 6
- **What it produces:** the main hexagram, the changed hexagram, the mutual hexagram, and the trigram numbers (先天 numbers 1–8), which some players turn into 4D digits.
- **Can it be computed?** Yes, it's the easiest of the three.

**How I'd test them:** the same way as before.
- **Analyses A–D:** the digit mix for each value, numbers coming back when a value recurs, the S1, S2, S3 and rank-pair picks, and whole-number hot and cold. Each one alone and paired with the 78 existing parameters.
- **Direct number tests:** whether the numbers these methods produce (Tai Yi counts, Mei Hua trigram numbers, Liu Ren branch numbers) turn up as 4D digits more often than chance.
- **Checks:** shifted calendars and the walk-forward check (choose on 1985–2011, test on 2012–2026).

Should I run all three? Mei Hua and Da Liu Ren are fully determined by the inputs above. For Tai Yi I'd use the 太乙统宗 convention unless you follow a different school.

---

## 68. Question (2026-10-22 04:28)

> Yes

**Answer** (2026-10-22 04:31)

The analysis of the three methods is running in the background and should take about an hour. The script (`analysis/chinese_divination.py`) is committed and pushed.

**What each method contributes (20 new parameters):**

| Method | Parameters |
|---|---|
| Mei Hua Yi Shu (time casting at the 7 pm Xu hour) | upper, lower and main hexagram, moving line, changed hexagram, mutual hexagram, body/use (体用) relation |
| Da Liu Ren (7 pm plate) | monthly general (plate rotation), first, middle and last transmission, all three together, heavenly general on the first transmission (night noble), method used, number of 贼 and 克 lessons |
| Tai Yi | the day count's 72, 24 (palace), 18 (Wenchang) and 360-day cycles |

**Tests:** 1,780, made up of the 20 alone, all pairs within the group, and each one paired with the 78 existing parameters. They go through analyses A–D:
- A: digit mix for each value
- B: numbers coming back
- C: S1, S2, S3 and the rank pairs
- D: whole-number hot and cold

Each is compared with shifted calendars, and C and D also get the walk-forward check.

**Direct number test:** do the Mei Hua numbers (upper, lower, moving line) and the Liu Ren transmission branch numbers turn up among each draw's winning digits more often than chance?

**What I simplified:**
- **Da Liu Ren 涉害:** when the main rules leave a tie, this rule normally decides by depth. I used a simpler tie-break: 孟 first, then 仲, then the first lesson.
- **Da Liu Ren 别责 and 八专:** these special rules aren't implemented separately; the cases they cover fall back to the other rules.
- **Tai Yi host and guest counts (主算, 客算):** left out, because they depend on one school's conventions. The cycle tests cover every epoch, but not those counts.

I'll report the results when the run finishes.

I fixed the bug, and the full run has restarted in the background. It takes about an hour.

A quick run of the direct number test (with only 3 shifted calendars) already shows no effect:

| Numbers | Winning digits that match, vs expected | z |
|---|---|---|
| Mei Hua (upper, lower, moving line) | ×0.998 | −1.20 |
| Da Liu Ren (transmission branch numbers) | ×1.0008 | +0.52 |

Both are within ordinary variation, and the full run repeats this test against 30 shifted calendars.

One thing to know about Mei Hua cast at a fixed 7 pm hour: the lower trigram is always the upper plus 3 (mod 8), so only 8 of the 64 hexagrams ever occur. The test still covers all of them; there are just fewer distinct values.

I'll report all three methods when the run finishes.

That edit to the shared script was the wrong approach, so I'll undo it and add a separate D-only option to the Chinese divination script instead.

The whole-number part (D) is running again on its own, with 4 shifted calendars; it should take about 25 minutes. The other analyses (A–C) and the direct number test finished, and none of the three methods shows an effect.

**Direct number test** (30 shifted calendars):

| Numbers | Winning digits matched, vs expected | Shifted calendars as high |
|---|---|---|
| Mei Hua upper, lower and moving-line numbers | ×0.998 | 27 of 30 |
| Da Liu Ren transmission branch numbers | ×1.0008 | 10 of 30 |

**A. Digit mix for each value** (learned on 1985–2011, tested on 2012–2026; 0 means no information): 1 test out of 1,672 scored above zero, at +0.001. Shifted calendars managed 0.8 such tests on average, so this is chance. All 20 parameters on their own score below zero:
- Mei Hua: −0.03 to −0.37
- Liu Ren: −0.12 to −1.05
- Tai Yi cycles: −0.36 to −1.06

**B. Same number coming back when a value recurs:** the best results sit inside the shifted-calendar range, with one exception. i-Box on any later day reached z +10.84 (Liu Ren method × Mars retrograde), against at most +5.90 on the shifted calendars. But the actual gain is only ×1.002, and i-Box scores in this version have always been inflated. It isn't a usable effect.

**C. Digit-position picks** (S1, S2, S3 and rank pairs; 42 combinations):

| | Real calendar | Shifted calendars (chance) |
|---|---|---|
| Average forward z after 2012 | −0.15 | −0.07 |
| Combinations beating every shifted calendar | 3 | about 4.7 |

The best test held up only a little:
- **Tai Yi 360-day cycle × Yoga** (3rd + 8th digits, previous same-value day, Straight): ×1.12 after 2012 (z +1.34).
- That rests on a 360-value cycle split further by Yoga. Each such day pairing has only a few earlier matching days, so the result is very noisy.

So far Mei Hua, Da Liu Ren and the Tai Yi cycles all come out at chance, like every other system tested. I'll add the whole-number results and commit everything when the last part finishes.

I've committed and pushed the pending changes, so the repo is clean. That covers:
- the bug fix in the whole-number test,
- the option to rerun only the whole-number part,
- the saved results from the analyses that already finished.

The whole-number part is still running. When it finishes I'll add its results to the same results file, commit, and send you the final summary for all three methods.

None of the three methods (Mei Hua Yi Shu, Da Liu Ren, Tai Yi) shows any link to the 4D results. The whole-number part, the last one, is done too.

**D. Whole-number hot and cold** (forward z after 2012; 0 means chance):

| Picks | Real calendar | Shifted calendars (chance) | Shifted calendars as high |
|---|---|---|---|
| Hot, Straight | −0.68 | +0.11 | 4 of 4 |
| Hot, Reverse | −0.16 | −0.13 | 1 of 4 |
| Hot, i-Box | +1.03 | −0.26 | 0 of 4 |
| Cold, Straight | +0.68 | +0.56 | 1 of 4 |
| Cold, Reverse | −1.41 | −0.70 | 4 of 4 |
| Cold, i-Box | −0.48 | −0.36 | 2 of 4 |

Only Hot i-Box beat all 4 shifted calendars. That's 1 of 6 combinations, with just 4 calendars to compare against, so it isn't real evidence.

**All three methods, every test:**

| Test | Mei Hua Yi Shu | Da Liu Ren | Tai Yi day cycles |
|---|---|---|---|
| Direct number test | ×0.998 | ×1.0008 | – |
| A. Digit mix for each value | at chance (below zero) | at chance (below zero) | at chance (below zero) |
| B. Same number coming back | within chance | within chance | within chance |
| C. Digit-position picks | at chance | at chance | at chance |
| D. Whole-number hot / cold | at chance | at chance | at chance |

- **The direct number test** checks whether each method's numbers turn up as winning digits more often than chance. Neither Mei Hua's trigram and moving-line numbers nor Da Liu Ren's transmission branch numbers do.
- **Tai Yi** wasn't part of that test, because its host and guest counts weren't computed.
- **In the scans,** no single test stood out beyond what chance produces.
- **These methods take the same building blocks as before** (day pillar, lunar date, solar term, hour) and combine them in their own ways. None of those combinations predicts the results.

The scripts, results and findings are committed and pushed.

---

## 69. Question (2026-10-22 07:24)

> Show me the leads from Mei Hua and Da Liu Ren and their performance from the last 3 draws

**Answer** (2026-10-22 07:26)

I'll find the best Mei Hua and Da Liu Ren tests from the digit-position scan, choosing them fairly on draws before 2012, then rebuild their picks for 17, 18 and 21 Oct and score them.

Here are the 3 best Mei Hua and Da Liu Ren leads and how they did over the last 3 draws. Each was the top test in its picks combination on 1985–2011 draws, and I kept the 3 per method that did best on 2012–2026. As a group these methods don't beat chance: the tests chosen fairly before 2012 averaged z −0.07 (Mei Hua) and −0.29 (Da Liu Ren) after 2012.

Each lead is 16 numbers bet on all 3 operators, so RM48 per draw and RM144 over the 3 draws.

**Mei Hua Yi Shu leads**

| Lead | 2012–2026 | 17 Oct | 18 Oct | 21 Oct | Straight won | i-Box (approx.) |
|---|---|---|---|---|---|---|
| 1. Body/use × Month stem, 2nd + 9th digits (b), Reverse | ×1.11 | 3 i-Box | 1 i-Box (4937 Toto 3rd) | **9821 Magnum Special** | RM180 | 6 matches, ~RM48 |
| 2. Upper trigram × KP Asc star lord, 1st + 10th digits (a), Straight | ×1.11 | 0 | 0 | **1134 Magnum Special**; i-Box 4831 Toto 2nd | RM180 | 3 matches, ~RM62 |
| 3. Upper trigram × Moving line, 4th + 7th digits (a), i-Box | ×1.02 | **8790 Toto Special** | 3 i-Box | **8667 DMC Consolation** | RM240 | 6 matches, ~RM53 |

**Da Liu Ren leads**

| Lead | 2012–2026 | 17 Oct | 18 Oct | 21 Oct | Straight won | i-Box (approx.) |
|---|---|---|---|---|---|---|
| 1. Transmission method × Mars nakshatra, S1 (a), Reverse | ×1.09 | **9574 Magnum Special**; i-Box 7652 DMC 3rd | 0 | 4 i-Box | RM180 | 7 matches, ~RM51 |
| 2. General on first transmission × Month stem, S1 (b), i-Box | ×1.02 | 1 i-Box | 2 i-Box (0127 Magnum 3rd) | 0 | RM0 | 3 matches, ~RM31 |
| 3. Lesson pattern × 7 pm hour stem, S1 (a), Straight | ×1.07 | 1 i-Box | 2 i-Box | 7 i-Box, incl. **5195 → 5915 Toto 1st** | RM0 | 10 matches, ~RM276 |

**Tonight's numbers for these leads** were rebuilt from results up to 18 Oct. Bold numbers won.
- **Mei Hua 1:** 2104 2101 2124 2121 2804 2801 2824 2821 9104 9101 9124 9121 9804 9801 9824 **9821**
- **Mei Hua 2:** 1834 1833 1814 1813 **1134** 1133 1114 1113 2834 2833 2814 2813 2134 2133 2114 2113
- **Da Liu Ren 3:** 5898 5895 5878 5875 5198 **5195** 5178 5175 0898 0895 0878 0875 0198 0195 0178 0175. As i-Box, 5195 matches Toto's 1st prize 5915.

**How to read this:**
- **Straight:** the 6 leads won 6 Straight prizes over the 3 draws, all Specials or Consolations, RM60 to RM240 per lead on RM144. That's about what chance gives: around 0.11 hits per lead per draw, so about 2 expected across all of them.
- **i-Box:** Da Liu Ren 3 came out ahead (~RM276 on RM144) because one number matched Toto's 1st prize. A single lucky match like that is how i-Box results usually swing.
- **None of these were logged before the draws.** The picks use only earlier results, but I built them today, and the "best 3" ranking used 2012–2026 data, which includes these draws. So treat this as a look back, not a clean live test.

If you want a fair test, I can log these 6 leads' picks before Saturday's draw (24 Oct) together with the main leads. The script is `analysis/mh_lr_leads.py`, committed and pushed.

---

## 70. Question (2026-10-22 08:19)

> day_of_month × aspect_venus_jupiter 
> sun_sign_tropical × aspect_moon_saturn 
> year_stem × lagna_navamsa_lord 
> nayin_element × plum_trigrams 
> aspect_mars_jupiter × rahu_d27 
> moon_rashi × aspects_hard 
> plum_trigrams × saturn_navamsa 
> mercury_nakshatra × saturn_combust 
> lunar_month × sun_sign_tropical 
> pof_rashi × aspect_venus_jupiter 
> nakshatra × sun_sign_tropical 
> kp_asc_star_lord × year_pillar 
> pof_sign × moon_d27_lord 
> lagna_rashi × saturn_retrograde 
> day_pillar × aspect_jupiter_saturn 
> sun_sign_tropical × aspect_moon_saturn 
> mars_combust × aspect_jupiter_saturn 
> day_element × aspect_moon_jupiter 
> saturn_retrograde × nayin 
> aspect_moon_mars × aspect_mercury_mars 
> ayana × lunar_leap_month 
> saturn_d24 
> moon_phase × lagna_d24 
> saturn_retrograde × aspect_mercury_jupiter 
> aspect_venus_jupiter × sun_navamsa 
> day_element × aspect_moon_jupiter 
> moon_sign_tropical × sun_navamsa 
> saturn_rashi × kp_asc_star_lord 
> mercury_combust × aspects_soft 
> paksha × venus_rashi 
> mars_combust × aspect_moon_mercury 
> venus_retrograde × venus_d30 
> lagna_navamsa_lord × vargottama_count 
> day_vs_year_branch × jupiter_d7 
> aspect_sun_mars × aspect_moon_venus 
> aspect_venus_jupiter × universal_day 
> rahu_rashi × vargottama_d10_count 
> samvatsara × vargottama_d24_count 
> kp_sun_star_lord × day_stem 
> kp_sun_number × lagna_d7 
> rahu_nakshatra × kp_asc_sub_lord 
> sun_rashi × nayin_element 
> hour_stem_19h × sun_sign_tropical 
> masa × day_god 
> paksha × venus_rashi 
> karana × masa 
> hora_lord × mars_combust 
> mercury_nakshatra × saturn_combust 
> hora_lord × mars_retrograde 
> mercury_rashi × kp_asc_sub_lord 
> masa × adhika_masa 
> mercury_nakshatra × aspects_soft 
> ayana × kp_moon_star_lord 
> lagna_rashi × day_officer 
> mercury_rashi × kp_asc_sub_lord 
> hora_lord × adhika_masa 
> month_branch × aspect_venus_jupiter 
> nakshatra × nayin 
> hora_lord × mars_combust 
> lagna_nakshatra × rahu_navamsa 
> sun_rashi × planets_with_moon 
> karana × aspect_venus_mars 
> saturn_combust × plum_trigrams 
> mars_retrograde × moon_phase 
> aspect_mars_saturn × mars_navamsa 
> lagna_rashi × lunar_day 
> mercury_rashi × day_branch 
> day_element × lagna_navamsa_lord 
> month_branch × aspects_soft 
> sun_nakshatra × lunar_month 
> kp_sun_sub_lord × year_yinyang 
> kp_moon_number × nayin_element 
> mars_rashi × month 
> month_stem × kp_ruling_planets 
> kp_sun_star_lord × month_pillar 
> Check the performance of this and tell me if they are better

**Answer** (2026-10-22 08:20)

Many of these parameters aren't ones I've built, such as Part of Fortune, aspect counts, tropical signs and vargottama counts. There's an `Astro` folder next to this repo, so I'll check whether that's where this list and its definitions come from.

Your list isn't better than our leads, and overall it's only slightly better than random formulas. I tested 69 distinct formulas: your 75 lines include some repeats, such as Paksha × Venus rashi twice.

**How I tested it:** your list doesn't say which picking method goes with each formula. So for each one I chose its best digit-position method using 1985–2011 draws only (S1, S2 or a rank pair; version a or b; Straight, Reverse or i-Box), then scored that method on 2012–2026. I did the same for 500 random pairs drawn from the same 265 parameters, to show what chance looks like.

**2012–2026 results** (z; 0 means chance):

| | Your list (69) | 500 random pairs |
|---|---|---|
| Average z with the method chosen before 2012 | −0.21 | −0.42 |
| Above chance | 29 of 69 (42%) | 35% |
| z > 2 | 1 | 2% (about 1.4 expected in 69) |
| Average over all 42 methods (no method choice) | −0.02 | −0.03 |

- **With the method chosen before 2012, your list is a little ahead of random:** only 5% of random sets of 69 did as well.
- **With all methods averaged, it's exactly the same as random.** So the formulas themselves carry no information.
- **Which period was used to find them matters.** If whoever made this list found these formulas using data that included 2012–2026, that alone would explain a small advantage, and I can't verify it. If you know how they were found, I can test them on draws that weren't used.

**Best formulas on 2012–2026:**

| Formula | Method chosen before 2012 | 2012–2026 |
|---|---|---|
| Rahu rashi × D10 vargottama count | 5+6 (a), i-Box | ×1.038, z +2.55 |
| KP Sun star lord × Day stem | S2 (b), i-Box | ×1.028, z +1.92 |
| Day element × Lagna navamsa lord | 4+7 (b), Reverse | ×1.095, z +1.57 |
| Saturn retrograde × Nayin | 4+7 (b), Reverse | ×1.092, z +1.51 |

**Compared with our leads:**
- **Karana × Day pillar:** ×1.04 and z +2.67 after 2012, above chance in 14 of 15 years, and none of 50 shifted calendars matched it.
- **KP Moon number × Year element:** ×1.16 after 2012.

Your best, Rahu rashi × D10 vargottama count at z +2.55, is about the size you'd expect for the best of 69 random tries. It isn't stronger than our top lead.

**Last 3 draws (17, 18 and 21 Oct),** with each formula's picks rebuilt from earlier results only:

| | Your list |
|---|---|
| Total staked | RM9,936 (69 formulas × 16 numbers × 3 operators × 3 draws) |
| Straight hits | 19, against about 23 expected by chance |
| Straight won | RM4,240 |
| i-Box matches | 414, ~RM7,590 |

Best individual results over the 3 draws:
- **Hora lord × Mars retrograde:** a 2nd prize, RM1,000
- **Saturn retrograde × Nayin, Saturn rashi × KP Asc star lord, KP Asc star lord × Year pillar:** a 3rd prize each, RM500

Overall the list got slightly fewer Straight hits than chance would give, so it isn't doing better on recent draws either.

The script, list and results are committed and pushed (`analysis/formula_list_test.py`). If you know which picking method each formula is supposed to use, send it and I'll test exactly that instead of choosing one.

---

## 71. Question (2026-10-22 08:31)

> Show me the performance of all this leads in table for the last 5 draws

**Answer** (2026-10-22 08:31)

I'll rerun the formula list on the last 5 draws (11, 14, 17, 18 and 21 Oct), keeping the result for each draw separately.

Over the last 5 draws (11, 14, 17, 18 and 21 Oct), your 69 formulas got 24 Straight hits worth RM5,720 on RM16,560 staked. Chance would give about 38 hits, so the list did slightly worse than random numbers.

Each formula used the picking method chosen for it on 1985–2011 draws, and its picks were rebuilt before every draw from earlier results only. Stakes are RM1 Big on 16 numbers with each of the 3 operators, so RM48 per draw and RM240 per formula over the 5 draws.

**The 19 formulas with Straight hits:**

| # | Formula | Method | 2012–26 | 11 Oct | 14 Oct | 17 Oct | 18 Oct | 21 Oct | Straight RM |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Hora lord × Mars retrograde | 4+7 (a) Reverse | ×1.027 | – | – | – | **1240 DMC 2nd** | – | 1,000 |
| 2 | Mars retrograde × Moon phase | S1 (a) Reverse | ×0.964 | **4847 DMC 2nd** | – | – | – | – | 1,000 |
| 3 | Saturn retrograde × Nayin | 4+7 (b) Reverse | ×1.092 | – | – | **7652 DMC 3rd** | – | – | 500 |
| 4 | Saturn rashi × KP Asc star lord | S2 (b) Reverse | ×1.038 | – | – | **5541 Magnum 3rd** | – | – | 500 |
| 5 | KP Asc star lord × Year pillar | S2 (b) Reverse | ×1.015 | – | – | **5541 Magnum 3rd** | – | – | 500 |
| 6 | Plum trigrams × Saturn navamsa | S2 (b) Reverse | ×0.889 | – | – | 6040 Magnum Spec | – | 7901 Magnum Spec | 360 |
| 7 | Saturn combust × Plum trigrams | 5+6 (a) i-Box | ×1.018 | 0513 Magnum Cons | – | – | 3853 Toto Spec | – | 240 |
| 8 | Mercury rashi × KP Asc sub lord | 5+6 (b) Reverse | ×0.976 | – | – | – | 5304 Toto Cons | 9821 Magnum Spec | 240 |
| 9 | Sun rashi × Planets with Moon | S2 (a) i-Box | ×0.989 | – | 8649 Toto Cons | – | – | 2252 DMC Spec | 240 |
| 10 | Sun sign (tropical) × Moon–Saturn aspect | 1+10 (a) Straight | ×1.083 | – | – | – | 3665 DMC Spec | – | 180 |
| 11 | Day of month × Venus–Jupiter aspect | 5+6 (b) Straight | ×1.004 | – | 7150 DMC Spec | – | – | – | 180 |
| 12 | Day vs Year branch × Jupiter D7 | 2+9 (b) Reverse | ×0.988 | – | – | – | – | 9821 Magnum Spec | 180 |
| 13 | Moon–Mars × Mercury–Mars aspect | 2+9 (b) Reverse | ×0.924 | – | 1710 DMC Spec | – | – | – | 180 |
| 14 | Mars combust × Moon–Mercury aspect | 4+7 (a) Reverse | ×1.015 | – | – | 8033 Magnum Cons | – | 2338 Magnum Cons | 120 |
| 15 | Sun rashi × Nayin element | 5+6 (b) Straight | ×1.062 | – | – | 8426 Toto Cons | – | – | 60 |
| 16 | Moon rashi × Hard aspects | 2+9 (b) Reverse | ×1.046 | – | – | 0431 Toto Cons | – | – | 60 |
| 17 | Mars–Saturn aspect × Mars navamsa | 4+7 (b) i-Box | ×1.008 | – | – | – | – | 2338 Magnum Cons | 60 |
| 18 | Samvatsara × D24 vargottama count | 5+6 (b) Straight | ×1.008 | – | – | – | 5304 Toto Cons | – | 60 |
| 19 | Year stem × Lagna navamsa lord | 2+9 (b) Reverse | ×0.953 | – | – | – | – | 2338 Magnum Cons | 60 |

**The other 50 formulas had no Straight hits** in these 5 draws. That includes your two best on 2012–2026, Rahu rashi × D10 vargottama count (×1.038) and KP Sun star lord × Day stem (×1.028). Each formula still had 2 to 18 i-Box matches, worth about RM18 to RM434 per formula over the 5 draws.

**Totals by draw:**

| Draw | Straight hits | Straight RM |
|---|---|---|
| 11 Oct | 2 | 1,060 |
| 14 Oct | 3 | 420 |
| 17 Oct | 7 | 1,860 |
| 18 Oct | 5 | 1,480 |
| 21 Oct | 7 | 900 |
| **All 5** | **24** (about 38 expected by chance) | **5,720** on RM16,560 staked |

- Straight returned **35% of stakes** and i-Box about 68% (~RM11,300 over 673 matches). Both are below the usual payout share for random numbers, which is about 64%.
- **The biggest wins** were two 2nd prizes (RM1,000 each) and three 3rd prizes (RM500 each). They came from formulas that are near or below chance on 2012–2026, so they're luck, not signal.

In short, this list doesn't beat chance or our own leads. The full table, with i-Box detail for all 69 formulas, is in `analysis/formula_list_last5.md`, committed and pushed.

---

## 72. Question (2026-10-22 08:38)

> what about ibox? show me the table for that

**Answer** (2026-10-22 08:38)

I'll rebuild each formula's i-Box picks for the 5 draws, using the same method as before, so the table can show the actual i-Box matches including any top-3 prizes.

Bet as i-Box, the list returned about RM11,325 on RM16,560 over the last 5 draws, or 68% of stakes. That's close to the roughly 64% random numbers return. Of the 69 formulas, 12 came out ahead (over RM240 on RM240 staked), and the other 57 lost.

Each formula's 16 numbers were bet RM1 i-Box on all 3 operators, so RM48 per draw and RM240 over the 5 draws. A cell shows matches (~RM won). The i-Box payout is approximate: the Big prize divided by the number of arrangements, so about RM104 for a 1st-prize match with 4 different digits.

**The 12 formulas that came out ahead:**

| # | Formula | Method | 11 Oct | 14 Oct | 17 Oct | 18 Oct | 21 Oct | ~RM on RM240 | Top-3 prize matches |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Sun–Mars × Moon–Venus aspect | S2 (a) i-Box | 6 (129) | 1 (208) | 2 (5) | 2 (45) | 3 (47) | **434** | DMC 1st ×2 (7952, 6906), Magnum 2nd 6537 |
| 2 | Samvatsara × D24 vargottama count | 5+6 (b) Straight | 2 (83) | 1 (8) | 2 (107) | 7 (42) | 6 (139) | **379** | Toto 1st 1508, Magnum 1st 8450, Toto 2nd 2149 ×2 |
| 3 | Mars retrograde × Moon phase | S1 (a) Reverse | 2 (167) | 2 (10) | 2 (15) | 1 (5) | 4 (168) | **365** | DMC 2nd 4847 ×2, Magnum 1st 8450, Toto 2nd 4831 |
| 4 | Saturn combust × Plum trigrams | 5+6 (a) i-Box | 4 (52) | 6 (128) | 3 (38) | 1 (15) | 4 (129) | **362** | Magnum 2nd ×3 (5321, 3175), Magnum 1st 8450 |
| 5 | Mars–Saturn aspect × Mars navamsa | 4+7 (b) i-Box | 2 (30) | 3 (88) | 4 (114) | 3 (98) | 3 (28) | **358** | Toto 1st 1508, Toto 2nd 6640, DMC 3rd 6516 ×2 |
| 6 | Masa × Day god | 4+7 (b) i-Box | 2 (47) | 1 (8) | 2 (12) | 4 (223) | 3 (20) | 310 | DMC 1st 2454, DMC 3rd 9772 |
| 7 | KP Sun sub lord × Year yin-yang | 1+10 (b) Straight | 3 (57) | 1 (208) | 2 (22) | 2 (15) | 0 | 302 | DMC 1st 6906, Toto 3rd 3561 ×2 |
| 8 | Month stem × KP ruling planets | S2 (b) Reverse | 4 (148) | 0 | 2 (22) | 1 (8) | 3 (125) | 302 | Magnum 1st 6319, Magnum 2nd 6537, 3rd ×3 |
| 9 | Day element × Moon–Jupiter aspect | 4+7 (b) Straight | 3 (18) | 3 (91) | 3 (12) | 3 (98) | 2 (83) | 302 | Magnum 2nd 6537 ×2, Toto 2nd ×2 |
| 10 | Karana × Venus–Mars aspect | S2 (b) i-Box | 2 (20) | 3 (25) | 1 (8) | 4 (226) | 1 (8) | 286 | Toto 1st 3166 |
| 11 | Day element × Lagna navamsa lord | 4+7 (b) Reverse | 4 (69) | 3 (91) | 0 | 3 (98) | 2 (15) | 273 | 2nd prizes ×3 |
| 12 | Paksha × Venus rashi | 2+9 (b) Reverse | 4 (127) | 1 (8) | 2 (119) | 1 (15) | 1 (2) | 271 | Magnum 1st 6319, 1294 |

**Bottom of the list:** the weakest returned RM18 to RM70, for example Hour stem × Tropical Sun sign (RM18) and KP Sun star lord × Day stem (RM52). Your two best formulas on 2012–2026 were among those losing: Rahu rashi × D10 vargottama count returned RM75 and KP Sun star lord × Day stem RM52.

**By draw:**

| Draw | i-Box matches (all 69) |
|---|---|
| 11 Oct | 162 |
| 14 Oct | 97 |
| 17 Oct | 155 |
| 18 Oct | 132 |
| 21 Oct | 127 |
| **Total** | **673**, ~RM11,325 on RM16,560 (68%) |

**Notes:**
- **i-Box wins depend almost entirely on landing a top-3 prize match.** Every formula above RM240 got there through one or two 1st or 2nd prize matches, worth RM40–RM208 each. Special and Consolation matches pay only about RM2.50–RM7.50.
- **Ten of the formulas gave identical picks on 17 Oct.** These are the ones using 2+9 (b) Reverse, such as Lunar month × Tropical Sun sign and Masa × Adhika masa. They all matched 1294, Magnum's 1st prize, so that one match is counted ten times. The list has fewer independent picks than it looks.
- **Overall:** 68% back is in line with chance, and the profitable formulas aren't the ones that tested best on 2012–2026. So the i-Box results don't single out any formula either.

The full 69-row i-Box table is in `analysis/formula_list_last5_ibox.md`, committed and pushed.

---

## 73. Question (2026-10-22 08:47)

> OK now, do note that, fo all the leads that we have so far, you combined mag, toto, damacai and did the analysis. now i want you to redo all the analysis again, while separating them to see if there are leads that performs well in certain races, do every analysis that we have done before on singles and pairs

**Answer** (2026-10-22 08:47)

I'll check which per-row fields the data loader keeps, so each analysis can be restricted to one operator's winning numbers.

The per-operator analysis is running in the background, one operator after another: Magnum, then Sports Toto, then Da Ma Cai. The full run should take about 3 hours. The script (`analysis/per_operator.py`) is committed and pushed.

Each operator gets the same suite as before, on all 78 single parameters and 3,003 pairs:

| | Analysis |
|---|---|
| A | digit mix for each value, learned on 1985–2011 and tested on 2012–2026 |
| B | the same number coming back (Straight, Reverse, i-Box; any later day and next day) |
| C | digit-position picks: S1, S2, S3 and rank pairs 2+9 to 5+6; versions (a) and (b); Straight, Reverse and i-Box; with the walk-forward check |
| D | whole-number hot and cold, with the walk-forward check |

The difference from before is that each operator's picks are built only from that operator's own past winning numbers. They are scored only against that operator's results, and the chance level uses its own digit mix each year. So a lead that only works for Magnum, say, would now show up instead of being averaged out.

**One fix needed first:** Sports Toto and Da Ma Cai start in 1992, so their 1985–1991 digit mix was empty and would have broken the expected counts. I fixed that before starting the run.

When it finishes I'll give you a side-by-side table for the three operators. It will show which combinations stand out from chance, and the best leads each operator has that hold up after 2012.

While the other two run, here are the Magnum results:

Magnum is finished. It shows a slightly stronger result than the pooled analysis, but the effects are small. Sports Toto and Da Ma Cai are still running, about 2.5 to 3 hours more.

**Magnum on its own (3,081 tests):**

| Analysis | Real calendar | Shifted calendars (chance) | Verdict |
|---|---|---|---|
| A. Digit mix: tests above zero | 42 | 12.5 | above chance |
| A. Best single parameter | **Weekday** +0.032 | best +0.013 (0 of 6 as high) | above chance, very small |
| B. Same number coming back | best z +4.14 (Venus rashi × KP Sun number, next day, ×1.25) | best +3.17 (0 of 6) | one outlier, mostly chance |
| C. Average forward z after 2012 | +0.095 | −0.037 | slightly above |
| C. Combinations beating every shifted calendar | 10 of 42 | about 6 | slightly above |
| D. Whole-number hot / cold | mixed | – | chance |

- **The weekday result is the first parameter-type signal so far that beats every shifted calendar.** Magnum's digit mix seems to differ a little between Wednesday, Saturday and Sunday draws. That fits the Magnum digit bias found earlier for 2019–2025, which could come from different draw sessions or equipment. But the size is tiny, about 0.03 thousandths of a unit of information per digit, far too small to win money.
- **Best Magnum picks chosen before 2012** (S1, S2 and rank pairs), with their results after 2012:

| Pick | Method | After 2012 |
|---|---|---|
| Hour stem at 7 pm | 4th + 7th digits (a), Straight | ×1.18 (z +1.73) |
| KP Ascendant number × Nine star year | 2nd + 9th digits (b), Straight | ×1.15 (z +1.44) |
| KP Moon number × Day officer | 4th + 7th digits (b), Straight | ×1.14 (z +1.23) |

The Magnum results are committed. I'll send the three-operator comparison and the best lead for each operator when Sports Toto and Da Ma Cai finish.

The progress watcher timed out again, but the analysis itself kept running.

- **Done:** Magnum and Sports Toto, both committed and pushed.
- **Still running:** Da Ma Cai, on its last part (whole-number hot and cold), about 25 minutes left.

I've set a new watcher and will send the comparison of all three operators when Da Ma Cai finishes.

Separating the three operators didn't uncover a usable lead. Magnum shows slightly more than chance, but the effects are far too small to bet on. Sports Toto and Da Ma Cai are at chance.

Each operator's picks were built only from its own past winning numbers and scored only on its own results, across all 78 single parameters and 3,003 pairs.

**Side by side:**

| Analysis | Magnum | Sports Toto | Da Ma Cai |
|---|---|---|---|
| **A. Digit mix:** tests above zero, real vs chance | **42 vs 12.5** | 32 vs 24 | **52 vs 16** |
| A. Best test, real vs best by chance | **Weekday +0.032 vs +0.013** (no shifted calendar as high) | +0.013 vs +0.009 | +0.013 vs +0.009 |
| **B. Same number coming back:** best z, real vs chance | +4.14 vs +3.17 | +3.83 vs +3.32 | +4.03 vs +3.58 |
| **C. Digit-position picks:** forward z after 2012, real vs chance | **+0.10 vs −0.04** | −0.00 vs −0.06 | +0.05 vs +0.06 |
| C. Combinations beating every shifted calendar (about 6 expected by chance) | **10 of 42** | 4 of 42 | 7 of 42 |
| **D. Whole-number hot / cold** | chance | chance | chance |

- **A. Digit mix:** for Magnum and Da Ma Cai, more tests score above zero than chance gives. Only Magnum has a single parameter that beats every shifted calendar, and that's Weekday: Magnum's digits differ a little between Wednesday, Saturday and Sunday draws. All these gains are a few hundredths of a thousandth of a unit of information per digit, far too small to win money.
- **B. Same number coming back:** each operator has one or two tests beyond the shifted-calendar range, about what chance gives across 6 tests per operator. Examples: for Magnum, Venus rashi × KP Sun number on the next same-value day (×1.25); for Sports Toto, Mercury rashi × Lunar day (×1.25); for Da Ma Cai, Mercury nakshatra × KP Moon sub lord (×1.25). Each is a single test out of thousands, not a pattern.
- **C. Digit-position picks:** Magnum is the only operator a little above chance overall.
- **D. Whole-number hot and cold:** no operator beat chance.

**Best picks for each operator,** chosen on 1985–2011 and checked on 2012–2026:

| Operator | Formula | Method | After 2012 |
|---|---|---|---|
| Magnum | Hour stem at 7 pm | 4+7 (a), Straight | ×1.18 (z +1.73) |
| Magnum | KP Ascendant number × Nine star year | 2+9 (b), Straight | ×1.15 (z +1.44) |
| Magnum | KP Moon number × Day officer | 4+7 (b), Straight | ×1.14 (z +1.23) |
| Sports Toto | Mercury rashi × Moon navamsa | 3+8 (b), i-Box | ×1.05 (z +2.00) |
| Sports Toto | Mercury combust × KP Moon star lord | 4+7 (b), Reverse | ×1.13 (z +1.21) |
| Da Ma Cai | KP Moon sub lord × Nine star month | 5+6 (a), Straight | ×1.16 (z +1.53) |
| Da Ma Cai | Month branch × Hour stem at 7 pm | 1+10 (a), Reverse | ×1.14 (z +1.31) |

None of these is stronger than our pooled lead, Karana × Day pillar, at z +2.67 after 2012 with 14 of 15 good years. And on one operator, 16 numbers win only about once every 27 draws by chance, so a ×1.15 edge still means very few hits.

**Conclusion:** splitting by operator hints that Magnum's draws aren't quite as random as the others; the digit-bias finding from 2019–2025 also fits that. But no operator has a parameter-based lead strong enough to make money.

All three result files and the summary in `FINDINGS.md` are committed and pushed. I can log the best per-operator picks for Saturday's draw if you'd like to test them live.

---

## 74. Question (2026-10-22 13:52)

> show me their performance for the last 5 draws

**Answer** (2026-10-22 13:52)

I'll rebuild each operator's leads from that operator's results only, before each of the last 5 draws (11, 14, 17, 18 and 21 Oct), and score them on that operator's draw as Straight and i-Box.

Over the last 5 draws (11, 14, 17, 18 and 21 Oct), the 7 per-operator leads won RM540 on Straight and about RM252 on i-Box, against RM544 staked. That's about break-even on Straight, from just 3 Special prizes, and i-Box returned under half.

Each lead's 16 numbers were rebuilt before every draw from that operator's own earlier results, and bet RM1 each on that operator only: RM16 per draw, RM80 over 5 draws. A dash means no match, and "iB" means i-Box matches.

| Operator | Lead | Method | 11 Oct | 14 Oct | 17 Oct | 18 Oct | 21 Oct | Straight won | i-Box (approx.) |
|---|---|---|---|---|---|---|---|---|---|
| Magnum | Hour stem 7 pm | 4+7 (a) Straight | – | – | 1 iB | – | 1 iB | RM0 | 2, ~RM15 |
| Magnum | KP Asc number × Nine star year | 2+9 (b) Straight | 1 iB | – | **2321 Special** | 1 iB | 1 iB | **RM180** | 4, ~RM33 |
| Magnum | KP Moon number × Day officer | 4+7 (b) Straight | – | – | – | 1 iB | no picks | RM0 (RM64 staked) | 1, ~RM8 |
| Sports Toto | Mercury rashi × Moon navamsa | 3+8 (b) i-Box | 2 iB (incl. 3561 **3rd**) | – | **6693 Special** | – | – | **RM180** | 3, ~RM43 |
| Sports Toto | Mercury combust × KP Moon star lord | 4+7 (b) Reverse | 2 iB (incl. 3561 **3rd**) | – | – | 2 iB | 1 iB | RM0 | 5, ~RM48 |
| Da Ma Cai | KP Moon sub lord × Nine star month | 5+6 (a) Straight | – | 1 iB | 1 iB | – | – | RM0 | 2, ~RM8 |
| Da Ma Cai | Month branch × Hour stem 7 pm | 1+10 (a) Reverse | 2 iB | 1 iB (2888 Special) | – | 2 iB | 2 iB | RM0 | 7, ~RM98 |

**Totals by operator:**

| Operator | Staked | Straight hits | Straight won | i-Box matches | i-Box won (approx.) |
|---|---|---|---|---|---|
| Magnum (3 leads) | RM224 | 1 | RM180 | 7 | ~RM55 |
| Sports Toto (2 leads) | RM160 | 1 | RM180 | 8 | ~RM92 |
| Da Ma Cai (2 leads) | RM160 | 0 | RM0 | 9 | ~RM105 |
| **All 7** | **RM544** | **2** | **RM360** | **24** | **~RM252** |

**Correction to my opening line:** the Straight total is RM360, not RM540, which is 66% of stakes rather than break-even. Over these 5 draws the 7 leads together:
- **Straight:** won RM360 on RM544 staked (66%), from 2 Special prizes.
- **i-Box:** won about RM252 on RM544 (46%).

**What to make of it:**
- **Two Straight hits in 34 lead-draws is close to chance.** With 16 numbers on one operator, chance gives about 0.037 hits per draw, so about 1.3 expected; there were 2.
- **The best per-lead results came from single Special prizes:** KP Asc number × Nine star year on Magnum (2321) and Mercury rashi × Moon navamsa on Sports Toto (6693), each RM180 on RM80 staked.
- **The near-misses:** both Sports Toto leads had an arrangement of 3561, Toto's 3rd prize on 11 Oct. They'd have paid only as i-Box.
- **Overall:** the per-operator leads perform about like random picks over these 5 draws, which matches the scan results.

The script (`analysis/per_operator_leads.py`) is committed and pushed. I can log these 7 leads' picks before Saturday's draw on 24 Oct, with the other leads, so they get a clean live test.

---

## 75. Question (2026-10-22 13:56)

> so compare how per oeprator and pooled perform

**Answer** (2026-10-22 13:56)

I'll score the pooled leads on the same 5 draws so the two can be compared directly. Stakes differ: pooled leads bet 16 numbers on all 3 operators (RM48 per draw), per-operator leads on one operator (RM16 per draw). So I'll compare return as a percentage of stake.

Neither approach beats chance in a way you could profit from. The pooled leads look better over the last 5 draws, but that comes from two lucky big prizes, not a reliable edge.

**Over the last 5 draws (11–21 Oct),** with picks rebuilt before every draw:

| | Pooled leads (16 numbers × all 3 operators) | Per-operator leads (16 numbers × 1 operator) |
|---|---|---|
| Leads | 9 | 7 |
| Staked | RM1,968 | RM544 |
| Straight hits | 8 (about 4.5 expected) | 2 (about 1.3 expected) |
| Straight won | RM4,100 (**208%** of stake) | RM360 (**66%**) |
| Straight without the one 1st prize (3872, Magnum 14 Oct) | RM1,600 (**81%**) | – |
| i-Box won (approx.) | ~RM1,099 (**56%**) | ~RM252 (**46%**) |
| Biggest wins | 3872 Magnum 1st (RM2,500, S2 Mars triple); 6537 Magnum 2nd (RM1,000, Mercury nakshatra × Venus rashi) | 2321 Magnum Special; 6693 Toto Special (RM180 each) |

- **Straight:** the pooled leads got about twice the hits chance gives (8 vs 4.5), and two of them were top prizes. Without the single 1st prize their return drops from 208% to 81%. That's the normal swing of a lottery over 5 draws.
- **i-Box:** both approaches returned about half their stake, a little below the roughly 64% random numbers would return.

**Over the long run (chosen on 1985–2011, tested on 2012–2026):**

| | Pooled | Per operator |
|---|---|---|
| Whole scan vs chance (average forward z, real vs shifted) | at chance for S1/S2, S3 and rank pairs | Magnum +0.10 vs −0.04; Sports Toto −0.00 vs −0.06; Da Ma Cai +0.05 vs +0.06 |
| Combinations beating every shifted calendar | about what chance gives (e.g. 3 of 30 vs 2.7) | Magnum 10 of 42 (about 6 expected); Sports Toto 4; Da Ma Cai 7 |
| Best leads after 2012 | ×1.03 to ×1.16 | ×1.05 to ×1.18 |
| Most consistent lead | Karana × Day pillar: 14 of 15 years above chance, no shifted calendar matched it | none tested for year-by-year consistency |
| Expected hits per draw (16 numbers) | about 0.11 | about 0.037 |

- **Edge size:** the best leads are about the same in both approaches, roughly 5–18% more hits than chance.
- **Pooled gives clearer evidence.** It counts three times as many winning numbers, so each estimate is steadier. That's how Karana × Day pillar could be confirmed year by year.
- **Per-operator shows something only for Magnum,** which leans slightly above chance. That matches its Wednesday/weekend digit differences and the earlier 2019–2025 Magnum bias, but the effect is too small to use.
- **Per-operator picks hit rarely:** about once every 27 draws by chance. Five draws can't tell those leads apart.

**Bottom line:** neither approach is better in a way you could profit from. The pooled leads look much better over these 5 draws only because of the 3872 1st prize and the 6537 2nd prize. If you keep testing live, pooled leads give more hits to judge them by. Per operator, only Magnum is worth tracking.

---

## 76. Question (2026-10-22 13:59)

> none tested for year-by-year consistency why is this not done? please do this analysis

**Answer** (2026-10-22 13:59)

That's a fair point. The year-by-year check was only run on the pooled leads, because those were the ones I was comparing at the time. I'll run the same check for each operator, and redo it for pooled under the identical procedure so the two can be compared directly:

1. **Candidates:** every forward pick chosen on 1985–2011 data alone. That's the top 5 tests in each method combination, about 200 per operator.
2. **Yearly count:** for each candidate, with picks rebuilt before every draw, count how many years in 2012–2026 it was above chance.
3. **Chance level:** the same candidates on shifted calendars show how many good years luck produces.
4. **Best candidates:** the top ones get 50 shifted calendars each, plus a no-parameter version for comparison.

The year-by-year check is running for each operator. Pooled is done, and Magnum, Sports Toto and Da Ma Cai are still running, a few minutes each.

**Pooled results** (210 candidates, all chosen on 1985–2011 data alone; years above chance out of the 15 from 2012 to 2026):

| | Real calendar | 20 shifted calendars (chance) |
|---|---|---|
| Average good years per candidate | 7.34 | 7.26 |
| Candidates with 12+ good years | 2 | 3.25 on average (range 1–6) |
| Best candidate | 14 years | 12.8 on average (range 12–14); 4 of 20 reached 14 |

**Most consistent pooled candidates:**

| Candidate | Good years | 2012–2026 | 50 shifted calendars as high | Same picks without the parameter |
|---|---|---|---|---|
| Karana × Day pillar, S1 (b), i-Box | 14 of 15 | ×1.04 | 0 of 50 | 6 of 15 |
| Mars nakshatra × KP Asc number, 5+6 (b), i-Box | 13 of 15 | ×1.05 | 0 of 50 | 10 of 15 |
| KP Moon number × Year element, 2+9 (b), Straight | 11 of 15 | ×1.16 | 0 of 50 | 7 of 15 |

**Correction to what I told you earlier.** Karana × Day pillar is still the most consistent lead, and on its own no shifted calendar matched it.
- **It's the best of 210 candidates,** though, and in 4 of the 20 shifted calendars at least one candidate also reached 14 good years.
- **That makes luck about a 20% explanation.** I previously estimated about 3%, which didn't fully account for how many candidates were searched.
- **Overall:** the pooled candidates as a group average 7.34 good years, no better than chance (7.26).

So it's a weaker lead than I described. I'll correct `FINDINGS.md` when the operator results come in.

When the run finishes I'll send the same table for Magnum, Sports Toto and Da Ma Cai, and commit everything.

I've committed and pushed the year-by-year check script and the results so far (pooled and Magnum). Sports Toto and Da Ma Cai are still running. When they finish I'll commit their results, correct `FINDINGS.md`, and send the comparison table for all three operators.

The year-by-year check is done for pooled and for each operator, all using the same procedure. As a group, no run is more consistent than chance. Magnum comes closest and has the strongest single candidate.

**How it works:** each run takes the 210 candidates chosen on 1985–2011 data alone. With picks rebuilt before every draw, it counts how many of the 15 years from 2012 to 2026 each candidate was above chance. The same candidates are then run on 20 shifted calendars to show what luck produces.

| Run | Average good years, real vs shifted | Candidates with 12+ good years, real vs shifted | Best candidate (shifted calendars reaching it) |
|---|---|---|---|
| Pooled | 7.34 vs 7.26 | 2 vs 3.3 | 14 years (4 of 20) |
| **Magnum** | 7.45 vs 7.25 | **5 vs 2.5** | 13 years (7 of 20) |
| Sports Toto | 7.25 vs 7.18 | 2 vs 2.7 | 12 years (20 of 20) |
| Da Ma Cai | 7.19 vs 7.16 | 4 vs 2.7 | 12 years (19 of 20) |

**Most consistent candidates:**

| Run | Candidate | Method | Good years | Gain 2012–26 | 50 shifted calendars as high | Without the parameter |
|---|---|---|---|---|---|---|
| Pooled | Karana × Day pillar | S1 (b) i-Box | 14 / 15 | ×1.04 | 0 of 50 | 6 / 15 |
| Pooled | Mars nakshatra × KP Asc number | 5+6 (b) i-Box | 13 / 15 | ×1.05 | 0 of 50 | 10 / 15 |
| **Magnum** | **Jupiter retrograde × KP Asc sub lord** | 4+7 (b) Straight | **13 / 15** | **×1.36** | 0 of 50 | 7 / 15 |
| Magnum | Nakshatra lord × Day stem | 2+9 (b) Reverse | 12 / 15 | ×1.29 | 2 of 50 | 4 / 15 |
| Magnum | Moon rashi × Day god | 1+10 (b) i-Box | 12 / 15 | ×1.06 | 0 of 50 | 9 / 15 |
| Sports Toto | Lunar month × Day element | S2 (b) i-Box | 12 / 15 | ×1.07 | 1 of 50 | 8 / 15 |
| Sports Toto | Mercury rashi × Moon navamsa | 3+8 (b) i-Box | 12 / 15 | ×1.05 | 1 of 50 | 10 / 15 |
| Da Ma Cai | Ayana × KP Asc star lord | 1+10 (a) Reverse | 12 / 15 | ×1.21 | 1 of 50 | 8 / 15 |
| Da Ma Cai | Ritu × Day stem | 5+6 (a) i-Box | 12 / 15 | ×1.05 | 1 of 50 | 8 / 15 |

**What this shows:**
- **No run is more consistent than chance as a whole.** Average good years are equal to the shifted calendars everywhere. The best candidate in each run is within the shifted-calendar range too: 4 to 20 of the 20 calendars produced a candidate as consistent.
- **Magnum stands out a little:** it has twice as many candidates with 12+ good years as chance (5 vs 2.5). That fits Magnum being slightly less random, as the earlier Weekday digit-mix result also suggested.
- **The strongest single candidate is Magnum's Jupiter retrograde × KP Asc sub lord** (4th + 7th digits from the previous same-value day, Straight). It was above chance in 13 of 15 years, and its gain of about 1.36× is far larger than our other leads. Without the parameter, the same picks are ordinary (7 good years). But 7 of 20 shifted calendars produced a Magnum candidate as consistent, so it's still within what luck can produce.
- **Correction:** I said earlier that Karana × Day pillar had about a 3% chance of being luck. Counting properly for the 210 candidates searched, it's about 20%. It remains the most consistent pooled lead, but the evidence is weaker than I described.

If you want to keep testing, the two most worth tracking live are Jupiter retrograde × KP Asc sub lord on Magnum and Karana × Day pillar pooled. I can log their picks before each draw from Saturday 24 Oct. The results and the corrected `FINDINGS.md` are committed and pushed.

---

## 77. Question (2026-10-22 14:06)

> Check how those 2 performed on the last 5 draws

**Answer** (2026-10-22 14:07)

Neither lead had a Straight hit over the last 5 draws (11, 14, 17, 18 and 21 Oct), and both made only small i-Box matches. Each lead's picks were rebuilt before every draw from earlier results only.

**1. Karana × Day pillar, pooled.** 16 numbers on all 3 operators, bet as i-Box: RM48 per draw, RM240 in total.

| Draw | Straight | i-Box matches | i-Box won (approx.) |
|---|---|---|---|
| 11 Oct | 0 | 2 (Magnum Consolation 4601, Toto Special 6514) | RM10 |
| 14 Oct | 0 | 2 (Toto Consolation 4381, 6901) | RM5 |
| 17 Oct | 0 | 2 (Toto Consolation 7819, DMC Consolation 2980) | RM5 |
| 18 Oct | 0 | 5 (Magnum Special 4960, 9569; Toto Special 4950; DMC Special 9406, 5619) | RM45 |
| 21 Oct | 0 | 3 (Magnum Special 4036, Toto Special 4409, **Toto 3rd 4246**) | RM64 |
| **Total** | **0** | **14** | **~RM129 on RM240 (54%)** |

**2. Jupiter retrograde × KP Asc sub lord, Magnum only.** 16 numbers on Magnum, bet as Straight: RM16 per draw, RM80 in total.

| Draw | Picks | Straight | i-Box matches |
|---|---|---|---|
| 11 Oct | 6719 6714 6729 6724 6219 6214 6229 6224 9719 9714 9729 9724 9219 9214 9229 9224 | 0 | 0 |
| 14 Oct | 7302 7309 7322 7329 7902 7909 7922 7929 2302 2309 2322 2329 2902 2909 2922 2929 | 0 | 0 |
| 17 Oct | 0538 0531 0588 0581 0238 0231 0288 0281 7538 7531 7588 7581 7238 7231 7288 7281 | 0 | 1 (7581 → 5871 Consolation) |
| 18 Oct | 5395 5396 5355 5356 5795 5796 5755 5756 4395 4396 4355 4356 4795 4796 4755 4756 | 0 | 0 |
| 21 Oct | 8065 8062 8055 8052 8465 8462 8455 8452 5065 5062 5055 5052 5465 5462 5455 5452 | 0 | 2 (8465 → 4856, 8462 → 8624 Consolation) |
| **Total** | | **RM0 on RM80** | **3 matches, ~RM7.50** |

**How to read this:**
- **Karana × Day pillar** got 14 i-Box matches. Chance gives about 9 over 5 draws (roughly 1.8 per draw), so it's slightly above average, the same small edge (×1.04) it showed in 2012–2026. But i-Box matches are mostly Specials and Consolations, so it returned only about half its stake.
- **Jupiter retrograde × KP Asc sub lord** had no Straight hit, which is normal. With 16 numbers on one operator, even at its 2012–2026 rate of ×1.36 you'd expect only about 0.25 hits in 5 draws, or one hit every 20 or so draws. Five draws can't confirm or rule it out.

Neither lead shows anything unusual in these 5 draws, either good or bad. If you want a proper live test, I can log both leads' picks before every draw from Saturday 24 Oct and keep a running score.

---

## 78. Question (2026-10-22 14:14)

> "Run	Candidate	Method	Good years	Gain 2012–26	50 shifted calendars as high	Without the parameter
> Pooled	Karana × Day pillar	S1 (b) i-Box	14 / 15	×1.04	0 of 50	6 / 15
> Pooled	Mars nakshatra × KP Asc number	5+6 (b) i-Box	13 / 15	×1.05	0 of 50	10 / 15
> Magnum	Jupiter retrograde × KP Asc sub lord	4+7 (b) Straight	13 / 15	×1.36	0 of 50	7 / 15
> Magnum	Nakshatra lord × Day stem	2+9 (b) Reverse	12 / 15	×1.29	2 of 50	4 / 15
> Magnum	Moon rashi × Day god	1+10 (b) i-Box	12 / 15	×1.06	0 of 50	9 / 15
> Sports Toto	Lunar month × Day element	S2 (b) i-Box	12 / 15	×1.07	1 of 50	8 / 15
> Sports Toto	Mercury rashi × Moon navamsa	3+8 (b) i-Box	12 / 15	×1.05	1 of 50	10 / 15
> Da Ma Cai	Ayana × KP Asc star lord	1+10 (a) Reverse	12 / 15	×1.21	1 of 50	8 / 15
> Da Ma Cai	Ritu × Day stem	5+6 (a) i-Box	12 / 15	×1.05	1 of 50	8 / 15" among this do the last 5 draws performance

**Answer** (2026-10-22 14:16)

Over the last 5 draws (11, 14, 17, 18 and 21 Oct), only one of the 9 leads came out ahead: **Ritu × Day stem on Da Ma Cai**. It won about RM213 on RM80 as i-Box, and almost all of that came from one match with DMC's 1st prize on 14 Oct. The other 8 lost money.

Each lead's picks were rebuilt before every draw from earlier results only. Pooled leads bet 16 numbers on all 3 operators (RM48 per draw); operator leads bet 16 numbers on that operator only (RM16 per draw).

**Totals, scored with each lead's own bet type:**

| Run | Candidate | Bet type | Staked | Straight hits | i-Box matches | Won with its own bet type | Return |
|---|---|---|---|---|---|---|---|
| Pooled | Karana × Day pillar | i-Box | RM240 | 0 | 14 | ~RM129 | 54% |
| Pooled | Mars nakshatra × KP Asc number | i-Box | RM192 (no picks on 21 Oct) | 1 (5304 Toto Cons) | 12 | ~RM75 | 39% |
| Magnum | Jupiter retrograde × KP Asc sub lord | Straight | RM80 | 0 | 3 | RM0 | 0% |
| Magnum | Nakshatra lord × Day stem | Reverse | RM80 | 1 (0876 Cons) | 6 (incl. **5321 2nd**) | RM60 Straight / ~RM69 i-Box | 75–86% |
| Magnum | Moon rashi × Day god | i-Box | RM80 | 0 | 4 | ~RM23 | 28% |
| Sports Toto | Lunar month × Day element | i-Box | RM80 | 0 | 3 (incl. 4937 **3rd**) | ~RM31 | 39% |
| Sports Toto | Mercury rashi × Moon navamsa | i-Box | RM80 | 1 (**6693 Special**, RM180 Straight) | 3 (incl. 3561 **3rd**) | ~RM43 | 54% |
| Da Ma Cai | Ayana × KP Asc star lord | Reverse | RM80 | 0 | 2 | ~RM30 | 38% |
| **Da Ma Cai** | **Ritu × Day stem** | i-Box | RM80 | 0 | 3 (incl. **6906 1st**) | **~RM213** | **267%** |

**Draw by draw:**

| Lead | 11 Oct | 14 Oct | 17 Oct | 18 Oct | 21 Oct |
|---|---|---|---|---|---|
| Karana × Day pillar | 2 iB | 2 iB | 2 iB | 5 iB | 3 iB (4246 Toto 3rd) |
| Mars nakshatra × KP Asc number | – | 3 iB | 2 iB | **5304 Toto Cons** + 7 iB | no picks |
| Jupiter retrograde × KP Asc sub lord (Mag) | – | – | 1 iB | – | 2 iB |
| Nakshatra lord × Day stem (Mag) | 1 iB (**5321 Mag 2nd**) | 1 iB | – | 1 iB | **0876 Mag Cons** + 3 iB |
| Moon rashi × Day god (Mag) | – | – | 1 iB | – | 3 iB |
| Lunar month × Day element (Toto) | 1 iB | – | 1 iB | 1 iB (4937 **3rd**) | – |
| Mercury rashi × Moon navamsa (Toto) | 2 iB (3561 **3rd**) | – | **6693 Toto Special** | – | – |
| Ayana × KP Asc star lord (DMC) | – | 1 iB | 1 iB | – | – |
| Ritu × Day stem (DMC) | 1 iB | **9066 → 6906 DMC 1st** (~RM208) | 1 iB | – | – |

A dash means nothing matched; "iB" means i-Box matches.

**How to read this:**
- **All 9 together** staked RM832 and won about RM620 with their own bet types (75%). Without Ritu × Day stem's one 1st-prize match it's about RM407 (49%).
- **Straight hits:** 3 in 5 draws across all leads, about what chance gives. None of the three were top prizes.
- **The near-misses:** a 2nd prize (5321, Magnum) and two 3rd prizes (4937 and 3561, Toto) came in as different arrangements of picked numbers. As i-Box bets they pay only part of the prize.
- **Overall:** 5 draws are far too few to judge leads whose edge is at most about 1.36×. These results are within normal luck, good or bad.

The script is `analysis/consistent_leads_live.py`, committed and pushed. If you'd like these 9 tracked live, I can log their picks before Saturday's draw on 24 Oct and score them after each draw.

---

## 79. Question (2026-10-22 14:23)

> lets analyse Karana x Day Pillar and try to check if there's a way to get profit out of it? maybe focus on operator and try to reduce the numbers to bet, if there's a distinct pattern in the ibox especially the last 5 draws

**Answer** (2026-10-22 14:23)

I'll take Karana × Day pillar apart: which operator it works on, which of its 16 numbers carry the edge, what kind of numbers they are (how many distinct digits), and which prize tiers its i-Box matches land in. Any narrower betting rule gets chosen on 1985–2011 and checked on 2012–2026, so it can't be fitted to recent luck. I'll also look at the last 5 draws in detail.

I couldn't find a way to make Karana × Day pillar profitable. Its edge is real but small, only about 4% more i-Box matches than chance. No choice of operator or of which numbers to bet, made on 1985–2011 data, pushes it near break-even after 2012.

**The full lead** (16 picks × 3 operators, every draw since 1985):

| | Before 2012 | 2012–2026 |
|---|---|---|
| i-Box matches vs chance | ×1.03 | ×1.04 |
| Return as Big i-Box | 66.5% | 68.2% |
| Return as Small i-Box | 68.2% | 69.9% |
| Random numbers, for comparison | about 64% | about 64% |

It's steadily better than random numbers, but you'd still lose about 30 sen of every ringgit.

**1. Focusing on one operator**

| Operator | Before 2012 | 2012–2026 | Big i-Box return after 2012 |
|---|---|---|---|
| Magnum | ×1.04 | ×1.00 | 65.9% |
| Sports Toto | ×1.01 | **×1.09** | 67.6% |
| Da Ma Cai | ×1.04 | ×1.02 | 71.2% |

Sports Toto has done best since 2012, and 7 of the 14 matches in the last 5 draws were Toto. But it was the weakest operator before 2012, so picking it now would be choosing with hindsight. No operator is consistently best.

**2. Betting fewer numbers.** Rules chosen on 1985–2011 data, then checked on 2012–2026:

| Rule (chosen before 2012) | Numbers bet | After 2012 | Big i-Box return |
|---|---|---|---|
| All 16 picks | 16 | ×1.037 | 68.2% |
| The 13 grid positions that were above chance before 2012 | 13 | ×1.045 | 69.3% |
| Excluding numbers with 4 or fewer arrangements | about 15 | ×1.036 | 68.1% |
| All filters combined | about 12 | ×1.045 | 69.2% |

Filtering trims about 1 percentage point off the loss at most. None of the 16 grid positions held up as better in both periods; the before-2012 and after-2012 rankings don't line up.

**3. Number type (how many arrangements a number has)** is the one interesting result:

| Type | Example | Before 2012 | 2012–2026 | Small i-Box return after |
|---|---|---|---|---|
| 24 arrangements (all digits different) | 6340 | ×1.04 | ×1.04 | 66.5% |
| 12 arrangements (one pair) | 9596 | ×1.01 | ×1.02 | 71.6% |
| **6 arrangements (two pairs)** | **3311, 7744** | **×1.42** | **×1.26** | **~103%** |
| 4 arrangements (three of a kind) | 4442 | ×0.84 | ×1.11 | 75.6% |

- **Two-pair picks (AABB type)** matched more often in both periods, and as Small i-Box they returned about break-even both times (105% before 2012, 103% after).
- **But that rests on very few wins:** just 8 top-3 matches in 15 years, against about 5.7 expected by chance. Small i-Box only pays on 1st, 2nd and 3rd prize. Getting 8 or more when 5.7 is expected happens about 1 time in 4 by luck.
- **These picks are rare:** only about 0.6 two-pair numbers per draw across all 3 operators, so you'd often have nothing to bet.
- **At best it breaks even.** Even if the effect is real, about 103% isn't enough to profit after variance, and it could easily be luck.

**4. Prize tiers:** matches are spread evenly across tiers, slightly high everywhere (3rd ×1.11, 1st ×1.07, Special ×1.03). They don't concentrate in a tier that would favour Big over Small bets.

**5. The last 5 draws** (14 i-Box matches, against 10.7 expected):
- **Prizes:** 12 of the 14 were Specials or Consolations, and one was Toto's 3rd prize (6442 → 4246).
- **Number types:** mostly 24-arrangement numbers, with no two-pair matches.
- **Operators:** Sports Toto had 7 matches, against 3.6 expected; Magnum had 4 and Da Ma Cai 3.
- **Grid positions:** spread across many positions, with nothing repeating.
- **Return:** Specials and Consolations pay so little that 14 matches returned only 54% as Big i-Box.

There's no distinct pattern here. It's the usual mix of small matches.

**Conclusion:** the most this lead can do is lose a little less than random numbers (about 68–69% back instead of 64%). The two-pair Small i-Box subset is the only angle near break-even, and it's too rare and too uncertain to count on. The analysis is in `analysis/karana_profit.py`, committed and pushed.

---

## 80. Question (2026-10-22 14:30)

> 6 arrangements (two pairs)	3311, 7744	×1.42	×1.26	~103% this will be added as a lead and also tell me how this performed in the last 5 drwas

**Answer** (2026-10-22 14:30)

I'll check which of Karana × Day pillar's picks in the last 5 draws were two-pair (6-arrangement) numbers and how they did. Then I'll add it to the leads and log its picks for Saturday's draw (24 Oct).

I've added the two-pair lead to `FINDINGS.md` and pushed it. In the last 5 draws it had only 2 numbers to bet, and neither matched.

**The lead:** take Karana × Day pillar's 16 picks (S1 from the previous same-value day) and bet only the two-pair numbers (6 arrangements, like 3311 or 7744). Bet them as Small i-Box on all 3 operators.

**Last 5 draws:**

| Draw | Two-pair picks | Staked (Small i-Box, 3 operators) | Result |
|---|---|---|---|
| 11 Oct | 6116 | RM3 | no match |
| 14 Oct | none | – | – |
| 17 Oct | none | – | – |
| 18 Oct | 9696 | RM3 | no match |
| 21 Oct | none | – | – |
| **Total** | **2 numbers** | **RM6** | **RM0** |

**This is normal for this lead.** It averages only about 0.6 two-pair numbers per draw across the operators, so most draws have nothing to bet. Small i-Box pays only on the 1st, 2nd or 3rd prize, so even with a pick, a win comes along only every few years: 8 times in 2012–2026.

**Saturday 24 Oct:** no bet. Tonight's values are Garaja × Xin Wei, taken from the last matching draw on 23 Jan 2021, and none of the 16 numbers is a two-pair:

0411 0416 0451 0456 0911 0916 0951 0956 1411 1416 1451 1456 1911 1916 1951 1956

**How to judge this lead:** it needs years of draws, not weeks. Even at its best 2012–2026 rate it only about broke even (103% back), from 8 wins where chance gives about 5.7, which could be luck. I'll keep checking it whenever a two-pair pick comes up and add any result to the live log.

---

## 81. Question (2026-10-22 14:33)

> ok now since there's many types of ibox, as one of it is 2 pairs aabb, redo all the analysis to see if certain leads is more into certain pattern of ibox

**Answer** (2026-10-22 14:33)

The number types for i-Box are:

| Pattern | Arrangements | Example |
|---|---|---|
| ABCD (all different) | 24 | 6340 |
| AABC (one pair) | 12 | 9596 |
| AABB (two pairs) | 6 | 3311 |
| AAAB (three of a kind) | 4 | 4442 |
| AAAA (four of a kind) | 1 | 7777 |

I'll rerun the digit-position picks (S1, S2, S3 and rank pairs, versions a and b) for all singles and pairs. This time each pick's i-Box matches are scored separately by its pattern. Each pick counts as its own bet.

For each pattern I'll check two things:
- **Walk-forward:** the top tests chosen on 1985–2011 data, scored on 2012–2026.
- **Whole pattern:** whether that pattern does better than chance across all tests, compared with shifted calendars.

This runs pooled and then for each operator.

The i-Box pattern analysis is running in the background: pooled first, then Magnum, Sports Toto and Da Ma Cai. It should take about 1.5 hours, and the script (`analysis/pattern_ibox.py`) is committed and pushed.

For every single parameter and pair, the S1, S2, S3 and rank-pair picks are scored as i-Box, with each pick's matches counted under its own pattern:

| Pattern | Arrangements | Example |
|---|---|---|
| ABCD | 24 | 6340 |
| AABC | 12 | 9596 |
| AABB | 6 | 3311 |
| AAAB | 4 | 4442 |
| AAAA | 1 | 7777 |

For each pattern I'll report:
- **Overall:** whether that pattern beats chance across all tests, compared with shifted calendars.
- **Forward:** the top tests chosen on 1985–2011, scored on 2012–2026, also against shifted calendars.
- **Best leads per pattern:** for example, whether the two-pair (AABB) edge seen in Karana × Day pillar also appears in other formulas, or only there.

I'll send the comparison for all four runs when it finishes.

No i-Box pattern beats chance in general, and none of the strong-looking per-pattern leads survived checking, except our existing Karana × Day pillar two-pair lead.

I ran this for all singles and pairs, with every pick method (S1, S2, S3 and rank pairs; versions a and b), pooled and for each operator, splitting each pick's i-Box matches by its pattern. The scores below are average z on 2012–2026; 0 means chance.

**Each pattern across all tests, real vs shifted calendars (chance):**

| Pattern | Share of matches | Pooled | Magnum | Sports Toto | Da Ma Cai |
|---|---|---|---|---|---|
| ABCD (24 arrangements) | 68% | +0.07 vs +0.08 | −0.19 vs −0.17 | −0.02 vs −0.02 | +0.17 vs +0.19 |
| AABC (12) | 30% | −0.02 vs −0.03 | +0.03 vs +0.05 | +0.08 vs +0.09 | −0.24 vs −0.23 |
| AABB (6, two pairs) | 1% | +0.18 vs +0.20 | +0.44 vs +0.43 | −0.18 vs −0.12 | −0.11 vs −0.09 |
| AAAB (4) | 1% | +0.14 vs +0.13 | −0.08 vs −0.06 | +0.01 vs +0.05 | +0.16 vs +0.14 |
| AAAA (1) | under 0.1% | +0.08 vs +0.08 | +0.17 vs +0.14 | +0.10 vs +0.09 | −0.03 vs −0.02 |

In every case, real and shifted calendars are equal. No pattern does better than chance in general, for any operator.

**Forward check** (5 best tests chosen on 1985–2011, scored on 2012–2026):
- **Pooled two-pair (AABB) is the only lean:** +0.29 against +0.19 by chance, and 5 of 14 pick methods beat every shifted calendar where about 2 are expected.
- **Everything else is at chance:** all other patterns and all per-operator results are within the shifted-calendar range, with only 0 to 5 methods beating them.

**A counting problem with two-pair and three-of-a-kind picks.** A pick set can hold several numbers with the same digits, for example 7227, 7272 and 7722. One winning number then matches all of them, so each pick's tally rises at once.
- **The biggest outlier was mostly this effect:** Da Ma Cai's KP Moon number × KP Asc star lord (two-pair) showed 46 matches after 2012 against 21.7 expected (z +5.22). But only 21 different winning numbers were involved, which is exactly what chance gives. Its return was 57% as Big i-Box and 31% as Small.
- **The other big "best" per-pattern results are unreliable too.** Many rest on only 1 or 2 matches (for example, the four-of-a-kind leads at ×7 to ×21), or on the same double counting.
- **Comparisons with the shifted calendars are still fair,** because those calendars count the same way.

**Karana × Day pillar two-pair (the lead added earlier) still holds up** when each winning number is counted once:

| | Distinct winners matched vs expected | Top-3 prize matches | Small i-Box return |
|---|---|---|---|
| Before 2012 | 81 vs 52 (×1.55) | 10 | 105% |
| 2012–2026 | 53 vs 42 (×1.26) | 8 | 103% |

Its picks rarely share the same digits, so the double counting barely affected it. It's still the only setup near break-even, and it still rests on very few top-3 wins.

**So no lead specialises in a particular i-Box pattern** beyond what chance produces. The two-pair edge found in Karana × Day pillar is unusual and doesn't generalise to other formulas.

The results and the note on double counting are in `FINDINGS.md`, committed and pushed.

---

## 82. Question (2026-10-22 16:15)

> The biggest outlier was mostly this effect: Da Ma Cai’s KP Moon number × KP Asc star lord (two-pair) showed 46 matches after 2012 against 21.7 expected (z +5.22). But only 21 different winning numbers were involved, which is exactly what chance gives. Its return was 57% as Big i-Box and 31% as Small. tell me more about this and its performance for the last 5 draws

**Answer** (2026-10-22 16:15)

This formula looked like the strongest two-pair lead, but it's a counting artifact. It has no real edge, and in the last 5 draws it had only one two-pair pick, which didn't win.

**How it works:**
- **Operator:** Da Ma Cai only. Picks are built from Da Ma Cai's past results and scored on its draws.
- **Parameters:**
  - **KP Moon number:** the KP sub-division the Moon is in at 7 pm. There are 249 of these, and it changes every couple of hours.
  - **KP Ascendant star lord:** one of 9 planets.
- **Combinations:** 249 × 9 gives over 2,000 possible pairs (2,043 have occurred). Each one recurs only every few years, so the history behind each set of picks is very thin, often just 1 to 5 earlier draws.
- **Method, 3+8 (a):** take all earlier Da Ma Cai draws with the same KP Moon number and Ascendant star lord. Count the digits in each position, and combine the 3rd-hottest and 8th-hottest digit in each position into 16 numbers.
- **Two-pair subset:** only the numbers among those 16 with two pairs (like 7227), bet as i-Box.

**Why its z of +5.22 was misleading:**

| 2012–2026 | Value |
|---|---|
| Two-pair numbers bet | 1,600 |
| Matches, counted per pick | 46 (21.7 expected), which gave z +5.22 |
| Different winning numbers involved | **21** (21.7 expected), which is chance |
| Return as Big i-Box | 57% |
| Return as Small i-Box | 31% |

- **One winning number gets counted several times.** Its picks often include several arrangements of the same digits. On 12 Apr 2023, DMC's Consolation 7227 matched three picks at once: 7227, 7272 and 7722.
- **In 2023 alone,** 13 matches came from just 3 winning numbers.
- **Its "before 2012" score of z +4.17 was inflated the same way**, which is why it got chosen in the first place.
- **Prize tiers:** almost every match was a Special or Consolation (33 Consolation, 11 Special, one 3rd and one 2nd). That's why it returned so little.

**Last 5 draws on Da Ma Cai:**

| Draw | KP Moon number × Asc star lord | Earlier same-value draws | 16 picks | Two-pair picks | Two-pair result | All 16 as i-Box |
|---|---|---|---|---|---|---|
| 11 Oct | 127 × Mercury | 5 | 3082 3081 3022 3021 3682 3681 3622 3621 5082 5081 5022 5021 5682 5681 5622 5621 | none | – | 0 |
| 14 Oct | 153 × Mercury | 3 | 1595 1598 1535 1538 1795 1798 1735 1738 8595 8598 8535 8538 8795 8798 8735 8738 | none | – | 0 |
| 17 Oct | 178 × Ketu | 2 | 0457 0454 0447 0444 0657 0654 0647 0644 9457 9454 9447 9444 9657 9654 9647 9644 | none | – | 2 (0474 Cons, 7459 Special), ~RM12.50 |
| 18 Oct | 187 × Ketu | 3 | 5022 5024 5042 5044 5622 5624 5642 5644 8022 8024 8042 8044 8622 8624 8642 8644 | none | – | 3 (2405 Cons ×2, 4456 Cons), ~RM10 |
| 21 Oct | 211 × Ketu | 1 | 4142 4143 4172 4173 4342 4343 4372 4373 0142 0143 0172 0173 0342 0343 0372 0373 | 4343 | no match | 0 |

- **As the two-pair lead:** only 1 number in 5 draws (4343 on 21 Oct, RM1 staked), and it didn't win.
- **As all 16 numbers:** no Straight hits and 5 small i-Box matches, worth about RM22 on RM80 staked.
- **Thin history:** each draw's picks came from just 1 to 5 earlier matching draws.
- **The 18 Oct double count:** 2405 matched twice (5024 and 5042), the same effect as above.

**Verdict:** this isn't a real lead. When each winning number is counted once it's exactly at chance, it returned only 31–57% of stakes, and its picks rest on very little history. The Karana × Day pillar two-pair lead is different: it holds up when counted by distinct winners, so it stays on the list and this one doesn't.

---

## 83. Question (2026-10-22 16:17)

> Karana × Day pillar two-pair (the lead added earlier) still holds up when each winning number is counted once: hmmm this looks interesting lets analyse karana x day pillar deeply, how does triplets perform here?

**Answer** (2026-10-22 16:18)

I'll take Karana × Day pillar apart by number pattern, with each winning number counted once. That covers triplets (AAAB, three of a kind) alongside the other patterns. For each pattern I'll show matches against chance, top-3 prizes, Big and Small i-Box returns, a split by operator, a year-by-year view for the rare patterns, and the last 5 draws.

Triplets (AAAB, three of a kind) don't work for Karana × Day pillar: below chance before 2012, slightly above after, and losing money as both Big and Small i-Box. The two-pair (AABB) numbers remain the only pattern that stands out, and they also look quite consistent year by year.

All counts below take each winning number once per draw and operator.

**By pattern, all 3 operators:**

| Pattern | Before 2012: distinct winners vs chance | 2012–2026 | Big i-Box return, before → after | Small i-Box return, before → after |
|---|---|---|---|---|
| ABCD (all different) | 4,234 vs 4,073, ×1.04 (z +2.5) | ×1.05 (z +2.6) | 67% → 66% | 67% → 67% |
| AABC (one pair) | ×1.01 | ×1.02 | 66% → 69% | 68% → 72% |
| **AABB (two pairs)** | **81 vs 59, ×1.37 (z +2.8)** | **53 vs 42, ×1.25 (z +1.6)** | **99% → 97%** | **105% → 103%** |
| AAAB (triplet) | 47 vs 55, ×0.86 (z −1.1) | 44 vs 39, ×1.13 (z +0.8) | 54% → 73% | 64% → 76% |
| AAAA (four of a kind) | 0 vs 0.4 | 0 vs 0.3 | 0% | 0% |

**Triplets (AAAB):**
- They were below chance before 2012 and only slightly above after, so there's no steady edge.
- They lost money both ways: at best 73% back as Big i-Box and 76% as Small.
- By operator after 2012 it's ×1.01 to ×1.22, all within noise. Da Ma Cai triplets returned 114% as Small i-Box after 2012, but that's from just 3 top-3 wins, and before 2012 Da Ma Cai triplets were the worst (×0.52).
- They were above chance in 10 of the 15 years.
- Top-3 wins since 2012: 6 in total (6222 Magnum 1st, 3033 DMC 1st, 1555 DMC 2nd, 0060 Toto 2nd, 3444 Toto 3rd, 0500 DMC 3rd).

**Two pairs (AABB) in more detail:**
- **Above chance in 12 of 15 years** (2012–2026). Its matches were in 8 to 10 different years, not one lucky run.
- **8 top-3 wins since 2012,** across all three operators:

| Date | Operator | Number | Prize |
|---|---|---|---|
| 19 Feb 2013 | Toto | 2727 | 1st |
| 27 Aug 2013 | DMC | 8855 | 2nd |
| 5 Oct 2013 | Magnum | 7744 | 1st |
| 15 Apr 2018 | Toto | 8833 | 2nd |
| 18 May 2019 | Toto | 2772 | 2nd |
| 18 Sep 2019 | DMC | 1001 | 1st |
| 6 Mar 2022 | Toto | 3131 | 2nd |
| 12 Nov 2023 | Toto | 3030 | 3rd |

- **No operator is reliably better.** Magnum was strong before 2012 (×1.43) and weak after (×0.77). Sports Toto was the opposite (×1.32, then ×1.41). Da Ma Cai was steady at ×1.33 then ×1.57.

So it works across operators rather than on one, which is why betting all three makes sense.

**ABCD numbers carry most of the lead's ordinary edge.** They're a small edge (×1.04–1.05), but it's statistically solid in both periods (z +2.5), because they make up most of the bets. They still return only about 66% of stakes.

**Last 5 draws:**

| Draw | Picks by pattern | Matches |
|---|---|---|
| 11 Oct | 9 ABCD, 6 AABC, 1 AABB (6116) | ABCD: 4601 Mag Cons, 6514 Toto Spec |
| 14 Oct | 12 ABCD, 4 AABC | ABCD: 4381, 6901 Toto Cons |
| 17 Oct | 8 ABCD, 8 AABC | ABCD: 7819 Toto Cons, 2980 DMC Cons |
| 18 Oct | 9 ABCD, 6 AABC, 1 AABB (9696) | ABCD: 4960 Mag, 4950 Toto, 9406 + 5619 DMC (Specials); AABC: 9569 Mag Spec |
| 21 Oct | 12 ABCD, 4 AABC | ABCD: 4036 Mag Spec; AABC: 4409 Toto Spec, **4246 Toto 3rd** |

- **No triplet picks** came up in these 5 draws, and the two two-pair picks (6116, 9696) didn't match.
- **ABCD:** 11 matches against 8.3 expected, but all Specials and Consolations, so it returned only 38% as Big i-Box.
- **AABC:** 3 matches, including Toto's 3rd prize, returning 85% Big and 99% Small.

**Summary:**
- **Triplets aren't worth betting** with this lead.
- **Two-pair numbers are the only pattern near break-even,** at 103–105% as Small i-Box in both periods and above chance in 12 of 15 years. It still rests on few big wins (8 top-3 in 15 years), and you'd only have a number to bet on about 1 draw in 3.

The script (`analysis/karana_patterns.py`) is committed and pushed.

---

## 84. Question (2026-10-22 16:27)

> so have you done the same analysis for all the singles and pairs not only the leads in the similar fashion?

**Answer** (2026-10-22 16:27)

Partly. The earlier run (`pattern_ibox.py`) covered every single parameter and pair, with every pick method, pooled and for each operator, split by i-Box pattern. But it wasn't done the way I just analysed Karana × Day pillar. It's missing three things:

| | Karana deep dive | All singles and pairs (`pattern_ibox.py`) |
|---|---|---|
| Counts each winning number once (no double counting) | yes | **no**: counted per pick, which inflates two-pair and triplet results (the Da Ma Cai outlier) |
| Money returns as Big and Small i-Box | yes | **no**: match counts only |
| Number of top-3 prize wins | yes | **no** |
| Year-by-year consistency (good years out of 15) | yes | **no** |
| Split by operator | yes | yes |
| Compared with shifted calendars | (single lead) | yes |

So the existing all-tests results can say that no pattern beats chance overall. They can't fairly say whether some other formula has a two-pair or triplet edge like Karana × Day pillar's, because the per-test numbers for those patterns are inflated by double counting.

To do it properly I'd rerun all 78 singles and 3,003 pairs, with all pick methods (S1, S2, S3 and the rank pairs, versions a and b), pooled and for each operator. For each pattern I'd:
- count each winning number once,
- add Big and Small i-Box returns and top-3 wins,
- choose candidates on 1985–2011 and check them on 2012–2026,
- count good years for the best candidates,
- compare everything with shifted calendars.

It would take about 2 to 3 hours. Should I run it?

---

## 85. Question (2026-10-22 16:29)

> ok thats fine lets do the same analysis for our second best lead only

**Answer** (2026-10-22 16:29)

I'll use **Mars nakshatra × KP Asc number** (5th + 6th digits from the previous same-value day, i-Box) as the second-best lead. It ranks second in the latest pooled consistency check, at 13 of 15 years. I'll make the Karana script work for any lead and run it on this one.

I took the second-best lead to be **Mars nakshatra × KP Asc number** (5th + 6th digits from the previous same-value day, i-Box), which is second in the pooled year-by-year ranking at 13 of 15 years. Its two-pair numbers also match more often than chance, like Karana × Day pillar's. Unlike Karana's, they don't turn that into money, because they've had very few top-3 wins since 2012.

All counts take each winning number once per draw and operator, with all 3 operators bet.

**By pattern:**

| Pattern | Before 2012: distinct winners vs chance | 2012–2026 | Top-3 wins (before / after) | Big i-Box return (before → after) | Small i-Box return |
|---|---|---|---|---|---|
| ABCD | ×1.04 (z +1.6) | ×1.04 (z +1.8) | 191 / 286 | 65% → 72% | 65% → 77% |
| AABC (one pair) | ×1.06 (z +1.6) | ×1.06 (z +1.7) | 91 / 121 | 74% → 68% | 76% → 70% |
| **AABB (two pairs)** | **30 vs 21, ×1.41** | **38 vs 27, ×1.39 (z +2.0)** | 6 / **3** | 92% → **58%** | 111% → **41%** |
| AAAB (triplet) | ×1.02 | ×1.20 | 2 / 3 | 47% → 82% | 46% → 71% |
| AAAA | 0 | 0 | 0 / 0 | 0% | 0% |

- **Two pairs:** it matches ×1.4 more often than chance in both periods, a bigger excess than Karana's. But since 2012 it had only 3 top-3 wins, so Small i-Box returned just 41%:
  - 6060, Sports Toto 3rd (Oct 2015)
  - 2992, Magnum 2nd (Apr 2021)
  - 0066, Magnum 2nd (May 2022)

  It was above chance in only 9 of 15 years, and 10 of its 38 matches came in 2022 alone.
- **Triplets:** about chance before 2012 (×1.02), a bit higher after (×1.20), and above chance in 9 of 15 years. Magnum and Sports Toto triplets returned about 100–120% as Big or Small i-Box after 2012, but each rests on 1 or 2 top-3 wins: 8880 Magnum 1st (2013), 9444 Toto 1st (2013), 2444 Toto 3rd (2019). Da Ma Cai went from the best before 2012 to the worst after.
- **Ordinary numbers (ABCD and AABC):** steady small edges of about ×1.04–1.06 in both periods. Most of its matches come from these, and they returned 68–77%.

**Last 5 draws:**

| Draw | Picks | Matches |
|---|---|---|
| 11 Oct | 12 ABCD, 4 AABC | none |
| 14 Oct | 5 ABCD, 10 AABC, 1 AABB (0440) | 0164 Mag Spec, 1480 Toto Cons, 0014 Toto Spec |
| 17 Oct | 8 ABCD, 8 AABC | 8033 Mag Cons, 5620 Toto Cons |
| 18 Oct | 12 ABCD, 4 AABC | 3804, 0382, 3005 Mag Spec; 4380 Mag Cons; 5304, 3280 Toto Cons; 8030 DMC Cons |
| 21 Oct | no picks (no earlier same-value day) | – |

There were 12 matches (8.3 expected), but all Specials and Consolations, so the return was low: 32% for ABCD and 51% for AABC as Big i-Box. The one two-pair pick (0440) and no triplets came up, and nothing matched in those.

**Why two pairs show up in both leads:**
- Across all winning numbers since 1985, two-pair numbers come up a little more often than the digit-mix model expects: 2.75% vs 2.70%, ×1.02. That's real but tiny. It's slightly stronger for Magnum since 2012 (×1.06).
- That general bias is far smaller than the ×1.25–1.4 these two leads show. So their two-pair edge is mostly specific to them, though each rests on only 40–80 matches.
- Making money from it depends on landing top-3 prizes, which is a matter of luck at these numbers. Karana got 8 of them since 2012; Mars × KP Asc got only 3.

**Comparing the two leads:**

| | Karana × Day pillar | Mars nakshatra × KP Asc number |
|---|---|---|
| Two-pair matches vs chance (before / after) | ×1.37 / ×1.25 | ×1.41 / ×1.39 |
| Two-pair years above chance | 12 of 15 | 9 of 15 |
| Two-pair top-3 wins since 2012 | 8 | 3 |
| Two-pair Small i-Box return since 2012 | 103% | 41% |
| Triplets | not useful | not useful (rests on 3 wins) |

So the two-pair edge appears in both leads, but only Karana's has come anywhere near break-even. Mars × KP Asc shows that even with more matches than chance, the return depends on whether top-3 prizes happen to land.

The script now works for any lead and is committed: `python3 analysis/karana_patterns.py mars_nakshatra kp_asc_number 5+6 b`.

---

## 86. Question (2026-10-22 16:45)

> the fact that karana x day pillar is so good at being predictive model needs to be investigated further if their family acts the same, and also the family within them is able to produce a better result

**Answer** (2026-10-22 16:45)

I'll investigate the Karana × Day pillar family the same way I did for Mercury × Venus earlier. All scores use the lead's own method (S1 from the previous same-value day, bet as i-Box), and each family member's picks are rebuilt before every draw:

1. **The lead in every version:** all pick methods and bet types, before and after 2012.
2. **Its two halves alone:** Karana alone and Day pillar alone.
3. **Families:**
   - Karana × every other parameter
   - Day pillar × every other parameter
   - Karana × the parts of the day pillar (day stem, day branch, nayin, day element)
   - every Panchanga element (tithi, karana, yoga, nakshatra, weekday) × every Chinese day element (day pillar, stem, branch, nayin, element, officer, god)
4. **Is any relative better?** The best member chosen on 1985–2011, checked on 2012–2026 and compared with the lead.
5. **Which values drive it:** each karana and each day pillar.

Every family is compared with shifted calendars.

The family does share the effect, and it comes from the **Day pillar** side. With the lead's method (S1 from the previous same-value day, bet as i-Box), Day pillar paired with almost anything tends to do better than chance after 2012. Karana's other pairs don't. No relative chosen in advance beats the original lead, though.

**1. The lead in its other versions:** across all 42 pick methods and bet types, Karana × Day pillar averages z −0.18 after 2012, and only 10 of 42 versions were positive in both periods. Its strength is specific to one version:

| Version | z before 2012 | z after 2012 |
|---|---|---|
| **S1 (b) i-Box (the lead)** | **+2.52** | **+2.72 (×1.04)** |
| 4+7 (a) i-Box | +2.35 | +1.44 |
| S1 (a) i-Box | +0.53 | +1.36 |

**2. The halves alone:**

| Test | z before | z after | Good years | After 2012 |
|---|---|---|---|---|
| Karana alone | +1.23 | −0.87 | 7 of 15 | ×0.99 |
| Day pillar alone | +0.02 | +0.71 | 10 of 15 | ×1.01 |
| **Karana × Day pillar** | **+2.52** | **+2.72** | **14 of 15** | **×1.04** |

The pair is much stronger than either half.

**3. Families,** scored with the lead's method and with the lead itself left out. All 3,081 tests average z −0.19 after 2012:

| Family | Tests | z after 2012 | Shifted calendars (chance) | Good years (chance) | Above chance after 2012 |
|---|---|---|---|---|---|
| Karana × any other parameter | 76 | −0.31 | −0.21 (11 of 20 as high) | 6.9 (7.0) | 20 of 76 |
| **Day pillar × any other parameter** | 76 | **+0.43** | −0.17 (**1 of 20 as high**) | **8.3 (7.2)** | **53 of 76** |
| Karana × parts of the day pillar | 4 | +0.91 | −0.08 (0 of 20) | 9.5 (7.2) | 3 of 4 |
| **Panchanga × Chinese day elements** | 34 | **+0.30** | −0.12 (**0 of 20**) | 7.7 (7.2) | 23 of 34 |

- **Day pillar's family behaves the same way.** 53 of its 76 pairings beat chance after 2012, the family beat 19 of 20 shifted calendars, and it averaged about one more good year than chance. This is the first family-level effect we've found that holds up against shifted calendars. Panchanga × Chinese day elements shows the same, partly because it includes Day pillar pairs.
- **Karana's family doesn't.** Karana works only in combination with Day pillar.
- **The size is small:** the family averages only about z +0.4, roughly 1% more i-Box matches than chance.

**4. Is any relative better?** Choosing the best member of each family on 1985–2011 only:

| Family | Best chosen before 2012 | After 2012 |
|---|---|---|
| Day pillar × any | Yoga × Day pillar (z +3.02 before) | z +1.09, ×1.016, 10 of 15 years |
| Karana × any | Karana × Masa (z +2.02 before) | z −0.66 |
| Karana × parts of the day pillar | Karana × Day stem | z +0.69, 10 of 15 years |

None beats the lead (z +2.72, 14 of 15 years). Some family members look good after 2012 only with hindsight:
- **Mercury retrograde × Day pillar:** z +2.00, 13 of 15 years
- **Moon navamsa × Day pillar:** z +1.94, 13 of 15 years
- **Karana × Day branch:** z +2.42, 12 of 15 years

All three were at or below chance before 2012, so choosing them now would be fitting to the period they're judged on.

**5. Which values carry it:**
- **Karana:** 7 of 11 karanas were above chance after 2012, and 5 in both periods. Before and after line up somewhat (correlation +0.43). Vanija (×1.04 → ×1.14), Bava, Vishti and Balava are the steadiest.
- **Day pillar:** 43 of 60 pillars were above chance after 2012, but which ones doesn't repeat between periods (correlation −0.12). The edge is spread across all pillars rather than concentrated in a few.

**What this means:**
- **The Day pillar side carries a small, real-looking effect.** Day pillar repeats every 60 days, so with the previous same-pillar draw as the source, the picks seem to carry over slightly more than chance, and this survives the shifted-calendar test.
- **Karana sharpens it** into the strongest single version, which is why the pair stands out.
- **It's still too small to beat the house edge:** the best is about ×1.04 on i-Box, around 68% back. Only the two-pair subset gets near break-even.

The script and results are committed (`analysis/karana_family.py`), and `FINDINGS.md` has a summary. A good next step would be to test the Day pillar 60-day carry-over directly: for example, using only the previous same-pillar draw with no second parameter, under different pick methods, and per operator.

---

## 87. Question (2026-10-22 16:50)

> ok now how does day pillar performs with other pairs combined with it? is it better than karana?

**Answer** (2026-10-22 16:51)

Karana is the best partner for Day pillar, and it's the only one that looked strong both before and after 2012. Most other partners also come out slightly positive after 2012, but you couldn't have picked the good ones in advance.

All 76 pairs below use the lead's method (S1 from the previous same-value day, bet as i-Box). Six of them are really just Day pillar alone (z +0.71 after 2012), because those parameters are fixed by the day pillar: Day stem, Day branch, Nayin, Nayin element, Day element and Hour stem at 7 pm.

**Day pillar's partners vs Karana:**

| Partner | z before 2012 | z after 2012 | After 2012 | Good years (of 15) |
|---|---|---|---|---|
| **Karana (the lead)** | **+2.52** | **+2.72** | **×1.040** | **14** |
| Mercury retrograde | −0.13 | +2.00 | ×1.030 | 13 |
| Ritu (season) | −0.57 | +1.96 | ×1.029 | 11 |
| Moon navamsa | −1.11 | +1.94 | ×1.029 | 13 |
| Day god | −0.34 | +1.92 | ×1.028 | 10 |
| Jupiter retrograde | +0.23 | +1.88 | ×1.028 | 11 |
| Month branch | −0.05 | +1.79 | ×1.026 | 10 |
| Day officer | −0.05 | +1.79 | ×1.026 | 10 |
| Mars retrograde | +0.04 | +1.68 | ×1.025 | 10 |
| Saturn nakshatra | +0.44 | +1.57 | ×1.024 | 10 |
| Yoga | **+3.02** | +1.09 | ×1.016 | 10 |
| Day pillar alone | +0.02 | +0.71 | ×1.010 | 10 |
| … the weakest: Moon rashi | −1.43 | −2.09 | ×0.969 | 5 |

**Across all 76 pairs:**
- **Most are positive after 2012:** 53 of 76 are above chance after 2012, against about half by chance.
- **But few are steady:** only 27 are above chance in both periods.
- **No other partner comes close to Karana.** Karana's gain (×1.040) and consistency (14 of 15 years) are clearly ahead. The next best, Mercury retrograde and Moon navamsa, reach ×1.03 and 13 years.
- **The runners-up only look good with hindsight.** Mercury retrograde, Ritu, Moon navamsa and Day god were all at or below chance before 2012 (z −0.13 to −1.11). Choosing them now would mean choosing on the period they're being judged on.

**Choosing a partner fairly, on 1985–2011 only:**
- **Yoga came first** (z +3.02) and **Karana second** (z +2.52). After 2012, Yoga dropped to z +1.09, and Karana went up to z +2.72.
- **The top 10 partners chosen before 2012 averaged only z +0.06 after,** with 7.4 good years. That's essentially chance.

So Day pillar with a random partner gives at most a small lift. Karana is the one partner that held up in both periods.

**Conclusion:** Karana is clearly the best Day pillar partner. Day pillar does seem to carry a small effect into most pairings, but the pairing with Karana is what turns it into the most consistent lead we've found. The others are too small or too inconsistent to use on their own.

---

## 88. Question (2026-10-22 16:52)

> no no i mean take a pair and then combine it with day pillar and check and see if it is better than karana

**Answer** (2026-10-22 16:52)

I see: you mean a triple, Day pillar plus a pair of other parameters (A × B × Day pillar), compared with Karana × Day pillar. I'll test every pair of the other 77 parameters with Day pillar added, 2,926 triples in all, including the 76 that add a third parameter to Karana × Day pillar. Everything uses the lead's method (S1 from the previous same-value day, i-Box).

Each triple is scored before and after 2012 and counted for good years. The best ones are chosen on 1985–2011 only, and everything is compared with shifted calendars.

A few triples have no earlier draws in one period, which produced invalid averages (nan) in the summary. I'll make the summary skip those and rerun.

No triple clearly beats Karana × Day pillar. Adding Day pillar to other pairs does help a little as a group, though, more than chance.

I tested Day pillar with every pair of the other parameters (A × B × Day pillar), 2,485 triples, all with the lead's method (S1 from the previous same-value day, bet as i-Box). I left out the 6 parameters fixed by the day pillar, such as Day stem and Nayin.

**Karana × Day pillar, for reference:** z +2.52 before 2012, z +2.72 after (×1.040), and 14 of 15 good years.

**The triples as a group,** compared with 10 shifted calendars:

| | Real calendar | Shifted calendars, mean (range) |
|---|---|---|
| Average z after 2012, all triples | +0.17 | −0.00 (−0.19 to +0.34) |
| Average good years, all triples | 7.6 | 7.2 (6.7 to 7.9) |
| **Top 20 chosen before 2012: z after 2012** | **+0.79** | +0.04 (−0.46 to +0.52) |
| **Top 20 chosen before 2012: good years** | **9.2** | 7.4 (6.2 to 8.3) |
| Triples with z after above the lead's +2.72 | 8 | 5.4 (1 to 12) |
| Triples with 14+ good years | 4 | 1.6 (0 to 7) |

The top 20 triples chosen in advance beat every shifted calendar, so Day pillar does seem to improve triples a little. But individually, none chosen fairly comes out clearly ahead of the lead.

**Best triples chosen on 1985–2011 only:**

| Triple | z before | z after | After 2012 | Good years |
|---|---|---|---|---|
| Yoga × Year yin-yang × Day pillar | +3.81 | +1.50 | ×1.024 | 11 |
| Yoga × Lunar leap month × Day pillar | +3.47 | +0.60 | ×1.009 | 9 |
| Yoga × Adhika masa × Day pillar | +3.29 | +1.40 | ×1.021 | 10 |
| Yoga × Venus retrograde × Day pillar | +2.79 | +1.49 | ×1.023 | 10 |
| Karana × Venus combust × Day pillar | +2.76 | +1.48 | ×1.022 | 8 |
| **Karana × Lunar leap month × Day pillar** | **+2.74** | **+2.92** | **×1.044** | **14** |

- **Yoga triples** led before 2012 but dropped to about half that after (z +0.6 to +1.5).
- **Karana × Lunar leap month × Day pillar** is the only one slightly ahead of the lead (z +2.92 vs +2.72, ×1.044 vs ×1.040). But Lunar leap month is only "yes" in leap months, about one month every three years. So this triple is almost the same as Karana × Day pillar.

**Karana × Day pillar plus a third parameter (70 triples):** z after +0.75 on average and 8.9 good years. Adding a third parameter usually weakens the lead, because each value combination recurs less often and the picks rest on older draws. Only 3 of the 70 beat the lead after 2012:

| Triple | z before | z after | Good years |
|---|---|---|---|
| Karana × Lunar leap month × Day pillar | +2.74 | +2.92 | 14 |
| Karana × Sun rashi × Day pillar | +0.94 | +2.86 | 11 |
| Karana × Mars retrograde × Day pillar | +1.16 | +2.76 | 11 |

Of these, only Lunar leap month was also strong before 2012.

**Best after 2012, with hindsight** (these can't be trusted, because they were weak or negative before 2012):

| Triple | z before | z after | Good years |
|---|---|---|---|
| Rahu rashi × Mercury retrograde × Day pillar | −1.27 | +3.55 (×1.053) | 14 |
| Saturn retrograde × Masa × Day pillar | −0.18 | +2.93 | 11 |
| Rahu rashi × Day god × Day pillar | −1.24 | +2.81 | 12 |

**Conclusion:**
- **Karana × Day pillar is still the best lead.** No triple chosen in advance beats it by a meaningful margin, and the slightly better Karana × Lunar leap month × Day pillar is essentially the same lead.
- **Day pillar does add something as a family:** triples that include it and look good before 2012 tend to stay a little above chance afterwards. The effect is small, at most about 2–4% more i-Box matches than chance.

The script and results are committed and pushed (`analysis/day_pillar_triples.py`).

---

## 89. Question (2026-10-22 17:13)

> what are other test that we can do to investigate karana x day pillar?

**Answer** (2026-10-22 17:14)

Here are tests that would tell us whether the Karana × Day pillar effect is real and where it comes from. None of them has been done yet.

**Is it real? These would confirm or rule out the effect:**

1. **Test it on other 4D games.** Singapore 4D, Sabah 88, Sandakan, Sarawak CashSweep and Grand Dragon are completely separate draws we've never used. If the same formula beats chance there, that would be strong evidence. If it doesn't, it's probably luck in our data. This means collecting their past results first, for example from 4dmoon.com with TinyFish. *This is the strongest test available.*
2. **Shuffle Karana within each Day pillar.** Keep the real Day pillar dates but randomly reassign which Karana each date gets, about 200 times. This is a stricter chance check aimed at this pair: it shows whether Karana adds anything beyond Day pillar's own effect.
3. **Track the edge over time.** Plot the running total of matches above chance year by year, with a range of uncertainty from resampling by year. That would show whether the edge is steady, growing or fading.

**Where does it come from?**

4. **How far back the source draw is.** The picks come from the previous draw with the same Karana and Day pillar, which could be weeks or years earlier. Split results by that distance. If only recent sources work, it's probably a short-term carry-over effect, not astrology.
5. **A control matched on distance.** Use a random earlier draw that is the same distance back but has a different Karana and Day pillar. If that works just as well, the edge comes from timing, not the parameters.
6. **Traditional Karana timing.** I calculated Karana at the 7 pm draw time, but in a traditional almanac the day's Karana is taken at sunrise. Test sunrise Karana, and also 7:30 pm. If the effect only appears at exactly 7 pm, that's suspicious; if it appears at sunrise too, it fits the tradition better.
7. **Which source numbers matter.** Build the picks from only the top 3 prizes, only the Specials, only the Consolations, or only one operator's numbers from the source day. That shows which part of the source draw carries the information.

**Can it make money?**

8. **Pick construction variants.** Try the top 3 digits per position instead of 2, a ranked top 8 or 32 numbers, and the two-pair subset with Big vs Small bets. The aim is the best balance of hits and payout.
9. **Bankroll simulation, 2012–2026.** Simulate betting it every draw with fixed stakes, for the full set and for the two-pair-only version. Report total return, the longest losing streak and the worst drop, so you can see what playing it would actually feel like.

**My recommendation:** start with 1, 2 and 4. Test 1 is the only independent check. Test 2 shows whether Karana itself matters. Test 4 shows whether the edge is astrological or just a time effect.

Shall I go ahead with those three? For test 1 I'd first need to collect the other games' results.

---

## 90. Question (2026-10-22 17:15)

> try all 9

**Answer** (2026-10-22 17:15)

I'll run all 9. Tests 2–9 use the data we already have. Test 1 needs results from the other games, so first I'll check whether we can reach a source for those directly.

Writing one script that runs tests 2–9 together. After that I'll look for history for the other 4D games (test 1).

Found a public Singapore 4D dataset going back to 1986 and I'm cloning it for test 1. Tests 2, 6, 7 and 9 are still running in the background.

Tests 2–5 and 8 are done; the Karana shuffle (test 2) beat all 200 permutations. Tests 6, 7 and 9 are rerunning after a sunrise-time fix, and I'm starting the Singapore run alongside them.

I'll wait for the background watcher.

Singapore's first numbers are in, and the lead fails there: z −1.60 from 2012 to 2026. Waiting for the shifted-calendar null and the rank among all tests.

Both jobs are done. Next I'm adding the write-up to FINDINGS.md and committing.

I ran 8 of the 9 checks; for test 1 I could only get Singapore 4D. The lead held steady in Malaysia but failed on Singapore 4D, the one game it was never fitted to.

| # | Check | Result | What it means |
|---|---|---|---|
| **1** | **Other games: Singapore 4D**, 5,508 draws 1986–2026, from a public dataset | Before 2012: z −0.57. 2012–2026: z −1.60 (×0.956), 6/15 good years. 194 of 200 shifted calendars did as well. It ranks **2,958th of 3,081** tests there. | **Fails.** The 20 best Malaysian tests chosen before 2012 average z −0.33 on Singapore, the same as all tests (−0.31). |
| 2 | Shuffle Karana within each Day pillar, 200 times | 0 of 200 shuffles as good before 2012, 1 of 200 after | The exact Karana split matters in Malaysia. But this is weak evidence: the lead was picked as one of the best of 3,081 tests, so random splits will usually lose to it. |
| 3 | Edge over time | Hits above chance build up steadily from 1987 to 2026. 2012–2026: ×1.040, 95% range ×1.025–1.059. 2012–18: ×1.046, 2019–26: ×1.035. | Steady and slightly fading. It doesn't rest on one lucky year. |
| 4 | How old the source draw is | Median 660 days back. Recent sources (under 420 days) do a little better (×1.05–1.07 after 2012) than very old ones (×1.01). | Slight fade with age; few days in each group. |
| 5 | Control: use a draw 1–3 draws next to the real source | Controls ×1.010; real source ×1.040 | Recent draws help a little on their own, but the matching Karana × Day pillar draw does about 4 times better. |
| 6 | Karana at sunrise or 19:30 instead of 19:00 | Sunrise z +2.27, 19:30 z +2.44, 19:00 z +2.72 after 2012 | 19:00 is best. Sunrise isn't a fair test: its Karana is usually just the one before 19:00's, so it groups the days almost the same way. |
| 7 | Build picks from only some source numbers | Top-3 only, Specials only, Consolations only and any single operator are all weaker. Magnum only is the best of these (z +1.41 after 2012, 12/15 good years). | Needs all the source day's numbers (up to 69). |
| 8 | Other ways to build picks | Top-3 digits per position (81 numbers): z −0.59. Ranked top 4, 8, 16 or 32: z +0.18 to +0.93. | Only the original 16-number grid works, which suggests the lead fits its exact form rather than a real effect. |
| 9 | Bankroll 2012–2026, RM1 per pick per operator | **All 16 picks, Big i-Box:** staked RM117,168, got back 68.2% (random picks 63.7%), worst drawdown RM37,524. **Two-pair picks only:** Big i-Box 97.2%; Small i-Box 102.9%, which is +RM93 on RM3,157 from just 8 winning days out of 883, with a 350-draw losing streak. | All 16 loses money. Two-pair Small i-Box breaks even, and only through a handful of wins. |

**Overall:** in Malaysia the lead is consistent, but it only works in one exact form: Karana at 19:00, the 16-number grid, all the source numbers, and the matching earlier draw as the source. It doesn't carry over to Singapore 4D. That points to a pattern in Malaysian data rather than an astrological effect, so it isn't something to bet real money on.

**Gaps:**
- **Other games:** I found no bulk history for Sabah 88, Sandakan, CashSweep or Grand Dragon. Getting it would mean fetching thousands of single-date pages, so I skipped those games.
- **Singapore data:** it runs only to 12 Jul 2026.
- **Conversation log:** `docs/conversation.md` still stops at 17 Oct and doesn't include this or later discussions.

The new scripts (`analysis/karana_tests.py`, `analysis/karana_singapore.py`), their results, the Singapore data (`data/singapore4d.csv`) and a new section in `analysis/FINDINGS.md` are committed and pushed to `claude/4d-results-scraper-9ptbd5`.

The progress watch timed out after both jobs had already finished, so nothing changed and nothing was lost. The results above are final and pushed.

---

## 91. Question (2026-10-23 00:13)

> Have you checked the lunar date rule? If the repeats maybe from +-7 or some other numbers creates a lead? Do this analysis on all that we have tested before

**Answer** (2026-10-23 00:23)

The plain lags and the lunar-date rule look like noise so far. The scan of all 3,081 tests is done, and the 10 shifted-calendar runs will take about 90 minutes.

The analysis is running in the background, and I'll report when it finishes.

The lag script and its output so far are committed and pushed. The analysis is still running, and I'll commit the final results when it finishes.

The container restart killed the job halfway through the shifted calendars, so I'm rerunning it with 6 shifts (about an hour).

The job is running again, and I'll report when it finishes.

Pushed. `lag_rule_output.txt` will keep showing as changed while the job writes to it, and I'll commit the final version when the run finishes.

---

## 92. Question (2026-10-23 02:16)

> ok im wondering if shadbala or ashtakavarga matrix are used in your analysis? if not carry out this type of analysis as well on all that have been tested

**Answer** (2026-10-23 02:20)

The lag scan finished, and one result looks too strong to be real: offset +1 with ayana (S2 Straight, z +6.6). I'm checking it for a data artifact before I report anything.

Not a real effect: that result comes from only 12 scored days (7 hits where well under 1 was expected). Next I'm checking the walk-forward results as a whole against the shifted calendars.

The Shadbala/Ashtakavarga suite has started (32 new parameters, 3,024 tests), and I'll report when it finishes. The lag-rule results are already in FINDINGS.md and pushed.

Pushed. The Shadbala/Ashtakavarga run is still going, and I'll commit its final results when it finishes.

I'm waiting on the rest of the suite, and I'll report B–D when it finishes.

Pushed. The output file will keep changing until the run finishes, and I'll commit the final version then.

The run survived the restart and is on its last stage (whole-number hot/cold).

I'll report as soon as the last stage finishes.

Pushed. I'll commit the final results when the run ends.

Neither new idea gives a lead: the offset/lunar-date rule and Shadbala/Ashtakavarga both come out at chance. One part is still running: the whole-number hot/cold stage (D) for Shadbala/Ashtakavarga.

**1. Offset and lunar-date rule (`lag_rule.py`, finished)**

I moved the source draw by k days from the matching day (k = −7…+7, ±14, ±28, ±30). I ran this on all 3,081 single and pair tests, for S1 and S2 picks and for Straight, Reverse and i-Box. Each result was compared with 6 shifted calendars.
- **Picked before 2012, scored 2012–2026:** mean z +0.12, against −0.02 for the shifted calendars. 22 of 126 offset/rule combinations beat every shifted calendar, and about 18 would by chance. No offset stands out once you allow for having tried 21 of them; the best is k = +1.
- **Same lunar month and day in an earlier year,** with the same offsets: all at chance.
- **Plain lags with no parameter** (the draw 1–10, 14, 21, 28–30, 59–60, 354–365 or 384 days earlier): all at chance.
- **The biggest single numbers are not real.** For example, ayana × year pillar at k = +1 shows z +6.6, but ayana alone at k = +1 scores only 12 days (7 hits where under 1 was expected).

**2. Shadbala and Ashtakavarga (`shadbala_ashtakavarga.py`)**

Neither had been used before. I built 32 new parameters from the planet positions at 19:00:
- each planet's Ashtakavarga bindus in the sign it occupies;
- the Sarvashtakavarga total of each planet's sign, the Lagna and the 11th house;
- each planet's sign dignity;
- each planet's strength (weak / medium / strong) and the strongest and weakest planet.

The Shadbala is simplified. It leaves out Kala, Drik and Ayana bala, because they need birth-time details or barely change within a day.

I ran 3,024 tests (the new parameters alone, paired with each other, and paired with the 78 existing ones) through the same full suite as the Navamsa and D-chart work.

| Analysis | Result | Reading |
|---|---|---|
| A. Digit mix given the value | Best gain +0.001 milli-nats per digit | No information |
| B. Same 4D number when the value recurs | Best Straight z +3.75 (Mercury bindus × KP Moon number, ×1.04), but tests with z > 2 are near chance (62 vs 56). i-Box versions fall below the shifted calendars. | No lead |
| C. S1/S2/rank-pair picks, chosen before 2012 | Mean z −0.04 vs −0.03 shifted. 3 of 42 combinations beat every shift, about 6 expected by chance. Their top picks score z −0.47 to +0.63 after 2012. | No lead |
| D. Whole-number hot / cold | Still running | I'll add it when it finishes |

Both sections are in `analysis/FINDINGS.md`, and everything so far is pushed to `claude/4d-results-scraper-9ptbd5`.

---

## 93. Question (2026-10-24 09:55)

> @"/root/.claude/uploads/4d3b52ef-651f-53fd-9445-0b98be50b85b/102c96fa-20261024-174109-768464-flash.md" Check if this is right

**Answer** (2026-10-24 09:56)

The update picks don't fully match; I'll check the frozen/lead sets too.

The file is mostly right, but **three of the lead pick sets are wrong**, and one update set is wrong for two operators. I regenerated the 24 Oct picks from the repo with the same data, results through 21 Oct.

**Wrong:**

| Lead | File says | Correct |
|---|---|---|
| **lead1 Karana × Day pillar S1 (b)** | 4011 4016 4051 4056 4911 4916 4951 4956 9011 9016 9051 9056 9911 9916 9951 9956 | **0411 0416 0451 0456 0911 0916 0951 0956 1411 1416 1451 1456 1911 1916 1951 1956** (Garaja × Xin Wei, from 23 Jan 2021) |
| **lead2 KP Moon number × Year element 2+9 (b)** | 1980 1985 1900 1905 1380 … | **5479 5473 5409 5403 5979 5973 5909 5903 1479 1473 1409 1403 1979 1973 1909 1903** (KP 239 × Fire, from 1 Feb 2017) |
| **lead6 Jupiter nakshatra × Mercury combust S2 (a)** | 5650 5652 5640 5642 5850 … | **5850 5853 5840 5843 5950 5953 5940 5943 2850 2853 2840 2843 2950 2953 2940 2943** |
| **S2 Mars triple `_upd`**, Magnum | Same as the frozen set (4016 4017 …) | **4226 4227 4266 4267 4626 4627 4666 4667 6226 6227 6266 6267 6626 6627 6666 6667** |
| **S2 Mars triple `_upd`**, Da Ma Cai | Same as the frozen set (2142 2146 …) | **2342 2346 2362 2366 2742 2746 2762 2766 4342 4346 4362 4366 4742 4746 4762 4766** |

The file contradicts itself on lead1. Its `recur_S1b_karana_daypillar_ibox` set is correct, and that is the same lead, so the two should be identical. Its S2 "update" sets were simply copied from the frozen sets, not recalculated.

**Correct:** recur_S1b Karana × Day pillar, recur_S1a and lead5 Mercury nakshatra × Venus rashi (the same numbers in a different order), lead3 Tithi × Sun nakshatra, and lead8 Mercury navamsa × Venus rashi. The S1 Mars triple update sets are also correct for all three operators, and so is the S2 update set for Sports Toto.

**Not checked:** the older model sets (`both`, `chinese`, `vedic`, `manual`, `manual_v2`, the `single_*` sets and the positional sets).

**Other points in the file:**
- The data cutoff is correct: no 24 Oct results were in the data.
- Its "PASS (MATCH)" claims against `forward_log.csv` don't fit the errors above. At least lead1's generator can't be producing the right numbers.
- Skipping the 8 ML variants because LightGBM is missing is reasonable. Installing it (`pip install lightgbm`) would let it run them.

---

## 94. Question (2026-10-24 10:02)

> Why do you think this happened? Where did the error was being made because it solely looked at the repo

**Answer** (2026-10-24 10:04)

I can only partly answer this without the other agent's script, `picks_2026-10-24.py`. That file stayed on their machine and isn't in the repo. Here is what I could establish by trying to reproduce their numbers:

**1. The repo has no script that makes lead picks for a future date.** This is the main cause.
- `score_leads.py` builds leads 1–8, but only for a date that already has results in the data. It needs the draw to be in the data file. 24 Oct wasn't, so the other agent had to write its own code to work out that date's parameters and build the picks.
- Only `update_picks.py` handles a future date, and it covers just the two `recur_*` sets and the Mars triple. Those are the sets it got right.

**2. Its own code counts digits differently from the repo.** I tried every value of each lead's two parameters, with both the latest data and the 17 Oct frozen cutoff, plus every single earlier draw day as the source. None of these produce its lead1, lead2 or lead6 numbers. So it didn't just pick a wrong value like a wrong Karana. Its counting or pick-building differs, possibly in how it deduplicates numbers, filters rows, breaks ties or handles digit positions. Its own `recur_S1b` set, which came from the repo script, is correct for the same Karana × Day pillar lead. That shows the fault is in the code it wrote.

**3. The S2 "update" sets used the frozen cutoff.** I ran `update_picks.py 2026-10-24 2026-10-17`, and it reproduces its S2 `_upd` sets exactly. So those are frozen picks under an update label. Its S1 `_upd` sets were run correctly with the newer cutoff.

**4. Its "PASS (MATCH)" check proves nothing about the new numbers.** It most likely checked the entries already logged in `forward_log.csv` for 21 Oct and 18 Oct, which pass by definition. It never checked that its new code gives the same picks as the repo for any date.

**Fix:** I can add a `leads_for_date.py` that builds all the leads for any future date, using the same code as `score_leads.py`. It would also have a self-check that rebuilds 21 Oct and compares the result with the log. Then any agent reading the repo has one correct command and doesn't need to rewrite anything. If you upload their `picks_2026-10-24.py`, I can find the exact line where their counting goes wrong.

---

## 95. Question (2026-10-24 10:05)

> Yes make sure all type of code that is used for the analysis and predictions are all updated into the repo

**Answer** (2026-10-24 10:06)

Several variants in the log have no generator script in the repo at all (manual, positional, ml_*, lead1…). I'm digging through the session transcript to recover how they were made.

Recovered all the one-off code. Now I'm writing one script, `predict_all.py`, that builds every logged variant for any date and can check itself against the log.

The mismatches are only cutoffs: those sets were logged once on 17 Oct from the data at that time. I'm making them frozen at the 17 Oct cutoff, plus `_upd` versions.

Every set built in-process matches the log for both 21 and 18 Oct. Next I'm checking the astro_model sets (vedic, chinese, both).

`--before 2026-10-17` reproduces the logged vedic set exactly. I'm adding these sets to `predict_all.py`.

Those sets were logged at 00:47 on 17 Oct, ten minutes before the 11 and 14 Oct results were added. So their real cutoff is 11 Oct. Fixing that:

Every non-ML set now matches the log on both dates. Last, the ML sets: I'll find when they were logged and try to reproduce them.

Meanwhile I'm committing what's done and adding a "how to predict" section to the README.

I'm also archiving every one-off script from the session (scratchpad files and inline commands from the transcript) into `analysis/adhoc/`, so nothing used only exists on this machine.

Everything that made the analyses and picks is now in the repo. One new command rebuilds every non-ML pick set for any date, and it reproduces all of them exactly against what was logged for 18 and 21 Oct. I'm still re-running the ML model for 21 Oct to check its 8 sets the same way.

**`analysis/predict_all.py` (new):**
- `predict_all.py 2026-10-24` prints every pick set from results before that date. Add `--log` to append them to `forward_log.csv`.
- `predict_all.py --check 2026-10-21` rebuilds a date that was already logged and compares it with the log, set by set.
- It calls the analysis code itself, so another agent has no reason to rewrite the pick logic, which is what went wrong on 24 Oct. The README now has a "Making picks for a draw (use these; do not re-implement)" section.

**What `--check` showed:**
- **Different cutoffs, not bugs:** some sets first looked wrong only because they were logged at an earlier point. The single-parameter and positional sets were frozen at 17 Oct, and vedic, chinese and both were logged before the 11 and 14 Oct results were added, so their cutoff is 11 Oct. Each set without a suffix now uses its original cutoff, and each also has an `_upd` version that uses all results before the draw.
- **Real bug fixed:** `astro_model.py predict` counted every result in the data, so re-running it for a past date included that draw's own results. I added a `--before` cutoff, defaulting to the draw date.

**Code that only existed in this session:**
- **Moved in:** the manual_v2 formula, the six single-parameter formulas, the positional picks and the 21 Oct lead logging are all now part of `predict_all.py`.
- **Archived:**
  - `analysis/adhoc/` now holds the scratchpad scripts.
  - `analysis/adhoc/inline_snippets.md` holds all 165 inline analysis commands from the session, in order with timestamps.
- **Can't be rebuilt:** the original "manual" set, logged before the formula fix on 17 Oct, can't be reproduced and is excluded.

Everything is committed and pushed to `claude/4d-results-scraper-9ptbd5`.

The ML sets check out too. Re-running `ml_model.py predict --date 2026-10-21 --before 2026-10-17` reproduces all 24 logged sets exactly: 8 models × 3 operators. The README now gives that cutoff, and the change is pushed.

So every logged pick set except the old pre-fix "manual" one can be rebuilt from the repo and matches the log:
- **Non-ML sets:** rebuilt with `predict_all.py`.
- **ML sets:** rebuilt with `ml_model.py --before`.

---

## 96. Question (2026-10-24 10:47)

> The corrected picks file is sent, and it now matches your sets, but the root cause the worker gave for lead1 and lead2 doesn't fit what you saw. Score 88/100, PASS.
> 
> - **Matches your sets:** a set comparison shows lead1, lead2, lead6 and the S2 `_upd` sets for Magnum and Da Ma Cai equal yours. recur_S1b now equals lead1.
> - **ML leads added:** the 8 ML leads now have 10 picks per operator. On 10-21 the kernel leads match the forward log only on a tie-break.
> - **Root cause:** the worker says the lead1 and lead2 sets were the same numbers as yours, just in a different order from unsorted output. That doesn't fit what you saw, because the 4011… set you quoted for lead1 is a different set from 0411…. The worker's "prior" strings also don't match your quote, and the old file was overwritten, so I can't confirm its explanation. The lead6 explanation has no printed evidence, and the four `_upd` rows sit outside the table header.
> - **Still unchecked:** both, chinese, vedic, manual, manual_v2, the `single_*` sets and the positional sets. I didn't verify them against your numbers.
> 
> Pro: mode conserve · score 88/100 · retries 0 · effort S3/S5 medium/low
> With SaveToken Pro - Actual 5h: -13.133% · Weekly: -1.876% (app: 5h 23%->38%, wk 41%->43%) | Claude: in 805.2k out 62.3k cache 10487.1k | Gemini: in 3022.7k out 763.5k | Ollama: in 0 out 0
> Without (Opus 5.5 Low, est.) - 5h: -113.253% · Weekly: -16.179% | Est. tokens saved: 3,786,254 (88% of the limit cost) what do you think about this?

**Answer** (2026-10-24 10:48)

I mostly agree with the review. Its one weak point is that it doesn't push hard enough on the root cause.

**Where the review is right:**
- **The worker's explanation is wrong.** Sorting or reordering can't turn 4011 4016 … into 0411 0416 …, because those are different numbers. Order only explains why lead5 and recur_S1a looked shuffled. I also searched every parameter value and every earlier draw day under the repo's counting, and none produces the old 4011… or 1980… sets. The real cause was the worker's own reimplemented counting, as I said earlier. With the old script overwritten, nobody can show the exact line now.
- **Tie-breaks are a real issue for the kernel leads.** Their top picks are arrangements of the same digits (4222 2422 2242 2224), which score equally, so the tie-break rule decides which 10 appear. "Matches on a tie-break" is acceptable as long as the same code is used, which is what `predict_all.py` / `ml_model.py` now guarantee.

**Where I'd push back:**
- **88/100 and PASS is generous** for a report whose root-cause section is wrong. The numbers are now right only because they were re-done against my sets, not because the worker found its bug.
- **The "still unchecked" list is easy to close.** `python3 analysis/predict_all.py 2026-10-24` prints both, chinese, vedic, manual_v2, the `single_*` sets and the positional sets from the repo code. I've already confirmed that this code reproduces the 18 and 21 Oct logs exactly. Send me the corrected file and I'll compare every set. The old "manual" set can't be rebuilt.
- **The token-savings figures** I can't verify.

**Recommendation:** have every worker run `predict_all.py` rather than writing its own pick code, and accept a picks file only if `predict_all.py --check` passes on the last logged draw. That would have caught this on 24 Oct.

One thing to check on your side: `analysis/predict_all.py` (and `karana_tests.py`) changed on disk after my last commit, outside this session. If the worker edited `predict_all.py`, I'd re-run `--check 2026-10-21` before trusting it.

---

## 97. Question (2026-10-24 11:17)

> `predict_all.py` agrees with the picks file on every lead it can rebuild. Both `--check` runs passed, but I can't say whether the file changed on disk.
> 
> - **Checks:** `--check 2026-10-21` and `--check 2026-10-18` both passed with 0 mismatches against `forward_log.csv` (all variants logged for those dates).
> - **Comparison:** `predict_all.py 2026-10-24` against `picks_2026-10-24.md` gave 102 MATCH, 0 DIFF, 3 can't-rebuild. That covers every lead: both, chinese, vedic, manual_v2, `single_*`, positional, `ml_*` and `_upd`. The 3 are the old "manual" set (one per operator), which `predict_all.py` itself says can't be rebuilt.
> - **Your corrected sets:** lead1, lead2, lead6 and the S2 `_upd` sets for Magnum and Da Ma Cai match your numbers.
> - **What I couldn't confirm:** the report says nothing about whether `predict_all.py` or `karana_tests.py` changed on disk, so that part of your concern is still open. I also can't tell whether any of the picks file was itself generated by `predict_all.py`, in which case the match would partly be circular. The `--check` passes against the logged draws are the independent evidence.
> 
> The full table is in `work/4d-frozen-leads/predict_all_compare.md`. The wrong root-cause section in `root_cause.md` is still there; say if you want it replaced with "cause not recoverable". This is their reply

**Answer** (2026-10-24 11:17)

I can settle the on-disk question from here:

Their result checks out, and the open question about files changing on disk is closed.

**Nothing changed outside my commits.** Here, `git status` and `git diff` are clean, and the remote branch has no commits beyond mine. The "changed on disk" notices I passed on came from my own scripted edits to those files, not from someone else. That concern was a false alarm on my part.

**On their reply:**
- **The result is trustworthy.** `--check` passing on 18 and 21 Oct is independent evidence: it compares rebuilt picks against picks logged before those draws, so it can't be circular. The 102/102 match on 24 Oct then confirms their file equals the repo's output. Whether their file was itself made with `predict_all.py` doesn't matter now. Either way the numbers are the ones the repo produces.
- **The 3 rows it can't rebuild** are expected: the old "manual" set from before the 17 Oct fix.
- **`root_cause.md` should be replaced.** Its current text (same sets, different order) is wrong, so leaving it in would mislead whoever reads it next. Suggested wording:

> Cause not recoverable: the original script was overwritten. The 24 Oct lead1, lead2 and lead6 sets can't be produced by the repo's counting for any parameter value or source day, so the worker's own pick code was wrong, not the order. The S2 `_upd` sets used the frozen 17 Oct cutoff. Fix: picks come only from `analysis/predict_all.py`, and `--check` must pass on the last logged draw before a picks file is accepted.

So yes: tell them to replace it with that.

---

## 98. Question (2026-10-24 11:21)

> Because when I’m connecting this repo to other llm, that llm must understand each and every progress that you have and need to continue from where you have left, so that, it don’t have to redo the same analysis but to move forward in the research. So, do you confirm you have everything needed in the repo? Or is there anything missing that needs to be added?

**Answer** (2026-10-24 11:21)

Not yet. The code and results are all there, but a new model would still be missing a few things. I'll check what exactly.

---
