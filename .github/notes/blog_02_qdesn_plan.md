# Blog 02: Fixed recurrent quantile features

Investigation and teaching plan, October 27, 2026.

## Evidence and decisions

Read the reservoir construction and evaluation sections of the local
`Article-Q-DESN---Version-2/main.tex` and the announced manuscript:
https://arxiv.org/html/2609.17579v1. The design fixes recurrent weights and
conditions readout inference on that representation. Forecast information sets
and calibration choices are part of the method, not incidental preprocessing.
The paper's comparisons are heterogeneous; do not turn them into a superiority
claim. The current public title, not an older README title, is authoritative.

Use quantreg's existing optimizer rather than invent an optimizer or reproduce
the research sampler in a short tutorial. Inspect `quantreg::rq.fit` and the
installed version (6.1). Reference https://CRAN.R-project.org/package=quantreg
and https://doi.org/10.2307/1913643 for the convex readout problem.

## Teaching sequence

1. Define the upper conditional quantile before discussing neural features.
2. Separate a deterministic recurrent representation from an estimated readout.
3. Simulate a nonlinear series; fix scaling with training data only.
4. Build a small, single-layer reservoir from lagged observations; hold weights
   fixed. Explain washout and why spectral-radius scaling is not a general
   echo-state-property proof.
5. Fit a quantile readout and a linear autoregressive baseline on identical rows.
6. Evaluate rolling one-step predictions, allowing only already observed lags.
7. Explain what Bayesian Q-DESN adds and what this example does not implement.

## Acceptance

Execute the article's R fences directly. Check dimensions, finite predictions,
training-only scaling, spectral radius, and invariance of earlier features to
perturbed future observations. Check loss against an independent piecewise
definition. Generate a labeled simulated-data figure with an explicit cutoff.
Record actual results after execution; do not select a seed for model victory.
Run publication/static tests and final shared Jekyll/browser checks. Preserve
unrelated data changes and use the real publication date.

## Executed checks

R 4.5.3 / quantreg 6.1: four published R blocks passed. Mean held-out check
loss was 0.1273208 for recurrent features and 0.1343470 for the linear baseline.
This is one simulated series, not evidence of general superiority. Temporal
invariance, spectral radius, finite dimensions, and independent loss checks
passed. Figure generated directly from these blocks.
