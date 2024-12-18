---
layout: post
title: "Bayesian Workflow"
date: 2024-12-10
theme: Review
tags: [statistics, bayesian, methodology]
excerpt: "A review on the recently proposed Bayesian Workflow, and some commentary."
---

## Introduction

- Gelman et al. (2020)
- The purpose is to detangle and structure the complex and dynamic workflow of applied Bayesian Statistics.
- We must distinguish between Bayesian Inference, Bayesian Data analysis, and Bayesian Workflow (BW).
- Bayesian inference is just the formulation and computation of conditional probabilities or posteriors.
- BW includes model building, inference, model checking/improvement, and model comparison (not only for model selection or model averaging) for the better undertaking of these models. This includes fitting and analysis models that, in retrospect, are poor choices, useful but flawed, and worth reporting. 

- Why?
  - Alleviate computational burden through organized and iterative steps for model understanding.
  - Typically, we need to know which model to fit, which assumptions are worth relaxing, and which are not.
  - We want to understand model fitting and its relationship with data for those poor and old choices.
  - Different models yield different conclusions. 

Share diagram in paper or improve it*

Essential ideas in statistics that started as hacks and have been brought into the core of statistics: 
- Multilevel modeling is a formalization of what has been called Empirical Bayes Estimation of priors, expanding the model to fold inference about prior into a fully Bayesian framework.
- Exploratory Data Analysis, a form of predictive model checking.
- Regularization Methods, which have replaced ad hoc variable selection tools in regression.
- Non-parametric models can be considered Bayesian Replacements for procedures such as kernel smoothing.

In each of these cases and many others, a framework of statistical methodology has been expanded to include existing methods, along the way making the methods more modular and potentially useful. 

Statistics is all about uncertainty. In addition to the usual uncertainties in the data and model parameters, we are often uncertain whether we are fitting our models correctly, uncertain about how best to set up and expand our models, and uncertain in their interpretation. 

Once we go beyond simple preassigned designs and analysis, our workflow can be disorderly.
Moreover, practical considerations—especially available time, computational resources, and the severity of the penalty for being wrong—can compel a practitioner to take shortcuts. 



---

## 1. Before Fitting a Model
- **2.1** Choosing an initial model
  - The starting point of almost all analyses is to adapt what has been done before.
- **2.2** Modular construction
  - A Bayesian model is bNaming model modules rather than whole models makes it easier to see connections between seemingly dierent models and adapt them to the specific requirements of the given analysis project.
  - Built from modules which can often be viewed as placeholders to be replaced as necessary.
- **2.3** Scaling and transforming the parameters
  - We like our parameters to be interpretable for both practical and ethical reasons. Complicated transformations can also make parameters more interpretable, thus facilitating the use of prior information.
- **2.4** Prior predictive checking
  - Prior predictive checks are a useful tool to understand the implications of a prior distribution in the context of a generative model.
  - A useful approach is to consider priors on outcomes and then derive a corresponding joint prior
on parameters.
  - Prior predictive simulations is that they can be used to elicit expert prior knowledge on the measurable quantities of interest, which is often easier than soliciting expert opinion on model parameters that are not observable 
- **2.5** Generative and partially generative models
  - Fully Bayesian data analysis requires a generative model—that is, a joint probability distribution
for all the data and parameters.
  - In a Red Box: 
    -Bayesian inference does not require the generative model. All it needs from the data is the likelihood, and different generative models can have the same likelihood.
    - Bayesian data analysis requires the generative model to be able to perform predictive simulation and model checking,
    - Bayesian workflow will consider a series of generative models.
  - Prior and posterior predictive checks can look different under these different generative models, which satisfies the likelihood principle.
  - It is common in Bayesian analysis to use models that are not fully generative. For example, in regression, and survival data with censoring.
  - Bayesian models that use improper priors are not fully generative because they do not have a joint distribution for data and parameters, and it would be impossible to sample from the prior predictive distribution. When we do use improper priors, we think of them as being placeholders or steps along the road to a full Bayesian model with a proper joint distribution over parameters and data.
  - In applied work, complexity often arises from incorporating different sources of data.
  - In a box: We can consider progressing from least to most generative models.
    - At one extreme, completely non-generative methods are defined simply as data summaries, with no model for the data at all.
    - Next come classical statistical models, characterized by probability distributions p(y; \theta) for data y gave parameters \theta, but with no probability distribution for \theta.
    - At the next step are the Bayesian models we usually fit, which are generative on y and \theta but include additional unmodeled data x such as sample sizes, design settings, and hyperparameters; we write such models as p(y, \theta|x).
    - The final step would be a completely generative model p(y, \theta, x) with no “left out” data, 

---

## 2. Fitting a Model

A little of history. Traditionally, Bayesian computation has been performed using a combination of analytic calculation
and normal approximation. Then, in the 1990s, it became possible to perform Bayesian inference for a wide range of models using Gibbs and Metropolis algorithms, sequential Monte Carlo. 
- Variational inference is a generalization of the expectation-maximization (EM) algorithm and can, in the Bayesian context, provide a fast but possibly inaccurate approximation to the posterior distribution.
- Sequential Monte Carlo is a generalization of the Metropolis algorithm that can be applied to any
Bayesian computation.
- HMC is a different generalization of Metropolis that uses gradient computation to move efciently through continuous probability spaces

To safely use an inference algorithm in Bayesian workflow, it is vital that the algorithm provides
strong diagnostics to determine when the computation is unreliable.

- **2.1** Initial values, adaptation, and warmup.
  - Initial values for algorithm procedure such as MC simulations and Variational Bayes are not supposed to matter in the asymptotic limit, but they can matter in practice, and a wrong choice can threaten the validity of the results.
  - Te first state fo those algorithms is refer as to as the warmup phase which is intended to move the simulations from their possibly unrepresentative initial values to something closer to the region of parameter space where the log posterior density is close to its expected value, which is related to the concept of “typical set” in information theory.
    -  (a) to run through a transient phase to reduce the bias due to dependence on the initial values
    -  (b) to provide information about the target distribution to use in setting tuning parameters
    -  (c) quickly flag computationally problematic models
- **2.2** How long to run an iterative algorithm
  - For MCMC algorithms
    - Recommended standard practice is to run at least until \hat{R}, the measure of mixing of chains, is less than 1.01 for all parameters and quantities of interest.
    - Also monitor the multivariate mixing statistic R^*
  -  It might seem like a safe and conservative choice to run MCMC until the effective sample size is in the thousands or Monte Carlo standard error is tiny in comparison to the required precision for parameter interpretation—but if this takes a long time, it limits the number of models that can be fit in the exploration stage.
  -  Another choice in computation is how to best make use of available parallelism, beyond the default of running 4 or 8 separate chains on multiple cores. Instead of increasing the number of iterations, effective variance reduction can also be obtained by increasing the number of parallel chains. 
- **2.3** Approximate algorithms and approximate models
  - Markov chain simulation is a form of approximation where the theoretical error approaches zero
as the number of simulations increases. Unfortunately, running MCMC to convergence is not always a scalable solution as data and
models get large, hence the desire for faster approximations.
  - Techniques:
    - Empirical Bayes
    - Linearization
    - Laplace approximation
    - Nested approximations, like INLA
    - Sometimes data-splitting methods, like expectation propagation,
    - Mode-finding approximations, like variational inference
    - Penalized maximum likelihood.
  - There is no one-size-fits-all approximate inference algorithm
  - Generic diagnostic tools can be used to verify that a particular approximate algorithm reproduces the features of the
posterior that you care about for a specific model.
  - An alternative view is to understand an approximate algorithm as an exact algorithm for an approximate model.
    - Empirical Bayes approximations as replacing a model’s prior distributions with a particular data-dependent point-mass prior. 
    - Laplace approximation can be viewed as a data-dependent linearization of the desired model
    - Nested Laplace approximation uses a linearized conditional posterior as the posited conditional posterior.

- **2.4** Fit fast, fail fast
  - Fail fast when fitting bad models, can be considered as a shortcut that avoids spending a lot of time for (near) perfect inference for a bad model.
  - In a box: There is a large literature on approximate algorithms to fit the desired model fast, but little on algorithms designed to waste as little time as possible on the models that we will ultimately abandon.
    
---

## 3. Using Constructed Data to Find and Understand Problems

- **3.1** Fake-data simulation  

- **3.2** Simulation-based calibration  

- **3.3** Experimentation using constructed data  

---

## 4. Addressing Computational Problems

- **4.1** The folk theorem of statistical computing  

- **4.2** Starting at simple and complex models and meeting in the middle  

- **4.3** Getting a handle on models that take a long time to fit  

- **4.4** Monitoring intermediate quantities  

- **4.5** Stacking to reweight poorly mixing chains  

- **4.6** Posterior distributions with multimodality and other difficult geometry  

- **4.7** Reparameterization  

- **4.8** Marginalization  

- **4.9** Adding prior information  

- **4.10** Adding data  

---

## 5. Evaluating and Using a Fitted Model

- **5.1** Posterior predictive checking  

- **5.2** Cross-validation and influence of individual data points and subsets of the data  

- **5.3** Influence of prior information  

- **5.4** Summarizing inference and propagating uncertainty  

---

## 6. Modifying a Model

- **6.1** Constructing a model for the data  

- **7.2** Incorporating additional data  

- **7.3** Working with prior distributions  

- **7.4** A topology of models  


---

## 7. Understanding and Comparing Multiple Models

- **7.1** Visualizing models in relation to each other  

- **7.2** Cross-validation and model averaging  

- **7.3** Comparing a large number of models 

---

## 8. Modeling as Software Development

- **8.1** Version control smooths collaborations with others and with your past self  

- **8.2** Testing as you go  

- **8.3** Making it essentially reproducible  

- **8.4** Making it readable and maintainable  

## Discussion
