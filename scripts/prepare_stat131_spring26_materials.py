#!/usr/bin/env python3
"""Prepare curated STAT 131 Spring 2026 PDFs for the teaching page.

The source material lives in Notability as .note packages. Notability packages
can include embedded PDFs; when they do, this script extracts those PDFs,
validates the approved subset, copies them into files/teaching/stat131-spring26,
and updates _data/teaching.yml. Exported PDFs are also supported directly.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
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


def iter_sources(source_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in source_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in {".pdf", ".note"}
    )


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
            raise RuntimeError(f"ambiguous source candidates for {material.title}: {names}")
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


def embedded_pdf_members(note_path: Path) -> list[zipfile.ZipInfo]:
    if not zipfile.is_zipfile(note_path):
        raise RuntimeError(f"{note_path} is not a readable Notability package")
    with zipfile.ZipFile(note_path) as zf:
        members = [
            info
            for info in zf.infolist()
            if not info.is_dir()
            and info.filename.lower().endswith(".pdf")
            and "/pdfs/" in info.filename.lower()
        ]
        if members:
            return members
        return [
            info
            for info in zf.infolist()
            if not info.is_dir() and info.filename.lower().endswith(".pdf")
        ]


def _write_embedded_pdfs(note_path: Path, output_dir: Path) -> list[Path]:
    members = embedded_pdf_members(note_path)
    if not members:
        raise RuntimeError(f"{note_path.name} does not contain an embedded PDF")

    extracted: list[Path] = []
    with zipfile.ZipFile(note_path) as zf:
        for index, member in enumerate(members, start=1):
            payload = zf.read(member)
            if not payload.startswith(b"%PDF"):
                raise RuntimeError(f"{note_path.name}:{member.filename} is not a valid embedded PDF")
            target = output_dir / f"embedded-{index:02d}.pdf"
            target.write_bytes(payload)
            pdf_page_count(target)
            extracted.append(target)
    return extracted


def _merge_pdfs(pdfs: list[Path], output_path: Path) -> None:
    if shutil.which("gs") is None:
        names = ", ".join(path.name for path in pdfs)
        raise RuntimeError(
            "Notability package contains multiple embedded PDFs, but Ghostscript "
            f"is not installed to merge them: {names}"
        )

    result = subprocess.run(
        [
            "gs",
            "-q",
            "-dBATCH",
            "-dNOPAUSE",
            "-sDEVICE=pdfwrite",
            f"-sOutputFile={output_path}",
            *[str(path) for path in pdfs],
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Ghostscript failed while merging embedded PDFs: {result.stderr.strip()}")


def extract_pdf_from_note(note_path: Path, output_path: Path) -> int:
    with tempfile.TemporaryDirectory(prefix="stat131-note-") as tmp:
        tmp_dir = Path(tmp)
        extracted = _write_embedded_pdfs(note_path, tmp_dir)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if len(extracted) == 1:
            shutil.copy2(extracted[0], output_path)
        else:
            _merge_pdfs(extracted, output_path)
        return pdf_page_count(output_path)


def source_page_count(path: Path) -> int:
    if path.suffix.lower() == ".pdf":
        return pdf_page_count(path)
    if path.suffix.lower() == ".note":
        with tempfile.TemporaryDirectory(prefix="stat131-note-check-") as tmp:
            return extract_pdf_from_note(path, Path(tmp) / "extracted.pdf")
    raise RuntimeError(f"unsupported source type: {path}")


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
        flat_resources.extend(dict(resource) for resource in resources)

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


def yaml_quote(value: object) -> str:
    text = str(value)
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def render_course_entry(entry: dict[str, object]) -> str:
    resources = entry.get("resources")
    groups = entry.get("resource_groups")
    if not isinstance(resources, list):
        raise RuntimeError("course entry must define resources")
    if not isinstance(groups, list):
        raise RuntimeError("course entry must define resource_groups")

    lines = [
        f"- id: {entry['id']}",
        f"  course: {yaml_quote(entry['course'])}",
        f"  role: {yaml_quote(entry['role'])}",
        f"  terms: {yaml_quote(entry['terms'])}",
        f"  summary: {yaml_quote(entry['summary'])}",
        "  resources:",
    ]
    for resource in resources:
        if not isinstance(resource, dict):
            raise RuntimeError("each teaching resource must be an object")
        lines.extend(
            [
                f"    - title: {yaml_quote(resource['title'])}",
                f"      type: {yaml_quote(resource['type'])}",
                f"      term: {yaml_quote(resource['term'])}",
                f"      file: {yaml_quote(resource['file'])}",
            ]
        )
    lines.append("  resource_groups:")
    for group in groups:
        if not isinstance(group, dict) or not isinstance(group.get("resources"), list):
            raise RuntimeError("each resource group must define resources")
        lines.append(f"    - title: {yaml_quote(group['title'])}")
        lines.append("      resources:")
        for resource in group["resources"]:
            if not isinstance(resource, dict):
                raise RuntimeError("each teaching resource must be an object")
            lines.extend(
                [
                    f"        - title: {yaml_quote(resource['title'])}",
                    f"          type: {yaml_quote(resource['type'])}",
                    f"          term: {yaml_quote(resource['term'])}",
                    f"          file: {yaml_quote(resource['file'])}",
                ]
            )
    return "\n".join(lines) + "\n"


def top_level_course_id(line: str) -> str | None:
    match = re.match(r"^- id:\s*['\"]?([^'\"\n]+)['\"]?\s*$", line)
    return match.group(1) if match else None


def remove_course_block(lines: list[str], course_id: str) -> list[str]:
    output: list[str] = []
    index = 0
    while index < len(lines):
        if top_level_course_id(lines[index].rstrip("\n")) == course_id:
            index += 1
            while index < len(lines) and top_level_course_id(lines[index].rstrip("\n")) is None:
                index += 1
            continue
        output.append(lines[index])
        index += 1
    return output


def insert_after_course(lines: list[str], after_course_id: str, block: str) -> list[str]:
    insert_at = len(lines)
    for index, line in enumerate(lines):
        if top_level_course_id(line.rstrip("\n")) == after_course_id:
            insert_at = index + 1
            while insert_at < len(lines) and top_level_course_id(lines[insert_at].rstrip("\n")) is None:
                insert_at += 1
            break

    block_lines = [line + "\n" for line in block.rstrip("\n").split("\n")]
    return lines[:insert_at] + block_lines + lines[insert_at:]


def update_teaching_yaml(path: Path, entry: dict[str, object]) -> None:
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text) or []
    if not isinstance(data, list):
        raise RuntimeError(f"{path} must contain a top-level list")

    lines = remove_course_block(text.splitlines(keepends=True), COURSE_ID)
    lines = insert_after_course(lines, "stat131", render_course_entry(entry))
    path.write_text("".join(lines), encoding="utf-8")


def describe_unmatched(sources: list[Path], selected_paths: set[Path]) -> list[Path]:
    unmatched = []
    for path in sources:
        if path in selected_paths:
            continue
        normalized = normalize(path.name)
        if any(hint in normalized for hint in PRIVATE_OR_EXCLUDED_HINTS):
            continue
        unmatched.append(path)
    return unmatched


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate and publish curated STAT 131 Spring 2026 PDFs from PDF exports or Notability .note packages.",
    )
    parser.add_argument("--source-dir", required=True, type=Path, help="Directory containing PDF exports or .note packages.")
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

    sources = iter_sources(source_dir)
    if not sources:
        print(f"[ERROR] found no PDFs or Notability .note packages in {source_dir}", file=sys.stderr)
        return 2

    index = build_index(sources)
    selected: list[tuple[Material, Path, int]] = []
    missing: list[Material] = []
    for material in PUBLIC_MATERIALS:
        source = find_source(material, index)
        if source is None:
            missing.append(material)
            continue
        pages = source_page_count(source)
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
    unmatched = describe_unmatched(sources, selected_paths)

    print(f"[OK] source files found: {len(sources)}")
    print(f"[OK] curated sources matched: {len(selected)}")
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
        target = output_dir / material.target
        if source.suffix.lower() == ".pdf":
            shutil.copy2(source, target)
        elif source.suffix.lower() == ".note":
            extract_pdf_from_note(source, target)
        else:
            raise RuntimeError(f"unsupported source type: {source}")

    if not args.skip_yaml:
        entry = build_course_entry([material for material, _, _ in selected])
        update_teaching_yaml(teaching_yaml, entry)
        print(f"[OK] updated {display_path(teaching_yaml)}")

    print(f"[OK] copied PDFs to {display_path(output_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
