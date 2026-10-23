# QA Results — Dallas Stars Forecasting Project

Generated 2026-10-23. These files verify implementation rules; they are not
certainty about the real season, and they are not an instructor signoff.

## Commands run
```
source .venv/bin/activate
python -m stars_forecast collect-data   -> exit 1 (source blocker recorded)
python -m stars_forecast validate-data  -> exit 1 (real processed inputs missing)
python -m stars_forecast data-report    -> exit 0 (docs/data-report.md regenerated)
python -m stars_forecast run-all ...    -> exit 1 without real data (clear message)
python -m pytest --junitxml=outputs/qa/test-results.xml  -> 25 passed
```

## QA artifacts
- outputs/qa/test-results.xml — pytest JUnit report, 25 tests, 0 failures
- outputs/qa/data-validation.json — validation contracts; all 8 required processed
  inputs missing (source blocker), 0/9 checks passed, documented honestly
- docs/data-report.md — evidence-based data report documenting the blocker and
  completeness checklist A-G
- tests/fixtures/* — SYNTHETIC fixtures only, labeled `source = "synthetic_fixture"`

## Test results (25 passed)
Data contracts: 82-game season, unique game IDs, regular-season filtering,
no missing mandatory values, valid units, result categories {REG/OT/SO},
season accounting W+RL+OTL=82, points=2W+OTL, points in [0,164], no
2026-27 rows in fitting data, gamelog-to-totals reconciliation under the
regulation convention, missing-file handling.
Model: season accounting, fixed-seed reproducibility, different-seed
difference, positive-rate validation, hand-built REG/OT/SO result-category
fixture, shootout decision-goal exclusion, Poisson fit on synthetic data
(lam > 0, p_ot_win in [0,1], GOF p in [0,1], tied-games > 0), summary and
threshold-probability structure.
Scenarios: offense-only isolation, zero-change equals baseline, roster
projection units (projected goals = prior goals/prior games × future games ×
role factor ÷ 82), scenario structure, interval ordering (p95 contains p80),
monotonicity sanity with common random numbers (noise-tolerant).
Backtest: train/eval separation (2024-25 train, 2025-26 eval-only), metric
structure, runs without actuals.

## Limitations (honest disclosure)
- No real NHL/Hockey-Reference data reachable from this environment
  (SSL/connection failure on every attempted URL, bounded retries). Datasets
  A-G are not collected; the model has not run on observed 2025-26 data.
- Forecasts, figures, thresholds, and the backtest cannot complete until
  validated real CSVs exist under data/processed/.
- Synthetic fixtures verify code contracts only and are never reported as
  observed data.
- One backtest (when data is available) does not establish general forecasting
  accuracy; post-backtest revisions will be recorded separately.

## Defect / fix history
1. pytest-xml 3.x incompatible with pytest 8 (`Notset` import) — removed
   pytest-xml; core pytest --junitxml used instead.
2. `PoissonModel.fit()` mixed length-82 and length-(tied games) boolean arrays
   when estimating OT/SO win probability — fixed by indexing finish types on
   the tied subset only.
3. `PoissonModel.gof` pooled-chi-square loop referenced an undefined loop
   variable — rewrote with enumerate and flush-on-last-category pooling.
4. `simulate_season` signature requires `p_ot_win` — tests updated to pass it
   explicitly.