from __future__ import annotations

import datetime as dt
import os
import sys
import time
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.backfill import (  # noqa: E402
    GEFS_AWS_AVAILABLE_FROM_UTC,
    GEFS_EARLIEST_INIT_UTC,
    _availability_start_for_config,
    _cleanup_stale_temp_dirs,
    _failed_cycle_tags,
    count_cycles_inclusive,
    iter_cycle_times,
    pilot_start_for_days,
    resolve_backfill_window,
)


def test_iter_cycle_times_inclusive_and_step() -> None:
    start = dt.datetime(2026, 2, 24, 0, 0, tzinfo=dt.timezone.utc)
    end = dt.datetime(2026, 2, 24, 18, 0, tzinfo=dt.timezone.utc)
    cycles = iter_cycle_times(start, end)
    assert len(cycles) == 4
    assert cycles[0] == start
    assert cycles[-1] == end
    for left, right in zip(cycles[:-1], cycles[1:]):
        assert (right - left).total_seconds() == 6 * 3600


def test_pilot_start_for_days_returns_exact_cycle_count() -> None:
    end = dt.datetime(2026, 3, 1, 0, 0, tzinfo=dt.timezone.utc)
    start = pilot_start_for_days(end, pilot_days=7)
    assert count_cycles_inclusive(start, end) == 28


def test_resolve_window_pilot_clamps_to_gefs_start(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_latest = dt.datetime(2017, 1, 2, 0, 0, tzinfo=dt.timezone.utc)
    monkeypatch.setattr("src.backfill.discover_latest_complete_init", lambda cfg_path: fake_latest)
    monkeypatch.setattr(
        "src.backfill._availability_start_for_config", lambda cfg_path: GEFS_EARLIEST_INIT_UTC
    )
    start, end = resolve_backfill_window(
        cfg_path=Path("/tmp/gefs.yaml"),
        start_init_utc=None,
        end_init_utc=None,
        pilot_days=7,
    )
    assert end == fake_latest
    assert start == GEFS_EARLIEST_INIT_UTC


def test_resolve_window_rejects_pilot_plus_explicit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.backfill._availability_start_for_config", lambda cfg_path: GEFS_EARLIEST_INIT_UTC
    )
    with pytest.raises(ValueError):
        resolve_backfill_window(
            cfg_path=Path("/tmp/gefs.yaml"),
            start_init_utc=dt.datetime(2026, 2, 1, 0, 0, tzinfo=dt.timezone.utc),
            end_init_utc=None,
            pilot_days=7,
        )


def test_availability_start_for_aws_gefs(tmp_path: Path) -> None:
    cfg_path = tmp_path / "gefs.yaml"
    cfg_path.write_text(
        """
source_priority: ["aws"]
model: "gefs"
products_try: ["atmos.5"]
members: ["c00"]
lead_hours:
  start: 0
  end: 3
  step: 3
variables:
  precip:
    canonical_name: "APCP"
    search_strings: ["APCP"]
runtime: {}
output: {}
qc: {}
""".strip()
        + "\n",
        encoding="utf-8",
    )
    assert _availability_start_for_config(cfg_path) == GEFS_AWS_AVAILABLE_FROM_UTC


def test_failed_cycle_tags_extracts_unique_tags(tmp_path: Path) -> None:
    cycles = tmp_path / "cycles"
    cycles.mkdir(parents=True, exist_ok=True)
    (cycles / ".failed_20260223_06_aaa111").mkdir()
    (cycles / ".failed_20260223_06_bbb222").mkdir()
    (cycles / ".failed_20260223_12_ccc333").mkdir()
    (cycles / "20260223_18").mkdir()
    tags = _failed_cycle_tags(cycles)
    assert tags == {"20260223_06", "20260223_12"}


def test_cleanup_stale_temp_dirs_removes_old_only(tmp_path: Path) -> None:
    cycles = tmp_path / "cycles"
    cycles.mkdir(parents=True, exist_ok=True)
    old_tmp = cycles / ".tmp_20260223_06_deadbeef"
    new_tmp = cycles / ".tmp_20260224_00_feedface"
    old_tmp.mkdir()
    new_tmp.mkdir()
    (old_tmp / "old.bin").write_text("x", encoding="utf-8")
    (new_tmp / "new.bin").write_text("x", encoding="utf-8")

    now = time.time()
    os.utime(old_tmp, (now - 3 * 3600, now - 3 * 3600))
    os.utime(new_tmp, (now, now))

    deleted = _cleanup_stale_temp_dirs(cycles, older_than_hours=1)
    assert old_tmp.name in deleted
    assert not old_tmp.exists()
    assert new_tmp.exists()
