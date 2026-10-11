#!/usr/bin/env python3
"""Scrape past 4D results (Magnum, Sports Toto, Da Ma Cai) from www.4dmoon.com.

Each calendar day has a page at https://www.4dmoon.com/past-results/YYYY-MM-DD
listing every operator that drew on that day. This script walks every day in a
range, extracts the 1st/2nd/3rd, Special and Consolation numbers for the three
West Malaysian 4D operators, and writes one CSV per operator:

    data/magnum.csv, data/sportstoto.csv, data/damacai.csv

Columns: date, day, operator, prize, 4d_number

Usage:
    python3 scraper.py                 # update: re-scan from the latest date already saved
    python3 scraper.py --full          # rebuild the whole history (from 1985-04-01)
    python3 scraper.py --start 2024-01-01 --end 2024-12-31

Only the Python standard library is used. Raw pages are cached under
.cache/pages/ so interrupted runs resume without re-downloading.
"""

import argparse
import concurrent.futures
import csv
import datetime as dt
import html
import os
import re
import sys
import time
import urllib.error
import urllib.request

BASE_URL = "https://www.4dmoon.com/past-results/"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) 4DPrediction-scraper"
# Magnum's first draw on the site is #001/85 in late April 1985.
EARLIEST_DATE = dt.date(1985, 4, 1)

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "data")
CACHE_DIR = os.path.join(ROOT, ".cache", "pages")

# Block title on the page -> (output operator name, CSV file stem).
OPERATORS = {
    "Magnum 4D": ("Magnum", "magnum"),
    "SportsToto 4D": ("Sports Toto", "sportstoto"),
    "Damacai 1+3D": ("Da Ma Cai", "damacai"),
}
FIELDS = ["date", "day", "operator", "prize", "4d_number"]
PRIZE_ORDER = {"1st": 0, "2nd": 1, "3rd": 2, "Special": 3, "Consolation": 4}

BLOCK_RE = re.compile(r'<div class="mbx">(.*?)</table></div>', re.S)
TITLE_RE = re.compile(
    r'style="width:75%">\s*([^<]+?)\s*<br><span class="rdd">\((\w+)\)\s*(\d{2}-\w{3}-\d{4})'
)
# Section labels and number cells, in document order.
TOKEN_RE = re.compile(r'class="(rpl|rtn|rbn)"[^>]*>(.*?)</td>', re.S)
NUMBER_RE = re.compile(r"^\d{4}$")


def fetch(day, retries=5):
    """Return the HTML for one day, using the on-disk cache when possible."""
    path = os.path.join(CACHE_DIR, f"{day.isoformat()}.html")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    req = urllib.request.Request(BASE_URL + day.isoformat(), headers={"User-Agent": USER_AGENT})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8", errors="replace")
            break
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if attempt == retries - 1:
                raise RuntimeError(f"{day}: {e}") from e
            time.sleep(2 ** attempt)
    # Cache only past days; today's page may still be incomplete.
    if day < dt.date.today():
        os.makedirs(CACHE_DIR, exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(body)
        os.replace(tmp, path)
    return body


def parse(page, requested):
    """Extract 4D rows for the tracked operators from one day's page."""
    rows = []
    for block in BLOCK_RE.findall(page):
        m = TITLE_RE.search(block)
        if not m or m.group(1) not in OPERATORS:
            continue
        operator, _ = OPERATORS[m.group(1)]
        draw_date = dt.datetime.strptime(m.group(3), "%d-%b-%Y").date()
        if draw_date != requested:
            print(f"warning: {requested} page shows {operator} draw dated {draw_date}", file=sys.stderr)
        day_name = m.group(2)

        top_labels = []  # pending 1st/2nd/3rd labels, filled by following rtn cells
        section = None
        for cls, raw in TOKEN_RE.findall(block[m.end():]):
            text = html.unescape(re.sub(r"<[^>]+>", "", raw)).strip()
            if cls == "rpl":
                label = text.replace(" Prize", "")
                if label in ("1st", "2nd", "3rd"):
                    top_labels.append(label)
                    section = None
                elif label in ("Special", "Consolation"):
                    section = label
                else:
                    section = None
                continue
            if cls == "rtn" and top_labels:
                prize = top_labels.pop(0)
            elif cls == "rbn" and section:
                prize = section
            else:
                continue
            if NUMBER_RE.match(text):  # skips "----" placeholders and blanks
                rows.append({
                    "date": draw_date.isoformat(),
                    "day": day_name,
                    "operator": operator,
                    "prize": prize,
                    "4d_number": text,
                })
    return rows


def load_existing():
    rows = {}
    for operator, stem in OPERATORS.values():
        path = os.path.join(DATA_DIR, f"{stem}.csv")
        if os.path.exists(path):
            with open(path, newline="", encoding="utf-8") as f:
                rows[operator] = list(csv.DictReader(f))
        else:
            rows[operator] = []
    return rows


def write_csvs(rows_by_operator):
    os.makedirs(DATA_DIR, exist_ok=True)
    for operator, stem in OPERATORS.values():
        rows = rows_by_operator.get(operator, [])
        rows.sort(key=lambda r: (r["date"], PRIZE_ORDER[r["prize"]]))
        path = os.path.join(DATA_DIR, f"{stem}.csv")
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
        draws = len({r["date"] for r in rows})
        print(f"{path}: {len(rows)} rows, {draws} draws")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", type=dt.date.fromisoformat, help="first date (YYYY-MM-DD)")
    ap.add_argument("--end", type=dt.date.fromisoformat, help="last date (default: yesterday)")
    ap.add_argument("--full", action="store_true", help="rescan the whole history")
    ap.add_argument("--workers", type=int, default=4, help="parallel requests (default 4)")
    args = ap.parse_args()

    existing = {} if args.full else load_existing()
    end = args.end or dt.date.today() - dt.timedelta(days=1)
    if args.start:
        start = args.start
    elif existing and any(existing.values()):
        latest = max(r["date"] for rows in existing.values() for r in rows)
        start = dt.date.fromisoformat(latest) - dt.timedelta(days=7)
    else:
        start = EARLIEST_DATE

    days = [start + dt.timedelta(days=i) for i in range((end - start).days + 1)]
    print(f"Scanning {len(days)} days: {start} .. {end}")

    scanned = {d.isoformat() for d in days}
    merged = {
        op: [r for r in rows if r["date"] not in scanned] for op, rows in existing.items()
    }
    # (operator, date) of every draw already collected, so a draw that shows up on
    # more than one page is kept once. Numbers within a draw are kept as published,
    # since old draws occasionally list the same number twice.
    seen_draws = {(op, r["date"]) for op, rows in merged.items() for r in rows}
    failed = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(fetch, d): d for d in days}
        for i, fut in enumerate(concurrent.futures.as_completed(futures), 1):
            day = futures[fut]
            try:
                page_rows = parse(fut.result(), day)
            except Exception as e:  # keep going; report at the end
                failed.append((day, e))
                page_rows = []
            new_draws = {(r["operator"], r["date"]) for r in page_rows} - seen_draws
            for row in page_rows:
                if (row["operator"], row["date"]) in new_draws:
                    merged.setdefault(row["operator"], []).append(row)
            seen_draws |= new_draws
            if i % 500 == 0:
                print(f"  {i}/{len(days)} days processed")

    write_csvs(merged)
    if failed:
        print(f"{len(failed)} days failed:", file=sys.stderr)
        for day, e in failed[:20]:
            print(f"  {day}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
