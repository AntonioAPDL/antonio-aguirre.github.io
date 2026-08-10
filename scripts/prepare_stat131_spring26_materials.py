#!/usr/bin/env python3
"""Prepare curated STAT 131 Spring 2026 PDFs for the teaching page.

The source material lives in Notability as .note packages. This script does not
try to convert .note files. It expects PDFs exported from Notability, validates
the approved subset, copies them into files/teaching/stat131-spring26, and
updates _data/teaching.yml.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml  # type: ignore


ROOT = Path(__file__).resolve().parents[1]
COURSE_ID = "stat131-spring26"
DEFAULT_OUTPUT_DIR = ROOT / "files" / "teaching" / COURSE_ID
DEFAULT_TEACHING_YAML = ROOT / "_data" / "teaching.yml"


@dataclass(frozen=True)
class Material:
    group: str
    title: str
    kind: str
    target: str
    aliases: tuple[str, ...]


PUBLIC_MATERIALS: tuple[Material, ...] = (
    Material(
        "Lecture Slides",
        "Lecture 4 Slides",
        "Slides",
        "stat131-spring26-lecture-04-slides.pdf",
        ("Lec_4___Winter_26___Slides",),
    ),
    Material(
        "Lecture Slides",
        "Lecture 5 Slides",
        "Slides",
        "stat131-spring26-lecture-05-slides.pdf",
        ("Lec_5___Winter_26___Slides (2)", "Lec_5___Winter_26___Slides"),
    ),
    Material(
        "Lecture Slides",
        "Lecture 6 Slides",
        "Slides",
        "stat131-spring26-lecture-06-slides.pdf",
        ("Lec_6___Winter_26___Slides",),
    ),
    Material(
        "Lecture Slides",
        "Lecture 7 Slides",
        "Slides",
        "stat131-spring26-lecture-07-slides.pdf",
        ("Lec_7___Winter_26___Slides",),
    ),
    Material(
        "Lecture Slides",
        "Lecture 8 Slides",
        "Slides",
        "stat131-spring26-lecture-08-slides.pdf",
        (
            "Lec_8___Winter_26___Slides (4)",
            "Lec_8___Winter_26___Slides (3)",
            "Lec_8___Winter_26___Slides (2)",
            "Lec_8___Winter_26___Slides (1)",
            "Lec_8___Winter_26___Slides",
        ),
    ),
    Material(
        "Lecture Slides",
        "Lecture 9 Slides",
        "Slides",
        "stat131-spring26-lecture-09-slides.pdf",
        ("Lec_9___Winter_26___Slides",),
    ),
    Material(
        "Lecture Slides",
        "Lecture 10 Slides",
        "Slides",
        "stat131-spring26-lecture-10-slides.pdf",
        ("Lec_10___Winter_26___Slides",),
    ),
    Material(
        "Discussion Sections",
        "Discussion Section 1",
        "Section Notes",
        "stat131-spring26-discussion-01.pdf",
        ("DS1 Spring26", "DS_1___Spring_26"),
    ),
    Material(
        "Discussion Sections",
        "Discussion Section 2",
        "Section Notes",
        "stat131-spring26-discussion-02.pdf",
        ("DS_2___Winter_26",),
    ),
    Material(
        "Discussion Sections",
        "Discussion Sections 3-4",
        "Section Notes",
        "stat131-spring26-discussion-03-04.pdf",
        ("DS_3_4___Winter_26",),
    ),
    Material(
        "Discussion Sections",
        "Discussion Section 5",
        "Section Notes",
        "stat131-spring26-discussion-05.pdf",
        ("DS_5___Winter_26 (3)", "DS_5___Winter_26"),
    ),
    Material(
        "Discussion Sections",
        "Discussion Section 6",
        "Section Notes",
        "stat131-spring26-discussion-06.pdf",
        ("DS_6_Alt___Winter_26", "DS_6___Winter_26"),
    ),
    Material(
        "Discussion Sections",
        "Discussion Section 7",
        "Section Notes",
        "stat131-spring26-discussion-07.pdf",
        ("DS_7___Winter_26 (3)", "DS_7___Winter_26"),
    ),
    Material(
        "Discussion Sections",
        "Discussion Section 8",
        "Section Notes",
        "stat131-spring26-discussion-08.pdf",
        ("DS_8_l_Alt2___Winter_26", "DS_8_l_Alt___Winter_26", "DS_8___Winter_26"),
    ),
    Material(
        "Discussion Sections",
        "Discussion Section 9",
        "Section Notes",
        "stat131-spring26-discussion-09.pdf",
        ("DS_9___Winter_26 (1)", "DS_9___Winter_26"),
    ),
    Material(
        "Review Materials",
        "Final Review",
        "Review",
        "stat131-spring26-final-review.pdf",
        ("Final_Review_Spring_2026", "Final Review Spring 2026"),
    ),
)


PRIVATE_OR_EXCLUDED_HINTS = (
    "2508",
    "cruzid",
    "degroot",
    "login",
    "midterm",
    "names",
    "note apr",
    "note may",
    "pearson",
    "practice midterm",
    "schervish",
    "solution",
    "syllabus",
    "template",
)


def normalize(value: str) -> str:
    stem = Path(value).stem
    return re.sub(r"[^a-z0-9]+", " ", stem.lower()).strip()


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def iter_pdfs(source_dir: Path) -> list[Path]:
    return sorted(path for path in source_dir.rglob("*.pdf") if path.is_file())


def build_index(paths: Iterable[Path]) -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = {}
    for path in paths:
        index.setdefault(normalize(path.name), []).append(path)
    return index


def find_source(material: Material, index: dict[str, list[Path]]) -> Path | None:
    for alias in (*material.aliases, material.target):
        matches = index.get(normalize(alias), [])
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            names = ", ".join(str(path) for path in matches)
            raise RuntimeError(f"ambiguous PDF candidates for {material.title}: {names}")
    return None


def pdf_page_count(path: Path) -> int:
    with path.open("rb") as fh:
        header = fh.read(4)
    if header != b"%PDF":
        raise RuntimeError(f"{path} does not start with a PDF header")
    if shutil.which("pdfinfo") is None:
        return -1
    result = subprocess.run(
        ["pdfinfo", str(path)],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise RuntimeError(f"pdfinfo failed for {path}: {result.stderr.strip()}")
    match = re.search(r"(?m)^Pages:\s+(\d+)$", result.stdout)
    if not match:
        raise RuntimeError(f"pdfinfo did not report a page count for {path}")
    return int(match.group(1))


def material_resource(material: Material) -> dict[str, str]:
    return {
        "title": material.title,
        "type": material.kind,
        "term": "Spring 2026",
        "file": f"/files/teaching/{COURSE_ID}/{material.target}",
    }


def build_course_entry(selected: list[Material]) -> dict[str, object]:
    groups: list[dict[str, object]] = []
    flat_resources: list[dict[str, str]] = []
    for group_name in dict.fromkeys(material.group for material in selected):
        resources = [material_resource(material) for material in selected if material.group == group_name]
        groups.append({"title": group_name, "resources": resources})
        flat_resources.extend(resources)

    return {
        "id": COURSE_ID,
        "course": "STAT 131: Probability Theory - Spring 2026 Section Materials",
        "role": "Teaching Assistant",
        "terms": "Spring 2026",
        "summary": (
            "Curated section slides and review notes prepared for STAT 131. "
            "These materials are kept separate from the broader STAT 131 review archive."
        ),
        "resources": flat_resources,
        "resource_groups": groups,
    }


def update_teaching_yaml(path: Path, entry: dict[str, object]) -> None:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    if not isinstance(data, list):
        raise RuntimeError(f"{path} must contain a top-level list")

    data = [course for course in data if not (isinstance(course, dict) and course.get("id") == COURSE_ID)]
    insert_at = 1
    for index, course in enumerate(data):
        if isinstance(course, dict) and course.get("id") == "stat131":
            insert_at = index + 1
            break
    data.insert(insert_at, entry)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=False), encoding="utf-8")


def describe_unmatched(pdfs: list[Path], selected_paths: set[Path]) -> list[Path]:
    unmatched = []
    for path in pdfs:
        if path in selected_paths:
            continue
        normalized = normalize(path.name)
        if any(hint in normalized for hint in PRIVATE_OR_EXCLUDED_HINTS):
            continue
        unmatched.append(path)
    return unmatched


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate and publish curated STAT 131 Spring 2026 PDFs exported from Notability.",
    )
    parser.add_argument("--source-dir", required=True, type=Path, help="Directory containing PDF exports.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Public PDF output directory.")
    parser.add_argument("--teaching-yaml", type=Path, default=DEFAULT_TEACHING_YAML, help="Teaching data YAML.")
    parser.add_argument("--apply", action="store_true", help="Copy PDFs and update teaching YAML.")
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Publish the matched curated subset instead of requiring every expected PDF.",
    )
    parser.add_argument("--skip-yaml", action="store_true", help="Copy PDFs without updating teaching YAML.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_dir = args.source_dir.resolve()
    output_dir = args.output_dir.resolve()
    teaching_yaml = args.teaching_yaml.resolve()

    if not source_dir.exists() or not source_dir.is_dir():
        print(f"[ERROR] source directory does not exist: {source_dir}", file=sys.stderr)
        return 2
    if not teaching_yaml.exists():
        print(f"[ERROR] teaching YAML does not exist: {teaching_yaml}", file=sys.stderr)
        return 2

    pdfs = iter_pdfs(source_dir)
    if not pdfs:
        note_count = sum(1 for path in source_dir.rglob("*.note") if path.is_file())
        print(f"[ERROR] found no PDFs in {source_dir}", file=sys.stderr)
        if note_count:
            print(f"[ERROR] found {note_count} .note files; export them from Notability as PDF first.", file=sys.stderr)
        return 2

    index = build_index(pdfs)
    selected: list[tuple[Material, Path, int]] = []
    missing: list[Material] = []
    for material in PUBLIC_MATERIALS:
        source = find_source(material, index)
        if source is None:
            missing.append(material)
            continue
        pages = pdf_page_count(source)
        selected.append((material, source, pages))

    if missing and not args.allow_missing:
        print("[ERROR] missing expected curated PDFs:", file=sys.stderr)
        for material in missing:
            print(f"  - {material.title}: expected one of {', '.join(material.aliases)}", file=sys.stderr)
        print("[ERROR] re-run with --allow-missing only if the subset is intentionally incomplete.", file=sys.stderr)
        return 2
    if not selected:
        print("[ERROR] no curated PDFs matched the manifest", file=sys.stderr)
        return 2

    selected_paths = {source for _, source, _ in selected}
    unmatched = describe_unmatched(pdfs, selected_paths)

    print(f"[OK] source PDFs found: {len(pdfs)}")
    print(f"[OK] curated PDFs matched: {len(selected)}")
    for material, source, pages in selected:
        page_text = "unknown pages" if pages < 0 else f"{pages} pages"
        print(f"  - {material.target} <- {source.name} ({page_text})")
    if missing:
        print(f"[WARN] missing curated PDFs allowed: {len(missing)}")
    if unmatched:
        print("[WARN] PDFs not in the curated manifest; review before publishing:")
        for path in unmatched:
            print(f"  - {path.name}")

    if not args.apply:
        print("[DRY RUN] no files changed; re-run with --apply to publish the matched PDFs.")
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    for material, source, _ in selected:
        shutil.copy2(source, output_dir / material.target)

    if not args.skip_yaml:
        entry = build_course_entry([material for material, _, _ in selected])
        update_teaching_yaml(teaching_yaml, entry)
        print(f"[OK] updated {display_path(teaching_yaml)}")

    print(f"[OK] copied PDFs to {display_path(output_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
