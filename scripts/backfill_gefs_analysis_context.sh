#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIPELINE_DIR="${REPO_ROOT}/_sandbox/gefs_point_pipeline"
FULL_CFG="${PIPELINE_DIR}/config/gefs.yaml"
ASSET_JSON="${REPO_ROOT}/assets/data/forecasts/gefs_big_trees_latest.json"
WINDOW_DAYS="${WINDOW_DAYS:-20}"
MAX_CYCLES="${MAX_CYCLES:-160}"
STRICT_MODE="${STRICT_MODE:-1}"
START_CYCLE_UTC="${START_CYCLE_UTC:-}"
END_CYCLE_UTC="${END_CYCLE_UTC:-}"
VENV_ACTIVATE="${PIPELINE_DIR}/.venv/bin/activate"

if [[ ! -f "${FULL_CFG}" ]]; then
  echo "[ERROR] Missing GEFS config: ${FULL_CFG}" >&2
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
  echo "[ERROR] Missing Python dependencies for GEFS pipeline." >&2
  exit 1
fi

TMP_CFG="$(mktemp)"
trap 'rm -f "${TMP_CFG}"' EXIT

python - "${FULL_CFG}" "${TMP_CFG}" <<'PY'
from pathlib import Path
import sys
import yaml

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
cfg = yaml.safe_load(src.read_text(encoding="utf-8"))
cfg["lead_hours"] = {"start": 0, "end": 3, "step": 3}
cfg["runtime"]["keep_cycles"] = 1
cfg["runtime"]["max_workers"] = min(int(cfg["runtime"].get("max_workers", 8)), 8)
dst.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
PY

echo "[INFO] Backfill config created: ${TMP_CFG}"
echo "[INFO] window_days=${WINDOW_DAYS} max_cycles=${MAX_CYCLES} strict_mode=${STRICT_MODE}"

readarray -t CYCLES < <(
  python - "${WINDOW_DAYS}" "${MAX_CYCLES}" "${START_CYCLE_UTC}" "${END_CYCLE_UTC}" <<'PY'
import datetime as dt
import sys

window_days = max(1, int(sys.argv[1]))
max_cycles = max(1, int(sys.argv[2]))
start_arg = sys.argv[3].strip()
end_arg = sys.argv[4].strip()

def parse_iso(value: str) -> dt.datetime:
    out = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if out.tzinfo is None:
        out = out.replace(tzinfo=dt.timezone.utc)
    return out.astimezone(dt.timezone.utc)

def floor_to_6h(value: dt.datetime) -> dt.datetime:
    value = value.astimezone(dt.timezone.utc)
    return value.replace(minute=0, second=0, microsecond=0, hour=(value.hour // 6) * 6)

if end_arg:
    end_cycle = floor_to_6h(parse_iso(end_arg))
else:
    now_utc = dt.datetime.now(dt.timezone.utc)
    end_cycle = floor_to_6h(now_utc - dt.timedelta(hours=6))

if start_arg:
    start_cycle = floor_to_6h(parse_iso(start_arg))
else:
    start_cycle = floor_to_6h(end_cycle - dt.timedelta(days=window_days))

if start_cycle > end_cycle:
    start_cycle, end_cycle = end_cycle, start_cycle

cursor = start_cycle
steps = []
while cursor <= end_cycle:
    steps.append(cursor)
    cursor += dt.timedelta(hours=6)

if len(steps) > max_cycles:
    steps = steps[-max_cycles:]

for value in steps:
    print(value.isoformat())
PY
)

if [[ "${#CYCLES[@]}" -eq 0 ]]; then
  echo "[ERROR] No cycles selected for backfill." >&2
  exit 1
fi

echo "[INFO] Selected cycles: ${#CYCLES[@]}"
echo "[INFO] First cycle: ${CYCLES[0]}"
echo "[INFO] Last cycle: ${CYCLES[-1]}"

attempted=0
succeeded=0
failed=0

for init_time in "${CYCLES[@]}"; do
  attempted=$((attempted + 1))
  run_tag="$(python - "${init_time}" <<'PY'
import datetime as dt
import sys
value = dt.datetime.fromisoformat(sys.argv[1].replace("Z", "+00:00"))
if value.tzinfo is None:
    value = value.replace(tzinfo=dt.timezone.utc)
value = value.astimezone(dt.timezone.utc)
print(value.strftime("%Y%m%d_%H"))
PY
)"
  echo "[INFO] Backfilling cycle ${init_time} (run_tag=${run_tag})"
  if ! python "${PIPELINE_DIR}/run_latest.py" \
    --gefs-config "${TMP_CFG}" \
    --profile full \
    --init-time "${init_time}" \
    --force \
    --log-level WARNING; then
    failed=$((failed + 1))
    echo "[WARN] Cycle failed during run_latest: ${init_time}" >&2
    continue
  fi
  if ! python "${PIPELINE_DIR}/export_latest_web_json.py" \
    --gefs-config "${TMP_CFG}" \
    --run-tag "${run_tag}" \
    --prior-web-json "${ASSET_JSON}" \
    --out "${ASSET_JSON}" \
    --observation-window-days "${WINDOW_DAYS}"; then
    failed=$((failed + 1))
    echo "[WARN] Cycle failed during export: ${init_time}" >&2
    continue
  fi
  succeeded=$((succeeded + 1))
done

echo "[INFO] Backfill sweep summary: attempted=${attempted} succeeded=${succeeded} failed=${failed}"

echo "[INFO] Rebuilding latest full GEFS payload after context backfill..."
"${REPO_ROOT}/scripts/update_big_trees_gefs_forecast.sh"

python - "${ASSET_JSON}" "${WINDOW_DAYS}" "${STRICT_MODE}" <<'PY'
import json
from pathlib import Path
import sys

asset = Path(sys.argv[1])
window_days = max(1, int(sys.argv[2]))
strict_mode = int(sys.argv[3]) > 0

data = json.loads(asset.read_text(encoding="utf-8"))
context = data.get("gefs_analysis_context", {})
if not isinstance(context, dict):
    raise SystemExit("gefs_analysis_context block missing after backfill.")

precip = context.get("precip_f003_proxy", {})
soil = context.get("soil_f000", {})
if not isinstance(precip, dict) or not isinstance(soil, dict):
    raise SystemExit("Invalid analysis context structure.")

precip_points = sum(len(v) for v in precip.values() if isinstance(v, list))
soil_points = sum(len(v) for v in soil.values() if isinstance(v, list))
first_soil_level = next((v for v in soil.values() if isinstance(v, list)), [])
soil_per_level = len(first_soil_level)

target_cycles = window_days * 4
print(f"[INFO] analysis_context_precip_points={precip_points}")
print(f"[INFO] analysis_context_soil_points={soil_points}")
print(f"[INFO] analysis_context_soil_per_level={soil_per_level}")
print(f"[INFO] target_cycles={target_cycles}")

if strict_mode:
    if precip_points < target_cycles:
        raise SystemExit(
            f"Strict check failed: precipitation context points={precip_points} < expected={target_cycles}"
        )
    if soil_per_level < target_cycles:
        raise SystemExit(
            f"Strict check failed: soil context points per level={soil_per_level} < expected={target_cycles}"
        )
PY

echo "[OK] GEFS analysis backfill complete."
