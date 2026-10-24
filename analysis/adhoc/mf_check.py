import sys, json, math, numpy as np
from collections import Counter
sys.path.insert(0, "analysis")
import astro_model as am, manual_formula as mf
data, codes, labels, rows, draws, year_of = am.load()
W = json.load(open("analysis/manual_formula.json"))["weights"]
pick_count, hit_count, prizes = Counter(), Counter(), Counter()
seq = []
for y in range(2018, int(year_of.max()) + 1):
    tab = mf.digit_tables(codes, rows, list(W), y)
    for (d, o), (win, pr) in sorted(draws.items()):
        if year_of[d] != y: continue
        picks = mf.top_numbers(mf.points(tab, W, codes, d), 5)
        seq.append((d, tuple(picks)))
        for n in picks: pick_count[n] += 1
        for p, n in pr:
            if n in picks: hit_count[n] += 1; prizes[p] += 1
print("distinct numbers ever picked:", len(pick_count))
print("most picked:", pick_count.most_common(8))
print("hits by number:", hit_count.most_common(10))
print("prizes:", dict(prizes))
# how often does the top-5 set change between consecutive draw dates?
ch = sum(1 for a, b in zip(seq, seq[1:]) if a[1] != b[1]); print("set changes:", ch, "of", len(seq) - 1)
# null: for each picked number, expected wins given how often it was picked (any number: 23/10000 per draw)
# fixed-random check: replace each distinct picked number by a random number, keep the same schedule
rng = np.random.default_rng(0)
allwin = {}
for (d, o), (win, pr) in draws.items():
    if year_of[d] >= 2018: allwin[(d, o)] = set(win)
keys = sorted(allwin)
sched = {}
i = 0
for y in range(2018, int(year_of.max()) + 1):
    tab = mf.digit_tables(codes, rows, list(W), y)
    for k in keys:
        if year_of[k[0]] == y: sched[k] = mf.top_numbers(mf.points(tab, W, codes, k[0]), 5)
real = sum(len(set(sched[k]) & allwin[k]) for k in keys)
sims = []
for _ in range(2000):
    m = {n: int(rng.integers(10000)) for n in pick_count}
    sims.append(sum(len({m[n] for n in sched[k]} & allwin[k]) for k in keys))
sims = np.array(sims)
print(f"real hits {real}; same schedule with random numbers swapped in: mean {sims.mean():.1f}, "
      f"95th pct {np.percentile(sims, 95):.0f}, P(sim >= real) = {np.mean(sims >= real):.3f}")
