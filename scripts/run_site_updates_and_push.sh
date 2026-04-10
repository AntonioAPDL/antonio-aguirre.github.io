#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${REPO_ROOT}/logs/site_updates"
RUN_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_LOG="${LOG_DIR}/run_${RUN_STAMP}.log"
RUN_LOCK="${LOG_DIR}/run.lock"

RUN_CLIMATE="${RUN_CLIMATE:-1}"
RUN_GEFS="${RUN_GEFS:-1}"
RUN_NWS="${RUN_NWS:-1}"
RUN_QDESN="${RUN_QDESN:-0}"
CLIMATE_TIMEOUT_SEC="${CLIMATE_TIMEOUT_SEC:-1800}"

ALLOW_DIRTY="${ALLOW_DIRTY:-0}"
ALLOW_STALE_ON_ERROR="${ALLOW_STALE_ON_ERROR:-1}"

PYTHON_BIN="${PYTHON_BIN:-python3}"
RSCRIPT_BIN="${RSCRIPT_BIN:-Rscript}"
export PYTHON_BIN

mkdir -p "${LOG_DIR}"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"; }

cd "${REPO_ROOT}"

exec 9>"${RUN_LOCK}"
if ! flock -n 9; then
  log "[INFO] Another site update is already running; skipping."
  exit 0
fi

if [[ "${ALLOW_DIRTY}" != "1" ]]; then
  if ! git diff --quiet || ! git diff --cached --quiet; then
    log "[ERROR] Working tree is not clean. Set ALLOW_DIRTY=1 to override."
    exit 1
  fi
  if [[ -n "$(git ls-files --others --exclude-standard)" ]]; then
    log "[ERROR] Untracked files present. Clean them or set ALLOW_DIRTY=1."
    exit 1
  fi
fi

log "[INFO] Syncing with origin/main..."
git fetch origin main >>"${RUN_LOG}" 2>&1 || true
if ! git rebase origin/main >>"${RUN_LOG}" 2>&1; then
  log "[ERROR] Rebase failed. Check ${RUN_LOG}"
  exit 1
fi

overall_rc=0

if [[ "${RUN_CLIMATE}" == "1" ]]; then
  log "[INFO] Running climate updates..."
  if command -v timeout >/dev/null && [[ "${CLIMATE_TIMEOUT_SEC}" -gt 0 ]]; then
    if ! timeout "${CLIMATE_TIMEOUT_SEC}" "${REPO_ROOT}/scripts/run_climate_updates_cron.sh" >>"${RUN_LOG}" 2>&1; then
      log "[WARN] Climate update failed or timed out (see log). Continuing."
      overall_rc=1
    fi
  else
    if ! "${REPO_ROOT}/scripts/run_climate_updates_cron.sh" >>"${RUN_LOG}" 2>&1; then
      log "[WARN] Climate update failed (see log). Continuing."
      overall_rc=1
    fi
  fi
fi

if [[ "${RUN_GEFS}" == "1" ]]; then
  log "[INFO] Running GEFS forecast update..."
  if ! GEFS_FORECAST_ALLOW_STALE_ON_ERROR="${ALLOW_STALE_ON_ERROR}" \
    "${REPO_ROOT}/scripts/update_big_trees_gefs_forecast.sh" >>"${RUN_LOG}" 2>&1; then
    log "[WARN] GEFS update failed (see log). Continuing."
    overall_rc=1
  fi
fi

if [[ "${RUN_NWS}" == "1" ]]; then
  log "[INFO] Running NWS/NWM forecast update..."
  if ! BIG_TREES_FORECAST_ALLOW_STALE_ON_ERROR="${ALLOW_STALE_ON_ERROR}" \
    "${REPO_ROOT}/scripts/update_big_trees_forecast.sh" >>"${RUN_LOG}" 2>&1; then
    log "[WARN] NWS/NWM update failed (see log). Continuing."
    overall_rc=1
  fi
fi

if [[ "${RUN_QDESN}" == "1" ]]; then
  log "[INFO] Running QDESN overlay update..."
  if ! BIG_TREES_QDESN_ALLOW_STALE_ON_ERROR="${ALLOW_STALE_ON_ERROR}" \
    "${REPO_ROOT}/scripts/update_big_trees_qdesn_fit.sh" >>"${RUN_LOG}" 2>&1; then
    log "[WARN] QDESN update failed (see log). Continuing."
    overall_rc=1
  fi
fi

TRACKED=(
  "assets/data/forecasts/gefs_big_trees_latest.json"
  "assets/data/forecasts/big_trees_latest.json"
  "assets/data/forecasts/big_trees_qdesn_latest.json"
  "prism_precipitation_santa_cruz_1987_2023.csv"
  "soil_moisture_data/soil_moisture_big_trees_daily_avg_1987_2023.csv"
  "soil_moisture_data/nwm_soil_moisture_big_trees_daily_1987_present.csv"
  "soil_moisture_data/nwm_soil_moisture_big_trees_daily_1987_present.meta.json"
  "climate_series_status.csv"
  "climate_daily_ppt_soil.csv"
)

git add -- "${TRACKED[@]}" >>"${RUN_LOG}" 2>&1 || true

if git diff --cached --quiet; then
  log "[INFO] No tracked updates to commit."
  exit "${overall_rc}"
fi

commit_msg="chore: automated site data refresh ($(date -u +%Y-%m-%d))"
git commit -m "${commit_msg}" >>"${RUN_LOG}" 2>&1

if ! git rebase origin/main >>"${RUN_LOG}" 2>&1; then
  log "[ERROR] Rebase failed after commit. Check ${RUN_LOG}"
  exit 1
fi

if ! git push >>"${RUN_LOG}" 2>&1; then
  log "[ERROR] Push failed. Check ${RUN_LOG}"
  exit 1
fi

log "[OK] Updates pushed successfully."
exit "${overall_rc}"
