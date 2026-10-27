# Blog model fit and forecast recheck

October 27, 2026. This record supersedes the initial numerical examples in
plans 01, 02, and 06; the earlier records are retained as history.

## Diagnosis

1. The exdqlm example generated a trend plus a period-80 sinusoid but fitted
   only a local trend. Its extrapolation could not represent seasonal turning
   points. Twenty verification observations also made tail assessment fragile.
2. The recurrent example's 210 fitting rows were a small upper-tail sample for
   twelve correlated features. Its plot did not show training predictions or
   distinguish target recovery from errors against noisy responses clearly.
   There was no discovered temporal-leakage bug, but a separate reservoir seed
   makes the data/feature-randomness separation clearer.
3. The endpoint example used 80 observations and a coarse grid. Its estimated
   intercept could differ visibly from the population value without a coding
   error. It also lacked independent verification and explicit recovery metrics.
4. The other three notes contain analytic interval calculations, an explicitly
   biased forecast negative control, and a tolerance-construction experiment.
   They are not poor fits to repair. Their existing calculations were rerun.

## Changes and safeguards

- exdqlm: keep the original simulation seed, noise SD, trend, period, and
  seasonal amplitude. Use 800 training observations and 80 final verification
  observations. Add `seasMod()` to the trend, giving four states. The final
  teaching model fixes discount 1 to match the stated constant-coefficient
  generating mechanism, retaining state uncertainty without evolution shocks.
  Fit this specification to training data only. Reconstruct the quantile with
  the full observation vector; the
  first state alone omits the seasonal contribution. Add a credible static
  harmonic-regression baseline alongside the constant recent-cycle baseline.
- Recurrent readout: keep the generating mechanism, original data seed, target,
  and reservoir dimensions. Increase training/test sizes to 1,600/400. Set an
  independent fixed reservoir seed (210), retain training-only normalization,
  and include the original lag alongside recurrent features, consistent with
  the research representation. Plot a predetermined 140-row window and show
  target recovery for every held-out row in a separate panel. These remain
  rolling one-step forecasts, not a 400-step trajectory issued at the cutoff.
- Endpoint regression: retain the original data seed and model; increase to
  600 training observations and a 41-by-41-by-41 grid. Keep the fixed learning
  rates, prior, and support. Evaluate 1,000 independent responses using a new,
  explicitly separate seed. Calculate endpoint RMSE and population content
  under the known simulation CDF. These remain endpoint credible bands, not
  predictive or tolerance bands.

No oracle quantile values enter fitting or coefficient updates. The known
simulation structure informs the model specification, as explicitly disclosed.
No offsets are added after seeing verification responses to force coverage.
No seed is selected for a favorable figure. Larger samples are an explicit
change to the teaching experiments, not evidence of a new inference algorithm.

## Reference results

R 4.5.3; exdqlm 1.1.2 in an isolated library; quantreg 6.1.

| Example | Current recovery and verification |
| --- | --- |
| exdqlm | Fixed discount 1; 43 iterations; target RMSE 0.08005434; check loss 0.1882; fraction below 0.8125 versus oracle 0.8375 |
| Harmonic baseline | Check loss 0.1842; fraction below 0.825; same training/test rows and known seasonal period |
| Recurrent readout | Target RMSE 0.1392275; check loss 0.1077158 versus linear 0.1176063; fraction below 0.9025 versus oracle 0.8950 |
| Endpoint regression | Endpoint RMSE 0.02096199; mean population content 0.78789635; independent held-out fraction 0.778; boundary posterior mass about 1.51e-13 |

None is described as perfect. A good recovered curve does not erase finite
verification-sample tail discrepancies.

### Rejected small-validation tuning approach

The audit initially tried choosing among 0.98, 0.995, and 1 at training origins
240 and 320, each with an 80-step validation window. The reference seed chose
0.995 and had target RMSE 0.1694. On data seeds 1--3, this rule chose discounts
1, 0.98, and 0.98 and produced RMSE 0.0720, 0.3313, and 0.3303. It introduced
unnecessary variability for this known constant-coefficient simulation. The
final article therefore uses the structurally matching fixed-evolution case,
not this unstable selection rule. Adaptivity selection for genuinely changing
signals needs a broader validation design. This is an openly revised teaching
experiment, not a claim of preregistered model selection or blind evaluation.

With fixed evolution, the 400-observation reference fit had RMSE 0.1951864.
Increasing the training record from five to ten cycles improved the precision
of the estimated slope and seasonal coefficients: the final 800-observation
reference has RMSE 0.08005434. The simulation seed, generating mechanism,
noise scale, and forecast horizon are unchanged. The time-series figure shows
only the last two training cycles plus the forecast cycle, explicitly labeled,
so a long global trend does not visually conceal local forecast errors.

## Repeated-seed audit

`scripts/audit_blog_fit_recovery.R` executes the actual published R fences,
substituting only the data seed. The recurrent feature-map seed stays fixed;
endpoint verification uses its own seed. It reports every seed in the fixed
panel, without selecting an example based on performance. Ten runs each give:

| Model | Mean target RMSE | Mean held-out fraction |
| --- | --- | --- |
| Recurrent, seeds 1--10 | 0.1345922 | 0.8880 (target 0.9) |
| Endpoints, seeds 1--10 | 0.03661275 | 0.7962 (target 0.8) |
| Seasonal, 400 training rows (development), seeds 1--3 | 0.1205301 | 0.8667 (target 0.85) |
| Seasonal, final 800 training rows, seeds 1--3 | 0.09714019 | 0.8500 (target 0.85) |

The recurrent fraction ranges from 0.8325 to 0.9075; endpoint fractions range
from 0.762 to 0.820. Reporting the range avoids disguising run-to-run variation.
These small simulation panels are regression diagnostics, not calibration
theorems or model-superiority studies.

The 400-row development seasonal runs have RMSE 0.07200227, 0.20364563, and
0.08594229; corresponding fractions below are 0.8625, 0.8875, and 0.85.
All fits converged. The original reference data seed is retained even though
these additional seeds have smaller errors; there was no favorable-seed swap.

For the final 800-row seasonal example, seeds 1--3 give RMSE 0.07500577,
0.10601090, and 0.11040389, with fractions below 0.8875, 0.8750, and 0.7875.
All converge with the fixed discount 1. Together with the recurrent and endpoint
panels, this is 23 additional simulated-data runs beyond the reference examples.

Reproduce the two panels with:

```bash
Rscript --vanilla scripts/run_research_blog_examples.R
Rscript --vanilla scripts/audit_blog_fit_recovery.R
```

With the reference exdqlm library active, add `--include-exdqlm` to repeat the
entire fixed-evolution fit and forecast procedure on three further data seeds.
This involves many additional fits and can take several minutes. The reference
seasonal example runs through `scripts/run_exdqlm_blog_example.R`.

The scoped research-example CI workflow now executes both the article checks
and the ten-seed recurrent/endpoint panels. Local site gates, the Python suite,
the pinned Jekyll build, and desktop/mobile/light/dark browser checks accompany
the numerical checks. Existing climate-data worktree changes are out of scope.
