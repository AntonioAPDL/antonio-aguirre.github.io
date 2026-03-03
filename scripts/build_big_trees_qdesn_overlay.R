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
period <- get_arg("--period", "P1825D")
window_days <- as.integer(get_arg("--window-days", "20"))
nd_draws <- as.integer(get_arg("--nd-draws", "3000"))
chunk_size <- as.integer(get_arg("--chunk", "250"))
exdqlm_repo <- get_arg("--exdqlm-repo", Sys.getenv("BIG_TREES_QDESN_EXDQLM_REPO", ""))
install_github <- has_flag("--install-github") ||
  identical(Sys.getenv("BIG_TREES_QDESN_INSTALL_EXDQLM", "0"), "1")

if (!nzchar(output_path)) stop("--output is required.", call. = FALSE)
if (!nzchar(site_id)) stop("--site-id is required.", call. = FALSE)
if (!nzchar(parameter_cd)) stop("--parameter-cd is required.", call. = FALSE)
if (!nzchar(period)) stop("--period is required.", call. = FALSE)
if (!is.finite(window_days) || window_days < 1L) window_days <- 20L
if (!is.finite(nd_draws) || nd_draws < 500L) nd_draws <- 3000L
if (!is.finite(chunk_size) || chunk_size < 50L) chunk_size <- 250L

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

fetch_usgs_iv_daily <- function(site_id, parameter_cd, period) {
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
  iv$date_utc <- as.Date(iv$timestamp_utc, tz = "UTC")
  daily <- stats::aggregate(value_cfs ~ date_utc, data = iv, FUN = function(z) mean(z, na.rm = TRUE))
  daily <- daily[is.finite(daily$value_cfs), , drop = FALSE]
  daily <- daily[order(daily$date_utc), , drop = FALSE]
  rownames(daily) <- NULL
  daily
}

daily <- fetch_usgs_iv_daily(site_id, parameter_cd, period)
if (nrow(daily) < 800L) {
  stop(sprintf("Need at least 800 daily observations; found %d.", nrow(daily)), call. = FALSE)
}

y_raw <- as.numeric(daily$value_cfs)
y_mean <- mean(y_raw, na.rm = TRUE)
y_sd <- stats::sd(y_raw, na.rm = TRUE)
if (!is.finite(y_sd) || y_sd <= 0) y_sd <- 1
y <- (y_raw - y_mean) / y_sd
bt_y <- function(z) z * y_sd + y_mean

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

design <- do.call(
  exdqlm::qdesn_fit_vb,
  c(list(y = y, p0 = 0.5, fit_readout = FALSE), desn_args)
)

keep_idx <- as.integer(design$meta$keep_idx)
X <- as.matrix(design$X)
y_fit <- y[keep_idx]
date_fit <- as.Date(daily$date_utc[keep_idx])

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
  M = 10L,
  K = 40L,
  W = 100L,
  L_loc = 2L,
  window_passes = 1L,
  maxit_sigmagam = 500L,
  jitter = 1e-10,
  warm_start_frac = 0.7,
  keep_trace = FALSE,
  update_rhs = TRUE,
  update_sigmagam = TRUE
)

# Force RHS tau-freeze warmup and LD/Delta path controls explicitly.
vb_cfg <- list(
  max_iter = 100L,
  tol = 1.0e-4,
  tol_par = 1.0e-4,
  n_samp_xi = 100L,
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
pp <- exdqlm::exal_vb_posterior_predict(
  fit,
  X_new = X,
  nd = nrow(draws$beta),
  chunk = chunk_size,
  draws = draws
)

mu_draws <- as.matrix(pp$mu_draws)
if (nrow(mu_draws) != length(y_fit) && ncol(mu_draws) == length(y_fit)) {
  mu_draws <- t(mu_draws)
}
if (nrow(mu_draws) != length(y_fit)) {
  stop("Posterior predictive draw matrix has unexpected dimensions.", call. = FALSE)
}

row_q <- function(mat, p) {
  apply(mat, 1L, stats::quantile, probs = p, na.rm = TRUE, names = FALSE, type = 7L)
}
q50 <- bt_y(as.numeric(row_q(mu_draws, 0.50)))
lo95 <- bt_y(as.numeric(row_q(mu_draws, 0.025)))
hi95 <- bt_y(as.numeric(row_q(mu_draws, 0.975)))

latest_date <- max(date_fit)
start_date <- latest_date - (window_days - 1L)
sel <- which(date_fit >= start_date)
if (!length(sel)) {
  sel <- seq.int(max(1L, length(date_fit) - window_days + 1L), length(date_fit))
}

to_points <- function(dates, values) {
  lapply(seq_along(dates), function(i) {
    list(
      t = sprintf("%sT00:00:00Z", format(as.Date(dates[i]), "%Y-%m-%d")),
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
    start_date_utc = as.character(min(daily$date_utc)),
    end_date_utc = as.character(max(daily$date_utc)),
    n_daily_observations = nrow(daily),
    n_fit = length(y_fit)
  ),
  window = list(
    n_days = as.integer(length(sel)),
    start_date_utc = as.character(min(date_fit[sel])),
    end_date_utc = as.character(max(date_fit[sel]))
  ),
  series = list(
    q50 = to_points(date_fit[sel], q50[sel]),
    lo95 = to_points(date_fit[sel], lo95[sel]),
    hi95 = to_points(date_fit[sel], hi95[sel])
  )
)

out_dir <- dirname(output_path)
if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
jsonlite::write_json(payload, output_path, pretty = TRUE, auto_unbox = TRUE, na = "null")

cat("QDESN overlay file:", output_path, "\n")
cat("Generated UTC:", payload$generated_at_utc, "\n")
cat("Window:", payload$window$start_date_utc, "to", payload$window$end_date_utc,
    sprintf("(%d points)\n", payload$window$n_days))
