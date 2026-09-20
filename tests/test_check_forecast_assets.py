from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER = REPO_ROOT / "scripts" / "check_forecast_assets.py"


def points(end: datetime, count: int, *, start_lag: int = 1) -> list[dict[str, object]]:
    return [
        {"t": (end - timedelta(days=lag)).isoformat(), "v": 1.0}
        for lag in range(start_lag + count - 1, start_lag - 1, -1)
    ]


def write_fixture(path: Path, *, precip_count: int = 20) -> None:
    init = datetime.now(timezone.utc).replace(microsecond=0)
    payload = {
        "generated_at_utc": init.isoformat(),
        "init_time_utc": init.isoformat(),
        "member_count": 31,
        "observation_window_days": 20,
        "precip": {
            "surface": {
                "units": "mm",
                "time_support": "24-hour total",
                "p50": points(init + timedelta(days=10), 10),
            }
        },
        "soil_moisture": {
            "0-0.1m": {
                "units": "m3/m3",
                "time_support": "24-hour mean",
                "p50": points(init + timedelta(days=10), 10),
            }
        },
        "observed_retrospective": {
            "daily_avg_ppt": points(init, precip_count),
            "daily_avg_soil_ERA5": points(init, 10, start_lag=6),
            "daily_avg_soil_NWM_SOIL_W": points(init - timedelta(days=1000), 20),
        },
        "gefs_analysis_context_summary": {"status": "ok"},
        "quality_warnings": [],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def run_checker(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(CHECKER),
            "--gefs",
            str(path),
            "--require-observed-retrospective",
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


class ForecastAssetCheckTests(unittest.TestCase):
    def test_accepts_complete_recent_observed_context(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "gefs.json"
            write_fixture(path)
            result = run_checker(path)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_sparse_precipitation_context(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "gefs.json"
            write_fixture(path, precip_count=1)
            result = run_checker(path)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("precipitation coverage too sparse", result.stderr)


if __name__ == "__main__":
    unittest.main()
