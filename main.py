from pathlib import Path
from datetime import datetime
import os
import pandas as pd

from dotenv import load_dotenv

from src.ingestion.download_pjm_load import download_pjm_load_data
from src.cleaning.validate_pjm_load import validate_pjm_load
from src.utils.date_ranges import generate_monthly_ranges

# ---------------------------
# Project configuration
# ---------------------------

PROJECT_ROOT = Path(__file__).resolve().parent

# Load API credentials from local .env file
load_dotenv(PROJECT_ROOT / '.env')

API_KEY = os.getenv('PJM_API_KEY')

if not API_KEY:
    raise RuntimeError('PJM_API_KEY is missing. Configure it as an environment variable')

# ---------------------------
# PJM API configuration
# ---------------------------
BASE_URL = 'https://api.pjm.com/api/v1'

START_EPT = '12-01-2023 00:00'
END_EPT = '12-31-2023 23:00'

# ---------------------------
# Main pipeline
# ---------------------------

def main():
    print ("Starting PJM Data pipeline...")
    print(f"Date range: {START_EPT} to {END_EPT}")
    print("PJM API credentials loaded successfully.")

    # Generate monthly date ranges
    monthly_ranges = generate_monthly_ranges(START_EPT, END_EPT)

    for month_start, month_end in monthly_ranges:
        print(f"\nProcessing: {month_start} to {month_end}")

        # Generate monthly output directory
        start_date = datetime.strptime(month_start, "%m-%d-%Y %H:%M")
        month_folder = start_date.strftime("%Y-%m")

        google_drive_root = Path(
            os.environ["GRID_STRESS_RAW_DIR"]
        )

        raw_dir = google_drive_root / month_folder

        # Check whether monthly files already exist
        csv_file = raw_dir / "pjm_dom_hourly_load.csv"
        json_file = raw_dir / "pjm_dom_hourly_load.json"

        if csv_file.is_file() and json_file.is_file():
            print(f"Existing monthly files found: {month_folder}")

            existing_df = pd.read_csv(csv_file)

            validate_pjm_load(
                existing_df,
                start_ept=month_start,
                end_ept=month_end
            )

            print(f"Existing data validated: {month_folder}")
            continue

        # Step 1: Download hourly metered load data
        df_load = download_pjm_load_data(
            base_url=BASE_URL,
            start_ept=month_start,
            end_ept=month_end,
            api_key=API_KEY,
            raw_dir=raw_dir
        )

        print(f"PJM hourly load downloaded: {len(df_load)} rows")

        # Step 2: Validate hourly metered load data
        validate_pjm_load(
            df_load,
            start_ept=month_start,
            end_ept=month_end
        )

    # Future pipeline stages:
    # 1. Download hourly metered load
    # 2. Download historical load
    # 3. Download generation outages
    # 4. Download congestion data
    # 5. Clean and validate datasets
    # 6. Merge datasets
    # 7. Save analysis-ready dataset for modeling

if __name__ == "__main__":
    main()
