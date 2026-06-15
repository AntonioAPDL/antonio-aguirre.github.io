---
layout: default
title: Research
description: "Research on Bayesian forecasting, quantile modeling, scalable inference, and research software."
---

<div class="research-section">
  <!-- Title and Introduction -->
  <header class="research-hero page-header">
    <h1 class="page-title">Research</h1>
    <p class="page-lede">
      I develop Bayesian time-series methods for probabilistic forecasting, with an emphasis on quantile modeling,
      uncertainty quantification, scalable inference, and reusable research software.
    </p>
    <p class="page-lede">
      Much of this work is motivated by hydrological and environmental forecasting, where forecasts need to be calibrated,
      interpretable, computationally practical, and easy to update as new data arrive.
    </p>
  </header>

  <section class="research-area-grid" aria-label="Research areas">
    <article class="research-area">
      <span>Forecasting</span>
      <h2>Forecast Correction and Synthesis</h2>
      <p>
        Bayesian quantile methods for correcting river-flow forecasts, combining forecast sources,
        and evaluating predictive distributions with proper scoring rules.
      </p>
    </article>
    <article class="research-area">
      <span>Nonlinear Time Series</span>
      <h2>Q-DESN Quantile Forecasting</h2>
      <p>
        Bayesian quantile readouts for fixed Deep Echo State Network features, with regularized readouts,
        exAL working likelihoods, MCMC, and variational approximations.
      </p>
    </article>
    <article class="research-area">
      <span>State Space Models</span>
      <h2>Dynamic Quantile Models</h2>
      <p>
        Flexible dynamic quantile linear models with trend, seasonal, regression, transfer-function,
        forecasting, diagnostics, and posterior synthesis components.
      </p>
    </article>
    <article class="research-area">
      <span>Computation</span>
      <h2>Scalable Inference and Diagnostics</h2>
      <p>
        Variational Bayes, Sequential Monte Carlo, simulation diagnostics, and reproducible workflows
        for models that need to run repeatedly and be checked carefully.
      </p>
    </article>
  </section>

  <!-- Selected Publications -->
  <div class="publication-section">
    <h2>Selected Papers &amp; Software</h2>
    <ul class="research-output-list">
      <li class="research-output-item">
        <span class="research-output__status">Submitted / CRAN v1.0.0</span>
        <div>
          Aguirre, A., Barata, R., Prado, R., Sansó, B.
          <em>exdqlm: An R Package for Estimation and Analysis of Flexible Dynamic Quantile Linear Models</em>.
          Manuscript submitted to the <em>Journal of Statistical Software</em>; companion package released on
          <a href="https://CRAN.R-project.org/package=exdqlm" target="_blank" rel="noopener noreferrer">CRAN</a>.
        </div>
      </li>
      <li class="research-output-item">
        <span class="research-output__status">Working paper</span>
        <div>
          Aguirre, A., Prado, R., Sansó, B.
          <em>Bayesian Quantile Readouts for Fixed Deep Echo State Networks</em>.
          Current work on Q-DESN quantile forecasting.
        </div>
      </li>
      <li class="research-output-item">
        <span class="research-output__status">In revision</span>
        <div>
          Aguirre, A., Sansó, B., Prado, R.
          <em>A Bayesian Quantile-Based Correction and Synthesis of River Flow Forecasts</em>.
          Manuscript in revision.
        </div>
      </li>
      <li class="research-output-item">
        <span class="research-output__status">Published</span>
        <div>
          Aguirre, A., Lobato, I.N. (2024).
          <em>Evidence of Non-Fundamentalness in OECD Capital Stocks</em>.
          <em>Empirical Economics</em>.
          <a href="https://doi.org/10.1007/s00181-024-02564-5" target="_blank" rel="noopener noreferrer">DOI</a>.
        </div>
      </li>
    </ul>
  </div>

  <div class="research-software-note">
    <h2>Code and Reproducibility</h2>
    <p>
      Selected package code, manuscript-support scripts, and data-processing workflows are collected on the
      <a href="/software/">Software page</a>. I keep that page selective so each public example has a clear purpose
      and enough context to be useful.
    </p>
  </div>
</div>
