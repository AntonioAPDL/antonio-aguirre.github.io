from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER = REPO_ROOT / "scripts" / "check_climate_assets.py"
TARGET = date(2026, 9, 20)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_fixture(root: Path, ppt_days: int = 20, soil_days: int = 15, combined_ppt_lag: int = 1) -> None:
    ppt_dates = [TARGET - timedelta(days=offset) for offset in range(1, ppt_days + 1)]
    soil_dates = [TARGET - timedelta(days=offset) for offset in range(6, 6 + soil_days)]
    write_csv(
        root / "prism_precipitation_santa_cruz_1987_2023.csv",
        ["Date", "PRCP_mm"],
        [{"Date": day.isoformat(), "PRCP_mm": 0.0} for day in sorted(ppt_dates)],
    )
    write_csv(
        root / "soil_moisture_data/soil_moisture_big_trees_daily_avg_1987_2023.csv",
        ["Date", "Daily_Avg_Soil_Moisture"],
        [{"Date": day.isoformat(), "Daily_Avg_Soil_Moisture": 0.15} for day in sorted(soil_dates)],
    )

    combined_dates = sorted(set(ppt_dates) | set(soil_dates))
    ppt_set = {day for day in ppt_dates if day <= TARGET - timedelta(days=combined_ppt_lag)}
    soil_set = set(soil_dates)
    write_csv(
        root / "climate_daily_ppt_soil.csv",
        [
            "timestamp",
            "daily_avg_ppt",
            "daily_avg_soil_ERA5",
            "daily_avg_soil_NWM_SOIL_M",
            "daily_avg_soil_NWM_SOIL_W",
        ],
        [
            {
                "timestamp": day.isoformat(),
                "daily_avg_ppt": 0.0 if day in ppt_set else "",
                "daily_avg_soil_ERA5": 0.15 if day in soil_set else "",
                "daily_avg_soil_NWM_SOIL_M": "",
                "daily_avg_soil_NWM_SOIL_W": "",
            }
            for day in combined_dates
        ],
    )


def run_checker(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(CHECKER),
            "--root-dir",
            str(root),
            "--target-date",
            TARGET.isoformat(),
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


class ClimateAssetCheckTests(unittest.TestCase):
    def test_accepts_fresh_well_covered_assets(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            build_fixture(root)
            result = run_checker(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_sparse_stale_precipitation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            build_fixture(root, ppt_days=1, combined_ppt_lag=19)
            result = run_checker(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("precipitation", result.stderr)

    def test_rejects_combined_endpoint_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            build_fixture(root, combined_ppt_lag=2)
            result = run_checker(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("endpoint does not match", result.stderr)


if __name__ == "__main__":
    unittest.main()
