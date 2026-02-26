from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict, Iterable, List

import pandas as pd


RUN_DIR_RE = re.compile(r"^\d{8}_\d{2}$")
FAILED_RUN_RE = re.compile(r"^\.failed_\d{8}_\d{2}_[A-Za-z0-9]+$")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def build_ensemble_summary(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby(
        ["site_id", "init_time_utc", "lead_hours", "valid_time_utc", "variable", "level"],
        dropna=False,
    )["value"]
    summary = grouped.agg(["mean", "std"]).reset_index()
    q = grouped.quantile([0.1, 0.5, 0.9]).unstack(level=-1).reset_index()
    q = q.rename(columns={0.1: "q10", 0.5: "q50", 0.9: "q90"})
    out = summary.merge(q, on=["site_id", "init_time_utc", "lead_hours", "valid_time_utc", "variable", "level"])
    counts = grouped.count().reset_index(name="member_count")
    out = out.merge(
        counts,
        on=["site_id", "init_time_utc", "lead_hours", "valid_time_utc", "variable", "level"],
    )
    return out.sort_values(["variable", "level", "lead_hours"]).reset_index(drop=True)


def write_run_outputs(
    run_dir: Path,
    member_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    manifest: Dict[str, Any],
    log_lines: Iterable[str],
) -> None:
    ensure_dir(run_dir)
    member_path = run_dir / "point_member.parquet"
    summary_path = run_dir / "point_ens_summary.parquet"
    manifest_path = run_dir / "manifest.json"
    log_path = run_dir / "run.log"

    member_df.to_parquet(member_path, index=False)
    summary_df.to_parquet(summary_path, index=False)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")


def read_manifest(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def is_successful_run(run_dir: Path) -> bool:
    manifest = read_manifest(run_dir / "manifest.json")
    return bool(manifest.get("status") == "success")


def publish_run(temp_dir: Path, final_dir: Path, force: bool) -> None:
    if final_dir.exists():
        if not force:
            raise FileExistsError(f"Destination run directory exists: {final_dir}")
        shutil.rmtree(final_dir)
    os.replace(str(temp_dir), str(final_dir))


def update_latest_pointer(runs_root: Path, latest_pointer_name: str, run_tag: str) -> None:
    pointer_path = runs_root / latest_pointer_name
    pointer_path.write_text(run_tag + "\n", encoding="utf-8")
    latest_link = runs_root / "latest"
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    try:
        latest_link.symlink_to(run_tag)
    except OSError:
        pass


def prune_old_runs(runs_root: Path, keep_cycles: int, protected: List[str]) -> List[str]:
    if keep_cycles < 1:
        keep_cycles = 1
    protected_set = set(protected)
    protected_existing = [
        p
        for p in runs_root.iterdir()
        if p.is_dir() and RUN_DIR_RE.match(p.name) and p.name in protected_set
    ]
    keep_unprotected = max(0, keep_cycles - len(protected_existing))
    dirs = [
        p
        for p in runs_root.iterdir()
        if p.is_dir() and RUN_DIR_RE.match(p.name) and p.name not in protected_set
    ]
    dirs.sort(key=lambda p: p.name, reverse=True)
    to_delete = dirs[keep_unprotected:]
    deleted: List[str] = []
    for path in to_delete:
        shutil.rmtree(path, ignore_errors=True)
        deleted.append(path.name)
    return deleted


def prune_failed_runs(runs_root: Path, keep_failed_runs: int) -> List[str]:
    if keep_failed_runs < 0:
        keep_failed_runs = 0
    dirs = [p for p in runs_root.iterdir() if p.is_dir() and FAILED_RUN_RE.match(p.name)]
    dirs.sort(key=lambda p: p.name, reverse=True)
    to_delete = dirs[keep_failed_runs:]
    deleted: List[str] = []
    for path in to_delete:
        shutil.rmtree(path, ignore_errors=True)
        deleted.append(path.name)
    return deleted
