"""Parsing helpers for Brazilian boleto fields."""

import re
from datetime import datetime

DATE_FORMATS = ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d")


def parse_value_to_cents(value_str: str | None) -> int | None:
    """Parse a Brazilian currency string to cents.

    Args:
        value_str: Value string like "199,00" or "1.234,56".

    Returns:
        Value in cents (19900) or None if parsing fails.
    """
    if not value_str:
        return None

    try:
        cleaned = re.sub(r"[^\d,]", "", value_str)
        cleaned = cleaned.replace(",", ".")
        return int(float(cleaned) * 100)
    except (ValueError, AttributeError):
        return None


def parse_due_date(date_str: str | None) -> datetime | None:
    """Parse a Brazilian date string to datetime.

    Args:
        date_str: Date string like "15/01/2026".

    Returns:
        Datetime object or None if parsing fails.
    """
    if not date_str:
        return None

    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None
