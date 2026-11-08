import calendar
from datetime import datetime

def generate_monthly_ranges(start_ept, end_ept):
    """
    Generate monthly PJM date ranges between two dates.

    Returns a list of (month_start, month_end) tuples.
    """

    date_format = "%m-%d-%Y %H:%M"

    start = datetime.strptime(start_ept, date_format)
    end = datetime.strptime(end_ept, date_format)

    if start > end:
        raise ValueError("Start date must not be after end date.")

    monthly_ranges = []
    current = start

    while current <= end:
        last_day = calendar.monthrange(current.year, current.month)[1]

        month_end = current.replace(
            day=last_day,
            hour=23,
            minute=0
        )

        month_end = min(month_end, end)

        monthly_ranges.append((
            current.strftime(date_format),
            month_end.strftime(date_format)
        ))

        # Move to the first day of the next month
        if month_end.month == 12:
            current = month_end.replace(
                year=month_end.year + 1,
                month=1,
                day=1,
                hour=0,
                minute=0
            )

        else:
            current = month_end.replace(
                month=month_end.month + 1,
                day=1,
                hour=0,
                minute=0
            )

    return monthly_ranges