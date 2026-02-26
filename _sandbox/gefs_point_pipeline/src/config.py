from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass(frozen=True)
class PointConfig:
    point_id: str
    usgs_site: str
    lat: float
    lon: float
    search_max_km: float
    method: str


@dataclass(frozen=True)
class VariableConfig:
    key: str
    canonical_name: str
    search_strings: List[str]
    levels_preference: List[str]


@dataclass(frozen=True)
class LeadConfig:
    start: int
    end: int
    step: int

    def values(self) -> List[int]:
        return list(range(self.start, self.end + 1, self.step))


@dataclass(frozen=True)
class RuntimeConfig:
    candidate_lookback_hours: int
    representative_fxx: int
    completeness_probe_fxx: int
    max_workers: int
    retries: int
    retry_backoff_sec: float
    keep_cycles: int
    keep_failed_runs: int
    keep_smoke_runs: int
    schema_version: int
    require_member_count: int
    latest_pointer_name: str


@dataclass(frozen=True)
class OutputConfig:
    runs_root: Path
    smoke_runs_root: Path
    web_out_dir: Path
    web_filename: str


@dataclass(frozen=True)
class QcConfig:
    nan_tolerance: float
    value_range_checks: Dict[str, List[float]]


@dataclass(frozen=True)
class PipelineConfig:
    source_priority: List[str]
    model: str
    products_try: List[str]
    members: List[str]
    leads: LeadConfig
    variables: List[VariableConfig]
    runtime: RuntimeConfig
    output: OutputConfig
    qc: QcConfig


def _read_yaml(path: Path) -> Dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_point_config(path: Path, point_id: str) -> PointConfig:
    raw = _read_yaml(path)
    if point_id not in raw:
        raise KeyError(f"Point '{point_id}' not found in {path}")
    point = raw[point_id]
    return PointConfig(
        point_id=point_id,
        usgs_site=str(point["usgs_site"]),
        lat=float(point["lat"]),
        lon=float(point["lon"]),
        search_max_km=float(point.get("search_max_km", 200.0)),
        method=str(point.get("method", "nearest_non_nan")),
    )


def load_pipeline_config(path: Path) -> PipelineConfig:
    raw = _read_yaml(path)

    leads = raw.get("lead_hours", {})
    var_raw = raw.get("variables", {})
    variables = [
        VariableConfig(
            key=str(key),
            canonical_name=str(cfg.get("canonical_name", key.upper())),
            search_strings=[str(x) for x in cfg.get("search_strings", [])],
            levels_preference=[str(x) for x in cfg.get("levels_preference", [])],
        )
        for key, cfg in var_raw.items()
    ]
    if not variables:
        raise ValueError("No variables configured in gefs.yaml")

    runtime_raw = raw.get("runtime", {})
    output_raw = raw.get("output", {})
    qc_raw = raw.get("qc", {})

    return PipelineConfig(
        source_priority=[str(x) for x in raw.get("source_priority", ["aws"])],
        model=str(raw.get("model", "gefs")),
        products_try=[str(x) for x in raw.get("products_try", ["atmos.5", "atmos.5b"])],
        members=[str(x) for x in raw.get("members", [])],
        leads=LeadConfig(
            start=int(leads.get("start", 0)),
            end=int(leads.get("end", 240)),
            step=int(leads.get("step", 3)),
        ),
        variables=variables,
        runtime=RuntimeConfig(
            candidate_lookback_hours=int(runtime_raw.get("candidate_lookback_hours", 36)),
            representative_fxx=int(runtime_raw.get("representative_fxx", 0)),
            completeness_probe_fxx=int(runtime_raw.get("completeness_probe_fxx", 3)),
            max_workers=int(runtime_raw.get("max_workers", 8)),
            retries=int(runtime_raw.get("retries", 3)),
            retry_backoff_sec=float(runtime_raw.get("retry_backoff_sec", 1.5)),
            keep_cycles=int(runtime_raw.get("keep_cycles", 1)),
            keep_failed_runs=int(runtime_raw.get("keep_failed_runs", 3)),
            keep_smoke_runs=int(runtime_raw.get("keep_smoke_runs", 5)),
            schema_version=int(runtime_raw.get("schema_version", 1)),
            require_member_count=int(runtime_raw.get("require_member_count", 31)),
            latest_pointer_name=str(runtime_raw.get("latest_pointer_name", "latest_init.txt")),
        ),
        output=OutputConfig(
            runs_root=Path(str(output_raw.get("runs_root", "data/_sandbox_gefs/runs"))),
            smoke_runs_root=Path(
                str(output_raw.get("smoke_runs_root", "data/_sandbox_gefs/smoke_runs"))
            ),
            web_out_dir=Path(str(output_raw.get("web_out_dir", "data/_sandbox_gefs/web"))),
            web_filename=str(output_raw.get("web_filename", "gefs_big_trees_latest.json")),
        ),
        qc=QcConfig(
            nan_tolerance=float(qc_raw.get("nan_tolerance", 0.05)),
            value_range_checks={
                str(k): [float(v[0]), float(v[1])]
                for k, v in (qc_raw.get("value_range_checks", {}) or {}).items()
            },
        ),
    )


def config_fingerprint(config: PipelineConfig, point: PointConfig) -> str:
    payload = {
        "pipeline": dataclasses.asdict(config),
        "point": dataclasses.asdict(point),
    }
    return json.dumps(payload, sort_keys=True, default=str)


def parse_init_time(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    return text.strip()
