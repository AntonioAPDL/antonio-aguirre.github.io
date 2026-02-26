from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import datetime as dt

from export_latest_web_json import (  # noqa: E402
    _build_observed_retrospective_payload,
    _build_retrospective_payload,
)


def _point(ts: str, value: float) -> dict:
    return {"t": ts, "v": value}


def test_retrospective_merges_rollforward_and_forecast_points() -> None:
    current_payload = {
        "init_time_utc": "2026-02-24T00:00:00+00:00",
        "precip": {"surface": {"p50": []}},
        "soil_moisture": {"0-0.1 m below ground": {"p50": []}},
    }
    prior_payload = {
        "init_time_utc": "2026-02-23T18:00:00+00:00",
        "precip": {
            "surface": {
                "p10": [_point("2026-02-23T21:00:00+00:00", 0.1)],
                "p50": [_point("2026-02-23T21:00:00+00:00", 1.25)],
                "p90": [_point("2026-02-23T21:00:00+00:00", 2.2)],
                "mean": [_point("2026-02-23T21:00:00+00:00", 1.5)],
            }
        },
        "soil_moisture": {
            "0-0.1 m below ground": {
                "p50": [_point("2026-02-23T21:00:00+00:00", 0.34)],
            }
        },
        "retrospective": {
            "precip": {
                "surface": {
                    "p10": [_point("2026-02-10T00:00:00+00:00", 0.05)],
                    "p50": [
                        _point("2026-02-10T00:00:00+00:00", 0.5),
                        _point("2026-02-23T21:00:00+00:00", 99.0),
                    ],
                    "p90": [_point("2026-02-10T00:00:00+00:00", 0.95)],
                    "mean": [_point("2026-02-10T00:00:00+00:00", 0.6)],
                }
            },
            "soil_moisture": {
                "0-0.1 m below ground": {
                    "p50": [_point("2026-02-10T00:00:00+00:00", 0.3)]
                }
            },
        },
    }

    retro = _build_retrospective_payload(
        current_payload=current_payload,
        prior_payload=prior_payload,
        observation_window_days=20,
    )

    assert retro["window_days"] == 20
    assert retro["start_utc"] == "2026-02-04T00:00:00+00:00"
    assert retro["end_utc"] == "2026-02-24T00:00:00+00:00"

    precip_p50 = retro["precip"]["surface"]["p50"]
    assert precip_p50[0]["t"] == "2026-02-10T00:00:00+00:00"
    assert precip_p50[1]["t"] == "2026-02-23T21:00:00+00:00"
    # Forecast points from prior payload should override duplicated carried values.
    assert precip_p50[1]["v"] == 1.25

    soil_p50 = retro["soil_moisture"]["0-0.1 m below ground"]["p50"]
    assert [point["t"] for point in soil_p50] == [
        "2026-02-10T00:00:00+00:00",
        "2026-02-23T21:00:00+00:00",
    ]


def test_retrospective_drops_points_outside_window() -> None:
    current_payload = {
        "init_time_utc": "2026-02-24T00:00:00+00:00",
        "precip": {"surface": {"p50": []}},
        "soil_moisture": {"0-0.1 m below ground": {"p50": []}},
    }
    prior_payload = {
        "precip": {
            "surface": {
                "p50": [_point("2026-01-30T00:00:00+00:00", 9.0)],
            }
        },
        "soil_moisture": {
            "0-0.1 m below ground": {
                "p50": [_point("2026-01-30T00:00:00+00:00", 0.9)],
            }
        },
        "retrospective": {
            "precip": {"surface": {"p50": [_point("2026-01-31T00:00:00+00:00", 8.0)]}},
            "soil_moisture": {"0-0.1 m below ground": {"p50": [_point("2026-01-31T00:00:00+00:00", 0.8)]}},
        },
    }

    retro = _build_retrospective_payload(
        current_payload=current_payload,
        prior_payload=prior_payload,
        observation_window_days=20,
    )

    assert retro["precip"] == {}
    assert retro["soil_moisture"] == {}


def test_observed_retrospective_from_combined_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "climate_daily_ppt_soil.csv"
    csv_path.write_text(
        "\n".join(
            [
                "timestamp,daily_avg_ppt,daily_avg_soil_ERA5,daily_avg_soil_NWM_SOIL_M,daily_avg_soil_NWM_SOIL_W",
                "2026-02-01,1.2,0.31,0.41,0.42",
                "2026-02-15,2.4,0.33,0.44,0.45",
                "2026-02-24,5.0,0.40,0.50,0.51",
            ]
        ),
        encoding="utf-8",
    )
    payload = _build_observed_retrospective_payload(
        climate_csv_path=csv_path,
        init_time_utc=dt.datetime(2026, 2, 24, 0, 0, tzinfo=dt.timezone.utc),
        observation_window_days=20,
    )
    assert payload["start_utc"] == "2026-02-04T00:00:00+00:00"
    assert payload["end_utc"] == "2026-02-24T00:00:00+00:00"
    assert [p["t"] for p in payload["daily_avg_ppt"]] == ["2026-02-15T00:00:00+00:00"]
    assert payload["daily_avg_soil_ERA5"][0]["v"] == 0.33
    assert payload["daily_avg_soil_NWM_SOIL_M"][0]["v"] == 0.44
    assert payload["daily_avg_soil_NWM_SOIL_W"][0]["v"] == 0.45


def test_observed_retrospective_empty_when_missing_file(tmp_path: Path) -> None:
    payload = _build_observed_retrospective_payload(
        climate_csv_path=tmp_path / "missing.csv",
        init_time_utc=dt.datetime(2026, 2, 24, 0, 0, tzinfo=dt.timezone.utc),
        observation_window_days=20,
    )
    assert payload["daily_avg_ppt"] == []
    assert payload["daily_avg_soil_ERA5"] == []
