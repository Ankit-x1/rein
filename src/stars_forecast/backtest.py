"""Isolated backtest: fit on 2024-25 only, simulate 2025-26, evaluate against the
verified 2025-26 actual outcome loaded for evaluation only. No tuning to target.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .model import PoissonModel, season_summary, threshold_probs

ROOT = Path(__file__).resolve().parents[2]


@dataclass
class BacktestResult:
    train_season: str
    eval_season: str
    n_seasons: int
    seed: int
    train_lam_gf: float
    train_lam_ga: float
    train_p_ot_win: float
    predicted: dict
    actual: dict | None
    abs_point_error: float | None
    actual_in_80: bool | None
    actual_in_95: bool | None
    actual_w: int | None
    actual_reg_l: int | None
    actual_otl: int | None
    predicted_w: float | None
    predicted_reg_l: float | None
    predicted_otl: float | None


def run_backtest(model: PoissonModel, train_gamelog: pd.DataFrame, eval_actual: dict | None,
                 n_seasons: int = 10000, seed: int = 3315) -> BacktestResult:
    model.fit(train_gamelog)
    pred = model.predict(n_seasons, seed)
    summary = pred["summary"]
    probs = pred["threshold_probs"]

    actual = None
    abs_err = None
    in_80 = in_95 = None
    act_w = act_reg = act_otl = None
    if eval_actual is not None:
        actual = {
            "points": int(eval_actual["points"]),
            "wins": int(eval_actual["wins"]),
            "regulation_losses": int(eval_actual["regulation_losses"]),
            "ot_sol": int(eval_actual["ot_sol"]),
        }
        act_w = actual["wins"]
        act_reg = actual["regulation_losses"]
        act_otl = actual["ot_sol"]
        abs_err = float(abs(summary["mean_points"] - actual["points"]))
        in_80 = summary["p80_lo"] <= actual["points"] <= summary["p80_hi"]
        in_95 = summary["p95_lo"] <= actual["points"] <= summary["p95_hi"]

    return BacktestResult(
        train_season="2024-25",
        eval_season="2025-26",
        n_seasons=n_seasons,
        seed=seed,
        train_lam_gf=model.lam_gf,
        train_lam_ga=model.lam_ga,
        train_p_ot_win=model.p_ot_win,
        predicted={"points": summary, "thresholds": probs},
        actual=actual,
        abs_point_error=abs_err,
        actual_in_80=in_80,
        actual_in_95=in_95,
        actual_w=act_w,
        actual_reg_l=act_reg,
        actual_otl=act_otl,
        predicted_w=summary["mean_w"],
        predicted_reg_l=summary["mean_regulation_losses"],
        predicted_otl=summary["mean_ot_sol"],
    )
