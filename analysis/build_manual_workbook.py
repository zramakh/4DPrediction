#!/usr/bin/env python3
"""Build analysis/manual_formula.xlsx from analysis/manual_formula.json.

Run from the repo root after manual_formula.py:  python3 analysis/build_manual_workbook.py
"""

import datetime as dt
import json
import os

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = json.load(open(os.path.join(ROOT, "analysis", "manual_formula.json")))
OUT = os.path.join(ROOT, "analysis", "manual_formula.xlsx")

F = "Arial"
BOLD = Font(name=F, bold=True)
NORM = Font(name=F)
BLUE = Font(name=F, color="0000FF")
GREEN = Font(name=F, color="008000")
TITLE = Font(name=F, bold=True, size=14)
YELLOW = PatternFill("solid", fgColor="FFFF00")
GREY = PatternFill("solid", fgColor="EEEEEE")
BEST = PatternFill("solid", fgColor="C6EFCE")
THIN = Border(*(Side(style="thin", color="BBBBBB"),) * 4)
PARAMS = list(J["weights"])
NICE = {"year_yinyang": "Chinese year yin/yang", "venus_combust": "Venus combust (Vedic)",
        "jupiter_combust": "Jupiter combust (Vedic)", "masa": "Masa, lunar month (Vedic)",
        "year_stem": "Chinese year heavenly stem", "lunar_day": "Chinese lunar day"}

wb = Workbook()

# ---------------------------------------------------------------- Tables
tb = wb.active
tb.title = "Tables"
head = ["Parameter", "Value", "Key"] + [f"P{p + 1} d{d}" for p in range(4) for d in range(10)]
for c, h in enumerate(head, 1):
    tb.cell(1, c, h).font = BOLD
r = 2
for f in PARAMS:
    for v, grid in J["tables"][f].items():
        tb.cell(r, 1, f).font = NORM
        tb.cell(r, 2, str(v)).font = BLUE
        tb.cell(r, 3, f'=A{r}&"|"&B{r}').font = NORM
        for p in range(4):
            for d in range(10):
                tb.cell(r, 4 + p * 10 + d, int(grid[p][d])).font = BLUE
        r += 1
TB_LAST = r - 1
tb.cell(r + 1, 1, "Points = round(10000 x weight x log[ share of digit d at position p among past winners on dates "
                  "with this value / its overall share ]), from all Magnum, Sports Toto and Da Ma Cai draws "
                  f"1985 to {J['tables_all_draws_to']} (each number once per draw, smoothed with 50 pseudo-draws). "
                  "Source: data/*.csv, analysis/manual_formula.py.").font = Font(name=F, italic=True)
tb.freeze_panes = "D2"
for c in range(1, 4):
    tb.column_dimensions[L(c)].width = 18
for c in range(4, 44):
    tb.column_dimensions[L(c)].width = 6

# ---------------------------------------------------------------- Calendar
ca = wb.create_sheet("Calendar")
ch = ["Date", "Weekday"] + PARAMS
for c, h in enumerate(ch, 1):
    ca.cell(1, c, h).font = BOLD
for i, row in enumerate(J["calendar"], 2):
    ca.cell(i, 1, dt.date.fromisoformat(row["date"])).number_format = "yyyy-mm-dd"
    ca.cell(i, 1).font = BLUE
    ca.cell(i, 2, row["weekday"]).font = BLUE
    for c, f in enumerate(PARAMS, 3):
        ca.cell(i, c, str(row[f])).font = BLUE
CA_LAST = len(J["calendar"]) + 1
ca.cell(CA_LAST + 2, 1, "Parameter values at 19:00 Malaysia time, computed by analysis/almanac.py "
                        "(Meeus ephemeris, Lahiri ayanamsa, Chinese lunisolar calendar).").font = Font(name=F, italic=True)
ca.freeze_panes = "A2"
for c in range(1, len(ch) + 1):
    ca.column_dimensions[L(c)].width = 16

# ---------------------------------------------------------------- Predict
pr = wb.create_sheet("Predict", 0)
pr["A1"] = "4D manual formula: top 5 numbers for a draw date"
pr["A1"].font = TITLE
pr["A3"] = "Draw date"
pr["A3"].font = BOLD
pr["B3"] = dt.date(2026, 10, 18)
pr["B3"].number_format = "yyyy-mm-dd"
pr["B3"].fill = YELLOW
pr["B3"].font = BLUE
pr["B3"].comment = Comment(f"Type any date from {J['calendar'][0]['date']} to {J['calendar'][-1]['date']} "
                           "(the Calendar sheet). Example: 2026-10-18.", "Claude")
dv = DataValidation(type="date", operator="between", formula1=f"Calendar!$A$2", formula2=f"Calendar!$A${CA_LAST}",
                    showErrorMessage=True, error="Date must be in the Calendar sheet range.")
pr.add_data_validation(dv)
dv.add("B3")
pr["C3"] = '=IFERROR(INDEX(Calendar!$B$2:$B$%d,MATCH($B$3,Calendar!$A$2:$A$%d,0)),"date not in Calendar")' % (CA_LAST, CA_LAST)
pr["C3"].font = GREEN
pr["E3"] = "Yellow cell = the only input. Everything else is calculated."
pr["E3"].font = Font(name=F, italic=True)

pr["A5"] = "Step 1: the date's parameters"
pr["A5"].font = BOLD
for c, h in enumerate(["Parameter", "Value on this date", "Lookup key"], 1):
    pr.cell(6, c, h).font = BOLD
    pr.cell(6, c).fill = GREY
PROW = {}
for i, f in enumerate(PARAMS):
    r = 7 + i
    PROW[f] = r
    pr.cell(r, 1, NICE.get(f, f)).font = NORM
    col = L(3 + i)
    pr.cell(r, 2, f'=IFERROR(INDEX(Calendar!${col}$2:${col}${CA_LAST},MATCH($B$3,Calendar!$A$2:$A${CA_LAST},0)),"")').font = GREEN
    pr.cell(r, 3, f'="{f}|"&B{r}').font = NORM

# helper block: points looked up per parameter (rows 16-21), 40 columns from D
pr["A15"] = "Step 2: points from each parameter's table (position 1-4, digit 0-9)"
pr["A15"].font = BOLD
for p in range(4):
    for d in range(10):
        c = 4 + p * 10 + d
        pr.cell(16, c, f"P{p + 1} {d}").font = BOLD
        pr.cell(16, c).fill = GREY
for i, f in enumerate(PARAMS):
    r = 17 + i
    pr.cell(r, 1, NICE.get(f, f)).font = NORM
    for k in range(40):
        c = 4 + k
        pr.cell(r, c, f"=IFERROR(INDEX(Tables!${L(4 + k)}$2:${L(4 + k)}${TB_LAST},"
                      f"MATCH($C${PROW[f]},Tables!$C$2:$C${TB_LAST},0)),0)").font = GREEN
HELP_FIRST, HELP_LAST = 17, 16 + len(PARAMS)

# summary grid 4 x 10
G0 = HELP_LAST + 3
pr.cell(G0 - 1, 1, "Step 3: total points = sum of the rows above (best digit per position highlighted)").font = BOLD
pr.cell(G0, 1, "Position").font = BOLD
for d in range(10):
    pr.cell(G0, 2 + d, d).font = BOLD
    pr.cell(G0, 2 + d).fill = GREY
pr.cell(G0, 13, "Best digit").font = BOLD
pr.cell(G0, 14, "2nd best").font = BOLD
pr.cell(G0, 36, "Tie-break helper (points + digit/1,000,000)").font = Font(name=F, italic=True, color="999999")
for p in range(4):
    r = G0 + 1 + p
    pr.cell(r, 1, f"Position {p + 1}").font = BOLD
    for d in range(10):
        hc = L(4 + p * 10 + d)
        pr.cell(r, 2 + d, f"=SUM({hc}{HELP_FIRST}:{hc}{HELP_LAST})").font = NORM
        pr.cell(r, 2 + d).number_format = "0"
        pr.cell(r, 2 + d).border = THIN
        # tie-break copy (columns AJ:AS): equal points -> the higher digit, as in manual_formula.py
        pr.cell(r, 36 + d, f"={L(2 + d)}{r}+{d}/1000000").font = Font(name=F, color="999999")
    rng = f"$AJ{r}:$AS{r}"
    pr.cell(r, 13, f"=MATCH(MAX({rng}),{rng},0)-1").font = BOLD
    pr.cell(r, 14, f"=MATCH(LARGE({rng},2),{rng},0)-1").font = NORM
GRID = {p: G0 + 1 + p for p in range(4)}

# 16 combinations
C0 = G0 + 7
pr.cell(C0 - 1, 1, "Step 4: the 16 combinations of best / 2nd-best digits (0 = best, 1 = 2nd best)").font = BOLD
for c, h in enumerate(["#", "Pos1", "Pos2", "Pos3", "Pos4", "Number", "Total points"], 1):
    pr.cell(C0, c, h).font = BOLD
    pr.cell(C0, c).fill = GREY
for i in range(16):
    r = C0 + 1 + i
    bits = [(i >> (3 - p)) & 1 for p in range(4)]
    pr.cell(r, 1, i + 1).font = NORM
    dig_refs = []
    for p in range(4):
        g = GRID[p]
        pr.cell(r, 2 + p, f"=IF({bits[p]}=0,$M${g},$N${g})").font = NORM
        dig_refs.append(f"{L(2 + p)}{r}")
    pr.cell(r, 6, "=TEXT(" + "*1000+".join(dig_refs[:1]) + "*1000+" + dig_refs[1] + "*100+" + dig_refs[2] +
            "*10+" + dig_refs[3] + ',"0000")').font = NORM
    total = "+".join(f"INDEX($B${GRID[p]}:$K${GRID[p]},{dig_refs[p]}+1)" for p in range(4))
    pr.cell(r, 7, f"={total}-{sum(bits)}/1000000000-{i}/1000000000000").font = NORM
    pr.cell(r, 7).number_format = "0"
COMBO = (C0 + 1, C0 + 16)

# result
pr["P5"] = "RESULT: top 5 numbers"
pr["P5"].font = TITLE
pr["P6"] = "Rank"
pr["Q6"] = "Number"
pr["R6"] = "Points"
for c in ("P6", "Q6", "R6"):
    pr[c].font = BOLD
    pr[c].fill = GREY
for k in range(1, 6):
    r = 6 + k
    pr.cell(r, 16, k).font = BOLD
    tot = f"$G${COMBO[0]}:$G${COMBO[1]}"
    pr.cell(r, 17, f"=INDEX($F${COMBO[0]}:$F${COMBO[1]},MATCH(LARGE({tot},{k}),{tot},0))").font = Font(name=F, bold=True, size=13)
    pr.cell(r, 17).fill = BEST
    pr.cell(r, 18, f"=LARGE({tot},{k})").font = NORM
    pr.cell(r, 18).number_format = "0"
pr["P13"] = "Same numbers for Magnum, Sports Toto and Da Ma Cai (the tables pool all three)."
pr["P13"].font = Font(name=F, italic=True)
pr["P14"] = "Not a guarantee: see the 'How to use' sheet for the tested hit rate."
pr["P14"].font = Font(name=F, italic=True)
pr.column_dimensions["A"].width = 28
pr.column_dimensions["B"].width = 14
pr.column_dimensions["C"].width = 22
for c in range(4, 44):
    pr.column_dimensions[L(c)].width = 7
pr.column_dimensions["Q"].width = 12

# ---------------------------------------------------------------- How to use
hw = wb.create_sheet("How to use", 1)
t = J["forward_test_2018_2026"]
lines = [
    ("4D manual formula (Vedic + Chinese parameters)", TITLE),
    ("", NORM),
    ("How to use", BOLD),
    ("1. Go to the Predict sheet and type the draw date in the yellow cell B3.", NORM),
    ("2. Read the top 5 numbers in the green box (column Q). The steps below the date show how they are worked out.", NORM),
    ("3. To do it fully by hand: look up the date's six parameter values (Calendar sheet), find each value's row in "
     "the Tables sheet, add the six rows together column by column, take the highest digit in each position.", NORM),
    ("", NORM),
    ("The formula", BOLD),
    ("Points(position p, digit d) = sum over the 6 parameters of TABLE[parameter value on the date][p][d]", NORM),
    ("Number #1 = the digit with the most points in each of the 4 positions.", NORM),
    ("Numbers #2-#5 = the next best of the 16 combinations of each position's best and 2nd-best digit, by total points.", NORM),
    ("Parameters (chosen on 2012-2017 draws, then frozen): " + ", ".join(
        f"{NICE.get(f, f)} (weight {w})" for f, w in J["weights"].items()), NORM),
    ("", NORM),
    ("How it performed on 2018-2026 draws it had not seen (tables rebuilt each January from earlier draws only)", BOLD),
    (f"Top 5 numbers: {t['top5']['hits']} wins of any prize in {t['top5']['draws']} draws vs {t['top5']['expected']} for "
     f"random picks ({t['top5']['lift']}x, z = {t['top5']['z']}); Big Forecast return RM{t['top5']['big_return_per_RM1']} "
     "per RM1.", NORM),
    (f"Top 1 number: {t['top1']['hits']} wins vs {t['top1']['expected']} ({t['top1']['lift']}x); return "
     f"RM{t['top1']['big_return_per_RM1']} per RM1.", NORM),
    ("By operator (top 5): " + ", ".join(f"{op} {v['lift']}x" for op, v in t["top5_by_operator"].items()), NORM),
    ("", NORM),
    ("Read this before betting", BOLD),
    ("This formula performs like random picking on unseen draws. An earlier version of this workbook (points "
     "x100) looked better (1.37x), but that came from a rounding artefact: most table cells were 0 and ties were "
     "broken toward digit 9. With the tables at x10000 the result above is what is left.", NORM),
    ("Most of the six parameters change only monthly or yearly, so the picks stay similar for weeks.", NORM),
    ("Treat the numbers as a reproducible way of choosing, not as more likely winners.", NORM),
    ("Live forward test: analysis/forward_log.csv in the 4DPrediction repository.", NORM),
    ("", NORM),
    ("Legend: yellow = input cell; blue = fixed data (tables, calendar); green = looked up from another sheet; "
     "black = calculated.", Font(name=F, italic=True)),
]
for i, (text, font) in enumerate(lines, 1):
    hw.cell(i, 1, text).font = font
    hw.cell(i, 1).alignment = Alignment(wrap_text=False)
hw.column_dimensions["A"].width = 160

wb.save(OUT)
print("wrote", OUT)
