from pathlib import Path
import calendar
import pandas as pd

from src.cleaning.validate_pjm_load_all import validate_pjm_load_all

def audit_pjm_files(raw_dir: Path, start_year: int, end_year: int):
    """
    Check whether all expected monthly PJM CSV files exist.
    """

    print("Starting PJM historical data audit...")

    missing_months = []
    found_months = []

    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            month_folder = f"{year}-{month:02d}"
            csv_file = raw_dir / month_folder / "pjm_hourly_load.csv"

            if csv_file.is_file():
                found_months.append(month_folder)
            else:
                missing_months.append(month_folder)

    print(f"Expected months: {(end_year - start_year + 1) * 12}")
    print(f"Found months: {len(found_months)}")
    print(f"Missing months: {len(missing_months)}")

    if missing_months:
        print(f"Missing monthly files: {missing_months}")

    return found_months, missing_months

def audit_pjm_monthly_data(raw_dir: Path, start_year: int, end_year: int):
    """
    Validate each monthly PJM dataset using existing validation rules.
    """
    results = []

    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            month_folder = f"{year}-{month:02d}"
            csv_file = raw_dir / month_folder / "pjm_hourly_load.csv"

            # Determine the expected date boundaries
            last_day = calendar.monthrange(year, month)[1]
            start_ept = f"{month:02d}-01-{year} 00:00"
            end_ept = f"{month:02d}-{last_day:02d}-{year} 23:00"

            print(f"\nAuditing: {month_folder}")

            try:
                df = pd.read_csv(csv_file)

                validate_pjm_load_all(
                    df,
                    start_ept=start_ept,
                    end_ept=end_ept
                )

                results.append({
                    "month": month_folder,
                    "status": "PASS",
                    "records": len(df),
                    "error": ""
                })

            except (FileNotFoundError, ValueError, KeyError, pd.errors.ParserError) as exc:
                print(f"Audit failed for {month_folder}: {exc}")

                results.append({
                    "month": month_folder,
                    "status": "FAIL",
                    "records": None,
                    "error": str(exc)
                })

    return pd.DataFrame(results)

def save_audit_report(report: pd.DataFrame, reports_dir: Path) -> Path:
    """
    Save the PJM monthly data quality audit results as a CSV.
    """

    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)

    report_file = reports_dir / "pjm_load_all_audit_2020_2024.csv"

    report.to_csv(report_file, index=False)

    print(f"Audit report saved: {report_file}")

    return report_file