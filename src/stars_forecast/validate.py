"""Data validation contracts on cleaned CSVs under data/processed/.

Exits nonzero with a clear message when required processed inputs are missing
or fail a contract. Writes outputs/qa/data-validation.json with pass/fail
evidence. Synthetic data is never validated as if it were real.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
QA_DIR = ROOT / "outputs" / "qa"
VALIDATION_PATH = QA_DIR / "data-validation.json"

REQUIRED_FILES = {
    "dallas_2025_26_team_totals.csv": "A: 2025-26 Dallas team totals",
    "dallas_2025_26_gamelog.csv": "B: 2025-26 Dallas game log",
    "dallas_2025_26_skaters.csv": "C: 2025-26 Dallas skaters",
    "dallas_2025_26_goalies.csv": "D: 2025-26 Dallas goalies",
    "dallas_2024_25_team_totals.csv": "E: 2024-25 Dallas team totals",
    "dallas_2024_25_gamelog.csv": "E: 2024-25 Dallas game log",
    "central_division_standings_2021_22_to_2025_26.csv": "F: Central Division standings",
    "dallas_2026_27_roster.csv": "G: initial 2026-27 roster",
}

GAMELOG_MANDATORY = [
    "game_id", "date", "season", "regular_season", "opponent", "home_away",
    "gf_regulation", "ga_regulation", "gf_final", "ga_final", "result",
    "finish_type", "shots_for", "shots_against",
]
TEAM_TOTALS_MANDATORY = ["season", "games_played", "wins", "regulation_losses", "ot_sol",
                         "points", "gf", "ga"]


def _fail(checks, name, detail):
    checks.append({"check": name, "pass": False, "detail": detail})


def _pass(checks, name, detail=""):
    checks.append({"check": name, "pass": True, "detail": detail})


def _validate_file(filename: str) -> list[dict]:
    checks: list[dict] = []
    path = PROCESSED / filename
    if not path.exists():
        _fail(checks, f"file-present:{filename}", f"missing required input {path}")
        return checks
    try:
        df = pd.read_csv(path)
    except Exception as exc:  # noqa: BLE001
        _fail(checks, f"readable:{filename}", f"cannot read CSV: {exc}")
        return checks

    _pass(checks, f"file-present:{filename}", f"{len(df)} rows, {len(df.columns)} columns")

    if "game_id" in df.columns:
        dupes = int(df["game_id"].duplicated().sum())
        _fail(checks, f"unique-game-ids:{filename}", f"{dupes} duplicate game_id values") if dupes else _pass(checks, f"unique-game-ids:{filename}")

    if "season" in df.columns:
        seasons = sorted(df["season"].dropna().astype(str).unique().tolist())
        future = [s for s in seasons if s.startswith("2026")]
        if future:
            _fail(checks, f"no-2026-27-fitting-data:{filename}", f"future fitting seasons present: {future}")
        else:
            _pass(checks, f"no-2026-27-fitting-data:{filename}")

    mandatory = GAMELOG_MANDATORY if "gamelog" in filename else TEAM_TOTALS_MANDATORY
    mandatory = [c for c in mandatory if c in df.columns]
    missing_vals = int(df[mandatory].isna().sum().sum()) if mandatory else 0
    if missing_vals:
        _fail(checks, f"no-missing-mandatory:{filename}", f"{missing_vals} missing mandatory values")
    else:
        _pass(checks, f"no-missing-mandatory:{filename}")

    if "gf_regulation" in df.columns and "ga_regulation" in df.columns:
        bad_units = int(((df["gf_regulation"] < 0) | (df["ga_regulation"] < 0)).sum())
        non_int = int((df["gf_regulation"] % 1 != 0).sum()) + int((df["ga_regulation"] % 1 != 0).sum())
        detail = []
        if bad_units: detail.append(f"{bad_units} negative goals")
        if non_int: detail.append(f"{non_int} non-integer goals")
        if detail:
            _fail(checks, f"valid-units:{filename}", "; ".join(detail))
        else:
            _pass(checks, f"valid-units:{filename}", "regulation goals non-negative integers")

    if "finish_type" in df.columns:
        invalid = df.loc[~df["finish_type"].isin(["REG", "OT", "SO"]), "finish_type"]
        if len(invalid):
            _fail(checks, f"valid-result-categories:{filename}", f"invalid finish_type: {sorted(invalid.unique().tolist())}")
        else:
            _pass(checks, f"valid-result-categories:{filename}", "all finish_type in {REG, OT, SO}")

    if "regular_season" in df.columns:
        non_rs = int((df["regular_season"] != 1).sum())
        if non_rs:
            _fail(checks, f"regular-season-only:{filename}", f"{non_rs} non-regular-season rows")
        else:
            _pass(checks, f"regular-season-only:{filename}", "all rows regular season")

    if {"wins", "regulation_losses", "ot_sol", "games_played", "points"}.issubset(df.columns):
        row = df.iloc[0]
        ok_cat = int(row["wins"]) + int(row["regulation_losses"]) + int(row["ot_sol"]) == int(row["games_played"])
        ok_pts = int(row["points"]) == 2 * int(row["wins"]) + int(row["ot_sol"])
        ok_gp = int(row["games_played"]) == 82
        if not (ok_cat and ok_pts and ok_gp):
            _fail(checks, f"season-accounting:{filename}",
                  f"W+RL+OTL=GP: {ok_cat}, points=2W+OTL: {ok_pts}, GP=82: {ok_gp}")
        else:
            _pass(checks, f"season-accounting:{filename}", "W+RL+OTL=82, points=2W+OTL")

    return checks


def _reconciliation(checks: list[dict]) -> None:
    totals_path = PROCESSED / "dallas_2025_26_team_totals.csv"
    log_path = PROCESSED / "dallas_2025_26_gamelog.csv"
    if not (totals_path.exists() and log_path.exists()):
        _fail(checks, "reconciliation: gamelog vs team totals", "one of the files missing; skipped")
        return
    try:
        totals = pd.read_csv(totals_path).iloc[0]
        log = pd.read_csv(log_path)
        log_gf = int(log["gf_regulation"].sum())
        log_ga = int(log["ga_regulation"].sum())
        diff_gf = log_gf - int(totals["gf"])
        diff_ga = log_ga - int(totals["ga"])
        ok = diff_gf == 0 and diff_ga == 0
        detail = f"gamelog GF={log_gf} vs totals GF={int(totals['gf'])} (diff {diff_gf}); "
        detail += f"gamelog GA={log_ga} vs totals GA={int(totals['ga'])} (diff {diff_ga})"
        if ok:
            _pass(checks, "reconciliation: gamelog vs team totals", detail + " (regulation convention)")
        else:
            _fail(checks, "reconciliation: gamelog vs team totals", detail)
    except Exception as exc:  # noqa: BLE001
        _fail(checks, "reconciliation: gamelog vs team totals", f"error: {exc}")


def cmd_validate(args) -> None:
    QA_DIR.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    all_checks: list[dict] = []
    missing_files = [f for f in REQUIRED_FILES if not (PROCESSED / f).exists()]

    for filename in REQUIRED_FILES:
        all_checks.extend(_validate_file(filename))

    _reconciliation(all_checks)

    passed = sum(1 for c in all_checks if c["pass"])
    total = len(all_checks)
    report = {
        "validated_utc": started,
        "processed_dir": str(PROCESSED),
        "missing_files": missing_files,
        "checks": all_checks,
        "passed": passed,
        "total": total,
        "all_pass": passed == total and not missing_files,
    }
    VALIDATION_PATH.write_text(json.dumps(report, indent=2))

    print(f"[validate] {passed}/{total} checks passed")
    if missing_files:
        print(f"[validate] MISSING processed inputs: {missing_files}")
        print("[validate] run collect-data first (requires reachable NHL.com / Hockey-Reference)")
    if not report["all_pass"]:
        print("[validate] validation FAILED — see outputs/qa/data-validation.json")
        sys.exit(1)
    print("[validate] all validation checks passed")
