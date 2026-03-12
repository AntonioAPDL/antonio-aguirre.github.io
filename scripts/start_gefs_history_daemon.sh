#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIPELINE_DIR="${ROOT_DIR}/_sandbox/gefs_point_pipeline"
STATE_DIR="${ROOT_DIR}/data/_sandbox_gefs/history/state"
LOG_DIR="${ROOT_DIR}/data/_sandbox_gefs/history/logs"
PID_FILE="${STATE_DIR}/daemon.pid"
STATUS_FILE="${STATE_DIR}/daemon_status.json"
LOG_FILE="${LOG_DIR}/daemon.log"
PYTHON_BIN="${PIPELINE_DIR}/.venv/bin/python"
SESSION_NAME="${GEFS_DAEMON_TMUX_SESSION:-gefs_history_daemon}"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "[ERROR] Missing Python runtime: ${PYTHON_BIN}" >&2
  echo "[ERROR] Create and install deps first:" >&2
  echo "  cd ${PIPELINE_DIR} && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt" >&2
  exit 1
fi

mkdir -p "${STATE_DIR}" "${LOG_DIR}"

if command -v tmux >/dev/null 2>&1; then
  if tmux has-session -t "${SESSION_NAME}" 2>/dev/null; then
    echo "[INFO] GEFS daemon tmux session already running (${SESSION_NAME})."
    exit 0
  fi
fi

EXISTING_DAEMON_PID="$(pgrep -f "run_backfill_daemon.py" | head -n 1 || true)"
if [[ -n "${EXISTING_DAEMON_PID}" ]]; then
  echo "${EXISTING_DAEMON_PID}" > "${PID_FILE}"
  echo "[INFO] GEFS daemon process already running (pid=${EXISTING_DAEMON_PID})."
  echo "[INFO] status_file=${STATUS_FILE}"
  exit 0
fi

cd "${PIPELINE_DIR}"

DEFAULT_ARGS=(
  --full-start-init 2020-10-01T00:00:00Z
  --incremental-pilot-days 3
  --sleep-seconds 1800
  --catchup-every-hours 1
  --workers 4
  --cycle-max-workers 8
  --catchup-chunk-cycles 1
  --run-label gefs_history_daemon
)

if [[ $# -gt 0 ]]; then
  ARGS=("$@")
else
  ARGS=("${DEFAULT_ARGS[@]}")
fi

if command -v tmux >/dev/null 2>&1; then
  ARG_STR=""
  for item in "${ARGS[@]}"; do
    ARG_STR+=" $(printf '%q' "${item}")"
  done
  CMD="cd $(printf '%q' "${PIPELINE_DIR}") && exec $(printf '%q' "${PYTHON_BIN}") run_backfill_daemon.py${ARG_STR} >> $(printf '%q' "${LOG_FILE}") 2>&1"
  if ! tmux new-session -d -s "${SESSION_NAME}" "${CMD}" 2>/dev/null; then
    if tmux has-session -t "${SESSION_NAME}" 2>/dev/null; then
      echo "[INFO] GEFS daemon tmux session already running (${SESSION_NAME})."
      exit 0
    fi
    echo "[ERROR] Unable to start tmux session ${SESSION_NAME}; see ${LOG_FILE}" >&2
    exit 1
  fi
  sleep 1
  if tmux has-session -t "${SESSION_NAME}" 2>/dev/null; then
    echo "[OK] GEFS daemon started in tmux session ${SESSION_NAME}."
    echo "[INFO] status_file=${STATUS_FILE}"
    echo "[INFO] log_file=${LOG_FILE}"
    exit 0
  fi
  echo "[ERROR] tmux session failed to start; see ${LOG_FILE}" >&2
  exit 1
fi

nohup "${PYTHON_BIN}" run_backfill_daemon.py "${ARGS[@]}" >>"${LOG_FILE}" 2>&1 &
NEW_PID=$!
echo "${NEW_PID}" > "${PID_FILE}"
sleep 2
if kill -0 "${NEW_PID}" 2>/dev/null; then
  echo "[OK] GEFS daemon started (pid=${NEW_PID})."
  echo "[INFO] status_file=${STATUS_FILE}"
  echo "[INFO] log_file=${LOG_FILE}"
  exit 0
fi
echo "[ERROR] GEFS daemon failed to stay running; see ${LOG_FILE}" >&2
exit 1
