---
layout: post
published: true
title: "From questions to a generative model"
date: 2024-09-29
updated: 2026-07-29
theme: Bayesian workflow
tags: [bayesian-statistics, workflow, modeling]
series: "Bayesian workflow"
series_order: 1
description: "A practical first step in Bayesian workflow: translate a scientific or forecasting question into a generative model that can be checked."
excerpt: "Bayesian analysis starts with a target, a data-generating story, and assumptions that can be inspected before fitting."
math: true
---

Bayesian workflow is not only the posterior calculation. The calculation matters, but it comes after a more basic task: deciding what the analysis is trying to learn and writing assumptions clearly enough that they can be checked. A model can be computationally elegant and still answer the wrong question. A useful workflow keeps the target, the data, and the model connected throughout the analysis.

The first distinction is between an estimand, a prediction target, and a decision quantity. An estimand might be an average treatment effect or a regression coefficient under a specified sampling process. A prediction target might be a future river-flow distribution, a default probability, or a demand interval. A decision quantity adds a loss function or operational threshold. These objects are related, but they are not interchangeable. The model should be built around the object that will be reported or used.

Once the target is explicit, the next question is what population or future setting the analysis should generalize to. In a time-series problem, random cross-validation may not represent the future task. In a grouped data problem, a new observation from an existing group and a new observation from a new group require different predictive distributions. In a sensor or environmental application, the data record may mix true signal, measurement error, missingness, and changes in instrumentation. These details belong in the modeling plan before software is written.

## From data to assumptions

A generative model is useful because it forces the analyst to state how observations could have been produced. This does not mean every model must be a literal physical simulator. It means the model should define enough of the data-generating structure to support simulation, prior predictive checks, posterior predictive checks, and criticism.

A minimal generative description should answer these questions:

- What is random, and what is conditioned on?
- What variables are measured directly, transformed, censored, rounded, or missing?
- Which observations are exchangeable, temporally ordered, spatially linked, or grouped?
- Which parameters describe scientific structure, and which absorb observation noise or nuisance variation?
- What predictions or summaries will be checked after fitting?

These questions prevent a common error: treating the likelihood as the whole applied problem. A likelihood can be enough for formal Bayesian updating, but model checking usually needs a story about replicated data. If the model cannot say what future or repeated data would look like, it is hard to know what a posterior predictive check is checking.

## Model modules

Most useful models are modular. A time-series forecasting model may have an observation equation, a latent state evolution, covariate effects, error terms, and priors on scale parameters. A hierarchical regression may have individual-level variation, group-level variation, and partial pooling. Naming these pieces is not cosmetic. It makes revision possible.

For example, if forecasts are biased at high flows, that could point to an observation model, a nonlinear covariate effect, a missing predictor, or an inadequate state evolution. If all these pieces are hidden inside one monolithic expression, revision becomes guesswork. If they are named, the analyst can ask which assumption is failing.

Modularity also helps with prior work. Existing models are often the best starting point, but they rarely match the new data exactly. A prior implementation can provide a baseline likelihood or computation strategy while other pieces are replaced. The goal is not to invent a new model for every analysis. The goal is to make the reused pieces visible enough that they can be evaluated.

## Priors as predictive statements

Priors are often easier to defend on observable scales than on raw parameter scales. A prior on an autoregressive coefficient, a regression slope, or a variance parameter may be technically convenient but hard to interpret. Before fitting, it is usually more informative to simulate implied data and ask whether those simulated outcomes are plausible.

Prior predictive simulation is especially useful when parameters interact. A weak prior on each component can imply unreasonable outcomes after the components are combined. In hierarchical models, priors on group-level scale parameters can imply too much or too little pooling. In dynamic models, small changes in persistence or innovation variance can produce long-run behavior that was not intended.

The prior predictive check does not prove the prior is correct. It rules out priors that make the model fail before seeing the data. That is already valuable. It also creates a record of what the analyst was willing to assume before observing posterior results.

## A first complete model

The first model should be complete enough to run end to end, not complete enough to be final. It should produce fitted values, predictions, posterior or generalized-posterior summaries, residuals or discrepancy summaries, and simulated replicated data. A simple complete model is usually more useful than an ambitious partial model because it exposes the whole workflow.

A reasonable first model has these properties:

- It answers the stated target at least approximately.
- Its inputs and transformations are reproducible.
- Its priors or regularization choices can be simulated.
- Its computation can be checked on small cases.
- Its predictions can be compared with simple baselines.
- Its failures can be localized to model components.

The point is to create an object that can be criticized. A model that fails clearly is useful. It tells the analyst where the next revision should happen. A model that cannot be checked is much less useful, even if the posterior summaries look precise.

## Pre-fit checklist

Before fitting, I try to make the following items explicit:

1. The target quantity and the future or population setting.
2. The observed data, transformations, exclusions, and missingness rules.
3. The modular generative assumptions.
4. The priors or regularization choices on observable scales.
5. The smallest data example that should run correctly.
6. The posterior or predictive summaries that will be reported.
7. The first checks that would make the model unacceptable.

This checklist is not bureaucratic. It saves time. Most difficult modeling projects fail because the question, data structure, computation, and evaluation target drift apart. Writing them down early makes the later posterior calculation more meaningful.

## References

- Gelman, A., Vehtari, A., Simpson, D., et al. "Bayesian workflow." [arXiv:2011.01808](https://arxiv.org/abs/2011.01808).
- Gelman, A., Carlin, J., Stern, H., Dunson, D., Vehtari, A., and Rubin, D. [Bayesian Data Analysis](http://www.stat.columbia.edu/~gelman/book/).
