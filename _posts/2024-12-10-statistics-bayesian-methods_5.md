---
layout: post
published: true
title: "Comparing and combining predictive models"
date: 2024-12-02
updated: 2026-07-29
theme: Bayesian workflow
tags: [bayesian-statistics, forecasting, model-comparison]
series: "Bayesian workflow"
series_order: 5
description: "A practical guide to predictive model comparison, validation design, proper scores, stacking, Bayesian model averaging, and projection predictive inference."
excerpt: "Model comparison should match the prediction task, report uncertainty, and avoid treating stacking weights as posterior model probabilities."
math: true
---

Model comparison begins with the prediction task. A score computed under the wrong validation design can be precise and still misleading. If the future task is forecasting the next month, random folds that mix future and past observations are not the right test. If the future task is prediction for new groups, validation should hold out groups rather than individual rows. If preprocessing uses the full dataset before splitting, information can leak into the evaluation.

The comparison should reproduce the deployment setting as closely as possible. That includes the timing of covariates, data availability at prediction time, grouping structure, spatial or temporal dependence, and the loss function that matters. A model that wins under one score or split design may not be better for a different target.

## Proper scores and uncertainty

For probabilistic forecasts, proper scoring rules reward calibrated and sharp predictive distributions. Log predictive density, continuous ranked probability score, energy score, variogram score, interval score, and quantile score emphasize different features. The score should be chosen because it matches the target, not because it is convenient.

Average score differences should be reported with uncertainty. A small difference can be overwhelmed by sampling variability, dependence across folds, or the number of candidate models tried. Selecting the model with the best noisy estimate creates optimism. This is especially important when many models are compared after repeated exploration.

The best average score is also not the whole story. Subgroup performance, tail behavior, lead-time performance, and failure modes can matter more than a single average. In forecasting, the average score may hide poor behavior during rare but important events.

## Cross-validation design

Cross-validation estimates predictive performance under a specific data-generating and data-splitting scheme. The split design is part of the estimand. For independent and identically distributed rows, random folds may be reasonable. For time series, blocked or rolling-origin validation is often more appropriate. For hierarchical data, leaving out groups may answer a different question than leaving out observations within known groups.

All preprocessing that would be unavailable at prediction time should happen inside each training fold. This includes scaling, feature selection, imputation, tuning, and sometimes transformation choices. Otherwise the validation score can be too optimistic.

## PSIS-LOO and diagnostics

Pareto-smoothed importance sampling leave-one-out cross-validation can be efficient for Bayesian models because it reuses posterior draws from the full-data fit. Its diagnostics are essential. Large Pareto $$k$$ values indicate that the approximation to leaving out an observation is unreliable. The fix may be exact refitting for problematic points, a different validation design, or a model revision.

PSIS-LOO estimates pointwise out-of-sample predictive accuracy under a leave-one-observation structure. It does not automatically validate time-series extrapolation, new-group prediction, or decisions with asymmetric costs. The interpretation depends on whether the leave-one-out task matches the target.

## Stacking

Stacking combines predictive distributions by choosing weights that optimize predictive performance under a validation criterion. It can be useful when different models capture different parts of the data. The combined forecast can outperform each individual model under the chosen score.

Stacking weights should not be read as posterior probabilities that each model is true. They are optimization weights for prediction under a specified criterion and validation design. A model can receive a high stacking weight because it complements other models, not because it is the most plausible data-generating mechanism. Conversely, a useful diagnostic model may receive a low weight because it adds little to the ensemble.

## Bayesian model averaging

Bayesian model averaging is different. It averages over models using posterior model probabilities under a model space and prior probabilities on models. This can be principled when the model list is meaningful, the priors are defensible, and the likelihood comparison is stable. In many applied workflows, the candidate models are not a clean exhaustive model space. They are a sequence of approximations, diagnostics, and engineering choices. In that setting, stacking or explicit predictive comparison may be more transparent.

## Projection predictive inference

When the goal is a smaller model rather than the single best model, projection predictive inference is useful. A rich reference model is fit first. Smaller models are then chosen by how well they approximate the reference model's predictions. This avoids fitting every small model independently and selecting the one with the noisiest validation advantage.

Projection is especially useful when a complex model is acceptable for discovery but a smaller model is needed for deployment, interpretation, or cost. The target is not truth in an absolute sense. The target is predictive behavior close to the reference model with fewer inputs or simpler structure.

## What to report

A useful comparison report includes the validation design, the score, uncertainty in score differences, diagnostic warnings, subgroup or tail behavior, and whether the final choice was a single model, a stacked combination, or a reduced projection. It should also state what the comparison does not establish. A good score does not prove the model is mechanistically correct. It supports a predictive claim under the evaluation design.

## References

- Vehtari, A., Gelman, A., and Gabry, J. "Practical Bayesian model evaluation using leave-one-out cross-validation and WAIC." [Statistics and Computing](https://doi.org/10.1007/s11222-016-9696-4).
- Yao, Y., Vehtari, A., Simpson, D., and Gelman, A. "Using stacking to average Bayesian predictive distributions." [Bayesian Analysis](https://doi.org/10.1214/17-BA1091).
