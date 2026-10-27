---
layout: post
published: true
title: "Checking quantile forecasts across levels and horizons"
date: 2025-12-04
updated: 2026-10-27
last_modified_at: 2026-10-27
theme: Forecast evaluation
tags: [forecasting, quantile-regression, calibration, scoring-rules]
description: "Use check loss, calibration diagnostics, crossing checks, and horizon-specific comparisons to evaluate quantile forecasts."
excerpt: "A forecast can have plausible overall coverage and still be wrong at particular horizons or in particular conditions."
math: true
---

A model can produce a smooth set of quantile forecasts and still make poor predictions. Numerical convergence tells us whether a computation has settled according to its stopping rule. It does not tell us whether the forecast target is estimated accurately, whether the forecast uses only available information, or whether its uncertainty is calibrated.

In comparing forecasting methods, I find it useful to keep three questions separate: What information was available? What object was predicted? How was that object evaluated? This note develops a small example for quantile forecasts. The calculations use known Gaussian distributions rather than fitted models, making the evaluation mechanics easier to inspect.

## Define an evaluation row

A row should identify a forecast origin, a horizon, a verifying observation, and the predictions being compared. All methods should be scored on the same eligible rows. If a source is missing on some dates, either restrict the comparison to common support or report the different support explicitly. Otherwise a difference attributed to the method may be a difference in which cases were evaluated.

For a time series, random train-test shuffling usually does not reproduce the prediction task. Scaling, feature selection, tuning, and coefficient estimation must respect the information available at each origin. Rolling evaluation can incorporate newly observed responses, but that update rule must be the same one the application would permit. [The fixed-feature example]({{ '/2025/09/09/fixed-recurrent-quantile-features/' | relative_url }}) illustrates rolling one-step prediction, not a long forecast from a single origin.

## Use a score that matches the target

For a conditional quantile at level $$p$$, check loss is

$$
\rho_p(y-q)=(y-q)\{p-\mathbf{1}(y<q)\}.
$$

Lower is better. Under the usual regularity conditions, expected check loss is minimized by a true quantile at that level. An upper-quantile miss receives a different penalty from an error of the same size in the other direction. Squared error instead targets a conditional mean; it is not a replacement for this comparison.

```r
set.seed(1847)
levels <- c(0.1, 0.5, 0.9)
horizons <- 1:6
replicates <- 800L
h <- rep(horizons, each = replicates)
sigma <- sqrt(h)
y <- rnorm(length(h), sd = sigma)
correct <- outer(sigma, qnorm(levels))
biased <- correct + 0.6 * sigma
check <- function(u, p) u * (p - (u < 0))
score <- function(Q) {
  residual <- matrix(y, nrow(Q), ncol(Q)) - Q
  loss <- sweep(residual, 2, levels, function(u, p) check(u, p))
  list(loss = loss, coverage = colMeans(y <= Q),
       by_horizon = tapply(rowMeans(loss), h, mean))
}
good <- score(correct)
bad <- score(biased)
print(rbind(correct = good$coverage, biased = bad$coverage))
```

Each simulated case is independent here. Increasing the horizon increases its standard deviation. The second forecast shifts every quantile upward by 0.6 standard deviations. Neither forecast has been trained, and the comparison is not a claim about any research model. It simply makes a known defect visible through the diagnostics.

## Coverage and accuracy answer different questions

The fraction of observations below the estimated $$p$$ quantile should be near $$p$$ in a calibrated sequence. But aggregate agreement can conceal errors that cancel across seasons, regimes, groups, or horizons. A forecast that ignores useful covariates can also be marginally calibrated while being uninformative conditionally.

For that reason, inspect coverage by conditions relevant to the task, together with scores that account for error magnitude. In real rolling-origin evaluations, overlapping horizons create dependence. Binomial error bars assuming independent rows can be misleading. Uncertainty estimates need to reflect the sampling and dependence structure, for example through a justified block resampling design.

```r
figure_dir <- Sys.getenv("RESEARCH_BLOG_FIGURE_DIR", tempdir())
png(file.path(figure_dir, "checking-quantile-forecasts.png"),
    width = 1400, height = 800, res = 150)
par(mfrow = c(1, 2), mar = c(4, 4, 2, 1))
plot(levels, good$coverage, type = "b", pch = 16, col = "#25734A",
     xlim = c(0, 1), ylim = c(0, 1),
     xlab = "Nominal quantile level", ylab = "Fraction below forecast")
abline(0, 1, lty = 3, col = "#65737E")
lines(levels, bad$coverage, type = "b", pch = 17, col = "#176A94")
legend("topleft", c("Correct distribution", "Upward shift"),
       col = c("#25734A", "#176A94"), pch = c(16, 17), bty = "n", cex = 0.8)
plot(horizons, good$by_horizon, type = "b", pch = 16, col = "#25734A",
     ylim = range(good$by_horizon, bad$by_horizon),
     xlab = "Forecast horizon", ylab = "Mean check loss across three levels")
lines(horizons, bad$by_horizon, type = "b", pch = 17, col = "#176A94")
dev.off()
```

<figure>
  <a href="{{ '/public/images/blog/checking-quantile-forecasts.png' | relative_url }}"><img src="{{ '/public/images/blog/checking-quantile-forecasts.png' | relative_url }}" alt="Calibration fractions for correct and shifted Gaussian quantiles, and their mean check losses at six horizons." width="1400" height="800" loading="lazy"></a>
  <figcaption>Independent simulated cases. The diagonal is the calibration reference. Scores increase with horizon partly because the simulated response scale increases; compare methods within the same horizon.</figcaption>
</figure>

## Check ordering before interpreting a quantile curve

Quantiles must be nondecreasing in their probability level. Separately estimated regressions can cross. On an equally spaced grid, sorting each forecast vector provides a discrete rearrangement. Keep the original crossing diagnostic and apply the same stated reporting rule to all methods.

```r
crossed <- rbind(c(-1, 0.4, 0.2), c(-0.5, 0, 1))
has_crossing <- apply(crossed, 1, function(z) any(diff(z) < 0))
rearranged <- t(apply(crossed, 1, sort))
stopifnot(identical(has_crossing, c(TRUE, FALSE)),
          all(apply(rearranged, 1, function(z) all(diff(z) >= 0))))
```

Sorting is not joint Bayesian estimation. It does not create posterior dependence between independently fitted levels, repair an incorrect uncertainty calculation, or prove calibration. For irregular probability grids, an unweighted sort is not the corresponding probability-weighted rearrangement. A finite set of ordered quantiles also leaves interpolation and tail behavior unspecified.

## Be precise about CRPS

For a distribution with quantile function $$Q$$ and finite first moment,

$$
\operatorname{CRPS}(F,y)=2\int_0^1\rho_p\{y-Q(p)\}\,dp.
$$

A prespecified positively weighted sum at a finite set of levels is a valid quantile-vector score. It is not automatically the full-distribution CRPS. A numerical approximation to this integral needs probability weights and adequate tail resolution. Here a dense midpoint grid can be checked against a standard-normal closed form.

```r
grid <- (seq_len(20000L) - 0.5) / 20000L
observation <- 0.7
approx_crps <- 2 * mean(check(observation - qnorm(grid), grid))
exact_crps <- observation * (2 * pnorm(observation) - 1) +
  2 * dnorm(observation) - 1 / sqrt(pi)
residual <- matrix(y, nrow(correct), ncol(correct)) - correct
independent <- sweep(residual, 2, levels, function(u, p)
  ifelse(u >= 0, p * u, (1 - p) * -u))
stopifnot(max(abs(independent - good$loss)) < 1e-12,
          abs(approx_crps - exact_crps) < 1e-4,
          identical(dim(good$loss), c(4800L, 3L)),
          all(is.finite(bad$by_horizon)))
print(c(approx_crps = approx_crps, exact_crps = exact_crps))
example_verified <- TRUE
```

Choose the levels, weights, horizon aggregation, and missing-data rule before inspecting the final comparison. Report horizon-specific differences when a pooled score would hide an important weakness. A small average improvement with substantial uncertainty should remain a small, uncertain improvement in the written conclusion.

Finally, marginal quantile scores do not validate a joint future trajectory. Two forecasts can have identical quantiles at every horizon and different temporal dependence. Path-dependent decisions require additional evaluation of the joint prediction object. The same principle applies throughout: validate the object actually used, rather than treating one favorable diagnostic as a general certificate.

## References

- Gneiting, T., and Raftery, A. E. (2007). Strictly proper scoring rules, prediction, and estimation. [JASA](https://doi.org/10.1198/016214506000001437).
- Chernozhukov, V., Fernandez-Val, I., and Galichon, A. (2010). Quantile and probability curves without crossing. [Econometrica](https://doi.org/10.3982/ECTA7880).
- De Leon, A., Prado, R., and Sanso, B. *Bayesian Quantile Deep Echo State Networks for Nonlinear Time Series*. [arXiv:2609.17579, version 1](https://arxiv.org/abs/2609.17579v1).
