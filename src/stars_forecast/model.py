"""Core model: independent Poisson regulation goal counts + Monte Carlo seasons.

Three goal definitions are preserved: displayed final score, final hockey goals
excluding shootout decision increments, and regulation goals at 60 minutes. The
Poisson fit uses regulation goals only.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

SEASON_GAMES = 82
RESULT_WIN = "W"
RESULT_REG_LOSS = "REG_L"
RESULT_OT_SO_LOSS = "OTL"


@dataclass
class SeasonResult:
    games: int
    wins: int
    regulation_losses: int
    ot_sol: int
    points: int
    gf: int
    ga: int
    gd: int

    def to_dict(self) -> dict:
        return {
            "games": self.games,
            "wins": self.wins,
            "regulation_losses": self.regulation_losses,
            "ot_sol": self.ot_sol,
            "points": self.points,
            "gf": self.gf,
            "ga": self.ga,
            "gd": self.gd,
        }


def simulate_season(lam_gf: float, lam_ga: float, p_ot_win: float,
                    n_games: int = SEASON_GAMES, rng: np.random.Generator | None = None) -> SeasonResult:
    """Simulate one 82-game season.

    Each game: X ~ Pois(lam_gf), Y ~ Pois(lam_ga). X > Y win, X < Y regulation
    loss, tie -> OT/SO decided with Dallas win probability p_ot_win (estimated
    empirically from games tied after regulation). Points: win 2, OTL 1, REG L 0.
    Regulation goal differential is preserved for auditing; an OT deciding goal
    is never double-counted into goal differential.
    """
    if lam_gf <= 0 or lam_ga <= 0:
        raise ValueError("rates must be positive")
    if not 0.0 <= p_ot_win <= 1.0:
        raise ValueError("p_ot_win must be in [0, 1]")
    if rng is None:
        rng = np.random.default_rng()

    gf = rng.poisson(lam_gf, n_games)
    ga = rng.poisson(lam_ga, n_games)
    tied = gf == ga
    ot_win = rng.random(n_games) < p_ot_win

    wins = (gf > ga) | (tied & ot_win)
    reg_loss = (gf < ga) & (~tied)
    otl = tied & (~ot_win)
    points = 2 * wins.astype(int) + otl.astype(int)

    return SeasonResult(
        games=n_games,
        wins=int(wins.sum()),
        regulation_losses=int(reg_loss.sum()),
        ot_sol=int(otl.sum()),
        points=int(points.sum()),
        gf=int(gf.sum()),
        ga=int(ga.sum()),
        gd=int(gf.sum() - ga.sum()),
    )


def simulate_seasons(n_seasons: int, lam_gf: float, lam_ga: float, p_ot_win: float,
                     seed: int, n_games: int = SEASON_GAMES) -> pd.DataFrame:
    """Simulate n_seasons independent seasons with one seeded RNG stream."""
    rng = np.random.default_rng(seed)
    rows = [simulate_season(lam_gf, lam_ga, p_ot_win, n_games, rng) for _ in range(n_seasons)]
    return pd.DataFrame([r.to_dict() for r in rows])


def season_summary(df: pd.DataFrame) -> dict:
    points = df["points"]
    return {
        "n_seasons": int(len(df)),
        "mean_points": float(points.mean()),
        "median_points": float(points.median()),
        "p80_lo": float(points.quantile(0.10)),
        "p80_hi": float(points.quantile(0.90)),
        "p95_lo": float(points.quantile(0.025)),
        "p95_hi": float(points.quantile(0.975)),
        "mean_w": float(df["wins"].mean()),
        "mean_regulation_losses": float(df["regulation_losses"].mean()),
        "mean_ot_sol": float(df["ot_sol"].mean()),
        "mean_gf": float(df["gf"].mean()),
        "mean_ga": float(df["ga"].mean()),
        "mean_gd": float(df["gd"].mean()),
    }


def threshold_probs(df: pd.DataFrame, thresholds=(90, 95, 100, 105, 110)) -> dict:
    points = df["points"]
    return {f"p_ge_{t}": float((points >= t).mean()) for t in thresholds}


@dataclass
class FitDiagnostics:
    lam_gf: float
    lam_ga: float
    mean_gf: float
    var_gf: float
    mean_ga: float
    var_ga: float
    dispersion_gf: float  # var / mean
    dispersion_ga: float
    gof_gf_stat: float
    gof_gf_p: float
    gof_ga_stat: float
    gof_ga_p: float
    overdispersion_flag: bool
    n_tied_games: int
    p_ot_win: float
    p_ot: float
    p_so: float


class PoissonModel:
    """Independent Poisson regulation GF/GA model with empirical OT/SO resolution."""

    def __init__(self) -> None:
        self.lam_gf: float | None = None
        self.lam_ga: float | None = None
        self.p_ot_win: float | None = None
        self.diagnostics: FitDiagnostics | None = None

    def fit(self, gamelog: pd.DataFrame) -> FitDiagnostics:
        gf = gamelog["gf_regulation"].astype(float).to_numpy()
        ga = gamelog["ga_regulation"].astype(float).to_numpy()
        finish = gamelog["finish_type"].astype(str).to_numpy()

        self.lam_gf = float(gf.mean())
        self.lam_ga = float(ga.mean())

        # OT/SO probability from games tied after regulation only.
        tied = gf == ga
        n_tied = int(tied.sum())
        if n_tied == 0:
            raise ValueError("no tied-after-regulation games; cannot estimate OT/SO behavior empirically")
        tied_games = gamelog.loc[tied]
        finish_tied = finish[tied]
        # Dallas win in a tied game = winner of the OT/SO decision.
        p_ot_win = float((tied_games["result"] == RESULT_WIN).mean()) if "result" in gamelog.columns else 0.5
        p_ot = float((finish_tied == "OT").mean()) if len(finish_tied) else 0.0
        p_so = float((finish_tied == "SO").mean()) if len(finish_tied) else 0.0
        self.p_ot_win = p_ot_win

        def gof(counts: np.ndarray, lam: float) -> tuple[float, float]:
            counts = counts.astype(int)
            max_c = int(counts.max())
            ks = np.arange(0, max_c + 1)
            expected = len(counts) * stats.poisson.pmf(ks, lam)
            obs = np.array([(counts == k).sum() for k in ks])
            # Pool sparse categories so every expected count >= 5 where possible.
            pooled_obs, pooled_exp = [], []
            cur_o, cur_e = 0.0, 0.0
            for idx, (o, e) in enumerate(zip(obs, expected)):
                cur_o += o
                cur_e += e
                if cur_e >= 5 or idx == len(obs) - 1:
                    pooled_obs.append(cur_o)
                    pooled_exp.append(cur_e)
                    cur_o, cur_e = 0.0, 0.0
            if cur_e > 0:
                pooled_obs[-1] += cur_o
                pooled_exp[-1] += cur_e
            pooled_exp = np.array(pooled_exp, dtype=float)
            stat = float(((np.array(pooled_obs) - pooled_exp) ** 2 / pooled_exp).sum())
            dfree = max(len(pooled_exp) - 2, 1)
            pval = float(stats.chi2.sf(stat, dfree))
            return stat, pval

        gof_gf_stat, gof_gf_p = gof(gf, self.lam_gf)
        gof_ga_stat, gof_ga_p = gof(ga, self.lam_ga)
        disp_gf = float(gf.var() / self.lam_gf) if self.lam_gf else float("nan")
        disp_ga = float(ga.var() / self.lam_ga) if self.lam_ga else float("nan")
        overdispersion = bool(disp_gf > 1.5 or disp_ga > 1.5)

        self.diagnostics = FitDiagnostics(
            lam_gf=self.lam_gf, lam_ga=self.lam_ga,
            mean_gf=float(gf.mean()), var_gf=float(gf.var()),
            mean_ga=float(ga.mean()), var_ga=float(ga.var()),
            dispersion_gf=disp_gf, dispersion_ga=disp_ga,
            gof_gf_stat=gof_gf_stat, gof_gf_p=gof_gf_p,
            gof_ga_stat=gof_ga_stat, gof_ga_p=gof_ga_p,
            overdispersion_flag=overdispersion,
            n_tied_games=n_tied, p_ot_win=p_ot_win, p_ot=p_ot, p_so=p_so,
        )
        return self.diagnostics

    def predict(self, n_seasons: int, seed: int, offense_change: float = 0.0,
                defense_change: float = 0.0, roster_delta_g: float = 0.0,
                roster_delta_ga: float = 0.0) -> dict:
        """Run one scenario. defense_change: negative = improved defense (lower GA)."""
        if self.lam_gf is None or self.lam_ga is None or self.p_ot_win is None:
            raise RuntimeError("model must be fit before prediction")
        lam_gf = self.lam_gf * (1.0 + offense_change) + roster_delta_g
        lam_ga = self.lam_ga * (1.0 + defense_change) + roster_delta_ga
        if lam_gf <= 0 or lam_ga <= 0:
            raise ValueError("scenario produced a non-positive rate")
        df = simulate_seasons(n_seasons, lam_gf, lam_ga, self.p_ot_win, seed)
        return {
            "lam_gf": lam_gf,
            "lam_ga": lam_ga,
            "p_ot_win": self.p_ot_win,
            "seasons": df,
            "summary": season_summary(df),
            "threshold_probs": threshold_probs(df),
        }

    def to_dict(self) -> dict:
        return {
            "lam_gf": self.lam_gf,
            "lam_ga": self.lam_ga,
            "p_ot_win": self.p_ot_win,
            "diagnostics": self.diagnostics.__dict__ if self.diagnostics else None,
        }
