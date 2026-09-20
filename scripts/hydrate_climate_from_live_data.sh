#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE="${LIVE_DATA_REMOTE:-origin}"
BRANCH="${LIVE_DATA_BRANCH:-live-data}"

ARTIFACTS=(
  "prism_precipitation_santa_cruz_1987_2023.csv"
  "soil_moisture_data/soil_moisture_big_trees_daily_avg_1987_2023.csv"
  "soil_moisture_data/nwm_soil_moisture_big_trees_daily_1987_present.csv"
  "soil_moisture_data/nwm_soil_moisture_big_trees_daily_1987_present.meta.json"
  "climate_series_status.csv"
  "climate_daily_ppt_soil.csv"
)

cd "${REPO_ROOT}"

if ! git ls-remote --exit-code --heads "${REMOTE}" "${BRANCH}" >/dev/null 2>&1; then
  echo "[WARN] ${REMOTE}/${BRANCH} does not exist; keeping the checked-out climate baseline."
  exit 0
fi

git fetch --quiet "${REMOTE}" "+${BRANCH}:refs/remotes/${REMOTE}/${BRANCH}"

loaded=0
for artifact in "${ARTIFACTS[@]}"; do
  if ! git cat-file -e "${REMOTE}/${BRANCH}:${artifact}" 2>/dev/null; then
    echo "[WARN] ${artifact} is missing from ${REMOTE}/${BRANCH}; keeping the checked-out copy."
    continue
  fi
  mkdir -p "$(dirname "${artifact}")"
  tmp_path="${artifact}.live-data.tmp"
  git show "${REMOTE}/${BRANCH}:${artifact}" > "${tmp_path}"
  mv "${tmp_path}" "${artifact}"
  echo "[OK] hydrated ${artifact} from ${REMOTE}/${BRANCH}"
  loaded=$((loaded + 1))
done

echo "[OK] hydrated ${loaded}/${#ARTIFACTS[@]} climate artifacts from ${REMOTE}/${BRANCH}"
