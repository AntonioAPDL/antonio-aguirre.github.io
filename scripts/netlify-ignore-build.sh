#!/usr/bin/env bash
set -euo pipefail

# Netlify ignore commands use exit code 0 to skip a build and 1 to continue.
# This site should rebuild for website/code/CV changes, but not for data-only
# commits that may exist from older automation or manual backfills.

HEAD_REF="${COMMIT_REF:-HEAD}"
BASE_REF="${CACHED_COMMIT_REF:-}"

if [[ -z "${BASE_REF}" || "${BASE_REF}" =~ ^0+$ ]]; then
  if git rev-parse --verify HEAD^ >/dev/null 2>&1; then
    BASE_REF="HEAD^"
  else
    echo "No previous commit is available; running build."
    exit 1
  fi
fi

if ! git rev-parse --verify "${BASE_REF}^{commit}" >/dev/null 2>&1; then
  echo "Could not resolve base commit ${BASE_REF}; running build."
  exit 1
fi

if ! git rev-parse --verify "${HEAD_REF}^{commit}" >/dev/null 2>&1; then
  echo "Could not resolve head commit ${HEAD_REF}; running build."
  exit 1
fi

mapfile -t changed_files < <(git diff --name-only "${BASE_REF}" "${HEAD_REF}" --)

if [[ "${#changed_files[@]}" -eq 0 ]]; then
  echo "No file changes detected; skipping build."
  exit 0
fi

is_data_only_path() {
  case "$1" in
    assets/data/forecasts/*) return 0 ;;
    climate_daily_ppt_soil.csv) return 0 ;;
    climate_series_status.csv) return 0 ;;
    prism_precipitation_santa_cruz_1987_2023.csv) return 0 ;;
    soil_moisture_data/*) return 0 ;;
    data/_sandbox_gefs/history/state/*) return 0 ;;
    data/_sandbox_gefs/web/*) return 0 ;;
    data/_sandbox_nws/*) return 0 ;;
    logs/climate_updates/*) return 0 ;;
    *) return 1 ;;
  esac
}

for path in "${changed_files[@]}"; do
  if ! is_data_only_path "${path}"; then
    echo "Build required because ${path} changed."
    exit 1
  fi
done

echo "Only generated data artifacts changed; skipping Netlify build."
exit 0
