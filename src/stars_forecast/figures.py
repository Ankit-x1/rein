"""Labeled figures: observed vs fitted goal frequencies, point distributions,
sensitivity curves, personnel/combined comparisons, historical translation,
backtest. Saved as PNGs under outputs/figures/."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
FIG_DIR = ROOT / "outputs" / "figures"


def _save(fig, name: str) -> str:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    path = FIG_DIR / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def goal_fit_figure(gf_counts, ga_counts, lam_gf, lam_ga, out_name="goal_fit.png"):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    kmax = max(int(gf_counts.max()), int(ga_counts.max())) + 1
    ks = np.arange(0, kmax)
    for ax, counts, lam, title in ((axes[0], gf_counts, lam_gf, "Goals For"),
                                   (axes[1], ga_counts, lam_ga, "Goals Against")):
        obs = np.array([(counts == k).sum() for k in ks])
        exp = len(counts) * stats.poisson.pmf(ks, lam)
        ax.bar(ks - 0.2, obs, width=0.4, label="Observed", alpha=0.8)
        ax.bar(ks + 0.2, exp, width=0.4, label=f"Poisson(λ={lam:.3f})", alpha=0.8)
        ax.set_xlabel("Regulation goals per game")
        ax.set_ylabel("Number of games")
        ax.set_title(title)
        ax.legend()
    fig.suptitle("Observed goal frequencies vs fitted Poisson (regulation goals)")
    return _save(fig, out_name)


def point_distributions(results: dict, out_name="point_distributions.png"):
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = {"S0": "#1f77b4"}
    for name, res in results.items():
        s = res.summary
        ax.axvline(s["mean_points"], color=colors.get(name, "#555555"), linestyle="--", alpha=0.6)
    ax.set_xlabel("Simulated standings points per 82-game season")
    ax.set_ylabel("Scenario")
    ax.set_title("Mean simulated points by scenario (fixed seed, >=10,000 seasons)")
    names = list(results.keys())
    means = [results[n].summary["mean_points"] for n in names]
    ax.barh(names, means, color=[colors.get(n, "#555555") for n in names])
    for n, m in zip(names, means):
        ax.text(m, n, f"  {m:.1f}", va="center")
    ax.invert_yaxis()
    return _save(fig, out_name)


def sensitivity_curve(results: dict, family: str, xlabel: str, out_name: str):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    xs, ys = [], []
    for name in sorted(results):
        if not name.startswith(family):
            continue
        xs.append(float(name.split("_")[-1].replace("+", "").replace("-", "-")))
        ys.append(results[name].summary["mean_points"])
    order = np.argsort(xs)
    xs = [xs[i] for i in order]; ys = [ys[i] for i in order]
    ax.plot(xs, ys, marker="o")
    ax.axhline(results["S0"].summary["mean_points"], color="gray", linestyle="--", label="baseline")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Mean simulated points")
    ax.set_title(f"{xlabel} sensitivity (baseline mean = {results['S0'].summary['mean_points']:.1f})")
    ax.legend()
    return _save(fig, out_name)


def comparison_bar(results: dict, names: list[str], out_name: str):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    means = [results[n].summary["mean_points"] for n in names]
    diffs = [results[n].diff_vs_baseline_points for n in names]
    bars = ax.bar(names, means)
    for b, n, d in zip(bars, names, diffs):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f"{d:+.1f}", ha="center", va="bottom", fontsize=9)
    ax.set_ylabel("Mean simulated points")
    ax.set_title("Personnel / combined scenarios vs baseline (difference labeled)")
    ax.axhline(results["S0"].summary["mean_points"], color="gray", linestyle="--", label="baseline")
    ax.legend()
    fig.autofmt_xdate()
    return _save(fig, out_name)


def historical_translation(trans, out_name="historical_translation.png"):
    fig, ax = plt.subplots(figsize=(7, 4))
    seasons = list(trans.third_place_thresholds.keys())
    thresholds = list(trans.third_place_thresholds.values())
    ax.bar(seasons, thresholds)
    ax.axhline(trans.mean_threshold, color="red", linestyle="--",
               label=f"mean 3rd-place threshold = {trans.mean_threshold:.1f}")
    ax.set_xlabel("Central Division season")
    ax.set_ylabel("Points (3rd-place threshold)")
    ax.set_title(f"Historical 3rd-place point threshold (top-3 point-level probability = {trans.top3_point_level_probability:.1%})")
    ax.legend()
    fig.autofmt_xdate()
    return _save(fig, out_name)


def backtest_figure(backtest, out_name="backtest.png"):
    fig, ax = plt.subplots(figsize=(7, 4))
    pred = backtest.predicted["points"]
    ax.axvline(pred["mean_points"], color="#1f77b4", linestyle="--",
               label=f"predicted mean = {pred['mean_points']:.1f}")
    ax.axvspan(pred["p80_lo"], pred["p80_hi"], color="#1f77b4", alpha=0.2, label="80% interval")
    ax.axvspan(pred["p95_lo"], pred["p95_hi"], color="#1f77b4", alpha=0.1, label="95% interval")
    if backtest.actual is not None:
        ax.axvline(backtest.actual["points"], color="red", linestyle="-", linewidth=2,
                   label=f"actual 2025-26 = {backtest.actual['points']}")
    ax.set_xlabel("Standings points")
    ax.set_yticks([])
    ax.set_title(f"Backtest: train 2024-25 -> eval 2025-26 (abs point error = {backtest.abs_point_error})")
    ax.legend()
    return _save(fig, out_name)
