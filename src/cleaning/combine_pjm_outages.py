from pathlib import Path
import pandas as pd

def combine_pjm_outages(raw_dir: Path, start_year: int, end_year: int) -> pd.DataFrame:
    """
    Combine monthly PJM generation outage CSV files into one dataset.
    """
    monthly_data = []

    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            month_folder = f"{year}-{month:02d}"
            csv_file = raw_dir / month_folder / "pjm_outages.csv"

            print(f"Combining: {month_folder}")
            df = pd.read_csv(csv_file)
            monthly_data.append(df)

    combined = pd.concat(monthly_data, ignore_index=True)

    combined["forecast_execution_date_ept"] = pd.to_datetime(
        combined["forecast_execution_date_ept"]
    )

    combined = combined.sort_values(
        "forecast_execution_date_ept"
    ).reset_index(drop=True)

    print(f"Total combined records: {len(combined):,}")

    return combined

def save_combined_pjm_outages(combined: pd.DataFrame, output_dir: Path) -> Path:
    """
    Save the combined PJM generation outage dataset.
    """

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "pjm_outages_2020_2024.csv"

    combined.to_csv(output_file, index=False)

    print(f"Combined dataset saved: {output_file}")

    return output_file