# CV Source

This directory contains the editable LaTeX source for the website CV.

## Files

- `antonio_aguirre_cv.tex`: canonical source file.
- `../files/cv/antonio-deleon-cv.pdf`: canonical public PDF linked from `../cv.html`.
- `../files/cv/antonio-aguirre-cv.pdf`: legacy alias kept in sync for older links.
- `../files/cv/cv.pdf`: legacy alias kept in sync for older links.

## Update Workflow

Edit the source and render the website PDFs:

```bash
$EDITOR cv/antonio_aguirre_cv.tex
scripts/render_cv.sh
scripts/render_cv.sh --check
```

Commit the `.tex` source and regenerated PDFs together. On `main`, `.github/workflows/render_cv_pdf.yml` can also render and commit the PDFs automatically after source changes.
