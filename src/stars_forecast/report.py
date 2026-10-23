"""docs/data-report.md generation from collected data + validation evidence.

Honest about availability: if real inputs are missing, the report documents
the blocker and the completeness checklist (A-G) rather than inventing data.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
DOCS = ROOT / "docs"
REPORT_PATH = DOCS / "data-report.md"
COLLECTION_DATE = "2026-10-23"


def _manifest() -> dict:
    p = DATA_RAW / "collection_manifest.json"
    return json.loads(p.read_text()) if p.exists() else {}


def _blocker() -> dict | None:
    p = DATA_RAW / "collection_blocker.json"
    return json.loads(p.read_text()) if p.exists() else None


def cmd_data_report(args=None) -> int:
    DOCS.mkdir(parents=True, exist_ok=True)
    manifest = _manifest()
    blocker = _blocker()
    sources = manifest.get("sources", []) if manifest else []

    lines = []
    lines.append("# Dallas Stars 2026-27 Forecast — Data Report")
    lines.append("")
    lines.append(f"_Generated {COLLECTION_DATE}. Evidence-based report on collected datasets; "
                 "separate from model results and the final academic report._")
    lines.append("")
    lines.append("## Scope and cutoff")
    lines.append("- Model-fitting data cutoff: end of the 2025-26 regular season.")
    lines.append("- No 2026-27 game results are used to fit the model.")
    lines.append("- Real, cited source data is required for datasets A-G; see completeness checklist below.")
    lines.append("")
    lines.append("## Collection attempt — " + COLLECTION_DATE)
    lines.append("")
    lines.append("Attempted sources (NHL.com and Hockey-Reference per the proposal data plan):")
    for s in sources:
        status = "OK" if s.get("ok") else "FAILED"
        err = f" — {s.get('error')}" if s.get("error") else ""
        lines.append(f"- [{s.get('dataset')}] {s.get('label')} — {status}{err}")
    if blocker:
        lines.append("")
        lines.append("### Blocker evidence")
        lines.append(f"- Recorded: {blocker.get('recorded_utc')}")
        lines.append(f"- Type: {blocker.get('blocker')}")
        lines.append(f"- Detail: {blocker.get('detail')}")
        lines.append(f"- Failed datasets: {', '.join(blocker.get('failed_datasets', []))}")
        lines.append(f"- Next step: {blocker.get('next_step')}")
    lines.append("")
    lines.append("> No raw downloads were saved successfully; no real dataset rows exist under data/raw/ or data/processed/. "
                 "Synthetic data is used only in labeled test fixtures (tests/fixtures/) and never as observed data.")
    lines.append("")
    lines.append("## Datasets A-G — coverage and status")
    lines.append("")
    datasets = {
        "A": "2025-26 Dallas regular-season team totals (GP, W/L/OTL, points, GF/GA, GF/GP, GA/GP, PP%, PK%, shots, faceoff %)",
        "B": "2025-26 Dallas game log (game ID, date, opponent, home/away, regulation/final goals, finish type, shots, PP)",
        "C": "2025-26 Dallas skater statistics (player, position, GP, goals, assists, points, shots, shooting %, PPG, TOI)",
        "D": "2025-26 Dallas goalie statistics (GP/GS, W-L-OTL, shots against, saves, GA, SV%, GAA, shutouts)",
        "E": "2024-25 Dallas team totals and game log (backtest calibration)",
        "F": "Central Division standings 2021-22 through 2025-26 (all teams, rank, playoff status)",
        "G": "Initial 2026-27 Dallas roster (player, position, roster date, source)",
    }
    for key in ["A", "B", "C", "D", "E", "F", "G"]:
        got = any(s.get("dataset") == key and s.get("ok") for s in sources)
        lines.append(f"- **Dataset {key}** — {datasets[key]}")
        lines.append(f"  - Status: {'collected' if got else 'BLOCKED — source unreachable; not collected'}")
        lines.append(f"  - Rows: —")
        lines.append(f"  - Source URL: attempted in collection section above")
        lines.append(f"  - Retrieval date: —")
    lines.append("")
    lines.append("## Field definitions, units, and conventions")
    lines.append("- Regulation goals: goals scored/allowed at 60 minutes, excluding shootout decision increments.")
    lines.append("- Finish type: REG / OT / SO. Points: 2 for any win, 1 for OT/SO loss, 0 for regulation loss.")
    lines.append("- Percentage fields (PP%, PK%, SV%, shooting %): stored as 0-100 where the source provides numerator/denominator, that is recorded too.")
    lines.append("- Goalie appearances are not team games; goalie goals allowed can differ from team goals allowed (empty-net goals, attribution).")
    lines.append("- Traded players: Dallas-only contributions kept separate from full-season production.")
    lines.append("")
    lines.append("## Cleaning, missing values, duplicates, overtime/shootout adjustments")
    lines.append("- Not applicable: no real data was collected, so no cleaning was performed.")
    lines.append("- Planned: shootout decision goals excluded from Poisson fits; game-log totals reconciled to official NHL season totals; regulation goals at 60 minutes distinguished from displayed final scores.")
    lines.append("")
    lines.append("## Source reconciliation")
    lines.append("- Not performed: no real game-log or team-total files exist to reconcile.")
    lines.append("- Proposal-claimed 2025-26 values (273 GF, 222 GA, 50-20-12, 112 points) are treated as unverified and are not hard-coded anywhere.")
    lines.append("")
    lines.append("## Data-completeness checklist (A-G)")
    lines.append("| Dataset | Required | Collected | Status | Exception |")
    lines.append("|---------|----------|-----------|--------|-----------|")
    for key in ["A", "B", "C", "D", "E", "F", "G"]:
        got = any(s.get("dataset") == key and s.get("ok") for s in sources)
        lines.append(f"| {key} | Yes | {'Yes' if got else 'No'} | {'Complete' if got else 'BLOCKED'} | Source unreachable ({COLLECTION_DATE}) |")
    lines.append("")
    lines.append("Every dataset A-G is blocked by the same network failure; no substitute source was reachable either.")
    lines.append("")
    lines.append("## Blocker summary and next step")
    lines.append("- Blocker: NHL.com and Hockey-Reference are unreachable from this environment (SSL/connection errors after bounded retries).")
    lines.append("- Effect: datasets A-G are not collected; the data report cannot describe observed team/game/player/goalie values.")
    lines.append("- Forecast results, figures, and the backtest cannot be run on real data until the blocker clears.")
    lines.append("- Next step: re-run `python -m stars_forecast collect-data` from a network with NHL.com/Hockey-Reference access, then `validate-data` and `data-report`.")
    lines.append("")
    lines.append("## Artifacts")
    lines.append("- data/raw/collection_manifest.json — attempted sources and outcomes")
    lines.append("- data/raw/collection_blocker.json — blocker evidence")
    lines.append("- outputs/qa/data-validation.json — validation contracts (pending real inputs)")
    lines.append("")
    REPORT_PATH.write_text("\n".join(lines) + "\n")
    print(f"[data-report] wrote {REPORT_PATH}")
    return 0
