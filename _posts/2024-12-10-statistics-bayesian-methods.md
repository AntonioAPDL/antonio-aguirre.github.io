---
layout: post
published: true
title: "From questions to a generative model"
date: 2024-09-29
updated: 2026-10-27
last_modified_at: 2026-10-27
theme: Bayesian workflow
tags: [bayesian-statistics, workflow, modeling]
series: "Bayesian workflow"
series_order: 1
description: "Specify an analysis target, describe the observation process, and assess the predictive implications of a generative model before fitting."
excerpt: "Define the target quantity, observation process, and modeling assumptions before computing a posterior."
math: true
---

Before computing a posterior, an analysis needs a defined target and a description of how the observations were obtained. The target determines which model outputs are relevant; the observation process determines which assumptions are needed to interpret them. These choices guide model construction, computation, and evaluation throughout a Bayesian analysis.

The first distinction is between an estimand, a prediction target, and a decision quantity. An estimand might be an average treatment effect or a regression coefficient under a specified sampling process. A prediction target might be a future river-flow distribution, a default probability, or a demand interval. A decision quantity adds a loss function or operational threshold. These objects are related, but they are not interchangeable. The model should be built around the object that will be reported or used.

Once the target is explicit, the next question is what population or future setting the analysis should generalize to. In a time-series problem, random cross-validation may not represent the future task. In a grouped data problem, a new observation from an existing group and a new observation from a new group require different predictive distributions. In a sensor or environmental application, the data record may mix true signal, measurement error, missingness, and changes in instrumentation. These details belong in the modeling plan before software is written.

## From data to assumptions

A generative model describes how observations could arise under specified assumptions. It need not reproduce the physical process in every detail. It must specify the distributions and dependencies needed to simulate observations, examine prior and posterior predictive behavior, and assess discrepancies relevant to the analysis target.

A minimal generative description should answer these questions:

- What is random, and what is conditioned on?
- What variables are measured directly, transformed, censored, rounded, or missing?
- Which observations are exchangeable, temporally ordered, spatially linked, or grouped?
- Which parameters describe scientific structure, and which absorb observation noise or nuisance variation?
- What predictions or summaries will be checked after fitting?

The likelihood describes the observed-data contribution to Bayesian updating. Predictive checking additionally requires a specification of replicated data: which quantities are generated again, which are conditioned on, and which sampling or measurement features are retained. These choices determine the interpretation of a posterior predictive comparison.

## Model modules

A model can be organized into components with separate statistical roles. A time-series model may include an observation equation, latent-state evolution, covariate effects, and scale priors. A hierarchical regression may separate individual-level and group-level variation through partial pooling. Describing these components separately helps identify which assumption to revise when a diagnostic fails.

For example, systematic underprediction at high response values could arise from the observation distribution, a missing nonlinear effect, an omitted predictor, or the state evolution. Separate components allow these explanations to be examined through reduced fits and targeted predictive checks. A discrepancy alone does not identify which explanation is correct.

Existing models can supply an initial observation distribution or computational method while other components are adapted to the new setting. Document which components are retained, which are changed, and why. Reused code still needs checks for the new data dimensions, units, transformations, and predictive task.

## Priors as predictive statements

Priors are often easier to defend on observable scales than on raw parameter scales. A prior on an autoregressive coefficient, a regression slope, or a variance parameter may be technically convenient but hard to interpret. Before fitting, it is usually more informative to simulate implied data and ask whether those simulated outcomes are plausible.

Individually broad priors can imply implausible outcomes when parameters interact. In hierarchical models, group-level scale priors control the degree of pooling. In dynamic models, persistence and innovation variance jointly determine long-run behavior. Prior predictive simulation assesses these combined implications on the response scale, where unrealistic ranges or trajectories can be compared with domain knowledge.

Prior predictive checks can identify implications that conflict with available domain knowledge before posterior results are examined. Passing these checks does not establish that a prior is correct. Record the simulated ranges, dependencies, and extreme outcomes considered acceptable, together with the reasons for that assessment.

## A first complete model

An initial model should support the complete analysis, from data preparation through the summaries and checks required by the target. For a generative Bayesian model, these include fitted values, predictions, posterior summaries, discrepancy measures, and replicated data. Starting with a limited specification allows each stage to be tested before additional components are introduced.

A reasonable first model has these properties:

- It answers the stated target at least approximately.
- Its inputs and transformations are reproducible.
- Its priors or regularization choices can be simulated.
- Its computation can be checked on small cases.
- Its predictions can be compared with simple baselines.
- Its failures can be localized to model components.

Specify how each reported output will be evaluated. A discrepancy is easier to investigate when it can be connected to a particular model component or data-processing step. Narrow posterior intervals alone do not establish that the model represents the relevant features of the data.

## Pre-fit checklist

Before fitting, I try to make the following items explicit:

1. The target quantity and the future or population setting.
2. The observed data, transformations, exclusions, and missingness rules.
3. The modular generative assumptions.
4. The priors or regularization choices on observable scales.
5. The smallest data example that should run correctly.
6. The posterior or predictive summaries that will be reported.
7. The first checks that would make the model unacceptable.

Keep this specification with the analysis code and revise it when the target or data change. It provides a basis for checking whether a later model revision still answers the original question, or whether the scope of the analysis has changed and requires a different evaluation.

## References

- Gelman, A., Vehtari, A., Simpson, D., et al. "Bayesian workflow." [arXiv:2011.01808](https://arxiv.org/abs/2011.01808).
- Gelman, A., Carlin, J., Stern, H., Dunson, D., Vehtari, A., and Rubin, D. [Bayesian Data Analysis](http://www.stat.columbia.edu/~gelman/book/).
