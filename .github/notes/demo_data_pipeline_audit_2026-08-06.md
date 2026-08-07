# Demo Data Pipeline Audit - 2026-08-06

## Scope

This note records the diagnosis and repair plan for stale data on the demos page:

- `assets/data/forecasts/big_trees_latest.json`
- `assets/data/forecasts/gefs_big_trees_latest.json`
- scheduled GitHub Actions publishing to the `live-data` branch
- browser behavior in `public/js/sanlorenzo_flow.js` and `public/js/gefs_forecast_panel.js`

## Provider Contract Checked

- NOAA NWPS is the correct source for official streamflow forecasts, stream observations, and National Water Model streamflow output:
  https://water.noaa.gov/about/api
- NWPS reach streamflow uses `series` values `analysis_assimilation`, `short_range`, `medium_range`, `long_range`, and `medium_range_blend`:
  https://api.water.noaa.gov/nwps/v1/docs/swagger.json
- NOAA GEFS is published on the AWS open-data bucket four times daily, every six hours:
  https://registry.opendata.aws/noaa-gefs/

## Findings

1. The frontend assets and provider URLs were reachable. USGS observations returned current data for site `11160500` with units `ft3/s`.
2. The public GEFS JSON on `live-data` was stale at `2026-05-24T18:32:40Z`.
3. The public streamflow JSON on `live-data` was stale at `2026-07-29T08:58:59Z`.
4. Scheduled workflows were active, but stale fallback was allowed and could produce green runs or noise commits without fresh data.
5. Both streamflow and GEFS updaters tried to write previous-live fallback files before creating the parent directory, so the intended previous-live baseline path failed.
6. The GEFS pipeline produced current forecasts, but validation rejected them when the 20-day retrospective analysis context was sparse. That made a current forecast unavailable because an auxiliary context layer was incomplete.
7. The streamflow builder could produce current analysis/short-range data while NWPS reach medium/long series timed out. The previous browser code ignored short-range guidance, so partial fresh payloads still looked like no forecast update.

## Repair Decisions

1. Treat stale fallback as a failure by default. A fallback may keep the deployed page from losing a file, but it must not be reported as a successful refresh.
2. Publish streamflow partials when core analysis/short-range guidance is current. Medium/long guidance remains preferred, but temporary NWPS reach failures should not block all current information.
3. Plot available short-range NWS guidance in the discharge panel.
4. Treat GEFS retrospective context completeness as a warning, not a blocker, when current forecast series are valid.
5. Add a publish-layer guard so `live-data` cannot be downgraded from a newer JSON to an older JSON.
6. Add a reusable freshness validator for scheduled workflows and manual operations.

## Reproducible Checks

```bash
python3 scripts/check_forecast_assets.py \
  --streamflow assets/data/forecasts/big_trees_latest.json \
  --max-age-hours 36

python3 scripts/check_forecast_assets.py \
  --gefs assets/data/forecasts/gefs_big_trees_latest.json \
  --max-age-hours 36
```

The scheduled workflows run these checks before publishing to `live-data`.
