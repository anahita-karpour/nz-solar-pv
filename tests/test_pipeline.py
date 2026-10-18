import sqlite3

import pandas as pd

from solar import ingest, pipeline


def fake_payload():
    return {"outputs": {"hourly": [
        {"time": "20200101:0010", "P": 0.0, "G(i)": 0.0, "T2m": 14.0, "WS10m": 3.0},
        {"time": "20200101:0110", "P": 90.0, "G(i)": 120.0, "T2m": 15.0, "WS10m": 2.0},
    ]}}


def test_pipeline_loads_good_locations_and_skips_failures(monkeypatch, tmp_path):
    def fake_fetch(lat, lon, *args, **kwargs):
        if lat > 0:  # pretend this location's request fails
            raise ingest.PVGISError("simulated failure")
        return fake_payload()

    monkeypatch.setattr(ingest, "fetch_pvgis", fake_fetch)
    db = tmp_path / "test.db"
    locations = {"Good": (-41.0, 174.0), "Bad": (10.0, 10.0)}

    result = pipeline.run(db_path=str(db), locations=locations)

    assert result == {"loaded": 1, "skipped": ["Bad"]}
    with sqlite3.connect(db) as conn:
        rows = pd.read_sql("SELECT * FROM hourly_pv", conn)
    assert set(rows["location"]) == {"Good"}
    assert len(rows) == 2
