"""Target-date partitions and expanding-window folds."""

from __future__ import annotations

import random
from typing import Any

import pandas as pd

from research.aqi_forecasting.protocol import (
    HORIZONS_DAYS,
    MIN_CITY_TEST_CASES,
    TEST_START,
    TEST_END,
    TEST_START,
    TRAIN_END,
    TRAIN_START,
    VALIDATION_END,
    VALIDATION_START,
)
from research.aqi_forecasting.date_utils import parse_calendar_dates

_PARTITION_BOUNDS = {
    "train": (TRAIN_START, TRAIN_END),
    "validation": (VALIDATION_START, VALIDATION_END),
    "test": (TEST_START, TEST_END),
}

_EXPANDING_FOLDS = (
    ("fold_2017", "2015-01-01", "2016-12-31", "2017-01-01", "2017-12-31"),
    ("fold_2018", "2015-01-01", "2017-12-31", "2018-01-01", "2018-12-31"),
    ("fold_2019", "2015-01-01", "2018-12-31", "2019-01-01", "2019-12-31"),
)


def assign_partition(samples: pd.DataFrame, *, target_column: str = "target_date") -> pd.DataFrame:
    """Assign target dates to the approved inclusive date ranges."""
    if target_column not in samples:
        raise KeyError(f"Missing target date column {target_column!r}")
    result = samples.copy(deep=True)
    dates = parse_calendar_dates(result[target_column], field_name=target_column)
    if dates.isna().any():
        raise ValueError("Target dates must all be valid before partition assignment")
    result["partition"] = pd.Series(pd.NA, index=result.index, dtype="object")
    for partition, (start, end) in _PARTITION_BOUNDS.items():
        mask = dates.between(start, end, inclusive="both")
        if result.loc[mask, "partition"].notna().any():
            raise AssertionError("A target date was assigned to multiple partitions")
        result.loc[mask, "partition"] = partition
    result["target_date"] = dates if target_column == "target_date" else result[target_column]
    return result


def expanding_window_folds() -> list[dict[str, str]]:
    """Return the three protocol-fixed train/validation date folds."""
    return [
        {
            "name": name,
            "train_start": train_start,
            "train_end": train_end,
            "validation_start": validation_start,
            "validation_end": validation_end,
        }
        for name, train_start, train_end, validation_start, validation_end in _EXPANDING_FOLDS
    ]


def split_fold(samples: pd.DataFrame, fold: dict[str, str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split by target date using non-overlapping inclusive date ranges."""
    required_bounds = {
        "train_start",
        "train_end",
        "validation_start",
        "validation_end",
    }
    missing_bounds = required_bounds.difference(fold)
    if missing_bounds:
        raise ValueError(f"Fold is missing date bounds: {sorted(missing_bounds)}")
    if "target_date" not in samples:
        raise KeyError("Samples are missing required target_date column")

    parsed_bounds: dict[str, pd.Timestamp] = {}
    for name in sorted(required_bounds):
        parsed = parse_calendar_dates(
            pd.Series([fold[name]]), field_name=f"fold {name}"
        ).iloc[0]
        if pd.isna(parsed):
            raise ValueError(f"Fold {name} must be a valid date")
        parsed_bounds[name] = parsed
    if parsed_bounds["train_start"] > parsed_bounds["train_end"]:
        raise ValueError("Fold training date range is reversed")
    if parsed_bounds["validation_start"] > parsed_bounds["validation_end"]:
        raise ValueError("Fold validation date range is reversed")
    if parsed_bounds["train_end"] >= parsed_bounds["validation_start"]:
        raise ValueError(
            "Fold training and validation target-date ranges must be chronological and non-overlapping"
        )
    if parsed_bounds["validation_end"] >= pd.Timestamp(TEST_START):
        raise ValueError(
            f"Development folds must end before the final test starts on {TEST_START}"
        )

    result = samples.copy(deep=True)
    dates = parse_calendar_dates(result["target_date"], field_name="target_date")
    if dates.isna().any():
        raise ValueError("Target dates must all be valid before fold splitting")
    train_mask = dates.between(
        parsed_bounds["train_start"], parsed_bounds["train_end"], inclusive="both"
    )
    validation_mask = dates.between(
        parsed_bounds["validation_start"],
        parsed_bounds["validation_end"],
        inclusive="both",
    )
    training = result.loc[train_mask].copy()
    validation = result.loc[validation_mask].copy()
    if "case_id" in result and set(training["case_id"]) & set(validation["case_id"]):
        raise AssertionError("Training and validation sample IDs overlap")
    return training, validation


def assign_city_folds(cities: list[str] | tuple[str, ...], *, n_folds: int = 5, seed: int = 42) -> dict[str, int]:
    """Create deterministic, balanced city folds without inspecting outcomes."""
    if any(not isinstance(city, str) or not city.strip() for city in cities):
        raise ValueError("City labels must be non-empty strings")
    unique_cities = sorted(set(cities))
    if n_folds < 2:
        raise ValueError("n_folds must be at least 2")
    if n_folds > len(unique_cities):
        raise ValueError("n_folds cannot exceed the number of unique cities")
    shuffled = unique_cities.copy()
    random.Random(seed).shuffle(shuffled)
    return {city: index % n_folds for index, city in enumerate(shuffled)}


def held_out_city_split(
    samples: pd.DataFrame,
    city_folds: dict[str, int],
    fold: int,
    *,
    minimum_test_cases: int = MIN_CITY_TEST_CASES,
) -> dict[str, Any]:
    """Return fold city sets and test coverage gate, without using model scores."""
    if "City" not in samples:
        raise KeyError("Samples must include City")
    if not city_folds:
        raise ValueError("City fold assignment must not be empty")
    if any(not isinstance(city, str) or not city.strip() for city in city_folds):
        raise ValueError("City fold assignment contains an empty or invalid city label")
    if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in city_folds.values()):
        raise ValueError("City fold IDs must be non-negative integers")
    if not isinstance(fold, int) or isinstance(fold, bool) or fold < 0:
        raise ValueError("Requested city fold must be a non-negative integer")
    if not isinstance(minimum_test_cases, int) or isinstance(minimum_test_cases, bool) or minimum_test_cases < 1:
        raise ValueError("minimum_test_cases must be a positive integer")
    if fold not in set(city_folds.values()):
        raise ValueError(f"Requested city fold {fold!r} is not present in the assignment")
    unknown = sorted(set(samples["City"]) - set(city_folds))
    if unknown:
        raise ValueError(f"City fold assignment is missing labels: {unknown}")
    held_out = sorted(city for city, assigned_fold in city_folds.items() if assigned_fold == fold)
    training = sorted(city for city, assigned_fold in city_folds.items() if assigned_fold != fold)
    if set(held_out) & set(training):
        raise AssertionError("A city is both held out and in training")
    test_rows = samples.loc[
        samples["City"].isin(held_out)
        & samples.get("eligible", pd.Series(True, index=samples.index)).astype(bool)
        & samples.get("partition", pd.Series("", index=samples.index)).eq("test")
    ]
    case_counts = test_rows.groupby("City").size().to_dict()
    included = sorted(city for city in held_out if case_counts.get(city, 0) >= minimum_test_cases)
    low_coverage = sorted(city for city in held_out if case_counts.get(city, 0) < minimum_test_cases)
    return {
        "fold": int(fold),
        "held_out_cities": held_out,
        "training_cities": training,
        "test_case_counts": {city: int(case_counts.get(city, 0)) for city in held_out},
        "included_in_macro_summary": included,
        "below_coverage_gate": low_coverage,
        "minimum_test_cases": int(minimum_test_cases),
    }
