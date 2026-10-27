---
layout: post
published: true
title: "Iteration, stopping, and reporting"
date: 2024-12-19
updated: 2026-10-27
last_modified_at: 2026-10-27
theme: Bayesian workflow
tags: [bayesian-statistics, reproducibility, reporting]
series: "Bayesian workflow"
series_order: 6
description: "How to stop an iterative Bayesian workflow, control repeated model search, and report what was checked, changed, and left unresolved."
excerpt: "A model is ready to report when it answers the target with acceptable uncertainty, not when every possible discrepancy has disappeared."
math: true
---

Bayesian analyses commonly involve repeated model construction, fitting, checking, and revision. Each revision uses information from the data and previous results. The report should distinguish exploratory changes from the procedure used for final evaluation, particularly when the same observations informed both model selection and performance assessment.

Before reporting results, assess whether the remaining uncertainty and model limitations are acceptable for the target. This requires a defined precision or predictive requirement and a record of unresolved discrepancies. Further model development may be possible even when the current analysis meets those requirements.

## Different working modes

Applied modeling often moves through several modes. In an exploratory mode, the analyst tries models to understand data structure, software behavior, and possible failures. Approximate computation and rough checks may be acceptable because the goal is learning. In a development mode, the analyst stabilizes the model, checks simulations, evaluates predictive behavior, and records decisions. In a reporting or deployment mode, the analysis should be reproducible, diagnostics should be complete, and the final evaluation should be protected from uncontrolled repeated tuning.

A validation set consulted repeatedly during development contributes to model selection. Its results should not then be described as an untouched final evaluation. Similarly, an exploratory fit needs further computational checks before reporting, and selection from many alternatives should be disclosed. Specify the transition to final evaluation and which model choices are fixed at that stage.

## Practical stopping criteria

I consider a model ready to report when these conditions are met:

- The model answers the stated target at the required resolution.
- Major posterior or predictive summaries are stable under reasonable computational settings.
- Monte Carlo or optimization error is small relative to inferential uncertainty.
- Prior and posterior predictive checks do not reveal target-relevant failures.
- Predictive comparisons are designed for the intended future task.
- Conclusions are stable under plausible assumptions that the data cannot resolve.
- Additional complexity gives little practical improvement relative to cost and interpretability.

These criteria concern adequacy for a specified task, not the truth of the complete model. Record the tolerance used for numerical error, the predictive failures considered unacceptable, and the assumptions examined in sensitivity analysis. Readers can then assess the basis for stopping and the scope of the conclusions.

## Repeated search and validation

Every model revision uses information. If the same data are used repeatedly to choose transformations, priors, covariates, interactions, and diagnostics, the final performance estimate can be optimistic. This is not unique to Bayesian analysis. It is a general consequence of researcher degrees of freedom.

Several practices reduce the problem:

- keep a log of material model revisions;
- separate exploratory diagnostics from locked final evaluation when possible;
- use validation designs that reflect the deployment setting;
- report sensitivity to plausible alternatives;
- avoid claiming confirmatory evidence from a test that guided model construction;
- reserve a final holdout or future-data evaluation for high-stakes predictive claims.

When exploration and confirmation cannot be separated, describe how the data informed successive choices. State which conclusions are exploratory and which have independent predictive or confirmatory support. A transparent account of data reuse is necessary to interpret the reported evidence and any limitations of the final evaluation.

## Reporting the workflow

A report should describe the revisions that affected the target, model assumptions, computation, or interpretation. Minor exploratory variations need not all receive equal attention, but readers need enough information to reconstruct the main decisions. I include:

1. The target quantity or prediction task.
2. The data source, preprocessing, exclusions, and timing.
3. The model structure and assumptions governing the reported inference.
4. Prior or regularization choices and their observable implications.
5. Computational method, diagnostics, and remaining numerical limitations.
6. Simulation checks, posterior predictive checks, or calibration checks.
7. Predictive comparison design and uncertainty in score differences.
8. Sensitivity analyses for assumptions not identified by the data.
9. The final limitations and what would change the conclusion.

The same information can support a paper, technical note, model-review document, or software vignette. Organizing it consistently allows a later revision to identify which assumptions, inputs, and checks have changed, and which earlier results remain applicable.

## Versioning and reproducibility

Model results should be connected to code, data, and environment versions. At minimum, record a repository commit, data snapshot, random seeds, software versions, and the command or configuration used to generate results. For long-running jobs, save logs and intermediate artifacts. For public work, separate generated outputs from source code and document how the outputs were produced.

When a result changes, the run record should distinguish changes in data, code, dependencies, configuration, and model specification. Keep enough provenance to rerun the earlier calculation as well as the revised one, subject to any restrictions on the underlying data.

## Final audit

Before releasing a model-based analysis, I use a final audit:

- Does the introduction state the actual target?
- Are the reported quantities produced by the model being described?
- Are figures labeled with correct units, dates, and uncertainty definitions?
- Are approximation and computation limitations stated plainly?
- Are predictive claims supported by the validation design?
- Are model weights, posterior probabilities, and score differences interpreted correctly?
- Are unresolved failures either fixed or disclosed?

Document the stopping criteria, diagnostic results, and limitations alongside the final model specification. This record allows readers to assess which revisions were supported by evidence, whether unresolved discrepancies affect the target, and what additional observations or checks would be needed to extend the conclusions.

## References

- Gelman, A., Vehtari, A., Simpson, D., et al. "Bayesian workflow." [arXiv:2011.01808](https://arxiv.org/abs/2011.01808).
- Vehtari, A., Simpson, D., Gelman, A., Yao, Y., and Gabry, J. "Pareto smoothed importance sampling." [Journal of Machine Learning Research](https://www.jmlr.org/papers/v25/19-556.html).
