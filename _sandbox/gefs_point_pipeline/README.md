# GEFS Point Pipeline (Sandbox)

Pipeline for GEFS point extraction at USGS `11160500` (Big Trees) with:

- Latest complete-cycle discovery
- Multi-product field resolution (`atmos.5`, `atmos.5b`)
- Multi-layer SOILW extraction (4 target depths)
- QC fail-fast and schema validation
- Idempotent publish + strict retention hygiene
- Web JSON export for homepage panel

## Setup

```bash
cd _sandbox/gefs_point_pipeline
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run Profiles

`run_latest.py` supports explicit profiles:

- `full` (default): production scope (`31` members, leads `0..240 step 3`)
- `smoke`: reduced scope for quick validation

Compatibility flags:

- `--smoke` is retained and maps to profile `smoke`
- `--profile full|smoke` is explicit and preferred

Examples:

```bash
# Smoke profile
python run_latest.py --smoke --log-level INFO

# Full profile
python run_latest.py --profile full --log-level INFO
```

Common options:

- `--force`: overwrite existing run directory for same init/profile
- `--init-time 2026-02-24T00:00:00Z`: force cycle instead of discovery
- `--point-id big_trees`: location key from `config/points.yaml`

## Output Layout

Full runs:

- `data/_sandbox_gefs/runs/<YYYYMMDD_HH>/`

Smoke runs:

- `data/_sandbox_gefs/smoke_runs/<YYYYMMDD_HH>/`

Per run:

- `point_member.parquet`
- `point_ens_summary.parquet`
- `manifest.json`
- `run.log`

Full profile only:

- `data/_sandbox_gefs/runs/latest_init.txt`
- `data/_sandbox_gefs/runs/latest` symlink (best effort)

## Historical Backfill (Point-Only, No Raw Retention)

Use `run_backfill.py` to build compact per-cycle point history across many cycles.

Pilot benchmark for last 7 days:

```bash
python run_backfill.py --pilot-days 7 --workers 2 --cycle-max-workers 2
```

Fast smoke benchmark (same window logic, reduced members/leads):

```bash
python run_backfill.py --pilot-days 7 --run-profile smoke --workers 2 --cycle-max-workers 2
```

Full historical build (AWS GEFS availability window to latest complete cycle):

```bash
python run_backfill.py \
  --start-init 2020-10-01T00:00:00Z \
  --workers 4 \
  --cycle-max-workers 2
```

Retry only failed cycles in a window:

```bash
python run_backfill.py \
  --start-init 2020-10-01T00:00:00Z \
  --retry-failed-only
```

Note: for `source_priority: ["aws"]`, historical GEFS point backfill is clamped to
`2020-10-01T00:00:00Z` to avoid unavailable pre-publication cycles.

Artifacts are written under `data/_sandbox_gefs/history/`:

- `cycles/<YYYYMMDD_HH>/` per-cycle compact parquet + manifest
- `state/backfill_status.json` live progress snapshot
- `state/<run_id>_benchmark.json` benchmark/timing summary
- `logs/<run_id>_failures.jsonl` structured failures for retry/debug
- `state/backfill.lock` concurrency lock metadata

Backfill runs are resumable:

- existing successful cycle directories are skipped by default
- use `--force` to re-run all cycles in the target window
- `--retry-failed-only` reprocesses only `.failed_*` cycles
- stale `.tmp_*` dirs are cleaned before each run (default `--cleanup-stale-tmp-hours 6`)
- lock protection prevents overlapping runs (`--wait-for-lock` optional)

## Daemon Mode (No Live Monitoring Needed)

Use `run_backfill_daemon.py` to keep the history continuously updated in the background:

```bash
python run_backfill_daemon.py \
  --full-start-init 2020-10-01T00:00:00Z \
  --incremental-pilot-days 3 \
  --sleep-seconds 21600 \
  --workers 2 \
  --cycle-max-workers 4
```

Daemon state artifacts:

- `data/_sandbox_gefs/history/state/daemon_status.json`
- `data/_sandbox_gefs/history/state/daemon_runs.jsonl`
- `data/_sandbox_gefs/history/state/backfill_status.json`
- `data/_sandbox_gefs/history/state/daemon.lock` (single-instance lock metadata)
- `data/_sandbox_gefs/history/state/daemon.pid`

Operational wrappers from repo root:

- `scripts/start_gefs_history_daemon.sh`
- `scripts/stop_gefs_history_daemon.sh`
- `scripts/status_gefs_history_daemon.sh`
- `scripts/install_gefs_history_daemon_cron.sh` (`@reboot` + `*/30` watchdog)
- start wrapper prefers detached `tmux` session `gefs_history_daemon`

Retention controls (in `config/gefs.yaml`):

- `runtime.keep_cycles` (full successful runs, default `1`)
- `runtime.keep_smoke_runs` (smoke successful runs)
- `runtime.keep_failed_runs` (bounded `.failed_*` retention)

## Manifest Contract Highlights

`manifest.json` includes:

- `run_profile`
- `resolved_fields`
- `resolved_products`
- `resolved_soil_levels`
- `missing_expected_levels`
- `bytes_downloaded`
- `record_counts_by_variable_level`
- `rows_expected`
- `qc` check list with pass/fail details

## Web Export

Export latest successful **full** run to web JSON:

```bash
python export_latest_web_json.py
```

Default output:

- `data/_sandbox_gefs/web/gefs_big_trees_latest.json`

Payload includes:

- metadata (`generated_at_utc`, `site_id`, `init_time_utc`, `member_count`, `schema_version`)
- `precip` quantile/mean series by level
- `soil_moisture` quantile/mean series by depth level
- `missing_levels`

## End-to-End Update Script

From repo root:

```bash
scripts/update_big_trees_gefs_forecast.sh
```

This script:

1. Runs full profile pipeline.
2. Exports latest web JSON.
3. Copies tracked asset to `assets/data/forecasts/gefs_big_trees_latest.json`.

## Scheduler

GitHub Actions workflow:

- `.github/workflows/update_gefs_forecast.yml`
- schedule: every 3 hours (`0 */3 * * *`)
- overlap protection via `concurrency`
- commits only the GEFS asset when content changed
