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
excerpt: "A recurrent network can supply a fixed representation of the past while a much smaller regression estimates the forecast target."
math: true
---

A time series can depend on its past in ways that a straight line does not capture. The effect of yesterday's value may flatten, change direction, or interact with earlier observations. A recurrent feature map offers one way to represent that history. Quantile regression then lets us ask about an upper or lower part of the conditional distribution, rather than only its mean.

The useful separation is between **constructing features** and **estimating the readout**. An echo state network fixes its recurrent weights and estimates an output model using the resulting states. In my Q-DESN research, the readout is Bayesian and the representation can contain several recurrent layers. Here I use one small layer and ordinary quantile regression so that the information flow is visible. This is an illustration of fixed recurrent features, not an implementation of the paper's Bayesian model.

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

This construction is causal in the forecasting sense: row $$t$$ uses responses only through $$t-1$$. A direct check is to change later observations and confirm that earlier feature rows do not change. Fixing a random seed makes this particular representation reproducible; it does not establish that the representation is a good one.

The spectral radius 0.7 and leak 0.4 are example settings, not a general proof that initialization is forgotten under every input sequence. Larger reservoirs, deeper layers, and stronger persistence introduce additional choices. Those choices need training or validation data, not repeated consultation of the final test scores.

## Estimate the readout, not the reservoir

For a target level $$p$$, quantile regression minimizes the sum of check losses,

$$
\rho_p(u)=u\{p-\mathbf{1}(u<0)\}.
$$

The regression coefficients turn each feature row into an estimated conditional quantile. The readout includes the original lag as well as the recurrent features, so the nonlinear representation supplements rather than replaces the simplest predictor. A linear autoregression provides a baseline using the same training rows, lag information, and target level.

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

These are **rolling one-step predictions**. At time 1,602, observation 1,601 has already become available and can update the recurrent state. The coefficients remain fixed. This is not a four-hundred-step forecast issued once at time 1,600: that task would require a rule for propagating unknown future inputs. Confusing those two designs can make an evaluation appear substantially easier than the intended application.

## Look at errors as well as the score

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
  <figcaption>Simulated data. Left: the final 40 training rows and first 100 one-step forecasts; the dotted line marks the cutoff. Right: target recovery on all 400 held-out rows. A good upper-quantile forecast follows the known quantile, not the individual response values.</figcaption>
</figure>

An aggregate score can conceal periods of poor fit. Inspect upper-tail misses, persistent errors, and instability alongside the mean loss. The recovery RMSE compares the estimates with the known conditional quantiles, while the check loss scores actual responses. Even the oracle quantile has a random realized fraction below it, so exact agreement with 0.9 is not a sensible requirement for one sample. One seed and one target level cannot establish a general advantage for either approach. A larger comparison would repeat the simulation and examine several forecast origins and horizons under a common protocol.

The reference run has target RMSE **0.1392**. The fraction below the estimated 90th quantile is **0.9025**, compared with **0.8950** for the known target. Mean check loss is **0.1077**, versus **0.1176** for the linear readout. These numbers describe this simulated series, not an expected improvement on other data.

## Where the Bayesian model enters

The research model places priors on the readout coefficients and uses posterior computation to describe uncertainty conditional on the chosen representation. Shrinkage matters when many recurrent features carry similar information. MCMC and variational inference also introduce diagnostic questions that the convex fit above does not answer.

Posterior uncertainty conditional on one reservoir is not uncertainty over every possible reservoir or every tuning decision. Likewise, an asymmetric-Laplace working likelihood does not by itself validate the entire response distribution. Held-out quantile scores and calibration checks remain necessary. The next note, [checking quantile forecasts]({{ '/2025/12/04/checking-quantile-forecasts/' | relative_url }}), separates those checks across levels and horizons.

## References

- De Leon, A., Prado, R., and Sanso, B. *Bayesian Quantile Deep Echo State Networks for Nonlinear Time Series*. [arXiv:2609.17579, version 1](https://arxiv.org/abs/2609.17579v1).
- Koenker, R., and Bassett, G. (1978). Regression quantiles. [Econometrica](https://doi.org/10.2307/1913643).
- Koenker, R., et al. *quantreg: Quantile Regression*. [CRAN package and documentation](https://CRAN.R-project.org/package=quantreg).
