#!/usr/bin/env python3
"""Lightweight repository integrity checks for the static site.

This is intentionally small and dependency-light. If PyYAML is available it
also parses YAML files; otherwise YAML validation is skipped with a warning.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]

CSV_SCHEMAS = {
    "prism_precipitation_santa_cruz_1987_2023.csv": {
        "date_col": "Date",
        "required": ["Date", "PRCP_mm"],
    },
    "soil_moisture_data/soil_moisture_big_trees_daily_avg_1987_2023.csv": {
        "date_col": "Date",
        "required": ["Date", "Daily_Avg_Soil_Moisture"],
    },
    "soil_moisture_data/nwm_soil_moisture_big_trees_daily_1987_present.csv": {
        "date_col": "Date",
        "required": ["Date", "NWM_SOIL_M", "NWM_SOIL_W"],
    },
    "climate_daily_ppt_soil.csv": {
        "date_col": "timestamp",
        "required": [
            "timestamp",
            "daily_avg_ppt",
            "daily_avg_soil_ERA5",
            "daily_avg_soil_NWM_SOIL_M",
            "daily_avg_soil_NWM_SOIL_W",
        ],
    },
    "climate_series_status.csv": {
        "date_col": "",
        "required": [
            "variable",
            "csv_path",
            "rows",
            "min_date",
            "max_date",
            "target_date",
            "target_reached",
            "lag_days",
            "value_column",
            "latest_value",
            "updated_at_utc",
        ],
    },
}

TEXT_SUFFIXES = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".R",
    ".sh",
    ".toml",
    ".xml",
    ".yml",
    ".yaml",
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def parse_date(raw: str) -> bool:
    try:
        datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def iter_content_files() -> Iterable[Path]:
    roots = [
        ROOT,
        ROOT / "_includes",
        ROOT / "_layouts",
        ROOT / "_posts",
    ]
    for directory in roots:
        for pattern in ("*.html", "*.md"):
            yield from directory.glob(pattern)


def check_csvs(errors: list[str], warnings: list[str]) -> None:
    for path_text, schema in CSV_SCHEMAS.items():
        path = ROOT / path_text
        if not path.exists():
            errors.append(f"missing CSV: {path_text}")
            continue
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
        columns = reader.fieldnames or []
        missing = [col for col in schema["required"] if col not in columns]
        if missing:
            errors.append(f"{path_text}: missing columns {missing}")
            continue
        date_col = schema["date_col"]
        if date_col:
            seen: set[str] = set()
            duplicates: list[str] = []
            invalid_dates: list[str] = []
            for row in rows:
                value = row.get(date_col, "")
                if value in seen:
                    duplicates.append(value)
                seen.add(value)
                if not parse_date(value):
                    invalid_dates.append(value)
            if duplicates:
                errors.append(f"{path_text}: duplicate {date_col} values {duplicates[:5]}")
            if invalid_dates:
                errors.append(f"{path_text}: invalid {date_col} values {invalid_dates[:5]}")
        if path_text == "climate_series_status.csv":
            for row in rows:
                if row.get("variable", "").startswith("soil_nwm"):
                    try:
                        lag_days = int(float(row.get("lag_days", "")))
                    except ValueError:
                        continue
                    if lag_days > 365:
                        warnings.append(
                            f"{path_text}: {row.get('variable')} is provider-limited/stale "
                            f"({lag_days} lag days)"
                        )


def check_json(errors: list[str]) -> None:
    for path in sorted((ROOT / "assets" / "data" / "forecasts").glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{rel(path)}: invalid JSON ({exc})")
            continue
        if not isinstance(data, dict):
            errors.append(f"{rel(path)}: top-level JSON must be an object")


def check_yaml(errors: list[str], warnings: list[str]) -> None:
    try:
        import yaml  # type: ignore
    except Exception:
        warnings.append("PyYAML is not installed; YAML parse checks skipped")
        return

    paths = [
        ROOT / "_config.yml",
        ROOT / "_data" / "colab_links.yml",
        ROOT / "_sandbox" / "gefs_point_pipeline" / "config" / "gefs.yaml",
        ROOT / "_sandbox" / "gefs_point_pipeline" / "config" / "points.yaml",
    ]
    paths.extend(sorted((ROOT / ".github" / "workflows").glob("*.yml")))
    for path in paths:
        if not path.exists():
            errors.append(f"missing YAML: {rel(path)}")
            continue
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{rel(path)}: invalid YAML ({exc})")


def check_local_asset_refs(errors: list[str]) -> None:
    ref_re = re.compile(r"""(?:href|src)=["'](/(?:assets|files|public)/[^"'?#]+)""")
    for path in iter_content_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in ref_re.finditer(text):
            url = match.group(1)
            if "{{" in url or "}}" in url:
                continue
            target = ROOT / url.lstrip("/")
            if not target.exists():
                errors.append(f"{rel(path)}: missing local asset reference {url}")


def check_conflict_markers(errors: list[str]) -> None:
    skip_parts = {".git", "_site", ".jekyll-cache", ".venv", "__pycache__"}
    marker_re = re.compile(r"(?m)^(<<<<<<< .+|=======$|>>>>>>> .+)$")
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        if any(part in skip_parts for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if marker_re.search(text):
            errors.append(f"{rel(path)}: possible conflict marker")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    check_csvs(errors, warnings)
    check_json(errors)
    check_yaml(errors, warnings)
    check_local_asset_refs(errors)
    check_conflict_markers(errors)

    for warning in warnings:
        print(f"[WARN] {warning}")
    if errors:
        for error in errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        return 1
    print("[OK] site integrity checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
