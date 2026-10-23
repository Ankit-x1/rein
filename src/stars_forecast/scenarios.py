"""Scenario families S0-S4 with a versioned configuration file.

Baseline calibration is kept independent of scenario mutations. All rates are
validated positive; impossible games-played assumptions are rejected.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from .model import PoissonModel, season_summary, threshold_probs, SEASON_GAMES

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "scenarios.json"


@dataclass
class ScenarioResult:
    name: str
    family: str
    lam_gf: float
    lam_ga: float
    p_ot_win: float
    n_seasons: int
    seed: int
    summary: dict
    threshold_probs: dict
    diff_vs_baseline_points: float = 0.0
    seasons_df: pd.DataFrame | None = None


@dataclass
class ScenarioConfig:
    version: int
    n_seasons: int
    seed: int
    season_games: int
    offense_changes: list[float]
    defense_changes: list[float]
    point_thresholds: list[int]
    s3: list[dict] = field(default_factory=list)
    s4: dict | None = None

    @classmethod
    def load(cls, path: Path = CONFIG_PATH) -> "ScenarioConfig":
        raw = json.loads(path.read_text())
        if raw.get("version", 0) < 1:
            raise ValueError("unsupported scenario config version")
        return cls(
            version=int(raw["version"]),
            n_seasons=int(raw.get("n_seasons", 10000)),
            seed=int(raw.get("seed", 3315)),
            season_games=int(raw.get("season_games", SEASON_GAMES)),
            offense_changes=list(raw["s1_offense"]["changes"]),
            defense_changes=list(raw["s2_defense"]["changes"]),
            point_thresholds=list(raw.get("point_thresholds", [90, 95, 100, 105, 110])),
            s3=list(raw.get("s3_personnel", [])),
            s4=raw.get("s4_combined"),
        )

    def validate(self) -> None:
        if self.n_seasons < 100:
            raise ValueError("n_seasons must be >= 1000")
        for c in self.offense_changes + self.defense_changes:
            if c <= -1.0:
                raise ValueError(f"invalid rate change {c}: rate would be non-positive")
        for s in self.s3:
            if s.get("future_games", 0) <= 0 or s.get("future_games", 0) > 200:
                raise ValueError(f"impossible future_games in {s.get('id')}")
        if self.season_games != SEASON_GAMES:
            raise ValueError("season_games must be 82")


def _roster_delta_goals(scenario: dict, prior_goals_out: float | None, prior_gp_out: float | None,
                        prior_goals_in: float | None, prior_gp_in: float | None) -> float:
    """Projected per-team-game goal contribution: prior goals / prior games *
    future games * role factor, divided by 82. Incoming minus outgoing."""
    def proj(goals, gp, role_factor):
        if goals is None or gp in (None, 0):
            return 0.0
        return float(goals) / float(gp) * float(scenario.get("future_games", 82)) * float(role_factor or 1.0)
    g_out = proj(prior_goals_out, prior_gp_out, scenario.get("role_factor"))
    g_in = proj(prior_goals_in, prior_gp_in, scenario.get("role_factor"))
    return (g_in - g_out) / SEASON_GAMES


def run_scenarios(model: PoissonModel, cfg: ScenarioConfig, roster_stats: dict | None = None) -> dict[str, ScenarioResult]:
    """Run every scenario family. roster_stats holds verified player stats for S3 (optional)."""
    cfg.validate()
    results: dict[str, ScenarioResult] = {}

    # S0 baseline
    base = model.predict(cfg.n_seasons, cfg.seed)
    results["S0"] = ScenarioResult("S0", "baseline", base["lam_gf"], base["lam_ga"], base["p_ot_win"],
                                   cfg.n_seasons, cfg.seed, base["summary"], base["threshold_probs"],
                                   seasons_df=base["seasons"])
    baseline_points = base["summary"]["mean_points"]

    # S1 offense sensitivity
    for i, change in enumerate(cfg.offense_changes):
        out = model.predict(cfg.n_seasons, cfg.seed, offense_change=change)
        results[f"S1_{change:+.0%}"] = ScenarioResult(
            f"S1 {change:+.0%} offense", "s1_offense", out["lam_gf"], out["lam_ga"], out["p_ot_win"],
            cfg.n_seasons, cfg.seed, out["summary"], out["threshold_probs"],
            diff_vs_baseline_points=out["summary"]["mean_points"] - baseline_points,
            seasons_df=out["seasons"],
        )

    # S2 defense sensitivity (negative change = improved defense -> lower GA)
    for i, change in enumerate(cfg.defense_changes):
        out = model.predict(cfg.n_seasons, cfg.seed, defense_change=change)
        results[f"S2_{change:+.0%}"] = ScenarioResult(
            f"S2 {change:+.0%} defense", "s2_defense", out["lam_gf"], out["lam_ga"], out["p_ot_win"],
            cfg.n_seasons, cfg.seed, out["summary"], out["threshold_probs"],
            diff_vs_baseline_points=out["summary"]["mean_points"] - baseline_points,
            seasons_df=out["seasons"],
        )

    # S3 personnel scenarios
    roster_stats = roster_stats or {}
    for s in cfg.s3:
        sid = s.get("id", "S3")
        delta_g = _roster_delta_goals(
            s,
            roster_stats.get(f"{sid}_outgoing_goals"),
            roster_stats.get(f"{sid}_outgoing_gp"),
            roster_stats.get(f"{sid}_incoming_goals"),
            roster_stats.get(f"{sid}_incoming_gp"),
        )
        delta_ga = float(s.get("delta_ga_per_game", 0.0) or 0.0)
        out = model.predict(cfg.n_seasons, cfg.seed + hash(sid) % 1000,
                            roster_delta_g=delta_g, roster_delta_ga=delta_ga)
        results[sid] = ScenarioResult(
            sid, "s3_personnel", out["lam_gf"], out["lam_ga"], out["p_ot_win"],
            cfg.n_seasons, cfg.seed, out["summary"], out["threshold_probs"],
            diff_vs_baseline_points=out["summary"]["mean_points"] - baseline_points,
            seasons_df=out["seasons"],
        )

    # S4 combined
    if cfg.s4:
        s4 = cfg.s4
        out = model.predict(cfg.n_seasons, cfg.seed + 777,
                            offense_change=float(s4.get("offense_change", 0.0)),
                            defense_change=float(s4.get("defense_change", 0.0)),
                            roster_delta_g=float(s4.get("roster_delta_g_per_game", 0.0)),
                            roster_delta_ga=float(s4.get("roster_delta_ga_per_game", 0.0)))
        results["S4"] = ScenarioResult("S4", "s4_combined", out["lam_gf"], out["lam_ga"], out["p_ot_win"],
                                       cfg.n_seasons, cfg.seed, out["summary"], out["threshold_probs"],
                                       diff_vs_baseline_points=out["summary"]["mean_points"] - baseline_points,
                                       seasons_df=out["seasons"])

    return results
