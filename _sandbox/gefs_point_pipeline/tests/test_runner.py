from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.inventory import ResolvedField  # noqa: E402
from src.runner import _is_compatible_success_run, _normalize_xarray_result  # noqa: E402


def test_compatible_success_requires_matching_profile_and_scope() -> None:
    fields = [
        ResolvedField(
            variable_key="precip",
            canonical_name="APCP",
            level_label="surface",
            search_string="APCP:surface",
            product="atmos.5",
            pattern_used="APCP:surface",
            descriptor="x",
            probe_fxx=6,
        )
    ]
    manifest = {
        "status": "success",
        "run_profile": "full",
        "members_requested": ["c00", "p01"],
        "lead_hours_requested": [0, 3, 6],
        "resolved_fields": [
            {
                "product": "atmos.5",
                "canonical_name": "APCP",
                "level_label": "surface",
                "search_string": "APCP:surface",
            }
        ],
    }
    assert _is_compatible_success_run(manifest, "full", ["c00", "p01"], [0, 3, 6], fields)
    assert not _is_compatible_success_run(manifest, "smoke", ["c00", "p01"], [0, 3, 6], fields)
    assert not _is_compatible_success_run(manifest, "full", ["c00"], [0, 3, 6], fields)


def test_normalize_xarray_result_accepts_dataset_and_list() -> None:
    one = object()
    assert _normalize_xarray_result(one) == [one]
    assert _normalize_xarray_result([one, one]) == [one, one]
