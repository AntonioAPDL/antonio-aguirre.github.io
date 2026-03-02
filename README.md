# Antonio Aguirre - Personal Website

This repository contains the source for antonio-aguirre.com, built with Jekyll and the Lanyon/Poole theme foundation.

## Local development

1. Install Ruby (see `.ruby-version`).
2. Install dependencies:
   ```bash
   bundle install
   ```
3. Run the site:
   ```bash
   bundle exec jekyll serve
   ```
4. Visit `http://localhost:4000`.

## Structure

- `index.html`, `about.md`, `research.md`, `teaching.html`, `software.md`, `blog.html`, `cv.html`, `contact.md`: main pages
- `_posts/`: blog posts
- `_layouts/`, `_includes/`: shared templates
- `public/`: theme assets and custom styles
- `files/`: PDFs and images

## San Lorenzo River live USGS plot

The home page includes a client-side Plotly chart of USGS instantaneous values for the San Lorenzo River (site 11160500). It is fully static and runs in the browser, with a mode toggle for stage or discharge.

- **Page location:** `index.html` (Plot Section).
- **Container class:** `.usgs-iv-plot`.
- **Client script:** `public/js/sanlorenzo_flow.js`.
- **Plotting library:** Plotly (pinned CDN version in `index.html`).
- **Data source:** USGS NWIS IV JSON endpoint.

### Configuration via data attributes

Stage mode (authoritative NOAA thresholds, exact stage values):

```html
<div class="usgs-iv-plot"
     data-site="11160500"
     data-mode="stage"
     data-period="P30D"
     data-refresh-min="15"
     data-timeout-sec="20"
     data-y-min="0"
     data-y-max="25"
     data-threshold-minor="16.5"
     data-threshold-moderate="19.5"
     data-threshold-major="21.76"
     data-title="San Lorenzo River Stage"
     data-ylabel="Stage">
  ...
</div>
```

Discharge mode (thresholds must be rating-derived; log axis optional):

```html
<div class="usgs-iv-plot"
     data-site="11160500"
     data-mode="discharge"
     data-period="P30D"
     data-refresh-min="15"
     data-timeout-sec="20"
     data-log-y="true"
     data-y-min="10"
     data-y-max="50000"
     data-threshold-minor="REPLACE_WITH_CFS"
     data-threshold-moderate="REPLACE_WITH_CFS"
     data-threshold-major="REPLACE_WITH_CFS"
     data-title="San Lorenzo River Discharge"
     data-ylabel="Discharge">
  ...
</div>
```

Supported attributes:

- `data-site` (required)
- `data-mode` (`stage` or `discharge`, default `discharge`)
- `data-parameter` (optional; overrides the mode default of `00065` for stage or `00060` for discharge)
- `data-period` (e.g., `P7D`, `P30D`, `P90D`)
- `data-refresh-min` (poll interval in minutes)
- `data-timeout-sec` (fetch timeout in seconds)
- `data-log-y` (`true`/`false` to enable a log-scale y-axis)
- `data-title` (optional label for accessibility)
- `data-ylabel` (base Y-axis label; units are appended automatically when available)
- `data-y-min`, `data-y-max` (optional fixed Y-axis range)
- `data-threshold-minor`, `data-threshold-moderate`, `data-threshold-major` (horizontal threshold lines + shaded regions)
- `data-forecast-url` (optional forecast overlay JSON; defaults to `/assets/data/forecasts/big_trees_latest.json`)
- `data-flood-minor-cfs`, `data-flood-moderate-cfs`, `data-flood-major-cfs` (discharge-only thresholds; optional)

### Forecast overlay (NWS/NWM)

The plot can overlay forecast guidance from a tracked JSON artifact:

- **Artifact:** `assets/data/forecasts/big_trees_latest.json` (tracked in git)
- **Update script:** `scripts/update_big_trees_forecast.sh`
- **Included series:** JSON may include NWPS analysis/short deterministic plus NWM medium/long quantiles (`p10/p50/p90`); the USGS panel overlay uses ensemble quantiles (medium/long) only.
- **Plot overlay behavior:** USGS observed discharge remains the base trace; NWS ensemble guidance is overlaid as medium/long `p10-p90` bands plus `p50` lines.
- **Unit harmonization:** forecast series are unit-normalized and converted (`cfs`/`cms`) to match the observed USGS discharge axis before plotting.
- **TODO:** HEFS ensembles once location_id lookup is resolved
- **Fallback behavior:** if `_sandbox/nws_ensemble_point` is absent, updater builds JSON directly from NOAA NWPS APIs.
- **Ops guard:** on updater errors, CI can keep the last tracked artifact by setting `BIG_TREES_FORECAST_ALLOW_STALE_ON_ERROR=1`.

To update the tracked forecast JSON:

```bash
scripts/update_big_trees_forecast.sh
```

If the forecast JSON is missing, the plot still renders observations only and logs a console warning.

## GEFS forecast panel (new, additive)

The home page now includes a second panel for GEFS point forecasts (precipitation + soil moisture) near Big Trees.

- **Panel container:** `index.html` (`.gefs-forecast-panel`)
- **Client script:** `public/js/gefs_forecast_panel.js`
- **Tracked asset:** `assets/data/forecasts/gefs_big_trees_latest.json`
- **Pipeline source:** `_sandbox/gefs_point_pipeline`
- **Update script:** `scripts/update_big_trees_gefs_forecast.sh`
- **Scheduled workflow:** `.github/workflows/update_gefs_forecast.yml` (every 3 hours)

Behavior:

- Fetches `gefs_big_trees_latest.json`
- Renders two Plotly charts:
  - APCP band (`p10-p90`) + `p50` + mean
  - SOILW depth-level medians (`p50`) with optional uncertainty bands
- Adds retrospective context from prior GEFS cycles and shows a fixed 20-day pre-forecast window
- Displays metadata and freshness warning if stale
- Degrades gracefully when JSON is missing/invalid

GEFS JSON includes optional retrospective metadata used by the panel:

- `observation_window_days` (default `20`)
- `retrospective.start_utc`, `retrospective.end_utc`
- `retrospective.precip.<level>.{p10,p50,p90,mean}`
- `retrospective.soil_moisture.<level>.p50`
- `gefs_analysis_context.precip_f003_proxy.<level>` (GEFS cycle-history analysis proxy, plotted)
- `gefs_analysis_context.soil_f000.<level>` (GEFS cycle-history analysis, plotted)
- Plot units are harmonized by panel logic (`APCP` in mm water-equivalent; `SOILW` in m3/m3)
- PRISM/ERA5 observed overlays are intentionally disabled in the panel (GEFS-only context mode)
- Exporter default is GEFS-only; observed payload is opt-in with `--include-observed-retrospective`
- Exporter uses a history-scan guard: skips git-history backfill when prior 20-day GEFS context is already complete

Background historical GEFS updater (no live monitoring):

- `scripts/start_gefs_history_daemon.sh`
- `scripts/stop_gefs_history_daemon.sh`
- `scripts/status_gefs_history_daemon.sh`
- `scripts/install_gefs_history_daemon_cron.sh` (optional `@reboot` + 30-minute watchdog install)
- launcher prefers a detached `tmux` session (`gefs_history_daemon`) when available
- for `source_priority: ["aws"]`, history catchup starts from `2020-10-01T00:00:00Z`

The daemon writes status to:

- `data/_sandbox_gefs/history/state/daemon_status.json`
- `data/_sandbox_gefs/history/state/backfill_status.json`
- `data/_sandbox_gefs/history/state/daemon_runs.jsonl`

Panel override:

- `data-observation-window-days` (defaults to `20` if omitted)

The existing USGS discharge panel logic in `public/js/sanlorenzo_flow.js` remains unchanged.

## Climate Data Automation (PRISM + ERA5 + NWM retro soil)

This repo includes a cron-safe climate stack that keeps canonical point series and a merged table:

- `prism_precipitation_santa_cruz_1987_2023.csv`
- `soil_moisture_data/soil_moisture_big_trees_daily_avg_1987_2023.csv`
- `soil_moisture_data/nwm_soil_moisture_big_trees_daily_1987_present.csv`
- `climate_daily_ppt_soil.csv`
- `climate_series_status.csv`

Fixed point:

- latitude `37.0443931`
- longitude `-122.072464`

Main scripts:

- `scripts/build_prism_ppt_point_series.R`
- `scripts/update_ppt_incremental.sh`
- `scripts/build_era5_soil_moisture_point_series.py`
- `scripts/update_soil_incremental.sh`
- `scripts/build_nwm_retro_soil_point_series.py`
- `scripts/update_nwm_soil_retro_full.sh`
- `scripts/build_climate_daily_combined_csv.py`
- `scripts/write_climate_series_status.py`
- `scripts/run_climate_updates_cron.sh`
- `scripts/install_climate_update_cron.sh`

Install cron (default every 6h at minute 17):

```bash
scripts/install_climate_update_cron.sh
```

Run one manual cycle:

```bash
scripts/run_climate_updates_cron.sh
```

Logs are written under `logs/climate_updates/` and `latest.log` points to the newest run log.

### GitHub Actions Automation

The repo now supports fully hosted climate + GEFS refresh on GitHub Actions:

- `.github/workflows/update_climate_series.yml`
  - cadence: disabled (manual `workflow_dispatch` only)
  - updates and commits:
    - `prism_precipitation_santa_cruz_1987_2023.csv`
    - `soil_moisture_data/soil_moisture_big_trees_daily_avg_1987_2023.csv`
    - `soil_moisture_data/nwm_soil_moisture_big_trees_daily_1987_present.csv`
    - `soil_moisture_data/nwm_soil_moisture_big_trees_daily_1987_present.meta.json`
    - `climate_series_status.csv`
    - `climate_daily_ppt_soil.csv`
  - dispatches `update_gefs_forecast.yml` after climate changes are pushed

- `.github/workflows/update_gefs_forecast.yml`
  - cadence: every 3 hours (`0 */3 * * *`)
  - updates and commits:
    - `assets/data/forecasts/gefs_big_trees_latest.json`
  - fail-fast checks in `scripts/update_big_trees_gefs_forecast.sh` ensure:
    - latest init is not stale
    - 20-day GEFS analysis context coverage remains dense and current
  - race guards:
    - hard sync to latest `origin/main` before processing
    - rebase-conflict-safe push (concurrent updates are skipped without failing the job)

- `.github/workflows/backfill_gefs_analysis_context.yml` (manual)
  - one-time/manual bootstrap for GEFS cycle-analysis context
  - backfills missing `f003` precip proxy and `f000` soil markers over a target window (default 20 days)
  - rewrites latest full GEFS payload at the end so forecast panel remains complete

Required repository secrets for ERA5 updates:

- `CDSAPI_KEY` (format: `<uid>:<api-token>`)
- optional `CDSAPI_URL` (defaults to `https://cds.climate.copernicus.eu/api`)

NWS/NWM overlay JSON fields (abridged, existing USGS panel):
- `generated_utc`, `provider_mix`, `init_times`
- `ranges.{analysis|short|medium_range|long_range}` with deterministic or p10/p50/p90 series

### Deriving discharge thresholds from stage

Discharge thresholds are not canonical constants; derive them from the USGS rating curve and record the run date.

Script:

```bash
Rscript scripts/compute_discharge_thresholds_from_stage.R 11160500 16.5 19.5 21.76
```

Update the `data-threshold-*` values in the HTML with the computed cfs numbers and note the rating retrieval date.

### Cache behavior (localStorage)

The last successful data payload is cached in `localStorage` and used on load if not stale (max of 4x refresh interval or 30 minutes). If USGS is unavailable, the last known plot stays visible with a warning.

To clear the cache, open dev tools and remove keys starting with `usgs-iv:` or run:

```js
localStorage.removeItem('usgs-iv:11160500:00065:P30D:v3');
```

### Troubleshooting

- **CORS errors:** USGS normally allows cross-origin requests. If blocked, test the endpoint directly in a browser to confirm availability.
- **Rate limiting (403/429):** The script backs off and shows a warning. Increase `data-refresh-min` if needed.
- **Offline:** The status line reports offline and retries when the connection returns.
- **Unexpected response:** A schema or JSON error will show a warning; verify the endpoint.
- **Threshold units:** Thresholds must match the parameter units. NOAA flood thresholds are stage (ft); for discharge (`00060`), use rating-derived cfs thresholds.
