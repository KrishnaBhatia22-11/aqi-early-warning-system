"""Calendar-date parsing shared by audits and forecast construction."""

from __future__ import annotations

import re

import pandas as pd

_TIMEZONE_SUFFIX = re.compile(
    r"(?:T|\s)\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}(?::?\d{2})?)\s*$",
    flags=re.IGNORECASE,
)


def parse_calendar_dates(values: pd.Series, *, field_name: str) -> pd.Series:
    """Parse mixed date formats and normalize to naive calendar-day values.

    Time-zone-aware values are rejected because converting them could move an
    observation to a different calendar day and change daily AQI alignment.
    """
    if isinstance(values.dtype, pd.DatetimeTZDtype):
        raise ValueError(f"{field_name} must be timezone-naive calendar dates")
    text = values.astype("string")
    if text.str.contains(_TIMEZONE_SUFFIX, na=False).any():
        raise ValueError(f"{field_name} must be timezone-naive calendar dates")

    parsed = pd.to_datetime(values, format="mixed", errors="coerce")
    if isinstance(parsed.dtype, pd.DatetimeTZDtype):
        raise ValueError(f"{field_name} must be timezone-naive calendar dates")
    return parsed.dt.normalize()
