"""Exact-calendar target and AQI-lag construction for direct forecasts."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

from research.aqi_forecasting.protocol import (
    AQI_LAGS_DAYS,
    HORIZONS_DAYS,
    PRIMARY_FEATURE_COLUMNS,
)
from research.aqi_forecasting.target_policies import apply_target_policy
from research.aqi_forecasting.date_utils import parse_calendar_dates

_LAG_COLUMNS = {
    0: ("aqi_lag_origin", "aqi_origin_date", "aqi_origin_status", "missing_origin_aqi"),
    1: ("aqi_lag_1d", "aqi_lag_1d_date", "aqi_lag_1d_status", "missing_one_day_lag"),
    7: ("aqi_lag_7d", "aqi_lag_7d_date", "aqi_lag_7d_status", "missing_seven_day_lag"),
}


def _case_id(city: Any, target_date: pd.Timestamp, horizon_days: int) -> str:
    return f"{city}|{target_date.date().isoformat()}|h{horizon_days}"


def build_forecast_samples(
    frame: pd.DataFrame,
    horizon_days: int,
    policy: str,
) -> pd.DataFrame:
    """Create auditable rows for one policy/horizon, including ineligible cases.

    Required historical inputs are AQI at the exact origin date, origin minus
    one day, and origin minus seven days. Calendar features are known in
    advance and derive only from the target date.
    """
    if horizon_days not in HORIZONS_DAYS:
        raise ValueError(f"Unsupported horizon {horizon_days}; expected {HORIZONS_DAYS}")
    if not {"City", "Date", "AQI"}.issubset(frame.columns):
        raise ValueError("Input must contain City, Date, and AQI columns")

    work = frame.loc[:, ["City", "Date", "AQI"]].copy(deep=True)
    work["target_date"] = parse_calendar_dates(work["Date"], field_name="Date")
    invalid_dates = int(work["target_date"].isna().sum())
    if invalid_dates:
        raise ValueError(f"Cannot construct forecasts: {invalid_dates} rows have invalid dates")
    if work["City"].isna().any():
        raise ValueError("Cannot construct forecasts: City contains missing values")
    duplicate_mask = work.duplicated(["City", "target_date"], keep=False)
    if duplicate_mask.any():
        duplicate_examples = work.loc[duplicate_mask, ["City", "target_date"]].head(5)
        raise ValueError(
            "Duplicate (City, Date) keys prevent unambiguous exact-date joins: "
            f"{duplicate_examples.to_dict(orient='records')}"
        )

    policy_frame, _ = apply_target_policy(work, policy)
    source = policy_frame.loc[:, ["City", "target_date", "aqi_value", "aqi_valid", "aqi_status"]]
    targets = policy_frame.loc[:, ["City", "target_date", "aqi_raw", "aqi_value", "aqi_valid", "aqi_status"]].copy()
    targets = targets.rename(
        columns={
            "target_date": "target_date",
            "aqi_raw": "target_raw",
            "aqi_value": "target",
            "aqi_valid": "target_valid",
            "aqi_status": "target_status",
        }
    )
    targets["origin_date"] = targets["target_date"] - pd.to_timedelta(horizon_days, unit="D")
    targets["horizon_days"] = int(horizon_days)
    targets["policy"] = policy
    targets["case_id"] = [
        _case_id(city, date, horizon_days)
        for city, date in zip(targets["City"], targets["target_date"])
    ]
    targets["policy_case_id"] = targets["case_id"] + f"|{policy}"

    for lag_days in AQI_LAGS_DAYS:
        feature_name, date_name, status_name, _ = _LAG_COLUMNS[lag_days]
        offset = horizon_days + lag_days
        lookup = source.copy()
        lookup["source_date"] = lookup["target_date"]
        lookup = lookup.rename(
            columns={
                "aqi_value": feature_name,
                "aqi_valid": f"{feature_name}_valid",
                "aqi_status": status_name,
            }
        ).drop(columns="target_date")
        targets[date_name] = targets["target_date"] - pd.to_timedelta(offset, unit="D")
        targets = targets.merge(
            lookup,
            left_on=["City", date_name],
            right_on=["City", "source_date"],
            how="left",
            validate="one_to_one",
            sort=False,
        ).drop(columns="source_date")
        no_exact_date = targets[status_name].isna()
        targets.loc[no_exact_date, status_name] = "no_city_date"
        targets[f"{feature_name}_valid"] = targets[f"{feature_name}_valid"].eq(True)

    month = targets["target_date"].dt.month.astype(float) - 1.0
    weekday = targets["target_date"].dt.dayofweek.astype(float)
    targets["target_month_sin"] = (2 * math.pi * month / 12).map(math.sin)
    targets["target_month_cos"] = (2 * math.pi * month / 12).map(math.cos)
    targets["target_weekday_sin"] = (2 * math.pi * weekday / 7).map(math.sin)
    targets["target_weekday_cos"] = (2 * math.pi * weekday / 7).map(math.cos)

    reasons: list[tuple[str, ...]] = []
    for row in targets.itertuples(index=False):
        row_map = row._asdict()
        row_reasons: list[str] = []
        target_status = row_map["target_status"]
        if not row_map["target_valid"]:
            if target_status == "missing":
                row_reasons.append("missing_target")
            else:
                row_reasons.append(f"invalid_target_{target_status}")

        for lag_days in AQI_LAGS_DAYS:
            feature_name, _, status_name, reason_base = _LAG_COLUMNS[lag_days]
            lag_status = row_map[status_name]
            if not row_map[f"{feature_name}_valid"]:
                if lag_status in ("missing", "no_city_date"):
                    row_reasons.append(reason_base)
                else:
                    row_reasons.append(f"invalid_{reason_base}_{lag_status}")
            if pd.notna(row_map[feature_name]) and pd.Timestamp(row_map[_LAG_COLUMNS[lag_days][1]]) > row_map["origin_date"]:
                raise AssertionError(f"{feature_name} timestamp is after forecast origin")
        reasons.append(tuple(row_reasons))
    targets["exclusion_reasons"] = reasons
    targets["eligible"] = targets["exclusion_reasons"].map(len).eq(0)

    # This timestamp is audit metadata, not a predictor. AQI lag dates are
    # exact and never later than the origin; target-date calendar is preknown.
    lag_dates = [targets[date_name] for _, date_name, _, _ in _LAG_COLUMNS.values()]
    targets["max_aqi_feature_date"] = pd.concat(lag_dates, axis=1).max(axis=1)
    if (targets["max_aqi_feature_date"] > targets["origin_date"]).any():
        raise AssertionError("At least one AQI feature timestamp is after its origin")
    targets.attrs["feature_columns"] = list(PRIMARY_FEATURE_COLUMNS)
    targets.attrs["horizon_days"] = int(horizon_days)
    targets.attrs["policy"] = policy
    return targets
