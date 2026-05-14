---
layout: default
title: Software
description: "Public packages, research code, and selected implementation examples."
---

<div class="software-section">
  <header class="software-hero">
    <p class="software-kicker">Research Software</p>
    <h1 class="section-heading">Software</h1>
    <p class="software-intro">
      Public packages, research code, and selected implementation examples for Bayesian modeling,
      forecasting, and scientific computing.
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
        An R package for Bayesian estimation and analysis of dynamic quantile linear models under the extended asymmetric
        Laplace family. It supports MCMC and Laplace-delta variational Bayes, state-space components, transfer-function
        effects, forecasting, diagnostics, and posterior synthesis across fitted quantiles.
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
    <h2>Release &amp; Manuscript</h2>
    <p>
      <code>exdqlm</code> is available on CRAN. A companion article,
      <em>exdqlm: An R Package for Estimation and Analysis of Flexible Dynamic Quantile Linear Models</em>, has been
      submitted to the <em>Journal of Statistical Software</em>; manuscript examples are maintained alongside package development.
    </p>
    <p class="software-updated">Last updated: May 14, 2026</p>
  </section>

  <section class="software-capability-grid" aria-label="exdqlm capabilities">
    <div class="software-capability">
      <i class="fas fa-chart-line" aria-hidden="true"></i>
      <h3>Dynamic Quantile Models</h3>
      <p>State-space quantile models with trend, seasonal, regression, and transfer-function components.</p>
    </div>
    <div class="software-capability">
      <i class="fas fa-tachometer-alt" aria-hidden="true"></i>
      <h3>Inference Engines</h3>
      <p>MCMC for posterior simulation and LDVB for scalable approximate inference on longer time series.</p>
    </div>
    <div class="software-capability">
      <i class="fas fa-vial" aria-hidden="true"></i>
      <h3>Diagnostics &amp; Forecasting</h3>
      <p>Forecast summaries, calibration checks, scoring rules, and posterior predictive output.</p>
    </div>
  </section>

  <section class="software-samples" aria-label="Public projects and artifacts">
    <div class="software-samples__header">
      <p class="software-kicker">Public Work</p>
      <h2>Projects &amp; Artifacts</h2>
      <p>
        Released packages, manuscript materials, public site workflows, and methods notes. Each item is linked
        so readers can inspect the repository or source files directly.
      </p>
    </div>

    <div class="software-project-grid">
      <article class="software-project">
        <div class="software-project__meta">
          <span>Released package</span>
          <span>R / C++</span>
        </div>
        <h3><code>exdqlm</code></h3>
        <p>
          CRAN package for Bayesian dynamic quantile state-space modeling, with MCMC, LDVB, C++ kernels,
          forecast diagnostics, and multi-quantile synthesis.
        </p>
        <a href="https://github.com/AntonioAPDL/exdqlm" target="_blank" rel="noopener noreferrer">
          <span>Package repository</span>
          <i class="fas fa-external-link-alt" aria-hidden="true"></i>
        </a>
      </article>

      <article class="software-project">
        <div class="software-project__meta">
          <span>Article workflow</span>
          <span>R / TeX</span>
        </div>
        <h3><code>exdqlm</code> JSS Article</h3>
        <p>
          Public manuscript source, supplement files, and reproducibility notes for the submitted
          <em>Journal of Statistical Software</em> article.
        </p>
        <a href="https://github.com/AntonioAPDL/exdqlm---Article" target="_blank" rel="noopener noreferrer">
          <span>Article repository</span>
          <i class="fas fa-external-link-alt" aria-hidden="true"></i>
        </a>
      </article>

      <article class="software-project">
        <div class="software-project__meta">
          <span>Site workflows</span>
          <span>Python / R / Bash</span>
        </div>
        <h3>Forecast &amp; Climate Tools</h3>
        <p>
          Public scripts behind this website's forecast and climate-data outputs, including NOAA NWPS
          requests, climate/soil-moisture merges, and repository checks.
        </p>
        <a href="https://github.com/AntonioAPDL/antonio-aguirre.github.io/tree/main/scripts" target="_blank" rel="noopener noreferrer">
          <span>Browse scripts</span>
          <i class="fas fa-external-link-alt" aria-hidden="true"></i>
        </a>
      </article>

      <article class="software-project">
        <div class="software-project__meta">
          <span>Methods notes</span>
          <span>Q-DESN</span>
        </div>
        <h3>Q-DESN Theory Notes</h3>
        <p>
          Public notes for Q-DESN implementation ideas, notation, and model structure. Application code will
          be added after it is documented for public use.
        </p>
        <a href="https://github.com/AntonioAPDL/Q-DESN---Theory-for-implementation" target="_blank" rel="noopener noreferrer">
          <span>Read notes</span>
          <i class="fas fa-external-link-alt" aria-hidden="true"></i>
        </a>
      </article>
    </div>
  </section>

  <section class="software-samples" aria-label="Selected implementation examples">
    <div class="software-samples__header">
      <p class="software-kicker">Code Samples</p>
      <h2>Selected Implementations</h2>
      <p>
        Concrete files from public repositories. The goal is not to list everything, but to show implementation
        style across package APIs, numerical kernels, data pipelines, and checks.
      </p>
    </div>

    <div class="software-sample-grid">
      <article class="software-sample">
        <div class="software-sample__icon"><i class="fab fa-r-project" aria-hidden="true"></i></div>
        <h3>LDVB Inference Interface</h3>
        <p>
          Main LDVB interface for dynamic quantile state-space models, with controls for initialization,
          diagnostics, and posterior predictive summaries.
        </p>
        <a href="https://github.com/AntonioAPDL/exdqlm/blob/main/R/exdqlmLDVB.R" target="_blank" rel="noopener noreferrer">
          <span>View R source</span>
          <i class="fas fa-external-link-alt" aria-hidden="true"></i>
        </a>
      </article>

      <article class="software-sample">
        <div class="software-sample__icon"><i class="fab fa-r-project" aria-hidden="true"></i></div>
        <h3>Q-DESN Overlay Builder</h3>
        <p>
          R script for building a Big Trees Q-DESN forecast overlay with explicit arguments, API access,
          and package-loading checks.
        </p>
        <a href="https://github.com/AntonioAPDL/antonio-aguirre.github.io/blob/main/scripts/build_big_trees_qdesn_overlay.R" target="_blank" rel="noopener noreferrer">
          <span>View R source</span>
          <i class="fas fa-external-link-alt" aria-hidden="true"></i>
        </a>
      </article>

      <article class="software-sample">
        <div class="software-sample__icon"><i class="fas fa-microchip" aria-hidden="true"></i></div>
        <h3>exAL Numerics</h3>
        <p>
          Rcpp/Boost implementation of extended asymmetric Laplace distribution utilities and parameter-bound calculations.
        </p>
        <a href="https://github.com/AntonioAPDL/exdqlm/blob/main/src/exAL.cpp" target="_blank" rel="noopener noreferrer">
          <span>View C++ source</span>
          <i class="fas fa-external-link-alt" aria-hidden="true"></i>
        </a>
      </article>

      <article class="software-sample">
        <div class="software-sample__icon"><i class="fab fa-python" aria-hidden="true"></i></div>
        <h3>NOAA Forecast Builder</h3>
        <p>
          Dependency-light Python builder for Big Trees streamflow forecast JSON from NOAA NWPS APIs.
        </p>
        <a href="https://github.com/AntonioAPDL/antonio-aguirre.github.io/blob/main/scripts/build_big_trees_forecast_json.py" target="_blank" rel="noopener noreferrer">
          <span>View Python source</span>
          <i class="fas fa-external-link-alt" aria-hidden="true"></i>
        </a>
      </article>

      <article class="software-sample">
        <div class="software-sample__icon"><i class="fab fa-python" aria-hidden="true"></i></div>
        <h3>Climate Data Merge</h3>
        <p>
          Python workflow for joining precipitation, ERA5 soil moisture, and NWM retrospective soil series.
        </p>
        <a href="https://github.com/AntonioAPDL/antonio-aguirre.github.io/blob/main/scripts/build_climate_daily_combined_csv.py" target="_blank" rel="noopener noreferrer">
          <span>View Python source</span>
          <i class="fas fa-external-link-alt" aria-hidden="true"></i>
        </a>
      </article>

      <article class="software-sample">
        <div class="software-sample__icon"><i class="fas fa-vial" aria-hidden="true"></i></div>
        <h3>Site Integrity Checks</h3>
        <p>
          Lightweight validation for site data schemas, local references, generated assets, and conflict markers.
        </p>
        <a href="https://github.com/AntonioAPDL/antonio-aguirre.github.io/blob/main/scripts/check_site_integrity.py" target="_blank" rel="noopener noreferrer">
          <span>View Python source</span>
          <i class="fas fa-external-link-alt" aria-hidden="true"></i>
        </a>
      </article>
    </div>

    <div class="software-github-cta">
      <div>
        <h3>Explore More on GitHub</h3>
        <p>
          Public repositories include released packages, manuscript materials, website code, and research notes.
          GitHub activity is the best place to see current updates.
        </p>
      </div>
      <div class="software-github-cta__actions" aria-label="GitHub profile links">
        <a class="software-button" href="https://github.com/AntonioAPDL?tab=overview" target="_blank" rel="noopener noreferrer">
          <i class="fab fa-github" aria-hidden="true"></i>
          <span>GitHub Activity</span>
        </a>
        <a class="software-button software-button--secondary" href="https://github.com/AntonioAPDL?tab=repositories" target="_blank" rel="noopener noreferrer">
          <i class="fas fa-folder-open" aria-hidden="true"></i>
          <span>Repositories</span>
        </a>
      </div>
    </div>
  </section>

  <section class="software-note software-note--compact">
    <h2>Next Additions</h2>
    <p>
      Additional Python, MATLAB, Julia, and Q-DESN application code will be added when the examples have
      clear entry points, documentation, and setup that makes sense outside my local environment.
    </p>
  </section>
</div>
