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
- **Update script:** `scripts/update_big_trees_forecast.sh` (runs the sandbox extractor as needed)
- **Included series:** NWPS analysis/short (deterministic) + NWM medium/long ensembles (p10/p50/p90)
- **TODO:** HEFS ensembles once location_id lookup is resolved

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

Panel override:

- `data-observation-window-days` (defaults to `20` if omitted)

The existing USGS discharge panel logic in `public/js/sanlorenzo_flow.js` remains unchanged.

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
