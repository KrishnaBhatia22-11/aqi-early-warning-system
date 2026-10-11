"""Read-only audit for the raw city-day AQI dataset."""

from __future__ import annotations

import hashlib
from io import BytesIO
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from research.aqi_forecasting.protocol import (
    AQI_MAX,
    AQI_MIN,
    TEST_END,
    TEST_START,
    TRAIN_END,
    TRAIN_START,
    VALIDATION_END,
    VALIDATION_START,
)
from research.aqi_forecasting.target_policies import apply_target_policy
from research.aqi_forecasting.date_utils import parse_calendar_dates


def _aqi_counts(raw: pd.Series, numeric: pd.Series) -> dict[str, int]:
    """Count disjoint AQI quality categories using target-policy semantics."""
    missing = raw.isna()
    non_numeric = ~missing & numeric.isna()
    values = numeric.to_numpy(dtype="float64", na_value=float("nan"))
    finite_values = np.isfinite(values)
    finite = pd.Series(finite_values, index=raw.index)
    positive_infinity = numeric.eq(float("inf")).fillna(False)
    negative_infinity = numeric.eq(float("-inf")).fillna(False)
    non_finite = numeric.notna() & ~finite & ~positive_infinity & ~negative_infinity
    negative = finite & numeric.lt(AQI_MIN)
    above_500 = finite & numeric.gt(AQI_MAX)
    valid = finite & numeric.between(AQI_MIN, AQI_MAX, inclusive="both")
    return {
        "missing": int(missing.sum()),
        "non_numeric": int(non_numeric.sum()),
        "negative": int(negative.sum()),
        "valid_0_to_500": int(valid.sum()),
        "above_500": int(above_500.sum()),
        "positive_infinity": int(positive_infinity.sum()),
        "negative_infinity": int(negative_infinity.sum()),
        "other_non_finite": int(non_finite.sum()),
    }


def audit_raw_dataset(path: str | Path) -> dict[str, Any]:
    """Audit raw file identity, panel completeness, missingness, and AQI labels."""
    csv_path = Path(path)
    if not csv_path.is_file():
        raise FileNotFoundError(f"Raw dataset not found: {csv_path}")

    raw_bytes = csv_path.read_bytes()
    try:
        frame = pd.read_csv(BytesIO(raw_bytes))
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise ValueError(f"Could not parse raw CSV snapshot {csv_path}: {exc}") from exc
    required = {"City", "Date", "AQI"}
    missing_columns = sorted(required.difference(frame.columns))
    if missing_columns:
        raise ValueError(f"Raw dataset lacks required columns: {missing_columns}")

    parsed_dates = parse_calendar_dates(frame["Date"], field_name="Date")
    valid_dates = parsed_dates.notna()
    key_frame = pd.DataFrame({"City": frame["City"], "Date": parsed_dates})
    valid_key_frame = key_frame.loc[valid_dates]
    duplicate_mask = valid_key_frame.duplicated(["City", "Date"], keep=False)
    duplicate_key_rows = int(duplicate_mask.sum())
    duplicate_key_excess = int(valid_key_frame.duplicated(["City", "Date"]).sum())
    duplicate_city_day_keys = [
        {"city": str(city), "date": date.date().isoformat(), "row_count": int(count)}
        for (city, date), count in valid_key_frame.loc[duplicate_mask].groupby(
            ["City", "Date"], sort=True
        ).size().items()
    ]

    city_coverage: dict[str, Any] = {}
    valid_keys = key_frame.loc[valid_dates & frame["City"].notna()]
    for city, group in valid_keys.groupby("City", sort=True):
        city_dates = pd.DatetimeIndex(group["Date"].drop_duplicates().sort_values())
        calendar_days = int((city_dates.max() - city_dates.min()).days + 1) if len(city_dates) else 0
        city_coverage[str(city)] = {
            "rows_with_valid_date": int(len(group)),
            "unique_dates": int(len(city_dates)),
            "first_date": city_dates.min().date().isoformat() if len(city_dates) else None,
            "last_date": city_dates.max().date().isoformat() if len(city_dates) else None,
            "missing_calendar_dates_within_observed_span": max(0, calendar_days - len(city_dates)),
        }

    numeric_aqi = pd.to_numeric(frame["AQI"], errors="coerce")
    aqi_counts = _aqi_counts(frame["AQI"], numeric_aqi)

    partitions = {
        "train": (TRAIN_START, TRAIN_END),
        "validation": (VALIDATION_START, VALIDATION_END),
        "test": (TEST_START, TEST_END),
    }
    target_counts: dict[str, Any] = {}
    for partition, (start, end) in partitions.items():
        mask = valid_dates & parsed_dates.between(start, end, inclusive="both")
        partition_counts = _aqi_counts(frame.loc[mask, "AQI"], numeric_aqi.loc[mask])
        target_counts[partition] = {
            "raw_city_date_rows": int(mask.sum()),
            **partition_counts,
        }

    exclusion, exclusion_metadata = apply_target_policy(frame, "exclude")
    capping, capping_metadata = apply_target_policy(frame, "cap")
    del exclusion, capping

    date_values = parsed_dates.loc[valid_dates]
    return {
        "path": str(csv_path.resolve()),
        "file_size_bytes": len(raw_bytes),
        "sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "rows": int(len(frame)),
        "columns": int(len(frame.columns)),
        "column_names": [str(column) for column in frame.columns],
        "dtypes": {str(column): str(dtype) for column, dtype in frame.dtypes.items()},
        "missing_by_column": {
            str(column): {
                "count": int(count),
                "fraction": float(count / len(frame)) if len(frame) else 0.0,
            }
            for column, count in frame.isna().sum().items()
        },
        "city_labels": sorted(str(city) for city in frame["City"].dropna().unique()),
        "city_count": int(frame["City"].nunique(dropna=True)),
        "invalid_date_rows": int((~valid_dates).sum()),
        "date_min": date_values.min().date().isoformat() if len(date_values) else None,
        "date_max": date_values.max().date().isoformat() if len(date_values) else None,
        "unique_dates": int(date_values.nunique()),
        "duplicate_city_date_rows": duplicate_key_rows,
        "duplicate_city_date_excess": duplicate_key_excess,
        "duplicate_city_day_keys": duplicate_city_day_keys,
        "city_coverage": city_coverage,
        "aqi": {
            **aqi_counts,
            "policy_exclude": exclusion_metadata,
            "policy_cap": capping_metadata,
        },
        "target_counts_by_partition": target_counts,
        "pollutant_missing_counts": {
            str(column): int(frame[column].isna().sum())
            for column in ("PM2.5", "PM10", "NO", "NO2", "NOx", "NH3", "CO", "SO2", "O3", "Benzene", "Toluene", "Xylene")
            if column in frame.columns
        },
    }


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    print(json.dumps(audit_raw_dataset(root / "data" / "raw" / "city_day.csv"), indent=2))


if __name__ == "__main__":
    main()
