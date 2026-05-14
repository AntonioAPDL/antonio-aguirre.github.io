---
layout: default
title: Software
description: "Public packages, research code, and selected implementation examples."
---

<div class="software-section">
  <header class="software-hero page-header">
    <p class="software-kicker">Research Software</p>
    <h1 class="page-title">Software</h1>
    <p class="page-lede">
      Public packages, research code, and selected implementation examples for Bayesian modeling,
      forecasting, and scientific computing.
    </p>
  </header>

  <section class="software-overview" aria-label="Software at a glance">
    <div class="software-overview-item">
      <i class="fas fa-cube" aria-hidden="true"></i>
      <h3>Released Package</h3>
      <p>CRAN-published R software with inspectable source and tests.</p>
    </div>
    <div class="software-overview-item">
      <i class="fas fa-water" aria-hidden="true"></i>
      <h3>Forecast Pipelines</h3>
      <p>Scripts for streamflow forecasts, climate data, and site outputs.</p>
    </div>
    <div class="software-overview-item">
      <i class="fas fa-microchip" aria-hidden="true"></i>
      <h3>Numerical Code</h3>
      <p>Rcpp/C++ kernels for distribution utilities and state-space computation.</p>
    </div>
    <div class="software-overview-item">
      <i class="fas fa-book-open" aria-hidden="true"></i>
      <h3>Research Notes</h3>
      <p>Public methods notes and manuscript-support materials.</p>
    </div>
  </section>

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

      <div class="software-feature__details">
        <div class="software-feature__status">
          <h3>Release &amp; Manuscript</h3>
          <p>
            <code>exdqlm</code> is available on CRAN. A companion article has been submitted to the
            <em>Journal of Statistical Software</em>, with examples maintained alongside package development.
          </p>
          <p class="software-updated">Last updated: May 14, 2026</p>
        </div>
        <ul class="software-feature__checks" aria-label="exdqlm capabilities">
          <li>
            <strong>Models</strong>
            <span>State-space quantile models with trend, seasonal, regression, and transfer-function components.</span>
          </li>
          <li>
            <strong>Inference</strong>
            <span>MCMC for posterior simulation and LDVB for scalable approximate inference.</span>
          </li>
          <li>
            <strong>Evaluation</strong>
            <span>Forecast summaries, calibration checks, scoring rules, and posterior predictive output.</span>
          </li>
        </ul>
      </div>
    </div>
  </article>

  <section class="software-samples" aria-label="Public projects and artifacts">
    <div class="software-samples__header">
      <p class="software-kicker">Repositories</p>
      <h2>Public Projects</h2>
      <p>
        Selected repositories and materials that are ready to inspect: article sources, site scripts,
        methods notes, and manuscript-support code.
      </p>
    </div>

    <div class="software-project-grid">
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
          <span>Manuscript support</span>
          <span>Python / TeX</span>
        </div>
        <h3>Forecast Correction Manuscript</h3>
        <p>
          Revised Environmetrics manuscript materials with generated asset manifests, figure/table reports,
          and validation scripts.
        </p>
        <a href="https://github.com/AntonioAPDL/Evironmetrics---REVISED-DOC-2" target="_blank" rel="noopener noreferrer">
          <span>Manuscript repository</span>
          <i class="fas fa-external-link-alt" aria-hidden="true"></i>
        </a>
      </article>

      <article class="software-project">
        <div class="software-project__meta">
          <span>Site scripts</span>
          <span>Python / R / Bash</span>
        </div>
        <h3>Forecast &amp; Climate Tools</h3>
        <p>
          Scripts behind this website's forecast and climate-data outputs, including NOAA NWPS requests,
          climate/soil-moisture joins, and repository checks.
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
          Public notes for Q-DESN notation, model structure, and implementation ideas behind current research code.
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
        Selected files that show how I structure package APIs, numerical code, data pipelines,
        manuscript checks, and site automation.
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
        <div class="software-sample__icon"><i class="fas fa-file-alt" aria-hidden="true"></i></div>
        <h3>Manuscript Figure Validator</h3>
        <p>
          Python check that resolves TeX figure paths and fails when manuscript assets are missing.
        </p>
        <a href="https://github.com/AntonioAPDL/Evironmetrics---REVISED-DOC-2/blob/main/scripts/validate_manuscript_figure_paths.py" target="_blank" rel="noopener noreferrer">
          <span>View Python source</span>
          <i class="fas fa-external-link-alt" aria-hidden="true"></i>
        </a>
      </article>
    </div>

    <div class="software-github-cta">
      <div>
        <h3>Explore More on GitHub</h3>
        <p>
          Browse current repositories, recent activity, and source files. More selected examples will be added
          when they have clear setup notes and reusable examples.
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
</div>
