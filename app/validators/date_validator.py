from datetime import datetime, date
import re


def normalize_date(value: str) -> str:
    parts = re.findall(r"\d+", value)
    if len(parts) != 3:
        return value.strip()
    day, month, year = parts
    if len(year) == 2:
        year = ("19" if int(year) > date.today().year % 100 else "20") + year
    return f"{int(day):02d}.{int(month):02d}.{int(year):04d}"


def validate_date(value: str) -> bool:
    try:
        parsed = datetime.strptime(value, "%d.%m.%Y").date()
        return date(1900, 1, 1) <= parsed <= date.today()
    except (ValueError, TypeError):
        return False
