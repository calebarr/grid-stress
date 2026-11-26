from pathlib import Path
from datetime import datetime
import argparse
import os
import time
import pandas as pd

from dotenv import load_dotenv

# ---------------------------
# Project configuration
# ---------------------------

PROJECT_ROOT = Path(__file__).resolve().parent

# Load API credentials from local .env file
load_dotenv(PROJECT_ROOT / '.env')

from src.ingestion.download_pjm_load_all import download_pjm_load_all
from src.ingestion.download_pjm_outages import download_pjm_outages
from src.ingestion.download_pjm_congestion import download_pjm_congestion
from src.cleaning import audit_pjm_load_all
from src.cleaning import audit_pjm_outages
from src.cleaning import audit_pjm_congestion
from src.cleaning.combine_pjm_load_all import(
    combine_pjm_load_all,
    save_combined_pjm_load_all
)
from src.cleaning.combine_pjm_outages import(
    combine_pjm_outages,
    save_combined_pjm_outages
)

from src.cleaning.combine_pjm_congestion import(
    combine_pjm_congestion,
    save_combined_pjm_congestion
)
from src.cleaning.validate_pjm_load_all import validate_pjm_load_all
from src.utils.date_ranges import generate_monthly_ranges



# ---------------------------
# PJM API configuration
# ---------------------------
BASE_URL = 'https://api.pjm.com/api/v1'

START_EPT = '01-01-2020 00:00'
END_EPT = '12-31-2024 23:00'

# ---------------------------
# Main pipeline
# ---------------------------

def run_download():

    API_KEY = os.getenv('PJM_API_KEY')

    if not API_KEY:
        raise RuntimeError(
            "PJM_API_KEY is missing. "
            "Configure it in the local .env file."
        )

    print("Starting PJM Data pipeline...")


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
        csv_file = raw_dir / "pjm_hourly_load.csv"
        json_file = raw_dir / "pjm_hourly_load.json"

        if csv_file.is_file() and json_file.is_file():
            print(f"Existing monthly files found: {month_folder}")

            existing_df = pd.read_csv(csv_file)

            validate_pjm_load_all(
                existing_df,
                start_ept=month_start,
                end_ept=month_end
            )

            print(f"Existing data validated: {month_folder}")

        else:

            # Step 1: Download hourly metered load data
            df_load = download_pjm_load_all(
                base_url=BASE_URL,
                start_ept=month_start,
                end_ept=month_end,
                api_key=API_KEY,
                raw_dir=raw_dir
            )

            print(f"PJM hourly load downloaded: {len(df_load)} rows")

            # Step 2: Validate hourly metered load data
            validate_pjm_load_all(
                df_load,
                start_ept=month_start,
                end_ept=month_end
            )

            # Step 3: Pause between monthly API downloads
            print("Waiting 10 seconds before the next month...")
            time.sleep(10)


        # Step 4: Download PJM generation outages
        outage_start = datetime.strptime(
            month_start, "%m-%d-%Y %H:%M"
        ).strftime("%m-%d-%Y")

        outage_end = datetime.strptime(
            month_end, "%m-%d-%Y %H:%M"
        ).strftime("%m-%d-%Y")

        download_pjm_outages(
            start_ept=outage_start,
            end_ept=outage_end
        )

        # Pause between monthly API request
        print("Waiting 10 seconds before the next month...")
        time.sleep(10)

        # Step 5: Download PJM hourly congestion and electricity prices
        download_pjm_congestion(
            start_ept=month_start,
            end_ept=month_end
        )

        print("Waiting 10 seconds before the next month...")
        time.sleep(10)
    print("\nPJM data acquisition completed.")

# ------------------------------
# Stage 2: Audit PJM data
 # ------------------------------

def run_audit():
    print("\nStarting PJM data audit...")

    load_dir = Path(os.environ["GRID_STRESS_RAW_DIR"])
    outages_dir = load_dir.parent / "pjm_outages"
    congestion_dir = load_dir.parent / "pjm_congestion"

    start_year = datetime.strptime(START_EPT, "%m-%d-%Y %H:%M").year
    end_year = datetime.strptime(END_EPT, "%m-%d-%Y %H:%M").year

    reports_dir = PROJECT_ROOT / "reports"

    datasets = [
        ("Hourly Load", load_dir, audit_pjm_load_all),
        ("Generation Outages", outages_dir, audit_pjm_outages),
        ("Congestion", congestion_dir, audit_pjm_congestion)
    ]

    audit_failed = False

    for name, raw_dir, audit_module in datasets:
        print(f"\nAuditing {name}...")

        found, missing = audit_module.audit_pjm_files(
            raw_dir, start_year, end_year
        )

        report = audit_module.audit_pjm_monthly_data(
            raw_dir, start_year, end_year
        )

        audit_module.save_audit_report(report, reports_dir)

        if missing or not report["status"].eq("PASS").all():
            audit_failed = True

    if audit_failed:
        raise RuntimeError("PJM data audit failed. Review audit reports.")

    print("\nAll PJM data audits passed.")

# -------------------------------
# Stage 3: Combine PJM data
# -------------------------------

def run_combine():
    run_audit()

    print("\nCombining PJM historical datasets...")

    load_dir = Path(os.environ["GRID_STRESS_RAW_DIR"])
    outages_dir = load_dir.parent / "pjm_outages"
    congestion_dir = load_dir.parent / "pjm_congestion"

    interim_dir = load_dir.parent.parent / "interim"

    start_year = datetime.strptime(START_EPT, "%m-%d-%Y %H:%M").year
    end_year = datetime.strptime(END_EPT, "%m-%d-%Y %H:%M").year

    # Combine hourly metered load
    print("\nCombining hourly load data...")

    combined_load = combine_pjm_load_all(
        load_dir, start_year, end_year
    )

    save_combined_pjm_load_all(combined_load, interim_dir)
    del combined_load

    # Combine generation outages
    print("\nCombining generation outage data...")

    combined_outages = combine_pjm_outages(
        outages_dir, start_year, end_year
    )

    save_combined_pjm_outages(combined_outages, interim_dir)
    del combined_outages

    # Combine congestion data
    print("\nCombining congestion data...")

    combined_congestion = combine_pjm_congestion(
        congestion_dir, start_year, end_year
    )

    save_combined_pjm_congestion(combined_congestion, interim_dir)
    del combined_congestion

    print("\nAll PJM datasets combined successfully.")

# ---------------------------------
# Command-line interface
# ---------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="PJM historical data pipeline"
    )

    group = parser.add_mutually_exclusive_group()

    group.add_argument(
        "--download", action="store_true",
        help="Download historical PJM data"
    )

    group.add_argument(
        "--audit", action="store_true",
        help="Audit existing PJM data"
    )

    group.add_argument(
        "--combine", action="store_true",
        help="Audit and combine historical PJM data"
    )

    args = parser.parse_args()

    if args.download:
        run_download()
    elif args.audit:
        run_audit()
    elif args.combine:
        run_combine()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
