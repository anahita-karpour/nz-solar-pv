import numpy as np
import pandas as pd

from solar import validate


def make_clean_df():
    return pd.DataFrame({
        "timestamp": pd.date_range("2020-01-01", periods=3, freq="h", tz="UTC"),
        "power_w": [0.0, 100.0, 200.0],
        "irradiance_wm2": [0.0, 150.0, 300.0],
    })


def test_missing_values_passes_on_clean_data():
    assert validate.check_missing_values(make_clean_df()) == []


def test_missing_values_catches_gaps():
    df = make_clean_df()
    df.loc[1, "power_w"] = np.nan

    problems = validate.check_missing_values(df)

    assert problems == ["power_w: 1 missing values"]

# TODO: add tests for the checks you write (duplicates, expected hours,value ranges, night-time power).
def test_duplicate_timestamps_passes_on_clean_data():
    assert validate.check_duplicate_timestamps(make_clean_df()) == []

def test_duplicate_timestamps_catches_repeated_row():
    df = make_clean_df()
    bad = pd.concat([df, df.iloc[[0]]], ignore_index=True)   # first row added again

    problems = validate.check_duplicate_timestamps(bad)

    assert problems == ['1 duplicate timestamps']

def test_night_time_power_passes_on_clean_data():
    assert validate.check_night_time_power(make_clean_df()) == []

def test_check_night_time_power_catches_non_zero_row():
    df = make_clean_df()

    df.loc[0, "irradiance_wm2"] = 0.0
    df.loc[0, "power_w"] = 50   # location[row 0, column power_w]

    problems = validate.check_night_time_power(df)
    # print(problems)

    assert problems == ['1 hours where irradiance is zero but power output is not.']

def test_expected_hours_passes_on_clean_data():
    assert validate.check_expected_hours(make_clean_df()) == []

def test_check_night_time_power_catches_non_zero_row():
    df = make_clean_df()

    df.loc[0, "irradiance_wm2"] = 0.0
    df.loc[0, "power_w"] = 50   # location[row 0, column power_w]

    problems = validate.check_night_time_power(df)
    # print(problems)

    assert problems == ['1 hours where irradiance is zero but power output is not.']