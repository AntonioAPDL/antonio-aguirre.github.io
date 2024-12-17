---
layout: post
title: "Bayesian Worklflow"
date: 2024-12-20
theme: Review
tags: [statistics, bayesian, math, methodology]
excerpt: "A review on the recently proposed Bayesian Workflow, and some commentary."
---
# Bayesian Workflow Table of Contents

## 1. Introduction
- **1.1** From Bayesian inference to Bayesian workflow
- **1.2** Why do we need a Bayesian workflow?  
- **1.3** “Workflow” and its relation to statistical theory and practice  
- **1.4** Organizing the many aspects of Bayesian workflow  
- **1.5** Aim and structure of this article  

---

## 2. Before Fitting a Model
- **2.1** Choosing an initial model  
- **2.2** Modular construction  
- **2.3** Scaling and transforming the parameters  
- **2.4** Prior predictive checking  
- **2.5** Generative and partially generative models  

---

## 3. Fitting a Model
- **3.1** Initial values, adaptation, and warmup  
- **3.2** How long to run an iterative algorithm  
- **3.3** Approximate algorithms and approximate models  
- **3.4** Fit fast, fail fast  

---

## 4. Using Constructed Data to Find and Understand Problems
- **4.1** Fake-data simulation  
- **4.2** Simulation-based calibration  
- **4.3** Experimentation using constructed data  

---

## 5. Addressing Computational Problems
- **5.1** The folk theorem of statistical computing  
- **5.2** Starting at simple and complex models and meeting in the middle  
- **5.3** Getting a handle on models that take a long time to fit  
- **5.4** Monitoring intermediate quantities  
- **5.5** Stacking to reweight poorly mixing chains  
- **5.6** Posterior distributions with multimodality and other difficult geometry  
- **5.7** Reparameterization  
- **5.8** Marginalization  
- **5.9** Adding prior information  
- **5.10** Adding data  

---

## 6. Evaluating and Using a Fitted Model
- **6.1** Posterior predictive checking  
- **6.2** Cross-validation and influence of individual data points and subsets of the data  
- **6.3** Influence of prior information  
- **6.4** Summarizing inference and propagating uncertainty  

---

## 7. Modifying a Model
- **7.1** Constructing a model for the data  
- **7.2** Incorporating additional data  
- **7.3** Working with prior distributions  
- **7.4** A topology of models  

---

## 8. Understanding and Comparing Multiple Models
- **8.1** Visualizing models in relation to each other  
- **8.2** Cross-validation and model averaging  
- **8.3** Comparing a large number of models  

---

## 9. Modeling as Software Development
- **9.1** Version control smooths collaborations with others and with your past self  
- **9.2** Testing as you go  
- **9.3** Making it essentially reproducible  
- **9.4** Making it readable and maintainable  

---

## 10. Example of Workflow Involving Model Building and Expansion: Golf Putting
- **10.1** First model: logistic regression  
- **10.2** Modeling from first principles  
- **10.3** Testing the fitted model on new data  
- **10.4** A new model accounting for how hard the ball is hit  
- **10.5** Expanding the model by including a fudge factor  
- **10.6** General lessons from the golf example  

---

## 11. Example of Workflow for a Model with Unexpected Multimodality: Planetary Motion
- **11.1** Mechanistic model of motion  
- **11.2** Fitting a simplified model  
- **11.3** Bad Markov chain, slow Markov chain?  
- **11.4** Building up the model  
- **11.5** General lessons from the planetary motion example  

---

## 12. Discussion
- **12.1** Different perspectives on statistical modeling and prediction  
- **12.2** Justification of iterative model building  
- **12.3** Model selection and overfitting  
- **12.4** Bigger datasets demand bigger models  
- **12.5** Prediction, generalization, and poststratification  
- **12.6** Going forward  
