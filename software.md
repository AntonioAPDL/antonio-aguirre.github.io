---
layout: default
title: Software
description: "Public packages, research code, and selected implementation examples for Bayesian quantile modeling and forecast evaluation."
---

{% assign exdqlm = site.data.cran_packages.exdqlm %}
{% assign outputs = site.data.research_outputs %}
{% assign exdqlm_version = exdqlm.version | default: "1.1.0" %}
{% assign exdqlm_published_label = exdqlm.published_label | default: "July 9, 2026" %}
{% assign exdqlm_article = outputs.exdqlm_article %}
{% assign exdqlm_arxiv_url = exdqlm_article.arxiv_url | default: exdqlm.arxiv_url %}
{% assign mti_tolerance = outputs.mti_tolerance %}
{% assign mti_regression = outputs.mti_regression %}
{% assign qdesn = outputs.qdesn %}
{% assign correction = outputs.forecast_correction %}

<div class="software-section">
  <header class="software-hero page-header">
    <p class="software-kicker">Research Software</p>
    <h1 class="page-title">Software</h1>
    <p class="page-lede">
      Selected software and reproducibility materials for Bayesian quantile modeling, forecast evaluation,
      posterior synthesis, and scientific computing.
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
        <span>CRAN {{ exdqlm_version }}</span>
        <span>JSS software article submitted</span>
      </div>
      <h2><code>exdqlm</code>: Extended Dynamic Quantile Linear Models</h2>
      <p>
        <code>exdqlm</code> implements dynamic extended quantile linear models and static extended-asymmetric-Laplace regression.
        The package provides MCMC and Laplace–delta variational Bayes (LDVB), model diagnostics, forecasting tools,
        optional C++ acceleration, and posterior synthesis across separately fitted quantiles.
      </p>
      <div class="software-actions" aria-label="exdqlm links">
        <a class="software-button" href="https://CRAN.R-project.org/package=exdqlm" target="_blank" rel="noopener noreferrer">
          <i class="fas fa-cube" aria-hidden="true"></i>
          <span>CRAN</span>
        </a>
        <a class="software-button software-button--secondary" href="{{ exdqlm_arxiv_url }}" target="_blank" rel="noopener noreferrer">
          <i class="far fa-file-alt" aria-hidden="true"></i>
          <span>arXiv</span>
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
            <code>exdqlm</code> {{ exdqlm_version }} is available on CRAN. The companion software article has been submitted to the
            <em>Journal of Statistical Software</em> and is available as an arXiv preprint; the article repository tracks the
            manuscript source, supplement, examples, and reproducibility checks.
          </p>
          <p class="software-updated">CRAN release: {{ exdqlm_published_label }}</p>
        </div>
        <ul class="software-feature__checks" aria-label="exdqlm capabilities">
          <li>
            <strong>Models</strong>
            <span>Dynamic exDQLMs plus static exAL regression, with trend, seasonal, regression, and transfer-function components.</span>
          </li>
          <li>
            <strong>Inference</strong>
            <span>Laplace–delta variational Bayes for approximate inference and MCMC for posterior simulation.</span>
          </li>
          <li>
            <strong>Diagnostics &amp; Synthesis</strong>
            <span>Forecast summaries, calibration checks, scoring rules, and posterior synthesis across fitted quantiles.</span>
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
        Selected public repositories supporting released software and current manuscripts. Each entry states its maturity and scope.
      </p>
    </div>

    <div class="software-project-grid">
      <article class="software-project">
        <div class="software-project__meta">
          <span>Submitted article</span>
          <span>R / TeX</span>
        </div>
        <h3><code>exdqlm</code> JSS Article</h3>
        <p>
          Article source for <em>{{ exdqlm_article.title }}</em>, with arXiv preprint materials,
          supplement files, reproducibility checks, and manuscript-support examples.
        </p>
        <a href="https://github.com/AntonioAPDL/exdqlm---Article" target="_blank" rel="noopener noreferrer">
          <span>Article repository</span>
          <i class="fas fa-external-link-alt" aria-hidden="true"></i>
        </a>
      </article>

      <article class="software-project">
        <div class="software-project__meta">
          <span>arXiv preprint</span>
          <span>R / TeX</span>
        </div>
        <h3>Forecast-Correction Article</h3>
        <p>
          Manuscript and reproducibility workspace for Bayesian quantile-based correction
          and synthesis of environmental forecast products.
        </p>
        <div class="software-project__links">
          <a href="https://github.com/AntonioAPDL/Evironmetrics---REVISED-DOC-Corrected-2" target="_blank" rel="noopener noreferrer">
            <span>Article repository</span>
            <i class="fas fa-external-link-alt" aria-hidden="true"></i>
          </a>
          <a href="{{ correction.arxiv_url }}" target="_blank" rel="noopener noreferrer">
            <span>arXiv preprint</span>
            <i class="fas fa-external-link-alt" aria-hidden="true"></i>
          </a>
        </div>
      </article>

      <article class="software-project">
        <div class="software-project__meta">
          <span>Working manuscript</span>
          <span>Q-DESN / TeX</span>
        </div>
        <h3>{{ qdesn.title }}</h3>
        <p>
          Source and reproducibility materials for Bayesian quantile forecasting with fixed nonlinear recurrent features,
          simulation studies, and empirical forecast comparisons.
        </p>
        <a href="{{ qdesn.repository_url }}" target="_blank" rel="noopener noreferrer">
          <span>Article repository</span>
          <i class="fas fa-external-link-alt" aria-hidden="true"></i>
        </a>
      </article>

      <article class="software-project">
        <div class="software-project__meta">
          <span>arXiv preprint / manuscript</span>
          <span>R / C++ / TeX</span>
        </div>
        <h3>Mean-Tilted Intervals</h3>
        <p>
          Manuscript and computation workspace for MTI fixed-content and tolerance intervals,
          with <em>{{ mti_regression.title }}</em> listed as a submitted manuscript.
        </p>
        <div class="software-project__links">
          <a href="{{ mti_tolerance.repository_url }}" target="_blank" rel="noopener noreferrer">
            <span>Project repository</span>
            <i class="fas fa-external-link-alt" aria-hidden="true"></i>
          </a>
          <a href="{{ mti_tolerance.arxiv_url }}" target="_blank" rel="noopener noreferrer">
            <span>arXiv preprint</span>
            <i class="fas fa-external-link-alt" aria-hidden="true"></i>
          </a>
        </div>
      </article>

    </div>
  </section>

  <section class="software-samples" aria-label="Selected implementation examples">
    <div class="software-samples__header">
      <p class="software-kicker">Code Samples</p>
      <h2>Selected Implementations</h2>
      <p>
        A short source tour for API design, numerical implementation, and posterior synthesis in <code>exdqlm</code>.
      </p>
    </div>

    <div class="software-sample-grid">
      <article class="software-sample">
        <div class="software-sample__icon"><i class="fab fa-r-project" aria-hidden="true"></i></div>
        <h3>LDVB Inference Interface</h3>
        <p>
          Main Laplace–delta variational Bayes interface for dynamic quantile state-space models, including convergence controls,
          diagnostics, and posterior predictive summaries.
        </p>
        <a href="https://github.com/AntonioAPDL/exdqlm/blob/main/R/exdqlmLDVB.R" target="_blank" rel="noopener noreferrer">
          <span>View R source</span>
          <i class="fas fa-external-link-alt" aria-hidden="true"></i>
        </a>
      </article>

      <article class="software-sample">
        <div class="software-sample__icon"><i class="fab fa-r-project" aria-hidden="true"></i></div>
        <h3>Static exAL Regression</h3>
        <p>
          Static Bayesian quantile-regression interface under the exAL likelihood, including LDVB controls
          and shrinkage-prior support.
        </p>
        <a href="https://github.com/AntonioAPDL/exdqlm/blob/main/R/exalStaticLDVB.R" target="_blank" rel="noopener noreferrer">
          <span>View R source</span>
          <i class="fas fa-external-link-alt" aria-hidden="true"></i>
        </a>
      </article>

      <article class="software-sample">
        <div class="software-sample__icon"><i class="fas fa-microchip" aria-hidden="true"></i></div>
        <h3>exAL Numerics</h3>
        <p>
          Rcpp/Boost implementation of extended asymmetric Laplace density, distribution, quantile, simulation,
          and parameter-bound utilities.
        </p>
        <a href="https://github.com/AntonioAPDL/exdqlm/blob/main/src/exAL.cpp" target="_blank" rel="noopener noreferrer">
          <span>View C++ source</span>
          <i class="fas fa-external-link-alt" aria-hidden="true"></i>
        </a>
      </article>

      <article class="software-sample">
        <div class="software-sample__icon"><i class="fab fa-r-project" aria-hidden="true"></i></div>
        <h3>Quantile Synthesis</h3>
        <p>
          Post hoc synthesis tools for combining separately fitted quantile models into coherent
          posterior predictive draws.
        </p>
        <a href="https://github.com/AntonioAPDL/exdqlm/blob/main/R/quantileSynthesis.R" target="_blank" rel="noopener noreferrer">
          <span>View R source</span>
          <i class="fas fa-external-link-alt" aria-hidden="true"></i>
        </a>
      </article>

    </div>

    <div class="software-github-cta">
      <div>
        <h3>Explore More on GitHub</h3>
        <p>
          Additional repositories and development history are available on GitHub. The items above are the projects
          most relevant to my current research and software work.
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
