# tests/fixtures — SYNTHETIC TEST FIXTURES ONLY

All files under this directory are **synthetic, hand-generated data for
code-contract testing**. They are NOT real NHL.com / Hockey-Reference data.

Per the project rules, synthetic data may be used only in clearly labeled test
fixtures and must never appear in real datasets, forecast results, or
docs/data-report.md as observed data.

Files:
- synthetic_2025_26_gamelog.csv / synthetic_2024_25_gamelog.csv — 82-game game logs
- synthetic_2025_26_team_totals.csv / synthetic_2024_25_team_totals.csv — season totals
- synthetic_central_standings.csv — Central Division standings (5 seasons)
- synthetic_2025_26_skaters.csv / synthetic_2025_26_goalies.csv — player/goalie rows

Every row carries `source = "synthetic_fixture"`.
