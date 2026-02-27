#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NWS_ROOT="${REPO_ROOT}/_sandbox/nws_ensemble_point"
EXTRACTOR="${REPO_ROOT}/_sandbox/nws_ensemble_point/nwx_extract.py"
CONFIG="${REPO_ROOT}/_sandbox/nws_ensemble_point/config.yaml"
REQUIREMENTS="${REPO_ROOT}/_sandbox/nws_ensemble_point/requirements.txt"
API_BUILDER="${REPO_ROOT}/scripts/build_big_trees_forecast_json.py"
SANDBOX_JSON="${REPO_ROOT}/data/_sandbox_nws/big_trees_latest.json"
ASSETS_JSON="${REPO_ROOT}/assets/data/forecasts/big_trees_latest.json"
VENV_ACTIVATE="${REPO_ROOT}/_sandbox/nws_ensemble_point/.venv/bin/activate"
MAX_SANDBOX_AGE_SEC=21600

INSTALL_DEPS="${BIG_TREES_FORECAST_INSTALL_DEPS:-0}"
ALLOW_STALE_ON_ERROR="${BIG_TREES_FORECAST_ALLOW_STALE_ON_ERROR:-${BIG_TREES_FORECAST_ALLOW_STALE_ON_MISSING_PIPELINE:-0}}"

log_info() { echo "[INFO] $*"; }
log_warn() { echo "[WARN] $*" >&2; }
log_error() { echo "[ERROR] $*" >&2; }

gh_warn() {
  local message="$*"
  if [[ -n "${GITHUB_ACTIONS:-}" ]]; then
    echo "::warning::${message}"
  else
    log_warn "${message}"
  fi
}

cd "${REPO_ROOT}"

if command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
else
  log_error "Python interpreter not found on PATH (checked: python, python3)."
  exit 3
fi

keep_stale_and_exit() {
  local reason="$1"
  if [[ "${ALLOW_STALE_ON_ERROR}" == "1" ]] && [[ -f "${ASSETS_JSON}" ]]; then
    gh_warn "${reason}"
    gh_warn "Keeping tracked asset without update: ${ASSETS_JSON}"
    "${PYTHON_BIN}" - <<'PY'
import json
from pathlib import Path
path = Path("assets/data/forecasts/big_trees_latest.json")
data = json.loads(path.read_text(encoding="utf-8"))
print("[INFO] using existing tracked asset:", path)
print("[INFO] existing generated_at_utc:", data.get("generated_at_utc"))
PY
    exit 0
  fi

  log_error "${reason}"
  log_error "To allow stale-asset fallback, set BIG_TREES_FORECAST_ALLOW_STALE_ON_ERROR=1."
  exit 2
}

legacy_ready=1
for required in "${NWS_ROOT}" "${EXTRACTOR}" "${CONFIG}" "${REQUIREMENTS}"; do
  if [[ ! -e "${required}" ]]; then
    legacy_ready=0
    break
  fi
done

run_legacy_pipeline() {
  if [[ -f "${VENV_ACTIVATE}" ]]; then
    # shellcheck disable=SC1090
    source "${VENV_ACTIVATE}"
  fi

  if [[ "${INSTALL_DEPS}" == "1" ]]; then
    log_info "Installing dependencies from ${REQUIREMENTS}"
    "${PYTHON_BIN}" -m pip install --upgrade pip
    "${PYTHON_BIN}" -m pip install -r "${REQUIREMENTS}"
  fi

  if ! "${PYTHON_BIN}" - <<'PY' 2>/dev/null
import pandas, numpy, yaml, requests  # noqa: F401
PY
  then
    return 1
  fi

  local run_extractor=1
  if [[ -f "${SANDBOX_JSON}" ]]; then
    local now_ts file_ts age_sec
    now_ts=$(date +%s)
    file_ts=$(stat -c %Y "${SANDBOX_JSON}")
    age_sec=$((now_ts - file_ts))
    if [[ ${age_sec} -lt ${MAX_SANDBOX_AGE_SEC} ]]; then
      log_info "Recent sandbox artifact found (${age_sec}s old); skipping legacy extractor run."
      run_extractor=0
    fi
  fi

  if [[ ${run_extractor} -eq 1 ]]; then
    set +e
    local output status
    output=$("${PYTHON_BIN}" "${EXTRACTOR}" --config "${CONFIG}" --latest --profile web --export-web 2>&1)
    status=$?
    set -e

    if [[ ${status} -ne 0 ]]; then
      if command -v rg >/dev/null 2>&1; then
        CHECK_CMD=(rg -q "unrecognized arguments: --profile")
      else
        CHECK_CMD=(grep -q "unrecognized arguments: --profile")
      fi
      if echo "${output}" | "${CHECK_CMD[@]}"; then
        log_warn "Profile flag not supported; falling back to --latest --export-web."
        "${PYTHON_BIN}" "${EXTRACTOR}" --config "${CONFIG}" --latest --export-web
      else
        echo "${output}" >&2
        return ${status}
      fi
    fi
  fi
  return 0
}

run_api_builder() {
  if [[ ! -f "${API_BUILDER}" ]]; then
    return 4
  fi

  mkdir -p "$(dirname "${SANDBOX_JSON}")"
  "${PYTHON_BIN}" "${API_BUILDER}" \
    --gauge-id "BTEC1" \
    --reach-id "17682474" \
    --output "${SANDBOX_JSON}"
}

if [[ "${legacy_ready}" == "1" ]]; then
  log_info "Using legacy _sandbox/nws_ensemble_point extractor."
  if ! run_legacy_pipeline; then
    keep_stale_and_exit "Legacy extractor failed."
  fi
else
  log_warn "Legacy _sandbox/nws_ensemble_point extractor not found; using API builder fallback."
  if ! run_api_builder; then
    keep_stale_and_exit "API builder failed to produce Big Trees forecast JSON."
  fi
fi

if [[ ! -f "${SANDBOX_JSON}" ]]; then
  keep_stale_and_exit "Expected export not found: ${SANDBOX_JSON}"
fi

mkdir -p "$(dirname "${ASSETS_JSON}")"
cp "${SANDBOX_JSON}" "${ASSETS_JSON}"

"${PYTHON_BIN}" - <<'PY'
import json
from pathlib import Path

path = Path("assets/data/forecasts/big_trees_latest.json")
data = json.loads(path.read_text(encoding="utf-8"))
print("Forecast file:", path)
print("generated_at_utc:", data.get("generated_at_utc"))
for range_name, payload in (data.get("ranges") or {}).items():
    if "deterministic" in payload:
        series = payload["deterministic"]
        if series:
            print(f"{range_name}: deterministic points={len(series)} start={series[0]['t']} end={series[-1]['t']}")
    else:
        p50 = payload.get("p50") or []
        if p50:
            print(f"{range_name}: p50 points={len(p50)} start={p50[0]['t']} end={p50[-1]['t']}")
PY
