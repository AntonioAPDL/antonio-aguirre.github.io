---
layout: post
published: true
title: "Simulation, recovery, and calibration"
date: 2024-11-01
updated: 2026-10-27
last_modified_at: 2026-10-27
theme: Bayesian workflow
tags: [bayesian-statistics, simulation, calibration]
series: "Bayesian workflow"
series_order: 3
description: "Simulation checks for Bayesian models: code verification, parameter recovery, prior predictive behavior, repeated-sampling performance, and simulation-based calibration."
excerpt: "Simulation helps separate coding errors, weak identification, poor priors, and biased computation before real-data conclusions are trusted."
math: true
---

Simulation allows a statistical procedure to be examined under a specified data-generating mechanism. With known parameters and distributions, discrepancies can be traced to implementation, identification, prior assumptions, or computation. The conclusions remain conditional on the simulation design: performance under a chosen mechanism does not establish performance on an unknown real process.

The checks below address distinct questions. Record the generating assumptions, fitted procedure, and diagnostic target for each one; a successful recovery experiment does not replace a prior predictive or computational calibration check.

## Deterministic checks

Before fitting any simulated data, check deterministic pieces of the model. If a link function, matrix construction, indexing rule, state update, or likelihood contribution is wrong, posterior diagnostics will be confusing. Unit tests for these pieces are often simple: feed in a small input whose output can be calculated by hand, then verify the code returns the same result.

A shifted time index, transposed design matrix, or incorrect scale conversion can produce plausible numerical output. Test these operations against known inputs before interpreting fitted parameters or predictions. Numerical tolerances should reflect the operation being checked, and failures should identify the input and expected result so they can be reproduced.

## Fixed-parameter recovery

Choose known parameter values, simulate observations, and apply the fitted procedure at sample sizes relevant to the application. Compare estimates and uncertainty summaries with the generating values. These experiments assess recovery under the selected parameter settings and can identify combinations that the available observations distinguish poorly.

A single posterior interval that excludes the generating value is insufficient to diagnose a failure. Repeated simulations can assess bias and interval coverage under the specified mechanism. Parameter recovery and predictive accuracy can also differ: in overparameterized or partially identified models, several parameter settings may imply nearly identical predictive distributions.

Include both parameter estimates and observable implications in recovery checks. Limited recovery of a latent parameter restricts scientific claims about that parameter, even when predictions are accurate. If prediction is the primary target, evaluate the predictive distribution directly and specify which aspects of parameter uncertainty affect it.

## Prior predictive simulation

Prior predictive simulation checks the consequences of priors before the observed outcome is used. It answers a simple question: what kinds of data does this model think are plausible before fitting?

Nonlinear transformations and dynamic recursions can amplify the combined effects of prior assumptions. Broad parameter priors may imply impossible counts, explosive series, negative physical quantities after transformation, or implausibly smooth trajectories. Simulate the complete observation process to assess these outcomes; examining each marginal parameter prior separately may not reveal them.

Choose summaries on the scale of the intended analysis. For forecasting, inspect simulated trajectories and intervals. For regression, inspect outcome ranges over relevant covariate settings. For hierarchical models, examine between-group and within-group variation separately. Compare these implications with domain knowledge and document any revisions made before using the observed outcomes to fit the model.

## Repeated-sampling behavior

Sometimes the question is frequentist in form: if this procedure were used repeatedly under a specified data-generating mechanism, how often would intervals cover, how biased would estimates be, or how well calibrated would predictive probabilities be? This is a property of a procedure under a simulation design, not a universal property of Bayesian inference.

Repeated-sampling checks assess a procedure over a defined set of operating conditions. Include the sample sizes, parameter settings, and forms of misspecification relevant to the application. Calibration under the fitted model and calibration under a different generating mechanism are separate results; report the conditions under which each result was obtained.

## Simulation-based calibration

Simulation-based calibration, or SBC, checks whether the combination of prior, data simulation, and posterior computation is calibrated. The basic idea is to draw parameters from the prior, simulate data from the model, fit the model, and compare the true simulated parameter values with posterior draws. Under correct implementation and exact computation, the rank of the true value among posterior draws should be uniform, up to Monte Carlo error.

SBC can reveal discrepancies associated with biased computation, poor mixing, incorrect likelihoods, and coding errors. Each simulated dataset requires a fit, and interpretation must account for autocorrelation in posterior draws and the number of simulated datasets. Extreme datasets drawn under broad priors may require separate examination to identify where a computational discrepancy occurs.

The shape of SBC rank histograms is informative. U-shaped patterns can indicate underdispersed posteriors. Hump-shaped patterns can indicate overdispersion. Skew can indicate bias. But SBC should be interpreted with simulation uncertainty and with knowledge of the model geometry.

## Posterior predictive simulation

After fitting real data, posterior predictive simulation checks whether the fitted model can reproduce features of the observed data that matter for the target. This is not the same as parameter recovery. It asks whether replicated data from the fitted model resemble the observed data in relevant ways.

Choose posterior predictive summaries according to the features being modeled. For time series, relevant checks may include persistence, extremes, seasonality, and residual autocorrelation, with separate held-out assessment of forecast calibration. For grouped data, examine behavior within and between groups. For quantile models, assess predictions at the levels being reported.

## Sequence of simulation checks

The sequence I prefer is:

1. Deterministic code checks.
2. Fixed-parameter simulation and recovery.
3. Prior predictive simulation.
4. Repeated-sampling checks for selected operating regimes.
5. SBC when the computational burden is justified.
6. Posterior predictive checks on real data.

The sequence separates implementation checks from assessments of inference and model fit. Failed deterministic tests identify discrepancies in specific operations. Recovery failures can indicate estimation bias or limited identification. Implausible prior predictive outcomes indicate assumptions to reconsider. Posterior predictive discrepancies identify features of the observed data that the fitted model does not reproduce, even when the earlier computational checks pass.

## References

- Talts, S., Betancourt, M., Simpson, D., Vehtari, A., and Gelman, A. "Validating Bayesian inference algorithms with simulation-based calibration." [arXiv:1804.06788](https://arxiv.org/abs/1804.06788).
- Gabry, J., Simpson, D., Vehtari, A., Betancourt, M., and Gelman, A. "Visualization in Bayesian workflow." [Journal of the Royal Statistical Society: Series A](https://doi.org/10.1111/rssa.12378).
