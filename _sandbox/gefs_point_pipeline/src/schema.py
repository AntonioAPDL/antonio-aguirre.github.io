from __future__ import annotations

from typing import Iterable, List

import pandas as pd


MEMBER_REQUIRED_COLUMNS: List[str] = [
    "site_id",
    "init_time_utc",
    "lead_hours",
    "valid_time_utc",
    "member",
    "variable",
    "level",
    "value",
    "units",
    "grid_lat",
    "grid_lon",
    "distance_km",
    "used_fallback_point",
    "product",
    "source",
    "search_string",
    "descriptor",
    "file_ref",
    "error",
    "schema_version",
]

SUMMARY_REQUIRED_COLUMNS: List[str] = [
    "site_id",
    "init_time_utc",
    "lead_hours",
    "valid_time_utc",
    "variable",
    "level",
    "mean",
    "std",
    "q10",
    "q50",
    "q90",
    "member_count",
    "schema_version",
]


def _require_columns(df: pd.DataFrame, required: Iterable[str], label: str) -> None:
    missing = [name for name in required if name not in df.columns]
    if missing:
        raise ValueError(f"{label} schema missing columns: {missing}")


def validate_member_schema(df: pd.DataFrame, schema_version: int) -> pd.DataFrame:
    out = df.copy()
    out["schema_version"] = int(schema_version)
    _require_columns(out, MEMBER_REQUIRED_COLUMNS, "member parquet")
    out["init_time_utc"] = pd.to_datetime(out["init_time_utc"], utc=True)
    out["valid_time_utc"] = pd.to_datetime(out["valid_time_utc"], utc=True)
    out["lead_hours"] = out["lead_hours"].astype(int)
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    out["grid_lat"] = pd.to_numeric(out["grid_lat"], errors="coerce")
    out["grid_lon"] = pd.to_numeric(out["grid_lon"], errors="coerce")
    out["distance_km"] = pd.to_numeric(out["distance_km"], errors="coerce")
    out["used_fallback_point"] = out["used_fallback_point"].astype(bool)

    non_null_cols = ["site_id", "member", "variable", "level", "product", "source"]
    if out[non_null_cols].isna().any().any():
        raise ValueError("member parquet has nulls in required string keys")
    return out


def validate_summary_schema(df: pd.DataFrame, schema_version: int) -> pd.DataFrame:
    out = df.copy()
    out["schema_version"] = int(schema_version)
    _require_columns(out, SUMMARY_REQUIRED_COLUMNS, "summary parquet")
    out["init_time_utc"] = pd.to_datetime(out["init_time_utc"], utc=True)
    out["valid_time_utc"] = pd.to_datetime(out["valid_time_utc"], utc=True)
    out["lead_hours"] = out["lead_hours"].astype(int)
    for col in ("mean", "std", "q10", "q50", "q90"):
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["member_count"] = out["member_count"].astype(int)
    return out
