# Blog 06: Endpoint regression and dynamics

Investigation and teaching plan, October 27, 2026.

## Evidence and scope

Read Sections 2--6 of local MTI-EXTENSIONS/main.tex and compare with the
announced https://arxiv.org/html/2610.13960v1. Verify the residual-product loss,
fixed-tilt term, root-label symmetry, learning-rate distinction, and conditional
Gaussian versus joint-quartic computation. Generalized Bayes reference:
https://doi.org/10.1111/rssb.12158. Do not present endpoint uncertainty as a
response likelihood, a predictive distribution, or a tolerance certificate.

## Teaching sequence

1. Move from a population interval to covariate-dependent midpoint and width.
2. Define product-residual loss and explain why its sign records inclusion.
3. Derive a small discrete generalized posterior: linear midpoint, positive
   constant half-width, zero tilt, proper finite-grid prior. This is a restricted
   teaching model, not the paper's unrestricted two-root sampler.
4. Evaluate all grid points, normalize log weights stably, check normalization,
   and compute pointwise endpoint credible bands without sampling.
5. Separate the learning rate from content and tilt. Report sensitivity without
   claiming frequentist calibration. State that the grid defines the model,
   not a certified quadrature approximation to a continuous posterior.
6. Explain raw-root sorting at predictor values, then dynamic endpoint states.
   Gaussian conditional root updates do not make the joint observation kernel
   Gaussian, and dynamic regression does not inherit iid tolerance calibration.

## Acceptance

Execute every R block, verify normalized finite posterior masses, ordering,
constant-width support, root-swap loss invariance, and exact loss normalization
against direct exponentiation after subtracting the minimum loss. Check the
learning-rate sensitivity and boundary posterior mass. Figure must distinguish
endpoint uncertainty bands from the fitted interval and known simulation target.
Final production/browser checks apply to all five posts together.

## Executed checks

All four blocks passed under R 4.5.3. At learning rate 1 the posterior mean
intercept, slope, and half-width were 0.6017088, 0.8732874, and 0.7541208.
Boundary mass was 0.002284933. At rate 0.5 the corresponding means were
0.5912024, 0.8488333, and 0.7609133. Normalization, independent weight
calculation, endpoint ordering, credible-bound ordering, and root-swap
invariance passed. No response-predictive or tolerance claim is made.
