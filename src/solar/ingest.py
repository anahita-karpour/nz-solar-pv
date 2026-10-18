"""Fetch hourly PV data from the PVGIS API and turn it into a tidy Panda DataFrame.


"""
import logging

import pandas as pd
import requests

from solar import config

log = logging.getLogger(__name__)

#API Endpoint and mapping constants
PVGIS_URL = "https://re.jrc.ec.europa.eu/api/v5_3/seriescalc"
# this will ask the api for 1 year of data on Wellington:
#https://re.jrc.ec.europa.eu/api/seriescalc?
        # lat=-41.29&lon=174.78&
        # startyear=2020&
        # endyear=2020&
        # pvcalculation=1&
        # peakpower=1&
        # loss=14&
        # optimalangles=1&
        # raddatabase=PVGIS-ERA5&
        # outputformat=json

# PVGIS column name -> our column name
COLUMN_MAP = {
    "P": "power_w",
    "G(i)": "irradiance_wm2",
    "T2m": "temp_c",
    "WS10m": "wind_ms",
}


class PVGISError(Exception):
    """Raised when PVGIS can't be reached or returns something unusable."""


def fetch_pvgis(lat, lon, start_year=config.START_YEAR,
                end_year=config.END_YEAR, timeout=60):
    """Request hourly modelled PV output for one location; return the JSON."""
    params = {
        "lat": lat,
        "lon": lon,
        "startyear": start_year,
        "endyear": end_year,
        "pvcalculation": 1,
        "peakpower": config.PEAK_POWER_KW,
        "loss": config.SYSTEM_LOSS_PCT,
        "optimalangles": 1,  # let PVGIS choose tilt/azimuth for the site
        "raddatabase": config.RAD_DATABASE,
        "outputformat": "json",
    }
    try:
        response = requests.get(PVGIS_URL, params=params, timeout=timeout)
        if not response.ok:
            log.error("PVGIS returned: %s: %s",
                      response.status_code, response.text
                      )
            response.raise_for_status()
        return response.json() #changes response to Python dictionary(with lists inside it)
    except (requests.RequestException, ValueError) as ex:
        raise PVGISError(f"PVGIS request failed for ({lat}, {lon}): {ex}") from ex


def parse_pvgis_response(payload):
    """Turn a PVGIS JSON payload into a DataFrame with a UTC 'timestamp' column."""
    try:
        records = payload["outputs"]["hourly"]
    except (KeyError, TypeError) as ex:
        raise PVGISError("Unexpected PVGIS response: no outputs.hourly") from ex

    df = pd.DataFrame(records)
    if df.empty or "time" not in df.columns:
        raise PVGISError("PVGIS returned no usable hourly records")

    df["timestamp"] = pd.to_datetime(df["time"], format="%Y%m%d:%H%M", utc=True)
    df = df.rename(columns=COLUMN_MAP)
    keep = ["timestamp"] + [c for c in COLUMN_MAP.values() if c in df.columns]
    return df[keep]
