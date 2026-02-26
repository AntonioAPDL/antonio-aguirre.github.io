from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, Optional, Sequence, Tuple

import numpy as np


LAT_CANDIDATES = ("latitude", "lat", "gridlat", "y")
LON_CANDIDATES = ("longitude", "lon", "gridlon", "x")
DEPTH_DIM_CANDIDATES = ("depthBelowLandLayer", "depthBelowGroundLayer", "depth")


@dataclass(frozen=True)
class PointExtraction:
    value: float
    grid_lat: float
    grid_lon: float
    distance_km: float
    used_fallback_point: bool
    units: str
    source_var: str


def normalize_lon180(lon: float) -> float:
    return ((lon + 180.0) % 360.0) - 180.0


def haversine_km(lat1: np.ndarray, lon1: np.ndarray, lat2: float, lon2: float) -> np.ndarray:
    r_earth = 6371.0
    lat1r = np.radians(lat1)
    lon1r = np.radians(lon1)
    lat2r = math.radians(lat2)
    lon2r = math.radians(lon2)
    dlat = lat1r - lat2r
    dlon = lon1r - lon2r
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1r) * math.cos(lat2r) * np.sin(dlon / 2.0) ** 2
    return 2.0 * r_earth * np.arcsin(np.sqrt(a))


def _find_coord_name(data_array: Any, candidates: Sequence[str]) -> Optional[str]:
    for name in candidates:
        if name in data_array.coords:
            coord = data_array.coords[name]
            if coord.ndim in (1, 2):
                return name
    return None


def _pick_data_array(dataset: Any, canonical_name: str) -> Any:
    data_vars = list(dataset.data_vars)
    if not data_vars:
        raise ValueError("Dataset has no data variables")
    if canonical_name in dataset.data_vars:
        return dataset[canonical_name]
    canonical_upper = canonical_name.upper()
    for name in data_vars:
        if canonical_upper in name.upper():
            return dataset[name]
    return dataset[data_vars[0]]


def _parse_soil_level_start_depth(level_label: Optional[str]) -> Optional[float]:
    if not level_label:
        return None
    match = re.search(r"([0-9.]+)\s*-\s*([0-9.]+)\s*m", level_label)
    if not match:
        return None
    return float(match.group(1))


def _prepare_field_and_grid(
    data_array: Any,
    level_label: Optional[str] = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    lat_name = _find_coord_name(data_array, LAT_CANDIDATES)
    lon_name = _find_coord_name(data_array, LON_CANDIDATES)
    if lat_name is None or lon_name is None:
        raise ValueError("Could not locate latitude/longitude coordinates in dataset")

    lat_coord = data_array.coords[lat_name]
    lon_coord = data_array.coords[lon_name]

    if lat_coord.ndim == 2 and lon_coord.ndim == 2:
        horiz_dims = lat_coord.dims
    elif lat_coord.ndim == 1 and lon_coord.ndim == 1:
        horiz_dims = (lat_coord.dims[0], lon_coord.dims[0])
    else:
        raise ValueError("Unsupported lat/lon coordinate dimensionality")

    working = data_array
    level_start_depth = _parse_soil_level_start_depth(level_label)
    for dim in list(working.dims):
        if dim not in horiz_dims:
            if level_start_depth is not None and dim in DEPTH_DIM_CANDIDATES and dim in working.coords:
                depth_values = np.asarray(working.coords[dim].values, dtype=float)
                idx = int(np.argmin(np.abs(depth_values - level_start_depth)))
                working = working.isel({dim: idx})
            else:
                working = working.isel({dim: 0})

    if lat_coord.ndim == 2:
        lat2d = np.asarray(lat_coord.values)
        lon2d = np.asarray(lon_coord.values)
    else:
        lat1d = np.asarray(lat_coord.values)
        lon1d = np.asarray(lon_coord.values)
        lat2d, lon2d = np.meshgrid(lat1d, lon1d, indexing="ij")

    values = np.asarray(working.values)
    if values.ndim != 2:
        values = np.squeeze(values)
    if values.ndim != 2:
        raise ValueError("Could not reduce data array to 2D field for point extraction")

    if values.shape != lat2d.shape or values.shape != lon2d.shape:
        raise ValueError(
            f"Field/grid shape mismatch: values={values.shape} lat={lat2d.shape} lon={lon2d.shape}"
        )

    return values, lat2d, lon2d


def extract_point_value(
    dataset: Any,
    canonical_name: str,
    target_lat: float,
    target_lon: float,
    search_max_km: float,
    level_label: Optional[str] = None,
) -> PointExtraction:
    data_array = _pick_data_array(dataset, canonical_name)
    units = str(data_array.attrs.get("units", ""))
    source_var = str(data_array.name)
    values, lat2d, lon2d = _prepare_field_and_grid(data_array, level_label=level_label)

    lon180 = np.vectorize(normalize_lon180)(lon2d)
    target_lon180 = normalize_lon180(target_lon)
    distances = haversine_km(lat2d, lon180, target_lat, target_lon180)
    flat_idx = np.argsort(distances, axis=None)

    first_idx = flat_idx[0]
    fallback = False
    for rank, idx in enumerate(flat_idx):
        r, c = np.unravel_index(int(idx), values.shape)
        dist = float(distances[r, c])
        if dist > search_max_km:
            break
        value = values[r, c]
        if np.isnan(value):
            continue
        if rank > 0:
            fallback = True
        return PointExtraction(
            value=float(value),
            grid_lat=float(lat2d[r, c]),
            grid_lon=float(normalize_lon180(float(lon2d[r, c]))),
            distance_km=dist,
            used_fallback_point=fallback,
            units=units,
            source_var=source_var,
        )

    r0, c0 = np.unravel_index(int(first_idx), values.shape)
    nearest_distance = float(distances[r0, c0])
    raise ValueError(
        "No non-NaN gridpoint found within search_max_km="
        f"{search_max_km}. nearest_distance_km={nearest_distance:.3f}"
    )
