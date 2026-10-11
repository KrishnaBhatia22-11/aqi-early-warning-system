"""Explicit invariants for forecasting inputs and target-date partitions."""

from __future__ import annotations

import pandas as pd

from research.aqi_forecasting.protocol import PRIMARY_FEATURE_COLUMNS
from research.aqi_forecasting.protocol import AQI_LAGS_DAYS, HORIZONS_DAYS
from research.aqi_forecasting.date_utils import parse_calendar_dates

_LAG_DATE_COLUMNS = {
    0: "aqi_origin_date",
    1: "aqi_lag_1d_date",
    7: "aqi_lag_7d_date",
}


def validate_feature_schema(feature_columns: list[str] | tuple[str, ...]) -> None:
    """Require exactly the approved primary feature schema."""
    actual = tuple(feature_columns)
    if actual != PRIMARY_FEATURE_COLUMNS:
        raise ValueError(
            f"Primary feature schema must be {PRIMARY_FEATURE_COLUMNS}, got {actual}"
        )


def validate_sample_timestamps(samples: pd.DataFrame) -> None:
    """Verify exact target/origin and every exact AQI lag source timestamp."""
    required = {
        "target_date",
        "origin_date",
        "horizon_days",
        "max_aqi_feature_date",
        *_LAG_DATE_COLUMNS.values(),
    }
    missing = required.difference(samples.columns)
    if missing:
        raise ValueError(f"Missing timestamp audit columns: {sorted(missing)}")
    target = parse_calendar_dates(samples["target_date"], field_name="target_date")
    origin = parse_calendar_dates(samples["origin_date"], field_name="origin_date")
    max_feature = parse_calendar_dates(
        samples["max_aqi_feature_date"], field_name="max_aqi_feature_date"
    )
    if target.isna().any() or origin.isna().any() or max_feature.isna().any():
        raise ValueError("Target, origin, and feature dates must be valid")
    invalid_horizons = ~samples["horizon_days"].isin(HORIZONS_DAYS)
    if invalid_horizons.any():
        raise ValueError("Forecast horizons must be one of the approved horizons")
    expected_origin = target - pd.to_timedelta(samples["horizon_days"], unit="D")
    if not origin.eq(expected_origin).all():
        raise AssertionError("Origin date does not equal target date minus horizon")

    lag_dates: list[pd.Series] = []
    for lag_days in AQI_LAGS_DAYS:
        date_column = _LAG_DATE_COLUMNS[lag_days]
        lag_date = parse_calendar_dates(samples[date_column], field_name=date_column)
        if lag_date.isna().any():
            raise ValueError(f"AQI lag timestamp {date_column!r} must be valid")
        expected_lag_date = origin - pd.to_timedelta(lag_days, unit="D")
        if not lag_date.eq(expected_lag_date).all():
            raise AssertionError(
                f"AQI lag timestamp {date_column!r} does not match its required offset"
            )
        if (lag_date > origin).any():
            raise AssertionError(f"AQI lag timestamp {date_column!r} follows forecast origin")
        lag_dates.append(lag_date)
    actual_max = pd.concat(lag_dates, axis=1).max(axis=1)
    if not max_feature.eq(actual_max).all():
        raise AssertionError("Recorded maximum AQI feature date disagrees with lag timestamps")


def validate_partitions(samples: pd.DataFrame) -> None:
    """Ensure dates map to at most one named partition across cities."""
    required = {"City", "target_date", "partition", "horizon_days", "policy"}
    missing = required.difference(samples.columns)
    if missing:
        raise ValueError(f"Samples are missing partition identity columns: {sorted(missing)}")
    assigned = samples.loc[samples["partition"].notna()]
    counts = assigned.groupby("target_date")["partition"].nunique()
    if (counts > 1).any():
        raise AssertionError("Cities on one target date were assigned to different partitions")
    if assigned.duplicated(["City", "target_date", "horizon_days", "policy"]).any():
        raise AssertionError("Duplicate sample identity detected")
