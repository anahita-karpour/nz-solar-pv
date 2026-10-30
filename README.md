# NZ Solar PV Pipeline

![tests](https://github.com/anahita-karpour/nz-solar-pv/actions/workflows/ci.yml/badge.svg)

A small data pipeline that pulls modelled hourly solar PV output for several
New Zealand locations from the EU's PVGIS service, validates it, and stores
it in SQLite. It is the foundation for a larger NZ Solar PV Performance & ROI
analyser (comparison across locations, payback calculator, Streamlit
dashboard) which is still to be built.

## Pipeline

    PVGIS API -> parse into DataFrame -> data quality checks -> SQLite

- `src/solar/ingest.py`: fetches and parses PVGIS responses; network
  failures and malformed responses raise a clear `PVGISError`.
- `src/solar/validate.py`: data quality checks (missing values, duplicate
  timestamps, expected row count, night-time output, value ranges).
- `src/solar/pipeline.py`: runs everything per location. A location that
  fails to download or fails validation is skipped and logged, and re-running
  replaces the table (so it is safe to run repeatedly).
- `tests/`: pytest tests. Network calls are replaced with fake data, so tests
  run offline.

## Run it

    python -m venv .venv
    .venv\Scripts\activate          # Windows
    pip install -r requirements.txt
    pytest
    set PYTHONPATH=src              # Windows cmd (PowerShell: $env:PYTHONPATH="src")
    python -m solar.pipeline

In PyCharm, right-click the `src` folder and choose Mark Directory as >
Sources Root instead of setting PYTHONPATH.

## Status

- [x] Ingestion, parsing, error handling
- [x] Pipeline and SQLite storage
- [x] Data quality checks (missing values, duplicates, expected row count, night-time output)
- [x] Value-range check (physically impossible values)
- [ ] Location comparison and ROI calculator
- [ ] Streamlit dashboard

Data: PVGIS, European Commission Joint Research Centre.
