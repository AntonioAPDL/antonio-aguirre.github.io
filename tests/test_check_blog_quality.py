"""Keep the publication gate open to new notes without losing its safeguards."""

import contextlib
import importlib.util
import io
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("blog_quality", ROOT / "scripts/check_blog_quality.py")
blog_quality = importlib.util.module_from_spec(spec)
spec.loader.exec_module(blog_quality)


class BlogPublicationGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.posts = Path(self.tmp.name)
        legacy = sorted(
            p for p in (ROOT / "_posts").glob("*.md")
            if p.name.startswith("2024-") or p.name in {
                "2025-02-12-Multivariate_CRPS.md", "2025-02-16-HB-Tutorial.md",
                "2025-03-21-VBLD.md",
            }
        )
        self.assertEqual(len(legacy), 9)
        for source in legacy:
            shutil.copyfile(source, self.posts / source.name)

    def run_gate(self):
        with patch.object(blog_quality, "POSTS_DIR", self.posts):
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                blog_quality.main()

    def test_existing_collection_and_additional_post_pass(self):
        self.run_gate()
        source = self.posts / "2025-03-21-VBLD.md"
        new_post = source.read_text().replace(
            'title: "Laplace-delta variational inference for nonconjugate models"',
            'title: "An additional statistical note"',
        )
        (self.posts / "2026-10-27-additional-note.md").write_text(new_post)
        self.run_gate()

    def test_missing_legacy_post_is_rejected(self):
        (self.posts / "2025-03-21-VBLD.md").unlink()
        with self.assertRaises(SystemExit):
            self.run_gate()

    def test_extra_post_does_not_bypass_duplicate_title_check(self):
        source = self.posts / "2025-03-21-VBLD.md"
        shutil.copyfile(source, self.posts / "2026-10-27-duplicate.md")
        with self.assertRaises(SystemExit):
            self.run_gate()

    def test_code_comment_is_not_a_duplicate_heading(self):
        post = self.posts / "2025-03-21-VBLD.md"
        with post.open("a") as stream:
            stream.write('\n```r\n# A valid R comment\nx <- 1\n```\n')
        self.run_gate()

    def test_body_h1_is_still_rejected(self):
        post = self.posts / "2025-03-21-VBLD.md"
        with post.open("a") as stream:
            stream.write('\n# A duplicate article heading\n')
        with self.assertRaises(SystemExit):
            self.run_gate()
