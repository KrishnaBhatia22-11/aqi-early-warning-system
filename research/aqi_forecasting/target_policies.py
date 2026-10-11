"""Explicit AQI target policies shared by labels and historical AQI lags."""

from __future__ import annotations

from typing import Any

import pandas as pd

from research.aqi_forecasting.protocol import AQI_MAX, AQI_MIN, TARGET_POLICIES


def apply_target_policy(
    frame: pd.DataFrame,
    policy: str,
    *,
    source_column: str = "AQI",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Return a copy with raw, transformed, valid, and status AQI columns.

    Status values are ``valid``, ``missing``, ``non_numeric``, ``non_finite``,
    ``negative``, or ``above_500``. Under ``cap``, an above-500 value is valid
    and transformed to 500; under ``exclude`` it remains unavailable.
    """
    if policy not in TARGET_POLICIES:
        raise ValueError(f"Unknown target policy {policy!r}; expected {TARGET_POLICIES}")
    if source_column not in frame.columns:
        raise KeyError(f"Required source column {source_column!r} is missing")
    if any(column in frame.columns for column in ("aqi_raw", "aqi_value", "aqi_valid", "aqi_status")):
        raise ValueError("Input already contains AQI policy output columns")

    result = frame.copy(deep=True)
    raw = result[source_column].copy(deep=True)
    numeric = pd.to_numeric(raw, errors="coerce")

    status = pd.Series("valid", index=result.index, dtype="object")
    missing = raw.isna()
    non_numeric = ~missing & numeric.isna()
    numeric_values = numeric.to_numpy(dtype="float64", na_value=float("nan"))
    finite = pd.Series(numeric_values, index=result.index).map(lambda value: pd.notna(value) and abs(value) != float("inf"))
    non_finite = ~missing & ~non_numeric & ~finite
    negative = finite & numeric.lt(AQI_MIN)
    above_max = finite & numeric.gt(AQI_MAX)

    status.loc[missing] = "missing"
    status.loc[non_numeric] = "non_numeric"
    status.loc[non_finite] = "non_finite"
    status.loc[negative] = "negative"
    status.loc[above_max] = "above_500"

    transformed = numeric.astype("float64").copy()
    if policy == "cap":
        transformed.loc[above_max] = AQI_MAX
        valid = finite & numeric.ge(AQI_MIN)
    else:
        valid = finite & numeric.between(AQI_MIN, AQI_MAX, inclusive="both")
    transformed.loc[~valid] = float("nan")

    result["aqi_raw"] = raw
    result["aqi_value"] = transformed
    result["aqi_valid"] = valid.astype(bool)
    result["aqi_status"] = status

    counts = status.value_counts(dropna=False).to_dict()
    metadata = {
        "policy": policy,
        "source_column": source_column,
        "rows": int(len(result)),
        "valid_targets_or_lags": int(valid.sum()),
        "status_counts": {str(key): int(value) for key, value in counts.items()},
        "above_500_capped": int(above_max.sum()) if policy == "cap" else 0,
        "above_500_excluded": int(above_max.sum()) if policy == "exclude" else 0,
    }
    return result, metadata
