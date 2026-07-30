#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NWS_ROOT="${REPO_ROOT}/_sandbox/nws_ensemble_point"
EXTRACTOR="${REPO_ROOT}/_sandbox/nws_ensemble_point/nwx_extract.py"
CONFIG="${REPO_ROOT}/_sandbox/nws_ensemble_point/config.yaml"
REQUIREMENTS="${REPO_ROOT}/_sandbox/nws_ensemble_point/requirements.txt"
API_BUILDER="${REPO_ROOT}/scripts/build_big_trees_forecast_json.py"
SANDBOX_JSON="${REPO_ROOT}/data/_sandbox_nws/big_trees_latest.json"
ASSET_REL="assets/data/forecasts/big_trees_latest.json"
ASSETS_JSON="${REPO_ROOT}/${ASSET_REL}"
PREVIOUS_LIVE_JSON="${REPO_ROOT}/data/_sandbox_nws/big_trees_latest.previous_live.json"
PREVIOUS_LIVE_COMMIT_FILE="${PREVIOUS_LIVE_JSON}.commit"
VENV_ACTIVATE="${REPO_ROOT}/_sandbox/nws_ensemble_point/.venv/bin/activate"
MAX_SANDBOX_AGE_SEC=21600

INSTALL_DEPS="${BIG_TREES_FORECAST_INSTALL_DEPS:-0}"
ALLOW_STALE_ON_ERROR="${BIG_TREES_FORECAST_ALLOW_STALE_ON_ERROR:-${BIG_TREES_FORECAST_ALLOW_STALE_ON_MISSING_PIPELINE:-0}}"
REQUIRE_EXTENDED_RANGES="${BIG_TREES_FORECAST_REQUIRE_EXTENDED_RANGES:-1}"
BASELINE_MAX_COMMITS="${BIG_TREES_FORECAST_BASELINE_MAX_COMMITS:-36}"
API_TIMEOUT_SEC="${BIG_TREES_FORECAST_TIMEOUT_SEC:-30}"
API_RETRIES="${BIG_TREES_FORECAST_RETRIES:-4}"

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

payload_has_extended_ranges() {
  local path="$1"
  [[ -f "${path}" ]] || return 1
  STREAMFLOW_VALIDATE_PATH="${path}" "${PYTHON_BIN}" - <<'PY' >/dev/null
import json
import os
from pathlib import Path

path = Path(os.environ["STREAMFLOW_VALIDATE_PATH"])
data = json.loads(path.read_text(encoding="utf-8"))
ranges = data.get("ranges") or {}

def count(name):
    block = ranges.get(name) or {}
    if not isinstance(block, dict):
        return 0
    series = block.get("p50") or []
    return len(series) if isinstance(series, list) else 0

raise SystemExit(0 if count("medium_range") > 0 and count("long_range") > 0 else 1)
PY
}

print_streamflow_asset_metadata() {
  local path="$1"
  STREAMFLOW_ASSET_PATH="${path}" "${PYTHON_BIN}" - <<'PY'
import json
import os
from pathlib import Path

path = Path(os.environ["STREAMFLOW_ASSET_PATH"])
try:
    data = json.loads(path.read_text(encoding="utf-8"))
except Exception as exc:
    print("[WARN] streamflow asset is not valid JSON:", path, exc)
    raise SystemExit(0)

print("[INFO] using streamflow asset:", path)
print("[INFO] generated_at_utc:", data.get("generated_at_utc"))
print("[INFO] init_times:", data.get("init_times"))
for name, payload in (data.get("ranges") or {}).items():
    if not isinstance(payload, dict):
        continue
    if "deterministic" in payload:
        series = payload.get("deterministic") or []
        if series:
            print(f"[INFO] {name}: deterministic points={len(series)} start={series[0].get('t')} end={series[-1].get('t')}")
    else:
        p50 = payload.get("p50") or []
        if p50:
            print(f"[INFO] {name}: p50 points={len(p50)} start={p50[0].get('t')} end={p50[-1].get('t')}")
        else:
            print(f"[INFO] {name}: p50 points=0")
PY
}

load_previous_live_baseline() {
  rm -f "${PREVIOUS_LIVE_JSON}" "${PREVIOUS_LIVE_JSON}.candidate" "${PREVIOUS_LIVE_COMMIT_FILE}"

  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    return 0
  fi

  if ! git ls-remote --exit-code --heads origin live-data >/dev/null 2>&1; then
    return 0
  fi

  if ! git fetch --quiet origin +live-data:refs/remotes/origin/live-data; then
    gh_warn "Could not fetch origin/live-data for streamflow stale fallback."
    return 0
  fi

  local commits=()
  mapfile -t commits < <(git log -n "${BASELINE_MAX_COMMITS}" --format=%H origin/live-data -- "${ASSET_REL}" 2>/dev/null || true)
  for commit in "${commits[@]}"; do
    if git show "${commit}:${ASSET_REL}" > "${PREVIOUS_LIVE_JSON}.candidate" 2>/dev/null \
      && payload_has_extended_ranges "${PREVIOUS_LIVE_JSON}.candidate"; then
      mv "${PREVIOUS_LIVE_JSON}.candidate" "${PREVIOUS_LIVE_JSON}"
      printf '%s\n' "${commit}" > "${PREVIOUS_LIVE_COMMIT_FILE}"
      log_info "Loaded previous complete streamflow live-data baseline from ${commit}."
      return 0
    fi
  done

  rm -f "${PREVIOUS_LIVE_JSON}.candidate"
}

validate_streamflow_export() {
  local path="$1"
  if [[ "${REQUIRE_EXTENDED_RANGES}" != "1" ]]; then
    return 0
  fi

  STREAMFLOW_VALIDATE_PATH="${path}" "${PYTHON_BIN}" - <<'PY'
import json
import os
from pathlib import Path

path = Path(os.environ["STREAMFLOW_VALIDATE_PATH"])
data = json.loads(path.read_text(encoding="utf-8"))
ranges = data.get("ranges") or {}

def p50_count(name):
    block = ranges.get(name) or {}
    if not isinstance(block, dict):
        return 0
    series = block.get("p50") or []
    return len(series) if isinstance(series, list) else 0

medium_n = p50_count("medium_range")
long_n = p50_count("long_range")
print(f"[INFO] streamflow validation: medium_p50={medium_n} long_p50={long_n}")
if medium_n <= 0 or long_n <= 0:
    print("[WARN] streamflow validation failed: medium and long-range guidance are required for publishing.")
    raise SystemExit(1)
print("[INFO] streamflow validation_status=ok")
PY
}

cd "${REPO_ROOT}"

if [[ -n "${PYTHON_BIN:-}" ]]; then
  :
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  log_error "Python interpreter not found on PATH (checked: python3, python)."
  exit 3
fi

if ! "${PYTHON_BIN}" - <<'PY' >/dev/null 2>&1
import sys

raise SystemExit(0 if sys.version_info >= (3, 8) else 1)
PY
then
  log_error "Big Trees forecast updater requires Python 3.8+ (selected: ${PYTHON_BIN})."
  exit 3
fi

load_previous_live_baseline

keep_stale_and_exit() {
  local reason="$1"
  if [[ "${ALLOW_STALE_ON_ERROR}" == "1" ]] && [[ -f "${PREVIOUS_LIVE_JSON}" ]]; then
    gh_warn "${reason}"
    mkdir -p "$(dirname "${ASSETS_JSON}")"
    cp "${PREVIOUS_LIVE_JSON}" "${ASSETS_JSON}"
    local baseline_commit="unknown"
    if [[ -f "${PREVIOUS_LIVE_COMMIT_FILE}" ]]; then
      baseline_commit="$(cat "${PREVIOUS_LIVE_COMMIT_FILE}")"
    fi
    gh_warn "Restored previous complete live-data streamflow asset from ${baseline_commit}."
    print_streamflow_asset_metadata "${ASSETS_JSON}"
    exit 0
  fi

  if [[ "${ALLOW_STALE_ON_ERROR}" == "1" ]] && [[ -f "${ASSETS_JSON}" ]]; then
    gh_warn "${reason}"
    gh_warn "Keeping tracked asset without update: ${ASSETS_JSON}"
    print_streamflow_asset_metadata "${ASSETS_JSON}"
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
    --timeout-sec "${API_TIMEOUT_SEC}" \
    --retries "${API_RETRIES}" \
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

if ! validate_streamflow_export "${SANDBOX_JSON}"; then
  keep_stale_and_exit "Big Trees streamflow update produced incomplete medium/long-range guidance."
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
