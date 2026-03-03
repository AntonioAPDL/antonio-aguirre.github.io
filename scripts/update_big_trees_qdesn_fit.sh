#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILDER="${REPO_ROOT}/scripts/build_big_trees_qdesn_overlay.R"
SANDBOX_JSON="${REPO_ROOT}/data/_sandbox_qdesn/big_trees_qdesn_latest.json"
ASSETS_JSON="${REPO_ROOT}/assets/data/forecasts/big_trees_qdesn_latest.json"

ALLOW_STALE_ON_ERROR="${BIG_TREES_QDESN_ALLOW_STALE_ON_ERROR:-1}"
INSTALL_FROM_GITHUB="${BIG_TREES_QDESN_INSTALL_EXDQLM:-0}"
EXDQLM_REPO="${BIG_TREES_QDESN_EXDQLM_REPO:-/data/muscat_data/jaguir26/exdqlm}"
PERIOD="${BIG_TREES_QDESN_PERIOD:-P1825D}"
WINDOW_DAYS="${BIG_TREES_QDESN_WINDOW_DAYS:-20}"

log_info() { echo "[INFO] $*"; }
log_warn() { echo "[WARN] $*" >&2; }
log_error() { echo "[ERROR] $*" >&2; }

keep_stale_and_exit() {
  local reason="$1"
  if [[ "${ALLOW_STALE_ON_ERROR}" == "1" ]] && [[ -f "${ASSETS_JSON}" ]]; then
    log_warn "${reason}"
    log_warn "Keeping tracked QDESN asset without update: ${ASSETS_JSON}"
    exit 0
  fi
  log_error "${reason}"
  log_error "No fallback asset available (or stale fallback disabled)."
  exit 2
}

if ! command -v Rscript >/dev/null 2>&1; then
  keep_stale_and_exit "Rscript not found on PATH."
fi

if [[ ! -f "${BUILDER}" ]]; then
  keep_stale_and_exit "Missing builder script: ${BUILDER}"
fi

cd "${REPO_ROOT}"
mkdir -p "$(dirname "${SANDBOX_JSON}")" "$(dirname "${ASSETS_JSON}")"

cmd=(
  Rscript "${BUILDER}"
  --output "${SANDBOX_JSON}"
  --period "${PERIOD}"
  --window-days "${WINDOW_DAYS}"
  --exdqlm-repo "${EXDQLM_REPO}"
)
if [[ "${INSTALL_FROM_GITHUB}" == "1" ]]; then
  cmd+=(--install-github)
fi

set +e
"${cmd[@]}"
status=$?
set -e
if [[ ${status} -ne 0 ]]; then
  keep_stale_and_exit "QDESN builder failed with status ${status}."
fi

if [[ ! -f "${SANDBOX_JSON}" ]]; then
  keep_stale_and_exit "QDESN builder did not produce sandbox JSON."
fi

cp "${SANDBOX_JSON}" "${ASSETS_JSON}"

log_info "Updated QDESN overlay JSON: ${ASSETS_JSON}"
Rscript - <<'RS'
library(jsonlite)
`%||%` <- function(x, y) if (!is.null(x)) x else y
p <- "assets/data/forecasts/big_trees_qdesn_latest.json"
x <- fromJSON(p, simplifyVector = FALSE)
cat("[INFO] generated_at_utc:", x$generated_at_utc %||% "NA", "\n")
if (!is.null(x$window)) {
  cat("[INFO] window:", x$window$start_date_utc %||% "NA", "->", x$window$end_date_utc %||% "NA",
      sprintf("(%s points)\n", as.character(x$window$n_days %||% "NA")))
}
RS
