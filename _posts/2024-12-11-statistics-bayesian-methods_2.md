---
layout: post
title: "On Bayesian Methodology Part. 2/6"
date: 2024-12-11
theme: Review
tags: [statistics, bayesian, methodology]
excerpt: "Modern Bayesian Methodology: Before and While Fitting a Model "
---


## I. Before Fitting a Model

**Choosing an Initial Model**  
The starting point of almost all analyses is to adapt what has been done before. Drawing from existing methods provides a foundation for further refinement.

**Modular Construction**  
A Bayesian model is built from **modules** rather than whole models. Naming and constructing models in a modular fashion makes it easier to:
- Identify connections between seemingly different models.
- Adapt models to the specific requirements of an analysis project.  

Modules often act as placeholders, which can be replaced or expanded as necessary.

**Scaling and Transforming the Parameters**  
Parameters should be interpretable for both practical and ethical reasons. Transformations can make parameters more meaningful, aiding in:
- Clear communication of results.
- Effective use of prior information.

**Prior Predictive Checking**  
Prior predictive checks are invaluable for understanding the implications of prior distributions within generative models.  

<div class="green-box">
  <strong>Key Approaches</strong>  
  <ul>
    <li>Considering priors on outcomes and deriving corresponding joint priors on parameters.</li>
    <li>Using simulations to elicit expert knowledge on measurable quantities, which is often easier than soliciting opinions on unobservable model parameters.</li>
  </ul>
</div>

**Generative and Partially Generative Models**  
Fully Bayesian data analysis typically requires a **generative model**, a joint probability distribution for all data and parameters.

<div class="yellow-box">
  <strong>Insights</strong>  
  <ul>
    <li>Bayesian inference does not require the generative model. It only needs the likelihood derived from the data, and different generative models can share the same likelihood.</li>
    <li>Bayesian data analysis, however, depends on the generative model to enable predictive simulation and model checking.</li>
    <li>The Bayesian workflow evaluates a series of generative models to improve understanding and predictions.</li>
  </ul>
</div>

Prior and posterior predictive checks can vary under different generative models while satisfying the likelihood principle.  
Some models commonly used in Bayesian analysis are not fully generative:
- Regression models and survival data with censoring.
- Models with improper priors, which lack a joint distribution for data and parameters and cannot sample from the prior predictive distribution. Improper priors often serve as placeholders on the path to a fully Bayesian model.

In applied Bayesian work, complexity often arises from incorporating multiple data sources. This necessitates balancing simplicity with flexibility in modeling.

<div class="green-box">
  <strong>Progression of Generative Models</strong>  
  <ul>
    <li>At one extreme, non-generative methods consist solely of data summaries with no model for the data.</li>
    <li>Classical statistical models provide probability distributions \( p(y; \theta) \) for data \( y \) given parameters \( \theta \), but no distribution for \( \theta \).</li>
    <li>Partially generative Bayesian models include unmodeled data \( x \), such as sample sizes, design settings, or hyperparameters, represented as \( p(y, \theta \mid x) \).</li>
    <li>Fully generative models encompass everything, represented as \( p(y, \theta, x) \), leaving no data “left out.”</li>
  </ul>
</div>


---

## II. Fitting a Model

Bayesian computation has evolved significantly over time. Early methods relied on analytic calculations and normal approximations. In the 1990s, the advent of advanced algorithms expanded the landscape for exploring posterior distributions:
- **Gibbs and Metropolis Algorithms:** Enabled Bayesian inference for many models.
- **Sequential Monte Carlo (SMC):** A generalization of Metropolis applicable to broader Bayesian computations.
- **Variational Inference (VI):** A fast but potentially inaccurate approximation, building on the expectation-maximization (EM) algorithm.
- **Hamiltonian Monte Carlo (HMC):** Uses gradient computations to navigate continuous probability spaces efficiently.

These innovations have revolutionized Bayesian workflow, but safe usage requires strong diagnostics to flag unreliable computations.

### Initial Values, Adaptation, and Warmup
The initial phase of inference algorithms is critical:
- **Initial Values:** While theoretically irrelevant in the asymptotic limit, poor initial values can bias results.
- **Warmup Phase:** Moves simulations from unrepresentative initial values toward the typical set, a concept in information theory. This phase serves three purposes:
  1. Reduces bias from initial values.
  2. Provides information to tune algorithm parameters.
  3. Flags computational issues early.

### How Long to Run an Iterative Algorithm
The duration of iterative algorithms like MCMC impacts result reliability and computational efficiency:
- **Convergence Diagnostics:**  
  - Standard practice: Run until a mixing measure, Vehtari et al. (2020), is below 1.01 for all parameters.  
  - Monitor the multivariate mixing statistic, Lambert and Vehtari (2020).  
- **Balancing Accuracy and Speed:**  
  While increasing adequate sample size or reducing Monte Carlo error improves accuracy, it limits model exploration if computation is too slow.
- **Leveraging Parallelism:**  
  Instead of increasing iterations, variance reduction can be achieved by increasing parallel chains.

### Approximate Algorithms and Models
Markov chain simulation is an approximation where theoretical error reduces with more iterations. However, scalability challenges arise as models and datasets grow larger, necessitating faster alternatives:
- **Techniques for Approximation:**  
  - Empirical Bayes  
  - Linearization  
  - Laplace approximation  
  - Nested approximations (e.g., INLA)  
  - Data-splitting (e.g., expectation propagation)  
  - Mode-finding (e.g., variational inference)  
  - Penalized maximum likelihood  

- **Diagnostics for Approximate Algorithms:**  
  Use diagnostic tools to ensure the algorithm reproduces key posterior features for the specific model.

<div class="yellow-box">
  <strong>Insights</strong>: Approximate algorithms can be viewed as exact algorithms for approximate models.  
  <ul>
    <li> <strong>Empirical Bayes:</strong>   Replaces prior distributions with data-dependent point-mass priors. </li>
    <li> strong>Laplace Approximation:</strong>   Data-dependent linearization of the model.   </li>
    <li> <strong>Nested Laplace Approximation:</strong>   Linearizes conditional posterior distributions.</li>
  </ul>
</div>

### Fit Fast, Fail Fast
Efficient Bayesian workflow emphasizes quickly identifying and discarding flawed models:
- **Failing Fast:** Saves time by avoiding perfect inference for fundamentally flawed models.
  
<div class="red-box">
  <strong>Fast Algorithms vs. Early Failure</strong>  
  There is extensive literature on fast approximation algorithms to fit desired models, but less focus on algorithms designed to minimize time spent on models that will ultimately be abandoned.
</div>
