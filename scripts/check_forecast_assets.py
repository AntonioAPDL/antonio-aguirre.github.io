#!/usr/bin/env python3
"""Validate public forecast JSON artifacts used by the demos page."""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_time(value: Any) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"{path}: could not parse JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def age_hours(value: datetime) -> float:
    return (datetime.now(timezone.utc) - value).total_seconds() / 3600.0


def check_age(label: str, stamp: datetime | None, max_age_hours: float, errors: list[str]) -> None:
    if stamp is None:
        errors.append(f"{label}: missing timestamp")
        return
    age = age_hours(stamp)
    print(f"[INFO] {label}: {stamp.isoformat()} age_h={age:.2f}")
    if age < -1:
        errors.append(f"{label}: timestamp is unexpectedly in the future")
    if age > max_age_hours:
        errors.append(f"{label}: stale ({age:.1f}h > {max_age_hours:.1f}h)")


def streamflow_count(data: dict[str, Any], range_name: str, key: str) -> int:
    block = (data.get("ranges") or {}).get(range_name) or {}
    if not isinstance(block, dict):
        return 0
    series = block.get(key) or []
    return len(series) if isinstance(series, list) else 0


def check_streamflow(path: Path, max_age_hours: float, require_extended: bool) -> int:
    errors: list[str] = []
    data = load_json(path)
    generated = parse_time(data.get("generated_at_utc") or data.get("generated_utc"))
    check_age(f"{path}: generated_at_utc", generated, max_age_hours, errors)

    units = data.get("units")
    if units != ["ft3/s"]:
        errors.append(f"{path}: expected units ['ft3/s'], found {units!r}")

    analysis_n = streamflow_count(data, "analysis", "deterministic")
    short_n = streamflow_count(data, "short", "deterministic")
    medium_n = streamflow_count(data, "medium_range", "p50")
    long_n = streamflow_count(data, "long_range", "p50")
    print(
        "[INFO] streamflow counts: "
        f"analysis={analysis_n} short={short_n} medium_p50={medium_n} long_p50={long_n}"
    )

    if analysis_n <= 0 and short_n <= 0:
        errors.append(f"{path}: analysis or short-range guidance is required")
    if medium_n <= 0 or long_n <= 0:
        message = f"{path}: medium/long guidance incomplete"
        if require_extended:
            errors.append(message)
        else:
            print(f"[WARN] {message}; partial streamflow artifact accepted")

    if errors:
        for error in errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        return 1
    print(f"[OK] streamflow artifact accepted: {path}")
    return 0


def best_series_count(section: Any) -> int:
    if not isinstance(section, dict):
        return 0
    best = 0
    for level_block in section.values():
        if not isinstance(level_block, dict):
            continue
        for metric in ("p50", "mean", "p10", "p90"):
            series = level_block.get(metric)
            if isinstance(series, list):
                best = max(best, len(series))
    return best


def section_units(section: Any) -> list[str]:
    units: list[str] = []
    if not isinstance(section, dict):
        return units
    for level_block in section.values():
        if not isinstance(level_block, dict):
            continue
        unit = str(level_block.get("units") or "").strip()
        if unit:
            units.append(unit)
    return sorted(set(units))


def precip_has_24h_support(section: Any) -> bool:
    if not isinstance(section, dict):
        return False
    for level_block in section.values():
        if not isinstance(level_block, dict):
            continue
        support = str(level_block.get("time_support") or "").lower()
        if "24-hour" in support:
            return True
    return False


def soil_has_24h_mean_support(section: Any) -> bool:
    if not isinstance(section, dict):
        return False
    for level_block in section.values():
        if not isinstance(level_block, dict):
            continue
        support = str(level_block.get("time_support") or "").lower()
        if "24-hour mean" in support:
            return True
    return False


def check_gefs(
    path: Path,
    max_age_hours: float,
    require_context: bool,
    require_observed: bool,
) -> int:
    errors: list[str] = []
    data = load_json(path)
    generated = parse_time(data.get("generated_at_utc"))
    init_time = parse_time(data.get("init_time_utc"))
    check_age(f"{path}: generated_at_utc", generated, max_age_hours, errors)
    check_age(f"{path}: init_time_utc", init_time, max_age_hours, errors)

    member_count = data.get("member_count")
    if not isinstance(member_count, int) or member_count <= 0:
        errors.append(f"{path}: member_count must be positive")

    precip_n = best_series_count(data.get("precip"))
    soil_n = best_series_count(data.get("soil_moisture"))
    print(f"[INFO] GEFS forecast counts: precip={precip_n} soil={soil_n}")
    print(f"[INFO] GEFS precip units: {section_units(data.get('precip'))}")
    print(f"[INFO] GEFS soil units: {section_units(data.get('soil_moisture'))}")
    if precip_n <= 0:
        errors.append(f"{path}: precipitation forecast series missing")
    if soil_n <= 0:
        errors.append(f"{path}: soil-moisture forecast series missing")

    observed = data.get("observed_retrospective") or {}
    observed_ppt_n = 0
    observed_soil_n = 0
    if isinstance(observed, dict):
        ppt = observed.get("daily_avg_ppt")
        observed_ppt_n = len(ppt) if isinstance(ppt, list) else 0
        for key in (
            "daily_avg_soil_ERA5",
            "daily_avg_soil_NWM_SOIL_M",
            "daily_avg_soil_NWM_SOIL_W",
        ):
            series = observed.get(key)
            if isinstance(series, list):
                observed_soil_n = max(observed_soil_n, len(series))
    print(f"[INFO] GEFS observed context counts: precip={observed_ppt_n} soil={observed_soil_n}")
    if require_observed and observed_ppt_n <= 0 and observed_soil_n <= 0:
        errors.append(f"{path}: observed retrospective precipitation or soil series required")
    if require_observed and observed_ppt_n > 0 and not precip_has_24h_support(data.get("precip")):
        errors.append(
            f"{path}: observed PRISM precipitation is daily, so GEFS precipitation must be exported as 24-hour totals"
        )
    if require_observed and observed_soil_n > 0 and not soil_has_24h_mean_support(data.get("soil_moisture")):
        errors.append(
            f"{path}: observed ERA5 soil moisture is daily, so GEFS soil moisture must be exported as 24-hour means"
        )

    context_summary = data.get("gefs_analysis_context_summary") or {}
    context_status = context_summary.get("status") if isinstance(context_summary, dict) else None
    if context_status and context_status != "ok":
        message = f"{path}: GEFS analysis context status={context_status}"
        if require_context:
            errors.append(message)
        else:
            print(f"[INFO] {message}; analysis context is not required for the public chart")
    for warning in data.get("quality_warnings") or []:
        if isinstance(warning, str) and warning.strip():
            print(f"[WARN] {warning.strip()}")

    if errors:
        for error in errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        return 1
    print(f"[OK] GEFS artifact accepted: {path}")
    return 0


def positive_float(value: str) -> float:
    out = float(value)
    if not math.isfinite(out) or out <= 0:
        raise argparse.ArgumentTypeError("must be a positive finite number")
    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--streamflow", type=Path, help="Path to Big Trees streamflow JSON")
    parser.add_argument("--gefs", type=Path, help="Path to GEFS Big Trees JSON")
    parser.add_argument("--max-age-hours", type=positive_float, default=36.0)
    parser.add_argument("--require-extended-streamflow", action="store_true")
    parser.add_argument("--require-gefs-context", action="store_true")
    parser.add_argument("--require-observed-retrospective", action="store_true")
    args = parser.parse_args()
    if not args.streamflow and not args.gefs:
        parser.error("provide --streamflow, --gefs, or both")
    return args


def main() -> int:
    args = parse_args()
    rc = 0
    if args.streamflow:
        rc |= check_streamflow(args.streamflow, args.max_age_hours, args.require_extended_streamflow)
    if args.gefs:
        rc |= check_gefs(
            args.gefs,
            args.max_age_hours,
            args.require_gefs_context,
            args.require_observed_retrospective,
        )
    return 1 if rc else 0


if __name__ == "__main__":
    raise SystemExit(main())
