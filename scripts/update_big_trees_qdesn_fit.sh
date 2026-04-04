#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILDER="${REPO_ROOT}/scripts/build_big_trees_qdesn_overlay.R"
SANDBOX_JSON="${REPO_ROOT}/data/_sandbox_qdesn/big_trees_qdesn_latest.json"
ASSETS_JSON="${REPO_ROOT}/assets/data/forecasts/big_trees_qdesn_latest.json"

ALLOW_STALE_ON_ERROR="${BIG_TREES_QDESN_ALLOW_STALE_ON_ERROR:-1}"
INSTALL_FROM_GITHUB="${BIG_TREES_QDESN_INSTALL_EXDQLM:-0}"
EXDQLM_REPO="${BIG_TREES_QDESN_EXDQLM_REPO:-/data/muscat_data/jaguir26/exdqlm}"
START_DATE="${BIG_TREES_QDESN_START_DATE:-1990-01-01}"
LOCAL_TZ="${BIG_TREES_QDESN_LOCAL_TZ:-America/Los_Angeles}"
IV_RECENT_DAYS="${BIG_TREES_QDESN_IV_RECENT_DAYS:-90}"
IV_MIN_COVERAGE="${BIG_TREES_QDESN_IV_MIN_COVERAGE:-0.90}"
WARM_START_N="${BIG_TREES_QDESN_WARM_START_N:-2500}"
WINDOW_DAYS="${BIG_TREES_QDESN_WINDOW_DAYS:-20}"
ND_DRAWS="${BIG_TREES_QDESN_ND_DRAWS:-3000}"
CHUNK_SIZE="${BIG_TREES_QDESN_CHUNK_SIZE:-250}"
VB_MAX_ITER="${BIG_TREES_QDESN_VB_MAX_ITER:-35}"
VB_N_SAMP_XI="${BIG_TREES_QDESN_VB_N_SAMP_XI:-50}"
ONLINE_MAXIT_SIGMAGAM="${BIG_TREES_QDESN_ONLINE_MAXIT_SIGMAGAM:-250}"
ONLINE_M="${BIG_TREES_QDESN_ONLINE_M:-20}"
ONLINE_K="${BIG_TREES_QDESN_ONLINE_K:-80}"
ONLINE_W="${BIG_TREES_QDESN_ONLINE_W:-60}"
ONLINE_L_LOC="${BIG_TREES_QDESN_ONLINE_L_LOC:-1}"
ONLINE_WINDOW_PASSES="${BIG_TREES_QDESN_ONLINE_WINDOW_PASSES:-0}"

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
  --start-date "${START_DATE}"
  --local-tz "${LOCAL_TZ}"
  --iv-recent-days "${IV_RECENT_DAYS}"
  --iv-min-coverage "${IV_MIN_COVERAGE}"
  --warm-start-n "${WARM_START_N}"
  --window-days "${WINDOW_DAYS}"
  --nd-draws "${ND_DRAWS}"
  --chunk "${CHUNK_SIZE}"
  --vb-max-iter "${VB_MAX_ITER}"
  --vb-n-samp-xi "${VB_N_SAMP_XI}"
  --online-maxit-sigmagam "${ONLINE_MAXIT_SIGMAGAM}"
  --online-M "${ONLINE_M}"
  --online-K "${ONLINE_K}"
  --online-W "${ONLINE_W}"
  --online-L-loc "${ONLINE_L_LOC}"
  --online-window-passes "${ONLINE_WINDOW_PASSES}"
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
