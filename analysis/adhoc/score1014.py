import sys, re
sys.path.insert(0, "/tmp/claude-0/-home-user/4d3b52ef-651f-53fd-9445-0b98be50b85b/scratchpad")
from res_1014 import RES
BIG = {"1st": 2500, "2nd": 1000, "3rd": 500, "Special": 180, "Consolation": 60}
R = RES["2026-10-14"]
PICKS = {
 "S7 digit formula (top 10)": {"Magnum": "6599 9599 5599 1599 6899 0599 6596 9596 6549 5899", "Sports Toto": "7597 5524 7594 0597 5527 5594 0594 7524 5597 5994", "Da Ma Cai": "5591 5594 5592 5097 6594 6591 5094 5597 5091 5092"},
 "S8 Vedic formula (top 10)": {"Magnum": "5265 7492 7294 7429 5228 5526 5256 5562 7249 6166", "Sports Toto": "7206 6207 7996 9796 0726 0267 6997 6799 2706 9697", "Da Ma Cai": "6704 0764 6720 6740 6702 6799 6834 8795 0726 2794"},
 "S8 Chinese formula (top 10)": {"Magnum": "0992 0403 2834 3824 8607 4823 0929 9029 2909 0867", "Sports Toto": "8142 0826 8726 8421 1494 2394 1824 7862 0403 5723", "Da Ma Cai": "9091 1891 8840 0992 2941 9029 0991 2777 7727 5758"},
 "S8 Vedic+Chinese (top 10)": {"Magnum": "3044 4043 3440 6798 7997 0799 0443 5526 7909 6793", "Sports Toto": "9796 8807 7206 8708 0788 7260 7808 0627 6207 9967", "Da Ma Cai": "2093 0799 0293 9032 3092 6395 7895 0791 0392 2390"},
 "S10 manual v1, buggy (top 5)": {op: "9999 9989 9899 8999 9889" for op in R},
 "S10 manual v2, corrected (top 5)": {op: "8796 8726 8799 0796 8729" for op in R},
}
# ML picks from the predict log
for line in open(sys.argv[1]):
    m = re.match(r"\s+(\S+)\s+(Magnum|Sports Toto|Da Ma Cai)\s+([\d ]+)$", line.rstrip())
    if m:
        PICKS.setdefault(f"S9 {m.group(1)} (top 10)", {})[m.group(2)] = m.group(3).strip()
GROUP = lambda n: "".join(sorted(n))
print(f"{'Formula':<34} {'picks':>5} {'straight':>9} {'exp':>6} {'i-Box':>6} {'exp':>6}  Big RM back / staked   details")
for name, ops in PICKS.items():
    npk = st = ib = pay = 0; est = eib = 0.0; det = []
    for op, s in ops.items():
        win = {n: p for p, v in R[op].items() for n in v.split()}
        groups = {GROUP(w) for w in win}
        from itertools import permutations
        ib_numbers = {"".join(q) for w in win for q in permutations(w)} - set(win)
        for n in s.split():
            npk += 1
            est += len(win) / 10000
            eib += len(ib_numbers) / 10000
            if n in win:
                st += 1; pay += BIG[win[n]]; det.append(f"{op} {n} {win[n]}")
            elif GROUP(n) in groups:
                ib += 1; det.append(f"{op} {n}~i-Box of {[w for w in win if GROUP(w)==GROUP(n)][0]} ({[win[w] for w in win if GROUP(w)==GROUP(n)][0]})")
    print(f"{name:<34} {npk:>5} {st:>9} {est:>6.2f} {ib:>6} {eib:>6.2f}  RM{pay} / RM{npk}   {'; '.join(det) or '-'}")
