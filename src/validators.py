"""Input validation for WasteLess AI.

Every user-supplied value that reaches the database passes through these
helpers first. They raise ValueError with a human-readable message.
"""

from __future__ import annotations

import re
from datetime import date, datetime

VALID_CATEGORIES = [
    "Produce",
    "Dairy & Eggs",
    "Meat & Seafood",
    "Bakery",
    "Pantry",
    "Frozen",
    "Beverages",
    "Other",
]

VALID_LOCATIONS = ["Fridge", "Freezer", "Pantry", "Cupboard", "Counter", "Other"]

VALID_UNITS = [
    "pcs", "g", "kg", "ml", "l", "cup", "tbsp", "tsp", "slice", "bunch", "can", "pack",
]

VALID_DATE_TYPES = ["best_before", "use_by", "user"]
DATE_TYPE_LABELS = {
    "best_before": "Best before (quality guidance)",
    "use_by": "Use by (safety-critical label)",
    "user": "User-entered date",
}

_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 .'&()\-]{0,79}$")


def clean_text(value: str | None, field: str = "value", max_len: int = 120) -> str:
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{field} cannot be empty.")
    if len(text) > max_len:
        raise ValueError(f"{field} is too long (max {max_len} characters).")
    if not _NAME_RE.match(text) and field == "name":
        raise ValueError(
            "Name may only contain letters, numbers, spaces and . ' & ( ) -"
        )
    return text


def validate_name(value: str | None) -> str:
    return clean_text(value, field="name", max_len=80)


def validate_quantity(value) -> float:
    try:
        qty = float(value)
    except (TypeError, ValueError):
        raise ValueError("Quantity must be a number.") from None
    if qty != qty or qty in (float("inf"), float("-inf")):
        raise ValueError("Quantity must be a finite number.")
    if qty <= 0:
        raise ValueError("Quantity must be greater than zero.")
    if qty > 100000:
        raise ValueError("Quantity is unreasonably large.")
    return round(qty, 3)


def validate_unit(value: str | None) -> str:
    unit = (value or "pcs").strip().lower()
    if unit not in VALID_UNITS:
        raise ValueError(f"Unit must be one of: {', '.join(VALID_UNITS)}")
    return unit


def validate_category(value: str | None) -> str:
    cat = (value or "Other").strip()
    if cat not in VALID_CATEGORIES:
        raise ValueError(f"Category must be one of: {', '.join(VALID_CATEGORIES)}")
    return cat


def validate_location(value: str | None) -> str:
    loc = (value or "Pantry").strip()
    if loc not in VALID_LOCATIONS:
        raise ValueError(f"Location must be one of: {', '.join(VALID_LOCATIONS)}")
    return loc


def validate_date_type(value: str | None) -> str:
    dt = (value or "user").strip()
    if dt not in VALID_DATE_TYPES:
        raise ValueError("Date type must be best_before, use_by or user.")
    return dt


def validate_iso_date(value, field: str = "date", allow_none: bool = False) -> str | None:
    if value in (None, ""):
        if allow_none:
            return None
        raise ValueError(f"{field} is required.")
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"{field} '{text}' is not a valid date (use YYYY-MM-DD).")


def validate_price(value, allow_none: bool = True) -> float | None:
    if value in (None, ""):
        if allow_none:
            return None
        raise ValueError("Price is required.")
    try:
        price = float(value)
    except (TypeError, ValueError):
        raise ValueError("Price must be a number.") from None
    if price < 0:
        raise ValueError("Price cannot be negative.")
    if price > 100000:
        raise ValueError("Price is unreasonably large.")
    return round(price, 2)


def validate_threshold(value) -> float:
    try:
        t = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(t, 100000.0))
