#!/usr/bin/env python3
"""Import 4dmoon.com past-results pages fetched through TinyFish into data/*.csv.

TinyFish's fetch_content (format="html") returns the page's result tables
with CSS classes stripped, which scraper.py's parser relies on. This module
parses that cleaned HTML instead. Use it when 4dmoon.com cannot be reached
directly (e.g. from a sandbox whose proxy blocks the site):

  1. Fetch https://www.4dmoon.com/past-results/YYYY-MM-DD with TinyFish
     fetch_content, format "html" (up to 10 dates per call).
  2. Save each result's "text" to a file, or save the whole JSON response.
  3. python3 tinyfish_import.py page1.html [page2.html ...]
     python3 tinyfish_import.py response.json

Existing rows are kept; dates already present for an operator are not
duplicated. Special slots shown as ---- are omitted, as in scraper.py.
"""

import datetime as dt
import json
import re
import sys

import scraper

TITLE_RE = re.compile(r"(Magnum 4D|SportsToto 4D|Damacai 1\+3D)\s*<br\s*/?>\s*\((\w{3})\)\s*(\d{2}-\w{3}-\d{4})")
BLOCK_START = "<table><tr><td><table><tr><td></td><td>"
NUM_RE = re.compile(r"<td>\s*(\d{4}|-{4})\s*</td>")


def parse(text):
    """Rows (dicts with scraper.FIELDS) for Magnum, Sports Toto and Da Ma Cai in one page."""
    rows = []
    for m in TITLE_RE.finditer(text):
        title, day, date_s = m.groups()
        operator = scraper.OPERATORS[title][0]
        date = dt.datetime.strptime(date_s, "%d-%b-%Y").date()
        end = text.find(BLOCK_START, m.end())
        block = text[m.end(): end if end != -1 else len(text)]
        i_sp, i_co = block.find(">Special<"), block.find(">Consolation<")
        if i_sp == -1 or i_co == -1:
            raise ValueError(f"{title} {date}: Special/Consolation section not found")
        top = [x for x in NUM_RE.findall(block[:i_sp]) if x != "----"][:3]
        special = [x for x in NUM_RE.findall(block[i_sp:i_co]) if x != "----"]
        consolation = [x for x in NUM_RE.findall(block[i_co:]) if x != "----"][:10]
        if len(top) != 3 or len(consolation) != 10 or len(special) > 13:
            raise ValueError(f"{title} {date}: unexpected counts {len(top)}/{len(special)}/{len(consolation)}")
        for prize, nums in (("1st", top[:1]), ("2nd", top[1:2]), ("3rd", top[2:3]),
                            ("Special", special), ("Consolation", consolation)):
            for n in nums:
                rows.append({"date": date.isoformat(), "day": date.strftime("%a"), "operator": operator,
                             "prize": prize, "4d_number": n})
    return rows


def texts_from(path):
    raw = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        doc = json.loads(raw)
        return [r["text"] for r in doc.get("results", [doc]) if r.get("text")]
    return [raw]


def merge(new_rows):
    existing = scraper.load_existing()
    added = {}
    for op in existing:
        have = {r["date"] for r in existing[op]}
        fresh = [r for r in new_rows if r["operator"] == op and r["date"] not in have]
        existing[op].extend(fresh)
        added[op] = sorted({r["date"] for r in fresh})
    scraper.write_csvs(existing)
    return added


def main(paths):
    rows = [r for p in paths for t in texts_from(p) for r in parse(t)]
    if not rows:
        print("no Magnum / Sports Toto / Da Ma Cai results found")
        return
    for op, dates in merge(rows).items():
        print(f"  {op}: added {', '.join(dates) if dates else 'nothing new'}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
