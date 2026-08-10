# Antonio De Leon - Personal Website

This repository contains the source for antonio-de-leon.com, built with Jekyll and the Lanyon/Poole theme foundation.

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

## Verification

Useful checks before committing site or data-pipeline changes:

```bash
python3 scripts/check_site_integrity.py
_sandbox/gefs_point_pipeline/.venv/bin/python -m pytest _sandbox/gefs_point_pipeline/tests
bundle exec jekyll build --trace
```

Notes:

- `scripts/check_site_integrity.py` validates generated CSV schemas, JSON assets, YAML config/workflows when PyYAML is available, local asset references, and unresolved conflict markers.
- The Jekyll build requires Ruby from `.ruby-version` plus Bundler `2.5.23` from `Gemfile.lock`.
- The GEFS tests use the sandbox virtualenv described in `_sandbox/gefs_point_pipeline/README.md`.

## Structure

- `index.html`, `about.md`, `research.md`, `teaching.html`, `software.md`, `demos.html`, `cv.html`, `contact.md`: main public pages
- `blog.html`, `_posts/`: unpublished technical notes under review
- `_layouts/`, `_includes/`: shared templates
- `public/`: theme assets and custom styles
- `files/`: PDFs and images

## Teaching materials

Teaching resources are driven by `_data/teaching.yml` and rendered by
`teaching.html`. Public PDFs live under `files/teaching/`.

The STAT 131 Spring 2026 Notability materials must be exported from Notability
as PDFs before publication. Raw `.note` packages are not committed or linked
from the public site.

```bash
# 1. Export approved Notability notes as PDFs into a local staging folder.
#    This folder is gitignored.
mkdir -p local_teaching_exports/stat131-spring26-pdf

# 2. Validate, copy, and register the curated public subset.
python3 scripts/prepare_stat131_spring26_materials.py \
  --source-dir local_teaching_exports/stat131-spring26-pdf \
  --apply

# 3. Verify before committing.
python3 scripts/check_site_integrity.py
bundle exec jekyll build --trace
```

The intake script creates a separate
`STAT 131: Probability Theory - Spring 2026 Section Materials` entry instead of
mixing these files into the broader STAT 131 archive. It excludes likely private
or restricted files such as names, login notes, assessment solutions, templates,
and textbook copies.

## CV source and PDF publishing

The website CV is maintained from LaTeX source and published as a tracked PDF.

- Source: `cv/antonio_deleon_cv.tex`
- Canonical website PDF: `files/cv/antonio-deleon-cv.pdf`
- CV page link: `cv.html`

To update the CV:

```bash
# 1. Edit the LaTeX source.
$EDITOR cv/antonio_deleon_cv.tex

# 2. Render the website PDF.
scripts/render_cv.sh

# 3. Verify the committed PDFs match the source.
scripts/render_cv.sh --check
```

`scripts/render_cv.sh` uses `latexmk`, `pdflatex`, or `tectonic`, in that order. The GitHub Actions workflow `.github/workflows/render_cv_pdf.yml` can also render and commit the PDF from `main` when the CV source changes, or from a manual dispatch.

## CRAN package metadata

The `exdqlm` version shown on the website is stored in `_data/cran_packages.yml` and read through Jekyll/Liquid. The same CRAN version is also reflected in the LaTeX CV source.

To refresh the metadata manually:

```bash
python3 scripts/update_cran_package_metadata.py
scripts/render_cv.sh
scripts/render_cv.sh --check
```

The scheduled GitHub Actions workflow `.github/workflows/update_cran_package_metadata.yml` checks CRAN daily. It updates `_data/cran_packages.yml`, updates the CV source, renders the website CV PDF, and commits only when CRAN publishes a new package version or publication date.

## San Lorenzo River live USGS plot

The demos page includes a client-side Plotly chart of USGS instantaneous values for the San Lorenzo River (site 11160500). It is fully static and runs in the browser, with a mode toggle for stage or discharge.

- **Page location:** `demos.html` (Live Research Displays).
- **Container class:** `.usgs-iv-plot`.
- **Client script:** `public/js/sanlorenzo_flow.js`.
- **Plotting library:** Plotly (pinned CDN version in `demos.html`).
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
- `data-observation-stale-hours` (warning threshold for delayed USGS observations; default `6`)
- `data-forecast-stale-hours` (warning threshold for delayed forecast-overlay JSON; default `36`)
- `data-log-y` (`true`/`false` to enable a log-scale y-axis)
- `data-title` (optional label for accessibility)
- `data-ylabel` (base Y-axis label; units are appended automatically when available)
- `data-y-min`, `data-y-max` (optional fixed Y-axis range)
- `data-threshold-minor`, `data-threshold-moderate`, `data-threshold-major` (horizontal threshold lines + shaded regions)
- `data-forecast-url` (optional forecast overlay JSON; the site uses the `live-data` branch raw URL in production)
- `data-forecast-fallback-url` (optional bundled JSON fallback if the live-data request fails)
- `data-qdesn-url` (optional QDESN overlay JSON; currently disabled on the site; omit to keep it off)
- `data-flood-minor-cfs`, `data-flood-moderate-cfs`, `data-flood-major-cfs` (discharge-only thresholds; optional)

### Forecast overlay (NWS/NWM)

The plot can overlay forecast guidance from a JSON artifact published by scheduled automation:

- **Live artifact:** `assets/data/forecasts/big_trees_latest.json` on the `live-data` branch
- **Bundled fallback:** `assets/data/forecasts/big_trees_latest.json` on `main`
- **Update script:** `scripts/update_big_trees_forecast.sh`
- **Publish helper:** `scripts/publish_live_data_artifacts.sh`
- **Included series:** JSON may include NWPS analysis/short deterministic plus NWM medium/long quantiles (`p10/p50/p90`). The medium range may fall back to `medium_range_blend` when the direct medium-range series is unavailable.
- **Plot overlay behavior:** USGS observed discharge remains the base trace; the browser overlays available NWS short-range guidance and medium/long `p10-p90` bands when present.
- **Browser guard:** live and fallback forecast JSON are fetched with cache-busting. The browser prefers a fresh usable overlay and warns when observations or forecast guidance are delayed instead of silently showing stale data.
- **Unit harmonization:** the forecast JSON stores streamflow in `ft3/s` (cfs). The browser also normalizes `cfs`/`cms` labels and converts any forecast overlay to the observed USGS discharge axis before plotting.
- **TODO:** HEFS ensembles once location_id lookup is resolved
- **Fallback behavior:** if `_sandbox/nws_ensemble_point` is absent, updater builds JSON directly from NOAA NWPS APIs.
- **Ops guard:** stale fallback is disabled in scheduled CI. If `BIG_TREES_FORECAST_ALLOW_STALE_ON_ERROR=1` is set manually, fallback still exits nonzero by default so stale data is not reported as a successful refresh.

To refresh the bundled forecast JSON locally:

```bash
scripts/update_big_trees_forecast.sh
python3 scripts/check_forecast_assets.py \
  --streamflow assets/data/forecasts/big_trees_latest.json \
  --max-age-hours 36
python3 scripts/check_usgs_plot_health.py \
  --forecast-json assets/data/forecasts/big_trees_latest.json
```

If the live-data request fails, the page tries the bundled fallback. If both are missing, the plot still renders observations only and logs a console warning.

### QDESN overlay (median + 95% CI)

The QDESN discharge overlay is currently disabled on the site and the scheduled workflow is off. The artifacts and updater remain in the repo for future re-enable.

## GEFS forecast panel (new, additive)

The demos page includes a second panel for GEFS point forecasts (precipitation + soil moisture) near Big Trees.

- **Panel container:** `demos.html` (`.gefs-forecast-panel`)
- **Client script:** `public/js/gefs_forecast_panel.js`
- **Live artifact:** `assets/data/forecasts/gefs_big_trees_latest.json` on the `live-data` branch
- **Bundled fallback:** `assets/data/forecasts/gefs_big_trees_latest.json` on `main`
- **Pipeline source:** `_sandbox/gefs_point_pipeline`
- **Update script:** `scripts/update_big_trees_gefs_forecast.sh`
- **Publish helper:** `scripts/publish_live_data_artifacts.sh`
- **Scheduled workflow:** `.github/workflows/update_gefs_forecast.yml` (3 times/day at `01:20`, `09:20`, and `17:20` UTC, aligned to completed GEFS cycles)

Behavior:

- Fetches `gefs_big_trees_latest.json` from the `live-data` branch and falls back to the bundled site copy if needed
- Renders two Plotly charts:
  - APCP band (`p10-p90`) + `p50` + mean
  - SOILW depth-level medians (`p50`) with optional uncertainty bands
- Adds observed daily climate context plus retrospective context from prior GEFS cycles, shown over a fixed 20-day pre-forecast window
- Loads the observed retrospective window from `climate_daily_ppt_soil.csv` when that CSV is fresher or more complete than the GEFS JSON payload
- Displays metadata and freshness warning if stale
- Displays a context-quality warning if the forecast is current but the rolling GEFS analysis context is incomplete
- Degrades gracefully when JSON is missing/invalid

GEFS JSON includes optional retrospective metadata used by the panel:

- `observation_window_days` (default `20`)
- `retrospective.start_utc`, `retrospective.end_utc`
- `retrospective.precip.<level>.{p10,p50,p90,mean}`
- `retrospective.soil_moisture.<level>.p50`
- `gefs_analysis_context.precip_f003_proxy.<level>` (GEFS cycle-history analysis proxy, plotted)
- `gefs_analysis_context.soil_f000.<level>` (GEFS cycle-history analysis, plotted)
- `observed_retrospective.daily_avg_ppt` (observed daily precipitation, plotted)
- `observed_retrospective.daily_avg_soil_ERA5` and available NWM soil fields (observed daily soil context, plotted)
- `gefs_analysis_context_summary` and `quality_warnings` describe whether the rolling context is complete enough for display
- Plot units are harmonized by panel logic (`APCP` in mm water-equivalent; `SOILW` in m3/m3)
- Scheduled GEFS exports enable observed retrospective context by default from the latest `live-data` climate CSV, with a repository-root fallback
- The browser also has `data-observed-csv-url` / `data-observed-fallback-csv-url` support so observed PRISM/ERA5/NWM context can be reconstructed from the combined CSV at render time
- The exporter still supports GEFS-only context when run manually without `--include-observed-retrospective`
- Exporter uses a history-scan guard: skips git-history backfill when prior 20-day GEFS context is already complete
- GEFS cycle-history context may be limited after a stale period; observed daily context keeps the pre-forecast window populated while cycle context accumulates or is backfilled.

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

The USGS discharge panel in `public/js/sanlorenzo_flow.js` supports optional overlays:

- NWS/NWM forecast overlay (`data-forecast-url`)
- QDESN fit overlay (`data-qdesn-url`, currently disabled)

## Climate Data Automation (PRISM + ERA5 + NWM retro soil)

This repo includes a cron-safe climate stack that keeps canonical point series and a merged table used as observed context for the GEFS demo:

- `prism_precipitation_santa_cruz_1987_2023.csv`
- `soil_moisture_data/soil_moisture_big_trees_daily_avg_1987_2023.csv`
- `soil_moisture_data/nwm_soil_moisture_big_trees_daily_1987_present.csv`
- `climate_daily_ppt_soil.csv`
- `climate_series_status.csv`

`climate_series_status.csv` is the source of truth for provider coverage. PRISM and ERA5 are expected to trail real time by provider lag. The tracked NWM retrospective v3.0 source is historical and currently provider-limited to 2023 data; the wrapper rechecks upstream availability periodically instead of attempting a heavy full extraction on every scheduled run.

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

Install cron (default every 8h at minute 17):

```bash
scripts/install_climate_update_cron.sh
```

Run one manual cycle:

```bash
scripts/run_climate_updates_cron.sh
```

Logs are written under `logs/climate_updates/` and `latest.log` points to the newest run log.

The local climate and site-update runners select a compatible Python `>= 3.9` before calling the climate scripts. This matters on servers where cron's default `/usr/bin/python3` may be older than the interactive shell Python.

NWM retrospective controls:

- `NWM_RETRO_PROVIDER_RECHECK_DAYS` controls how often the wrapper reruns the heavy extraction when the prior metadata shows the upstream retrospective source is provider-limited before the target date. Default: `30`.
- `NWM_RETRO_FORCE_REFRESH=1` bypasses the provider-limited skip and forces a refresh attempt.

### GitHub Actions Automation

The repo supports fully hosted forecast and climate refresh on GitHub Actions without spending Netlify production-deploy credits. Scheduled data jobs publish artifacts to the `live-data` branch; `main` remains the website branch that Netlify deploys.

- `.github/workflows/update_forecast.yml`
  - cadence: every 4 hours at minute 20 UTC (`20 */4 * * *`) plus manual `workflow_dispatch`
  - bounded to 30 minutes so upstream API stalls fail clearly instead of consuming long runner time
  - publishes to `live-data`:
    - `assets/data/forecasts/big_trees_latest.json`
  - validates `generated_at_utc`, units, and core analysis/short-range series before publishing
  - accepts partial streamflow artifacts when medium/long guidance is unavailable, but the browser labels that state
  - race guards:
    - hard sync to latest `origin/main` before processing
    - rebase-safe live-data publish with retry support
    - publish helper refuses to replace a newer live-data JSON with an older candidate

- `.github/workflows/update_climate_series.yml`
  - cadence: daily at `06:17` UTC (`17 6 * * *`) plus manual `workflow_dispatch`
  - bounded to 120 minutes because PRISM, ERA5, and NWM archive checks can be provider-lagged or slow
  - publishes to `live-data`:
    - `prism_precipitation_santa_cruz_1987_2023.csv`
    - `soil_moisture_data/soil_moisture_big_trees_daily_avg_1987_2023.csv`
    - `soil_moisture_data/nwm_soil_moisture_big_trees_daily_1987_present.csv`
    - `soil_moisture_data/nwm_soil_moisture_big_trees_daily_1987_present.meta.json`
    - `climate_series_status.csv`
    - `climate_daily_ppt_soil.csv`
  - incremental PRISM/ERA5 updaters probe backward to the latest available provider date instead of failing the whole run on a too-recent request
  - routine climate refreshes are data-only `live-data` commits, so they should not trigger Netlify production deploys

- `.github/workflows/update_gefs_forecast.yml`
  - cadence: `01:20`, `09:20`, `17:20` UTC (`20 1,9,17 * * *`)
  - bounded to 120 minutes because full GEFS extraction is heavier than the streamflow refresh
  - publishes to `live-data`:
    - `assets/data/forecasts/gefs_big_trees_latest.json`
  - caches pip dependencies and performs a latest-cycle freshness precheck before the heavy full refresh
  - fail-fast checks in `scripts/update_big_trees_gefs_forecast.sh` ensure:
    - latest init is not stale
    - current precipitation and soil-moisture forecast series exist
    - observed retrospective precipitation or soil context is present
    - 20-day GEFS analysis context coverage is reported as `ok` or `limited`; limited context is a warning, not a blocker for publishing a current forecast
  - race guards:
    - hard sync to latest `origin/main` before processing
    - rebase-safe live-data publish with retry support
    - publish helper refuses stale or older JSON artifacts when `LIVE_DATA_MAX_AGE_HOURS` is set

- `.github/workflows/backfill_gefs_analysis_context.yml` (manual)
  - one-time/manual bootstrap for GEFS cycle-analysis context
  - backfills missing `f003` precip proxy and `f000` soil markers over a target window (default 20 days)
  - rewrites latest full GEFS payload at the end so forecast panel remains complete

- `.github/workflows/update_qdesn_fit.yml` (manual)
  - disabled by default from the homepage, but kept for future QDESN overlay refreshes
  - updates and commits:
    - `assets/data/forecasts/big_trees_qdesn_latest.json`
  - uses the same hard-sync and rebase-safe push pattern as the other generated-asset workflows

- `.github/workflows/verify_site_build.yml`
  - runs `bundle exec jekyll build --trace` on pushes to `main` and on manual dispatch
  - ignores generated data-only changes so GitHub Actions does not spend build time on non-site edits
  - catches site-build regressions in GitHub Actions before Netlify production publishes stale pages

Netlify is protected by `scripts/netlify-ignore-build.sh`, wired through `netlify.toml`. The script skips production builds when the only changed files are generated data artifacts. Website code/content/CV changes still build normally.

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
localStorage.removeItem('usgs-iv:11160500:00060:P20D:v4');
```

### Troubleshooting

- **CORS errors:** USGS normally allows cross-origin requests. If blocked, test the endpoint directly in a browser to confirm availability.
- **Rate limiting (403/429):** The script backs off and shows a warning. Increase `data-refresh-min` if needed.
- **Offline:** The status line reports offline and retries when the connection returns.
- **Unexpected response:** A schema or JSON error will show a warning; verify the endpoint.
- **Threshold units:** Thresholds must match the parameter units. NOAA flood thresholds are stage (ft); for discharge (`00060`), use rating-derived cfs thresholds.
