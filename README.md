# rein — Dallas Stars 2026–27 Season Forecasting Model

Probabilistic forecast of the Dallas Stars' 2026–27 regular season from
completed NHL data through the end of 2025–26. Independent Poisson
regulation goal-for/goal-against submodels plus Monte Carlo 82-game seasons
(>= 10,000 seasons per scenario), offensive/defensive sensitivity, personnel
scenarios, historical Central Division point translation, and a
2024–25 -> 2025–26 backtest.

Built per the project proposal (annotated-MATH_331520Project20Updated.md)
and MASTER-PROMPT.md instructions. Small, student-team-readable Python:
pandas, NumPy, SciPy, Matplotlib, requests, pytest. No web app, dashboard,
database, or skills workflow.

## Status (2026-10-23)
**Real data is blocked.** The sandbox cannot reach nhl.com or
hockey-reference.com (SSL/connection failure). Real datasets A–G from the
proposal are therefore not collected, and no real or synthetic data appears in
forecast results or the data report. Synthetic data is used only in clearly
labeled test fixtures under `tests/fixtures/`. The CLI is complete and fails
with a clear nonzero exit when validated real inputs are missing.

## Layout
```
src/stars_forecast/   package + CLI (collect-data, validate-data, data-report, run-all)
tests/                pytest suite on labeled synthetic fixtures
config/               versioned scenario parameters (scenarios.json)
data/raw/             unchanged source downloads (cached by collect-data)
data/processed/       cleaned canonical CSVs
docs/                 progress.md, model-decisions.md, data-report.md
outputs/              figures/, tables/, qa/ (results-summary.md, test results)
```

## Install (fresh Python virtual environment)
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .        # optional: makes the `stars-forecast` script available
```

## Commands
```
source .venv/bin/activate

# 1. Attempt real downloads from NHL.com / Hockey-Reference, cache raw responses,
#    write the source manifest. Exits nonzero with a clear message if sources
#    are unreachable (current blocker).
python -m stars_forecast collect-data

# 2. Validate cleaned CSVs under data/processed/ (contracts: 82 games, unique
#    game IDs, mandatory fields, units, result categories, points formula).
python -m stars_forecast validate-data

# 3. Regenerate docs/data-report.md from collected data + validation evidence.
python -m stars_forecast data-report

# 4. Full run: diagnostics, scenarios S0-S4, backtest, historical translation,
#    figures, tables, run manifest, results summary. Requires validated real
#    inputs in data/processed/ (exits nonzero otherwise).
python -m stars_forecast run-all --n-seasons 10000 --seed 3315

# 5. Automated QA (runs offline on synthetic fixtures).
python -m pytest --junitxml=outputs/qa/test-results.xml
```

## Data licensing
Do not commit NHL.com/Hockey-Reference snapshots publicly without checking each
source's redistribution terms. `data/raw/` and `data/processed/` are excluded
from commits by `.gitignore` unless you explicitly add validated inputs.

## Repo
https://github.com/Ankit-x1/rein.git — branch `arena/8fb377a2-rein`.
