"""Locked final-test refitting, city-cluster bootstrap, and lockdown split.

Nothing here changes the frozen protocol. The only difference from
development fitting is the declared refit window: the selected Ridge alpha,
the selected XGBoost configuration, and the city/month climatology are refit
on ALL training and development targets (2015-01-01 through 2019-12-31)
before predicting the locked test targets (2020-01-01 through 2020-07-01).
Deterministic baselines keep their normal exact-date, origin-available
lookups.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from research.aqi_forecasting.baselines import (
    CityMonthClimatology,
    _metric_values,
    _single_protocol_value,
)
from research.aqi_forecasting.leakage_checks import validate_feature_schema
from research.aqi_forecasting.protocol import (
    PRIMARY_FEATURE_COLUMNS,
    TEST_END,
    TEST_START,
    TRAIN_START,
    VALIDATION_END,
)
from research.aqi_forecasting.xgboost_model import (
    XGBoostConfig,
    _new_regressor,
    eligible_fit_rows,
)

REFIT_START = TRAIN_START
REFIT_END = VALIDATION_END
REFIT_PARTITIONS = frozenset({"train", "validation"})

REFIT_PROCEDURE = (
    "Refit on every train and validation target from "
    f"{REFIT_START} through {REFIT_END} inclusive, then predict the locked "
    f"test targets from {TEST_START} through {TEST_END} inclusive."
)

LOCKDOWN_START = "2020-03-25"
PRE_LOCKDOWN_WINDOW = (TEST_START, "2020-03-24")
LOCKDOWN_WINDOW = (LOCKDOWN_START, TEST_END)

BOOTSTRAP_REPLICATES = 2000
BOOTSTRAP_SEED = 20200101
BOOTSTRAP_CONFIDENCE = 0.95
PERSISTENCE_METHOD = "persistence"


def validate_refit_samples(samples: pd.DataFrame) -> pd.DataFrame:
    """Reject any refit row outside the declared 2015-2019 refit window."""
    if "partition" not in samples:
        raise ValueError("Refit samples must carry partition labels")
    partitions = set(samples["partition"].dropna().astype(str))
    unexpected = partitions - set(REFIT_PARTITIONS)
    if unexpected:
        raise ValueError(f"Refit samples contain forbidden partitions: {sorted(unexpected)}")
    if "target_date" not in samples:
        raise ValueError("Refit samples require target_date")
    dates = pd.to_datetime(samples["target_date"], errors="coerce").dt.normalize()
    if dates.isna().any():
        raise ValueError("Refit target dates must be valid")
    if dates.empty:
        raise ValueError("Refit samples must not be empty")
    if not dates.between(REFIT_START, REFIT_END, inclusive="both").all():
        raise ValueError(
            f"Refit targets must fall within {REFIT_START} through {REFIT_END}"
        )
    if dates.max() >= pd.Timestamp(TEST_START):
        raise AssertionError("A locked final-test target reached the refit set")
    return samples


def fit_refit_ridge(samples: pd.DataFrame, alpha: float) -> Pipeline:
    """Refit the standardized Ridge pipeline on 2015-2019 eligible rows."""
    validate_feature_schema(PRIMARY_FEATURE_COLUMNS)
    if not np.isfinite(alpha) or alpha <= 0:
        raise ValueError("Ridge alpha must be a finite positive number")
    validate_refit_samples(samples)
    fit_rows = eligible_fit_rows(samples, model_name="Ridge refit")
    model = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("ridge", Ridge(alpha=float(alpha))),
        ]
    )
    model.fit(
        fit_rows.loc[:, list(PRIMARY_FEATURE_COLUMNS)].astype(float),
        fit_rows["target"].astype(float),
    )
    return model


def fit_refit_xgboost(samples: pd.DataFrame, config: XGBoostConfig):
    """Refit the selected XGBoost configuration on 2015-2019 eligible rows."""
    validate_feature_schema(PRIMARY_FEATURE_COLUMNS)
    if not isinstance(config, XGBoostConfig):
        raise TypeError("config must be an XGBoostConfig")
    validate_refit_samples(samples)
    fit_rows = eligible_fit_rows(samples, model_name="XGBoost refit")
    model = _new_regressor(config)
    model.fit(
        fit_rows.loc[:, list(PRIMARY_FEATURE_COLUMNS)].astype(float),
        fit_rows["target"].astype(float),
    )
    return model


def fit_refit_climatology(samples: pd.DataFrame) -> CityMonthClimatology:
    """Refit city/month and pooled-month means on 2015-2019 valid targets."""
    policy = str(_single_protocol_value(samples, "policy"))
    horizon = int(_single_protocol_value(samples, "horizon_days"))
    validate_refit_samples(samples)
    required = {"City", "target_date", "target", "target_valid"}
    missing = required.difference(samples.columns)
    if missing:
        raise ValueError(f"Climatology refit samples are missing columns: {sorted(missing)}")
    valid = samples.loc[samples["target_valid"].astype(bool)].copy()
    if valid["target"].isna().any() or not np.isfinite(valid["target"].astype(float)).all():
        raise ValueError("Valid refit targets must be finite numeric values")
    valid["target_month"] = pd.to_datetime(valid["target_date"]).dt.month
    city_month = (
        valid.groupby(["City", "target_month"], sort=True)["target"].mean().astype(float).to_dict()
    )
    pooled_month = (
        valid.groupby("target_month", sort=True)["target"].mean().astype(float).to_dict()
    )
    if not pooled_month:
        raise ValueError("No valid refit targets are available for climatology")
    return CityMonthClimatology(
        policy=policy,
        horizon_days=horizon,
        city_month_means=city_month,
        pooled_month_means=pooled_month,
        training_case_count=int(len(valid)),
        training_city_count=int(valid["City"].nunique()),
    )


def common_case_frames(
    predictions_by_model: dict[str, pd.DataFrame], *, partition: str
) -> tuple[dict[str, pd.DataFrame], set[str]]:
    """Return each method's scored rows restricted to the shared case set."""
    scoped: dict[str, pd.DataFrame] = {}
    scorable_ids: list[set[str]] = []
    for method, predictions in predictions_by_model.items():
        frame = predictions.loc[predictions["partition"].eq(partition)].copy()
        if frame["case_id"].duplicated().any():
            raise ValueError(f"{method} predictions contain duplicate case IDs")
        valid = frame["target_valid"].astype(bool) & frame["target"].notna()
        available = valid & frame["prediction_available"].astype(bool)
        scoped[method] = frame.loc[available].copy()
        scorable_ids.append(set(frame.loc[available, "case_id"].astype(str)))
    common = set.intersection(*scorable_ids) if scorable_ids else set()
    result: dict[str, pd.DataFrame] = {}
    for method, frame in scoped.items():
        paired = frame.loc[frame["case_id"].astype(str).isin(common)].copy()
        paired = paired.sort_values("case_id").reset_index(drop=True)
        result[method] = paired
    return result, common


def _city_error_sums(frame: pd.DataFrame, cities: list[str]) -> tuple[np.ndarray, np.ndarray]:
    error = np.abs(
        frame["prediction"].astype(float).to_numpy() - frame["target"].astype(float).to_numpy()
    )
    city_values = frame["City"].astype(str).to_numpy()
    index = {city: position for position, city in enumerate(cities)}
    sums = np.zeros(len(cities), dtype="float64")
    counts = np.zeros(len(cities), dtype="float64")
    for city, value in zip(city_values, error):
        position = index[city]
        sums[position] += float(value)
        counts[position] += 1.0
    return sums, counts


def city_cluster_bootstrap(
    common_frames: dict[str, pd.DataFrame],
    *,
    replicates: int = BOOTSTRAP_REPLICATES,
    seed: int = BOOTSTRAP_SEED,
    confidence: float = BOOTSTRAP_CONFIDENCE,
    paired_reference: str = PERSISTENCE_METHOD,
) -> dict[str, Any]:
    """City-cluster bootstrap CIs for common-case MAE and paired differences.

    Cities are the resampling clusters: each replicate draws the full set of
    contributing cities with replacement and recomputes pooled MAE from the
    resampled clusters. Every method uses the identical city draw in a given
    replicate, so paired differences share the replicate's resample.
    """
    if not common_frames:
        raise ValueError("At least one common-case frame is required")
    if replicates < 1:
        raise ValueError("replicates must be positive")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must lie strictly between 0 and 1")
    case_sets = {
        method: tuple(frame["case_id"].astype(str)) for method, frame in common_frames.items()
    }
    if len(set(case_sets.values())) != 1:
        raise ValueError("Common-case frames must contain identical, identically ordered cases")
    cities = sorted({str(city) for frame in common_frames.values() for city in frame["City"]})
    if not cities:
        return {
            "replicates": int(replicates),
            "seed": int(seed),
            "cities": [],
            "city_count": 0,
            "confidence": confidence,
            "mae": {},
            "paired_difference": {},
        }
    sums: dict[str, np.ndarray] = {}
    counts: dict[str, np.ndarray] = {}
    for method, frame in common_frames.items():
        method_sums, method_counts = _city_error_sums(frame, cities)
        sums[method] = method_sums
        counts[method] = method_counts
    reference_counts = next(iter(counts.values()))
    for method, method_counts in counts.items():
        if not np.array_equal(method_counts, reference_counts):
            raise AssertionError(f"{method} common-case counts differ by city")

    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(cities), size=(int(replicates), len(cities)))
    weights = np.zeros((int(replicates), len(cities)), dtype="float64")
    for replicate in range(int(replicates)):
        weights[replicate] = np.bincount(draws[replicate], minlength=len(cities)).astype("float64")
    denominator = weights @ reference_counts

    lower_percentile = 100.0 * (1.0 - confidence) / 2.0
    upper_percentile = 100.0 * (1.0 + confidence) / 2.0

    mae_results: dict[str, Any] = {}
    replicate_mae: dict[str, np.ndarray] = {}
    for method in sorted(common_frames):
        values = (weights @ sums[method]) / denominator
        replicate_mae[method] = values
        point = float(sums[method].sum() / reference_counts.sum())
        mae_results[method] = {
            "mae": point,
            "ci_lower": float(np.percentile(values, lower_percentile)),
            "ci_upper": float(np.percentile(values, upper_percentile)),
            "bootstrap_mean": float(np.mean(values)),
            "bootstrap_std_error": float(np.std(values, ddof=1)),
        }

    paired: dict[str, Any] = {}
    if paired_reference in common_frames:
        for method in sorted(common_frames):
            if method == paired_reference:
                continue
            differences = replicate_mae[method] - replicate_mae[paired_reference]
            point = float(
                (sums[method].sum() - sums[paired_reference].sum()) / reference_counts.sum()
            )
            paired[f"{method}_minus_{paired_reference}"] = {
                "method": method,
                "reference": paired_reference,
                "mae_difference": point,
                "ci_lower": float(np.percentile(differences, lower_percentile)),
                "ci_upper": float(np.percentile(differences, upper_percentile)),
                "bootstrap_mean": float(np.mean(differences)),
                "bootstrap_std_error": float(np.std(differences, ddof=1)),
                "excludes_zero": bool(
                    np.percentile(differences, lower_percentile) > 0.0
                    or np.percentile(differences, upper_percentile) < 0.0
                ),
            }
    return {
        "replicates": int(replicates),
        "seed": int(seed),
        "confidence": confidence,
        "cities": cities,
        "city_count": len(cities),
        "resampling_unit": "city cluster, drawn with replacement",
        "mae": mae_results,
        "paired_difference": paired,
    }


def lockdown_split_metrics(common_frames: dict[str, pd.DataFrame]) -> dict[str, Any]:
    """Common-case MAE per method for the pre-lockdown and lockdown windows."""
    windows = {
        "pre_lockdown": PRE_LOCKDOWN_WINDOW,
        "lockdown": LOCKDOWN_WINDOW,
    }
    result: dict[str, Any] = {
        "lockdown_start": LOCKDOWN_START,
        "windows": {name: list(bounds) for name, bounds in windows.items()},
        "methods": {},
    }
    for name, (start, end) in windows.items():
        counts: set[int] = set()
        for method in sorted(common_frames):
            frame = common_frames[method]
            dates = pd.to_datetime(frame["target_date"]).dt.normalize()
            window = frame.loc[dates.between(start, end, inclusive="both")]
            metrics = _metric_values(window)
            counts.add(int(metrics["count"]))
            result["methods"].setdefault(method, {})[name] = {
                "count": metrics["count"],
                "mae": metrics["mae"],
                "rmse": metrics["rmse"],
            }
        if len(counts) > 1:
            raise AssertionError(f"Common-case counts differ across methods in {name}")
        result[f"{name}_common_cases"] = counts.pop() if counts else 0
    return result


__all__ = [
    "BOOTSTRAP_CONFIDENCE",
    "BOOTSTRAP_REPLICATES",
    "BOOTSTRAP_SEED",
    "LOCKDOWN_START",
    "LOCKDOWN_WINDOW",
    "PRE_LOCKDOWN_WINDOW",
    "REFIT_END",
    "REFIT_PARTITIONS",
    "REFIT_PROCEDURE",
    "REFIT_START",
    "city_cluster_bootstrap",
    "common_case_frames",
    "fit_refit_climatology",
    "fit_refit_ridge",
    "fit_refit_xgboost",
    "lockdown_split_metrics",
    "validate_refit_samples",
]
