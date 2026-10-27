---
layout: post
published: true
title: "Energy scores for Gaussian forecasts: what is closed form and what is not"
date: 2025-02-12
updated: 2026-10-27
last_modified_at: 2026-10-27
theme: Probabilistic forecasting
tags: [forecasting, scoring-rules, gaussian-models, r]
description: "Compute Gaussian energy scores using the spherical closed form, a general-covariance integral, or Monte Carlo estimation."
excerpt: "The standard noncentral-chi expression applies to spherical Gaussian covariance. General covariance requires a generalized quadratic-form calculation or simulation."
math: true
---

The energy score extends continuous ranked probability scoring to multivariate distributions. For Gaussian forecasts, the calculation depends on the covariance structure: a noncentral-chi closed form applies under spherical covariance, while a general positive-definite covariance matrix requires a different calculation. The distinction concerns the distribution of the Euclidean norm in the score.

For a forecast distribution $$P$$ on $$\mathbb R^d$$ and an observation $$y$$, the energy score with Euclidean distance is

$$
\operatorname{ES}(P,y)
=
\mathbb E_P\|X-y\|_2
-
\frac{1}{2}\mathbb E_P\|X-X'\|_2,
$$

where $$X$$ and $$X'$$ are independent draws from $$P$$. Smaller values are better. The usual power-score family requires the corresponding moment condition; for the Euclidean version above, finite first moments are enough.

## The Gaussian problem

Let $$X \sim N_d(\mu,\Sigma)$$. The two terms in the score are expectations of Euclidean norms:

$$
\mathbb E\|X-y\|_2
\quad\text{and}\quad
\mathbb E\|X-X'\|_2.
$$

The second term is another Gaussian norm because $$X-X' \sim N_d(0,2\Sigma)$$. The difficulty is therefore the same in both terms: compute $$\mathbb E\sqrt{Z^\top Z}$$ for $$Z \sim N_d(m,\Sigma)$$.

When $$\Sigma = \sigma^2 I_d$$, the scaled norm $$\|Z\|_2/\sigma$$ is noncentral chi. Standard formulas for the mean of a noncentral-chi random variable apply. When $$\Sigma$$ has unequal eigenvalues, $$Z^\top Z$$ is a generalized noncentral quadratic form. It is not a scaled standard noncentral chi-square variable. Treating it that way gives the wrong score.

## Integral for general covariance

For general positive-definite $$\Sigma$$, use the Laplace transform of

$$
Q = Z^\top Z.
$$

For $$Z \sim N_d(m,\Sigma)$$,

$$
\mathcal L_Q(t)
=
\det(I+2t\Sigma)^{-1/2}
\exp\left\{
-t m^\top(I+2t\Sigma)^{-1}m
\right\}.
$$

Then

$$
\mathbb E\sqrt Q
=
\frac{1}{2\sqrt\pi}
\int_0^\infty
\{1-\mathcal L_Q(t)\}t^{-3/2}\,dt.
$$

This representation reduces each Gaussian norm expectation to a one-dimensional numerical integral and applies to arbitrary positive-definite covariance matrices. It retains the full covariance structure through the determinant and quadratic term. Numerical evaluation requires checks near both integration boundaries and against cases with known answers.

## Base R implementation

The following code uses only base R. It maps the semi-infinite integral to $$u\in(0,1)$$ through $$t=u/(1-u)$$.

```r
norm_mean_quad <- function(mean, Sigma, rel.tol = 1e-8) {
  mean <- as.numeric(mean)
  Sigma <- as.matrix(Sigma)
  d <- length(mean)
  stopifnot(nrow(Sigma) == d, ncol(Sigma) == d)
  Sigma <- 0.5 * (Sigma + t(Sigma))
  if (min(eigen(Sigma, symmetric = TRUE, only.values = TRUE)$values) <= 0) {
    stop("Sigma must be positive definite")
  }

  laplace_q <- function(tval) {
    A <- diag(d) + 2 * tval * Sigma
    chol_A <- chol(A)
    log_det <- 2 * sum(log(diag(chol_A)))
    sol <- backsolve(chol_A, forwardsolve(t(chol_A), mean))
    exp(-0.5 * log_det - tval * sum(mean * sol))
  }

  integrand <- function(u) {
    vapply(u, function(ui) {
      if (ui <= 0 || ui >= 1) return(0)
      tval <- ui / (1 - ui)
      (1 - laplace_q(tval)) * tval^(-1.5) / (1 - ui)^2
    }, numeric(1))
  }

  integrate(integrand, lower = 0, upper = 1, rel.tol = rel.tol,
            subdivisions = 1000)$value / (2 * sqrt(pi))
}

gaussian_energy_score <- function(mu, Sigma, y, rel.tol = 1e-8) {
  mu <- as.numeric(mu)
  y <- as.numeric(y)
  Sigma <- as.matrix(Sigma)
  term1 <- norm_mean_quad(mu - y, Sigma, rel.tol = rel.tol)
  term2 <- norm_mean_quad(rep(0, length(mu)), 2 * Sigma, rel.tol = rel.tol)
  term1 - 0.5 * term2
}

energy_score_draws <- function(draws, y) {
  y <- as.numeric(y)
  draws <- as.matrix(draws)
  first <- mean(sqrt(rowSums((draws - matrix(y, nrow(draws), length(y), TRUE))^2)))
  pair_index <- sample.int(nrow(draws), nrow(draws), replace = TRUE)
  second <- mean(sqrt(rowSums((draws - draws[pair_index, , drop = FALSE])^2)))
  first - 0.5 * second
}
```

The draw-based estimator applies to forecast distributions from which independent samples can be obtained. The integral provides an alternative for Gaussian forecasts of moderate dimension. In higher dimensions, compare its numerical cost with direct simulation or methods designed for Gaussian quadratic forms, using the same covariance convention and response units.

Two numerical checks are needed. First, symmetrize the covariance matrix to remove small floating-point asymmetries, then check positive definiteness; symmetrization does not correct an invalid covariance matrix. Second, the quadrature formula contains the difference $$1-\mathcal L_Q(t)$$, which is small near zero. Check integration tolerances against simulation on representative cases, including covariance matrices with substantially different eigenvalues.

Monte Carlo estimation provides an independent comparison for the integral. Account for simulation error when interpreting a difference between the two estimates. Computing all draw pairs can be expensive; the random-pair calculation above avoids that quadratic cost. If disagreement exceeds Monte Carlo uncertainty, check covariance scaling, vector dimensions, and whether the draws represent the intended response distribution.

## Checks

For a one-dimensional normal forecast at its mean, the energy score equals the Gaussian CRPS:

$$
\operatorname{CRPS}\{N(\mu,\sigma^2),\mu\}
=
\sigma\left(\sqrt{\frac{2}{\pi}}-\frac{1}{\sqrt{\pi}}\right).
$$

The identity checks both the scale and the factor of one half in the second energy-score term. It can be tested at several positive standard deviations, alongside the general-covariance simulation comparison, before applying the implementation to forecast outputs.

```r
set.seed(1)
sigma <- 1.7
quad_1d <- gaussian_energy_score(0, matrix(sigma^2), 0)
crps_mean <- sigma * (sqrt(2 / pi) - 1 / sqrt(pi))
stopifnot(abs(quad_1d - crps_mean) < 1e-7)

mu <- c(0.5, -0.3)
Sigma <- matrix(c(1.2, 0.4, 0.4, 0.8), 2, 2)
y <- c(0.1, 0.2)
score_quad <- gaussian_energy_score(mu, Sigma, y)
stopifnot(is.finite(score_quad))
```

## Spherical covariance

When $$\Sigma=\sigma^2I_d$$, the noncentral-chi representation is valid. In that case $$\|X-y\|_2/\sigma$$ has noncentrality $$\|\mu-y\|_2/\sigma$$, and $$\|X-X'\|_2/(\sqrt{2}\sigma)$$ is central chi. The closed form can be evaluated through the mean of a noncentral-chi variate, using special functions.

That result should be presented as a spherical-covariance formula. It should not be used as the general multivariate Gaussian formula.

## Dependence sensitivity

The energy score is proper, but in higher dimensions it may be less sensitive to dependence misspecification than analysts expect. Forecasts with different covariance structures can have similar Euclidean-distance behavior. For multivariate forecasting problems where dependence matters, the energy score should often be paired with variogram scores, marginal calibration checks, rank histograms, event-specific scores, or summaries tied to the decision problem.

Choose the calculation from the forecast representation. For a spherical Gaussian forecast, the noncentral-chi expression applies. For a general Gaussian forecast, the calculation must retain the full covariance matrix. For a forecast supplied as independent response draws, use a draw-based estimator and report its simulation uncertainty. These choices concern numerical evaluation of the same scoring rule.

Report the estimator, covariance convention, number of simulation draws, and quadrature tolerances as applicable. Include a check against a known case, such as the one-dimensional CRPS identity or a spherical example. This information distinguishes changes in forecast quality from changes in the numerical procedure used to calculate the score.

## References

- Gneiting, T. and Raftery, A. E. "Strictly proper scoring rules, prediction, and estimation." [Journal of the American Statistical Association](https://doi.org/10.1198/016214506000001437).
- Scheuerer, M. and Hamill, T. M. "Variogram-based proper scoring rules for probabilistic forecasts of multivariate quantities." [Monthly Weather Review](https://doi.org/10.1175/MWR-D-14-00269.1).
