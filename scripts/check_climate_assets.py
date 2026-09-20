#!/usr/bin/env python3
"""Validate climate-series freshness and recent-window coverage before publication."""

from __future__ import annotations

import argparse
import math
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def fraction(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or not 0 < parsed <= 1:
        raise argparse.ArgumentTypeError("must be in (0, 1]")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root-dir", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--target-date", default=datetime.now(timezone.utc).date().isoformat())
    parser.add_argument("--window-days", type=positive_int, default=20)
    parser.add_argument("--max-ppt-lag-days", type=positive_int, default=7)
    parser.add_argument("--max-soil-lag-days", type=positive_int, default=10)
    parser.add_argument("--min-window-coverage", type=fraction, default=0.5)
    return parser.parse_args()


def load_daily_csv(path: Path, date_column: str, value_column: str) -> pd.DataFrame:
    if not path.exists():
        raise ValueError(f"missing file: {path}")
    frame = pd.read_csv(path)
    missing = [name for name in (date_column, value_column) if name not in frame.columns]
    if missing:
        raise ValueError(f"{path}: missing columns {missing}")

    frame = frame[[date_column, value_column]].copy()
    frame[date_column] = pd.to_datetime(frame[date_column], errors="coerce").dt.normalize()
    frame[value_column] = pd.to_numeric(frame[value_column], errors="coerce")
    if frame[date_column].isna().any():
        raise ValueError(f"{path}: invalid dates present")
    if frame[date_column].duplicated().any():
        duplicated = frame.loc[frame[date_column].duplicated(), date_column].dt.strftime("%Y-%m-%d").tolist()
        raise ValueError(f"{path}: duplicate dates {duplicated[:5]}")
    if not frame[date_column].is_monotonic_increasing:
        raise ValueError(f"{path}: dates are not sorted")
    return frame


def describe_series(
    label: str,
    frame: pd.DataFrame,
    date_column: str,
    value_column: str,
    target: pd.Timestamp,
    window_days: int,
    max_lag_days: int,
    min_window_coverage: float,
    errors: list[str],
) -> tuple[pd.Timestamp | None, int]:
    valid = frame.dropna(subset=[value_column])
    if valid.empty:
        errors.append(f"{label}: no numeric observations")
        return None, 0

    latest = valid[date_column].max()
    lag_days = int((target - latest).days)
    window_start = target - pd.Timedelta(days=window_days)
    recent = valid[(valid[date_column] >= window_start) & (valid[date_column] < target)]
    min_points = max(1, math.ceil(window_days * min_window_coverage))

    print(
        f"[INFO] {label}: latest={latest.date().isoformat()} lag_days={lag_days} "
        f"window_points={len(recent)}/{window_days} required={min_points}"
    )
    if lag_days < 0:
        errors.append(f"{label}: latest observation is after target date")
    elif lag_days > max_lag_days:
        errors.append(f"{label}: stale by {lag_days} days (maximum {max_lag_days})")
    if len(recent) < min_points:
        errors.append(f"{label}: recent coverage too sparse ({len(recent)} < {min_points})")
    return latest, len(recent)


def main() -> int:
    args = parse_args()
    root = args.root_dir.resolve()
    try:
        target = pd.Timestamp(date.fromisoformat(args.target_date))
    except ValueError as exc:
        print(f"[ERROR] invalid --target-date {args.target_date!r}: {exc}", file=sys.stderr)
        return 2

    errors: list[str] = []
    try:
        ppt = load_daily_csv(
            root / "prism_precipitation_santa_cruz_1987_2023.csv", "Date", "PRCP_mm"
        )
        soil = load_daily_csv(
            root / "soil_moisture_data/soil_moisture_big_trees_daily_avg_1987_2023.csv",
            "Date",
            "Daily_Avg_Soil_Moisture",
        )
        combined_ppt = load_daily_csv(
            root / "climate_daily_ppt_soil.csv", "timestamp", "daily_avg_ppt"
        )
        combined_soil = load_daily_csv(
            root / "climate_daily_ppt_soil.csv", "timestamp", "daily_avg_soil_ERA5"
        )
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    ppt_latest, _ = describe_series(
        "PRISM precipitation",
        ppt,
        "Date",
        "PRCP_mm",
        target,
        args.window_days,
        args.max_ppt_lag_days,
        args.min_window_coverage,
        errors,
    )
    soil_latest, _ = describe_series(
        "ERA5-Land soil moisture",
        soil,
        "Date",
        "Daily_Avg_Soil_Moisture",
        target,
        args.window_days,
        args.max_soil_lag_days,
        args.min_window_coverage,
        errors,
    )
    combined_ppt_latest, _ = describe_series(
        "combined precipitation",
        combined_ppt,
        "timestamp",
        "daily_avg_ppt",
        target,
        args.window_days,
        args.max_ppt_lag_days,
        args.min_window_coverage,
        errors,
    )
    combined_soil_latest, _ = describe_series(
        "combined soil moisture",
        combined_soil,
        "timestamp",
        "daily_avg_soil_ERA5",
        target,
        args.window_days,
        args.max_soil_lag_days,
        args.min_window_coverage,
        errors,
    )

    if ppt_latest != combined_ppt_latest:
        errors.append(
            "combined precipitation endpoint does not match the canonical PRISM endpoint "
            f"({combined_ppt_latest} != {ppt_latest})"
        )
    if soil_latest != combined_soil_latest:
        errors.append(
            "combined soil endpoint does not match the canonical ERA5 endpoint "
            f"({combined_soil_latest} != {soil_latest})"
        )

    if errors:
        for error in errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        return 1
    print("[OK] climate assets are fresh, internally consistent, and adequately covered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
