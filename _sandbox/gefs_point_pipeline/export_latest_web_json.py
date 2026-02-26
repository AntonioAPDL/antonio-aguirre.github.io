#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Dict, List

import pandas as pd


SCRIPT_PATH = Path(__file__).resolve()
PIPELINE_DIR = SCRIPT_PATH.parent
if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))

from src.config import load_pipeline_config  # noqa: E402
from src.storage import read_manifest  # noqa: E402


def _series_points(series: pd.Series) -> List[Dict[str, float]]:
    out: List[Dict[str, float]] = []
    for ts, value in series.sort_index().items():
        if pd.isna(value):
            continue
        out.append({"t": pd.Timestamp(ts).isoformat(), "v": float(value)})
    return out


def _quantile_payload(df: pd.DataFrame) -> Dict[str, List[Dict[str, float]]]:
    pivot = df.pivot_table(index="valid_time_utc", columns="member", values="value", aggfunc="mean")
    return {
        "mean": _series_points(pivot.mean(axis=1)),
        "p10": _series_points(pivot.quantile(0.1, axis=1)),
        "p50": _series_points(pivot.quantile(0.5, axis=1)),
        "p90": _series_points(pivot.quantile(0.9, axis=1)),
    }


def _latest_run_tag(runs_root: Path, pointer_name: str) -> str:
    pointer = runs_root / pointer_name
    if pointer.exists():
        value = pointer.read_text(encoding="utf-8").strip()
        if value:
            return value
    raise FileNotFoundError(f"latest run pointer not found at {pointer}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export GEFS latest full run to web JSON format.")
    parser.add_argument(
        "--gefs-config",
        default=str(PIPELINE_DIR / "config" / "gefs.yaml"),
        help="Path to GEFS config file",
    )
    parser.add_argument(
        "--run-tag",
        default=None,
        help="Optional run tag (YYYYMMDD_HH). Defaults to latest full run pointer.",
    )
    parser.add_argument(
        "--stale-after-hours",
        type=int,
        default=12,
        help="Staleness threshold used by web panel metadata.",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Optional override output JSON path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cfg = load_pipeline_config(Path(args.gefs_config))
    repo_root = PIPELINE_DIR.parents[1]
    runs_root = (repo_root / cfg.output.runs_root).resolve()

    run_tag = args.run_tag or _latest_run_tag(runs_root, cfg.runtime.latest_pointer_name)
    run_dir = runs_root / run_tag
    manifest_path = run_dir / "manifest.json"
    member_path = run_dir / "point_member.parquet"
    manifest = read_manifest(manifest_path)
    if manifest.get("status") != "success":
        raise RuntimeError(f"Run manifest is not successful: {manifest_path}")
    if manifest.get("run_profile", "full") != "full":
        raise RuntimeError(f"Expected full run manifest, found profile={manifest.get('run_profile')}")
    if not member_path.exists():
        raise FileNotFoundError(f"Member parquet not found: {member_path}")

    df = pd.read_parquet(member_path)
    if df.empty:
        raise RuntimeError("Member parquet is empty; cannot export web JSON")

    df["valid_time_utc"] = pd.to_datetime(df["valid_time_utc"], utc=True)
    df["init_time_utc"] = pd.to_datetime(df["init_time_utc"], utc=True)
    member_count = int(df["member"].nunique())

    payload: Dict[str, object] = {
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "site_id": str(manifest.get("site_id") or df["site_id"].iloc[0]),
        "init_time_utc": str(manifest.get("init_time_utc") or df["init_time_utc"].iloc[0].isoformat()),
        "member_count": member_count,
        "schema_version": int(manifest.get("schema_version", cfg.runtime.schema_version)),
        "stale_after_hours": int(args.stale_after_hours),
        "missing_levels": (manifest.get("missing_expected_levels", {}) or {}).get("soil_moisture", []),
        "precip": {},
        "soil_moisture": {},
    }

    precip = df[df["variable"] == "APCP"]
    for level, level_df in precip.groupby("level"):
        section = _quantile_payload(level_df)
        section["units"] = str(level_df["units"].dropna().iloc[0]) if not level_df["units"].dropna().empty else ""
        payload["precip"][str(level)] = section

    soil = df[df["variable"] == "SOILW"]
    for level, level_df in soil.groupby("level"):
        section = _quantile_payload(level_df)
        section["units"] = str(level_df["units"].dropna().iloc[0]) if not level_df["units"].dropna().empty else ""
        payload["soil_moisture"][str(level)] = section

    out_path = Path(args.out) if args.out else (repo_root / cfg.output.web_out_dir / cfg.output.web_filename)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"status=success")
    print(f"run_tag={run_tag}")
    print(f"run_dir={run_dir}")
    print(f"out_path={out_path}")
    print(f"member_count={member_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
