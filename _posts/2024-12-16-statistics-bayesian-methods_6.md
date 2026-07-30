---
layout: post
published: true
title: "Iteration, stopping, and reporting"
date: 2024-12-19
updated: 2026-07-29
theme: Bayesian workflow
tags: [bayesian-statistics, reproducibility, reporting]
series: "Bayesian workflow"
series_order: 6
description: "How to stop an iterative Bayesian workflow, control repeated model search, and report what was checked, changed, and left unresolved."
excerpt: "A model is ready to report when it answers the target with acceptable uncertainty, not when every possible discrepancy has disappeared."
math: true
---

Bayesian workflow is iterative by design. Models are built, fit, checked, revised, compared, and sometimes simplified. That iteration is a strength because it lets the analysis respond to data structure and model failure. It is also a risk because repeated model search can blur the distinction between discovery, validation, and final reporting.

The final step of a workflow is therefore not only choosing a model. It is deciding whether the remaining uncertainty and model limitations are acceptable for the target. A workflow should stop because the analysis is adequate for its purpose, not because the model has become impossible to improve.

## Different working modes

Applied modeling often moves through several modes. In an exploratory mode, the analyst tries models to understand data structure, software behavior, and possible failures. Approximate computation and rough checks may be acceptable because the goal is learning. In a development mode, the analyst stabilizes the model, checks simulations, evaluates predictive behavior, and records decisions. In a reporting or deployment mode, the analysis should be reproducible, diagnostics should be complete, and the final evaluation should be protected from uncontrolled repeated tuning.

Problems arise when these modes are mixed. A validation set used repeatedly during model development becomes part of the modeling process. A rough exploratory fit can be overinterpreted. A model selected from many unreported alternatives can appear more certain than it is. The workflow needs a point where the rules become stricter.

## Practical stopping criteria

I consider a model ready to report when these conditions are met:

- The model answers the stated target at the required resolution.
- Major posterior or predictive summaries are stable under reasonable computational settings.
- Monte Carlo or optimization error is small relative to inferential uncertainty.
- Prior and posterior predictive checks do not reveal target-relevant failures.
- Predictive comparisons are designed for the intended future task.
- Conclusions are stable under plausible assumptions that the data cannot resolve.
- Additional complexity gives little practical improvement relative to cost and interpretability.

This is not a proof that the model is true. It is a practical standard for using a model responsibly. Statistical reports should avoid implying more certainty than the workflow supports.

## Repeated search and validation

Every model revision uses information. If the same data are used repeatedly to choose transformations, priors, covariates, interactions, and diagnostics, the final performance estimate can be optimistic. This is not unique to Bayesian analysis. It is a general consequence of researcher degrees of freedom.

Several practices reduce the problem:

- keep a log of material model revisions;
- separate exploratory diagnostics from locked final evaluation when possible;
- use validation designs that reflect the deployment setting;
- report sensitivity to plausible alternatives;
- avoid claiming confirmatory evidence from a test that guided model construction;
- reserve a final holdout or future-data evaluation for high-stakes predictive claims.

In many research settings, a perfect split between exploration and confirmation is not possible. The honest solution is to describe the workflow and state which conclusions are exploratory, predictive, mechanistic, or decision-oriented.

## Reporting the workflow

A good report does not need to list every failed model, but it should include enough information for a reader to understand why the final model is credible. I try to report:

1. The target quantity or prediction task.
2. The data source, preprocessing, exclusions, and timing.
3. The model structure and important assumptions.
4. Prior or regularization choices and their observable implications.
5. Computational method, diagnostics, and remaining numerical limitations.
6. Simulation checks, posterior predictive checks, or calibration checks.
7. Predictive comparison design and uncertainty in score differences.
8. Sensitivity analyses for assumptions not identified by the data.
9. The final limitations and what would change the conclusion.

This structure is useful for papers, technical notes, internal model-review documents, and research software vignettes. It also makes later revision easier because the assumptions are visible.

## Versioning and reproducibility

Model results should be connected to code, data, and environment versions. At minimum, record a repository commit, data snapshot, random seeds, software versions, and the command or configuration used to generate results. For long-running jobs, save logs and intermediate artifacts. For public work, separate generated outputs from source code and document how the outputs were produced.

This is not only about replication by others. It protects the analyst. When a result changes six months later, a recorded workflow makes it possible to determine whether the change came from data, code, dependencies, or the model itself.

## Final audit

Before releasing a model-based analysis, I use a final audit:

- Does the introduction state the actual target?
- Are the reported quantities produced by the model being described?
- Are figures labeled with correct units, dates, and uncertainty definitions?
- Are approximation and computation limitations stated plainly?
- Are predictive claims supported by the validation design?
- Are model weights, posterior probabilities, and score differences interpreted correctly?
- Are unresolved failures either fixed or disclosed?

The purpose of iteration is not to make a model immune to criticism. It is to make the criticism specific, documented, and useful. A clear stopping rule and a careful report turn an exploratory sequence into work that can be evaluated.

## References

- Gelman, A., Vehtari, A., Simpson, D., et al. "Bayesian workflow." [arXiv:2011.01808](https://arxiv.org/abs/2011.01808).
- Vehtari, A., Simpson, D., Gelman, A., Yao, Y., and Gabry, J. "Pareto smoothed importance sampling." [Journal of Machine Learning Research](https://www.jmlr.org/papers/v25/19-556.html).
