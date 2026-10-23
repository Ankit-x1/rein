# Dallas Stars 2026-27 Forecast — Data Report

_Generated 2026-10-23. Evidence-based report on collected datasets; separate from model results and the final academic report._

## Scope and cutoff
- Model-fitting data cutoff: end of the 2025-26 regular season.
- No 2026-27 game results are used to fit the model.
- Real, cited source data is required for datasets A-G; see completeness checklist below.

## Collection attempt — 2026-10-23

Attempted sources (NHL.com and Hockey-Reference per the proposal data plan):
- [A] 2025-26 Dallas team totals (NHL.com) — FAILED — SSLError: HTTPSConnectionPool(host='www.nhl.com', port=443): Max retries exceeded with url: /stats/teams?gameType=2&page=0&pageSize=50&reportType=season&seasonFrom=20252026&seasonTo=20252026 (Caused by SSLError(SSLZeroReturnError(6, 'TLS/SSL connection has been closed (EOF) (_ssl.c:992)')))
- [C] 2025-26 Dallas skater statistics (NHL.com) — FAILED — SSLError: HTTPSConnectionPool(host='www.nhl.com', port=443): Max retries exceeded with url: /stats/skaters?gameType=2&page=0&pageSize=50&reportType=season&seasonFrom=20252026&seasonTo=20252026 (Caused by SSLError(SSLZeroReturnError(6, 'TLS/SSL connection has been closed (EOF) (_ssl.c:992)')))
- [D] 2025-26 Dallas goalie statistics (NHL.com) — FAILED — SSLError: HTTPSConnectionPool(host='www.nhl.com', port=443): Max retries exceeded with url: /stats/goalies?gameType=2&page=0&pageSize=50&reportType=season&seasonFrom=20252026&seasonTo=20252026 (Caused by SSLError(SSLZeroReturnError(6, 'TLS/SSL connection has been closed (EOF) (_ssl.c:992)')))
- [B] 2025-26 Dallas team gamelog (Hockey-Reference) — FAILED — SSLError: HTTPSConnectionPool(host='www.hockey-reference.com', port=443): Max retries exceeded with url: /teams/DAL/2026_gamelog.html (Caused by SSLError(SSLZeroReturnError(6, 'TLS/SSL connection has been closed (EOF) (_ssl.c:992)')))
- [E] 2024-25 Dallas team gamelog (Hockey-Reference) — FAILED — SSLError: HTTPSConnectionPool(host='www.hockey-reference.com', port=443): Max retries exceeded with url: /teams/DAL/2025_gamelog.html (Caused by SSLError(SSLZeroReturnError(6, 'TLS/SSL connection has been closed (EOF) (_ssl.c:992)')))
- [F] NHL Central Division standings history (Hockey-Reference) — FAILED — SSLError: HTTPSConnectionPool(host='www.hockey-reference.com', port=443): Max retries exceeded with url: /leagues/NHL_2026_standings.html (Caused by SSLError(SSLZeroReturnError(6, 'TLS/SSL connection has been closed (EOF) (_ssl.c:992)')))
- [G] Dallas Stars initial 2026-27 roster announcement — FAILED — SSLError: HTTPSConnectionPool(host='www.nhl.com', port=443): Max retries exceeded with url: /stars/news/dallas-stars-announce-initial-roster-for-2026-27-season-092826 (Caused by SSLError(SSLZeroReturnError(6, 'TLS/SSL connection has been closed (EOF) (_ssl.c:992)')))

### Blocker evidence
- Recorded: 2026-10-23T21:52:02.768624+00:00
- Type: data-source-unreachable
- Detail: All NHL.com and Hockey-Reference URLs in the proposal data plan failed with SSL/connection errors after bounded retries. Real datasets A-G are not collected.
- Failed datasets: A, B, C, D, E, F, G
- Next step: Re-run collect-data from a network that can reach NHL.com / Hockey-Reference, then place cleaned CSVs under data/processed/ and run validate-data.

> No raw downloads were saved successfully; no real dataset rows exist under data/raw/ or data/processed/. Synthetic data is used only in labeled test fixtures (tests/fixtures/) and never as observed data.

## Datasets A-G — coverage and status

- **Dataset A** — 2025-26 Dallas regular-season team totals (GP, W/L/OTL, points, GF/GA, GF/GP, GA/GP, PP%, PK%, shots, faceoff %)
  - Status: BLOCKED — source unreachable; not collected
  - Rows: —
  - Source URL: attempted in collection section above
  - Retrieval date: —
- **Dataset B** — 2025-26 Dallas game log (game ID, date, opponent, home/away, regulation/final goals, finish type, shots, PP)
  - Status: BLOCKED — source unreachable; not collected
  - Rows: —
  - Source URL: attempted in collection section above
  - Retrieval date: —
- **Dataset C** — 2025-26 Dallas skater statistics (player, position, GP, goals, assists, points, shots, shooting %, PPG, TOI)
  - Status: BLOCKED — source unreachable; not collected
  - Rows: —
  - Source URL: attempted in collection section above
  - Retrieval date: —
- **Dataset D** — 2025-26 Dallas goalie statistics (GP/GS, W-L-OTL, shots against, saves, GA, SV%, GAA, shutouts)
  - Status: BLOCKED — source unreachable; not collected
  - Rows: —
  - Source URL: attempted in collection section above
  - Retrieval date: —
- **Dataset E** — 2024-25 Dallas team totals and game log (backtest calibration)
  - Status: BLOCKED — source unreachable; not collected
  - Rows: —
  - Source URL: attempted in collection section above
  - Retrieval date: —
- **Dataset F** — Central Division standings 2021-22 through 2025-26 (all teams, rank, playoff status)
  - Status: BLOCKED — source unreachable; not collected
  - Rows: —
  - Source URL: attempted in collection section above
  - Retrieval date: —
- **Dataset G** — Initial 2026-27 Dallas roster (player, position, roster date, source)
  - Status: BLOCKED — source unreachable; not collected
  - Rows: —
  - Source URL: attempted in collection section above
  - Retrieval date: —

## Field definitions, units, and conventions
- Regulation goals: goals scored/allowed at 60 minutes, excluding shootout decision increments.
- Finish type: REG / OT / SO. Points: 2 for any win, 1 for OT/SO loss, 0 for regulation loss.
- Percentage fields (PP%, PK%, SV%, shooting %): stored as 0-100 where the source provides numerator/denominator, that is recorded too.
- Goalie appearances are not team games; goalie goals allowed can differ from team goals allowed (empty-net goals, attribution).
- Traded players: Dallas-only contributions kept separate from full-season production.

## Cleaning, missing values, duplicates, overtime/shootout adjustments
- Not applicable: no real data was collected, so no cleaning was performed.
- Planned: shootout decision goals excluded from Poisson fits; game-log totals reconciled to official NHL season totals; regulation goals at 60 minutes distinguished from displayed final scores.

## Source reconciliation
- Not performed: no real game-log or team-total files exist to reconcile.
- Proposal-claimed 2025-26 values (273 GF, 222 GA, 50-20-12, 112 points) are treated as unverified and are not hard-coded anywhere.

## Data-completeness checklist (A-G)
| Dataset | Required | Collected | Status | Exception |
|---------|----------|-----------|--------|-----------|
| A | Yes | No | BLOCKED | Source unreachable (2026-10-23) |
| B | Yes | No | BLOCKED | Source unreachable (2026-10-23) |
| C | Yes | No | BLOCKED | Source unreachable (2026-10-23) |
| D | Yes | No | BLOCKED | Source unreachable (2026-10-23) |
| E | Yes | No | BLOCKED | Source unreachable (2026-10-23) |
| F | Yes | No | BLOCKED | Source unreachable (2026-10-23) |
| G | Yes | No | BLOCKED | Source unreachable (2026-10-23) |

Every dataset A-G is blocked by the same network failure; no substitute source was reachable either.

## Blocker summary and next step
- Blocker: NHL.com and Hockey-Reference are unreachable from this environment (SSL/connection errors after bounded retries).
- Effect: datasets A-G are not collected; the data report cannot describe observed team/game/player/goalie values.
- Forecast results, figures, and the backtest cannot be run on real data until the blocker clears.
- Next step: re-run `python -m stars_forecast collect-data` from a network with NHL.com/Hockey-Reference access, then `validate-data` and `data-report`.

## Artifacts
- data/raw/collection_manifest.json — attempted sources and outcomes
- data/raw/collection_blocker.json — blocker evidence
- outputs/qa/data-validation.json — validation contracts (pending real inputs)

