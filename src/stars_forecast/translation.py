"""Historical Central Division point-level translation.

Completed 82-game Central seasons 2021-22 through 2025-26. For each simulated
Dallas point total, report the historical frequency of meeting/exceeding the
third-place point threshold, averaged over seasons. Explicit equality/tie rules.
Not an actual playoff-qualification probability.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


@dataclass
class TranslationResult:
    seasons_used: list[str]
    third_place_thresholds: dict[str, float]
    mean_threshold: float
    top3_point_level_probability: float
    per_season_meet: dict[str, bool]


def translate(standings: pd.DataFrame, simulated_points: pd.Series) -> TranslationResult:
    """standings: columns season, team, division, points, rank, playoff, gf, ga, games_played.
    Historical Dallas is excluded from competitor tables when estimating rank;
    here we use point-level thresholds only (point level, not exact rank)."""
    central = standings[standings["division"].str.contains("Central", case=False, na=False)].copy()
    seasons = sorted(central["season"].astype(str).unique().tolist())

    thresholds: dict[str, float] = {}
    meet: dict[str, bool] = {}
    for season in seasons:
        sub = central[central["season"].astype(str) == season].sort_values("points", ascending=False)
        # Completed 82-game seasons only.
        sub = sub[sub["games_played"] == 82]
        if len(sub) < 3:
            continue
        third = float(sub.iloc[2]["points"])  # third-place point threshold
        thresholds[season] = third
        meet[season] = bool((simulated_points >= third).mean() >= 0.0)  # per-season threshold recorded

    # Probability that a simulated Dallas point total meets/exceeds the historical
    # third-place threshold, averaged over seasons (not correlated rows as independent).
    probs = []
    for season, third in thresholds.items():
        probs.append(float((simulated_points >= third).mean()))
    mean_threshold = float(sum(thresholds.values()) / len(thresholds)) if thresholds else float("nan")
    top3_prob = float(sum(probs) / len(probs)) if probs else 0.0

    return TranslationResult(
        seasons_used=seasons,
        third_place_thresholds=thresholds,
        mean_threshold=mean_threshold,
        top3_point_level_probability=top3_prob,
        per_season_meet=meet,
    )
