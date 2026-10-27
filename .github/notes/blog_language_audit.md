# Blog language and tone audit

Reviewed and revised October 27, 2026, against baseline commit `851c32b`.
Scope: all 15 published posts, their descriptions and excerpts, selected
headings and captions, and the Blog index introduction.

## Editorial findings

The main problems were sentence patterns, not individual vocabulary:

- Generic emphasis: statements such as "This matters because" introduced a
  consequence without stating it directly.
- Repeated contrasts: "not X, but Y" constructions sometimes repeated a
  distinction already established in the preceding paragraph.
- Evaluative language: "powerful," "reassuring," "serious analysis," and
  "useful" sometimes expressed approval without an observable criterion.
- Moral framing: "honest," "earned," "blindly," and "silently" introduced
  judgments where a description of the evidence or procedure was sufficient.
- Broad claims: statements about why most projects fail, what failure is most
  common, or which approach is best lacked support within the article.
- Repeated conclusions: closing paragraphs sometimes restated an abstract
  lesson instead of specifying what to report or which limitation remained.

These are editorial judgments. No word or sentence pattern establishes whether
a passage was written by an AI system. Technical terms and necessary contrasts
were retained where they describe the statistical problem accurately.

## Revisions by article

| Article | Main changes |
| --- | --- |
| From questions to a generative model | Replaced claims about elegant models and failed projects with a direct account of targets, observation processes, model components, and replicated data. |
| Preparing and monitoring computation | Replaced "This matters" and broad endorsements of approximate methods with quantity-specific Monte Carlo checks, numerical tolerances, and reporting requirements. |
| Simulation, recovery, and calibration | Removed praise of simulation and "not glamorous" wording; distinguished the purposes of deterministic, recovery, prior predictive, SBC, and predictive checks. |
| Diagnosing fit and revising the model | Removed claims about disciplined responses and guaranteed benefits of revision; described failure categories, diagnostic experiments, and limits of attribution. |
| Comparing and combining predictive models | Replaced winner-oriented phrasing with uncertainty in score differences, selection effects, validation scope, and the interpretation of stacking, BMA, and projection. |
| Iteration, stopping, and reporting | Removed moral framing and rhetorical closing contrasts; described data reuse, stopping criteria, provenance, and what readers need to reconstruct decisions. |
| Gaussian energy score | Removed generic assurances and the "goal is not" conclusion; specified covariance requirements, numerical comparisons, random-pair computation, and reporting details. |
| UCSC Hummingbird | Removed "blindly," "source of truth," and an unsupported most-common-failure claim; described allocation checks, threading, measured requests, and batch-environment requirements. |
| Laplace-delta variational inference | Replaced "clean," "attractive," "the distinctions matter," and "keep the approximation modest" with explicit approximation targets and numerical diagnostics. |
| Dynamic quantile models with exdqlm | Shortened the introduction and baseline discussion; removed moral language around historical validation and convergence; retained working-likelihood and uncertainty distinctions. |
| Fixed recurrent quantile features | Described the feature/readout separation directly; replaced generic good-model claims with target-recovery diagnostics and precise one-step information sets. |
| Checking quantile forecasts | Replaced conversational opening questions and favorable-diagnostic rhetoric with information sets, prediction objects, evaluation rules, and the scope of marginal scores. |
| Intervals with equal content | Replaced a rhetorical opening and "important question" with the content-placement distinction; clarified the role of retained means and tolerance confidence. |
| Tolerance intervals | Removed "clever," "the phrase matters," and "a guarantee it has not earned"; stated the fixed-index assumption, selection adjustment, and guarantee scope directly. |
| Endpoint regression | Removed "inspectable," "reassuring," "serious analysis," and fitting-function rhetoric; described the discrete model, boundary-mass diagnostic, and conditional computation. |

## Representative changes

| Earlier wording | Revised approach |
| --- | --- |
| "This matters because Bayesian computation can fail quietly." | Describe how effective sample size, objective stability, and local optimization can fail to assess the reported target. |
| "These checks are not glamorous, but they are high value." | Identify time-index, matrix-orientation, and unit-conversion errors that the tests detect. |
| "The honest solution is to describe the workflow." | State how data informed successive choices and which conclusions have independent support. |
| "A serious analysis would examine grid refinement." | Specify sensitivity to grid resolution and parameter support without judging the analyst. |
| "A guarantee it has not earned." | State which content-confidence argument must cover the actual construction and selection rule. |

## Preservation and scope

- All 40 fenced code blocks are byte-identical to the baseline.
- All 115 mathematical spans are byte-identical and in their original order.
- Reference sections and Markdown link targets are unchanged.
- Publication dates, URLs, series order, and verification dates are unchanged.
- Existing model results and figure files are unchanged.
- Revision dates and sitemap modification dates reflect October 27, 2026.
- Hummingbird's operational `last_verified` date remains July 29; this editorial
  review does not claim to have reverified the cluster configuration.
- Prose word count changed from 14,049 to 13,623. No content threshold was
  weakened, and no text was added merely to meet the existing 700-word minimum.
- Existing climate-data worktree changes are outside this edit.

The emphasis is precision and readability, not indiscriminate shortening.
Some passages grew because a vague judgment was replaced with specific checks
or a qualified explanation. Model limitations were retained alongside results.

## Guidelines for later posts

1. Name the statistical quantity or computational operation before explaining
   its consequence. Prefer the consequence itself to "this matters."
2. Support evaluative words with an observable property: coverage, score,
   numerical error, computational cost, or a stated assumption.
3. Use contrasts where two technical objects genuinely differ, but avoid
   repeating the same contrast in the opening, caption, and conclusion.
4. Separate algorithm convergence, approximation accuracy, predictive quality,
   and uncertainty calibration. Do not compress them into a generic assurance.
5. Describe what a diagnostic establishes and what remains unassessed.
6. Preserve conventional terminology. Words such as "importance," "weak
   identification," and "robustness" are not evidence of synthetic authorship.
7. Keep introductions and summaries specific to the article. Close with the
   applicable assumptions, reporting requirements, or next methodological step.

## Validation

All 15 posts passed the existing publication gate. The 16 Python regression
tests, static checks for 29 R and 10 Bash fences, and site integrity checks
passed. The five research-example reference calculations were rerun; their
results are unchanged. Code, mathematics, references, link targets, and selected
metadata were also compared directly with the baseline commit.

The pinned Ruby 3.3.4 / Bundler 2.5.23 production build passed. Both Atom feeds
parsed successfully with current revision timestamps. Browser tests passed all
60 article/viewport/theme combinations (15 posts, 1440px and 390px, light and
dark). Checks covered one H1, the References section, rendered mathematics,
loaded images, internal links, revision dates, and page-wide overflow. Selected
mobile/dark and desktop/light screenshots were visually inspected.

The existing provider-limited NWM soil-staleness warnings remain unrelated to
this editorial change. Publication is followed by live text and metadata checks.
