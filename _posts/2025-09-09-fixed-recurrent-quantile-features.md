---
layout: post
published: true
title: "Quantile forecasting with fixed recurrent features"
date: 2025-09-09
updated: 2026-10-27
last_modified_at: 2026-10-27
theme: Prediction models
tags: [quantile-regression, recurrent-features, forecasting, r]
description: "Build fixed recurrent features, fit an upper-quantile readout, and evaluate rolling one-step predictions without using future observations."
excerpt: "Use fixed recurrent states as predictors in quantile regression, then evaluate one-step forecasts with training-only preprocessing."
math: true
---

A time series can depend nonlinearly on earlier observations. The effect of a lagged value may flatten, change direction, or depend on previous states. A recurrent feature map represents this history through a sequence of nonlinear states. Quantile regression can use those states to estimate selected parts of the conditional response distribution.

An echo state network separates **feature construction** from **readout estimation**. Its recurrent weights are fixed, and an output model is estimated using the resulting states. My Q-DESN research uses Bayesian readouts and can include several recurrent layers. The example here uses one layer and ordinary quantile regression to show how inputs become features and forecasts; it does not implement the paper's Bayesian model.

## Start with a target and a split

Suppose the next observation has a nonlinear conditional mean and a noise scale that increases with the magnitude of its most recent value. The simulation below gives us a known conditional 90th quantile. That known curve is available only because we generated the data; it will not be passed to either fitted model.

```r
library(quantreg) # Reference run: quantreg 6.1, R 4.5.3
set.seed(90210)
n <- 2000L
n_train <- 1600L
p <- 0.9
y <- numeric(n)
for (t in 2:n) {
  mu <- 0.45 * y[t - 1] + 0.8 * sin(y[t - 1])
  y[t] <- mu + rnorm(1, sd = 0.35 + 0.2 * abs(y[t - 1]))
}
center <- mean(y[1:n_train])
scale <- sd(y[1:n_train])
train <- 31:n_train
test <- (n_train + 1L):n
lagged <- c(0, head(y, -1))
truth <- 0.45 * lagged + 0.8 * sin(lagged) +
  (0.35 + 0.2 * abs(lagged)) * qnorm(p)
```

The split precedes feature construction and fitting. There are 1,600 training observations and 400 held-out observations. The centering and scaling constants use training observations only. This is appropriate for a model first fitted at observation 1,600; it would not be appropriate to describe those constants as available at the beginning of the series. The first thirty rows are excluded from both fits to allow the recurrent state to move away from its arbitrary zero initialization. The larger training sample helps estimate an upper quantile without relying on a handful of tail observations.

## Hold the recurrent map fixed

At each time, the state combines the previous state with a nonlinear transformation of that state and the most recent observed response. The leak parameter controls the mixture. The recurrent matrix is scaled once, and neither it nor the input matrix is optimized against the response.

```r
set.seed(210) # Feature-map randomness is separate from data generation.
units <- 12L
W <- matrix(rnorm(units^2, sd = 0.3), units)
radius <- max(Mod(eigen(W, only.values = TRUE)$values))
W <- 0.7 * W / radius
Win <- matrix(runif(units * 2, -0.6, 0.6), units, 2)
features <- function(z) {
  H <- matrix(0, length(z), units)
  state <- numeric(units)
  for (t in seq_along(z)) {
    previous <- if (t == 1L) 0 else z[t - 1L]
    input <- c(1, (previous - center) / scale)
    state <- 0.6 * state + 0.4 * tanh(W %*% state + Win %*% input)
    H[t, ] <- state
  }
  H
}
H <- features(y)
X <- cbind(1, (lagged - center) / scale, H)
X_linear <- cbind(1, lagged)
```

The feature recursion is causal in the forecasting sense: row $$t$$ uses responses only through $$t-1$$. Changing later observations must leave earlier feature rows unchanged. The code checks this property directly. A fixed random seed reproduces the feature map; its predictive adequacy is assessed through held-out evaluation.

The spectral radius 0.7 and leak 0.4 are example settings, not a general proof that initialization is forgotten under every input sequence. Larger reservoirs, deeper layers, and stronger persistence introduce additional choices. Those choices need training or validation data, not repeated consultation of the final test scores.

## Estimate the readout, not the reservoir

For a target level $$p$$, quantile regression minimizes the sum of check losses,

$$
\rho_p(u)=u\{p-\mathbf{1}(u<0)\}.
$$

The regression coefficients map each feature row to an estimated conditional quantile. The readout includes the original response lag alongside the recurrent states, allowing direct and nonlinear lag effects. A linear autoregression provides a baseline at the same target level, with identical training rows and available lag information.

```r
fit <- rq.fit(X[train, ], y[train], tau = p, method = "fn")
baseline <- rq.fit(X_linear[train, ], y[train], tau = p, method = "fn")
q <- drop(X[test, ] %*% fit$coefficients)
q_linear <- drop(X_linear[test, ] %*% baseline$coefficients)
check <- function(u, p) u * (p - (u < 0))
scores <- c(recurrent = mean(check(y[test] - q, p)),
            linear = mean(check(y[test] - q_linear, p)))
print(scores)
recovery <- c(target_RMSE = sqrt(mean((q - truth[test])^2)),
              fraction_below = mean(y[test] <= q),
              oracle_fraction_below = mean(y[test] <= truth[test]))
print(recovery)
changed <- y
changed[(n_train + 20L):n] <- changed[(n_train + 20L):n] + 100
unchanged <- seq_len(n_train + 20L)
stopifnot(max(abs(features(changed)[unchanged, ] - H[unchanged, ])) == 0,
          abs(max(Mod(eigen(W)$values)) - 0.7) < 1e-10,
          all(is.finite(q)), length(q) == length(test),
          abs(scores[1] - mean(ifelse(y[test] >= q,
            p * (y[test] - q), (1 - p) * (q - y[test])))) < 1e-12)
example_verified <- TRUE
```

These are **rolling one-step predictions**. At time 1,602, observation 1,601 is available to update the recurrent state, while the coefficients remain fixed. A four-hundred-step forecast issued at time 1,600 would instead require a rule for unknown future inputs. Specify which task is being evaluated: sequentially observed response lags are unavailable for a trajectory issued at a single origin.

## Forecast diagnostics and target recovery

```r
figure_dir <- Sys.getenv("RESEARCH_BLOG_FIGURE_DIR", tempdir())
png(file.path(figure_dir, "fixed-recurrent-quantile-features.png"),
    width = 1400, height = 800, res = 150)
par(mfrow = c(1, 2), mar = c(4, 4.3, 2, 1))
shown <- (n_train - 39L):(n_train + 100L)
shown_test <- test[1:100]
fitted <- drop(X[train, ] %*% fit$coefficients)
plot(shown, y[shown], type = "p", pch = 16, cex = 0.45,
     col = "#65737E", xlab = "Observation", ylab = "Response / 90th quantile",
     ylim = range(y[shown], truth[shown], q[1:100]))
abline(v = n_train + 0.5, lty = 3, col = "#65737E")
lines(shown, truth[shown], col = "#9B7400", lty = 2, lwd = 2)
context <- train[train >= min(shown)]
lines(context, fitted[match(context, train)], col = "#25734A", lwd = 1.6)
lines(shown_test, q[1:100], col = "#176A94", lwd = 1.6)
legend("topleft", c("Known quantile", "Training fit", "One-step forecast"),
       col = c("#9B7400", "#25734A", "#176A94"), lty = c(2, 1, 1),
       lwd = 2, bty = "n", cex = 0.7)
limits <- range(truth[test], q)
plot(truth[test], q, xlim = limits, ylim = limits, pch = 16,
     cex = 0.5, col = adjustcolor("#176A94", 0.5),
     xlab = "Known 90th quantile", ylab = "Estimated 90th quantile")
abline(0, 1, col = "#9B7400", lty = 2, lwd = 2)
dev.off()
```

<figure>
  <a href="{{ '/public/images/blog/fixed-recurrent-quantile-features.png' | relative_url }}"><img src="{{ '/public/images/blog/fixed-recurrent-quantile-features.png' | relative_url }}" alt="Training quantile estimates and the first 100 rolling forecasts, alongside known-versus-estimated quantiles for all 400 held-out observations." width="1400" height="800" loading="lazy"></a>
  <figcaption>Simulated data. Left: the final 40 training rows and first 100 one-step forecasts; the dotted line marks the cutoff. Right: estimated versus known conditional quantiles on all 400 held-out rows. The diagonal indicates exact target recovery.</figcaption>
</figure>

Inspect upper-tail misses, error persistence, and variability over time alongside the mean loss. Recovery RMSE compares estimates with known conditional quantiles; check loss evaluates predictions against realized responses. Even the oracle quantile has a random fraction of observations below it in a finite sample. Results from one data seed and one level do not establish general performance differences. A broader comparison would repeat the simulation and evaluate several origins and horizons under a common protocol.

The reference run has target RMSE **0.1392**. The fraction below the estimated 90th quantile is **0.9025**, compared with **0.8950** for the known target. Mean check loss is **0.1077**, versus **0.1176** for the linear readout. These numbers describe this simulated series, not an expected improvement on other data.

## Where the Bayesian model enters

The research model places priors on the readout coefficients and computes posterior uncertainty conditional on the feature representation. Shrinkage regularizes coefficients when recurrent features are correlated or weakly informed by the data. MCMC and variational inference require additional convergence and approximation checks beyond those of the convex quantile-regression fit above.

Posterior uncertainty conditional on one reservoir is not uncertainty over every possible reservoir or every tuning decision. Likewise, an asymmetric-Laplace working likelihood does not by itself validate the entire response distribution. Held-out quantile scores and calibration checks remain necessary. The next note, [checking quantile forecasts]({{ '/2025/12/04/checking-quantile-forecasts/' | relative_url }}), separates those checks across levels and horizons.

## References

- De Leon, A., Prado, R., and Sanso, B. *Bayesian Quantile Deep Echo State Networks for Nonlinear Time Series*. [arXiv:2609.17579, version 1](https://arxiv.org/abs/2609.17579v1).
- Koenker, R., and Bassett, G. (1978). Regression quantiles. [Econometrica](https://doi.org/10.2307/1913643).
- Koenker, R., et al. *quantreg: Quantile Regression*. [CRAN package and documentation](https://CRAN.R-project.org/package=quantreg).
