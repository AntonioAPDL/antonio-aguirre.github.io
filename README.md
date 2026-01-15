# Antonio Aguirre - Personal Website

This repository contains the source for antonio-aguirre.com, built with Jekyll and the Lanyon/Poole theme foundation.

## Local development

1. Install Ruby (see `.ruby-version`).
2. Install dependencies:
   ```bash
   bundle install
   ```
3. Run the site:
   ```bash
   bundle exec jekyll serve
   ```
4. Visit `http://localhost:4000`.

## Structure

- `index.html`, `about.md`, `research.md`, `teaching.html`, `software.md`, `blog.html`, `cv.html`, `contact.md`: main pages
- `_posts/`: blog posts
- `_layouts/`, `_includes/`: shared templates
- `public/`: theme assets and custom styles
- `files/`: PDFs and images
