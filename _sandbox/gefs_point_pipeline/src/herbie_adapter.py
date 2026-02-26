from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List

import pandas as pd

try:
    from herbie import Herbie
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependency: herbie-data. Install requirements in _sandbox/gefs_point_pipeline."
    ) from exc


def _naive_utc(value: dt.datetime) -> dt.datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(dt.timezone.utc).replace(tzinfo=None)


def make_herbie(
    init_time_utc: dt.datetime,
    model: str,
    product: str,
    member: str,
    fxx: int,
    source_priority: List[str],
) -> Any:
    kwargs: Dict[str, Any] = {
        "model": model,
        "product": product,
        "member": member,
        "fxx": int(fxx),
        "priority": source_priority,
        "overwrite": False,
        "verbose": False,
    }
    for candidate in (
        kwargs,
        {k: v for k, v in kwargs.items() if k != "verbose"},
        {k: v for k, v in kwargs.items() if k != "priority"},
        {k: v for k, v in kwargs.items() if k not in {"priority", "verbose"}},
    ):
        try:
            return Herbie(_naive_utc(init_time_utc), **candidate)
        except TypeError:
            continue
    return Herbie(
        _naive_utc(init_time_utc), model=model, product=product, member=member, fxx=int(fxx)
    )


def inventory_frame(handle: Any) -> pd.DataFrame:
    inv = handle.inventory()
    if isinstance(inv, pd.DataFrame):
        return inv
    if inv is None:
        return pd.DataFrame()
    try:
        return pd.DataFrame(inv)
    except Exception:
        return pd.DataFrame()


def xarray_subset(handle: Any, search_string: str) -> Any:
    for method in (
        lambda: handle.xarray(searchString=search_string, remove_grib=False),
        lambda: handle.xarray(search_string, remove_grib=False),
        lambda: handle.xarray(searchString=search_string),
        lambda: handle.xarray(search_string),
    ):
        try:
            return method()
        except TypeError:
            continue
    return handle.xarray(searchString=search_string)


def download_subset(handle: Any, search_string: str) -> Any:
    for method in (
        lambda: handle.download(searchString=search_string, overwrite=False),
        lambda: handle.download(search_string, overwrite=False),
    ):
        try:
            return method()
        except TypeError:
            continue
    return handle.download(searchString=search_string, overwrite=False)
