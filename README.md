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

If 4dmoon.com cannot be reached directly, fetch the pages with TinyFish
(`fetch_content`, format `html`) and import them:

```sh
python3 tinyfish_import.py page.html [more.html ...]   # or the saved JSON response
python3 -m unittest tests/test_tinyfish_import.py
```

## Making picks for a draw (use these; do not re-implement)

```
python3 analysis/predict_all.py 2026-10-24            # every logged pick set, from results before that date
python3 analysis/predict_all.py 2026-10-24 --log      # also append them to analysis/forward_log.csv
python3 analysis/predict_all.py --check 2026-10-21    # rebuild a logged date and compare with the log
python3 analysis/ml_model.py predict --date 2026-10-24 --before 2026-10-24   # ml_* sets (needs lightgbm; --before 2026-10-17 reproduces the logged ones)
```

`predict_all.py` uses the analysis code itself (score_leads, update_picks,
astro_model, manual_formula) and the same parameter values. Sets without a
suffix are frozen at their original cutoff (vedic / chinese / both: results
before 11 Oct 2026; the rest: before 17 Oct 2026); `_upd` sets use all results
before the draw. `--check` on 18 and 21 Oct reproduces every logged non-ML set.

## Findings

See [analysis/FINDINGS.md](analysis/FINDINGS.md) for a summary of every test, the ranked leads and live checks.

The full question-and-answer log of the analysis is in [docs/conversation.md](docs/conversation.md).
