---
layout: post
published: true
title: "Comparing and combining predictive models"
date: 2024-12-02
updated: 2026-10-27
last_modified_at: 2026-10-27
theme: Bayesian workflow
tags: [bayesian-statistics, forecasting, model-comparison]
series: "Bayesian workflow"
series_order: 5
description: "Predictive model comparison with task-specific validation, proper scores, stacking, Bayesian model averaging, and projection predictive inference."
excerpt: "Model comparison should match the prediction task, report uncertainty, and avoid treating stacking weights as posterior model probabilities."
math: true
---

Model comparison begins with the prediction task. A score computed under the wrong validation design can be precise and still misleading. If the future task is forecasting the next month, random folds that mix future and past observations are not the right test. If the future task is prediction for new groups, validation should hold out groups rather than individual rows. If preprocessing uses the full dataset before splitting, information can leak into the evaluation.

The evaluation should reproduce the intended prediction setting. Specify when covariates become available, which observations are grouped, how temporal or spatial dependence is handled, and which loss corresponds to the intended use. A model ranking obtained under one score or split design need not apply to a different target or population.

## Proper scores and uncertainty

For probabilistic forecasts, proper scoring rules reward calibrated and sharp predictive distributions. Log predictive density, continuous ranked probability score, energy score, variogram score, interval score, and quantile score emphasize different features. The score should be chosen because it matches the target, not because it is convenient.

Report uncertainty in average score differences. Sampling variability and dependence across validation folds can make small differences inconclusive. Selecting the best estimated score from many candidate models also introduces selection optimism. The reported uncertainty and interpretation should account for the comparison design and the extent of model selection.

Report performance by subgroup, response range, and forecast lead time when those distinctions affect the intended use. An overall mean can obscure systematic errors in a small subset of observations. For rare-event forecasts, include the number and type of events represented in validation so readers can assess how much evidence supports tail-performance claims.

## Cross-validation design

Cross-validation estimates predictive performance under a specific data-generating and data-splitting scheme. The split design is part of the estimand. For independent and identically distributed rows, random folds may be reasonable. For time series, blocked or rolling-origin validation is often more appropriate. For hierarchical data, leaving out groups may answer a different question than leaving out observations within known groups.

All preprocessing that would be unavailable at prediction time should happen inside each training fold. This includes scaling, feature selection, imputation, tuning, and sometimes transformation choices. Otherwise the validation score can be too optimistic.

## PSIS-LOO and diagnostics

Pareto-smoothed importance sampling leave-one-out cross-validation reuses posterior draws from the full-data fit to estimate leave-one-out predictive accuracy. Large Pareto $$k$$ values indicate unreliable importance-sampling estimates. Depending on the source of the problem, further analysis may require exact refits for affected observations, a different validation design, or a revision of the model.

PSIS-LOO estimates pointwise out-of-sample predictive accuracy under a leave-one-observation structure. It does not automatically validate time-series extrapolation, new-group prediction, or decisions with asymmetric costs. The interpretation depends on whether the leave-one-out task matches the target.

## Stacking

Stacking combines predictive distributions using weights estimated under a validation criterion. Models can contribute different predictive features, so a combination may score better than any individual member. Its performance must still be evaluated under the stated prediction task, with the weight-estimation step included in the evaluation design.

Stacking weights should not be read as posterior probabilities that each model is true. They are optimization weights for prediction under a specified criterion and validation design. A model can receive a high stacking weight because it complements other models, not because it is the most plausible data-generating mechanism. Conversely, a useful diagnostic model may receive a low weight because it adds little to the ensemble.

## Bayesian model averaging

Bayesian model averaging uses posterior model probabilities defined by a model space, model-specific priors, and prior probabilities on models. Its interpretation depends on those specifications and on the stability of the marginal-likelihood calculation. When candidates arise through successive diagnostic revisions, describe how that collection was constructed. Predictive comparison or stacking may be more suitable if the objective is forecast accuracy over this selected collection rather than inference about model probabilities.

## Projection predictive inference

Projection predictive inference seeks a reduced model that approximates a fitted reference model's predictions. The reference model is fitted first, and candidate reductions are assessed relative to its predictive distribution. This separates predictive reduction from an unrestricted search for the best noisy validation score among independently fitted small models.

A reduced model may be required because of measurement costs, computational constraints, or interpretation. State which inputs or components can be removed and how much predictive deviation is acceptable. The resulting model is assessed relative to the reference distribution; its interpretation therefore also depends on the reference model's adequacy.

## What to report

A comparison report should specify the validation design, scoring rule, uncertainty in score differences, diagnostic warnings, and subgroup or tail results. Identify whether the final output is a single model, a stacked distribution, or a reduced projection. Predictive accuracy under this design supports a claim about the specified prediction task; it does not establish a correct scientific mechanism.

## References

- Vehtari, A., Gelman, A., and Gabry, J. "Practical Bayesian model evaluation using leave-one-out cross-validation and WAIC." [Statistics and Computing](https://doi.org/10.1007/s11222-016-9696-4).
- Yao, Y., Vehtari, A., Simpson, D., and Gelman, A. "Using stacking to average Bayesian predictive distributions." [Bayesian Analysis](https://doi.org/10.1214/17-BA1091).
