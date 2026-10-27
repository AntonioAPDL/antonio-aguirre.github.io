---
layout: post
published: true
title: "Fitting and checking dynamic quantile models in R"
date: 2026-10-27
updated: 2026-10-27
theme: Statistical software
tags: [quantile-regression, forecasting, exdqlm, r]
description: "Fit a trend-plus-seasonal quantile model with fixed evolution, inspect its diagnostics, and check forecasts against a known simulation target."
excerpt: "A fitted quantile curve and a forecast answer different questions. This example keeps the distinction explicit and checks an upper-quantile forecast against a simple baseline."
math: true
---

A forecast of the mean describes the center of a distribution. If the question concerns unusually high values, an upper conditional quantile can be more useful. An 85th quantile is a threshold with 85% of the conditional distribution below it, assuming a continuous distribution. That interpretation provides a target to estimate and a property to check.

The R package `exdqlm`, which I co-develop, fits quantile models with coefficients that evolve through time. This note simulates a changing seasonal series, fits its upper quantile using trend and seasonal components, and evaluates eighty forecasts made from the end of the training period. The example uses the asymmetric Laplace special case of the package. It is a starting point for understanding the workflow, rather than a demonstration of every feature.

## A series with a known quantile

Simulated data let us separate the target from its estimate. Here the observations have a smooth, changing level and independent Gaussian noise with standard deviation 0.8. The conditional 85th quantile is therefore the level plus `0.8 * qnorm(0.85)`. In an application that curve would be unknown.

The code below was run with `exdqlm` 1.1.2 and R 4.5.3. The package requires compilation when installed from source; CRAN also provides binaries for supported systems.

```r
# Run once if needed:
# install.packages("exdqlm", repos = "https://cloud.r-project.org")
library(exdqlm)
stopifnot(packageVersion("exdqlm") >= "1.1.2")

set.seed(31415)
t <- seq_len(880)
level <- 0.02 * t + 0.7 * sin(2 * pi * t / 80)
y <- level + rnorm(length(t), sd = 0.8)
p0 <- 0.85
true_quantile <- level + 0.8 * qnorm(p0)

n_train <- 800L
train_index <- seq_len(n_train)
test_index <- (n_train + 1L):length(y)
y_train <- y[train_index]
y_test <- y[test_index]
```

The split comes before fitting. Ten complete cycles, observations 1 through 800, provide enough training data to estimate an upper quantile and seasonal coefficients with reasonable precision. Observations 801 through 880 are reserved for final evaluation. The period of 80 is treated as known, as a calendar period might be in an application; the seasonal amplitude and phase are estimated. The known quantile curve is excluded from fitting. Its role is to help interpret recovery after the fit.

These data do not follow an asymmetric Laplace observation model. That is deliberate: the example uses it as a working likelihood for estimating a quantile. This does not make the rest of the fitted response distribution correct. Quantile accuracy, predictive-distribution accuracy, and uncertainty calibration need separate checks.

## Include both trend and seasonality

A local linear trend has two states: the current quantile level and its rate of change. Between observations, the model propagates the level by adding the slope, and propagates the slope unchanged, before allowing for evolution uncertainty. Its observation vector and evolution matrix are

$$
F = \begin{pmatrix}1\\0\end{pmatrix},
\qquad
G = \begin{pmatrix}1 & 1\\0 & 1\end{pmatrix}.
$$

The quantity $$F^\top\theta_t$$ is the modeled quantile of the observation distribution conditional on the state. `polytrendMod(order = 2)` builds the trend block. A second, two-state Fourier block represents the known periodic component. Omitting it would force a local trend to extrapolate through seasonal turning points, even though the simulation explicitly contains a repeating cycle.

The initial mean below centers the level on the empirical upper quantile of the first twenty training observations and sets the slope and seasonal states to zero. This is a training-informed initialization, not an independently elicited prior. The fitted quantile is the sum of the trend level and the active seasonal coordinate, not just the first state.

```r
model <- polytrendMod(
  order = 2,
  m0 = c(unname(quantile(y_train[1:20], p0)), 0),
  C0 = diag(c(4, 0.05))
) + seasMod(p = 80, h = 1, m0 = c(0, 0), C0 = diag(2))

check_loss <- function(y, q, p) {
  u <- y - q
  mean(u * (p - (u < 0)))
}
discount <- 1

set.seed(2718)
fit <- exdqlmLDVB(
  y = y_train, p0 = p0, model = model,
  df = discount, dim.df = 4,
  dqlm.ind = TRUE, sig.init = 0.3,
  tol = 1e-4, n.samp = 1000, verbose = FALSE
)
```

`dim.df = 4` assigns all four states to one discount block. The discount factor controls evolution uncertainty. Values below one allow adaptation; one gives deterministic state evolution between observations while retaining uncertainty about the unknown states. The choice **one** matches this toy's fixed slope and seasonal coefficients. It is a structural choice for the stated simulation, not a discount selected to improve its test score.

The quantile state still changes through its trend and seasonal rotation, but there are no additional random evolution shocks in this restricted example. A series with changing slope or seasonal amplitude would need a different specification. Choose such adaptivity inside training data, using enough forecast origins to assess stability; one or two validation windows can favor noise. A seasonal period not supplied by the task must likewise be learned without final test observations.

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

The trace includes the evidence lower bound, scale, and changes in the quantities used for stopping. An iteration limit should prompt investigation rather than be silently reported as convergence. Likewise, a stable objective does not establish that a variational approximation has the right uncertainty. Comparisons with MCMC on small cases and repeated simulation studies answer questions that a stopping flag cannot.

The historical state estimates stored in `fit$theta.out$sm` are **smoothed**: they use all 800 training observations. They can describe the training period, but they are not forecasts that could have been issued at each historical time. Even filtered states from a full-sample fit can use global parameters estimated with later observations. An honest historical forecasting study requires origin-specific fitting and preprocessing.

## Forecast from the training cutoff

Now propagate the fitted model eighty steps ahead. The test observations are not arguments to `predict()`. The combined model's design and evolution matrices stay constant, so the future matrices equal those used in fitting. The seasonal rotation in the evolution matrix carries the cycle forward without access to future responses.

```r
forecast <- predict(
  fit, start.t = n_train, k = length(y_test),
  fFF = model$FF, fGG = model$GG,
  return.draws = TRUE, n.samp = 1000, seed = 1618
)

stopifnot(length(forecast$ff) == length(y_test))
stopifnot(identical(dim(forecast$samp.fore), c(80L, 1000L)))
```

The field `ff` contains forecast means of the quantile state. `samp.fore` contains simulated future **observations** under the fitted working model. They are different outputs. In particular, a posterior mean of a conditional quantile need not equal the same quantile of a distribution that integrates over state and parameter uncertainty.

<figure>
  <a href="/public/images/blog/exdqlm-dynamic-quantile-example.png" target="_blank" rel="noopener noreferrer" aria-label="Open forecast comparison at full size">
    <img src="/public/images/blog/exdqlm-dynamic-quantile-example.png" alt="The final two training cycles of simulated seasonal data and eighty forecasts after observation 800, compared with the known 85th quantile." loading="lazy" width="1400" height="800">
  </a>
  <figcaption>Simulated data: the final two training cycles and one full forecast cycle. Green shows smoothed training estimates; blue shows forecast quantile-state means. The dashed gold curve is the known simulation target. The figure has no response prediction band.</figcaption>
</figure>

The forecast now has a component capable of representing the cycle used in this toy problem. Its unknown amplitude, phase, trend, and scale are learned from training observations. The known target remains an evaluation reference, not a value substituted into the fitted forecast.

The following plotting block reproduces the figure. Its default output is a temporary directory; set `EXDQLM_BLOG_FIGURE_DIR` to choose another location.

```r
figure_dir <- Sys.getenv("EXDQLM_BLOG_FIGURE_DIR", unset = tempdir())
dir.create(figure_dir, recursive = TRUE, showWarnings = FALSE)
png(file.path(figure_dir, "exdqlm-dynamic-quantile-example.png"),
    width = 1400, height = 800, res = 150, bg = "white")
par(mar = c(4, 4.2, 1.2, 1), las = 1, family = "sans",
    fg = "#263238", col.axis = "#263238", col.lab = "#263238")
shown <- (n_train - 159L):length(y)
plot(t[shown], y[shown], type = "n", xlab = "Observation", ylab = "Value",
     ylim = range(y[shown], true_quantile[shown], forecast$ff))
rect(n_train + 0.5, par("usr")[3], max(t), par("usr")[4],
     col = "#EDF5FA", border = NA)
points(t[shown], y[shown], pch = 16, cex = 0.5, col = "#65737E")
lines(t[shown], true_quantile[shown], col = "#9B7400", lwd = 2, lty = 2)
smoothed_quantile <- drop(t(model$FF) %*% fit$theta.out$sm)
visible_train <- intersect(train_index, shown)
lines(visible_train, smoothed_quantile[visible_train], col = "#25734A", lwd = 2)
lines(c(n_train, test_index),
      c(tail(smoothed_quantile, 1), forecast$ff),
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

The recent-cycle baseline holds the empirical 85th quantile of the last eighty training observations constant. Its window spans one complete cycle. A stronger baseline fits a linear trend plus sine and cosine terms by least squares, then adds the empirical 85th quantile of its training residuals. This is appropriate for the homoscedastic additive-noise simulation and requires only base R. All methods use the same cutoff and are scored on the same eighty observations.

```r
baseline <- rep(unname(quantile(tail(y_train, 80), p0)), length(y_test))
harmonic_design <- function(index) {
  cbind(1, index, sin(2 * pi * index / 80), cos(2 * pi * index / 80))
}
harmonic_fit <- lm.fit(harmonic_design(train_index), y_train)
harmonic_forecast <- drop(harmonic_design(test_index) %*% harmonic_fit$coefficients) +
  unname(quantile(harmonic_fit$residuals, p0))
scores <- data.frame(
  method = c("Trend plus seasonality", "Harmonic regression", "Recent-cycle quantile"),
  mean_check_loss = c(check_loss(y_test, forecast$ff, p0),
                      check_loss(y_test, harmonic_forecast, p0),
                      check_loss(y_test, baseline, p0)),
  fraction_below = c(mean(y_test <= forecast$ff),
                    mean(y_test <= harmonic_forecast),
                    mean(y_test <= baseline))
)
print(scores, row.names = FALSE, digits = 4)
forecast_rmse <- sqrt(mean((forecast$ff - true_quantile[test_index])^2))
oracle_fraction <- mean(y_test <= true_quantile[test_index])
print(c(target_RMSE = forecast_rmse, oracle_fraction_below = oracle_fraction))

forecast_checks <- diagnostics(forecast, y = y_test)
stopifnot(isTRUE(all.equal(scores$mean_check_loss[1],
                          forecast_checks$m1.check_loss)))
```

Check loss measures errors against actual responses; target RMSE measures recovery of the known conditional quantile. A good upper-quantile estimate should follow that target, not pass through the noisy observations. The oracle fraction below its own quantile is also random in a finite verification sample. Exact empirical agreement with 0.85 should not be forced by changing the fitted forecasts after seeing test outcomes.

The reference fit converges in 43 iterations. Forecast target RMSE is **0.0801**, compared with observation-noise standard deviation 0.8. The estimated quantile has **81.25%** of verification responses below it, versus **83.75%** for the known target in this sample. Mean check losses are **0.1882** for the seasonal model and **0.1842** for harmonic regression. The curve recovers the seasonal pattern, but finite-sample estimation and tail errors remain; those should be reported rather than adjusted away after verification.


The harmonic regression is a meaningful comparator, not a method the dynamic model must beat to validate this example. Constant coefficients are sufficient for the generating mechanism, so a static harmonic model can be competitive. This remains one series and one final forecast origin, not evidence of general superiority or calibrated posterior uncertainty. The errors share the same fitted model and origin. Assess repeated simulations, inspect performance by horizon, and quantify variability before drawing broader conclusions.

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
