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

  <section class="research-poster-feature" id="isba2026-poster" aria-labelledby="isba2026-poster-title">
    <a class="research-poster-feature__media" href="/files/posters/isba-2026-poster-aguirre.pdf" target="_blank" rel="noopener noreferrer">
      <img
        src="/public/images/posters/isba-2026-poster-preview.jpg"
        alt="Preview of the ISBA 2026 poster Bayesian quantile-based correction and synthesis of climate products"
        loading="lazy">
    </a>
    <div class="research-poster-feature__body">
      <p class="software-kicker">Conference Poster</p>
      <h2 id="isba2026-poster-title">ISBA 2026 World Meeting</h2>
      <p>
        My poster <em>Bayesian quantile-based correction and synthesis of climate products</em> was accepted
        for the ISBA 2026 World Meeting in Nagoya, Japan. The work presents a Bayesian quantile workflow
        for correcting climate-product forecasts and synthesizing the corrected quantile lanes into a
        posterior predictive distribution, with daily San Lorenzo River flow as the case study.
      </p>
      <dl class="research-poster-feature__details">
        <div>
          <dt>Authors</dt>
          <dd>Antonio Aguirre, Raquel Prado, and Bruno Sansó</dd>
        </div>
        <div>
          <dt>Focus</dt>
          <dd>Forecast correction, quantile dynamic modeling, posterior synthesis, and state-space modelling.</dd>
        </div>
      </dl>
      <div class="research-poster-feature__actions">
        <a class="software-button" href="/files/posters/isba-2026-poster-aguirre.pdf" target="_blank" rel="noopener noreferrer">
          <i class="far fa-file-pdf" aria-hidden="true"></i>
          <span>Open Poster</span>
        </a>
        <a class="software-button software-button--secondary" href="/files/posters/isba-2026-poster-aguirre.pdf" download>
          <i class="fas fa-download" aria-hidden="true"></i>
          <span>Download PDF</span>
        </a>
      </div>
    </div>
  </section>

  <!-- Selected Publications -->
  <div class="publication-section">
    <h2>Selected Papers, Posters &amp; Software</h2>
    <ul class="research-output-list">
      <li class="research-output-item">
        <span class="research-output__status">Accepted poster</span>
        <div>
          Aguirre, A., Prado, R., Sansó, B.
          <em>Bayesian quantile-based correction and synthesis of climate products</em>.
          ISBA 2026 World Meeting, Nagoya, Japan.
          <a href="/files/posters/isba-2026-poster-aguirre.pdf" target="_blank" rel="noopener noreferrer">Poster PDF</a>.
        </div>
      </li>
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
