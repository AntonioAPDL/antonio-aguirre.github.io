#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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


def _parse_iso(value: Any) -> Optional[dt.datetime]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def _series_in_window(
    points: Any,
    start_utc: dt.datetime,
    end_utc: dt.datetime,
) -> Dict[str, Tuple[dt.datetime, float]]:
    out: Dict[str, Tuple[dt.datetime, float]] = {}
    if not isinstance(points, list):
        return out
    for point in points:
        if not isinstance(point, dict):
            continue
        ts = _parse_iso(point.get("t"))
        if ts is None or not (start_utc <= ts < end_utc):
            continue
        try:
            value = float(point.get("v"))
        except (TypeError, ValueError):
            continue
        out[ts.isoformat()] = (ts, value)
    return out


def _merge_series_window(
    carry_points: Any,
    prior_forecast_points: Any,
    start_utc: dt.datetime,
    end_utc: dt.datetime,
) -> List[Dict[str, float]]:
    merged = _series_in_window(carry_points, start_utc, end_utc)
    # Prefer freshest values from the prior cycle forecast for duplicate timestamps.
    merged.update(_series_in_window(prior_forecast_points, start_utc, end_utc))
    ordered = sorted(merged.values(), key=lambda item: item[0])
    return [{"t": ts.isoformat(), "v": value} for ts, value in ordered]


def _point_list(points: Any) -> List[Tuple[dt.datetime, float]]:
    out: List[Tuple[dt.datetime, float]] = []
    if not isinstance(points, list):
        return out
    for point in points:
        if not isinstance(point, dict):
            continue
        ts = _parse_iso(point.get("t"))
        if ts is None:
            continue
        try:
            value = float(point.get("v"))
        except (TypeError, ValueError):
            continue
        out.append((ts, value))
    out.sort(key=lambda item: item[0])
    return out


def _select_cycle_marker(points: Any, init_time_utc: dt.datetime, require_after_init: bool) -> Optional[Dict[str, float]]:
    parsed = _point_list(points)
    if not parsed:
        return None
    if require_after_init:
        for ts, value in parsed:
            if ts > init_time_utc:
                return {"t": ts.isoformat(), "v": value}
        for ts, value in parsed:
            if ts >= init_time_utc:
                return {"t": ts.isoformat(), "v": value}
    else:
        for ts, value in parsed:
            if ts >= init_time_utc:
                return {"t": ts.isoformat(), "v": value}
    ts, value = parsed[0]
    return {"t": ts.isoformat(), "v": value}


def _extract_cycle_analysis_points(payload: Any) -> Dict[str, Dict[str, List[Dict[str, float]]]]:
    out: Dict[str, Dict[str, List[Dict[str, float]]]] = {
        "soil_f000": {},
        "precip_f003_proxy": {},
    }
    if not isinstance(payload, dict):
        return out
    init_time = _parse_iso(payload.get("init_time_utc"))
    if init_time is None:
        return out

    soil_levels = payload.get("soil_moisture")
    if isinstance(soil_levels, dict):
        for level_name, level_block in soil_levels.items():
            if not isinstance(level_block, dict):
                continue
            marker = _select_cycle_marker(level_block.get("p50"), init_time, require_after_init=False)
            if marker:
                out["soil_f000"][str(level_name)] = [marker]

    precip_levels = payload.get("precip")
    if isinstance(precip_levels, dict):
        for level_name, level_block in precip_levels.items():
            if not isinstance(level_block, dict):
                continue
            marker = _select_cycle_marker(level_block.get("p50"), init_time, require_after_init=True)
            if marker:
                out["precip_f003_proxy"][str(level_name)] = [marker]

    return out


def _merge_context_series(
    carry_points: Any,
    history_points: Any,
    prior_cycle_points: Any,
    current_cycle_points: Any,
    start_utc: dt.datetime,
    end_utc: dt.datetime,
) -> List[Dict[str, float]]:
    merged = _series_in_window(carry_points, start_utc, end_utc)
    merged.update(_series_in_window(history_points, start_utc, end_utc))
    merged.update(_series_in_window(prior_cycle_points, start_utc, end_utc))
    merged.update(_series_in_window(current_cycle_points, start_utc, end_utc))
    ordered = sorted(merged.values(), key=lambda item: item[0])
    return [{"t": ts.isoformat(), "v": value} for ts, value in ordered]


def _collect_cycle_context_from_payloads(
    payloads: List[Dict[str, Any]],
    start_utc: dt.datetime,
    precip_end_utc: dt.datetime,
    soil_end_utc: dt.datetime,
) -> Dict[str, Dict[str, List[Dict[str, float]]]]:
    precip: Dict[str, Dict[str, Tuple[dt.datetime, float]]] = {}
    soil: Dict[str, Dict[str, Tuple[dt.datetime, float]]] = {}
    for payload in payloads:
        cycle = _extract_cycle_analysis_points(payload)
        for level_name, points in cycle.get("precip_f003_proxy", {}).items():
            level_key = str(level_name)
            bucket = precip.setdefault(level_key, {})
            bucket.update(_series_in_window(points, start_utc, precip_end_utc))
        for level_name, points in cycle.get("soil_f000", {}).items():
            level_key = str(level_name)
            bucket = soil.setdefault(level_key, {})
            bucket.update(_series_in_window(points, start_utc, soil_end_utc))

    def _to_sorted_points(
        mapping: Dict[str, Dict[str, Tuple[dt.datetime, float]]]
    ) -> Dict[str, List[Dict[str, float]]]:
        out: Dict[str, List[Dict[str, float]]] = {}
        for level_name, ts_map in mapping.items():
            ordered = sorted(ts_map.values(), key=lambda item: item[0])
            if not ordered:
                continue
            out[level_name] = [{"t": ts.isoformat(), "v": value} for ts, value in ordered]
        return out

    return {
        "precip_f003_proxy": _to_sorted_points(precip),
        "soil_f000": _to_sorted_points(soil),
    }


def _load_payload_history_from_git(
    repo_root: Path,
    tracked_json_path: Path,
    max_commits: int,
) -> List[Dict[str, Any]]:
    try:
        rel_path = tracked_json_path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return []

    rev_cmd = [
        "git",
        "-C",
        str(repo_root),
        "rev-list",
        f"--max-count={max(1, int(max_commits))}",
        "HEAD",
        "--",
        rel_path,
    ]
    rev_proc = subprocess.run(rev_cmd, capture_output=True, text=True, check=False)
    if rev_proc.returncode != 0:
        return []
    hashes = [line.strip() for line in rev_proc.stdout.splitlines() if line.strip()]
    if not hashes:
        return []

    payloads: List[Dict[str, Any]] = []
    for rev in reversed(hashes):
        show_cmd = ["git", "-C", str(repo_root), "show", f"{rev}:{rel_path}"]
        show_proc = subprocess.run(show_cmd, capture_output=True, text=True, check=False)
        if show_proc.returncode != 0 or not show_proc.stdout.strip():
            continue
        try:
            data = json.loads(show_proc.stdout)
        except Exception:
            continue
        if isinstance(data, dict):
            payloads.append(data)
    return payloads


def _build_gefs_analysis_context_payload(
    current_payload: Dict[str, Any],
    prior_payload: Optional[Dict[str, Any]],
    observation_window_days: int,
    history_payloads: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    init_time = _parse_iso(current_payload.get("init_time_utc"))
    if init_time is None:
        return {}

    start_time = init_time - dt.timedelta(days=max(1, int(observation_window_days)))
    # Keep soil context strictly up to init. Precip proxy may include f003 from the current cycle.
    soil_end = init_time + dt.timedelta(minutes=1)
    precip_end = init_time + dt.timedelta(hours=3, minutes=1)

    prior_payload = prior_payload or {}
    prior_context = prior_payload.get("gefs_analysis_context") if isinstance(prior_payload, dict) else {}
    if not isinstance(prior_context, dict):
        prior_context = {}

    prior_cycle = _extract_cycle_analysis_points(prior_payload)
    current_cycle = _extract_cycle_analysis_points(current_payload)
    history_cycle = _collect_cycle_context_from_payloads(
        payloads=history_payloads or [],
        start_utc=start_time,
        precip_end_utc=precip_end,
        soil_end_utc=soil_end,
    )

    context: Dict[str, Any] = {
        "window_days": int(max(1, observation_window_days)),
        "start_utc": start_time.isoformat(),
        "end_utc": init_time.isoformat(),
        "precip_proxy_valid_offset_hours": 3,
        "precip_f003_proxy": {},
        "soil_f000": {},
    }

    precip_levels = set(current_cycle["precip_f003_proxy"].keys())
    precip_levels.update((prior_context.get("precip_f003_proxy") or {}).keys())
    precip_levels.update(prior_cycle["precip_f003_proxy"].keys())
    precip_levels.update(history_cycle["precip_f003_proxy"].keys())
    for level_name in sorted(str(level) for level in precip_levels):
        merged = _merge_context_series(
            carry_points=(prior_context.get("precip_f003_proxy") or {}).get(level_name, []),
            history_points=history_cycle["precip_f003_proxy"].get(level_name, []),
            prior_cycle_points=prior_cycle["precip_f003_proxy"].get(level_name, []),
            current_cycle_points=current_cycle["precip_f003_proxy"].get(level_name, []),
            start_utc=start_time,
            end_utc=precip_end,
        )
        if merged:
            context["precip_f003_proxy"][level_name] = merged

    soil_levels = set(current_cycle["soil_f000"].keys())
    soil_levels.update((prior_context.get("soil_f000") or {}).keys())
    soil_levels.update(prior_cycle["soil_f000"].keys())
    soil_levels.update(history_cycle["soil_f000"].keys())
    for level_name in sorted(str(level) for level in soil_levels):
        merged = _merge_context_series(
            carry_points=(prior_context.get("soil_f000") or {}).get(level_name, []),
            history_points=history_cycle["soil_f000"].get(level_name, []),
            prior_cycle_points=prior_cycle["soil_f000"].get(level_name, []),
            current_cycle_points=current_cycle["soil_f000"].get(level_name, []),
            start_utc=start_time,
            end_utc=soil_end,
        )
        if merged:
            context["soil_f000"][level_name] = merged

    return context


def _build_retrospective_payload(
    current_payload: Dict[str, Any],
    prior_payload: Optional[Dict[str, Any]],
    observation_window_days: int,
) -> Dict[str, Any]:
    init_time = _parse_iso(current_payload.get("init_time_utc"))
    if init_time is None:
        return {}

    start_time = init_time - dt.timedelta(days=max(1, int(observation_window_days)))
    prior_payload = prior_payload or {}
    prior_retro = prior_payload.get("retrospective") if isinstance(prior_payload, dict) else {}
    if not isinstance(prior_retro, dict):
        prior_retro = {}

    retrospective: Dict[str, Any] = {
        "window_days": int(max(1, observation_window_days)),
        "start_utc": start_time.isoformat(),
        "end_utc": init_time.isoformat(),
        "precip": {},
        "soil_moisture": {},
    }

    # Precip retains full forecast statistics (p10/p50/p90/mean) for retrospective context.
    precip_levels = current_payload.get("precip")
    if isinstance(precip_levels, dict):
        for level_name in precip_levels.keys():
            level_name = str(level_name)
            level_block: Dict[str, Any] = {}
            prior_forecast_level = (
                (prior_payload.get("precip") or {}).get(level_name, {})
                if isinstance(prior_payload, dict)
                else {}
            )
            prior_retro_level = (prior_retro.get("precip") or {}).get(level_name, {})
            for metric in ("p10", "p50", "p90", "mean"):
                merged = _merge_series_window(
                    carry_points=(prior_retro_level or {}).get(metric, []),
                    prior_forecast_points=(prior_forecast_level or {}).get(metric, []),
                    start_utc=start_time,
                    end_utc=init_time,
                )
                if merged:
                    level_block[metric] = merged
            if level_block:
                retrospective["precip"][level_name] = level_block

    # Soil moisture retrospective emphasizes p50 for readability.
    soil_levels = current_payload.get("soil_moisture")
    if isinstance(soil_levels, dict):
        for level_name in soil_levels.keys():
            level_name = str(level_name)
            prior_forecast_level = (
                (prior_payload.get("soil_moisture") or {}).get(level_name, {})
                if isinstance(prior_payload, dict)
                else {}
            )
            prior_retro_level = (prior_retro.get("soil_moisture") or {}).get(level_name, {})
            merged = _merge_series_window(
                carry_points=(prior_retro_level or {}).get("p50", []),
                prior_forecast_points=(prior_forecast_level or {}).get("p50", []),
                start_utc=start_time,
                end_utc=init_time,
            )
            if merged:
                retrospective["soil_moisture"][level_name] = {"p50": merged}

    return retrospective


def _load_optional_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    return data


def _build_observed_retrospective_payload(
    climate_csv_path: Path,
    init_time_utc: dt.datetime,
    observation_window_days: int,
) -> Dict[str, Any]:
    start_time = init_time_utc - dt.timedelta(days=max(1, int(observation_window_days)))
    end_time = init_time_utc
    payload: Dict[str, Any] = {
        "window_days": int(max(1, observation_window_days)),
        "start_utc": start_time.isoformat(),
        "end_utc": end_time.isoformat(),
        "source_csv": str(climate_csv_path),
        "daily_avg_ppt": [],
        "daily_avg_soil_ERA5": [],
        "daily_avg_soil_NWM_SOIL_M": [],
        "daily_avg_soil_NWM_SOIL_W": [],
    }

    if not climate_csv_path.exists():
        return payload

    try:
        df = pd.read_csv(climate_csv_path)
    except Exception:
        return payload
    if "timestamp" not in df.columns:
        return payload

    ts = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    valid = df.loc[ts.notna()].copy()
    if valid.empty:
        return payload
    valid["timestamp"] = pd.to_datetime(valid["timestamp"], errors="coerce", utc=True)
    valid = valid.sort_values("timestamp").drop_duplicates(subset=["timestamp"], keep="last")
    mask = (valid["timestamp"] >= pd.Timestamp(start_time)) & (valid["timestamp"] < pd.Timestamp(end_time))
    window = valid.loc[mask].copy()
    if window.empty:
        return payload

    def series_for(column: str) -> List[Dict[str, float]]:
        if column not in window.columns:
            return []
        vals = pd.to_numeric(window[column], errors="coerce")
        out: List[Dict[str, float]] = []
        for ts_val, num in zip(window["timestamp"], vals):
            if pd.isna(num):
                continue
            out.append({"t": pd.Timestamp(ts_val).isoformat(), "v": float(num)})
        return out

    payload["daily_avg_ppt"] = series_for("daily_avg_ppt")
    payload["daily_avg_soil_ERA5"] = series_for("daily_avg_soil_ERA5")
    payload["daily_avg_soil_NWM_SOIL_M"] = series_for("daily_avg_soil_NWM_SOIL_M")
    payload["daily_avg_soil_NWM_SOIL_W"] = series_for("daily_avg_soil_NWM_SOIL_W")
    return payload


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
        "--observation-window-days",
        type=int,
        default=20,
        help="Retrospective observation window size before init time.",
    )
    parser.add_argument(
        "--prior-web-json",
        default=None,
        help="Optional prior web JSON used to roll retrospective context.",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Optional override output JSON path.",
    )
    parser.add_argument(
        "--analysis-history-max-commits",
        type=int,
        default=320,
        help="Max historical commits to scan for GEFS analysis context backfill.",
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
        "observation_window_days": int(max(1, args.observation_window_days)),
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

    default_prior_path = repo_root / "assets/data/forecasts/gefs_big_trees_latest.json"
    prior_path = Path(args.prior_web_json) if args.prior_web_json else default_prior_path
    prior_payload = _load_optional_json(prior_path)
    history_payloads: List[Dict[str, Any]] = []
    if prior_path.exists():
        history_payloads = _load_payload_history_from_git(
            repo_root=repo_root,
            tracked_json_path=prior_path,
            max_commits=int(max(1, args.analysis_history_max_commits)),
        )
    payload["gefs_analysis_context"] = _build_gefs_analysis_context_payload(
        current_payload=payload,
        prior_payload=prior_payload,
        observation_window_days=int(max(1, args.observation_window_days)),
        history_payloads=history_payloads,
    )
    payload["retrospective"] = _build_retrospective_payload(
        current_payload=payload,
        prior_payload=prior_payload,
        observation_window_days=int(max(1, args.observation_window_days)),
    )
    init_for_window = _parse_iso(payload.get("init_time_utc"))
    if init_for_window is not None:
        payload["observed_retrospective"] = _build_observed_retrospective_payload(
            climate_csv_path=(repo_root / "climate_daily_ppt_soil.csv"),
            init_time_utc=init_for_window,
            observation_window_days=int(max(1, args.observation_window_days)),
        )

    out_path = Path(args.out) if args.out else (repo_root / cfg.output.web_out_dir / cfg.output.web_filename)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"status=success")
    print(f"run_tag={run_tag}")
    print(f"run_dir={run_dir}")
    print(f"out_path={out_path}")
    print(f"member_count={member_count}")
    print(
        f"retrospective_points="
        f"{sum(len(v.get('p50', [])) for v in (payload.get('retrospective', {}).get('soil_moisture', {}) or {}).values())}"
    )
    context = payload.get("gefs_analysis_context", {})
    if isinstance(context, dict):
        precip_ctx = context.get("precip_f003_proxy", {})
        soil_ctx = context.get("soil_f000", {})
        precip_ctx_points = 0
        soil_ctx_points = 0
        if isinstance(precip_ctx, dict):
            precip_ctx_points = sum(len(points) for points in precip_ctx.values() if isinstance(points, list))
        if isinstance(soil_ctx, dict):
            soil_ctx_points = sum(len(points) for points in soil_ctx.values() if isinstance(points, list))
        print(f"analysis_context_precip_points={precip_ctx_points}")
        print(f"analysis_context_soil_points={soil_ctx_points}")
    print(f"analysis_history_payloads={len(history_payloads)}")
    obs = payload.get("observed_retrospective", {})
    if isinstance(obs, dict):
        print(f"observed_ppt_points={len(obs.get('daily_avg_ppt', []))}")
        print(f"observed_soil_era5_points={len(obs.get('daily_avg_soil_ERA5', []))}")
        print(f"observed_soil_nwm_m_points={len(obs.get('daily_avg_soil_NWM_SOIL_M', []))}")
        print(f"observed_soil_nwm_w_points={len(obs.get('daily_avg_soil_NWM_SOIL_W', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
