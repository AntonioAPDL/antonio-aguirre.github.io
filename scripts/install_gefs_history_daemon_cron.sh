#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
START_SCRIPT="${ROOT_DIR}/scripts/start_gefs_history_daemon.sh"
LOG_DIR="${ROOT_DIR}/data/_sandbox_gefs/history/logs"
CRON_LOG="${LOG_DIR}/daemon_watchdog.log"
mkdir -p "${LOG_DIR}"

if [[ ! -x "${START_SCRIPT}" ]]; then
  echo "[ERROR] Missing executable start script: ${START_SCRIPT}" >&2
  exit 1
fi

EXISTING="$(crontab -l 2>/dev/null || true)"
START_LINE="@reboot cd ${ROOT_DIR} && ${START_SCRIPT} >> ${CRON_LOG} 2>&1"
WATCHDOG_LINE="*/30 * * * * cd ${ROOT_DIR} && ${START_SCRIPT} >> ${CRON_LOG} 2>&1"

FILTERED="$(printf '%s\n' "${EXISTING}" | grep -v "${START_SCRIPT}" || true)"
{
  printf '%s\n' "${FILTERED}"
  printf '%s\n' "${START_LINE}"
  printf '%s\n' "${WATCHDOG_LINE}"
} | sed '/^$/d' | crontab -

echo "[OK] Installed GEFS daemon cron entries:"
echo "  ${START_LINE}"
echo "  ${WATCHDOG_LINE}"
