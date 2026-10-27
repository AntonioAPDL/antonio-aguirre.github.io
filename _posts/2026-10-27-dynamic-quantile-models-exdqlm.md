---
layout: post
published: true
title: "Fitting and checking dynamic quantile models in R"
date: 2026-10-27
updated: 2026-10-27
theme: Statistical software
tags: [quantile-regression, forecasting, exdqlm, r]
description: "A worked exdqlm example: specify a dynamic quantile model, inspect its numerical diagnostics, and evaluate forecasts on observations kept outside the fit."
excerpt: "A fitted quantile curve and a forecast answer different questions. This example keeps the distinction explicit and checks an upper-quantile forecast against a simple baseline."
math: true
---

A forecast of the mean describes the center of a distribution. If the question concerns unusually high values, an upper conditional quantile can be more useful. An 85th quantile is a threshold with 85% of the conditional distribution below it, assuming a continuous distribution. That interpretation provides a target to estimate and a property to check.

The R package `exdqlm`, which I co-develop, fits quantile models with coefficients that evolve through time. This note works through one small example: simulate a changing series, fit a dynamic trend to its upper quantile, and evaluate twenty forecasts made from the end of the training period. The example uses the asymmetric Laplace special case of the package. It is a starting point for understanding the workflow, rather than a demonstration of every feature.

## A series with a known quantile

Simulated data let us separate the target from its estimate. Here the observations have a smooth, changing level and independent Gaussian noise with standard deviation 0.8. The conditional 85th quantile is therefore the level plus `0.8 * qnorm(0.85)`. In an application that curve would be unknown.

The code below was run with `exdqlm` 1.1.2 and R 4.5.3. The package requires compilation when installed from source; CRAN also provides binaries for supported systems.

```r
# Run once if needed:
# install.packages("exdqlm", repos = "https://cloud.r-project.org")
library(exdqlm)
stopifnot(packageVersion("exdqlm") >= "1.1.2")

set.seed(31415)
t <- seq_len(180)
level <- 0.02 * t + 0.7 * sin(2 * pi * t / 80)
y <- level + rnorm(length(t), sd = 0.8)
p0 <- 0.85
true_quantile <- level + 0.8 * qnorm(p0)

n_train <- 160L
train_index <- seq_len(n_train)
test_index <- (n_train + 1L):length(y)
y_train <- y[train_index]
y_test <- y[test_index]
```

The split comes before fitting. Observations 161 through 180 will be used only for evaluation. The known simulation curve is also excluded from model construction and fitting; its role is to help interpret the final figure.

These data do not follow an asymmetric Laplace observation model. That is deliberate: the example uses it as a working likelihood for estimating a quantile. This does not make the rest of the fitted response distribution correct. Quantile accuracy, predictive-distribution accuracy, and uncertainty calibration need separate checks.

## Let the quantile have a level and a slope

A local linear trend has two states: the current quantile level and its rate of change. Between observations, the model propagates the level by adding the slope, and propagates the slope unchanged, before allowing for evolution uncertainty. Its observation vector and evolution matrix are

$$
F = \begin{pmatrix}1\\0\end{pmatrix},
\qquad
G = \begin{pmatrix}1 & 1\\0 & 1\end{pmatrix}.
$$

The quantity $$F^\top\theta_t$$ is the modeled quantile of the observation distribution conditional on the state. `polytrendMod(order = 2)` builds this specification. The initial mean below centers the level on the empirical upper quantile of the first twenty training observations and sets the slope to zero. This is a training-informed initialization, not an independently elicited prior.

```r
model <- polytrendMod(
  order = 2,
  m0 = c(unname(quantile(y_train[1:20], p0)), 0),
  C0 = diag(c(4, 0.05))
)

set.seed(2718)
fit <- exdqlmLDVB(
  y = y_train, p0 = p0, model = model,
  df = 0.98, dim.df = 2,
  dqlm.ind = TRUE, sig.init = 0.3,
  tol = 1e-4, n.samp = 1000, verbose = FALSE
)
```

The discount factor `df` controls how much evolution uncertainty is allowed. Values closer to one generally make the state less adaptive; smaller values allow more change. `dim.df = 2` assigns both states to one discount block. The choice 0.98 is fixed for this example, with no selection using the test observations.

`dqlm.ind = TRUE` fixes the extra shape parameter to zero, giving the asymmetric Laplace/DQLM special case. The scale is estimated: `sig.init` is an initial value, not a fixed scale, and is not the Gaussian standard deviation used to generate the data. The unrestricted exAL model is available without this restriction, but adds a shape parameter and more computation to inspect.

## Check what stopped the algorithm

`exdqlmLDVB()` uses variational inference. A returned object alone does not establish that the numerical stopping criteria were met. Inspect both the status and the final iteration trace:

```r
convergence <- fit$diagnostics$convergence
print(convergence[c("converged", "stop_reason", "iter")])
trace <- fit$diagnostics$vb_trace
print(tail(trace[, c("iter", "elbo", "sigma",
                    "delta_state", "delta_sigma", "delta_elbo")], 3))
stopifnot(isTRUE(convergence$converged))
```

In the reference run the algorithm met its joint criteria after 31 iterations. The trace includes the evidence lower bound, scale, and changes in the quantities used for stopping. An iteration limit should prompt investigation rather than be silently reported as convergence. Likewise, a stable objective does not establish that a variational approximation has the right uncertainty. Comparisons with MCMC on small cases and repeated simulation studies answer questions that a stopping flag cannot.

The historical state estimates stored in `fit$theta.out$sm` are **smoothed**: they use all 160 training observations. They can describe the training period, but they are not forecasts that could have been issued at each historical time. Even filtered states from a full-sample fit can use global parameters estimated with later observations. An honest historical forecasting study requires origin-specific fitting and preprocessing.

## Forecast from the training cutoff

Now propagate the fitted model twenty steps ahead. The test observations are not arguments to `predict()`. Here the design and evolution matrices stay constant, so the future matrices equal those used in the trend model.

```r
forecast <- predict(
  fit, start.t = n_train, k = length(y_test),
  fFF = model$FF, fGG = model$GG,
  return.draws = TRUE, n.samp = 1000, seed = 1618
)

stopifnot(length(forecast$ff) == length(y_test))
stopifnot(identical(dim(forecast$samp.fore), c(20L, 1000L)))
```

The field `ff` contains forecast means of the quantile state. `samp.fore` contains simulated future **observations** under the fitted working model. They are different outputs. In particular, a posterior mean of a conditional quantile need not equal the same quantile of a distribution that integrates over state and parameter uncertainty.

<figure>
  <a href="/public/images/blog/exdqlm-dynamic-quantile-example.png" target="_blank" rel="noopener noreferrer" aria-label="Open forecast comparison at full size">
    <img src="/public/images/blog/exdqlm-dynamic-quantile-example.png" alt="Simulated observations and their known 85th quantile, with smoothed training estimates and twenty forecasts after the cutoff at observation 160." loading="lazy" width="1400" height="800">
  </a>
  <figcaption>Simulated data. Green shows smoothed training estimates; blue shows forecast quantile-state means. The dashed gold curve is the known simulation target. The figure has no response prediction band.</figcaption>
</figure>

The forecast continues a local trend. It does not know that the simulated level follows a sine wave. That mismatch is visible after the cutoff and is useful to examine rather than hide by changing the example after scoring it.

The following plotting block reproduces the figure. Its default output is a temporary directory; set `EXDQLM_BLOG_FIGURE_DIR` to choose another location.

```r
figure_dir <- Sys.getenv("EXDQLM_BLOG_FIGURE_DIR", unset = tempdir())
dir.create(figure_dir, recursive = TRUE, showWarnings = FALSE)
png(file.path(figure_dir, "exdqlm-dynamic-quantile-example.png"),
    width = 1400, height = 800, res = 150, bg = "white")
par(mar = c(4, 4.2, 1.2, 1), las = 1, family = "sans",
    fg = "#263238", col.axis = "#263238", col.lab = "#263238")
plot(t, y, type = "n", xlab = "Observation", ylab = "Value",
     ylim = range(y, true_quantile, forecast$ff))
rect(n_train + 0.5, par("usr")[3], max(t), par("usr")[4],
     col = "#EDF5FA", border = NA)
points(t, y, pch = 16, cex = 0.5, col = "#65737E")
lines(t, true_quantile, col = "#9B7400", lwd = 2, lty = 2)
lines(train_index, fit$theta.out$sm[1, ], col = "#25734A", lwd = 2)
lines(c(n_train, test_index),
      c(tail(fit$theta.out$sm[1, ], 1), forecast$ff),
      col = "#176A94", lwd = 2.5)
abline(v = n_train + 0.5, lty = 3, col = "#263238")
legend("topleft", bty = "n", cex = 0.85,
       legend = c("Observed", "Known 85th quantile", "Smoothed estimate",
                  "Forecast quantile mean"),
       col = c("#65737E", "#9B7400", "#25734A", "#176A94"),
       pch = c(16, NA, NA, NA), lty = c(NA, 2, 1, 1),
       lwd = c(NA, 2, 2, 2.5))
dev.off()
```

## Score the forecasts against a baseline

For a target level $$p$$, quantile check loss is

$$
\rho_p(y-q)=(y-q)\{p-\mathbf{1}(y<q)\}.
$$

Smaller average loss is better. At $$p=0.85$$, underpredicting by one unit costs 0.85, while overpredicting by one unit costs 0.15. This asymmetry is what makes the upper quantile, rather than the mean, the relevant target.

The baseline holds the empirical 85th quantile of the last forty training observations constant over the forecast horizon. Its window is specified before evaluation. Both methods use the same cutoff and are scored on the same twenty observations.

```r
check_loss <- function(y, q, p) {
  u <- y - q
  mean(u * (p - (u < 0)))
}
baseline <- rep(unname(quantile(tail(y_train, 40), p0)), length(y_test))
scores <- data.frame(
  method = c("Dynamic trend", "Recent-window quantile"),
  mean_check_loss = c(check_loss(y_test, forecast$ff, p0),
                      check_loss(y_test, baseline, p0)),
  fraction_below = c(mean(y_test <= forecast$ff),
                    mean(y_test <= baseline))
)
print(scores, row.names = FALSE, digits = 4)

forecast_checks <- diagnostics(forecast, y = y_test)
stopifnot(isTRUE(all.equal(scores$mean_check_loss[1],
                          forecast_checks$m1.check_loss)))
```

The reference run gives mean check losses of approximately **0.3955** for the dynamic trend and **0.6601** for the baseline. The dynamic model has the lower loss in this example. That is one result on one simulated series, not evidence of general superiority.

There is also a warning in the result: only **10 of the 20** test observations fall below the dynamic forecast. That is far from the target fraction 0.85. A model can improve on a weak baseline and still give poor upper-quantile forecasts. Twenty observations from one forecast origin are too little evidence for a general calibration claim; the errors also share the same fitted model and origin. Assess multiple origins, inspect performance by horizon, and quantify variability before drawing broader conclusions.

The package diagnostics also return a CRPS approximation computed from predictive draws using a finite grid of quantile scores. That assesses the working model's response distribution, not just the target quantile. Here the observation likelihood is deliberately misspecified, so the target-quantile check loss is the primary comparison. Neither a predictive score nor an exceedance count verifies posterior credible-interval coverage for the quantile curve.

## What to change for an application

Start with a forecasting cutoff and the information available there. Choose trend, seasonal, or regression components for the question at hand. Any discount-factor selection, scaling, or covariate processing should occur inside the training period, using an inner validation period if necessary. For repeated forecasting, rebuild that information set at each origin.

Then inspect computation and forecasting separately. Check stopping diagnostics, compare approximations on manageable cases, and retain simple baselines. If forecasts miss the upper tail, investigate the state dynamics, likelihood, scale, and relevant predictors rather than treating a successful numerical fit as the answer. Several separately fitted quantiles introduce additional issues, including crossings and predictive synthesis; those deserve their own example.

The [companion software article](https://arxiv.org/abs/2607.22760) describes the broader package workflow and its methodological foundations. The [released source and manual](https://CRAN.R-project.org/package=exdqlm) document the interfaces used here. The complete calculation can also be rerun with the [example runner](https://github.com/AntonioAPDL/antonio-aguirre.github.io/blob/main/scripts/run_exdqlm_blog_example.R) from this website repository.

## References

- De Leon, A., Barata, R., Prado, R., and Sanso, B. [exdqlm: An R Package for Estimation and Analysis of Flexible Dynamic Quantile Linear Models](https://arxiv.org/abs/2607.22760). arXiv preprint; software article submitted to the Journal of Statistical Software.
- Barata, R., Prado, R., and Sanso, B. [Fast inference for time-varying quantiles via flexible dynamic models with application to the characterization of atmospheric rivers](https://doi.org/10.1214/21-AOAS1497). Annals of Applied Statistics.
- Koenker, R. and Bassett, G. [Regression quantiles](https://doi.org/10.2307/1913643). Econometrica, 1978.
- Gneiting, T. and Raftery, A. E. [Strictly proper scoring rules, prediction, and estimation](https://doi.org/10.1198/016214506000001437). Journal of the American Statistical Association, 2007.
- [exdqlm on CRAN](https://CRAN.R-project.org/package=exdqlm), including the reference manual and source release.
