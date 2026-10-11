"""Coverage counts and policy-common-case comparisons."""

from __future__ import annotations

from typing import Any

import pandas as pd
from pandas.api.types import is_bool_dtype


def coverage_summary(samples: pd.DataFrame) -> dict[str, Any]:
    """Summarize target/lag exclusions, eligible cases, and city coverage."""
    required = {
        "City",
        "eligible",
        "target_valid",
        "target_status",
        "exclusion_reasons",
        "partition",
        "target_date",
        "horizon_days",
        "policy",
    }
    missing = required.difference(samples.columns)
    if missing:
        raise ValueError(f"Samples lack coverage columns: {sorted(missing)}")
    for column in ("eligible", "target_valid"):
        if samples[column].isna().any():
            raise ValueError(f"Coverage column {column!r} must not contain missing values")
        if not is_bool_dtype(samples[column].dtype):
            raise ValueError(f"Coverage column {column!r} must contain boolean values")
    eligible = samples["eligible"].astype(bool)
    reason_counts: dict[str, int] = {}
    for reasons in samples["exclusion_reasons"]:
        for reason in reasons:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
    by_city = (
        samples.loc[eligible].groupby("City").size().astype(int).to_dict()
        if eligible.any()
        else {}
    )
    result = {
        "raw_target_rows": int(len(samples)),
        "valid_target_labels": int(samples["target_valid"].astype(bool).sum()),
        "eligible_forecasts": int(eligible.sum()),
        "ineligible_forecasts": int((~eligible).sum()),
        "contributing_cities": int(len(by_city)),
        "exclusion_reason_counts": reason_counts,
        "eligible_cases_by_city": {str(city): int(count) for city, count in by_city.items()},
        "target_status_counts": {
            str(key): int(value)
            for key, value in samples["target_status"].value_counts(dropna=False).items()
        },
    }
    if "partition" in samples:
        result["by_partition"] = {}
        for partition, group in samples.groupby("partition", dropna=False, sort=True):
            result["by_partition"][str(partition)] = {
                "raw_target_rows": int(len(group)),
                "valid_target_labels": int(group["target_valid"].astype(bool).sum()),
                "eligible_forecasts": int(group["eligible"].astype(bool).sum()),
                "contributing_cities": int(group.loc[group["eligible"].astype(bool), "City"].nunique()),
            }
    return result


def common_case_ids(*sample_frames: pd.DataFrame) -> set[str]:
    """Return city/date/horizon keys eligible under every supplied policy."""
    if not sample_frames:
        return set()
    common: set[str] | None = None
    expected_horizon: int | None = None
    for frame in sample_frames:
        required = {"eligible", "case_id", "City", "target_date", "horizon_days", "policy"}
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"Samples lack common-case columns: {sorted(missing)}")
        if frame["eligible"].isna().any():
            raise ValueError("Common-case eligibility must not contain missing values")
        if not is_bool_dtype(frame["eligible"].dtype):
            raise ValueError("Common-case eligibility must contain boolean values")
        if frame["case_id"].duplicated().any():
            raise ValueError("Common-case sample identifiers must be unique within each frame")
        horizons = frame["horizon_days"].dropna().unique()
        policies = frame["policy"].dropna().unique()
        if len(horizons) > 1 or len(policies) > 1:
            raise ValueError("Each common-case frame must contain one horizon and one policy")
        if len(horizons) == 1:
            horizon = int(horizons[0])
            if expected_horizon is None:
                expected_horizon = horizon
            elif horizon != expected_horizon:
                raise ValueError("Common-case frames must use the same horizon")
        eligible = frame.loc[frame["eligible"].astype(bool), "case_id"]
        ids = set(eligible.astype(str))
        common = ids if common is None else common.intersection(ids)
    return common or set()
