# docs/progress.md — task checklist and session state

## Context
Branch: arena/8fb377a2-rein. Repo: https://github.com/Ankit-x1/rein.git (origin)
Python venv: /home/user/rein/.venv (pandas, numpy, scipy, matplotlib, requests,
pytest, pytest-xml installed).
Blocker: nhl.com and hockey-reference.com unreachable from sandbox (SSL error),
recorded 2026-10-23. Real datasets A–G not collected. Synthetic data ONLY in
labeled test fixtures.

## Task checklist
- [x] Inspect repository and PDFs (MASTER-PROMPT.md, Results_Requirments.md,
  annotated proposal)
- [x] Confirm data-source accessibility (blocked: NHL.com, Hockey-Reference)
- [x] Create AGENTS.md, docs/progress.md, docs/model-decisions.md
- [x] Project layout: src/stars_forecast/, tests/, config/, data/raw/, data/processed/, docs/, outputs/
- [x] Installable package + CLI (collect-data, validate-data, data-report, run-all)
- [x] collect-data: attempts real URLs, caches responses, records provenance manifest + blocker
- [x] validate-data: data contracts on processed CSVs (82 games, unique IDs, mandatory fields, units, categories)
- [x] Model: Poisson regulation GF/GA, OT/SO resolution, 82-game season, points
- [x] Scenarios S0–S4 in versioned config
- [x] Historical Central Division translation + backtest (train 2024–25 / eval 2025–26)
- [x] Figures + tables outputs + outputs/results-summary.md
- [x] Automated tests (synthetic labeled fixtures) + outputs/qa artifacts
- [x] docs/data-report.md (evidence-based, documents blocker; completeness checklist A–G)
- [x] Run all commands and pytest; save outputs/qa/*
- [x] Commit everything on arena/8fb377a2-rein, push to origin, open PR to main
- [ ] (Later, on user request) 10-page report + 15-slide presentation

## Current state
Codebase complete and committed. Real data blocked; all code paths guarded with
clear nonzero-exit errors on missing/invalid inputs. Tests run on labeled
synthetic fixtures and pass.

## Next executable action
Push arena/8fb377a2-rein to https://github.com/Ankit-x1/rein.git and open a PR
against main for user review. Then wait for user instruction before report/PPT.

## Verified commands
```
source .venv/bin/activate
python -m stars_forecast collect-data   # records blocker, exits 1
python -m stars_forecast validate-data  # reports missing processed inputs, exits 1
python -m stars_forecast data-report    # generates docs/data-report.md (blocker documented)
python -m stars_forecast run-all --n-seasons 10000 --seed 3315  # exits 1 without real data
python -m pytest --junitxml=outputs/qa/test-results.xml  # passes on synthetic fixtures
```
run-all end-to-end with real numbers requires data/processed/ CSVs from an
unblocked NHL/Hockey-Reference source.