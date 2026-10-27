#!/usr/bin/env Rscript
# Execute the examples exactly as published, in separate environments.
args <- commandArgs(trailingOnly = TRUE)
file_arg <- grep("^--file=", commandArgs(), value = TRUE)
root <- dirname(dirname(normalizePath(sub("^--file=", "", file_arg[[1L]]))))
slugs <- c("fixed-recurrent-quantile-features", "checking-quantile-forecasts",
           "same-content-different-intervals", "tolerance-intervals",
           "interval-endpoint-regression")
figure_arg <- grep("^--figure-dir=", args, value = TRUE)
selected <- args[!startsWith(args, "--figure-dir=")]
if (length(figure_arg) > 1L || any(!selected %in% slugs)) {
  stop("Usage: Rscript scripts/run_research_blog_examples.R [SLUG ...] [--figure-dir=PATH]")
}
if (length(figure_arg)) {
  figure_dir <- sub("^--figure-dir=", "", figure_arg)
  if (!nzchar(figure_dir)) stop("Figure directory cannot be empty.")
  Sys.setenv(RESEARCH_BLOG_FIGURE_DIR = normalizePath(figure_dir, mustWork = TRUE))
}
if (!length(selected)) selected <- slugs
for (slug in selected) {
  post <- file.path(root, "_posts", paste0("2026-10-27-", slug, ".md"))
  lines <- readLines(post, warn = FALSE)
  env <- new.env(parent = globalenv())
  in_r <- FALSE
  block <- character()
  count <- 0L
  for (line in lines) {
    if (!in_r && identical(line, "```r")) {
      in_r <- TRUE
      block <- character()
    } else if (in_r && identical(line, "```")) {
      eval(parse(text = block), envir = env)
      in_r <- FALSE
      count <- count + 1L
    } else if (in_r) {
      block <- c(block, line)
    }
  }
  stopifnot(!in_r, count > 0L, isTRUE(env$example_verified))
  switch(slug,
    "fixed-recurrent-quantile-features" = {
      stopifnot(max(env$train) < min(env$test),
                identical(as.numeric(env$center), mean(env$y[1:env$n_train])),
                identical(dim(env$H), c(2000L, 12L)),
                abs(env$scores[1] - 0.1077158) < 1e-5,
                abs(env$scores[2] - 0.1176063) < 1e-5,
                env$recovery["target_RMSE"] < 0.25,
                abs(env$recovery["fraction_below"] - env$p) < 0.06)
    },
    "checking-quantile-forecasts" = {
      stopifnot(max(abs(env$good$coverage - c(0.1025, 0.5064583333, 0.90125))) < 1e-9,
                abs(env$exact_crps - 0.4215692) < 1e-6)
    },
    "same-content-different-intervals" = {
      stopifnot(abs(env$summary$width[1] - log(5)) < 1e-10,
                abs(env$summary$retained_mean[3] - 1) < 1e-9)
    },
    "tolerance-intervals" = {
      stopifnot(env$d == 88L, abs(env$bound[env$d] - 0.990791) < 1e-6,
                abs(env$success - 0.994) < 1e-12)
    },
    "interval-endpoint-regression" = {
      stopifnot(nrow(env$grid) == 68921L,
                abs(sum(env$weight * env$grid$intercept) - 0.5088470) < 1e-6,
                sum(env$weight[env$boundary]) < 1e-6,
                env$endpoint_RMSE < 0.08,
                abs(env$heldout_content - env$content) < 0.06,
                abs(env$population_content - env$content) < 0.04)
    }
  )
  cat(sprintf("PASS: %s; %d R blocks and embedded numerical checks.\n", slug, count))
}
cat(R.version.string, "\n")
if ("fixed-recurrent-quantile-features" %in% selected) {
  cat("quantreg:", as.character(packageVersion("quantreg")), "\n")
}
