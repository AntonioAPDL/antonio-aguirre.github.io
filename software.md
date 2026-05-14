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

  <section class="software-note">
    <h2>Publication Track</h2>
    <p>
      The companion article, <em>exdqlm: An R Package for Estimation and Analysis of Flexible Dynamic Quantile Linear Models</em>,
      has been submitted to the <em>Journal of Statistical Software</em>. The reproducible manuscript workflow tracks the current
      package-development branch, while the public package release is available on CRAN.
    </p>
    <p class="software-updated">Last updated: May 14, 2026</p>
  </section>

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

  <section class="software-samples" aria-label="Selected open-access code samples">
    <div class="software-samples__header">
      <p class="software-kicker">Open-Access Samples</p>
      <h2>Selected Code</h2>
      <p>
        A small, curated sample of public code from my research software work. These examples highlight documented
        R interfaces, numerical C++ kernels, diagnostics, and tests; more samples will be added as active projects
        mature into public release branches.
      </p>
    </div>

    <div class="software-sample-grid">
      <article class="software-sample">
        <div class="software-sample__icon"><i class="fab fa-r-project" aria-hidden="true"></i></div>
        <h3>Laplace-Delta VB Engine</h3>
        <p>
          Dynamic Bayesian quantile state-space inference with documented controls, warm starts, diagnostics,
          and posterior predictive output.
        </p>
        <a href="https://github.com/AntonioAPDL/exdqlm/blob/main/R/exdqlmLDVB.R" target="_blank" rel="noopener noreferrer">
          <span>View R source</span>
          <i class="fas fa-external-link-alt" aria-hidden="true"></i>
        </a>
      </article>

      <article class="software-sample">
        <div class="software-sample__icon"><i class="fab fa-r-project" aria-hidden="true"></i></div>
        <h3>Posterior Simulation</h3>
        <p>
          MCMC workflow for exDQLM posterior sampling, including VB initialization paths and dynamic model controls.
        </p>
        <a href="https://github.com/AntonioAPDL/exdqlm/blob/main/R/exdqlmMCMC.R" target="_blank" rel="noopener noreferrer">
          <span>View R source</span>
          <i class="fas fa-external-link-alt" aria-hidden="true"></i>
        </a>
      </article>

      <article class="software-sample">
        <div class="software-sample__icon"><i class="fas fa-layer-group" aria-hidden="true"></i></div>
        <h3>Quantile Synthesis</h3>
        <p>
          Post-processing for separately fitted quantile models, using isotonic correction and monotone rearrangement
          to produce coherent predictive summaries.
        </p>
        <a href="https://github.com/AntonioAPDL/exdqlm/blob/main/R/quantileSynthesis.R" target="_blank" rel="noopener noreferrer">
          <span>View R source</span>
          <i class="fas fa-external-link-alt" aria-hidden="true"></i>
        </a>
      </article>

      <article class="software-sample">
        <div class="software-sample__icon"><i class="fas fa-microchip" aria-hidden="true"></i></div>
        <h3>exAL Numerics</h3>
        <p>
          Rcpp/Boost implementation of extended asymmetric Laplace distribution utilities, including stable
          parameter-bound calculations.
        </p>
        <a href="https://github.com/AntonioAPDL/exdqlm/blob/main/src/exAL.cpp" target="_blank" rel="noopener noreferrer">
          <span>View C++ source</span>
          <i class="fas fa-external-link-alt" aria-hidden="true"></i>
        </a>
      </article>

      <article class="software-sample">
        <div class="software-sample__icon"><i class="fas fa-wave-square" aria-hidden="true"></i></div>
        <h3>Kalman &amp; FFBS Kernels</h3>
        <p>
          C++ acceleration for state updates and forward-filtering backward-sampling routines used by dynamic
          quantile workflows.
        </p>
        <a href="https://github.com/AntonioAPDL/exdqlm/tree/main/src" target="_blank" rel="noopener noreferrer">
          <span>Browse C++ kernels</span>
          <i class="fas fa-external-link-alt" aria-hidden="true"></i>
        </a>
      </article>

      <article class="software-sample">
        <div class="software-sample__icon"><i class="fas fa-vial" aria-hidden="true"></i></div>
        <h3>Regression Tests</h3>
        <p>
          Focused tests for diagnostics, exAL utilities, synthesis behavior, and package-level reproducibility contracts.
        </p>
        <a href="https://github.com/AntonioAPDL/exdqlm/tree/main/tests/testthat" target="_blank" rel="noopener noreferrer">
          <span>Browse tests</span>
          <i class="fas fa-external-link-alt" aria-hidden="true"></i>
        </a>
      </article>
    </div>

    <div class="software-github-cta">
      <div>
        <h3>Open Development on GitHub</h3>
        <p>
          Public repositories linked from this page are open access. I use GitHub to track releases, tests,
          reproducible manuscript workflows, and selected statistical-computing prototypes as they become ready
          for public review.
        </p>
      </div>
      <div class="software-github-cta__actions" aria-label="GitHub profile links">
        <a class="software-button" href="https://github.com/AntonioAPDL?tab=overview" target="_blank" rel="noopener noreferrer">
          <i class="fab fa-github" aria-hidden="true"></i>
          <span>View Activity</span>
        </a>
        <a class="software-button software-button--secondary" href="https://github.com/AntonioAPDL?tab=repositories" target="_blank" rel="noopener noreferrer">
          <i class="fas fa-folder-open" aria-hidden="true"></i>
          <span>Browse Repos</span>
        </a>
      </div>
    </div>
  </section>

  <section class="language-software" aria-label="Languages and environments">
    <h2>Languages &amp; Environments</h2>
    <p class="software-stack-intro">
      The current public samples emphasize the mature R/C++ release path behind <code>exdqlm</code>. I also work across
      Python, MATLAB, and Julia for data workflows, research prototypes, and numerical experiments; those projects will be
      added here as curated, documented public snapshots when they are ready for reuse.
    </p>
    <ul class="software-stack">
      <li><img src="{{ '/public/images/devicons/r.svg' | absolute_url }}" alt="" loading="lazy" class="software-icon"> R package development</li>
      <li><img src="{{ '/public/images/devicons/cpp.svg' | absolute_url }}" alt="" loading="lazy" class="software-icon"> C++ acceleration through Rcpp</li>
      <li><img src="{{ '/public/images/devicons/python.svg' | absolute_url }}" alt="" loading="lazy" class="software-icon"> Python workflows for data and automation</li>
      <li><img src="{{ '/public/images/devicons/matlab.svg' | absolute_url }}" alt="" loading="lazy" class="software-icon"> MATLAB research prototypes</li>
      <li><img src="{{ '/public/images/devicons/julia.svg' | absolute_url }}" alt="" loading="lazy" class="software-icon"> Julia exploration for numerical computing</li>
    </ul>
    <div class="software-future-note">
      <h3>More Software in Preparation</h3>
      <p>
        Additional MATLAB, Julia, and Python examples are planned for this page after cleanup for documentation,
        reproducibility, and publishability. The goal is to share code that is useful beyond a single project folder,
        with clear entry points and enough context for readers to understand what each sample demonstrates.
      </p>
    </div>
  </section>
</div>
