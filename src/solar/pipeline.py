"""Fetch -> parse -> validate -> store, for every configured location."""
# print("__name__ is: ", __name__)

import logging
import sqlite3
import pandas as pd
from pathlib import Path
from solar import config, ingest, validate

log = logging.getLogger(__name__)


def run(db_path=config.DB_PATH, locations=None):
    """Load validated data for each location into SQLite.

    A location that fails to download or fails validation is skipped and
    logged, so one bad location doesn't stop the others. Re-running replaces
    the table, so the pipeline is safe to run repeatedly.
    """
    locations = locations or config.LOCATIONS
    good_frames, skipped = [], []

    for name, (lat, lon) in locations.items():
        try:
            payload = ingest.fetch_pvgis(lat, lon)
            df = ingest.parse_pvgis_response(payload)
        except ingest.PVGISError as ex:
            log.error("Skipping %s: %s", name, ex)
            skipped.append(name)
            continue

        problems = validate.run_all_checks(df)
        if problems:
            log.error("Skipping %s: failed validation: %s", name, "; ".join(problems))
            skipped.append(name)
            continue

        good_frames.append(df.assign(location=name))
        log.info("Validated %s: %d rows", name, len(df))

    if good_frames:
        combined = pd.concat(good_frames, ignore_index=True)
        # SQLite has no timezone type, so store timestamps as ISO text
        combined["timestamp"] = combined["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(db_path) as conn:
            combined.to_sql("hourly_pv", conn, if_exists="replace", index=False)

    log.info("Done: %d loaded, %d skipped", len(good_frames), len(skipped))
    return {"loaded": len(good_frames), "skipped": skipped}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    run()
