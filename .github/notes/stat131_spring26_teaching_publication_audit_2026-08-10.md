# STAT 131 Spring 2026 Teaching Publication Audit

Date: 2026-08-10

## Source

- Google Drive account connected to Codex: `jaguir26@ucsc.edu`
- Shared Drive path: `Notability / TAing / TA - Spring 26`
- Folder ID: `1Sha5SLutVcgPs_J-PjWbV9Zz2Tmw4LpC`
- Folder URL: `https://drive.google.com/drive/folders/1Sha5SLutVcgPs_J-PjWbV9Zz2Tmw4LpC`
- Permission observed through the connector: shared, listable, downloadable

## Diagnosis

The source folder contains Notability `.note` packages, exposed by Google Drive
as `application/x-zip`. The folder did not contain PDFs, native Google Slides,
or PowerPoint files at audit time. Google Drive can download these raw packages,
but it cannot export `.note` files to PDF.

Follow-up validation showed that the Notability packages are ZIP archives and
the selected packages contain embedded PDFs under their package `PDFs/`
directories. The website publication path can therefore extract those embedded
PDFs directly, validate them, and publish only browser-readable PDF files.

The robust path is therefore:

1. Download the approved Notability `.note` packages from Drive, or export them
   from Notability as PDFs.
2. Place those local sources in a gitignored staging directory.
3. Run `scripts/prepare_stat131_spring26_materials.py`.
4. Validate the site before committing.

This avoids publishing proprietary `.note` files, avoids broken website links,
and keeps the conversion rule local, auditable, and repeatable.

## Conversion Constraint

Notability's official export and backup documentation supports exporting notes
as PDF, Note, JPEG, PNG, or NTB. The `.note` format is Notability's editable
custom format. Public website delivery should use PDF because it is stable,
browser-readable, and appropriate for course handouts.

Known local-conversion alternatives were rejected:

- The available public converter route requires macOS plus the Notability app.
- The website server is Linux and does not have Notability installed.
- Publishing raw `.note` internals is not appropriate for website delivery.
- Extracting an embedded PDF from the package is acceptable because the public
  artifact remains the PDF that Notability already stores inside the package.

## Public Curation Rules

Publish only selected lecture, discussion, and review materials. Do not publish
files that appear to contain assessment solutions, login information, names,
templates, copyrighted textbook copies, or unrelated paper notes.

Default public candidates:

- Lecture slides: 4 through 10
- Discussion section notes: 1 through 9, with combined or alternate files
  selected where the source naming indicates that is the cleaner version
- Final review

Default exclusions:

- `Names.note`
- `CruzID Gold Login.note`
- `stat131_midterm_*`
- `practice_midterm-*`
- `STAT131_template*`
- `Morris H DeGroot_ Mark J Schervish - Probability and statistics-*`
- `2508.04875v4.note`
- generic date notes unless manually approved
- syllabus files unless manually approved

## Website Integration

The public course section should be separate from the current STAT 131 archive:

- Public label: `STAT 131: Probability Theory - Spring 2026 Section Materials`
- Data ID: `stat131-spring26`
- Public asset folder: `files/teaching/stat131-spring26/`

The teaching page now supports optional grouped resources through
`resource_groups`. Existing courses continue to render through the flat
`resources` list.

## Reproducible Intake Command

After staging approved `.note` packages or exported PDFs:

```bash
python3 scripts/prepare_stat131_spring26_materials.py \
  --source-dir local_teaching_exports/stat131-spring26-notes \
  --apply

python3 scripts/check_site_integrity.py
bundle exec jekyll build --trace
```

Use `--allow-missing` only if a partial public subset is intentional.

## Acceptance Checks

- Every published file is a valid PDF.
- Every published file opens through `pdfinfo`.
- `_data/teaching.yml` contains one `stat131-spring26` course entry.
- The teaching page builds with grouped resources.
- No `.note`, login, names, solution, or textbook-copy files are committed.
- Git status contains only the teaching-publication changes before commit.
