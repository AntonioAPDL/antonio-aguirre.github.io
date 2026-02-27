#!/usr/bin/env python3
"""Build Big Trees streamflow forecast JSON directly from NOAA NWPS APIs.

This script is a robust in-repo fallback when the legacy
_sandbox/nws_ensemble_point extractor is unavailable.
"""

from __future__ import annotations

import argparse
import json
import math
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


DEFAULT_GAUGE_ID = "BTEC1"
DEFAULT_REACH_ID = "17682474"
DEFAULT_OUTPUT = "data/_sandbox_nws/big_trees_latest.json"
DEFAULT_TIMEOUT_SEC = 30
DEFAULT_RETRIES = 4
DEFAULT_ANALYSIS_POINTS = 120


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build assets/data/forecasts/big_trees_latest.json from NWPS APIs."
    )
    parser.add_argument("--gauge-id", default=DEFAULT_GAUGE_ID)
    parser.add_argument("--reach-id", default=DEFAULT_REACH_ID)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout-sec", type=int, default=DEFAULT_TIMEOUT_SEC)
    parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES)
    parser.add_argument("--analysis-points", type=int, default=DEFAULT_ANALYSIS_POINTS)
    return parser.parse_args()


def parse_time(raw: Any) -> Optional[datetime]:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def iso_ts(raw: Any) -> Optional[str]:
    dt = parse_time(raw)
    if not dt:
        return None
    return dt.isoformat(timespec="seconds")


def init_ts(raw: Any) -> Optional[str]:
    dt = parse_time(raw)
    if not dt:
        return None
    return dt.strftime("%Y-%m-%d %H:%M:%S+00:00")


def to_float(raw: Any) -> Optional[float]:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value):
        return None
    return value


def fetch_json(url: str, timeout_sec: int, retries: int) -> Dict[str, Any]:
    headers = {
        "User-Agent": "antonio-aguirre-forecast-updater/1.0",
        "Accept": "application/json",
    }
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                payload = resp.read().decode("utf-8")
            data = json.loads(payload)
            if not isinstance(data, dict):
                raise ValueError(f"Expected JSON object from {url}, got {type(data).__name__}")
            return data
        except urllib.error.HTTPError as exc:
            retriable = exc.code in {429, 500, 502, 503, 504}
            if (not retriable) or attempt >= retries:
                raise
        except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
            if attempt >= retries:
                raise
        time.sleep(2**attempt)
    raise RuntimeError(f"Unable to fetch {url} after retries")


def extract_stageflow_secondary(series_obj: Dict[str, Any], scale: float = 1000.0) -> List[Dict[str, float]]:
    out: List[Dict[str, float]] = []
    for row in series_obj.get("data", []) or []:
        ts = iso_ts(row.get("validTime"))
        val = to_float(row.get("secondary"))
        if ts is None or val is None:
            continue
        out.append({"t": ts, "v": float(val * scale)})
    out.sort(key=lambda row: row["t"])
    return out


def extract_reach_flow_series(series_obj: Dict[str, Any]) -> List[Dict[str, float]]:
    out: List[Dict[str, float]] = []
    for row in series_obj.get("data", []) or []:
        ts = iso_ts(row.get("validTime"))
        val = to_float(row.get("flow"))
        if ts is None or val is None:
            continue
        out.append({"t": ts, "v": float(val)})
    out.sort(key=lambda row: row["t"])
    return out


def _quantile(sorted_values: List[float], q: float) -> float:
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    pos = (len(sorted_values) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return float(sorted_values[lo])
    frac = pos - lo
    return float(sorted_values[lo] * (1.0 - frac) + sorted_values[hi] * frac)


def quantile_series(member_series: Iterable[List[Dict[str, float]]]) -> Tuple[List[Dict[str, float]], List[Dict[str, float]], List[Dict[str, float]]]:
    by_time: Dict[str, List[float]] = {}
    for series in member_series:
        for row in series:
            by_time.setdefault(row["t"], []).append(float(row["v"]))
    p10: List[Dict[str, float]] = []
    p50: List[Dict[str, float]] = []
    p90: List[Dict[str, float]] = []
    for ts in sorted(by_time.keys()):
        values = sorted(v for v in by_time[ts] if math.isfinite(v))
        if not values:
            continue
        p10.append({"t": ts, "v": _quantile(values, 0.10)})
        p50.append({"t": ts, "v": _quantile(values, 0.50)})
        p90.append({"t": ts, "v": _quantile(values, 0.90)})
    return p10, p50, p90


def build_range_quantiles(range_obj: Dict[str, Any], label: str) -> Tuple[List[Dict[str, float]], List[Dict[str, float]], List[Dict[str, float]], Optional[str], List[str]]:
    notes: List[str] = []
    member_series: List[List[Dict[str, float]]] = []
    mean_series = extract_reach_flow_series((range_obj or {}).get("mean", {}) or {})
    init_time = init_ts(((range_obj or {}).get("mean", {}) or {}).get("referenceTime"))

    for key, value in (range_obj or {}).items():
        if not key.startswith("member"):
            continue
        series = extract_reach_flow_series(value or {})
        if series:
            member_series.append(series)
            if init_time is None:
                init_time = init_ts((value or {}).get("referenceTime"))

    if not member_series and mean_series:
        member_series = [mean_series]
        notes.append(f"{label}: member series unavailable; using mean as p10/p50/p90 proxy.")

    if not member_series:
        notes.append(f"{label}: no data available from reach streamflow endpoint.")
        return [], [], [], init_time, notes

    p10, p50, p90 = quantile_series(member_series)
    if not p50:
        notes.append(f"{label}: unable to derive quantiles from available series.")
    return p10, p50, p90, init_time, notes


def dedupe(seq: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for item in seq:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def fetch_reach_streamflow_series(reach_id: str, series_name: str, timeout_sec: int, retries: int) -> Dict[str, Any]:
    url = f"https://api.water.noaa.gov/nwps/v1/reaches/{reach_id}/streamflow?series={series_name}"
    return fetch_json(url, timeout_sec=timeout_sec, retries=retries)


def build_payload(args: argparse.Namespace) -> Dict[str, Any]:
    notes: List[str] = []
    provider_mix = ["nwps"]

    stageflow_url = f"https://api.water.noaa.gov/nwps/v1/gauges/{args.gauge_id}/stageflow"
    stageflow = fetch_json(stageflow_url, timeout_sec=args.timeout_sec, retries=args.retries)

    reach_streamflow: Dict[str, Any] = {
        "analysisAssimilation": {},
        "shortRange": {},
        "mediumRange": {},
        "longRange": {},
        "mediumRangeBlend": {},
    }
    fetch_map = {
        "analysis_assimilation": "analysisAssimilation",
        "short_range": "shortRange",
        "medium_range": "mediumRange",
        "long_range": "longRange",
        "medium_range_blend": "mediumRangeBlend",
    }
    reach_fetch_success = False
    for series_query, json_key in fetch_map.items():
        try:
            partial = fetch_reach_streamflow_series(
                str(args.reach_id),
                series_name=series_query,
                timeout_sec=args.timeout_sec,
                retries=args.retries,
            )
            reach_streamflow[json_key] = partial.get(json_key, {}) or {}
            if reach_streamflow[json_key]:
                reach_fetch_success = True
        except Exception as exc:  # noqa: BLE001
            notes.append(f"Reach streamflow {series_query} unavailable ({exc.__class__.__name__}).")
    if reach_fetch_success:
        provider_mix.append("raw_nwm")
    else:
        notes.append("Reach streamflow endpoint unavailable; medium/long ensembles may be missing.")

    observed_series = extract_stageflow_secondary(stageflow.get("observed", {}) or {}, scale=1000.0)
    forecast_fallback_series = extract_stageflow_secondary(stageflow.get("forecast", {}) or {}, scale=1000.0)

    analysis_raw = extract_reach_flow_series((((reach_streamflow.get("analysisAssimilation") or {}).get("series")) or {}))
    if analysis_raw:
        analysis_series = analysis_raw[-args.analysis_points :]
        analysis_init = init_ts((((reach_streamflow.get("analysisAssimilation") or {}).get("series")) or {}).get("referenceTime"))
    else:
        analysis_series = observed_series[-args.analysis_points :]
        analysis_init = init_ts((stageflow.get("observed") or {}).get("issuedTime"))
        notes.append("Using NWPS observed stageflow as analysis fallback.")

    short_raw = extract_reach_flow_series((((reach_streamflow.get("shortRange") or {}).get("series")) or {}))
    if short_raw:
        short_series = short_raw
        short_init = init_ts((((reach_streamflow.get("shortRange") or {}).get("series")) or {}).get("referenceTime"))
    else:
        short_series = forecast_fallback_series[:18]
        short_init = init_ts((stageflow.get("forecast") or {}).get("issuedTime"))
        notes.append("Using NWPS stageflow forecast as short-range fallback.")

    medium_p10: List[Dict[str, float]]
    medium_p50: List[Dict[str, float]]
    medium_p90: List[Dict[str, float]]
    medium_init: Optional[str]
    medium_notes: List[str]
    medium_p10, medium_p50, medium_p90, medium_init, medium_notes = build_range_quantiles(
        reach_streamflow.get("mediumRange", {}) or {},
        "NWM medium_range",
    )
    notes.extend(medium_notes)

    long_p10: List[Dict[str, float]]
    long_p50: List[Dict[str, float]]
    long_p90: List[Dict[str, float]]
    long_init: Optional[str]
    long_notes: List[str]
    long_p10, long_p50, long_p90, long_init, long_notes = build_range_quantiles(
        reach_streamflow.get("longRange", {}) or {},
        "NWM long_range",
    )
    notes.extend(long_notes)

    if not analysis_series and not short_series and not long_p50 and not medium_p50:
        raise RuntimeError("No usable forecast/analysis series were produced.")

    generated = datetime.now(timezone.utc).isoformat(timespec="microseconds")
    payload: Dict[str, Any] = {
        "generated_utc": generated,
        "generated_at_utc": generated,
        "provider_used": "api",
        "provider_mix": provider_mix,
        "location": {
            "reach_id": str(args.reach_id),
            "location_id": None,
            "gauge_id": str(args.gauge_id),
        },
        "variable": ["streamflow"],
        "units": ["ft3/s", "m3 s-1"],
        "init_times": {
            "analysis": analysis_init,
            "long_range": long_init,
            "medium_range": medium_init,
            "short": short_init,
        },
        "notes": dedupe(notes),
        "ranges": {
            "analysis": {"deterministic": analysis_series},
            "short": {"deterministic": short_series},
            "medium_range": {"p10": medium_p10, "p50": medium_p50, "p90": medium_p90},
            "long_range": {"p10": long_p10, "p50": long_p50, "p90": long_p90},
        },
    }
    return payload


def write_json_atomic(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def main() -> int:
    args = parse_args()
    output_path = Path(args.output)
    payload = build_payload(args)
    write_json_atomic(output_path, payload)

    analysis_n = len(payload["ranges"]["analysis"]["deterministic"])
    short_n = len(payload["ranges"]["short"]["deterministic"])
    med_n = len(payload["ranges"]["medium_range"]["p50"])
    long_n = len(payload["ranges"]["long_range"]["p50"])
    print(f"[OK] wrote {output_path}")
    print(
        "[OK] points: "
        f"analysis={analysis_n} short={short_n} medium_p50={med_n} long_p50={long_n}"
    )
    if payload.get("notes"):
        print("[INFO] notes:")
        for note in payload["notes"]:
            print(f"  - {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
