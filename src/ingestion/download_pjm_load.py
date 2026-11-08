import os
import json
import requests
from pathlib import Path
import pandas as pd

# Locate the repository root directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Google Drive storage location
GOOGLE_DRIVE_DIR = (
    Path.home() / "Library/CloudStorage/GoogleDrive-calebar@umich.edu"
    / "My Drive/grid-stress-data/raw/pjm_load"
)

# Use Google Drive by default, or an explicitly configured location
RAW_DATA_DIR = Path(
    os.environ.get("GRID_STRESS_RAW_DIR", str(GOOGLE_DRIVE_DIR))
)

def save_raw_data(df: pd.DataFrame, filename: str) -> Path:
    """
    Save acquired data without project-specific transformations.
    """
    # Ensure the raw data directory exists
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_path = RAW_DATA_DIR / filename
    df.to_csv(output_path, index=False)

    print(f"Saved raw data to {output_path}")

    return output_path



# PJM hourly metered load endpoint
ENDPOINT = "hrl_load_metered"

def download_pjm_load_data(base_url, start_ept, end_ept, api_key, raw_dir):
    """
    Download PJM hourly metered load data.

    Configuration is provided by main.py.
    """
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({
        'Ocp-Apim-Subscription-Key': api_key,
        'Accept': 'application/json'
    })

    print("Downloading PJM hourly metered load data...")
    print(f"Date range: {start_ept} to {end_ept}")

    # Download all availabe pages
    records = []
    page_size = 1000
    start_row = 1
    total_rows = None

    while True:
        params = {
            "datetime_beginning_ept": f"{start_ept} to {end_ept}",
            "zone": "DOM",
            "rowCount": page_size,
            "startRow": start_row
        }

        response = session.get(
            f"{base_url}/{ENDPOINT}",
            params=params,
            timeout=120
        )

        response.raise_for_status()
        data = response.json()

        page_records = data.get("items", [])

        if total_rows is None:
            total_rows = int(data["totalRows"])
            print(f"Total matching records: {total_rows}")

        if not page_records:
            break

        records.extend(page_records)

        print(f"Download {len(records)} of {total_rows} records")

        if len(records) >= total_rows:
            break

        start_row += len(page_records)

    if len(records) != total_rows:
        raise ValueError(
            f"Incomplete download: expected {total_rows}, "
            f"receiced {len(records)}."
        )

    if not records:
        raise RuntimeError("No records returned from the PJM API.")

    # Save consolidated API records from all pages
    json_file = raw_dir / "pjm_dom_hourly_load.json"

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "totalRows": total_rows,
                "items": records
            },
            f,
            indent=2

        )

    # Save hourly records as CSV
    df = pd.DataFrame(records)
    csv_file = raw_dir / "pjm_dom_hourly_load.csv"
    df.to_csv(csv_file, index=False)

    print("JSON saved:" , json_file)
    print("CSV saved:" , csv_file)
    print("Download complete.")

    return df

if __name__ == "__main__":
    print("PJM Load Ingestion Pipeline")
    print(f"Raw Data Directory: {RAW_DATA_DIR}")

    """
    Synthetic data for testing storage only
    test_data = pd.DataFrame({
        "datetime":[
            "2024-01-01 00:00:00",
            "2024-01-01 01:00:00",
            "2024-01-01 02:00:00"
            ],
            "zone": ["DOM", "DOM", "DOM"],
                "load_mw": [15000, 15200, 14800]
        })

    save_raw_data(test_data, "test_pjm_load.csv")

    """