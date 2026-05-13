# GEFS Panel Decision (2026-02-27)

## Decision
- GEFS homepage panel uses **GEFS-only context**.
- PRISM/ERA5 observed retrospective overlays are disabled.
- Automated climate-series updates remain decoupled from the GEFS panel. They can stay scheduled for the standalone canonical CSV products without being plotted in the panel.

## Why
- Direct side-by-side overlays created misleading visual comparisons due to data semantics mismatch:
  - GEFS precipitation context uses cycle-based short accumulation proxies, while PRISM is daily totals.
  - GEFS SOILW and ERA5 swvl1 differ by model structure/depth behavior and can show persistent offsets.
- The panel goal is now consistency and operational clarity for GEFS products only.

## What changed
- Frontend no longer fetches or plots `observed_retrospective` for GEFS charts.
- GEFS exporter no longer emits `observed_retrospective` unless explicitly requested with:
  - `--include-observed-retrospective`
- `.github/workflows/update_climate_series.yml` may remain scheduled because it maintains separate climate CSV artifacts; the GEFS panel ignores those artifacts by default.

## Re-enable path (future)
- If we want external observed overlays again, do it with explicit harmonization:
  - precipitation: same temporal support (daily-to-daily or 3h-to-3h)
  - soil moisture: layer/depth harmonization and documented bias-adjustment strategy
