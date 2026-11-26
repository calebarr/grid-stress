from pathlib import Path
import pandas as pd

def combine_pjm_load_all(raw_dir: Path, start_year: int, end_year: int) -> pd.DataFrame:
    """
    Combine monthly PJM hourly load CSV files into one DataFrame.
    """

    monthly_data = []

    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            month_folder = f"{year}-{month:02d}"
            csv_file = raw_dir / month_folder / "pjm_hourly_load.csv"

            df = pd.read_csv(csv_file)
            monthly_data.append(df)

    combined_df = pd.concat(monthly_data, ignore_index=True)

    print(f"Combined {len(monthly_data)} monthly files.")
    print(f"Total records: {len(combined_df)}")

    return combined_df

def save_combined_pjm_load_all(
        df: pd.DataFrame,
        interim_dir: Path
) -> Path:
    """
    Save the combined PJM hourly load dataset.
    """
    interim_dir = Path(interim_dir)
    interim_dir.mkdir(parents=True, exist_ok=True)

    output_file = interim_dir / "pjm_hourly_load_2020_2024.csv"

    # Sort records chronologically before saving
    df = df.copy()
    df["datetime_beginning_utc"] = pd.to_datetime(
        df["datetime_beginning_utc"],
        utc=True
    )

    df = df.sort_values(
        "datetime_beginning_utc",
        ignore_index=True
        )

    df.to_csv(output_file, index=False)

    print(f"Combined dataset saved: {output_file}")

    return output_file