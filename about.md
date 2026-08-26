---
layout: default
title: About
description: "Background, research focus, teaching, service, and applied experience of Antonio De Leon."
---

{% assign exdqlm = site.data.cran_packages.exdqlm %}
{% assign outputs = site.data.research_outputs %}
{% assign exdqlm_version = exdqlm.version | default: "1.1.0" %}
{% assign exdqlm_article = outputs.exdqlm_article %}
{% assign exdqlm_arxiv_url = exdqlm_article.arxiv_url | default: exdqlm.arxiv_url %}
{% assign rqr = outputs.rqr %}
{% assign qdesn = outputs.qdesn %}
{% assign correction = outputs.forecast_correction %}

<div class="about-section">
  <!-- Introduction Section -->
  <div class="intro-section about-card">
    <img src="/files/images/Me.jpg" alt="Antonio De Leon" class="profile-pic">
    <h1 class="page-title">Antonio De Leon</h1>
    <p class="page-lede">
      I am a Ph.D. candidate in <strong>Statistics</strong> at the
      <a href="https://engineering.ucsc.edu/departments/statistics/" target="_blank" rel="noopener noreferrer">University of California, Santa Cruz</a>,
      advised by <a href="https://users.soe.ucsc.edu/~bruno/" target="_blank" rel="noopener noreferrer">Bruno Sansó</a> and
      <a href="https://raquel.soe.ucsc.edu/" target="_blank" rel="noopener noreferrer">Raquel Prado</a>.
      I work on Bayesian forecasting, quantile methods, and statistical software, with emphasis on uncertainty
      quantification, approximate and simulation-based inference, and reproducible R/Python workflows.
      Current projects include forecast correction for environmental products used in risk assessment, dynamic quantile
      state-space models, {{ qdesn.title }}, and generalized-Bayes interval methods.
    </p>
  </div>

  <!-- Applied and Professional Experience -->
  <div class="service-section about-card">
    <h2 class="section-heading">Applied and Professional Experience</h2>
    <ul class="about-list">
      <li>
        <strong>Computer Systems Coordinator, UCSC Statistics:</strong> Administer Linux research servers and build automation for research workflows (2024–present).
      </li>
      <li>
        <strong>Quantitative Researcher, Delos Financial Technologies:</strong> Built evaluation workflows, automated backtests on AWS, and standardized model diagnostics (2025).
      </li>
      <li>
        <strong>Data Analyst, NeatLeaf Inc.:</strong> Developed data pipelines and spatiotemporal models for greenhouse telemetry and anomaly detection (2021–2022).
      </li>
      <li>
        <strong>Data Analyst, Banco de México:</strong> Built pipelines for image datasets, anomaly classification models, and forecasting prototypes (2018–2019).
      </li>
    </ul>
  </div>

  <!-- Current Work Section -->
  <div class="highlights-section about-card">
    <h2 class="section-heading">Current Work</h2>
    <ul class="about-list about-highlight-list">
      <li>
        <strong><a href="https://CRAN.R-project.org/package=exdqlm" target="_blank" rel="noopener noreferrer"><code>exdqlm</code></a>:</strong>
        CRAN v{{ exdqlm_version }} R package for Bayesian quantile modeling, with a companion
        <a href="{{ exdqlm_arxiv_url }}" target="_blank" rel="noopener noreferrer">arXiv:{{ exdqlm_article.arxiv_id }}</a> and a manuscript submitted to
        <em>Journal of Statistical Software</em>.
      </li>
      <li>
        <strong>Forecast correction preprint:</strong>
        <a href="{{ correction.arxiv_url }}" target="_blank" rel="noopener noreferrer">Bayesian quantile-based correction and synthesis</a>
        of environmental forecast products for risk assessment; manuscript submitted to <em>Environmetrics</em>.
      </li>
      <li>
        <strong>Q-DESN forecasting:</strong>
        Working paper on Bayesian quantile forecasting with fixed nonlinear recurrent features.
      </li>
      <li>
        <strong>RQR preprint:</strong>
        <a href="{{ rqr.arxiv_url }}" target="_blank" rel="noopener noreferrer">{{ rqr.title }}</a>.
      </li>
    </ul>
  </div>

  <!-- Teaching and Service Section -->
  <div class="service-section about-card">
    <h2 class="section-heading">Teaching and Mentoring</h2>
    <ul class="about-list">
      <li>
        <strong>Graduate Student Instructor:</strong> Data Visualization (STAT 80B), Spring 2025.
      </li>
      <li>
        <strong>Teaching Assistant:</strong> Supported Probability Theory, Classical and Bayesian Inference, Statistics, and related courses (2021–present).
      </li>
      <li>
        <strong>UCSC Statistics TA Resources:</strong> Co-maintain the
        <a href="https://github.com/UCSC-Statistics/TA-resources/wiki" target="_blank" rel="noopener noreferrer">department TA wiki</a>,
        a public guide for TA responsibilities, teaching practices, and course support.
      </li>
      <li>
        <strong>ASA DataFest Mentor:</strong> Guided student teams on modeling and communication (2023).
      </li>
    </ul>
  </div>

  <!-- Education Section -->
  <div class="education-section about-card">
    <h2 class="section-heading">Education</h2>
    <ul class="about-list about-list-disc">
      <li>
        <strong>Ph.D. in Statistics:</strong>
        <a href="https://engineering.ucsc.edu/departments/statistics/" target="_blank" rel="noopener noreferrer">University of California, Santa Cruz</a> (2021–present, expected 2026)
      </li>
      <li>
        <strong>M.Sc. in Economic Theory:</strong>
        <a href="https://mteoriaeconomica.itam.mx/en/conoce-el-posgrado-teoriaeconomica" target="_blank" rel="noopener noreferrer">Instituto Tecnológico Autónomo de México (ITAM)</a> (2018–2020)
      </li>
      <li>
        <strong>B.Sc. in Applied Mathematics:</strong>
        <a href="https://departamentodematematicas.itam.mx/" target="_blank" rel="noopener noreferrer">Instituto Tecnológico Autónomo de México (ITAM)</a> (2014–2018)
      </li>
    </ul>
  </div>

  <!-- Beyond Research Section -->
  <div class="beyond-research-section about-card">
    <h2 class="section-heading">Beyond Research</h2>
    <p class="intro-text">
      Outside work, I enjoy baking bread, cooking Mexican food, reading history and philosophy of science, and studying German.
    </p>
    <p class="intro-text">
      For collaboration, questions, or related work, the <a href="/contact/">Contact page</a> lists the best ways to reach me.
    </p>
  </div>
</div>
