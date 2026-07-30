---
layout: post
published: true
title: "Diagnosing fit and revising the model"
date: 2024-11-13
updated: 2026-07-29
theme: Bayesian workflow
tags: [bayesian-statistics, diagnostics, model-checking]
series: "Bayesian workflow"
series_order: 4
description: "How to separate computational failure from model failure, use posterior predictive checks, and revise a Bayesian model without losing the target."
excerpt: "A failed diagnostic should lead to a specific revision: code, computation, parameterization, prior information, or model structure."
math: true
---

Model checking is useful only if it leads to a disciplined response. A poor fit, a divergent transition, a biased residual pattern, or an unstable forecast should not trigger an automatic search for a larger model. The first task is to identify what kind of failure is being observed.

There are at least three different failures that often look similar in practice. The code may not implement the intended model. The computation may not approximate the posterior or generalized posterior well. The model may be a poor description of the data-generating process for the target being studied. Revising the wrong layer can waste substantial time. Adding covariates will not fix an indexing bug. Running more iterations will not fix an impossible prior predictive distribution. Reparameterizing may not fix a missing seasonal component.

## Start with the failure type

When a fit looks wrong, I try to classify the failure before changing the model:

- **Implementation failure:** dimensions, transformations, offsets, dates, units, or likelihood contributions are wrong.
- **Computational failure:** the intended model is hard for the algorithm to explore or optimize.
- **Model failure:** the fitted model cannot reproduce features of the data that matter.
- **Target failure:** the model may fit observed data but does not answer the intended prediction or decision question.

This separation is not always clean, but it is a useful starting point. For example, in Hamiltonian Monte Carlo, divergences may indicate difficult posterior geometry. That geometry may come from a centered parameterization, a weak prior, a funnel-shaped hierarchy, a coding mistake, or a real lack of information. The diagnostic points to a region that needs investigation; it does not name the repair by itself.

## The statistical computing folk theorem

The informal folk theorem says that computational problems often reveal model problems. This is a useful heuristic, not a theorem. Poor computation can be caused by model geometry that reflects weak information, unrealistic priors, or awkward parameterization. It can also be caused by a software mistake or by asking an algorithm to solve a problem outside its strengths.

The practical lesson is to inspect the model rather than only increasing runtime. More computation is appropriate after the geometry and implementation are understood. Before that, it can hide the issue. A chain that eventually produces many draws from a poorly parameterized model may still leave the analyst with a fragile workflow.

## Localize the problem

A good debugging strategy moves in both directions. Simplify the current model until the failure disappears. Separately, start from a small model that works and add components until the failure appears. The point where behavior changes is often more informative than the final failed model.

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

Posterior predictive checks compare observed data with data replicated from the fitted model. They are most useful when the discrepancy is chosen before looking only at the most convenient summary. A model can match the marginal distribution while failing on extremes, temporal dependence, spatial structure, or subgroup behavior.

For a forecasting model, I would check calibration of forecast intervals, behavior at high and low values, residual autocorrelation, seasonal structure, and performance by lead time. For a regression model, I would check residual patterns over covariates and groups. For a dynamic latent-state model, I would check whether latent trajectories imply realistic observed series.

The check should be tied to the target. If the analysis reports upper-tail flood risk, a posterior predictive check that only examines the mean is insufficient. If the analysis supports resource allocation by group, average predictive performance can hide unacceptable subgroup errors.

## Revise one assumption at a time when possible

Model revision should follow the diagnostic. If residuals show temporal dependence, revise the dynamic or error structure. If high values are systematically underpredicted, revise the tail behavior, transformation, covariates, or regime structure. If the posterior is weakly identified, revise the prior, data design, or target summary. If computation fails because of a funnel, try a noncentered parameterization or stronger scale information.

Not every discrepancy deserves a model expansion. A discrepancy matters when it affects the target, reveals a known scientific mechanism, or undermines the interpretation being reported. A model can always be made more flexible, but flexibility can hide misspecification and make computation harder. The revision should improve the analysis, not only the appearance of fit.

## Sensitivity analysis

Some assumptions cannot be learned well from the available data. Priors on weakly identified parameters, missing-data mechanisms, tail behavior, and extrapolation rules often need sensitivity analysis. The question is not whether the analyst can find one assumption that gives a preferred result. The question is whether the conclusion is stable across assumptions that remain plausible.

Sensitivity analysis should be reported in a way that connects to the decision or scientific statement. If a forecast ranking changes under a plausible prior, say so. If an interval endpoint is stable but a latent parameter is not, separate those results. If the data do not identify a mechanism, the report should not imply that they do.

## A revision loop

A disciplined revision loop is:

1. Identify the failure and the affected target.
2. Determine whether it is implementation, computation, model structure, or target mismatch.
3. Run a minimal diagnostic experiment.
4. Revise the smallest relevant component.
5. Re-run prior, computational, and posterior predictive checks.
6. Record why the revision was made.

This loop is slower than trying many changes at once, but it produces an analysis that can be explained. The final model is not just the one that survived. It is the result of a documented sequence of checks and revisions.

## References

- Gabry, J., Simpson, D., Vehtari, A., Betancourt, M., and Gelman, A. "Visualization in Bayesian workflow." [Journal of the Royal Statistical Society: Series A](https://doi.org/10.1111/rssa.12378).
- Betancourt, M. "A conceptual introduction to Hamiltonian Monte Carlo." [arXiv:1701.02434](https://arxiv.org/abs/1701.02434).
