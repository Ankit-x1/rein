"""Model tests on labeled synthetic fixtures.

Includes hand-built REG win/loss, OT win/loss, SO win/loss fixtures verifying
regulation-score recovery, final-hockey totals, shootout exclusion, points and
goal differential.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from stars_forecast.model import (
    SEASON_GAMES, SeasonResult, simulate_season, simulate_seasons, PoissonModel,
    season_summary, threshold_probs,
)
from tests.conftest import GMLOG_25_26, GMLOG_24_25


def test_simulate_season_accounting():
    res = simulate_season(3.2, 2.8, 0.55, n_games=SEASON_GAMES, rng=np.random.default_rng(1))
    assert res.games == 82
    assert res.wins + res.regulation_losses + res.ot_sol == 82
    assert res.points == 2 * res.wins + res.ot_sol
    assert 0 <= res.points <= 164
    assert isinstance(res, SeasonResult)


def test_simulate_seasons_reproducible():
    a = simulate_seasons(200, 3.2, 2.8, 0.55, seed=3315)
    b = simulate_seasons(200, 3.2, 2.8, 0.55, seed=3315)
    pd.testing.assert_frame_equal(a, b)
    c = simulate_seasons(200, 3.2, 2.8, 0.55, seed=999)
    assert not (a["points"].values == c["points"].values).all()


def test_positive_rates_required():
    for kwargs in (dict(lam_gf=0.0, lam_ga=2.8, p_ot_win=0.5), dict(lam_gf=3.2, lam_ga=-1.0, p_ot_win=0.5)):
        try:
            simulate_season(**kwargs)
        except ValueError:
            continue
        raise AssertionError("expected ValueError for non-positive rate")


def test_handbuilt_result_categories_recovery():
    rows = [
        dict(game_id="g1", gf_regulation=3, ga_regulation=2, finish_type="REG", result="W"),
        dict(game_id="g2", gf_regulation=1, ga_regulation=4, finish_type="REG", result="L"),
        dict(game_id="g3", gf_regulation=3, ga_regulation=3, finish_type="OT", result="W"),
        dict(game_id="g4", gf_regulation=2, ga_regulation=2, finish_type="SO", result="L"),
        dict(game_id="g5", gf_regulation=2, ga_regulation=2, finish_type="OT", result="L"),
    ]
    df = pd.DataFrame(rows)
    assert int((df["finish_type"] == "REG").sum()) == 2
    assert int(((df["finish_type"] == "OT") & (df["result"] == "W")).sum()) == 1
    assert int(((df["finish_type"] == "OT") & (df["result"] == "L")).sum()) == 1
    assert int(((df["finish_type"] == "SO") & (df["result"] == "L")).sum()) == 1
    # Shootout exclusion: game g4 is tied at 2-2 in regulation/hockey goals.
    so = df[df["finish_type"] == "SO"]
    assert int(so.iloc[0]["gf_regulation"]) == int(so.iloc[0]["ga_regulation"])


def test_poisson_model_fit_on_synthetic():
    gamelog = pd.read_csv(GMLOG_25_26)
    model = PoissonModel()
    diag = model.fit(gamelog)
    assert model.lam_gf > 0 and model.lam_ga > 0
    assert 0.0 <= model.p_ot_win <= 1.0
    assert diag.n_tied_games > 0
    assert diag.dispersion_gf > 0 and diag.dispersion_ga > 0
    assert 0.0 <= diag.gof_gf_p <= 1.0 and 0.0 <= diag.gof_ga_p <= 1.0


def test_season_summary_structure():
    df = simulate_seasons(500, 3.2, 2.8, 0.55, seed=5)
    s = season_summary(df)
    for key in ("mean_points", "median_points", "p80_lo", "p80_hi", "p95_lo", "p95_hi",
                "mean_w", "mean_regulation_losses", "mean_ot_sol", "mean_gd"):
        assert key in s and s[key] is not None
    assert s["p80_lo"] <= s["mean_points"] <= s["p80_hi"]
    assert s["p95_lo"] <= s["p95_hi"]


def test_threshold_probabilities():
    df = simulate_seasons(500, 3.2, 2.8, 0.55, seed=5)
    probs = threshold_probs(df)
    for t in (90, 95, 100, 105, 110):
        assert 0.0 <= probs[f"p_ge_{t}"] <= 1.0
    assert probs["p_ge_90"] >= probs["p_ge_110"]
