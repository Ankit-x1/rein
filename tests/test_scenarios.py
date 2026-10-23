"""Scenario tests on labeled synthetic fixtures: isolation, zero-change behavior,
roster units, threshold probabilities, interval ordering, monotonicity sanity
with common random numbers (same seed across scenarios).
"""

from __future__ import annotations

import pandas as pd

from stars_forecast.model import PoissonModel
from stars_forecast.scenarios import ScenarioConfig, run_scenarios, _roster_delta_goals
from tests.conftest import GMLOG_25_26


def test_scenario_isolation_offense_only_moves_lam_gf():
    model = PoissonModel(); model.fit(pd.read_csv(GMLOG_25_26))
    base = model.predict(300, 1)
    up = model.predict(300, 1, offense_change=0.10)
    assert abs(up["lam_ga"] - base["lam_ga"]) < 1e-12
    assert up["lam_gf"] > base["lam_gf"]


def test_zero_change_equals_baseline():
    model = PoissonModel(); model.fit(pd.read_csv(GMLOG_25_26))
    base = model.predict(300, 10)
    same = model.predict(300, 10, offense_change=0.0, defense_change=0.0)
    pd.testing.assert_frame_equal(base["seasons"], same["seasons"])


def test_roster_delta_units():
    delta = _roster_delta_goals(dict(future_games=82, role_factor=0.75),
                                prior_goals_out=30, prior_gp_out=78,
                                prior_goals_in=20, prior_gp_in=82)
    proj_out = 30 / 78 * 82 * 0.75
    proj_in = 20 / 82 * 82 * 0.75
    assert abs(delta - (proj_in - proj_out) / 82) < 1e-12
    # Missing player stats contribute zero, never crash.
    assert _roster_delta_goals(dict(future_games=82), None, None, None, None) == 0.0


def test_run_scenarios_structure():
    model = PoissonModel(); model.fit(pd.read_csv(GMLOG_25_26))
    cfg = ScenarioConfig(version=1, n_seasons=1000, seed=11, season_games=82,
                         offense_changes=[0.05], defense_changes=[-0.05],
                         point_thresholds=[90, 100], s3=[], s4=None)
    results = run_scenarios(model, cfg)
    assert "S0" in results and "S1_+5%" in results and "S2_-5%" in results
    for res in results.values():
        assert res.lam_gf > 0 and res.lam_ga > 0
        assert 0.0 <= res.p_ot_win <= 1.0
        assert res.summary["mean_points"] > 0


def test_interval_ordering():
    model = PoissonModel(); model.fit(pd.read_csv(GMLOG_25_26))
    results = run_scenarios(model, ScenarioConfig(
        version=1, n_seasons=1000, seed=11, season_games=82,
        offense_changes=[0.1], defense_changes=[-0.1],
        point_thresholds=[90], s3=[], s4=None))
    for res in results.values():
        s = res.summary
        assert s["p80_lo"] <= s["p80_hi"]
        assert s["p95_lo"] <= s["p95_hi"]
        assert s["p80_lo"] >= s["p95_lo"]
        assert s["p80_hi"] <= s["p95_hi"]


def test_monotonicity_sanity_common_random_numbers():
    model = PoissonModel(); model.fit(pd.read_csv(GMLOG_25_26))
    cfg = ScenarioConfig(version=1, n_seasons=2000, seed=42, season_games=82,
                         offense_changes=[-0.10, 0.0, 0.10],
                         defense_changes=[0.0], point_thresholds=[90], s3=[], s4=None)
    results = run_scenarios(model, cfg)
    # Same seed across scenarios => coupled random numbers; stronger offense
    # should not systematically worsen expected points (allow MC noise tolerance).
    low = results["S1_-10%"].summary["mean_points"]
    base = results["S1_+0%"].summary["mean_points"]
    high = results["S1_+10%"].summary["mean_points"]
    tol = 2 * ((results["S1_+0%"].summary["mean_points"] ** 2 / 2000) ** 0.5) * 4  # rough noise band
    assert high >= low - tol
    assert base >= low - tol
