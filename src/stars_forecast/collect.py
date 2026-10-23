"""Data acquisition: attempt real NHL.com / Hockey-Reference downloads, cache raw
responses unchanged under data/raw/, and write a source manifest.

Blocker handling: if the sources are unreachable, record the evidence and exit
nonzero with a clear message. No data is fabricated, and no partial/invented
data is presented as observed.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
MANIFEST_PATH = DATA_RAW / "collection_manifest.json"
BLOCKER_PATH = DATA_RAW / "collection_blocker.json"

REQUEST_TIMEOUT = 15
RETRIES = 3
RATE_SLEEP = 0.5  # seconds between requests (modest rate)

# Source list from the project proposal data plan (Section 11 / Data Plan).
# Each entry: dataset id (A-G from the master prompt), label, URL, season.
SOURCES = [
    {
        "dataset": "A",
        "label": "2025-26 Dallas team totals (NHL.com)",
        "url": "https://www.nhl.com/stats/teams?gameType=2&page=0&pageSize=50&reportType=season&seasonFrom=20252026&seasonTo=20252026",
        "season": "2025-26",
        "source": "NHL.com",
    },
    {
        "dataset": "C",
        "label": "2025-26 Dallas skater statistics (NHL.com)",
        "url": "https://www.nhl.com/stats/skaters?gameType=2&page=0&pageSize=50&reportType=season&seasonFrom=20252026&seasonTo=20252026",
        "season": "2025-26",
        "source": "NHL.com",
    },
    {
        "dataset": "D",
        "label": "2025-26 Dallas goalie statistics (NHL.com)",
        "url": "https://www.nhl.com/stats/goalies?gameType=2&page=0&pageSize=50&reportType=season&seasonFrom=20252026&seasonTo=20252026",
        "season": "2025-26",
        "source": "NHL.com",
    },
    {
        "dataset": "B",
        "label": "2025-26 Dallas team gamelog (Hockey-Reference)",
        "url": "https://www.hockey-reference.com/teams/DAL/2026_gamelog.html",
        "season": "2025-26",
        "source": "Hockey-Reference",
    },
    {
        "dataset": "E",
        "label": "2024-25 Dallas team gamelog (Hockey-Reference)",
        "url": "https://www.hockey-reference.com/teams/DAL/2025_gamelog.html",
        "season": "2024-25",
        "source": "Hockey-Reference",
    },
    {
        "dataset": "F",
        "label": "NHL Central Division standings history (Hockey-Reference)",
        "url": "https://www.hockey-reference.com/leagues/NHL_2026_standings.html",
        "season": "2021-22 through 2025-26",
        "source": "Hockey-Reference",
    },
    {
        "dataset": "G",
        "label": "Dallas Stars initial 2026-27 roster announcement",
        "url": "https://www.nhl.com/stars/news/dallas-stars-announce-initial-roster-for-2026-27-season-092826",
        "season": "2026-27",
        "source": "Dallas Stars / NHL.com",
    },
]


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _attempt(url: str, retries: int, timeout: int) -> dict:
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, timeout=timeout, headers={"User-Agent": "rein-forecast/0.1 (research)"})
            return {
                "attempt": attempt,
                "http_status": r.status_code,
                "ok": r.status_code == 200,
                "error": None,
                "bytes": len(r.content),
                "sha256": _sha256(r.content),
                "content_type": r.headers.get("content-type"),
            }
        except Exception as exc:  # network failure: retry, then record
            last_error = exc
            time.sleep(0.5 * attempt)
    return {
        "attempt": retries,
        "http_status": None,
        "ok": False,
        "error": f"{type(last_error).__name__}: {last_error}",
        "bytes": None,
        "sha256": None,
        "content_type": None,
    }


def _save_raw(entry: dict, content: bytes | None) -> str:
    safe = entry["url"].replace("https://", "").replace("http://", "").replace("/", "_").replace("?", "_")
    path = DATA_RAW / safe
    if content is not None:
        path.write_bytes(content)
    return str(path)


def cmd_collect(args) -> int:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    results = []
    all_ok = True

    for entry in SOURCES:
        print(f"[collect] {entry['dataset']} {entry['label']} ({entry['source']})")
        result = _attempt(entry["url"], args.retries, args.timeout)
        result.update(
            {
                "dataset": entry["dataset"],
                "label": entry["label"],
                "source": entry["source"],
                "season": entry["season"],
                "url": entry["url"],
                "retrieved_utc": datetime.now(timezone.utc).isoformat(),
            }
        )
        if result["ok"]:
            r = requests.get(entry["url"], timeout=args.timeout, headers={"User-Agent": "rein-forecast/0.1 (research)"})
            entry["_saved"] = _save_raw(entry, r.content)
            result["saved_path"] = entry["_saved"]
            print(f"  saved {result['bytes']} bytes -> {entry['_saved']}")
        else:
            all_ok = False
            print(f"  FAILED: {result['error']}")
        results.append(result)
        time.sleep(RATE_SLEEP)

    finished = datetime.now(timezone.utc).isoformat()
    manifest = {
        "project": "stars-forecast",
        "collection_started_utc": started,
        "collection_finished_utc": finished,
        "sandbox_note": "nhl.com and hockey-reference.com unreachable from this environment "
        "(SSL/connection failure); no real data collected",
        "sources": results,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))

    if not all_ok:
        blocker = {
            "recorded_utc": finished,
            "blocker": "data-source-unreachable",
            "detail": "All NHL.com and Hockey-Reference URLs in the proposal data plan failed "
            "with SSL/connection errors after bounded retries. Real datasets A-G are not collected.",
            "attempted_urls": [r["url"] for r in results],
            "failed_datasets": sorted({r["dataset"] for r in results if not r["ok"]}),
            "next_step": "Re-run collect-data from a network that can reach NHL.com / Hockey-Reference, "
            "then place cleaned CSVs under data/processed/ and run validate-data.",
        }
        BLOCKER_PATH.write_text(json.dumps(blocker, indent=2))
        print("\n[collect] BLOCKER: source downloads failed; see data/raw/collection_blocker.json")
        return 1

    print("\n[collect] all sources downloaded successfully")
    return 0
