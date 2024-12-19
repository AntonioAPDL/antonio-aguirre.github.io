---
layout: post
title: "A review on 'Bayesian Workflow'"
date: 2024-12-10
theme: Review
tags: [statistics, bayesian, methodology]
excerpt: "A review on the recently proposed Bayesian Workflow, and some commentary."
---

# Bayesian Workflow: A Structured Review

The **Bayesian Workflow (BW)** is a critical framework for applied Bayesian Statistics, designed to detangle and organize the complex processes involved. This review builds upon the ideas presented in Gelman et al. (2020) and offers additional insights.

---

## Introduction

Bayesian Workflow (BW) provides a structured approach to managing the dynamic and iterative nature of applied Bayesian Statistics. It’s helpful to differentiate three closely related concepts:

1. **Bayesian Inference:**  
   The computation of conditional probabilities or posterior distributions.

2. **Bayesian Data Analysis:**  
   The application of Bayesian inference to specific datasets.

3. **Bayesian Workflow (BW):**  
   A broader framework that includes:
   - Model building
   - Inference
   - Model checking and improvement
   - Model comparison (not limited to selection or averaging)

The workflow emphasizes the value of analyzing models that may initially seem flawed or suboptimal, as they often provide important insights.

---

## Why Is Bayesian Workflow Important?

A well-defined Bayesian Workflow addresses several challenges in statistical modeling:

- **Organized Model Understanding:**  
  It alleviates computational burdens by structuring model evaluation and refinement into manageable steps.

- **Better Decision-Making:**  
  It helps practitioners identify which assumptions to relax and which to retain, enabling more thoughtful model selection.

- **Model-Data Relationships:**  
  Understanding how models fit the data, even when models are poor choices, can provide useful insights.

- **Diverse Conclusions:**  
  Different models often lead to different conclusions; BW encourages practitioners to explore and understand these variations.

---

## Key Ideas in Bayesian Workflow

### Referencing the Diagram  
The paper by Gelman et al. (2020) provides a useful diagram summarizing the Bayesian Workflow. Enhancing this diagram could offer even more clarity on the process.

### Integrating Statistical Innovations  
Many statistical methodologies began as informal techniques or "hacks" and have since been formalized within Bayesian frameworks. Key examples include:

- **Multilevel Modeling:**  
  Extends empirical Bayes methods by incorporating prior inference directly into Bayesian models.

- **Exploratory Data Analysis (EDA):**  
  Functions as a form of predictive model checking.

- **Regularization Techniques:**  
  Replace ad hoc variable selection methods in regression, offering more robust solutions.

- **Non-parametric Models:**  
  Serve as Bayesian replacements for techniques like kernel smoothing, broadening their application.

These methods have expanded statistical frameworks, making them more modular and adaptable while retaining their core principles.

---

## Statistics and Uncertainty

At its heart, statistics is about managing uncertainty. Bayesian Workflow recognizes and addresses uncertainty in several forms:

- **Data and Model Parameters:**  
  Variability and imprecision inherent in the data and parameters.

- **Model Fitting:**  
  Challenges in determining whether a model is appropriately specified.

- **Model Setup and Expansion:**  
  Difficulty in deciding how to structure and extend models to capture key dynamics.

- **Interpretation:**  
  Ambiguity in translating statistical results into meaningful conclusions.

Workflows often become disorderly when moving beyond predefined designs and analyses. Practical constraints—such as limited time, computational resources, and the consequences of incorrect decisions—frequently necessitate shortcuts. A structured Bayesian Workflow mitigates these challenges by offering a systematic approach to balancing rigor with practicality.

---

The Bayesian Workflow provides a comprehensive framework for organizing applied Bayesian Statistics. It embraces the iterative nature of statistical modeling, acknowledges the importance of learning from flawed models, and prioritizes the exploration of uncertainty. By following these structured principles, practitioners can make informed, defensible decisions while navigating the complexities of statistical analysis.

For those interested in exploring this further, I recommend reviewing Gelman et al. (2020) and considering how these principles can be applied in your own work. 

---

## Before Fitting a Model

**Choosing an Initial Model**  
The starting point of almost all analyses is to adapt what has been done before. Drawing from existing methods provides a foundation for further refinement.

---

**Modular Construction**  
A Bayesian model is built from **modules** rather than whole models. Naming and constructing models in a modular fashion makes it easier to:
- Identify connections between seemingly different models.
- Adapt models to the specific requirements of an analysis project.  

Modules often act as placeholders, which can be replaced or expanded as necessary.

---

**Scaling and Transforming the Parameters**  
Parameters should be interpretable for both practical and ethical reasons. Transformations can make parameters more meaningful, aiding in:
- Clear communication of results.
- Effective use of prior information.

---

**Prior Predictive Checking**  
Prior predictive checks are invaluable for understanding the implications of prior distributions within generative models.  
Key approaches include:
- Considering priors on outcomes and deriving corresponding joint priors on parameters.
- Using simulations to elicit expert knowledge on measurable quantities, which is often easier than soliciting opinions on unobservable model parameters.

---

**Generative and Partially Generative Models**  
Fully Bayesian data analysis typically requires a **generative model**, which is a joint probability distribution for all data and parameters.

<div class="red-box">
  <strong>Key Insights About Bayesian Inference and Generative Models</strong>  
  <ul>
    <li>Bayesian inference does not require the generative model. It only needs the likelihood derived from the data, and different generative models can share the same likelihood.</li>
    <li>Bayesian data analysis, however, depends on the generative model to enable predictive simulation and model checking.</li>
    <li>The Bayesian workflow evaluates a series of generative models to improve understanding and predictions.</li>
  </ul>
</div>

---

Prior and posterior predictive checks can vary under different generative models while still satisfying the likelihood principle.  
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

## Fitting a Model

### Historical Context
Bayesian computation has evolved significantly over time. Early methods relied on analytic calculations and normal approximations. In the 1990s, the advent of advanced algorithms expanded the landscape:
- **Gibbs and Metropolis Algorithms:** Enabled Bayesian inference for a wide range of models.
- **Sequential Monte Carlo (SMC):** A generalization of Metropolis applicable to broader Bayesian computations.
- **Variational Inference (VI):** A fast but potentially inaccurate approximation, building on the expectation-maximization (EM) algorithm.
- **Hamiltonian Monte Carlo (HMC):** Uses gradient computations to navigate continuous probability spaces efficiently.

These innovations have revolutionized Bayesian workflow, but safe usage requires strong diagnostics to flag unreliable computations.

---

### Initial Values, Adaptation, and Warmup
The initial phase of inference algorithms is critical:
- **Initial Values:** While theoretically irrelevant in the asymptotic limit, poor initial values can bias results.
- **Warmup Phase:** Moves simulations from unrepresentative initial values toward the typical set, a concept in information theory. This phase serves three purposes:
  1. Reduces bias from initial values.
  2. Provides information to tune algorithm parameters.
  3. Flags computational issues early.

---

### How Long to Run an Iterative Algorithm
The duration of iterative algorithms like MCMC impacts result reliability and computational efficiency:
- **Convergence Diagnostics:**  
  - Standard practice: Run until \(\hat{R}\), a mixing measure, is below 1.01 for all parameters.  
  - Monitor the multivariate mixing statistic \(R^*\).  
- **Balancing Accuracy and Speed:**  
  While increasing effective sample size or reducing Monte Carlo error improves accuracy, it limits model exploration if computation is too slow.
- **Leveraging Parallelism:**  
  Instead of increasing iterations, variance reduction can be achieved by increasing parallel chains.

---

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

> **Key Perspective**  
> {: .green-box}  
> Approximate algorithms can be viewed as exact algorithms for approximate models.  
> - **Empirical Bayes:** Replaces prior distributions with data-dependent point-mass priors.  
> - **Laplace Approximation:** Data-dependent linearization of the model.  
> - **Nested Laplace Approximation:** Linearizes conditional posterior distributions.

---

### Fit Fast, Fail Fast
Efficient Bayesian workflow emphasizes quickly identifying and discarding flawed models:
- **Failing Fast:** Saves time by avoiding perfect inference for fundamentally flawed models.
  
<div class="red-box">
  <strong>Fast Algorithms vs. Early Failure</strong>  
  There is extensive literature on fast approximation algorithms to fit desired models, but less focus on algorithms designed to minimize time spent on models that will ultimately be abandoned.
</div>


---

## 3. Using Constructed Data to Find and Understand Problems

- **3.1** Fake-data simulation
  - The basic idea is to check whether our procedure recovers the correct parameter values when fitting fake data.
  - Typically, we choose parameter values that seem reasonable a priori and then simulate a fake dataset of the same size, shape, and structure as the original data.
    - a) Check to see if the observed data can provide additional information beyond the prior. The procedure is to simulate some fake data from the model with fixed, known parameters and then see whether our method comes close to reproducing the known truth. We can look at point estimates and also the coverage of posterior intervals.
    - b) The second thing that we check is if the true parameters can be recovered to roughly within the uncertainty implied by the fitted posterior distribution. 
    - c) The third thing that we can do is use fake data simulations to understand how the behavior of a model can change across different parts of the parameter space. In this sense, a statistical model can contain many stories of how the data get generated.
  - All this implies that fake data simulation can be particularly relevant in the zone of the parameter space that is predictive of the data. This, in turn, suggests a two-step procedure in which we first fit the model to real data and then draw parameters from the resulting posterior distribution to use in fake-data checking.
  -   In box: The statistical properties of such a procedure are unclear
  -   To carry this idea further, we may break our method by creating fake data that cause our procedure to give bad answers. This sort of simulation-and-exploration can be the first step in a deeper understanding of an inference method.
  -   If our goal is not merely prediction but estimating the latent variables, examining predictions only helps us so much. This is especially true of overparameterized models, where wildly different parameter values can yield comparable predictions
  -   If a model can make good inference on fake-data generated from that very model, this provides no guarantee that its inference on real data will be sensible.But if a model cannot make good inference on such fake data, then it’s hopeless to expect the model to provide reasonable inference on real data.
  -   A more comprehensive approach than what we present in Section 4.1 is simulation-based
calibration (SBC). While in many ways superior to benchmarking against a truth point, simulation-based calibration requires fitting the model multiple times, which incurs a substantial computational cost. Simulation-based calibration and truth-point benchmarking are two ends of a spectrum.
  - Box: It is an open research question to understand SBC with a small number of draws.
  - A serious problem with SBC is that it clashes somewhat with most modelers’ tendency to specify their priors wider than they believe necessary. The slightly conservative nature of weakly informative priors can cause the data sets simulated during SBC to be extreme occasionally.

- **3.2** Simulation-based calibration
  - There is a formal, and at times practical, issue when comparing the result of Bayesian inference, a posterior distribution, to a single (true) point.
  - Box in red:
    - Using a single fake data simulation to test a model will not necessarily “work”, even if the computational algorithm is working correctly (there is a 5% chance that a random draw will be outside a 95% uncertainty interval) but also because Bayesian inference will in general only be calibrated when averaging over the prior.
    - Furthermore, parameter recovery may fail not because the algorithm fails but because the observed data are not providing information
that could update the uncertainty quantified by the prior for a particular parameter. 

- **3.3** Experimentation using constructed data
  - A good way to understand a model is to fit it to data simulated from different scenarios.
  - One interesting question here is, how bad will these inferences be?
  - In the context of the present article, the point of this example is to demonstrate how simulation of a statistical system under different conditions can give us insight, not just about computational issues but also about data and inference more generally

---

## 4. Addressing Computational Problems

- **4.1** The folk theorem of statistical computing  
In a box: When you have computational problems, often there’s a problem with your model.M
Many cases of poor convergence correspond to regions of parameter space that are not of substantive interest or even to a nonsensical model.
Our first instinct when faced with a problematic model should not be to throw more computational resources on
the model, but to check whether our model contains some substantive pathology.

- **4.2** Starting at simple and complex models and meeting in the middle  
The path toward diagnosing the problem is to move from two directions:
  - to gradually simplify the poorly-performing model, stripping it down until you get something that works;
  - and from the other direction, starting with a simple and well-understood model and gradually adding features until the problem appears.
- **4.3** Getting a handle on models that take a long time to fit  
  - Slow computation is often a sign of other problems, indicating a poorly performing HMC. However the very fact that the fit takes long means the model is harder to debug.
  - The common theme in all these tips is to think of any particular model choice as provisional, and to recognize that data analysis requires many models to be fit in order to gain control over the process of computation and inference for a particular applied problem.
    
- **4.4** Monitoring intermediate quantities  
  - Another useful approach to diagnosing model issues is to save intermediate quantities in our
 computations and plot them.

- **4.5** Stacking to reweight poorly mixing chains  
  - It is also common to be in an intermediate situation where multiple chains are slow to mix but they are in a generally reasonable range. In this case we can use stacking to combine the simulations, using cross validation to assign weights to the dierent chains.
  - Especially suitable during the model exploration phase.

- **4.6** Posterior distributions with multimodality and other difficult geometry  
  - Challenges associated to multimodality:
    - Efectively disjoint posterior volumes, where all but one of the modes have near-zero mass.
    - Efectively disjoint posterior volumes of high probability mass that are trivially symmetric, such as label switching in a mixture model.
    - Efectively disjoint posterior volumes of high probability mass that are diferent
    - A single posterior volume of high probability mass with an arithmetically unstable tail.

- **4.7** Reparameterization  
  - Generally, an HMC-based sampler will work best if its mass matrix is appropriately tuned and the geometry of the joint posterior distribution is relatively uninteresting, in that it has no sharp corners, cusps, or other irregularities.
    - Easily satisfied for many classical models, where results like the Bernstein-von Mises theorem suggest that the posterior will become fairly simple when there is enough data.
    - When not, behavior of HMC can be greatly improved by judiciously choosing a parameterization that makes the posterior geometry simpler.

- **4.8** Marginalization  
  - Challenging geometries in the posterior distribution are often due to interactions between parameters. And sometimes the marginals of each parameter behave better.
  - Exploiting the structure of the problem, we can approximate these distributions using a Laplace approximation, notably for latent Gaussian models. 

- **4.9** Adding prior information  
  - Often the problems in computation can be fixed by including prior information that is already available but which had not yet been included in the model.
  - Many fitting problems go away when reasonable prior information is added, which is not to say that the primary use of priors is to resolve fitting problems
  - In classical statistics, models are sometimes classified as identifiable or nonidentifiable.
  - Red box: “identification” is formally defined in statistics as an asymptotic property, but in Bayesian inference we care about inference with finite data.
  - If the data are not informative on some aspects of the model, we may improve the situation by providing more information via priors.
  - We often prefer to use a model with parameters that can be updated by the information in the data instead of a model that may be closer to the truth but where data are not able to provide sufficient information.
  - Consider four steps on a ladder of abstraction:
    1. Poor mixing of MCMC;
    2. Dicult geometry as a mathematical explanation for the above;
    3. Weakly informative data for some parts of the model as a statistical explanation for the above;
    4. Substantive prior information as a solution to the above.
    - Starting from the beginning of this ladder, we have computational troubleshooting; starting from the end, computational workflow. 

- **4.10** Adding data  
  - Similarly to adding prior information, one can constrain the model by adding new data sources that are handled within the model.
  - In other cases, models that are well-behaved for larger datasets can have computational issues in small data regimes; 

---

## 5. Evaluating and Using a Fitted Model

There are many different things that can be checked for a fitted model, and each of these checks can lead in many directions.
Statistical models can be fit with multiple goals in mind, and statistical methods are developed for different groups of users. 
The aspects of a model that need to be checked will depend on the application.

- **5.1** Posterior predictive checking  
  - This refers to simulations that come from the posterior distribution rather than the prior.
  - There is no general way to choose which checks one should perform on a model, but running a few such direct checks is a good safeguard against gross misspecification.
  - There is also no general way to decide when a check that fails requires adjustments to the model.
  - Depending on the goals of the analysis and the costs and benefits specific to the circumstances.
  - Box: In general, we try to find “severe tests”: checks that are likely to fail if the model gives misleading answers to the questions we care most about.

- **5.2** Cross-validation and influence of individual data points and subsets of the data  
  - Posterior predictive checking is often sufficient for revealing model misfits.
  - CV improves predictive checking diagnostics, especially for flexible models.
  - Three diagnostic approaches:
    1. calibration checks using the cross-validation predictive distribution,
    2. identifying which observations or groups of observations are most difficult to predict
    3. identifying how influential particular observations are, that is, how much information they provide on top of other observations.
  - Although perfect calibration of predictive distributions is not the ultimate goal of Bayesian inference, looking at how well calibrated leave-one-out cross-validation (LOO-CV) predictive distributions are can reveal opportunities to improve the model.
  - Box: posterior predictive checking often compares the marginal distribution of the predictions to the data distribution, leave-one-out
cross-validation predictive checking looks at the calibration of conditional predictive distributions.
  - Under good calibration, the s probability integral transformations, PIT, given the left-out observations are uniform.
  - We can also look at which observations are hard to predict and see if there is a pattern or explanation for why some are harder to predict than others.
  - Cross-validation for multilevel (hierarchical) models requires more thought. Leave-one-out is still possible, but it only sometimes matches our inferential goals! 
      
- **5.3** Influence of prior information  
  - Understanding how posterior inferences under a fitted model depend on the data and priors is relevant.
  - Box: A statistical model can be understood in two ways:
  - generatively; we want to understand how the parameters map to the data. We can perform prior predictive simulations to visualize possible data from the model.
  - inferentially; we want to understand the path from inputs (data and prior distributions) to outputs (estimates and uncertainties).
  - Sensitivity analysis:
    - compute the shrinkage between prior and posterior (e.g. posterior standard deviations for each parameter or by comparing prior and posterior quantiles). 
  - Importance sampling to approximate the posterior of the new model using the posterior of the old model and compare similarity.
  - Static sensitivity analysis, which is a way to study sensitivity of posterior inferences to perturbations in the prior without requiring that the model be re-fit using alternative prior distributions.

- **5.4** Summarizing inference and propagating uncertainty  
  - The usual ways of displaying Bayesian inference do not fully capture the multiple levels of variation and uncertainty in our inferences.
  -  A table or even a graph of parameter estimates, uncertainties, and standard errors is only showing one-dimensional margins.
  -  Graphs of marginal posterior distributions are unwieldy for models with many parameters and also fail to capture the interplay between uncertainty and variation in a hierarchical model.
  -  R package bayesplot.
    
---

## 6. Modifying a Model


- **6.1** Constructing a model for the data  
  - Box: The model building is a language-like task in which the modeler puts together existing components in order to encompass new data
and additional features of existing data, along with links to underlying processes of interest
  - Box: Model expansion can come in response to new data, failures of models fit to existing data, or computational struggles with existing fitting procedures.

- **7.2** Incorporating additional data  
  - It is sometimes said that the most important aspect of a statistical method is not what it does with the data, but what data are used.
  - A key part of BW is expanding a model to make use of more data.
    
- **7.3** Working with prior distributions  
  - Traditionally, in Bayesian statistics, we speak of noninformative or fully informative priors, but neither of these generally exist.
    - A uniform prior contains some information, as it depends on the parameterization of the model;
    - A reference prior depends on an assumed asymptotic regime for collecting new, fictional data (Berger et al., 2009);
    - Even an informative prior rarely includes all available knowledge.
  - Rather, think of a ladder of possibilities:
    - (improper) flat prior;
    - super-vague but proper prior;
    - very weakly informative prior;
    - generic weakly informative prior;
    - specific informative prior.
  - Another way to view a prior distribution, or a statistical model more generally, is as a constraint.
    - Prior distributions to shrink towards simpler models
  - Box: Any clear distinction between model and prior is largely arbitrary and often depends mostly on the conceptual background of the one making the distinction.
  - The amount of prior information needed to get reasonable inference depends strongly on
    - the role of the parameter in the model 
    - the depth of the parameter in the hierarchy
  - Putting appropriate priors on our new parameters, we probably need to tighten up the priors on the overall mean and observation standard deviation, lest a lack of information lead to nonsense estimates. A related issue is the concentration of measure in higher-dimensional space.
  - In red Box: Priors must be specified for each model within a workflow. An expanded model can require additional thought regarding parameterization. In general, we need to think in terms of the joint prior over all the parameters in a model, to be assessed in the context of the generative model for the data, lest unfortunate cancellations or resonances lead to less stabilizing or more informative priors than the modeler actually wants
      
- **7.4** A topology of models  
  - We would want the models considered within a framework to have their own topology or network structure as determined by the models in the class and their partial ordering.
  - In red box: We speak of this as a topology of models rather than a probability space because we are not necessarily interested in assigning probabilities to the individual models. Our interest here is not in averaging over models but in navigating among them, and the topology refers to the connections between models and between parameters in neighboring models in the network
    - Examples: Automatic Statistician (Hwang et al., 2016, Gharamani et al., 2019), which searches through models in specified but open-ended classes (for example, time series models and linear regression models), using inference and model criticism to explore the model and data space. Prophet (Taylor and Lethem, 2018) allows users to put together models (in this case, for time series forecasting) from some set of building blocks.
  - However, unlike combining variables, where in many cases a simple and often automated additive model is enough, here, each model itself is a high-dimensional object.
  - Box: The outputs from different models, as probabilistic random variables, can be added, multiplied, linearly mixed, loglinearly-mixed, pointwisely-mixed, etc, which is within the choice of model topology we need to specify. In addition, each model within a framework has its own internal structure involving parameters that can be estimated from data. And, importantly, the parameters within different models in the network can “talk with each other” in the sense of having a shared.
    - Examples: forecasting and causal inference.

---

## 7. Understanding and Comparing Multiple Models

- **7.1** Visualizing models in relation to each other  
  - BW key aspect is that we are fitting many models while working on a single problem.
  - In red box: We are not talking here about model selection or model averaging but rather of the use of a series of fitted models to better understand each one.
  - We seek to explore the **process** of model fitting, not just the end result.
  - Given that we are fitting multiple models, we also have to be concerned with researcher degrees of freedom, most directly from overfitting if a single best model is picked, or more subtly that if we are not careful, we can consider our inferences from a set of fitted models to bracket some total uncertainty, without recognizing that there are other models we could have fit.
  - Multiverse analyst: When multiple models pass all the checks.
    
- **7.2** Cross-validation and model averaging  
  - In red box: When performing model comparison, if there is non-negligible uncertainty in the comparison, we should not simply choose the single model with the best cross validation results, as this would discard all the uncertainty from the cross validation process.
  - Instead, we can maintain this information and use stacking to combine inferences using a weighting that is set up to
minimize cross validation error.
  - In concept, stacking can sometimes be viewed as pointwise model selection.
  - If we fit many models that we will not be interested in including in any average; such “scaolds” include models that are deliberately overly simple (included just for comparison to the models of interest) and models constructed for purely experimental purposes, as well as models that have major flaws or even coding errors.
  -  But even after these mistakes or deliberate oversimplifications have been removed, there might be several models over which
to average when making predictions. They prefer continuous model expansion over model averaging, but there will be settings where users will reasonably want to make predictions averaging over competing Bayesian models.
- **7.3** Comparing a large number of models 
  - If the number of candidate models is large, we are often interested in finding a comparably smaller model that has the same predictive performance as our expanded model. This leads to the problem of predictor (variable) selection.
  - In red Box: If we have many models making similar predictions, selecting one of these models based on minimizing cross validation error would lead to overfitting and suboptimal model choices.
  - In contrast, projection predictive variable selection has been shown to be stable and reliable in finding smaller models
with good predictive performance. The projection predictive approach avoids overfittin by examining only the projected submodels
based on the expanded model’s predictions and not fitting each model independently to the data.

---

## Discussion

**Different perspectives on statistical modeling and prediction**
  - Traditional statistical perspective. In textbooks, statistical inference is typically set up as a problem in which a model has been chosen ahead of time, and in the Bayesian context the goal is to accurately summarize the posterior distribution. Computation is supposed to be done as long as necessary to reach approximate convergence.
  - Machine learning perspective. In machine learning, the usual goal is prediction, not parameter estimation, and computation can stop when cross validation prediction accuracy has plateaued.
  - Model exploration perspective. In applied statistical work, much of our modeling effort is spent in exploration, trying out a series of models, many of which will have terrible fit to data, poor predictive performance, and slow convergence.
- These three scenarios imply dierent inferential goals.
  - In a traditional statistical modeling problem, it can make sense to run computation for a long time, using approximations only when absolutely necessary. The approximation might be in the choice of model rather than in the computation.
  - In machine learning, we want to pick an algorithm that trades of predictive accuracy, generalizability, and scalability, so as to make use of as much data as possible within a fixed computational budget and predictive goal.
  - In model exploration, we want to cycle through many models, which makes approximations attractive. But there is a caveat here: if we are to efficiently and accurately explore the model space rather than the algorithm space, we require any approximation to be suciently faithful as to reproduce the salient features of the posterior.
- In red: The distinction here is not about inference vs. prediction, or exploratory vs. confirmatory analysis.
- In box: distinction is how much we trust a given model and allow the computation to approximate.
- This is one reason that subfields in applied statistics advance from application to application, as new wrinkles become apparent in existing models.
  
**Justification of iterative model building**
- Model navigation as the next transformative step in data science.
  - The first big step of data science, up to 1900 or so, was data summarization.
  - The next big step, beginning with Gauss and Laplace and continuing to the present day, was modeling.
  - Currently in the midst of another big step, computation.
- In the real world, we need to take into account the limitations of humans and computers. One goal of BW is to make the process 
 easier for humans even in the idealized setting where exact computation can be performed automatically.
- There is no fully automated computation that yields perfect results.
- It is easier to understand computational challenges when there are fewer moving parts

**Model selection and overfitting**
- A potential issue with the proposed iterative workflow is that model improvement is conditioned on discrepancy between the currently considered model and the data, and thus at least some aspects of the data are used more than once.
  - In red box: This “double dipping” can in principle threaten the frequency properties of our inferences, and it is important to be aware of the possibility of overfitting arising from model selection.
- A related issue is the garden of forking paths, the idea that different models would have been fit had the data come out differently. We do not advocate selecting the best fit among some such set of models. Instead, we describe a process of building to a more complex model taking the time to understand and justify each decision.
- In box:  Suppose we fit model M1, then a posterior predictive check reveals problems with its fit to data, so we move to an improved M2 that, we hope, includes more prior information and makes more sense with respect to the data and the applied problem under study. But had the data been different, we would have been satisfied with M1. The steps of model checking and improvement, while absolutely necessary, represent an aspect of fitting to data that is not captured in the likelihood or the prior.
- This is an example of the problem of post-selection inference.
-  There is a problem of inference conditional on having “searched for the strongest associations.” BW does not involve searching for optimally fitting models or making hard model selection under uncertainty.
- Their main message on the concerns about post-selection inference is that the final model should account for as much information as possible, and when we might be selecting among a large set of possible models, we instead embed these in a larger model, perform predictive model averaging, or use all of the models simultaneously
- Perform severe tests of many of the assumptions that underlie the models being examined.

**Bigger datasets demand bigger models**
- Hierarchical Bayesian modeling, deep learning, and other regularization-based approaches are allowing researchers to fit larger, more complex models to real-world data, enabling information aggregation and partial pooling of inferences from different sources of data.
- Statistical extrapolation should be more effective if we adjust for more factors, that is, include more information—but we quickly reach a technical barrier.
- Models that adjust for many factors can become hard to estimate, and effective modeling requires
  - (a) Regularization to get more stable estimates.
  - (b) Modeling of latent variables, missingness, and measurement error.
- In a box: The model does not exist in isolation and is not specified from the outside; it emerges from engagement with the application and the available data.

**Prediction, generalization, and poststratification**
- The three core tasks of statistics are
    1. generalizing from sample to population,
    2. generalizing from control to treatment group,
    3. and generalizing from observed data to underlying constructs of interest.
- Bayesian methods use
  - Hierarchical modeling or partial pooling to appropriately generalize across similar but not identical settings,
  - Regularization to facilitate the use of large nonparametric models
  - Multilevel modeling for latent variables
  - Connections between transportability and Bayesian graph models
- Box: Just as the prior can often only be understood in the context of the likelihood so should the model be understood in light of how it will be used.








