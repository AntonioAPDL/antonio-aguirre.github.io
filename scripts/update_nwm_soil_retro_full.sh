#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_END_DATE="${1:-$(date -u +%Y-%m-%d)}"
OUT_DIR="${ROOT_DIR}/soil_moisture_data"
OUT_CSV="${OUT_DIR}/nwm_soil_moisture_big_trees_daily_1987_present.csv"
OUT_META="${OUT_DIR}/nwm_soil_moisture_big_trees_daily_1987_present.meta.json"
PYTHON_BIN_DEFAULT="/home/jaguir26/python39/bin/python3"
PYTHON_BIN="${PYTHON_BIN:-$PYTHON_BIN_DEFAULT}"
NWM_RETRO_FORCE_REFRESH="${NWM_RETRO_FORCE_REFRESH:-0}"
NWM_RETRO_PROVIDER_RECHECK_DAYS="${NWM_RETRO_PROVIDER_RECHECK_DAYS:-30}"

mkdir -p "${OUT_DIR}"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="$(command -v python3)"
fi

if [[ "${NWM_RETRO_FORCE_REFRESH}" != "1" && -f "${OUT_CSV}" && -f "${OUT_META}" ]]; then
  SKIP_DECISION="$(
  "${PYTHON_BIN}" - <<'PY' "${OUT_CSV}" "${OUT_META}" "${TARGET_END_DATE}" "${NWM_RETRO_PROVIDER_RECHECK_DAYS}"
import json
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timezone

csv_path = Path(sys.argv[1])
meta_path = Path(sys.argv[2])
target_end = pd.Timestamp(sys.argv[3]).date()
recheck_days_raw = sys.argv[4]
try:
    recheck_days = max(1, int(recheck_days_raw))
except Exception:
    recheck_days = 30

try:
    df = pd.read_csv(csv_path)
    dmax = pd.to_datetime(df.get("Date"), errors="coerce").max()
except Exception:
    dmax = pd.NaT

try:
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    m_end_raw = meta.get("effective_end_date", "")
    m_end = pd.Timestamp(m_end_raw).date() if m_end_raw else None
    created_raw = meta.get("created_utc", "")
    created = pd.Timestamp(created_raw).to_pydatetime() if created_raw else None
    if created is not None and created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
except Exception:
    m_end = None
    created = None

if pd.notna(dmax) and dmax.date() >= target_end:
    print(f"skip_complete|NWM retrospective soil already complete through {target_end.isoformat()}.")
    raise SystemExit(0)

if pd.notna(dmax) and m_end is not None and dmax.date() >= m_end and m_end < target_end:
    if created is not None:
        age_days = (datetime.now(timezone.utc) - created.astimezone(timezone.utc)).total_seconds() / 86400.0
        if age_days < recheck_days:
            print(
                "skip_provider_limited|"
                f"NWM retrospective source last available through {m_end.isoformat()}; "
                f"next provider recheck after {recheck_days - age_days:.1f} days "
                f"(set NWM_RETRO_FORCE_REFRESH=1 to override)."
            )
            raise SystemExit(0)

print("run_refresh|NWM retrospective soil refresh required.")
PY
  )"
  DECISION="${SKIP_DECISION%%|*}"
  MESSAGE="${SKIP_DECISION#*|}"
  if [[ "${DECISION}" == "skip_complete" || "${DECISION}" == "skip_provider_limited" ]]; then
    echo "[INFO] ${MESSAGE}"
    exit 0
  fi
  echo "[INFO] ${MESSAGE}"
fi

"${PYTHON_BIN}" "${ROOT_DIR}/scripts/build_nwm_retro_soil_point_series.py" \
  --lat 37.0443931 \
  --lon -122.072464 \
  --start-date 1987-01-01 \
  --end-date "${TARGET_END_DATE}" \
  --soil-layer-index 0 \
  --out-csv "${OUT_CSV}" \
  --out-meta "${OUT_META}"

echo "[OK] NWM retrospective soil build complete."
echo "[OK] CSV: ${OUT_CSV}"
echo "[OK] META: ${OUT_META}"
