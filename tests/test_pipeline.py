import sqlite3
import pandas as pd
from solar import ingest, pipeline, validate


def fake_payload(): #fake download that returns two hourly rows for a location
    return {"outputs": {"hourly": [
        {"time": "20200101:0010", "P": 0.0, "G(i)": 0.0, "T2m": 14.0, "WS10m": 3.0},
        {"time": "20200101:0110", "P": 90.0, "G(i)": 120.0, "T2m": 15.0, "WS10m": 2.0},
    ]}}


def bad_payload(): #fake download that returns two hourly rows for a location with negative power to fail the CHECKS.
    return {"outputs": {"hourly": [
        {"time": "20200101:0010", "P": -5.0, "G(i)": 0.0, "T2m": 14.0, "WS10m": 3.0},
        {"time": "20200101:0110", "P": 90.0, "G(i)": 120.0, "T2m": 15.0, "WS10m": 2.0},
    ]}}


def test_pipeline_loads_good_locations_and_skips_failures(monkeypatch, tmp_path):
    def fake_fetch(lat, lon, *args, **kwargs):
        if lat > 0:  # pretend this location's request fails
            raise ingest.PVGISError("simulated failure")
        return fake_payload()

    monkeypatch.setattr(ingest, "fetch_pvgis", fake_fetch)
    monkeypatch.setattr(validate, "CHECKS",
                        #for validate.CHECKS use a list of checks that don't depend on the number of rows.
                        [validate.check_missing_values,
                         validate.check_duplicate_timestamps,
                         validate.check_night_time_power,
                         validate.check_value_ranges])

    db = tmp_path / "test.db"
    locations = {"Good": (-41.0, 174.0), "Bad": (10.0, 10.0)}
    result = pipeline.run(db_path=str(db), locations=locations)

    assert result == {"loaded": 1, "skipped": ["Bad"]} #Bad means a failed download
    with sqlite3.connect(db) as conn:
        rows = pd.read_sql("SELECT * FROM hourly_pv", conn)
    assert set(rows["location"]) == {"Good"}
    assert len(rows) == 2


def test_pipeline_skips_location_that_fails_validation(monkeypatch, tmp_path):
    def fake_fetch(lat, lon, *args, **kwargs): #it doesn't raise an error, it returns data for both locations.
        if lat < -50:
            return bad_payload()
        return fake_payload()
    monkeypatch.setattr(ingest, "fetch_pvgis", fake_fetch)
    monkeypatch.setattr(validate, "CHECKS",[validate.check_value_ranges])#only one check since the test is about this check
    db = tmp_path / "test.db"
    locations = {"Good": (-41.0, 174.0), "BadData": (-52, 10.0)} #BadData: means data that fails a check
    result = pipeline.run(db_path=str(db), locations=locations)
    assert result == {"loaded": 1, "skipped": ["BadData"]}
    with sqlite3.connect(db) as conn:
        rows = pd.read_sql("SELECT * FROM hourly_pv", conn)
    assert set(rows["location"]) == {"Good"}