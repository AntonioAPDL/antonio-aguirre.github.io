#!/usr/bin/env python3
"""Static sanity checks for fenced code blocks in blog posts."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "_posts"
CHECKED_LANGS = {"bash", "sh", "r"}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def iter_fences(text: str):
    in_block = False
    lang = ""
    lines: list[str] = []
    start_line = 0
    for line_no, line in enumerate(text.splitlines(), start=1):
        if line.startswith("```"):
            if not in_block:
                in_block = True
                lang = line[3:].strip().lower()
                lines = []
                start_line = line_no
            else:
                yield lang, "\n".join(lines), start_line
                in_block = False
            continue
        if in_block:
            lines.append(line)
    if in_block:
        fail("unterminated fenced code block")


def check_bash(code: str, label: str) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as tmp:
        tmp.write(code)
        tmp_path = Path(tmp.name)
    try:
        result = subprocess.run(["bash", "-n", str(tmp_path)], text=True, capture_output=True)
        if result.returncode != 0:
            fail(f"{label}: bash syntax failed: {result.stderr.strip()}")
    finally:
        tmp_path.unlink(missing_ok=True)


def check_r(code: str, label: str) -> bool:
    rscript = shutil.which("Rscript")
    if not rscript:
        return False
    expression = f"parse(text = readChar('{label}', file.info('{label}')$size))"
    with tempfile.NamedTemporaryFile("w", suffix=".R", delete=False) as tmp:
        tmp.write(code)
        tmp_path = Path(tmp.name)
    try:
        result = subprocess.run(
            [rscript, "--vanilla", "-e", expression.replace(label, str(tmp_path))],
            text=True,
            capture_output=True,
        )
        if result.returncode != 0:
            fail(f"{label}: R parse failed: {result.stderr.strip()}")
    finally:
        tmp_path.unlink(missing_ok=True)
    return True


def main() -> None:
    counts = {"bash": 0, "r": 0, "text": 0, "other": 0}
    r_checked = True
    for path in sorted(POSTS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for lang, code, line_no in iter_fences(text):
            label = f"{path}:{line_no}"
            if not lang:
                fail(f"{label}: missing code-fence language")
            if lang in {"bash", "sh"}:
                counts["bash"] += 1
                check_bash(code, label)
            elif lang == "r":
                counts["r"] += 1
                r_checked = check_r(code, label) and r_checked
            elif lang == "text":
                counts["text"] += 1
            else:
                counts["other"] += 1

    suffix = "" if r_checked else " Rscript unavailable; R blocks were not parsed."
    print(
        "PASS: non-executing code checks completed for "
        f"{counts['bash']} Bash, {counts['r']} R, {counts['text']} text, "
        f"and {counts['other']} other fenced blocks.{suffix}"
    )


if __name__ == "__main__":
    main()
