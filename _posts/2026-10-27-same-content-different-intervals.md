---
layout: post
published: true
title: "Intervals with the same coverage can look very different"
date: 2026-10-27
updated: 2026-10-27
theme: Interval targets
tags: [intervals, uncertainty, mean-tilted-intervals, r]
description: "Compare shortest, equal-tailed, and mean-preserving intervals under a known skewed distribution, and see why content alone does not determine placement."
excerpt: "An interval containing 80% of a distribution need not be central, shortest, or balanced around the mean. Those are different statistical targets."
math: true
---

An interval is often introduced by saying how much of a distribution it contains. That leaves an important question unanswered: **which part of the distribution should it contain?** Many intervals can have the same probability content and different locations, widths, and tail allocations.

For a symmetric unimodal distribution, familiar choices can coincide. A skewed distribution exposes the distinction. This note uses an exponential distribution, where every calculation can be checked directly, to compare three targets: the shortest interval, the equal-tailed interval, and the mean-preserving interval. These are population quantities. No data have yet been sampled, so there is no endpoint-estimation uncertainty or tolerance confidence to discuss.

## Describe the whole content class

Let $$Y$$ have an exponential distribution with rate one. Its mean is one, and its distribution function on the nonnegative half-line is $$F(y)=1-e^{-y}$$. An interval with probability content $$c=0.8$$ contains 80% of this population.

Write the probability below its lower endpoint as $$s$$. Then the endpoints are $$F^{-1}(s)$$ and $$F^{-1}(s+c)$$. For this distribution, finite windows correspond to $$0\leq s<1-c$$. Moving $$s$$ changes placement while keeping content fixed. It does not change the distribution or the requested content.

```r
content <- 0.8
population_mean <- 1
endpoints <- function(s) qexp(c(s, s + content))
retained_mean <- function(s) {
  ab <- endpoints(s)
  ((ab[1] + 1) * exp(-ab[1]) -
     (ab[2] + 1) * exp(-ab[2])) / content
}
s_equal <- (1 - content) / 2
s_mpi <- uniroot(function(s) retained_mean(s) - population_mean,
                 c(0, 1 - content - 1e-8), tol = 1e-12)$root
tail_mass <- c(shortest = 0, equal_tailed = s_equal, mean_preserving = s_mpi)
intervals <- t(vapply(tail_mass, endpoints, numeric(2)))
colnames(intervals) <- c("lower", "upper")
summary <- data.frame(intervals,
  width = intervals[, 2] - intervals[, 1],
  retained_mean = vapply(tail_mass, retained_mean, numeric(1)))
summary$tilt <- summary$retained_mean - population_mean
print(round(summary, 4))
```

The shortest interval starts at zero because the density decreases throughout its support: moving a fixed-content window to the right makes it wider. The equal-tailed interval instead leaves 10% in each tail. That symmetry is in probability, not in distances from the mean or in the density heights at the endpoints.

The mean-preserving interval chooses a third placement. The average value among the observations retained inside it equals the population mean. It excludes some of the high-density region near zero and extends farther into the upper tail than the shortest window. None of these statements makes one target universally preferable. The choice depends on what the interval is supposed to summarize.

## Compute the retained mean

For endpoints $$a<b$$ with content $$c$$, integration gives

$$
\mathbb{E}(Y\mid a<Y<b)
=\frac{(a+1)e^{-a}-(b+1)e^{-b}}{c}.
$$

This expression makes the comparison more informative than just listing widths. The shortest window has a retained mean below the population mean because it omits the upper tail. Equal tails do not restore mean balance under skewness. Solving the retained-mean equation determines the mean-preserving member in this example.

```r
actual_content <- pexp(intervals[, 2]) - pexp(intervals[, 1])
numerical_means <- vapply(seq_len(nrow(intervals)), function(i) {
  integrate(function(y) y * dexp(y), intervals[i, 1], intervals[i, 2])$value /
    content
}, numeric(1))
stopifnot(max(abs(actual_content - content)) < 1e-12,
          abs(retained_mean(s_mpi) - 1) < 1e-9,
          max(abs(numerical_means - summary$retained_mean)) < 1e-9,
          all(summary$width > 0),
          summary$width[1] < summary$width[2])
example_verified <- TRUE
```

The numerical integral is an independent check of the analytic expression. It is not an estimate from a sample. In particular, the exact 80% content in these calculations is available because the generating distribution is known.

## What the mean tilt specifies

Mean-tilted intervals keep the content target and specify an offset in retained mean:

$$
\Pr(a<Y<b)=c,\qquad
\mathbb{E}(Y\mid a<Y<b)=\mu+\delta.
$$

Here $$\mu$$ is the full population mean and $$\delta$$ is the tilt. Zero tilt gives the mean-preserving interval. Other admissible tilts identify different placements. The units of the tilt are the units of the response, which helps distinguish it from the dimensionless probability content.

The residual-product loss introduced by Pouplin and colleagues identifies the zero-tilt target under appropriate conditions. The MTI formulation changes the retained-mean balance while preserving the content equation at regular unrestricted interior solutions. A tilt is therefore part of the target specification. Estimating it freely as though it were an ordinary nuisance parameter would combine different questions.

For the exponential example, the shortest member touches the boundary of the support. It should not be justified by interior stationary equations that assume two interior endpoints. Boundary cases require their own treatment, or qualified limiting arguments. More generally, gaps in support, nonunique minimizers, missing moments, or a restrictive regression family can prevent the simple unrestricted characterization from applying.

```r
figure_dir <- Sys.getenv("RESEARCH_BLOG_FIGURE_DIR", tempdir())
png(file.path(figure_dir, "same-content-different-intervals.png"),
    width = 1400, height = 800, res = 150)
par(mfrow = c(1, 3), mar = c(4, 4.6, 3, 0.8))
titles <- c("Shortest", "Equal-tailed", "Mean-preserving")
colors <- c("#9B7400", "#176A94", "#25734A")
x <- seq(0, 5, length.out = 1000)
for (i in 1:3) {
  plot(x, dexp(x), type = "l", xlim = c(0, 5), ylim = c(0, 1),
       xlab = "Response", ylab = "Density", main = titles[i], cex.main = 1)
  xx <- seq(intervals[i, 1], intervals[i, 2], length.out = 300)
  polygon(c(xx[1], xx, tail(xx, 1)), c(0, dexp(xx), 0),
          col = adjustcolor(colors[i], alpha.f = 0.3), border = NA)
  lines(x, dexp(x), col = colors[i], lwd = 2)
  abline(v = population_mean, lty = 3, col = "#65737E")
  segments(intervals[i, 1], 0, intervals[i, 2], 0, lwd = 4, col = colors[i])
}
dev.off()
```

<figure>
  <a href="{{ '/public/images/blog/same-content-different-intervals.png' | relative_url }}"><img src="{{ '/public/images/blog/same-content-different-intervals.png' | relative_url }}" alt="Three exponential density panels shading shortest, equal-tailed, and mean-preserving intervals, each containing 80 percent of the distribution." width="1400" height="800" loading="lazy"></a>
  <figcaption>All shaded regions have population content 0.8. The vertical dotted line is the population mean, not the retained mean of each shaded region. Identical axes make the placement differences visible.</figcaption>
</figure>

## Keep the target separate from its uncertainty

If the distribution were unknown, we would need to estimate the chosen interval from data. That introduces a new question: how variable are its endpoints? A posterior distribution or a sampling calculation can address endpoint uncertainty, but that uncertainty should not be confused with the probability mass between the endpoints.

A tolerance interval asks something stronger and different: how often will the interval-construction procedure contain at least the requested population fraction over repeated samples? Neither a fitted 80% interval nor an endpoint credible band supplies that statement automatically. [The next note]({{ '/2026/10/27/tolerance-intervals/' | relative_url }}) makes the extra requirement explicit.

Before comparing interval procedures, name the target. Equal-tailed, shortest, and mean-preserving intervals answer different placement questions even when their content agrees. An evaluation that rewards one placement should not silently be presented as a neutral test of all the others.

## References

- Pouplin, T., Jeffares, A., Seedat, N., and van der Schaar, M. (2024). Relaxed quantile regression: prediction intervals for asymmetric noise. [ICML / PMLR](https://proceedings.mlr.press/v235/pouplin24a.html).
- De Leon, A., Prado, R., and Sanso, B. *Mean-Tilted Intervals: Short Tolerance Intervals*. [arXiv:2607.26098, version 3](https://arxiv.org/abs/2607.26098v3).
- De Leon, A., Prado, R., and Sanso, B. *Mean-Tilted Intervals: Regression and Dynamic Models*. [arXiv:2610.13960, version 1](https://arxiv.org/abs/2610.13960v1).
