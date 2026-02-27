# GEFS Panel Decision (2026-02-27)

## Decision
- GEFS homepage panel uses **GEFS-only context**.
- PRISM/ERA5 observed retrospective overlays are disabled.
- Automated climate-series cron updates are disabled for this panel path.

## Why
- Direct side-by-side overlays created misleading visual comparisons due to data semantics mismatch:
  - GEFS precipitation context uses cycle-based short accumulation proxies, while PRISM is daily totals.
  - GEFS SOILW and ERA5 swvl1 differ by model structure/depth behavior and can show persistent offsets.
- The panel goal is now consistency and operational clarity for GEFS products only.

## What changed
- Frontend no longer fetches or plots `observed_retrospective` for GEFS charts.
- GEFS exporter no longer emits `observed_retrospective` unless explicitly requested with:
  - `--include-observed-retrospective`
- `.github/workflows/update_climate_series.yml` cron trigger removed (manual dispatch kept).

## Re-enable path (future)
- If we want external observed overlays again, do it with explicit harmonization:
  - precipitation: same temporal support (daily-to-daily or 3h-to-3h)
  - soil moisture: layer/depth harmonization and documented bias-adjustment strategy
