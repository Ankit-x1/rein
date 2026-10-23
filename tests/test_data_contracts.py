"""Data-contract tests on labeled synthetic fixtures (never real data).

Covers: regular-season filtering, unique game IDs, complete season counts,
missing mandatory values, valid units, result categories, source reconciliation
under matching conventions, and absence of 2026-27 fitting data.
"""

from __future__ import annotations

import pandas as pd

from stars_forecast.validate import (
    REQUIRED_FILES, GAMELOG_MANDATORY, TEAM_TOTALS_MANDATORY, _validate_file,
    _reconciliation,
)
from tests.conftest import GMLOG_25_26, GMLOG_24_25, TOTALS_25_26


def _load(path):
    return pd.read_csv(path)


def test_gamelog_has_82_regular_season_games():
    df = _load(GMLOG_25_26)
    assert len(df) == 82
    assert (df["regular_season"] == 1).all()


def test_gamelog_unique_game_ids():
    df = _load(GMLOG_25_26)
    assert df["game_id"].is_unique


def test_gamelog_no_missing_mandatory_values():
    df = _load(GMLOG_25_26)
    mandatory = [c for c in GAMELOG_MANDATORY if c in df.columns]
    assert df[mandatory].isna().sum().sum() == 0


def test_gamelog_valid_units_and_categories():
    df = _load(GMLOG_25_26)
    assert ((df["gf_regulation"] >= 0) & (df["ga_regulation"] >= 0)).all()
    assert ((df["gf_regulation"] % 1 == 0) & (df["ga_regulation"] % 1 == 0)).all()
    assert df["finish_type"].isin(["REG", "OT", "SO"]).all()


def test_season_accounting():
    df = _load(GMLOG_25_26)
    w = int((df["result"] == "W").sum())
    rl = int(((df["result"] == "L") & (df["finish_type"] == "REG")).sum())
    otl = int(((df["result"] == "L") & (df["finish_type"] != "REG")).sum())
    assert w + rl + otl == 82
    totals = _load(TOTALS_25_26).iloc[0]
    assert int(totals["points"]) == 2 * w + otl
    assert 0 <= int(totals["points"]) <= 164


def test_no_2026_27_fitting_data():
    df = _load(GMLOG_25_26)
    assert not df["season"].astype(str).str.startswith("2026").any()


def test_reconciliation_matching_conventions():
    gamelog = _load(GMLOG_25_26)
    totals = _load(TOTALS_25_26).iloc[0]
    assert int(gamelog["gf_regulation"].sum()) == int(totals["gf"])
    assert int(gamelog["ga_regulation"].sum()) == int(totals["ga"])


def test_validate_file_runs_on_fixture(tmp_path, monkeypatch):
    import stars_forecast.validate as v
    monkeypatch.setattr(v, "PROCESSED", GMLOG_25_26.parent)
    monkeypatch.setattr(v, "QA_DIR", tmp_path / "qa")
    checks = _validate_file("synthetic_2025_26_gamelog.csv")
    passed = sum(1 for c in checks if c["pass"])
    assert passed >= 1
    names = {c["check"] for c in checks}
    assert "unique-game-ids:synthetic_2025_26_gamelog.csv" in names


def test_validate_missing_file(tmp_path, monkeypatch):
    import stars_forecast.validate as v
    monkeypatch.setattr(v, "PROCESSED", tmp_path / "empty")
    monkeypatch.setattr(v, "QA_DIR", tmp_path / "qa")
    checks = _validate_file("does_not_exist.csv")
    assert len(checks) == 1
    assert checks[0]["pass"] is False
    assert "missing" in checks[0]["detail"]


def test_shootout_decision_goal_excluded_from_hockey_goals():
    df = _load(GMLOG_25_26)
    so = df[df["finish_type"] == "SO"]
    assert len(so) > 0
    # In SO losses the displayed final score carries a shootout decision increment;
    # regulation/hockey goals remain tied.
    losers = so[(so["result"] == "L")]
    if len(losers):
        assert ((losers["ga_final"] - losers["ga_regulation"]) == 1).all()
        assert ((losers["gf_final"] - losers["gf_regulation"]) == 0).all()
