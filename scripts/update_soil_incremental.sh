#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_END_DATE="${1:-$(date -u +%Y-%m-%d)}"
ERA5_LAG_DAYS="${ERA5_LAG_DAYS:-6}"
CSV_PATH="${ROOT_DIR}/soil_moisture_data/soil_moisture_big_trees_daily_avg_1987_2023.csv"
TMP_DIR="${ROOT_DIR}/soil_moisture_data/.tmp_era5_incremental_$$"
TMP_DAILY="${ROOT_DIR}/soil_moisture_data/.soil_daily_incremental_${TARGET_END_DATE}_$$.csv"
TMP_ATTEMPT_LOG="${ROOT_DIR}/soil_moisture_data/.soil_attempt_${TARGET_END_DATE}_$$.log"
PYTHON_BIN_DEFAULT="/home/jaguir26/python39/bin/python3"
PYTHON_BIN="${PYTHON_BIN:-$PYTHON_BIN_DEFAULT}"

mkdir -p "${ROOT_DIR}/soil_moisture_data"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="$(command -v python3)"
fi

cleanup() {
  rm -f "${TMP_DAILY}" "${TMP_ATTEMPT_LOG}"
  rm -rf "${TMP_DIR}"
}

trap cleanup EXIT

shift_date_back_one_day() {
  "${PYTHON_BIN}" - <<'PY' "$1"
import sys
from datetime import timedelta

import pandas as pd

print((pd.Timestamp(sys.argv[1]).date() - timedelta(days=1)).isoformat())
PY
}

count_csv_rows() {
  "${PYTHON_BIN}" - <<'PY' "$1"
import sys
from pathlib import Path

import pandas as pd

path = Path(sys.argv[1])
if not path.exists():
    print(0)
    raise SystemExit(0)

df = pd.read_csv(path)
print(len(df.index))
PY
}

if [[ -n "${ERA5_LAG_DAYS}" ]]; then
  MAX_END_DATE="$(
    "${PYTHON_BIN}" - <<'PY' "${ERA5_LAG_DAYS}"
import sys
from datetime import datetime, timedelta, timezone

raw = sys.argv[1]
try:
    lag_days = int(raw)
except Exception:
    lag_days = 0

if lag_days <= 0:
    print("")
    raise SystemExit(0)

today = datetime.now(timezone.utc).date()
max_date = today - timedelta(days=lag_days)
print(max_date.isoformat())
PY
  )"

  if [[ -n "${MAX_END_DATE}" && "${TARGET_END_DATE}" > "${MAX_END_DATE}" ]]; then
    echo "[INFO] Capping ERA5 target end date from ${TARGET_END_DATE} to ${MAX_END_DATE} (ERA5_LAG_DAYS=${ERA5_LAG_DAYS})"
    TARGET_END_DATE="${MAX_END_DATE}"
  fi
fi

START_DATE="$(
"${PYTHON_BIN}" - <<'PY' "${CSV_PATH}"
import sys
from datetime import timedelta
from pathlib import Path
import pandas as pd

csv_path = Path(sys.argv[1])
if not csv_path.exists():
    print("1987-01-01")
    raise SystemExit(0)

df = pd.read_csv(csv_path)
if "Date" not in df.columns:
    print("1987-01-01")
    raise SystemExit(0)

dt = pd.to_datetime(df["Date"], errors="coerce")
if dt.notna().any():
    print((dt.max().date() + timedelta(days=1)).isoformat())
else:
    print("1987-01-01")
PY
)"

echo "[INFO] Soil incremental start=${START_DATE} end=${TARGET_END_DATE}"
if [[ "${START_DATE}" > "${TARGET_END_DATE}" ]]; then
  echo "[INFO] Soil already up to date; nothing to do."
  exit 0
fi

ATTEMPT_END_DATE="${TARGET_END_DATE}"
FOUND_ROWS=0

while [[ ! "${ATTEMPT_END_DATE}" < "${START_DATE}" ]]; do
  rm -f "${TMP_DAILY}" "${TMP_ATTEMPT_LOG}"
  rm -rf "${TMP_DIR}"

  set +e
  "${PYTHON_BIN}" -u "${ROOT_DIR}/scripts/build_era5_soil_moisture_point_series.py" \
    --start-date "${START_DATE}" \
    --end-date "${ATTEMPT_END_DATE}" \
    --cds-url "https://cds.climate.copernicus.eu/api" \
    --tmp-dir "${TMP_DIR}" \
    --daily-csv "${TMP_DAILY}" \
    --overwrite >"${TMP_ATTEMPT_LOG}" 2>&1
  ATTEMPT_RC=$?
  set -e

  cat "${TMP_ATTEMPT_LOG}"

  if [[ "${ATTEMPT_RC}" -eq 0 ]]; then
    ROW_COUNT="$(count_csv_rows "${TMP_DAILY}")"
    if [[ "${ROW_COUNT}" -gt 0 ]]; then
      TARGET_END_DATE="${ATTEMPT_END_DATE}"
      FOUND_ROWS=1
      break
    fi
  elif ! grep -Eiq "The job has failed|No daily rows produced|none of the data you have requested is available yet|latest date available|multiadapternodataerror|no data available" "${TMP_ATTEMPT_LOG}"; then
    exit "${ATTEMPT_RC}"
  fi

  if [[ "${ATTEMPT_END_DATE}" == "${START_DATE}" ]]; then
    break
  fi

  NEXT_END_DATE="$(shift_date_back_one_day "${ATTEMPT_END_DATE}")"
  echo "[INFO] No ERA5 rows available through ${ATTEMPT_END_DATE}; retrying with ${NEXT_END_DATE}."
  ATTEMPT_END_DATE="${NEXT_END_DATE}"
done

if [[ "${FOUND_ROWS}" != "1" ]]; then
  echo "[INFO] No new ERA5 rows are available yet after probing back to ${START_DATE}."
  exit 0
fi

"${PYTHON_BIN}" - <<'PY' "${CSV_PATH}" "${TMP_DAILY}" "${START_DATE}" "${TARGET_END_DATE}"
import sys
from pathlib import Path
import pandas as pd

base_csv = Path(sys.argv[1])
inc_csv = Path(sys.argv[2])
start_date = pd.Timestamp(sys.argv[3])
end_date = pd.Timestamp(sys.argv[4])

parts = []
if base_csv.exists():
    base_df = pd.read_csv(base_csv)
    if "Date" in base_df.columns:
        parts.append(base_df)

if inc_csv.exists():
    inc_df = pd.read_csv(inc_csv)
    if "Date" in inc_df.columns:
        inc_df["Date"] = pd.to_datetime(inc_df["Date"], errors="coerce")
        inc_df = inc_df.dropna(subset=["Date"])
        inc_df = inc_df[(inc_df["Date"] >= start_date) & (inc_df["Date"] <= end_date)]
        if not inc_df.empty:
            inc_df["Date"] = inc_df["Date"].dt.strftime("%Y-%m-%d")
            parts.append(inc_df)

if not parts:
    print("[WARN] No soil dataframes available to merge.")
    raise SystemExit(0)

out = pd.concat(parts, ignore_index=True)
out["Date"] = pd.to_datetime(out["Date"], errors="coerce")
out = out.dropna(subset=["Date"])
if "Daily_Avg_Soil_Moisture" in out.columns:
    out["Daily_Avg_Soil_Moisture"] = pd.to_numeric(out["Daily_Avg_Soil_Moisture"], errors="coerce")
out = out[out["Date"] <= end_date]
out = out.sort_values("Date").drop_duplicates(subset=["Date"], keep="last")
out["Date"] = out["Date"].dt.strftime("%Y-%m-%d")
out.to_csv(base_csv, index=False)
print(f"[OK] merged soil rows={len(out)} output={base_csv}")
PY

echo "[OK] Soil incremental update complete."
