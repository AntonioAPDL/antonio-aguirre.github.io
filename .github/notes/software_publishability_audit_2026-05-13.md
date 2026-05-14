# Software Publishability Audit (2026-05-13)

## Purpose

Identify which active research/software repositories are strong candidates for the website software page, which code assets are worth highlighting, and which repositories need cleanup before public promotion.

## Repositories Checked

| Repository | Local status after fetch | Visibility observed via GitHub | Publishability read |
|---|---:|---:|---|
| `antonio-aguirre.github.io` | clean, synced | public | Current site source of truth. |
| `exdqlm` | local checkout dirty on `feature/benchmark-data-pipeline`; inspected temp worktrees for `origin/feature/0.5.0-crps-iqs` and `origin/feature/glofas-discrepancy-qdesn` | public | Strongest software-page candidate. Package code is documented, tested, and CRAN-relevant. |
| `exdqlm---Article` | clean, synced | public | Good publication-context link; not a code showcase by itself. |
| `project1_ucsc_phd` | dirty on `feature/export_posterior_tables`, ahead 1 | public as `Project1` | Technically rich but not safe to promote raw yet. Needs credential/path cleanup and a public-facing README. |
| `project1_ucsc_phd/Evironmetrics---REVISED-DOC-2` | fetched, clean, local branch `math-notation-integration` at `origin/main` | public | Revised manuscript/artifact freeze. Good for paper provenance; not a software showcase. |
| `Corrections---Project-1` | clean, synced | public | Response workbook; useful internally, not software-page material. |
| `Environmetrics_paper_repo` | clean, synced | public | Older paper repo; superseded by revised article repo for current work. |
| `Article-Q-DESN` | clean, synced | private | Strong active research repo, but not ready as a public link while private and engine-dependent. |
| `Q-DESN---Theory-for-implementation` | fast-forwarded, clean, synced | public | Theory note; useful context, not a code/software item. |
| `QDESN---Multivariate-Application` | inspected via temp clone | public | Single Overleaf-style theory note only; not software-page material yet. |
| `NDLM---Ensemble` | dirty | public | Theory/prototype material; not ready to feature until cleaned and scoped. |

## Key Findings

1. `exdqlm` should remain the primary featured software item.
   - CRAN release and JSS manuscript status already justify top placement.
   - The package has coherent user-facing APIs, R documentation, C++ kernels, tests, and release notes.
   - `origin/feature/0.5.0-crps-iqs` is a clean next-release story: deterministic KL diagnostics and CRPS/IQS-style forecast scoring.

2. `project1_ucsc_phd` should not be linked raw from the software page yet.
   - It contains a tracked notebook with a literal database password string. Treat this as credential exposure until rotated and scrubbed.
   - It has many absolute local paths under `/data/muscat_data` and `/home/jaguir26`.
   - It is a high-value internal evidence repo, but too operational/private-path-heavy for polished public presentation in its current state.

3. The revised Environmetrics article repo is the current paper source of truth.
   - `Corrections---Project-1/WORKFLOW.md` points to `project1_ucsc_phd/Evironmetrics---REVISED-DOC-2`, not the older standalone `Environmetrics_paper_repo`.
   - This repo is useful for provenance, generated figures, table manifests, and reproducibility claims.

4. `Article-Q-DESN` is high-quality but not public-facing yet.
   - It has an excellent staged application workflow, contracts, tests, and documentation.
   - Local application tests currently fail when the Q-DESN discrepancy engine is unavailable, which is expected but means the repo cannot be marketed as push-button reproducible yet.
   - It is private, so the website should mention the working paper, not link the repository unless a public snapshot is prepared.

5. The Q-DESN discrepancy engine branch is promising but not release-ready.
   - `origin/feature/glofas-discrepancy-qdesn` adds `qdesn_fit_discrepancy()`, AL MCMC/VB source-indexed fits, capability gating, and tests.
   - A local smoke test could not run because the branch imports `brms`, which is unavailable locally and is a heavy dependency for package promotion.
   - Before public promotion, decide whether `brms` truly belongs in `Imports`; if not, move it to `Suggests` or isolate optional code paths.

## Candidate Assets Worth Featuring

### Ready Now

Feature through the existing `exdqlm` card:

- `R/exdqlmLDVB.R`: dynamic exDQLM Laplace-delta VB engine.
- `R/exdqlmMCMC.R`: dynamic posterior simulation path.
- `R/quantileSynthesis.R`: post hoc noncrossing multi-quantile synthesis.
- `R/exdqlmDiagnostics.R` and `R/kl_diagnostics.R` from `origin/feature/0.5.0-crps-iqs`: deterministic KL and finite-grid CRPS diagnostics for forecast evaluation.
- `src/exAL.cpp`: exAL density/CDF/quantile/random-generation numerics.
- `src/kalman.cpp` and `src/mcmc_ffbs.cpp`: C++ Kalman/FFBS acceleration and posterior state simulation kernels.

Best website framing:

> `exdqlm` is a CRAN-published R package for Bayesian dynamic quantile state-space modeling, combining LDVB, MCMC, optional C++ Kalman/FFBS acceleration, diagnostics, and multi-quantile posterior-predictive synthesis.

### Good After Light Cleanup

Use only after a small public-facing wrapper or README is prepared:

- `project1_ucsc_phd/scripts/audit_he2_bayesian_publication_relaunch_liveness.py`: strong Python operational tooling; targeted tests pass.
- `project1_ucsc_phd/R/unified/post_publication_figures.R`: strong R figure-production and publication styling logic.
- `project1_ucsc_phd/R/unified/stages/stage_fit.R`: robust health checks and fit-stage contracts, but too coupled to local runtime paths for direct promotion.
- `project1_ucsc_phd/DISC_kalman_synth.cpp`, `sampling_exal.cpp`, `sampling_truncnorm.cpp`: sophisticated C++ kernels, but should be presented through `exdqlm` package equivalents where possible rather than raw research scripts.

### Not Yet

- Raw `project1_ucsc_phd` repo link: blocked by credential risk, private paths, and heavy operational coupling.
- `Article-Q-DESN` repo link: private and dependent on an external Q-DESN engine branch.
- `QDESN---Multivariate-Application`: theory-only single-file repo.
- `NDLM---Ensemble`: dirty local tree and theory/prototype orientation.

## Verification Performed

- Fetched key local repositories and remote branches.
- Fast-forwarded `Q-DESN---Theory-for-implementation`.
- Inspected `exdqlm` branches via temp worktrees:
  - `origin/feature/0.5.0-crps-iqs`
  - `origin/feature/glofas-discrepancy-qdesn`
- Ran targeted tests:
  - `project1_ucsc_phd`: `17 passed` for HE2 relaunch/liveness Python tests.
  - `exdqlm` `origin/feature/0.5.0-crps-iqs`: package-loaded tests passed for diagnostics, KL diagnostics, and quantile synthesis.
- Q-DESN application tests:
  - `Article-Q-DESN/application/tests/run_tests.R` failed because the Q-DESN discrepancy engine was unavailable.
- Q-DESN discrepancy branch:
  - package load was blocked by missing `brms` dependency.

## Recommended Website Strategy

1. Keep one polished primary software item: `exdqlm`.
2. Add a smaller "Research Engineering" subsection only after cleanup, with 2-3 curated examples rather than raw repo sprawl.
3. Do not publish raw code snippets directly on the website; link to repos/files only after:
   - secrets are removed and rotated;
   - absolute local paths are replaced by env/config variables;
   - a clear README explains inputs, outputs, and reproducibility limits;
   - representative tests pass in a clean checkout.
4. For Q-DESN, describe it as an active working-paper software pipeline, but wait to link code until either:
   - `Article-Q-DESN` gets a public reproducibility snapshot, or
   - the Q-DESN engine is merged into a release branch of `exdqlm` with lightweight dependencies.

## Immediate Next Actions

1. Rotate/scrub the database credential found in `project1_ucsc_phd/Characteristic.ipynb`; remove it from git history if the public repo has exposed it.
2. Decide whether `project1_ucsc_phd` should remain public or become private until cleanup.
3. Prepare a public-safe `project1_ucsc_phd` README focused on reproducible workflow architecture, not machine-local paths.
4. Keep `exdqlm` as the only website-linked code repo for now.
5. Revisit the software page once `exdqlm` `0.5.0` and/or Q-DESN discrepancy work has a clean release branch.
