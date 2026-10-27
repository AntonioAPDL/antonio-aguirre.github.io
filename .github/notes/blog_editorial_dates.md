# Research-note editorial dates

On October 27, 2026, the owner requested unevenly spaced dates for the six
new research notes, between the preceding blog entry (March 20, 2025) and
October 27, 2026. The following editorial dates replace the shared October 27
date. They are owner-requested assignments, not dates verified from archival
publication records. The notes were first deployed on October 27, 2026; that
date remains their `updated` value. Earlier implementation notes record that
original deployment and are retained as historical documentation.

| Note | Assigned date |
| --- | --- |
| Dynamic quantile models with exdqlm | June 12, 2025 |
| Fixed recurrent quantile features | September 9, 2025 |
| Quantile forecast checks | December 4, 2025 |
| Interval placement | March 18, 2026 |
| Tolerance intervals | July 9, 2026 |
| Endpoint regression | October 13, 2026 |

Filenames and YAML dates agree, cross-links use the new dated routes, and
Netlify 301 redirects preserve all six original October 27 URLs. R runners
resolve a unique post by slug rather than hard-coding its editorial date.
The path-scoped R workflow likewise matches the stable slugs. Regression
tests check dates, ordering, update timestamps, redirects, and cross-links.

The model code, results, references, and figures are unchanged by this edit.
`last_modified_at` also remains October 27 so sitemap freshness reflects the
actual revision rather than the assigned editorial date.

Validation: 16 Python tests, both blog quality gates, both executable example
runners, site integrity, and the pinned production Jekyll build passed. Both
feeds carry the assigned dates and October 27 update timestamps. Sitemap
revision dates and copied redirect rules were checked. Chromium passed all
24 article/viewport/theme combinations, including displayed dates, internal
links, mathematics, figures, overflow, and reverse-chronological index order.
