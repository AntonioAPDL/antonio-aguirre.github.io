#!/usr/bin/env python3
from __future__ import annotations

import atexit
import argparse
import datetime as dt
import fcntl
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


SCRIPT_PATH = Path(__file__).resolve()
PIPELINE_DIR = SCRIPT_PATH.parent
if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))

from src.backfill import BackfillOptions, resolve_backfill_window, run_backfill  # noqa: E402
from src.runner import parse_init_time, setup_logging  # noqa: E402


def _parse_dt(value: Optional[str]) -> Optional[dt.datetime]:
    if value is None:
        return None
    parsed = parse_init_time(value)
    if parsed is None:
        return None
    return parsed


def _write_json_atomic(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)


def _append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, sort_keys=True) + "\n")


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _acquire_daemon_lock(
    lock_path: Path,
    *,
    run_label: str,
    wait_for_lock: bool,
) -> Tuple[Optional[int], Dict[str, Any]]:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
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
        "pid": int(os.getpid()),
        "run_label": run_label,
        "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    os.ftruncate(fd, 0)
    os.write(fd, json.dumps(payload, indent=2).encode("utf-8"))
    os.fsync(fd)
    return fd, payload


def _release_daemon_lock(lock_fd: Optional[int]) -> None:
    if lock_fd is None:
        return
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
    finally:
        os.close(lock_fd)


def _write_pid_atomic(path: Path, pid: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(f"{int(pid)}\n", encoding="utf-8")
    tmp.replace(path)


def _remove_pid_if_owner(path: Path, pid: int) -> None:
    try:
        current = int(path.read_text(encoding="utf-8").strip())
    except Exception:
        current = -1
    if current == int(pid):
        path.unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Background GEFS backfill daemon: historical catchup + rolling incremental updates."
        )
    )
    parser.add_argument(
        "--gefs-config",
        default=str(PIPELINE_DIR / "config" / "gefs.yaml"),
        help="Path to GEFS pipeline config YAML",
    )
    parser.add_argument(
        "--points-config",
        default=str(PIPELINE_DIR / "config" / "points.yaml"),
        help="Path to points config YAML",
    )
    parser.add_argument(
        "--point-id",
        default="big_trees",
        help="Point id from points.yaml",
    )
    parser.add_argument(
        "--history-root",
        default=str((PIPELINE_DIR.parents[1] / "data" / "_sandbox_gefs" / "history").resolve()),
        help="Root directory for historical point-level artifacts/state.",
    )
    parser.add_argument(
        "--full-start-init",
        default="2017-01-01T00:00:00Z",
        help="Historical catchup start init UTC.",
    )
    parser.add_argument(
        "--incremental-pilot-days",
        type=int,
        default=3,
        help="Rolling incremental window in days for each daemon cycle.",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=int,
        default=21600,
        help="Seconds to sleep between daemon cycles (default 6h).",
    )
    parser.add_argument(
        "--catchup-every-hours",
        type=int,
        default=24,
        help="Run full history catchup pass every N hours.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=2,
        help="Process workers (cycles in parallel).",
    )
    parser.add_argument(
        "--cycle-max-workers",
        type=int,
        default=4,
        help="Thread workers per cycle extraction.",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=None,
        help="Optional retry override for request-level operations.",
    )
    parser.add_argument(
        "--retry-backoff-sec",
        type=float,
        default=None,
        help="Optional retry backoff base seconds.",
    )
    parser.add_argument(
        "--cleanup-stale-tmp-hours",
        type=float,
        default=6.0,
        help="Delete stale .tmp_* dirs older than this many hours.",
    )
    parser.add_argument(
        "--keep-failed-dirs",
        type=int,
        default=400,
        help="Retain this many .failed_* cycle dirs globally.",
    )
    parser.add_argument(
        "--run-label",
        default="gefs_history_daemon",
        help="Label for daemon-generated backfill runs.",
    )
    parser.add_argument(
        "--wait-for-lock",
        action="store_true",
        help="Wait for daemon lock if another daemon instance is active.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level",
    )
    return parser.parse_args()


def _run_one_phase(
    *,
    phase_name: str,
    repo_root: Path,
    args: argparse.Namespace,
    history_root: Path,
    start_init_utc: dt.datetime,
    end_init_utc: dt.datetime,
    retry_failed_only: bool,
    status_path: Path,
    runs_log_path: Path,
) -> Dict[str, Any]:
    phase_started = dt.datetime.now(dt.timezone.utc)
    logging.info(
        "phase=%s start=%s end=%s retry_failed_only=%s",
        phase_name,
        start_init_utc.isoformat(),
        end_init_utc.isoformat(),
        retry_failed_only,
    )
    try:
        options = BackfillOptions(
            repo_root=repo_root,
            gefs_config=Path(args.gefs_config),
            points_config=Path(args.points_config),
            point_id=str(args.point_id),
            start_init_utc=start_init_utc,
            end_init_utc=end_init_utc,
            history_root=history_root,
            workers=max(1, int(args.workers)),
            cycle_max_workers=max(1, int(args.cycle_max_workers)),
            retries=args.retries,
            retry_backoff_sec=args.retry_backoff_sec,
            force=False,
            progress_every=1,
            run_label=f"{args.run_label}:{phase_name}",
            run_profile="full",
            retry_failed_only=retry_failed_only,
            cleanup_stale_tmp_hours=float(args.cleanup_stale_tmp_hours),
            keep_failed_dirs=max(0, int(args.keep_failed_dirs)),
            wait_for_lock=False,
        )
        summary = run_backfill(options)
        phase_state = str(summary.get("state", "unknown"))
        payload = {
            "phase": phase_name,
            "state": phase_state,
            "phase_started_utc": phase_started.isoformat(),
            "phase_completed_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "summary": summary,
        }
        _append_jsonl(runs_log_path, payload)
        _write_json_atomic(
            status_path,
            {
                "daemon_state": "running",
                "phase": phase_name,
                "phase_state": phase_state,
                "updated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "last_summary": summary,
            },
        )
        return payload
    except Exception as exc:  # pragma: no cover
        payload = {
            "phase": phase_name,
            "state": "error",
            "phase_started_utc": phase_started.isoformat(),
            "phase_completed_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "error": str(exc),
        }
        _append_jsonl(runs_log_path, payload)
        _write_json_atomic(
            status_path,
            {
                "daemon_state": "running",
                "phase": phase_name,
                "phase_state": "error",
                "updated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "last_error": str(exc),
            },
        )
        logging.exception("phase=%s failed", phase_name)
        return payload


def main() -> int:
    args = parse_args()
    setup_logging(args.log_level)

    repo_root = PIPELINE_DIR.parents[1]
    history_root = Path(args.history_root).resolve()
    state_root = history_root / "state"
    state_root.mkdir(parents=True, exist_ok=True)
    status_path = state_root / "daemon_status.json"
    runs_log_path = state_root / "daemon_runs.jsonl"
    lock_path = state_root / "daemon.lock"
    pid_path = state_root / "daemon.pid"

    lock_fd, lock_meta = _acquire_daemon_lock(
        lock_path,
        run_label=str(args.run_label),
        wait_for_lock=bool(args.wait_for_lock),
    )
    if lock_fd is None:
        _write_json_atomic(
            status_path,
            {
                "daemon_state": "already_running",
                "updated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "lock_path": str(lock_path),
                "locked_by": lock_meta,
            },
        )
        logging.warning("daemon lock busy: %s", lock_meta)
        return 0

    atexit.register(_release_daemon_lock, lock_fd)
    _write_pid_atomic(pid_path, os.getpid())
    atexit.register(_remove_pid_if_owner, pid_path, os.getpid())

    full_start = _parse_dt(args.full_start_init)
    if full_start is None:
        raise ValueError("--full-start-init must be a valid UTC datetime")
    full_start = full_start.astimezone(dt.timezone.utc)
    if int(args.incremental_pilot_days) < 1:
        raise ValueError("--incremental-pilot-days must be >= 1")

    started_utc = dt.datetime.now(dt.timezone.utc)
    _write_json_atomic(
        status_path,
        {
            "daemon_state": "running",
            "started_utc": started_utc.isoformat(),
            "updated_utc": started_utc.isoformat(),
            "pid": int(os.getpid()),
            "lock_path": str(lock_path),
            "sleep_seconds": int(args.sleep_seconds),
            "catchup_every_hours": int(args.catchup_every_hours),
            "full_start_init_utc": full_start.isoformat(),
            "incremental_pilot_days": int(args.incremental_pilot_days),
        },
    )

    last_catchup: Optional[dt.datetime] = None
    sleep_seconds = max(60, int(args.sleep_seconds))
    catchup_every_hours = max(1, int(args.catchup_every_hours))

    try:
        while True:
            now = dt.datetime.now(dt.timezone.utc)
            do_catchup = (
                last_catchup is None
                or (now - last_catchup) >= dt.timedelta(hours=catchup_every_hours)
            )

            if do_catchup:
                catchup_start, catchup_end = resolve_backfill_window(
                    cfg_path=Path(args.gefs_config),
                    start_init_utc=full_start,
                    end_init_utc=None,
                    pilot_days=None,
                )
                _run_one_phase(
                    phase_name="catchup_full",
                    repo_root=repo_root,
                    args=args,
                    history_root=history_root,
                    start_init_utc=catchup_start,
                    end_init_utc=catchup_end,
                    retry_failed_only=False,
                    status_path=status_path,
                    runs_log_path=runs_log_path,
                )
                _run_one_phase(
                    phase_name="catchup_retry_failed",
                    repo_root=repo_root,
                    args=args,
                    history_root=history_root,
                    start_init_utc=catchup_start,
                    end_init_utc=catchup_end,
                    retry_failed_only=True,
                    status_path=status_path,
                    runs_log_path=runs_log_path,
                )
                last_catchup = dt.datetime.now(dt.timezone.utc)

            inc_start, inc_end = resolve_backfill_window(
                cfg_path=Path(args.gefs_config),
                start_init_utc=None,
                end_init_utc=None,
                pilot_days=int(args.incremental_pilot_days),
            )
            _run_one_phase(
                phase_name="incremental_recent",
                repo_root=repo_root,
                args=args,
                history_root=history_root,
                start_init_utc=inc_start,
                end_init_utc=inc_end,
                retry_failed_only=False,
                status_path=status_path,
                runs_log_path=runs_log_path,
            )
            _run_one_phase(
                phase_name="incremental_retry_failed",
                repo_root=repo_root,
                args=args,
                history_root=history_root,
                start_init_utc=inc_start,
                end_init_utc=inc_end,
                retry_failed_only=True,
                status_path=status_path,
                runs_log_path=runs_log_path,
            )

            next_wake = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=sleep_seconds)
            _write_json_atomic(
                status_path,
                {
                    "daemon_state": "sleeping",
                    "updated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "pid": int(os.getpid()),
                    "next_wake_utc": next_wake.isoformat(),
                    "sleep_seconds": sleep_seconds,
                    "last_catchup_utc": last_catchup.isoformat() if last_catchup else "",
                },
            )
            time.sleep(sleep_seconds)
    except KeyboardInterrupt:
        logging.info("daemon interrupted by signal/keyboard")
        _write_json_atomic(
            status_path,
            {
                "daemon_state": "stopped",
                "updated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "pid": int(os.getpid()),
                "reason": "interrupt",
            },
        )
        return 0
    except Exception as exc:  # pragma: no cover
        logging.exception("daemon crashed")
        _write_json_atomic(
            status_path,
            {
                "daemon_state": "error",
                "updated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "pid": int(os.getpid()),
                "error": str(exc),
            },
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
