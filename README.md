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

## San Lorenzo River live discharge plot

The home page includes a client-side Plotly chart of USGS instantaneous discharge data for the San Lorenzo River (site 11160500, parameter 00060). It is fully static and runs in the browser.

- **Page location:** `index.html` (Plot Section).
- **Container class:** `.usgs-iv-plot`.
- **Client script:** `public/js/sanlorenzo_flow.js`.
- **Plotting library:** Plotly (pinned CDN version in `index.html`).
- **Data source:** USGS NWIS IV JSON endpoint.

### Configuration via data attributes

The plot reads settings from HTML `data-*` attributes. Example:

```html
<div class="usgs-iv-plot"
     data-site="11160500"
     data-parameter="00060"
     data-period="P30D"
     data-refresh-min="15"
     data-timeout-sec="20"
     data-title="San Lorenzo River Discharge Flow"
     data-ylabel="Discharge">
  ...
</div>
```

Supported attributes:

- `data-site` (required), `data-parameter` (required)
- `data-period` (e.g., `P7D`, `P30D`, `P90D`)
- `data-refresh-min` (poll interval in minutes)
- `data-timeout-sec` (fetch timeout in seconds)
- `data-title` (optional label for accessibility)
- `data-ylabel` (base Y-axis label; units are appended automatically when available)
- `data-y-min`, `data-y-max` (fixed Y-axis range; defaults to 0–12 for log scale)
- `data-threshold-minor`, `data-threshold-major` (horizontal threshold lines + shaded regions)

The plot currently applies a log transform (`log(value + 1)`) to discharge values for stability.
If you want a different transform, edit `transformValue()` in `public/js/sanlorenzo_flow.js`.

Current flood threshold settings (discharge):
- Minor: ~6100 cfs (approximate discharge equivalent of 16.5 ft stage).
- Major: ~15000 cfs (approximate discharge at 21.76 ft stage).

### Cache behavior (localStorage)

The last successful data payload is cached in `localStorage` and used on load if not stale (max of 4x refresh interval or 30 minutes). If USGS is unavailable, the last known plot stays visible with a warning.

To clear the cache, open dev tools and remove keys starting with `usgs-iv:` or run:

```js
localStorage.removeItem('usgs-iv:11160500:00060:P30D:v1');
```

### Troubleshooting

- **CORS errors:** USGS normally allows cross-origin requests. If blocked, test the endpoint directly in a browser to confirm availability.
- **Rate limiting (403/429):** The script backs off and shows a warning. Increase `data-refresh-min` if needed.
- **Offline:** The status line reports offline and retries when the connection returns.
- **Unexpected response:** A schema or JSON error will show a warning; verify the endpoint.
- **Threshold units:** Thresholds are assumed to be in the same units as the USGS parameter. NOAA flood thresholds are typically stage (feet), while parameter `00060` is discharge (cfs). If you want exact discharge thresholds, derive them from the USGS rating curve or switch to parameter `00065` (gage height).
