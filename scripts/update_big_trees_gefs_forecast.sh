#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIPELINE_DIR="${REPO_ROOT}/_sandbox/gefs_point_pipeline"
RUNNER="${PIPELINE_DIR}/run_latest.py"
EXPORTER="${PIPELINE_DIR}/export_latest_web_json.py"
CFG="${PIPELINE_DIR}/config/gefs.yaml"
VENV_ACTIVATE="${PIPELINE_DIR}/.venv/bin/activate"
WEB_JSON="${REPO_ROOT}/data/_sandbox_gefs/web/gefs_big_trees_latest.json"
ASSET_JSON="${REPO_ROOT}/assets/data/forecasts/gefs_big_trees_latest.json"

cd "${REPO_ROOT}"

if [[ ! -f "${RUNNER}" ]]; then
  echo "Runner not found at ${RUNNER}" >&2
  exit 1
fi

if [[ ! -f "${EXPORTER}" ]]; then
  echo "Exporter not found at ${EXPORTER}" >&2
  exit 1
fi

if [[ -f "${VENV_ACTIVATE}" ]]; then
  # shellcheck disable=SC1090
  source "${VENV_ACTIVATE}"
fi

if ! python - <<'PY' 2>/dev/null
import pandas, numpy, yaml, xarray, herbie, cfgrib  # noqa: F401
PY
then
  echo "Missing Python dependencies for GEFS pipeline." >&2
  echo "Install with:" >&2
  echo "  cd _sandbox/gefs_point_pipeline && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt" >&2
  exit 1
fi

python "${RUNNER}" --gefs-config "${CFG}" --profile full --log-level INFO
python "${EXPORTER}" --gefs-config "${CFG}"

if [[ ! -f "${WEB_JSON}" ]]; then
  echo "Expected web export not found: ${WEB_JSON}" >&2
  exit 1
fi

mkdir -p "$(dirname "${ASSET_JSON}")"
cp "${WEB_JSON}" "${ASSET_JSON}"

python - <<'PY'
import json
from pathlib import Path

path = Path("assets/data/forecasts/gefs_big_trees_latest.json")
data = json.loads(path.read_text(encoding="utf-8"))
print("GEFS file:", path)
print("generated_at_utc:", data.get("generated_at_utc"))
print("init_time_utc:", data.get("init_time_utc"))
print("member_count:", data.get("member_count"))
print("missing_levels:", data.get("missing_levels"))
print("precip_levels:", list((data.get("precip") or {}).keys()))
print("soil_levels:", list((data.get("soil_moisture") or {}).keys()))
retro = data.get("retrospective") or {}
print("observation_window_days:", data.get("observation_window_days"))
print("retrospective_start_utc:", retro.get("start_utc"))
print("retrospective_end_utc:", retro.get("end_utc"))
print("retrospective_precip_levels:", list((retro.get("precip") or {}).keys()))
print("retrospective_soil_levels:", list((retro.get("soil_moisture") or {}).keys()))
obs = data.get("observed_retrospective") or {}
print("observed_retrospective_start_utc:", obs.get("start_utc"))
print("observed_retrospective_end_utc:", obs.get("end_utc"))
print("observed_ppt_points:", len(obs.get("daily_avg_ppt") or []))
print("observed_soil_era5_points:", len(obs.get("daily_avg_soil_ERA5") or []))
print("observed_soil_nwm_m_points:", len(obs.get("daily_avg_soil_NWM_SOIL_M") or []))
print("observed_soil_nwm_w_points:", len(obs.get("daily_avg_soil_NWM_SOIL_W") or []))
PY
