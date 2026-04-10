#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${ROOT_DIR}/logs/site_updates"
RUNNER="${ROOT_DIR}/scripts/run_site_updates_and_push.sh"
CRON_SCHEDULE="${1:-20 1,7,13,19 * * *}"
BEGIN_MARKER="# >>> antonio-website site updates >>>"
END_MARKER="# <<< antonio-website site updates <<<"

mkdir -p "${LOG_DIR}"

if [[ ! -x "${RUNNER}" ]]; then
  chmod +x "${RUNNER}" || true
fi

tmp_existing="$(mktemp)"
tmp_new="$(mktemp)"
trap 'rm -f "${tmp_existing}" "${tmp_new}"' EXIT

crontab -l >"${tmp_existing}" 2>/dev/null || true

awk -v begin="${BEGIN_MARKER}" -v end="${END_MARKER}" '
  $0 == begin {skip=1; next}
  $0 == end   {skip=0; next}
  !skip {print}
' "${tmp_existing}" > "${tmp_new}"

{
  echo "${BEGIN_MARKER}"
  echo "CRON_TZ=UTC"
  echo "${CRON_SCHEDULE} ${RUNNER} >> ${LOG_DIR}/cron_driver.log 2>&1"
  echo "${END_MARKER}"
} >> "${tmp_new}"

crontab "${tmp_new}"

echo "[OK] Installed site update cron block."
echo "[OK] Schedule (UTC): ${CRON_SCHEDULE}"
echo "[OK] Runner: ${RUNNER}"
echo "[OK] Driver log: ${LOG_DIR}/cron_driver.log"
