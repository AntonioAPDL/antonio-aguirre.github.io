#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXTRACTOR="${REPO_ROOT}/_sandbox/nws_ensemble_point/nwx_extract.py"
CONFIG="${REPO_ROOT}/_sandbox/nws_ensemble_point/config.yaml"
SANDBOX_JSON="${REPO_ROOT}/data/_sandbox_nws/big_trees_latest.json"
ASSETS_JSON="${REPO_ROOT}/assets/data/forecasts/big_trees_latest.json"
VENV_ACTIVATE="${REPO_ROOT}/_sandbox/nws_ensemble_point/.venv/bin/activate"

if [[ ! -f "${EXTRACTOR}" ]]; then
  echo "Extractor not found at ${EXTRACTOR}" >&2
  exit 1
fi

if [[ -f "${VENV_ACTIVATE}" ]]; then
  # shellcheck disable=SC1090
  source "${VENV_ACTIVATE}"
fi

if ! python - <<'PY' 2>/dev/null
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
  if [[ $AGE_SEC -lt 21600 ]]; then
    RUN_EXTRACTOR=0
  fi
fi

if [[ $RUN_EXTRACTOR -eq 1 ]]; then
  set +e
  OUTPUT=$(python "${EXTRACTOR}" --config "${CONFIG}" --latest --profile web --export-web 2>&1)
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
      python "${EXTRACTOR}" --config "${CONFIG}" --latest --export-web
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

python - <<'PY'
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
