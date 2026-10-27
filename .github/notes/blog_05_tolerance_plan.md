# Blog 05: Tolerance confidence

Investigation and teaching plan, October 27, 2026.

## Evidence and scope

Read the announced tolerance manuscript's distinction between TCSP's scan
certificate and generalized-posterior endpoint summaries:
https://arxiv.org/html/2607.26098v3. Confirm the classical reference:
Wilks (1941), https://doi.org/10.1214/aoms/1177731788.

The public example will NOT implement TCSP. Derive a simpler conservative
shortest-window rule from fixed uniform order-statistic spacings and the union
bound. This avoids requiring unreviewed scan-calibration code or pretending
Monte Carlo produces a theorem. State iid continuity and the finite closed
sample-window convention. Distinguish the spacing d from the retained count
d+1; include the sample-range feasibility calculation explicitly.

## Teaching sequence

1. Define content c and repeated-sampling confidence gamma separately.
2. Show why the sample range can be insufficient at small n.
3. Derive the Beta(d,n+1-d) content of a fixed indexed window.
4. Explain why choosing the shortest window invalidates a fixed-window argument.
5. Calibrate d before seeing data using a union bound over n-d windows.
6. Simulate the complete fixed rule, calculate true content under a known CDF,
   and report Monte Carlo uncertainty, not just success frequency.
7. Explain conservatism, scan-specific improvements, and limits under dependence
   and regression. Link to the endpoint-regression note, not a claimed dynamic
   tolerance guarantee.

## Acceptance

Check range formula against Beta tail; calibrate d deterministically; enumerate
all allowed windows; independently compare selected width with their minimum.
Assert requested confidence is met by the analytic bound. Verify finite content
and ordered endpoints. Simulation is a diagnostic only. Render the feasibility
and simulation panels; final shared browser and publication checks apply.

## Executed checks

R 4.5.3: all four blocks passed. For n=30 and c=0.9 the sample-range
confidence is 0.816305. For n=90, the conservative rule selected spacing 88
(89 retained points), with lower bound 0.990791. In 2,000 exponential samples,
the success fraction was 0.994, Monte Carlo SE 0.001726847. Candidate-width
enumeration and Beta-tail cross-checks passed. This simulation does not certify
TCSP or any regression/dynamic procedure.
