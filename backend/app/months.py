import re
from datetime import date

from fastapi import HTTPException

MONTH_PATTERN = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")


def parse_month(value: str | None) -> date:
    """Parse "YYYY-MM" into the first day of that month; default to the current month."""
    if value is None:
        return date.today().replace(day=1)
    match = MONTH_PATTERN.match(value)
    if not match:
        raise HTTPException(status_code=422, detail="month must be in YYYY-MM format")
    return date(int(match.group(1)), int(match.group(2)), 1)


def add_months(first_of_month: date, months: int) -> date:
    index = first_of_month.year * 12 + first_of_month.month - 1 + months
    return date(index // 12, index % 12 + 1, 1)


def month_label(first_of_month: date) -> str:
    return first_of_month.strftime("%Y-%m")
