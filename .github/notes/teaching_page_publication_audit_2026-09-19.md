# Teaching page publication audit — 2026-09-19

## Scope and source selection

This update uses two authoritative Google Drive sources:

- **STAT 7L, Summer 2026:** the published-masters tree, not the private working folder or student copies.
- **CSE 107, Fall 2026:** the current `02_Course_Materials` tree, not prior-quarter shared folders, instructor planning, LaTeX sources, private solutions, examinations, or archives.

The website stores stable local copies of the two course syllabi and all eleven CSE 107 lecture PDFs. The STAT 7L notebooks and report templates remain canonical Google links because they are interactive or collaboratively maintained Drive documents.

### 2026-09-22 refresh

The CSE 107 public PDFs were rechecked against the current `CSE107_Fall2026_Student_PDFs.zip` bundle in `02_Course_Materials`, modified in Drive on 2026-09-22. The public website copies now match the bundle for:

- `CSE107_Syllabus.pdf`;
- `CSE107_M00_Lectures.pdf` through `CSE107_M10_Lectures.pdf`.

The refresh changed the syllabus and lecture decks M00--M02. Decks M03--M10 were already byte-identical to the Drive bundle. The bundle also contains notes, practice files, formula sheets, and answer-labeled materials; those were intentionally not added to the teaching page in this pass because the public page currently exposes only the syllabus and lecture decks for CSE 107.

## Published inventory

### CSE 107

| Resource | Topic | Pages |
| --- | --- | ---: |
| Syllabus | Course policies, grading, schedule, and logistics | 10 |
| 00 | Opening Week | 16 |
| 01 | Counting and Conditioning | 36 |
| 02 | Discrete Random Variables | 30 |
| 03 | Expectation and Midterm 1 | 27 |
| 04 | Variance and Joint Discrete Laws | 37 |
| 05 | Continuous Random Variables | 40 |
| 06 | Conditioning, Covariance, and Transformations | 38 |
| 07 | Bounds, the Weak Law, and Review | 30 |
| 08 | The Central Limit Theorem | 28 |
| 09 | Estimation and Poisson Models | 29 |
| 10 | Poisson Processes, Markov Chains, and Review | 38 |

Each downloaded byte count matched its current Drive source during the audit. `pdfinfo` and first-page text extraction confirmed that every file is a readable PDF and that its title matches the weekly sequence in the syllabus and Weekly Guide.

### STAT 7L

| Lab | Notebook focus | Public resources |
| --- | --- | --- |
| 0 | R and Google Colab orientation | Colab + PDF-submission practice template |
| 1 | Study design and descriptive statistics | Colab + group-report template |
| 2 | Probability and discrete random variables | Colab + group-report template |
| 3 | Normal and sampling distributions | Colab + group-report template |
| 4 | Confidence intervals and one-parameter tests | Colab + group-report template |
| 5 | Multiple samples, association, and modeling | Colab + cumulative-report template |

The six notebooks were inspected at cell level to verify their titles, objectives, code/data references, and alignment with the corresponding report prompts. Drive metadata confirmed that all twelve linked artifacts have an `anyone` reader permission.

## Publication boundaries

The public page intentionally excludes:

- student submissions and student-identifying material;
- answer keys, private solutions, examinations, and reserve assessments;
- instructor planning files and editable course-source bundles;
- older CSE 107 course copies when a Fall 2026 source exists;
- private STAT 7L working copies when a published master exists.

## Reproducibility and regression checks

The teaching catalog is defined in `_data/teaching.yml`. `scripts/check_site_integrity.py` now verifies that:

1. every teaching item defines exactly one local file or HTTPS URL;
2. every local teaching artifact exists;
3. CSE 107 publishes exactly the M00–M10 lecture sequence;
4. STAT 7L points to the exact six published Colabs and six published report templates;
5. the two new course entries do not expose paths labeled private, solution, or examination.

Verification commands:

```bash
python3 scripts/check_site_integrity.py
python3 -m unittest discover -s tests -p 'test_*.py'
BUNDLE_FROZEN=true bundle exec jekyll build --trace
```

The Jekyll build should render 12 CSE 107 resources (syllabus plus 11 decks) and 13 STAT 7L resources (syllabus plus 12 Drive links).
