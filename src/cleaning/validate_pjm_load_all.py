import pandas as pd
from datetime import datetime

def validate_pjm_load_all(
        df: pd.DataFrame,
        start_ept: str,
        end_ept: str
) -> None:

    """
    Validate the PJM hourly metered load data for all regions.

    Raises ValueError if any validation checks fail.
    """
    print("Validating PJM hourly load data...")

    # 1.  Check required columns
    required_columns = {
        "datetime_beginning_utc",
        "zone",
        "load_area",
        "mw"
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # 2 Check missing values
    if df.isnull().any().any():
        raise ValueError("Missing values found in PJM data.")


    # 4. Check electricity demand
    mw = pd.to_numeric(df["mw"], errors="coerce")

    if mw.isna().any() or mw.lt(0).any():
        raise ValueError("Invalid or negative MW values found.")

    # 5. Convert timestamps to UTC
    timestamps = pd.to_datetime(
        df["datetime_beginning_utc"],
        utc=True,
        errors="coerce"

    )

    if timestamps.isna().any():
        raise ValueError("Invalid UTC timestamps found.")

    # 6. Check duplicate records for each zone/load area/hour
    keys = df[["zone", "load_area"]].copy()
    keys["datetime_beginning_utc"] = timestamps

    if keys.duplicated().any():
        raise ValueError("Duplicate zone/load-area/hour records found.")

    # 7. Check missing hourly intervals
    for (zone, load_area), group in keys.groupby(["zone", "load_area"]):
        group_hours = pd.DatetimeIndex(group["datetime_beginning_utc"])

        expected_hours = pd.date_range(
            start=timestamps.min(),
            end=timestamps.max(),
            freq="h"
        )

        missing_hours = expected_hours.difference(group_hours)

        if len(missing_hours) > 0:
            raise ValueError(
                f"Missing {len(missing_hours)} hourly intervals "
                f"for {zone}/{load_area}."
            )

    # 8. Validate requested date boundaries
    date_format = "%m-%d-%Y %H:%M"

    requested_start = datetime.strptime(start_ept, date_format)
    requested_end = datetime.strptime(end_ept, date_format)

    expected_start_utc = (
        pd.Timestamp(requested_start)
        .tz_localize("America/New_York")
        .tz_convert("UTC")
    )

    expected_end_utc = (
        pd.Timestamp(requested_end)
        .tz_localize("America/New_York")
        .tz_convert("UTC")
    )

    # Verify the first timestamp
    if timestamps.min() != expected_start_utc:
        raise ValueError(
            f"Incorrect start boundary: expected {expected_start_utc}, "
            f"received {timestamps.min()}."
        )

    if timestamps.max() != expected_end_utc:
        raise ValueError(
            f"Incorrect end boundary: expected {expected_end_utc}, "
            f"received {timestamps.max()}."
        )


    print(f"Validation successful: {len(df)} hourly records.")