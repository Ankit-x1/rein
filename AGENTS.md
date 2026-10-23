# AGENTS.md — Dallas Stars 2026–27 Forecasting Project

## Purpose
Probabilistic forecast of the Dallas Stars' 2026–27 regular season using completed
NHL data through the end of 2025–26. Independent Poisson regulation goal-for /
goal-against submodels + Monte Carlo 82-game seasons (>= 10,000 seasons per
scenario), offensive/defensive sensitivity, personnel scenarios, historical
Central Division point translation, and a 2024–25 -> 2025–26 backtest.

## Data cutoff
Model-fitting cutoff: end of the 2025–26 regular season. No 2026–27 game
results may be used to fit the model. The initial 2026–27 roster may be used
for scenario context only.

## BLOCKER (data access, recorded 2026-10-23)
The sandbox cannot reach nhl.com or hockey-reference.com (SSL/connection
failure on every attempt). Real datasets A–G from the proposal/data plan are
therefore NOT collected. No real data appears in data/raw/, data/processed/,
forecast results, or docs/data-report.md. Synthetic data is used ONLY in
clearly labeled test fixtures under tests/fixtures/.
Until a real NHL/Hockey-Reference source is reachable:
- `collect-data` records the blocker and exits nonzero.
- `validate-data` / `data-report` report missing real inputs and the blocker.
- `run-all` exits nonzero with a clear message (no silent demo results).

## Scientific constraints
- Three goal definitions preserved: displayed final score, final hockey goals
  excluding shootout decision increments, regulation goals at 60 minutes.
- Poisson fit uses regulation goals only; shootout increments excluded.
- OT/SO win probability estimated empirically from games tied after regulation
  (never an unstated 50% fallback).
- Points = 2*W + OTL; W + regulation_L + OTL = 82 per 82-game season.
- Historical Central translation: "top-three point-level probability," not a
  playoff-qualification guarantee.

## Commands (venv at .venv)
```
source .venv/bin/activate
python -m stars_forecast collect-data
python -m stars_forecast validate-data
python -m stars_forecast data-report
python -m stars_forecast run-all --n-seasons 10000 --seed 3315
python -m pytest --junitxml=outputs/qa/test-results.xml
```
`run-all` requires validated real inputs under data/processed/.

## Completion rules
Real datasets with provenance + regenerated data report + source reconciliation
or disclosed blockers + installable CLI + all scenario families + figures +
backtest + passing automated checks + tested README reproduction path. No
slides or final academic report yet (user will request those later).

## Repository
Remote: https://github.com/Ankit-x1/rein.git (origin). Work on branch
arena/8fb377a2-rein; push only to that branch. Many small commits, then a PR
from arena/8fb377a2-rein to main for review.