#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NWS_ROOT="${REPO_ROOT}/_sandbox/nws_ensemble_point"
EXTRACTOR="${REPO_ROOT}/_sandbox/nws_ensemble_point/nwx_extract.py"
CONFIG="${REPO_ROOT}/_sandbox/nws_ensemble_point/config.yaml"
REQUIREMENTS="${REPO_ROOT}/_sandbox/nws_ensemble_point/requirements.txt"
SANDBOX_JSON="${REPO_ROOT}/data/_sandbox_nws/big_trees_latest.json"
ASSETS_JSON="${REPO_ROOT}/assets/data/forecasts/big_trees_latest.json"
VENV_ACTIVATE="${REPO_ROOT}/_sandbox/nws_ensemble_point/.venv/bin/activate"
MAX_SANDBOX_AGE_SEC=21600

INSTALL_DEPS="${BIG_TREES_FORECAST_INSTALL_DEPS:-0}"
ALLOW_STALE_ON_MISSING_PIPELINE="${BIG_TREES_FORECAST_ALLOW_STALE_ON_MISSING_PIPELINE:-0}"

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

missing_paths=()
for required in "${NWS_ROOT}" "${EXTRACTOR}" "${CONFIG}" "${REQUIREMENTS}"; do
  if [[ ! -e "${required}" ]]; then
    missing_paths+=("${required}")
  fi
done

if (( ${#missing_paths[@]} > 0 )); then
  if [[ "${ALLOW_STALE_ON_MISSING_PIPELINE}" == "1" ]] && [[ -f "${ASSETS_JSON}" ]]; then
    gh_warn "NWS ensemble pipeline is incomplete in this repository clone."
    for path in "${missing_paths[@]}"; do
      gh_warn "Missing required path: ${path}"
    done
    gh_warn "Skipping Big Trees forecast extraction; pipeline files are missing. Keeping tracked asset: ${ASSETS_JSON}"
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

  log_error "NWS ensemble pipeline is incomplete in this repository clone."
  for path in "${missing_paths[@]}"; do
    log_error "Missing required path: ${path}"
  done
  log_error "Failing fast. To allow stale-asset fallback, set BIG_TREES_FORECAST_ALLOW_STALE_ON_MISSING_PIPELINE=1."
  exit 2
fi

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
  echo "Missing Python dependencies for the extractor. Activate the sandbox venv and install requirements:" >&2
  echo "  cd _sandbox/nws_ensemble_point && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt" >&2
  exit 1
fi

RUN_EXTRACTOR=1
if [[ -f "${SANDBOX_JSON}" ]]; then
  NOW_TS=$(date +%s)
  FILE_TS=$(stat -c %Y "${SANDBOX_JSON}")
  AGE_SEC=$((NOW_TS - FILE_TS))
  if [[ $AGE_SEC -lt ${MAX_SANDBOX_AGE_SEC} ]]; then
    log_info "Recent sandbox artifact found (${AGE_SEC}s old); skipping extractor run."
    RUN_EXTRACTOR=0
  fi
fi

if [[ $RUN_EXTRACTOR -eq 1 ]]; then
  set +e
  OUTPUT=$("${PYTHON_BIN}" "${EXTRACTOR}" --config "${CONFIG}" --latest --profile web --export-web 2>&1)
  STATUS=$?
  set -e

  if [[ $STATUS -ne 0 ]]; then
    if command -v rg >/dev/null 2>&1; then
      CHECK_CMD=(rg -q "unrecognized arguments: --profile")
    else
      CHECK_CMD=(grep -q "unrecognized arguments: --profile")
    fi
    if echo "${OUTPUT}" | "${CHECK_CMD[@]}"; then
      echo "Profile flag not supported; falling back to --latest --export-web." >&2
      "${PYTHON_BIN}" "${EXTRACTOR}" --config "${CONFIG}" --latest --export-web
    else
      echo "${OUTPUT}" >&2
      exit $STATUS
    fi
  fi
fi

if [[ ! -f "${SANDBOX_JSON}" ]]; then
  echo "Expected export not found: ${SANDBOX_JSON}" >&2
  exit 1
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
