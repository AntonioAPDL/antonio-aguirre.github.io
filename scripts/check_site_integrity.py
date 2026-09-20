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
import shutil
import subprocess
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
    ".tex",
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
            continue
        if path.name == "big_trees_latest.json":
            if data.get("units") != ["ft3/s"]:
                errors.append(f"{rel(path)}: streamflow forecast units must be ['ft3/s']")


def check_yaml(errors: list[str], warnings: list[str]) -> None:
    try:
        import yaml  # type: ignore
    except Exception:
        warnings.append("PyYAML is not installed; YAML parse checks skipped")
        return

    paths = [
        ROOT / "_config.yml",
        ROOT / "_sandbox" / "gefs_point_pipeline" / "config" / "gefs.yaml",
        ROOT / "_sandbox" / "gefs_point_pipeline" / "config" / "points.yaml",
    ]
    paths.extend(sorted((ROOT / "_data").glob("*.yml")))
    paths.extend(sorted((ROOT / ".github" / "workflows").glob("*.yml")))
    for path in paths:
        if not path.exists():
            errors.append(f"missing YAML: {rel(path)}")
            continue
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{rel(path)}: invalid YAML ({exc})")


def check_research_metadata(errors: list[str]) -> None:
    try:
        import yaml  # type: ignore
    except Exception:
        return

    path = ROOT / "_data" / "research_outputs.yml"
    if not path.exists():
        errors.append("missing YAML: _data/research_outputs.yml")
        return
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        errors.append("_data/research_outputs.yml: top-level value must be an object")
        return

    for key, output in data.items():
        if not isinstance(output, dict):
            errors.append(f"_data/research_outputs.yml: {key} must be an object")
            continue
        arxiv_id = str(output.get("arxiv_id") or "").strip()
        if not arxiv_id:
            continue
        expected_arxiv = f"https://arxiv.org/abs/{arxiv_id}"
        expected_doi = f"https://doi.org/10.48550/arXiv.{arxiv_id}"
        if output.get("arxiv_url") != expected_arxiv:
            errors.append(
                f"_data/research_outputs.yml: {key}.arxiv_url must be {expected_arxiv}"
            )
        if output.get("doi_url") != expected_doi:
            errors.append(
                f"_data/research_outputs.yml: {key}.doi_url must be {expected_doi}"
            )

    qdesn = data.get("qdesn") or {}
    if not isinstance(qdesn, dict) or qdesn.get("arxiv_id") != "2609.17579":
        errors.append("_data/research_outputs.yml: qdesn must identify arXiv:2609.17579")
    if isinstance(qdesn, dict) and qdesn.get("status_label") != "arXiv preprint":
        errors.append("_data/research_outputs.yml: qdesn status must be 'arXiv preprint'")
    if isinstance(qdesn, dict):
        if qdesn.get("pdf_url") != "https://arxiv.org/pdf/2609.17579":
            errors.append("_data/research_outputs.yml: qdesn PDF URL is not canonical")
        if qdesn.get("html_url") != "https://arxiv.org/html/2609.17579v1":
            errors.append("_data/research_outputs.yml: qdesn HTML URL is not the published v1")


def check_teaching_data(errors: list[str]) -> None:
    try:
        import yaml  # type: ignore
    except Exception:
        return

    def validate_resources(course_id: object, resources: object, context: str) -> list[dict]:
        if not isinstance(resources, list):
            errors.append(f"_data/teaching.yml: course {course_id} {context} resources must be a list")
            return []
        valid_resources: list[dict] = []
        for resource_index, resource in enumerate(resources, start=1):
            if not isinstance(resource, dict):
                errors.append(
                    f"_data/teaching.yml: course {course_id} {context} resource "
                    f"{resource_index} must be an object"
                )
                continue
            valid_resources.append(resource)
            file_value = resource.get("file")
            url_value = resource.get("url")
            if bool(file_value) == bool(url_value):
                errors.append(
                    f"_data/teaching.yml: course {course_id} {context} resource "
                    f"{resource_index} must define exactly one of file or url"
                )
                continue
            if file_value:
                target = ROOT / str(file_value).lstrip("/")
                if not target.exists():
                    errors.append(f"_data/teaching.yml: missing teaching resource {file_value}")
            elif not str(url_value).startswith("https://"):
                errors.append(
                    f"_data/teaching.yml: course {course_id} {context} resource "
                    f"{resource_index} external URL must use HTTPS"
                )
        return valid_resources

    path = ROOT / "_data" / "teaching.yml"
    if not path.exists():
        errors.append("missing YAML: _data/teaching.yml")
        return
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    if not isinstance(data, list):
        errors.append("_data/teaching.yml: top-level value must be a list")
        return
    courses_by_id: dict[str, dict] = {}
    course_resources: dict[str, list[dict]] = {}
    for course_index, course in enumerate(data, start=1):
        if not isinstance(course, dict):
            errors.append(f"_data/teaching.yml: course {course_index} must be an object")
            continue
        for key in ("id", "course", "role", "summary"):
            if key not in course:
                errors.append(f"_data/teaching.yml: course {course_index} missing {key!r}")
        course_id = course.get("id", course_index)
        course_id_string = str(course_id)
        if course_id_string in courses_by_id:
            errors.append(f"_data/teaching.yml: duplicate course id {course_id_string}")
        courses_by_id[course_id_string] = course
        flattened_resources: list[dict] = []
        resources = course.get("resources", [])
        resource_groups = course.get("resource_groups", [])
        if not resources and not resource_groups:
            errors.append(f"_data/teaching.yml: course {course_id} must define resources or resource_groups")
        flattened_resources.extend(validate_resources(course_id, resources, "flat"))
        if resource_groups:
            if not isinstance(resource_groups, list):
                errors.append(f"_data/teaching.yml: course {course_id} resource_groups must be a list")
                continue
            for group_index, group in enumerate(resource_groups, start=1):
                if not isinstance(group, dict):
                    errors.append(
                        f"_data/teaching.yml: course {course_id} resource group "
                        f"{group_index} must be an object"
                    )
                    continue
                if not group.get("title"):
                    errors.append(
                        f"_data/teaching.yml: course {course_id} resource group "
                        f"{group_index} missing title"
                    )
                group_resources = group.get("resources", [])
                if not group_resources:
                    errors.append(
                        f"_data/teaching.yml: course {course_id} resource group "
                        f"{group_index} has no resources"
                    )
                    continue
                flattened_resources.extend(
                    validate_resources(course_id, group_resources, f"group {group_index}")
                )
        course_resources[course_id_string] = flattened_resources

        notebooks = course.get("notebooks", [])
        if notebooks and not isinstance(notebooks, list):
            errors.append(f"_data/teaching.yml: course {course_id} notebooks must be a list")
        elif isinstance(notebooks, list):
            for notebook_index, notebook in enumerate(notebooks, start=1):
                if not isinstance(notebook, dict) or not notebook.get("title"):
                    errors.append(
                        f"_data/teaching.yml: course {course_id} notebook "
                        f"{notebook_index} must have a title"
                    )
                elif not str(notebook.get("url", "")).startswith("https://"):
                    errors.append(
                        f"_data/teaching.yml: course {course_id} notebook "
                        f"{notebook_index} URL must use HTTPS"
                    )

    cse_resources = course_resources.get("cse107-fall26", [])
    cse_slide_files = {
        str(resource.get("file"))
        for resource in cse_resources
        if resource.get("type") == "Lecture Slides"
    }
    expected_cse_slide_files = {
        f"/files/teaching/cse107-fall26/cse107-m{module:02d}-lectures.pdf"
        for module in range(11)
    }
    if cse_slide_files != expected_cse_slide_files:
        errors.append(
            "_data/teaching.yml: CSE 107 Fall 2026 must publish exactly the M00-M10 lecture decks"
        )

    stat7l_resources = course_resources.get("stat7l-summer26", [])
    stat7l_urls = {str(resource.get("url")) for resource in stat7l_resources if resource.get("url")}
    expected_stat7l_ids = {
        "1MTuEYv2iDNzWFYeV-Lc01SU6YdBs9JxZ",
        "1FRq4Zj7V9iJ_2VzDKr1nxRLOzSoMACejVnys2R85Dj4",
        "119mNNHegWtAMfVzV_NIvQef1RjE3snJW",
        "15mmcpcrkf4-H1DlpwcKenqsbliCrCDFq0BZENrckOYY",
        "1b3wtfvlwJUorlQYPGTFlzn2ZGN4S-zWY",
        "1EweZjPgqZi1UEARHcNeeJZkXmVKBu1YE6GORy1yxJjE",
        "1p8-iljAje2Bc4WYdhEe0sN_JaqAdzXzB",
        "10zJ13NwBqmXj43qIAywf3av4EvUjz8Lf9CQ5vyleMko",
        "169Vxw6UHb8Fd8_JxPd-wB3Vv0dM1gzwW",
        "16ThE_kRAcJRzBbWZPVy2wA-HB6eQbZqY6u9QfxvIBnI",
        "1kh88qhkKvjLolKVB9ARzkx8ss5IRaQSB",
        "10VREjbe31atHku7RAMxZCy-wj7PRIgps4QVuEx0TAwI",
    }
    found_stat7l_ids = {
        match.group(1)
        for url in stat7l_urls
        if (match := re.search(r"/(?:d/|drive/)([A-Za-z0-9_-]+)", url))
    }
    if found_stat7l_ids != expected_stat7l_ids:
        errors.append(
            "_data/teaching.yml: STAT 7L Summer 2026 must link the six published Colabs "
            "and six published report templates"
        )

    for course_id in ("cse107-fall26", "stat7l-summer26"):
        for resource in course_resources.get(course_id, []):
            published_reference = " ".join(
                str(resource.get(key, "")) for key in ("file", "url")
            ).lower()
            if any(marker in published_reference for marker in ("private", "solution", "examination")):
                errors.append(
                    f"_data/teaching.yml: course {course_id} exposes a restricted resource"
                )


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


def check_canonical_cv(errors: list[str], warnings: list[str]) -> None:
    canonical_source = ROOT / "cv" / "antonio_deleon_cv.tex"
    canonical_pdf = ROOT / "files" / "cv" / "antonio-deleon-cv.pdf"
    forbidden = [
        ROOT / "cv" / "antonio_aguirre_cv.tex",
        ROOT / "files" / "cv" / "antonio-aguirre-cv.pdf",
        ROOT / "files" / "cv" / "cv.pdf",
        ROOT / "files" / "cv" / "CV___Winter_26.pdf",
    ]

    if not canonical_source.exists():
        errors.append("missing canonical CV source: cv/antonio_deleon_cv.tex")
    if not canonical_pdf.exists():
        errors.append("missing canonical CV PDF: files/cv/antonio-deleon-cv.pdf")
    for path in forbidden:
        if path.exists():
            errors.append(f"legacy/stale CV artifact should not be present: {rel(path)}")

    if canonical_pdf.exists() and shutil.which("pdfinfo"):
        result = subprocess.run(
            ["pdfinfo", str(canonical_pdf)],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        pages = re.search(r"(?m)^Pages:\s+(\d+)$", result.stdout)
        if pages and pages.group(1) != "2":
            errors.append(f"{rel(canonical_pdf)}: expected 2 pages, found {pages.group(1)}")
    elif canonical_pdf.exists():
        warnings.append("pdfinfo is not installed; CV page-count check skipped")


def check_forbidden_machine_paths(errors: list[str]) -> None:
    skip_parts = {
        ".git",
        "_site",
        ".jekyll-cache",
        ".venv",
        "__pycache__",
        ".local_gefs_hist_pipeline",
        "data",
        "local_audit_reports",
        "vendor",
    }
    forbidden_re = re.compile(r"(/data/(?:muscat_data/)?jaguir26|/home/jaguir26/python39)")
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        if path == Path(__file__).resolve():
            continue
        if any(part in skip_parts for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if forbidden_re.search(text):
            errors.append(f"{rel(path)}: machine-local path found")


def check_conflict_markers(errors: list[str]) -> None:
    skip_parts = {".git", "_site", ".jekyll-cache", ".venv", "__pycache__", "vendor"}
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
    check_research_metadata(errors)
    check_teaching_data(errors)
    check_local_asset_refs(errors)
    check_canonical_cv(errors, warnings)
    check_forbidden_machine_paths(errors)
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
