"""run-all orchestration: diagnostics -> scenarios -> backtest -> translation ->
figures -> tables -> results summary + run manifest. Requires validated real
inputs under data/processed/ (exits nonzero with a clear message otherwise).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .collect import ROOT
from .model import PoissonModel, simulate_seasons, season_summary, threshold_probs
from .scenarios import ScenarioConfig, run_scenarios
from .backtest import run_backtest
from .translation import translate
from . import figures as figs

PROCESSED = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"
TABLES = OUTPUTS / "tables"
FIG_DIR = OUTPUTS / "figures"
QA_DIR = OUTPUTS / "qa"
SUMMARY_PATH = OUTPUTS / "results-summary.md"
MANIFEST_PATH = OUTPUTS / "run_manifest.json"
REQUIRED = [
    "dallas_2025_26_gamelog.csv",
    "dallas_2024_25_gamelog.csv",
    "dallas_2025_26_team_totals.csv",
    "central_division_standings_2021_22_to_2025_26.csv",
]


def _load(name: str) -> pd.DataFrame:
    path = PROCESSED / name
    if not path.exists():
        print(f"[run-all] MISSING required input: {path}")
        print("[run-all] run collect-data (needs reachable NHL.com / Hockey-Reference), then validate-data")
        sys.exit(1)
    return pd.read_csv(path)


def _dependency_versions() -> dict:
    try:
        import importlib.metadata as md
        return {pkg: md.version(pkg) for pkg in ["pandas", "numpy", "scipy", "matplotlib", "requests", "pytest"]}
    except Exception:  # noqa: BLE001
        return {}


def cmd_run_all(args) -> int:
    for name in REQUIRED:
        _load(name)  # side effect: exits if missing
    gamelog = _load("dallas_2025_26_gamelog.csv")
    train_gamelog = _load("dallas_2024_25_gamelog.csv")
    standings = _load("central_division_standings_2021_22_to_2025_26.csv")

    cfg = ScenarioConfig.load()
    cfg.n_seasons = int(args.n_seasons)
    cfg.seed = int(args.seed)

    model = PoissonModel()
    diag = model.fit(gamelog)

    results = run_scenarios(model, cfg)

    # Backtest: train 2024-25, evaluate 2025-26 actual (loaded for evaluation only).
    totals = _load("dallas_2025_26_team_totals.csv").iloc[0]
    actual_2025_26 = {
        "points": int(totals["points"]),
        "wins": int(totals["wins"]),
        "regulation_losses": int(totals["regulation_losses"]),
        "ot_sol": int(totals["ot_sol"]),
    }
    backtest = run_backtest(model, train_gamelog, actual_2025_26, n_seasons=cfg.n_seasons, seed=cfg.seed)

    # Historical translation from simulated baseline points.
    trans = translate(standings, results["S0"].seasons_df["points"])

    # Save tables.
    TABLES.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, res in results.items():
        rows.append({"scenario": name, "family": res.family, "lam_gf": res.lam_gf, "lam_ga": res.lam_ga,
                     "mean_points": res.summary["mean_points"], "median_points": res.summary["median_points"],
                     "p80_lo": res.summary["p80_lo"], "p80_hi": res.summary["p80_hi"],
                     "p95_lo": res.summary["p95_lo"], "p95_hi": res.summary["p95_hi"],
                     "mean_w": res.summary["mean_w"], "mean_regulation_losses": res.summary["mean_regulation_losses"],
                     "mean_ot_sol": res.summary["mean_ot_sol"], "mean_gd": res.summary["mean_gd"],
                     "diff_vs_baseline_points": res.diff_vs_baseline_points,
                     **res.threshold_probs})
    pd.DataFrame(rows).to_csv(TABLES / "scenario_summary.csv", index=False)
    for name, res in results.items():
        res.seasons_df.to_csv(TABLES / f"{name.lower()}_seasons.csv", index=False)
    pd.DataFrame([backtest.__dict__]).to_csv(TABLES / "backtest.csv", index=False)

    # Figures.
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    figs.goal_fit_figure(gamelog["gf_regulation"].to_numpy(), gamelog["ga_regulation"].to_numpy(),
                         diag.lam_gf, diag.lam_ga)
    figs.point_distributions(results)
    figs.sensitivity_curve(results, "S1_", "Offense change", "sensitivity_offense.png")
    figs.sensitivity_curve(results, "S2_", "Defense change", "sensitivity_defense.png")
    s3_names = [n for n in results if results[n].family == "s3_personnel"] + (["S4"] if "S4" in results else [])
    if s3_names:
        figs.comparison_bar(results, s3_names, "personnel_comparison.png")
    figs.historical_translation(trans)
    figs.backtest_figure(backtest)

    # Results summary.
    lines = ["# Computational Results Summary", "", f"Seed: {cfg.seed}  |  Seasons per scenario: {cfg.n_seasons}", ""]
    lines.append("## Baseline (S0, verified 2025-26 calibration)")
    s = results["S0"].summary
    lines.append(f"- Mean points: {s['mean_points']:.1f} (median {s['median_points']:.1f})")
    lines.append(f"- 80% interval: [{s['p80_lo']:.1f}, {s['p80_hi']:.1f}]; 95% interval: [{s['p95_lo']:.1f}, {s['p95_hi']:.1f}]")
    lines.append(f"- Mean W / REG_L / OTL: {s['mean_w']:.1f} / {s['mean_regulation_losses']:.1f} / {s['mean_ot_sol']:.1f}")
    lines.append(f"- Mean goal differential: {s['mean_gd']:.1f}")
    lines.append("")
    lines.append("## Threshold probabilities (baseline)")
    for t in [90, 95, 100, 105, 110]:
        lines.append(f"- P(>= {t} points): {results['S0'].threshold_probs[f'p_ge_{t}']:.3f}")
    lines.append("")
    lines.append(f"## Historical translation — top-three point-level probability: {trans.top3_point_level_probability:.1%}")
    lines.append(f"Mean historical 3rd-place threshold: {trans.mean_threshold:.1f} points over {', '.join(trans.seasons_used)}")
    lines.append("")
    lines.append("## Backtest (train 2024-25, evaluate 2025-26 actual only)")
    lines.append(f"- Predicted mean points: {backtest.predicted['points']['mean_points']:.1f}")
    lines.append(f"- Actual 2025-26 points: {backtest.actual['points']}")
    lines.append(f"- Absolute point error: {backtest.abs_point_error}")
    lines.append(f"- Actual inside 80% interval: {backtest.actual_in_80}; inside 95% interval: {backtest.actual_in_95}")
    lines.append("")
    lines.append("## Diagnostics")
    lines.append(f"- lambda_GF = {diag.lam_gf:.4f}, lambda_GA = {diag.lam_ga:.4f}")
    lines.append(f"- Dispersion GF = {diag.dispersion_gf:.2f}, GA = {diag.dispersion_ga:.2f} (var/mean; >1.5 flags overdispersion)")
    lines.append(f"- Overdispersion flag: {diag.overdispersion_flag}; Poisson GOF p GF = {diag.gof_gf_p:.3f}, GA = {diag.gof_ga_p:.3f}")
    lines.append(f"- Games tied after regulation: {diag.n_tied_games}; Dallas OT/SO win prob: {diag.p_ot_win:.3f}")
    lines.append("")
    lines.append("All intervals are simulation/prediction intervals conditional on the model, not confidence intervals.")
    SUMMARY_PATH.write_text("\n".join(lines) + "\n")

    manifest = {
        "model_version": "0.1.0",
        "seed": cfg.seed,
        "n_seasons": cfg.n_seasons,
        "season_games": cfg.season_games,
        "rates": {"lam_gf": model.lam_gf, "lam_ga": model.lam_ga, "p_ot_win": model.p_ot_win},
        "scenario_config": str(ROOT / "config" / "scenarios.json"),
        "data_checksums": {},  # filled when real processed data exists; see data/raw manifest
        "dependency_versions": _dependency_versions(),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "outputs": {
            "summary": str(SUMMARY_PATH),
            "tables": str(TABLES),
            "figures": str(FIG_DIR),
        },
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))
    print(f"[run-all] complete. See {SUMMARY_PATH} and {MANIFEST_PATH}")
    return 0
