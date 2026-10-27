# Research blog collection: validation record

October 27, 2026. Five standalone articles follow the first exdqlm tutorial.
All use the actual publication date, not invented historical dates. Each has
its own source investigation and teaching plan in notes 02--06.

## Reproducibility

`Rscript --vanilla scripts/run_research_blog_examples.R` executes the nineteen
R fences directly, with a separate environment for each article. Reference
environment: R 4.5.3, quantreg 6.1. Four articles use base R only. No private
data, manuscript checkout, or research package is required to reproduce them.
All five have been run individually to generate their figures, then together
without a public output directory to verify the normal read-only usage.

Checks include causal feature construction, training-only scaling, independent
check-loss calculations, dense-grid versus analytic CRPS, analytic versus
integrated retained means, fixed-window versus selected-window distinctions,
order-statistic range feasibility, exhaustive width comparisons, stable finite
posterior normalization, root-label invariance, and endpoint ordering.

The scoped GitHub workflow fixes R and records the CRAN quantreg version. Its
reference assertions intentionally surface changes after dependency updates;
review numerical drift rather than silently refreshing expected results.

## Local acceptance results

- All nineteen executable R fences and their embedded assertions passed.
- Publication quality gate: 15 posts, original six-part workflow intact.
- Static fenced-code checks: 10 Bash, 29 R, and 1 text block passed.
- Python regression suite: 12 tests passed.
- Site integrity passed; existing provider-limited NWM soil staleness warnings
  are unrelated to the articles and were not modified.
- Production Jekyll build passed using Ruby 3.3.4, Bundler 2.5.23, and locked
  dependencies in a temporary container. Source mounted read-only.
- Chromium/Playwright: five articles at 1440px and 390px, light and dark modes,
  all twenty combinations passed. Checked one H1, rendered math without errors,
  expected R block counts, no page-wide overflow, loaded figures, all local
  article links and image links, and no JavaScript page errors.
- Blog index retained six workflow entries and displayed nine standalone notes,
  including all five new articles. Same-day dates do not repeat as Updated dates.
- All five original PNGs visually inspected. Fixed a clipped first-panel axis
  label in the interval-placement figure and regenerated from the article.
- A second complete figure run in a separate temporary directory reproduced
  all five published PNGs byte for byte.
- Both Atom feeds parsed as XML and contained all five new article URLs
  (15 entries in atom.xml; the latest 10 in feed.xml).
- Desktop/light and mobile/dark page screenshots inspected for spacing,
  typography, hierarchy, and readable wrapping. Figures link to full-size PNGs.

## Scientific boundaries retained

The reservoir example is a single-layer frequentist quantile readout, not the
Bayesian research implementation. The forecast example uses known simulated
distributions, not fitted model performance. Population interval geometry is
not a finite-sample certificate. The tolerance rule uses a conservative union
bound, not TCSP's sharper scan calibration. The endpoint example defines a
restricted discrete generalized posterior, not response-predictive inference
or an approximation certified for the continuous manuscript model.

No model-superiority, operational-deployment, or unearned tolerance claim was
introduced. The public citations identify announced arXiv versions rather than
mixing them with unannounced local revisions. Existing climate/data worktree
changes remain outside this publication.
