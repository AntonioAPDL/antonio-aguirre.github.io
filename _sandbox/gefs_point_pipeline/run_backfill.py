#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import sys
from pathlib import Path
from typing import Optional


SCRIPT_PATH = Path(__file__).resolve()
PIPELINE_DIR = SCRIPT_PATH.parent
SRC_DIR = PIPELINE_DIR / "src"
if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))

from src.backfill import (  # noqa: E402
    BackfillOptions,
    resolve_backfill_window,
    run_backfill,
)
from src.runner import parse_init_time, setup_logging  # noqa: E402


def _parse_dt(value: Optional[str]) -> Optional[dt.datetime]:
    if value is None:
        return None
    parsed = parse_init_time(value)
    if parsed is None:
        return None
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Backfill GEFS point ensembles into compact per-cycle history without retaining raw files."
        )
    )
    parser.add_argument(
        "--gefs-config",
        default=str(PIPELINE_DIR / "config" / "gefs.yaml"),
        help="Path to GEFS pipeline config YAML",
    )
    parser.add_argument(
        "--points-config",
        default=str(PIPELINE_DIR / "config" / "points.yaml"),
        help="Path to points config YAML",
    )
    parser.add_argument(
        "--point-id",
        default="big_trees",
        help="Point id from points.yaml",
    )
    parser.add_argument(
        "--pilot-days",
        type=int,
        default=None,
        help="Pilot mode for last N days using latest complete cycle as end.",
    )
    parser.add_argument(
        "--start-init",
        default=None,
        help="Start cycle init UTC (ISO8601), e.g. 2017-01-01T00:00:00Z",
    )
    parser.add_argument(
        "--end-init",
        default=None,
        help="End cycle init UTC (ISO8601). Default is latest complete cycle.",
    )
    parser.add_argument(
        "--history-root",
        default=str((PIPELINE_DIR.parents[1] / "data" / "_sandbox_gefs" / "history").resolve()),
        help="Root directory for historical point-level backfill artifacts.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=2,
        help="Process workers (cycles in parallel).",
    )
    parser.add_argument(
        "--cycle-max-workers",
        type=int,
        default=2,
        help="Thread workers per cycle extraction.",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=None,
        help="Optional override for retry attempts per request.",
    )
    parser.add_argument(
        "--retry-backoff-sec",
        type=float,
        default=None,
        help="Optional override for exponential retry backoff base seconds.",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=1,
        help="Write status snapshot every N completed cycles.",
    )
    parser.add_argument(
        "--run-profile",
        default="full",
        choices=["full", "smoke"],
        help="Cycle extraction profile. Use smoke for faster benchmarking.",
    )
    parser.add_argument(
        "--retry-failed-only",
        action="store_true",
        help="Only process cycles that currently have .failed_* history entries.",
    )
    parser.add_argument(
        "--cleanup-stale-tmp-hours",
        type=float,
        default=6.0,
        help="Delete stale .tmp_* cycle dirs older than this many hours before each run.",
    )
    parser.add_argument(
        "--keep-failed-dirs",
        type=int,
        default=200,
        help="Retain this many .failed_* cycle dirs (global) after each run.",
    )
    parser.add_argument(
        "--wait-for-lock",
        action="store_true",
        help="Wait for lock if another backfill run is active. Default is skip-locked.",
    )
    parser.add_argument("--force", action="store_true", help="Re-run cycles even if already successful.")
    parser.add_argument(
        "--run-label",
        default="gefs_history_backfill",
        help="Label embedded in status/benchmark files.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    setup_logging(args.log_level)

    repo_root = PIPELINE_DIR.parents[1]
    start_init = _parse_dt(args.start_init)
    end_init = _parse_dt(args.end_init)

    start_cycle, end_cycle = resolve_backfill_window(
        cfg_path=Path(args.gefs_config),
        start_init_utc=start_init,
        end_init_utc=end_init,
        pilot_days=args.pilot_days,
    )

    logging.info(
        "Resolved backfill window: start=%s end=%s pilot_days=%s",
        start_cycle.isoformat(),
        end_cycle.isoformat(),
        args.pilot_days,
    )

    options = BackfillOptions(
        repo_root=repo_root,
        gefs_config=Path(args.gefs_config),
        points_config=Path(args.points_config),
        point_id=str(args.point_id),
        start_init_utc=start_cycle,
        end_init_utc=end_cycle,
        history_root=Path(args.history_root),
        workers=max(1, int(args.workers)),
        cycle_max_workers=max(1, int(args.cycle_max_workers)),
        retries=args.retries,
        retry_backoff_sec=args.retry_backoff_sec,
        force=bool(args.force),
        progress_every=max(1, int(args.progress_every)),
        run_label=str(args.run_label),
        run_profile=str(args.run_profile),
        retry_failed_only=bool(args.retry_failed_only),
        cleanup_stale_tmp_hours=float(args.cleanup_stale_tmp_hours),
        keep_failed_dirs=int(args.keep_failed_dirs),
        wait_for_lock=bool(args.wait_for_lock),
    )
    summary = run_backfill(options)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
