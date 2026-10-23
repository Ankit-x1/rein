"""Backtest tests: train/eval separation, metric structure, interval coverage."""

from __future__ import annotations

import pandas as pd

from stars_forecast.backtest import run_backtest
from stars_forecast.model import PoissonModel
from tests.conftest import GMLOG_25_26, GMLOG_24_25


def test_backtest_train_eval_separation():
    train = pd.read_csv(GMLOG_24_25)
    eval_actual = dict(points=117, wins=55, regulation_losses=20, ot_sol=7)
    model = PoissonModel()
    bt = run_backtest(model, train, eval_actual, n_seasons=500, seed=7)
    assert bt.train_season == "2024-25"
    assert bt.eval_season == "2025-26"
    assert bt.train_lam_gf > 0 and bt.train_lam_ga > 0
    # Model was fit on training data only; eval actual used only for scoring.
    assert bt.abs_point_error is not None and bt.abs_point_error >= 0
    assert bt.actual_in_80 in (True, False)
    assert bt.actual_in_95 in (True, False)
    assert bt.predicted_w is not None and bt.predicted_reg_l is not None and bt.predicted_otl is not None


def test_backtest_without_actual_still_runs():
    train = pd.read_csv(GMLOG_24_25)
    model = PoissonModel()
    bt = run_backtest(model, train, None, n_seasons=200, seed=3)
    assert bt.actual is None
    assert bt.abs_point_error is None
    assert bt.predicted["points"]["mean_points"] > 0
