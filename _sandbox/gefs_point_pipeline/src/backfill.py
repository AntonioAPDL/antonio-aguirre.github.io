from __future__ import annotations

import concurrent.futures
import dataclasses
import datetime as dt
import fcntl
import json
import math
import os
import re
import tempfile
import time
import traceback
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .config import load_pipeline_config, load_point_config
from .cycle import CYCLE_HOURS, cycle_tag, discover_latest_complete_cycle
from .runner import RunOptions, run_pipeline
from .storage import ensure_dir, prune_failed_runs, read_manifest


CYCLE_STEP_HOURS = 6
GEFS_EARLIEST_INIT_UTC = dt.datetime(2017, 1, 1, 0, 0, tzinfo=dt.timezone.utc)
FAILED_CYCLE_RE = re.compile(r"^\.failed_(\d{8}_\d{2})_[A-Za-z0-9]+$")


@dataclass(frozen=True)
class BackfillOptions:
    repo_root: Path
    gefs_config: Path
    points_config: Path
    point_id: str
    start_init_utc: dt.datetime
    end_init_utc: dt.datetime
    history_root: Path
    workers: int
    cycle_max_workers: int
    retries: Optional[int]
    retry_backoff_sec: Optional[float]
    force: bool
    progress_every: int
    run_label: str
    run_profile: str
    retry_failed_only: bool = False
    cleanup_stale_tmp_hours: float = 6.0
    keep_failed_dirs: int = 200
    wait_for_lock: bool = False


@dataclass(frozen=True)
class WorkerInput:
    repo_root: str
    gefs_config: str
    points_config: str
    point_id: str
    init_time_utc: str
    runs_root: str
    web_out_dir: str
    cycle_max_workers: int
    retries: Optional[int]
    retry_backoff_sec: Optional[float]
    force: bool
    run_profile: str


@dataclass(frozen=True)
class LockHandle:
    path: Path
    fd: int


@dataclass(frozen=True)
class CycleResult:
    init_time_utc: str
    run_tag: str
    status: str
    elapsed_sec: float
    run_dir: str
    manifest_path: str
    bytes_downloaded: int
    timing_seconds: Dict[str, float]
    error: str
    traceback: str


def to_utc(value: dt.datetime) -> dt.datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=dt.timezone.utc)
    return value.astimezone(dt.timezone.utc)


def require_cycle_alignment(value: dt.datetime) -> dt.datetime:
    utc = to_utc(value)
    if utc.minute != 0 or utc.second != 0 or utc.microsecond != 0:
        raise ValueError(f"Cycle must be at exact hour: {utc.isoformat()}")
    if utc.hour not in CYCLE_HOURS:
        raise ValueError(f"Cycle hour must be one of {CYCLE_HOURS}: {utc.isoformat()}")
    return utc


def iter_cycle_times(start_init_utc: dt.datetime, end_init_utc: dt.datetime) -> List[dt.datetime]:
    start = require_cycle_alignment(start_init_utc)
    end = require_cycle_alignment(end_init_utc)
    if start > end:
        raise ValueError("start_init_utc cannot be after end_init_utc")
    out: List[dt.datetime] = []
    cur = start
    step = dt.timedelta(hours=CYCLE_STEP_HOURS)
    while cur <= end:
        out.append(cur)
        cur = cur + step
    return out


def pilot_start_for_days(end_init_utc: dt.datetime, pilot_days: int) -> dt.datetime:
    if pilot_days < 1:
        raise ValueError("pilot_days must be >= 1")
    cycles = pilot_days * int(24 // CYCLE_STEP_HOURS)
    start = require_cycle_alignment(end_init_utc) - dt.timedelta(
        hours=CYCLE_STEP_HOURS * max(0, cycles - 1)
    )
    return start


def count_cycles_inclusive(start_init_utc: dt.datetime, end_init_utc: dt.datetime) -> int:
    start = require_cycle_alignment(start_init_utc)
    end = require_cycle_alignment(end_init_utc)
    if start > end:
        return 0
    hours = (end - start).total_seconds() / 3600.0
    return int(hours // CYCLE_STEP_HOURS) + 1


def discover_latest_complete_init(cfg_path: Path) -> dt.datetime:
    cfg = load_pipeline_config(cfg_path)
    with tempfile.TemporaryDirectory(prefix="gefs_cycle_probe_") as temp_dir:
        selection = discover_latest_complete_cycle(
            cfg,
            dt.datetime.now(dt.timezone.utc),
            save_dir=Path(temp_dir),
        )
    return to_utc(selection.init_time_utc)


def resolve_backfill_window(
    cfg_path: Path,
    start_init_utc: Optional[dt.datetime],
    end_init_utc: Optional[dt.datetime],
    pilot_days: Optional[int],
) -> Tuple[dt.datetime, dt.datetime]:
    if pilot_days is not None and (start_init_utc is not None or end_init_utc is not None):
        raise ValueError("Use either pilot_days or explicit start/end window, not both")

    if pilot_days is not None:
        end = discover_latest_complete_init(cfg_path)
        start = pilot_start_for_days(end, pilot_days)
        start = max(start, GEFS_EARLIEST_INIT_UTC)
        return start, end

    start = to_utc(start_init_utc or GEFS_EARLIEST_INIT_UTC)
    end = to_utc(end_init_utc or discover_latest_complete_init(cfg_path))
    if start < GEFS_EARLIEST_INIT_UTC:
        start = GEFS_EARLIEST_INIT_UTC
    return require_cycle_alignment(start), require_cycle_alignment(end)


def _write_json_atomic(path: Path, payload: Dict[str, Any]) -> None:
    ensure_dir(path.parent)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp_path.replace(path)


def _append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    ensure_dir(path.parent)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, sort_keys=True) + "\n")


def _history_paths(history_root: Path) -> Dict[str, Path]:
    root = history_root.resolve()
    return {
        "root": root,
        "cycles": root / "cycles",
        "state": root / "state",
        "logs": root / "logs",
    }


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _acquire_lock(
    lock_path: Path,
    run_id: str,
    run_label: str,
    wait_for_lock: bool,
) -> Tuple[Optional[LockHandle], Dict[str, Any]]:
    ensure_dir(lock_path.parent)
    fd = os.open(str(lock_path), os.O_RDWR | os.O_CREAT, 0o664)
    try:
        flags = fcntl.LOCK_EX
        if not wait_for_lock:
            flags |= fcntl.LOCK_NB
        fcntl.flock(fd, flags)
    except BlockingIOError:
        existing = _read_json(lock_path)
        os.close(fd)
        return None, existing

    payload = {
        "run_id": run_id,
        "run_label": run_label,
        "pid": int(os.getpid()),
        "acquired_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    os.ftruncate(fd, 0)
    os.write(fd, json.dumps(payload).encode("utf-8"))
    os.fsync(fd)
    return LockHandle(path=lock_path, fd=fd), payload


def _release_lock(handle: Optional[LockHandle]) -> None:
    if handle is None:
        return
    try:
        fcntl.flock(handle.fd, fcntl.LOCK_UN)
    except Exception:
        pass
    try:
        os.close(handle.fd)
    except OSError:
        pass


def _cleanup_stale_temp_dirs(cycles_root: Path, older_than_hours: float) -> List[str]:
    if older_than_hours <= 0:
        return []
    if not cycles_root.exists():
        return []

    cutoff = time.time() - (float(older_than_hours) * 3600.0)
    deleted: List[str] = []
    for entry in cycles_root.iterdir():
        if not entry.is_dir() or not entry.name.startswith(".tmp_"):
            continue
        try:
            mtime = entry.stat().st_mtime
        except OSError:
            continue
        if mtime > cutoff:
            continue
        for sub in sorted(entry.rglob("*"), reverse=True):
            try:
                if sub.is_file() or sub.is_symlink():
                    sub.unlink(missing_ok=True)  # type: ignore[arg-type]
                elif sub.is_dir():
                    sub.rmdir()
            except Exception:
                pass
        try:
            entry.rmdir()
            deleted.append(entry.name)
        except Exception:
            pass
    return sorted(deleted)


def _failed_cycle_tags(cycles_root: Path) -> set[str]:
    tags: set[str] = set()
    if not cycles_root.exists():
        return tags
    for entry in cycles_root.iterdir():
        if not entry.is_dir():
            continue
        match = FAILED_CYCLE_RE.match(entry.name)
        if not match:
            continue
        tags.add(match.group(1))
    return tags


def _existing_successful_tags(cycles_root: Path) -> set[str]:
    if not cycles_root.exists():
        return set()
    out: set[str] = set()
    for run_dir in cycles_root.iterdir():
        if not run_dir.is_dir():
            continue
        manifest = read_manifest(run_dir / "manifest.json")
        if manifest.get("status") == "success":
            out.add(run_dir.name)
    return out


def _override_config_for_history(
    worker: WorkerInput,
):
    cfg = load_pipeline_config(Path(worker.gefs_config))
    point = load_point_config(Path(worker.points_config), worker.point_id)

    runtime_updates: Dict[str, Any] = {
        "max_workers": max(1, int(worker.cycle_max_workers)),
    }
    if worker.retries is not None:
        runtime_updates["retries"] = int(worker.retries)
    if worker.retry_backoff_sec is not None:
        runtime_updates["retry_backoff_sec"] = float(worker.retry_backoff_sec)
    runtime = dataclasses.replace(cfg.runtime, **runtime_updates)

    output = dataclasses.replace(
        cfg.output,
        runs_root=Path(worker.runs_root),
        smoke_runs_root=Path(worker.runs_root),
        web_out_dir=Path(worker.web_out_dir),
    )

    effective_cfg = dataclasses.replace(cfg, runtime=runtime, output=output)
    return effective_cfg, point


def _run_cycle_worker(worker: WorkerInput) -> CycleResult:
    started = time.perf_counter()
    init = to_utc(dt.datetime.fromisoformat(worker.init_time_utc.replace("Z", "+00:00")))
    run_tag = cycle_tag(init)
    run_dir = Path(worker.runs_root) / run_tag
    manifest_path = run_dir / "manifest.json"

    try:
        cfg, point = _override_config_for_history(worker)
        with tempfile.TemporaryDirectory(prefix=f"gefs_hist_{run_tag}_") as temp_download:
            options = RunOptions(
                repo_root=Path(worker.repo_root),
                force=bool(worker.force),
                smoke=str(worker.run_profile).lower() == "smoke",
                run_profile=str(worker.run_profile),
                explicit_init_time_utc=init,
                herbie_save_dir=Path(temp_download),
                disable_pruning=True,
            )
            result = run_pipeline(cfg=cfg, point=point, options=options)

        manifest = read_manifest(result.manifest_path)
        elapsed = time.perf_counter() - started
        timing = manifest.get("timing_seconds", {}) if isinstance(manifest, dict) else {}
        return CycleResult(
            init_time_utc=init.isoformat(),
            run_tag=run_tag,
            status=str(result.status),
            elapsed_sec=float(elapsed),
            run_dir=str(result.run_dir),
            manifest_path=str(result.manifest_path),
            bytes_downloaded=int(manifest.get("bytes_downloaded", 0) or 0),
            timing_seconds={str(k): float(v) for k, v in timing.items() if isinstance(v, (int, float))},
            error="",
            traceback="",
        )
    except Exception as exc:  # pragma: no cover - exercised in integration.
        elapsed = time.perf_counter() - started
        return CycleResult(
            init_time_utc=init.isoformat(),
            run_tag=run_tag,
            status="failed",
            elapsed_sec=float(elapsed),
            run_dir=str(run_dir),
            manifest_path=str(manifest_path),
            bytes_downloaded=0,
            timing_seconds={},
            error=str(exc),
            traceback=traceback.format_exc(),
        )


def _timing_summary(cycle_results: Sequence[CycleResult]) -> Dict[str, Any]:
    elapsed_values = [float(result.elapsed_sec) for result in cycle_results if result.elapsed_sec > 0]
    stage_values: Dict[str, List[float]] = {}
    for result in cycle_results:
        for stage, value in result.timing_seconds.items():
            if isinstance(value, (int, float)):
                stage_values.setdefault(stage, []).append(float(value))

    def _quantile(values: Sequence[float], q: float) -> float:
        if not values:
            return 0.0
        ordered = sorted(values)
        idx = min(len(ordered) - 1, max(0, int(math.floor((len(ordered) - 1) * q))))
        return float(ordered[idx])

    out: Dict[str, Any] = {
        "count": len(elapsed_values),
        "avg_cycle_sec": float(sum(elapsed_values) / len(elapsed_values)) if elapsed_values else 0.0,
        "p50_cycle_sec": _quantile(elapsed_values, 0.50),
        "p90_cycle_sec": _quantile(elapsed_values, 0.90),
    }
    for stage, values in sorted(stage_values.items()):
        if not values:
            continue
        out[f"avg_stage_{stage}_sec"] = float(sum(values) / len(values))
    return out


def _progress_payload(
    *,
    run_id: str,
    run_label: str,
    state: str,
    started_utc: dt.datetime,
    updated_utc: dt.datetime,
    start_init_utc: dt.datetime,
    end_init_utc: dt.datetime,
    total_cycles: int,
    queued_cycles: int,
    pre_skipped_success: int,
    success_count: int,
    failed_count: int,
    skipped_existing_count: int,
    completed_count: int,
    wall_seconds: float,
    history_paths: Dict[str, Path],
    failure_log_path: Path,
    workers: int,
    cycle_max_workers: int,
) -> Dict[str, Any]:
    avg_sec = float(wall_seconds / completed_count) if completed_count > 0 else 0.0
    rate_cph = float((completed_count / wall_seconds) * 3600.0) if wall_seconds > 0 else 0.0
    remaining = max(0, queued_cycles - completed_count)
    eta_utc = (
        updated_utc + dt.timedelta(seconds=avg_sec * remaining)
        if avg_sec > 0 and remaining > 0
        else None
    )
    return {
        "run_id": run_id,
        "run_label": run_label,
        "state": state,
        "started_utc": started_utc.isoformat(),
        "updated_utc": updated_utc.isoformat(),
        "start_init_utc": start_init_utc.isoformat(),
        "end_init_utc": end_init_utc.isoformat(),
        "total_cycles": int(total_cycles),
        "queued_cycles": int(queued_cycles),
        "pre_skipped_success_cycles": int(pre_skipped_success),
        "completed_cycles": int(completed_count),
        "success_cycles": int(success_count),
        "failed_cycles": int(failed_count),
        "skipped_existing_cycles": int(skipped_existing_count),
        "remaining_cycles": int(remaining),
        "avg_cycle_wall_sec": avg_sec,
        "throughput_cycles_per_hour": rate_cph,
        "eta_utc": eta_utc.isoformat() if eta_utc is not None else "",
        "workers_processes": int(workers),
        "workers_threads_per_cycle": int(cycle_max_workers),
        "history_root": str(history_paths["root"]),
        "cycles_root": str(history_paths["cycles"]),
        "state_root": str(history_paths["state"]),
        "logs_root": str(history_paths["logs"]),
        "failure_log_path": str(failure_log_path),
    }


def run_backfill(options: BackfillOptions) -> Dict[str, Any]:
    history_paths = _history_paths(options.history_root)
    ensure_dir(history_paths["cycles"])
    ensure_dir(history_paths["state"])
    ensure_dir(history_paths["logs"])

    run_id = f"gefs_backfill_{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d-%H%M%S')}_{uuid.uuid4().hex[:6]}"
    status_path = history_paths["state"] / "backfill_status.json"
    benchmark_path = history_paths["state"] / f"{run_id}_benchmark.json"
    failures_path = history_paths["logs"] / f"{run_id}_failures.jsonl"
    lock_path = history_paths["state"] / "backfill.lock"

    lock_handle, lock_meta = _acquire_lock(
        lock_path=lock_path,
        run_id=run_id,
        run_label=options.run_label,
        wait_for_lock=bool(options.wait_for_lock),
    )
    if lock_handle is None:
        return {
            "run_id": run_id,
            "run_label": options.run_label,
            "run_profile": options.run_profile,
            "state": "skipped_locked",
            "lock_path": str(lock_path),
            "locked_by": lock_meta,
            "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        }

    stale_tmp_deleted: List[str] = []
    deleted_failed_dirs: List[str] = []

    try:
        stale_tmp_deleted = _cleanup_stale_temp_dirs(
            history_paths["cycles"],
            older_than_hours=float(options.cleanup_stale_tmp_hours),
        )

        all_cycles = iter_cycle_times(options.start_init_utc, options.end_init_utc)
        existing_success = _existing_successful_tags(history_paths["cycles"]) if not options.force else set()
        if options.retry_failed_only:
            failed_tags = _failed_cycle_tags(history_paths["cycles"])
            queued = [
                cycle
                for cycle in all_cycles
                if cycle_tag(cycle) in failed_tags
                and (options.force or cycle_tag(cycle) not in existing_success)
            ]
        else:
            queued = [cycle for cycle in all_cycles if cycle_tag(cycle) not in existing_success]
        queued = sorted(queued)

        started_utc = dt.datetime.now(dt.timezone.utc)
        started_perf = time.perf_counter()
        _write_json_atomic(
            status_path,
            _progress_payload(
                run_id=run_id,
                run_label=options.run_label,
                state="running",
                started_utc=started_utc,
                updated_utc=started_utc,
                start_init_utc=options.start_init_utc,
                end_init_utc=options.end_init_utc,
                total_cycles=len(all_cycles),
                queued_cycles=len(queued),
                pre_skipped_success=len(all_cycles) - len(queued),
                success_count=0,
                failed_count=0,
                skipped_existing_count=0,
                completed_count=0,
                wall_seconds=0.0,
                history_paths=history_paths,
                failure_log_path=failures_path,
                workers=options.workers,
                cycle_max_workers=options.cycle_max_workers,
            ),
        )

        cycle_results: List[CycleResult] = []
        success_count = 0
        failed_count = 0
        skipped_existing_count = 0

        if not queued:
            completed_utc = dt.datetime.now(dt.timezone.utc)
            summary = {
                "run_id": run_id,
                "run_profile": options.run_profile,
                "run_mode": "retry_failed_only" if options.retry_failed_only else "window_backfill",
                "state": "completed",
                "started_utc": started_utc.isoformat(),
                "completed_utc": completed_utc.isoformat(),
                "window": {
                    "start_init_utc": options.start_init_utc.isoformat(),
                    "end_init_utc": options.end_init_utc.isoformat(),
                },
                "total_cycles": len(all_cycles),
                "queued_cycles": 0,
                "pre_skipped_success_cycles": len(all_cycles),
                "success_cycles": 0,
                "failed_cycles": 0,
                "skipped_existing_cycles": 0,
                "timing_summary": _timing_summary(cycle_results),
                "stale_tmp_deleted": stale_tmp_deleted,
                "deleted_failed_dirs": deleted_failed_dirs,
            }
            _write_json_atomic(benchmark_path, summary)
            _write_json_atomic(
                status_path,
                _progress_payload(
                    run_id=run_id,
                    run_label=options.run_label,
                    state="completed",
                    started_utc=started_utc,
                    updated_utc=completed_utc,
                    start_init_utc=options.start_init_utc,
                    end_init_utc=options.end_init_utc,
                    total_cycles=len(all_cycles),
                    queued_cycles=0,
                    pre_skipped_success=len(all_cycles),
                    success_count=0,
                    failed_count=0,
                    skipped_existing_count=0,
                    completed_count=0,
                    wall_seconds=0.0,
                    history_paths=history_paths,
                    failure_log_path=failures_path,
                    workers=options.workers,
                    cycle_max_workers=options.cycle_max_workers,
                ),
            )
            return summary

        worker_inputs = [
            WorkerInput(
                repo_root=str(options.repo_root),
                gefs_config=str(options.gefs_config),
                points_config=str(options.points_config),
                point_id=options.point_id,
                init_time_utc=cycle.isoformat(),
                runs_root=str(history_paths["cycles"]),
                web_out_dir=str(history_paths["root"] / "web_unused"),
                cycle_max_workers=max(1, int(options.cycle_max_workers)),
                retries=options.retries,
                retry_backoff_sec=options.retry_backoff_sec,
                force=bool(options.force),
                run_profile=str(options.run_profile),
            )
            for cycle in queued
        ]

        try:
            with concurrent.futures.ProcessPoolExecutor(max_workers=max(1, int(options.workers))) as pool:
                future_map = {
                    pool.submit(_run_cycle_worker, worker): worker.init_time_utc for worker in worker_inputs
                }
                pending = set(future_map.keys())
                heartbeat_sec = 30.0

                while pending:
                    done, pending = concurrent.futures.wait(
                        pending,
                        timeout=heartbeat_sec,
                        return_when=concurrent.futures.FIRST_COMPLETED,
                    )
                    if not done:
                        updated_utc = dt.datetime.now(dt.timezone.utc)
                        _write_json_atomic(
                            status_path,
                            _progress_payload(
                                run_id=run_id,
                                run_label=options.run_label,
                                state="running",
                                started_utc=started_utc,
                                updated_utc=updated_utc,
                                start_init_utc=options.start_init_utc,
                                end_init_utc=options.end_init_utc,
                                total_cycles=len(all_cycles),
                                queued_cycles=len(queued),
                                pre_skipped_success=len(all_cycles) - len(queued),
                                success_count=success_count,
                                failed_count=failed_count,
                                skipped_existing_count=skipped_existing_count,
                                completed_count=len(cycle_results),
                                wall_seconds=time.perf_counter() - started_perf,
                                history_paths=history_paths,
                                failure_log_path=failures_path,
                                workers=options.workers,
                                cycle_max_workers=options.cycle_max_workers,
                            ),
                        )
                        continue

                    for future in done:
                        try:
                            result = future.result()
                        except Exception as exc:  # pragma: no cover
                            init_time_utc = future_map[future]
                            result = CycleResult(
                                init_time_utc=init_time_utc,
                                run_tag=cycle_tag(to_utc(dt.datetime.fromisoformat(init_time_utc))),
                                status="failed",
                                elapsed_sec=0.0,
                                run_dir="",
                                manifest_path="",
                                bytes_downloaded=0,
                                timing_seconds={},
                                error=str(exc),
                                traceback=traceback.format_exc(),
                            )

                        cycle_results.append(result)
                        if result.status == "success":
                            success_count += 1
                        elif result.status == "skipped_existing":
                            skipped_existing_count += 1
                        else:
                            failed_count += 1
                            _append_jsonl(
                                failures_path,
                                {
                                    "run_id": run_id,
                                    "init_time_utc": result.init_time_utc,
                                    "run_tag": result.run_tag,
                                    "error": result.error,
                                    "traceback": result.traceback,
                                },
                            )

                        index = len(cycle_results)
                        if index % max(1, options.progress_every) == 0 or index == len(worker_inputs):
                            updated_utc = dt.datetime.now(dt.timezone.utc)
                            _write_json_atomic(
                                status_path,
                                _progress_payload(
                                    run_id=run_id,
                                    run_label=options.run_label,
                                    state="running",
                                    started_utc=started_utc,
                                    updated_utc=updated_utc,
                                    start_init_utc=options.start_init_utc,
                                    end_init_utc=options.end_init_utc,
                                    total_cycles=len(all_cycles),
                                    queued_cycles=len(queued),
                                    pre_skipped_success=len(all_cycles) - len(queued),
                                    success_count=success_count,
                                    failed_count=failed_count,
                                    skipped_existing_count=skipped_existing_count,
                                    completed_count=index,
                                    wall_seconds=time.perf_counter() - started_perf,
                                    history_paths=history_paths,
                                    failure_log_path=failures_path,
                                    workers=options.workers,
                                    cycle_max_workers=options.cycle_max_workers,
                                ),
                            )
        except KeyboardInterrupt:  # pragma: no cover
            updated_utc = dt.datetime.now(dt.timezone.utc)
            _write_json_atomic(
                status_path,
                _progress_payload(
                    run_id=run_id,
                    run_label=options.run_label,
                    state="aborted",
                    started_utc=started_utc,
                    updated_utc=updated_utc,
                    start_init_utc=options.start_init_utc,
                    end_init_utc=options.end_init_utc,
                    total_cycles=len(all_cycles),
                    queued_cycles=len(queued),
                    pre_skipped_success=len(all_cycles) - len(queued),
                    success_count=success_count,
                    failed_count=failed_count,
                    skipped_existing_count=skipped_existing_count,
                    completed_count=len(cycle_results),
                    wall_seconds=time.perf_counter() - started_perf,
                    history_paths=history_paths,
                    failure_log_path=failures_path,
                    workers=options.workers,
                    cycle_max_workers=options.cycle_max_workers,
                ),
            )
            raise

        if options.keep_failed_dirs >= 0:
            deleted_failed_dirs = prune_failed_runs(
                history_paths["cycles"],
                keep_failed_runs=int(options.keep_failed_dirs),
            )

        completed_utc = dt.datetime.now(dt.timezone.utc)
        wall_seconds = time.perf_counter() - started_perf
        cycles_per_hour = float((len(cycle_results) / wall_seconds) * 3600.0) if wall_seconds > 0 else 0.0

        pilot_timing = _timing_summary(cycle_results)
        full_cycle_count = count_cycles_inclusive(GEFS_EARLIEST_INIT_UTC, options.end_init_utc)
        estimated_full_hours = float(full_cycle_count / cycles_per_hour) if cycles_per_hour > 0 else 0.0

        summary = {
            "run_id": run_id,
            "run_label": options.run_label,
            "run_profile": options.run_profile,
            "run_mode": "retry_failed_only" if options.retry_failed_only else "window_backfill",
            "state": "completed",
            "started_utc": started_utc.isoformat(),
            "completed_utc": completed_utc.isoformat(),
            "window": {
                "start_init_utc": options.start_init_utc.isoformat(),
                "end_init_utc": options.end_init_utc.isoformat(),
            },
            "workers_processes": int(options.workers),
            "workers_threads_per_cycle": int(options.cycle_max_workers),
            "total_cycles": int(len(all_cycles)),
            "queued_cycles": int(len(queued)),
            "pre_skipped_success_cycles": int(len(all_cycles) - len(queued)),
            "success_cycles": int(success_count),
            "failed_cycles": int(failed_count),
            "skipped_existing_cycles": int(skipped_existing_count),
            "wall_seconds": float(wall_seconds),
            "throughput_cycles_per_hour": cycles_per_hour,
            "timing_summary": pilot_timing,
            "bytes_downloaded_total": int(sum(result.bytes_downloaded for result in cycle_results)),
            "stale_tmp_deleted": stale_tmp_deleted,
            "deleted_failed_dirs": deleted_failed_dirs,
            "estimated_full_backfill": {
                "start_init_utc": GEFS_EARLIEST_INIT_UTC.isoformat(),
                "end_init_utc": options.end_init_utc.isoformat(),
                "cycle_count": int(full_cycle_count),
                "estimated_hours_at_measured_rate": estimated_full_hours,
            },
            "paths": {
                "history_root": str(history_paths["root"]),
                "cycles_root": str(history_paths["cycles"]),
                "state_root": str(history_paths["state"]),
                "logs_root": str(history_paths["logs"]),
                "status_path": str(status_path),
                "benchmark_path": str(benchmark_path),
                "failure_log_path": str(failures_path),
                "lock_path": str(lock_path),
            },
        }
        _write_json_atomic(benchmark_path, summary)
        _write_json_atomic(
            status_path,
            _progress_payload(
                run_id=run_id,
                run_label=options.run_label,
                state="completed",
                started_utc=started_utc,
                updated_utc=completed_utc,
                start_init_utc=options.start_init_utc,
                end_init_utc=options.end_init_utc,
                total_cycles=len(all_cycles),
                queued_cycles=len(queued),
                pre_skipped_success=len(all_cycles) - len(queued),
                success_count=success_count,
                failed_count=failed_count,
                skipped_existing_count=skipped_existing_count,
                completed_count=len(cycle_results),
                wall_seconds=wall_seconds,
                history_paths=history_paths,
                failure_log_path=failures_path,
                workers=options.workers,
                cycle_max_workers=options.cycle_max_workers,
            ),
        )
        return summary
    finally:
        _release_lock(lock_handle)
