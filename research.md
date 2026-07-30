---
layout: default
title: Research
description: "Research on Bayesian forecasting, quantile modeling, scalable inference, and research software."
---

{% assign exdqlm = site.data.cran_packages.exdqlm %}
{% assign exdqlm_version = exdqlm.version | default: "1.1.0" %}
{% assign exdqlm_arxiv_url = exdqlm.arxiv_url | default: "https://arxiv.org/abs/2607.22760" %}
{% assign rqr_arxiv_url = "https://arxiv.org/abs/2607.26098" %}

<div class="research-section">
  <!-- Title and Introduction -->
  <header class="research-hero page-header">
    <h1 class="page-title">Research</h1>
    <p class="page-lede">
      I develop Bayesian quantile methods for probabilistic forecasting, interval modeling,
      scalable inference, and reusable research software.
    </p>
    <p class="page-lede">
      My Ph.D. work is organized around hydrologic forecast correction, dynamic quantile state-space models,
      fixed-reservoir quantile readouts, and generalized-Bayes interval functionals.
    </p>
  </header>

  <section class="research-area-grid" aria-label="Research areas">
    <article class="research-area">
      <span>In revision</span>
      <h2>Hydrologic Forecast Correction</h2>
      <p>
        Bayesian quantile correction and synthesis for USGS observations, retrospective products,
        and operational forecast products in river-flow forecasting.
      </p>
    </article>
    <article class="research-area">
      <span>Software / JSS</span>
      <h2>Dynamic Quantile State-Space Models</h2>
      <p>
        Extended dynamic quantile linear models with MCMC, Laplace-delta variational Bayes,
        diagnostics, forecasting, and posterior-predictive synthesis.
      </p>
    </article>
    <article class="research-area">
      <span>Working paper</span>
      <h2>Q-DESN Quantile Forecasting</h2>
      <p>
        Bayesian quantile readouts for fixed Deep Echo State Network features, with shrinkage priors,
        single-quantile and multi-quantile reporting, and forecast validation.
      </p>
    </article>
    <article class="research-area">
      <span>arXiv preprint</span>
      <h2>Mean-Tilted RQR</h2>
      <p>
        Relaxed quantile regression for fixed-content interval targets, treated through
        loss-based generalized posteriors and Gibbs computation.
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
      <p class="software-kicker">Best Poster Prize</p>
      <h2 id="isba2026-poster-title">ISBA 2026 World Meeting</h2>
      <p>
        My poster <em>Bayesian quantile-based correction and synthesis of climate products</em> received a
        Best Poster Prize at the ISBA 2026 World Meeting in Nagoya, Japan. The work presents a Bayesian
        quantile workflow for correcting hydrologic forecast products and synthesizing the corrected quantile
        lanes into a posterior predictive distribution, with daily San Lorenzo River flow as the case study.
      </p>
      <dl class="research-poster-feature__details">
        <div>
          <dt>Recognition</dt>
          <dd>Best Poster Prize, ISBA 2026 World Meeting.</dd>
        </div>
        <div>
          <dt>Authors</dt>
          <dd>Antonio De Leon, Raquel Prado, and Bruno Sansó</dd>
        </div>
        <div>
          <dt>Focus</dt>
          <dd>Forecast correction, quantile dynamic modeling, posterior synthesis, and state-space modeling.</dd>
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
    <h2>Selected Papers &amp; Software</h2>
    <ul class="research-output-list">
      <li class="research-output-item">
        <span class="research-output__status">JSS / CRAN v{{ exdqlm_version }}</span>
        <div>
          De Leon, A., Barata, R., Prado, R., Sansó, B.
          <em>exdqlm: An R Package for Estimation and Analysis of Flexible Dynamic Quantile Linear Models</em>.
          Manuscript submitted to the <em>Journal of Statistical Software</em>; package on
          <a href="https://CRAN.R-project.org/package=exdqlm" target="_blank" rel="noopener noreferrer">CRAN</a>;
          <a href="{{ exdqlm_arxiv_url }}" target="_blank" rel="noopener noreferrer">arXiv preprint</a>.
        </div>
      </li>
      <li class="research-output-item">
        <span class="research-output__status">In revision / awards</span>
        <div>
          De Leon, A., Prado, R., Sansó, B.
          <em>Bayesian Quantile-Based Correction and Synthesis of Hydrologic Products</em>.
          Manuscript in revision at <em>Environmetrics</em>. Related work received the EnviBayes Student Paper
          Competition award and the ISBA 2026 Best Poster Prize.
          <a href="/files/posters/isba-2026-poster-aguirre.pdf" target="_blank" rel="noopener noreferrer">Poster PDF</a>.
        </div>
      </li>
      <li class="research-output-item">
        <span class="research-output__status">Working paper</span>
        <div>
          De Leon, A., Prado, R., Sansó, B.
          <em>Bayesian Quantile Readouts for Fixed Deep Echo State Networks</em>.
          Working paper on fixed-reservoir quantile forecasting with Bayesian readouts.
        </div>
      </li>
      <li class="research-output-item">
        <span class="research-output__status">arXiv preprint</span>
        <div>
          De Leon, A., Prado, R., Sansó, B.
          <em>Mean-Tilted Relaxed Quantile Regression: Fixed-Content Interval Functionals and Generalized-Bayes Computation</em>.
          Preprint on interval-root functionals, fixed-content intervals, and generalized-Bayes computation.
          <a href="{{ rqr_arxiv_url }}" target="_blank" rel="noopener noreferrer">arXiv:2607.26098</a>.
        </div>
      </li>
      <li class="research-output-item">
        <span class="research-output__status">Published</span>
        <div>
          De Leon, A., Lobato, I.N. (2024).
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
