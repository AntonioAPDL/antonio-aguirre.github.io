---
layout: default
title: Research
description: "Research on Bayesian forecasting, quantile modeling, environmental risk applications, interval estimation, and statistical software."
---

{% assign exdqlm = site.data.cran_packages.exdqlm %}
{% assign outputs = site.data.research_outputs %}
{% assign exdqlm_version = exdqlm.version | default: "1.1.0" %}
{% assign exdqlm_article = outputs.exdqlm_article %}
{% assign exdqlm_arxiv_url = exdqlm_article.arxiv_url | default: exdqlm.arxiv_url %}
{% assign mti_tolerance = outputs.mti_tolerance %}
{% assign mti_regression = outputs.mti_regression %}
{% assign qdesn = outputs.qdesn %}
{% assign correction = outputs.forecast_correction %}
{% assign oecd = outputs.oecd_capital %}

<div class="research-section">
  <!-- Title and Introduction -->
  <header class="research-hero page-header">
    <h1 class="page-title">Research</h1>
    <p class="page-lede">
      I develop Bayesian methods for forecasting, uncertainty quantification, and interval estimation in dynamic data.
    </p>
    <p class="page-lede">
      Current projects use climate, environmental, and energy data to study forecast correction, posterior synthesis,
      temporal evaluation, and reproducible statistical software.
    </p>
  </header>

  <section class="research-area-grid" aria-label="Research areas">
    <article class="research-area">
      <span>arXiv preprint</span>
      <h2>Forecast Correction for Environmental Risk</h2>
      <p>
        Bayesian quantile methods for aligning observations, retrospective products, and forecast products from
        different systems, with evaluation tied to the information available at each forecast origin.
      </p>
    </article>
    <article class="research-area">
      <span>CRAN / JSS submission</span>
      <h2>Dynamic Quantile State-Space Models</h2>
      <p>
        Extended dynamic quantile linear models with MCMC, Laplace-delta variational Bayes,
        diagnostics, forecasting, and posterior predictive synthesis.
      </p>
    </article>
    <article class="research-area">
      <span>Working paper</span>
      <h2>{{ qdesn.title }}</h2>
      <p>
        Bayesian quantile forecasting with fixed nonlinear recurrent features, shrinkage priors,
        simulation studies, multi-quantile reporting, and held-out forecast comparisons.
      </p>
    </article>
    <article class="research-area">
      <span>arXiv preprint / submitted manuscript</span>
      <h2>Mean-Tilted Intervals</h2>
      <p>
        MTI work separates fixed-content and tolerance-interval targets from regression and
        dynamic-model extensions, with generalized-Bayes computation as the common thread.
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
        quantile workflow for correcting forecast products and synthesizing corrected quantile forecasts
        into a posterior predictive distribution. The case study uses local environmental observations and
        NOAA/NWS forecast guidance near Big Trees.
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
        <a class="software-button software-button--secondary" href="{{ correction.arxiv_url }}" target="_blank" rel="noopener noreferrer">
          <i class="far fa-file-alt" aria-hidden="true"></i>
          <span>Open Preprint</span>
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
          <em>{{ exdqlm_article.title }}</em>.
          Manuscript submitted to the <em>Journal of Statistical Software</em>; package on
          <a href="https://CRAN.R-project.org/package=exdqlm" target="_blank" rel="noopener noreferrer">CRAN</a>;
          <a href="{{ exdqlm_arxiv_url }}" target="_blank" rel="noopener noreferrer">arXiv:{{ exdqlm_article.arxiv_id }}</a>.
        </div>
      </li>
      <li class="research-output-item">
        <span class="research-output__status">arXiv / Environmetrics</span>
        <div>
          De Leon, A., Prado, R., Sansó, B.
          <em>{{ correction.title }}</em>.
          arXiv preprint; manuscript submitted to <em>Environmetrics</em>. Related work received the EnviBayes Student Paper
          Competition award and the ISBA 2026 Best Poster Prize.
          <a href="{{ correction.arxiv_url }}" target="_blank" rel="noopener noreferrer">arXiv:{{ correction.arxiv_id }}</a>.
          <a href="/files/posters/isba-2026-poster-aguirre.pdf" target="_blank" rel="noopener noreferrer">Poster PDF</a>.
        </div>
      </li>
      <li class="research-output-item">
        <span class="research-output__status">Working paper</span>
        <div>
          De Leon, A., Prado, R., Sansó, B.
          <em>{{ qdesn.title }}</em>.
          Working paper on Bayesian quantile forecasting with fixed nonlinear recurrent features, simulation studies,
          and selected empirical applications.
        </div>
      </li>
      <li class="research-output-item">
        <span class="research-output__status">arXiv preprint</span>
        <div>
          De Leon, A., Prado, R., Sansó, B.
          <em>{{ mti_tolerance.title }}</em>.
          Preprint on fixed-content interval targets, tolerance actions, and generalized-Bayes computation.
          <a href="{{ mti_tolerance.arxiv_url }}" target="_blank" rel="noopener noreferrer">arXiv:{{ mti_tolerance.arxiv_id }}</a>.
        </div>
      </li>
      <li class="research-output-item">
        <span class="research-output__status">{{ mti_regression.status_label }}</span>
        <div>
          De Leon, A., Prado, R., Sansó, B.
          <em>{{ mti_regression.title }}</em>.
          Manuscript on MTI regression and dynamic state-space extensions; public identifier pending.
        </div>
      </li>
      <li class="research-output-item">
        <span class="research-output__status">Published</span>
        <div>
          De Leon, A., Lobato, I. N. (2024).
          <em>{{ oecd.title }}</em>.
          <em>Empirical Economics</em>.
          <a href="{{ oecd.doi_url }}" target="_blank" rel="noopener noreferrer">DOI</a>.
        </div>
      </li>
    </ul>
  </div>

  <div class="research-software-note">
    <h2>Code and Reproducibility</h2>
    <p>
      Package source, manuscript repositories, and selected implementation examples are listed on the
      <a href="/software/">Software page</a>. Each item is labeled by release or manuscript status.
    </p>
  </div>
</div>
