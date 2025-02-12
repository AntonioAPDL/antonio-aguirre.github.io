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
\text{ES}(P, \mathbf{y}) = \sqrt{2\text{tr}(\mathbf{\Sigma}) \cdot \frac{\Gamma\left(\frac{d+1}{2}\right)}{\Gamma\left(\frac{d}{2}\right)} \left[ {}_1F_1\left(-\frac{1}{2}; \frac{d}{2}; -\frac{\delta^2}{2}\right) - 1 \right]
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

## Conclusion

The Energy Score provides a theoretically sound generalization of CRPS for multivariate normals, maintaining proper scoring rule properties while requiring careful handling of special functions. The univariate limit confirms consistency with classical results, validating its use in probabilistic forecasting.

**References**:  
1. Gneiting & Raftery (2007) - Strictly Proper Scoring Rules  
2. Székely & Rizzo (2013) - Energy Statistics
