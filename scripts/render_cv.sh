#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="${ROOT_DIR}/cv/antonio_aguirre_cv.tex"
OUTPUT="${ROOT_DIR}/files/cv/antonio-deleon-cv.pdf"
LEGACY_OUTPUTS=(
  "${ROOT_DIR}/files/cv/cv.pdf"
  "${ROOT_DIR}/files/cv/antonio-aguirre-cv.pdf"
)
CHECK_ONLY=0
KEEP_BUILD=0

usage() {
  cat <<'USAGE'
Usage: scripts/render_cv.sh [options]

Render the maintained LaTeX CV source into the website PDF assets.

Options:
  --check                 Render into a temporary directory and verify the
                          committed PDFs are current.
  --source PATH           Override the LaTeX source path.
  --output PATH           Override the canonical PDF output path.
  --legacy-output PATH    Override the legacy PDF alias path, replacing defaults.
  --keep-build            Keep the temporary build directory for debugging.
  -h, --help              Show this help text.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check)
      CHECK_ONLY=1
      shift
      ;;
    --source)
      if [[ $# -lt 2 ]]; then
        echo "[ERROR] --source requires a path." >&2
        exit 2
      fi
      SOURCE="$2"
      shift 2
      ;;
    --output)
      if [[ $# -lt 2 ]]; then
        echo "[ERROR] --output requires a path." >&2
        exit 2
      fi
      OUTPUT="$2"
      shift 2
      ;;
    --legacy-output)
      if [[ $# -lt 2 ]]; then
        echo "[ERROR] --legacy-output requires a path." >&2
        exit 2
      fi
      LEGACY_OUTPUTS=("$2")
      shift 2
      ;;
    --keep-build)
      KEEP_BUILD=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[ERROR] Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ ! -f "${SOURCE}" ]]; then
  echo "[ERROR] CV source not found: ${SOURCE}" >&2
  exit 1
fi

BUILD_DIR="$(mktemp -d "${TMPDIR:-/tmp}/cv-build.XXXXXX")"
RENDER_LOG="${BUILD_DIR}/render.log"
cleanup() {
  if [[ "${KEEP_BUILD}" != "1" ]]; then
    rm -rf "${BUILD_DIR}"
  else
    echo "[INFO] Kept build directory: ${BUILD_DIR}"
  fi
}
trap cleanup EXIT

# Keep generated PDFs byte-stable across local machines and CI runs.
export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-0}"
export FORCE_SOURCE_DATE=1

compile_with_latexmk() {
  latexmk \
    -pdf \
    -interaction=nonstopmode \
    -halt-on-error \
    -file-line-error \
    -outdir="${BUILD_DIR}" \
    "${SOURCE}" >"${RENDER_LOG}" 2>&1
}

compile_with_pdflatex() {
  : >"${RENDER_LOG}"
  for _ in 1 2; do
    pdflatex \
      -interaction=nonstopmode \
      -halt-on-error \
      -file-line-error \
      -output-directory "${BUILD_DIR}" \
      "${SOURCE}" >>"${RENDER_LOG}" 2>&1
  done
}

compile_with_tectonic() {
  tectonic \
    --keep-logs \
    --keep-intermediates \
    --outdir "${BUILD_DIR}" \
    "${SOURCE}" >"${RENDER_LOG}" 2>&1
}

if command -v latexmk >/dev/null 2>&1; then
  echo "[INFO] Rendering CV with latexmk."
  if ! compile_with_latexmk; then
    echo "[ERROR] CV render failed. Last log lines:" >&2
    tail -120 "${RENDER_LOG}" >&2 || true
    exit 1
  fi
elif command -v pdflatex >/dev/null 2>&1; then
  echo "[INFO] Rendering CV with pdflatex."
  if ! compile_with_pdflatex; then
    echo "[ERROR] CV render failed. Last log lines:" >&2
    tail -120 "${RENDER_LOG}" >&2 || true
    exit 1
  fi
elif command -v tectonic >/dev/null 2>&1; then
  echo "[INFO] Rendering CV with tectonic."
  if ! compile_with_tectonic; then
    echo "[ERROR] CV render failed. Last log lines:" >&2
    tail -120 "${RENDER_LOG}" >&2 || true
    exit 1
  fi
else
  echo "[ERROR] No LaTeX renderer found. Install latexmk, pdflatex, or tectonic." >&2
  exit 1
fi

PDF_NAME="$(basename "${SOURCE%.*}").pdf"
BUILT_PDF="${BUILD_DIR}/${PDF_NAME}"
if [[ ! -s "${BUILT_PDF}" ]]; then
  echo "[ERROR] Expected rendered PDF was not created: ${BUILT_PDF}" >&2
  exit 1
fi

normalize_pdf_text() {
  local pdf_path="$1"
  local text_path="$2"
  pdftotext -raw "${pdf_path}" - | tr -s '[:space:]' ' ' >"${text_path}"
}

pdf_page_count() {
  local pdf_path="$1"
  pdfinfo "${pdf_path}" | awk '/^Pages:/ {print $2}'
}

compare_rendered_content() {
  local expected_pdf="$1"
  local actual_pdf="$2"
  local label="$3"
  local expected_pages actual_pages
  local expected_text actual_text

  if ! command -v pdftotext >/dev/null 2>&1 || ! command -v pdfinfo >/dev/null 2>&1; then
    if cmp -s "${expected_pdf}" "${actual_pdf}"; then
      return 0
    fi
    echo "[ERROR] ${label} PDF differs and poppler tools are unavailable for content comparison: ${actual_pdf}" >&2
    return 1
  fi

  expected_pages="$(pdf_page_count "${expected_pdf}")"
  actual_pages="$(pdf_page_count "${actual_pdf}")"
  if [[ -z "${expected_pages}" || "${expected_pages}" != "${actual_pages}" ]]; then
    echo "[ERROR] ${label} PDF page count is out of date: ${actual_pdf}" >&2
    echo "        expected ${expected_pages:-unknown}, found ${actual_pages:-unknown}" >&2
    return 1
  fi

  expected_text="${BUILD_DIR}/${label}.expected.txt"
  actual_text="${BUILD_DIR}/${label}.actual.txt"
  normalize_pdf_text "${expected_pdf}" "${expected_text}"
  normalize_pdf_text "${actual_pdf}" "${actual_text}"
  if ! cmp -s "${expected_text}" "${actual_text}"; then
    echo "[ERROR] ${label} PDF text is out of date: ${actual_pdf}" >&2
    echo "        Run scripts/render_cv.sh and commit the updated PDF." >&2
    return 1
  fi
}

if [[ "${CHECK_ONLY}" == "1" ]]; then
  if [[ ! -s "${OUTPUT}" ]]; then
    echo "[ERROR] Canonical CV PDF is missing: ${OUTPUT}" >&2
    exit 1
  fi
  if ! compare_rendered_content "${BUILT_PDF}" "${OUTPUT}" "canonical"; then
    exit 1
  fi
  for legacy_pdf in "${LEGACY_OUTPUTS[@]}"; do
    if [[ ! -s "${legacy_pdf}" ]]; then
      echo "[ERROR] Legacy CV PDF is missing: ${legacy_pdf}" >&2
      exit 1
    fi
    if ! cmp -s "${OUTPUT}" "${legacy_pdf}"; then
      echo "[ERROR] Legacy CV PDF does not match the canonical PDF: ${legacy_pdf}" >&2
      exit 1
    fi
  done
  echo "[OK] CV source renders and published PDF content is current."
  exit 0
fi

mkdir -p "$(dirname "${OUTPUT}")"
cp "${BUILT_PDF}" "${OUTPUT}"
for legacy_pdf in "${LEGACY_OUTPUTS[@]}"; do
  mkdir -p "$(dirname "${legacy_pdf}")"
  cp "${BUILT_PDF}" "${legacy_pdf}"
done

echo "[OK] Wrote ${OUTPUT}"
for legacy_pdf in "${LEGACY_OUTPUTS[@]}"; do
  echo "[OK] Wrote ${legacy_pdf}"
done
