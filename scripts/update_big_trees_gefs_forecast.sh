#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIPELINE_DIR="${REPO_ROOT}/_sandbox/gefs_point_pipeline"
RUNNER="${PIPELINE_DIR}/run_latest.py"
EXPORTER="${PIPELINE_DIR}/export_latest_web_json.py"
CFG="${PIPELINE_DIR}/config/gefs.yaml"
VENV_ACTIVATE="${PIPELINE_DIR}/.venv/bin/activate"
WEB_JSON="${REPO_ROOT}/data/_sandbox_gefs/web/gefs_big_trees_latest.json"
ASSET_REL="assets/data/forecasts/gefs_big_trees_latest.json"
ASSET_JSON="${REPO_ROOT}/${ASSET_REL}"
PREVIOUS_LIVE_JSON="${REPO_ROOT}/data/_sandbox_gefs/web/gefs_big_trees_latest.previous_live.json"
LIVE_CLIMATE_REL="climate_daily_ppt_soil.csv"
LIVE_CLIMATE_CSV="${REPO_ROOT}/data/_sandbox_gefs/web/climate_daily_ppt_soil.live_data.csv"
OBS_WINDOW_DAYS="${OBS_WINDOW_DAYS:-20}"
ANALYSIS_HISTORY_MAX_COMMITS="${ANALYSIS_HISTORY_MAX_COMMITS:-240}"
ALLOW_STALE_ON_ERROR="${GEFS_FORECAST_ALLOW_STALE_ON_ERROR:-0}"
STALE_FALLBACK_IS_FAILURE="${GEFS_FORECAST_STALE_FALLBACK_IS_FAILURE:-1}"
INCLUDE_OBSERVED_RETROSPECTIVE="${GEFS_FORECAST_INCLUDE_OBSERVED_RETROSPECTIVE:-1}"
OBSERVED_RETROSPECTIVE_CSV="${GEFS_OBSERVED_RETROSPECTIVE_CSV:-}"

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

load_previous_live_asset() {
  mkdir -p "$(dirname "${PREVIOUS_LIVE_JSON}")"
  rm -f "${PREVIOUS_LIVE_JSON}"
  rm -f "${LIVE_CLIMATE_CSV}"

  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    return 0
  fi

  if ! git ls-remote --exit-code --heads origin live-data >/dev/null 2>&1; then
    return 0
  fi

  if ! git fetch --quiet origin +live-data:refs/remotes/origin/live-data; then
    gh_warn "Could not fetch origin/live-data for GEFS stale fallback."
    return 0
  fi

  if git show "origin/live-data:${ASSET_REL}" > "${PREVIOUS_LIVE_JSON}" 2>/dev/null; then
    mkdir -p "$(dirname "${ASSET_JSON}")"
    cp "${PREVIOUS_LIVE_JSON}" "${ASSET_JSON}"
    echo "[INFO] Loaded GEFS live-data baseline from origin/live-data."
  else
    rm -f "${PREVIOUS_LIVE_JSON}"
  fi

  if git show "origin/live-data:${LIVE_CLIMATE_REL}" > "${LIVE_CLIMATE_CSV}" 2>/dev/null; then
    echo "[INFO] Loaded climate live-data baseline for observed GEFS context."
  else
    rm -f "${LIVE_CLIMATE_CSV}"
  fi
}

print_asset_metadata() {
  python - <<'PY'
import json
from pathlib import Path

path = Path("assets/data/forecasts/gefs_big_trees_latest.json")
if not path.exists():
    print("[WARN] existing asset is missing:", path)
    raise SystemExit(0)
try:
    data = json.loads(path.read_text(encoding="utf-8"))
except Exception as exc:
    print("[WARN] existing asset is not valid JSON:", path, exc)
    raise SystemExit(0)
print("[INFO] using existing GEFS asset:", path)
print("[INFO] generated_at_utc:", data.get("generated_at_utc"))
print("[INFO] init_time_utc:", data.get("init_time_utc"))
print("[INFO] member_count:", data.get("member_count"))
PY
}

choose_observed_retrospective_csv() {
  local live_csv="${LIVE_CLIMATE_CSV}"
  local tracked_csv="${REPO_ROOT}/climate_daily_ppt_soil.csv"
  python - "${live_csv}" "${tracked_csv}" <<'PY'
import sys
from pathlib import Path

import pandas as pd

columns = [
    "daily_avg_ppt",
    "daily_avg_soil_ERA5",
    "daily_avg_soil_NWM_SOIL_M",
    "daily_avg_soil_NWM_SOIL_W",
]

best = None
for raw in sys.argv[1:]:
    path = Path(raw)
    if not path.exists():
        continue
    try:
        df = pd.read_csv(path)
    except Exception:
        continue
    if "timestamp" not in df.columns:
        continue
    ts = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    available_cols = [col for col in columns if col in df.columns]
    if not available_cols:
        continue
    values = df[available_cols].apply(pd.to_numeric, errors="coerce")
    valid = ts.notna() & values.notna().any(axis=1)
    if not valid.any():
        continue
    latest = ts[valid].max()
    score = (latest, int(valid.sum()))
    if best is None or score > best[0]:
        best = (score, path)

if best is not None:
    print(best[1])
PY
}

keep_stale_and_exit() {
  local reason="$1"
  local stale_rc=0
  if [[ "${STALE_FALLBACK_IS_FAILURE}" == "1" ]]; then
    stale_rc=1
  fi
  if [[ "${ALLOW_STALE_ON_ERROR}" == "1" ]] && [[ -f "${PREVIOUS_LIVE_JSON}" ]]; then
    mkdir -p "$(dirname "${ASSET_JSON}")"
    cp "${PREVIOUS_LIVE_JSON}" "${ASSET_JSON}"
    gh_warn "${reason}"
    gh_warn "Keeping latest live-data GEFS asset without update: ${ASSET_JSON}"
    print_asset_metadata
    exit "${stale_rc}"
  fi

  if [[ "${ALLOW_STALE_ON_ERROR}" == "1" ]] && [[ -f "${ASSET_JSON}" ]]; then
    gh_warn "${reason}"
    gh_warn "Keeping tracked GEFS asset without update: ${ASSET_JSON}"
    print_asset_metadata
    exit "${stale_rc}"
  fi
  log_error "${reason}"
  if [[ "${ALLOW_STALE_ON_ERROR}" != "1" ]]; then
    log_error "Set GEFS_FORECAST_ALLOW_STALE_ON_ERROR=1 to allow stale-asset fallback."
  elif [[ ! -f "${ASSET_JSON}" ]]; then
    log_error "Stale fallback was requested but no prior asset exists at ${ASSET_JSON}."
  fi
  exit 1
}

precheck_existing_asset() {
  if [[ ! -f "${ASSET_JSON}" ]]; then
    echo "[INFO] GEFS precheck: existing asset missing; full refresh required."
    return 0
  fi

  local output status
  set +e
  output="$(
    GEFS_PRECHECK_ASSET_PATH="${ASSET_JSON}" \
    GEFS_PRECHECK_CFG_PATH="${CFG}" \
    GEFS_PRECHECK_PIPELINE_DIR="${PIPELINE_DIR}" \
    GEFS_PRECHECK_REQUIRE_OBSERVED="${INCLUDE_OBSERVED_RETROSPECTIVE}" \
    python - <<'PY'
import datetime as dt
import json
import os
import sys
from pathlib import Path


def parse_iso(value):
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except Exception:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


pipeline_dir = Path(os.environ["GEFS_PRECHECK_PIPELINE_DIR"])
if str(pipeline_dir) not in sys.path:
    sys.path.insert(0, str(pipeline_dir))

from src.config import load_pipeline_config
from src.cycle import discover_latest_complete_cycle


asset_path = Path(os.environ["GEFS_PRECHECK_ASSET_PATH"])
cfg_path = Path(os.environ["GEFS_PRECHECK_CFG_PATH"])
require_observed = os.environ.get("GEFS_PRECHECK_REQUIRE_OBSERVED") == "1"

try:
    asset = json.loads(asset_path.read_text(encoding="utf-8"))
except Exception as exc:
    print(f"[WARN] GEFS precheck: could not parse existing asset: {exc}")
    raise SystemExit(2)

current_init = parse_iso(asset.get("init_time_utc"))
if current_init is None:
    print("[WARN] GEFS precheck: existing asset has no valid init_time_utc.")
    raise SystemExit(3)

cfg = load_pipeline_config(cfg_path)
latest = discover_latest_complete_cycle(cfg, dt.datetime.now(dt.timezone.utc))
print(f"[INFO] GEFS precheck latest_complete_init_utc={latest.init_time_utc.isoformat()}")
print(f"[INFO] GEFS precheck existing_asset_init_utc={current_init.isoformat()}")

if require_observed:
    observed = asset.get("observed_retrospective") or {}
    observed_ppt_n = 0
    observed_soil_n = 0
    if isinstance(observed, dict):
        ppt = observed.get("daily_avg_ppt")
        observed_ppt_n = len(ppt) if isinstance(ppt, list) else 0
        for key in (
            "daily_avg_soil_ERA5",
            "daily_avg_soil_NWM_SOIL_M",
            "daily_avg_soil_NWM_SOIL_W",
        ):
            series = observed.get(key)
            if isinstance(series, list):
                observed_soil_n = max(observed_soil_n, len(series))
    print(f"[INFO] GEFS precheck observed_context_precip_points={observed_ppt_n}")
    print(f"[INFO] GEFS precheck observed_context_soil_points={observed_soil_n}")
    if observed_ppt_n <= 0 and observed_soil_n <= 0:
        print("[INFO] GEFS precheck: observed retrospective context missing; refresh required.")
        raise SystemExit(11)
    precip = asset.get("precip") or {}
    precip_support_ok = False
    if isinstance(precip, dict):
        for block in precip.values():
            if isinstance(block, dict) and "24-hour" in str(block.get("time_support") or "").lower():
                precip_support_ok = True
                break
    if observed_ppt_n > 0 and not precip_support_ok:
        print("[INFO] GEFS precheck: observed PRISM context requires 24-hour GEFS precipitation totals; refresh required.")
        raise SystemExit(12)
    soil = asset.get("soil_moisture") or {}
    soil_support_ok = False
    if isinstance(soil, dict):
        for block in soil.values():
            if isinstance(block, dict) and "24-hour mean" in str(block.get("time_support") or "").lower():
                soil_support_ok = True
                break
    if observed_soil_n > 0 and not soil_support_ok:
        print("[INFO] GEFS precheck: observed ERA5 context requires 24-hour GEFS soil-moisture means; refresh required.")
        raise SystemExit(13)

if current_init >= latest.init_time_utc:
    raise SystemExit(10)
raise SystemExit(0)
PY
  )"
  status=$?
  set -e

  if [[ -n "${output}" ]]; then
    echo "${output}"
  fi

  if [[ ${status} -eq 10 ]]; then
    echo "[INFO] GEFS precheck: existing asset already matches the latest complete cycle; skipping full refresh."
    print_asset_metadata
    exit 0
  fi

  if [[ ${status} -ne 0 ]]; then
    echo "[WARN] GEFS precheck failed with status ${status}; continuing with full refresh."
  else
    echo "[INFO] GEFS precheck: existing asset is behind latest complete cycle; refreshing."
  fi
}

cd "${REPO_ROOT}"

if [[ ! -f "${RUNNER}" ]]; then
  log_error "Runner not found at ${RUNNER}"
  exit 1
fi

if [[ ! -f "${EXPORTER}" ]]; then
  log_error "Exporter not found at ${EXPORTER}"
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
  log_error "Missing Python dependencies for GEFS pipeline."
  echo "Install with:" >&2
  echo "  cd _sandbox/gefs_point_pipeline && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt" >&2
  exit 1
fi

load_previous_live_asset
precheck_existing_asset

if ! python "${RUNNER}" --gefs-config "${CFG}" --profile full --log-level INFO; then
  keep_stale_and_exit "GEFS runner failed."
fi

exporter_args=(
  "${EXPORTER}"
  --gefs-config "${CFG}"
  --observation-window-days "${OBS_WINDOW_DAYS}"
  --analysis-history-max-commits "${ANALYSIS_HISTORY_MAX_COMMITS}"
)
if [[ "${INCLUDE_OBSERVED_RETROSPECTIVE}" == "1" ]]; then
  if [[ -n "${OBSERVED_RETROSPECTIVE_CSV}" ]]; then
    observed_csv="${OBSERVED_RETROSPECTIVE_CSV}"
  else
    observed_csv="$(choose_observed_retrospective_csv)"
  fi
  if [[ -z "${observed_csv}" || ! -f "${observed_csv}" ]]; then
    keep_stale_and_exit "Observed retrospective CSV not found for GEFS export."
  fi
  echo "[INFO] Using observed retrospective CSV: ${observed_csv}"
  exporter_args+=(--include-observed-retrospective --observed-retrospective-csv "${observed_csv}")
fi

if ! python "${exporter_args[@]}"; then
  keep_stale_and_exit "GEFS exporter failed."
fi

if [[ ! -f "${WEB_JSON}" ]]; then
  keep_stale_and_exit "Expected web export not found: ${WEB_JSON}"
fi

if ! GEFS_VALIDATE_PATH="${WEB_JSON}" \
  GEFS_VALIDATE_REQUIRE_OBSERVED="${INCLUDE_OBSERVED_RETROSPECTIVE}" \
  python - <<'PY'
import json
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path

path = Path(os.environ.get("GEFS_VALIDATE_PATH", "assets/data/forecasts/gefs_big_trees_latest.json"))
require_observed = os.environ.get("GEFS_VALIDATE_REQUIRE_OBSERVED") == "1"
require_context = os.environ.get("GEFS_VALIDATE_REQUIRE_CONTEXT") == "1"
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
warnings = []
window_days = int(data.get("observation_window_days") or 0)
if window_days < 20:
    errors.append(f"observation_window_days={window_days} (expected >= 20)")

member_count = int(data.get("member_count") or 0)
if member_count <= 0:
    errors.append("member_count is missing or zero")

def best_series_count(section_name):
    section = data.get(section_name) or {}
    best = 0
    if not isinstance(section, dict):
        return 0
    for level_block in section.values():
        if not isinstance(level_block, dict):
            continue
        for metric in ("p50", "mean", "p10", "p90"):
            series = level_block.get(metric)
            if isinstance(series, list):
                best = max(best, len(series))
    return best

precip_forecast_points = best_series_count("precip")
soil_forecast_points = best_series_count("soil_moisture")
print("forecast_precip_representative_points:", precip_forecast_points)
print("forecast_soil_representative_points:", soil_forecast_points)
if precip_forecast_points <= 0:
    errors.append("precip forecast series are missing")
if soil_forecast_points <= 0:
    errors.append("soil-moisture forecast series are missing")

observed_ppt_points = 0
observed_soil_points = 0
if isinstance(obs, dict):
    ppt = obs.get("daily_avg_ppt")
    observed_ppt_points = len(ppt) if isinstance(ppt, list) else 0
    for key in (
        "daily_avg_soil_ERA5",
        "daily_avg_soil_NWM_SOIL_M",
        "daily_avg_soil_NWM_SOIL_W",
    ):
        series = obs.get(key)
        if isinstance(series, list):
            observed_soil_points = max(observed_soil_points, len(series))
print("observed_precip_points:", observed_ppt_points)
print("observed_soil_points:", observed_soil_points)
if require_observed and observed_ppt_points <= 0 and observed_soil_points <= 0:
    errors.append("observed retrospective precipitation or soil context is missing")
if require_observed and observed_ppt_points > 0:
    precip_support_ok = False
    precip = data.get("precip") or {}
    if isinstance(precip, dict):
        for block in precip.values():
            if isinstance(block, dict) and "24-hour" in str(block.get("time_support") or "").lower():
                precip_support_ok = True
                break
    print("forecast_precip_24h_support:", precip_support_ok)
    if not precip_support_ok:
        errors.append("observed PRISM precipitation is daily, but GEFS precipitation is not exported as 24-hour totals")
if require_observed and observed_soil_points > 0:
    soil_support_ok = False
    soil = data.get("soil_moisture") or {}
    if isinstance(soil, dict):
        for block in soil.values():
            if isinstance(block, dict) and "24-hour mean" in str(block.get("time_support") or "").lower():
                soil_support_ok = True
                break
    print("forecast_soil_24h_mean_support:", soil_support_ok)
    if not soil_support_ok:
        errors.append("observed ERA5 soil moisture is daily, but GEFS soil moisture is not exported as 24-hour means")

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
    if require_context and p_count < min_expected:
        warnings.append(f"precip analysis coverage too sparse ({p_count} < {min_expected})")
    if require_context and s_count < min_expected:
        warnings.append(f"soil analysis coverage too sparse ({s_count} < {min_expected})")
    if require_context and (p_first is None or p_first > (start + edge_tol)):
        warnings.append("precip analysis does not cover start of retrospective window")
    if require_context and (s_first is None or s_first > (start + edge_tol)):
        warnings.append("soil analysis does not cover start of retrospective window")
    if require_context and (p_last is None or p_last < (precip_end - edge_tol)):
        warnings.append("precip analysis does not include recent cycle context")
    if require_context and (s_last is None or s_last < (soil_end - edge_tol)):
        warnings.append("soil analysis does not include recent cycle context")

quality_warnings = data.get("quality_warnings") or []
if isinstance(quality_warnings, list):
    for warning in quality_warnings:
        if isinstance(warning, str) and warning.strip():
            warnings.append(warning.strip())

deduped_warnings = []
seen_warnings = set()
for warning in warnings:
    if warning in seen_warnings:
        continue
    seen_warnings.add(warning)
    deduped_warnings.append(warning)

if errors:
    print("validation_status=failed")
    for err in errors:
        print("validation_error:", err)
    raise SystemExit(1)
if deduped_warnings:
    print("validation_status=ok_with_warnings")
    for warning in deduped_warnings:
        print("validation_warning:", warning)
else:
    print("validation_status=ok")
PY
then
  keep_stale_and_exit "GEFS validation failed for freshly exported payload."
fi

mkdir -p "$(dirname "${ASSET_JSON}")"
cp "${WEB_JSON}" "${ASSET_JSON}"

print_asset_metadata
