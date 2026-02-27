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
OBS_WINDOW_DAYS="${OBS_WINDOW_DAYS:-20}"
ANALYSIS_HISTORY_MAX_COMMITS="${ANALYSIS_HISTORY_MAX_COMMITS:-240}"

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
python "${EXPORTER}" \
  --gefs-config "${CFG}" \
  --observation-window-days "${OBS_WINDOW_DAYS}" \
  --analysis-history-max-commits "${ANALYSIS_HISTORY_MAX_COMMITS}"

if [[ ! -f "${WEB_JSON}" ]]; then
  echo "Expected web export not found: ${WEB_JSON}" >&2
  exit 1
fi

mkdir -p "$(dirname "${ASSET_JSON}")"
cp "${WEB_JSON}" "${ASSET_JSON}"

python - <<'PY'
import json
from datetime import datetime, timedelta, timezone
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
print("observed_retrospective_enabled:", bool(obs))

def parse_iso(value):
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except Exception:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)

def series_bounds(series, start, end):
    rows = []
    if not isinstance(series, list):
        return 0, None, None
    for point in series:
        if not isinstance(point, dict):
            continue
        ts = parse_iso(point.get("t"))
        if ts is None:
            continue
        if not (start <= ts < end):
            continue
        rows.append(ts)
    if not rows:
        return 0, None, None
    rows.sort()
    return len(rows), rows[0], rows[-1]

def best_series(block):
    if not isinstance(block, dict):
        return []
    best = []
    for candidate in block.values():
        if isinstance(candidate, list) and len(candidate) > len(best):
            best = candidate
    return best

errors = []
window_days = int(data.get("observation_window_days") or 0)
if window_days < 20:
    errors.append(f"observation_window_days={window_days} (expected >= 20)")

init_time = parse_iso(data.get("init_time_utc"))
if init_time is None:
    errors.append("missing/invalid init_time_utc")
else:
    now_utc = datetime.now(timezone.utc)
    init_age_h = (now_utc - init_time).total_seconds() / 3600.0
    print("init_age_hours:", f"{init_age_h:.2f}")
    if init_age_h > 30:
        errors.append(f"init_time_utc is too old ({init_age_h:.1f}h)")

    start = init_time - timedelta(days=max(1, window_days))
    precip_end = init_time + timedelta(hours=3, minutes=1)
    soil_end = init_time + timedelta(minutes=1)

    context = data.get("gefs_analysis_context") or {}
    precip_series = best_series((context.get("precip_f003_proxy") or {}))
    soil_series = best_series((context.get("soil_f000") or {}))

    min_expected = max(8, int(round(max(1, window_days) * 4 * 0.75)))
    p_count, p_first, p_last = series_bounds(precip_series, start, precip_end)
    s_count, s_first, s_last = series_bounds(soil_series, start, soil_end)
    print("analysis_precip_points_window:", p_count)
    print("analysis_soil_points_window:", s_count)
    print("analysis_min_expected_points:", min_expected)
    print("analysis_precip_first_last:", p_first.isoformat() if p_first else None, p_last.isoformat() if p_last else None)
    print("analysis_soil_first_last:", s_first.isoformat() if s_first else None, s_last.isoformat() if s_last else None)

    edge_tol = timedelta(hours=9)
    if p_count < min_expected:
        errors.append(f"precip analysis coverage too sparse ({p_count} < {min_expected})")
    if s_count < min_expected:
        errors.append(f"soil analysis coverage too sparse ({s_count} < {min_expected})")
    if p_first is None or p_first > (start + edge_tol):
        errors.append("precip analysis does not cover start of retrospective window")
    if s_first is None or s_first > (start + edge_tol):
        errors.append("soil analysis does not cover start of retrospective window")
    if p_last is None or p_last < (precip_end - edge_tol):
        errors.append("precip analysis does not include recent cycle context")
    if s_last is None or s_last < (soil_end - edge_tol):
        errors.append("soil analysis does not include recent cycle context")

if errors:
    print("validation_status=failed")
    for err in errors:
        print("validation_error:", err)
    raise SystemExit(1)
print("validation_status=ok")
PY
