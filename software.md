---
layout: default
title: Software
description: "Overview of software projects and tools in development."
---

<div class="software-section">
  <header class="software-hero">
    <p class="software-kicker">Research Software</p>
    <h1 class="section-heading">Software</h1>
    <p class="software-intro">
      Tools for Bayesian modeling, time-series forecasting, uncertainty quantification, and reproducible scientific computing.
    </p>
  </header>

  <article class="software-feature">
    <div class="software-feature__media" aria-hidden="true">
      <img src="{{ '/public/images/devicons/r.svg' | absolute_url }}" alt="" loading="lazy" class="software-feature__icon">
      <span class="software-feature__monogram">ex</span>
    </div>
    <div class="software-feature__body">
      <div class="software-feature__eyebrow">
        <span>R package</span>
        <span>CRAN 0.4.0</span>
        <span>JSS manuscript submitted</span>
      </div>
      <h2><code>exdqlm</code>: Extended Dynamic Quantile Linear Models</h2>
      <p>
        Bayesian quantile-regression software for dynamic state-space models under the extended asymmetric Laplace family.
        The package supports MCMC and Laplace-delta variational Bayes inference, forecasting, diagnostics, static exAL
        regression with regularized priors, transfer-function effects, and posterior-predictive synthesis across fitted quantiles.
      </p>
      <div class="software-actions" aria-label="exdqlm links">
        <a class="software-button" href="https://CRAN.R-project.org/package=exdqlm" target="_blank" rel="noopener noreferrer">
          <i class="fas fa-cube" aria-hidden="true"></i>
          <span>CRAN</span>
        </a>
        <a class="software-button software-button--secondary" href="https://github.com/AntonioAPDL/exdqlm" target="_blank" rel="noopener noreferrer">
          <i class="fab fa-github" aria-hidden="true"></i>
          <span>GitHub</span>
        </a>
        <a class="software-button software-button--secondary" href="https://doi.org/10.32614/CRAN.package.exdqlm" target="_blank" rel="noopener noreferrer">
          <i class="fas fa-external-link-alt" aria-hidden="true"></i>
          <span>DOI</span>
        </a>
      </div>
    </div>
  </article>

  <section class="software-capability-grid" aria-label="exdqlm capabilities">
    <div class="software-capability">
      <i class="fas fa-chart-line" aria-hidden="true"></i>
      <h3>Dynamic Quantiles</h3>
      <p>Latent state-space quantile models with trend, seasonal, regression, and transfer-function components.</p>
    </div>
    <div class="software-capability">
      <i class="fas fa-tachometer-alt" aria-hidden="true"></i>
      <h3>Fast Inference</h3>
      <p>MCMC for full posterior simulation and LDVB for scalable approximate inference on longer time series.</p>
    </div>
    <div class="software-capability">
      <i class="fas fa-vial" aria-hidden="true"></i>
      <h3>Diagnostics</h3>
      <p>Forecast calibration checks, posterior predictive summaries, scoring rules, and reproducible manuscript examples.</p>
    </div>
  </section>

  <section class="software-note">
    <h2>Publication Track</h2>
    <p>
      The companion article, <em>exdqlm: An R Package for Estimation and Analysis of Flexible Dynamic Quantile Linear Models</em>,
      has been submitted to the <em>Journal of Statistical Software</em>. The reproducible manuscript workflow tracks the current
      package-development branch, while the public package release is available on CRAN.
    </p>
    <p class="software-updated">Last updated: May 13, 2026</p>
  </section>

  <section class="language-software" aria-label="Software stack">
    <h2>Stack</h2>
    <ul class="software-stack">
      <li><img src="{{ '/public/images/devicons/r.svg' | absolute_url }}" alt="" loading="lazy" class="software-icon"> R package development</li>
      <li><img src="{{ '/public/images/devicons/cpp.svg' | absolute_url }}" alt="" loading="lazy" class="software-icon"> C++ acceleration through Rcpp</li>
      <li><img src="{{ '/public/images/devicons/python.svg' | absolute_url }}" alt="" loading="lazy" class="software-icon"> Python workflows for data and automation</li>
      <li><img src="{{ '/public/images/devicons/matlab.svg' | absolute_url }}" alt="" loading="lazy" class="software-icon"> MATLAB research prototypes</li>
      <li><img src="{{ '/public/images/devicons/julia.svg' | absolute_url }}" alt="" loading="lazy" class="software-icon"> Julia exploration for numerical computing</li>
    </ul>
  </section>
</div>
