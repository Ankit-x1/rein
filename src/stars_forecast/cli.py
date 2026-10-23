"""Command-line interface for the Dallas Stars forecasting project."""

from __future__ import annotations

import argparse
import sys

from .collect import cmd_collect
from .validate import cmd_validate
from .report import cmd_data_report
from .run_all import cmd_run_all


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stars_forecast",
        description="Dallas Stars 2026-27 regular-season forecasting model.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_collect = sub.add_parser("collect-data", help="Attempt real source downloads and cache raw responses")
    p_collect.add_argument("--retries", type=int, default=3)
    p_collect.add_argument("--timeout", type=int, default=15)
    p_collect.set_defaults(func=cmd_collect)

    p_validate = sub.add_parser("validate-data", help="Validate cleaned CSVs under data/processed/")
    p_validate.set_defaults(func=cmd_validate)

    p_report = sub.add_parser("data-report", help="Regenerate docs/data-report.md from data + validation evidence")
    p_report.set_defaults(func=cmd_data_report)

    p_run = sub.add_parser("run-all", help="Diagnostics, scenarios, backtest, figures, tables, summary")
    p_run.add_argument("--n-seasons", type=int, default=10000)
    p_run.add_argument("--seed", type=int, default=3315)
    p_run.set_defaults(func=cmd_run_all)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
