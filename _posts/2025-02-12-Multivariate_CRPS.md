---
layout: post
title: "The Energy Score for Multivariate Normal Distributions"
date: 2025-02-12
theme: Review
tags: [statistics, forecasting, probabilistic-models, scores]
excerpt: "Closed-form expressions and special cases for the multivariate generalization of CRPS"
---

## Introduction

The Energy Score serves as the multivariate extension of the Continuous Ranked Probability Score (CRPS), maintaining its desirable properties while handling vector-valued forecasts. This post presents the closed-form expression for multivariate normal distributions and its connection to classical CRPS results.

<div class="green-box">
<strong>Key Insight:</strong>  
<li>The Energy Score generalizes CRPS through expectations of pairwise distances, avoiding direct integration over multivariate CDFs</li>
<li>Special function relationships enable closed-form solutions for normal distributions</li>
</div>

## Energy Score Definition

For a $d$-dimensional forecast distribution $P$ and observation vector $\mathbf{y} \in \mathbb{R}^d$:

$$
\text{ES}(P, \mathbf{y}) = \mathbb{E}\left[\|\mathbf{X} - \mathbf{y}\|\right] - \frac{1}{2} \mathbb{E}\left[\|\mathbf{X} - \mathbf{X'}\|\right]
$$

where $\mathbf{X}, \mathbf{X'} \sim P$ are independent random vectors.

## Main Result: Multivariate Normal Case

For $P = \mathcal{N}_d(\boldsymbol{\mu}, \mathbf{\Sigma})$ and observation $\mathbf{y}$:

$$
\text{ES}(P, \mathbf{y}) = \sqrt{2\text{tr}(\mathbf{\Sigma})} \cdot \frac{\Gamma\left(\frac{d+1}{2}\right)}{\Gamma\left(\frac{d}{2}\right)} \left[ {}_1F_1\left(-\frac{1}{2}; \frac{d}{2}; -\frac{\delta^2}{2}\right) - 1 \right]
$$

**Components**:
- $\delta^2 = (\boldsymbol{\mu} - \mathbf{y})^\top \mathbf{\Sigma}^{-1} (\boldsymbol{\mu} - \mathbf{y})$ (Mahalanobis distance squared)
- ${}_1F_1$: Confluent hypergeometric function
- $\Gamma$: Gamma function

<div class="yellow-box">
<strong>Practical Note:</strong>  
<li>Requires special function implementations (e.g., scipy.special.hyp1f1)</li>
<li>Reduces to familiar CRPS when $d=1$</li>
</div>

## Special Cases

### Isotropic Covariance

When $\mathbf{\Sigma} = \sigma^2\mathbf{I}_d$:

$$
\text{ES}(P, \mathbf{y}) = \sqrt{2d}\sigma \cdot \frac{\Gamma\left(\frac{d+1}{2}\right)}{\Gamma\left(\frac{d}{2}\right)} \left[ {}_1F_1\left(-\frac{1}{2}; \frac{d}{2}; -\frac{\|\boldsymbol{\mu} - \mathbf{y}\|^2}{2\sigma^2}\right) - 1 \right]
$$

### Univariate Case (Classical CRPS)

For $P = \mathcal{N}(\mu, \sigma^2)$ and observation $y$:

$$
\text{CRPS}(P, y) = \sigma \left[ z(2\Phi(z) - 1) + \sqrt{\frac{2}{\pi}}(e^{-z^2/2} - 1) \right]
$$

where $z = \frac{y - \mu}{\sigma}$ and $\Phi$ is the standard normal CDF.

## Computational Approaches

| Component               | Implementation Strategy          |
|-------------------------|-----------------------------------|
| ${}_1F_1$ function      | scipy.special.hyp1f1              |
| Gamma functions         | Standard math libraries           |
| High-dimensional cases  | Monte Carlo sampling              |

<div class="green-box">
<strong>Implementation Tip:</strong>  
<li>For d > 3, consider Monte Carlo approximation:</li>
$$
\text{ES}(P, \mathbf{y}) \approx \frac{1}{N}\sum_{i=1}^N \|\mathbf{X}_i - \mathbf{y}\| - \frac{1}{2N^2}\sum_{i,j=1}^N \|\mathbf{X}_i - \mathbf{X}_j\|
$$
</div>

## Proof Sketch

### Key Steps

1. **Non-central Chi Distribution**: $\|\mathbf{X}-\mathbf{y}\|$ follows a non-central chi distribution
2. **Central Chi Moments**: $\mathbb{E}[\|\mathbf{X}-\mathbf{X'}\|]$ uses central chi properties
3. **Hypergeometric Connection**: Relate Bessel functions to ${}_1F_1$ through series expansions

### Technical Lemma

For $\mathbf{V} \sim \mathcal{N}_d(\boldsymbol{\nu}, \mathbf{\Omega})$:

$$
\mathbb{E}[\|\mathbf{V}\|] = \sqrt{2\text{tr}(\mathbf{\Omega})} \cdot \frac{\Gamma\left(\frac{d+1}{2}\right)}{\Gamma\left(\frac{d}{2}\right)} \cdot {}_1F_1\left(-\frac{1}{2}; \frac{d}{2}; -\frac{\boldsymbol{\nu}^\top \mathbf{\Omega}^{-1} \boldsymbol{\nu}}{2}\right)
$$

## Comments

The Energy Score's extension of CRPS to multivariate settings addresses a critical need in modern probabilistic forecasting. Where the univariate CRPS revolutionized verification of scalar forecasts [1], complex systems increasingly demand *joint calibration assessments* of vector-valued predictions - from weather models (temperature-pressure-wind vectors) to financial risk (correlated asset returns).

<div class="green-box">
<strong>Key Motivations:</strong>
<li><strong>Dependency Awareness:</strong> Unlike marginal CRPS averaging, the Energy Score's pairwise distance terms (𝔼‖𝐗−𝐗'‖) directly penalize misrepresented correlations [2]</li>
<li><strong>Properness Preservation:</strong> Maintains the CRPS' crucial property of being strictly proper - forecasters can't game the system by misrepresenting uncertainties [1]</li>
<li><strong>Consistency:</strong> Reduces exactly to CRPS when 𝑑=1, ensuring backward compatibility</li>
</div>

While computation requires special functions (${}_1F_1$, Γ) or Monte Carlo methods, this cost reflects the intrinsic complexity of multivariate dependence structures. As shown in [3], alternative scores like the variogram score make different tradeoffs, but the Energy Score remains uniquely tied to the CRPS legacy.

<div class="yellow-box">
<strong>Implementation Insight:</strong>  
<li>For high-𝑑 systems, the hypergeometric term ${}_1F_1(−1/2;𝑑/2;−𝛿^2/2)$ approaches $e^{−𝛿^2/(2𝑑)}$ - revealing a deep connection to Gaussian kernels in RKHS theory [2]</li>
</div>

As multivariate probabilistic AI/ML systems proliferate, the Energy Score provides a principled verification framework - one that honors the CRPS' philosophy while embracing the geometric complexity of high-dimensional spaces.

---

**References**  
1. [Gneiting, T., & Raftery, A. E. (2007). Strictly proper scoring rules, prediction, and estimation. *JASA*](https://doi.org/10.1198/016214506000001437)  
2. [Székely, G. J., & Rizzo, M. L. (2013). Energy statistics: A class of statistics based on distances. *JSPI*](https://doi.org/10.1016/j.jspi.2013.03.018)  
3. [Pinson, P., & Girard, R. (2012). Evaluating the quality of scenarios of short-term wind power generation. *Applied Energy*](https://doi.org/10.1016/j.apenergy.2012.05.010)
