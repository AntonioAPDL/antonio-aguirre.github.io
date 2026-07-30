#!/usr/bin/env python3
"""Validate public blog posts before publication."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "_posts"
MIN_POSTS = 9
MIN_WORDS = 700
REQUIRED_FIELDS = {
    "layout",
    "published",
    "title",
    "date",
    "updated",
    "theme",
    "tags",
    "description",
    "excerpt",
}
PLACEHOLDER_PATTERNS = [
    r"\bTODO\b",
    r"\bTBD\b",
    r"Update with actual date",
    r"lorem ipsum",
    r"draft",
    r"all-encompassing framework",
    r"take advantage of the full potential",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def parse_front_matter(text: str, path: Path) -> tuple[dict[str, object], str]:
    if not text.startswith("---\n"):
        fail(f"{path}: missing YAML front matter")
    end = text.find("\n---\n", 4)
    if end == -1:
        fail(f"{path}: unterminated YAML front matter")
    raw = text[4:end]
    body = text[end + 5 :]
    data: dict[str, object] = {}
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            fail(f"{path}: malformed front-matter line: {line!r}")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value.lower() in {"true", "false"}:
            data[key] = value.lower() == "true"
        elif value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            data[key] = [item.strip().strip('"').strip("'") for item in inner.split(",") if item.strip()]
        elif value.isdigit():
            data[key] = int(value)
        else:
            data[key] = value.strip('"').strip("'")
    return data, body


def strip_code_blocks(body: str) -> str:
    return re.sub(r"```.*?```", " ", body, flags=re.DOTALL)


def prose_word_count(body: str) -> int:
    body = strip_code_blocks(body)
    body = re.sub(r"\$\$.*?\$\$", " ", body, flags=re.DOTALL)
    body = re.sub(r"<[^>]+>", " ", body)
    body = re.sub(r"https?://\S+", " ", body)
    body = re.sub(r"[`*_#>\[\]\(\)\{\}\\|=+\-]", " ", body)
    return len(re.findall(r"[A-Za-z][A-Za-z0-9'-]*", body))


def check_fences(path: Path, body: str) -> None:
    fence_lines = [line for line in body.splitlines() if line.startswith("```")]
    if len(fence_lines) % 2:
        fail(f"{path}: unbalanced fenced code blocks")
    for line in fence_lines[::2]:
        lang = line[3:].strip()
        if not lang:
            fail(f"{path}: fenced code block missing language identifier")


def check_math(path: Path, body: str) -> None:
    if r"\(" in body or r"\)" in body or r"\[" in body or r"\]" in body:
        fail(f"{path}: raw MathJax delimiters found; use dollar delimiters for Kramdown")
    if body.count("$$") % 2:
        fail(f"{path}: unbalanced $$ math delimiters")


def check_post(path: Path) -> tuple[dict[str, object], int]:
    text = path.read_text(encoding="utf-8")
    data, body = parse_front_matter(text, path)
    missing = REQUIRED_FIELDS - set(data)
    if missing:
        fail(f"{path}: missing required front-matter fields: {sorted(missing)}")
    if data.get("layout") != "post":
        fail(f"{path}: layout must be post")
    if data.get("published") is not True:
        fail(f"{path}: published must be true")
    if not isinstance(data.get("tags"), list) or len(data["tags"]) < 2:
        fail(f"{path}: tags must contain at least two entries")
    if re.search(r"^# ", body, flags=re.MULTILINE):
        fail(f"{path}: raw H1 heading found; layout owns the page H1")
    if "<li>" in body and "<ul>" not in body and "<ol>" not in body:
        fail(f"{path}: possible malformed standalone <li> markup")
    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            fail(f"{path}: placeholder or promotional marker matched {pattern!r}")
    check_fences(path, body)
    check_math(path, body)
    words = prose_word_count(body)
    if words < MIN_WORDS:
        fail(f"{path}: prose word count {words} is below {MIN_WORDS}")
    if "## References" not in body:
        fail(f"{path}: missing References section")
    links = re.findall(r"https?://[^)\s]+", body)
    if len(links) < 2:
        fail(f"{path}: expected at least two external references")
    return data, words


def main() -> None:
    paths = sorted(POSTS_DIR.glob("*.md"))
    if len(paths) != MIN_POSTS:
        fail(f"expected {MIN_POSTS} posts, found {len(paths)}")

    titles: set[str] = set()
    series_orders: list[int] = []
    total_words = 0
    for path in paths:
        data, words = check_post(path)
        total_words += words
        title = str(data["title"])
        if title in titles:
            fail(f"duplicate title: {title}")
        titles.add(title)
        if data.get("series") == "Bayesian workflow":
            order = data.get("series_order")
            if not isinstance(order, int):
                fail(f"{path}: Bayesian workflow post missing integer series_order")
            series_orders.append(order)

    if sorted(series_orders) != [1, 2, 3, 4, 5, 6]:
        fail(f"Bayesian workflow series_order must be 1..6; found {sorted(series_orders)}")

    print(
        f"PASS: {len(paths)} posts checked; {total_words:,} prose words; "
        "metadata, markup, math, references, and series checks passed."
    )


if __name__ == "__main__":
    main()
