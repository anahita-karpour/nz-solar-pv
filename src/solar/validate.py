"""Data quality checks.

Every check takes a DataFrame and returns a list of problem descriptions.
An empty list means the check passed.
"""
import pandas as pd
from solar import config

def check_missing_values(df, columns=None):
    """Report any column that contains missing values."""
    if columns is None:
        columns = [c for c in df.columns if c != "timestamp"]
    problems = []
    for col in columns:
        n_missing = int(df[col].isna().sum())
        if n_missing:
            problems.append(f"{col}: {n_missing} missing values")
    return problems

def check_duplicate_timestamps(df):
    """Report timestamps that appear more than once."""
    problems = []
    n_duplicates = int(df["timestamp"].duplicated().sum()) # how many repeated timestamps?
    if n_duplicates:
        problems.append(f"{n_duplicates} duplicate timestamps")
    return problems

def check_night_time_power(df):
    """Report hours where irradiance is zero but power output is not."""
    problems = []
    n_bad = int(((df["irradiance_wm2"] == 0) & (df["power_w"] > 0)).sum())
    if n_bad:
        problems.append(f"{n_bad} hours where irradiance is zero but power output is not.")
    return problems

# --- TODO: -------------------------------------------------------
# Write these, add each one to CHECKS below, and write tests for them in
# tests/test_validate.py (one test for "passes on clean data", one for
# "catches the problem").

def check_expected_hours(df, start_year = config.START_YEAR, end_year = config.END_YEAR):
    """Report if the number of hourly rows doesn't match the years requested
    (leap years: 2020 has 366 days)."""
    expected_hours = len(pd.date_range(f"{start_year}-01-01", #turns the year 2019 into the date string "2019-01-01"
                                       f"{end_year}-12-31 23:00", #the last hour of the last day, with midnight we will be 23 hours short.
                                       freq="h")) #builds one timestamp per hour between these two dates (counting leap years)
                                                # len will return the number of hours
    actual_hours = len(df) # number of rows we have
    if actual_hours != expected_hours:
        return [f"expected {expected_hours} hourly rows for {start_year} - {end_year}, "
                f"got {actual_hours}"] # both numbers in the message
    return []


def check_value_ranges(df):
    """Report physically impossible values, e.g. negative power or irradiance."""
    raise NotImplementedError



# Checks that run automatically. Add yours here once they're written.
CHECKS = [check_missing_values, check_duplicate_timestamps, check_night_time_power, check_expected_hours]


def run_all_checks(df):
    """Run every registered check and return all problems found."""
    problems = []
    for check in CHECKS:
        problems.extend(check(df))
    return problems
