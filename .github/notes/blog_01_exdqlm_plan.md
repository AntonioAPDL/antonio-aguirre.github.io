# Blog 01: Dynamic quantile modeling with exdqlm

Investigation and implementation plan, October 27, 2026.

## Sources and scope

- Public package: CRAN exdqlm 1.1.2, published September 16, 2026.
  https://CRAN.R-project.org/package=exdqlm
- Released source: https://cran.r-project.org/src/contrib/exdqlm_1.1.2.tar.gz
- Software article: https://arxiv.org/abs/2607.22760
- Model foundations: https://doi.org/10.1214/21-AOAS1497
- Quantile regression: https://doi.org/10.2307/1913643
- Forecast scoring: https://doi.org/10.1198/016214506000001437

The default local R installation contains exdqlm 0.4.0, and sibling package
checkouts contain development changes. Neither is the execution authority for
this post. Install the official CRAN source in a temporary library and run the
reader's example against that version. Preserve existing libraries and research
worktrees. The online HTML manual can lag the source release; inspect the
released R code and documentation when an interface is ambiguous.

## Reader and learning objectives

Audience: readers comfortable with basic R and regression, without assuming
state-space or exAL expertise. The article should let a reader:

1. Identify a conditional quantile and distinguish it from a mean forecast.
2. Translate a local linear trend into level and slope states.
3. Fit a reproducible, deliberately restricted AL/DQLM example with LDVB.
4. Distinguish smoothed historical estimates from genuine held-out forecasts.
5. Inspect stopping diagnostics without treating convergence as validation.
6. Compare target-quantile check loss and describe finite-sample limitations.

Use a small simulated series with known Gaussian observation noise and an
explicitly known conditional quantile. Fit the AL special case via
`dqlm.ind = TRUE`, explaining its working-likelihood misspecification. Estimate
scale rather than silently fixing it to the simulation standard deviation.
Do not imply that this restricted example demonstrates the full exAL model.

## Pedagogical sequence

1. Start with the forecasting question and a one-sentence quantile definition.
2. Generate the series; reserve the last block before specifying/fitting models.
3. Introduce level and slope, their matrices, and the discount factor. Set
   initialization and any baseline using training observations only.
4. Fit once, inspect convergence status and trace, then forecast from the end of
   the training data. Do not fit the complete series and forecast from an earlier
   index: estimated global parameters would then use held-out observations.
5. Plot observations, the known simulation target, smoothed historical estimates,
   and forecast quantile means. Mark the origin and distinguish quantities by
   labels and line styles. Do not label quantile-state uncertainty as a response
   prediction interval.
6. Compute check loss with a transparent implementation and cross-check it
   against the package's forecast diagnostics. Compare with a prespecified recent
   training-window quantile. Show the result even if the baseline wins.
7. Explain empirical exceedance fractions, horizon dependence, single-origin
   limitations, likelihood misspecification, and approximation uncertainty.
8. Link the article, package, and primary statistical references without turning
   the note into a release announcement or a manuscript abstract.

## Style and integration

Follow the existing standalone notes: sentence-case title, short opening,
descriptive H2 sections, restrained mathematics, executable R fences, figure
captions, and a References section. Use the existing post layout and palette.
Use concrete explanations, avoid promotional claims, and remove editorial or
internal workflow language from the public article. Publish this first article
with its actual publication date, October 27, 2026; no earlier draft date has
been established. Do not assign a new `series` value: the current index only
renders the Bayesian workflow series and standalone posts.

The quality gate currently rejects any count other than nine posts. Change it
to enforce a minimum while keeping the six existing series entries intact. Add
regression tests showing that nine and ten posts pass, an undersized collection
fails, and existing duplicate-title checks remain active.

## Reproducibility and acceptance

- Keep one executable source of the tutorial's calculations in its R fences.
  A small runner extracts those fences in order, executes them in a temporary
  directory, verifies fit/forecast dimensions and score agreement, and writes
  figures only when an explicit output directory is supplied.
- Record the package/R versions and seed choices. Run the example twice and
  compare numerical outputs; independently verify the check-loss calculation.
- Generate the public PNG from the executed example; retain descriptive alt
  text and a caption stating that the data are simulated.
- Run publication, fenced-code, and site-integrity checks. Confirm the new post
  appears on the index and feed and has correct mathematics and one H1.
- Inspect desktop/mobile rendering in light and dark modes, including the figure,
  tables, code, and any horizontal overflow. Use the pinned production build in
  CI and verify the live page after deployment.
- Stage only this post, its figure, narrowly required tooling/tests, and this
  plan. Preserve unrelated climate/data changes. Commit and push after checks.

Subsequent Q-DESN and MTI posts need their own investigation and teaching plan;
they are outside this first implementation.

## Executed reference checks

The CRAN source tarball SHA-256 was
`de2de1021b0160ff13ce8ec3aa09fec47274d95f9737da125a718ffc313a49b9`.
It was installed in a temporary library without replacing the user's 0.4.0
installation. R 4.5.3 with exdqlm 1.1.2 executed all six article R blocks twice.
Both runs converged in 31 iterations and reproduced these results:

| Quantity | Reference result |
| --- | ---: |
| Dynamic forecast mean check loss | 0.3955137 |
| Recent-window baseline mean check loss | 0.6600739 |
| Held-out observations below dynamic forecast | 10 of 20 |
| Forecast response-draw dimensions | 20 x 1000 |

The independent piecewise check-loss calculation agrees with the package's
forecast diagnostic. Both runs generated byte-identical PNG figures (SHA-256
`2997469a855a340bd200e771ce5b36cd1dcab309afb92757f17eb52589a5007b`).

The publication gate also needed to ignore fenced code before detecting body
H1 headings: a valid R comment otherwise looked like a duplicate heading. Tests
cover both that case and rejection of an actual body H1.

The preview build uses Ruby 3.3.4, Bundler 2.5.23, and the locked Jekyll 3.10.0
dependencies. Browser checks at 1440 px and 390 px in both themes verify one H1,
six R blocks, rendered mathematics without MathJax errors, a loaded figure,
index visibility, and no page-wide horizontal overflow. Equal publication and
revision dates are shown once in the visible post/index, while modification
metadata remains present. The preview feed includes the new entry.
