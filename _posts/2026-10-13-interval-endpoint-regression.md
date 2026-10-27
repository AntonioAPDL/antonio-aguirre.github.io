---
layout: post
published: true
title: "Modeling interval endpoints in regression and time series"
date: 2026-10-13
updated: 2026-10-27
last_modified_at: 2026-10-27
theme: Interval models
tags: [regression, generalized-bayes, mean-tilted-intervals, time-series]
description: "Build a small loss-based endpoint regression and distinguish interval content, posterior endpoint uncertainty, and dynamic-state computation."
excerpt: "A model for interval endpoints need not be a model for the whole response distribution. That distinction controls what its uncertainty summaries mean."
math: true
---

An interval estimated for a whole population may be too crude when the response depends on predictors. We might want its location to change with a covariate, or its endpoints to evolve through time. Before choosing a regression model, we still need to specify what the interval represents: an equal-tailed region, a shortest region, or another fixed-content target.

My work on mean-tilted intervals separates this target from the computation used to estimate it. This note introduces the endpoint-regression idea through a small, fully enumerated example. It does not reproduce the manuscript's continuous-parameter sampler. The aim is to make the loss, prior, and resulting uncertainty statements inspectable without hiding them inside a fitting function.

## Use a loss for the interval target

For ordered endpoints $$a<b$$, the product $$e=(y-a)(y-b)$$ is negative inside the interval and positive outside. Applying check loss at content level $$c$$ gives

$$
\ell_c(a,b;y)=\rho_c\{(y-a)(y-b)\},
\qquad \rho_c(r)=r\{c-\mathbf{1}(r<0)\}.
$$

The residual-product construction originates with Pouplin and colleagues. At a regular unrestricted population solution, it targets content $$c$$ and equality between the retained mean and the population mean: the mean-preserving interval. This is not ordinary regression at two prespecified endpoint quantiles. A restricted regression family need not satisfy those population equations exactly at every predictor value.

Midpoint and half-width coordinates make ordering easy: $$a(x)=m(x)-h(x)$$ and $$b(x)=m(x)+h(x)$$, with positive $$h(x)$$. Here the midpoint is linear and the half-width is constant. A fixed finite grid keeps the calculation small enough to enumerate.

```r
set.seed(61027)
n <- 600L
x <- seq(-1, 1, length.out = n)
y <- 0.5 + 0.8 * x + rnorm(n, sd = 0.55)
content <- 0.8
grid <- expand.grid(
  intercept = seq(-0.3, 1.3, length.out = 41),
  slope = seq(0.1, 1.5, length.out = 41),
  half_width = seq(0.35, 1.5, length.out = 41)
)
check <- function(u, c) u * (c - (u < 0))
loss <- vapply(seq_len(nrow(grid)), function(j) {
  m <- grid$intercept[j] + grid$slope[j] * x
  sum(check((y - m)^2 - grid$half_width[j]^2, content))
}, numeric(1))
log_prior <- dnorm(grid$intercept, 0, 1.5, log = TRUE) +
  dnorm(grid$slope, 0, 1, log = TRUE) +
  dnorm(grid$half_width, 0, 1, log = TRUE)
```

The prior assigns mass proportional to these positive weights on the 68,921 grid points. It is a proper discrete prior after normalization. Six hundred observations and a finer grid make endpoint recovery easier to assess than in a very small sample. This is the model itself, not a claim that this grid accurately approximates every feature of a continuous posterior. Its bounded coefficient support, constant-width restriction, and resolution are substantive limitations.

## Update with the loss

A generalized posterior weights parameter values by their cumulative loss and prior mass:

$$
\pi(\theta\mid D)\propto
\exp\{-\omega L_c(\theta;D)\}\pi_0(\theta).
$$

The learning rate $$\omega$$ controls the strength of the loss update. It is not the content level, not a retained-mean tilt, and not a response-noise standard deviation. Because this loss involves squared response units, changing response units without adjusting the learning rate changes the update.

```r
posterior <- function(rate) {
  log_weight <- log_prior - rate * loss
  weight <- exp(log_weight - max(log_weight))
  weight / sum(weight)
}
weight <- posterior(1)
weight_gentler <- posterior(0.5)
print(rbind(rate_1 = colSums(grid * weight),
            rate_0.5 = colSums(grid * weight_gentler)))
direct <- exp(log_prior - max(log_prior)) * exp(-(loss - min(loss)))
direct <- direct / sum(direct)
boundary <- grid$intercept %in% range(grid$intercept) |
  grid$slope %in% range(grid$slope) |
  grid$half_width %in% range(grid$half_width)
print(c(boundary_mass = sum(weight[boundary])))
stopifnot(abs(sum(weight) - 1) < 1e-12, all(is.finite(weight)),
          max(abs(weight - direct)) < 1e-12,
          all(grid$half_width > 0), sum(weight[boundary]) < 0.05)
```

Subtracting the largest log weight avoids unnecessary underflow. Reporting a second learning rate is a sensitivity check, not a calibration procedure. Small boundary mass is reassuring for this particular grid, but does not prove continuous-posterior accuracy. A serious analysis would examine grid refinement or use the manuscript's continuous-parameter methods with their numerical diagnostics.

## Summarize endpoint uncertainty, not response uncertainty

Each parameter value gives two endpoints at every predictor value. We can summarize their marginal generalized-posterior distributions separately. The following calculation uses exact sums over the finite grid, with no Monte Carlo error.

```r
weighted_quantile <- function(value, weight, probability) {
  o <- order(value)
  value[o][which(cumsum(weight[o]) >= probability)[1L]]
}
xx <- seq(-1, 1, length.out = 100)
summarize <- function(z, sign) {
  endpoint <- grid$intercept + grid$slope * z + sign * grid$half_width
  c(mean = sum(weight * endpoint),
    low = weighted_quantile(endpoint, weight, 0.05),
    high = weighted_quantile(endpoint, weight, 0.95))
}
lower <- vapply(xx, summarize, numeric(3), sign = -1)
upper <- vapply(xx, summarize, numeric(3), sign = 1)
known_half_width <- qnorm(0.9) * 0.55
target_lower <- 0.5 + 0.8 * xx - known_half_width
target_upper <- 0.5 + 0.8 * xx + known_half_width
endpoint_RMSE <- sqrt(mean(c(lower[1, ] - target_lower,
                            upper[1, ] - target_upper)^2))
set.seed(61028) # Independent verification observations, never used in fitting.
x_test <- seq(-1, 1, length.out = 1000)
y_test <- 0.5 + 0.8 * x_test + rnorm(length(x_test), sd = 0.55)
estimate <- colSums(grid * weight)
lower_test <- estimate[1] + estimate[2] * x_test - estimate[3]
upper_test <- estimate[1] + estimate[2] * x_test + estimate[3]
heldout_content <- mean(y_test >= lower_test & y_test <= upper_test)
population_content <- mean(pnorm((upper_test - 0.5 - 0.8 * x_test) / 0.55) -
                           pnorm((lower_test - 0.5 - 0.8 * x_test) / 0.55))
print(c(endpoint_RMSE = endpoint_RMSE, heldout_content = heldout_content,
        population_content = population_content))
a <- 0.1
b <- 1.2
stopifnot(all(lower[1, ] < upper[1, ]),
          all(lower[2, ] <= lower[3, ]), all(upper[2, ] <= upper[3, ]),
          max(abs(check((y - a) * (y - b), content) -
                  check((y - b) * (y - a), content))) == 0)
example_verified <- TRUE
```

The blue curves below are posterior means of endpoint functions. The pale bands are pointwise 90% credible bands for those endpoints under this discrete generalized posterior. They are **not** 90% response prediction bands, simultaneous bands over the covariate range, or a tolerance certificate. The region between the two endpoint curves represents the estimated interval target; uncertainty about those curves is a separate object.

The simulation also permits direct recovery checks: endpoint RMSE against the known target, content on 1,000 independent verification observations, and average population content calculated from the known Gaussian CDF. These checks are not used to select the learning rate, prior, or grid. An in-sample fraction alone would be much weaker evidence, and none of these checks establishes a tolerance guarantee or repeated-sampling coverage for the endpoint bands.

The reference endpoint RMSE is **0.0210**. Average population content is **0.7879**, and the independent sample fraction inside the estimated interval is **0.7780**, against a target of 0.8. The difference between the last two quantities reflects verification-sample variation; the difference from the target also includes endpoint-estimation error. The example reports both rather than shifting its fitted endpoints after verification.

```r
figure_dir <- Sys.getenv("RESEARCH_BLOG_FIGURE_DIR", tempdir())
png(file.path(figure_dir, "interval-endpoint-regression.png"),
    width = 1400, height = 800, res = 150)
par(mar = c(4, 4, 2, 1))
plot(x, y, pch = 16, cex = 0.4, col = adjustcolor("#65737E", 0.45),
     xlab = "Predictor", ylab = "Simulated response",
     ylim = range(y, lower, upper))
for (curve in list(lower, upper)) {
  polygon(c(xx, rev(xx)), c(curve[2, ], rev(curve[3, ])),
          col = adjustcolor("#176A94", 0.2), border = NA)
  lines(xx, curve[1, ], col = "#176A94", lwd = 2)
}
for (sign in c(-1, 1)) {
  lines(xx, 0.5 + 0.8 * xx + sign * known_half_width,
        col = "#25734A", lty = 2, lwd = 2)
}
legend("topleft", c("Posterior mean endpoints", "Known population endpoints"),
       col = c("#176A94", "#25734A"), lty = c(1, 2), lwd = 2,
       bty = "n", cex = 0.8)
dev.off()
```

<figure>
  <a href="{{ '/public/images/blog/interval-endpoint-regression.png' | relative_url }}"><img src="{{ '/public/images/blog/interval-endpoint-regression.png' | relative_url }}" alt="Simulated regression data with estimated lower and upper endpoint curves, pointwise endpoint uncertainty bands, and known population endpoints." width="1400" height="800" loading="lazy"></a>
  <figcaption>Zero-tilt endpoint regression on a finite parameter grid. Dashed green curves show the known Gaussian content-0.8 interval. Pale blue bands describe endpoint uncertainty, not uncertainty for future responses.</figcaption>
</figure>

## Add tilt or dynamics without changing the interpretation

A fixed retained-mean tilt adds $$-2c\delta(y-m)$$ to the per-observation loss. It changes the interval target; it is not another setting of the learning rate. This example keeps $$\delta=0$$. Nonzero tilt requires a justified target choice and suitable assumptions rather than a search for whichever interval happens to look best.

The manuscript allows more general root functions, including fixed nonlinear features and time-varying coefficients. Raw roots can exchange labels, so lower and upper endpoints must be obtained by sorting their values at each predictor, not by sorting regression coefficients. Our positive-half-width restriction avoids that ambiguity by construction.

In dynamic models, Gaussian state priors do not make the joint observation problem linear Gaussian. Under the augmentation, one root trajectory can have a Gaussian conditional update while the other root and latent scales are held fixed. Jointly, the augmented observation kernel is quartic in the roots. Alternating root-specific smoothing steps exploit conditional structure, not a single ordinary Kalman-filter solution for everything.

These models describe interval-root functionals. A predictive distribution for responses needs additional modeling, and a repeated-sampling tolerance guarantee needs separate calibration. The [tolerance note]({{ '/2026/07/09/tolerance-intervals/' | relative_url }}) gives an iid example of that extra step; its certificate does not automatically extend to regression or time series.

## References

- Pouplin, T., Jeffares, A., Seedat, N., and van der Schaar, M. (2024). Relaxed quantile regression: prediction intervals for asymmetric noise. [ICML / PMLR](https://proceedings.mlr.press/v235/pouplin24a.html).
- De Leon, A., Prado, R., and Sanso, B. *Mean-Tilted Intervals: Regression and Dynamic Models*. [arXiv:2610.13960, version 1](https://arxiv.org/abs/2610.13960v1).
- Bissiri, P. G., Holmes, C. C., and Walker, S. G. (2016). A general framework for updating belief distributions. [JRSS B](https://doi.org/10.1111/rssb.12158).
- De Leon, A., Prado, R., and Sanso, B. *Mean-Tilted Intervals: Short Tolerance Intervals*. [arXiv:2607.26098, version 3](https://arxiv.org/abs/2607.26098v3).
