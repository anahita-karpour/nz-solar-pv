from pathlib import Path

"""Project settings:
    which locations to analyse
    and how to query PVGIS."""

# name -> (latitude, longitude)
LOCATIONS = {
    "Auckland": (-36.85, 174.76),
    "Wellington": (-41.31, 174.81),
    "Christchurch": (-43.53, 172.64),
}

PROJECT_ROOT = Path(__file__).resolve().parents[2] #inner nz-solar-pv folder

DB_PATH = PROJECT_ROOT / "data" / "solar.db"
START_YEAR = 2019
END_YEAR = 2023           # keep to years the chosen database covers
PEAK_POWER_KW = 1.0       # modelled system size
SYSTEM_LOSS_PCT = 14.0    # system losses assumed in the PV model
RAD_DATABASE = "PVGIS-ERA5"  # global reanalysis data

# print("Config has been run")