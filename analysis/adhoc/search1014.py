import sys, math, itertools, numpy as np
sys.path.insert(0, "analysis"); sys.path.insert(0, "/tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad")
import astro_model as am
from res_1014 import RES
BIG = {"1st": 2500, "2nd": 1000, "3rd": 500, "Special": 180, "Consolation": 60}
data, codes, labels, rows, draws, year_of = am.load()
am._YEAR = year_of
d14 = int(rows["date"].max())
m = rows["date"] < d14
c = am.Counts(am.VEDIC + am.CHINESE, codes)
c.add(rows["date"][m], rows["op_ix"][m], rows["num"][m])
R = RES["2026-10-14"]
win = {op: {int(n): p for p, v in R[op].items() for n in v.split()} for op in am.OPS}
grp = lambda n: "".join(sorted(f"{n:04d}"))
wgrp = {op: {grp(n) for n in win[op]} for op in am.OPS}
def score(picks_by_op):
    st = ib = pay = 0
    for op, picks in picks_by_op.items():
        for n in picks:
            if n in win[op]: st += 1; pay += BIG[win[op][n]]
            elif grp(n) in wgrp[op]: ib += 1
    return st, ib, pay
res = []
for f in am.VEDIC + am.CHINESE:
    for kind in am.KINDS:
        picks = {}
        for o, op in enumerate(am.OPS):
            t = c.term(f, int(codes[f][d14]), kind, o)
            picks[op] = np.argsort(-(t + np.arange(10000) * 1e-12))[:10].tolist()
        st, ib, pay = score(picks)
        res.append((st, ib, pay, f, kind, picks))
rng = np.random.default_rng(1014)
rand = [score({op: rng.choice(10000, 10, replace=False).tolist() for op in am.OPS}) for _ in range(len(res))]
def dist(xs, i): return {k: sum(1 for x in xs if x[i] == k) for k in sorted({x[i] for x in xs})}
print(f"{len(res)} formulas, 30 picks each, 14 Oct 2026")
print("  straight hits  formulas:", dist(res, 0), "  random:", dist(rand, 0))
print("  i-Box hits     formulas:", dist(res, 1), "  random:", dist(rand, 1))
res.sort(key=lambda x: (-x[0], -x[2], -x[1]))
print("best formulas on 14 Oct:")
for st, ib, pay, f, kind, picks in res[:8]:
    hits = [f"{op} {n:04d} ({win[op][n]})" for op, ps in picks.items() for n in ps if n in win[op]]
    print(f"  {f:<20} {kind:<7} straight {st}  i-Box {ib}  Big RM{pay}/RM30  {hits}")
best = res[0]
import json; json.dump({"best": [best[3], best[4]], "picks": {op: [f"{n:04d}" for n in ps] for op, ps in best[5].items()}},
                       open("/tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad/best1014.json", "w"))
# test the 14-Oct winner on every draw 2018-2026 (walk-forward, draw by draw)
out, _ = am.forward_test("best_on_14oct", [(best[3], best[4], 1.0)], codes, rows, draws)
a = out["All"]
print(f"\nwinner '{best[3]} / {best[4]}' on 2018-2026 ({a['draws']} draws): top 10 {a['top10']['hits']} vs "
      f"{a['top10']['expected']} expected (x{a['top10']['lift']}, z={a['top10']['z']:+.1f}); Big top10 RM{a['big_return_top10']['per_RM1']} per RM1")
for st, ib, pay, f, kind, picks in res[1:4]:
    o2, _ = am.forward_test("x", [(f, kind, 1.0)], codes, rows, draws)
    a = o2["All"]
    print(f"runner-up '{f} / {kind}' on 2018-2026: top 10 x{a['top10']['lift']} (z={a['top10']['z']:+.1f}); Big RM{a['big_return_top10']['per_RM1']}")
