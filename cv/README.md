# CV Source

This directory contains the editable LaTeX source for the website CV.

## Files

- `antonio_deleon_cv.tex`: canonical source file.
- `../files/cv/antonio-deleon-cv.pdf`: canonical public PDF linked from `../cv.html`.

## Update Workflow

Edit the source and render the website PDF:

```bash
$EDITOR cv/antonio_deleon_cv.tex
scripts/render_cv.sh
scripts/render_cv.sh --check
```

Commit the `.tex` source and regenerated PDF together. On `main`, `.github/workflows/render_cv_pdf.yml` can also render and commit the PDF automatically after source changes.
