import pandas as pd
import pytest
import requests

from solar import ingest


@pytest.fixture
def sample_payload():
    """A tiny fake PVGIS response (same shape as the real one)."""
    return {"outputs": {"hourly": [
        {"time": "20200101:0010", "P": 0.0, "G(i)": 0.0, "H_sun": 0.0,
         "T2m": 14.2, "WS10m": 3.1, "Int": 0.0},
        {"time": "20200101:0110", "P": 120.5, "G(i)": 150.0, "H_sun": 20.0,
         "T2m": 15.0, "WS10m": 2.8, "Int": 0.0},
    ]}}


def test_parse_renames_columns_and_parses_timestamps(sample_payload):
    df = ingest.parse_pvgis_response(sample_payload)

    assert list(df.columns) == ["timestamp", "power_w", "irradiance_wm2",
                                "temp_c", "wind_ms"]
    assert len(df) == 2
    assert df["timestamp"].iloc[0] == pd.Timestamp("2020-01-01 00:10", tz="UTC")


def test_parse_rejects_unexpected_structure():
    with pytest.raises(ingest.PVGISError):
        ingest.parse_pvgis_response({"something": "else"})


def test_parse_rejects_empty_hourly_list():
    with pytest.raises(ingest.PVGISError):
        ingest.parse_pvgis_response({"outputs": {"hourly": []}})


def test_fetch_wraps_network_errors(monkeypatch):
    def boom(*args, **kwargs):
        raise requests.ConnectionError("no network")

    monkeypatch.setattr(ingest.requests, "get", boom)

    with pytest.raises(ingest.PVGISError):
        ingest.fetch_pvgis(-41.29, 174.78)
