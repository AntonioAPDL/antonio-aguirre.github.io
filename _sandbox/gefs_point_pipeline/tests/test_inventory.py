from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import (  # noqa: E402
    LeadConfig,
    OutputConfig,
    PipelineConfig,
    QcConfig,
    RuntimeConfig,
    VariableConfig,
)
from src.inventory import resolve_product_and_fields  # noqa: E402


def _cfg() -> PipelineConfig:
    return PipelineConfig(
        source_priority=["aws"],
        model="gefs",
        products_try=["atmos.5", "atmos.5b"],
        members=["c00", "p01", "p02"],
        leads=LeadConfig(start=0, end=12, step=3),
        variables=[
            VariableConfig(
                key="precip",
                canonical_name="APCP",
                search_strings=["APCP:surface", "APCP"],
                levels_preference=[],
            ),
            VariableConfig(
                key="soil_moisture",
                canonical_name="SOILW",
                search_strings=["SOILW"],
                levels_preference=[
                    "0-0.1 m below ground",
                    "0.1-0.4 m below ground",
                    "0.4-1 m below ground",
                    "1-2 m below ground",
                ],
            ),
        ],
        runtime=RuntimeConfig(
            candidate_lookback_hours=24,
            representative_fxx=0,
            completeness_probe_fxx=3,
            max_workers=4,
            retries=1,
            retry_backoff_sec=0.1,
            keep_cycles=1,
            keep_failed_runs=1,
            keep_smoke_runs=1,
            schema_version=1,
            require_member_count=3,
            latest_pointer_name="latest_init.txt",
        ),
        output=OutputConfig(
            runs_root=Path("data/_sandbox_gefs/runs"),
            smoke_runs_root=Path("data/_sandbox_gefs/smoke_runs"),
            web_out_dir=Path("data/_sandbox_gefs/web"),
            web_filename="gefs_big_trees_latest.json",
        ),
        qc=QcConfig(nan_tolerance=0.1, value_range_checks={}),
    )


def test_inventory_resolves_multilayer_soil_across_products(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = _cfg()
    init = dt.datetime(2026, 2, 24, 0, 0, tzinfo=dt.timezone.utc)

    # Minimal inventory-like rows with search_this + level columns.
    atmos5 = pd.DataFrame(
        [
            {"search_this": ":APCP:surface:0-6 hour acc fcst:ENS=low-res ctl:", "level": "surface"},
            {
                "search_this": ":SOILW:0-0.1 m below ground:6 hour fcst:ENS=low-res ctl:",
                "level": "0-0.1 m below ground",
            },
        ]
    )
    atmos5b = pd.DataFrame(
        [
            {"search_this": ":SOILW:0.1-0.4 m below ground:6 hour fcst:ENS=low-res ctl:", "level": "0.1-0.4 m below ground"},
            {"search_this": ":SOILW:0.4-1 m below ground:6 hour fcst:ENS=low-res ctl:", "level": "0.4-1 m below ground"},
            {"search_this": ":SOILW:1-2 m below ground:6 hour fcst:ENS=low-res ctl:", "level": "1-2 m below ground"},
        ]
    )

    def fake_make_herbie(init_time_utc, model, product, member, fxx, source_priority):
        return {"product": product, "fxx": fxx}

    def fake_inventory_frame(handle):
        if handle["product"] == "atmos.5" and handle["fxx"] in (0, 6):
            return atmos5
        if handle["product"] == "atmos.5b" and handle["fxx"] in (0, 6):
            return atmos5b
        return pd.DataFrame()

    monkeypatch.setattr("src.inventory.make_herbie", fake_make_herbie)
    monkeypatch.setattr("src.inventory.inventory_frame", fake_inventory_frame)

    fields, details = resolve_product_and_fields(cfg, init)
    by_level = {field.level_label: field.product for field in fields if field.canonical_name == "SOILW"}

    assert any(field.canonical_name == "APCP" for field in fields)
    assert by_level["0-0.1 m below ground"] == "atmos.5"
    assert by_level["0.1-0.4 m below ground"] == "atmos.5b"
    assert by_level["0.4-1 m below ground"] == "atmos.5b"
    assert by_level["1-2 m below ground"] == "atmos.5b"
    assert details["missing_expected_levels"].get("soil_moisture", []) == []


def test_inventory_records_missing_soil_layers_but_keeps_core_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = _cfg()
    init = dt.datetime(2026, 2, 24, 0, 0, tzinfo=dt.timezone.utc)

    atmos5 = pd.DataFrame(
        [
            {"search_this": ":APCP:surface:0-6 hour acc fcst:ENS=low-res ctl:", "level": "surface"},
            {
                "search_this": ":SOILW:0-0.1 m below ground:6 hour fcst:ENS=low-res ctl:",
                "level": "0-0.1 m below ground",
            },
        ]
    )
    atmos5b = pd.DataFrame(columns=["search_this", "level"])

    def fake_make_herbie(init_time_utc, model, product, member, fxx, source_priority):
        return {"product": product, "fxx": fxx}

    def fake_inventory_frame(handle):
        if handle["product"] == "atmos.5":
            return atmos5
        if handle["product"] == "atmos.5b":
            return atmos5b
        return pd.DataFrame()

    monkeypatch.setattr("src.inventory.make_herbie", fake_make_herbie)
    monkeypatch.setattr("src.inventory.inventory_frame", fake_inventory_frame)

    fields, details = resolve_product_and_fields(cfg, init)
    soil_fields = [field for field in fields if field.canonical_name == "SOILW"]

    assert len(soil_fields) == 1
    assert soil_fields[0].level_label == "0-0.1 m below ground"
    assert details["missing_expected_levels"]["soil_moisture"] == [
        "0.1-0.4 m below ground",
        "0.4-1 m below ground",
        "1-2 m below ground",
    ]
