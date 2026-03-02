from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.backfill import (  # noqa: E402
    GEFS_EARLIEST_INIT_UTC,
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
    start, end = resolve_backfill_window(
        cfg_path=Path("/tmp/gefs.yaml"),
        start_init_utc=None,
        end_init_utc=None,
        pilot_days=7,
    )
    assert end == fake_latest
    assert start == GEFS_EARLIEST_INIT_UTC


def test_resolve_window_rejects_pilot_plus_explicit() -> None:
    with pytest.raises(ValueError):
        resolve_backfill_window(
            cfg_path=Path("/tmp/gefs.yaml"),
            start_init_utc=dt.datetime(2026, 2, 1, 0, 0, tzinfo=dt.timezone.utc),
            end_init_utc=None,
            pilot_days=7,
        )
