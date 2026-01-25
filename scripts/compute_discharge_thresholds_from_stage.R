#!/usr/bin/env Rscript

# Compute discharge thresholds from stage values using the USGS rating curve.
# Usage:
#   Rscript scripts/compute_discharge_thresholds_from_stage.R 11160500 16.5 19.5 21.76

args <- commandArgs(trailingOnly = TRUE)
site_number <- if (length(args) >= 1) args[[1]] else "11160500"
stage_values <- if (length(args) >= 2) as.numeric(args[2:length(args)]) else c(16.5, 19.5, 21.76)
stage_values <- stage_values[!is.na(stage_values)]

if (!length(stage_values)) {
  stop("No valid stage inputs provided.", call. = FALSE)
}

if (!requireNamespace("dataRetrieval", quietly = TRUE)) {
  stop("Package 'dataRetrieval' is required. Install with install.packages('dataRetrieval').", call. = FALSE)
}

suppressPackageStartupMessages(library(dataRetrieval))

rating <- readNWISrating(siteNumber = site_number)

if (!all(c("INDEP", "DEP") %in% names(rating))) {
  stop("Unexpected rating curve format: missing INDEP/DEP columns.", call. = FALSE)
}

rating <- rating[order(rating$INDEP), ]
discharge <- approx(rating$INDEP, rating$DEP, xout = stage_values, rule = 2)$y

out <- data.frame(
  stage_ft = stage_values,
  discharge_cfs = discharge
)

print(out, row.names = FALSE)

retrieved <- attr(rating, "retrieved")
if (is.null(retrieved)) {
  retrieved <- Sys.Date()
}
cat("\nRating retrieval date:", retrieved, "\n")
