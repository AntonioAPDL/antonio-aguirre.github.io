#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="${ROOT_DIR}/data/_sandbox_gefs/history/state"
PID_FILE="${STATE_DIR}/daemon.pid"
SESSION_NAME="${GEFS_DAEMON_TMUX_SESSION:-gefs_history_daemon}"

if command -v tmux >/dev/null 2>&1; then
  if tmux has-session -t "${SESSION_NAME}" 2>/dev/null; then
    tmux kill-session -t "${SESSION_NAME}" || true
    sleep 1
    if ! tmux has-session -t "${SESSION_NAME}" 2>/dev/null; then
      echo "[OK] GEFS daemon tmux session stopped (${SESSION_NAME})."
    fi
    if tmux has-session -t "${SESSION_NAME}" 2>/dev/null; then
      echo "[WARN] tmux session still exists after kill attempt (${SESSION_NAME})."
    fi
  fi
fi

if [[ -f "${PID_FILE}" ]]; then
  PID="$(tr -d '[:space:]' < "${PID_FILE}" || true)"
else
  PID=""
fi

if [[ -z "${PID}" ]]; then
  rm -f "${PID_FILE}"
  echo "[INFO] No valid daemon PID file found; checking for orphan processes."
elif ! kill -0 "${PID}" 2>/dev/null; then
  rm -f "${PID_FILE}"
  echo "[INFO] GEFS daemon not running; stale PID file removed."
else
  kill "${PID}" 2>/dev/null || true
  for _ in $(seq 1 30); do
    if ! kill -0 "${PID}" 2>/dev/null; then
      break
    fi
    sleep 1
  done
  if kill -0 "${PID}" 2>/dev/null; then
    echo "[WARN] GEFS daemon did not exit within 30s, sending SIGKILL (pid=${PID})."
    kill -9 "${PID}" 2>/dev/null || true
  fi
fi

mapfile -t ORPHAN_PIDS < <(pgrep -f "run_backfill_daemon.py" || true)
if [[ ${#ORPHAN_PIDS[@]} -gt 0 ]]; then
  kill "${ORPHAN_PIDS[@]}" 2>/dev/null || true
  sleep 1
  mapfile -t STILL_UP < <(pgrep -f "run_backfill_daemon.py" || true)
  if [[ ${#STILL_UP[@]} -gt 0 ]]; then
    kill -9 "${STILL_UP[@]}" 2>/dev/null || true
  fi
fi

rm -f "${PID_FILE}"
echo "[OK] GEFS daemon stopped."
