---
layout: post
published: true
title: "Preparing and monitoring computation"
date: 2024-10-11
updated: 2026-07-29
theme: Bayesian workflow
tags: [bayesian-statistics, computation, diagnostics]
series: "Bayesian workflow"
series_order: 2
description: "How to prepare Bayesian computation, fit models in stages, and monitor the quantities that determine whether the approximation is usable."
excerpt: "Computation should be staged, diagnosed, and recorded against the quantities that will actually be reported."
math: true
---

After a first model is written, the next problem is not simply to run the largest dataset through the most sophisticated algorithm. The safer path is staged computation. Each stage should answer one question: does the code evaluate the model correctly, does the algorithm explore or optimize the relevant region, and is the remaining numerical error small enough for the reported target?

This matters because Bayesian computation can fail quietly. A Markov chain can have a high effective sample size for parameters that do not matter and still miss tail behavior that drives a decision. A variational objective can appear stable while the approximation is too narrow. An optimizer can converge to a local mode that is irrelevant for the posterior mass. Monitoring should be tied to the analysis target, not only to generic software output.

## Prepare the model for computation

Parameterization is often the difference between a model that is routine to fit and one that is fragile. Centered and noncentered parameterizations can behave very differently in hierarchical models. Raw scale parameters can create poor geometry if they span several orders of magnitude. Constrained parameters need transformations that preserve support while keeping gradients stable.

Before fitting the full model, I prefer to check the following:

- Can the log density be evaluated at reasonable parameter values?
- Do simulated data have the expected dimensions and units?
- Do transformed parameters remain finite under plausible inputs?
- Are constraints handled by the parameterization rather than by fragile penalties?
- Does a small artificial dataset produce interpretable output?

These checks catch many errors before they become statistical diagnostics. A divergent transition caused by a coding mistake and one caused by real posterior geometry can look similar. The first goal is to remove coding mistakes.

## Fit in stages

Start with small cases. Fit a reduced dataset, a reduced hierarchy, or a simpler likelihood before using the full model. This is not a substitute for the final fit. It is a way to isolate failure. If the small model fails, the full model is unlikely to clarify the issue. If the small model works and the full one fails, the difference is informative.

A typical sequence is:

1. Simulate from the prior or from fixed known parameters.
2. Fit the model to a small simulated dataset.
3. Fit the model to a small real-data subset.
4. Fit a simpler baseline to the full data.
5. Fit the intended model to the full data.
6. Re-run the final fit with the recorded production settings.

At each step, the diagnostic target changes. Early runs test code and geometry. Later runs test inference, approximation quality, and reproducibility. Mixing these purposes makes debugging slower.

## MCMC diagnostics

For Markov chain Monte Carlo, convergence is not a single number. Multiple chains should start from dispersed initial values when possible. Rank plots, trace plots, split $$\hat R$$, effective sample size, divergences, tree depth, energy diagnostics, and Monte Carlo standard errors all provide different information.

The most important diagnostic is whether Monte Carlo error is small for the quantities being reported. If the final result is a forecast interval, the Monte Carlo error of the interval endpoint matters more than the effective sample size of an unrelated latent state. If the final result is a tail probability, tail effective sample size matters. If the result is a model comparison, uncertainty in predictive score differences matters.

More iterations can be the right response after the model geometry is understood. But more iterations are not a cure for a broken parameterization, a multimodal posterior that chains cannot move between, or a prior that creates unreasonable regions of high curvature.

## Approximate inference diagnostics

Variational inference, Laplace approximations, expectation propagation, and other approximations need their own checks. A stable optimization objective does not guarantee a good approximation to the posterior. The approximation may understate uncertainty, miss dependence, or fail in tails.

For approximate inference, I look for:

- sensitivity to initialization;
- agreement with a slower method on small cases;
- calibration under simulated data;
- stability of reported summaries under alternative approximation settings;
- clear identification of which posterior features the approximation is expected to preserve.

Approximate methods can be excellent engineering choices. They should be presented as approximations with known diagnostics, not as exact posterior computation.

## Record the run

Reproducibility is easier if it is treated as part of computation rather than as a final cleanup step. A useful run record includes the data version, code commit, random seeds, package versions, hardware or cluster environment, model configuration, and output paths. For long jobs, logs should include enough information to identify whether the job failed because of model code, resource limits, missing files, or external services.

This record also protects interpretation. If a result changes, the analyst can ask whether the data changed, the code changed, the random seed changed, or the computational settings changed. Without that separation, the same analysis can become difficult to explain even to the person who ran it.

## Practical stopping rule for computation

Computational work can stop when the remaining numerical error is small relative to the statistical uncertainty and the conclusions are stable for the target summaries. That is a practical standard, not a claim that the posterior has been perfectly explored. It should be reported honestly: what method was used, what diagnostics were checked, and what limitations remain.

## References

- Vehtari, A., Gelman, A., Simpson, D., Carpenter, B., and Buerkner, P. "Rank-normalization, folding, and localization: An improved $$\hat R$$ for assessing convergence of MCMC." [Bayesian Analysis](https://projecteuclid.org/journals/bayesian-analysis/volume-16/issue-2/Rank-Normalization-Folding-and-Localization--An-Improved-R%cb%86-for/10.1214/20-BA1221.full).
- Stan Development Team. [Stan Reference Manual: MCMC diagnostics](https://mc-stan.org/docs/reference-manual/analysis.html).
