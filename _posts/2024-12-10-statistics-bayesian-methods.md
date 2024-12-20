---
layout: post
title: "A review on Bayesian Methodology"
date: 2024-12-10
theme: Review
tags: [statistics, bayesian, methodology]
excerpt: "A review on the modern Bayesian Methodology, and some commentary."
---

# Bayesian Methodology: Bayesian Workflow, as a structured framework. 

Now more than ever, we need a critical framework for applied Bayesian Statistics to detangle and organize the complex processes involved. This review builds upon the framework Gelman et al. (2020) presented, called Bayesian Workflow, and offers additional personal insights.

---

## What is Bayesian Workflow?

Bayesian Workflow (BW) provides a structured approach to managing the dynamic and iterative nature of applied Bayesian Statistics. To better understand it, it's helpful to differentiate three closely related concepts:

1. **Bayesian Inference:**  
   Whose primary goal is to compute the conditional probabilities or posterior distributions.

2. **Bayesian Data Analysis:**  
   Which refers to the application of Bayesian inference to specific datasets as described in Gelman et al. (2017)

3. **Bayesian Workflow (BW):**  
   A broader framework that includes:
   - Model building
   - Inference
   - Model checking and improvement
   - Model comparison (not limited to selection or averaging)

The workflow emphasizes the value of analyzing models that may initially seem flawed or suboptimal, as they often provide important insights to understand the model and potential extensions. 

---

## Why Is Bayesian Workflow Important?

A well-defined Bayesian Workflow addresses several challenges in statistical modeling:

- **Organized Model Understanding:**  
  It alleviates computational burdens by structuring model evaluation and refinement into manageable steps.

- **Better Decision-Making:**  
  It helps practitioners identify which assumptions to relax and which to retain, enabling more thoughtful model selection.

- **Model-Data Relationships:**  
  Understanding how models fit the data, even when models reflect poor performance, can provide useful insights.

- **Diverse Conclusions:**  
  Different models often lead to different conclusions; **BW** encourages practitioners to explore and understand these variations.

---

## The Big Picture

### ToDo: Include Diagram  

### Integrating Statistical Innovations  
Many statistical methodologies began as informal techniques or "hacks" and have since been formalized within Bayesian frameworks in recent years. Key examples include:

- **Multilevel Modeling:**  
  Extends empirical Bayes methods by incorporating prior inference directly into Bayesian models.

- **Exploratory Data Analysis (EDA):**  
  Functions as a form of predictive model checking.

- **Regularization Techniques:**  
  Replace ad hoc variable selection methods in regression, offering more robust solutions.

- **Non-parametric Models:**  
  They serve as Bayesian replacements for techniques like kernel smoothing and broadening their application.

These methods have expanded statistical frameworks, making them more modular and adaptable while retaining their core principles.

---

## Statistics and Uncertainty

At its heart, statistics is about *managing uncertainty*. **BW** recognizes and aims to address uncertainty in several forms:

- **Data and Model Parameters:**  
  Variability and imprecision are inherent in the data and parameters.

- **Model Fitting:**  
  Challenges in determining whether a model is appropriately specified.

- **Model Setup and Expansion:**  
  Difficulty in deciding how to structure and extend models to capture key dynamics.

- **Interpretation:**  
  Ambiguity in translating statistical results into meaningful conclusions.

Workflows often become disorderly when moving beyond predefined designs and analyses. Practical constraints—such as limited time, computational resources, and the consequences of incorrect decisions—frequently necessitate shortcuts. A structured workflow mitigates these challenges by offering a systematic approach to balancing rigor with practicality.

The **Bw** provides a comprehensive framework for organizing applied Bayesian Statistics. It embraces the iterative nature of statistical modeling, acknowledges the importance of learning from flawed models, and prioritizes the exploration of uncertainty. By following these structured principles, practitioners can make informed, defensible decisions while navigating the complexities of statistical analysis.

For those interested in exploring this further, I would recommend you review Gelman et al. (2020) and consider how these principles can be applied in your work. 

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


---
## III. Using Constructed Data to Find and Understand Problems

### Fake-Data Simulation
The core idea of fake-data simulation is to test whether a procedure can recover correct parameter values when applied to simulated data. This involves the following steps:

1. **Simulate Fake Data:**  
   Choose reasonable parameter values and generate a fake dataset that matches the size, structure, and shape of the original data.

2. **Evaluate the Procedure:**  
   - **Information Beyond the Prior:** Simulate fake data from the model using fixed, known parameters and check if the observed data adds meaningful information. Analyze point estimates and the coverage of posterior intervals.
   - **Parameter Recovery:** Assess whether the true parameters are recovered within the uncertainty range implied by the fitted posterior distribution.
   - **Behavior Across Parameter Space:** Explore how the model behaves in different regions of the parameter space, revealing the various "stories" the model encodes about data generation.

3. **Two-Step Procedure:**  
   Fit the model to real data, draw parameters from the resulting posterior distribution, and use these parameters for fake-data checking.

<div class="red-box">
  <strong>Key Insight:</strong>  
   <li> If a model cannot make reliable inferences on fake data generated from itself, it’s unlikely to provide reasonable inferences on real data.  </li>
</div>

While fake-data simulations help evaluate a model’s ability to recover parameters, they also highlight potential weaknesses. For example:
- Creating fake data that causes the procedure to fail can deepen understanding of an inference method.
- Overparameterized models may yield comparable predictions despite wildly different parameter estimates, limiting the usefulness of predictive checks.

### Simulation-Based Calibration (SBC)
SBC provides a more comprehensive approach than truth-point benchmarking by fitting the model multiple times and comparing posterior distributions to simulated data. However, SBC has its challenges:
- **Computational Cost:** Requires significant resources to fit the model repeatedly.
- **Priors and Modeler Bias:**  
  - Weakly informative priors, often chosen conservatively, can lead to extreme datasets during SBC.  
  - This mismatch can obscure insights about calibration and posterior behavior.

<div class="purple-box">
  <strong>Open Research Question:</strong>    
  How effective is SBC with a limited number of simulations?  
</div>

Simulation-based calibration and truth-point benchmarking are complementary, with SBC offering broader insights but at a higher computational expense.

### Experimentation Using Constructed Data
Simulating data from different scenarios provides valuable insights into models and inference methods. This experimentation allows practitioners to:
- Understand how a model performs under varying conditions.
- Explore the limits of inferences by fitting the model to data generated from challenging scenarios.
- Gain a deeper understanding of both computational issues and the underlying data.

<div class="red-box">
  <strong>Important Consideration:</strong> Testing a model with a single fake dataset is not sufficient.  
   <li> Even if the computational algorithm works, there’s a 5% chance that a random draw will fall outside a 95% uncertainty interval. </li>  
   <li> Bayesian inference is calibrated only when averaging over the prior.   </li>
   <li> Parameter recovery can fail not because of algorithmic errors but due to insufficient information in the observed data.  </li>
</div>

Simulation of statistical systems under diverse conditions not only addresses computational challenges but also enhances our understanding of data and inference.

---

## IV. Addressing Computational Problems

<div class="red-box">
  <strong>The Folk Theorem of Statistical Computing: </strong>   
 <li> When computational problems arise, they often indicate an issue with the model itself.  </li>
 <li> Many cases of poor convergence are tied to regions of parameter space that are either irrelevant or nonsensical. </li>
  <li> Instead of throwing more computational resources at the problem, the first step should be to identify and address potential model pathologies. </li>
</div>

### Starting at Simple and Complex Models and Meeting in the Middle
Diagnosing computational problems often requires a two-pronged approach:
- Simplify the problematic model step by step until it works reliably.
- Start with a simple, well-understood model and gradually add features until the issue reappears.

This process helps isolate the root cause of the problem.

### Getting a Handle on Models That Take a Long Time to Fit
Slow computation is often symptomatic of deeper issues, such as poorly performing Hamiltonian Monte Carlo (HMC). However, debugging becomes harder as computation times increase.  
Key strategies include:
- Viewing model choices as provisional.
- Fitting multiple models to understand computational and inferential behavior in the applied problem.

### Monitoring Intermediate Quantities
Saving and plotting intermediate quantities during computation can reveal hidden issues with the model or algorithm. These visualizations often provide valuable clues for debugging.

### Stacking to Reweight Poorly Mixing Chains
In situations where multiple chains mix slowly but remain within reasonable ranges, stacking can be used:
- Combine simulations by assigning weights to chains through cross-validation.
- Particularly useful during model exploration when diagnostics suggest some progress but full convergence remains elusive.

### Posterior Distributions with Multimodality and Difficult Geometry
Multimodality and complex posterior geometries pose significant challenges:
- **Disjoint Posterior Volumes:**  
  - Near-zero mass for all but one mode.  
  - Symmetric volumes, such as label switching in mixture models.  
  - Distinct volumes with significant probability mass.  
- **Unstable Tails:**  
  A single posterior volume with arithmetically unstable regions.

Each scenario requires tailored strategies for efficient computation.

### Reparameterization
HMC-based samplers perform best when:
- The mass matrix is well-tuned.
- The posterior geometry is smooth, with no sharp corners or irregularities.  

For many classical models, results like the Bernstein-von Mises theorem simplify posterior geometry with sufficient data. When this is not the case, reparameterization can significantly improve computational performance by simplifying posterior geometry.

### Marginalization
Challenging geometries in posterior distributions often stem from parameter interactions. Marginalizing over certain parameters can simplify computations:
- Approximations like the Laplace method can be particularly effective for latent Gaussian models.
- Exploiting the structure of the problem can lead to substantial improvements.

### Adding Prior Information
Many computational issues can be mitigated by incorporating prior information:
- Priors help address weakly informative data regions, improving model behavior without sacrificing inference quality.
- While the primary purpose of priors is not to fix fitting problems, their inclusion often resolves computational challenges.  

<div class="red-box">
  <strong>Identifiability?</strong>  
  <li> “Identification” is an asymptotic property in classical statistics </li>
  <li> Bayesian inference prioritizes inference with finite data. </li>
  <li> If data are insufficient for certain aspects of the model, priors can supply the necessary information. </li>
</div>

**Ladder of Abstraction:**  
1. Poor mixing of MCMC.  
2. Difficult geometry as a mathematical explanation.  
3. Weakly informative data as a statistical explanation.  
4. Substantive prior information as a solution.  

Addressing computational issues can start at either end of this ladder, transitioning from troubleshooting to workflow optimization.

### Adding Data
Similar to priors, additional data can constrain models and resolve computational problems:
- Incorporate new data sources into the model.
- Models that work well with larger datasets may struggle in small data regimes; expanding the dataset can improve performance.

Addressing computational problems in Bayesian modeling involves a combination of simplifying models, leveraging prior information, and refining computational techniques. A systematic approach, starting with diagnostics and iterative improvements, ensures both model reliability and computational efficiency.

---

## V. Evaluating and Using a Fitted Model

Evaluating a fitted model involves multiple checks, each tailored to the specific goals of the analysis. The aspects of the model that require evaluation depend on the application and the intended users of the statistical methods.

### Posterior Predictive Checking
Posterior predictive checking involves simulations from the posterior distribution to evaluate model performance:
- While there’s no universal guide for which checks to perform, conducting a few direct checks can safeguard against gross misspecification.
- Similarly, there’s no definitive rule for deciding when a failed check necessitates adjustments to the model.
- The choice of checks depends on the analysis goals and the costs and benefits of adjustments.

<div class="green-box">
   <strong>Key Principle:</strong>   
  <li> Seek “severe tests”—checks likely to fail if the model produces misleading answers to critical questions. </li>
</div>

### Cross-Validation and Influence of Individual Data Points
Cross-validation (CV) enhances predictive diagnostics, especially for flexible models, by providing insights into model fit and data influence:
1. **Calibration Checks:** Use the cross-validation predictive distribution to assess calibration.
2. **Difficult Observations:** Identify observations or groups that are hard to predict.
3. **Influence Diagnostics:** Examine the additional information provided by individual observations.

- Leave-one-out cross-validation (LOO-CV) is a popular method, though it doesn’t always align with inferential goals for multilevel (hierarchical) models.
- Calibration insights:
  - Posterior predictive checking compares marginal prediction distributions to data.
  - LOO-CV predictive checking evaluates the calibration of conditional predictive distributions.
  - Probability integral transformations (PIT) under good calibration are uniform.

<div class="blue-box">
  <strong>  Practical Tip:</strong>   
  <li> Cross-validation for multilevel models requires thoughtful implementation to ensure alignment with inferential goals. </li>
</div>

### Influence of Prior Information
Understanding how prior information affects posterior inferences is essential for a robust evaluation:
- A statistical model can be understood in two ways:
  1. **Generatively:** Explore how parameters map to data using prior predictive simulations.
  2. **Inferentially:** Examine the path from inputs (data and priors) to outputs (estimates and uncertainties).

- **Sensitivity Analysis:**
  - Measure shrinkage between prior and posterior distributions, such as comparing posterior standard deviations or quantiles.
  - Use importance sampling to approximate and compare posteriors across models.
  - Conduct static sensitivity analysis to study posterior sensitivity to prior perturbations without re-fitting the model.

<div class="green-box">
  <strong>Practical Insight:</strong>   
  <li> Sensitivity analysis highlights the balance between prior information and data, offering valuable diagnostic insights without excessive computation. </li>
</div>

### Summarizing Inference and Propagating Uncertainty
Traditional methods of summarizing Bayesian inference often fail to fully represent the complexity of variation and uncertainty:
- Tables and graphs of parameter estimates and uncertainties only capture one-dimensional margins.
- Marginal posterior distribution graphs become unwieldy for models with many parameters and fail to illustrate the interplay of hierarchical model uncertainties.

**Tools for Advanced Summaries:**
- Use visualization tools like the `bayesplot` R package to effectively summarize and explore Bayesian inference results.

Evaluating a fitted model is a multifaceted process. It involves a combination of diagnostic checks, sensitivity analyses, and advanced visualization techniques. The goal is not just to identify potential misfits but to refine the model for better inference and predictive accuracy.


---

## VI. Modifying a Model

### Constructing a Model for the Data
Model construction is a creative process where the modeler combines existing components to account for new data, enhance features of existing data, or establish links to underlying processes.

<div class="green-box">
  <strong>Model Building as a Task:</strong>  
  <li> Model construction is akin to a language-like task, where components are assembled to encompass new data, existing data features, and links to underlying processes. </li>
</div>

<div class="yellow-box">
  <strong>Reasons for Model Expansion:</strong>  
  <li> Response to new data.  </li>
  <li> Failures of models fit to existing data.   </li>
  <li> Computational challenges with current fitting procedures. </li>
</div>

### Incorporating Additional Data
Expanding a model to include more data is a critical step in Bayesian Workflow (BW).  
It’s often said that the value of a statistical method lies not just in how it handles data but in the choice of what data to use.

### Working with Prior Distributions
Traditionally, Bayesian statistics refers to noninformative or fully informative priors, but in practice, these rarely exist:
- **Uniform Prior:** Depends on parameterization, carrying implicit information.
- **Reference Prior:** Based on asymptotic regimes and fictional data assumptions.
- **Informative Prior:** Rarely encompasses all available knowledge.

**Ladder of Priors:**  
Think of prior distributions as existing on a continuum:
1. Improper flat prior.  
2. Super-vague but proper prior.  
3. Very weakly informative prior.  
4. Generic weakly informative prior.  
5. Specific informative prior.  

Priors also act as constraints, shrinking estimates toward simpler models. However, the need for prior information varies based on:
- The role of the parameter in the model.  
- The parameter’s position in the hierarchy.  

<div class="red-box">
  <strong>Critical Insight:</strong>   
  Priors must be specified for each model in the workflow. Expanded models often require additional thought regarding parameterization and joint priors to avoid unintended effects like cancellations or overly stabilizing priors.
</div>

When introducing new parameters:
- Consider tightening priors on overarching metrics like means and standard deviations.
- Be cautious of the concentration of measure in higher-dimensional spaces.

---

### A Topology of Models
Models within a framework can be thought of as forming a topology or network structure. This structure reflects connections and partial orderings rather than probabilities assigned to individual models.

<div class="yellow-box">
  <strong> Model Topology?:</strong>    
  <li> A topology of models refers to their connections and relationships, not a probability space. The goal is not to average over models but to navigate among them effectively.</li>
</div>

**Examples of Model Navigation Tools:**
- **Automatic Statistician:** Explores models in specified but open-ended classes, like time series or regression models, using inference and model criticism.  
- **Prophet:** A time series forecasting tool allowing users to build models from predefined building blocks.

**Model Operations:**
Models, treated as probabilistic random variables, can be combined in multiple ways:
- Additive, multiplicative, linear mixing, log-linear mixing, pointwise mixing, and more.  
Each model has its internal structure, with parameters estimated from data, and parameters across models can interact (e.g., shared parameters).

<div class="blue-box">
  <strong>Applications:</strong>  
  <li> <strong>Forecasting:</strong> Using interconnected models to predict future outcomes. </li> 
  <li> <strong>Causal Inference:</strong> Exploring relationships between variables using networked model structures. </li>
</div>


---

## VII. Understanding and Comparing Multiple Models

### Visualizing Models in Relation to Each Other
A key aspect of Bayesian Workflow (BW) is fitting multiple models for a single problem. This process is not about selecting the best model or averaging models, but rather using a series of fitted models to gain a deeper understanding of each one.

<div class="red-box">
  <strong>Remark:</strong>  
  <li> Model comparison in this context is not about selecting or averaging but about exploring the <strong>process</strong> of fitting multiple models to understand them better. </li>
</div>

**Considerations When Fitting Multiple Models:**
- Be aware of researcher degrees of freedom:
  - Overfitting can occur if a single “best” model is chosen.
  - A set of fitted models might appear to bracket total uncertainty, but other unconsidered models could still contribute.
- Multiverse analysis: Evaluate situations where multiple models pass all checks to ensure robustness.

### Cross-validation and Model Averaging
Cross-validation (CV) is a powerful tool for evaluating models, but it requires careful interpretation:

<div class="red-box">
  <strong>Key Principle:</strong>  
  <li> If there is significant uncertainty in model comparisons, avoid selecting the single model with the best cross-validation result. This discards the uncertainty from the CV process. </li>
</div>

**Alternative Approaches:**
- **Stacking:**  
  Combines inferences by weighting models to minimize cross-validation error. Stacking can sometimes be seen as pointwise model selection.
- **Scaffold Models:**  
  Include models that are deliberately simple (e.g., for comparison), experimental, or flawed (e.g., with coding errors). These models serve as benchmarks or stepping stones but are not included in final predictions.

While BW emphasizes continuous model expansion over averaging, there are cases where averaging predictions over competing Bayesian models is reasonable.

### Comparing a Large Number of Models
When faced with many candidate models, the goal is often to find a simpler model with comparable predictive performance to a more complex, expanded model.

<div class="red-box">
  <strong>Warning:</strong>  
  <li> Selecting one model based solely on minimizing cross-validation error risks overfitting and suboptimal choices. </li>
</div>

**Projection Predictive Variable Selection:**
- A stable and reliable method to identify smaller models with strong predictive performance.
- Avoids overfitting by:
  - Projecting submodels based on the expanded model’s predictions.
  - Not fitting each model independently to the data.

This approach enables efficient comparison of a large number of models while maintaining robust predictive performance.

### Final Thoughts
Understanding and comparing multiple models is an integral part of Bayesian Workflow. By focusing on the process of model fitting rather than rigid selection or averaging, practitioners can better navigate uncertainty and extract meaningful insights from their analyses. Tools like stacking and projection predictive variable selection ensure that model comparison remains both rigorous and practical.


---

## Discussion

### Different Perspectives on Statistical Modeling and Prediction
Statistical modeling and prediction can be approached from several perspectives, each with unique goals and implications:

1. **Traditional Statistical Perspective:**  
   - Models are typically predefined, and the goal is to accurately summarize the posterior distribution.  
   - Computation continues until approximate convergence is achieved, with approximations used sparingly.  

2. **Machine Learning Perspective:**  
   - The primary focus is on prediction rather than parameter estimation.  
   - Computation halts once cross-validation accuracy plateaus, emphasizing scalability and efficiency within a fixed computational budget.

3. **Model Exploration Perspective:**  
   - Applied statistical work often involves trying out many models, some of which may exhibit poor data fit, low predictive performance, or slow convergence.  
   - Approximations are more acceptable here but must faithfully reproduce key posterior features.

<div class="green-box">
  <strong>Key Insight:</strong>  
  The distinction here is not between inference vs. prediction or exploratory vs. confirmatory analysis, but rather how much trust is placed in a model and how computation approximates it.
</div>

<div class="yellow-box">
  <strong>Model Trust:</strong>  
  The process of iterative model building highlights how much computation and model development rely on trust in individual models and their approximations.
</div>

These differing perspectives influence how statistical methods evolve as new challenges emerge in applied settings.

### Justification of Iterative Model Building
The iterative model-building process is central to modern Bayesian Workflow (BW) and represents the next transformative step in data science:
- **Historical Progression:**  
  - **Data Summarization:** The foundation of statistics up to 1900.  
  - **Modeling:** Began with Gauss and Laplace, continuing to this day.  
  - **Computation:** The current focus, enabling iterative workflows and complex modeling.  

- **Real-World Considerations:**  
  - BW acknowledges the limitations of human and computational resources.  
  - The goal is to simplify processes for humans, even in idealized settings where exact computation is automated.  
  - Fully automated computation yielding perfect results remains unattainable.

<div class="green-box">
  <strong>Simplifying Challenges:</strong>   
  <li> Computational challenges are easier to address when fewer "moving parts" exist in the modeling process. </li>
</div>

---

### Model Selection and Overfitting
An iterative workflow risks overfitting, as model improvement often involves conditioning on data discrepancies:
- **Double Dipping:** Using data multiple times during model iteration can compromise the frequency properties of inferences.

<div class="red-box">
<strong>Warning:</strong>  
  <li> Double dipping and post-selection inference can lead to overfitting. Model improvement conditioned on discrepancies must be carefully managed. </li>
</div>

**Garden of Forking Paths:**  
- The model-building process often involves paths that depend on the specific data observed.  
- Instead of selecting the best-fitting model, BW emphasizes iterative improvements, ensuring each step is justified.

<div class="blue-box">
<strong>Example:</strong>  
 </li>  Suppose model \(M_1\) fails a posterior predictive check, leading to the development of \(M_2\), which incorporates more prior information and better fits the data. Had the data differed, \(M_1\) might have sufficed. This highlights the iterative nature of **BW**. </li>
</div>

To mitigate post-selection inference issues:
- Embed multiple models in a larger framework.
- Use predictive model averaging or incorporate all models simultaneously.
- Perform severe tests of the assumptions underlying each model.

### Bigger Datasets Demand Bigger Models
Larger datasets enable the fitting of complex models, such as hierarchical Bayesian models and deep learning approaches:
- These models facilitate information aggregation and partial pooling across diverse data sources.
- Effective modeling requires:
  1. **Regularization:** To stabilize estimates.  
  2. **Latent Variable Modeling:** To address missingness and measurement errors.

<div class="yellow-box">
<strong>Insight:</strong>  
  <li> A model does not exist in isolation; it emerges from engagement with the application and available data. </li>
</div>

### Prediction, Generalization, and Poststratification
Statistical tasks often involve generalization, which Bayesian methods address effectively:
1. **Generalizing from Sample to Population:** Using hierarchical models and partial pooling.  
2. **Generalizing from Control to Treatment Groups:** Leveraging regularization to handle large nonparametric models.  
3. **Generalizing from Observed Data to Underlying Constructs:** Applying multilevel modeling for latent variables.

<div class="green-box">
<strong>Key Principle:</strong>  
  <li> Just as priors are understood in the context of the likelihood, models should be understood in light of their intended use. </li>
</div>

**Methods in Bayesian Framework:**
- Hierarchical modeling and transportability via Bayesian graph models.
- Regularization to handle complex, large-scale models.

The iterative nature of Bayesian Workflow, with its emphasis on model trust, computational efficiency, and careful navigation of overfitting risks, reflects the dynamic and evolving nature of modern statistical practice. By embedding models within a larger framework and embracing the iterative process, BW ensures robust and insightful statistical analyses.






