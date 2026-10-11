# 4DPrediction

Historical 4D results for Malaysia's three main operators, scraped from
[4dmoon.com](https://www.4dmoon.com/past-results).

## Data

| File | Operator |
|------|----------|
| `data/magnum.csv` | Magnum 4D |
| `data/sportstoto.csv` | Sports Toto 4D |
| `data/damacai.csv` | Da Ma Cai 1+3D |

Columns: `date` (YYYY-MM-DD), `day` (Mon..Sun), `operator`, `prize`
(`1st`, `2nd`, `3rd`, `Special`, `Consolation`), `4d_number` (kept as text so
leading zeros survive). Special slots shown as `----` on the site (numbers
that moved up to a top prize) are omitted, so a draw may have fewer than 10
or 13 Special rows.

## Updating

```sh
python3 scraper.py          # fetch draws since the latest saved date
python3 scraper.py --full   # rebuild everything from April 1985
```

Standard library only (Python 3.9+). Downloaded pages are cached in `.cache/`.
