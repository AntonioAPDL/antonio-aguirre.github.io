from __future__ import annotations

import dataclasses
import datetime as dt
import json
import logging
import math
import os
import shutil
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from .config import PipelineConfig, PointConfig, config_fingerprint
from .cycle import CycleSelection, cycle_tag, discover_latest_complete_cycle
from .extract import PointExtraction, extract_point_value
from .herbie_adapter import make_herbie, xarray_subset
from .inventory import ResolvedField, resolve_product_and_fields
from .qc import run_qc
from .schema import validate_member_schema, validate_summary_schema
from .storage import (
    build_ensemble_summary,
    ensure_dir,
    prune_failed_runs,
    prune_old_runs,
    publish_run,
    read_manifest,
    update_latest_pointer,
    write_run_outputs,
)


LOG = logging.getLogger("gefs_point_pipeline")
PROFILES = {"full", "smoke"}


@dataclass(frozen=True)
class RunOptions:
    repo_root: Path
    force: bool
    smoke: bool
    run_profile: str
    explicit_init_time_utc: Optional[dt.datetime]


@dataclass(frozen=True)
class RunResult:
    status: str
    run_profile: str
    init_time_utc: dt.datetime
    run_tag: str
    run_dir: Path
    manifest_path: Path


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def parse_init_time(value: Optional[str]) -> Optional[dt.datetime]:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def setup_logging(level: str) -> None:
    numeric = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _resolve_path(repo_root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    return (repo_root / path).resolve()


def _retry_call(func, retries: int, backoff_sec: float) -> Any:
    last: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            return func()
        except Exception as exc:
            last = exc
            if attempt >= retries:
                break
            wait = backoff_sec * (2 ** (attempt - 1))
            LOG.warning("Retry %s/%s after error: %s", attempt, retries, exc)
            import time

            time.sleep(wait)
    if last is None:
        raise RuntimeError("retry_call reached invalid state")
    raise last


def _effective_profile(options: RunOptions) -> str:
    if options.smoke:
        return "smoke"
    profile = (options.run_profile or "full").strip().lower()
    if profile not in PROFILES:
        raise ValueError(f"run_profile must be one of {sorted(PROFILES)}")
    return profile


def _build_execution_scope(
    cfg: PipelineConfig,
    profile: str,
) -> Tuple[List[str], List[int]]:
    members = list(cfg.members)
    leads = cfg.leads.values()
    if profile == "smoke":
        members = members[: min(3, len(members))]
        leads = [lead for lead in leads if lead <= 12]
        if not leads:
            leads = cfg.leads.values()[: min(3, len(cfg.leads.values()))]
    return members, leads


def _runs_root_for_profile(cfg: PipelineConfig, repo_root: Path, profile: str) -> Path:
    if profile == "smoke":
        return _resolve_path(repo_root, cfg.output.smoke_runs_root)
    return _resolve_path(repo_root, cfg.output.runs_root)


def _determine_cycle(
    cfg: PipelineConfig,
    options: RunOptions,
) -> CycleSelection:
    if options.explicit_init_time_utc is not None:
        return CycleSelection(
            init_time_utc=options.explicit_init_time_utc,
            details={
                "mode": "explicit",
                "init_time_utc": options.explicit_init_time_utc.isoformat(),
            },
        )
    selected = discover_latest_complete_cycle(cfg, _utcnow())
    return selected


def _normalize_xarray_result(obj: Any) -> List[Any]:
    if isinstance(obj, list):
        return obj
    return [obj]


def _close_datasets(datasets: Iterable[Any]) -> None:
    seen: set[int] = set()
    for ds in datasets:
        obj_id = id(ds)
        if obj_id in seen:
            continue
        seen.add(obj_id)
        if hasattr(ds, "close"):
            ds.close()


def _dataset_matches_field(ds: Any, field: ResolvedField) -> bool:
    canonical = field.canonical_name.upper()
    var_names = [str(name).upper() for name in list(ds.data_vars)]
    canonical_shortname_map = {
        "APCP": {"APCP", "TP"},
        "SOILW": {"SOILW"},
    }
    expected_shortnames = canonical_shortname_map.get(canonical, {canonical})

    for name in list(ds.data_vars):
        da = ds[name]
        var_name = str(name).upper()
        short_name = str(da.attrs.get("GRIB_shortName", "")).upper()
        long_name = str(da.attrs.get("GRIB_name", "")).upper()
        cf_name = str(da.attrs.get("GRIB_cfVarName", "")).upper()
        if var_name in expected_shortnames:
            return True
        if short_name in expected_shortnames:
            return True
        if canonical in long_name or canonical in cf_name:
            return True

    # Fallbacks for common alias fields in cfgrib.
    if canonical == "APCP" and any(name in {"TP", "APCP"} for name in var_names):
        return True
    if canonical == "SOILW" and any("SOILW" in name for name in var_names):
        return True

    # Last-resort canonical containment check.
    return any(canonical in var for var in var_names)


def _dataset_for_field(datasets: List[Any], field: ResolvedField) -> Optional[Any]:
    matches = [ds for ds in datasets if _dataset_matches_field(ds, field)]
    if not matches:
        return None
    if len(matches) == 1:
        return matches[0]
    return matches[0]


def _local_grib_path(ds: Any) -> str:
    return str(ds.attrs.get("local_grib", "") or "")


def _collect_bytes(paths: Iterable[str], seen_sizes: Dict[str, int]) -> None:
    for path in paths:
        if not path or path in seen_sizes:
            continue
        try:
            seen_sizes[path] = int(os.path.getsize(path))
        except OSError:
            continue


def _field_lead_count(field: ResolvedField, leads: Sequence[int]) -> int:
    if field.canonical_name.upper() == "APCP" and 0 in leads:
        return len(leads) - 1
    return len(leads)


def _expected_row_count(fields: Sequence[ResolvedField], members: Sequence[str], leads: Sequence[int]) -> int:
    per_member = sum(_field_lead_count(field, leads) for field in fields)
    return int(per_member * len(members))


def _record_counts_by_variable_level(df: pd.DataFrame) -> Dict[str, int]:
    grouped = df.groupby(["variable", "level"], dropna=False).size().reset_index(name="rows")
    out: Dict[str, int] = {}
    for row in grouped.itertuples(index=False):
        key = f"{row.variable}|{row.level}"
        out[str(key)] = int(row.rows)
    return out


def _resolved_field_signature(fields: Sequence[ResolvedField]) -> List[str]:
    signature = [
        f"{field.product}|{field.canonical_name}|{field.level_label}|{field.search_string}"
        for field in fields
    ]
    return sorted(signature)


def _is_compatible_success_run(
    manifest: Dict[str, Any],
    run_profile: str,
    members: Sequence[str],
    leads: Sequence[int],
    fields: Sequence[ResolvedField],
) -> bool:
    if manifest.get("status") != "success":
        return False
    if str(manifest.get("run_profile", "full")) != run_profile:
        return False
    if list(manifest.get("members_requested", [])) != list(members):
        return False
    if list(manifest.get("lead_hours_requested", [])) != list(leads):
        return False

    manifest_fields = manifest.get("resolved_fields") or manifest.get("fields") or []
    existing = []
    for field in manifest_fields:
        existing.append(
            f"{field.get('product','')}|{field.get('canonical_name','')}|"
            f"{field.get('level_label', field.get('level',''))}|{field.get('search_string','')}"
        )
    return sorted(existing) == _resolved_field_signature(fields)


def _extract_member_lead(
    init_time_utc: dt.datetime,
    member: str,
    lead_hour: int,
    fields: Sequence[ResolvedField],
    cfg: PipelineConfig,
    point: PointConfig,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    rows: List[Dict[str, Any]] = []
    bytes_by_file: Dict[str, int] = {}
    valid_time = init_time_utc + dt.timedelta(hours=int(lead_hour))

    active_fields = [
        field
        for field in fields
        if not (field.canonical_name.upper() == "APCP" and int(lead_hour) == 0)
    ]
    fields_by_product: Dict[str, List[ResolvedField]] = {}
    for field in active_fields:
        fields_by_product.setdefault(field.product, []).append(field)

    for product, product_fields in fields_by_product.items():
        combined_search = "|".join(sorted({field.search_string for field in product_fields}))
        handle = make_herbie(
            init_time_utc=init_time_utc,
            model=cfg.model,
            product=product,
            member=member,
            fxx=lead_hour,
            source_priority=cfg.source_priority,
        )
        try:
            result = _retry_call(
                lambda: xarray_subset(handle, combined_search),
                retries=cfg.runtime.retries,
                backoff_sec=cfg.runtime.retry_backoff_sec,
            )
            datasets = _normalize_xarray_result(result)
            _collect_bytes((_local_grib_path(ds) for ds in datasets), bytes_by_file)
            for field in product_fields:
                matched_ds = _dataset_for_field(datasets, field)
                if matched_ds is None:
                    raise ValueError(
                        f"No dataset matched field {field.canonical_name}:{field.level_label}"
                    )
                point_value: PointExtraction = extract_point_value(
                    dataset=matched_ds,
                    canonical_name=field.canonical_name,
                    target_lat=point.lat,
                    target_lon=point.lon,
                    search_max_km=point.search_max_km,
                    level_label=field.level_label,
                )
                rows.append(
                    {
                        "site_id": point.usgs_site,
                        "init_time_utc": init_time_utc,
                        "lead_hours": int(lead_hour),
                        "valid_time_utc": valid_time,
                        "member": member,
                        "variable": field.canonical_name,
                        "level": field.level_label,
                        "value": point_value.value,
                        "units": point_value.units,
                        "grid_lat": point_value.grid_lat,
                        "grid_lon": point_value.grid_lon,
                        "distance_km": point_value.distance_km,
                        "used_fallback_point": point_value.used_fallback_point,
                        "product": field.product,
                        "source": "aws",
                        "search_string": field.search_string,
                        "descriptor": field.descriptor,
                        "file_ref": _local_grib_path(matched_ds),
                        "error": "",
                    }
                )
        except Exception as exc:
            for field in product_fields:
                rows.append(
                    {
                        "site_id": point.usgs_site,
                        "init_time_utc": init_time_utc,
                        "lead_hours": int(lead_hour),
                        "valid_time_utc": valid_time,
                        "member": member,
                        "variable": field.canonical_name,
                        "level": field.level_label,
                        "value": math.nan,
                        "units": "",
                        "grid_lat": math.nan,
                        "grid_lon": math.nan,
                        "distance_km": math.nan,
                        "used_fallback_point": False,
                        "product": field.product,
                        "source": "aws",
                        "search_string": field.search_string,
                        "descriptor": field.descriptor,
                        "file_ref": "",
                        "error": str(exc),
                    }
                )
        finally:
            if "datasets" in locals():
                _close_datasets(datasets)

    return rows, bytes_by_file


def _extract_all_rows(
    init_time_utc: dt.datetime,
    members: Sequence[str],
    leads: Sequence[int],
    fields: Sequence[ResolvedField],
    cfg: PipelineConfig,
    point: PointConfig,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    tasks = [(member, lead) for member in members for lead in leads]
    rows: List[Dict[str, Any]] = []
    bytes_by_file: Dict[str, int] = {}

    with ThreadPoolExecutor(max_workers=max(1, cfg.runtime.max_workers)) as pool:
        future_map = {
            pool.submit(
                _extract_member_lead, init_time_utc, member, lead, fields, cfg, point
            ): (member, lead)
            for member, lead in tasks
        }
        for future in as_completed(future_map):
            member, lead = future_map[future]
            try:
                task_rows, task_bytes = future.result()
                rows.extend(task_rows)
                for path, size in task_bytes.items():
                    bytes_by_file[path] = max(size, bytes_by_file.get(path, 0))
            except Exception as exc:
                LOG.error("Task failed for member=%s lead=%s: %s", member, lead, exc)
                valid_time = init_time_utc + dt.timedelta(hours=int(lead))
                for field in fields:
                    if field.canonical_name.upper() == "APCP" and int(lead) == 0:
                        continue
                    rows.append(
                        {
                            "site_id": point.usgs_site,
                            "init_time_utc": init_time_utc,
                            "lead_hours": int(lead),
                            "valid_time_utc": valid_time,
                            "member": member,
                            "variable": field.canonical_name,
                            "level": field.level_label,
                            "value": math.nan,
                            "units": "",
                            "grid_lat": math.nan,
                            "grid_lon": math.nan,
                            "distance_km": math.nan,
                            "used_fallback_point": False,
                            "product": field.product,
                            "source": "aws",
                            "search_string": field.search_string,
                            "descriptor": field.descriptor,
                            "file_ref": "",
                            "error": f"task_failure:{exc}",
                        }
                    )
    return rows, bytes_by_file


def _manifest_base(
    cfg: PipelineConfig,
    point: PointConfig,
    cycle: CycleSelection,
    run_profile: str,
    fields: Sequence[ResolvedField],
    members: Sequence[str],
    leads: Sequence[int],
    resolution: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "status": "running",
        "run_profile": run_profile,
        "schema_version": cfg.runtime.schema_version,
        "site_id": point.usgs_site,
        "point_id": point.point_id,
        "init_time_utc": cycle.init_time_utc.isoformat(),
        "members_requested": list(members),
        "lead_hours_requested": list(leads),
        "fields": [dataclasses.asdict(field) for field in fields],
        "resolved_fields": [dataclasses.asdict(field) for field in fields],
        "resolved_products": resolution.get("resolved_products", []),
        "resolved_soil_levels": resolution.get("resolved_soil_levels", []),
        "missing_expected_levels": resolution.get("missing_expected_levels", {}),
        "cycle_discovery": cycle.details,
        "inventory_resolution": resolution,
        "config_fingerprint": config_fingerprint(cfg, point),
    }


def _normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    typed = df.copy()
    typed["init_time_utc"] = pd.to_datetime(typed["init_time_utc"], utc=True)
    typed["valid_time_utc"] = pd.to_datetime(typed["valid_time_utc"], utc=True)
    typed["lead_hours"] = typed["lead_hours"].astype(int)
    typed["value"] = pd.to_numeric(typed["value"], errors="coerce")
    return typed.sort_values(["variable", "level", "member", "lead_hours"]).reset_index(drop=True)


def run_pipeline(
    cfg: PipelineConfig,
    point: PointConfig,
    options: RunOptions,
) -> RunResult:
    profile = _effective_profile(options)
    started = _utcnow()
    cycle = _determine_cycle(cfg, options)
    run_tag = cycle_tag(cycle.init_time_utc)

    runs_root = _runs_root_for_profile(cfg, options.repo_root, profile)
    ensure_dir(runs_root)
    run_dir = runs_root / run_tag
    manifest_path = run_dir / "manifest.json"

    members, leads = _build_execution_scope(cfg, profile)
    effective_cfg = cfg
    if profile == "smoke":
        effective_runtime = dataclasses.replace(
            cfg.runtime, require_member_count=len(members)
        )
        effective_cfg = dataclasses.replace(cfg, runtime=effective_runtime)

    fields, resolution = resolve_product_and_fields(effective_cfg, cycle.init_time_utc)
    existing_manifest = read_manifest(manifest_path)
    if (
        run_dir.exists()
        and not options.force
        and _is_compatible_success_run(existing_manifest, profile, members, leads, fields)
    ):
        LOG.info(
            "Run already exists and is successful for %s (profile=%s); skipping.",
            run_tag,
            profile,
        )
        return RunResult(
            status="skipped_existing",
            run_profile=profile,
            init_time_utc=cycle.init_time_utc,
            run_tag=run_tag,
            run_dir=run_dir,
            manifest_path=manifest_path,
        )

    overwrite_existing = options.force or run_dir.exists()
    if overwrite_existing and run_dir.exists():
        LOG.info("Replacing existing run directory for %s (profile=%s).", run_tag, profile)

    temp_dir = runs_root / f".tmp_{run_tag}_{uuid.uuid4().hex[:8]}"
    ensure_dir(temp_dir)
    logs: List[str] = []
    logs.append(f"run_started_utc={started.isoformat()}")
    logs.append(f"run_profile={profile}")
    logs.append(f"init_time_utc={cycle.init_time_utc.isoformat()}")
    logs.append(f"run_tag={run_tag}")
    logs.append(f"resolved_products={','.join(resolution.get('resolved_products', []))}")
    logs.append(f"members={','.join(members)}")
    logs.append(f"leads={','.join(str(x) for x in leads)}")

    base_manifest = _manifest_base(
        effective_cfg,
        point,
        cycle,
        run_profile=profile,
        fields=fields,
        members=members,
        leads=leads,
        resolution=resolution,
    )

    try:
        rows, bytes_by_file = _extract_all_rows(
            init_time_utc=cycle.init_time_utc,
            members=members,
            leads=leads,
            fields=fields,
            cfg=effective_cfg,
            point=point,
        )
        member_df = _normalize_dataframe(pd.DataFrame(rows))
        member_df = validate_member_schema(member_df, effective_cfg.runtime.schema_version)

        summary_df = build_ensemble_summary(member_df)
        summary_df = validate_summary_schema(summary_df, effective_cfg.runtime.schema_version)

        expected_rows = _expected_row_count(fields, members, leads)
        qc = run_qc(
            member_df,
            effective_cfg,
            expected_member_count=len(members),
            expected_rows=expected_rows,
            resolved_soil_levels=resolution.get("resolved_soil_levels", []),
            missing_expected_levels=resolution.get("missing_expected_levels", {}),
        )
        if not qc.get("pass", False):
            raise RuntimeError(f"QC failed: {json.dumps(qc, indent=2)}")

        bytes_downloaded = int(sum(bytes_by_file.values()))
        completed = _utcnow()

        manifest = dict(base_manifest)
        manifest.update(
            {
                "status": "success",
                "run_started_utc": started.isoformat(),
                "run_completed_utc": completed.isoformat(),
                "rows_member": int(len(member_df)),
                "rows_summary": int(len(summary_df)),
                "rows_expected": int(expected_rows),
                "nan_fraction": float(member_df["value"].isna().mean()),
                "error_rows": int((member_df["error"].astype(str) != "").sum()),
                "bytes_downloaded": bytes_downloaded,
                "downloaded_files_count": int(len(bytes_by_file)),
                "record_counts_by_variable_level": _record_counts_by_variable_level(member_df),
                "qc": qc,
                "deleted_runs": [],
                "deleted_failed_runs": [],
            }
        )

        logs.append(f"bytes_downloaded={bytes_downloaded}")
        logs.append("pruned_runs=pending")
        logs.append("pruned_failed_runs=pending")
        logs.append(f"run_completed_utc={completed.isoformat()}")

        write_run_outputs(temp_dir, member_df, summary_df, manifest, logs)
        publish_run(temp_dir, run_dir, force=overwrite_existing)

        deleted: List[str] = []
        deleted_failed: List[str] = []
        if profile == "full":
            update_latest_pointer(runs_root, effective_cfg.runtime.latest_pointer_name, run_tag)
            deleted = prune_old_runs(runs_root, effective_cfg.runtime.keep_cycles, protected=[run_tag])
            deleted_failed = prune_failed_runs(
                runs_root, keep_failed_runs=effective_cfg.runtime.keep_failed_runs
            )
        else:
            deleted = prune_old_runs(
                runs_root, effective_cfg.runtime.keep_smoke_runs, protected=[run_tag]
            )
            deleted_failed = prune_failed_runs(
                runs_root, keep_failed_runs=effective_cfg.runtime.keep_failed_runs
            )

        latest_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        latest_manifest["deleted_runs"] = deleted
        latest_manifest["deleted_failed_runs"] = deleted_failed
        manifest_path.write_text(json.dumps(latest_manifest, indent=2), encoding="utf-8")

        log_path = run_dir / "run.log"
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(f"pruned_runs={','.join(deleted) if deleted else 'none'}\n")
            fh.write(
                f"pruned_failed_runs={','.join(deleted_failed) if deleted_failed else 'none'}\n"
            )

        return RunResult(
            status="success",
            run_profile=profile,
            init_time_utc=cycle.init_time_utc,
            run_tag=run_tag,
            run_dir=run_dir,
            manifest_path=manifest_path,
        )
    except Exception as exc:
        failed_manifest = dict(base_manifest)
        failed_manifest.update(
            {
                "status": "failed",
                "run_started_utc": started.isoformat(),
                "run_failed_utc": _utcnow().isoformat(),
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }
        )
        logs.append(f"run_failed_utc={_utcnow().isoformat()}")
        logs.append(f"error={exc}")
        write_run_outputs(
            temp_dir,
            member_df=pd.DataFrame(),
            summary_df=pd.DataFrame(),
            manifest=failed_manifest,
            log_lines=logs,
        )
        failed_dir = runs_root / f".failed_{run_tag}_{uuid.uuid4().hex[:6]}"
        shutil.move(str(temp_dir), str(failed_dir))
        raise
