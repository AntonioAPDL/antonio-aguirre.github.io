#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="${ROOT_DIR}/data/_sandbox_gefs/history/state"
PID_FILE="${STATE_DIR}/daemon.pid"
STATUS_FILE="${STATE_DIR}/daemon_status.json"
BACKFILL_FILE="${STATE_DIR}/backfill_status.json"
SESSION_NAME="${GEFS_DAEMON_TMUX_SESSION:-gefs_history_daemon}"

if command -v tmux >/dev/null 2>&1; then
  if tmux has-session -t "${SESSION_NAME}" 2>/dev/null; then
    echo "[INFO] GEFS daemon tmux session active: ${SESSION_NAME}"
    tmux list-sessions -F '#{session_name} #{session_created}' | grep "^${SESSION_NAME} " || true
  else
    echo "[INFO] GEFS daemon tmux session not found: ${SESSION_NAME}"
  fi
fi

if [[ -f "${PID_FILE}" ]]; then
  PID="$(tr -d '[:space:]' < "${PID_FILE}" || true)"
  if [[ -n "${PID}" ]] && kill -0 "${PID}" 2>/dev/null; then
    CMD="$(ps -p "${PID}" -o cmd= 2>/dev/null || true)"
    echo "[INFO] GEFS daemon running pid=${PID}"
    echo "[INFO] cmd=${CMD}"
  else
    echo "[WARN] PID file exists but process is not running."
  fi
else
  echo "[INFO] GEFS daemon PID file not found."
fi

for f in "${STATUS_FILE}" "${BACKFILL_FILE}"; do
  if [[ -f "${f}" ]]; then
    echo "[INFO] $(basename "${f}"):"
    tail -n 40 "${f}"
  else
    echo "[INFO] Missing status file: ${f}"
  fi
done
