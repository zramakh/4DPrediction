# Conversation log

The questions asked and the answers given while building this analysis (16-17 Oct 2026, times in UTC).
Tool calls and raw command output are left out; the scripts and result files in `analysis/` hold those.
A summary of the conclusions is in [analysis/FINDINGS.md](../analysis/FINDINGS.md).

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

## 34. Question (2026-10-17 07:27)

> [Request interrupted by user]

---

## 35. Question (2026-10-17 07:28)

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

## 36. Question (2026-10-17 07:37)

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

## 37. Question (2026-10-17 08:07)

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

## 38. Question (2026-10-17 08:11)

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

## 39. Question (2026-10-17 09:19)

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

## 40. Question (2026-10-17 09:21)

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

## 41. Question (2026-10-17 09:28)

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

## 42. Question (2026-10-17 09:31)

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

## 43. Question (2026-10-17 09:34)

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

## 44. Question (2026-10-17 09:36)

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

## 45. Question (2026-10-17 10:02)

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

## 46. Question (2026-10-17 12:23)

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

## 47. Question (2026-10-17 13:18)

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

## 48. Question (2026-10-17 13:25)

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

## 49. Question (2026-10-17 13:26)

> what about all our conversations? can you add that too?
