from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import xarray as xr


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.extract import extract_point_value, normalize_lon180  # noqa: E402


def test_normalize_lon180() -> None:
    assert normalize_lon180(190.0) == -170.0
    assert normalize_lon180(-190.0) == 170.0


def test_extract_point_value_handles_nearest_non_nan() -> None:
    lat = np.array([37.0, 37.5])
    lon = np.array([237.8, 238.3])  # ~ -122.2, -121.7
    data = np.array([[np.nan, 5.0], [8.0, 12.0]])
    ds = xr.Dataset(
        data_vars={"APCP": (("lat", "lon"), data, {"units": "mm"})},
        coords={"lat": lat, "lon": lon},
    )
    out = extract_point_value(
        ds,
        canonical_name="APCP",
        target_lat=37.04,
        target_lon=-122.07,
        search_max_km=200.0,
    )
    assert np.isfinite(out.value)
    assert out.value in {5.0, 8.0, 12.0}


def test_extract_point_value_selects_depth_layer_by_level_label() -> None:
    lat = np.array([37.0, 37.5])
    lon = np.array([237.8, 238.3])
    depth = np.array([0.1, 0.4, 1.0])
    data = np.array(
        [
            [[0.11, 0.12], [0.13, 0.14]],  # 0.1-0.4
            [[0.41, 0.42], [0.43, 0.44]],  # 0.4-1
            [[0.91, 0.92], [0.93, 0.94]],  # 1-2
        ]
    )
    ds = xr.Dataset(
        data_vars={"soilw": (("depthBelowLandLayer", "latitude", "longitude"), data, {"units": "Proportion"})},
        coords={"depthBelowLandLayer": depth, "latitude": lat, "longitude": lon},
    )
    out = extract_point_value(
        ds,
        canonical_name="SOILW",
        target_lat=37.04,
        target_lon=-122.07,
        search_max_km=200.0,
        level_label="0.4-1 m below ground",
    )
    assert np.isfinite(out.value)
    assert 0.4 <= out.value < 0.5
