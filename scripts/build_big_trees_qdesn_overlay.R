#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE)

`%||%` <- function(x, y) if (!is.null(x)) x else y

args <- commandArgs(trailingOnly = TRUE)
get_arg <- function(flag, default = NULL) {
  i <- which(args == flag)
  if (length(i) && i < length(args)) args[i + 1L] else default
}
has_flag <- function(flag) any(args == flag)

output_path <- get_arg("--output", "data/_sandbox_qdesn/big_trees_qdesn_latest.json")
site_id <- get_arg("--site-id", "11160500")
parameter_cd <- get_arg("--parameter-cd", "00060")
start_date <- as.Date(get_arg("--start-date", Sys.getenv("BIG_TREES_QDESN_START_DATE", "1990-01-01")))
local_tz <- get_arg("--local-tz", Sys.getenv("BIG_TREES_QDESN_LOCAL_TZ", "America/Los_Angeles"))
iv_recent_days <- as.integer(get_arg("--iv-recent-days", Sys.getenv("BIG_TREES_QDESN_IV_RECENT_DAYS", "90")))
iv_min_coverage <- suppressWarnings(as.numeric(get_arg(
  "--iv-min-coverage",
  Sys.getenv("BIG_TREES_QDESN_IV_MIN_COVERAGE", "0.90")
)))
window_days <- as.integer(get_arg("--window-days", "20"))
nd_draws <- as.integer(get_arg("--nd-draws", "3000"))
chunk_size <- as.integer(get_arg("--chunk", "250"))
warm_start_n <- suppressWarnings(as.integer(get_arg("--warm-start-n", Sys.getenv("BIG_TREES_QDESN_WARM_START_N", "2500"))))
vb_max_iter <- suppressWarnings(as.integer(get_arg("--vb-max-iter", Sys.getenv("BIG_TREES_QDESN_VB_MAX_ITER", "35"))))
vb_n_samp_xi <- suppressWarnings(as.integer(get_arg("--vb-n-samp-xi", Sys.getenv("BIG_TREES_QDESN_VB_N_SAMP_XI", "50"))))
online_maxit_sigmagam <- suppressWarnings(as.integer(get_arg(
  "--online-maxit-sigmagam",
  Sys.getenv("BIG_TREES_QDESN_ONLINE_MAXIT_SIGMAGAM", "250")
)))
online_M <- suppressWarnings(as.integer(get_arg("--online-M", Sys.getenv("BIG_TREES_QDESN_ONLINE_M", "20"))))
online_K <- suppressWarnings(as.integer(get_arg("--online-K", Sys.getenv("BIG_TREES_QDESN_ONLINE_K", "80"))))
online_W <- suppressWarnings(as.integer(get_arg("--online-W", Sys.getenv("BIG_TREES_QDESN_ONLINE_W", "60"))))
online_L_loc <- suppressWarnings(as.integer(get_arg("--online-L-loc", Sys.getenv("BIG_TREES_QDESN_ONLINE_L_LOC", "1"))))
online_window_passes <- suppressWarnings(as.integer(get_arg(
  "--online-window-passes",
  Sys.getenv("BIG_TREES_QDESN_ONLINE_WINDOW_PASSES", "0")
)))
exdqlm_repo <- get_arg("--exdqlm-repo", Sys.getenv("BIG_TREES_QDESN_EXDQLM_REPO", ""))
install_github <- has_flag("--install-github") ||
  identical(Sys.getenv("BIG_TREES_QDESN_INSTALL_EXDQLM", "0"), "1")

if (!nzchar(output_path)) stop("--output is required.", call. = FALSE)
if (!nzchar(site_id)) stop("--site-id is required.", call. = FALSE)
if (!nzchar(parameter_cd)) stop("--parameter-cd is required.", call. = FALSE)
if (is.na(start_date)) stop("--start-date must be YYYY-MM-DD.", call. = FALSE)
if (!nzchar(local_tz)) stop("--local-tz is required.", call. = FALSE)
if (!is.finite(iv_recent_days) || iv_recent_days < 7L) iv_recent_days <- 90L
if (!is.finite(iv_min_coverage) || iv_min_coverage <= 0 || iv_min_coverage > 1) iv_min_coverage <- 0.90
if (!is.finite(window_days) || window_days < 1L) window_days <- 20L
if (!is.finite(nd_draws) || nd_draws < 500L) nd_draws <- 3000L
if (!is.finite(chunk_size) || chunk_size < 50L) chunk_size <- 250L
if (!is.finite(warm_start_n) || warm_start_n < 500L) warm_start_n <- 2500L
if (!is.finite(vb_max_iter) || vb_max_iter < 10L) vb_max_iter <- 35L
if (!is.finite(vb_n_samp_xi) || vb_n_samp_xi < 20L) vb_n_samp_xi <- 50L
if (!is.finite(online_maxit_sigmagam) || online_maxit_sigmagam < 50L) online_maxit_sigmagam <- 250L
if (!is.finite(online_M) || online_M < 1L) online_M <- 20L
if (!is.finite(online_K) || online_K < online_M) online_K <- max(online_M, 80L)
if (!is.finite(online_W) || online_W < 0L) online_W <- 60L
if (!is.finite(online_L_loc) || online_L_loc < 1L) online_L_loc <- 1L
if (!is.finite(online_window_passes) || online_window_passes < 0L) online_window_passes <- 0L

need_pkg <- function(pkg) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    install.packages(pkg, repos = "https://cloud.r-project.org")
  }
}

need_pkg("jsonlite")

has_online_exdqlm <- function() {
  if (!requireNamespace("exdqlm", quietly = TRUE)) return(FALSE)
  "exal_online_fit" %in% getNamespaceExports("exdqlm")
}

if (!has_online_exdqlm()) {
  if (nzchar(exdqlm_repo) && dir.exists(exdqlm_repo)) {
    need_pkg("pkgload")
    pkgload::load_all(exdqlm_repo, quiet = TRUE, export_all = FALSE)
  }
}

if (!has_online_exdqlm() && install_github) {
  need_pkg("remotes")
  remotes::install_github(
    "AntonioAPDL/exdqlm@feature/model-selection-v2-impl",
    upgrade = "never",
    dependencies = TRUE,
    quiet = TRUE
  )
}

if (!has_online_exdqlm()) {
  stop(
    paste(
      "Could not load exdqlm with online API.",
      "Set --exdqlm-repo to a local checkout or pass --install-github."
    ),
    call. = FALSE
  )
}

parse_timestamp_utc <- function(x) {
  x <- as.character(x)
  # strptime %z does not always accept timezone with colon; normalize first.
  norm <- sub("([+-][0-9]{2}):([0-9]{2})$", "\\1\\2", x, perl = TRUE)
  ts <- as.POSIXct(strptime(norm, "%Y-%m-%dT%H:%M:%OS%z", tz = "UTC"))
  bad <- is.na(ts)
  if (any(bad)) {
    ts[bad] <- as.POSIXct(strptime(norm[bad], "%Y-%m-%dT%H:%M:%S%z", tz = "UTC"))
  }
  ts
}

fetch_usgs_iv_daily <- function(site_id, parameter_cd, period, local_tz, min_coverage = 0.90) {
  url <- sprintf(
    "https://waterservices.usgs.gov/nwis/iv/?format=json&sites=%s&parameterCd=%s&period=%s&siteStatus=all",
    utils::URLencode(site_id, reserved = TRUE),
    utils::URLencode(parameter_cd, reserved = TRUE),
    utils::URLencode(period, reserved = TRUE)
  )
  txt <- readLines(url, warn = FALSE)
  obj <- jsonlite::fromJSON(paste(txt, collapse = "\n"), simplifyVector = FALSE)
  values <- obj$value$timeSeries[[1]]$values[[1]]$value
  if (is.null(values) || !length(values)) {
    stop("USGS IV payload has no values.", call. = FALSE)
  }

  ts <- parse_timestamp_utc(vapply(values, function(r) r$dateTime %||% NA_character_, character(1)))
  val <- suppressWarnings(as.numeric(vapply(values, function(r) r$value %||% NA_character_, character(1))))
  keep <- is.finite(val) & !is.na(ts)
  if (!any(keep)) stop("USGS IV payload did not yield numeric observations.", call. = FALSE)

  iv <- data.frame(
    timestamp_utc = ts[keep],
    value_cfs = val[keep]
  )
  iv$date_local <- as.Date(iv$timestamp_utc, tz = local_tz)
  iv <- iv[order(iv$timestamp_utc), , drop = FALSE]

  step_seconds <- suppressWarnings(stats::median(
    as.numeric(diff(iv$timestamp_utc), units = "secs"),
    na.rm = TRUE
  ))
  if (!is.finite(step_seconds) || step_seconds <= 0) step_seconds <- 900
  expected_per_day <- max(1L, as.integer(round(86400 / step_seconds)))
  min_points <- max(1L, as.integer(ceiling(expected_per_day * min_coverage)))

  n_points <- stats::aggregate(value_cfs ~ date_local, data = iv, FUN = length)
  names(n_points)[2] <- "n_points"
  daily <- stats::aggregate(value_cfs ~ date_local, data = iv, FUN = function(z) mean(z, na.rm = TRUE))
  daily <- merge(daily, n_points, by = "date_local", all.x = TRUE, sort = FALSE)
  daily <- daily[is.finite(daily$value_cfs) & as.integer(daily$n_points) >= min_points, , drop = FALSE]
  daily <- daily[order(daily$date_local), , drop = FALSE]
  rownames(daily) <- NULL
  attr(daily, "iv_raw_n") <- nrow(iv)
  attr(daily, "iv_raw_start_utc") <- if (nrow(iv)) as.character(min(iv$timestamp_utc)) else NA_character_
  attr(daily, "iv_raw_end_utc") <- if (nrow(iv)) as.character(max(iv$timestamp_utc)) else NA_character_
  attr(daily, "iv_expected_points_per_day") <- expected_per_day
  attr(daily, "iv_min_points_required") <- min_points
  attr(daily, "iv_min_coverage") <- min_coverage
  daily
}

fetch_usgs_dv_daily <- function(site_id, parameter_cd, start_date, end_date) {
  url <- sprintf(
    "https://waterservices.usgs.gov/nwis/dv/?format=json&sites=%s&parameterCd=%s&startDT=%s&endDT=%s&siteStatus=all",
    utils::URLencode(site_id, reserved = TRUE),
    utils::URLencode(parameter_cd, reserved = TRUE),
    utils::URLencode(as.character(start_date), reserved = TRUE),
    utils::URLencode(as.character(end_date), reserved = TRUE)
  )
  txt <- readLines(url, warn = FALSE)
  obj <- jsonlite::fromJSON(paste(txt, collapse = "\n"), simplifyVector = FALSE)
  values <- obj$value$timeSeries[[1]]$values[[1]]$value
  if (is.null(values) || !length(values)) {
    return(data.frame(date_local = as.Date(character(0)), value_cfs = numeric(0)))
  }
  dt <- as.Date(vapply(values, function(r) substr(r$dateTime %||% NA_character_, 1L, 10L), character(1)))
  val <- suppressWarnings(as.numeric(vapply(values, function(r) r$value %||% NA_character_, character(1))))
  keep <- is.finite(val) & !is.na(dt)
  daily <- data.frame(date_local = dt[keep], value_cfs = val[keep])
  daily <- daily[order(daily$date_local), , drop = FALSE]
  rownames(daily) <- NULL
  daily
}

assemble_daily_series <- function(site_id, parameter_cd, start_date, local_tz, iv_recent_days, iv_min_coverage) {
  today_local <- as.Date(Sys.time(), tz = local_tz)
  last_complete_day <- today_local - 1L
  if (start_date > last_complete_day) {
    stop("start-date is after the last complete local day.", call. = FALSE)
  }

  dv <- fetch_usgs_dv_daily(site_id, parameter_cd, start_date, last_complete_day)

  iv_period <- sprintf("P%dD", as.integer(iv_recent_days))
  iv_error <- NULL
  iv <- tryCatch(
    fetch_usgs_iv_daily(site_id, parameter_cd, iv_period, local_tz, min_coverage = iv_min_coverage),
    error = function(e) {
      iv_error <<- conditionMessage(e)
      data.frame(date_local = as.Date(character(0)), value_cfs = numeric(0), n_points = integer(0))
    }
  )
  iv_raw_n <- as.integer(attr(iv, "iv_raw_n") %||% NA_integer_)
  iv_raw_start_utc <- attr(iv, "iv_raw_start_utc")
  iv_raw_end_utc <- attr(iv, "iv_raw_end_utc")
  iv_expected_points_per_day <- as.integer(attr(iv, "iv_expected_points_per_day") %||% NA_integer_)
  iv_min_points_required <- as.integer(attr(iv, "iv_min_points_required") %||% NA_integer_)
  iv_min_coverage_used <- as.numeric(attr(iv, "iv_min_coverage") %||% iv_min_coverage)
  iv <- iv[iv$date_local >= start_date & iv$date_local <= last_complete_day, , drop = FALSE]

  dv2 <- dv
  names(dv2)[names(dv2) == "value_cfs"] <- "value_cfs_dv"
  iv2 <- iv
  names(iv2)[names(iv2) == "value_cfs"] <- "value_cfs_iv"

  all_dates <- sort(unique(c(dv2$date_local, iv2$date_local)))
  merged <- data.frame(date_local = all_dates)
  merged <- merge(merged, dv2, by = "date_local", all.x = TRUE)
  merged <- merge(merged, iv2, by = "date_local", all.x = TRUE)

  merged$value_cfs <- ifelse(is.finite(merged$value_cfs_iv), merged$value_cfs_iv, merged$value_cfs_dv)
  merged$source <- ifelse(is.finite(merged$value_cfs_iv), "iv_agg", "dv")
  merged <- merged[is.finite(merged$value_cfs), c("date_local", "value_cfs", "source"), drop = FALSE]
  merged <- merged[order(merged$date_local), , drop = FALSE]
  rownames(merged) <- NULL

  attr(merged, "n_dv_observations") <- nrow(dv)
  attr(merged, "n_iv_recent_daily_observations") <- nrow(iv)
  attr(merged, "n_iv_recent_raw_observations") <- iv_raw_n
  attr(merged, "iv_recent_raw_start_utc") <- iv_raw_start_utc
  attr(merged, "iv_recent_raw_end_utc") <- iv_raw_end_utc
  attr(merged, "iv_recent_expected_points_per_day") <- iv_expected_points_per_day
  attr(merged, "iv_recent_min_points_required") <- iv_min_points_required
  attr(merged, "iv_recent_min_coverage") <- iv_min_coverage_used
  attr(merged, "iv_recent_error") <- iv_error
  attr(merged, "last_complete_day_local") <- as.character(last_complete_day)
  merged
}

daily <- assemble_daily_series(site_id, parameter_cd, start_date, local_tz, iv_recent_days, iv_min_coverage)
if (nrow(daily) < 800L) {
  stop(sprintf("Need at least 800 daily observations; found %d.", nrow(daily)), call. = FALSE)
}

y_raw <- as.numeric(daily$value_cfs)
y_mean <- mean(y_raw, na.rm = TRUE)
y_sd <- stats::sd(y_raw, na.rm = TRUE)
if (!is.finite(y_sd) || y_sd <= 0) y_sd <- 1
y <- (y_raw - y_mean) / y_sd
bt_y <- function(z) z * y_sd + y_mean

# Mirror model-selection defaults for readout construction.
readout_cfg <- list(
  include_input = TRUE,
  reservoir_lags = 1L,
  input_position = "after_reservoir",
  scale = TRUE
)

desn_args <- list(
  D = 3L,
  n = c(50L, 50L, 50L),
  n_tilde = c(50L, 50L),
  m = 30L,
  alpha = c(0.2, 0.2, 0.2),
  rho = c(0.95, 0.95, 0.95),
  act_f = "tanh",
  act_k = "identity",
  pi_w = c(0.1, 0.1, 0.1),
  pi_in = c(1.0, 1.0, 1.0),
  washout = 500L,
  add_bias = TRUE,
  seed = c(12345, 12344, 12343)
)

ms_build_readout_design_sim <- getFromNamespace("ms_build_readout_design_sim", "exdqlm")
readout_scale_fit <- getFromNamespace("readout_scale_fit", "exdqlm")

design <- ms_build_readout_design_sim(
  y_full = y,
  desn_args = desn_args,
  readout_include_input = isTRUE(readout_cfg$include_input),
  readout_reservoir_lags = as.integer(readout_cfg$reservoir_lags)
)

keep_idx <- as.integer(design$keep_aug_abs)
X <- as.matrix(design$X_aug_all)
y_fit <- y[keep_idx]
date_fit <- as.Date(daily$date_local[keep_idx])

readout_scale_info <- NULL
if (isTRUE(readout_cfg$scale)) {
  # Same scaling convention as model-selection runs: scale non-intercept columns.
  scale_fit <- readout_scale_fit(X, has_intercept = isTRUE(desn_args$add_bias))
  X <- as.matrix(scale_fit$X)
  readout_scale_info <- scale_fit$scale_info
}

if (length(y_fit) != nrow(X)) {
  stop("Design/readout alignment mismatch.", call. = FALSE)
}

L_fn <- getFromNamespace("L.fn", "exdqlm")
U_fn <- getFromNamespace("U.fn", "exdqlm")
gamma_bounds <- c(as.numeric(L_fn(0.5)), as.numeric(U_fn(0.5)))

rhs_cfg <- list(
  tau0 = 0.001,
  nu = 4.0,
  s2 = 0.1,
  shrink_intercept = FALSE,
  intercept_prec = 1.0e-16,
  n_inner = 1,
  eta_bounds = list(
    lambda = c(-20, 20),
    tau = c(-20, 20),
    c2 = c(-20, 20)
  ),
  h_curv = 1.0e-8,
  var_floor = 1.0e-8,
  verbose = FALSE,
  init_log_lambda = 0.0,
  init_log_tau = NULL,
  init_log_c2 = 0.0
)

beta_prior_obj <- exdqlm::beta_prior("rhs", rhs = rhs_cfg)

online_cfg <- list(
  enabled = TRUE,
  strict = FALSE,
  M = as.integer(online_M),
  K = as.integer(online_K),
  W = as.integer(online_W),
  L_loc = as.integer(online_L_loc),
  window_passes = as.integer(online_window_passes),
  maxit_sigmagam = as.integer(online_maxit_sigmagam),
  jitter = 1e-10,
  warm_start_n = as.integer(warm_start_n),
  warm_start_frac = 0.7,
  keep_trace = FALSE,
  update_rhs = TRUE,
  update_sigmagam = TRUE
)

# Force RHS tau-freeze warmup and LD/Delta path controls explicitly.
vb_cfg <- list(
  max_iter = as.integer(vb_max_iter),
  tol = 1.0e-4,
  tol_par = 1.0e-4,
  n_samp_xi = as.integer(vb_n_samp_xi),
  verbose = FALSE,
  rhs_freeze_tau_iters = 20L,
  rhs_freeze_tau_warmup_iters = 20L,
  rhs_update_every = 1L,
  rhs_update_every_warmup = 1L,
  rhs_update_every_warmup_iters = 0L,
  rhs_beta_presteps = 1L,
  rhs_beta_presteps_iters = 0L,
  rhs_gradcheck = FALSE,
  rhs_gradcheck_iters = c(1L, 5L),
  rhs_gradcheck_h = 1.0e-5,
  rhs_tau_local_tol = 1.0e-3,
  rhs_min_tau_updates = 1L,
  rhs_max_tau_updates = NA_integer_,
  rhs_force_tau_after_warmup = TRUE,
  rhs_recompute_elbo_after_tau_update = TRUE
)

fit <- exdqlm::exal_online_fit(
  y = y_fit,
  X = X,
  p0 = 0.5,
  gamma_bounds = gamma_bounds,
  control = online_cfg,
  vb_control = vb_cfg,
  max_iter = vb_cfg$max_iter,
  tol = vb_cfg$tol,
  tol_par = vb_cfg$tol_par,
  n_samp_xi = vb_cfg$n_samp_xi,
  verbose = vb_cfg$verbose,
  init = list(gamma = 0, sigma = 1),
  beta_prior_obj = beta_prior_obj,
  log_prior_gamma = function(g) 0
)

draws <- exdqlm::exal_vb_posterior_draws(fit, nd = nd_draws)
latest_date <- max(date_fit)
start_date_window <- latest_date - (window_days - 1L)
sel <- which(date_fit >= start_date_window)
if (!length(sel)) {
  sel <- seq.int(max(1L, length(date_fit) - window_days + 1L), length(date_fit))
}

pp <- exdqlm::exal_vb_posterior_predict(
  fit,
  X_new = X[sel, , drop = FALSE],
  nd = nrow(draws$beta),
  chunk = chunk_size,
  draws = draws
)

mu_draws <- as.matrix(pp$mu_draws)
if (nrow(mu_draws) != length(sel) && ncol(mu_draws) == length(sel)) {
  mu_draws <- t(mu_draws)
}
if (nrow(mu_draws) != length(sel)) {
  stop("Posterior predictive draw matrix has unexpected dimensions.", call. = FALSE)
}

row_q <- function(mat, p) {
  apply(mat, 1L, stats::quantile, probs = p, na.rm = TRUE, names = FALSE, type = 7L)
}
q50 <- bt_y(as.numeric(row_q(mu_draws, 0.50)))
lo95 <- bt_y(as.numeric(row_q(mu_draws, 0.025)))
hi95 <- bt_y(as.numeric(row_q(mu_draws, 0.975)))
obs_daily <- as.numeric(daily$value_cfs[keep_idx][sel])

to_points <- function(dates, values) {
  lapply(seq_along(dates), function(i) {
    list(
      # Noon UTC avoids local-time date rollbacks when plotting in Pacific time.
      t = sprintf("%sT12:00:00Z", format(as.Date(dates[i]), "%Y-%m-%d")),
      v = as.numeric(values[i])
    )
  })
}

payload <- list(
  generated_at_utc = format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC"),
  location = list(
    site_id = site_id,
    parameter_cd = parameter_cd
  ),
  units = "cfs",
  model = list(
    name = "qdesn_online_vbld",
    quantile = 0.50,
    interval = "95%",
    lag_only = TRUE,
    beta_prior = list(type = "rhs", rhs = rhs_cfg),
    online = online_cfg,
    vb_control = vb_cfg,
    readout = list(
      include_input = isTRUE(readout_cfg$include_input),
      input_position = as.character(readout_cfg$input_position),
      input_lags_y = if (isTRUE(readout_cfg$include_input)) seq_len(as.integer(desn_args$m)) else integer(0),
      reservoir_lags = as.integer(readout_cfg$reservoir_lags),
      readout_scale = isTRUE(readout_cfg$scale),
      n_design_columns = as.integer(ncol(X)),
      n_scaled_columns = as.integer(length(readout_scale_info$idx %||% integer(0))),
      warm_start_n = as.integer(warm_start_n)
    ),
    inference = list(
      sigma_gamma_block = "laplace_delta",
      xi_expectation = "deterministic_delta_method",
      gaussian_moment_matching = FALSE
    )
  ),
  scaling = list(
    y_center = y_mean,
    y_scale = y_sd
  ),
  data_span = list(
    start_date_utc = as.character(min(daily$date_local)),
    end_date_utc = as.character(max(daily$date_local)),
    start_date_local = as.character(min(daily$date_local)),
    end_date_local = as.character(max(daily$date_local)),
    local_tz = local_tz,
    last_complete_day_local = attr(daily, "last_complete_day_local"),
    n_dv_observations = as.integer(attr(daily, "n_dv_observations") %||% NA_integer_),
    n_iv_recent_daily_observations = as.integer(attr(daily, "n_iv_recent_daily_observations") %||% NA_integer_),
    n_iv_recent_raw_observations = as.integer(attr(daily, "n_iv_recent_raw_observations") %||% NA_integer_),
    iv_recent_raw_start_utc = attr(daily, "iv_recent_raw_start_utc"),
    iv_recent_raw_end_utc = attr(daily, "iv_recent_raw_end_utc"),
    iv_recent_expected_points_per_day = as.integer(attr(daily, "iv_recent_expected_points_per_day") %||% NA_integer_),
    iv_recent_min_points_required = as.integer(attr(daily, "iv_recent_min_points_required") %||% NA_integer_),
    iv_recent_min_coverage = as.numeric(attr(daily, "iv_recent_min_coverage") %||% iv_min_coverage),
    iv_recent_error = attr(daily, "iv_recent_error"),
    n_daily_observations = nrow(daily),
    n_fit = length(y_fit)
  ),
  window = list(
    n_days = as.integer(length(sel)),
    start_date_utc = as.character(min(date_fit[sel])),
    end_date_utc = as.character(max(date_fit[sel]))
  ),
  series = list(
    q50 = to_points(date_fit[sel], q50),
    lo95 = to_points(date_fit[sel], lo95),
    hi95 = to_points(date_fit[sel], hi95),
    obs_daily = to_points(date_fit[sel], obs_daily)
  )
)

out_dir <- dirname(output_path)
if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
jsonlite::write_json(payload, output_path, pretty = TRUE, auto_unbox = TRUE, na = "null")

cat("QDESN overlay file:", output_path, "\n")
cat("Generated UTC:", payload$generated_at_utc, "\n")
cat("Window:", payload$window$start_date_utc, "to", payload$window$end_date_utc,
    sprintf("(%d points)\n", payload$window$n_days))
