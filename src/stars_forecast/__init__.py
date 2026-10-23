"""Dallas Stars 2026-27 regular-season forecasting package.

Poisson regulation goal-for / goal-against submodels + Monte Carlo 82-game
seasons, scenarios S0-S4, Central Division historical translation, backtest.
"""
from .model import SeasonResult, simulate_season, simulate_seasons, PoissonModel
from .scenarios import ScenarioConfig, run_scenarios

__version__ = "0.1.0"

__all__ = [
    "SeasonResult",
    "simulate_season",
    "simulate_seasons",
    "PoissonModel",
    "ScenarioConfig",
    "run_scenarios",
    "__version__",
]
