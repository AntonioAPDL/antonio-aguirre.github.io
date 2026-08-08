#!/usr/bin/env python3
"""Check live USGS observations and optional Big Trees forecast overlay health."""

from __future__ import annotations

import argparse
import http.client
import json
import math
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_USGS_URL = "https://waterservices.usgs.gov/nwis/iv/"


def parse_time(value: Any) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    if len(text) > 10 and text[10] == " ":
        text = text[:10] + "T" + text[11:]
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def age_hours(stamp: datetime) -> float:
    return (datetime.now(timezone.utc) - stamp).total_seconds() / 3600.0


def fetch_json(url: str, timeout_sec: int, retries: int) -> dict[str, Any]:
    headers = {
        "Accept": "application/json",
        "User-Agent": "antonio-de-leon-site-health/1.0",
    }
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout_sec) as response:
                payload = response.read().decode("utf-8")
            data = json.loads(payload)
            if not isinstance(data, dict):
                raise ValueError(f"expected JSON object, got {type(data).__name__}")
            return data
        except (
            OSError,
            http.client.IncompleteRead,
            urllib.error.HTTPError,
            urllib.error.URLError,
            json.JSONDecodeError,
            ValueError,
        ) as exc:
            last_error = exc
            if attempt >= retries:
                break
            time.sleep(min(8, 2**attempt))
    raise RuntimeError(f"failed to fetch {url}: {last_error}")


def load_json_source(source: str, timeout_sec: int, retries: int) -> dict[str, Any]:
    if source.startswith(("http://", "https://")):
        return fetch_json(source, timeout_sec=timeout_sec, retries=retries)
    path = Path(source)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def normalize_units(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = text.replace("³", "3").replace("^3", "3")
    text = " ".join(text.replace("\u00a0", " ").split())
    if text in {"ft3/s", "ft3 s-1", "ft3s-1", "cfs"}:
        return "cfs"
    if text in {"ft", "feet"}:
        return "ft"
    return text


def usgs_url(site: str, parameter: str, period: str) -> str:
    query = urllib.parse.urlencode(
        {
            "format": "json",
            "sites": site,
            "parameterCd": parameter,
            "period": period,
            "siteStatus": "all",
        }
    )
    return f"{DEFAULT_USGS_URL}?{query}"


def check_usgs(args: argparse.Namespace, errors: list[str]) -> None:
    url = usgs_url(args.site, args.parameter, args.period)
    data = fetch_json(url, timeout_sec=args.timeout_sec, retries=args.retries)
    series_list = ((data.get("value") or {}).get("timeSeries") or [])
    if not series_list:
        errors.append("USGS payload has no timeSeries entries")
        return
    series = series_list[0]
    values = (((series.get("values") or [{}])[0]).get("value") or [])
    points: list[tuple[datetime, float]] = []
    for row in values:
        stamp = parse_time(row.get("dateTime"))
        try:
            value = float(row.get("value"))
        except (TypeError, ValueError):
            continue
        if stamp is None or not math.isfinite(value):
            continue
        points.append((stamp, value))
    points.sort(key=lambda item: item[0])
    if not points:
        errors.append("USGS payload has no numeric observations")
        return

    variable = series.get("variable") or {}
    unit = normalize_units((variable.get("unit") or {}).get("unitCode"))
    expected = "ft" if args.parameter == "00065" else "cfs"
    if unit != expected:
        errors.append(f"USGS unit mismatch: expected {expected}, found {unit or 'unknown'}")

    last_stamp, last_value = points[-1]
    last_age = age_hours(last_stamp)
    print(
        "[INFO] USGS latest: "
        f"site={args.site} parameter={args.parameter} points={len(points)} "
        f"last={last_stamp.isoformat()} age_h={last_age:.2f} value={last_value:g} unit={unit}"
    )
    if last_age < -1:
        errors.append("USGS latest timestamp is unexpectedly in the future")
    if last_age > args.max_observation_age_hours:
        errors.append(
            f"USGS observations stale: age={last_age:.1f}h "
            f"> {args.max_observation_age_hours:.1f}h"
        )


def streamflow_count(data: dict[str, Any], range_name: str, key: str) -> int:
    block = (data.get("ranges") or {}).get(range_name) or {}
    if not isinstance(block, dict):
        return 0
    series = block.get(key) or []
    return len(series) if isinstance(series, list) else 0


def forecast_reference_time(data: dict[str, Any]) -> datetime | None:
    candidates: list[Any] = [
        data.get("generated_at_utc"),
        data.get("generated_utc"),
        data.get("init_time_utc"),
    ]
    init_times = data.get("init_times")
    if isinstance(init_times, dict):
        candidates.extend(init_times.values())
    parsed = [parse_time(value) for value in candidates]
    parsed = [value for value in parsed if value is not None]
    return max(parsed) if parsed else None


def check_forecast(source: str, args: argparse.Namespace, errors: list[str]) -> None:
    data = load_json_source(source, timeout_sec=args.timeout_sec, retries=args.retries)
    units = data.get("units")
    if units != ["ft3/s"]:
        errors.append(f"{source}: expected units ['ft3/s'], found {units!r}")

    stamp = forecast_reference_time(data)
    if stamp is None:
        errors.append(f"{source}: no parseable forecast timestamp")
        age = float("nan")
    else:
        age = age_hours(stamp)
        if age < -1:
            errors.append(f"{source}: forecast timestamp is unexpectedly in the future")
        if age > args.max_forecast_age_hours:
            errors.append(
                f"{source}: forecast stale: age={age:.1f}h > {args.max_forecast_age_hours:.1f}h"
            )

    analysis_n = streamflow_count(data, "analysis", "deterministic")
    short_n = streamflow_count(data, "short", "deterministic")
    medium_n = streamflow_count(data, "medium_range", "p50")
    long_n = streamflow_count(data, "long_range", "p50")
    print(
        "[INFO] forecast: "
        f"source={source} ref={stamp.isoformat() if stamp else 'NA'} "
        f"age_h={age:.2f} analysis={analysis_n} short={short_n} "
        f"medium_p50={medium_n} long_p50={long_n}"
    )
    if analysis_n <= 0 and short_n <= 0:
        errors.append(f"{source}: analysis or short-range guidance is required")
    if args.require_extended_forecast and (medium_n <= 0 or long_n <= 0):
        errors.append(f"{source}: medium/long guidance incomplete")


def positive_float(value: str) -> float:
    out = float(value)
    if not math.isfinite(out) or out <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return out


def positive_int(value: str) -> int:
    out = int(value)
    if out <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", default="11160500")
    parser.add_argument("--parameter", default="00060")
    parser.add_argument("--period", default="P2D")
    parser.add_argument("--timeout-sec", type=positive_int, default=30)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--max-observation-age-hours", type=positive_float, default=6.0)
    parser.add_argument("--max-forecast-age-hours", type=positive_float, default=36.0)
    parser.add_argument("--forecast-json", help="Local forecast JSON path to validate.")
    parser.add_argument("--forecast-url", help="Remote forecast JSON URL to validate.")
    parser.add_argument("--require-extended-forecast", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    check_usgs(args, errors)
    if args.forecast_json:
        check_forecast(args.forecast_json, args, errors)
    if args.forecast_url:
        check_forecast(args.forecast_url, args, errors)

    if errors:
        for error in errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        return 1
    print("[OK] USGS plot health checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
