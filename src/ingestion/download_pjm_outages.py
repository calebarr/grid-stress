import os
import requests
import time
import json
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("PJM_API_KEY")
BASE_URL = "https://api.pjm.com/api/v1"
ENDPOINT = "gen_outages_by_type"

def download_pjm_outages(start_ept, end_ept):
    """
    Download PJM generation outage records for a specified date range.
    Handle pagination and HTTP 429 rate limiting.
    """

    if not API_KEY:
        raise RuntimeError("PJM_API_KEY is missing.")

    raw_dir = os.getenv("GRID_STRESS_RAW_DIR")

    if not raw_dir:
        raise RuntimeError("GRID_STRESS_RAW_DIR is missing.")

    outages_dir = os.path.join(
        os.path.dirname(raw_dir),
        "pjm_outages"
    )

    month_name = pd.to_datetime(start_ept).strftime("%Y-%m")

    month_dir = os.path.join(
        outages_dir,
        month_name
    )

    os.makedirs(month_dir, exist_ok=True)

    json_path = os.path.join(
        month_dir,
        "pjm_outages.json"
    )

    csv_path = os.path.join(
        month_dir,
        "pjm_outages.csv"
    )

    if os.path.exists(csv_path) and os.path.exists(json_path):
        try:
            existing_df = pd.read_csv(csv_path)

            with open(json_path, "r", encoding="utf-8") as file:
                existing_records = json.load(file)

            if (
                isinstance(existing_records, list)
                and len(existing_df) == len(existing_records)
                and len(existing_df) > 0
            ):
                print(f"Existing files verified for {month_name}. Skipping.")
                return

            print(f"Existing files failed validation for {month_name}.")

        except (OSError, ValueError, TypeError, pd.errors.ParserError) as error:
            print(f"Could not validate {month_name}: {error}")

        print(f"Re-downloading {month_name}.")

    all_records = []
    start_row = 1
    page_size = 1000
    max_retries = 4

    params = {
        "forecast_execution_date_ept": f"{start_ept} to {end_ept}",
        "rowCount": page_size,
        "startRow": start_row
    }

    while True:
        params["startRow"] = start_row

        for attempt in range(max_retries):
            try:
                response = requests.get(
                    f"{BASE_URL}/{ENDPOINT}",
                    headers={
                        "Ocp-Apim-Subscription-Key": API_KEY,
                        "Accept": "application/json"
                    },
                    params=params,
                    timeout=(15, 120)
                )

                if response.status_code == 429 or 500 <= response.status_code < 600:
                    response.raise_for_status()

                response.raise_for_status()
                break

            except (requests.exceptions.Timeout,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.HTTPError) as error:

                if isinstance(error, requests.exceptions.HTTPError):
                    status = error.response.status_code

                    if status != 429 and not (500 <= status < 600):
                        raise

                if attempt == max_retries - 1:
                    raise RuntimeError(
                        f"PJM request failed after {max_retries} attempts "
                        f"for {month_name}, starting row {start_row}."
                    ) from error

                wait_seconds = 5 * (2 ** attempt)

                print(
                    f"PJM request failed: {error}. "
                    f"Retrying in {wait_seconds} seconds..."
                )

                time.sleep(wait_seconds)

        data = response.json()

        records = data.get("items", [])
        all_records.extend(records)

        print("Downloaded records:", len(all_records))

        total_rows = data.get("totalRows")

        if not records:
            break

        if total_rows is not None and len(all_records) >= int(total_rows):
            break

        if len(records) < page_size:
            break

        start_row += len(records)
        time.sleep(10)

    print("Total matching records:", total_rows)
    print("Downloaded records:", len(all_records))

    if total_rows is None:
        raise RuntimeError("PJM response is missing totalRows.")

    if len(all_records) != int(total_rows):
        raise RuntimeError(
            f"Incomplete download: expected {total_rows} records, "
            f"but received {len(all_records)}."
        )

    df = pd.DataFrame(all_records)

    df.to_csv(csv_path, index=False)

    print(f"CSV saved to {csv_path}")

    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(all_records, file, indent=2)

    print(f"JSON saved to {json_path}")

    print("\nColumns:")
    print(df.columns.to_list())

    print("\nFirst five records:")
    print(df.head().to_string(index=False))

    return df