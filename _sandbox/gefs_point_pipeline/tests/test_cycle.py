from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

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
from src.cycle import build_candidate_cycles, discover_latest_complete_cycle, floor_to_cycle  # noqa: E402


def test_floor_to_cycle_rounds_down() -> None:
    now = dt.datetime(2026, 2, 23, 5, 49, tzinfo=dt.timezone.utc)
    rounded = floor_to_cycle(now)
    assert rounded == dt.datetime(2026, 2, 23, 0, 0, tzinfo=dt.timezone.utc)


def test_build_candidate_cycles_count_and_spacing() -> None:
    now = dt.datetime(2026, 2, 23, 12, 30, tzinfo=dt.timezone.utc)
    candidates = build_candidate_cycles(now, lookback_hours=24)
    assert len(candidates) == 5
    for a, b in zip(candidates[:-1], candidates[1:]):
        assert (a - b).total_seconds() == 6 * 3600


def _cfg_for_cycle_test() -> PipelineConfig:
    return PipelineConfig(
        source_priority=["aws"],
        model="gefs",
        products_try=["atmos.5", "atmos.5b"],
        members=["c00", "p01", "p02"],
        leads=LeadConfig(start=0, end=6, step=3),
        variables=[
            VariableConfig(
                key="precip",
                canonical_name="APCP",
                search_strings=["APCP:surface"],
                levels_preference=[],
            )
        ],
        runtime=RuntimeConfig(
            candidate_lookback_hours=12,
            representative_fxx=0,
            completeness_probe_fxx=3,
            max_workers=2,
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


def test_discover_latest_complete_cycle_skips_partial_upload(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = _cfg_for_cycle_test()
    now = dt.datetime(2026, 2, 24, 2, 0, tzinfo=dt.timezone.utc)

    # Latest cycle (00z) is incomplete (missing one member at probe lead).
    incomplete_init = dt.datetime(2026, 2, 24, 0, 0, tzinfo=dt.timezone.utc)
    complete_init = dt.datetime(2026, 2, 23, 18, 0, tzinfo=dt.timezone.utc)

    def fake_has_inventory(
        init_time_utc: dt.datetime,
        model: str,
        product: str,
        member: str,
        fxx: int,
        source_priority,
        attempts: int = 3,
    ) -> bool:
        if init_time_utc == incomplete_init and fxx == 3 and member == "p02":
            return False
        if init_time_utc in (incomplete_init, complete_init):
            return True
        return False

    monkeypatch.setattr("src.cycle._member_has_inventory", fake_has_inventory)
    selected = discover_latest_complete_cycle(cfg, now)
    assert selected.init_time_utc == complete_init
