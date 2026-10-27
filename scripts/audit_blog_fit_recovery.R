#!/usr/bin/env Rscript
# Re-run the published fits with a fixed panel of independent simulation seeds.
args <- commandArgs(trailingOnly = TRUE)
if (length(args) > 1L || (length(args) && args != "--include-exdqlm")) {
  stop("Usage: Rscript scripts/audit_blog_fit_recovery.R [--include-exdqlm]")
}
file_arg <- grep("^--file=", commandArgs(), value = TRUE)
root <- dirname(dirname(normalizePath(sub("^--file=", "", file_arg[[1L]]))))
run_article <- function(slug, data_seed, seed) {
  lines <- readLines(file.path(root, "_posts", paste0("2026-10-27-", slug, ".md")))
  env <- new.env(parent = globalenv())
  env$set.seed <- function(value, ...) {
    if (value == data_seed) value <- seed
    if (value == 61028L) value <- 10000L + seed
    set.seed(value, ...)
  }
  inside <- FALSE
  code <- character()
  invisible(capture.output(for (line in lines) {
    if (!inside && identical(line, "```r")) {
      inside <- TRUE
      code <- character()
    } else if (inside && identical(line, "```")) {
      eval(parse(text = code), env)
      inside <- FALSE
    } else if (inside) code <- c(code, line)
  }))
  stopifnot(!inside)
  env
}
recurrent <- do.call(rbind, lapply(1:10, function(seed) {
  env <- run_article("fixed-recurrent-quantile-features", 90210L, seed)
  c(seed = seed, RMSE = env$recovery[1], coverage = env$recovery[2])
}))
endpoints <- do.call(rbind, lapply(1:10, function(seed) {
  env <- run_article("interval-endpoint-regression", 61027L, seed)
  c(seed = seed, RMSE = env$endpoint_RMSE,
    coverage = env$heldout_content, population_content = env$population_content)
}))
print(recurrent)
print(endpoints)
stopifnot(mean(recurrent[, 2]) < 0.3,
          abs(mean(recurrent[, 3]) - 0.9) < 0.05,
          mean(endpoints[, 2]) < 0.08,
          abs(mean(endpoints[, 3]) - 0.8) < 0.04)
if (length(args)) {
  stopifnot(packageVersion("exdqlm") == "1.1.2")
  dynamic <- do.call(rbind, lapply(1:3, function(seed) {
    env <- run_article("dynamic-quantile-models-exdqlm", 31415L, seed)
    c(seed = seed, RMSE = env$forecast_rmse,
      coverage = env$scores$fraction_below[1], discount = env$discount)
  }))
  print(dynamic)
  stopifnot(mean(dynamic[, 2]) < 0.35,
            abs(mean(dynamic[, 3]) - 0.85) < 0.12)
}
cat("PASS: fixed-seed recovery panel; all runs reported, no seed selection.\n")
