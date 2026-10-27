---
layout: post
published: true
title: "Diagnosing fit and revising the model"
date: 2024-11-13
updated: 2026-10-27
last_modified_at: 2026-10-27
theme: Bayesian workflow
tags: [bayesian-statistics, diagnostics, model-checking]
series: "Bayesian workflow"
series_order: 4
description: "Distinguish implementation, computation, and model-fit problems, then use targeted checks to guide revisions."
excerpt: "A failed diagnostic should lead to a specific revision: code, computation, parameterization, prior information, or model structure."
math: true
---

Poor fit, divergent transitions, residual bias, and unstable forecasts can have different causes. Before changing the model, identify which output failed and how that failure affects the analysis target. Expanding the model is appropriate only when the evidence indicates a limitation of the statistical specification.

Implementation, computation, and model specification can produce similar symptoms. The code may evaluate the wrong model; the algorithm may approximate the intended posterior poorly; or the fitted model may fail to represent the data features required by the target. These explanations require different responses. An indexing error needs a code correction, whereas missing seasonality requires a change in the model structure.

## Start with the failure type

When a fit looks wrong, I try to classify the failure before changing the model:

- **Implementation failure:** dimensions, transformations, offsets, dates, units, or likelihood contributions are wrong.
- **Computational failure:** the intended model is hard for the algorithm to explore or optimize.
- **Model failure:** the fitted model cannot reproduce data features relevant to the analysis target.
- **Target failure:** the model may fit observed data but does not answer the intended prediction or decision question.

The categories can overlap. In Hamiltonian Monte Carlo, divergences may indicate difficult posterior geometry associated with parameterization, prior assumptions, limited information, or a coding error. The diagnostic identifies behavior to investigate, but additional checks are needed to distinguish these causes and choose a revision.

## The statistical computing folk theorem

The statistical computing folk theorem is an informal observation that computational difficulties can reveal problems in the model. Weak information, unrealistic priors, and parameterization can all produce difficult posterior geometry. Implementation errors and limitations of the chosen algorithm are alternative explanations, so computational failure alone does not establish model misspecification.

Increasing runtime is justified when additional draws reduce Monte Carlo error for a sampler that explores the relevant distribution. It does not correct an implementation error or ensure movement between poorly connected regions. Examine the geometry and numerical behavior before deciding whether more iterations address the observed failure.

## Localize the problem

Two complementary debugging experiments can isolate a problem. Simplify the current model until the failure disappears, and separately add components to a verified small model until the failure appears. Comparing the two sequences can identify the component, data subset, or interaction associated with the change in behavior.

Useful simplifications include:

- fixing selected parameters at reasonable values;
- reducing hierarchy depth;
- shortening a time series;
- removing one data source;
- fitting one group or one season;
- replacing a nonlinear component with a linear approximation;
- using simulated data with known parameters.

These reductions should be temporary and documented. They are not the final analysis. They are diagnostic experiments.

## Posterior predictive checks

Posterior predictive checks compare observed data with data replicated from the fitted model. Select discrepancies that address the reported target, and document any additional checks suggested by the results. Agreement in a marginal distribution does not establish agreement in extremes, temporal dependence, spatial structure, or subgroup behavior.

For a forecasting model, I would check calibration of forecast intervals, behavior at high and low values, residual autocorrelation, seasonal structure, and performance by lead time. For a regression model, I would check residual patterns over covariates and groups. For a dynamic latent-state model, I would check whether latent trajectories imply realistic observed series.

Choose discrepancies that assess the reported target. For upper-tail flood risk, checks confined to the mean do not assess the relevant extremes. For resource allocation by group, report group-specific errors as well as average performance, since the overall summary may not represent the groups affected by the decision.

## Revise one assumption at a time when possible

Model revision should follow the diagnostic. If residuals show temporal dependence, revise the dynamic or error structure. If high values are systematically underpredicted, revise the tail behavior, transformation, covariates, or regime structure. If the posterior is weakly identified, revise the prior, data design, or target summary. If computation fails because of a funnel, try a noncentered parameterization or stronger scale information.

Assess whether a discrepancy changes the target estimate, conflicts with a scientific assumption, or limits the reported interpretation. Additional flexibility can improve in-sample agreement while increasing computational cost or weakening identification. Evaluate the proposed revision using the original diagnostic and the predictive or inferential criterion specified for the analysis.

## Sensitivity analysis

Some assumptions are poorly identified by the available data. Priors on weakly identified parameters, missing-data mechanisms, tail behavior, and extrapolation rules may therefore require sensitivity analysis. Specify plausible alternatives and compare the resulting target summaries. Report which conclusions remain stable and which depend on a particular assumption.

Sensitivity analysis should be reported in a way that connects to the decision or scientific statement. If a forecast ranking changes under a plausible prior, say so. If an interval endpoint is stable but a latent parameter is not, separate those results. If the data do not identify a mechanism, the report should not imply that they do.

## A revision loop

A disciplined revision loop is:

1. Identify the failure and the affected target.
2. Determine whether it is implementation, computation, model structure, or target mismatch.
3. Run a minimal diagnostic experiment.
4. Revise the smallest relevant component.
5. Re-run prior, computational, and posterior predictive checks.
6. Record why the revision was made.

Changing one component at a time helps attribute the resulting differences to a specific revision. Where several changes are necessary, record them together and state the limits of that attribution. Retain the diagnostic evidence that motivated each revision so the final specification can be compared with earlier versions.

## References

- Gabry, J., Simpson, D., Vehtari, A., Betancourt, M., and Gelman, A. "Visualization in Bayesian workflow." [Journal of the Royal Statistical Society: Series A](https://doi.org/10.1111/rssa.12378).
- Betancourt, M. "A conceptual introduction to Hamiltonian Monte Carlo." [arXiv:1701.02434](https://arxiv.org/abs/1701.02434).
