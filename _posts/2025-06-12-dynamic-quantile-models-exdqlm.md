---
layout: post
published: true
title: "Fitting and checking dynamic quantile models in R"
date: 2025-06-12
updated: 2026-10-27
last_modified_at: 2026-10-27
theme: Statistical software
tags: [quantile-regression, forecasting, exdqlm, r]
description: "Fit a trend-plus-seasonal quantile model with fixed evolution, inspect its diagnostics, and check forecasts against a known simulation target."
excerpt: "Fit a seasonal upper quantile, distinguish smoothed estimates from forecasts, and evaluate predictions against held-out observations and baseline models."
math: true
---

A conditional mean summarizes the expected response. An upper conditional quantile estimates a threshold exceeded with a specified probability. For a continuous distribution, the 85th percentile has 85% of the conditional probability below it. Forecast evaluation can assess both the estimated threshold and the frequency of observations below it.

The R package `exdqlm`, which I co-develop, fits time-varying quantile models. The example below uses its asymmetric Laplace special case to estimate an upper quantile of a seasonal series and evaluate eighty forecasts from a fixed cutoff. It covers component specification, computational diagnostics, and held-out evaluation; the software article describes the package's other methods.

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

The observations are Gaussian around the changing level, so the asymmetric Laplace distribution is a misspecified working likelihood. It is used to estimate the selected quantile. Accuracy at that quantile, accuracy of the full predictive distribution, and calibration of uncertainty summaries require separate assessments.

## Include both trend and seasonality

A local linear trend has two states: the current quantile level and its rate of change. Between observations, the model propagates the level by adding the slope, and propagates the slope unchanged, before allowing for evolution uncertainty. Its observation vector and evolution matrix are

$$
F = \begin{pmatrix}1\\0\end{pmatrix},
\qquad
G = \begin{pmatrix}1 & 1\\0 & 1\end{pmatrix}.
$$

The quantity $$F^\top\theta_t$$ is the modeled quantile of the observation distribution conditional on the state. `polytrendMod(order = 2)` builds the trend block. A second, two-state Fourier block represents the known periodic component. Omitting it would force a local trend to extrapolate through seasonal turning points, even though the simulation explicitly contains a repeating cycle.

The initial mean below centers the level on the empirical upper quantile of the first twenty training observations and sets the slope and seasonal states to zero. This initialization uses training data rather than an independently elicited prior mean. The fitted quantile combines the trend level and active seasonal coordinate through the full observation vector.

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

The quantile state changes through its trend and seasonal rotation, with no additional random evolution shocks in this restricted example. Changing slopes or seasonal amplitudes would require a different specification. Select adaptivity within training data across enough origins to assess variation in validation scores. A seasonal period not supplied by the task must also be estimated without final test observations.

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

The trace records the evidence lower bound, scale, and changes used in the stopping criteria. Distinguish termination at an iteration limit from satisfaction of those criteria. Objective stability alone does not establish accuracy of variational uncertainty estimates; comparisons with MCMC and repeated simulations can assess those estimates on manageable cases.

The historical state estimates stored in `fit$theta.out$sm` are **smoothed**: they use all 800 training observations. They describe the training period, not forecasts available at each historical time. Even filtered states from a full-sample fit can depend on global parameters estimated with later observations. Historical forecast evaluation therefore requires fitting and preprocessing that respect each origin's information set.

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

The seasonal component propagates the fitted cycle through the forecast period. Its amplitude and phase, together with the trend and scale, are estimated from training observations. The known simulation target is used only to measure recovery after fitting.

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

The recent-cycle baseline holds the empirical 85th quantile of the last eighty training observations constant over the forecast period. A second baseline fits a linear trend plus sine and cosine terms by least squares, then adds the empirical 85th quantile of the training residuals. This specification represents the simulation's fixed coefficients and additive homoscedastic noise. Both baselines use base R, and all methods use the same cutoff and eighty verification observations.

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

Check loss evaluates predictions against realized responses. Target RMSE measures error relative to the known conditional quantile, which differs from the individual noisy observations. Even the known quantile has a random fraction of verification observations below it. Report this fraction without adjusting forecasts after examining test outcomes.

The reference fit converges in 43 iterations. Forecast target RMSE is **0.0801**, compared with observation-noise standard deviation 0.8. The estimated quantile has **81.25%** of verification responses below it, versus **83.75%** for the known target in this sample. Mean check losses are **0.1882** for the seasonal model and **0.1842** for harmonic regression. These results describe recovery of the seasonal pattern and the remaining estimation error in this simulation.


Static harmonic regression represents the constant-coefficient generating mechanism, so it provides a relevant comparison for this example. Results from one series and one forecast origin do not establish general model rankings or calibrated posterior uncertainty. The forecast errors share a fitted model and origin; repeated simulations and horizon-specific results are needed to assess variability across forecasting settings.

The package diagnostics also return a CRPS approximation computed from predictive draws using a finite grid of quantile scores. It assesses the working model's response distribution. Since that distribution is misspecified here, target-quantile check loss is the primary comparison. Predictive scores and exceedance counts do not assess posterior credible-interval coverage for the quantile curve.

## What to change for an application

Start with a forecasting cutoff and the information available there. Choose trend, seasonal, or regression components for the question at hand. Any discount-factor selection, scaling, or covariate processing should occur inside the training period, using an inner validation period if necessary. For repeated forecasting, rebuild that information set at each origin.

Assess computational diagnostics and forecast performance separately. Compare approximations on manageable cases and include baseline forecasts. Systematic upper-tail errors require examination of the state dynamics, working likelihood, scale, and predictors. Fitting several quantile levels also requires checks for crossings and a specification of how the fitted quantiles will be combined into a predictive summary.

The [companion software article](https://arxiv.org/abs/2607.22760) describes the broader package workflow and its methodological foundations. The [released source and manual](https://CRAN.R-project.org/package=exdqlm) document the interfaces used here. The complete calculation can also be rerun with the [example runner](https://github.com/AntonioAPDL/antonio-aguirre.github.io/blob/main/scripts/run_exdqlm_blog_example.R) from this website repository.

## References

- De Leon, A., Barata, R., Prado, R., and Sanso, B. [exdqlm: An R Package for Estimation and Analysis of Flexible Dynamic Quantile Linear Models](https://arxiv.org/abs/2607.22760). arXiv preprint; software article submitted to the Journal of Statistical Software.
- Barata, R., Prado, R., and Sanso, B. [Fast inference for time-varying quantiles via flexible dynamic models with application to the characterization of atmospheric rivers](https://doi.org/10.1214/21-AOAS1497). Annals of Applied Statistics.
- Koenker, R. and Bassett, G. [Regression quantiles](https://doi.org/10.2307/1913643). Econometrica, 1978.
- Gneiting, T. and Raftery, A. E. [Strictly proper scoring rules, prediction, and estimation](https://doi.org/10.1198/016214506000001437). Journal of the American Statistical Association, 2007.
- [exdqlm on CRAN](https://CRAN.R-project.org/package=exdqlm), including the reference manual and source release.
