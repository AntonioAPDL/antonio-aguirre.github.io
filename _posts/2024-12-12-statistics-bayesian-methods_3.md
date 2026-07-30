---
layout: post
published: true
title: "Simulation, recovery, and calibration"
date: 2024-11-01
updated: 2026-07-29
theme: Bayesian workflow
tags: [bayesian-statistics, simulation, calibration]
series: "Bayesian workflow"
series_order: 3
description: "A diagnostic ladder for Bayesian models: deterministic checks, fake-data recovery, prior predictive checks, repeated-sampling behavior, and simulation-based calibration."
excerpt: "Simulation helps separate coding errors, weak identification, poor priors, and biased computation before real-data conclusions are trusted."
math: true
---

Simulation is one of the most useful tools in applied Bayesian work because it lets the analyst inspect a procedure under controlled conditions. Real data rarely reveal whether a failure comes from a coding error, weak information, an unrealistic prior, or an approximation that is too crude. Simulated data cannot solve the real scientific problem, but they can show whether the model and computation behave coherently when the truth is known.

It helps to separate several kinds of simulation. They answer different questions and should not be treated as one generic "fake-data check."

## Deterministic checks

Before fitting any simulated data, check deterministic pieces of the model. If a link function, matrix construction, indexing rule, state update, or likelihood contribution is wrong, posterior diagnostics will be confusing. Unit tests for these pieces are often simple: feed in a small input whose output can be calculated by hand, then verify the code returns the same result.

These checks are not glamorous, but they are high value. A model with a shifted time index, a transposed design matrix, or a scale parameter interpreted in the wrong units can produce plausible-looking output. The earlier these errors are caught, the less time is spent interpreting artifacts.

## Fixed-parameter recovery

The next step is to choose known parameter values, simulate data from the model, fit the model, and check whether the fitted procedure recovers the known values at the expected uncertainty level. This is useful for testing identifiability in realistic sample sizes.

Recovery should be evaluated carefully. If the posterior interval misses the truth once, that is not automatically a failure; a nominal 95 percent interval will miss sometimes. The more relevant question is whether repeated simulations show systematic bias or miscalibration. It is also possible for parameter recovery to be weak while prediction remains strong. In overparameterized or partially identified models, several parameter settings may imply nearly identical predictive distributions.

For this reason, recovery checks should include both parameters and observable implications. If a latent parameter is scientifically important, poor recovery is a real limitation. If the main target is prediction, the simulated predictive performance may be more relevant.

## Prior predictive simulation

Prior predictive simulation checks the consequences of priors before the observed outcome is used. It answers a simple question: what kinds of data does this model think are plausible before fitting?

This is especially important when priors interact with nonlinear transformations or dynamic recursions. A prior that looks weak on each parameter can imply impossible counts, explosive time series, negative physical quantities after transformation, or unrealistically smooth trajectories. Prior predictive checks can reveal these problems early.

A prior predictive check should be performed on the scale that matters. For a forecasting model, plot simulated forecasts and intervals. For a regression model, inspect outcome ranges over realistic covariate settings. For a hierarchical model, inspect between-group variation and within-group variation separately. The goal is not to tune priors until they match the observed data. The goal is to remove implications that are unreasonable before the data are used.

## Repeated-sampling behavior

Sometimes the question is frequentist in form: if this procedure were used repeatedly under a specified data-generating mechanism, how often would intervals cover, how biased would estimates be, or how well calibrated would predictive probabilities be? This is a property of a procedure under a simulation design, not a universal property of Bayesian inference.

Repeated-sampling checks are useful when a method will be deployed repeatedly or compared against alternatives. They require care because the simulation design determines the conclusion. A procedure can be calibrated under the model and fail under misspecification. That is not a contradiction; it is information about robustness.

## Simulation-based calibration

Simulation-based calibration, or SBC, checks whether the combination of prior, data simulation, and posterior computation is calibrated. The basic idea is to draw parameters from the prior, simulate data from the model, fit the model, and compare the true simulated parameter values with posterior draws. Under correct implementation and exact computation, the rank of the true value among posterior draws should be uniform, up to Monte Carlo error.

SBC is powerful because it can detect biased computation, poor mixing, incorrect likelihoods, and some coding errors. It is also expensive. Each simulated dataset requires a fit. Autocorrelation in posterior draws and finite simulation counts matter. Weakly informative priors can generate extreme datasets, which may dominate the diagnostic and obscure behavior in the practical region of interest.

The shape of SBC rank histograms is informative. U-shaped patterns can indicate underdispersed posteriors. Hump-shaped patterns can indicate overdispersion. Skew can indicate bias. But SBC should be interpreted with simulation uncertainty and with knowledge of the model geometry.

## Posterior predictive simulation

After fitting real data, posterior predictive simulation checks whether the fitted model can reproduce features of the observed data that matter for the target. This is not the same as parameter recovery. It asks whether replicated data from the fitted model resemble the observed data in relevant ways.

Good posterior predictive checks are targeted. A time-series model should be checked for persistence, extremes, seasonal behavior, residual autocorrelation, and forecast calibration if those features matter. A grouped model should be checked within and across groups. A quantile model should be checked at the quantile levels it claims to estimate.

## A diagnostic ladder

The sequence I prefer is:

1. Deterministic code checks.
2. Fixed-parameter simulation and recovery.
3. Prior predictive simulation.
4. Repeated-sampling checks for selected operating regimes.
5. SBC when the computational burden is justified.
6. Posterior predictive checks on real data.

The ladder is useful because each step narrows the source of failure. If deterministic checks fail, the model code is wrong. If fixed-parameter recovery fails, the procedure may be biased or weakly identified. If prior predictive simulation fails, the assumptions are unreasonable before seeing data. If posterior predictive checks fail after everything else passes, the model is probably missing structure in the real process.

## References

- Talts, S., Betancourt, M., Simpson, D., Vehtari, A., and Gelman, A. "Validating Bayesian inference algorithms with simulation-based calibration." [arXiv:1804.06788](https://arxiv.org/abs/1804.06788).
- Gabry, J., Simpson, D., Vehtari, A., Betancourt, M., and Gelman, A. "Visualization in Bayesian workflow." [Journal of the Royal Statistical Society: Series A](https://doi.org/10.1111/rssa.12378).
