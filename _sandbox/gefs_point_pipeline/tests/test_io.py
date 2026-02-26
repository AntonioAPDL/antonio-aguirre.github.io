from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.storage import prune_failed_runs, prune_old_runs  # noqa: E402


def test_prune_old_runs_keep_one(tmp_path: Path) -> None:
    runs = tmp_path / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    for tag in ("20260223_00", "20260223_06", "20260223_12"):
        (runs / tag).mkdir()
    deleted = prune_old_runs(runs, keep_cycles=1, protected=["20260223_12"])
    assert "20260223_00" in deleted
    assert "20260223_06" in deleted
    assert not (runs / "20260223_06").exists()
    assert (runs / "20260223_12").exists()


def test_prune_failed_runs_keep_two(tmp_path: Path) -> None:
    runs = tmp_path / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    for tag in (
        ".failed_20260223_18_aaa111",
        ".failed_20260223_18_bbb222",
        ".failed_20260223_18_ccc333",
    ):
        (runs / tag).mkdir()
    deleted = prune_failed_runs(runs, keep_failed_runs=2)
    assert ".failed_20260223_18_aaa111" in deleted
    assert (runs / ".failed_20260223_18_bbb222").exists()
    assert (runs / ".failed_20260223_18_ccc333").exists()
