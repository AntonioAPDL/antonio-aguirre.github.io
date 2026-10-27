# Blog 03: Checking quantile forecasts

Investigation and teaching plan, October 27, 2026.

## Evidence and scope

Read the scoring and rolling-evaluation sections of Q-DESN's announced version
https://arxiv.org/html/2609.17579v1 and the local main manuscript. Distinguish
oracle path recovery, realized-response scores, and posterior metric uncertainty.
Do not transfer numerical research results into a new simulation. Ground score
definitions in https://doi.org/10.1198/016214506000001437 and rearrangement in
https://doi.org/10.3982/ECTA7880. Read the existing Gaussian-energy-score and
Bayesian-workflow posts to avoid replacing their broader discussions.

## Teaching sequence

1. Specify origin, horizon, available information, and common verification rows.
2. Derive check loss and explain lower-is-better comparisons at fixed levels.
3. Simulate correct and biased Gaussian quantile forecasts at several horizons.
   These are oracle distributions, not fitted models or a forecast benchmark.
4. Inspect empirical quantile coverage and horizon-specific scores together.
5. Demonstrate crossing on an equally spaced quantile grid. Explain sorting as
   discrete rearrangement, not a substitute for joint posterior inference.
6. Relate a fixed finite-grid score to CRPS without calling a coarse score full
   CRPS. Verify a dense-grid approximation against the Gaussian formula.
7. Explain dependence, uncertainty in score differences, and untouched test data.

## Acceptance

Execute every R fence in order; independently check piecewise losses, score
dimensions, noncrossing after sorting, and numerical CRPS quadrature. Seed fixed
before comparison. Generate a two-panel, labeled figure. Run shared publication,
build, math, mobile, and dark-mode checks before publishing.

## Executed checks

All four R blocks passed under R 4.5.3. The correct distribution's empirical
fractions below its 0.1, 0.5, and 0.9 quantiles were 0.102500, 0.5064583,
and 0.9012500. Dense-grid CRPS and the Gaussian formula both rounded to
0.4215692 (absolute difference below 1e-4). Piecewise loss, dimensions,
finite scores, and rearrangement assertions passed.
