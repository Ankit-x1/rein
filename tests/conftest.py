"""Pytest configuration: paths to clearly labeled synthetic FIXTURES only.

tests/fixtures/* are synthetic data for code-contract testing. They are NOT
real NHL data and never appear in forecasts or the data report.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"

GMLOG_25_26 = FIXTURES / "synthetic_2025_26_gamelog.csv"
GMLOG_24_25 = FIXTURES / "synthetic_2024_25_gamelog.csv"
TOTALS_25_26 = FIXTURES / "synthetic_2025_26_team_totals.csv"
STANDINGS = FIXTURES / "synthetic_central_standings.csv"
SKATERS = FIXTURES / "synthetic_2025_26_skaters.csv"
GOALIES = FIXTURES / "synthetic_2025_26_goalies.csv"

__all__ = ["FIXTURES", "GMLOG_25_26", "GMLOG_24_25", "TOTALS_25_26", "STANDINGS", "SKATERS", "GOALIES"]
