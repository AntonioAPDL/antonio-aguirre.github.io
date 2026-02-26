#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
PIPELINE_DIR = SCRIPT_PATH.parent
SRC_DIR = PIPELINE_DIR / "src"
if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))

from src.config import load_pipeline_config, load_point_config  # noqa: E402
from src.runner import RunOptions, parse_init_time, run_pipeline, setup_logging  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run latest complete GEFS cycle point extraction for Big Trees."
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
        "--init-time",
        default=None,
        help="Force init time (ISO8601, e.g. 2026-02-23T00:00:00Z)",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite successful existing run")
    parser.add_argument("--smoke", action="store_true", help="Small member/lead subset for validation")
    parser.add_argument(
        "--profile",
        default="full",
        choices=["full", "smoke"],
        help="Run profile. --smoke is retained for backward compatibility.",
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

    pipeline_cfg = load_pipeline_config(Path(args.gefs_config))
    point_cfg = load_point_config(Path(args.points_config), point_id=args.point_id)

    repo_root = PIPELINE_DIR.parents[1]
    options = RunOptions(
        repo_root=repo_root,
        force=bool(args.force),
        smoke=bool(args.smoke),
        run_profile=str(args.profile),
        explicit_init_time_utc=parse_init_time(args.init_time),
    )
    result = run_pipeline(cfg=pipeline_cfg, point=point_cfg, options=options)
    print(f"status={result.status}")
    print(f"run_profile={result.run_profile}")
    print(f"init_time_utc={result.init_time_utc.isoformat()}")
    print(f"run_tag={result.run_tag}")
    print(f"run_dir={result.run_dir}")
    print(f"manifest_path={result.manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
