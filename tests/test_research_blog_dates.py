"""Keep the research-note chronology, dated URLs, and old links consistent."""

from datetime import date
from pathlib import Path
import re
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
DATES = [
    ("2025-06-12", "dynamic-quantile-models-exdqlm"),
    ("2025-09-09", "fixed-recurrent-quantile-features"),
    ("2025-12-04", "checking-quantile-forecasts"),
    ("2026-03-18", "same-content-different-intervals"),
    ("2026-07-09", "tolerance-intervals"),
    ("2026-10-13", "interval-endpoint-regression"),
]


class ResearchBlogDatesTests(unittest.TestCase):
    def test_dates_match_filenames_and_preserve_last_update(self):
        for day, slug in DATES:
            with self.subTest(slug=slug):
                paths = list((ROOT / "_posts").glob(f"*-{slug}.md"))
                self.assertEqual(len(paths), 1)
                self.assertEqual(paths[0].name, f"{day}-{slug}.md")
                data = yaml.safe_load(paths[0].read_text().split("---", 2)[1])
                self.assertEqual(data["date"], date.fromisoformat(day))
                self.assertEqual(data["updated"], date(2026, 10, 27))
                self.assertEqual(data["last_modified_at"], data["updated"])

    def test_order_and_spacing_within_requested_window(self):
        days = [date.fromisoformat(day) for day, _ in DATES]
        self.assertEqual(days, sorted(set(days)))
        self.assertGreater(days[0], date(2025, 3, 20))
        self.assertLessEqual(days[-1], date(2026, 10, 27))
        gaps = [(right - left).days for left, right in zip(days, days[1:])]
        self.assertGreater(len(set(gaps)), 1)

    def test_old_published_urls_redirect_to_current_posts(self):
        rules = {
            parts[0]: parts[1:]
            for line in (ROOT / "_redirects").read_text().splitlines()
            if (parts := line.split()) and not parts[0].startswith("#")
        }
        for day, slug in DATES:
            self.assertEqual(
                rules[f"/2026/10/27/{slug}/"],
                [f"/{day.replace('-', '/')}/{slug}/", "301!"],
            )

    def test_internal_research_links_use_current_urls(self):
        targets = {slug: f"/{day.replace('-', '/')}/{slug}/" for day, slug in DATES}
        for day, slug in DATES:
            text = (ROOT / "_posts" / f"{day}-{slug}.md").read_text()
            for link in re.findall(r"['\"](/[0-9]{4}/[0-9]{2}/[0-9]{2}/[^'\"]+/)['\"]", text):
                target_slug = link.rstrip("/").split("/")[-1]
                if target_slug in targets:
                    self.assertEqual(link, targets[target_slug])


if __name__ == "__main__":
    unittest.main()
