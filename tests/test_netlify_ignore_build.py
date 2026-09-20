from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
IGNORE_SCRIPT = REPO_ROOT / "scripts" / "netlify-ignore-build.sh"


def run(repo: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        cwd=repo,
        env={**os.environ, **(env or {})},
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def commit(repo: Path, message: str) -> None:
    result = run(repo, "git", "add", ".")
    if result.returncode:
        raise RuntimeError(result.stderr)
    result = run(repo, "git", "commit", "-m", message)
    if result.returncode:
        raise RuntimeError(result.stderr)


class NetlifyIgnoreBuildTests(unittest.TestCase):
    def make_repo(self, root: Path) -> Path:
        repo = root / "repo"
        (repo / "scripts").mkdir(parents=True)
        shutil.copy2(IGNORE_SCRIPT, repo / "scripts" / "netlify-ignore-build.sh")
        (repo / "index.html").write_text("initial\n", encoding="utf-8")
        (repo / "climate_series_status.csv").write_text("initial\n", encoding="utf-8")
        for args in (
            ("git", "init", "-b", "main"),
            ("git", "config", "user.name", "Test User"),
            ("git", "config", "user.email", "test@example.com"),
        ):
            result = run(repo, *args)
            self.assertEqual(result.returncode, 0, result.stderr)
        commit(repo, "initial")
        return repo

    def test_skips_data_only_change(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = self.make_repo(Path(raw))
            (repo / "climate_series_status.csv").write_text("updated\n", encoding="utf-8")
            commit(repo, "data update")
            result = run(
                repo,
                "./scripts/netlify-ignore-build.sh",
                env={"COMMIT_REF": "HEAD", "CACHED_COMMIT_REF": "HEAD^"},
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_cacheless_content_change_runs_build(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = self.make_repo(Path(raw))
            (repo / "index.html").write_text("updated\n", encoding="utf-8")
            commit(repo, "content update")
            result = run(
                repo,
                "./scripts/netlify-ignore-build.sh",
                env={"COMMIT_REF": "HEAD", "CACHED_COMMIT_REF": "HEAD"},
            )
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("Build required", result.stdout)


if __name__ == "__main__":
    unittest.main()
