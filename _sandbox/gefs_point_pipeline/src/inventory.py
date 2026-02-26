from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import pandas as pd

from .config import PipelineConfig, VariableConfig
from .herbie_adapter import inventory_frame, make_herbie


@dataclass(frozen=True)
class ResolvedField:
    variable_key: str
    canonical_name: str
    level_label: str
    search_string: str
    product: str
    pattern_used: str
    descriptor: str
    probe_fxx: int


def _inventory_text_column(inv: pd.DataFrame) -> pd.Series:
    if "search_this" in inv.columns:
        return inv["search_this"].astype(str)
    text_cols = [c for c in inv.columns if inv[c].dtype == object]
    if not text_cols:
        return pd.Series([""] * len(inv), index=inv.index)
    return inv[text_cols].astype(str).agg(" | ".join, axis=1)


def _contains(inv: pd.DataFrame, pattern: str) -> pd.DataFrame:
    if inv.empty:
        return inv
    text = _inventory_text_column(inv)
    mask = text.str.contains(pattern, case=False, regex=True, na=False)
    return inv.loc[mask].copy()


def _descriptor(row: pd.Series) -> str:
    if "search_this" in row.index:
        return str(row["search_this"])
    return " | ".join([f"{k}={row[k]}" for k in row.index])


def _level_label(row: pd.Series, fallback: str = "") -> str:
    if "level" in row.index and row["level"]:
        return str(row["level"])
    desc = _descriptor(row)
    if ":" in desc:
        parts = [p.strip() for p in desc.split(":") if p.strip()]
        if len(parts) >= 3:
            return parts[2]
    return fallback or "unspecified"


def _probe_fxx_candidates(cfg: PipelineConfig) -> List[int]:
    out: List[int] = []
    for candidate in (cfg.runtime.representative_fxx, 6, 3, 12, 0):
        if candidate not in out:
            out.append(candidate)
    return out


def _load_inventory_cache(
    cfg: PipelineConfig,
    init_time_utc: dt.datetime,
) -> Tuple[Dict[Tuple[str, int], pd.DataFrame], List[Dict[str, Any]]]:
    attempts: List[Dict[str, Any]] = []
    cache: Dict[Tuple[str, int], pd.DataFrame] = {}
    probe_member = "c00"
    for product in cfg.products_try:
        for fxx in _probe_fxx_candidates(cfg):
            key = (product, fxx)
            try:
                handle = make_herbie(
                    init_time_utc=init_time_utc,
                    model=cfg.model,
                    product=product,
                    member=probe_member,
                    fxx=fxx,
                    source_priority=cfg.source_priority,
                )
                inv = inventory_frame(handle)
            except Exception as exc:
                attempts.append(
                    {
                        "product": product,
                        "fxx": fxx,
                        "status": "error",
                        "reason": str(exc),
                    }
                )
                cache[key] = pd.DataFrame()
                continue
            cache[key] = inv
            attempts.append(
                {
                    "product": product,
                    "fxx": fxx,
                    "status": "loaded" if not inv.empty else "empty_inventory",
                    "inventory_rows": int(len(inv)),
                }
            )
    return cache, attempts


def _resolve_scalar_variable(
    cfg: PipelineConfig,
    var_cfg: VariableConfig,
    inv_cache: Dict[Tuple[str, int], pd.DataFrame],
) -> Tuple[List[ResolvedField], List[Dict[str, Any]]]:
    attempts: List[Dict[str, Any]] = []
    for product in cfg.products_try:
        for fxx in _probe_fxx_candidates(cfg):
            inv = inv_cache.get((product, fxx), pd.DataFrame())
            if inv.empty:
                continue
            for pattern in var_cfg.search_strings:
                matches = _contains(inv, pattern)
                attempts.append(
                    {
                        "variable": var_cfg.key,
                        "product": product,
                        "fxx": fxx,
                        "pattern": pattern,
                        "matches": int(len(matches)),
                    }
                )
                if matches.empty:
                    continue
                row = matches.iloc[0]
                return (
                    [
                        ResolvedField(
                            variable_key=var_cfg.key,
                            canonical_name=var_cfg.canonical_name,
                            level_label=_level_label(row, fallback="surface"),
                            search_string=pattern,
                            product=product,
                            pattern_used=pattern,
                            descriptor=_descriptor(row),
                            probe_fxx=int(fxx),
                        )
                    ],
                    attempts,
                )
    return [], attempts


def _resolve_layered_variable(
    cfg: PipelineConfig,
    var_cfg: VariableConfig,
    inv_cache: Dict[Tuple[str, int], pd.DataFrame],
) -> Tuple[List[ResolvedField], List[str], List[Dict[str, Any]]]:
    attempts: List[Dict[str, Any]] = []
    resolved: List[ResolvedField] = []
    missing_levels: List[str] = []
    base_pattern = var_cfg.search_strings[0] if var_cfg.search_strings else var_cfg.canonical_name

    for desired_level in var_cfg.levels_preference:
        found_for_level = False
        level_regex = re.escape(desired_level)

        for product in cfg.products_try:
            for fxx in _probe_fxx_candidates(cfg):
                inv = inv_cache.get((product, fxx), pd.DataFrame())
                if inv.empty:
                    continue
                base_matches = _contains(inv, base_pattern)
                if base_matches.empty:
                    attempts.append(
                        {
                            "variable": var_cfg.key,
                            "level": desired_level,
                            "product": product,
                            "fxx": fxx,
                            "pattern": base_pattern,
                            "matches": 0,
                        }
                    )
                    continue
                level_matches = _contains(base_matches, level_regex)
                attempts.append(
                    {
                        "variable": var_cfg.key,
                        "level": desired_level,
                        "product": product,
                        "fxx": fxx,
                        "pattern": f"{base_pattern} + {desired_level}",
                        "matches": int(len(level_matches)),
                    }
                )
                if level_matches.empty:
                    continue

                row = level_matches.iloc[0]
                level_label = _level_label(row, fallback=desired_level)
                resolved.append(
                    ResolvedField(
                        variable_key=var_cfg.key,
                        canonical_name=var_cfg.canonical_name,
                        level_label=level_label,
                        search_string=f"{var_cfg.canonical_name}:{level_label}",
                        product=product,
                        pattern_used=f"{base_pattern} + level={desired_level}",
                        descriptor=_descriptor(row),
                        probe_fxx=int(fxx),
                    )
                )
                found_for_level = True
                break
            if found_for_level:
                break

        if not found_for_level:
            missing_levels.append(desired_level)

    # Deduplicate potential repeated levels if inventories map aliases.
    deduped: Dict[str, ResolvedField] = {}
    for field in resolved:
        deduped[field.level_label] = field
    return list(deduped.values()), missing_levels, attempts


def resolve_product_and_fields(
    cfg: PipelineConfig,
    init_time_utc: dt.datetime,
) -> Tuple[List[ResolvedField], Dict[str, Any]]:
    inv_cache, inventory_attempts = _load_inventory_cache(cfg, init_time_utc)
    variable_attempts: List[Dict[str, Any]] = []
    resolved_fields: List[ResolvedField] = []
    missing_variables: List[str] = []
    missing_expected_levels: Dict[str, List[str]] = {}

    for var_cfg in cfg.variables:
        if var_cfg.levels_preference:
            levels, missing_levels, attempts = _resolve_layered_variable(cfg, var_cfg, inv_cache)
            variable_attempts.extend(attempts)
            if levels:
                resolved_fields.extend(levels)
            else:
                missing_variables.append(var_cfg.key)
            if missing_levels:
                missing_expected_levels[var_cfg.key] = missing_levels
            continue

        scalar, attempts = _resolve_scalar_variable(cfg, var_cfg, inv_cache)
        variable_attempts.extend(attempts)
        if scalar:
            resolved_fields.extend(scalar)
        else:
            missing_variables.append(var_cfg.key)

    required_missing = set(missing_variables)
    if "soil_moisture" in missing_expected_levels and "soil_moisture" not in required_missing:
        # Some soil levels are missing, but at least one resolved level exists.
        pass

    if required_missing:
        raise RuntimeError(
            "Could not resolve required variables. "
            f"missing_variables={sorted(required_missing)} "
            f"missing_expected_levels={missing_expected_levels}"
        )

    resolved_products = sorted({field.product for field in resolved_fields})
    resolved_soil_levels = sorted(
        {field.level_label for field in resolved_fields if field.variable_key == "soil_moisture"}
    )

    details = {
        "inventory_attempts": inventory_attempts,
        "variable_attempts": variable_attempts,
        "resolved_products": resolved_products,
        "resolved_soil_levels": resolved_soil_levels,
        "missing_expected_levels": missing_expected_levels,
    }
    return resolved_fields, details
