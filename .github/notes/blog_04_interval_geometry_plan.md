# Blog 04: Fixed content does not fix placement

Investigation and teaching plan, October 27, 2026.

## Evidence and version boundary

Read the fixed-content and retained-mean sections of the local RQR-GIBBS
manuscript and compare with https://arxiv.org/html/2607.26098v3. Local revisions
have changed the tolerance-computation emphasis; use the announced v3 for
the public paper title and distinguish population geometry from tolerance
calibration. Cross-check the midpoint/half-width loss against
https://arxiv.org/html/2610.13960v1, Section 2. Credit Pouplin et al. for the
original residual-product loss; MPI/MTI describes the target, not a new name
for ordinary equal-tailed quantile regression.

## Teaching sequence

1. Give a concrete right-skewed distribution whose CDF is known.
2. Parameterize all finite exponential content-c windows by lower-tail mass.
3. Compare shortest, equal-tailed, and mean-preserving windows at c=0.8.
4. Compute retained means analytically and solve only the scalar MPI equation
   with base R's established root solver.
5. Introduce tilt as a specified retained-mean offset, not a fitted nuisance.
6. State interior regularity assumptions and treat the shortest support-boundary
   example as a boundary member, not an interior score-equation solution.
7. Separate population targets, estimated endpoints, and tolerance guarantees.

## Acceptance

Check each interval's probability content, MPI retained mean, endpoint ordering,
and analytic retained means against independent integration. Generate three
panels with identical axes. No simulation performance claims and no tolerance
certificate in this post. Check rendered equations, caption, and mobile layout.

## Executed checks

Three article R blocks passed under R 4.5.3. Widths were 1.6094 (shortest),
2.1972 (equal-tailed), and 2.9130 (MPI). All contents equaled 0.8 to numerical
precision; MPI retained mean equaled 1. Analytic retained means agreed with
independent integration within 1e-9. The figure uses identical axes.
