# Inline analysis code run during the session

Every Python snippet run inline (heredocs) while building the analysis, in order, with its UTC time.
Most of the work lives in the scripts in `analysis/`; these are the one-off checks, scorings and loggings.
Pick generation for any date is in `analysis/predict_all.py`; do not copy snippets from here for that.

## 1. 2026-10-16 16:32 — Rewrite statistics section with sparse vectorised code

```bash
cd /home/user/4DPrediction/analysis; python3 - <<'EOF'
import re
s = open("conditional_numbers.py").read()
start = s.index("# ------------------------------------------------------------------ statistics")
end = s.index("def main():")
new = '''# ------------------------------------------------------------------ statistics
LGAMMA = np.array([math.lgamma(j + 1) for j in range(2000)])
TAIL = np.arange(80)


def poisson_sf(k, lam):
    """P(X >= k) for X ~ Poisson(lam), vectorised and accurate in the far tail."""
    k, lam = np.atleast_1d(k).astype(int), np.atleast_1d(lam).astype(float)
    j = k[:, None] + TAIL[None, :]
    p = np.exp(j * np.log(lam)[:, None] - lam[:, None] - LGAMMA[j]).sum(1)
    return np.where(k <= 0, 1.0, np.minimum(p, 1.0))


def best_of(p, n):
    """Chance that the best of n independent tries is at least this extreme."""
    p = np.minimum(np.asarray(p, float), 1 - 1e-16)
    return -np.expm1(n * np.log1p(-p))


def cell_codes(sel, rows_date, codes, prize, fset):
    """Cell index of each selected row for a factor set, and the size of each factor."""
    cell = np.zeros(sel.sum(), dtype=np.int64)
    sizes = []
    for f in fset:
        col = prize[sel] if f == "prize" else codes[f][rows_date[sel]]
        k = 3 if f == "prize" else int(codes[f].max()) + 1
        cell = cell * k + col
        sizes.append(k)
    return cell, sizes


def decode(c, fset, sizes, labels):
    parts = []
    for f, k in zip(reversed(fset), reversed(sizes)):
        parts.append(f"{f}={labels[f][c % k]}")
        c //= k
    return " & ".join(reversed(parts))


def sparse_counts(cell, unit_ix, n_units):
    """Non-zero (cell, unit) counts, sorted by cell."""
    key, cnt = np.unique(cell * n_units + unit_ix, return_counts=True)
    return key // n_units, key % n_units, cnt


def scan(cell, unit_ix, n_units, share, overall):
    """Unevenness statistic and the most over-represented unit of every cell.

    Unevenness is the chi-square of the (cell x unit) table against
    expected = cell size x scope-wide frequency of the unit, so a unit that is
    common everywhere (e.g. the Magnum digit bias) does not count; only
    dependence on the cell does. Computed from non-zero entries:
    sum (c-e)^2/e = sum c^2/e - N.
    """
    c, u, cnt = sparse_counts(cell, unit_ix, n_units)
    n_cell = np.bincount(cell)
    chi = float((cnt ** 2 / (n_cell[c] * overall[u])).sum() - len(cell))
    exp = n_cell[c] * share[u]
    z = (cnt - exp) / np.sqrt(exp)
    order = np.lexsort((-z, c))               # by cell, most over-represented first
    first = order[np.r_[True, c[order][1:] != c[order][:-1]]]
    p = best_of(poisson_sf(cnt[first], exp[first]), n_units)
    return chi, c[first], u[first], cnt[first], exp[first], p


def replicate(cell, unit_ix, n_units, share, train, test):
    """Learn the TOP_K most over-represented units of each cell on `train`, then
    count their wins in the same cell on `test` against the random expectation."""
    c, u, cnt = sparse_counts(cell[train], unit_ix[train], n_units)
    score = cnt / share[u] + RNG.random(len(cnt)) * 1e-3   # random tie-break
    order = np.lexsort((-score, c))
    c, u = c[order], u[order]
    start = np.r_[0, np.flatnonzero(c[1:] != c[:-1]) + 1]
    rank = np.arange(len(c)) - np.repeat(start, np.diff(np.r_[start, len(c)]))
    keep = rank < TOP_K
    c, u = c[keep], u[keep]
    te_cell, te_unit = cell[test], unit_ix[test]
    n_te = np.bincount(te_cell, minlength=cell.max() + 1)
    tk, tc = np.unique(te_cell * n_units + te_unit, return_counts=True)
    pos = np.searchsorted(tk, c * n_units + u)
    pos = np.minimum(pos, len(tk) - 1)
    hits = int(np.where(tk[pos] == c * n_units + u, tc[pos], 0).sum())
    exp = float((n_te[c] * share[u]).sum())
    if exp == 0:
        return None
    return {"hits": hits, "expected": round(exp, 1), "lift": round(hits / exp, 3),
            "z": round((hits - exp) / math.sqrt(exp), 2)}


# ------------------------------------------------------------------ analysis
def scopes_of(data):
    s = {op: data["op"] == op for op in OPERATORS}
    s["All operators"] = np.ones(len(data["num"]), bool)
    return s


def analyse(data, codes, labels, n_dates):
    fsets = [(f,) for f in FACTORS] + list(itertools.combinations(FACTORS, 2))
    perms = [RNG.permutation(n_dates) for _ in range(N_SHUFFLES)]
    results = {"settings": {"split_year": SPLIT_YEAR, "top_k": TOP_K, "shuffles": N_SHUFFLES,
                            "factors": FACTORS, "factor_sets": len(fsets)}, "scopes": {}}
    assoc = {u: [] for u in UNITS}
    null_best = {u: np.ones(N_SHUFFLES) for u in UNITS}
    total_cells = {u: 0 for u in UNITS}
    for scope, sel in scopes_of(data).items():
        t = time.time()
        num, years = data["num"][sel], data["year"][sel]
        splits = {"before_vs_after_2012": (years < SPLIT_YEAR, years >= SPLIT_YEAR),
                  "even_vs_odd_years": (years % 2 == 0, years % 2 == 1)}
        sr = {}
        for fset in fsets:
            cell, sizes = cell_codes(sel, data["date"], codes, data["prize"], fset)
            entry = {}
            for u, (n_units, share, fmt) in UNITS.items():
                ux = num if u == "number" else GROUP_OF[num]
                overall = np.bincount(ux, minlength=n_units) / len(ux)
                chi, cc, cu, ccnt, cexp, cp = scan(cell, ux, n_units, share, overall)
                total_cells[u] += len(cc)
                for i in np.argsort(cp)[:3]:
                    assoc[u].append({"scope": scope, "factors": " x ".join(fset),
                                     "cell": decode(int(cc[i]), list(fset), sizes, labels),
                                     "value": fmt(int(cu[i])), "wins": int(ccnt[i]),
                                     "expected": round(float(cexp[i]), 2), "p_best_in_cell": float(cp[i])})
                null_chi = []
                if fset != ("prize",):  # prize is per row, shuffling dates does not move it
                    for s, perm in enumerate(perms):
                        pcell, _ = cell_codes(sel, perm[data["date"]], codes, data["prize"], fset)
                        chi0, *_, p0 = scan(pcell, ux, n_units, share, overall)
                        null_chi.append(chi0)
                        null_best[u][s] = min(null_best[u][s], p0.min())
                z = None
                if null_chi:
                    z = round(float((chi - np.mean(null_chi)) / np.std(null_chi, ddof=1)), 2)
                entry[u] = {"cells": len(cc), "unevenness_z_vs_shuffled": z,
                            "replication": {k: replicate(cell, ux, n_units, share, tr, te)
                                            for k, (tr, te) in splits.items()}}
            sr[" x ".join(fset)] = entry
        results["scopes"][scope] = sr
        print(f"{scope}: {len(fsets)} parameter sets scanned in {time.time() - t:.0f}s", flush=True)

    for u in UNITS:
        a = sorted(assoc[u], key=lambda x: x["p_best_in_cell"])
        for x in a:
            x["p_all_cells"] = float(best_of(x["p_best_in_cell"], total_cells[u]))
        results[f"top_{u}_associations"] = a[:25]
        results[f"shuffle_{u}"] = {
            "real_best_p_in_cell": a[0]["p_best_in_cell"],
            "shuffled_best_p_in_cell": sorted(float(v) for v in null_best[u]),
            "share_of_shuffles_at_least_as_extreme": float(np.mean(null_best[u] <= a[0]["p_best_in_cell"])),
            "cells_searched": total_cells[u]}
    return results


def discover_then_test(data, codes, labels):
    """Find the strongest associations using draws before 2012 only, then see what they did after."""
    fsets = [(f,) for f in FACTORS if f != "era_5yr"] + \\
        [p for p in itertools.combinations(FACTORS, 2) if "era_5yr" not in p]
    out = {}
    for u, (n_units, share, fmt) in UNITS.items():
        found = []
        for scope, sel in scopes_of(data).items():
            num, years = data["num"][sel], data["year"][sel]
            ux = num if u == "number" else GROUP_OF[num]
            tr, te = years < SPLIT_YEAR, years >= SPLIT_YEAR
            for fset in fsets:
                cell, sizes = cell_codes(sel, data["date"], codes, data["prize"], fset)
                _, cc, cu, ccnt, cexp, _ = scan(cell[tr], ux[tr], n_units, share, np.full(n_units, 1 / n_units))
                p = poisson_sf(ccnt, cexp)
                n_te = np.bincount(cell[te], minlength=cell.max() + 1)
                tk, tc = np.unique(cell[te] * n_units + ux[te], return_counts=True)
                key = cc * n_units + cu
                pos = np.minimum(np.searchsorted(tk, key), len(tk) - 1)
                after = np.where(tk[pos] == key, tc[pos], 0)
                for i in np.flatnonzero(n_te[cc] > 0):
                    found.append((float(p[i]), scope, " x ".join(fset), decode(int(cc[i]), list(fset), sizes, labels),
                                  fmt(int(cu[i])), int(ccnt[i]), float(cexp[i]), int(after[i]),
                                  float(n_te[cc[i]] * share[cu[i]])))
        found.sort(key=lambda x: x[0])
        top = found[:200]
        hits, exp = sum(x[7] for x in top), sum(x[8] for x in top)
        out[u] = {
            "summary_top200": {"wins_from_2012": hits, "expected_if_random": round(exp, 1),
                               "lift": round(hits / exp, 3), "z": round((hits - exp) / math.sqrt(exp), 2)},
            "top20": [{"scope": x[1], "factors": x[2], "cell": x[3], "value": x[4],
                       "wins_before_2012": x[5], "expected_before": round(x[6], 2),
                       "wins_from_2012": x[7], "expected_from_2012": round(x[8], 2)} for x in found[:20]],
        }
    return out


'''
s = s[:start] + new + s[end:]
s = s.replace('results["discover_before_2012_test_after"] = discover_then_test(data, codes, labels, n_dates)',
              'results["discover_before_2012_test_after"] = discover_then_test(data, codes, labels)')
open("conditional_numbers.py","w").write(s)
EOF
grep -n "later_check\|_key" conditional_numbers.py
```

## 2. 2026-10-16 16:37 — Add report section, commit and push

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
s = open("analysis/REPORT.md").read()
sec = '''## 6. Specific numbers under specific conditions (single and paired parameters)

`python3 analysis/conditional_numbers.py` (~5 min). Full output in
`analysis/conditional_results.json`.

This asks the question directly: is there a condition, or a combination of two
conditions, under which a particular number (e.g. 7345) or permutation group
(e.g. any order of 4458, i.e. an i-Box) wins unusually often? 13 parameters:
weekday, month, day of month, 5-year era, moon phase, moon sign, sun sign,
Chinese lunar month, lunar day, Chinese zodiac year, nakshatra, tithi and prize
tier (top 3 / special / consolation). All 13 singles and all 78 pairs were
scanned for each operator and for all operators pooled: 364 parameter sets,
66,656 cells (e.g. "Magnum, day of month = 2 & tithi = 16"), and 10,000
numbers plus 715 permutation groups in every cell.

**The strongest associations look striking but are what chance produces.**

| Operator | Condition | Number | Wins | Expected |
|---|---|---|---|---|
| Magnum | day of month 2 & tithi 16 | 7345 | 4 | 0.02 |
| Sports Toto | Horse year & tithi 3 | 7380 | 4 | 0.03 |
| Da Ma Cai | day of month 22 & Horse year | 6174 | 4 | 0.03 |
| Sports Toto | Sun in Capricorn & Pig year | 9543 | 5 | 0.09 |
| Magnum | October & lunar day 9 | 4458 (any order) | 8 | 0.47 |
| Magnum | lunar month 9 & lunar day 9 | 4458 (any order) | 8 | 0.50 |
| Da Ma Cai | first-quarter moon & Snake year | 0456 (any order) | 18 | 3.75 |

Each looks like a 100–200× effect, but each is the best of 10,000 numbers in
its cell and its cell is one of 66,656. Corrected for that search, every one is
at p ≈ 0.84–1.00. As a direct check, the whole search was rerun 20 times
with the draw dates shuffled (each draw keeps its numbers but gets another
date's parameters, so no real link can exist). The shuffled data produced
equally or more extreme "best associations" 65% of the time for single numbers
and 50% for permutation groups.

**No parameter set makes the winners cluster.** For each set, the overall
unevenness of the number × cell table (beyond each number's overall frequency)
was compared with the shuffled-date runs. Sports Toto, Da Ma Cai and the pooled
data had no set above z = 3 for single numbers (median z ≈ 0). Magnum had a
few (moon sign × prize 3.4; month × moon sign 3.1; and, for permutation groups,
sets involving the 5-year era). The era sets are the known Magnum equipment
drift (section 2). The others did not replicate (next point).

**Nothing replicates.** The top 10 numbers of every cell were learned on one
part of the data and checked in the same cell on the other part:

| Test | Single numbers | Permutation groups |
|---|---|---|
| Learn before 2012, test 2012 onward (all sets, all operators) | 1.00–1.05× random | 0.99–1.03× |
| Learn on even years, test on odd years | 1.00–1.01× | 1.00–1.01× |
| Top 200 associations found before 2012, from 2012 onward | 20 wins vs 15.2 expected (z = 1.2) | 139 vs 145.7 (z = −0.6) |

Almost every headline association found before 2012 scored **zero** wins in
the same condition afterwards (e.g. Sports Toto 9586 on the 17th under a waning
gibbous moon: 4 wins before 2012, 0 after; Magnum 6678 in any order on the 22nd
in Rat years: 6 before, 0 after). Of 1,456 replication tests, 7 had z > 3
(about 2 expected). None held in both splits.

**Conclusion:** no single parameter or pair of parameters has a number or
i-Box group that reliably wins more often. The "hot under condition X"
numbers are selection effects from searching a very large space.

'''
s = s.replace("## Conclusion\n", sec + "## Conclusion\n")
open("analysis/REPORT.md", "w").write(s)
EOF
git add analysis && git commit -q -m "Report per-number conditional analysis: no single or paired parameter favours specific numbers

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q -u origin claude/4d-results-scraper-9ptbd5 && git log --oneline -1
```

## 3. 2026-10-16 17:10 — Look for duplicated or near-duplicated draws

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
import csv
from collections import defaultdict
for stem in ["magnum","sportstoto","damacai"]:
    by=defaultdict(list)
    for r in csv.DictReader(open(f"data/{stem}.csv")): by[r["date"]].append(r["4d_number"])
    ds=sorted(by); big=[]
    for lag in (1,2,3):
        for a,b in zip(ds,ds[lag:]):
            ov=len(set(by[a])&set(by[b]))
            if ov>=5: big.append((lag,a,b,ov,len(by[a]),len(by[b])))
    # distribution of overlap lag1
    from collections import Counter
    c=Counter(len(set(by[a])&set(by[b])) for a,b in zip(ds,ds[1:]))
    print(stem, len(ds), "lag1 overlap dist", sorted(c.items()), "n big", len(big)); print(big[:15])
EOF
```

## 4. 2026-10-16 17:11 — Find any pair of draws with large number overlap

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
import csv, numpy as np
from collections import defaultdict, Counter
for stem in ["magnum","sportstoto","damacai"]:
    by=defaultdict(set)
    for r in csv.DictReader(open(f"data/{stem}.csv")): by[r["date"]].add(int(r["4d_number"]))
    ds=sorted(by); M=np.zeros((len(ds),10000),np.float32)
    for i,d in enumerate(ds): M[i,list(by[d])]=1
    O=M@M.T; np.fill_diagonal(O,0)
    i,j=np.where(np.triu(O)>=4)
    print(stem, "pairs with >=4 shared:", len(i), Counter(O[np.triu(O)>0].astype(int).ravel()).most_common())
    for a,b in list(zip(i,j))[:25]: print("  ",ds[a],ds[b],int(O[a,b]))
EOF
```

## 5. 2026-10-16 17:11 — Check in-draw repeats and draw sizes by year

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
import csv
from collections import defaultdict, Counter
for stem in ["magnum","sportstoto","damacai"]:
    by=defaultdict(list)
    for r in csv.DictReader(open(f"data/{stem}.csv")): by[r["date"]].append(r["4d_number"])
    dup=Counter(); size=defaultdict(Counter)
    for d,v in by.items():
        if len(v)!=len(set(v)): dup[d[:4]]+=1
        size[d[:4]][len(v)]+=1
    print(stem,"draws with an in-draw repeat by year:",dict(sorted(dup.items())))
    print("  sizes by year (sample):",{y:dict(size[y]) for y in sorted(size)[::4]})
EOF
```

## 6. 2026-10-16 17:11 — Diagnose the biggest contributors to unevenness

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
import sys; sys.path.insert(0,'analysis')
import conditional_extended as ce, conditional_numbers as cn, numpy as np
from collections import Counter
d,c,l,f,n=ce.load()
import csv
dates=sorted({r["date"] for s in cn.OPERATORS.values() for r in csv.DictReader(open(f"data/{s}.csv"))})
for scope,fs in [("Da Ma Cai",("year_animal","kp_asc_number")),("Sports Toto",("saturn_nakshatra","kp_sun_number"))]:
    sel=d["op"]==scope
    cell,sizes=cn.cell_codes(sel,d["date"],c,d["prize"],fs)
    num=d["num"][sel]; dt_=d["date"][sel]
    ov=np.bincount(num,minlength=10000)/len(num)
    cc,uu,cnt=cn.sparse_counts(cell,num,10000)
    ncell=np.bincount(cell)
    contrib=cnt**2/(ncell[cc]*ov[uu])
    print(scope,fs,"total chi",contrib.sum()-len(cell),"cells",len(set(cell)),"rows/cell median",np.median(ncell[ncell>0]))
    for k in np.argsort(-contrib)[:8]:
        m=(cell==cc[k])&(num==uu[k])
        print("  cell",cn.decode(int(cc[k]),list(fs),sizes,l),"num",uu[k],"count",cnt[k],"cell rows",ncell[cc[k]],"overall count",int(ov[uu[k]]*len(num)),
              "contrib",round(contrib[k]),"dates",sorted({dates[i] for i in dt_[m]}))
EOF
```

## 7. 2026-10-16 17:12 — Patch both scripts for once-per-draw counting and between-draw statistic

```bash
cd /home/user/4DPrediction/analysis; python3 - <<'EOF'
s = open("conditional_numbers.py").read()
old_scan = s[s.index("def scan(cell, unit_ix, n_units, share, overall):"):s.index("    exp = n_cell[c] * share[u]\n")]
new_scan = '''def once_per_draw(date_ix, unit_ix, n_units):
    """Mask keeping each number (or permutation group) once per draw.

    Published draws occasionally repeat a number across prize slots; counted
    twice, a single draw would look like a number "recurring" under its
    conditions.
    """
    _, first = np.unique(date_ix * n_units + unit_ix, return_index=True)
    keep = np.zeros(len(unit_ix), bool)
    keep[first] = True
    return keep


def scan(cell, unit_ix, n_units, share):
    """Unevenness statistic and the most over-represented unit of every cell.

    Rows must already be once-per-draw (see once_per_draw). Unevenness is
    sum over cells and units of c(c-1) / (cell size x share): the number of
    times the same number won in two different draws of the same cell,
    weighted by how unlikely that is. Comparing it with shuffled dates (same
    draws, parameters reassigned) shows whether numbers cluster under
    particular conditions. Overall number/digit bias is the same in the
    shuffles, so it cancels out.
    """
    c, u, cnt = sparse_counts(cell, unit_ix, n_units)
    n_cell = np.bincount(cell)
    chi = float((cnt * (cnt - 1) / (n_cell[c] * share[u])).sum())
'''
s = s.replace(old_scan, new_scan)
# analyse(): dedupe per unit
s = s.replace('''                ux = num if u == "number" else GROUP_OF[num]
                overall = np.bincount(ux, minlength=n_units) / len(ux)
                chi, cc, cu, ccnt, cexp, cp = scan(cell, ux, n_units, share, overall)''',
'''                ux = num if u == "number" else GROUP_OF[num]
                k1 = once_per_draw(data["date"][sel], ux, n_units)
                ux, ucell = ux[k1], cell[k1]
                chi, cc, cu, ccnt, cexp, cp = scan(ucell, ux, n_units, share)''')
s = s.replace('''                        pcell, _ = cell_codes(sel, perm[data["date"]], codes, data["prize"], fset)
                        chi0, *_, p0 = scan(pcell, ux, n_units, share, overall)''',
'''                        pcell, _ = cell_codes(sel, perm[data["date"]], codes, data["prize"], fset)
                        chi0, *_, p0 = scan(pcell[k1], ux, n_units, share)''')
s = s.replace('''                            "replication": {k: replicate(cell, ux, n_units, share, tr, te)''',
'''                            "replication": {k: replicate(ucell, ux, n_units, share, tr[k1], te[k1])''')
# discover_then_test
s = s.replace('''            ux = num if u == "number" else GROUP_OF[num]
            tr, te = years < SPLIT_YEAR, years >= SPLIT_YEAR
            for fset in fsets:
                cell, sizes = cell_codes(sel, data["date"], codes, data["prize"], fset)
                _, cc, cu, ccnt, cexp, _ = scan(cell[tr], ux[tr], n_units, share, np.full(n_units, 1 / n_units))''',
'''            ux = num if u == "number" else GROUP_OF[num]
            k1 = once_per_draw(data["date"][sel], ux, n_units)
            ux, years = ux[k1], years[k1]
            tr, te = years < SPLIT_YEAR, years >= SPLIT_YEAR
            for fset in fsets:
                cell, sizes = cell_codes(sel, data["date"], codes, data["prize"], fset)
                cell = cell[k1]
                _, cc, cu, ccnt, cexp, _ = scan(cell[tr], ux[tr], n_units, share)''')
assert "overall" not in s.split("def scan")[1].split("def replicate")[0] or True
open("conditional_numbers.py","w").write(s)

e = open("conditional_extended.py").read()
e = e.replace('''            ux = num if u == "number" else cn.GROUP_OF[num]
            overall = np.bincount(ux, minlength=n_units) / len(ux)
            chi, cc, cu, ccnt, cexp, cp = cn.scan(cell, ux, n_units, share, overall)''',
'''            ux = num if u == "number" else cn.GROUP_OF[num]
            k1 = cn.once_per_draw(data["date"][sel], ux, n_units)
            ux, ucell, uyears = ux[k1], cell[k1], years[k1]
            chi, cc, cu, ccnt, cexp, cp = cn.scan(ucell, ux, n_units, share)''')
e = e.replace('''                    c0, *_, p0 = cn.scan(pc, ux, n_units, share, overall)''',
'''                    c0, *_, p0 = cn.scan(pc[k1], ux, n_units, share)''')
e = e.replace('''                zc = round(float((cn.scan(ccal, ux, n_units, share, overall)[0] - m) / sd), 2)''',
'''                zc = round(float((cn.scan(ccal[k1], ux, n_units, share)[0] - m) / sd), 2)''')
e = e.replace('''                        "replication": {k: cn.replicate(cell, ux, n_units, share, tr, te)
                                        for k, (tr, te) in splits.items()}}''',
'''                        "replication": {k: cn.replicate(ucell, ux, n_units, share, tr[k1], te[k1])
                                        for k, (tr, te) in splits.items()}}''')
e = e.replace('''                tr, te = splits["before_vs_after_2012"]
                _, dc, du, dcnt, dexp, _ = cn.scan(cell[tr], ux[tr], n_units, share, np.full(n_units, 1 / n_units))
                n_te = np.bincount(cell[te], minlength=cell.max() + 1)''',
'''                tr, te = uyears < SPLIT_YEAR, uyears >= SPLIT_YEAR
                _, dc, du, dcnt, dexp, _ = cn.scan(ucell[tr], ux[tr], n_units, share)
                n_te = np.bincount(ucell[te], minlength=ucell.max() + 1)''')
e = e.replace('''                tk, tcount = np.unique(cell[te] * n_units + ux[te], return_counts=True)''',
'''                tk, tcount = np.unique(ucell[te] * n_units + ux[te], return_counts=True)''')
open("conditional_extended.py","w").write(e)
EOF
grep -n "overall" conditional_numbers.py conditional_extended.py
```

## 8. 2026-10-16 17:13 — Exclude the duplicated Magnum draw

```bash
cd /home/user/4DPrediction/analysis; python3 - <<'EOF'
s=open("conditional_numbers.py").read()
s=s.replace('''RNG = np.random.default_rng(20261016)''','''RNG = np.random.default_rng(20261016)
# 2015-01-09 repeats 22 of the 23 numbers of 2015-01-07 on the source site; a copy, not a draw
EXCLUDE = {("Magnum", "2015-01-09")}''')
s=s.replace('''            for r in csv.DictReader(f):
                rows.append((op, r["date"], r["prize"], int(r["4d_number"])))
    dates = sorted({r[1] for r in rows})
    t = time.time()
    ctx = [date_context(d) for d in dates]''','''            for r in csv.DictReader(f):
                if (op, r["date"]) not in EXCLUDE:
                    rows.append((op, r["date"], r["prize"], int(r["4d_number"])))
    dates = sorted({r[1] for r in rows})
    t = time.time()
    ctx = [date_context(d) for d in dates]''')
open("conditional_numbers.py","w").write(s)
e=open("conditional_extended.py").read()
e=e.replace('''            for r in csv.DictReader(f):
                rows.append((op, r["date"], r["prize"], int(r["4d_number"])))''','''            for r in csv.DictReader(f):
                if (op, r["date"]) not in cn.EXCLUDE:
                    rows.append((op, r["date"], r["prize"], int(r["4d_number"])))''')
open("conditional_extended.py","w").write(e)
EOF
grep -n "EXCLUDE" conditional_numbers.py conditional_extended.py
```

## 9. 2026-10-16 17:19 — Retest with shuffles stratified by operator set

```bash
cd /home/user/4DPrediction; S=/tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad; python3 - <<'EOF'
import re
p="/tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad/confound.py"
s=open(p).read()
s=s.replace('rng=np.random.default_rng(5); perms=[rng.permutation(n) for _ in range(20)]','''rng=np.random.default_rng(5)
opset=np.zeros(n,int)
for b,op in enumerate(cn.OPERATORS): opset[np.unique(d["date"][d["op"]==op])]|=1<<b
def strat_perm():
    p=np.arange(n)
    for v in np.unique(opset):
        ix=np.flatnonzero(opset==v); p[ix]=rng.permutation(ix)
    return p
import collections; print(collections.Counter(opset))
perms=[strat_perm() for _ in range(20)]''')
open(p,"w").write(s)
EOF
python3 $S/confound.py
```

## 10. 2026-10-16 17:20 — Stop run and switch to stratified shuffles

```bash
pkill -f conditional_extended.py; sleep 1; cd /home/user/4DPrediction/analysis; python3 - <<'EOF'
s=open("conditional_numbers.py").read()
s=s.replace('''# ------------------------------------------------------------------ analysis
def scopes_of(data):''','''# ------------------------------------------------------------------ analysis
def stratified_perms(data, n_dates, k, rng):
    """k shuffles of the draw dates that only swap dates on which the same set
    of operators drew. A plain shuffle would move e.g. a Wednesday with three
    operators' results onto a weekday that really only has one operator's
    special draws, changing the size of the cells and faking clustering."""
    opset = np.zeros(n_dates, int)
    for b, op in enumerate(OPERATORS):
        opset[np.unique(data["date"][data["op"] == op])] |= 1 << b
    out = []
    for _ in range(k):
        p = np.arange(n_dates)
        for v in np.unique(opset):
            ix = np.flatnonzero(opset == v)
            p[ix] = rng.permutation(ix)
        out.append(p)
    return out


def scopes_of(data):''')
s=s.replace("    perms = [RNG.permutation(n_dates) for _ in range(N_SHUFFLES)]\n","    perms = stratified_perms(data, n_dates, N_SHUFFLES, RNG)\n")
s=s.replace("""2. Is any of this beyond chance? The same search is repeated with the draw
   dates shuffled (each draw keeps its numbers but gets another date's
   parameters).""","""2. Is any of this beyond chance? The same search is repeated with the draw
   dates shuffled (each draw keeps its numbers but gets another date's
   parameters; dates are only swapped with dates on which the same operators
   drew).""")
open("conditional_numbers.py","w").write(s)
e=open("conditional_extended.py").read()
old='''    G.update(data=data, codes=codes, labels=labels,
             perms=[rng.permutation(n_dates) for _ in range(N_SHUFFLES)], calib=rng.permutation(n_dates))'''
assert old in e
e=e.replace(old,'''    perms = cn.stratified_perms(data, n_dates, N_SHUFFLES + 1, rng)
    G.update(data=data, codes=codes, labels=labels, perms=perms[:-1], calib=perms[-1])''')
open("conditional_extended.py","w").write(e)
EOF
grep -n "stratified_perms" conditional_numbers.py conditional_extended.py
```

## 11. 2026-10-16 17:20 — Apply stratified shuffle patch

```bash
cd /home/user/4DPrediction/analysis; python3 - <<'EOF'
s=open("conditional_numbers.py").read()
s=s.replace('''# ------------------------------------------------------------------ analysis
def scopes_of(data):''','''# ------------------------------------------------------------------ analysis
def stratified_perms(data, n_dates, k, rng):
    """k shuffles of the draw dates that only swap dates on which the same set
    of operators drew. A plain shuffle would move e.g. a Wednesday with three
    operators' results onto a weekday that really only has one operator's
    special draws, changing the size of the cells and faking clustering."""
    opset = np.zeros(n_dates, int)
    for b, op in enumerate(OPERATORS):
        opset[np.unique(data["date"][data["op"] == op])] |= 1 << b
    out = []
    for _ in range(k):
        p = np.arange(n_dates)
        for v in np.unique(opset):
            ix = np.flatnonzero(opset == v)
            p[ix] = rng.permutation(ix)
        out.append(p)
    return out


def scopes_of(data):''')
s=s.replace("    perms = [RNG.permutation(n_dates) for _ in range(N_SHUFFLES)]\n","    perms = stratified_perms(data, n_dates, N_SHUFFLES, RNG)\n")
s=s.replace("""   dates shuffled (each draw keeps its numbers but gets another date's
   parameters).""","""   dates shuffled (each draw keeps its numbers but gets another date's
   parameters; dates are only swapped with dates on which the same operators
   drew).""")
open("conditional_numbers.py","w").write(s)
e=open("conditional_extended.py").read()
old='''    G.update(data=data, codes=codes, labels=labels,
             perms=[rng.permutation(n_dates) for _ in range(N_SHUFFLES)], calib=rng.permutation(n_dates))'''
assert old in e
e=e.replace(old,'''    perms = cn.stratified_perms(data, n_dates, N_SHUFFLES + 1, rng)
    G.update(data=data, codes=codes, labels=labels, perms=perms[:-1], calib=perms[-1])''')
open("conditional_extended.py","w").write(e)
EOF
grep -c "stratified_perms" conditional_numbers.py conditional_extended.py
```

## 12. 2026-10-16 17:53 — Inspect which discoveries scored after 2012

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
import json
from collections import Counter
r=json.load(open("analysis/conditional_extended_results.json"))
d=r["discover_before_2012_number"]
print(d["summary_top200"])
# need full list: only top30 saved. Use top30
for x in d["top30"][:30]:
    if x["wins_from_2012"]>0: print(x["scope"],x["cell"],x["value"],x["wins_before_2012"],x["expected_before"],x["wins_from_2012"],round(x["expected_from_2012"],2))
EOF
```

## 13. 2026-10-16 18:07 — Fix and rerun checks

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
p="analysis/conditional_checks.py"; s=open(p).read()
s=s.replace("z = [(r[3] - r[4]) / math.sqrt(r[4]) for r in rows]","z = [(r[3] - r[4]) / math.sqrt(r[4]) for r in rows if r[4] > 0]")
s=s.replace("zn = [(r[5][0] - r[6][0]) / math.sqrt(r[6][0]) for r in rows]","zn = [(r[5][0] - r[6][0]) / math.sqrt(r[6][0]) for r in rows if r[6][0] > 0]")
open(p,"w").write(s)
EOF
python3 analysis/conditional_checks.py > /tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad/checks.log 2>&1; grep -v chunks /tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad/checks.log
```

## 14. 2026-10-16 18:21 — Check overall frequency of 1024 before and after 2012

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
import csv, math
from collections import Counter
pre,post=Counter(),Counter(); npre=npost=0
for s in ["magnum","sportstoto","damacai"]:
    seen=set()
    for r in csv.DictReader(open(f"data/{s}.csv")):
        k=(r["date"],r["4d_number"])
        if k in seen: continue
        seen.add(k)
        if r["date"]<"2012": pre[r["4d_number"]]+=1; npre+=1
        else: post[r["4d_number"]]+=1; npost+=1
for n in ["1024","1288"]:
    print(n,"pre",pre[n],"exp",round(npre/1e4,1),"post",post[n],"exp",round(npost/1e4,1))
print("rank of 1024 pre:",sorted(pre.values(),reverse=True).index(pre["1024"])+1, "max pre",max(pre.values()))
top=[n for n,_ in pre.most_common(10)]
print("top10 pre-2012 numbers post-2012 wins:",sum(post[n] for n in top),"exp",round(10*npost/1e4,1), top)
EOF
```

## 15. 2026-10-16 18:21 — Break down 1024 wins with Python

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
import csv
from collections import Counter
rows=[r for s in ["magnum","sportstoto","damacai"] for r in csv.DictReader(open(f"data/{s}.csv")) if r["4d_number"]=="1024"]
print(len(rows)); print(Counter(r["operator"] for r in rows)); print(Counter(r["prize"] for r in rows))
print(sorted(Counter(r["date"][:4] for r in rows).items()))
print("dates with >1:",[d for d,c in Counter(r["date"] for r in rows).items() if c>1])
# expected per operator
for s in ["magnum","sportstoto","damacai"]:
    n=sum(1 for _ in csv.DictReader(open(f"data/{s}.csv"))); print(s, "expected", round(n/1e4,1))
EOF
```

## 16. 2026-10-16 18:22 — Assess how unusual 1024's frequency is

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
import csv, math
from collections import Counter
import numpy as np
c=Counter(); n=0
per={}
for s in ["magnum","sportstoto","damacai"]:
    cc=Counter()
    for r in csv.DictReader(open(f"data/{s}.csv")): c[r["4d_number"]]+=1; cc[r["4d_number"]]+=1; n+=1
    per[s]=cc
lam=n/1e4
def sf(k,l): return sum(math.exp(j*math.log(l)-l-math.lgamma(j+1)) for j in range(k,k+200))
print("lambda",lam, "top 8:",c.most_common(8))
p=sf(c["1024"],lam); print("P(X>=79)",p,"best of 10000:",1-(1-p)**10000)
# simulate: max count among 10000 numbers via multinomial-ish Poisson
rng=np.random.default_rng(0); mx=[rng.poisson(lam,10000).max() for _ in range(2000)]
print("sim max distribution: median",np.median(mx),"99.9%",np.percentile(mx,99.9),"P(max>=79)",np.mean(np.array(mx)>=79))
for s,cc in per.items():
    l=sum(cc.values())/1e4; print(s, cc["1024"], round(l,1), "rank", sorted(cc.values(),reverse=True).index(cc["1024"])+1)
EOF
grep -n "1024" scraper.py | head
```

## 17. 2026-10-16 18:23 — 1024 by operator before and after 2012

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
import csv
for s in ["magnum","sportstoto","damacai"]:
    rows=list(csv.DictReader(open(f"data/{s}.csv")))
    for lo,hi in (("0","2012"),("2012","9")):
        sub=[r for r in rows if lo<=r["date"]<hi]
        print(s, f"{lo}-{hi}", sum(r["4d_number"]=="1024" for r in sub), "exp", round(len(sub)/1e4,1))
EOF
```

## 18. 2026-10-16 18:23 — Update report section 6, commit and push

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
s=open("analysis/REPORT.md").read()
a=s.index("## 6. Specific numbers under specific conditions")
b=s.index("## Conclusion\n")
new='''## 6. Specific numbers under specific conditions (single and paired parameters)

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

'''
s=s[:a]+new+s[b:]
open("analysis/REPORT.md","w").write(s)
EOF
git add analysis && git commit -q -m "Report full Chinese almanac and Vedic/KP parameter scan; flag 1024 as an overall outlier

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q -u origin claude/4d-results-scraper-9ptbd5 && git log --oneline -1 && git status --short
```

## 19. 2026-10-17 00:01 — Fix JSON bug, add finer weights, rerun

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
p="analysis/predictive_model.py"; s=open(p).read()
s=s.replace("    grid = (0.25, 0.5, 1, 2, 4)\n","    grid = (0.02, 0.05, 0.1, 0.25, 0.5, 1, 2)\n")
s=s.replace("""    cfg = {"weights": weights, "validation_gain_millinats_per_winner": 1000 * joint[scale] / n_win,
           "single_component": {k: {"weight": w, "gain_millinats": 1000 * g / n_win} for k, (w, g) in best.items()},""",
"""    weights = {k: float(w) for k, w in weights.items()}
    cfg = {"weights": weights, "validation_gain_millinats_per_winner": float(1000 * joint[scale] / n_win),
           "single_component": {k: {"weight": float(w), "gain_millinats": float(1000 * g / n_win)}
                                for k, (w, g) in best.items()},""")
s=s.replace("""        json.dump(out, fh, indent=1)""","""        json.dump(out, fh, indent=1, default=float)""")
open(p,"w").write(s)
EOF
python3 analysis/predictive_model.py > /tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad/model.log 2>&1; tail -30 /tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad/model.log
```

## 20. 2026-10-17 00:04 — Add report section 7, commit and push

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
s=open("analysis/REPORT.md").read()
sec='''## 7. A predictive formula, tested on draws it never saw

`python3 analysis/predictive_model.py` (~2 min) builds, tunes and tests it.
`python3 analysis/predictive_model.py predict --date YYYY-MM-DD [--operator Magnum] [--k 5]`
prints the top K numbers for any future draw.

**The formula.** For a draw of operator *op* on date *t*, every number *n* gets

```
score(n) = w_hot  * log[(wins_op(n) + a) / (expected + a)]                 overall hot number
         + w_pool * (same, all operators pooled)
         + w_dig  * Σ_pos log[p_op(pos, digit) / 0.1]                       recent digit bias (half-life 300 draws)
         + w_cdig / 84 * Σ_f Σ_pos log[p(pos, digit | f = f(t)) / p(pos, digit)]
         + w_cnum / 84 * Σ_f log[(wins(n | f = f(t)) + a) / (expected + a)]
         + w_cbox / 84 * Σ_f log[(wins(i-Box(n) | f = f(t)) + a) / (expected + a)]
```

f runs over all 84 date parameters (section 6). The picks are the K
top-scoring numbers.

**Protocol.**
1. Count from draws before 2012.
2. Choose the weights and smoothing on 2012–2017 by the likelihood the
   formula gives the real winners (74,000 of them).
3. Freeze the formula.
4. Test it on 2018 – Oct 2026 (4,180 draws). For each test year, re-learn
   the counts from all earlier draws only.

**Tuning outcome.** Most ingredients made the validation predictions *worse*
at every weight tried. That includes hot numbers (1024 among them), pooled hot
numbers, and the number-level "wins under this condition" signal. Only tiny
weights on the recent digit bias, the conditional digit signal and the
conditional i-Box signal helped, by 0.007 thousandths of a nat per winner,
effectively nothing. Frozen formula: `w_dig = 0.05, w_cdig = 0.25,
w_cbox = 0.02`, all others 0 (`analysis/predictive_model_config.json`).

**Test on unseen draws (2018–2026, all operators).**

| Picks per draw | Wins (any prize) | Random expectation | Lift | z |
|---|---|---|---|---|
| Top 5 | 54 | 48.0 | 1.13× | +0.9 |
| Top 10 | 111 | 96.0 | 1.16× | +1.5 |
| Top 23 | 243 | 220.9 | 1.10× | +1.5 |
| Top 100 | 963 | 960.3 | 1.00× | +0.1 |

Per operator, top 10: Magnum 1.03×, Sports Toto 1.22×, Da Ma Cai 1.23× (all
|z| < 1.5). None of this is statistically distinguishable from random
picking. The year-by-year top-10 counts swing from 2 to 22 hits against ~9–12
expected.

Big Forecast returns per RM1 in the test: top 1 RM1.09, top 5 RM0.60, top
10 RM0.63. A random number returns RM0.64 on average. Returns over a few
thousand draws are dominated by whether a 1st/2nd prize happened to land:
the simulated random picks run alongside the test returned anywhere from
RM0.16 to RM2.89 per RM1. The top-1 figure is one lucky top-prize hit, not
an edge. Breaking even needs about 1.56× the random hit rate *sustained*.
The formula's 1.0–1.16× is within noise of 1.0.

The hot-number baseline did no better (1.01× for top 10 and top 23).

**Bottom line.** Combining every parameter we have into one tuned formula,
and testing it honestly on later draws, gives results consistent with random
picking. The formula is kept as a tool: it produces numbers for any date,
but no claim is made that they are more likely to win.

'''
s=s.replace("## Conclusion\n", sec+"## Conclusion\n")
open("analysis/REPORT.md","w").write(s)
EOF
git add analysis && git commit -q -m "Test predictive formula on unseen 2018-2026 draws; fix predict date index; report section 7

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q -u origin claude/4d-results-scraper-9ptbd5 && git log --oneline -1 && git status --short
```

## 21. 2026-10-17 00:43 — Optimise counting and tuning loops

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
p="analysis/astro_model.py"; s=open(p).read()
old=s[s.index("    def add(self, date_ix, op_ix, num):"):s.index("    def term(self, f, v, kind, op_i):")]
new='''    def add(self, date_ix, op_ix, num):
        """Add winning rows (already once-per-draw). Bulk loads use bincount, single dates np.add.at."""
        grp = cn.GROUP_OF[num]
        bulk = len(num) > 5000
        for s, m in ((0, np.ones(len(num), bool)), *((i + 1, op_ix == i) for i in range(3))):
            if not m.any():
                continue
            d, n, g = date_ix[m], num[m], grp[m]
            self.T[s] += len(n)
            self.all[s] += np.bincount(n, minlength=10000)
            self.gall[s] += np.bincount(g, minlength=NG)
            for p in range(4):
                self.dall[s, p] += np.bincount(DIG[n, p], minlength=10)
            for f in self.factors:
                v = self.codes[f][d]
                V = self.V[f]
                if bulk:
                    self.num[f][s] += np.bincount(v * 10000 + n, minlength=V * 10000).reshape(V, 10000)
                    self.box[f][s] += np.bincount(v * NG + g, minlength=V * NG).reshape(V, NG)
                    self.nv[f][s] += np.bincount(v, minlength=V)
                    for p in range(4):
                        self.dig[f][s][:, p, :] += np.bincount(v * 10 + DIG[n, p], minlength=V * 10).reshape(V, 10)
                else:
                    np.add.at(self.num[f][s], (v, n), 1)
                    np.add.at(self.box[f][s], (v, g), 1)
                    np.add.at(self.nv[f][s], v, 1)
                    for p in range(4):
                        np.add.at(self.dig[f][s], (v, p, DIG[n, p]), 1)

'''
s=s.replace(old,new)
old=s[s.index("    # 1. each (parameter, kind) on its own, three weights"):s.index("    g, k, scale = best\n")]
new='''    # 1. each (parameter, kind) on its own, three weights
    W = (0.1, 0.3, 1.0)
    single = []
    for f in factors:
        for kind in KINDS:
            groups = {}
            for d, o, win in val:
                key = (int(codes[f][d]), o if kind.endswith("_op") else -1)
                groups.setdefault(key, []).append(win)
            g = dict.fromkeys(W, 0.0)
            for (v, o), wins in groups.items():
                t = c.term(f, v, kind, max(o, 0))
                tw = sum(t[w_].sum() for w_ in wins)
                nw = sum(len(w_) for w_ in wins)
                for w in W:
                    m = (w * t).max()
                    lse = m + math.log(np.exp(w * t - m).sum())
                    g[w] += w * tw - nw * lse + nw * math.log(10000)
            w, best = max(g.items(), key=lambda x: x[1])
            single.append((best, f, kind, w))
    single.sort(reverse=True)
    useful = [x for x in single if x[0] > 0]
    print(f"[{variant}] {len(single)} terms scored alone; {len(useful)} help on validation "
          f"({time.time() - t0:.0f}s)", flush=True)
    for g_, f, kind, w in single[:8]:
        print(f"    {f:<22} {kind:<7} w={w:<4} gain {1000 * g_ / n_win:+.4f} millinats/winner")
    # 2. best prefix of the ranked useful terms, and a joint scale
    cands = (useful if useful else single[:1])[:30]
    prefixes = sorted(k for k in {1, 2, 3, 5, 8, 12, 20, 30} if k <= len(cands)) or [len(cands)]
    scales = (0.25, 0.5, 1.0)
    tot = {(k, sc): 0.0 for k in prefixes for sc in scales}
    for d, o, win in val:
        acc = np.zeros(10000)
        j = 0
        for k in prefixes:
            while j < k:
                _, f, kind, w = cands[j]
                acc += w * c.term(f, int(codes[f][d]), kind, o)
                j += 1
            for sc in scales:
                tot[(k, sc)] += gain(sc * acc, win)
    (k, scale), g = max(tot.items(), key=lambda x: x[1])
    best = (g, k, scale)
'''
s=s.replace(old,new)
open(p,"w").write(s)
EOF
python3 -c "import ast;ast.parse(open('/home/user/4DPrediction/analysis/astro_model.py').read())" && echo ok
```

## 22. 2026-10-17 00:45 — Fix and rerun forward test with frozen formulas

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
p="analysis/astro_model.py"; s=open(p).read()
s=s.replace('''    return out, {y: {"hits@10": h, "expected@10": round(e, 1)} for y, (h, e) in sorted(yearly.items())}''',
'''    return out, {int(y): {"hits@10": h, "expected@10": round(e, 1)} for y, (h, e) in sorted(yearly.items())}''')
old='''    formulas, results = {}, {}
    for v in VARIANTS:
        formulas[v] = tune(v, codes, rows, draws)
    with open(FORMULAS, "w") as fh:
        json.dump(formulas, fh, indent=1)
    print("formulas frozen ->", FORMULAS, flush=True)'''
new='''    results = {}
    if os.path.exists(FORMULAS) and not a.retune:
        with open(FORMULAS) as fh:
            formulas = json.load(fh)
        print("using the frozen formulas in", FORMULAS, "(--retune to tune again)", flush=True)
    else:
        formulas = {v: tune(v, codes, rows, draws) for v in VARIANTS}
        with open(FORMULAS, "w") as fh:
            json.dump(formulas, fh, indent=1)
        print("formulas frozen ->", FORMULAS, flush=True)'''
assert old in s; s=s.replace(old,new)
s=s.replace('''    ap.add_argument("--k", type=int, default=10)''','''    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--retune", action="store_true")''')
open(p,"w").write(s)
EOF
python3 analysis/astro_model.py 2>&1 | sed -n '/using the frozen/p;/=== Forward/,$p'
```

## 23. 2026-10-17 00:47 — Add report section 8, commit and push

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
s=open("analysis/REPORT.md").read()
sec='''## 8. Vedic-only, Chinese-only and combined formulas, forward-tested draw by draw

`python3 analysis/astro_model.py` (~1 min with the frozen formulas;
`--retune` to tune again). Unlike section 7, these formulas use **only** Vedic
and/or Chinese parameters: no hot numbers, no digit bias, no weekday/month or
Western astrology. (Weekday enters the Vedic set only as the vara.) Every term
compares how often a number, its digits or its i-Box group won on dates with
the same parameter value against how often it won overall.

For a draw on date *t*:

```
score(n) = Σ over the formula's terms (parameter f, kind, weight w)  w · L_kind(f, f(t), n)

L_num (f,v,n) = log[(wins of n on dates with f = v + 10) / (expected + 10)]
L_box (f,v,n) = log[(wins of n's i-Box group on dates with f = v + 50) / (expected + 50)]
L_dig (f,v,n) = Σ_pos log[p(digit | f = v) / p(digit)]           (50 pseudo-draws)
*_op          = the same, counting only the draw's own operator
```

**Tuning.**
1. Count from draws before 2012.
2. Score every (parameter, kind) term alone on 2012–2017: 312 Vedic, 156
   Chinese, 468 combined.
3. Rank the ones that helped (61, 36 and 97) and keep the best prefix and
   scale. The result is 30 terms for each formula.
4. Freeze the formulas and commit them (`analysis/astro_model_formulas.json`,
   commit c5d2c7d) before any test was run.

The top terms were Mars's nakshatra (i-Box), Jupiter's nakshatra and rashi
(digits), ayana and ritu for the Vedic formula; day element, day stem, day
officer, year stem and Nine Star for the Chinese one.

**Forward test, 2018-01-01 to 2026-10-10, draw by draw.** Each of 4,180 draws
was predicted from all draws strictly before its date. Its results were then
added to the counts before the next date was predicted.

| Formula | Top 5 | Top 10 | Top 23 | Top 100 | Fit to winners vs uniform |
|---|---|---|---|---|---|
| Vedic | 39 / 48.0 (0.81×) | 87 / 96.0 (0.91×) | 210 / 220.9 (0.95×) | 899 / 960.3 (0.94×, z = −2.0) | worse |
| Chinese | 49 / 48.0 (1.02×) | 99 / 96.0 (1.03×) | 234 / 220.9 (1.06×) | 944 / 960.3 (0.98×) | worse |
| Vedic + Chinese | 41 / 48.0 (0.85×) | 75 / 96.0 (0.78×, z = −2.1) | 188 / 220.9 (0.85×, z = −2.2) | 1000 / 960.3 (1.04×) | worse |

(wins of any prize / expected for random picks.)

All three formulas fit the real winners *worse* than assuming every number
equally likely, although each had looked better on the tuning years. The
terms that "helped" in 2012–2017 were fitting noise: with 300–470 terms tried,
about half look helpful by chance. Big Forecast returns per RM1 (top 10):
Vedic RM0.58, Chinese RM0.65, combined RM0.47, against RM0.64 for an average
random number.

**Live forward log.** `python3 analysis/astro_model.py log --date YYYY-MM-DD`
appends each formula's picks for a future draw to `analysis/forward_log.csv`,
with the time they were made. `python3 analysis/astro_model.py score` scores
every logged pick that was made before its draw, once `scraper.py` has added
that draw's results to `data/`. Picks for 2026-10-18 and 2026-10-21 were
logged on 2026-10-17 00:47 UTC.

'''
s=s.replace("## Conclusion\n", sec+"## Conclusion\n")
open("analysis/REPORT.md","w").write(s)
EOF
git add analysis && git commit -q -m "Forward-test Vedic/Chinese formulas draw by draw; log live picks for 18 and 21 Oct; report section 8

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q -u origin claude/4d-results-scraper-9ptbd5 && git log --oneline -1 && git status --short
```

## 24. 2026-10-17 00:54 — Score 14 Oct picks against published results

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
res = {
 "Magnum": {"top3":"3872 3175 1274","special":"9432 0504 7685 3683 0877 0164 8480 5730 9152 1613","consol":None},
 "Sports Toto": {"top3":"9332 0305 0606","special":"3342 8253 0014 5484 2858 7445 6147 8346 8435 5213","consol":"2212 6901 8649 8189 3036 3226 2131 1480 4381 2363"},
 "Da Ma Cai": {"top3":"6906 7100 6516","special":"8626 2888 1164 7150 6415 2016 4406 1710 7120 1777","consol":"0779 4696 4454 7436 8259 6972 1294 7155 6467 4482"},
}
picks = """vedic Magnum 5265 7492 7294 7429 5228 5526 5256 5562 7249 6166
vedic Sports_Toto 7206 6207 7996 9796 0726 0267 6997 6799 2706 9697
vedic Da_Ma_Cai 6704 0764 6720 6740 6702 6799 6834 8795 0726 2794
chinese Magnum 0992 0403 2834 3824 8607 4823 0929 9029 2909 0867
chinese Sports_Toto 8142 0826 8726 8421 1494 2394 1824 7862 0403 5723
chinese Da_Ma_Cai 9091 1891 8840 0992 2941 9029 0991 2777 7727 5758
both Magnum 3044 4043 3440 6798 7997 0799 0443 5526 7909 6793
both Sports_Toto 9796 8807 7206 8708 0788 7260 7808 0627 6207 9967
both Da_Ma_Cai 2093 0799 0293 9032 3092 6395 7895 0791 0392 2390"""
allwin = set()
for op, r in res.items():
    for v in r.values():
        if v: allwin |= set(v.split())
for line in picks.splitlines():
    v, op, *nums = line.split(); op = op.replace("_"," ")
    r = res[op]; hits=[]
    for n in nums:
        for k,val in r.items():
            if val and n in val.split(): hits.append((n,k))
    # near misses: same digits any order (i-Box) against this operator's winners
    win = [w for val in r.values() if val for w in val.split()]
    ibox = [(n,w) for n in nums for w in win if sorted(n)==sorted(w)]
    print(f"{v:<8}{op:<12} straight hits: {hits or 'none'}   i-Box matches: {ibox or 'none'}")
EOF
```

## 25. 2026-10-17 00:57 — Score all 14 Oct picks against official 4dmoon results

```bash
cd /home/user/4DPrediction; cat > /tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad/res_1014.py <<'EOF'
RES = {
 "2026-10-11": {
  "Magnum": {"1st":"6319","2nd":"5321","3rd":"3186","Special":"0316 6709 9757 3775 2263 6225 1339 7786 1012 6114","Consolation":"0513 7507 0365 6575 4432 0955 5576 4601 1371 9840"},
  "Sports Toto": {"1st":"2224","2nd":"2149","3rd":"3561","Special":"6514 2017 7072 0288 2962 1512 5314 9089 0253 6951","Consolation":"8603 9696 0293 3841 2975 3132 4640 0214 3711 7118"},
  "Da Ma Cai": {"1st":"7952","2nd":"4847","3rd":"9772","Special":"7208 2464 7148 8680 4396 9420 1917 9424 3619 7877","Consolation":"6329 9700 8721 5562 3366 9919 6536 1738 6299 5759"}},
 "2026-10-14": {
  "Magnum": {"1st":"3872","2nd":"3175","3rd":"1274","Special":"9432 0504 7685 3683 0877 0164 8480 5730 9152 1613","Consolation":"4661 2995 3368 3934 2300 3039 9686 6307 7484 4904"},
  "Sports Toto": {"1st":"9332","2nd":"0305","3rd":"0606","Special":"3342 8253 0014 5484 2858 7445 6147 8346 8435 5213","Consolation":"2212 6901 8649 8189 3036 3226 2131 1480 4381 2363"},
  "Da Ma Cai": {"1st":"6906","2nd":"7100","3rd":"6516","Special":"8626 2888 1164 7150 6415 2016 4406 1710 7120 1777","Consolation":"0779 4696 4454 7436 8259 6972 1294 7155 6467 4482"}},
}
EOF
python3 - <<'EOF'
import sys; sys.path.insert(0,"/tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad")
from res_1014 import RES
BIG={"1st":2500,"2nd":1000,"3rd":500,"Special":180,"Consolation":60}
r=RES["2026-10-14"]
picks = {
"astro vedic":   {"Magnum":"5265 7492 7294 7429 5228 5526 5256 5562 7249 6166","Sports Toto":"7206 6207 7996 9796 0726 0267 6997 6799 2706 9697","Da Ma Cai":"6704 0764 6720 6740 6702 6799 6834 8795 0726 2794"},
"astro chinese": {"Magnum":"0992 0403 2834 3824 8607 4823 0929 9029 2909 0867","Sports Toto":"8142 0826 8726 8421 1494 2394 1824 7862 0403 5723","Da Ma Cai":"9091 1891 8840 0992 2941 9029 0991 2777 7727 5758"},
"astro both":    {"Magnum":"3044 4043 3440 6798 7997 0799 0443 5526 7909 6793","Sports Toto":"9796 8807 7206 8708 0788 7260 7808 0627 6207 9967","Da Ma Cai":"2093 0799 0293 9032 3092 6395 7895 0791 0392 2390"},
"first model":   {"Magnum":"6599 9599 5599 1599 6899 0599 6596 9596 6549 5899","Sports Toto":"7597 5524 7594 0597 5527 5594 0594 7524 5597 5994","Da Ma Cai":"5591 5594 5592 5097 6594 6591 5094 5597 5091 5092"},
}
for m, ops in picks.items():
    out=[]; pay=0
    for op, s in ops.items():
        win={n:p for p,v in r[op].items() for n in v.split()}
        for n in s.split():
            if n in win: out.append(f"{op} {n} straight {win[n]}"); pay+=BIG[win[n]]
            for w,p in win.items():
                if w!=n and sorted(w)==sorted(n): out.append(f"{op} {n}~{w} i-Box {p}")
    print(f"{m:<14} 30 picks: {out or 'no matches'}; Big RM{pay} back on RM30")
EOF
```

## 26. 2026-10-17 00:57 — Append 11 and 14 Oct results to data

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
import sys, csv, datetime as dt
sys.path.insert(0,"/tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad")
from res_1014 import RES
files={"Magnum":"data/magnum.csv","Sports Toto":"data/sportstoto.csv","Da Ma Cai":"data/damacai.csv"}
for op,path in files.items():
    existing={r["date"] for r in csv.DictReader(open(path,newline=""))}
    with open(path,"a",newline="") as f:
        w=csv.writer(f)
        for date in sorted(RES):
            if date in existing: continue
            day=dt.date.fromisoformat(date).strftime("%a")
            for prize in ("1st","2nd","3rd","Special","Consolation"):
                for n in RES[date][op][prize].split():
                    w.writerow([date,day,op,prize,n])
    print(path, "appended")
EOF
tail -2 data/damacai.csv; git diff --stat
```

## 27. 2026-10-17 01:02 — Test the TinyFish importer

```bash
cd /home/user/4DPrediction; python3 -m unittest tests/test_tinyfish_import.py -v 2>&1 | tail -8; python3 - <<'EOF'
# consistency check: parser output for 14 Oct equals the rows already in data/
import csv, tinyfish_import as t
rows=t.parse(open("tests/fixtures/tinyfish_2026-10-14.html").read())
for op,f in [("Magnum","data/magnum.csv"),("Sports Toto","data/sportstoto.csv"),("Da Ma Cai","data/damacai.csv")]:
    have=[(r["prize"],r["4d_number"]) for r in csv.DictReader(open(f)) if r["date"]=="2026-10-14"]
    new=[(r["prize"],r["4d_number"]) for r in rows if r["operator"]==op]
    print(op, "matches data/:", have==new)
EOF
```

## 28. 2026-10-17 01:02 — Document and commit the importer

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
s=open("README.md").read()
s=s.replace("Standard library only (Python 3.9+). Downloaded pages are cached in `.cache/`.",
"""Standard library only (Python 3.9+). Downloaded pages are cached in `.cache/`.

If 4dmoon.com cannot be reached directly, fetch the pages with TinyFish
(`fetch_content`, format `html`) and import them:

```sh
python3 tinyfish_import.py page.html [more.html ...]   # or the saved JSON response
python3 -m unittest tests/test_tinyfish_import.py
```""")
open("README.md","w").write(s)
EOF
git add README.md tinyfish_import.py tests && git commit -q -m "Add TinyFish importer for 4dmoon pages with tests

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q -u origin claude/4d-results-scraper-9ptbd5 && git log --oneline -1
```

## 29. 2026-10-17 01:44 — Add logging and generate ML picks for 18 and 21 Oct

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
p="analysis/ml_model.py"; s=open(p).read()
s=s.replace('''    ap.add_argument("--k", type=int, default=10)
    a = ap.parse_args()''','''    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--log", action="store_true", help="append the picks to analysis/forward_log.csv")
    a = ap.parse_args()''')
s=s.replace('''        for d, by_model in res.items():
            print(f"Picks for {d} (top {a.k}):")''','''        if a.log:
            import csv
            new = not os.path.exists(am.LOG)
            now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
            with open(am.LOG, "a", newline="") as fh:
                w = csv.writer(fh)
                if new:
                    w.writerow(["logged_at_utc", "draw_date", "variant", "operator", "rank", "4d_number"])
                for d, by_model in res.items():
                    for name, by_op in by_model.items():
                        for op, nums in by_op.items():
                            for r, n in enumerate(nums, 1):
                                w.writerow([now, d, f"ml_{name}", op, r, f"{n:04d}"])
        for d, by_model in res.items():
            print(f"Picks for {d} (top {a.k}):")''')
open(p,"w").write(s)
EOF
date -u; python3 analysis/ml_model.py predict --date 2026-10-18 --date 2026-10-21 --k 10 --log > /tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad/mlpred.log 2>&1; echo "exit $?" >> /tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad/mlpred.log
```

## 30. 2026-10-17 01:45 — Write report section 9

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
s=open("analysis/REPORT.md").read()
sec='''## 9. Non-linear models (gradient-boosted trees, similar-days kernel, ensemble)

`python3 analysis/ml_model.py` (~30 min, LightGBM). It is walk-forward: from
2012 every model is retrained at the start of each year on earlier draws
only. 2012–2017 is the validation period and 2018 – Oct 2026 the test
period (4,180 draws). The selection rule was fixed before the run: the best
validation log-likelihood.

| Model | What it is |
|---|---|
| A_all | Gradient-boosted trees over (draw, number) pairs. Inputs: digits and pattern; the number's own history (all-time / last-200 / last-1000 wins, draws since last win, i-Box group counts, wins at any operator on the previous date, recent digit bias); aggregated Vedic and Chinese lifts; and 15 raw Vedic/Chinese parameters, so the trees can learn interactions such as digit × nakshatra |
| A_astro | Same trees with only digits/pattern and the Vedic/Chinese inputs |
| A_hist | Same trees with only digits/pattern and number history (control) |
| C_digit | Four multiclass tree models, one per digit position, predicting each digit from the Vedic/Chinese parameters, operator and recent digit frequencies; P(number) = product |
| B_kernel | "Similar days": past dates weighted by exp(β × number of the 78 Vedic + Chinese parameters they share with the target date), applied to i-Box group wins; β = 0.1, 0.3, 1.0 |
| E_ens | Average of A_all, A_astro, C_digit and B_kernel(0.3) |

**Test, all operators (wins of any prize / random expectation).**

| Model | Validation top 10 | Test top 5 | Test top 10 | Test top 23 | Test top 100 | Big RM1, top 10 |
|---|---|---|---|---|---|---|
| **B_kernel β=0.1 (selected)** | 0.91× | 61/48.1 (1.27×, z = +1.9) | 115/96.2 (1.20×, z = +1.9) | 251/221.2 (1.13×, z = +2.0) | 1.01× | RM0.71 |
| A_all | 1.03× | 1.19× | 1.13× | 1.14× (z = +2.1) | 1.06× | RM0.57 |
| E_ens | 0.95× | 1.23× | 1.18× | 1.12× | 0.96× | RM0.71 |
| B_kernel β=1.0 | 0.97× | 1.06× | 1.18× | 1.09× | 1.00× | RM0.86 |
| A_astro | 1.03× | 1.04× | 1.03× | 1.08× | 1.01× | RM0.68 |
| A_hist | 0.92× | 1.00× | 1.04× | 0.96× | 0.99× | RM0.65 |
| C_digit | 0.96× | 1.00× | 0.97× | 0.98× | 1.00× | RM0.57 |
| B_kernel β=0.3 | 0.99× | 1.04× | 1.06× | 1.08× | 1.00× | RM0.73 |

**Reading it.**
* No model gives the real winners a higher likelihood than "every number
  equally likely", in either period. The models are confident in a way the
  data does not support.
* Several test lifts reach z ≈ 2. With 8 models × 4 pick sizes, a couple of
  z ≈ 2 results are expected by chance (p ≈ 0.02 each, one-sided). None was
  visible in the validation years: the selected kernel was *below* random
  there (0.91×).
* The gains move around between operators and models. B_kernel's test excess
  is mostly Da Ma Cai; A_all's is Sports Toto and Magnum; E_ens's is Sports
  Toto. Over 2012–2017 the same models were at 0.80–1.17× by operator. A real
  effect would show up consistently.
* Money: the best top-10 Big return is RM0.86 per RM1, still below a random
  number's long-run RM0.64 + noise band, and far from the 1.56× hit rate
  needed to break even.

**Verdict.** Non-linear trees, digit-position models, similar-days kernels
and an ensemble, with Vedic, Chinese and history inputs combined, all perform
like random picking on unseen draws. The selected model (B_kernel β=0.1)
had the best test numbers but failed its validation period. It goes into the
live forward log (`analysis/forward_log.csv`, variants `ml_*`) so that future
draws, which no model has seen, can settle it.

'''
s=s.replace("## Conclusion\n", sec+"## Conclusion\n")
open("analysis/REPORT.md","w").write(s)
EOF
echo ok
```

## 31. 2026-10-17 02:49 — Choose parameters, test the manual formula, export tables

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
p="analysis/manual_formula.py"; s=open(p).read()
a=s.index("    start = dt.date.fromisoformat("); b=s.index("    cal = []")
s=s[:a]+s[b:]
open(p,"w").write(s)
EOF
python3 analysis/manual_formula.py 2>&1 | grep -v "computed"
```

## 32. 2026-10-17 02:52 — Compare against a plain 9-heavy number strategy

```bash
cd /home/user/4DPrediction; python3 - <<'EOF' 2>&1 | grep -v computed
import sys, math, numpy as np
sys.path.insert(0,"analysis")
import astro_model as am
data, codes, labels, rows, draws, year_of = am.load()
DIG=am.DIG
for per,(a,b) in {"1985-2011":(0,2012),"2012-2017":(2012,2018),"2018-2026":(2018,3000)}.items():
    for o,op in enumerate(am.OPS):
        m=(rows["op_ix"]==o)&(rows["year"]>=a)&(rows["year"]<b)
        n=rows["num"][m]
        if len(n)==0: continue
        share=[(DIG[n,p]==9).mean() for p in range(4)]
        tot=(DIG[n]==9).mean(); z=(tot-0.1)/math.sqrt(0.09/(4*len(n)))
        print(f"{per} {op:<12} digit-9 share by position {[round(100*s,2) for s in share]}  overall {100*tot:.2f}% (z={z:+.1f})")
# fixed strategy: always the 5 most-picked numbers
fixed={9999,9989,9899,9998,8999}
h=e=0
for (d,o),(win,pr) in draws.items():
    if year_of[d]>=2018:
        h+=len(fixed & set(win)); e+=5*len(win)/10000
print(f"always 9999/9989/9899/9998/8999, 2018-2026: {h} hits vs {e:.1f} expected (x{h/e:.2f})")
h=e=0
for (d,o),(win,pr) in draws.items():
    if 2012<=year_of[d]<2018:
        h+=len(fixed & set(win)); e+=5*len(win)/10000
print(f"same fixed 5 in 2012-2017: {h} vs {e:.1f}")
EOF
```

## 33. 2026-10-17 02:53 — Verify workbook matches Python for two dates

```bash
cd /home/user/4DPrediction; S=/tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad; python3 - <<'EOF' 2>&1 | grep -v computed
import sys, json, datetime as dt, shutil, subprocess
sys.path.insert(0,"analysis")
from openpyxl import load_workbook
import numpy as np, astro_model as am, manual_formula as mf
J=json.load(open("analysis/manual_formula.json")); W=J["weights"]
def py_top5(date):
    row=next(r for r in J["calendar"] if r["date"]==date)
    P=np.zeros((4,10))
    for f in W: P+=np.array(J["tables"][f][row[f]])
    return [f"{n:04d}" for n in mf.top_numbers(P,5)], row
def xl_top5(path):
    ws=load_workbook(path,data_only=True)["Predict"]
    return [ws.cell(7+k,17).value for k in range(5)], [ws.cell(7+i,2).value for i in range(6)]
print("2026-10-18 python:", py_top5("2026-10-18"))
print("2026-10-18 excel :", xl_top5("analysis/manual_formula.xlsx"))
# second date: edit B3, recalc a copy
S="/tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad/mf_copy.xlsx"
wb=load_workbook("analysis/manual_formula.xlsx"); wb["Predict"]["B3"]=dt.date(2027,3,14); wb.save(S)
subprocess.run(["python3","/root/.claude/skills/synced/981f7279-2cd5-466c-9d0a-1ea18c88fa31_71864801-9a9c-44ca-8106-82c0b941d4fd/xlsx/scripts/recalc.py",S,"120"],capture_output=True)
print("2027-03-14 python:", py_top5("2027-03-14"))
print("2027-03-14 excel :", xl_top5(S))
EOF
```

## 34. 2026-10-17 02:54 — Fix tie-breaking, rebuild, verify six dates

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
p="analysis/build_manual_workbook.py"; s=open(p).read()
old='''        # +digit/10000 breaks ties toward the higher digit, as in manual_formula.py
        pr.cell(r, 2 + d, f"=SUM({hc}{HELP_FIRST}:{hc}{HELP_LAST})+{d}/10000").font = NORM
        pr.cell(r, 2 + d).number_format = "0"
        pr.cell(r, 2 + d).border = THIN
    rng = f"$B{r}:$K{r}"
    pr.cell(r, 13, f"=MATCH(MAX({rng}),{rng},0)-1").font = BOLD
    pr.cell(r, 14, f"=MATCH(LARGE({rng},2),{rng},0)-1").font = NORM'''
new='''        pr.cell(r, 2 + d, f"=SUM({hc}{HELP_FIRST}:{hc}{HELP_LAST})").font = NORM
        pr.cell(r, 2 + d).number_format = "0"
        pr.cell(r, 2 + d).border = THIN
        # tie-break copy (columns AJ:AS): equal points -> the higher digit, as in manual_formula.py
        pr.cell(r, 36 + d, f"={L(2 + d)}{r}+{d}/1000000").font = Font(name=F, color="999999")
    rng = f"$AJ{r}:$AS{r}"
    pr.cell(r, 13, f"=MATCH(MAX({rng}),{rng},0)-1").font = BOLD
    pr.cell(r, 14, f"=MATCH(LARGE({rng},2),{rng},0)-1").font = NORM'''
assert old in s; s=s.replace(old,new)
s=s.replace('''pr.cell(G0, 14, "2nd best").font = BOLD''','''pr.cell(G0, 14, "2nd best").font = BOLD
pr.cell(G0, 36, "Tie-break helper (points + digit/1,000,000)").font = Font(name=F, italic=True, color="999999")''')
open(p,"w").write(s)
EOF
python3 analysis/build_manual_workbook.py && python3 /root/.claude/skills/synced/981f7279-2cd5-466c-9d0a-1ea18c88fa31_71864801-9a9c-44ca-8106-82c0b941d4fd/xlsx/scripts/recalc.py analysis/manual_formula.xlsx 120 && python3 - <<'EOF' 2>&1 | grep -v computed
import sys, json, datetime as dt, subprocess
sys.path.insert(0,"analysis")
from openpyxl import load_workbook
import numpy as np, manual_formula as mf
J=json.load(open("analysis/manual_formula.json")); W=J["weights"]
REC="/root/.claude/skills/synced/981f7279-2cd5-466c-9d0a-1ea18c88fa31_71864801-9a9c-44ca-8106-82c0b941d4fd/xlsx/scripts/recalc.py"
S="/tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad/mf_copy.xlsx"
bad=0
for date in ["2026-10-18","2026-10-21","2026-12-25","2027-03-14","2027-08-08","2027-12-29"]:
    row=next(r for r in J["calendar"] if r["date"]==date)
    P=np.zeros((4,10))
    for f in W: P+=np.array(J["tables"][f][row[f]])
    py=[f"{n:04d}" for n in mf.top_numbers(P,5)]
    wb=load_workbook("analysis/manual_formula.xlsx"); wb["Predict"]["B3"]=dt.date.fromisoformat(date); wb.save(S)
    subprocess.run(["python3",REC,S,"120"],capture_output=True)
    ws=load_workbook(S,data_only=True)["Predict"]
    xl=[ws.cell(7+k,17).value for k in range(5)]
    bad+=py!=xl
    print(date, "python", py, "excel", xl, "OK" if py==xl else "MISMATCH")
print("mismatches:", bad)
EOF
```

## 35. 2026-10-17 02:54 — Log manual picks, commit and push workbook

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
import csv, json, datetime as dt, sys
sys.path.insert(0,"analysis")
import numpy as np, manual_formula as mf
J=json.load(open("analysis/manual_formula.json"))
now=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
with open("analysis/forward_log.csv","a",newline="") as fh:
    w=csv.writer(fh)
    for date in ["2026-10-18","2026-10-21"]:
        row=next(r for r in J["calendar"] if r["date"]==date)
        P=np.zeros((4,10))
        for f in J["weights"]: P+=np.array(J["tables"][f][row[f]])
        for op in ["Magnum","Sports Toto","Da Ma Cai"]:
            for r,n in enumerate(mf.top_numbers(P,5),1):
                w.writerow([now,date,"manual",op,r,f"{n:04d}"])
print("logged at", now)
EOF
git add analysis/manual_formula.py analysis/manual_formula.json analysis/build_manual_workbook.py analysis/manual_formula.xlsx analysis/forward_log.csv && git commit -q -m "Add hand-usable Vedic/Chinese digit formula, its forward test, and an Excel workbook

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q -u origin claude/4d-results-scraper-9ptbd5 && git log --oneline -1
```

## 36. 2026-10-17 02:55 — Score the manual formula on 14 Oct with leak-free tables

```bash
cd /home/user/4DPrediction; python3 - <<'EOF' 2>&1 | grep -v computed
import sys, json, numpy as np
sys.path.insert(0,"analysis"); sys.path.insert(0,"/tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad")
import astro_model as am, manual_formula as mf, conditional_extended as ce
from res_1014 import RES
data, codes, labels, rows, draws, year_of = am.load()
W=json.load(open("analysis/manual_formula.json"))["weights"]
import csv
dates=sorted({r["date"] for s in ["magnum","sportstoto","damacai"] for r in csv.DictReader(open(f"data/{s}.csv"))})
d14=dates.index("2026-10-14")
# tables from draws strictly before 14 Oct
m=rows["date"]<d14
sub={k:(v[m] if hasattr(v,'__len__') and len(v)==len(m) else v) for k,v in rows.items()}
sub["year"]=np.zeros(m.sum(),int)
tab=mf.digit_tables(codes, sub, list(W), 1)
ctx=ce.date_context("2026-10-14")
print("parameters on 14 Oct:", {f:ctx[f] for f in W})
P=mf.points(tab,W,codes,d14)
picks=[f"{n:04d}" for n in mf.top_numbers(P,5)]
print("top 5:", picks)
BIG={"1st":2500,"2nd":1000,"3rd":500,"Special":180,"Consolation":60}
for op,res in RES["2026-10-14"].items():
    win={n:p for p,v in res.items() for n in v.split()}
    straight=[(n,win[n]) for n in picks if n in win]
    ibox=[(n,w,p) for n in picks for w,p in win.items() if w!=n and sorted(w)==sorted(n)]
    near=[(n,w,p) for n in picks for w,p in win.items() if sum(a==b for a,b in zip(n,w))==3]
    print(f"{op:<12} straight: {straight or 'none'}  i-Box: {ibox or 'none'}  3-of-4 digits in place: {near or 'none'}")
EOF
```

## 37. 2026-10-17 02:55 — Score manual formula on 14 Oct

```bash
cd /home/user/4DPrediction; python3 - <<'EOF' 2>&1 | grep -v computed
import sys, json, numpy as np
sys.path.insert(0,"analysis"); sys.path.insert(0,"/tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad")
import astro_model as am, manual_formula as mf, conditional_extended as ce
from res_1014 import RES
data, codes, labels, rows, draws, year_of = am.load()
W=json.load(open("analysis/manual_formula.json"))["weights"]
d14=int(rows["date"].max())
print("date index check:", d14, labels["weekday"][codes["weekday"][d14]], {f: labels[f][codes[f][d14]] for f in W})
m=rows["date"]<d14
sub={k:v[m] for k,v in rows.items()}
sub["year"]=np.zeros(m.sum(),int)
tab=mf.digit_tables(codes, sub, list(W), 1)
P=mf.points(tab,W,codes,d14)
picks=[f"{n:04d}" for n in mf.top_numbers(P,5)]
print("top 5 for 14 Oct (tables from draws up to 11 Oct):", picks)
for p in range(4):
    o=np.argsort(-P[p]); print(f"  position {p+1}: best {o[0]} ({P[p,o[0]]:.0f} pts), 2nd {o[1]} ({P[p,o[1]]:.0f})")
for op,res in RES["2026-10-14"].items():
    win={n:p for p,v in res.items() for n in v.split()}
    straight=[(n,win[n]) for n in picks if n in win]
    ibox=[(n,w,p) for n in picks for w,p in win.items() if w!=n and sorted(w)==sorted(n)]
    near=[(n,w,p) for n in picks for w,p in win.items() if sum(a==b for a,b in zip(n,w))==3]
    print(f"{op:<12} straight: {straight or 'none'}  i-Box: {ibox or 'none'}  3 of 4 digits in place: {near or 'none'}")
EOF
```

## 38. 2026-10-17 02:56 — Measure how much the tie-break drives the picks

```bash
cd /home/user/4DPrediction; python3 - <<'EOF' 2>&1 | grep -v computed
import sys, json, numpy as np
sys.path.insert(0,"analysis")
import astro_model as am, manual_formula as mf
J=json.load(open("analysis/manual_formula.json")); W=J["weights"]
for f,t in J["tables"].items():
    a=np.array(list(t.values())); print(f"{f:<16} w={W[f]}  values {len(t)}  points range {a.min()}..{a.max()}  share of zero cells {np.mean(a==0):.0%}")
data, codes, labels, rows, draws, year_of = am.load()
# over the 2018-2026 test: how often is the best digit decided by the tie-break (max shared by >1 digit)?
ties=tot=0; nine=0
for y in range(2018,2027):
    tab=mf.digit_tables(codes, rows, list(W), y)
    for d in sorted({d for (d,o) in draws if year_of[d]==y}):
        P=mf.points(tab,W,codes,d)
        for p in range(4):
            mx=P[p].max(); tot+=1; ties+=(P[p]==mx).sum()>1; nine+= P[p].argmax()==9 or (P[p][9]==mx)
print(f"positions where the best digit was a tie broken toward the higher digit: {ties}/{tot} = {ties/tot:.0%}")
EOF
```

## 39. 2026-10-17 02:56 — Re-test the manual formula with proper scaling

```bash
cd /home/user/4DPrediction; python3 - <<'EOF' 2>&1 | grep -v computed
import sys, json, math, numpy as np
sys.path.insert(0,"analysis")
import astro_model as am, manual_formula as mf
J=json.load(open("analysis/manual_formula.json")); W=J["weights"]
data, codes, labels, rows, draws, year_of = am.load()
for scale in (10000,):
    h=e=pay=0; nd=0; ties=tot=0
    for y in range(2018,2027):
        tab=mf.digit_tables(codes, rows, list(W), y)
        for (d,o),(win,pr) in draws.items():
            if year_of[d]!=y: continue
            P=np.zeros((4,10))
            for f,w in W.items(): P+=np.round(scale*w*tab[f][codes[f][d]])
            for p in range(4):
                tot+=1; ties+=(P[p]==P[p].max()).sum()>1
            picks=set(mf.top_numbers(P,5))
            h+=len(picks & set(win)); e+=5*len(win)/10000; nd+=1
            pay+=sum(am.BIG[p] for p,n in pr if n in picks)
    print(f"scale {scale}: top-5 {h} wins vs {e:.1f} expected (x{h/e:.3f}, z={(h-e)/math.sqrt(e):+.2f}); Big RM{pay/(5*nd):.3f} per RM1; tie positions {ties/tot:.1%}")
EOF
```

## 40. 2026-10-17 02:56 — Fix scaling in formula and workbook, re-test, rebuild

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
p="analysis/manual_formula.py"; s=open(p).read()
s=s.replace("N_PARAMS = 6\n","N_PARAMS = 6\nSCALE = 10000   # points per unit of weighted log-lift; 100 rounded most cells to 0 (see REPORT section 10)\n")
s=s.replace("        P += np.round(100 * w * tables[f][codes[f][date_ix]])","        P += np.round(SCALE * w * tables[f][codes[f][date_ix]])")
s=s.replace("    tables = {f: {str(labels[f][v]): np.round(100 * w * tab[f][v]).astype(int).tolist()",
            "    tables = {f: {str(labels[f][v]): np.round(SCALE * w * tab[f][v]).astype(int).tolist()")
s=s.replace("    TABLE_f[v][p][d] = round( 100 * w_f * log[ p(d at p | f = v) / p(d at p) ] )",
            "    TABLE_f[v][p][d] = round( 10000 * w_f * log[ p(d at p | f = v) / p(d at p) ] )")
open(p,"w").write(s)
b="analysis/build_manual_workbook.py"; s=open(b).read()
s=s.replace('tb.cell(r + 1, 1, "Points = round(100 x weight','tb.cell(r + 1, 1, "Points = round(10000 x weight')
s=s.replace('''    ("This was about the 16th formula tested in this project. Allowing for that, a result this good happens by luck "
     "roughly 1 time in 5-10.", NORM),
    ("The picks are mostly 9-heavy numbers (9999, 9989, 9899, 9998, 8999 ...) and stay the same for weeks, "
     "because most of the six parameters change only monthly or yearly.", NORM),
    ("The return above RM1 comes from a handful of prizes (2 x 1st, 9 x 2nd in 4,186 draws) and can disappear with "
     "the next few draws. Treat it as a hypothesis under forward test, not an edge.", NORM),''',
'''    ("This formula performs like random picking on unseen draws. An earlier version of this workbook (points "
     "x100) looked better (1.37x), but that came from a rounding artefact: most table cells were 0 and ties were "
     "broken toward digit 9. With the tables at x10000 the result above is what is left.", NORM),
    ("Most of the six parameters change only monthly or yearly, so the picks stay similar for weeks.", NORM),
    ("Treat the numbers as a reproducible way of choosing, not as more likely winners.", NORM),''')
open(b,"w").write(s)
EOF
python3 analysis/manual_formula.py 2>&1 | grep -A12 '"top5"' | head -8; python3 analysis/build_manual_workbook.py && python3 /root/.claude/skills/synced/981f7279-2cd5-466c-9d0a-1ea18c88fa31_71864801-9a9c-44ca-8106-82c0b941d4fd/xlsx/scripts/recalc.py analysis/manual_formula.xlsx 120
```

## 41. 2026-10-17 02:58 — Verify, score 14 Oct, and log corrected picks

```bash
cd /home/user/4DPrediction; python3 - <<'EOF' 2>&1 | grep -v computed
import sys, json, csv, datetime as dt, subprocess, numpy as np
sys.path.insert(0,"analysis"); sys.path.insert(0,"/tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad")
from openpyxl import load_workbook
import astro_model as am, manual_formula as mf
from res_1014 import RES
J=json.load(open("analysis/manual_formula.json")); W=J["weights"]
def py_top5(date):
    row=next(r for r in J["calendar"] if r["date"]==date)
    P=np.zeros((4,10))
    for f in W: P+=np.array(J["tables"][f][row[f]])
    return [f"{n:04d}" for n in mf.top_numbers(P,5)]
ws=load_workbook("analysis/manual_formula.xlsx",data_only=True)["Predict"]
xl=[ws.cell(7+k,17).value for k in range(5)]
print("18 Oct python", py_top5("2026-10-18"), "excel", xl, "OK" if xl==py_top5("2026-10-18") else "MISMATCH")
# 14 Oct, leak-free
data, codes, labels, rows, draws, year_of = am.load()
d14=int(rows["date"].max()); m=rows["date"]<d14
sub={k:v[m] for k,v in rows.items()}; sub["year"]=np.zeros(m.sum(),int)
tab=mf.digit_tables(codes, sub, list(W), 1)
picks=[f"{n:04d}" for n in mf.top_numbers(mf.points(tab,W,codes,d14),5)]
print("corrected formula, 14 Oct:", picks)
for op,res in RES["2026-10-14"].items():
    win={n:p for p,v in res.items() for n in v.split()}
    print(f"  {op:<12} straight {[(n,win[n]) for n in picks if n in win] or 'none'}; i-Box "
          f"{[(n,w,p) for n in picks for w,p in win.items() if w!=n and sorted(w)==sorted(n)] or 'none'}")
now=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
with open("analysis/forward_log.csv","a",newline="") as fh:
    w=csv.writer(fh)
    for date in ["2026-10-18","2026-10-21"]:
        for op in am.OPS:
            for r,n in enumerate(py_top5(date),1): w.writerow([now,date,"manual_v2",op,r,n])
print("18 Oct:", py_top5("2026-10-18"), " 21 Oct:", py_top5("2026-10-21"), " logged", now)
EOF
```

## 42. 2026-10-17 02:58 — Report the correction, commit and push

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
s=open("analysis/REPORT.md").read()
sec='''## 10. A hand-usable formula, and a correction

`python3 analysis/manual_formula.py`, then `python3 analysis/build_manual_workbook.py`
→ `analysis/manual_formula.xlsx`. Enter a date in the Predict sheet and the
workbook shows the top 5 numbers.

```
Points(position p, digit d) = Σ over 6 parameters  TABLE_f[value on the date][p][d]
TABLE_f[v][p][d] = round(10000 · w_f · log[p(d at p | f = v) / p(d at p)])
Number #1 = best digit per position; #2–#5 = next best of the 16 best/2nd-best combinations
```

The six parameters, chosen on 2012–2017 by the likelihood of their digit term
alone and then frozen: Chinese year yin/yang (w 0.3), Venus combust (0.3),
Jupiter combust (0.3), masa (0.1), Chinese year stem (0.1) and Chinese lunar
day (0.1).

**Correction.** The first version used `round(100 · w · …)`. At that scale
three of the six tables were entirely 0 and most other cells were 0. In 71% of
digit positions the "best" digit was a tie, settled by the tie-break "higher
digit wins", so the picks were mostly 9s (9999, 9989, 9899 …). That version
appeared to do well on 2018–2026: top 5 1.37×, z = +2.6, RM1.05 per RM1. It
even passed a random-swap check (p = 0.007). But the result belonged to the
tie-break, not to the parameters, and it was not the formula as specified.
With the tables at ×10000 (ties in 1.7% of positions):

| | Wins (top 5) | Random | Lift | Big RM1 |
|---|---|---|---|---|
| Formula as specified (×10000) | 49 | 48.1 | 1.02× (z = +0.1) | RM0.63 |

That is random-level performance. The 9-heavy result is not evidence of
anything: it came from one of very many ways of choosing numbers that this
project has now tried. Both versions' picks for 18 and 21 Oct are in the
forward log (`manual` = first version, `manual_v2` = corrected).

'''
s=s.replace("## Conclusion\n", sec+"## Conclusion\n")
open("analysis/REPORT.md","w").write(s)
EOF
git add analysis && git commit -q -m "Fix manual formula scaling (x100 rounded tables to 0, picks were the tie-break); re-test, rebuild workbook, report section 10

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q -u origin claude/4d-results-scraper-9ptbd5 && git log --oneline -1 && git status --short
```

## 43. 2026-10-17 03:02 — Add date cutoff and run ML models for 14 Oct

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
p="analysis/ml_model.py"; s=open(p).read()
s=s.replace('''def walk(predict_dates=None, k=10):
    t0 = time.time()
    data, codes, labels, rows, draws, year_of = am.load()''','''def walk(predict_dates=None, k=10, before=None):
    t0 = time.time()
    data, codes, labels, rows, draws, year_of = am.load()
    if before:  # use only draws strictly before this date (leak-free predictions for a past date)
        import csv as _csv
        dates = sorted({r["date"] for op, stem in cn.OPERATORS.items()
                        for r in _csv.DictReader(open(os.path.join(ROOT, "data", f"{stem}.csv")))
                        if (op, r["date"]) not in cn.EXCLUDE})
        cut = sum(d < before for d in dates)
        keep = rows["date"] < cut
        rows = {key: v[keep] for key, v in rows.items()}
        draws = {key: v for key, v in draws.items() if key[0] < cut}''')
s=s.replace('''    ap.add_argument("--log", action="store_true", help="append the picks to analysis/forward_log.csv")''',
'''    ap.add_argument("--log", action="store_true", help="append the picks to analysis/forward_log.csv")
    ap.add_argument("--before", help="use only draws before this date (YYYY-MM-DD)")''')
s=s.replace('''        res = walk(predict_dates=a.date or [dt.date.today().isoformat()], k=a.k)''',
'''        res = walk(predict_dates=a.date or [dt.date.today().isoformat()], k=a.k, before=a.before)''')
open(p,"w").write(s)
EOF
python3 analysis/ml_model.py predict --date 2026-10-14 --before 2026-10-14 --k 10 > /tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad/ml1014.log 2>&1; echo "exit $?" >> /tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad/ml1014.log
```

## 44. 2026-10-17 03:14 — Save the search as a reusable script and commit

```bash
cd /home/user/4DPrediction; S=/tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad; python3 - <<EOF
s=open("$S/search1014.py").read()
s=s.replace('sys.path.insert(0, "analysis"); sys.path.insert(0, "/tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad")\nimport astro_model as am\nfrom res_1014 import RES\n',
'''import csv, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am
DATE = sys.argv[1] if len(sys.argv) > 1 else "2026-10-14"
''')
s=s.replace('d14 = int(rows["date"].max())','''_dates = sorted({r["date"] for op, stem in am.cn.OPERATORS.items()
                 for r in csv.DictReader(open(os.path.join(am.ROOT, "data", f"{stem}.csv"))) if (op, r["date"]) not in am.cn.EXCLUDE})
d14 = _dates.index(DATE)''')
s=s.replace('R = RES["2026-10-14"]\nwin = {op: {int(n): p for p, v in R[op].items() for n in v.split()} for op in am.OPS}',
'''win = {op: {} for op in am.OPS}
for op, stem in am.cn.OPERATORS.items():
    for r in csv.DictReader(open(os.path.join(am.ROOT, "data", f"{stem}.csv"))):
        if r["date"] == DATE:
            win[op][int(r["4d_number"])] = r["prize"]''')
s=s.replace('print(f"{len(res)} formulas, 30 picks each, 14 Oct 2026")','print(f"{len(res)} formulas, 30 picks each, {DATE}")')
s=s.replace('''import json; json.dump({"best": [best[3], best[4]], "picks": {op: [f"{n:04d}" for n in ps] for op, ps in best[5].items()}},
                       open("/tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad/best1014.json", "w"))''',
'''print("winner's picks:", {op: [f"{n:04d}" for n in ps] for op, ps in best[5].items()})''')
s='"""Try every single-parameter Vedic / Chinese formula (468) on one past draw, compare with random picks,\\nthen test the best one on 2018-2026. Shows how a formula that \\'predicts\\' one draw does on others.\\n\\nUsage: python3 analysis/search_single_draw.py 2026-10-14\\n"""\\n'+s
open("analysis/search_single_draw.py","w").write(s)
EOF
python3 analysis/search_single_draw.py 2026-10-14 2>&1 | grep -E "straight hits|winner" | head -3
git add analysis/search_single_draw.py && git commit -q -m "Add single-draw formula search with random baseline and out-of-sample check

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q -u origin claude/4d-results-scraper-9ptbd5 && git log --oneline -1
```

## 45. 2026-10-17 03:24 — Fix and run the held-out test for non-ML formulas

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
p="analysis/last_draws_test.py"; s=open(p).read()
s=s.replace('''    held = [d for d in dates if any(results(d)[op] for op in OPS)][-a.n:]''','''    held = dates[-a.n:]''')
s=s.replace('''        tab7 = pm.Tables(pdata, pcodes, pfactors, pdata["date"] < di,
                         alphas=[10], betas=[50], half_lives=[300])''','''        tab7 = pm.Tables(pdata, pcodes, pfactors, pdata["date"] < di,
                         alphas=sorted({int(k.split("_a")[1]) for k in pweights if "_a" in k}) or [10],
                         betas=sorted({int(k.split("_b")[1]) for k in pweights if "_b" in k}) or [50],
                         half_lives=sorted({int(k.split("_h")[1]) for k in pweights if "_h" in k}) or [0])''')
open(p,"w").write(s)
EOF
grep -n "held = \|alphas=sorted" analysis/last_draws_test.py; tail -3 data/magnum.csv | cut -c1-12; python3 analysis/last_draws_test.py --n 3 2>&1 | grep -v computed | tail -40
```

## 46. 2026-10-17 03:25 — Check overlap between formulas' hits

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
import json
r=json.load(open("analysis/last_draws_results.json"))
for k in ["single jupiter_nakshatra / num_op","single saturn_combust / num_op","single yellow_black_path / num_op"]:
    print(k, {D: r["formulas"][k][D]["hits"] for D in r["held_out"]})
# distinct winning numbers caught by any single formula, per date
for D in r["held_out"]:
    caught={}
    for k,v in r["formulas"].items():
        if k.startswith("single"):
            for h in v[D]["hits"]: caught.setdefault(h,0); caught[h]+=1
    print(D, "distinct winning numbers caught by the 468 formulas:", len(caught), "| how many formulas caught each:", sorted(caught.values(), reverse=True)[:8])
EOF
```

## 47. 2026-10-17 03:48 — Compute worked examples for the three formulas

```bash
cd /home/user/4DPrediction; python3 - <<'EOF' 2>&1 | grep -v computed
import sys, csv, os, numpy as np
sys.path.insert(0,"analysis")
import astro_model as am
data, codes, labels, rows, draws, year_of = am.load()
dates = sorted({r["date"] for op, stem in am.cn.OPERATORS.items() for r in csv.DictReader(open(f"data/{stem}.csv")) if (op, r["date"]) not in am.cn.EXCLUDE})
DIG=am.DIG
def explain_num(f, D, op, n):
    di=dates.index(D); o=am.OPS.index(op); v=codes[f][di]
    m=(rows["date"]<di)&(rows["op_ix"]==o)
    d,num=rows["date"][m],rows["num"][m]
    same=codes[f][d]==v
    n_v=same.sum(); c=(num[same]==n).sum(); T=len(num); all_n=(num==n).sum()
    q=(all_n+20)/(T+20*10000)
    L=np.log((c+10)/(n_v*q+10))
    ndraws=len(set(d[same]))
    # rank among all numbers
    t=np.log((np.bincount(num[same],minlength=10000)+10)/(n_v*(np.bincount(num,minlength=10000)+20)/(T+200000)+10))
    rank=int((t>t[n]).sum())+1
    print(f"{f} on {D} = {labels[f][v]} | {op}: {ndraws} past draws with this value ({n_v} winning numbers); "
          f"{n:04d} won {c} times on them (expected {n_v*q:.2f}); overall {all_n} wins in {T} winners; "
          f"score log(({c}+10)/({n_v*q:.2f}+10)) = {L:.3f}; rank {rank} of 10000")
explain_num("jupiter_nakshatra","2026-10-10","Sports Toto",1236)
explain_num("yellow_black_path","2026-10-14","Sports Toto",305)
# digit formula month_branch / dig_op for 0606 on 14 Oct (Sports Toto)
f,D,op,n="month_branch","2026-10-14","Sports Toto",606
di=dates.index(D); o=am.OPS.index(op); v=codes[f][di]
m=(rows["date"]<di)&(rows["op_ix"]==o); d,num=rows["date"][m],rows["num"][m]; same=codes[f][d]==v
base=np.stack([np.bincount(DIG[num,p],minlength=10) for p in range(4)])/len(num)
cnt=np.stack([np.bincount(DIG[num[same],p],minlength=10) for p in range(4)])
pc=(cnt+50*base)/(same.sum()+50)
print(f"{f} on {D} = {labels[f][v]} | {op}: {len(set(d[same]))} past draws, {same.sum()} winning numbers")
tot=0
for p in range(4):
    dd=DIG[n,p]; l=np.log(pc[p,dd]/base[p,dd]); tot+=l
    best=np.argsort(-(pc[p]/base[p]))[:3]
    print(f"  position {p+1}: digit {dd} share {100*pc[p,dd]:.2f}% vs overall {100*base[p,dd]:.2f}% -> {l:+.4f}; top digits here {best.tolist()}")
s=sum(np.log(pc[p][DIG[:,p]]/base[p][DIG[:,p]]) for p in range(4))
print(f"  total {tot:+.4f}; rank of 0606 {int((s>s[n]).sum())+1} of 10000")
EOF
```

## 48. 2026-10-17 03:51 — Add frozen-training and multi-date ML options

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
p="analysis/last_draws_test.py"; s=open(p).read()
s=s.replace('''def ml_picks(path):
    out = {}
    for line in open(path):''','''def ml_picks_multi(path):
    """{date: {model: {op: picks}}} from a multi-date ml_model.py predict log."""
    out, cur = {}, None
    for line in open(path):
        m = re.match(r"Picks for (\\d{4}-\\d{2}-\\d{2})", line)
        if m:
            cur = out.setdefault(m.group(1), {})
            continue
        m = re.match(r"\\s+(\\S+)\\s+(Magnum|Sports Toto|Da Ma Cai)\\s+([\\d ]+)$", line.rstrip())
        if m and cur is not None:
            cur.setdefault(f"ML {m.group(1)}", {})[m.group(2)] = [int(x) for x in m.group(3).split()]
    return out


SELECTED = ["single jupiter_nakshatra / num_op", "single yellow_black_path / num_op", "single month_branch / dig_op"]


def ml_picks(path):
    out = {}
    for line in open(path):''')
s=s.replace('''    ap.add_argument("--ml", action="append", default=[])
    a = ap.parse_args()
    ml_logs = dict(x.split("=", 1) for x in a.ml)''','''    ap.add_argument("--ml", action="append", default=[])
    ap.add_argument("--ml-multi", help="one ml_model.py predict log holding several dates")
    ap.add_argument("--frozen", action="store_true",
                    help="train once on draws before the first held-out date (no updating between held-out draws)")
    a = ap.parse_args()
    ml_logs = dict(x.split("=", 1) for x in a.ml)
    ml_multi = ml_picks_multi(a.ml_multi) if a.ml_multi else {}''')
old='''    for D in held:
        di = dates.index(D)
        win = results(D)
        m = rows["date"] < di
        c = am.Counts(am.VEDIC + am.CHINESE, codes)
        c.add(rows["date"][m], rows["op_ix"][m], rows["num"][m])'''
new='''    cache = {}
    for D in held:
        di = dates.index(D)
        win = results(D)
        cut = dates.index(held[0]) if a.frozen else di      # training uses draws before `cut` only
        m = rows["date"] < cut
        if cut not in cache:
            c = am.Counts(am.VEDIC + am.CHINESE, codes)
            c.add(rows["date"][m], rows["op_ix"][m], rows["num"][m])
            cache = {cut: c}
        c = cache[cut]'''
assert old in s; s=s.replace(old,new)
s=s.replace('''        tab7 = pm.Tables(pdata, pcodes, pfactors, pdata["date"] < di,''','''        tab7 = pm.Tables(pdata, pcodes, pfactors, pdata["date"] < cut,''')
s=s.replace('''        if D in ml_logs:
            for name, picks in ml_picks(ml_logs[D]).items():
                table.setdefault(name, {})[D] = score(picks, win)''','''        if D in ml_logs:
            for name, picks in ml_picks(ml_logs[D]).items():
                table.setdefault(name, {})[D] = score(picks, win)
        for name, picks in ml_multi.get(D, {}).items():
            table.setdefault(name, {})[D] = score(picks, win)
        for k in SELECTED:
            table[k][D]["picks_list"] = None''')
s=s.replace('''    print(f"\\nHeld-out draws: {', '.join(held)} (each predicted from earlier draws only)")''','''    mode = f"trained once on draws before {held[0]}" if a.frozen else "each predicted from all earlier draws"
    print(f"\\nHeld-out draws: {', '.join(held)} ({mode})")''')
s=s.replace('''    out = {"held_out": held, "formulas": table,''','''    print("\\nSelected formulas, draw by draw:")
    for k in SELECTED:
        st, pay, ib, npk = tot(table[k])
        print(f"  {k}: total {st} straight hits, {ib} i-Box, Big RM{pay} back on RM{npk}")
        for D in held:
            x = table[k][D]
            print(f"    {D}: {x['straight']} hit(s) {x['hits'] or ''}  i-Box {x['ibox']}  RM{x['payout']} / RM{x['picks']}")
    rs_tot = [sum(random_scores[D][i]["straight"] for D in held) for i in range(468)]
    rp_tot = [sum(random_scores[D][i]["payout"] for D in held) for i in range(468)]
    print(f"\\nRandom baseline over these draws (468 sets of 30 picks per draw): straight hits per set "
          f"mean {np.mean(rs_tot):.2f}, {np.mean(np.array(rs_tot) >= 1):.0%} of sets got at least one, "
          f"{np.mean(np.array(rs_tot) >= 2):.0%} got two or more; mean Big return RM{np.mean(rp_tot):.0f} on RM{30 * len(held)}")
    out = {"held_out": held, "frozen": a.frozen, "formulas": table,''')
s=s.replace('''    with open(os.path.join(ROOT, "analysis", "last_draws_results.json"), "w") as fh:''','''    name = f"last{len(held)}_{'frozen' if a.frozen else 'rolling'}_results.json"
    with open(os.path.join(ROOT, "analysis", name), "w") as fh:''')
open(p,"w").write(s)
EOF
grep -n 'picks_list' analysis/last_draws_test.py
```

## 49. 2026-10-17 03:58 — Score the next three formulas and long-test all six

```bash
cd /home/user/4DPrediction; python3 - <<'EOF' 2>&1 | grep -v computed
import json, sys
sys.path.insert(0,"analysis")
r=json.load(open("analysis/last5_frozen_results.json"))
NEW=["single saturn_combust / num_op","single mercury_nakshatra / box","single mars_retrograde / box_op"]
OLD=["single jupiter_nakshatra / num_op","single yellow_black_path / num_op","single month_branch / dig_op"]
for k in NEW+OLD:
    v=r["formulas"][k]; tot=sum(v[D]["straight"] for D in r["held_out"]); pay=sum(v[D]["payout"] for D in r["held_out"])
    row=" | ".join(f"{D[5:]}: {v[D]['straight']}{' '+str(v[D]['hits']) if v[D]['hits'] else ''}" for D in r["held_out"])
    print(f"{k:<38} total {tot}, RM{pay}/RM150 | {row}")
import astro_model as am
data, codes, labels, rows, draws, year_of = am.load(); am._YEAR = year_of
print("\n2018-2026 walk-forward (each draw predicted from earlier draws only):")
for k in OLD+NEW:
    _, f, _, kind = k.split()
    out,_ = am.forward_test(k, [(f, kind, 1.0)], codes, rows, draws)
    a=out["All"]
    print(f"  {f+' / '+kind:<30} top10 {a['top10']['hits']} vs {a['top10']['expected']} (x{a['top10']['lift']}, z={a['top10']['z']:+.1f})  "
          f"top23 x{a['top23']['lift']}  Big top10 RM{a['big_return_top10']['per_RM1']} per RM1  "
          f"by operator top10: " + ", ".join(f"{op} x{out[op]['top10']['lift']}" for op in am.OPS))
EOF
```

## 50. 2026-10-17 03:59 — Log the six formulas' picks for upcoming draws

```bash
cd /home/user/4DPrediction; python3 - <<'EOF' 2>&1 | grep -v computed
import sys, csv, datetime as dt, numpy as np
sys.path.insert(0,"analysis")
import astro_model as am
data, codes, labels, rows, draws, year_of = am.load()
SIX=[("jupiter_nakshatra","num_op"),("yellow_black_path","num_op"),("month_branch","dig_op"),
     ("saturn_combust","num_op"),("mercury_nakshatra","box"),("mars_retrograde","box_op")]
facs=sorted({f for f,_ in SIX})
now=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
out=[]
for date in ["2026-10-18","2026-10-21"]:
    ix, codes2, ctx = am.date_codes(date, codes, labels, facs)
    c=am.Counts(facs, codes2); c.add(rows["date"], rows["op_ix"], rows["num"])
    print(f"{date}: " + ", ".join(f"{f}={ctx[f]}" for f in facs))
    for f,kind in SIX:
        for o,op in enumerate(am.OPS):
            t=c.term(f,int(codes2[f][ix]),kind,o)
            picks=np.argsort(-(t+np.arange(10000)*1e-12))[:10]
            print(f"  {f+'/'+kind:<26} {op:<12} "+" ".join(f"{n:04d}" for n in picks))
            for r,n in enumerate(picks,1): out.append([now,date,f"single_{f}/{kind}",op,r,f"{n:04d}"])
with open("analysis/forward_log.csv","a",newline="") as fh: csv.writer(fh).writerows(out)
print("logged", len(out), "picks at", now)
EOF
git add analysis/forward_log.csv && git commit -q -m "Log the six selected single-parameter formulas' picks for 18 and 21 Oct before the draws

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q -u origin claude/4d-results-scraper-9ptbd5 && git log --oneline -1
```

## 51. 2026-10-17 04:30 — Let Counts skip number-level tables for joint factors

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
p="analysis/astro_model.py"; s=open(p).read()
s=s.replace('''    def __init__(self, factors, codes):
        self.factors, self.codes = factors, codes
        self.V = {f: int(codes[f].max()) + 2 for f in factors}       # +1 spare row for unseen values
        z = np.zeros
        self.num = {f: z((4, self.V[f], 10000), np.float32) for f in factors}   # [pooled, op0, op1, op2]''',
'''    def __init__(self, factors, codes, num_factors=None):
        """num_factors: factors that need number-level tables (default: all). Leaving large
        joint-pair factors out saves V x 10000 floats per factor."""
        self.factors, self.codes = factors, codes
        self.V = {f: int(codes[f].max()) + 2 for f in factors}       # +1 spare row for unseen values
        z = np.zeros
        nf = set(factors if num_factors is None else num_factors)
        self.num = {f: z((4, self.V[f], 10000), np.float32) if f in nf else None
                    for f in factors}                                  # [pooled, op0, op1, op2]''')
s=s.replace('''                if bulk:
                    self.num[f][s] += np.bincount(v * 10000 + n, minlength=V * 10000).reshape(V, 10000)''',
'''                if bulk:
                    if self.num[f] is not None:
                        self.num[f][s] += np.bincount(v * 10000 + n, minlength=V * 10000).reshape(V, 10000)''')
s=s.replace('''                else:
                    np.add.at(self.num[f][s], (v, n), 1)''','''                else:
                    if self.num[f] is not None:
                        np.add.at(self.num[f][s], (v, n), 1)''')
open(p,"w").write(s)
EOF
python3 -c "import ast;ast.parse(open('analysis/astro_model.py').read())" && echo ok
```

## 52. 2026-10-17 04:31 — Pass number-level factor list through forward_test

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
p="analysis/astro_model.py"; s=open(p).read()
s=s.replace('''def counts_before(factors, codes, rows, year):
    c = Counts(factors, codes)''','''def counts_before(factors, codes, rows, year, num_factors=None):
    c = Counts(factors, codes, num_factors)''')
old='''    factors = sorted({f for f, _, _ in formula})
    c = counts_before(factors, codes, rows, VALID_END)'''
assert old in s
s=s.replace(old,'''    factors = sorted({f for f, _, _ in formula})
    num_f = sorted({f for f, k, _ in formula if k.split("_")[0] == "num"})
    c = counts_before(factors, codes, rows, VALID_END, num_f)''')
open(p,"w").write(s)
EOF
grep -n "num_f\b\|num_factors" analysis/astro_model.py | head
```

## 53. 2026-10-17 04:34 — Test top joint pairs and gather lead comparison

```bash
cd /home/user/4DPrediction; python3 - <<'EOF' 2>&1 | grep -v "computed\|forward test:"
import sys, json
sys.path.insert(0,"analysis")
import astro_model as am, pairs_test as pt
data, codes, labels, rows, draws, year_of = am.load(); am._YEAR=year_of
dates=pt.all_dates(); held=dates[-5:]; wins={D:pt.results(D) for D in held}
J=[("venus_retrograde","day_element","box",0.42),("venus_retrograde","day_stem","box",0.38),("day_stem","day_element","box",0.35)]
res=[]
for f1,f2,k,w in J:
    formula=[(pt.joint_key(codes,f1,f2),k,w)]
    out,_=am.forward_test("j",formula,codes,rows,draws); a=out["All"]
    l5=pt.last5(formula,codes,rows,dates,held,wins)
    res.append({"formula":f"{f1} x {f2} (joint {k})","wf":a["top10"],"big":a["big_return_top10"]["per_RM1"],"last5":l5})
    print(f"{f1} x {f2} joint/{k}: 2018-2026 x{a['top10']['lift']} z={a['top10']['z']:+.1f} Big RM{a['big_return_top10']['per_RM1']}; last5 hits "
          + " | ".join(f"{D[5:]}: {', '.join(l5[D]['hits']) or '-'}" for D in held))
r=json.load(open("analysis/pairs_results.json")); r["joint_top3"]=res; json.dump(r,open("analysis/pairs_results.json","w"),indent=1,default=float)
nk=json.load(open("analysis/nakshatra_results.json"))["frozen_last5"]
for k in ["saturn_nakshatra / num_op","kp_asc_star_lord@19:30 / num","kp_asc_star_lord / dig_op"]:
    print(k, "last5:", {D[5:]: nk[k][D][0] for D in held})
EOF
git add analysis/pairs_results.json && git commit -q -m "Pair test results incl. top joint pairs

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q -u origin claude/4d-results-scraper-9ptbd5 && git log --oneline -1
```

## 54. 2026-10-17 05:02 — Vectorise recurrence lookup, fix permutations, check combo indexing

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
p="analysis/strategies_test.py"; s=open(p).read()
old='''        before = np.flatnonzero(dj < cut)
        lastpos = {}
        for jj in before[np.argsort(dj[before], kind="stable")]:
            lastpos[jc[jj]] = jj
        P = np.array([R16[lastpos[c]] if c in lastpos else np.full(16, -1) for c in jc[hmask]])'''
new='''        before = np.flatnonzero(dj < cut)                              # keys are already in time order
        rb_ = before[::-1]
        u, first = np.unique(jc[rb_], return_index=True)                # last earlier draw per cell
        lastj = rb_[first]
        hc = jc[hmask]
        pos = np.minimum(np.searchsorted(u, hc), len(u) - 1)
        found = u[pos] == hc
        P = np.where(found[:, None], R16[lastj[pos]], -1)'''
assert old in s; s=s.replace(old,new)
old=s[s.index("    perms = np.array("):s.index("    s4 = {")]
new='''    def perms16(n):
        ps = sorted({int("".join(q)) for q in itertools.permutations(f"{n:04d}")}, key=lambda x: (x != n, x))[:16]
        return ps + [-1] * (16 - len(ps))
    perms = np.array([perms16(int(n)) for n in Wm[:, 0]])
'''
s=s.replace(old,new)
open(p,"w").write(s)
EOF
python3 -c "import ast;ast.parse(open('/home/user/4DPrediction/analysis/strategies_test.py').read())" && python3 -c "
import numpy as np, itertools
BITS=np.array(list(itertools.product((0,1),repeat=4))); top2=np.random.randint(0,10,(3,4,2))
d=np.take_along_axis(top2,BITS.T[None,:,:],2); print(d.shape, top2[0,:,0], d[0,:,0])"
```

## 55. 2026-10-17 05:09 — Check a no-parameter positional baseline

```bash
cd /home/user/4DPrediction; python3 - <<'EOF' 2>&1 | grep -v computed
# Diagnostic: positional top-1 with NO parameter at all (operator-wide digit counts), yearly refresh, same scoring
import sys, numpy as np
sys.path.insert(0,"analysis")
import strategies_test as st
codes, rows, draws, keys, dj, oj, yj, Wm, Pm, R16 = st.setup()
DIG=st.DIG; rn,ro,ry=rows["num"],rows["op_ix"],rows["year"]; nwin=(Wm>=0).sum(1)
for strat,sign in (("hot",-1),("cold",1)):
    for per,(a,b) in {"2012-2017":(2012,2018),"2018-2026":(2018,2027)}.items():
        h=e=0
        for y in range(a,b):
            m=ry<y; sel=yj==y
            for o in range(3):
                C=np.stack([np.bincount(DIG[rn[m&(ro==o)],p],minlength=10) for p in range(4)])
                d=np.argsort(sign*C,1)[:,0]; n=int((d*st.POW).sum())
                s2=sel&(oj==o)
                h+=int((Wm[s2]==n).any(1).sum()); e+=float(nwin[s2].sum()/10000)
        print(f"no-parameter positional {strat} top-1, {per}: {h} hits vs {e:.1f} expected (x{h/e:.2f})")
EOF
```

## 56. 2026-10-17 05:10 — See which numbers the no-parameter picks were and where the hits came from

```bash
cd /home/user/4DPrediction; python3 - <<'EOF' 2>&1 | grep -v computed
import sys, numpy as np, math
from collections import Counter
sys.path.insert(0,"analysis")
import strategies_test as st
codes, rows, draws, keys, dj, oj, yj, Wm, Pm, R16 = st.setup()
DIG=st.DIG; rn,ro,ry=rows["num"],rows["op_ix"],rows["year"]; nwin=(Wm>=0).sum(1)
OPS=["Magnum","Sports Toto","Da Ma Cai"]
for strat,sign in (("hot",-1),("cold",1)):
    hits=Counter(); picks=[]
    for y in range(2012,2027):
        m=ry<y
        for o in range(3):
            C=np.stack([np.bincount(DIG[rn[m&(ro==o)],p],minlength=10) for p in range(4)])
            n=int((np.argsort(sign*C,1)[:,0]*st.POW).sum()); picks.append((y,OPS[o],f"{n:04d}"))
            s2=(yj==y)&(oj==o); k=int((Wm[s2]==n).any(1).sum())
            if k: hits[(y,OPS[o],f"{n:04d}")]+=k
    print(strat, "distinct picks 2012-2026:", len({p[2] for p in picks}), "| hits:", dict(hits))
# how often does any single fixed number win 3+ times in a year for an operator? (luck reference)
cnt=Counter()
for j in range(len(Wm)):
    for n in Wm[j][Wm[j]>=0]: cnt[(yj[j],oj[j],n)]+=1
per_year=Counter(v for v in cnt.values())
print("distribution of wins per number per operator-year:", sorted(per_year.items())[:6])
EOF
```

## 57. 2026-10-17 05:10 — Score no-parameter rule on last 5, log its picks, commit

```bash
cd /home/user/4DPrediction; python3 - <<'EOF' 2>&1 | grep -v computed
import sys, csv, datetime as dt, numpy as np, itertools
sys.path.insert(0,"analysis")
import strategies_test as st
codes, rows, draws, keys, dj, oj, yj, Wm, Pm, R16 = st.setup()
DIG=st.DIG; rn,ro,rd=rows["num"],rows["op_ix"],rows["date"]
dates=st.all_dates(); held=dates[-5:]; cut=dates.index(held[0])
OPS=["Magnum","Sports Toto","Da Ma Cai"]
def picks(mask,o,sign):
    C=np.stack([np.bincount(DIG[rn[mask&(ro==o)],p],minlength=10) for p in range(4)]).astype(float)
    top2=np.argsort(sign*C,1)[:,:2]
    return [int((np.array([top2[p,b] for p,b in enumerate(bits)])*st.POW).sum()) for bits in itertools.product((0,1),repeat=4)]
for strat,sign in (("hot",-1),("cold",1)):
    tot1=tot16=0; pay16=0; det=[]
    for o in range(3):
        P=picks(rd<cut,o,sign)
        for D in held:
            j=keys.index((dates.index(D),o)); w=list(Wm[j]); 
            for i,n in enumerate(P):
                if n in w:
                    tot16+=1; pay16+=Pm[j][w.index(n)]; det.append(f"{D[5:]} {OPS[o]} {n:04d}")
                    if i==0: tot1+=1
    print(f"no-parameter {strat} positional, last 5 draws: top-1 {tot1} hits, top-16 {tot16} hits (Big RM{pay16:.0f} on RM240) {det}")
# log picks for 18 and 21 Oct (counts from all data; the same for both dates since no parameters)
now=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
out=[]
for strat,sign in (("hot",-1),("cold",1)):
    for o in range(3):
        P=picks(np.ones(len(rn),bool),o,sign)
        print(f"  {strat} {OPS[o]:<12} top-1 {P[0]:04d}; 16: {' '.join(f'{n:04d}' for n in P)}")
        for D in ("2026-10-18","2026-10-21"):
            for r,n in enumerate(P,1): out.append([now,D,f"positional_{strat}_noparam",OPS[o],r,f"{n:04d}"])
with open("analysis/forward_log.csv","a",newline="") as fh: csv.writer(fh).writerows(out)
print("logged", len(out), "at", now)
EOF
git add analysis/strategies_results.json analysis/forward_log.csv && git commit -q -m "Strategy test results; log no-parameter positional hot/cold picks for 18 and 21 Oct

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q -u origin claude/4d-results-scraper-9ptbd5 && git log --oneline -1
```

## 58. 2026-10-17 05:18 — Show frozen no-parameter picks and per-draw results

```bash
cd /home/user/4DPrediction; python3 - <<'EOF' 2>&1 | grep -v computed
import sys, numpy as np, itertools
sys.path.insert(0,"analysis")
import strategies_test as st
codes, rows, draws, keys, dj, oj, yj, Wm, Pm, R16 = st.setup()
DIG=st.DIG; rn,ro,rd=rows["num"],rows["op_ix"],rows["date"]
dates=st.all_dates(); held=dates[-5:]; cut=dates.index(held[0])
OPS=["Magnum","Sports Toto","Da Ma Cai"]; PR={2500:"1st",1000:"2nd",500:"3rd",180:"Special",60:"Consolation"}
for strat,sign in (("HOT",-1),("COLD",1)):
    print(f"== {strat} digits per position (counts from draws before {held[0]}) ==")
    tot1=tot16=pay=0
    for o in range(3):
        C=np.stack([np.bincount(DIG[rn[(rd<cut)&(ro==o)],p],minlength=10) for p in range(4)]).astype(float)
        top2=np.argsort(sign*C,1)[:,:2]
        P=[int((np.array([top2[p,b] for p,b in enumerate(bits)])*st.POW).sum()) for bits in itertools.product((0,1),repeat=4)]
        line=[]
        for D in held:
            j=keys.index((dates.index(D),o)); w=list(Wm[j])
            h=[(n, PR[int(Pm[j][w.index(n)])]) for n in P if n in w]
            tot16+=len(h); tot1+=int(P[0] in w); pay+=sum(int(Pm[j][w.index(n)]) for n,_ in h)
            line.append(f"{D[5:]}: " + (", ".join(f"{n:04d} {p}" for n,p in h) or "-"))
        print(f"  {OPS[o]:<12} #1 {P[0]:04d} | 16: {' '.join(f'{n:04d}' for n in P)}")
        print(f"  {'':<12} {' | '.join(line)}")
    print(f"  total: top-1 {tot1} hits (RM15 staked), top-16 {tot16} hits, Big RM{pay} back on RM240\n")
EOF
```

## 59. 2026-10-17 05:21 — Last-5 results for S1/S2 split by single and pair parameters

```bash
cd /home/user/4DPrediction; python3 - <<'EOF' 2>&1 | grep -v computed
import sys, itertools, numpy as np, json
sys.path.insert(0,"analysis")
import strategies_test as st
codes, rows, draws, keys, dj, oj, yj, Wm, Pm, R16 = st.setup()
DIG=st.DIG; rn,ro,rd=rows["num"],rows["op_ix"],rows["date"]
dates=st.all_dates(); held=dates[-5:]; cut=dates.index(held[0])
hm=dj>=cut; W5,P5,o5,d5=Wm[hm],Pm[hm],oj[hm],dj[hm]
overall=np.stack([np.stack([np.bincount(DIG[rn[ro==o],p],minlength=10) for p in range(4)]) for o in range(3)]).astype(float)
overall/=overall.sum(2,keepdims=True)
F=st.FACT; mc=rd<cut
PR={2500:"1st",1000:"2nd",500:"3rd",180:"Special",60:"Consol"}
OPS=["Magnum","Toto","DMC"]
res={}
for fs in [(f,) for f in F]+list(itertools.combinations(F,2)):
    c=np.zeros(len(codes[F[0]]),np.int64)
    for f in fs: c=c*(int(codes[f].max())+1)+codes[f]
    U=int(c.max())+1; rc=c[rd]*3+ro; jc=c[d5]*3+o5
    cnt=np.zeros(U*120)
    for p in range(4): cnt+=np.bincount(rc[mc]*40+p*10+DIG[rn[mc],p],minlength=U*120)
    C=cnt.reshape(U*3,4,10)[jc]+1e-6*overall[o5]
    for strat,sign in (("S1",-1),("S2",1)):
        top2=np.argsort(sign*C,2)[:,:,:2]
        P=(np.take_along_axis(top2,st.BITS.T[None,:,:],2)*st.POW[None,:,None]).sum(1)
        for k in (1,16):
            eq=(P[:,:k,None]==W5[:,None,:])
            hits=[f"{dates[d5[i]][5:]} {OPS[o5[i]]} {P[i,a]:04d} {PR[int(P5[i,b])]}" for i,a,b in zip(*np.nonzero(eq))]
            res[(strat,len(fs),k," x ".join(fs))]=(len(hits),int((eq*P5[:,None,:]).sum()),hits)
rng=np.random.default_rng(3); rnd={}
for k in (1,16):
    h=[int((rng.integers(0,10000,(15,k))[:,:,None]==W5[:,None,:]).any(2).sum()) for _ in range(20000)]
    rnd[k]=(np.mean(h),np.mean(np.array(h)>=1),np.mean(np.array(h)>=2))
for strat in ("S1","S2"):
    for npar,label in ((1,"single parameter (78)"),(2,"pair of parameters (3,003)")):
        for k in (1,16):
            v=[x for (s,n,kk,_),x in res.items() if s==strat and n==npar and kk==k]
            h=np.array([x[0] for x in v]); pay=np.array([x[1] for x in v])
            r=rnd[k]
            print(f"{strat} {label}, {k} pick(s)/operator-draw: hit>=1 {np.mean(h>=1):.0%} (random {r[1]:.0%}), "
                  f">=2 {np.mean(h>=2):.1%} (random {r[2]:.1%}), mean hits {h.mean():.3f} (random {r[0]:.3f}), "
                  f"mean Big RM{pay.mean():.0f} on RM{15*k}")
            best=sorted(((x[0],x[1],nm,x[2]) for (s,n,kk,nm),x in res.items() if s==strat and n==npar and kk==k),key=lambda t:(-t[0],-t[1]))[:3]
            for hh,pp,nm,hl in best: print(f"     {nm:<40} {hh} hits RM{pp}: {'; '.join(hl)}")
json.dump({f"{s}|{n}|{k}|{nm}":x for (s,n,k,nm),x in res.items()},open("analysis/strategies_last5_detail.json","w"))
EOF
```

## 60. 2026-10-17 05:37 — Show a worked example for one draw

```bash
cd /home/user/4DPrediction; python3 - <<'EOF' 2>&1 | grep -v computed
import sys, itertools, numpy as np
sys.path.insert(0,"analysis")
import strategies_test as st, astro_model as am
codes, rows, draws, keys, dj, oj, yj, Wm, Pm, R16 = st.setup()
data, codes2, labels, *_ = am.load()
DIG=st.DIG; rn,ro,rd=rows["num"],rows["op_ix"],rows["date"]
dates=st.all_dates(); cut=dates.index("2026-10-04"); di=dates.index("2026-10-14"); o=0  # Magnum
fs=["mars_nakshatra","mars_rashi","mercury_combust"]
today={f: labels[f][codes[f][di]] for f in fs}
print("Draw to predict: Magnum, Wed 14 Oct 2026, 7pm")
print("Its parameter values:", today)
match=np.ones(len(rd),bool)
for f in fs: match&=codes[f][rd]==codes[f][di]
m=match&(ro==o)&(rd<cut)
mdates=sorted({dates[d] for d in rd[m]})
print(f"Past Magnum draws (before 4 Oct) with ALL three values the same: {len(mdates)} draws "
      f"({mdates[0]} .. {mdates[-1]}), {m.sum()} winning numbers")
print("Examples of matching past dates:", ", ".join(mdates[-6:]))
C=np.stack([np.bincount(DIG[rn[m],p],minlength=10) for p in range(4)])
print("\nDigit counts in those matching draws only (rows = position, columns = digit 0..9):")
for p in range(4): print(f"  position {p+1}: " + " ".join(f"{c:>3}" for c in C[p]))
for name,sign in (("S1 hot",-1),("S2 cold",1)):
    top2=np.argsort(sign*C,1,kind="stable")[:,:2]
    P=[int("".join(str(top2[p,b]) for p,b in enumerate(bits))) for bits in itertools.product((0,1),repeat=4)]
    print(f"\n{name}: best digits per position {top2[:,0].tolist()}, 2nd best {top2[:,1].tolist()}")
    print("  16 numbers:", " ".join(f"{n:04d}" for n in P))
print("\nActual Magnum 1st prize on 14 Oct: 3872")
EOF
```

## 61. 2026-10-17 05:38 — Compute the formula's values and picks for 17, 18 and 21 Oct and log them

```bash
cd /home/user/4DPrediction; date -u; python3 - <<'EOF' 2>&1 | grep -v computed
import sys, itertools, csv, datetime as dt, numpy as np
sys.path.insert(0,"analysis")
import astro_model as am, conditional_extended as ce
data, codes, labels, rows, draws, year_of = am.load()
DIG=am.DIG; rn,ro,rd=rows["num"],rows["op_ix"],rows["date"]
fs=["mars_nakshatra","mars_rashi","mercury_combust"]
d14=int(rd.max())
print("14 Oct values:", {f: labels[f][codes[f][d14]] for f in fs})
out=[]; now=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
for D in ["2026-10-17","2026-10-18","2026-10-21"]:
    ctx=ce.date_context(D); vals={f: ctx[f] for f in fs}
    print(f"\n{D} ({dt.date.fromisoformat(D):%a}) values: {vals}" + ("  <- same as 14 Oct" if all(vals[f]==labels[f][codes[f][d14]] for f in fs) else "  <- CHANGED"))
    match=np.ones(len(rd),bool)
    for f in fs:
        if vals[f] in labels[f]: match&=codes[f][rd]==labels[f].index(vals[f])
        else: match&=False
    for o,op in enumerate(am.OPS):
        m=match&(ro==o)
        nd=len(set(rd[m]))
        C=np.stack([np.bincount(DIG[rn[m],p],minlength=10) for p in range(4)])
        res={}
        for name,sign in (("S1",-1),("S2",1)):
            top2=np.argsort(sign*C,1,kind="stable")[:,:2]
            P=[int("".join(str(top2[p,b]) for p,b in enumerate(bits))) for bits in itertools.product((0,1),repeat=4)]
            res[name]=P
            for r,n in enumerate(P,1): out.append([now,D,f"{name}_marsnak_marsrashi_mercombust",op,r,f"{n:04d}"])
        print(f"  {op:<12} {nd} matching past draws | S1 #1 {res['S1'][0]:04d}, S2 #1 {res['S2'][0]:04d} | S2 16: {' '.join(f'{n:04d}' for n in res['S2'])}")
with open("analysis/forward_log.csv","a",newline="") as fh: csv.writer(fh).writerows(out)
print("\nlogged", len(out), "picks at", now, "UTC")
EOF
git add analysis/forward_log.csv && git commit -q -m "Log Mars nakshatra x Mars rashi x Mercury combust S1/S2 picks for 17, 18, 21 Oct before the draws

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q -u origin claude/4d-results-scraper-9ptbd5 && git log --oneline -1
```

## 62. 2026-10-17 06:29 — Summarise match/backoff models and commit

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
import json, numpy as np
r=json.load(open("analysis/digit_models_results.json"))["models"]
def g(x): return 1000*x["ll"]/x["digits"]
def lift(x,k,K): e=K*x["winners"]/10000; return x[k]/e
for fam in ("match","backoff"):
    ks=[k for k in r if k.startswith(fam)]
    v=np.array([g(r[k]["validation"]) for k in ks]); t=np.array([g(r[k]["test"]) for k in ks])
    print(f"{fam}: {len(ks)} models; digit ll valid median {np.median(v):+.2f} (best {v.max():+.2f}), test median {np.median(t):+.2f} (best {t.max():+.2f}); positive in both: {int(((v>0)&(t>0)).sum())}")
    best=sorted(ks,key=lambda k:-g(r[k]["validation"]))[:3]
    for k in best:
        x=r[k]; print(f"   {k:<70} valid {g(x['validation']):+.2f} test {g(x['test']):+.2f} | test hot16 x{lift(x['test'],'hot16_hits',16):.2f} cold16 x{lift(x['test'],'cold16_hits',16):.2f} | last5 hot16 {x['last5']['hot16_hits']} cold16 {x['last5']['cold16_hits']}")
    l5=[r[k]["last5"]["hot16_hits"]+r[k]["last5"]["cold16_hits"] for k in ks]
    print(f"   last 5, hot16+cold16 hits per model: mean {np.mean(l5)/2:.2f} per construction (random 0.54)")
EOF
git add analysis/digit_models_results.json && git commit -q -m "Digit model results

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q -u origin claude/4d-results-scraper-9ptbd5 && git log --oneline -1
```

## 63. 2026-10-17 06:35 — Get Big returns for the top leads

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
import json
r=json.load(open("analysis/digit_models_results.json"))["models"]["global"]
for per in ("validation","test"):
    x=r[per]; e=x["winners"]/10000
    print(per, f"cold #1: {x['cold1_hits']} hits vs {e:.1f}, Big RM{x['cold1_pay']/x['draws']:.2f} per RM1 | hot #1: {x['hot1_hits']} hits, Big RM{x['hot1_pay']/x['draws']:.2f}")
EOF
python3 - <<'EOF'
import csv
BIG={"1st":2500,"2nd":1000,"3rd":500,"Special":180,"Consolation":60}
for s in ["magnum","sportstoto","damacai"]:
    rows=list(csv.DictReader(open(f"/home/user/4DPrediction/data/{s}.csv")))
    post=[r for r in rows if r["date"]>="2012"]
    nd=len({r["date"] for r in post}); pay=sum(BIG[r["prize"]] for r in post if r["4d_number"]=="1024")
    print(s, f"1024 since 2012: {sum(r['4d_number']=='1024' for r in post)} wins in {nd} draws, Big RM{pay/nd:.2f} per RM1")
EOF
```

## 64. 2026-10-17 06:35 — See which prizes the cold pick won

```bash
cd /home/user/4DPrediction; python3 - <<'EOF' 2>&1 | grep -v computed
import sys, numpy as np
sys.path.insert(0,"analysis")
import digit_models as dm
D=dm.Data(); PR={2500:"1st",1000:"2nd",500:"3rd",180:"Special",60:"Consolation"}
from collections import Counter
c=Counter(); lst=[]
for y in range(2012,2027):
    J=np.flatnonzero((D.yj==y)&(D.dj<D.cut))
    P=dm.Global(D).fit((D.ry<y)&(D.rd<D.cut)).predict(J)
    N=dm.numbers(P,cold=True)[:,0]
    for i,j in enumerate(J):
        w=list(D.Wm[j])
        if N[i] in w:
            pr=PR[int(D.Pm[j][w.index(N[i])])]; c[pr]+=1
            if pr in ("1st","2nd","3rd"): lst.append(f"{D.dates[D.dj[j]]} {dm.am.OPS[D.oj[j]]} {N[i]:04d} {pr}")
print(dict(c)); print(lst)
EOF
```

## 65. 2026-10-17 06:48 — Stop run and switch to vectorised gammaln

```bash
cd /home/user/4DPrediction; ps aux | grep "analysis/new_[m]odels" | awk '{print $2}' | xargs -r kill; python3 -c "import scipy; print(scipy.__version__)"; python3 - <<'EOF'
p="analysis/new_models.py"; s=open(p).read()
s=s.replace("from math import lgamma\n","from scipy.special import gammaln\n")
s=s.replace('''                ll = (np.array([lgamma(s) for s in A.sum(1)]) - np.array([lgamma(s) for s in A.sum(1) + x.sum()])
                      + np.sum(np.vectorize(lgamma)(A + x) - np.vectorize(lgamma)(A), 1))''','''                As = A.sum(1)
                ll = gammaln(As) - gammaln(As + x.sum()) + (gammaln(A + x) - gammaln(A)).sum(1)''')
s=s.replace('''    for o, seq in op_sequences().items():
        pass
''','')
open(p,"w").write(s)
EOF
grep -n "gammaln" analysis/new_models.py | head -3
```

## 66. 2026-10-17 06:48 — Apply the gammaln patch

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
p="analysis/new_models.py"; s=open(p).read()
s=s.replace("from math import lgamma\n","from scipy.special import gammaln\n")
s=s.replace('''                ll = (np.array([lgamma(s) for s in A.sum(1)]) - np.array([lgamma(s) for s in A.sum(1) + x.sum()])
                      + np.sum(np.vectorize(lgamma)(A + x) - np.vectorize(lgamma)(A), 1))''','''                As = A.sum(1)
                ll = gammaln(As) - gammaln(As + x.sum()) + (gammaln(A + x) - gammaln(A)).sum(1)''')
s=s.replace('''    for o, seq in op_sequences().items():
        pass
''','')
open(p,"w").write(s)
EOF
grep -c "gammaln" analysis/new_models.py; ps aux | grep -c "[n]ew_models.py"
```

## 67. 2026-10-17 06:56 — Fix M2 intercept, rerun M2, commit

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
p="analysis/new_models.py"; s=open(p).read()
old='''            A = np.hstack([Z[tr], np.ones((tr.sum(), 1))])
            W = np.linalg.solve(A.T @ A + lam * np.eye(A.shape[1]), A.T @ S[tr])
            fitted[key] = W
        pred = (np.append(Z[j], 1) @ fitted[key]).reshape(4, 10)'''
new='''            zm, ym = Z[tr].mean(0), S[tr].mean(0)                  # intercept left unpenalised
            A = Z[tr] - zm
            W = np.linalg.solve(A.T @ A + lam * np.eye(A.shape[1]), A.T @ (S[tr] - ym))
            fitted[key] = (W, zm, ym)
        W, zm, ym = fitted[key]
        pred = (ym + (Z[j] - zm) @ W).reshape(4, 10)'''
assert old in s; s=s.replace(old,new); open(p,"w").write(s)
EOF
python3 - <<'EOF' 2>&1 | grep -v computed
import sys, json
sys.path.insert(0,"analysis")
import new_models as nm, digit_models as dm
nm.D=dm.Data()
X,S=nm.ar_features()
res=json.load(open("analysis/new_models_results.json"))
for k in [k for k in res["models"] if k.startswith("M2")]: del res["models"][k]
for lam in (1e2,1e4,1e6,1e8):
    s=nm.m2(lam,X,S).summary(); name=f"M2 autoregression lambda={lam:g}"; res["models"][name]=s
    v,t,l=s["validation"],s["test"],s["last5"]
    print(f"{name:<34} ll valid {v['ll_milli_per_unit']:+.2f} test {t['ll_milli_per_unit']:+.2f} | test hot16 x{t['lift_hot16']:.2f} cold16 x{t['lift_cold16']:.2f} Big16 RM{t['big16_per_RM1']:.2f} | last5 hot16 {l['hot16']} cold16 {l['cold16']}")
ks=[k for k in res["models"] if k.startswith("M2")]
res["best"]["M2"]=max(ks,key=lambda k:res["models"][k]["validation"]["ll_milli_per_unit"])
json.dump(res,open("analysis/new_models_results.json","w"),indent=1,default=float)
print("best M2:",res["best"]["M2"])
EOF
git add analysis/new_models.py analysis/new_models_results.json && git commit -q -m "Fix M2 ridge intercept (unpenalised), rerun; new model results

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q -u origin claude/4d-results-scraper-9ptbd5 && git log --oneline -1
```

## 68. 2026-10-17 07:29 — Check whether consecutive draw days share more numbers

```bash
cd /home/user/4DPrediction; python3 - <<'EOF' 2>&1 | grep -v computed
import sys, datetime as dt, numpy as np
sys.path.insert(0,"analysis")
import digit_models as dm
D=dm.Data()
day=np.array([(dt.date.fromisoformat(d)-dt.date(1985,1,1)).days for d in D.dates])
ws={}
for d,n in zip(D.rd,D.rn): ws.setdefault(int(d),set()).add(int(n))
nwin=np.array([len(ws.get(i,())) for i in range(len(D.dates))])
from collections import defaultdict
cons=defaultdict(lambda:[0,0,0]); noncons=defaultdict(lambda:[0,0,0])
for i in range(1,len(D.dates)):
    for j in range(max(0,i-6),i):
        g=day[i]-day[j]
        if g>7: continue
        o=len(ws[i]&ws[j]); e=nwin[i]*nwin[j]/10000
        t=cons if j==i-1 else noncons
        t[g][0]+=o; t[g][1]+=e; t[g][2]+=1
print("gap | consecutive draw days: shared / expected-from-sizes | non-consecutive")
for g in range(1,8):
    c=cons[g]; n=noncons[g]
    print(f" {g}  | {c[0]:>5}/{c[1]:7.1f} (x{c[0]/c[1] if c[1] else 0:.3f}, {c[2]} pairs) | {n[0]:>5}/{n[1]:7.1f} (x{n[0]/n[1] if n[1] else 0:.3f}, {n[2]} pairs)")
EOF
```

## 69. 2026-10-17 07:30 — Fix the chance level and rerun

```bash
cd /home/user/4DPrediction; python3 - <<'EOF'
p="analysis/recurrence_test.py"; s=open(p).read()
a=s.index("    # ---- r(g): shared winners"); b=s.index("    res = []\n")
new='''    # ---- chance level: E[shared] for two draw days = n_i * n_j / 10000 * c(g), where n = winners that day and
    #      c(g) = observed / size-expected over ALL pairs of draw days g days apart (log-binned gaps)
    nwin = np.bincount(wd, minlength=nd).astype(float)
    sz = np.zeros(T)
    sz[day] = nwin
    Fs = np.fft.rfft(sz, L)
    size_g = np.fft.irfft(Fs * np.conj(Fs), L)[:T] / 10000          # sum of n_i n_j / 10000 at gap g
    coin_g = np.zeros(T)
    order = np.argsort(wn, kind="stable")
    wn_s, wd_s = wn[order], wd[order]
    bounds = np.r_[0, np.flatnonzero(np.diff(wn_s)) + 1, len(wn_s)]
    groups = [day[wd_s[a:b]] for a, b in zip(bounds[:-1], bounds[1:]) if b - a >= 2]
    for s0 in range(0, len(groups), 512):
        M = np.zeros((len(groups[s0:s0 + 512]), T))
        for i, dd in enumerate(groups[s0:s0 + 512]):
            M[i, dd] = 1
        F = np.fft.rfft(M, L, axis=1)
        coin_g += np.rint(np.fft.irfft((F * np.conj(F)).sum(0), L)[:T])
    edges = np.unique(np.round(np.logspace(0, np.log10(T), 60)).astype(int))
    gb = np.searchsorted(edges, np.arange(T), side="right")
    cb = np.bincount(gb[1:], weights=coin_g[1:], minlength=len(edges) + 2)
    sb = np.bincount(gb[1:], weights=size_g[1:], minlength=len(edges) + 2)
    cg = np.where(sb > 0, cb / np.maximum(sb, 1e-12), 1.0)[gb]
    cg[0] = 0
    print(f"shared numbers vs size-based chance, over all pairs of draw days: "
          f"x{coin_g[1:].sum() / size_g[1:].sum():.3f} (1-7 days apart x{coin_g[1:8].sum() / size_g[1:8].sum():.3f})", flush=True)

'''
s=s[:a]+new+s[b:]
s=s.replace('''        exp_a = 0.0
        for v in np.unique(c):
            ind = np.zeros(T)
            ind[day[c == v]] = 1
            Fi = np.fft.rfft(ind, L)
            npg = np.rint(np.fft.irfft(Fi * np.conj(Fi), L)[:T])
            exp_a += float((npg[1:] * rs[1:]).sum() / 2) * 2 / 2''','''        exp_a = 0.0
        for v in np.unique(c):
            ind = np.zeros(T)
            ind[day[c == v]] = nwin[c == v]
            Fi = np.fft.rfft(ind, L)
            sv = np.fft.irfft(Fi * np.conj(Fi), L)[:T] / 10000      # each unordered pair once for g >= 1
            exp_a += float((sv[1:] * cg[1:]).sum())''')
s=s.replace('''                exp_b += rs[day[i] - day[j]]''','''                exp_b += nwin[i] * nwin[j] / 10000 * cg[day[i] - day[j]]''')
s=s.replace('''            e = rs[day[i] - day[j]]''','''            e = nwin[i] * nwin[j] / 10000 * cg[day[i] - day[j]]''')
s=s.replace('''    json.dump({"gap_rate_1_7_days": float(rs[1:8].mean()), "results": res''','''    json.dump({"results": res''')
open(p,"w").write(s)
EOF
grep -n "rs\[" analysis/recurrence_test.py; timeout 3000 python3 analysis/recurrence_test.py 2>&1 | grep -v computed
```

## 70. 2026-10-17 08:09 — Sanity check vs earlier results and timing

```bash
sed -i 's/np.sort(dm.DIG if hasattr(dm, "DIG") else am.DIG, axis=1)/np.sort(am.DIG, axis=1)/' analysis/recurrence_perm.py && python3 - <<'EOF'
import sys, time, json
sys.path.insert(0, "analysis")
import recurrence_perm as rp
rp.setup()
old = {x["parameter"]: x for x in json.load(open("analysis/recurrence_results.json"))["results"]}
for f in ["day_element", "moon_navamsa", "weekday"]:
    t = time.time(); r = rp.evaluate(rp.cells_of((f,))); dt = time.time() - t
    o = old[f]
    print(f, f"{dt:.2f}s", "new straight", [round(v, 1) for v in r["straight"]],
          "old", [round(o[k], 1) for k in ("all_pairs_obs", "all_pairs_exp", "next_obs", "next_exp")])
    print("   rev", [round(v, 1) for v in r["reverse"]], "ibox", [round(v, 1) for v in r["ibox"]])
t = time.time(); r = rp.evaluate(rp.cells_of(("nakshatra", "mercury_nakshatra"))); print("pair", time.time() - t, r)
EOF
```

## 71. 2026-10-17 08:12 — Write S1/S2 recurrence test and sanity-run it

```bash
cat > analysis/recurrence_s12.py <<'EOF'
#!/usr/bin/env python3
"""Recurrence test for the S1 (hot) / S2 (cold) positional-digit picks, for all
78 single parameters and 3,003 pairs, scored as Straight, Reverse and i-Box.

For a draw day whose parameter value (or pair of values) occurred before:
  (a) source = ALL earlier draw days with the same value
  (b) source = only the PREVIOUS draw day with the same value
Count each digit in each position over the source days' winners (any prize,
any operator, each number once per date); S1 = the 2 most frequent digits per
position, S2 = the 2 least frequent (ties -> lower digit), 2^4 = 16 numbers.
Hits on the later day:
  Straight  a winner equals one of the 16
  Reverse   a winner's reversed digits equal one of the 16 (palindromes excluded)
  i-Box     a winner is any arrangement of one of the 16
Chance level for each day = winners that day x probability a random number
hits, using that year's digit mix per position (so a parameter must beat the
plain year-level digit bias, not just uniform chance).
The whole scan is repeated on circularly shifted parameter calendars (one
shift for all parameters, at least about a year of draw days) to get the best
z and number of z > 2 that the scan reaches by chance.

Run from the repo root:  python3 analysis/recurrence_s12.py [n_shifts]
"""

import itertools
import json
import math
import multiprocessing as mp
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am  # noqa: E402
import digit_models as dm  # noqa: E402

ROOT = am.ROOT
FACT = am.VEDIC + am.CHINESE
DIG = am.DIG
POW = np.array([1000, 100, 10, 1])
BITS = np.array([[(k >> (3 - p)) & 1 for p in range(4)] for k in range(16)])     # (16, 4)
RULES = ("straight", "reverse", "ibox")
COLS = [f"{s}_{v}_{r}" for s in ("S1", "S2") for v in "ab" for r in RULES]
G = {}


def norm_sf(z):
    return 0.5 * math.erfc(z / math.sqrt(2))


def setup():
    D = dm.Data()
    nd = len(D.dates)
    key = np.unique(D.rd.astype(np.int64) * 10000 + D.rn)
    wd, wn = key // 10000, key % 10000
    nwin = np.bincount(wd, minlength=nd).astype(float)
    W = np.zeros((nd, 10000), bool)
    W[wd, wn] = True
    dday = np.zeros((nd, 4, 10))
    for p in range(4):
        np.add.at(dday, (wd, p, DIG[wn, p]), 1)
    num = np.arange(10000)
    rev = (DIG[:, ::-1] * POW).sum(1)
    box = np.unique(np.sort(DIG, axis=1) @ POW, return_inverse=True)[1]
    nbox = int(box.max()) + 1
    Cb = np.zeros((nd, nbox), np.float32)
    np.add.at(Cb, (wd, box[wn]), 1)
    yr = np.array([int(d[:4]) for d in D.dates])
    yix = yr - yr.min()
    q = np.zeros((yix.max() + 1, 4, 10))
    np.add.at(q, yix, dday)
    q /= q.sum(2, keepdims=True)
    Py = q[:, 0, DIG[:, 0]] * q[:, 1, DIG[:, 1]] * q[:, 2, DIG[:, 2]] * q[:, 3, DIG[:, 3]]     # (years, 10000)
    Pbox = np.stack([np.bincount(box, weights=Py[y], minlength=nbox) for y in range(len(Py))])
    G.update(D=D, nd=nd, nwin=nwin, W=W, dday=dday, rev=rev, pal=rev == num, box=box, Cb=Cb, yix=yix, Py=Py, Pbox=Pbox)


def cells_of(test, shift=0):
    D = G["D"]
    c = np.zeros(G["nd"], np.int64)
    for f in test:
        c = c * (int(D.codes[f].max()) + 1) + D.codes[f]
    return np.roll(c, shift) if shift else c


def picks(C, hot):
    """(n, 4, 10) digit counts -> (n, 16) numbers."""
    top2 = np.argsort(-C if hot else C, axis=2, kind="stable")[:, :, :2]
    dig = np.take_along_axis(top2, BITS.T[None, :, :], 2)                   # (n, 4, 16)
    return (dig * POW[None, :, None]).sum(1)


def score(days, P):
    """obs / exp per rule for picks P (n, 16) on the given days."""
    W, rev, pal, box, Cb, Py, Pbox, nwin = (G[k] for k in ("W", "rev", "pal", "box", "Cb", "Py", "Pbox", "nwin"))
    y = G["yix"][days]
    out = {}
    out["straight"] = (float(W[days[:, None], P].sum()), float((nwin[days] * Py[y[:, None], P].sum(1)).sum()))
    R = rev[P]
    ok = ~pal[P]
    out["reverse"] = (float((W[days[:, None], R] & ok).sum()), float((nwin[days] * (Py[y[:, None], R] * ok).sum(1)).sum()))
    B = np.sort(box[P], axis=1)
    first = np.ones_like(B, bool)
    first[:, 1:] = B[:, 1:] != B[:, :-1]
    out["ibox"] = (float((Cb[days[:, None], B] * first).sum()), float((nwin[days] * (Pbox[y[:, None], B] * first).sum(1)).sum()))
    return out


def evaluate(cells):
    dday = G["dday"]
    order = np.lexsort((np.arange(len(cells)), cells))
    sc = cells[order]
    newgrp = np.r_[True, sc[1:] != sc[:-1]]
    has_prev = ~newgrp
    days = order[has_prev]
    # (a) all earlier same-value days: exclusive cumulative sum within each group
    cs = np.cumsum(dday[order], axis=0)
    start = np.maximum.accumulate(np.where(newgrp, np.arange(len(sc)), 0))
    base = np.where((start > 0)[:, None, None], cs[np.maximum(start - 1, 0)], 0)
    excl = cs - dday[order] - base
    Ca = excl[has_prev]
    # (b) previous same-value day only
    Cbsrc = dday[order[:-1]][has_prev[1:]]
    res = {}
    for s, hot in (("S1", True), ("S2", False)):
        for v, C in (("a", Ca), ("b", Cbsrc)):
            for r, oe in score(days, picks(C, hot)).items():
                res[f"{s}_{v}_{r}"] = oe
    return res


def task(args):
    test, shift = args
    return evaluate(cells_of(test, shift))


def z_of(r):
    return [(r[c][0] - r[c][1]) / math.sqrt(r[c][1]) for c in COLS]


def main():
    n_shifts = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    t0 = time.time()
    setup()
    tests = [(f,) for f in FACT] + list(itertools.combinations(FACT, 2))
    n = len(tests)
    # reference: no parameter (one cell) -> (a) all earlier days, (b) the previous draw day
    ref = evaluate(np.zeros(G["nd"], np.int64))
    print("No parameter (reference): " + "; ".join(f"{c} x{ref[c][0] / ref[c][1]:.3f}" for c in COLS), flush=True)
    with mp.get_context("fork").Pool(4) as pool:
        real = pool.map(task, [(t, 0) for t in tests], chunksize=16)
        print(f"{n} tests evaluated ({time.time() - t0:.0f}s)", flush=True)
        Z = np.array([z_of(r) for r in real])
        rng = np.random.default_rng(3)
        null = []
        for k in range(n_shifts):
            sh = int(rng.integers(170, G["nd"] - 170))
            Zs = np.array([z_of(r) for r in pool.map(task, [(t, sh) for t in tests], chunksize=16)])
            null.append({"shift": sh, "max_z": Zs.max(0).tolist(), "z_gt_2": (Zs > 2).sum(0).tolist()})
            print(f"shift {k + 1}/{n_shifts} done ({time.time() - t0:.0f}s)", flush=True)
    names = [" x ".join(t) for t in tests]
    report = {"tests": n, "n_shifts": n_shifts, "reference_no_parameter": ref, "null": null, "by_column": {}}
    print("\ncolumn                    z>2 real | shifted mean (range)   best z real | shifted mean (range) | shifts as high")
    for ci, col in enumerate(COLS):
        nm = np.array([x["max_z"][ci] for x in null])
        ng = np.array([x["z_gt_2"][ci] for x in null])
        q = int(np.argmax(Z[:, ci]))
        print(f"{col:<24} {int((Z[:, ci] > 2).sum()):>5} | {ng.mean():>5.0f} ({ng.min()}-{ng.max()})      "
              f"{Z[q, ci]:+.2f} | {nm.mean():+.2f} ({nm.min():+.2f} to {nm.max():+.2f}) | {int((nm >= Z[q, ci]).sum())}/{len(nm)}")
        top = np.argsort(-Z[:, ci])[:5]
        rows = []
        for t in top:
            o, e = real[t][col]
            rows.append({"test": names[t], "hits": o, "expected": e, "ratio": o / e, "z": float(Z[t, ci]),
                         "p_bonf": min(1.0, n * norm_sf(Z[t, ci])), "shift_scans_as_high": int((nm >= Z[t, ci]).sum())})
        report["by_column"][col] = {"z_gt_2": int((Z[:, ci] > 2).sum()), "null_z_gt_2": ng.tolist(),
                                    "null_max_z": nm.tolist(), "top": rows}
    print("\nTop 3 per column:")
    for col in COLS:
        print(f"  {col}")
        for x in report["by_column"][col]["top"][:3]:
            print(f"     {x['test']:<44} {x['hits']:>6.0f} hits vs {x['expected']:>8.1f} (x{x['ratio']:.3f}, z={x['z']:+.2f}, "
                  f"corrected p={x['p_bonf']:.2f}, shifted scans' best >= this {x['shift_scans_as_high']}/{n_shifts})")
    json.dump(report, open(os.path.join(ROOT, "analysis", "recurrence_s12_results.json"), "w"), indent=1)
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
EOF
python3 - <<'EOF'
import sys, time
sys.path.insert(0, "analysis")
import recurrence_s12 as r
r.setup()
t=time.time(); ref = r.evaluate(r.np.zeros(r.G["nd"], r.np.int64)); print(time.time()-t)
for c,(o,e) in ref.items(): print(c, o, round(e,1), round(o/e,3))
t=time.time(); x = r.evaluate(r.cells_of(("nakshatra","mercury_nakshatra"))); print("pair", time.time()-t, x["S1_a_straight"], x["S2_b_ibox"])
EOF
```

## 72. 2026-10-17 09:03 — Commit results; split-period check of the 2 best candidates

```bash
git add analysis/recurrence_s12_results.json && git commit -qm "Add S1/S2 recurrence results

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q origin claude/4d-results-scraper-9ptbd5 && echo pushed
python3 - <<'EOF'
import sys
sys.path.insert(0, "analysis")
import numpy as np
import recurrence_s12 as r
r.setup()
yr = np.array([int(d[:4]) for d in r.G["D"].dates])
# split evaluate by period: monkeypatch score to restrict days
orig = r.score
for lo, hi in ((1985, 2005), (2006, 2016), (2017, 2027)):
    def sc(days, P, lo=lo, hi=hi):
        m = (yr[days] >= lo) & (yr[days] < hi)
        return orig(days[m], P[m])
    r.score = sc
    for test, col in ((("mercury_nakshatra", "venus_rashi"), "S1_a_straight"), (("karana", "day_pillar"), "S1_b_ibox")):
        o, e = r.evaluate(r.cells_of(test))[col]
        print(lo, hi - 1, " x ".join(test), col, f"{o:.0f} vs {e:.1f} x{o/e:.3f} z={(o-e)/e**.5:+.2f}")
EOF
```

## 73. 2026-10-17 09:08 — Picks for upcoming draws from the two leads

```bash
python3 - <<'EOF'
import sys
sys.path.insert(0, "analysis")
import numpy as np
import recurrence_s12 as r
import astro_model as am
r.setup()
D = r.G["D"]; dday = r.G["dday"]
print("last data date", D.dates[-1])
for date in ("2026-10-17", "2026-10-18", "2026-10-21"):
    for (f1, f2), v in ((("mercury_nakshatra", "venus_rashi"), "a"), (("karana", "day_pillar"), "b")):
        ix, c2, ctx = am.date_codes(date, D.codes, D.labels, [f1, f2])
        same = (D.codes[f1] == c2[f1][-1]) & (D.codes[f2] == c2[f2][-1])
        idx = np.flatnonzero(same)
        if len(idx) == 0:
            print(date, f1, f2, "no earlier day"); continue
        C = dday[idx].sum(0, keepdims=True) if v == "a" else dday[idx[-1:]]
        P = sorted(r.picks(C, True)[0])
        print(date, f"{f1}={ctx[f1]} x {f2}={ctx[f2]} ({v}: {len(idx)} earlier days, last {D.dates[idx[-1]]})")
        print("   S1 picks:", " ".join(f"{n:04d}" for n in P))
EOF
```

## 74. 2026-10-17 09:08 — Log picks and commit forward check

```bash
cd /home/user/4DPrediction && T=$(date -u "+%Y-%m-%d %H:%M") && python3 - "$T" <<'EOF'
import sys
T = sys.argv[1]
P = {
 ("2026-10-17", "recur_S1a_mercurynak_venusrashi"): "6335 6337 6345 6347 6535 6537 6545 6547 7335 7337 7345 7347 7535 7537 7545 7547",
 ("2026-10-18", "recur_S1a_mercurynak_venusrashi"): "6335 6337 6345 6347 6535 6537 6545 6547 7335 7337 7345 7347 7535 7537 7545 7547",
 ("2026-10-21", "recur_S1a_mercurynak_venusrashi"): "6335 6337 6345 6347 6535 6537 6545 6547 7335 7337 7345 7347 7535 7537 7545 7547",
 ("2026-10-17", "recur_S1b_karana_daypillar_ibox"): "1210 1217 1290 1297 1910 1917 1990 1997 8210 8217 8290 8297 8910 8917 8990 8997",
 ("2026-10-18", "recur_S1b_karana_daypillar_ibox"): "1540 1546 1590 1596 1640 1646 1690 1696 9540 9546 9590 9596 9640 9646 9690 9696",
 ("2026-10-21", "recur_S1b_karana_daypillar_ibox"): "6340 6342 6370 6372 6440 6442 6470 6472 9340 9342 9370 9372 9440 9442 9470 9472",
}
with open("analysis/forward_log.csv", "a") as fh:
    for (d, v), nums in P.items():
        for k, n in enumerate(nums.split(), 1):
            fh.write(f"{T},{d},{v},All,{k},{n}\n")
print(T)
EOF
tail -1 analysis/forward_log.csv
git add analysis/recurrence_s12_forward.py analysis/recurrence_s12_forward_results.json analysis/forward_log.csv && git commit -qm "Walk-forward check of S1/S2 recurrence leads; log picks for 17/18/21 Oct

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q origin claude/4d-results-scraper-9ptbd5 && echo pushed
```

## 75. 2026-10-17 09:19 — List result files and find triple lead details

```bash
cd /home/user/4DPrediction/analysis && ls *.json | head -50; python3 - <<'EOF'
import json
d = json.load(open("s12_combos_results.json")) if __import__("os").path.exists("s12_combos_results.json") else None
if d:
    print(list(d.keys())[:20])
    s = json.dumps(d)
    i = s.find("mars_nakshatra")
    print(s[max(0,i-600):i+900])
EOF
```

## 76. 2026-10-17 09:19 — Pull numbers for S1/S2 combo and cold-number leads

```bash
python3 - <<'EOF'
import json
d = json.load(open("s12_combos_results.json"))
for k in ["S1|16|triples","S2|16|triples","S1|16|pairs","S2|16|pairs"]:
    v = d[k]; print(k, {a:b for a,b in v.items() if a!="best"})
    for b in v["best"][:2]:
        print("   ", {a:(round(x,3) if isinstance(x,float) else x) for a,x in b.items() if a!="last5_detail"})
f = json.load(open("first_prize_results.json")); print(f["cold_number_first_prizes"])
print(f["B_number_level"])
EOF
grep -n "1024" *.json | head -5
```

## 77. 2026-10-17 09:31 — Compute hits per draw day for the lead

```bash
python3 - <<'EOF'
import sys; sys.path.insert(0, "analysis")
import numpy as np
import recurrence_s12 as r, s12_lead_cells as lc
r.setup(); G = r.G; D = G["D"]
yr = np.array([int(d[:4]) for d in D.dates])
days, hits, exp = lc.per_day()
for name, m in (("before 2012", yr[days] < 2012), ("2012-2026", yr[days] >= 2012), ("2019-2026", yr[days] >= 2019), ("all", np.ones(len(days), bool))):
    n = m.sum()
    print(f"{name:<12} draw days {n:>5}  hits {hits[m].sum():>4.0f}  expected {exp[m].sum():6.1f}  "
          f"per day {hits[m].mean():.4f} vs {exp[m].mean():.4f}  P(>=1 hit) {np.mean(hits[m] > 0):.4f}  "
          f"days per hit {n / hits[m].sum():.1f} (chance {n / exp[m].sum():.1f})  winners/day {G['nwin'][days[m]].mean():.1f}")
# per operator after 2012
for o, nm in enumerate(r.am.OPS):
    sel = D.ro == o
    key = np.unique(D.rd[sel].astype(np.int64) * 10000 + D.rn[sel])
    W = np.zeros_like(G["W"]); W[key // 10000, key % 10000] = True
    m = yr[days] >= 2012
    cells = r.cells_of((lc.F1, lc.F2))
    # recompute picks
    order = np.lexsort((np.arange(len(cells)), cells)); sc = cells[order]
    ng = np.r_[True, sc[1:] != sc[:-1]]
    cs = np.cumsum(G["dday"][order], 0); st = np.maximum.accumulate(np.where(ng, np.arange(len(sc)), 0))
    base = np.where((st > 0)[:, None, None], cs[np.maximum(st - 1, 0)], 0)
    P = r.picks((cs - G["dday"][order] - base)[~ng], True)
    h = W[days[:, None], P].sum(1)
    drew = np.isin(days, np.unique(key // 10000))
    mm = m & drew
    print(f"   {nm:<12} 2012-2026: {mm.sum()} draw days, {h[mm].sum()} hits, per day {h[mm].mean():.4f} (chance ~{16*23/10000:.4f})")
EOF
```

## 78. 2026-10-17 10:03 — Write pick-count scan and check against earlier lead numbers

```bash
cd /home/user/4DPrediction && cat > analysis/recurrence_s12_k.py <<'EOF'
#!/usr/bin/env python3
"""recurrence_s12.py with the number of picks varied, for all 78 single
parameters and 3,003 pairs, S1 (hot) / S2 (cold), (a) all earlier / (b)
previous same-value day, scored as Straight / Reverse / i-Box.

Picks per draw day from the source days' digit counts per position:
  top K   numbers ranked by sum over positions of log(count + 1) (S1: highest,
          S2: lowest; ties -> lower number), K = 1, 2, 4, 8, 16, 32, 64
  grid    top-2 / top-3 digits per position: 16 / 81 numbers (grid 16 = S1/S2
          as in recurrence_s12.py)
Chance per day uses that year's digit mix per position (as before).
Every test is scored before 2012 and 2012-2026. Two checks per column
(strategy x version x rule x pick amount):
  scan     number of tests with z > 2 and best z over all years
  forward  the 5 tests with the best z before 2012, scored 2012-2026
Both are repeated on circularly shifted parameter calendars (one shift for all
parameters, at least about a year of draw days) for the chance level.

Run from the repo root:  python3 analysis/recurrence_s12_k.py [n_shifts]
"""

import itertools
import json
import math
import multiprocessing as mp
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recurrence_s12 as r  # noqa: E402

KS = [1, 2, 4, 8, 16, 32, 64]
PICKS = [f"top{k}" for k in KS] + ["grid16", "grid81"]
RULES = ("straight", "reverse", "ibox")
COLS = [(s, v, rule, p) for s in ("S1", "S2") for v in "ab" for rule in RULES for p in PICKS]
SPLIT = 2012
POW = np.array([1000, 100, 10, 1])
# rank tuples that can be in the top 64: a number with digit ranks r is beaten by prod(r + 1) - 1 numbers
TUP = np.array([t for t in itertools.product(range(10), repeat=4) if np.prod(np.array(t) + 1) <= 64])
G16 = np.flatnonzero(TUP.max(1) < 2)
G81 = np.flatnonzero(TUP.max(1) < 3)


def pick_sets(C, hot):
    """C (n, 4, 10) -> {pick name: (n, K) numbers}."""
    order = np.argsort(-C if hot else C, axis=2, kind="stable")             # digit at each rank
    L = np.log(C + 1) * (1 if hot else -1)
    n = len(C)
    dig = np.stack([order[:, p, TUP[:, p]] for p in range(4)], axis=2)        # (n, m, 4)
    sc = sum(np.take_along_axis(L[:, p], dig[:, :, p], 1) for p in range(4))
    num = (dig * POW).sum(2)
    srt = np.lexsort((num, -np.round(sc, 9)), axis=-1)
    ranked = np.take_along_axis(num, srt, 1)
    out = {f"top{k}": ranked[:, :k] for k in KS}
    out["grid16"] = num[:, G16]
    out["grid81"] = num[:, G81]
    return out


def score_days(days, P):
    """Per-day (hits, expected) for each rule: dict rule -> (2, n)."""
    G = r.G
    W, rev, pal, box, Cb, Py, Pbox, nwin = (G[k] for k in ("W", "rev", "pal", "box", "Cb", "Py", "Pbox", "nwin"))
    y = G["yix"][days]
    nw = nwin[days]
    out = {"straight": (W[days[:, None], P].sum(1), nw * Py[y[:, None], P].sum(1))}
    R = rev[P]
    ok = ~pal[P]
    out["reverse"] = ((W[days[:, None], R] & ok).sum(1), nw * (Py[y[:, None], R] * ok).sum(1))
    B = np.sort(box[P], axis=1)
    first = np.ones_like(B, bool)
    first[:, 1:] = B[:, 1:] != B[:, :-1]
    out["ibox"] = ((Cb[days[:, None], B] * first).sum(1), nw * (Pbox[y[:, None], B] * first).sum(1))
    return out


def evaluate(cells):
    """(len(COLS), 4) array: hits before, expected before, hits after, expected after."""
    G = r.G
    dday = G["dday"]
    order = np.lexsort((np.arange(len(cells)), cells))
    sc = cells[order]
    newgrp = np.r_[True, sc[1:] != sc[:-1]]
    has_prev = ~newgrp
    days = order[has_prev]
    late = G["yr"][days] >= SPLIT
    cs = np.cumsum(dday[order], axis=0)
    start = np.maximum.accumulate(np.where(newgrp, np.arange(len(sc)), 0))
    base = np.where((start > 0)[:, None, None], cs[np.maximum(start - 1, 0)], 0)
    src = {"a": (cs - dday[order] - base)[has_prev], "b": dday[order[:-1]][has_prev[1:]]}
    res = {}
    for s, hot in (("S1", True), ("S2", False)):
        for v in "ab":
            for pname, P in pick_sets(src[v], hot).items():
                for rule, (h, e) in score_days(days, P).items():
                    res[(s, v, rule, pname)] = (h[~late].sum(), e[~late].sum(), h[late].sum(), e[late].sum())
    return np.array([res[c] for c in COLS], float)


def task(args):
    test, shift = args
    return evaluate(r.cells_of(test, shift))


def zz(o, e):
    return (o - e) / np.sqrt(np.maximum(e, 1e-9))


def stats(A):
    """A (tests, cols, 4) -> per column: z>2 count, best z (all years), forward mean z of top-5-before."""
    z_all = zz(A[:, :, 0] + A[:, :, 2], A[:, :, 1] + A[:, :, 3])
    z_b = zz(A[:, :, 0], A[:, :, 1])
    z_a = zz(A[:, :, 2], A[:, :, 3])
    top = np.argsort(-z_b, axis=0)[:5]                                       # (5, cols)
    fwd = np.take_along_axis(z_a, top, 0).mean(0)
    return (z_all > 2).sum(0), z_all.max(0), fwd, z_all, z_b, z_a, top


def main():
    n_shifts = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    t0 = time.time()
    r.setup()
    r.G["yr"] = np.array([int(d[:4]) for d in r.G["D"].dates])
    tests = [(f,) for f in r.FACT] + list(itertools.combinations(r.FACT, 2))
    names = [" x ".join(t) for t in tests]
    with mp.get_context("fork").Pool(4) as pool:
        A = np.array(pool.map(task, [(t, 0) for t in tests], chunksize=8))
        print(f"{len(tests)} tests x {len(COLS)} columns ({time.time() - t0:.0f}s)", flush=True)
        rng = np.random.default_rng(5)
        nulls = []
        for k in range(n_shifts):
            sh = int(rng.integers(170, r.G["nd"] - 170))
            nulls.append(stats(np.array(pool.map(task, [(t, sh) for t in tests], chunksize=8)))[:3])
            print(f"shift {k + 1}/{n_shifts} ({time.time() - t0:.0f}s)", flush=True)
    cnt, best, fwd, z_all, z_b, z_a, top = stats(A)
    ncnt = np.array([x[0] for x in nulls])
    nbest = np.array([x[1] for x in nulls])
    nfwd = np.array([x[2] for x in nulls])
    report = {"tests": len(tests), "n_shifts": n_shifts, "columns": []}
    print("\nPer column: z>2 count real (shifted mean) | best z real (shifted mean, shifts as high) | "
          "forward: top 5 chosen before 2012, mean z 2012-2026 real (shifted mean, shifts as high)")
    for ci, (s, v, rule, p) in enumerate(COLS):
        if p == PICKS[0]:
            print(f"\n{s} ({v}) {rule}")
        fb = int((nfwd[:, ci] >= fwd[ci]).sum())
        bb = int((nbest[:, ci] >= best[ci]).sum())
        print(f"   {p:<7} z>2 {cnt[ci]:>4} ({ncnt[:, ci].mean():>5.0f}) | best {best[ci]:+.2f} ({nbest[:, ci].mean():+.2f}, {bb}/{n_shifts}) | "
              f"forward {fwd[ci]:+.2f} ({nfwd[:, ci].mean():+.2f}, {fb}/{n_shifts})  [{names[int(np.argmax(z_all[:, ci]))]}]")
        report["columns"].append({
            "strategy": s, "version": v, "rule": rule, "picks": p, "z_gt_2": int(cnt[ci]),
            "null_z_gt_2": ncnt[:, ci].tolist(), "best_z": float(best[ci]), "null_best_z": nbest[:, ci].tolist(),
            "best_test": names[int(np.argmax(z_all[:, ci]))], "forward_mean_z": float(fwd[ci]),
            "null_forward_mean_z": nfwd[:, ci].tolist(),
            "forward_tests": [{"test": names[int(q)], "z_before": float(z_b[q, ci]), "z_after": float(z_a[q, ci]),
                               "hits_after": float(A[q, ci, 2]), "exp_after": float(A[q, ci, 3])} for q in top[:, ci]]})
    # overall: how often does the real forward beat its shifted versions, across all columns?
    beat = np.array([(nfwd[:, ci] < fwd[ci]).mean() for ci in range(len(COLS))])
    print(f"\nAcross all {len(COLS)} columns: forward mean z real {fwd.mean():+.3f} vs shifted {nfwd.mean():+.3f}; "
          f"real forward beats all {n_shifts} shifts in {int((beat == 1).sum())} columns "
          f"(about {len(COLS) / (n_shifts + 1):.0f} expected by chance)")
    best_cols = sorted(range(len(COLS)), key=lambda c: -(fwd[c] - nfwd[:, c].mean()) / max(nfwd[:, c].std(), 1e-9))[:8]
    print("\nColumns whose forward result stands out most from their shifted versions:")
    for c in best_cols:
        s, v, rule, p = COLS[c]
        print(f"   {s} ({v}) {rule} {p}: forward {fwd[c]:+.2f} vs shifted {nfwd[:, c].mean():+.2f} +/- {nfwd[:, c].std():.2f}")
        for q in top[:, c][:3]:
            print(f"      {names[q]:<44} before z {z_b[q, c]:+.2f} -> after {A[q, c, 2]:.0f}/{A[q, c, 3]:.1f} "
                  f"(x{A[q, c, 2] / A[q, c, 3]:.3f}, z {z_a[q, c]:+.2f})")
    report["overall"] = {"forward_real_mean": float(fwd.mean()), "forward_null_mean": float(nfwd.mean()),
                         "columns_beating_all_shifts": int((beat == 1).sum())}
    json.dump(report, open(os.path.join(r.ROOT, "analysis", "recurrence_s12_k_results.json"), "w"), indent=1)
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
EOF
python3 - <<'EOF'
import sys, time
sys.path.insert(0, "analysis")
import numpy as np
import recurrence_s12_k as k
k.r.setup(); k.r.G["yr"] = np.array([int(d[:4]) for d in k.r.G["D"].dates])
print(len(k.TUP), len(k.G16), len(k.G81))
t = time.time(); A = k.evaluate(k.r.cells_of(("mercury_nakshatra", "venus_rashi"))); print("time", time.time() - t)
for c, row in zip(k.COLS, A):
    if c[0] == "S1" and c[1] == "a" and c[2] == "straight": print(c[3], row.round(1))
EOF
```

## 79. 2026-10-17 10:04 — Speed up pick-count scan and recheck against earlier results

```bash
python3 - <<'EOF'
import re
p = "analysis/recurrence_s12_k.py"
s = open(p).read()
s = s.replace("""TUP = np.array([t for t in itertools.product(range(10), repeat=4) if np.prod(np.array(t) + 1) <= 64])""",
"""TUP = np.array([t for t in itertools.product(range(10), repeat=4)
                if np.prod(np.array(t) + 1) <= 64 or max(t) < 3])""")
old_start = s.index("def pick_sets(C, hot):")
old_end = s.index("def evaluate(cells):")
new = '''def pick_sets(C, hot):
    """C (n, 4, 10) -> (ranked top-64 numbers in rank order (n, 64), grid16 (n, 16), grid81 (n, 81))."""
    order = np.argsort(-C if hot else C, axis=2, kind="stable")             # digit at each rank
    L = np.log(C + 1) * (1 if hot else -1)
    dig = np.stack([order[:, p, TUP[:, p]] for p in range(4)], axis=2)        # (n, m, 4)
    sc = sum(np.take_along_axis(L[:, p], dig[:, :, p], 1) for p in range(4))
    num = (dig * POW).sum(2)
    key = -np.round(sc * 1e6).astype(np.int64) * 10000 + num                  # higher score first, ties -> lower number
    kmax = KS[-1]
    part = np.argpartition(key, kmax, axis=1)[:, :kmax]
    part = np.take_along_axis(part, np.argsort(np.take_along_axis(key, part, 1), axis=1), 1)
    return np.take_along_axis(num, part, 1), num[:, G16], num[:, G81]


def first_in_row(B):
    """Mask of the first occurrence of each value along each row, in the given order."""
    o = np.argsort(B, axis=1, kind="stable")
    sb = np.take_along_axis(B, o, 1)
    f = np.ones_like(sb, bool)
    f[:, 1:] = sb[:, 1:] != sb[:, :-1]
    out = np.empty_like(f)
    np.put_along_axis(out, o, f, 1)
    return out


def score_days(days, P):
    """Per-day cumulative (hits, expected) along the columns of P for each rule: rule -> ((n, K), (n, K))."""
    G = r.G
    W, rev, pal, box, Cb, Py, Pbox, nwin = (G[k] for k in ("W", "rev", "pal", "box", "Cb", "Py", "Pbox", "nwin"))
    y = G["yix"][days][:, None]
    nw = nwin[days][:, None]
    d = days[:, None]
    out = {"straight": (np.cumsum(W[d, P], 1), nw * np.cumsum(Py[y, P], 1))}
    R = rev[P]
    ok = ~pal[P]
    out["reverse"] = (np.cumsum(W[d, R] & ok, 1), nw * np.cumsum(Py[y, R] * ok, 1))
    B = box[P]
    f = first_in_row(B)
    out["ibox"] = (np.cumsum(Cb[d, B] * f, 1), nw * np.cumsum(Pbox[y, B] * f, 1))
    return out


'''
s = s[:old_start] + new + s[old_end:]
s = s.replace("""            for pname, P in pick_sets(src[v], hot).items():
                for rule, (h, e) in score_days(days, P).items():
                    res[(s, v, rule, pname)] = (h[~late].sum(), e[~late].sum(), h[late].sum(), e[late].sum())""",
"""            ranked, g16, g81 = pick_sets(src[v], hot)
            for P, cols in ((ranked, {f"top{k}": k for k in KS}), (g16, {"grid16": 16}), (g81, {"grid81": 81})):
                for rule, (h, e) in score_days(days, P).items():
                    hb, eb, ha, ea = h[~late].sum(0), e[~late].sum(0), h[late].sum(0), e[late].sum(0)
                    for pname, kk in cols.items():
                        res[(s, v, rule, pname)] = (hb[kk - 1], eb[kk - 1], ha[kk - 1], ea[kk - 1])""")
open(p, "w").write(s)
EOF
python3 - <<'EOF'
import sys, time
sys.path.insert(0, "analysis")
import numpy as np
import recurrence_s12_k as k, recurrence_s12 as r0
k.r.setup(); k.r.G["yr"] = np.array([int(d[:4]) for d in k.r.G["D"].dates])
print(len(k.TUP), len(k.G16), len(k.G81))
t = time.time(); A = k.evaluate(k.r.cells_of(("mercury_nakshatra", "venus_rashi"))); print("time", time.time() - t)
for c, row in zip(k.COLS, A):
    if c[3] in ("grid16", "top1", "top64", "grid81") and c[1] == "a": print(c, row.round(1))
full = r0.evaluate(r0.cells_of(("mercury_nakshatra", "venus_rashi")))
print("recurrence_s12 grid16 all-years:", {c: tuple(round(x, 1) for x in v) for c, v in full.items() if c.endswith("_a_straight") or c.endswith("_a_ibox")})
EOF
```

## 80. 2026-10-17 10:04 — Profile the evaluate function

```bash
python3 - <<'EOF' 2>&1 | head -30
import sys, cProfile, pstats
sys.path.insert(0, "analysis")
import numpy as np
import recurrence_s12_k as k
k.r.setup(); k.r.G["yr"] = np.array([int(d[:4]) for d in k.r.G["D"].dates])
c = k.r.cells_of(("mercury_nakshatra", "venus_rashi"))
cProfile.run("k.evaluate(c)", "/tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad/prof")
pstats.Stats("/tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad/prof").sort_stats("tottime").print_stats(12)
EOF
```

## 81. 2026-10-17 10:05 — Faster two-half ranking; recheck numbers

```bash
python3 - <<'EOF'
p = "analysis/recurrence_s12_k.py"
s = open(p).read()
a = s.index("# rank tuples that can be in the top 64")
b = s.index("def first_in_row(B):")
new = '''KMAX = KS[-1]
H2 = np.array(list(itertools.product(range(10), repeat=2)))                 # digit-rank pairs for half a number
# (i, j) = ranks within the two halves; (i, j) is beaten by (i + 1)(j + 1) - 1 numbers, so only these can be top-64
IJ = np.array([(i, j) for i in range(KMAX) for j in range(KMAX) if (i + 1) * (j + 1) <= KMAX])
G3 = np.array(list(itertools.product(range(3), repeat=4)))
G16 = np.flatnonzero(G3.max(1) < 2)


def half(order, L, p):
    """Top-64 two-digit halves for positions p, p+1: (score, number 0-99) sorted best first."""
    d0 = order[:, p, H2[:, 0]]
    d1 = order[:, p + 1, H2[:, 1]]
    sc = np.take_along_axis(L[:, p], d0, 1) + np.take_along_axis(L[:, p + 1], d1, 1)
    hn = d0 * 10 + d1
    key = -np.round(sc * 1e6).astype(np.int64) * 100 + hn
    o = np.argsort(key, axis=1)[:, :KMAX]
    return np.take_along_axis(sc, o, 1), np.take_along_axis(hn, o, 1)


def pick_sets(C, hot):
    """C (n, 4, 10) -> (ranked top-64 numbers in rank order (n, 64), grid16 (n, 16), grid81 (n, 81))."""
    order = np.argsort(-C if hot else C, axis=2, kind="stable")             # digit at each rank (ties -> lower digit)
    L = np.log(C + 1) * (1 if hot else -1)
    s1, n1 = half(order, L, 0)
    s2, n2 = half(order, L, 2)
    sc = s1[:, IJ[:, 0]] + s2[:, IJ[:, 1]]
    num = n1[:, IJ[:, 0]] * 100 + n2[:, IJ[:, 1]]
    key = -np.round(sc * 1e6).astype(np.int64) * 10000 + num
    part = np.argpartition(key, KMAX, axis=1)[:, :KMAX]
    part = np.take_along_axis(part, np.argsort(np.take_along_axis(key, part, 1), axis=1), 1)
    g = sum(order[:, q, G3[:, q]] * POW[q] for q in range(4))                  # (n, 81) grid numbers
    return np.take_along_axis(num, part, 1), g[:, G16], g


'''
s = s[:a] + new + s[b:]
open(p, "w").write(s)
EOF
python3 - <<'EOF'
import sys, time
sys.path.insert(0, "analysis")
import numpy as np
import recurrence_s12_k as k
k.r.setup(); k.r.G["yr"] = np.array([int(d[:4]) for d in k.r.G["D"].dates])
print(len(k.IJ))
t = time.time(); A = k.evaluate(k.r.cells_of(("mercury_nakshatra", "venus_rashi"))); print("time", time.time() - t)
for c, row in zip(k.COLS, A):
    if c[1] == "a" and c[2] in ("straight", "ibox") and c[3] in ("grid16", "top1", "top64", "grid81"): print(c, row.round(1))
EOF
```

## 82. 2026-10-17 12:23 — Show today's lead digit counts

```bash
cd /home/user/4DPrediction && python3 - <<'EOF'
import sys; sys.path.insert(0, "analysis")
import numpy as np
import recurrence_s12 as r, astro_model as am
r.setup(); D = r.G["D"]
f1, f2 = "mercury_nakshatra", "venus_rashi"
ix, c2, ctx = am.date_codes("2026-10-17", D.codes, D.labels, [f1, f2])
idx = np.flatnonzero((D.codes[f1] == c2[f1][-1]) & (D.codes[f2] == c2[f2][-1]))
C = r.G["dday"][idx].sum(0)
print(ctx[f1], ctx[f2], len(idx), "earlier days", D.dates[idx[0]], "to", D.dates[idx[-1]])
for p in range(4):
    o = np.argsort(-C[p], kind="stable")
    print("pos", p + 1, [(int(d), int(C[p, d])) for d in o[:3]])
EOF
```

## 83. 2026-10-17 13:19 — Add 17 Oct results to data files

```bash
python3 - <<'EOF'
import csv
R = {
 "Magnum": ("magnum.csv", ["1294", "8044", "5541"], "6187 9574 5244 6040 0495 6050 0405 2533 2321 0116", "5871 3462 3311 4510 3076 8797 8033 6412 7305 4559"),
 "Sports Toto": ("sportstoto.csv", ["1508", "5241", "6336"], "2203 2182 9152 9276 4065 2275 6693 8790 9055 3493", "2464 0275 1077 0587 0431 5620 0478 8426 7819 3532"),
 "Da Ma Cai": ("damacai.csv", ["5434", "6342", "7652"], "3823 1405 2291 7459 4135 3141 5506 3223 6062 2542", "9361 6038 2980 0474 3591 9193 8698 7288 1624 4468"),
}
for op, (fn, top, sp, co) in R.items():
    path = f"data/{fn}"
    if any(r["date"] == "2026-10-17" for r in csv.DictReader(open(path))):
        print(op, "already present"); continue
    with open(path, "a", newline="") as fh:
        w = csv.writer(fh)
        for prize, n in zip(("1st", "2nd", "3rd"), top):
            w.writerow(["2026-10-17", "Sat", op, prize, n])
        for n in sp.split(): w.writerow(["2026-10-17", "Sat", op, "Special", n])
        for n in co.split(): w.writerow(["2026-10-17", "Sat", op, "Consolation", n])
    print(op, "added 23 rows")
EOF
tail -2 data/magnum.csv; tail -c 300 data/damacai.csv | tail -2
```

## 84. 2026-10-17 13:19 — Score all leads against 17 Oct results

```bash
python3 - <<'EOF'
import csv, collections
import numpy as np
res = collections.defaultdict(dict)   # op -> num -> prize
allrows = collections.defaultdict(list)
for fn in ("magnum.csv", "sportstoto.csv", "damacai.csv"):
    for r in csv.DictReader(open(f"data/{fn}")):
        if r["date"] == "2026-10-17":
            res[r["operator"]][r["4d_number"]] = r["prize"]
        elif r["date"] < "2026-10-17":
            allrows[r["operator"]].append(r["4d_number"])
BIG = {"1st": 2500, "2nd": 1000, "3rd": 500, "Special": 180, "Consolation": 60}
box = lambda n: "".join(sorted(n))
picks = collections.defaultdict(list)
for r in csv.DictReader(open("analysis/forward_log.csv")):
    if r["draw_date"] == "2026-10-17":
        picks[(r["variant"], r["operator"])].append(r["4d_number"])
def score(name, op_nums):
    s_hits, r_hits, b_hits, pay, stake = [], [], [], 0, 0
    for op, nums in op_nums.items():
        for n in nums:
            stake += 1
            w = res[op]
            if n in w:
                s_hits.append(f"{n} {op} {w[n]}"); pay += BIG[w[n]]
            rv = n[::-1]
            if rv != n and rv in w: r_hits.append(f"{n}->{rv} {op} {w[rv]}")
            for m, p in w.items():
                if m != n and box(m) == box(n): b_hits.append(f"{n}~{m} {op} {p}")
    print(f"{name}: {stake} RM1 Big bets -> straight {len(s_hits)} {s_hits} pay RM{pay}; reverse {r_hits}; i-Box (other arrangement) {b_hits}")
OPS = ["Magnum", "Sports Toto", "Da Ma Cai"]
for (v, op), nums in sorted(picks.items()):
    pass
variants = sorted({v for v, _ in picks})
for v in variants:
    d = {}
    for (vv, op), nums in picks.items():
        if vv != v: continue
        if op == "All":
            for o in OPS: d[o] = nums
        else: d[op] = nums
    score(v, d)
# lead 4: cold number per operator (each position's least frequent digit so far), lead 5: 1024 Magnum
cold = {}
for op in OPS:
    D = np.array([[int(c) for c in n] for n in allrows[op]])
    cnt = np.stack([np.bincount(D[:, p], minlength=10) for p in range(4)])
    cold[op] = ["".join(str(int(np.argmin(cnt[p] + np.arange(10) * 1e-9))) for p in range(4))]  # ties -> lower digit
print("cold numbers:", {o: c[0] for o, c in cold.items()})
score("cold number (lead 4)", cold)
score("1024 Magnum (lead 5)", {"Magnum": ["1024"]})
EOF
```

## 85. 2026-10-17 13:27 — Write the conversation log as markdown

```bash
mkdir -p docs && python3 - <<'EOF'
import json
m = json.load(open("/tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad/conv.json"))
L = ["# Conversation log", "",
     "The questions asked and the answers given while building this analysis (16-17 Oct 2026, times in UTC).",
     "Tool calls and raw command output are left out; the scripts and result files in `analysis/` hold those.",
     "A summary of the conclusions is in [analysis/FINDINGS.md](../analysis/FINDINGS.md).", ""]
q = 0
for role, ts, t in m:
    when = ts[:16].replace("T", " ")
    if role == "user":
        q += 1
        L += ["---", "", f"## {q}. Question ({when})", "", "> " + t.replace("\n", "\n> "), ""]
    else:
        L += [f"**Answer** ({when})", "", t, ""]
open("docs/conversation.md", "w").write("\n".join(L))
print(q, sum(len(x) for x in L))
EOF
grep -c "^## " docs/conversation.md; grep -n "gmail\|@" docs/conversation.md | head -3
```

## 86. 2026-10-18 12:02 — Add 18 Oct results and score all leads for 17 and 18 Oct

```bash
python3 - <<'EOF'
import csv
R = {
 "Magnum": ("magnum.csv", ["3196", "3806", "0127"], "3005 0382 9569 3804 4360 1744 0780 6132 0437 4960", "2176 4594 3006 9990 0063 2284 4380 1997 1844 9641"),
 "Sports Toto": ("sportstoto.csv", ["3166", "6640", "4937"], "9801 8909 9342 7417 3853 2567 5375 9038 6888 4950", "8216 3280 7885 8628 0712 6731 5304 8750 3767 4557"),
 "Da Ma Cai": ("damacai.csv", ["2454", "1240", "6521"], "9406 5673 5656 1068 5619 7556 3015 4694 9041 3665", "4974 4456 2836 8918 8030 1255 2405 7526 1467 8056"),
}
for op, (fn, top, sp, co) in R.items():
    path = f"data/{fn}"
    if any(r["date"] == "2026-10-18" for r in csv.DictReader(open(path))):
        print(op, "already present"); continue
    with open(path, "a", newline="") as fh:
        w = csv.writer(fh)
        for prize, n in zip(("1st", "2nd", "3rd"), top): w.writerow(["2026-10-18", "Sun", op, prize, n])
        for n in sp.split(): w.writerow(["2026-10-18", "Sun", op, "Special", n])
        for n in co.split(): w.writerow(["2026-10-18", "Sun", op, "Consolation", n])
    print(op, "added")
EOF
cat > analysis/score_live.py <<'EOF'
#!/usr/bin/env python3
"""Score the picks logged in forward_log.csv (before each draw) against the
results in data/*.csv, plus two no-formula leads computed from earlier draws:
the cold number (each position's least frequent digit per operator) and 1024 on
Magnum. RM1 Big per pick; payouts 1st 2500, 2nd 1000, 3rd 500, Special 180,
Consolation 60. Reverse and i-Box matches (other arrangements) are listed too.

Run from the repo root:  python3 analysis/score_live.py 2026-10-17 [2026-10-18 ...]
"""

import collections
import csv
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPS = ["Magnum", "Sports Toto", "Da Ma Cai"]
FILES = {"Magnum": "magnum.csv", "Sports Toto": "sportstoto.csv", "Da Ma Cai": "damacai.csv"}
BIG = {"1st": 2500, "2nd": 1000, "3rd": 500, "Special": 180, "Consolation": 60}


def load():
    rows = {op: list(csv.DictReader(open(os.path.join(ROOT, "data", f)))) for op, f in FILES.items()}
    log = list(csv.DictReader(open(os.path.join(ROOT, "analysis", "forward_log.csv"))))
    return rows, log


def picks_for(log, date):
    out = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in log:
        if r["draw_date"] == date:
            ops = OPS if r["operator"] in ("All", "all") else [r["operator"]]
            for o in ops:
                out[r["variant"]][o].append(r["4d_number"])
    return out


def cold_numbers(rows, date):
    out = {}
    for op in OPS:
        D = np.array([[int(c) for c in r["4d_number"]] for r in rows[op] if r["date"] < date])
        cnt = np.stack([np.bincount(D[:, p], minlength=10) for p in range(4)])
        out[op] = ["".join(str(int(np.argmin(cnt[p] + np.arange(10) * 1e-9))) for p in range(4))]
    return out


def score(nums_by_op, win):
    stake = pay = 0
    straight, reverse, ibox = [], [], []
    for op, nums in nums_by_op.items():
        w = win.get(op, {})
        for n in dict.fromkeys(nums):
            stake += 1
            if n in w:
                straight.append(f"{n} {op} {w[n]}")
                pay += BIG[w[n]]
            if n[::-1] != n and n[::-1] in w:
                reverse.append(f"{n}->{n[::-1]} {op} {w[n[::-1]]}")
            for m, p in w.items():
                if m != n and sorted(m) == sorted(n):
                    ibox.append(f"{n}~{m} {op} {p}")
    return stake, pay, straight, reverse, ibox


def main():
    rows, log = load()
    for date in sys.argv[1:]:
        win = {op: {r["4d_number"]: r["prize"] for r in rows[op] if r["date"] == date} for op in OPS}
        if not any(win.values()):
            print(f"{date}: no results in data/ yet")
            continue
        print(f"\n=== {date} ===")
        sets = dict(picks_for(log, date))
        sets["cold_number_noparam"] = cold_numbers(rows, date)
        sets["1024_magnum"] = {"Magnum": ["1024"]}
        tot_s = tot_p = 0
        for v in sorted(sets):
            stake, pay, s, rv, b = score(sets[v], win)
            tot_s += stake
            tot_p += pay
            extra = (f"; reverse {rv}" if rv else "") + (f"; i-Box {b}" if b else "")
            print(f"  {v:<36} {stake:>3} bets  straight {len(s)} {s if s else ''} RM{pay}{extra}")
        print(f"  all formulas together: RM{tot_p} back on RM{tot_s} staked")


if __name__ == "__main__":
    main()
EOF
python3 analysis/score_live.py 2026-10-17 2026-10-18
```

## 87. 2026-10-18 12:06 — Rebuild 18 Oct picks with old data to check they match the log

```bash
cat > analysis/update_picks.py <<'EOF'
#!/usr/bin/env python3
"""Rebuild the leads' picks for a draw date from all results before a cutoff,
so each new draw's results feed into the next draw's picks.

Leads:
  recur_S1a_mercurynak_venusrashi   S1 grid from all earlier days with the same
                                    Mercury nakshatra x Venus rashi (all operators)
  recur_S1b_karana_daypillar_ibox   S1 grid from the previous day with the same
                                    Karana x Day pillar (all operators)
  S1/S2_marsnak_marsrashi_mercombust per operator, S1 / S2 grid from all earlier
                                    days with the same Mars nakshatra x Mars rashi
                                    x Mercury combust (as in s12_combos.py)
The cold number and 1024 are handled in score_live.py.

Run from the repo root:
  python3 analysis/update_picks.py DRAW_DATE [CUTOFF]     (CUTOFF = DRAW_DATE by default;
                                                           only results dated before it are used)
  add --log to append the picks to forward_log.csv
"""

import datetime as dt
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am  # noqa: E402
import digit_models as dm  # noqa: E402

DIG = am.DIG
POW = np.array([1000, 100, 10, 1])
BITS = np.array([[(k >> (3 - p)) & 1 for p in range(4)] for k in range(16)])
D = None


def grid(top2):
    return sorted(int((top2[np.arange(4), BITS[k]] * POW).sum()) for k in range(16))


def same_days(date, factors, cutoff):
    ix, c2, ctx = am.date_codes(date, D.codes, D.labels, factors)
    m = np.ones(len(D.dates), bool)
    for f in factors:
        m &= D.codes[f] == c2[f][-1]
    m &= np.array([d < cutoff for d in D.dates])
    return np.flatnonzero(m), {f: ctx[f] for f in factors}


def counts(day_idx, op=None):
    sel = np.isin(D.rd, day_idx) & ((D.ro == op) if op is not None else True)
    if op is None:                                    # each number once per date over all operators
        key = np.unique(D.rd[sel].astype(np.int64) * 10000 + D.rn[sel])
        nums = key % 10000
    else:
        nums = D.rn[sel]
    C = np.zeros((4, 10))
    for p in range(4):
        C[p] = np.bincount(DIG[nums, p], minlength=10)
    return C


def picks_for(date, cutoff):
    out, info = {}, {}
    idx, v = same_days(date, ["mercury_nakshatra", "venus_rashi"], cutoff)
    C = counts(idx)
    out["recur_S1a_mercurynak_venusrashi"] = {"All": grid(np.argsort(-C, axis=1, kind="stable")[:, :2])}
    info["recur_S1a_mercurynak_venusrashi"] = f"{v}, {len(idx)} earlier days"
    idx, v = same_days(date, ["karana", "day_pillar"], cutoff)
    C = counts(idx[-1:])
    out["recur_S1b_karana_daypillar_ibox"] = {"All": grid(np.argsort(-C, axis=1, kind="stable")[:, :2])}
    info["recur_S1b_karana_daypillar_ibox"] = f"{v}, previous day {D.dates[idx[-1]]}"
    trip = ["mars_nakshatra", "mars_rashi", "mercury_combust"]
    idx, v = same_days(date, trip, cutoff)
    before = np.flatnonzero(np.array([d < cutoff for d in D.dates]))
    for s, sign in (("S1", -1), ("S2", 1)):
        name = f"{s}_marsnak_marsrashi_mercombust"
        out[name] = {}
        for o, op in enumerate(am.OPS):
            overall = counts(before, o)
            overall /= overall.sum(1, keepdims=True)
            C = counts(idx, o) + 1e-6 * overall
            out[name][op] = grid(np.argsort(sign * C, axis=1)[:, :2])
        info[name] = f"{v}, {len(idx)} earlier days"
    return out, info


def main():
    global D
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    date = args[0]
    cutoff = args[1] if len(args) > 1 else date
    D = dm.Data()
    out, info = picks_for(date, cutoff)
    print(f"Picks for {date} from results before {cutoff}:")
    for name, by_op in out.items():
        print(f"  {name} ({info[name]})")
        for op, nums in by_op.items():
            print(f"     {op:<12} " + " ".join(f"{n:04d}" for n in nums))
    if "--log" in sys.argv:
        now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
        with open(os.path.join(am.ROOT, "analysis", "forward_log.csv"), "a") as fh:
            for name, by_op in out.items():
                for op, nums in by_op.items():
                    for k, n in enumerate(nums, 1):
                        fh.write(f"{now},{date},{name}_upd,{op},{k},{n:04d}\n")
        print("logged to forward_log.csv with variant suffix _upd")


if __name__ == "__main__":
    main()
EOF
python3 analysis/update_picks.py 2026-10-18 2026-10-15 2>&1 | tail -14 > /tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad/old.txt; cat /tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad/old.txt
python3 - <<'EOF'
import csv, collections
lg = collections.defaultdict(list)
for r in csv.DictReader(open("analysis/forward_log.csv")):
    if r["draw_date"] == "2026-10-18" and ("recur" in r["variant"] or "marsnak" in r["variant"]):
        lg[(r["variant"], r["operator"])].append(r["4d_number"])
for k, v in sorted(lg.items()): print("logged", k, " ".join(sorted(v)))
EOF
```

## 88. 2026-10-18 12:06 — Rebuild 18 Oct picks with 17 Oct data and score them

```bash
python3 - <<'EOF'
import sys
sys.path.insert(0, "analysis")
import update_picks as up, score_live as sl, digit_models as dm
up.D = dm.Data()
rows, log = sl.load()
date = "2026-10-18"
win = {op: {r["4d_number"]: r["prize"] for r in rows[op] if r["date"] == date} for op in sl.OPS}
old, _ = up.picks_for(date, "2026-10-15")
new, info = up.picks_for(date, date)
for name in new:
    o = {op if op != "All" else "All": v for op, v in old[name].items()}
    changed = any(sorted(old[name][k]) != sorted(new[name][k]) for k in new[name])
    by_op = {op2: [f"{n:04d}" for n in v] for op, v in new[name].items() for op2 in (sl.OPS if op == "All" else [op])}
    stake, pay, s, rv, b = sl.score(by_op, win)
    print(f"{name}: {'CHANGED' if changed else 'unchanged'} ({info[name]})")
    for op, v in new[name].items():
        if sorted(v) != sorted(old[name][op]):
            print(f"    {op:<12} new: " + " ".join(f"{n:04d}" for n in v))
            print(f"    {'':<12} old: " + " ".join(f"{n:04d}" for n in old[name][op]))
    print(f"    vs 18 Oct: straight {s} RM{pay} on RM{stake}" + (f"; reverse {rv}" if rv else "") + (f"; i-Box {b}" if b else ""))
EOF
```

## 89. 2026-10-18 12:07 — Make and log updated picks for 21 Oct

```bash
python3 analysis/update_picks.py 2026-10-21 --log 2>&1 | tail -16; python3 - <<'EOF'
import sys; sys.path.insert(0, "analysis")
import score_live as sl
rows, _ = sl.load()
print("cold numbers for 21 Oct:", {o: v[0] for o, v in sl.cold_numbers(rows, "2026-10-21").items()})
EOF
```

## 90. 2026-10-18 12:08 — Check which data cutoff the 17 Oct picks used

```bash
python3 - <<'EOF'
import sys, csv, collections
sys.path.insert(0, "analysis")
import update_picks as up, digit_models as dm
up.D = dm.Data()
lg = collections.defaultdict(list)
for r in csv.DictReader(open("analysis/forward_log.csv")):
    if r["draw_date"] == "2026-10-17":
        lg[(r["variant"], r["operator"])].append(int(r["4d_number"]))
for cut in ("2026-10-04", "2026-10-15"):
    new, info = up.picks_for("2026-10-17", cut)
    same = {name: all(sorted(v) == sorted(lg[(name, op)]) for op, v in byop.items()) for name, byop in new.items()}
    print(f"cutoff before {cut}: matches logged 17 Oct picks -> {same}")
EOF
```

## 91. 2026-10-18 12:08 — Straight and i-Box hits for 17 and 18 Oct with up-to-date picks

```bash
python3 - <<'EOF'
import sys, math
sys.path.insert(0, "analysis")
import update_picks as up, digit_models as dm, score_live as sl
up.D = dm.Data()
for cut in ("2026-10-04", "2026-10-15"):
    _, info = up.picks_for("2026-10-17", cut)
    print("cutoff", cut, {k: v.split(", ")[-1] for k, v in info.items()})
rows, _ = sl.load()
BIG = sl.BIG
def perms(n):
    c = [n.count(d) for d in set(n)]
    return math.factorial(4) // math.prod(math.factorial(x) for x in c)
names = {"recur_S1a_mercurynak_venusrashi": "1. Mercury nakshatra x Venus rashi S1",
         "recur_S1b_karana_daypillar_ibox": "2. Karana x Day pillar S1",
         "S1_marsnak_marsrashi_mercombust": "3. S1 Mars triple",
         "S2_marsnak_marsrashi_mercombust": "3. S2 Mars triple"}
for date, cut in (("2026-10-17", "2026-10-17"), ("2026-10-18", "2026-10-18")):
    win = {op: {r["4d_number"]: r["prize"] for r in rows[op] if r["date"] == date} for op in sl.OPS}
    picks, _ = up.picks_for(date, cut)
    sets = {names[k]: {o2: [f"{n:04d}" for n in v] for o, v in bo.items() for o2 in (sl.OPS if o == "All" else [o])} for k, bo in picks.items()}
    sets["4. Cold number"] = sl.cold_numbers(rows, date)
    sets["5. 1024 (Magnum)"] = {"Magnum": ["1024"]}
    print(f"\n=== {date} ===")
    for name, byop in sets.items():
        st, ib, sp, ip, n = [], [], 0, 0.0, 0
        for op, nums in byop.items():
            w = win[op]
            for x in nums:
                n += 1
                if x in w: st.append(f"{x} {op} {w[x]}"); sp += BIG[w[x]]
                for m, p in w.items():
                    if sorted(m) == sorted(x):
                        ib.append(f"{x}->{m} {op} {p}"); ip += BIG[p] / perms(x)
        print(f"{name}|{n}|{len(st)}|{'; '.join(st) or '-'}|RM{sp}|{len(ib)}|{'; '.join(ib) or '-'}|RM{ip:.2f}")
EOF
```

## 92. 2026-10-18 12:15 — Show straight hits and de-duplicate i-Box pick sets

```bash
python3 - <<'EOF'
import json, csv
R = json.load(open("analysis/rescan_live_results.json"))
win = {}
for fn in ("magnum", "sportstoto", "damacai"):
    for r in csv.DictReader(open(f"data/{fn}.csv")):
        if r["date"] in R: win.setdefault(r["date"], {}).setdefault(r["4d_number"], []).append(f"{r['operator']} {r['prize']}")
for d, rep in R.items():
    for x in rep["top_tests"]:
        if x["column"].endswith("straight") and x["hits"]:
            ps = [f"{p:04d}" for p in x["picks"]]
            print(d, x["column"], x["test"], [(p, win[d][p]) for p in ps if p in win[d]])
    ib = [x for x in rep["top_tests"] if x["column"].endswith("ibox")]
    uniq = {}
    for x in ib: uniq[tuple(sorted(x["picks"]))] = x
    print(d, "i-Box top tests:", len(ib), "distinct pick sets:", len(uniq), "hits", sum(x["hits"] for x in uniq.values()), "exp", round(sum(x["expected"] for x in uniq.values()), 1))
EOF
```

## 93. 2026-10-18 12:15 — Commit and push rescan script, results and findings

```bash
python3 - <<'EOF'
p = "analysis/FINDINGS.md"
s = open(p).read()
s = s.replace("Score any date with `python3 analysis/score_live.py YYYY-MM-DD`;",
"""Full rescan before each draw (`rescan_live.py`: all singles and pairs, S1/S2, a/b,
Straight/Reverse/i-Box, using only earlier results): the top tests barely move
(z changes of about 0.01) and their picks score at chance: Straight 1 hit vs 2.2
expected on 17 Oct and 1 vs 2.0 on 18 Oct; i-Box (distinct pick sets) 27 vs 28.7
and 33 vs 30.6.

Score any date with `python3 analysis/score_live.py YYYY-MM-DD`;""")
open(p, "w").write(s)
EOF
git add analysis/rescan_live.py analysis/rescan_live_results.json analysis/FINDINGS.md && git commit -qm "Rescan all parameters before each live draw and score the new top picks

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q origin claude/4d-results-scraper-9ptbd5 && git status -sb | head -1
```

## 94. 2026-10-18 13:52 — Write whole-number hot/cold test and time one evaluation

```bash
cat > analysis/whole_number_test.py <<'EOF'
#!/usr/bin/env python3
"""Whole-number hot / cold picks from earlier days with the same parameter value(s).

For each draw day whose value (single parameter) or pair of values occurred
before: count how many times each 4D number won (any prize, any operator, once
per date) on ALL earlier same-value days.
  hot   16 numbers with the highest count (ties -> more wins overall before
        that day, then lower number)
  cold  16 numbers with the lowest count (ties -> fewer wins overall, then
        lower number)
Scored as Straight / Reverse / i-Box with chance from that year's digit mix
(as recurrence_s12.py). (The "previous same-value day only" version is the
number-recurrence test already done in recurrence_perm.py.)

Checks per column (hot/cold x rule): the 5 tests with the best z before 2012,
scored 2012-2026, against the same procedure on shifted parameter calendars.
References: hot / cold with no parameter.

Run from the repo root:  python3 analysis/whole_number_test.py [n_shifts]
"""

import itertools
import json
import math
import multiprocessing as mp
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recurrence_s12 as r  # noqa: E402
import recurrence_s12_k as rk  # noqa: E402

SPLIT = 2012
COLS = [(s, rule) for s in ("hot", "cold") for rule in ("straight", "reverse", "ibox")]
NUM = np.arange(10000)


def setup():
    r.setup()
    G = r.G
    G["yr"] = np.array([int(d[:4]) for d in G["D"].dates])
    W = G["W"]
    # wins of each number on all days before day t
    G["Gc"] = np.vstack([np.zeros((1, 10000), np.int16), np.cumsum(W, 0, dtype=np.int16)[:-1]])


def evaluate(cells):
    """(len(COLS), 4): hits before, expected before, hits after, expected after."""
    G = r.G
    W, Gc = G["W"], G["Gc"]
    order = np.lexsort((np.arange(len(cells)), cells))
    sc = cells[order]
    bounds = np.r_[0, np.flatnonzero(np.diff(sc)) + 1, len(sc)]
    days, hot, cold = [], [], []
    for a, b in zip(bounds[:-1], bounds[1:]):
        cnt = np.zeros(10000, np.float64)
        for k, t in enumerate(order[a:b]):
            if k:
                g = Gc[t].astype(np.float64)
                kh = cnt * 1e4 + g - NUM * 1e-5
                kc = -(cnt * 1e4 + g) - NUM * 1e-5
                hot.append(np.argpartition(-kh, 16)[:16])
                cold.append(np.argpartition(-kc, 16)[:16])
                days.append(t)
            cnt += W[t]
    days = np.array(days)
    late = G["yr"][days] >= SPLIT
    out = []
    for s, P in (("hot", np.array(hot)), ("cold", np.array(cold))):
        res = rk.score_days(days, P)
        for rule in ("straight", "reverse", "ibox"):
            h, e = res[rule][0][:, -1].astype(float), res[rule][1][:, -1]
            out.append((h[~late].sum(), e[~late].sum(), h[late].sum(), e[late].sum()))
    return np.array(out)


def task(args):
    test, shift = args
    return evaluate(r.cells_of(test, shift))


def zz(o, e):
    return (o - e) / np.sqrt(np.maximum(e, 1e-9))


def main():
    n_shifts = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    t0 = time.time()
    setup()
    tests = [(f,) for f in r.FACT] + list(itertools.combinations(r.FACT, 2))
    names = [" x ".join(t) for t in tests]
    ref = evaluate(np.zeros(r.G["nd"], np.int64))
    print("No parameter (all earlier days):")
    for ci, (s, rule) in enumerate(COLS):
        o = ref[ci]
        print(f"   {s:<5} {rule:<9} before 2012 x{o[0] / o[1]:.3f} (z {zz(o[0], o[1]):+.2f}) | "
              f"2012-2026 x{o[2] / o[3]:.3f} (z {zz(o[2], o[3]):+.2f})", flush=True)
    with mp.get_context("fork").Pool(4) as pool:
        A = np.array(pool.map(task, [(t, 0) for t in tests], chunksize=8))
        print(f"{len(tests)} tests ({time.time() - t0:.0f}s)", flush=True)
        rng = np.random.default_rng(9)
        null = []
        for k in range(n_shifts):
            sh = int(rng.integers(170, r.G["nd"] - 170))
            B = np.array(pool.map(task, [(t, sh) for t in tests], chunksize=8))
            zb, za = zz(B[:, :, 0], B[:, :, 1]), zz(B[:, :, 2], B[:, :, 3])
            top = np.argsort(-zb, axis=0)[:5]
            null.append({"forward": np.take_along_axis(za, top, 0).mean(0).tolist(),
                         "best_all": zz(B[:, :, 0] + B[:, :, 2], B[:, :, 1] + B[:, :, 3]).max(0).tolist()})
            print(f"shift {k + 1}/{n_shifts} ({time.time() - t0:.0f}s)", flush=True)
    zb, za = zz(A[:, :, 0], A[:, :, 1]), zz(A[:, :, 2], A[:, :, 3])
    zall = zz(A[:, :, 0] + A[:, :, 2], A[:, :, 1] + A[:, :, 3])
    top = np.argsort(-zb, axis=0)[:5]
    fwd = np.take_along_axis(za, top, 0).mean(0)
    nf = np.array([x["forward"] for x in null])
    nb = np.array([x["best_all"] for x in null])
    report = {"reference_no_parameter": ref.tolist(), "columns": []}
    print("\nPer column: forward = top 5 tests chosen on draws before 2012, mean z on 2012-2026")
    for ci, (s, rule) in enumerate(COLS):
        print(f"\n{s} {rule}: forward {fwd[ci]:+.2f} (shifted {nf[:, ci].mean():+.2f}, {int((nf[:, ci] >= fwd[ci]).sum())}/{n_shifts} as high) | "
              f"best z all years {zall[:, ci].max():+.2f} [{names[int(np.argmax(zall[:, ci]))]}] "
              f"(shifted best {nb[:, ci].mean():+.2f}, {int((nb[:, ci] >= zall[:, ci].max()).sum())}/{n_shifts} as high)")
        rows = []
        for q in top[:, ci]:
            o = A[q, ci]
            print(f"   {names[q]:<44} before z {zb[q, ci]:+.2f} -> after {o[2]:.0f}/{o[3]:.1f} (x{o[2] / o[3]:.3f}, z {za[q, ci]:+.2f})")
            rows.append({"test": names[q], "z_before": float(zb[q, ci]), "hits_after": float(o[2]),
                         "exp_after": float(o[3]), "z_after": float(za[q, ci])})
        report["columns"].append({"strategy": s, "rule": rule, "forward_mean_z": float(fwd[ci]),
                                  "null_forward": nf[:, ci].tolist(), "best_z_all": float(zall[:, ci].max()),
                                  "best_test": names[int(np.argmax(zall[:, ci]))], "null_best": nb[:, ci].tolist(),
                                  "forward_tests": rows})
    json.dump(report, open(os.path.join(r.ROOT, "analysis", "whole_number_results.json"), "w"), indent=1)
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
EOF
python3 - <<'EOF'
import sys, time
sys.path.insert(0, "analysis")
import numpy as np
import whole_number_test as w
w.setup()
t = time.time(); A = w.evaluate(w.r.cells_of(("mercury_nakshatra", "venus_rashi"))); print("time", round(time.time() - t, 2))
print(A.round(1))
EOF
```

## 95. 2026-10-18 13:53 — Speed up whole-number picks and confirm identical results

```bash
python3 - <<'EOF'
p = "analysis/whole_number_test.py"
s = open(p).read()
s = s.replace('''    G["Gc"] = np.vstack([np.zeros((1, 10000), np.int16), np.cumsum(W, 0, dtype=np.int16)[:-1]])
''', '''    G["Gc"] = np.vstack([np.zeros((1, 10000), np.int16), np.cumsum(W, 0, dtype=np.int16)[:-1]])
    # per day: numbers by overall wins before that day, hottest first / coldest first (ties -> lower number)
    G["ghot"] = np.array([np.lexsort((NUM, -g))[:64] for g in G["Gc"]])
    G["gcold"] = np.array([np.lexsort((NUM, g))[:300] for g in G["Gc"]])
''')
a = s.index("    days, hot, cold = [], [], []")
b = s.index("    days = np.array(days)")
s = s[:a] + '''    days, hot, cold = [], [], []
    ghot, gcold = G["ghot"], G["gcold"]
    for a, b in zip(bounds[:-1], bounds[1:]):
        cnt = np.zeros(10000, np.int32)
        for k, t in enumerate(order[a:b]):
            if k:
                nz = np.flatnonzero(cnt)
                cand = np.union1d(nz, ghot[t]) if len(nz) < 16 else nz
                g = Gc[t, cand].astype(np.float64)
                kh = cnt[cand] * 1e4 + g - cand * 1e-5
                hot.append(cand[np.argsort(-kh)[:16]])
                c = gcold[t][cnt[gcold[t]] == 0][:16]
                cold.append(c)
                days.append(t)
            cnt += W[t]
''' + s[b:]
open(p, "w").write(s)
EOF
python3 - <<'EOF'
import sys, time
sys.path.insert(0, "analysis")
import numpy as np
import whole_number_test as w
t = time.time(); w.setup(); print("setup", round(time.time() - t, 1))
t = time.time(); A = w.evaluate(w.r.cells_of(("mercury_nakshatra", "venus_rashi"))); print("time", round(time.time() - t, 2))
print(A.round(1))
EOF
```

## 96. 2026-10-18 14:01 — Check the no-parameter case runs

```bash
python3 - <<'EOF'
import sys, time
sys.path.insert(0, "analysis")
import numpy as np
import whole_number_test as w
w.setup()
t = time.time(); A = w.evaluate(np.zeros(w.r.G["nd"], np.int64)); print("noparam time", round(time.time() - t, 1)); print(A.round(1))
EOF
```

## 97. 2026-10-18 15:29 — Commit results and update findings list

```bash
python3 - <<'EOF'
p = "analysis/FINDINGS.md"
s = open(p).read()
s = s.replace("| S1 / S2 picks from earlier same-value days, Straight / Reverse / i-Box | `recurrence_s12.py`, `recurrence_s12_forward.py` |",
"| S1 / S2 picks from earlier same-value days, Straight / Reverse / i-Box | `recurrence_s12.py`, `recurrence_s12_forward.py` |\n| Whole-number hot / cold (16 numbers that won most / least on earlier same-value days) | `whole_number_test.py` |\n| Exact positions: longitudes, angles between planets, aspects, position within sign | `continuous_astro.py` |")
open(p, "w").write(s)
EOF
git add analysis/whole_number_results.json analysis/FINDINGS.md && git commit -qm "Add whole-number hot/cold results; list new tests in findings

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q origin claude/4d-results-scraper-9ptbd5 && git status -sb | head -1
```

## 98. 2026-10-19 01:53 — Write S3 test and sanity-check picks and timing

```bash
cd /home/user/4DPrediction && cat > analysis/recurrence_s3.py <<'EOF'
#!/usr/bin/env python3
"""S3 = the hottest AND the coldest digit in each position, combined: 2^4 = 16
numbers (e.g. hottest 7/3/4/7 and coldest 2/8/0/9 -> 7347, 7349, ..., 2809).

Tested like S1 / S2 in recurrence_s12.py: 78 single parameters and 3,003 pairs;
(a) digit counts from ALL earlier draw days with the same value(s), (b) from the
PREVIOUS same-value day only; Straight / Reverse / i-Box hits on all 3
operators; chance from that year's digit mix per position.
Checks per column (version x rule):
  scan     tests with z > 2 and best z over all years
  forward  the 5 tests with the best z before 2012, scored 2012-2026
both against the same procedure on circularly shifted parameter calendars.
Reference: S3 with no parameter.

Run from the repo root:  python3 analysis/recurrence_s3.py [n_shifts]
"""

import itertools
import json
import math
import multiprocessing as mp
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recurrence_s12 as r  # noqa: E402
import recurrence_s12_k as rk  # noqa: E402

SPLIT = 2012
RULES = ("straight", "reverse", "ibox")
COLS = [(v, rule) for v in "ab" for rule in RULES]
POW = np.array([1000, 100, 10, 1])
BITS = r.BITS


def s3_picks(C):
    """C (n, 4, 10) -> (n, 16): hottest and coldest digit per position (ties -> lower digit;
    if the two coincide, the next coldest is used)."""
    hot = np.argsort(-C, axis=2, kind="stable")[:, :, 0]
    asc = np.argsort(C, axis=2, kind="stable")
    cold = np.where(asc[:, :, 0] == hot, asc[:, :, 1], asc[:, :, 0])
    two = np.stack([hot, cold], axis=2)                                    # (n, 4, 2): bit 0 = hot, 1 = cold
    dig = np.take_along_axis(two, BITS.T[None, :, :], 2)                  # (n, 4, 16)
    return (dig * POW[None, :, None]).sum(1)


def evaluate(cells):
    G = r.G
    dday = G["dday"]
    order = np.lexsort((np.arange(len(cells)), cells))
    sc = cells[order]
    newgrp = np.r_[True, sc[1:] != sc[:-1]]
    has_prev = ~newgrp
    days = order[has_prev]
    late = G["yr"][days] >= SPLIT
    cs = np.cumsum(dday[order], axis=0)
    start = np.maximum.accumulate(np.where(newgrp, np.arange(len(sc)), 0))
    base = np.where((start > 0)[:, None, None], cs[np.maximum(start - 1, 0)], 0)
    src = {"a": (cs - dday[order] - base)[has_prev], "b": dday[order[:-1]][has_prev[1:]]}
    out = []
    for v in "ab":
        res = rk.score_days(days, s3_picks(src[v]))
        for rule in RULES:
            h, e = res[rule][0][:, -1].astype(float), res[rule][1][:, -1]
            out.append((h[~late].sum(), e[~late].sum(), h[late].sum(), e[late].sum()))
    return np.array(out)


def task(args):
    test, shift = args
    return evaluate(r.cells_of(test, shift))


def zz(o, e):
    return (o - e) / np.sqrt(np.maximum(e, 1e-9))


def summary(A):
    zb, za = zz(A[:, :, 0], A[:, :, 1]), zz(A[:, :, 2], A[:, :, 3])
    zall = zz(A[:, :, 0] + A[:, :, 2], A[:, :, 1] + A[:, :, 3])
    top = np.argsort(-zb, axis=0)[:5]
    return zb, za, zall, top, np.take_along_axis(za, top, 0).mean(0)


def main():
    n_shifts = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    t0 = time.time()
    r.setup()
    r.G["yr"] = np.array([int(d[:4]) for d in r.G["D"].dates])
    tests = [(f,) for f in r.FACT] + list(itertools.combinations(r.FACT, 2))
    names = [" x ".join(t) for t in tests]
    ref = evaluate(np.zeros(r.G["nd"], np.int64))
    print("S3 with no parameter:")
    for ci, (v, rule) in enumerate(COLS):
        o = ref[ci]
        print(f"   ({v}) {rule:<9} before 2012 x{o[0] / o[1]:.3f} (z {zz(o[0], o[1]):+.2f}) | 2012-2026 x{o[2] / o[3]:.3f} (z {zz(o[2], o[3]):+.2f})")
    with mp.get_context("fork").Pool(4) as pool:
        A = np.array(pool.map(task, [(t, 0) for t in tests], chunksize=16))
        print(f"{len(tests)} tests ({time.time() - t0:.0f}s)", flush=True)
        rng = np.random.default_rng(21)
        null = []
        for k in range(n_shifts):
            sh = int(rng.integers(170, r.G["nd"] - 170))
            B = np.array(pool.map(task, [(t, sh) for t in tests], chunksize=16))
            _, _, zallB, _, fwdB = summary(B)
            null.append({"z_gt_2": (zallB > 2).sum(0).tolist(), "best": zallB.max(0).tolist(), "forward": fwdB.tolist()})
            print(f"shift {k + 1}/{n_shifts} ({time.time() - t0:.0f}s)", flush=True)
    zb, za, zall, top, fwd = summary(A)
    ng = np.array([x["z_gt_2"] for x in null])
    nb = np.array([x["best"] for x in null])
    nf = np.array([x["forward"] for x in null])
    report = {"tests": len(tests), "n_shifts": n_shifts, "reference_no_parameter": ref.tolist(), "columns": []}
    print("\ncolumn          z>2 real | shifted mean (range)  best z real | shifted mean, shifts as high  "
          "forward real | shifted mean, shifts as high")
    for ci, (v, rule) in enumerate(COLS):
        cnt, best = int((zall[:, ci] > 2).sum()), float(zall[:, ci].max())
        print(f"({v}) {rule:<10} {cnt:>5} | {ng[:, ci].mean():>5.0f} ({ng[:, ci].min()}-{ng[:, ci].max()})   "
              f"{best:+.2f} | {nb[:, ci].mean():+.2f}, {int((nb[:, ci] >= best).sum())}/{n_shifts}   "
              f"{fwd[ci]:+.2f} | {nf[:, ci].mean():+.2f}, {int((nf[:, ci] >= fwd[ci]).sum())}/{n_shifts}")
        rows = []
        for q in top[:, ci]:
            o = A[q, ci]
            rows.append({"test": names[q], "z_before": float(zb[q, ci]), "hits_after": float(o[2]),
                         "exp_after": float(o[3]), "z_after": float(za[q, ci])})
        best_q = int(np.argmax(zall[:, ci]))
        report["columns"].append({"version": v, "rule": rule, "z_gt_2": cnt, "null_z_gt_2": ng[:, ci].tolist(),
                                  "best_z": best, "best_test": names[best_q], "null_best": nb[:, ci].tolist(),
                                  "forward_mean_z": float(fwd[ci]), "null_forward": nf[:, ci].tolist(),
                                  "forward_tests": rows})
    print("\nForward detail (top 5 chosen on draws before 2012 -> 2012-2026):")
    for c in report["columns"]:
        print(f"  ({c['version']}) {c['rule']}   best over all years: {c['best_test']} (z {c['best_z']:+.2f})")
        for x in c["forward_tests"]:
            print(f"     {x['test']:<44} before z {x['z_before']:+.2f} -> after {x['hits_after']:.0f}/{x['exp_after']:.1f} "
                  f"(x{x['hits_after'] / x['exp_after']:.3f}, z {x['z_after']:+.2f})")
    json.dump(report, open(os.path.join(r.ROOT, "analysis", "recurrence_s3_results.json"), "w"), indent=1)
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
EOF
python3 - <<'EOF'
import sys, time
sys.path.insert(0, "analysis")
import numpy as np
import recurrence_s3 as s
s.r.setup(); s.r.G["yr"] = np.array([int(d[:4]) for d in s.r.G["D"].dates])
C = np.zeros((1, 4, 10)); C[0] = [[605,601,581,500,500,500,500,500,499,470]]*4
print(sorted(s.s3_picks(C)[0]))
t = time.time(); A = s.evaluate(s.r.cells_of(("mercury_nakshatra", "venus_rashi"))); print(round(time.time() - t, 2)); print(A.round(1))
EOF
```

## 99. 2026-10-19 02:13 — Commit S3 results and update findings

```bash
python3 - <<'EOF'
p = "analysis/FINDINGS.md"
s = open(p).read()
s = s.replace("| Whole-number hot / cold", "| S3: hottest + coldest digit per position, 16 numbers, single / pair parameters | `recurrence_s3.py` |\n| Whole-number hot / cold", 1)
open(p, "w").write(s)
EOF
git add analysis/recurrence_s3_results.json analysis/FINDINGS.md && git commit -qm "Add S3 recurrence results

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q origin claude/4d-results-scraper-9ptbd5 && git status -sb | head -1
```

## 100. 2026-10-19 06:57 — Write rank-pair test and sanity-check picks and timing

```bash
cd /home/user/4DPrediction && cat > analysis/recurrence_rankpairs.py <<'EOF'
#!/usr/bin/env python3
"""S3-style picks for every hot/cold rank pair. In each position the digits are
ranked 1 (hottest) .. 10 (coldest) from earlier same-value days; a pair takes
the digit of rank k and rank 11-k in each position, 2^4 = 16 numbers:
  1+10 (= S3), 2+9, 3+8, 4+7, 5+6
Same tests and checks as recurrence_s3.py: 78 single parameters and 3,003 pairs,
(a) all earlier / (b) previous same-value day, Straight / Reverse / i-Box,
forward (top 5 before 2012 -> 2012-2026) and shifted parameter calendars.
Ranks use counts with ties to the lower digit.

Run from the repo root:  python3 analysis/recurrence_rankpairs.py [n_shifts]
"""

import itertools
import json
import os
import sys
import time
import multiprocessing as mp

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recurrence_s12 as r  # noqa: E402
import recurrence_s12_k as rk  # noqa: E402
import recurrence_s3 as s3  # noqa: E402

PAIRS = [(0, 9), (1, 8), (2, 7), (3, 6), (4, 5)]
RULES = s3.RULES
COLS = [(pr, v, rule) for pr in PAIRS for v in "ab" for rule in RULES]
POW = s3.POW
BITS = r.BITS
SPLIT = s3.SPLIT


def label(pr):
    return f"{pr[0] + 1}+{pr[1] + 1}"


def pair_picks(order, pr):
    two = order[:, :, list(pr)]                                           # (n, 4, 2)
    dig = np.take_along_axis(two, BITS.T[None, :, :], 2)
    return (dig * POW[None, :, None]).sum(1)


def evaluate(cells):
    G = r.G
    dday = G["dday"]
    order = np.lexsort((np.arange(len(cells)), cells))
    sc = cells[order]
    newgrp = np.r_[True, sc[1:] != sc[:-1]]
    has_prev = ~newgrp
    days = order[has_prev]
    late = G["yr"][days] >= SPLIT
    cs = np.cumsum(dday[order], axis=0)
    start = np.maximum.accumulate(np.where(newgrp, np.arange(len(sc)), 0))
    base = np.where((start > 0)[:, None, None], cs[np.maximum(start - 1, 0)], 0)
    src = {"a": (cs - dday[order] - base)[has_prev], "b": dday[order[:-1]][has_prev[1:]]}
    ranked = {v: np.argsort(-C, axis=2, kind="stable") for v, C in src.items()}   # digit at each rank
    res = {}
    for pr in PAIRS:
        for v in "ab":
            sd = rk.score_days(days, pair_picks(ranked[v], pr))
            for rule in RULES:
                h, e = sd[rule][0][:, -1].astype(float), sd[rule][1][:, -1]
                res[(pr, v, rule)] = (h[~late].sum(), e[~late].sum(), h[late].sum(), e[late].sum())
    return np.array([res[c] for c in COLS])


def task(args):
    test, shift = args
    return evaluate(r.cells_of(test, shift))


def main():
    n_shifts = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    t0 = time.time()
    r.setup()
    r.G["yr"] = np.array([int(d[:4]) for d in r.G["D"].dates])
    tests = [(f,) for f in r.FACT] + list(itertools.combinations(r.FACT, 2))
    names = [" x ".join(t) for t in tests]
    zz = s3.zz
    ref = evaluate(np.zeros(r.G["nd"], np.int64))
    with mp.get_context("fork").Pool(4) as pool:
        A = np.array(pool.map(task, [(t, 0) for t in tests], chunksize=16))
        print(f"{len(tests)} tests x {len(COLS)} columns ({time.time() - t0:.0f}s)", flush=True)
        rng = np.random.default_rng(31)
        null = []
        for k in range(n_shifts):
            sh = int(rng.integers(170, r.G["nd"] - 170))
            B = np.array(pool.map(task, [(t, sh) for t in tests], chunksize=16))
            _, _, zallB, _, fwdB = s3.summary(B)
            null.append({"z_gt_2": (zallB > 2).sum(0).tolist(), "best": zallB.max(0).tolist(), "forward": fwdB.tolist()})
            print(f"shift {k + 1}/{n_shifts} ({time.time() - t0:.0f}s)", flush=True)
    zb, za, zall, top, fwd = s3.summary(A)
    ng = np.array([x["z_gt_2"] for x in null])
    nb = np.array([x["best"] for x in null])
    nf = np.array([x["forward"] for x in null])
    report = {"tests": len(tests), "n_shifts": n_shifts, "columns": []}
    print(f"\nranks  ver rule      | no param 2012-26 | z>2 real (shifted) | best z real (shifted, as high) | forward real (shifted, as high)")
    for ci, (pr, v, rule) in enumerate(COLS):
        o = ref[ci]
        cnt, best = int((zall[:, ci] > 2).sum()), float(zall[:, ci].max())
        print(f"{label(pr):<6} ({v}) {rule:<9} | x{o[2] / o[3]:.3f} ({zz(o[2], o[3]):+.2f}) | {cnt:>4} ({ng[:, ci].mean():>4.0f}) | "
              f"{best:+.2f} ({nb[:, ci].mean():+.2f}, {int((nb[:, ci] >= best).sum())}/{n_shifts}) | "
              f"{fwd[ci]:+.2f} ({nf[:, ci].mean():+.2f}, {int((nf[:, ci] >= fwd[ci]).sum())}/{n_shifts})")
        report["columns"].append({
            "ranks": label(pr), "version": v, "rule": rule,
            "no_param_after": {"hits": float(o[2]), "exp": float(o[3])},
            "z_gt_2": cnt, "null_z_gt_2": ng[:, ci].tolist(), "best_z": best,
            "best_test": names[int(np.argmax(zall[:, ci]))], "null_best": nb[:, ci].tolist(),
            "forward_mean_z": float(fwd[ci]), "null_forward": nf[:, ci].tolist(),
            "forward_tests": [{"test": names[q], "z_before": float(zb[q, ci]), "hits_after": float(A[q, ci, 2]),
                               "exp_after": float(A[q, ci, 3]), "z_after": float(za[q, ci])} for q in top[:, ci]]})
    print("\nBy rank pair (averaged over versions and rules): forward real vs shifted; no-parameter ratio after 2012")
    for pr in PAIRS:
        idx = [ci for ci, c in enumerate(COLS) if c[0] == pr]
        nr = np.mean([ref[ci, 2] / ref[ci, 3] for ci in idx])
        print(f"   {label(pr):<5} forward {fwd[idx].mean():+.2f} vs shifted {nf[:, idx].mean():+.2f} "
              f"(real beats {np.mean([(nf[:, ci] < fwd[ci]).mean() for ci in idx]):.0%} of shifts); no-parameter x{nr:.3f}")
    beat = np.array([(nf[:, ci] < fwd[ci]).mean() for ci in range(len(COLS))])
    print(f"\nColumns where the real forward beats every shifted calendar: {int((beat == 1).sum())} of {len(COLS)} "
          f"(about {len(COLS) / (n_shifts + 1):.1f} expected by chance)")
    for ci in np.flatnonzero(beat == 1):
        pr, v, rule = COLS[ci]
        print(f"   {label(pr)} ({v}) {rule}: forward {fwd[ci]:+.2f} vs shifted {nf[:, ci].mean():+.2f}")
        for x in report["columns"][ci]["forward_tests"][:3]:
            print(f"      {x['test']:<44} before z {x['z_before']:+.2f} -> after {x['hits_after']:.0f}/{x['exp_after']:.1f} "
                  f"(x{x['hits_after'] / x['exp_after']:.3f}, z {x['z_after']:+.2f})")
    json.dump(report, open(os.path.join(r.ROOT, "analysis", "recurrence_rankpairs_results.json"), "w"), indent=1)
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
EOF
python3 - <<'EOF'
import sys, time
sys.path.insert(0, "analysis")
import numpy as np
import recurrence_rankpairs as rp
rp.r.setup(); rp.r.G["yr"] = np.array([int(d[:4]) for d in rp.r.G["D"].dates])
C = np.array([[[605,601,581,560,550,540,530,520,499,470]]*4], float)
o = np.argsort(-C, axis=2, kind="stable")
for pr in rp.PAIRS: print(rp.label(pr), sorted(rp.pair_picks(o, pr)[0])[:4])
t = time.time(); A = rp.evaluate(rp.r.cells_of(("mercury_nakshatra", "venus_rashi"))); print("time", round(time.time() - t, 2), A.shape)
EOF
```

## 101. 2026-10-19 07:34 — Commit rank-pair results and update findings

```bash
python3 - <<'EOF'
p = "analysis/FINDINGS.md"
s = open(p).read()
s = s.replace("| Whole-number hot / cold", "| Rank pairs: 2nd hottest + 2nd coldest, 3rd + 3rd, 4th + 4th, 5th + 6th (and S3 again) | `recurrence_rankpairs.py` |\n| Whole-number hot / cold", 1)
open(p, "w").write(s)
EOF
git add analysis/recurrence_rankpairs_results.json analysis/FINDINGS.md && git commit -qm "Add rank-pair results

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q origin claude/4d-results-scraper-9ptbd5 && git status -sb | head -1
```

## 102. 2026-10-19 10:21 — Year-by-year performance of the main leads since 2012

```bash
cd /home/user/4DPrediction && python3 - <<'EOF' 2>&1 | grep -v "^computed"
import sys
sys.path.insert(0, "analysis")
import numpy as np
import recurrence_s12 as r, recurrence_s12_k as rk, recurrence_rankpairs as rp
r.setup(); G = r.G; D = G["D"]
yr = np.array([int(d[:4]) for d in D.dates]); G["yr"] = yr

def per_day(test, kind, version):
    cells = r.cells_of(test)
    order = np.lexsort((np.arange(len(cells)), cells)); sc = cells[order]
    ng = np.r_[True, sc[1:] != sc[:-1]]; hp = ~ng; days = order[hp]
    cs = np.cumsum(G["dday"][order], 0); st = np.maximum.accumulate(np.where(ng, np.arange(len(sc)), 0))
    base = np.where((st > 0)[:, None, None], cs[np.maximum(st - 1, 0)], 0)
    C = (cs - G["dday"][order] - base)[hp] if version == "a" else G["dday"][order[:-1]][hp[1:]]
    if kind == "S1": P = r.picks(C, True)
    elif kind == "S2": P = r.picks(C, False)
    else: P = rp.pair_picks(np.argsort(-C, axis=2, kind="stable"), kind)
    return days, rk.score_days(days, P)

leads = [
 ("Mercury nakshatra x Venus rashi, S1 (a) Straight", ("mercury_nakshatra", "venus_rashi"), "S1", "a", "straight"),
 ("Karana x Day pillar, S1 (b) i-Box", ("karana", "day_pillar"), "S1", "b", "ibox"),
 ("KP Moon number x Year element, 2+9 (b) Straight", ("kp_moon_number", "year_element"), (1, 8), "b", "straight"),
 ("Tithi x Sun nakshatra, 2+9 (b) Straight", ("tithi", "sun_nakshatra"), (1, 8), "b", "straight"),
 ("KP Asc number x Year pillar, 5+6 (b) i-Box", ("kp_asc_number", "year_pillar"), (4, 5), "b", "ibox"),
 ("Jupiter nakshatra x Mercury combust, S2 (a) i-Box", ("jupiter_nakshatra", "mercury_combust"), "S2", "a", "ibox"),
]
for name, test, kind, v, rule in leads:
    days, sd = per_day(test, kind, v)
    h, e = sd[rule][0][:, -1].astype(float), sd[rule][1][:, -1]
    y = yr[days]
    up, tot = 0, 0; cells = []
    for Y in range(2012, 2027):
        m = y == Y
        if e[m].sum() == 0: continue
        tot += 1; up += h[m].sum() > e[m].sum()
        cells.append(f"{Y % 100:02d}:{h[m].sum() / e[m].sum():.2f}")
    a = y >= 2012; b = (y >= 2019)
    print(f"{name}\n   2012-26 x{h[a].sum() / e[a].sum():.3f} | 2019-26 x{h[b].sum() / e[b].sum():.3f} | years above chance {up}/{tot}\n   " + " ".join(cells))
EOF
```

## 103. 2026-10-19 10:21 — Check Karana x Day pillar consistency against shifted calendars

```bash
python3 - <<'EOF' 2>&1 | grep -v "^computed"
import sys
sys.path.insert(0, "analysis")
import numpy as np
import recurrence_s12 as r, recurrence_s12_k as rk
r.setup(); G = r.G; D = G["D"]
yr = np.array([int(d[:4]) for d in D.dates])

def stats(cells):
    order = np.lexsort((np.arange(len(cells)), cells)); sc = cells[order]
    ng = np.r_[True, sc[1:] != sc[:-1]]; hp = ~ng; days = order[hp]
    C = G["dday"][order[:-1]][hp[1:]]
    sd = rk.score_days(days, r.picks(C, True))
    h, e = sd["ibox"][0][:, -1].astype(float), sd["ibox"][1][:, -1]
    y = yr[days]
    up = sum(h[y == Y].sum() > e[y == Y].sum() for Y in range(2012, 2027))
    a = y >= 2012
    return up, h[a].sum() / e[a].sum()
real = stats(r.cells_of(("karana", "day_pillar")))
print("Karana x Day pillar S1 (b) i-Box: years above chance", real[0], "/15, x%.3f" % real[1])
nop = stats(np.zeros(G["nd"], np.int64))
print("No parameter S1 (b) i-Box (previous draw day):", nop[0], "/15, x%.3f" % nop[1])
rng = np.random.default_rng(3)
sims = [stats(r.cells_of(("karana", "day_pillar"), int(s))) for s in rng.integers(170, G["nd"] - 170, 50)]
ups = np.array([s[0] for s in sims]); rat = np.array([s[1] for s in sims])
print(f"50 shifted calendars: years above mean {ups.mean():.1f}, >=14 in {int((ups >= 14).sum())}/50; ratio mean x{rat.mean():.3f}, >= x{real[1]:.3f} in {int((rat >= real[1]).sum())}/50")
EOF
```

## 104. 2026-10-19 10:21 — Add the consistency result to findings and push

```bash
python3 - <<'EOF'
p = "analysis/FINDINGS.md"
s = open(p).read()
s = s.replace("## Live checks", """## Most consistent lead (picks rebuilt before every draw)

Karana x Day pillar, S1 from the previous same-value day, i-Box: chosen among the
top 5 of its column on 1985-2011, then above chance in 14 of 15 years 2012-2026
(x1.04 overall, x1.035 in 2019-2026). None of 50 shifted calendars got 14 years
(their average is 7.7), and the same picks without a parameter got 6 of 15 (x0.995).
Allowing for the ~60 picks checked forward, the chance of this by luck is about 3%.
The gain is small: as i-Box it would return about 67% of stakes instead of about 64%.

## Live checks""", 1)
open(p, "w").write(s)
EOF
git add analysis/FINDINGS.md && git commit -qm "Findings: most consistent lead under per-draw updating

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q origin claude/4d-results-scraper-9ptbd5 && git status -sb | head -1
```

## 105. 2026-10-19 10:24 — Score all leads on the last 3 draws with picks rebuilt each time

```bash
python3 - <<'EOF' 2>&1 | grep -v "^computed"
import sys, math
sys.path.insert(0, "analysis")
import numpy as np
import recurrence_s12 as r, recurrence_rankpairs as rp, score_live as sl, update_picks as up
r.setup(); G = r.G; D = G["D"]; up.D = D
rows, _ = sl.load()
BIG = sl.BIG
def perms(n):
    return math.factorial(4) // math.prod(math.factorial(n.count(d)) for d in set(n))
leads = [
 ("Karana x Day pillar, S1 (b) i-Box", ("karana", "day_pillar"), "S1", "b"),
 ("KP Moon number x Year element, 2+9 (b) Straight", ("kp_moon_number", "year_element"), (1, 8), "b"),
 ("Jupiter nakshatra x Mercury combust, S2 (a) i-Box", ("jupiter_nakshatra", "mercury_combust"), "S2", "a"),
 ("Mercury nakshatra x Venus rashi, S1 (a) Straight", ("mercury_nakshatra", "venus_rashi"), "S1", "a"),
 ("Tithi x Sun nakshatra, 2+9 (b) Straight", ("tithi", "sun_nakshatra"), (1, 8), "b"),
 ("KP Asc number x Year pillar, 5+6 (b) i-Box", ("kp_asc_number", "year_pillar"), (4, 5), "b"),
]
def picks(t, test, kind, v):
    cells = r.cells_of(test)
    e = np.flatnonzero((cells == cells[t]) & (np.arange(G["nd"]) < t))
    src = e if v == "a" else e[-1:]
    C = G["dday"][src].sum(0, keepdims=True)
    if kind == "S1": P = r.picks(C, True)
    elif kind == "S2": P = r.picks(C, False)
    else: P = rp.pair_picks(np.argsort(-C, axis=2, kind="stable"), kind)
    return [f"{n:04d}" for n in P[0]]
def score(byop, win):
    s, b, sp, bp = [], [], 0, 0.0
    for op, nums in byop.items():
        for x in nums:
            if x in win[op]: s.append(f"{x} {op} {win[op][x]}"); sp += BIG[win[op][x]]
            for m, p in win[op].items():
                if sorted(m) == sorted(x): b.append(f"{x}->{m} {op} {p}"); bp += BIG[p] / perms(x)
    return s, sp, b, bp
dates = ["2026-10-14", "2026-10-17", "2026-10-18"]
tot = {}
for d in dates:
    t = D.dates.index(d)
    win = {op: {x["4d_number"]: x["prize"] for x in rows[op] if x["date"] == d} for op in sl.OPS}
    sets = {n: {op: picks(t, test, k, v) for op in sl.OPS} for n, test, k, v in leads}
    mars, _ = up.picks_for(d, d)
    sets["S1 Mars triple (per operator)"] = {op: [f"{n:04d}" for n in v] for op, v in mars["S1_marsnak_marsrashi_mercombust"].items()}
    sets["S2 Mars triple (per operator)"] = {op: [f"{n:04d}" for n in v] for op, v in mars["S2_marsnak_marsrashi_mercombust"].items()}
    sets["Cold number"] = sl.cold_numbers(rows, d)
    sets["1024 Magnum"] = {"Magnum": ["1024"]}
    print(f"\n=== {d} ===")
    for n, byop in sets.items():
        s, sp, b, bp = score(byop, win)
        k = sum(len(v) for v in byop.values())
        T = tot.setdefault(n, [0, 0, 0, 0.0, 0]); T[0] += len(s); T[1] += sp; T[2] += len(b); T[3] += bp; T[4] += k
        print(f"{n}|{k}|{len(s)}|{'; '.join(s) or '-'}|{sp}|{len(b)}|{'; '.join(b) or '-'}|{bp:.2f}")
print("\n=== totals over 3 draws ===")
for n, (s, sp, b, bp, k) in tot.items():
    print(f"{n}|stake {k}|straight {s} RM{sp}|ibox {b} RM{bp:.2f}")
EOF
```

## 106. 2026-10-19 10:25 — Check how the Mars triple lead was selected

```bash
python3 - <<'EOF'
import json
d = json.load(open("analysis/s12_combos_results.json"))
for k in ("most_hits_last5_after_the_fact",):
    for x in d.get(k, [])[:10]: print(x)
for k, v in d.items():
    if isinstance(v, dict) and "best" in v:
        for b in v["best"]:
            if "mars_nakshatra" in b["formula"] and "mars_rashi" in b["formula"]:
                print(k, {a: (round(c, 2) if isinstance(c, float) else c) for a, c in b.items()})
EOF
grep -n "marsnak\|mars_nakshatra x mars_rashi" docs/conversation.md | head -10
```

## 107. 2026-10-20 00:08 — Write navamsa family script and sanity-check it

```bash
cat > analysis/navamsa_family.py <<'EOF'
#!/usr/bin/env python3
"""D9 navamsa family: does the navamsa (alone or paired) play a role?

New parameters at the 19:00 MYT draw (sidereal, Lahiri, from the positions in
continuous_astro_positions.npz):
  <body>_navamsa     D9 sign of Sun, Moon, Mars, Mercury, Jupiter, Venus,
                     Saturn, Rahu, Lagna (floor(longitude * 9 / 30) mod 12)
  <body>_vargottama  same sign in D1 (rashi) and D9 (navamsa)
Tests (1,557): the 18 alone, all 153 pairs within the family, and each with the
77 other Vedic / Chinese parameters. The analyses done before, on this family:
  A  digit mix given the value(s): learned before 2012, log-likelihood gain on
     2012-2026 (as continuous_astro.py)
  B  same 4D number again when the value(s) recur: Straight / Reverse / i-Box,
     (a) any later / (b) next same-value day (as recurrence_perm.py)
  C  digit-position picks from earlier same-value days, (a) all / (b) previous
     day: S1 (2 hottest), S2 (2 coldest), S3 and rank pairs 1+10, 2+9, 3+8,
     4+7, 5+6; Straight / Reverse / i-Box (as recurrence_s12.py, _s3, _rankpairs)
  D  whole-number hot / cold from all earlier same-value days (as
     whole_number_test.py)
Each is compared with the same scan on circularly shifted parameter calendars;
C and D also with the forward check (top 5 chosen before 2012, scored 2012-2026).

Run from the repo root:  python3 analysis/navamsa_family.py [n_shifts]
"""

import itertools
import json
import math
import multiprocessing as mp
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am  # noqa: E402
import recurrence_perm as rperm  # noqa: E402
import recurrence_rankpairs as rpair  # noqa: E402
import recurrence_s12 as r  # noqa: E402
import recurrence_s12_k as rk  # noqa: E402
import whole_number_test as wn  # noqa: E402

BODIES = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Lagna"]
RASHIS = ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya", "Tula", "Vrischika",
          "Dhanu", "Makara", "Kumbha", "Meena"]
NAVF = [f"{b.lower()}_navamsa" for b in BODIES] + [f"{b.lower()}_vargottama" for b in BODIES]
SPLIT = 2012
RULES = ("straight", "reverse", "ibox")
PICKERS = ["S1", "S2", (0, 9), (1, 8), (2, 7), (3, 6), (4, 5)]
C_COLS = [(p, v, rule) for p in PICKERS for v in "ab" for rule in RULES]


def pname(p):
    return p if isinstance(p, str) else f"{p[0] + 1}+{p[1] + 1}"


def nav_codes(dates):
    z = np.load(os.path.join(am.ROOT, "analysis", "continuous_astro_positions.npz"), allow_pickle=True)
    assert list(z["dates"]) == list(dates), "positions cache is out of date: run continuous_astro.py"
    lon = z["lon"]                                                        # (dates, 9) in BODIES order
    codes, labels = {}, {}
    for j, b in enumerate(BODIES):
        nav = (np.floor(lon[:, j] * 9 / 30) % 12).astype(int)
        rash = (lon[:, j] // 30).astype(int)
        codes[f"{b.lower()}_navamsa"] = nav
        labels[f"{b.lower()}_navamsa"] = RASHIS
        codes[f"{b.lower()}_vargottama"] = (nav == rash).astype(int)
        labels[f"{b.lower()}_vargottama"] = ["no", "yes"]
    return codes, labels


def inject(D, codes, labels):
    for k in codes:
        D.codes[k] = codes[k]
        D.labels[k] = labels[k]


def cells(D, test, shift=0):
    c = np.zeros(len(D.dates), np.int64)
    for f in test:
        c = c * (int(D.codes[f].max()) + 1) + D.codes[f]
    return np.roll(c, shift) if shift else c


# ---------- A: digit mix given the value(s)
def eval_A(cl):
    D = r.G["D"]
    yr = r.G["yr"]
    rd, dig = D.rd, D.rdig
    code = np.unique(cl, return_inverse=True)[1][rd]
    train = yr[rd] < SPLIT
    test = ~train
    base = np.stack([np.bincount(dig[train, p], minlength=10) for p in range(4)]).astype(float)
    base /= base.sum(1, keepdims=True)
    n = int(code.max()) + 1
    cnt = np.zeros((n, 4, 10))
    for p in range(4):
        np.add.at(cnt[:, p], (code[train], dig[train, p]), 1)
    q = (cnt + 500 * base[None]) / (cnt.sum(2, keepdims=True) + 500)
    ct = code[test]
    ll = sum(np.log(q[ct, p, dig[test, p]] / base[p, dig[test, p]]) for p in range(4))
    return np.array([1000 * ll.sum() / (4 * len(ll))])


# ---------- C: digit-position pickers with before / after split
def eval_C(cl):
    G = r.G
    dday = G["dday"]
    order = np.lexsort((np.arange(len(cl)), cl))
    sc = cl[order]
    newgrp = np.r_[True, sc[1:] != sc[:-1]]
    hp = ~newgrp
    days = order[hp]
    late = G["yr"][days] >= SPLIT
    cs = np.cumsum(dday[order], axis=0)
    start = np.maximum.accumulate(np.where(newgrp, np.arange(len(sc)), 0))
    base = np.where((start > 0)[:, None, None], cs[np.maximum(start - 1, 0)], 0)
    src = {"a": (cs - dday[order] - base)[hp], "b": dday[order[:-1]][hp[1:]]}
    ranked = {v: np.argsort(-C, axis=2, kind="stable") for v, C in src.items()}
    res = {}
    for p in PICKERS:
        for v in "ab":
            if p == "S1":
                P = r.picks(src[v], True)
            elif p == "S2":
                P = r.picks(src[v], False)
            else:
                P = rpair.pair_picks(ranked[v], p)
            sd = rk.score_days(days, P)
            for rule in RULES:
                h, e = sd[rule][0][:, -1].astype(float), sd[rule][1][:, -1]
                res[(p, v, rule)] = (h[~late].sum(), e[~late].sum(), h[late].sum(), e[late].sum())
    return np.array([res[c] for c in C_COLS])


def task(args):
    mode, test, shift = args
    if mode == "A":
        return eval_A(cells(r.G["D"], test, shift))
    if mode == "B":
        o = rperm.evaluate(cells(rperm.G["D"], test, shift))
        return np.array([x for t in RULES for x in o[t]])                 # obs_a, exp_a, obs_b, exp_b per rule
    if mode == "C":
        return eval_C(cells(r.G["D"], test, shift))
    return wn.evaluate(cells(r.G["D"], test, shift))


def zz(o, e):
    return (o - e) / np.sqrt(np.maximum(e, 1e-9))


def fwd_stats(A):
    zb, za = zz(A[:, :, 0], A[:, :, 1]), zz(A[:, :, 2], A[:, :, 3])
    zall = zz(A[:, :, 0] + A[:, :, 2], A[:, :, 1] + A[:, :, 3])
    top = np.argsort(-zb, axis=0)[:5]
    return zb, za, zall, top, np.take_along_axis(za, top, 0).mean(0)


def main():
    n_shifts = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    t0 = time.time()
    wn.setup()                                                            # also runs recurrence_s12.setup()
    rperm.setup()
    codes, labels = nav_codes(r.G["D"].dates)
    for D in (r.G["D"], rperm.G["D"]):
        inject(D, codes, labels)
    D = r.G["D"]
    same = np.mean([len(set(zip(D.codes["moon_navamsa"], codes["moon_navamsa"]))) == 12])
    print(f"check: moon_navamsa from positions matches the almanac's moon_navamsa: {bool(same)}")
    other = [f for f in r.FACT if f != "moon_navamsa"]
    tests = [(f,) for f in NAVF] + list(itertools.combinations(NAVF, 2)) + [(a, b) for a in NAVF for b in other]
    names = [" x ".join(t) for t in tests]
    print(f"{len(tests)} tests", flush=True)
    rng = np.random.default_rng(41)
    shifts = [int(s) for s in rng.integers(170, r.G["nd"] - 170, n_shifts)]
    out = {"tests": len(tests), "n_shifts": n_shifts}
    with mp.get_context("fork").Pool(4) as pool:
        def scan(mode, sh):
            return np.array(pool.map(task, [(mode, t, sh) for t in tests], chunksize=8))

        # A
        a_real = scan("A", 0)[:, 0]
        a_null = np.array([scan("A", s)[:, 0] for s in shifts])
        print(f"\nA. digit mix given the value(s), log-likelihood gain on 2012-2026 (milli-nats per digit; 0 = no information)")
        print(f"   tests with gain > 0: {int((a_real > 0).sum())} (shifted calendars {np.mean((a_null > 0).sum(1)):.1f})")
        print(f"   best {a_real.max():+.3f} [{names[int(a_real.argmax())]}] vs shifted best {a_null.max(1).mean():+.3f} "
              f"({int((a_null.max(1) >= a_real.max()).sum())}/{n_shifts} as high); singles: " +
              ", ".join(f"{t[0]} {a_real[i]:+.3f}" for i, t in enumerate(tests[:18])), flush=True)
        out["A"] = {"gain": dict(zip(names, a_real.tolist())), "null_best": a_null.max(1).tolist(),
                    "null_n_pos": (a_null > 0).sum(1).tolist()}

        # B
        b_real = scan("B", 0)
        b_null = [scan("B", s) for s in shifts]
        print(f"\nB. same 4D number when the value(s) recur ({time.time() - t0:.0f}s)")
        out["B"] = {}
        for k, rule in enumerate(RULES):
            for v, (oi, ei) in (("a any later day", (4 * k, 4 * k + 1)), ("b next day", (4 * k + 2, 4 * k + 3))):
                z = zz(b_real[:, oi], b_real[:, ei])
                zn = np.array([zz(x[:, oi], x[:, ei]) for x in b_null])
                q = int(np.argmax(z))
                print(f"   {rule:<9} ({v:<15}) z>2 {int((z > 2).sum()):>3} (shifted {np.mean((zn > 2).sum(1)):.0f}) | best {z[q]:+.2f} "
                      f"[{names[q]}] x{b_real[q, oi] / b_real[q, ei]:.3f} | shifted best {zn.max(1).mean():+.2f} "
                      f"({int((zn.max(1) >= z[q]).sum())}/{n_shifts} as high)", flush=True)
                out["B"][f"{rule} {v}"] = {"z_gt_2": int((z > 2).sum()), "null_z_gt_2": (zn > 2).sum(1).tolist(),
                                          "best": float(z[q]), "best_test": names[q], "null_best": zn.max(1).tolist()}

        # C
        c_real = scan("C", 0)
        c_null = [fwd_stats(scan("C", s)) for s in shifts]
        zb, za, zall, top, fwd = fwd_stats(c_real)
        nf = np.array([x[4] for x in c_null])
        nb = np.array([x[2].max(0) for x in c_null])
        ng = np.array([(x[2] > 2).sum(0) for x in c_null])
        print(f"\nC. digit-position picks ({time.time() - t0:.0f}s): z>2 real (shifted) | best z (shifted, as high) | "
              f"forward real (shifted, as high)")
        out["C"] = []
        for ci, (p, v, rule) in enumerate(C_COLS):
            best = float(zall[:, ci].max())
            print(f"   {pname(p):<5} ({v}) {rule:<9} {int((zall[:, ci] > 2).sum()):>4} ({ng[:, ci].mean():>4.0f}) | {best:+.2f} "
                  f"({nb[:, ci].mean():+.2f}, {int((nb[:, ci] >= best).sum())}/{n_shifts}) | {fwd[ci]:+.2f} "
                  f"({nf[:, ci].mean():+.2f}, {int((nf[:, ci] >= fwd[ci]).sum())}/{n_shifts})")
            out["C"].append({"picks": pname(p), "version": v, "rule": rule, "z_gt_2": int((zall[:, ci] > 2).sum()),
                             "null_z_gt_2": ng[:, ci].tolist(), "best_z": best,
                             "best_test": names[int(np.argmax(zall[:, ci]))], "null_best": nb[:, ci].tolist(),
                             "forward": float(fwd[ci]), "null_forward": nf[:, ci].tolist(),
                             "forward_tests": [{"test": names[q], "z_before": float(zb[q, ci]),
                                                "hits_after": float(c_real[q, ci, 2]), "exp_after": float(c_real[q, ci, 3]),
                                                "z_after": float(za[q, ci])} for q in top[:, ci]]})
        beat = np.array([(nf[:, ci] < fwd[ci]).mean() for ci in range(len(C_COLS))])
        print(f"   forward mean over all {len(C_COLS)} columns: real {fwd.mean():+.3f} vs shifted {nf.mean():+.3f}; "
              f"columns beating every shift: {int((beat == 1).sum())} (about {len(C_COLS) / (n_shifts + 1):.1f} by chance)")
        for ci in np.flatnonzero(beat == 1):
            p, v, rule = C_COLS[ci]
            x = out["C"][ci]["forward_tests"][0]
            print(f"      {pname(p)} ({v}) {rule}: forward {fwd[ci]:+.2f} vs {nf[:, ci].mean():+.2f}; top pick {x['test']} "
                  f"before z {x['z_before']:+.2f} -> after x{x['hits_after'] / x['exp_after']:.3f} (z {x['z_after']:+.2f})")
        sys.stdout.flush()

        # D
        nd_shift = shifts[:max(2, n_shifts // 2)]
        d_real = scan("D", 0)
        d_null = [fwd_stats(scan("D", s)) for s in nd_shift]
        zb, za, zall, top, fwd = fwd_stats(d_real)
        nf = np.array([x[4] for x in d_null])
        print(f"\nD. whole-number hot / cold ({time.time() - t0:.0f}s): forward real (shifted, as high) | best z all years")
        out["D"] = []
        for ci, (s, rule) in enumerate(wn.COLS):
            q = int(np.argmax(zall[:, ci]))
            print(f"   {s:<4} {rule:<9} forward {fwd[ci]:+.2f} ({nf[:, ci].mean():+.2f}, {int((nf[:, ci] >= fwd[ci]).sum())}/{len(nd_shift)}) | "
                  f"best {zall[q, ci]:+.2f} [{names[q]}]")
            out["D"].append({"strategy": s, "rule": rule, "forward": float(fwd[ci]), "null_forward": nf[:, ci].tolist(),
                             "best_z": float(zall[q, ci]), "best_test": names[q]})
    json.dump(out, open(os.path.join(am.ROOT, "analysis", "navamsa_family_results.json"), "w"), indent=1)
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
EOF
python3 - <<'EOF' 2>&1 | grep -v "^computed"
import sys, time
sys.path.insert(0, "analysis")
import numpy as np
import navamsa_family as nf
nf.wn.setup(); nf.rperm.setup()
codes, labels = nf.nav_codes(nf.r.G["D"].dates)
for D in (nf.r.G["D"], nf.rperm.G["D"]): nf.inject(D, codes, labels)
D = nf.r.G["D"]
print("moon navamsa pairs (almanac code, new code):", len(set(zip(D.codes["moon_navamsa"], codes["moon_navamsa"]))))
print({k: np.bincount(v).tolist() for k, v in codes.items() if "vargottama" in k})
for m in "ABCD":
    t = time.time(); x = nf.task((m, ("jupiter_navamsa", "venus_rashi"), 0)); print(m, round(time.time() - t, 2), np.shape(x))
EOF
```

## 108. 2026-10-20 01:28 — Commit navamsa results and update findings

```bash
python3 - <<'EOF'
p = "analysis/FINDINGS.md"
s = open(p).read()
s = s.replace("| Whole-number hot / cold", "| D9 navamsa family: navamsa sign and vargottama of 9 bodies, alone, in pairs and with all other parameters; tests A-D above | `navamsa_family.py` |\n| Whole-number hot / cold", 1)
open(p, "w").write(s)
EOF
git add analysis/navamsa_family_results.json analysis/FINDINGS.md && git commit -qm "Add D9 navamsa family results

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q origin claude/4d-results-scraper-9ptbd5 && git status -sb | head -1
```

## 109. 2026-10-20 05:15 — Refactor navamsa script into a reusable suite

```bash
cd /home/user/4DPrediction && python3 - <<'EOF'
p = "analysis/navamsa_family.py"
s = open(p).read()
a = s.index("def main():")
b = s.index('if __name__ == "__main__":')
new_main = '''def setup_all(extra_codes, extra_labels):
    """Load data for all analyses and add extra parameters to both data copies."""
    wn.setup()                                                            # also runs recurrence_s12.setup()
    rperm.setup()
    for D in (r.G["D"], rperm.G["D"]):
        inject(D, extra_codes, extra_labels)


def run_suite(tests, n_shifts, out_name, seed=41):
    """Analyses A-D on the given tests; prints the summary and writes analysis/<out_name>."""
    t0 = time.time()
    names = [" x ".join(t) for t in tests]
    print(f"{len(tests)} tests", flush=True)
    rng = np.random.default_rng(seed)
    shifts = [int(s) for s in rng.integers(170, r.G["nd"] - 170, n_shifts)]
    out = {"tests": len(tests), "n_shifts": n_shifts}
''' + s[s.index('    with mp.get_context("fork").Pool(4) as pool:\n        def scan'):s.index('    json.dump(out, open(os.path.join(am.ROOT, "analysis", "navamsa_family_results.json")')] + '''    json.dump(out, open(os.path.join(am.ROOT, "analysis", out_name), "w"), indent=1)
    print(f"done in {time.time() - t0:.0f}s")
    return out


def main():
    n_shifts = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    wn.setup()
    codes, labels = nav_codes(r.G["D"].dates)
    rperm.setup()
    for D in (r.G["D"], rperm.G["D"]):
        inject(D, codes, labels)
    D = r.G["D"]
    same = len(set(zip(D.codes["moon_navamsa"], codes["moon_navamsa"]))) == 12
    print(f"check: moon_navamsa from positions matches the almanac's moon_navamsa: {same}")
    other = [f for f in r.FACT if f != "moon_navamsa"]
    tests = [(f,) for f in NAVF] + list(itertools.combinations(NAVF, 2)) + [(a, b) for a in NAVF for b in other]
    run_suite(tests, n_shifts, "navamsa_family_results.json")


'''
s = s[:a] + new_main + s[b:]
open(p, "w").write(s)
EOF
python3 -c "import ast,sys; ast.parse(open('/home/user/4DPrediction/analysis/navamsa_family.py').read()); print('ok')"; grep -n "t0\b\|t0 " /home/user/4DPrediction/analysis/navamsa_family.py | head
```

## 110. 2026-10-20 05:15 — Write divisional charts test and check the sign rules

```bash
cat > analysis/divisional_charts.py <<'EOF'
#!/usr/bin/env python3
"""Other divisional charts (vargas) besides D9, run through the same analyses
A-D as navamsa_family.py.

Varga sign of Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Lagna at
19:00 MYT (sidereal positions from continuous_astro_positions.npz), standard
Parashara rules (sign s = 0 Aries .. 11 Pisces, d = degree in sign):
  D2  Hora           odd signs: 0-15 Leo, 15-30 Cancer; even signs reversed
  D3  Drekkana       s + 4k              (k = 10-degree part)
  D4  Chaturthamsa   s + 3k
  D7  Saptamsa       odd: s + k, even: s + 6 + k
  D10 Dasamsa        odd: s + k, even: s + 8 + k
  D12 Dwadasamsa     s + k
  D16 Shodasamsa     from Aries / Leo / Sagittarius (movable / fixed / dual) + k
  D20 Vimsamsa       from Aries / Sagittarius / Leo + k
  D24 Chaturvimsamsa odd: from Leo, even: from Cancer + k
  D27 Bhamsa         from Aries / Cancer / Libra / Capricorn (fire/earth/air/water) + k
  D30 Trimsamsa      odd: 5 Aries, 5 Aquarius, 8 Sagittarius, 7 Gemini, 5 Libra;
                     even: 5 Taurus, 7 Virgo, 8 Pisces, 5 Capricorn, 5 Scorpio
  D40 Khavedamsa     odd: from Aries, even: from Libra + k
  D45 Akshavedamsa   from Aries / Leo / Sagittarius + k
  D60 Shashtiamsa    s + k
Tests: each of the 126 alone and all 36 pairs within each chart (630 tests).
Note: the Lagna moves about 1 degree every 4 minutes, so its finer charts (D30
and up) are uncertain within the 19:00-19:30 draw window.

Run from the repo root:  python3 analysis/divisional_charts.py [n_shifts]
"""

import itertools
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am  # noqa: E402
import navamsa_family as nf  # noqa: E402

BODIES = nf.BODIES
RASHIS = nf.RASHIS
CHARTS = [2, 3, 4, 7, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]


def varga(lon, n):
    s = (lon // 30).astype(int) % 12
    d = lon % 30
    odd = s % 2 == 0                                                      # Aries, Gemini, ... are odd signs
    k = np.minimum((d * n / 30).astype(int), n - 1)
    mod, elem = s % 3, s % 4
    if n == 2:
        return np.where(odd == (d < 15), 4, 3)                           # Leo or Cancer
    if n == 3:
        return (s + 4 * k) % 12
    if n == 4:
        return (s + 3 * k) % 12
    if n == 7:
        return (s + np.where(odd, 0, 6) + k) % 12
    if n == 10:
        return (s + np.where(odd, 0, 8) + k) % 12
    if n in (12, 60):
        return (s + k) % 12
    if n == 16:
        return (np.array([0, 4, 8])[mod] + k) % 12
    if n == 20:
        return (np.array([0, 8, 4])[mod] + k) % 12
    if n == 24:
        return (np.where(odd, 4, 3) + k) % 12
    if n == 27:
        return (np.array([0, 3, 6, 9])[elem] + k) % 12
    if n == 30:
        odd_e, odd_s = np.array([5, 10, 18, 25, 30]), np.array([0, 10, 8, 2, 6])
        evn_e, evn_s = np.array([5, 12, 20, 25, 30]), np.array([1, 5, 11, 9, 7])
        io = np.searchsorted(odd_e, d, side="right").clip(0, 4)
        ie = np.searchsorted(evn_e, d, side="right").clip(0, 4)
        return np.where(odd, odd_s[io], evn_s[ie])
    if n == 40:
        return (np.where(odd, 0, 6) + k) % 12
    if n == 45:
        return (np.array([0, 4, 8])[mod] + k) % 12
    raise ValueError(n)


def chart_codes(dates):
    z = np.load(os.path.join(am.ROOT, "analysis", "continuous_astro_positions.npz"), allow_pickle=True)
    assert list(z["dates"]) == list(dates), "positions cache is out of date: run continuous_astro.py"
    lon = z["lon"]
    codes, labels = {}, {}
    for n in CHARTS:
        for j, b in enumerate(BODIES):
            k = f"{b.lower()}_d{n}"
            codes[k] = varga(lon[:, j], n)
            labels[k] = RASHIS
    return codes, labels


def main():
    n_shifts = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    nf.wn.setup()
    codes, labels = chart_codes(nf.r.G["D"].dates)
    nf.rperm.setup()
    for D in (nf.r.G["D"], nf.rperm.G["D"]):
        nf.inject(D, codes, labels)
    # sanity: D9 rule reproduces the navamsa; D1-equivalent checks
    tests = []
    for n in CHARTS:
        fam = [f"{b.lower()}_d{n}" for b in BODIES]
        tests += [(f,) for f in fam] + list(itertools.combinations(fam, 2))
    out = nf.run_suite(tests, n_shifts, "divisional_charts_results.json", seed=43)
    # per chart: forward mean of C over its own tests is not separable from the column summary,
    # so report each chart's best A gain and best C test
    names = [" x ".join(t) for t in tests]
    print("\nBy chart: best digit-mix gain (A) among its tests")
    for n in CHARTS:
        g = [out["A"]["gain"][nm] for nm in names if f"_d{n}" in nm and all(f"_d{n}" in p for p in nm.split(" x "))]
        print(f"   D{n:<3} best {max(g):+.3f}, mean {np.mean(g):+.3f} ({len(g)} tests)")


if __name__ == "__main__":
    main()
EOF
python3 - <<'EOF'
import sys
sys.path.insert(0, "/home/user/4DPrediction/analysis")
import numpy as np
import divisional_charts as dc
lon = np.array([0.5, 14.9, 15.1, 31.0, 45.0, 59.0, 95.0, 125.0, 200.0, 359.9])
for n in dc.CHARTS: print(n, dc.varga(lon, n).tolist())
EOF
```

## 111. 2026-10-20 05:48 — Recompute per-chart summary, fix script, commit

```bash
python3 - <<'EOF'
import json, re
import numpy as np
g = json.load(open("analysis/divisional_charts_results.json"))["A"]["gain"]
for n in [2, 3, 4, 7, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]:
    v = [x for k, x in g.items() if all(re.fullmatch(rf"\w+_d{n}", p) for p in k.split(" x "))]
    print(f"D{n:<3} best {max(v):+.3f} mean {np.mean(v):+.3f} ({len(v)} tests)")
EOF
python3 - <<'EOF'
p = "/home/user/4DPrediction/analysis/divisional_charts.py"
s = open(p).read()
s = s.replace('''        g = [out["A"]["gain"][nm] for nm in names if f"_d{n}" in nm and all(f"_d{n}" in p for p in nm.split(" x "))]''',
'''        g = [out["A"]["gain"][nm] for nm in names if all(p.endswith(f"_d{n}") for p in nm.split(" x "))]''')
s = s.replace("import itertools\nimport os", "import itertools\nimport os")
open(p, "w").write(s)
EOF
cd /home/user/4DPrediction && python3 - <<'EOF'
p = "analysis/FINDINGS.md"
s = open(p).read()
s = s.replace("| Whole-number hot / cold", "| Other divisional charts D2-D60 (14 charts x 9 bodies), alone and in pairs within each chart; tests A-D | `divisional_charts.py` |\n| Whole-number hot / cold", 1)
open(p, "w").write(s)
EOF
git add analysis/divisional_charts.py analysis/divisional_charts_results.json analysis/FINDINGS.md && git commit -qm "Add divisional charts results; fix per-chart grouping

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q origin claude/4d-results-scraper-9ptbd5 && git status -sb | head -1
```

## 112. 2026-10-21 08:10 — Build and log tonight's picks for all ranked leads

```bash
python3 - <<'EOF' 2>&1 | grep -v "^computed"
import sys, datetime as dt
sys.path.insert(0, "analysis")
import numpy as np
import recurrence_s12 as r, recurrence_rankpairs as rp, astro_model as am, score_live as sl, update_picks as up, vedic, ephemeris as eph
import navamsa_family as nf
r.setup(); G = r.G; D = G["D"]; up.D = D
DATE = "2026-10-21"
# navamsa codes for history + today
codes, labels = nf.nav_codes(D.dates)
nf.inject(D, codes, labels)
jd = eph.julian_day(dt.datetime(2026, 10, 21, 11))
merc_nav_today = int(vedic.sidereal("Mercury", jd) * 9 / 30) % 12

def today_code(f):
    if f == "mercury_navamsa": return merc_nav_today
    ix, c2, ctx = am.date_codes(DATE, D.codes, D.labels, [f])
    return int(c2[f][-1]), ctx[f]

def picks(test, kind, v):
    m = np.ones(G["nd"], bool); vals = []
    for f in test:
        c = today_code(f)
        code = c if isinstance(c, int) else c[0]
        vals.append(f"{f}={nf.RASHIS[code] if f=='mercury_navamsa' else c[1]}")
        m &= D.codes[f] == code
    e = np.flatnonzero(m)
    src = e if v == "a" else e[-1:]
    C = G["dday"][src].sum(0, keepdims=True)
    if kind == "S1": P = r.picks(C, True)
    elif kind == "S2": P = r.picks(C, False)
    else: P = rp.pair_picks(np.argsort(-C, axis=2, kind="stable"), kind)
    info = f"{', '.join(vals)}; " + (f"{len(e)} earlier days" if v == "a" else f"previous day {D.dates[e[-1]]}")
    return sorted(f"{n:04d}" for n in P[0]), info

leads = [
 ("1", "Karana x Day pillar", "S1 (b)", "i-Box", ("karana", "day_pillar"), "S1", "b"),
 ("2", "KP Moon number x Year element", "2+9 (b)", "Straight", ("kp_moon_number", "year_element"), (1, 8), "b"),
 ("3", "Tithi x Sun nakshatra", "2+9 (b)", "Straight", ("tithi", "sun_nakshatra"), (1, 8), "b"),
 ("4", "KP Asc number x Year pillar", "5+6 (b)", "i-Box", ("kp_asc_number", "year_pillar"), (4, 5), "b"),
 ("5", "Mercury nakshatra x Venus rashi", "S1 (a)", "Straight", ("mercury_nakshatra", "venus_rashi"), "S1", "a"),
 ("6", "Jupiter nakshatra x Mercury combust", "S2 (a)", "i-Box", ("jupiter_nakshatra", "mercury_combust"), "S2", "a"),
 ("8", "Mercury navamsa x Venus rashi", "S2 (b)", "Straight", ("mercury_navamsa", "venus_rashi"), "S2", "b"),
]
import csv, collections
rows = []
for rank, name, kind_s, bet, test, kind, v in leads:
    nums, info = picks(test, kind, v)
    print(f"{rank}|{name}|{kind_s}|{bet}|{info}|{' '.join(nums)}")
    rows.append((f"lead{rank}_{'_'.join(test)}_{kind_s.replace(' ', '').replace('(', '').replace(')', '')}", "All", nums))
mars, info = up.picks_for(DATE, DATE)
for s in ("S2", "S1"):
    k = f"{s}_marsnak_marsrashi_mercombust"
    print(f"7|{s} Mars triple|{info[k]}")
    for op, v in mars[k].items():
        print(f"   {op}: {' '.join(f'{n:04d}' for n in v)}")
rs, _ = sl.load()
print("cold:", {o: v[0] for o, v in sl.cold_numbers(rs, DATE).items()})
T = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
with open("analysis/forward_log.csv", "a") as fh:
    for var, op, nums in rows:
        for k, n in enumerate(nums, 1):
            fh.write(f"{T},{DATE},{var},{op},{k},{n}\n")
print("logged", len(rows), "lead pick sets at", T, "UTC")
EOF
```

## 113. 2026-10-21 08:11 — Build and log tonight's picks, skipping leads without history

```bash
python3 - <<'EOF' 2>&1 | grep -v "^computed"
import sys, datetime as dt
sys.path.insert(0, "analysis")
import numpy as np
import recurrence_s12 as r, recurrence_rankpairs as rp, astro_model as am, score_live as sl, update_picks as up, vedic, ephemeris as eph
import navamsa_family as nf
r.setup(); G = r.G; D = G["D"]; up.D = D
DATE = "2026-10-21"
codes, labels = nf.nav_codes(D.dates)
nf.inject(D, codes, labels)
jd = eph.julian_day(dt.datetime(2026, 10, 21, 11))
merc_nav_today = int(vedic.sidereal("Mercury", jd) * 9 / 30) % 12
def today_code(f):
    if f == "mercury_navamsa": return merc_nav_today, nf.RASHIS[merc_nav_today]
    ix, c2, ctx = am.date_codes(DATE, D.codes, D.labels, [f])
    return int(c2[f][-1]), ctx[f]
def picks(test, kind, v):
    m = np.ones(G["nd"], bool); vals = []
    for f in test:
        code, lab = today_code(f); vals.append(f"{f}={lab}"); m &= D.codes[f] == code
    e = np.flatnonzero(m)
    if len(e) == 0: return None, ", ".join(vals) + "; no earlier draw day with these values"
    src = e if v == "a" else e[-1:]
    C = G["dday"][src].sum(0, keepdims=True)
    if kind == "S1": P = r.picks(C, True)
    elif kind == "S2": P = r.picks(C, False)
    else: P = rp.pair_picks(np.argsort(-C, axis=2, kind="stable"), kind)
    return sorted(f"{n:04d}" for n in P[0]), ", ".join(vals) + "; " + (f"{len(e)} earlier days" if v == "a" else f"previous day {D.dates[e[-1]]}")
leads = [
 ("1", "Karana x Day pillar", "S1 (b)", "i-Box", ("karana", "day_pillar"), "S1", "b"),
 ("2", "KP Moon number x Year element", "2+9 (b)", "Straight", ("kp_moon_number", "year_element"), (1, 8), "b"),
 ("3", "Tithi x Sun nakshatra", "2+9 (b)", "Straight", ("tithi", "sun_nakshatra"), (1, 8), "b"),
 ("4", "KP Asc number x Year pillar", "5+6 (b)", "i-Box", ("kp_asc_number", "year_pillar"), (4, 5), "b"),
 ("5", "Mercury nakshatra x Venus rashi", "S1 (a)", "Straight", ("mercury_nakshatra", "venus_rashi"), "S1", "a"),
 ("6", "Jupiter nakshatra x Mercury combust", "S2 (a)", "i-Box", ("jupiter_nakshatra", "mercury_combust"), "S2", "a"),
 ("8", "Mercury navamsa x Venus rashi", "S2 (b)", "Straight", ("mercury_navamsa", "venus_rashi"), "S2", "b"),
]
rows = []
for rank, name, kind_s, bet, test, kind, v in leads:
    nums, info = picks(test, kind, v)
    print(f"{rank}|{name}|{kind_s}|{bet}|{info}|{' '.join(nums) if nums else '-'}")
    if nums: rows.append((f"lead{rank}_{'_'.join(test)}_{kind_s.replace(' ', '').replace('(', '').replace(')', '')}", "All", nums))
mars, info = up.picks_for(DATE, DATE)
for s in ("S2", "S1"):
    k = f"{s}_marsnak_marsrashi_mercombust"
    print(f"7|{s} Mars triple|{info[k]}")
    for op, v in mars[k].items(): print(f"   {op}: {' '.join(f'{n:04d}' for n in v)}")
rs, _ = sl.load()
print("cold:", {o: v[0] for o, v in sl.cold_numbers(rs, DATE).items()})
T = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
with open("analysis/forward_log.csv", "a") as fh:
    for var, op, nums in rows:
        for k, n in enumerate(nums, 1): fh.write(f"{T},{DATE},{var},{op},{k},{n}\n")
print("logged", len(rows), "pick sets at", T, "UTC")
EOF
```

## 114. 2026-10-21 11:47 — Add 21 Oct results and refresh planet positions

```bash
cd /home/user/4DPrediction && python3 - <<'EOF'
import csv
R = {
 "Magnum": ("magnum.csv", ["8450", "6537", "8694"], "9268 8895 4036 6414 1134 8247 7901 9821 1580 1679", "8624 9694 8518 0876 4856 4613 7611 6925 2338 8273"),
 "Sports Toto": ("sportstoto.csv", ["5915", "4831", "4246"], "2268 3947 6422 7634 8115 2187 5458 4409 8760 8606", "3334 2149 6677 5627 4689 8705 0963 6181 2926 9518"),
 "Da Ma Cai": ("damacai.csv", ["3145", "4268", "4566"], "9876 7703 2252 2007 5891 7332 1781 8089 0758 1659", "6999 7189 8782 8055 3514 1088 0602 8667 0514 9190"),
}
for op, (fn, top, sp, co) in R.items():
    path = f"data/{fn}"
    if any(r["date"] == "2026-10-21" for r in csv.DictReader(open(path))):
        print(op, "already present"); continue
    with open(path, "a", newline="") as fh:
        w = csv.writer(fh)
        for prize, n in zip(("1st", "2nd", "3rd"), top): w.writerow(["2026-10-21", "Wed", op, prize, n])
        for n in sp.split(): w.writerow(["2026-10-21", "Wed", op, "Special", n])
        for n in co.split(): w.writerow(["2026-10-21", "Wed", op, "Consolation", n])
    print(op, "added")
EOF
python3 analysis/continuous_astro.py > /dev/null 2>&1; python3 -c "
import numpy as np; z=np.load('/home/user/4DPrediction/analysis/continuous_astro_positions.npz', allow_pickle=True); print(len(z['dates']), z['dates'][-1])"
```

## 115. 2026-10-21 11:53 — Commit results, scorer and findings update

```bash
python3 - <<'EOF'
p = "analysis/FINDINGS.md"
s = open(p).read()
add = """| 21 Oct 2026 | 5. Mercury nakshatra x Venus rashi S1 (logged before the draw) | **6537 Magnum 2nd prize (Straight, RM1,000 on RM48)** |
| 21 Oct 2026 | 1. Karana x Day pillar S1 i-Box | 0 straight; i-Box 4036 Magnum Special, 4409 Toto Special, 4246 Toto 3rd |
| 21 Oct 2026 | 6. Jupiter nakshatra x Mercury combust S2 i-Box | i-Box 5840 -> 8450 Magnum 1st |
| 21 Oct 2026 | Others | 0 straight hits |

Score the ranked leads on any dates with `python3 analysis/score_leads.py DATE [DATE ...]`.

"""
s = s.replace("The 18 Oct picks were made before the 17 Oct draw.", add + "The 18 Oct picks were made before the 17 Oct draw.", 1)
open(p, "w").write(s)
EOF
git add data/*.csv analysis/score_leads.py analysis/FINDINGS.md analysis/continuous_astro_positions.npz analysis/continuous_astro_results.json && git commit -qm "Add 21 Oct 2026 results; score ranked leads on the last 3 draws

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q origin claude/4d-results-scraper-9ptbd5 && git status -sb | head -1
```

## 116. 2026-10-22 04:30 — Write the three methods and sanity-check sample dates

```bash
cat > analysis/chinese_divination.py <<'EOF'
#!/usr/bin/env python3
"""Mei Hua Yi Shu, Da Liu Ren and Tai Yi (day cycles) at the 19:00 MYT draw,
run through analyses A-D (navamsa_family.py) plus a direct digit test.

Mei Hua Yi Shu (time casting, 梅花易数): year-branch number Y (Zi=1 .. Hai=12),
lunar month M, lunar day D, hour-branch number H (19:00 = Xu = 11):
  upper trigram = (Y + M + D) mod 8, lower = (Y + M + D + H) mod 8 (0 -> 8),
  moving line = (Y + M + D + H) mod 6 (0 -> 6); trigram numbers Qian 1, Dui 2,
  Li 3, Zhen 4, Xun 5, Kan 6, Gen 7, Kun 8. Parameters: mh_upper, mh_lower,
  mh_hexagram, mh_moving, mh_changed, mh_mutual, mh_body_use (five-element
  relation of the body trigram to the use trigram, the one holding the moving line).
Da Liu Ren (大六壬) at the Xu hour: monthly general from the Sun's sign
  (after Yushui Hai, after Chunfen Xu, ... after Dahan Zi), heaven plate =
  general over Xu; four lessons from the day stem's lodging branch and the day
  branch; three transmissions by 贼克 > 比用 > 涉害 (simplified: 孟 > 仲 > first
  lesson) > 遥克 > 昴星, with 伏吟 by 刑; middle / last = heaven plate over the
  previous one. Night noble (夜贵) and the 12 generals, clockwise if the noble
  stands over Hai..Chen on the earth plate. Parameters: lr_general (plate
  rotation), lr_initial, lr_middle, lr_last, lr_transmission, lr_general_initial
  (heavenly general on the initial transmission), lr_method, lr_lessons (number
  of 贼 / 克 lessons).
Tai Yi (太乙): conventions differ mainly by the epoch, so the day count's cycles
  are tested directly as categories (any epoch only relabels them): ty_72 (one
  Tai Yi round), ty_24 (palace position, 8 palaces x 3), ty_18 (Wenchang cycle),
  ty_360. The host / guest counts (主算 / 客算) need one fixed convention and
  are not included.
Direct digit test: do the Mei Hua numbers (upper, lower, moving line) and the
  Liu Ren transmission branch numbers (1-12, last digit) appear among that
  draw's winning digits more often than the year's digit mix predicts?

Run from the repo root:  python3 analysis/chinese_divination.py [n_shifts]
"""

import datetime as dt
import itertools
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import almanac as al  # noqa: E402
import astro_model as am  # noqa: E402
import ephemeris as eph  # noqa: E402
import navamsa_family as nf  # noqa: E402

TRI_LINES = {1: (1, 1, 1), 2: (1, 1, 0), 3: (1, 0, 1), 4: (1, 0, 0),      # (bottom, middle, top), 1 = yang
             5: (0, 1, 1), 6: (0, 1, 0), 7: (0, 0, 1), 8: (0, 0, 0)}
LINES_TRI = {v: k for k, v in TRI_LINES.items()}
TRI_ELEM = {1: "Metal", 2: "Metal", 3: "Fire", 4: "Wood", 5: "Wood", 6: "Water", 7: "Earth", 8: "Earth"}
BR_ELEM = ["Water", "Earth", "Wood", "Wood", "Earth", "Fire", "Fire", "Earth", "Metal", "Metal", "Earth", "Water"]
ST_ELEM = al.STEM_ELEMENT
GEN = {"Wood": "Fire", "Fire": "Earth", "Earth": "Metal", "Metal": "Water", "Water": "Wood"}
CTRL = {"Wood": "Earth", "Earth": "Water", "Water": "Fire", "Fire": "Metal", "Metal": "Wood"}
LODGE = [2, 4, 5, 7, 5, 7, 8, 10, 11, 1]                                  # 寄宫 of Jia .. Gui
NIGHT_NOBLE = [7, 8, 9, 9, 7, 8, 7, 2, 3, 3]                               # 夜贵: Jia Wu Geng Wei, Yi Ji Shen, ...
GENERALS = ["Gui Ren", "Teng She", "Zhu Que", "Liu He", "Gou Chen", "Qing Long", "Tian Kong",
            "Bai Hu", "Tai Chang", "Xuan Wu", "Tai Yin", "Tian Hou"]
XING = {0: 3, 3: 0, 2: 5, 5: 8, 8: 2, 1: 10, 10: 7, 7: 1}                   # 刑; 辰午酉亥 punish themselves
HOUR = 10                                                                  # Xu


def relation(a, b):
    """Five-element relation of a to b."""
    if a == b:
        return "same"
    if GEN[a] == b:
        return "generates"
    if GEN[b] == a:
        return "generated by"
    if CTRL[a] == b:
        return "controls"
    return "controlled by"


def mei_hua(year_branch, lm, ld):
    Y, H = year_branch + 1, HOUR + 1
    s = Y + lm + ld
    up = s % 8 or 8
    lo = (s + H) % 8 or 8
    mv = (s + H) % 6 or 6
    lines = list(TRI_LINES[lo]) + list(TRI_LINES[up])
    ch = lines.copy()
    ch[mv - 1] ^= 1
    mutual_lo, mutual_up = LINES_TRI[tuple(lines[1:4])], LINES_TRI[tuple(lines[2:5])]
    body, use = (lo, up) if mv > 3 else (up, lo)
    return {"mh_upper": up, "mh_lower": lo, "mh_hexagram": f"{up}/{lo}", "mh_moving": mv,
            "mh_changed": f"{LINES_TRI[tuple(ch[3:])]}/{LINES_TRI[tuple(ch[:3])]}",
            "mh_mutual": f"{mutual_up}/{mutual_lo}", "mh_body_use": relation(TRI_ELEM[body], TRI_ELEM[use])}


def liu_ren(d_stem, d_branch, sun_trop):
    g = (11 - int(((sun_trop - 330) % 360) // 30)) % 12                    # monthly general
    off = (g - HOUR) % 12
    heaven = lambda b: (b + off) % 12                                      # noqa: E731
    lodge = LODGE[d_stem]
    u1 = heaven(lodge)
    u2 = heaven(u1)
    u3 = heaven(d_branch)
    u4 = heaven(u3)
    lessons = [(ST_ELEM[d_stem], u1), (BR_ELEM[u1], u2), (BR_ELEM[d_branch], u3), (BR_ELEM[u3], u4)]
    stem_yang = d_stem % 2 == 0
    zei = [u for lo, u in lessons if CTRL[lo] == BR_ELEM[u]]               # lower controls upper
    ke = [u for lo, u in lessons if CTRL[BR_ELEM[u]] == lo]               # upper controls lower

    def pick(cands):
        cands = list(dict.fromkeys(cands))
        if len(cands) == 1:
            return cands[0], ""
        same = [c for c in cands if (c % 2 == 0) == stem_yang]
        if len(same) == 1:
            return same[0], "bi yong"
        pool = same or cands
        for group in ((2, 5, 8, 11), (0, 3, 6, 9)):
            g2 = [c for c in pool if c in group]
            if g2:
                return g2[0], "she hai"
        return pool[0], "she hai"

    if off == 0:                                                           # 伏吟
        init = lodge if stem_yang else d_branch
        mid = XING.get(init, (init + 6) % 12)
        last = XING.get(mid, (mid + 6) % 12)
        method = "fu yin"
    else:
        if zei or ke:
            init, sub = pick(zei if zei else ke)
            method = ("zei" if zei else "ke") + (" " + sub if sub else "")
        else:
            far = [u for _, u in lessons[1:] if CTRL[BR_ELEM[u]] == ST_ELEM[d_stem]] or \
                  [u for _, u in lessons[1:] if CTRL[ST_ELEM[d_stem]] == BR_ELEM[u]]
            if far:
                init, sub = pick(far)
                method = "yao ke"
            else:                                                          # 昴星
                init = heaven(9) if stem_yang else [b for b in range(12) if heaven(b) == 9][0]
                method = "mao xing"
        mid, last = heaven(init), heaven(heaven(init))
        if method == "mao xing":
            mid, last = (u3, u1) if stem_yang else (u1, u3)
    noble_h = NIGHT_NOBLE[d_stem]                                          # noble on the heaven plate
    noble_e = (noble_h - off) % 12                                         # earth branch under it
    step = 1 if noble_e in (11, 0, 1, 2, 3, 4) else -1
    gen_of = {(noble_h + step * k) % 12: GENERALS[k] for k in range(12)}
    return {"lr_general": g, "lr_initial": init, "lr_middle": mid, "lr_last": last,
            "lr_transmission": f"{init}-{mid}-{last}", "lr_general_initial": gen_of[init],
            "lr_method": method, "lr_lessons": f"{len(zei)}z{len(ke)}k"}


def compute(dates):
    rows = []
    for d in dates:
        day = dt.date.fromisoformat(d)
        t = dt.datetime.combine(day, dt.time(11))
        sun = eph.sun_longitude(eph.julian_day(t))
        cny = eph.chinese_new_year(day.year)
        ly = day.year if day >= cny else day.year - 1
        lm, ld, _ = eph.lunar_date(day)
        d_ix = (al.jdn(day) - 11) % 60
        n = al.jdn(day)
        x = {}
        x.update(mei_hua((ly - 4) % 12, lm, ld))
        x.update(liu_ren(d_ix % 10, d_ix % 12, sun))
        x.update({"ty_72": n % 72, "ty_24": n % 24, "ty_18": n % 18, "ty_360": n % 360})
        rows.append(x)
    codes, labels = {}, {}
    for k in rows[0]:
        vals = [r[k] for r in rows]
        labs = sorted(set(vals), key=str)
        idx = {v: i for i, v in enumerate(labs)}
        codes[k] = np.array([idx[v] for v in vals])
        labels[k] = [str(v) for v in labs]
    return codes, labels, rows


def digit_test(rows, D, shifts):
    """Share of winning digits equal to the method's numbers vs the year digit mix."""
    yr = np.array([int(d[:4]) for d in D.dates])
    dig = D.rdig
    sets = {"Mei Hua upper/lower/moving": [{r["mh_upper"] % 10, r["mh_lower"] % 10, r["mh_moving"] % 10} for r in rows],
            "Liu Ren transmissions (branch no. 1-12)": [{(r["lr_initial"] + 1) % 10, (r["lr_middle"] + 1) % 10,
                                                         (r["lr_last"] + 1) % 10} for r in rows]}
    q = np.zeros((yr.max() - yr.min() + 1, 10))
    np.add.at(q, (yr[D.rd] - yr.min())[:, None].repeat(4, 1), dig)
    q /= q.sum(1, keepdims=True)
    out = {}
    for name, S in sets.items():
        M = np.zeros((len(D.dates), 10), bool)
        for i, s in enumerate(S):
            M[i, list(s)] = True

        def stat(Mx):
            hit = Mx[D.rd[:, None], dig].sum()
            exp = (Mx[D.rd] * q[yr[D.rd] - yr.min()]).sum() * 4
            return hit, exp, (hit - exp) / math.sqrt(exp)
        h, e, z = stat(M)
        zn = np.array([stat(np.roll(M, s, axis=0))[2] for s in shifts])
        print(f"   {name:<42} {h:.0f} digits vs {e:.0f} expected (x{h / e:.4f}, z {z:+.2f}); "
              f"shifted z {zn.mean():+.2f} +/- {zn.std():.2f}, {int((zn >= z).sum())}/{len(zn)} as high")
        out[name] = {"hits": float(h), "expected": float(e), "z": float(z), "null_z": zn.tolist()}
    return out


def main():
    n_shifts = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    nf.wn.setup()
    D = nf.r.G["D"]
    codes, labels, rows = compute(D.dates)
    nf.rperm.setup()
    for DD in (D, nf.rperm.G["D"]):
        nf.inject(DD, codes, labels)
    ex = dict(zip(D.dates, rows))["2026-10-21"]
    print("21 Oct 2026:", ex)
    print({k: len(v) for k, v in labels.items()})
    NEW = list(codes)
    tests = [(f,) for f in NEW] + list(itertools.combinations(NEW, 2)) + [(a, b) for a in NEW for b in nf.r.FACT]
    rng = np.random.default_rng(47)
    shifts = [int(s) for s in rng.integers(170, nf.r.G["nd"] - 170, 30)]
    print("\nDirect digit test (30 shifted calendars):")
    dt_out = digit_test(rows, D, shifts)
    out = nf.run_suite(tests, n_shifts, "chinese_divination_results.json", seed=47)
    out["digit_test"] = dt_out
    json.dump(out, open(os.path.join(am.ROOT, "analysis", "chinese_divination_results.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
EOF
python3 - <<'EOF'
import sys
sys.path.insert(0, "/home/user/4DPrediction/analysis")
import chinese_divination as cd
print(cd.mei_hua(6, 9, 12))   # 2026-10-21: Bing Wu year, 9th month day 12
print(cd.liu_ren(4, 4, 208.0))  # Wu Chen day, Sun 208 deg
codes, labels, rows = cd.compute(["2026-10-17", "2026-10-18", "2026-10-21", "2026-03-25"])
for r in rows: print(r)
EOF
```

## 117. 2026-10-22 04:32 — Fix the digit test and check it runs

```bash
python3 - <<'EOF'
p = "analysis/chinese_divination.py"
s = open(p).read()
s = s.replace("    np.add.at(q, (yr[D.rd] - yr.min())[:, None].repeat(4, 1), dig)",
              "    np.add.at(q, (np.repeat(yr[D.rd] - yr.min(), 4), dig.ravel()), 1)")
s = s.replace("""  mh_hexagram, mh_moving, mh_changed, mh_mutual, mh_body_use (five-element""",
"""  mh_hexagram, mh_moving, mh_changed, mh_mutual, mh_body_use (five-element""")
s = s.replace("  relation of the body trigram to the use trigram, the one holding the moving line).",
"  relation of the body trigram to the use trigram, the one holding the moving line).\n  With the hour fixed at Xu, lower = upper + 3 (mod 8), so only 8 hexagrams occur.")
open(p, "w").write(s)
EOF
python3 - <<'EOF' 2>&1 | grep -v "^computed"
import sys
sys.path.insert(0, "/home/user/4DPrediction/analysis")
import numpy as np, chinese_divination as cd, digit_models as dm
D = dm.Data()
codes, labels, rows = cd.compute(D.dates)
cd.digit_test(rows, D, [500, 1000, 2000])
EOF
```

## 118. 2026-10-22 05:15 — Guard empty case; begin adding mode selection

```bash
python3 - <<'EOF'
p = "analysis/whole_number_test.py"
s = open(p).read()
s = s.replace("    days = np.array(days)\n    late = G[\"yr\"][days] >= SPLIT",
"    if not days:                                             # no value ever repeats\n        return np.zeros((len(COLS), 4))\n    days = np.array(days, dtype=int)\n    late = G[\"yr\"][days] >= SPLIT")
open(p, "w").write(s)
p = "analysis/navamsa_family.py"
s = open(p).read()
s = s.replace("def run_suite(tests, n_shifts, out_name, seed=41):", "def run_suite(tests, n_shifts, out_name, seed=41, modes=\"ABCD\"):")
for m, start in (("A", "        # A\n"), ("B", "        # B\n"), ("C", "        # C\n"), ("D", "        # D\n")):
    assert start in s
s = s.replace("        # A\n", "        if \"A\" in modes:\n            pass\n        # A\n")
open(p, "w").write(s)
EOF
sed -n 176,250p analysis/navamsa_family.py | head -5; grep -n "        # [ABCD]$\|if \"A\" in modes" analysis/navamsa_family.py
```

## 119. 2026-10-22 05:15 — Add a D-only run, save A-C output, launch D

```bash
python3 - <<'EOF'
p = "analysis/navamsa_family.py"
s = open(p).read()
s = s.replace("        if \"A\" in modes:\n            pass\n        # A\n", "        # A\n")
s = s.replace("def run_suite(tests, n_shifts, out_name, seed=41, modes=\"ABCD\"):", "def run_suite(tests, n_shifts, out_name, seed=41):")
open(p, "w").write(s)
p = "analysis/chinese_divination.py"
s = open(p).read()
s = s.replace('''Run from the repo root:  python3 analysis/chinese_divination.py [n_shifts]''',
'''Run from the repo root:  python3 analysis/chinese_divination.py [n_shifts]
                         python3 analysis/chinese_divination.py --only-D [n_shifts]   (whole-number part only)''')
s = s.replace('''def main():
    n_shifts = int(sys.argv[1]) if len(sys.argv) > 1 else 8''', '''def only_d(tests, n_shifts):
    import multiprocessing as mp
    names = [" x ".join(t) for t in tests]
    rng = np.random.default_rng(47)
    shifts = [int(s) for s in rng.integers(170, nf.r.G["nd"] - 170, n_shifts)]
    with mp.get_context("fork").Pool(4) as pool:
        scan = lambda sh: np.array(pool.map(nf.task, [("D", t, sh) for t in tests], chunksize=8))  # noqa: E731
        real = scan(0)
        null = [nf.fwd_stats(scan(s)) for s in shifts]
    zb, za, zall, top, fwd = nf.fwd_stats(real)
    nfw = np.array([x[4] for x in null])
    print("D. whole-number hot / cold: forward real (shifted, as high) | best z all years")
    out = []
    for ci, (s, rule) in enumerate(nf.wn.COLS):
        q = int(np.argmax(zall[:, ci]))
        print(f"   {s:<4} {rule:<9} forward {fwd[ci]:+.2f} ({nfw[:, ci].mean():+.2f}, {int((nfw[:, ci] >= fwd[ci]).sum())}/{n_shifts}) | "
              f"best {zall[q, ci]:+.2f} [{names[q]}]")
        out.append({"strategy": s, "rule": rule, "forward": float(fwd[ci]), "null_forward": nfw[:, ci].tolist(),
                    "best_z": float(zall[q, ci]), "best_test": names[q]})
    return out


def main():
    only = "--only-D" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    n_shifts = int(args[0]) if args else 8''')
s = s.replace('''    rng = np.random.default_rng(47)
    shifts = [int(s) for s in rng.integers(170, nf.r.G["nd"] - 170, 30)]''', '''    if only:
        path = os.path.join(am.ROOT, "analysis", "chinese_divination_results.json")
        out = json.load(open(path)) if os.path.exists(path) else {}
        out["D"] = only_d(tests, n_shifts)
        json.dump(out, open(path, "w"), indent=1)
        return
    rng = np.random.default_rng(47)
    shifts = [int(s) for s in rng.integers(170, nf.r.G["nd"] - 170, 30)]''')
open(p, "w").write(s)
EOF
python3 -c "import ast; [ast.parse(open(f).read()) for f in ['/home/user/4DPrediction/analysis/chinese_divination.py','/home/user/4DPrediction/analysis/navamsa_family.py','/home/user/4DPrediction/analysis/whole_number_test.py']]; print('ok')"
cd /home/user/4DPrediction && python3 - <<'EOF'
# save the A-C output from the log as the results file to start
import json, re
txt = open("/tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/tasks/btpxlv9m2.output").read()
txt = txt.split("multiprocessing.pool.RemoteTraceback")[0]
json.dump({"log_A_to_C": txt}, open("analysis/chinese_divination_results.json", "w"), indent=1)
print(len(txt))
EOF
L=/tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad/div3d.log; setsid nohup bash -c "python3 analysis/chinese_divination.py --only-D 4 > $L 2>&1; echo exit \$? >> $L" > /dev/null 2>&1 < /dev/null & sleep 1; echo started
```

## 120. 2026-10-22 05:43 — Read D results, update findings, commit

```bash
cat /tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/tasks/bro048f5o.output | cut -c1-300; cd /home/user/4DPrediction && python3 - <<'EOF'
p = "analysis/FINDINGS.md"
s = open(p).read()
s = s.replace("| Whole-number hot / cold", "| Mei Hua Yi Shu (time casting), Da Liu Ren (7 pm plate, transmissions, generals), Tai Yi day cycles (72/24/18/360); tests A-D plus direct number test | `chinese_divination.py` |\n| Whole-number hot / cold", 1)
open(p, "w").write(s)
EOF
git add analysis/chinese_divination_results.json analysis/FINDINGS.md && git commit -qm "Add whole-number results for Chinese divination methods; list in findings

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q origin claude/4d-results-scraper-9ptbd5 && git status -sb | head -1
```

## 121. 2026-10-22 08:23 — Fix aspect names and baseline pool; rerun

```bash
python3 - <<'EOF'
p = "analysis/formula_list_test.py"
s = open(p).read()
s = s.replace('''        add(f"aspect_{a.lower()}_{b.lower()}", aspect(lon[:, COL[a]], lon[:, COL[b]]))''',
'''        add(f"aspect_{a.lower()}_{b.lower()}", aspect(lon[:, COL[a]], lon[:, COL[b]]))
        codes[f"aspect_{b.lower()}_{a.lower()}"] = codes[f"aspect_{a.lower()}_{b.lower()}"]   # either order
        labels[f"aspect_{b.lower()}_{a.lower()}"] = labels[f"aspect_{a.lower()}_{b.lower()}"]''')
s = s.replace('''    base = list(itertools.combinations(r_fact := nf.r.FACT, 2))
    rand = [base[i] for i in rng.choice(len(base), 500, replace=False)]''',
'''    pool_params = sorted(set(nf.r.FACT) | {p for p in codes if not re.match(r"aspect_(\\w+)_(\\w+)$", p) or
                                           p in {f"aspect_{a.lower()}_{b.lower()}" for a, b in
                                                 itertools.combinations(PLANETS7 + ["Rahu", "Lagna"], 2)}})
    rand = []
    while len(rand) < 500:                                                 # random pairs from the same pool of parameters
        a, b = rng.choice(len(pool_params), 2, replace=False)
        t = (pool_params[a], pool_params[b])
        if t not in rand and t not in formulas:
            rand.append(t)''')
s = s.replace('''    print(f"   500 random pairs: mean z''', '''    print(f"   (random pairs drawn from the same {len(pool_params)} parameters as the list, base and new)")
    print(f"   500 random pairs: mean z''')
open(p, "w").write(s)
EOF
python3 analysis/formula_list_test.py analysis/formula_list.txt 2026-10-17 2026-10-18 2026-10-21 2>&1 | grep -v "^computed" > /tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad/flist.txt; head -12 /tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad/flist.txt; grep -i "venus_jupiter\|mercury_mars\|venus_mars" /tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad/flist.txt
```

## 122. 2026-10-22 08:25 — Summarise recent-draw totals and commit

```bash
python3 - <<'EOF'
import json
d = json.load(open("analysis/formula_list_results.json"))
F = d["formulas"]
st = sum(f["recent"]["staked"] for f in F); sh = sum(f["recent"]["straight_hits"] for f in F); srm = sum(f["recent"]["straight_rm"] for f in F)
ib = sum(f["recent"]["ibox"] for f in F); irm = sum(f["recent"]["ibox_rm"] for f in F)
print(len(F), "formulas; staked", st, "straight hits", sh, "RM", srm, "| ibox", ib, "RM", round(irm))
print("expected straight hits at chance ~", round(st / 48 * 0.11, 1))
top = sorted(F, key=lambda f: -f["recent"]["straight_rm"])[:6]
for f in top: print(f["formula"], f["method"], f["recent"]["straight_hits"], f["recent"]["straight_rm"], "z_after", round(f["z_after"], 2))
EOF
sed -n 13,200p /tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad/flist.txt | grep "RM1000\|RM500"
git add analysis/formula_list_test.py analysis/formula_list.txt analysis/formula_list_results.json && git commit -qm "Test a given formula list against random pairs and recent draws

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q origin claude/4d-results-scraper-9ptbd5 && git status -sb | head -1
```

## 123. 2026-10-22 08:31 — Score the formula list on the last 5 draws, per draw

```bash
python3 - <<'EOF'
p = "analysis/formula_list_test.py"
s = open(p).read()
s = s.replace('''        tot = [0, 0, 0, 0.0, 0]
        for d in dates:''', '''        tot = [0, 0, 0, 0.0, 0]
        per = {}
        for d in dates:''')
s = s.replace('''            s, sp, b, bp = sc.score({op: pk for op in sl.OPS}, win)
            tot[0] += len(s); tot[1] += sp; tot[2] += len(b); tot[3] += bp; tot[4] += 48
        print(f"{' x '.join(f)} |''', '''            s, sp, b, bp = sc.score({op: pk for op in sl.OPS}, win)
            tot[0] += len(s); tot[1] += sp; tot[2] += len(b); tot[3] += bp; tot[4] += 48
            per[d] = {"straight": s, "straight_rm": sp, "ibox": len(b), "ibox_rm": bp}
        print(f"{' x '.join(f)} |''')
s = s.replace('''                               "ibox": tot[2], "ibox_rm": tot[3]}})''', '''                               "ibox": tot[2], "ibox_rm": tot[3]}, "per_draw": per})''')
open(p, "w").write(s)
EOF
python3 analysis/formula_list_test.py analysis/formula_list.txt 2026-10-11 2026-10-14 2026-10-17 2026-10-18 2026-10-21 2>&1 | grep -v "^computed" | head -9
python3 - <<'EOF'
import json
d = json.load(open("/home/user/4DPrediction/analysis/formula_list_results.json"))
dates = d["dates"]
F = sorted(d["formulas"], key=lambda f: (-f["recent"]["straight_rm"], -f["z_after"]))
short = lambda s: s.replace("Sports Toto", "Toto").replace("Da Ma Cai", "DMC").replace("Consolation", "Cons").replace("Special", "Spec")
print("| # | Formula | Method | 2012-26 | " + " | ".join(x[5:] for x in dates) + " | Straight RM | i-Box (~RM) |")
for i, f in enumerate(F, 1):
    cells = []
    for x in dates:
        p = f["per_draw"].get(x)
        if p is None: cells.append("n/a")
        elif p["straight"]: cells.append("; ".join(short(h) for h in p["straight"]))
        else: cells.append(f"– ({p['ibox']} iB)")
    r = f["recent"]
    print(f"| {i} | {f['formula']} | {f['method']} | x{f['ratio_after']:.3f} | " + " | ".join(cells) + f" | {r['straight_rm']} | {r['ibox']} (~{r['ibox_rm']:.0f}) |")
st = sum(f["recent"]["staked"] for f in F); sh = sum(f["recent"]["straight_hits"] for f in F); srm = sum(f["recent"]["straight_rm"] for f in F)
ib = sum(f["recent"]["ibox"] for f in F); irm = sum(f["recent"]["ibox_rm"] for f in F)
print(f"TOTAL staked {st} straight {sh} RM{srm} expected hits {st/48*0.11:.1f} ibox {ib} RM{irm:.0f}")
for x in dates:
    print(x, "straight hits", sum(len(f['per_draw'].get(x, {}).get('straight', [])) for f in F), "RM", sum(f['per_draw'].get(x, {}).get('straight_rm', 0) for f in F))
EOF
```

## 124. 2026-10-22 08:33 — Save full table to repo and commit

```bash
python3 - <<'EOF' > analysis/formula_list_last5.md
import json
d = json.load(open("analysis/formula_list_results.json"))
dates = d["dates"]
F = sorted(d["formulas"], key=lambda f: (-f["recent"]["straight_rm"], -f["z_after"]))
short = lambda s: s.replace("Sports Toto", "Toto").replace("Da Ma Cai", "DMC").replace("Consolation", "Cons").replace("Special", "Spec")
print("# Formula list: last 5 draws\n")
print("Picks rebuilt before each draw from earlier results only; method per formula chosen on 1985-2011 draws. "
      "RM1 Big on 16 numbers x 3 operators = RM48 per draw. iB = i-Box matches. From `formula_list_test.py`.\n")
print("| # | Formula | Method | 2012-26 | " + " | ".join(x[5:] for x in dates) + " | Straight RM | i-Box (~RM) |")
print("|---|---|---|---|" + "---|" * len(dates) + "---|---|")
for i, f in enumerate(F, 1):
    cells = []
    for x in dates:
        p = f["per_draw"].get(x)
        cells.append("n/a" if p is None else ("; ".join(short(h) for h in p["straight"]) if p["straight"] else f"– ({p['ibox']} iB)"))
    r = f["recent"]
    print(f"| {i} | {f['formula']} | {f['method']} | x{f['ratio_after']:.3f} | " + " | ".join(cells) + f" | {r['straight_rm']} | {r['ibox']} (~{r['ibox_rm']:.0f}) |")
EOF
git add analysis/formula_list_test.py analysis/formula_list_results.json analysis/formula_list_last5.md && git commit -qm "Formula list: per-draw results for the last 5 draws

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q origin claude/4d-results-scraper-9ptbd5 && git status -sb | head -1
```

## 125. 2026-10-22 08:38 — Rebuild picks and tabulate i-Box matches per draw

```bash
python3 - <<'EOF' 2>&1 | grep -v "^computed" > /tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad/ibox.txt; cat /tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad/ibox.txt
import sys, json, math, re
sys.path.insert(0, "analysis")
import numpy as np
import formula_list_test as fl, navamsa_family as nf, score_leads as sc, score_live as sl
nf.r.setup(); G = nf.r.G; D = G["D"]
codes, labels = fl.build(D); nf.inject(D, codes, labels)
res = json.load(open("analysis/formula_list_results.json"))
dates = res["dates"]
rows, _ = sl.load()
win = {d: {op: {x["4d_number"]: x["prize"] for x in rows[op] if x["date"] == d} for op in sl.OPS} for d in dates}
def perms(n): return math.factorial(4) // math.prod(math.factorial(n.count(c)) for c in set(n))
short = lambda s: s.replace("Sports Toto", "Toto").replace("Da Ma Cai", "DMC").replace("Consolation", "Cons").replace("Special", "Spec")
out = []
for f in res["formulas"]:
    m = re.match(r"(S1|S2|\d+\+\d+) \((a|b)\) (\w+)", f["method"])
    p, v = m.group(1), m.group(2)
    kind = p if p.startswith("S") else tuple(int(x) - 1 for x in p.split("+"))
    test = tuple(f["formula"].split(" x "))
    cells, tot_n, tot_rm, big = [], 0, 0.0, []
    for d in dates:
        pk = sc.picks(D.dates.index(d), test, kind, v)
        n, rm = 0, 0.0
        for op in sl.OPS:
            for x in pk:
                for w, pr in win[d][op].items():
                    if sorted(w) == sorted(x):
                        n += 1; rm += sl.BIG[pr] / perms(x)
                        if pr in ("1st", "2nd", "3rd"): big.append(f"{d[5:]} {x}->{w} {short(op)} {pr}")
        cells.append(f"{n} ({rm:.0f})"); tot_n += n; tot_rm += rm
    out.append((tot_rm, f["formula"], f["method"], cells, tot_n, big))
out.sort(key=lambda x: -x[0])
print("| # | Formula | Method | " + " | ".join(d[5:] for d in dates) + " | Total matches | ~RM on RM240 | Top-3 prize matches |")
print("|---|---|---|" + "---|" * len(dates) + "---|---|---|")
for i, (rm, f, meth, cells, n, big) in enumerate(out, 1):
    print(f"| {i} | {f} | {meth} | " + " | ".join(cells) + f" | {n} | {rm:.0f} | {'; '.join(big) or '-'} |")
tn = sum(o[4] for o in out); trm = sum(o[0] for o in out)
print(f"\nTOTAL matches {tn}, ~RM{trm:.0f} on RM{240*len(out)}; per draw: " + ", ".join(
    f"{d[5:]} {sum(int(o[3][k].split()[0]) for o in out)}" for k, d in enumerate(dates)))
EOF
```

## 126. 2026-10-22 08:48 — Write per-operator runner and check it restricts the data

```bash
cat > analysis/per_operator.py <<'EOF'
#!/usr/bin/env python3
"""All analyses on singles and pairs of the 78 Vedic / Chinese parameters,
separately for each operator.

Until now winners of Magnum, Sports Toto and Da Ma Cai were pooled. Here only
one operator's winning numbers are kept, both as the source of the picks (digit
counts, earlier winners) and as the hits scored, and the chance level uses that
operator's own digit mix per year. The same suite as navamsa_family.py:
  A  digit mix given the value(s), learned before 2012, scored 2012-2026
  B  same 4D number again when the value(s) recur (Straight / Reverse / i-Box,
     any later / next same-value day)
  C  digit-position picks: S1, S2, rank pairs 1+10 .. 5+6; (a) all / (b)
     previous same-value day; Straight / Reverse / i-Box; forward check
  D  whole-number hot / cold, forward check
each against circularly shifted parameter calendars.

Run from the repo root:  python3 analysis/per_operator.py OPERATOR [n_shifts]
   OPERATOR = Magnum | "Sports Toto" | "Da Ma Cai"
"""

import itertools
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am  # noqa: E402
import digit_models as dm  # noqa: E402

ROW_FIELDS = ("rd", "ro", "rn", "ry", "rdig", "rj")


def restrict_to(op_ix):
    """Make every Data() keep only one operator's winning-number rows."""
    orig = dm.Data.__init__

    def init(self, *a, **k):
        orig(self, *a, **k)
        m = self.ro == op_ix
        for f in ROW_FIELDS:
            setattr(self, f, getattr(self, f)[m])
    dm.Data.__init__ = init


def main():
    op = sys.argv[1]
    n_shifts = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    op_ix = am.OPS.index(op)
    restrict_to(op_ix)
    import navamsa_family as nf                                          # imported after the patch
    nf.wn.setup()
    nf.rperm.setup()
    D = nf.r.G["D"]
    assert set(np.unique(D.ro)) == {op_ix}
    print(f"=== {op}: {len(D.rn)} winning numbers on {len(np.unique(D.rd))} draw days ===")
    tests = [(f,) for f in nf.r.FACT] + list(itertools.combinations(nf.r.FACT, 2))
    tag = op.lower().replace(" ", "")
    nf.run_suite(tests, n_shifts, f"per_operator_{tag}_results.json", seed=61 + op_ix)


if __name__ == "__main__":
    main()
EOF
python3 - <<'EOF' 2>&1 | grep -v "^computed\|matches between"
import sys, time
sys.argv = ["x", "Sports Toto"]
sys.path.insert(0, "analysis")
import numpy as np
import per_operator as po, astro_model as am
po.restrict_to(am.OPS.index("Sports Toto"))
import navamsa_family as nf
nf.wn.setup(); nf.rperm.setup()
D = nf.r.G["D"]
print(np.unique(D.ro), len(D.rn), nf.r.G["nwin"][-3:], nf.rperm.G["nwin"][-3:])
for m in "ABCD":
    t = time.time(); x = nf.task((m, ("karana", "day_pillar"), 0)); print(m, round(time.time() - t, 2), np.shape(x))
EOF
```

## 127. 2026-10-22 08:48 — Fix empty-year digit mix and recheck

```bash
sed -n 72,76p analysis/recurrence_s12.py && python3 - <<'EOF'
p = "analysis/recurrence_s12.py"
s = open(p).read()
s = s.replace("    q /= q.sum(2, keepdims=True)\n", "    with np.errstate(invalid=\"ignore\"):\n        q /= q.sum(2, keepdims=True)\n    q = np.nan_to_num(q, nan=0.1)                                         # years with no draws (operator not yet running)\n", 1)
open(p, "w").write(s)
EOF
python3 - <<'EOF' 2>&1 | grep -v "^computed\|matches between"
import sys
sys.path.insert(0, "/home/user/4DPrediction/analysis")
import numpy as np, per_operator as po, astro_model as am
po.restrict_to(am.OPS.index("Da Ma Cai"))
import navamsa_family as nf
nf.wn.setup()
print("nan in Py:", np.isnan(nf.r.G["Py"]).any())
x = nf.task(("C", ("karana", "day_pillar"), 0)); print("nan in C:", np.isnan(x).any(), x[0])
x = nf.task(("D", ("karana", "day_pillar"), 0)); print("nan in D:", np.isnan(x).any(), x[0])
EOF
```

## 128. 2026-10-22 13:16 — Commit Da Ma Cai results and update findings

```bash
python3 - <<'EOF'
p = "analysis/FINDINGS.md"
s = open(p).read()
s = s.replace("| Whole-number hot / cold", "| Every analysis (A-D) on singles and pairs, separately for Magnum, Sports Toto, Da Ma Cai | `per_operator.py` |\n| Whole-number hot / cold", 1)
s = s.replace("## Live checks", """## Per operator (`per_operator.py`)

Picks built from and scored on one operator only. Magnum: weekday changes the digit mix
slightly (best of all tests, beats all shifted calendars) and analysis C is a little above
chance (forward +0.10 vs -0.04; 10 of 42 columns beat every shift vs ~6). Sports Toto and
Da Ma Cai: at chance (forward -0.00 vs -0.06 and +0.05 vs +0.06). Effects too small to bet on.

## Live checks""", 1)
open(p, "w").write(s)
EOF
git add analysis/per_operator_damacai_results.json analysis/FINDINGS.md && git commit -qm "Per-operator results: Da Ma Cai; summary in findings

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q origin claude/4d-results-scraper-9ptbd5 && git status -sb | head -1
```

## 129. 2026-10-22 14:03 — Update findings with corrected consistency results and commit

```bash
python3 - <<'EOF'
p = "analysis/FINDINGS.md"
s = open(p).read()
old_start = s.index("## Most consistent lead (picks rebuilt before every draw)")
old_end = s.index("## Per operator (`per_operator.py`)")
new = """## Most consistent leads (picks rebuilt before every draw; `yearly_consistency.py`)

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

"""
s = s[:old_start] + new + s[old_end:]
open(p, "w").write(s)
EOF
git add analysis/FINDINGS.md analysis/yearly_consistency_*.json && git commit -qm "Year-by-year consistency per operator; correct the Karana x Day pillar luck estimate

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q origin claude/4d-results-scraper-9ptbd5 && git status -sb | head -1
```

## 130. 2026-10-22 14:06 — Score the two most consistent leads on the last 5 draws

```bash
python3 analysis/score_leads.py 2026-10-11 2026-10-14 2026-10-17 2026-10-18 2026-10-21 2>&1 | grep "^=== \|^1 Karana"; python3 - <<'EOF' 2>&1 | grep -v "^computed\|RuntimeWarning\|q /="
import sys
sys.path.insert(0, "analysis")
import per_operator as po, astro_model as am
po.restrict_to(am.OPS.index("Magnum"))
import recurrence_s12 as r, score_leads as sc, score_live as sl
r.setup(); D = r.G["D"]; rows, _ = sl.load()
tot = [0, 0, 0, 0.0]
for d in ["2026-10-11", "2026-10-14", "2026-10-17", "2026-10-18", "2026-10-21"]:
    pk = sc.picks(D.dates.index(d), ("jupiter_retrograde", "kp_asc_sub_lord"), (3, 6), "b")
    win = {"Magnum": {x["4d_number"]: x["prize"] for x in rows["Magnum"] if x["date"] == d}}
    if pk is None: print(d, "no earlier same-value day"); continue
    s, sp, b, bp = sc.score({"Magnum": pk}, win)
    tot[0] += len(s); tot[1] += sp; tot[2] += len(b); tot[3] += bp
    print(d, " ".join(pk)); print("   straight", s or "-", sp, "| i-Box", b or "-", round(bp, 2))
print("TOTAL straight", tot[0], tot[1], "ibox", tot[2], round(tot[3], 2))
EOF
```

## 131. 2026-10-22 14:25 — Check how many top-3 matches drive the 6-arrangement result

```bash
python3 - <<'EOF' 2>&1 | grep -v "^computed"
import sys, math
sys.path.insert(0, "analysis")
import numpy as np
import karana_profit as kp, recurrence_s12 as r, astro_model as am
# re-run the record building quickly by importing main's logic
r.setup(); G = r.G; D = G["D"]
yr = np.array([int(d[:4]) for d in D.dates])
_, _, _, _, draws, _ = am.load()
cells = r.cells_of(kp.TEST); last = {}
stats = {}
for t in range(G["nd"]):
    c = cells[t]
    if c in last:
        P = r.picks(G["dday"][last[c]][None], True)[0]
        for o in range(3):
            if (t, o) not in draws: continue
            win = draws[(t, o)][1]
            for n in P:
                n = int(n); k = kp.perms_of(n)
                if k != 6: continue
                per = "before" if yr[t] < 2012 else "after"
                s = stats.setdefault(per, {"bets": 0, "top3": [], "small": 0.0})
                s["bets"] += 1
                for p, w in win:
                    if G["box"][w] == G["box"][n] and str(p) in ("1st", "2nd", "3rd"):
                        s["top3"].append((D.dates[t], am.OPS[o], f"{n:04d}", f"{w:04d}", str(p)))
                        s["small"] += kp.SMALL[str(p)] / 6
    last[c] = t
for per, s in stats.items():
    exp_top3 = s["bets"] * 3 * 6 / 10000
    print(per, "bets", s["bets"], "top-3 i-Box matches", len(s["top3"]), f"(chance ~{exp_top3:.1f})", "Small i-Box return", f"{100 * s['small'] / s['bets']:.0f}%")
    for x in s["top3"][-8:]: print("   ", x)
EOF
```

## 132. 2026-10-22 14:30 — Two-pair picks in the last 5 draws and for 24 Oct

```bash
python3 - <<'EOF' 2>&1 | grep -v "^computed"
import sys, datetime as dt
sys.path.insert(0, "analysis")
import numpy as np
import karana_profit as kp, recurrence_s12 as r, astro_model as am, score_live as sl
r.setup(); G = r.G; D = G["D"]
rows, _ = sl.load()
cells = r.cells_of(kp.TEST)
def picks_before(t, code):
    e = np.flatnonzero((cells == code) & (np.arange(G["nd"]) < t))
    return (r.picks(G["dday"][e[-1:]].sum(0, keepdims=True), True)[0], D.dates[e[-1]]) if len(e) else (None, None)
for d in kp.LAST5:
    t = D.dates.index(d)
    P, src = picks_before(t, cells[t])
    two = [f"{int(n):04d}" for n in P if kp.perms_of(int(n)) == 6]
    res = []
    for op in sl.OPS:
        win = {x["4d_number"]: x["prize"] for x in rows[op] if x["date"] == d}
        for n in two:
            for w, p in win.items():
                if sorted(w) == sorted(n): res.append(f"{n}->{w} {op} {p}")
    print(f"{d}: two-pair picks {two or 'none'} | matches {res or 'none'}")
# next draw 24 Oct: values and picks
ix, c2, ctx = am.date_codes("2026-10-24", D.codes, D.labels, list(kp.TEST))
code = 0
for f in kp.TEST: code = code * (int(D.codes[f].max()) + 1) + int(c2[f][-1])
e = np.flatnonzero(cells == code)
print("24 Oct:", {f: ctx[f] for f in kp.TEST}, "previous same-value day:", D.dates[e[-1]] if len(e) else None)
if len(e):
    P = r.picks(G["dday"][e[-1:]].sum(0, keepdims=True), True)[0]
    print("   all 16:", " ".join(sorted(f"{int(n):04d}" for n in P)))
    print("   two-pair:", [f"{int(n):04d}" for n in P if kp.perms_of(int(n)) == 6])
EOF
```

## 133. 2026-10-22 14:31 — Add the lead to findings and push

```bash
python3 - <<'EOF'
p = "analysis/FINDINGS.md"
s = open(p).read()
s = s.replace("## Per operator (`per_operator.py`)", """## Lead: Karana x Day pillar, two-pair picks only, Small i-Box (`karana_profit.py`)

From Karana x Day pillar's 16 picks (S1 from the previous same-value day), bet only the
numbers with two pairs (6 arrangements, e.g. 3311, 7744) as Small i-Box on all 3
operators. i-Box matches x1.42 before 2012 and x1.26 in 2012-2026; Small i-Box return
105% and 103%. Caveat: it rests on 8 top-3 matches in 2012-2026 against ~5.7 by chance
(about a 1-in-4 chance by luck), and such picks are rare (about 0.6 per draw).
Last 5 draws: two-pair picks only on 11 Oct (6116) and 18 Oct (9696), no matches.
24 Oct: no two-pair picks (Garaja x Xin Wei, from 23 Jan 2021).

## Per operator (`per_operator.py`)""", 1)
open(p, "w").write(s)
EOF
git add analysis/FINDINGS.md && git commit -qm "Add Karana x Day pillar two-pair Small i-Box lead to findings

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q origin claude/4d-results-scraper-9ptbd5 && git status -sb | head -1
```

## 134. 2026-10-22 14:34 — Write pattern i-Box test and check against the Karana breakdown

```bash
cat > analysis/pattern_ibox.py <<'EOF'
#!/usr/bin/env python3
"""Do some leads favour one i-Box number pattern?

i-Box patterns of a pick: ABCD (24 arrangements), AABC (12), AABB (6), AAAB (4),
AAAA (1). For every single parameter and pair, the digit-position picks of
analysis C (S1, S2, rank pairs 1+10 .. 5+6; (a) all / (b) previous same-value
day) are scored as i-Box per pick (each pick a separate bet), split by the
pick's pattern, before 2012 and 2012-2026. Chance per pick = winners x the
probability of a number in its box under that year's digit mix.
Per pattern:
  forward   the 5 tests with the best z before 2012 in each picks column, z on 2012-2026
  overall   average z on 2012-2026 over all tests (does the pattern beat chance in general?)
both against the same on circularly shifted parameter calendars.

Run from the repo root:  python3 analysis/pattern_ibox.py pooled|Magnum|"Sports Toto"|"Da Ma Cai" [n_shifts]
"""

import itertools
import json
import math
import multiprocessing as mp
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am  # noqa: E402
import per_operator as po  # noqa: E402

PATTERNS = [24, 12, 6, 4, 1]
PNAME = {24: "ABCD", 12: "AABC", 6: "AABB", 4: "AAAB", 1: "AAAA"}
PICKERS = ["S1", "S2", (0, 9), (1, 8), (2, 7), (3, 6), (4, 5)]
COLS = [(p, v, k) for p in PICKERS for v in "ab" for k in PATTERNS]
SPLIT = 2012
M = {}


def pname(p):
    return p if isinstance(p, str) else f"{p[0] + 1}+{p[1] + 1}"


def setup():
    import recurrence_rankpairs as rp
    import recurrence_s12 as r
    r.setup()
    G = r.G
    G["yr"] = np.array([int(d[:4]) for d in G["D"].dates])
    D = G["D"]
    perms = np.array([math.factorial(4) // math.prod(math.factorial(f"{n:04d}".count(c)) for c in set(f"{n:04d}"))
                      for n in range(10000)])
    M.update(r=r, rp=rp, perms=perms)


def evaluate(cells):
    r, rp = M["r"], M["rp"]
    G = r.G
    dday = G["dday"]
    order = np.lexsort((np.arange(len(cells)), cells))
    sc = cells[order]
    newgrp = np.r_[True, sc[1:] != sc[:-1]]
    hp = ~newgrp
    days = order[hp]
    late = G["yr"][days] >= SPLIT
    cs = np.cumsum(dday[order], axis=0)
    st = np.maximum.accumulate(np.where(newgrp, np.arange(len(sc)), 0))
    base = np.where((st > 0)[:, None, None], cs[np.maximum(st - 1, 0)], 0)
    src = {"a": (cs - dday[order] - base)[hp], "b": dday[order[:-1]][hp[1:]]}
    y = G["yix"][days][:, None]
    nw = G["nwin"][days][:, None]
    res = {}
    for p in PICKERS:
        for v in "ab":
            if p == "S1":
                P = r.picks(src[v], True)
            elif p == "S2":
                P = r.picks(src[v], False)
            else:
                P = rp.pair_picks(np.argsort(-src[v], axis=2, kind="stable"), p)
            B = G["box"][P]
            h = G["Cb"][days[:, None], B]                                  # i-Box matches per pick
            e = nw * G["Pbox"][y, B]
            k = M["perms"][P]
            for pat in PATTERNS:
                m = k == pat
                hb, eb = (h * m)[~late].sum(), (e * m)[~late].sum()
                ha, ea = (h * m)[late].sum(), (e * m)[late].sum()
                res[(p, v, pat)] = (hb, eb, ha, ea)
    return np.array([res[c] for c in COLS], float)


def task(args):
    test, shift = args
    return evaluate(M["r"].cells_of(test, shift))


def zz(o, e):
    return np.where(e > 0, (o - e) / np.sqrt(np.maximum(e, 1e-9)), 0.0)


def stats(A):
    zb, za = zz(A[:, :, 0], A[:, :, 1]), zz(A[:, :, 2], A[:, :, 3])
    top = np.argsort(-zb, axis=0)[:5]
    fwd = np.take_along_axis(za, top, 0).mean(0)
    return zb, za, top, fwd, za.mean(0)


def main():
    which = sys.argv[1]
    n_shifts = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    if which != "pooled":
        po.restrict_to(am.OPS.index(which))
    t0 = time.time()
    setup()
    r = M["r"]
    tests = [(f,) for f in r.FACT] + list(itertools.combinations(r.FACT, 2))
    names = [" x ".join(t) for t in tests]
    rng = np.random.default_rng(83)
    shifts = [int(s) for s in rng.integers(170, r.G["nd"] - 170, n_shifts)]
    with mp.get_context("fork").Pool(4) as pool:
        A = np.array(pool.map(task, [(t, 0) for t in tests], chunksize=16))
        print(f"{which}: {len(tests)} tests ({time.time() - t0:.0f}s)", flush=True)
        null = [stats(np.array(pool.map(task, [(t, s) for t in tests], chunksize=16))) for s in shifts]
    zb, za, top, fwd, allz = stats(A)
    nf = np.array([x[3] for x in null])
    na = np.array([x[4] for x in null])
    out = {"which": which, "patterns": {}}
    print(f"\n=== {which}: i-Box by pick pattern (z on 2012-2026; 0 = chance) ===")
    print("pattern | share of picks | no-parameter ratio after | overall mean z real (shifted) | forward mean z real (shifted) | columns beating every shift")
    for pat in PATTERNS:
        idx = [ci for ci, c in enumerate(COLS) if c[2] == pat]
        share = A[:, idx, 3].sum() / A[:, :, 3].sum()
        beat = sum(1 for ci in idx if (nf[:, ci] < fwd[ci]).all())
        print(f"{PNAME[pat]} ({pat}) | {100 * share:.1f}% of expected matches | | {allz[idx].mean():+.3f} ({na[:, idx].mean():+.3f}) | "
              f"{fwd[idx].mean():+.3f} ({nf[:, idx].mean():+.3f}) | {beat} of {len(idx)} (~{len(idx) / (n_shifts + 1):.1f} by chance)")
        cols = []
        for ci in idx:
            p, v, _ = COLS[ci]
            q = top[0, ci]
            cols.append({"picks": pname(p), "version": v, "forward": float(fwd[ci]), "null_forward": nf[:, ci].tolist(),
                         "overall": float(allz[ci]), "null_overall": na[:, ci].tolist(),
                         "top_tests": [{"test": names[t], "z_before": float(zb[t, ci]), "hits_after": float(A[t, ci, 2]),
                                        "exp_after": float(A[t, ci, 3]), "z_after": float(za[t, ci])} for t in top[:, ci]]})
        out["patterns"][PNAME[pat]] = cols
    print("\nBest forward picks per pattern (chosen before 2012, scored 2012-2026):")
    for pat in PATTERNS:
        best = []
        for ci, c in enumerate(COLS):
            if c[2] != pat:
                continue
            for t in top[:, ci]:
                best.append((za[t, ci], names[t], c, zb[t, ci], A[t, ci, 2], A[t, ci, 3]))
        best.sort(key=lambda x: -x[0])
        print(f"  {PNAME[pat]}:")
        for z, n, c, b, h, e in best[:3]:
            print(f"     {n:<42} {pname(c[0])} ({c[1]}) | before z {b:+.2f} | after {h:.0f}/{e:.1f} (x{h / e if e else 0:.3f}, z {z:+.2f})")
    tag = which.lower().replace(" ", "")
    json.dump(out, open(os.path.join(am.ROOT, "analysis", f"pattern_ibox_{tag}.json"), "w"), indent=1)
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
EOF
python3 - <<'EOF' 2>&1 | grep -v "^computed"
import sys, time
sys.argv = ["x", "pooled"]
sys.path.insert(0, "/home/user/4DPrediction/analysis")
import pattern_ibox as pi
pi.setup()
t = time.time(); A = pi.evaluate(pi.M["r"].cells_of(("karana", "day_pillar"))); print(round(time.time() - t, 2))
for ci, c in enumerate(pi.COLS):
    if c[0] == "S1" and c[1] == "b": print(pi.PNAME[c[2]], A[ci].round(1))
EOF
```

## 135. 2026-10-22 16:08 — Recount the Da Ma Cai two-pair outlier by year

```bash
python3 - <<'EOF' 2>&1 | grep -v "^computed\|errstate\|q /="
import sys, math
sys.path.insert(0, "analysis")
import numpy as np
import per_operator as po, astro_model as am
po.restrict_to(am.OPS.index("Da Ma Cai"))
import recurrence_s12 as r, recurrence_rankpairs as rp
r.setup(); G = r.G; D = G["D"]
yr = np.array([int(d[:4]) for d in D.dates])
_, _, _, _, draws, _ = am.load()
perms = lambda n: math.factorial(4) // math.prod(math.factorial(f"{n:04d}".count(c)) for c in set(f"{n:04d}"))
SMALL = {"1st": 3500, "2nd": 2000, "3rd": 1000}
BIG = {"1st": 2500, "2nd": 1000, "3rd": 500, "Special": 180, "Consolation": 60}
cells = r.cells_of(("kp_moon_number", "kp_asc_star_lord"))
order = np.lexsort((np.arange(len(cells)), cells))
by_year = {}
picks_tot = 0; events = []
seen_cell = {}
cum = {}
for t in range(G["nd"]):
    c = cells[t]
    if c in cum:
        C = cum[c][None]
        P = rp.pair_picks(np.argsort(-C, axis=2, kind="stable"), (2, 7))[0]
        two = [int(n) for n in P if perms(int(n)) == 6]
        if (t, 2) in draws and two:
            win = draws[(t, 2)][1]
            Y = yr[t]
            b = by_year.setdefault(Y, {"picks": 0, "match_pairs": 0, "distinct": 0, "exp": 0.0, "big": 0.0, "small": 0.0})
            b["picks"] += len(two)
            b["exp"] += sum(G["nwin"][t] * G["Pbox"][G["yix"][t], G["box"][n]] for n in two)
            hit_w = set()
            for n in two:
                for p, w in win:
                    if G["box"][w] == G["box"][n]:
                        b["match_pairs"] += 1; hit_w.add((w, str(p)))
                        b["big"] += BIG[str(p)] / 6; b["small"] += SMALL.get(str(p), 0) / 6
                        if yr[t] >= 2012: events.append((D.dates[t], f"{n:04d}", f"{w:04d}", str(p)))
            b["distinct"] += len(hit_w)
    cum[c] = cum.get(c, 0) + G["dday"][t]
print("year | two-pair picks | matches (counted per pick) | distinct winners matched | expected | Big i-Box RM | Small i-Box RM")
T = {"picks": 0, "match_pairs": 0, "distinct": 0, "exp": 0.0, "big": 0.0, "small": 0.0}
for Y in sorted(by_year):
    if Y < 2012: continue
    b = by_year[Y]
    for k in T: T[k] += b[k]
    print(f"{Y} | {b['picks']} | {b['match_pairs']} | {b['distinct']} | {b['exp']:.1f} | {b['big']:.0f} | {b['small']:.0f}")
print(f"2012-26 total | {T['picks']} | {T['match_pairs']} | {T['distinct']} | {T['exp']:.1f} | Big {T['big']:.0f} ({100*T['big']/T['picks']:.0f}%) | Small {T['small']:.0f} ({100*T['small']/T['picks']:.0f}%)")
from collections import Counter
print("prize tiers of matches:", Counter(e[3] for e in events))
print("last matches:", events[-6:])
EOF
```

## 136. 2026-10-22 16:08 — Recheck the Karana two-pair lead with distinct winners

```bash
python3 - <<'EOF' 2>&1 | grep -v "^computed"
import sys
sys.path.insert(0, "analysis")
import numpy as np
import karana_profit as kp, recurrence_s12 as r, astro_model as am
r.setup(); G = r.G; D = G["D"]
yr = np.array([int(d[:4]) for d in D.dates])
_, _, _, _, draws, _ = am.load()
cells = r.cells_of(kp.TEST); last = {}
S = {p: {"picks": 0, "pairs": 0, "distinct": 0, "exp_distinct": 0.0, "small": 0.0, "small_distinct": 0.0, "top3_distinct": 0} for p in ("before", "after")}
for t in range(G["nd"]):
    c = cells[t]
    if c in last:
        P = r.picks(G["dday"][last[c]][None], True)[0]
        two = [int(n) for n in P if kp.perms_of(int(n)) == 6]
        boxes = sorted({G["box"][n] for n in two})
        per = "before" if yr[t] < 2012 else "after"
        for o in range(3):
            if (t, o) not in draws or not two: continue
            win = draws[(t, o)][1]
            s = S[per]; s["picks"] += len(two)
            s["exp_distinct"] += sum(G["nwin"][t] / 3 * G["Pbox"][G["yix"][t], b] for b in boxes)
            for b in boxes:
                ws = [(w, str(p)) for p, w in win if G["box"][w] == b]
                k = sum(1 for n in two if G["box"][n] == b)
                s["pairs"] += k * len(ws); s["distinct"] += len(ws)
                for w, p in ws:
                    s["small"] += k * kp.SMALL[p] / 6
                    s["top3_distinct"] += p in ("1st", "2nd", "3rd")
    last[c] = t
for p, s in S.items():
    print(f"{p}: two-pair picks {s['picks']} | matches per pick {s['pairs']} | distinct winners {s['distinct']} vs ~{s['exp_distinct']:.1f} expected "
          f"(x{s['distinct'] / s['exp_distinct']:.2f}) | top-3 distinct {s['top3_distinct']} | Small i-Box return {100 * s['small'] / s['picks']:.0f}%")
EOF
```

## 137. 2026-10-22 16:09 — Commit pattern results and update findings

```bash
python3 - <<'EOF'
p = "analysis/FINDINGS.md"
s = open(p).read()
s = s.replace("| Whole-number hot / cold", "| i-Box by pick pattern (ABCD / AABC / AABB / AAAB / AAAA), all picks columns, pooled and per operator | `pattern_ibox.py` |\n| Whole-number hot / cold", 1)
s = s.replace("## Per operator (`per_operator.py`)", """## i-Box by number pattern (`pattern_ibox.py`)

No pattern beats chance in general (average over all tests equals the shifted calendars,
pooled and per operator). Pooled two-pair (AABB) forward picks lean positive (+0.29 vs
+0.19, 5 of 14 columns beat every shift vs ~2). Single-test z values for AABB / AAAB are
inflated because one winning number can match several same-digit picks (e.g. 7227 matches
7227, 7272, 7722): Da Ma Cai KP Moon number x KP Asc star lord (z +5.2) is 46 matches but
only 21 distinct winners vs 21.7 expected, i.e. chance. The Karana x Day pillar AABB lead
holds up when counted by distinct winners (81 vs 52 before 2012, 53 vs 42 after).

## Per operator (`per_operator.py`)""", 1)
open(p, "w").write(s)
EOF
git add analysis/pattern_ibox_*.json analysis/FINDINGS.md && git commit -qm "Add i-Box pattern results; note duplicate-match inflation for two-pair picks

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q origin claude/4d-results-scraper-9ptbd5 && git status -sb | head -1
```

## 138. 2026-10-22 16:15 — Describe the formula and score it on the last 5 draws

```bash
python3 - <<'EOF' 2>&1 | grep -v "^computed\|errstate\|q /="
import sys, math
sys.path.insert(0, "analysis")
import numpy as np
import per_operator as po, astro_model as am
po.restrict_to(am.OPS.index("Da Ma Cai"))
import recurrence_s12 as r, score_leads as sc, score_live as sl
r.setup(); G = r.G; D = G["D"]
rows, _ = sl.load()
perms = lambda n: math.factorial(4) // math.prod(math.factorial(n.count(c)) for c in set(n))
test = ("kp_moon_number", "kp_asc_star_lord")
cells = r.cells_of(test)
print("distinct values: kp_moon_number", len(D.labels["kp_moon_number"]), "| kp_asc_star_lord", len(D.labels["kp_asc_star_lord"]),
      "| combinations seen", len(np.unique(cells)), "| draw days", G["nd"])
for d in ["2026-10-11", "2026-10-14", "2026-10-17", "2026-10-18", "2026-10-21"]:
    t = D.dates.index(d)
    e = np.flatnonzero((cells == cells[t]) & (np.arange(G["nd"]) < t))
    vals = {f: D.labels[f][D.codes[f][t]] for f in test}
    pk = sc.picks(t, test, (2, 7), "a")
    win = {"Da Ma Cai": {x["4d_number"]: x["prize"] for x in rows["Da Ma Cai"] if x["date"] == d}}
    if pk is None:
        print(d, vals, "no earlier same-value day"); continue
    two = [n for n in pk if perms(n) == 6]
    s, sp, b, bp = sc.score({"Da Ma Cai": pk}, win)
    s2, sp2, b2, bp2 = sc.score({"Da Ma Cai": two}, win) if two else ([], 0, [], 0)
    print(f"{d} {vals} | {len(e)} earlier days")
    print(f"   16 picks: {' '.join(pk)}")
    print(f"   two-pair picks: {two or 'none'} -> straight {s2 or '-'} | i-Box {b2 or '-'}")
    print(f"   all 16: straight {s or '-'} RM{sp} | i-Box {len(b)} {b or ''} ~RM{bp:.1f}")
EOF
```

## 139. 2026-10-22 16:29 — Generalise the script, recheck Karana, run on the second lead

```bash
cd /home/user/4DPrediction && python3 - <<'EOF'
p = "analysis/karana_patterns.py"
s = open(p).read()
s = s.replace('''"""Karana x Day pillar (S1 from the previous same-value day) by i-Box pattern of
the pick:''', '''"""A lead's picks by i-Box pattern (default: Karana x Day pillar, S1 from the
previous same-value day). Pattern of the pick:''')
s = s.replace('''Run from the repo root:  python3 analysis/karana_patterns.py''', '''Run from the repo root:  python3 analysis/karana_patterns.py [param1 param2 picks version]
   e.g. python3 analysis/karana_patterns.py mars_nakshatra kp_asc_number 5+6 b''')
s = s.replace('''import recurrence_s12 as r  # noqa: E402''', '''import recurrence_rankpairs as rp  # noqa: E402
import recurrence_s12 as r  # noqa: E402''')
s = s.replace('''def main():
    r.setup()''', '''def make_picks(C, kind):
    if kind == "S1":
        return r.picks(C, True)[0]
    if kind == "S2":
        return r.picks(C, False)[0]
    a, b = (int(x) - 1 for x in kind.split("+"))
    return rp.pair_picks(np.argsort(-C, axis=2, kind="stable"), (a, b))[0]


def main():
    args = sys.argv[1:]
    test = tuple(args[:2]) if len(args) >= 2 else ("karana", "day_pillar")
    kind = args[2] if len(args) > 2 else "S1"
    version = args[3] if len(args) > 3 else "b"
    print(f"Lead: {' x '.join(test)}, {kind} ({version})")
    r.setup()''')
s = s.replace('''    cells = r.cells_of(("karana", "day_pillar"))''', '''    cells = r.cells_of(test)
    cum = {}''')
s = s.replace('''        if c in last:
            P = [int(n) for n in r.picks(G["dday"][last[c]][None], True)[0]]''', '''        if c in last:
            C = (cum[c] if version == "a" else G["dday"][last[c]])[None]
            P = [int(n) for n in make_picks(C, kind)]''')
s = s.replace('''                    recs.append((t, o, k, len(picks), distinct, exp, big, small, top3, det))
        last[c] = t''', '''                    recs.append((t, o, k, len(picks), distinct, exp, big, small, top3, det))
        last[c] = t
        cum[c] = cum.get(c, 0) + G["dday"][t]''')
s = s.replace('''        e = np.flatnonzero((cells == c) & (np.arange(G["nd"]) < t))
        P = [int(n) for n in r.picks(G["dday"][e[-1:]].sum(0, keepdims=True), True)[0]]''', '''        e = np.flatnonzero((cells == c) & (np.arange(G["nd"]) < t))
        if len(e) == 0:
            print(f"   {d}: no earlier same-value day")
            continue
        P = [int(n) for n in make_picks(G["dday"][e if version == "a" else e[-1:]].sum(0, keepdims=True), kind)]''')
open(p, "w").write(s)
EOF
python3 analysis/karana_patterns.py 2>&1 | grep -v "^computed" | sed -n 1,9p
python3 analysis/karana_patterns.py mars_nakshatra kp_asc_number 5+6 b 2>&1 | grep -v "^computed"
```

## 140. 2026-10-22 16:30 — Compare how often each pattern wins vs chance

```bash
python3 - <<'EOF' 2>&1 | grep -v "^computed"
import sys, math
sys.path.insert(0, "analysis")
import numpy as np
import recurrence_s12 as r, astro_model as am
r.setup(); G = r.G; D = G["D"]
perms = np.array([math.factorial(4) // math.prod(math.factorial(f"{n:04d}".count(c)) for c in set(f"{n:04d}")) for n in range(10000)])
names = {24: "ABCD", 12: "AABC", 6: "AABB", 4: "AAAB", 1: "AAAA"}
uni = {k: (perms == k).mean() for k in names}
yr = np.array([int(d[:4]) for d in D.dates])
for label, m in (("all years", np.ones(len(D.rn), bool)), ("before 2012", yr[D.rd] < 2012), ("2012-2026", yr[D.rd] >= 2012)):
    for o in (None, 0, 1, 2):
        mm = m & ((D.ro == o) if o is not None else True)
        k = perms[D.rn[mm]]
        # expected share under each draw's year digit mix (independent positions)
        exp = {kk: (G["Py"][G["yix"][D.rd[mm]]][:, perms == kk]).sum(1).mean() for kk in names}
        print(f"{label:<11} {('all operators' if o is None else am.OPS[o]):<13} n={mm.sum():>6} | " +
              " | ".join(f"{names[kk]} {100 * (k == kk).mean():.2f}% (uniform {100 * uni[kk]:.2f}%, digit-mix {100 * exp[kk]:.2f}%, x{(k == kk).mean() / exp[kk]:.2f})" for kk in (6, 4, 1)))
EOF
```

## 141. 2026-10-22 16:31 — Pattern shares of winning numbers vs the digit-mix model

```bash
python3 - <<'EOF' 2>&1 | grep -v "^computed"
import sys, math
sys.path.insert(0, "analysis")
import numpy as np
import recurrence_s12 as r, astro_model as am
r.setup(); G = r.G; D = G["D"]
perms = np.array([math.factorial(4) // math.prod(math.factorial(f"{n:04d}".count(c)) for c in set(f"{n:04d}")) for n in range(10000)])
names = {24: "ABCD", 12: "AABC", 6: "AABB", 4: "AAAB", 1: "AAAA"}
share_y = {kk: G["Py"][:, perms == kk].sum(1) for kk in names}       # per year, expected share of each pattern
yr = np.array([int(d[:4]) for d in D.dates])
for label, m in (("all years", np.ones(len(D.rn), bool)), ("before 2012", yr[D.rd] < 2012), ("2012-2026", yr[D.rd] >= 2012)):
    for o in (None, 0, 1, 2):
        mm = m & ((D.ro == o) if o is not None else True)
        k = perms[D.rn[mm]]; yi = G["yix"][D.rd[mm]]
        parts = []
        for kk in (6, 4, 1):
            obs = (k == kk).mean(); exp = share_y[kk][yi].mean(); n = mm.sum()
            z = (obs - exp) * n / math.sqrt(n * exp)
            parts.append(f"{names[kk]} {100 * obs:.2f}% vs {100 * exp:.2f}% (x{obs / exp:.2f}, z {z:+.1f})")
        print(f"{label:<11} {('all operators' if o is None else am.OPS[o]):<13} n={mm.sum():>6} | " + " | ".join(parts))
EOF
```

## 142. 2026-10-22 16:47 — Commit family results and update findings

```bash
python3 - <<'EOF'
p = "analysis/FINDINGS.md"
s = open(p).read()
s = s.replace("## i-Box by number pattern (`pattern_ibox.py`)", """## Karana x Day pillar family (`karana_family.py`)

Scored with the lead's method (S1 from the previous same-value day, i-Box). The Day
pillar side carries it: Day pillar x any other parameter averages z +0.43 after 2012
(shifted calendars -0.17, 1 of 20 as high; 53 of 76 above chance; 8.3 good years vs 7.2),
Panchanga x Chinese day +0.30 (0 of 20 as high). Karana x any other does not (-0.31 vs
-0.21). Halves alone: Day pillar +0.71, Karana -0.87. No relative chosen before 2012 beat
the lead after 2012 (best: Yoga x Day pillar, z +1.09). Only the lead's own method works
well; across its 42 versions the mean z after 2012 is -0.18.

## i-Box by number pattern (`pattern_ibox.py`)""", 1)
open(p, "w").write(s)
EOF
git add analysis/karana_family.py analysis/karana_family_results.json analysis/FINDINGS.md && git commit -qm "Karana x Day pillar family analysis

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q origin claude/4d-results-scraper-9ptbd5 && git status -sb | head -1
```

## 143. 2026-10-22 16:50 — Rank Day pillar pairs by performance

```bash
python3 - <<'EOF'
import json
d = json.load(open("analysis/karana_family_results.json"))["families"]["Day pillar x any other"]["members"]
rows = sorted(d.items(), key=lambda kv: -kv[1]["z_after"])
print("rank by 2012-2026 | pair | z before | z after | x after | good years")
for i, (k, v) in enumerate(rows, 1):
    print(f"{i} | {k} | {v['z_before']:+.2f} | {v['z_after']:+.2f} | x{v['ratio_after']:.3f} | {v['good_years']}")
both = [k for k, v in d.items() if v["z_before"] > 0 and v["z_after"] > 0]
print("positive in both periods:", len(both), "of", len(d))
bb = sorted(d.items(), key=lambda kv: -kv[1]["z_before"])[:10]
print("top 10 chosen before 2012 -> after:", [(k, round(v["z_before"], 2), round(v["z_after"], 2), v["good_years"]) for k, v in bb])
print("those 10 mean z after:", round(sum(v["z_after"] for k, v in bb) / 10, 2), "mean good years", sum(v["good_years"] for k, v in bb) / 10)
EOF
```

## 144. 2026-10-22 16:54 — Make the summary skip no-history triples and rerun

```bash
python3 - <<'EOF'
p = "analysis/day_pillar_triples.py"
s = open(p).read()
s = s.replace('''    def block(X):
        top = np.argsort(-X[:, 0])[:20]
        return X[:, 1].mean(), X[:, 2].mean(), X[top, 1].mean(), X[top, 2].mean(), int((X[:, 1] > lead[1]).sum()), \\
            int(((X[:, 2] >= lead[2])).sum()), int(((X[:, 0] > 2) & (X[:, 1] > 2)).sum())''', '''    def block(X):
        X = X[np.isfinite(X).all(1)]                                       # drop triples with no history in a period
        top = np.argsort(-X[:, 0])[:20]
        return X[:, 1].mean(), X[:, 2].mean(), X[top, 1].mean(), X[top, 2].mean(), int((X[:, 1] > lead[1]).sum()), \\
            int(((X[:, 2] >= lead[2])).sum()), int(((X[:, 0] > 2) & (X[:, 1] > 2)).sum())''')
s = s.replace('''    for q in np.argsort(-R[:, 0])[:10]:''', '''    R = np.where(np.isfinite(R), R, -99.0)                                  # no-history triples sort last
    for q in np.argsort(-R[:, 0])[:10]:''')
s = s.replace('''    K = R[kar]''', '''    K = R[kar]
    K = K[(K > -99).all(1)]''')
open(p, "w").write(s)
EOF
python3 -W ignore analysis/day_pillar_triples.py 2>&1 | grep -v "^computed" | sed -n 1,14p
```

## 145. 2026-10-22 17:19 — Run fast tests 3,4,5,8

```bash
python3 - <<'EOF'
s=open('karana_tests.py').read()
s=s.replace("    base = stats(*lead(cells)[::2], *lead(cells)[2][1:]) if False else None\n","")
s=s.replace("    nk = int(k.max()) + 1\n","")
s=s.replace(" if LEAD[0] == \"karana\" else None","")
open('karana_tests.py','w').write(s)
EOF
cd .. && time python3 analysis/karana_tests.py 3 4 5 8 2>&1 | tail -50
```

## 146. 2026-10-22 17:20 — Fix sunrise karana; rerun 6,7,9

```bash
python3 - <<'EOF'
p='analysis/karana_tests.py'
s=open(p).read()
s=s.replace('''        out[i] = lab.index(vedic.panchanga(t, day)["karana"])''','''        jd = vedic.eph.julian_day(t)
        half = int(((vedic.sidereal("Moon", jd) - vedic.sidereal("Sun", jd)) % 360) // 6)     # as vedic.panchanga
        k = ("Kimstughna" if half == 0 else ["Shakuni", "Chatushpada", "Naga"][half - 57] if half >= 57
             else vedic.KARANAS_MOVABLE[(half - 1) % 7])
        out[i] = lab.index(k)''')
open(p,'w').write(s)
EOF
grep -n "^import\|eph" analysis/vedic.py | head; setsid nohup bash -c "python3 analysis/karana_tests.py 6 7 9 > /tmp/claude-0/kt.log 2>&1; echo exit \$? >> /tmp/claude-0/kt.log" >/dev/null 2>&1 &
python3 - <<'EOF'
import json; d=json.load(open('/home/user/4DPrediction/analysis/karana_tests_results.json')); print(d.keys())
EOF
```

## 147. 2026-10-22 17:22 — Update FINDINGS, commit and push

```bash
cd /home/user/4DPrediction && cp /tmp/claude-0/kt.log analysis/karana_tests_output_6-9.txt && cp /tmp/claude-0/sg.log analysis/karana_singapore_output.txt && python3 - <<'EOF'
p='analysis/FINDINGS.md'
s=open(p).read()
sec='''## Karana x Day pillar: nine further checks (`karana_tests.py`, `karana_singapore.py`)

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

'''
s=s.replace("## i-Box by number pattern", sec+"## i-Box by number pattern",1)
open(p,'w').write(s)
EOF
git add -A analysis data && git commit -qm "Karana x Day pillar: nine further checks incl. Singapore 4D out-of-sample

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q -u origin claude/4d-results-scraper-9ptbd5 2>&1 | tail -2; git log --oneline -1
```

## 148. 2026-10-23 02:17 — Write Shadbala/Ashtakavarga script and test codes

```bash
cat > shadbala_ashtakavarga.py <<'EOF'
#!/usr/bin/env python3
"""Ashtakavarga and (simplified) Shadbala as parameters, run through the same
suite as the Navamsa / divisional-chart families (navamsa_family.run_suite:
A digit mix, B same-number recurrence, C S1 / S2 / rank-pair digit picks (a / b,
Straight / Reverse / i-Box, walk-forward), D whole-number hot / cold), each
against shifted calendars.

Chart: sidereal (Lahiri) positions at 19:00 MYT (continuous_astro_positions.npz).

Ashtakavarga (Parashara's bindu tables, 7 planets + Lagna as contributors)
  {planet}_bav       bindus (0-8) in the planet's own Bhinna Ashtakavarga for
                     the sign it occupies
  sav_{point}        Sarvashtakavarga bindus of the sign of Sun, Moon, ...,
                     Saturn, Lagna, and of the 11th house from Lagna; 5 bins
                     (<=22, 23-25, 26-28, 29-31, >=32)
Shadbala, simplified (no Kala / Drik / Ayana bala, which need birth-time
details or are near-constant across a few hours)
  sthana: uccha bala (distance from debilitation) + rashi dignity
  dig bala (distance from the planet's strong house: Jupiter / Mercury 1st,
  Sun / Mars 10th, Saturn 7th, Moon / Venus 4th)
  chesta bala (slow / retrograde motion; Mars - Saturn)
  paksha bala (Moon-Sun elongation: benefics gain with it, malefics lose)
  {planet}_strength  tercile of that sum (weak / medium / strong)
  strongest_planet, weakest_planet
  {planet}_dignity   exalted / own / friend / neutral / enemy / debilitated sign

Run from the repo root:  python3 analysis/shadbala_ashtakavarga.py [n_shifts]
"""

import datetime as dt
import itertools
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astro_model as am  # noqa: E402
import ephemeris as eph  # noqa: E402
import navamsa_family as nf  # noqa: E402
import vedic  # noqa: E402

PL = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
REF = PL + ["Lagna"]
# BAV[planet][reference] = houses (from the reference's sign) that give a bindu
BAV = {
    "Sun": [[1, 2, 4, 7, 8, 9, 10, 11], [3, 6, 10, 11], [1, 2, 4, 7, 8, 9, 10, 11], [3, 5, 6, 9, 10, 11, 12],
            [5, 6, 9, 11], [6, 7, 12], [1, 2, 4, 7, 8, 9, 10, 11], [3, 4, 6, 10, 11, 12]],
    "Moon": [[3, 6, 7, 8, 10, 11], [1, 3, 6, 7, 10, 11], [2, 3, 5, 6, 9, 10, 11], [1, 3, 4, 5, 7, 8, 10, 11],
             [1, 4, 7, 8, 10, 11, 12], [3, 4, 5, 7, 9, 10, 11], [3, 5, 6, 11], [3, 6, 10, 11]],
    "Mars": [[3, 5, 6, 10, 11], [3, 6, 11], [1, 2, 4, 7, 8, 10, 11], [3, 5, 6, 11], [6, 10, 11, 12],
             [6, 8, 11, 12], [1, 4, 7, 8, 9, 10, 11], [1, 3, 6, 10, 11]],
    "Mercury": [[5, 6, 9, 11, 12], [2, 4, 6, 8, 10, 11], [1, 2, 4, 7, 8, 9, 10, 11], [1, 3, 5, 6, 9, 10, 11, 12],
                [6, 8, 11, 12], [1, 2, 3, 4, 5, 8, 9, 11], [1, 2, 4, 7, 8, 9, 10, 11], [1, 2, 4, 6, 8, 10, 11]],
    "Jupiter": [[1, 2, 3, 4, 7, 8, 9, 10, 11], [2, 5, 7, 9, 11], [1, 2, 4, 7, 8, 10, 11], [1, 2, 4, 5, 6, 9, 10, 11],
                [1, 2, 3, 4, 7, 8, 10, 11], [2, 5, 6, 9, 10, 11], [3, 5, 6, 12], [1, 2, 4, 5, 6, 7, 9, 10, 11]],
    "Venus": [[8, 11, 12], [1, 2, 3, 4, 5, 8, 9, 11, 12], [3, 5, 6, 9, 11, 12], [3, 5, 6, 9, 11], [5, 8, 9, 10, 11],
              [1, 2, 3, 4, 5, 8, 9, 10, 11], [3, 4, 5, 8, 9, 10, 11], [1, 2, 3, 4, 5, 8, 9, 11]],
    "Saturn": [[1, 2, 4, 7, 8, 10, 11], [3, 6, 11], [3, 5, 6, 10, 11, 12], [6, 8, 9, 10, 11, 12], [5, 6, 11, 12],
               [6, 11, 12], [3, 5, 6, 11], [1, 3, 4, 6, 10, 11]],
}
assert sum(len(h) for v in BAV.values() for h in v) == 337
LORD = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
EXALT = {"Sun": 10, "Moon": 33, "Mars": 298, "Mercury": 165, "Jupiter": 95, "Venus": 357, "Saturn": 200}
FRIEND = {"Sun": ({"Moon", "Mars", "Jupiter"}, {"Venus", "Saturn"}), "Moon": ({"Sun", "Mercury"}, set()),
          "Mars": ({"Sun", "Moon", "Jupiter"}, {"Mercury"}), "Mercury": ({"Sun", "Venus"}, {"Moon"}),
          "Jupiter": ({"Sun", "Moon", "Mars"}, {"Mercury", "Venus"}), "Venus": ({"Mercury", "Saturn"}, {"Sun", "Moon"}),
          "Saturn": ({"Mercury", "Venus"}, {"Sun", "Moon", "Mars"})}
DIGNITY = ["exalted", "own", "friend", "neutral", "enemy", "debilitated"]
DIG_HOUSE = {"Sun": 10, "Mars": 10, "Jupiter": 1, "Mercury": 1, "Saturn": 7, "Moon": 4, "Venus": 4}
MEAN_SPEED = {"Mars": 0.524, "Mercury": 0.986, "Jupiter": 0.083, "Venus": 0.986, "Saturn": 0.033}
BENEFIC = {"Moon", "Mercury", "Jupiter", "Venus"}
SAV_BINS = [23, 26, 29, 32]


def angdist(a, b):
    d = np.abs(a - b) % 360
    return np.minimum(d, 360 - d)


def speeds(dates):
    cache = os.path.join(am.ROOT, "analysis", "shadbala_speeds.npz")
    if os.path.exists(cache):
        z = np.load(cache, allow_pickle=True)
        if list(z["dates"]) == list(dates):
            return z["v"]
    v = np.zeros((len(dates), len(MEAN_SPEED)))
    for i, d in enumerate(dates):
        jd = eph.julian_day(dt.datetime.combine(dt.date.fromisoformat(d), dt.time(11)))
        for j, p in enumerate(MEAN_SPEED):
            v[i, j] = (vedic.planet_longitude(p, jd + 0.5) - vedic.planet_longitude(p, jd - 0.5) + 180) % 360 - 180
    np.savez(cache, dates=np.array(dates), v=v)
    return v


def codes_for(dates):
    z = np.load(os.path.join(am.ROOT, "analysis", "continuous_astro_positions.npz"), allow_pickle=True)
    assert list(z["dates"]) == list(dates), "positions cache is out of date: run continuous_astro.py"
    lon = z["lon"]                                                       # Sun Moon Mars Mercury Jupiter Venus Saturn Rahu Lagna
    col = {p: lon[:, nf.BODIES.index(p)] for p in REF}
    sign = {p: (col[p] // 30).astype(int) for p in REF}
    n = len(dates)
    codes, labels = {}, {}
    # Ashtakavarga
    bav = {}
    for p in PL:
        b = np.zeros((n, 12), int)
        for ri, ref in enumerate(REF):
            for h in BAV[p][ri]:
                b[np.arange(n), (sign[ref] + h - 1) % 12] += 1
        bav[p] = b
        codes[f"{p.lower()}_bav"] = b[np.arange(n), sign[p]]
        labels[f"{p.lower()}_bav"] = [str(k) for k in range(9)]
    sav = sum(bav.values())
    for p in REF:
        codes[f"sav_{p.lower()}"] = np.digitize(sav[np.arange(n), sign[p]], SAV_BINS)
    codes["sav_11th"] = np.digitize(sav[np.arange(n), (sign["Lagna"] + 10) % 12], SAV_BINS)
    for k in [k for k in codes if k.startswith("sav_")]:
        labels[k] = ["<=22", "23-25", "26-28", "29-31", ">=32"]
    # Shadbala (simplified)
    v = speeds(dates)
    elong = (col["Moon"] - col["Sun"]) % 360
    paksha = angdist(elong, 0) / 3                                       # 0 at new Moon, 60 at full Moon
    total = np.zeros((n, len(PL)))
    for j, p in enumerate(PL):
        uccha = angdist(col[p], EXALT[p] + 180) / 3
        dignity = np.full(n, 3)                                          # neutral
        fr, en = FRIEND[p]
        lords = np.array(LORD)[sign[p]]
        dignity[np.isin(lords, list(fr))] = 2
        dignity[np.isin(lords, list(en))] = 4
        dignity[lords == p] = 1
        dignity[sign[p] == EXALT[p] // 30] = 0
        dignity[sign[p] == (EXALT[p] // 30 + 6) % 12] = 5
        codes[f"{p.lower()}_dignity"] = dignity
        labels[f"{p.lower()}_dignity"] = DIGNITY
        rashi_pts = np.array([30, 30, 15, 7.5, 3.75, 1.875])[dignity]
        strong_pt = col["Lagna"] + (DIG_HOUSE[p] - 1) * 30
        dig = 60 * (1 - angdist(col[p], strong_pt) / 180)
        chesta = np.zeros(n)
        if p in MEAN_SPEED:
            s = v[:, list(MEAN_SPEED).index(p)]
            chesta = np.clip(30 * (1 - s / MEAN_SPEED[p]) + 30 * (s < 0), 0, 60)
        pk = paksha if p in BENEFIC else 60 - paksha
        total[:, j] = uccha + rashi_pts + dig + chesta + pk
        q = np.quantile(total[:, j], [1 / 3, 2 / 3])
        codes[f"{p.lower()}_strength"] = np.digitize(total[:, j], q)
        labels[f"{p.lower()}_strength"] = ["weak", "medium", "strong"]
    codes["strongest_planet"] = total.argmax(1)
    codes["weakest_planet"] = total.argmin(1)
    labels["strongest_planet"] = labels["weakest_planet"] = PL
    return codes, labels


def main():
    n_shifts = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    nf.wn.setup()
    codes, labels = codes_for(nf.r.G["D"].dates)
    nf.rperm.setup()
    for D in (nf.r.G["D"], nf.rperm.G["D"]):
        nf.inject(D, codes, labels)
    new = list(codes)
    for k in new:
        c = np.bincount(codes[k], minlength=len(labels[k]))
        print(f"   {k:<18} " + " ".join(f"{labels[k][i]}:{c[i]}" for i in range(len(c)) if c[i]))
    tests = [(f,) for f in new] + list(itertools.combinations(new, 2)) + [(a, b) for a in new for b in nf.r.FACT]
    out = nf.run_suite(tests, n_shifts, "shadbala_ashtakavarga_results.json", seed=47)
    names = [" x ".join(t) for t in tests]
    print("\nBy group: best digit-mix gain (A) and best S1 (b) i-Box z all years (C)")
    for grp, pred in (("Ashtakavarga", lambda f: f.endswith("_bav") or f.startswith("sav_")),
                      ("Shadbala", lambda f: f.endswith(("_strength", "_planet", "_dignity")))):
        idx = [i for i, t in enumerate(tests) if any(pred(f) for f in t)]
        g = max(idx, key=lambda i: out["A"]["gain"][names[i]])
        print(f"   {grp:<13} {len(idx)} tests; best A {out['A']['gain'][names[g]]:+.3f} [{names[g]}]")


if __name__ == "__main__":
    main()
EOF
grep -n "def planet_longitude" vedic.py; python3 -c "
import sys;sys.path.insert(0,'.')
import digit_models as dm, shadbala_ashtakavarga as s
D=dm.Data(); c,l=s.codes_for(D.dates); print(len(c)); import numpy as np; print(np.bincount(c['strongest_planet']), np.bincount(c['moon_bav']))"
```

## 149. 2026-10-23 02:20 — Investigate ayana +1 artifact

```bash
python3 - <<'EOF'
import sys; sys.path.insert(0,'.')
import numpy as np, lag_rule as L, recurrence_s12 as r
L.setup(); G=r.G
cells=r.cells_of(("ayana",))
order=np.lexsort((np.arange(len(cells)),cells)); sc=cells[order]
hp=np.r_[False,sc[1:]==sc[:-1]]; days,prev=order[hp],order[:-1][hp[1:]]
s=L.at(prev,1); ok=(s>=0)&(s<days); days,s,prev=days[ok],s[ok],prev[ok]
P=r.picks(G["dday"][s],False)
h=G["W"][days[:,None],P].sum(1)
print(len(days), h.sum())
D=G["D"]
for i in np.flatnonzero(h>0)[:15]: print(D.dates[prev[i]],D.dates[s[i]],D.dates[days[i]],h[i], G["nwin"][s[i]])
from collections import Counter
print(Counter((days-s).tolist()).most_common(5))
EOF
```

## 150. 2026-10-23 02:21 — Summarize lag walk-forward vs null

```bash
python3 - <<'EOF'
import json,numpy as np
d=json.load(open('lag_rule_results.json'))
F=[];N=[];Bz=[];NB=[]
for k,v in d['forward'].items():
    F.append(v['mean_z_after']);N.append(v['null']);Bz.append(v['best_all']);NB.append(v['null_best'])
F=np.array(F);N=np.array(N)  # (offs,cols),(offs,shifts,cols)
beat=(N<F[:,None,:]).all(1)
print("forward mean real %.3f shifted %.3f; cells beating all 6 shifts %d of %d (chance %.1f)"%(F.mean(),N.mean(),beat.sum(),beat.size,beat.size/7))
offs=d['offsets']; i0=offs.index(0)
print("k=0 forward mean %.2f; per offset mean:"%F[i0].mean(), {k:round(F[i].mean()-N[i].mean(),2) for i,k in enumerate(offs)})
EOF
```

## 151. 2026-10-23 02:21 — Write lag findings, commit, check new run

```bash
cd /home/user/4DPrediction && head -40 analysis/shadbala_ashtakavarga_output.txt; python3 - <<'EOF'
p='analysis/FINDINGS.md'
s=open(p).read()
sec='''## Offset ("lag") and lunar-date rules (`lag_rule.py`)

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

'''
s=s.replace("## i-Box by number pattern", sec+"## i-Box by number pattern",1)
open(p,'w').write(s)
EOF
git add -A analysis && git commit -qm "Lag / lunar-date offset rule results; Shadbala and Ashtakavarga parameters

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q -u origin claude/4d-results-scraper-9ptbd5; git status -sb|head -3
```

## 152. 2026-10-23 06:02 — Write findings, commit, push

```bash
python3 - <<'EOF'
p='analysis/FINDINGS.md'
s=open(p).read()
sec='''## Shadbala and Ashtakavarga (`shadbala_ashtakavarga.py`)

32 new parameters from the sidereal chart at 19:00 MYT: each planet's Bhinna
Ashtakavarga bindus in its own sign (7), Sarvashtakavarga of each planet's sign, the
Lagna and the 11th house (9, binned), each planet's sign dignity (7), a simplified
Shadbala (uccha + rashi dignity + dig + chesta + paksha; tercile per planet, 7) and the
strongest / weakest planet. 3,024 tests (singles, pairs among them, and each x the 78
existing parameters), full suite A-D against 6 shifted calendars.

- A digit mix: 2 tests gain anything on 2012-2026 (best +0.001 milli-nats per digit,
  sun_strength x year_pillar), i.e. no information.
- B same-number recurrence: Straight (a) best z +3.75 (mercury_bav x kp_moon_number,
  x1.04) beats the 6 shifts, but the number of z > 2 tests (62) is near chance (56).
  i-Box and the (b) versions are below the shifted calendars.
- C digit-position picks, walk-forward: mean z -0.04 vs -0.03 shifted; 3 of 42 columns
  beat every shift (about 6 expected by chance); their top picks score z -0.47 to +0.63
  after 2012.
- No Shadbala or Ashtakavarga lead.

'''
s=s.replace("## i-Box by number pattern", sec+"## i-Box by number pattern",1)
open(p,'w').write(s)
EOF
git add -A analysis && git commit -qm "Shadbala / Ashtakavarga findings (A-C)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q -u origin claude/4d-results-scraper-9ptbd5; git status -sb|head -1
```

## 153. 2026-10-24 09:56 — Compute lead picks for 24 Oct

```bash
cd /home/user/4DPrediction/analysis && python3 - <<'EOF' 2>&1 | grep -v computed
import sys, datetime as dt; sys.path.insert(0,'.')
import numpy as np, almanac, recurrence_s12 as r, recurrence_rankpairs as rp, score_leads as sl
r.setup(); G=r.G; D=G["D"]
f=almanac.factors("2026-10-24"); f["weekday"]=dt.date(2026,10,24).weekday()
import navamsa_family as nf
nc,nl=nf.nav_codes(D.dates)
for name,test,kind,v in sl.LEADS:
    if any(t not in D.codes for t in test): 
        print(name,"(needs navamsa; skipped)"); continue
    m=np.ones(G["nd"],bool)
    vals=[]
    for t in test:
        val=f[t]; lab=D.labels[t]
        key=str(val) if str(val) in lab else val
        code=lab.index(key) if key in lab else None
        vals.append(val); m&= D.codes[t]==code
    e=np.flatnonzero(m)
    C=G["dday"][e if v=="a" else e[-1:]].sum(0,keepdims=True)
    P=r.picks(C,True) if kind=="S1" else r.picks(C,False) if kind=="S2" else rp.pair_picks(np.argsort(-C,axis=2,kind="stable"),kind)
    print(name, vals, len(e), D.dates[e[-1]] if len(e) else "-", " ".join(f"{n:04d}" for n in P[0]))
EOF
```

## 154. 2026-10-24 09:56 — Compute lead 8 picks for 24 Oct

```bash
python3 - <<'EOF' 2>&1 | grep -v computed
import sys, datetime as dt; sys.path.insert(0,'.')
import numpy as np, recurrence_s12 as r, vedic, ephemeris as eph, navamsa_family as nf, almanac
r.setup(); G=r.G; D=G["D"]
nc,nl=nf.nav_codes(D.dates)
jd=eph.julian_day(dt.datetime(2026,10,24,11))
merc_nav=int(np.floor(vedic.sidereal("Mercury",jd)*9/30)%12)
vr=almanac.factors("2026-10-24")["venus_rashi"]
m=(nc["mercury_navamsa"]==merc_nav)&(D.codes["venus_rashi"]==D.labels["venus_rashi"].index(vr))
e=np.flatnonzero(m); print(nf.RASHIS[merc_nav], vr, len(e), D.dates[e[-1]])
print(" ".join(f"{n:04d}" for n in r.picks(G["dday"][e[-1:]],False)[0]))
EOF
```

## 155. 2026-10-24 10:02 — Compute lead picks for 18 and 21 Oct

```bash
python3 - <<'EOF' 2>&1 | grep -v computed
import sys; sys.path.insert(0,'.')
import score_leads as sl, recurrence_s12 as r
r.setup(); D=r.G["D"]
for d in ("2026-10-18","2026-10-21"):
    t=D.dates.index(d)
    for name,test,kind,v in sl.LEADS[:6]:
        p=sl.picks(t,test,kind,v); print(d,name[:40],' '.join(p[:8]) if p else None)
EOF
```

## 156. 2026-10-24 10:03 — Find which single source day yields their picks

```bash
python3 - <<'EOF' 2>&1 | grep -v computed
import sys; sys.path.insert(0,'.')
import numpy as np, recurrence_s12 as r, recurrence_rankpairs as rp
r.setup(); G=r.G; D=G["D"]
targets={"lead1":("S1","4011 4016 4051 4056 4911 4916 4951 4956 9011 9016 9051 9056 9911 9916 9951 9956"),
 "lead2":((1,8),"1980 1985 1900 1905 1380 1385 1300 1305 6980 6985 6900 6905 6380 6385 6300 6305"),
 "lead6":("S2","5650 5652 5640 5642 5850 5852 5840 5842 2650 2652 2640 2642 2850 2852 2840 2842")}
def pk(C,kind):
    if kind=="S1": return r.picks(C,True)
    if kind=="S2": return r.picks(C,False)
    return rp.pair_picks(np.argsort(-C,axis=2,kind="stable"),kind)
for name,(kind,s) in targets.items():
    tgt=set(s.split())
    P=pk(G["dday"],kind)
    hit=[D.dates[i] for i in range(G["nd"]) if {f"{n:04d}" for n in P[i]}==tgt]
    print(name,"single-day source match:",hit[:5])
EOF
```

## 157. 2026-10-24 10:03 — Recount source day digits several ways

```bash
cd /home/user/4DPrediction && python3 - <<'EOF'
import csv, numpy as np, itertools
rows=[]
for f in ("magnum","sportstoto","damacai"):
    rows+= [r for r in csv.DictReader(open(f"data/{f}.csv")) if r["date"]=="2021-01-23"]
print(len(rows), rows[0].keys())
nums=[r[list(r.keys())[-1]] for r in rows]
def grid(C,hot=True,stable=True):
    o=np.argsort(-C if hot else C,axis=1,kind="stable")[:,:2]
    return {"".join(str(o[p,b[p]]) for p in range(4)) for b in itertools.product((0,1),repeat=4)}
for label,ns in (("all rows",nums),("unique",sorted(set(nums)))):
    C=np.zeros((4,10))
    for n in ns:
        for p,c in enumerate(n.zfill(4)): C[p,int(c)]+=1
    print(label, len(ns), C.astype(int).tolist()); print(sorted(grid(C)))
EOF
```

## 158. 2026-10-24 10:04 — Search which parameter values give their picks

```bash
cd /home/user/4DPrediction/analysis && python3 - <<'EOF' 2>&1 | grep -v computed
import sys; sys.path.insert(0,'.')
import numpy as np, recurrence_s12 as r, recurrence_rankpairs as rp
r.setup(); G=r.G; D=G["D"]
T={"lead1":(("karana","day_pillar"),"S1","b","4011 4016 4051 4056 4911 4916 4951 4956 9011 9016 9051 9056 9911 9916 9951 9956"),
"lead2":(("kp_moon_number","year_element"),(1,8),"b","1980 1985 1900 1905 1380 1385 1300 1305 6980 6985 6900 6905 6380 6385 6300 6305"),
"lead6":(("jupiter_nakshatra","mercury_combust"),"S2","a","5650 5652 5640 5642 5850 5852 5840 5842 2650 2652 2640 2642 2850 2852 2840 2842")}
def pk(C,kind):
    if kind=="S1": return r.picks(C,True)
    if kind=="S2": return r.picks(C,False)
    return rp.pair_picks(np.argsort(-C,axis=2,kind="stable"),kind)
for nm,(test,kind,v,s) in T.items():
    tgt=set(s.split()); a,b=test; found=[]
    for x in range(D.codes[a].max()+1):
        for y in range(D.codes[b].max()+1):
            e=np.flatnonzero((D.codes[a]==x)&(D.codes[b]==y))
            if not len(e): continue
            for cut in (len(D.dates), D.dates.index("2026-10-18")):
                ee=e[e<cut]
                if not len(ee): continue
                C=G["dday"][ee if v=="a" else ee[-1:]].sum(0,keepdims=True)
                if {f"{n:04d}" for n in pk(C,kind)[0]}==tgt: found.append((D.labels[a][x],D.labels[b][y],D.dates[ee[-1]],cut))
    print(nm,found[:5])
EOF
```

## 159. 2026-10-24 10:07 — Re-run self-check

```bash
python3 - <<'EOF'
p='analysis/predict_all.py'; s=open(p).read()
s=s.replace('''    up.D = r.G["D"]
''','''    up.D = r.G["D"]
    nf.inject(r.G["D"], *nf.nav_codes(r.G["D"].dates))
''')
open(p,'w').write(s)
EOF
python3 analysis/predict_all.py --check 2026-10-21 2>&1 | grep -v computed
```

## 160. 2026-10-24 10:08 — Fix cutoffs and re-check 21 and 18 Oct

```bash
python3 - <<'EOF'
p='analysis/predict_all.py'; s=open(p).read()
s=s.replace('''    out.update(singles(date, cutoff))
    out.update(positional(cutoff))
''','''    for cut, suffix in ((min(FROZEN, cutoff), ""), (cutoff, "_upd")):
        for k, v in {**singles(date, cut), **positional(cut)}.items():
            out[k + suffix] = v
''')
s=s.replace('''  single_<param>/<kind>                the six selected single-parameter formulas (astro_model Counts)
  positional_hot / cold_noparam        S1 / S2 grid from all earlier results of each operator''','''  single_<param>/<kind>                the six selected single-parameter formulas (astro_model Counts)
  positional_hot / cold_noparam        S1 / S2 grid from all earlier results of each operator
                                       (both: frozen = results before 2026-10-17, _upd = before DATE)''')
open(p,'w').write(s)
EOF
python3 analysis/predict_all.py --check 2026-10-21 2>&1 | grep -v "computed\|MATCH$"; python3 analysis/predict_all.py --check 2026-10-18 2>&1 | grep -v "computed\|MATCH$"
```

## 161. 2026-10-24 10:09 — Add cutoff to astro_model and compare

```bash
python3 - <<'EOF'
p='astro_model.py'; s=open(p).read()
s=s.replace('''def picks_for(date, variants, k):
    with open(FORMULAS) as fh:
        formulas = json.load(fh)
    data, codes, labels, rows, draws, _ = load()
    out = {}''','''def picks_for(date, variants, k, before=None):
    """Top-k picks per operator from the results of draws before `before` (default: `date`)."""
    with open(FORMULAS) as fh:
        formulas = json.load(fh)
    data, codes, labels, rows, draws, _ = load()
    dates = sorted({r["date"] for op, stem in cn.OPERATORS.items()
                    for r in csv.DictReader(open(os.path.join(ROOT, "data", f"{stem}.csv")))
                    if (op, r["date"]) not in cn.EXCLUDE})
    ok = np.array([d < (before or date) for d in dates])[rows["date"]]
    rows = {key: v[ok] for key, v in rows.items()}
    out = {}''')
s=s.replace('''    res = picks_for(a.date, variants, a.k)
    print(f"Picks for draws on {a.date} (top {a.k}):")''','''    res = picks_for(a.date, variants, a.k, a.before)
    print(f"Picks for draws on {a.date} (top {a.k}, results before {a.before or a.date}):")''')
s=s.replace('''    res = picks_for(a.date, list(VARIANTS), a.k)
    new =''','''    res = picks_for(a.date, list(VARIANTS), a.k, a.before)
    new =''')
s=s.replace('''    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--retune"''','''    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--before", help="use only results of draws before this date (default: --date)")
    ap.add_argument("--retune"''')
open(p,'w').write(s)
EOF
grep -n "^import csv\|cn\b" astro_model.py | head -3
cd .. && for c in 2026-10-17 2026-10-18; do python3 analysis/astro_model.py predict --date 2026-10-21 --before $c 2>&1 | grep "vedic    Magnum"; done; grep "2026-10-21,vedic,Magnum" analysis/forward_log.csv | cut -d, -f1,6 | tr '\n' ' '
```

## 162. 2026-10-24 10:10 — Integrate astro_model sets and recheck

```bash
python3 - <<'EOF'
p='analysis/predict_all.py'; s=open(p).read()
s=s.replace('''    out.update(manual_v2(date))
    return out, info''','''    out.update(manual_v2(date))
    for cut, suffix in ((min(FROZEN, cutoff), ""), (cutoff, "_upd")):
        for k, v in am.picks_for(date, list(am.VARIANTS), 10, cut).items():
            out[k + suffix] = v
    return out, info''')
s=s.replace("  vedic / chinese / both               astro_model.py frozen formulas (run as a separate process)",
            "  vedic / chinese / both               astro_model.py frozen formulas (results before 2026-10-17; _upd before DATE)")
s=s.replace('''    print("\\nAlso run:  python3 analysis/astro_model.py predict --date DATE   (vedic / chinese / both)")
    print("           python3 analysis/ml_model.py''','''    print("\\nAlso run:  python3 analysis/ml_model.py''')
s=s.replace("(astro_model.py / ml_model.py)","(ml_model.py)")
open(p,'w').write(s)
EOF
for d in 2026-10-21 2026-10-18; do python3 analysis/predict_all.py --check $d 2>&1 | grep -E "DIFFERENT|rebuilt|logged|vedic|chinese|both"; done
```

## 163. 2026-10-24 10:12 — Inspect scores near rank 10

```bash
cd /home/user/4DPrediction/analysis && python3 - <<'EOF' 2>&1 | grep -v computed
import sys; sys.path.insert(0,'.')
import numpy as np, astro_model as am, json, csv, os
F=json.load(open(am.FORMULAS)); data,codes,labels,rows,draws,_=am.load()
dates=sorted({r["date"] for op,st in am.cn.OPERATORS.items() for r in csv.DictReader(open(os.path.join(am.ROOT,"data",f"{st}.csv"))) if (op,r["date"]) not in am.cn.EXCLUDE})
ok=np.array([d<"2026-10-17" for d in dates])[rows["date"]]; rows={k:v[ok] for k,v in rows.items()}
formula=[tuple(t) for t in F["vedic"]["terms"]]; fs=sorted({f for f,_,_ in formula})
ix,c2,ctx=am.date_codes("2026-10-21",codes,labels,fs); c=am.Counts(fs,c2); c.add(rows["date"],rows["op_ix"],rows["num"])
s=am.score(c,formula,ix,1); o=np.argsort(-s)
for n in o[:14]: print(f"{n:04d} {s[n]:.6f}")
for n in (563,9596,504,633): print(n, s[n], int((s>s[n]).sum())+1)
EOF
```

## 164. 2026-10-24 10:13 — Set astro frozen cutoff and recheck

```bash
python3 - <<'EOF'
p='analysis/predict_all.py'; s=open(p).read()
s=s.replace('FROZEN = "2026-10-17"\n','FROZEN = "2026-10-17"\nASTRO_FROZEN = "2026-10-11"          # vedic / chinese / both were logged before the 11 and 14 Oct results were added\n')
s=s.replace('''        for k, v in am.picks_for(date, list(am.VARIANTS), 10, cut).items():''','''        cut = min(ASTRO_FROZEN, cutoff) if suffix == "" else cut
        for k, v in am.picks_for(date, list(am.VARIANTS), 10, cut).items():''')
s=s.replace("(results before 2026-10-17; _upd before DATE)","(results before 2026-10-11; _upd before DATE)")
open(p,'w').write(s)
EOF
for d in 2026-10-21 2026-10-18; do python3 analysis/predict_all.py --check $d 2>&1 | grep -E "DIFFERENT|rebuilt|logged " ; done; echo done
```

## 165. 2026-10-24 10:15 — Update README, commit and push

```bash
python3 - <<'EOF'
s=open('README.md').read()
sec='''## Making picks for a draw (use these; do not re-implement)

```
python3 analysis/predict_all.py 2026-10-24            # every logged pick set, from results before that date
python3 analysis/predict_all.py 2026-10-24 --log      # also append them to analysis/forward_log.csv
python3 analysis/predict_all.py --check 2026-10-21    # rebuild a logged date and compare with the log
python3 analysis/ml_model.py predict --date 2026-10-24 --before 2026-10-24   # ml_* sets (needs lightgbm)
```

`predict_all.py` uses the analysis code itself (score_leads, update_picks,
astro_model, manual_formula) and the same parameter values. Sets without a
suffix are frozen at their original cutoff (vedic / chinese / both: results
before 11 Oct 2026; the rest: before 17 Oct 2026); `_upd` sets use all results
before the draw. `--check` on 18 and 21 Oct reproduces every logged non-ML set.

'''
s=s.replace("## Findings", sec+"## Findings",1)
open('README.md','w').write(s)
EOF
git add -A README.md analysis && git commit -qm "predict_all.py: one generator for every logged pick set, with --check against forward_log; astro_model --before cutoff (no leak)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01D1qpw2EvSFGTDFzcosUbdt" && git push -q -u origin claude/4d-results-scraper-9ptbd5; git status -sb | head -3
```
