from __future__ import annotations

from typing import Any, Dict, List, Sequence

import pandas as pd

from .config import PipelineConfig


def run_qc(
    df: pd.DataFrame,
    cfg: PipelineConfig,
    expected_member_count: int,
    expected_rows: int,
    resolved_soil_levels: Sequence[str],
    missing_expected_levels: Dict[str, List[str]],
) -> Dict[str, Any]:
    checks: List[Dict[str, Any]] = []
    failed = False

    if df.empty:
        return {
            "pass": False,
            "checks": [{"name": "non_empty", "pass": False, "details": "no rows extracted"}],
        }

    unique_members = int(df["member"].nunique())
    member_ok = unique_members >= cfg.runtime.require_member_count
    checks.append(
        {
            "name": "member_count_global",
            "pass": member_ok,
            "expected": cfg.runtime.require_member_count,
            "observed": unique_members,
        }
    )
    if not member_ok:
        failed = True

    row_count_ok = int(len(df)) == int(expected_rows)
    checks.append(
        {
            "name": "row_count_expected",
            "pass": row_count_ok,
            "expected": int(expected_rows),
            "observed": int(len(df)),
        }
    )
    if not row_count_ok:
        failed = True

    group_counts = (
        df.groupby(["variable", "level", "lead_hours"], dropna=False)["member"]
        .nunique()
        .reset_index(name="member_count")
    )
    too_low = group_counts[group_counts["member_count"] < expected_member_count]
    group_ok = too_low.empty
    checks.append(
        {
            "name": "member_count_by_variable_level_lead",
            "pass": group_ok,
            "expected": expected_member_count,
            "violations": too_low.head(25).to_dict(orient="records"),
            "violation_count": int(len(too_low)),
        }
    )
    if not group_ok:
        failed = True

    nan_fraction = float(df["value"].isna().mean())
    nan_ok = nan_fraction <= cfg.qc.nan_tolerance
    checks.append(
        {
            "name": "nan_tolerance",
            "pass": nan_ok,
            "tolerance": cfg.qc.nan_tolerance,
            "observed": nan_fraction,
        }
    )
    if not nan_ok:
        failed = True

    time_ok = (
        (df["valid_time_utc"] - df["init_time_utc"]).dt.total_seconds() / 3600.0
        == df["lead_hours"].astype(float)
    ).all()
    checks.append({"name": "valid_time_consistency", "pass": bool(time_ok)})
    if not time_ok:
        failed = True

    soil_levels_observed = sorted(
        df[df["variable"] == "SOILW"]["level"].dropna().astype(str).unique().tolist()
    )
    missing_resolved = sorted(set(resolved_soil_levels) - set(soil_levels_observed))
    levels_ok = len(missing_resolved) == 0
    checks.append(
        {
            "name": "resolved_soil_levels_present",
            "pass": levels_ok,
            "resolved_soil_levels": sorted(set(resolved_soil_levels)),
            "observed_soil_levels": soil_levels_observed,
            "missing_resolved_soil_levels": missing_resolved,
        }
    )
    if not levels_ok:
        failed = True

    checks.append(
        {
            "name": "missing_expected_levels_recorded",
            "pass": True,
            "missing_expected_levels": missing_expected_levels,
        }
    )

    for var_name, bounds in cfg.qc.value_range_checks.items():
        lo, hi = bounds
        subset = df[df["variable"] == var_name]
        if subset.empty:
            checks.append(
                {
                    "name": f"value_range_{var_name}",
                    "pass": False,
                    "details": "variable missing from extracted dataset",
                }
            )
            failed = True
            continue
        out_of_range = subset[(subset["value"] < lo) | (subset["value"] > hi)]
        ok = out_of_range.empty
        checks.append(
            {
                "name": f"value_range_{var_name}",
                "pass": ok,
                "bounds": [lo, hi],
                "violation_count": int(len(out_of_range)),
            }
        )
        if not ok:
            failed = True

    return {"pass": not failed, "checks": checks}
