from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.schema import validate_member_schema  # noqa: E402
from src.schema import validate_summary_schema  # noqa: E402


def _valid_member_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "site_id": "11160500",
                "init_time_utc": dt.datetime(2026, 2, 24, 0, 0, tzinfo=dt.timezone.utc),
                "lead_hours": 3,
                "valid_time_utc": dt.datetime(2026, 2, 24, 3, 0, tzinfo=dt.timezone.utc),
                "member": "c00",
                "variable": "APCP",
                "level": "surface",
                "value": 0.0,
                "units": "kg m**-2",
                "grid_lat": 37.0,
                "grid_lon": -122.0,
                "distance_km": 8.1,
                "used_fallback_point": False,
                "product": "atmos.5",
                "source": "aws",
                "search_string": "APCP:surface",
                "descriptor": "x",
                "file_ref": "/tmp/foo",
                "error": "",
            }
        ]
    )


def test_validate_member_schema_accepts_valid_frame() -> None:
    out = validate_member_schema(_valid_member_df(), schema_version=1)
    assert "schema_version" in out.columns
    assert out["schema_version"].iloc[0] == 1


def test_validate_member_schema_rejects_missing_columns() -> None:
    bad = _valid_member_df().drop(columns=["variable"])
    with pytest.raises(ValueError):
        validate_member_schema(bad, schema_version=1)


def _valid_summary_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "site_id": "11160500",
                "init_time_utc": dt.datetime(2026, 2, 24, 0, 0, tzinfo=dt.timezone.utc),
                "lead_hours": 3,
                "valid_time_utc": dt.datetime(2026, 2, 24, 3, 0, tzinfo=dt.timezone.utc),
                "variable": "APCP",
                "level": "surface",
                "mean": 1.2,
                "std": 0.3,
                "q10": 0.2,
                "q50": 1.0,
                "q90": 2.0,
                "member_count": 31,
            }
        ]
    )


def test_validate_summary_schema_accepts_valid_frame() -> None:
    out = validate_summary_schema(_valid_summary_df(), schema_version=2)
    assert "schema_version" in out.columns
    assert out["schema_version"].iloc[0] == 2


def test_validate_summary_schema_rejects_missing_columns() -> None:
    bad = _valid_summary_df().drop(columns=["q90"])
    with pytest.raises(ValueError):
        validate_summary_schema(bad, schema_version=1)
