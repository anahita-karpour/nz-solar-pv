import pandas as pd
import pytest
import requests

from solar import ingest
from solar.ingest import PVGISError


class FakeResponse:
    ok = True #pretend the status code is good

    def json(self):
        return {"outputs": {"hourly": []}} #pretend this is the PVGIS data


class FakeBadResponse:
    ok = False  #pretend the status code is bad
    status_code = 500
    text = "server error"

    def raise_for_status(self):
        raise requests.HTTPError("500 Server Error")


def test_parse_renames_columns_and_parses_timestamps():
    payload = {"outputs": {"hourly": [{"time": "20200101:0010", "P": 0.0, "G(i)": 0.0, "H_sun": 0.0,
         "T2m": 14.2, "WS10m": 3.1, "Int": 0.0},
        {"time": "20200101:0110", "P": 120.5, "G(i)": 150.0, "H_sun": 20.0,
         "T2m": 15.0, "WS10m": 2.8, "Int": 0.0},
    ]}} #two hourly rows, same shape as a real PVGIS response

    df = ingest.parse_pvgis_response(payload)

    assert list(df.columns) == ["timestamp", "power_w", "irradiance_wm2",
                                "temp_c", "wind_ms"]
    assert len(df) == 2
    assert df["timestamp"].iloc[0] == pd.Timestamp("2020-01-01 00:10", tz="UTC")


def test_parse_rejects_unexpected_structure():
    payload = {"something": "else"}     #no "outputs" key
    with pytest.raises(PVGISError):
        ingest.parse_pvgis_response(payload)


def test_parse_rejects_empty_hourly_list():
    payload = {"outputs": {"hourly": []}} #right structure but no rows
    with pytest.raises(PVGISError):
        ingest.parse_pvgis_response(payload)


def test_parse_rejects_records_without_time_column():
    payload = {"outputs": {"hourly": [{"P": 1.0}]}} #one row and no "time" key
    with pytest.raises(PVGISError):
        ingest.parse_pvgis_response(payload)


def test_fetch_wraps_network_errors(monkeypatch):
    def boom(*args, **kwargs):
        raise requests.ConnectionError("no network")

    monkeypatch.setattr(ingest.requests, "get", boom)

    with pytest.raises(PVGISError):      #inside this block expect error
        ingest.fetch_pvgis(-41.29, 174.78)


def test_fetch_returns_json_when_response_ok(monkeypatch):
    def fake_get(*args, **kwargs):
        return FakeResponse() #a good response, not a network error
    monkeypatch.setattr(ingest.requests, "get", fake_get)
    result = ingest.fetch_pvgis(-41.29, 174.78)
    assert result == {"outputs": {"hourly": []}}


def test_fetch_raises_pvgis_error_when_response_not_ok(monkeypatch):
    def fake_get(*args, **kwargs):
        return FakeBadResponse()

    monkeypatch.setattr(ingest.requests, "get", fake_get)

    with pytest.raises(PVGISError):
        ingest.fetch_pvgis(-41.29, 174.78)