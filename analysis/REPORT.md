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

## 3. Predictive models (walk-forward backtest)

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
