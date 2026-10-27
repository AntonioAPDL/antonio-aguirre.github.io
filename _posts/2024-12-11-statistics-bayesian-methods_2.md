---
layout: post
published: true
title: "Preparing and monitoring computation"
date: 2024-10-11
updated: 2026-10-27
last_modified_at: 2026-10-27
theme: Bayesian workflow
tags: [bayesian-statistics, computation, diagnostics]
series: "Bayesian workflow"
series_order: 2
description: "How to prepare Bayesian computation, fit models in stages, and monitor the quantities that determine whether the approximation is usable."
excerpt: "Test computation on reduced cases, monitor error in the reported quantities, and record the settings needed to reproduce the fit."
math: true
---

Computational checks can proceed from small test cases to the full analysis. The stages address three questions: whether the code evaluates the intended model, whether the algorithm explores or optimizes the relevant region, and whether numerical error is sufficiently small for the quantities being reported. A failure at one stage determines which checks to run next.

A Markov chain can have high effective sample sizes for some parameters while estimating a decision-relevant tail probability poorly. A stable variational objective can accompany an underdispersed approximation. A local optimizer can miss regions with substantial posterior mass. Diagnostics therefore need to assess the reported quantities as well as the algorithm's standard output.

## Prepare the model for computation

Parameterization affects posterior geometry and numerical stability. Centered and noncentered forms can produce different computational behavior in hierarchical models. Scale parameters spanning several orders of magnitude may require rescaling or transformation. For constrained parameters, the transformation must preserve support and allow stable evaluation of the density and its derivatives.

Before fitting the full model, I prefer to check the following:

- Can the log density be evaluated at reasonable parameter values?
- Do simulated data have the expected dimensions and units?
- Do transformed parameters remain finite under plausible inputs?
- Are constraints handled by the parameterization rather than by fragile penalties?
- Does a small artificial dataset produce interpretable output?

These checks help separate implementation errors from difficulties caused by the intended posterior distribution. For example, a divergent transition alone does not distinguish an incorrect transformation from problematic posterior geometry. Checking dimensions, support, and density evaluations on known inputs can eliminate some implementation explanations before the sampler is changed.

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

Assess Monte Carlo error for the quantities being reported. For a forecast interval, estimate the numerical error of its endpoints. For tail probabilities, examine effective sample sizes and Monte Carlo uncertainty in the relevant tail. For model comparison, assess uncertainty in predictive score differences. Diagnostics for an unrelated latent state do not answer these questions.

Additional iterations can reduce Monte Carlo error when chains explore the relevant posterior regions. They do not ensure movement between separated modes or correct an invalid transformation. Persistent mixing problems require examination of the parameterization, prior assumptions, and sampling algorithm before a longer run is justified.

## Approximate inference diagnostics

Variational inference, Laplace approximations, expectation propagation, and other approximations need their own checks. A stable optimization objective does not guarantee a good approximation to the posterior. The approximation may understate uncertainty, miss dependence, or fail in tails.

For approximate inference, I look for:

- sensitivity to initialization;
- agreement with a slower method on small cases;
- calibration under simulated data;
- stability of reported summaries under alternative approximation settings;
- clear identification of which posterior features the approximation is expected to preserve.

Describe which posterior features the approximation is designed to retain and which checks support its use. Agreement in posterior means, for example, does not establish agreement in variances or tail probabilities. Report numerical approximation error separately from uncertainty under the fitted model whenever it can be assessed.

## Record the run

Record the data version, code commit, random seeds, package versions, hardware or cluster environment, model configuration, and output paths when launching a run. For long jobs, retain logs that distinguish failures in model code from resource limits, missing files, and external services. These records should be written with the results, before the computing environment changes.

This record also protects interpretation. If a result changes, the analyst can ask whether the data changed, the code changed, the random seed changed, or the computational settings changed. Without that separation, the same analysis can become difficult to explain even to the person who ran it.

## Practical stopping rule for computation

A computational stopping criterion should relate numerical error to the precision required for the reported summaries. Check stability across relevant settings and compare numerical error with statistical uncertainty. Meeting this criterion does not establish complete posterior exploration; the report should state the method, diagnostics, tolerances, and any unresolved limitations.

## References

- Vehtari, A., Gelman, A., Simpson, D., Carpenter, B., and Buerkner, P. "Rank-normalization, folding, and localization: An improved $$\hat R$$ for assessing convergence of MCMC." [Bayesian Analysis](https://projecteuclid.org/journals/bayesian-analysis/volume-16/issue-2/Rank-Normalization-Folding-and-Localization--An-Improved-R%cb%86-for/10.1214/20-BA1221.full).
- Stan Development Team. [Stan Reference Manual: MCMC diagnostics](https://mc-stan.org/docs/reference-manual/analysis.html).
