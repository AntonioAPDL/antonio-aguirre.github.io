# GEFS Observed-Context Harmonization (2026-08-07)

## Decision

The public GEFS Big Trees panel may show observed climate context only when the
plotted units and temporal support are explicit.

- PRISM precipitation is plotted as observed daily total precipitation in `mm`.
- GEFS APCP is exported as complete 24-hour water-equivalent totals. Native GEFS
  APCP values are not plotted directly against PRISM daily totals.
- ERA5-Land `swvl1` is plotted as near-surface observed soil-moisture context in
  `m3/m3`.
- GEFS SOILW is exported as complete 24-hour means in `m3/m3` by model
  soil-depth layer.

## Rationale

`1 kg m**-2` of liquid-water equivalent equals `1 mm`, so GEFS APCP units can be
converted directly to millimeters. The earlier mismatch was temporal support:
GEFS APCP arrives as accumulation windows, while PRISM is daily totals. The web
export now sums non-overlapping 6-hour GEFS accumulation windows into complete
24-hour totals before plotting.

GEFS SOILW and ERA5-Land `swvl1` are unit-compatible volumetric water fractions.
The exporter averages GEFS instantaneous 3-hourly SOILW values into complete
24-hour means before plotting them next to daily ERA5 context. They remain
different model/analysis products with different layer definitions, so ERA5 is
labeled as near-surface observed context rather than as a direct verification
target for every GEFS depth.

## Validation Expectations

- Forecast precipitation sections should declare `time_support:
  "24-hour accumulation"`.
- Forecast soil-moisture sections should declare `time_support: "24-hour mean"`.
- GEFS asset validation should fail when observed PRISM precipitation is present
  but GEFS precipitation is not exported as 24-hour totals.
- Observed climate freshness is provider-lagged. PRISM and ERA5 gaps immediately
  before the forecast cycle are expected when the providers have not yet
  released the latest dates.
