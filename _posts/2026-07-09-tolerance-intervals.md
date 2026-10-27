---
layout: post
published: true
title: "What makes an interval a tolerance interval?"
date: 2026-07-09
updated: 2026-10-27
last_modified_at: 2026-10-27
theme: Interval inference
tags: [tolerance-intervals, uncertainty, order-statistics, r]
description: "Separate population content from repeated-sampling confidence, then construct a conservative shortest-window tolerance rule with order statistics."
excerpt: "Containing a requested fraction of the observed sample is not the same as containing that fraction of the population with a stated confidence."
math: true
---

Suppose we want an interval containing at least 90% of a population. If the population distribution were known, we could calculate such an interval directly. With only a sample, its true content is unknown. An interval containing 90% of the observed values can contain less than 90% of the population.

A tolerance interval adds a repeated-sampling requirement. For an interval procedure $$[L(D),U(D)]$$ based on a sample $$D$$ from a continuous distribution $$F$$, the statement is

$$
\Pr_{D\sim F^n}\left\{F\bigl(U(D)\bigr)-F\bigl(L(D)\bigr)\geq c\right\}\geq\gamma.
$$

The content $$c$$ and confidence $$\gamma$$ play different roles. With $$c=0.9$$ and $$\gamma=0.95$$, the procedure must contain at least 90% of the population in at least 95% of repeated samples under the stated assumptions. This is neither a confidence interval for a population mean nor a statement about one future observation.

## Check feasibility before shortening the interval

Assume independent, identically distributed observations from a continuous distribution. Among intervals whose endpoints lie within the observed sample range, none can have more population content than the range itself. For sample size $$n$$, its probability of containing at least content $$c$$ is

$$
1-c^{n-1}\{n-(n-1)c\}.
$$

```r
content <- 0.9
confidence <- 0.95
range_confidence <- function(n, c) 1 - c^(n - 1) * (n - (n - 1) * c)
print(range_confidence(30, content))
stopifnot(abs(range_confidence(30, content) -
  pbeta(content, 29, 2, lower.tail = FALSE)) < 1e-12)
```

With thirty observations, this probability is about 0.816, below the requested 0.95. Every shorter window within the sample range has no greater population content, so selecting one cannot satisfy the requested guarantee. This limitation applies to finite sample-contained windows; other constructions may extend beyond the data under additional assumptions.

## A fixed window has a simple content distribution

Sort the sample as $$Y_{(1)}<\cdots<Y_{(n)}$$. Consider a fixed indexed window $$[Y_{(i)},Y_{(i+d)}]$$. It contains $$d+1$$ observed points, while $$d$$ is the number of spacings between its endpoints. Under continuity, its unknown population content has a $$\operatorname{Beta}(d,n+1-d)$$ distribution. This follows by transforming the observations through their population CDF to uniform order statistics.

The Beta calculation applies to an index fixed independently of the observed values. Choosing the shortest of all candidate windows makes the index data-dependent. A guarantee for the selected interval must account for this selection; the tail probability for a preselected window alone is insufficient.

## Calibrate the selection rule too

For a spacing $$d$$, there are $$n-d$$ candidate windows. Each has probability $$B_c(d,n+1-d)$$ of containing less than content $$c$$, where $$B_c$$ is the Beta CDF evaluated at $$c$$. The union bound therefore gives

$$
\Pr(\text{every candidate has content at least }c)
\geq 1-(n-d)B_c(d,n+1-d).
$$

If every candidate succeeds, the shortest candidate succeeds. We can choose the smallest spacing whose lower bound reaches the requested confidence, then select the shortest window at that spacing. Calibration uses only sample size, content, and confidence, before observing the values.

```r
n <- 90L
spacing <- 1:(n - 1L)
bound <- pmax(0, 1 - (n - spacing) *
  pbeta(content, spacing, n + 1L - spacing))
eligible <- which(bound >= confidence)
if (!length(eligible)) stop("No eligible finite sample-window rule.")
d <- spacing[eligible[1L]]
shortest_window <- function(y, d) {
  z <- sort(y)
  i <- seq_len(length(z) - d)
  widths <- z[i + d] - z[i]
  selected <- i[which.min(widths)]
  c(lower = z[selected], upper = z[selected + d])
}
print(c(spacing = d, retained_points = d + 1L,
        confidence_lower_bound = bound[d]))
stopifnot(bound[d] >= confidence,
          all(bound[spacing < d] < confidence))
```

The construction is conservative because it bounds the event that any candidate fails, even when the selected candidate succeeds. It does not exploit dependence among overlapping windows. TCSP in my tolerance-interval paper uses scan-specific calibration. The union-bound example here has a separate calibration rule and should not be interpreted as an implementation of TCSP.

## Simulate the complete procedure

An exponential generating distribution allows the true content of every selected interval to be calculated from its CDF. The experiment repeats sampling and interval selection across 2,000 independent datasets. These results check the implementation under that distribution. The content-confidence guarantee follows from the analytic bound, not from the observed simulation success rate.

```r
set.seed(51027)
repetitions <- 2000L
result <- replicate(repetitions, {
  sample <- rexp(n)
  ab <- shortest_window(sample, d)
  z <- sort(sample)
  all_widths <- z[(d + 1L):n] - z[1:(n - d)]
  stopifnot(abs(diff(ab) - min(all_widths)) < 1e-12)
  c(content = pexp(ab[2]) - pexp(ab[1]), width = ab[2] - ab[1])
})
success <- mean(result[1, ] >= content)
mc_se <- sqrt(success * (1 - success) / repetitions)
print(c(success_fraction = success, Monte_Carlo_SE = mc_se))
stopifnot(all(is.finite(result)), all(result[1, ] >= 0),
          all(result[1, ] <= 1), all(result[2, ] > 0))
example_verified <- TRUE
```

Do not tune the spacing after seeing these results and then retain the original guarantee. Any more adaptive procedure needs an argument covering its actual selection rule. Similarly, the observed fraction retained in one sample is not an estimate of the repeated-sampling confidence in the displayed formula.

```r
figure_dir <- Sys.getenv("RESEARCH_BLOG_FIGURE_DIR", tempdir())
png(file.path(figure_dir, "tolerance-intervals.png"),
    width = 1400, height = 800, res = 150)
par(mfrow = c(1, 2), mar = c(4, 4, 2, 1))
show <- spacing >= 78
plot(spacing[show], bound[show], type = "b", pch = 16,
     col = "#176A94", ylim = c(0, 1),
     xlab = "Order-statistic spacing", ylab = "Confidence lower bound")
abline(h = confidence, lty = 2, col = "#9B7400")
abline(v = d, lty = 3, col = "#65737E")
hist(result[1, ], breaks = 25, col = "#25734A", border = "white",
     xlim = c(0.85, 1), main = "", xlab = "True selected-interval content",
     ylab = "Number of simulated samples")
abline(v = content, lty = 2, col = "#9B7400", lwd = 2)
dev.off()
```

<figure>
  <a href="{{ '/public/images/blog/tolerance-intervals.png' | relative_url }}"><img src="{{ '/public/images/blog/tolerance-intervals.png' | relative_url }}" alt="Conservative confidence bounds across order-statistic spacings and a histogram of true contents from 2000 simulated exponential samples." width="1400" height="800" loading="lazy"></a>
  <figcaption>At n = 90, the rule fixes its spacing before sampling. The left dashed line marks confidence 0.95; the right dashed line marks population content 0.9. These are different quantities on different axes.</figcaption>
</figure>

## Scope of the tolerance guarantee

The argument assumes iid continuous observations. Serial dependence, ties from discrete outcomes, regression-dependent populations, and changing distributions need additional treatment. Running the same code on a time series does not preserve the theorem. Nor does a posterior credible interval for estimated endpoints provide the frequentist content-confidence statement automatically.

The population target, its estimator or posterior, and calibration of the reported action are separate specifications. [Interval placement]({{ '/2026/03/18/same-content-different-intervals/' | relative_url }}) addresses the target; [endpoint regression]({{ '/2026/10/13/interval-endpoint-regression/' | relative_url }}) concerns estimation. A tolerance claim additionally requires a content-confidence argument covering the actual construction, its selection rule, and the assumptions on the observations.

## References

- Wilks, S. S. (1941). Determination of sample sizes for setting tolerance limits. [Annals of Mathematical Statistics](https://doi.org/10.1214/aoms/1177731788).
- De Leon, A., Prado, R., and Sanso, B. *Mean-Tilted Intervals: Short Tolerance Intervals*. [arXiv:2607.26098, version 3](https://arxiv.org/abs/2607.26098v3).
