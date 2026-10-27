#!/usr/bin/env Rscript
# Execute the public article's R blocks rather than maintain a second example.
args <- commandArgs(trailingOnly = TRUE)
file_arg <- grep("^--file=", commandArgs(), value = TRUE)
script <- normalizePath(sub("^--file=", "", file_arg[[1L]]))
root <- dirname(dirname(script))
post <- Sys.glob(file.path(root, "_posts", "*-dynamic-quantile-models-exdqlm.md"))
if (length(post) != 1L) stop("Expected exactly one exdqlm tutorial.")
if (length(args) > 1L || (length(args) && !startsWith(args, "--figure-dir="))) {
  stop("Usage: Rscript scripts/run_exdqlm_blog_example.R [--figure-dir=PATH]")
}
if (!requireNamespace("exdqlm", quietly = TRUE) ||
    packageVersion("exdqlm") != "1.1.2") {
  stop("This reference run requires CRAN exdqlm 1.1.2; use an isolated R_LIBS if needed.")
}
if (length(args)) {
  path <- sub("^--figure-dir=", "", args)
  if (!nzchar(path)) stop("Figure directory cannot be empty.")
  Sys.setenv(EXDQLM_BLOG_FIGURE_DIR = path)
}
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
stopifnot(!in_r, count == 6L)
stopifnot(length(env$fit$y) == env$n_train,
          identical(as.numeric(env$fit$y), as.numeric(env$y_train)),
          identical(dim(env$fit$theta.out$sm), c(4L, 800L)),
          env$discount == 1,
          max(abs(env$smoothed_quantile -
            drop(t(env$model$FF) %*% env$fit$theta.out$sm))) < 1e-12,
          all(is.finite(env$forecast$ff)),
          all(is.finite(env$forecast$samp.fore)))

# An independent piecewise definition checks the reported quantile score.
u <- env$y_test - env$forecast$ff
independent <- mean(ifelse(u >= 0, env$p0 * u, (1 - env$p0) * -u))
stopifnot(isTRUE(all.equal(independent, env$scores$mean_check_loss[1])),
          env$forecast_rmse < 0.25,
          abs(env$forecast_rmse - 0.08005434) < 1e-6,
          abs(env$scores$fraction_below[1] - env$p0) < 0.12)
cat(sprintf("PASS: %d article R blocks executed; dimensions, training split, scores, and reference results verified.\n", count))
cat("R:", R.version.string, "\nexdqlm:", as.character(packageVersion("exdqlm")), "\n")
