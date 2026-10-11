"""Leakage-aware forecasting baseline predictors and development evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import math
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from research.aqi_forecasting.date_utils import parse_calendar_dates
from research.aqi_forecasting.leakage_checks import validate_feature_schema
from research.aqi_forecasting.protocol import (
    HORIZONS_DAYS,
    PRIMARY_FEATURE_COLUMNS,
    TRAIN_END,
    TRAIN_START,
)
from research.aqi_forecasting.target_policies import apply_target_policy
from research.aqi_forecasting.temporal_splits import (
    expanding_window_folds,
    split_fold,
)

PREDICTION_ID_COLUMNS = (
    "case_id",
    "City",
    "target_date",
    "origin_date",
    "horizon_days",
    "policy",
    "partition",
    "target",
    "target_valid",
)
RIDGE_ALPHA_CANDIDATES = (0.1, 1.0, 10.0)

_ANNUAL = "annual_seasonal_naive"
_PERSISTENCE = "persistence"
_WEEKLY = "weekly_seasonal_naive"
_CLIMATOLOGY = "city_month_climatology"
_RIDGE = "regularized_linear"


def _single_protocol_value(samples: pd.DataFrame, column: str) -> Any:
    if column not in samples:
        raise ValueError(f"Samples are missing required column {column!r}")
    values = samples[column].drop_duplicates()
    if len(values) != 1:
        raise ValueError(f"Samples must contain exactly one {column}")
    return values.iloc[0]


def _prediction_frame(
    samples: pd.DataFrame,
    method: str,
    predictions: list[float | None],
    reasons: list[str | None],
    *,
    sources: list[str | None] | None = None,
) -> pd.DataFrame:
    required = set(PREDICTION_ID_COLUMNS)
    missing = required.difference(samples.columns)
    if missing:
        raise ValueError(f"Samples are missing prediction identity columns: {sorted(missing)}")
    if len(predictions) != len(samples) or len(reasons) != len(samples):
        raise ValueError("Prediction and reason counts must match the sample rows")

    result = samples.loc[:, list(PREDICTION_ID_COLUMNS)].copy().reset_index(drop=True)
    result["method"] = method
    result["prediction"] = pd.array(predictions, dtype="Float64")
    result["prediction_available"] = result["prediction"].notna()
    result["prediction_exclusion_reason"] = reasons
    if sources is not None:
        if len(sources) != len(samples):
            raise ValueError("Prediction source count must match the sample rows")
        result["prediction_source"] = sources
    return result


def _sample_history_value(row: Any, feature: str, status_column: str) -> tuple[float | None, str | None]:
    value = getattr(row, feature)
    if pd.notna(value):
        return float(value), None
    status = getattr(row, status_column)
    if status in ("missing", "no_city_date"):
        return None, "missing_origin_aqi" if feature == "aqi_lag_origin" else f"missing_{feature}"
    return None, f"invalid_{feature}_{status}"


def _validate_training_dates(samples: pd.DataFrame) -> None:
    if "target_date" not in samples:
        raise ValueError("Training samples require target_date")
    dates = pd.to_datetime(samples["target_date"], errors="coerce").dt.normalize()
    if dates.isna().any():
        raise ValueError("Training target dates must be valid")
    if dates.empty or not dates.between(TRAIN_START, TRAIN_END, inclusive="both").all():
        raise ValueError(
            f"Training targets must fall within {TRAIN_START} through {TRAIN_END}"
        )


def persistence_predictions(samples: pd.DataFrame) -> pd.DataFrame:
    """Predict the policy-transformed AQI at the exact forecast origin."""
    predictions: list[float | None] = []
    reasons: list[str | None] = []
    for row in samples.itertuples(index=False):
        value, reason = _sample_history_value(
            row, "aqi_lag_origin", "aqi_origin_status"
        )
        predictions.append(value)
        reasons.append(reason)
    return _prediction_frame(samples, _PERSISTENCE, predictions, reasons)


def weekly_seasonal_naive_predictions(history: pd.DataFrame, samples: pd.DataFrame) -> pd.DataFrame:
    """Use exact target-date-minus-seven AQI when available by the origin."""
    horizon = int(_single_protocol_value(samples, "horizon_days"))
    if horizon not in HORIZONS_DAYS:
        raise ValueError(f"Unsupported forecast horizon {horizon}")
    latest_origin = pd.to_datetime(samples["origin_date"]).max().normalize()
    lookup = _prepare_history(
        history,
        str(_single_protocol_value(samples, "policy")),
        latest_available_date=latest_origin,
    )
    predictions: list[float | None] = []
    reasons: list[str | None] = []
    for row in samples.itertuples(index=False):
        target_date = pd.Timestamp(row.target_date)
        source_date = target_date - pd.Timedelta(days=7)
        origin_date = pd.Timestamp(row.origin_date)
        if source_date > origin_date:
            predictions.append(None)
            reasons.append("weekly_observation_after_origin")
            continue
        value, status = lookup.get((row.City, source_date), (None, "no_city_date"))
        if value is not None:
            predictions.append(value)
            reasons.append(None)
        elif status in ("missing", "no_city_date"):
            predictions.append(None)
            reasons.append("missing_weekly_observation")
        else:
            predictions.append(None)
            reasons.append(f"invalid_weekly_observation_{status}")
    return _prediction_frame(samples, _WEEKLY, predictions, reasons)


def _previous_year_date(target_date: pd.Timestamp) -> pd.Timestamp:
    """Map Feb 29 to Feb 28 in the prior year; otherwise preserve month/day."""
    source_date = target_date.date()
    try:
        prior = source_date.replace(year=source_date.year - 1)
    except ValueError:
        if source_date.month != 2 or source_date.day != 29:
            raise
        prior = date(source_date.year - 1, 2, 28)
    return pd.Timestamp(prior)


def _prepare_history(
    history: pd.DataFrame,
    policy: str,
    *,
    latest_available_date: pd.Timestamp,
) -> dict[tuple[Any, pd.Timestamp], tuple[float | None, str]]:
    required = {"City", "Date", "AQI"}
    missing = required.difference(history.columns)
    if missing:
        raise ValueError(f"Historical data is missing columns: {sorted(missing)}")
    work = history.loc[:, ["City", "Date", "AQI"]].copy(deep=True)
    work["source_date"] = parse_calendar_dates(work["Date"], field_name="Date")
    if work["source_date"].isna().any():
        raise ValueError("Historical data contains invalid dates")
    work = work.loc[work["source_date"] <= latest_available_date].copy()
    if work["City"].isna().any():
        raise ValueError("Historical data contains missing city labels")
    if work.duplicated(["City", "source_date"]).any():
        raise ValueError("Historical data contains duplicate city/calendar-day keys")
    transformed, _ = apply_target_policy(work, policy)
    return {
        (row.City, row.source_date): (
            float(row.aqi_value) if row.aqi_valid else None,
            str(row.aqi_status),
        )
        for row in transformed.itertuples(index=False)
    }


def annual_seasonal_naive_predictions(
    history: pd.DataFrame, samples: pd.DataFrame
) -> pd.DataFrame:
    """Use same-city AQI one calendar year earlier, with Feb-29 -> Feb-28."""
    horizon = int(_single_protocol_value(samples, "horizon_days"))
    if horizon not in HORIZONS_DAYS:
        raise ValueError(f"Unsupported forecast horizon {horizon}")
    policy = str(_single_protocol_value(samples, "policy"))
    latest_origin = pd.to_datetime(samples["origin_date"]).max().normalize()
    lookup = _prepare_history(
        history, policy, latest_available_date=latest_origin
    )
    predictions: list[float | None] = []
    reasons: list[str | None] = []
    sources: list[str | None] = []
    for row in samples.itertuples(index=False):
        source_date = _previous_year_date(pd.Timestamp(row.target_date))
        if source_date > pd.Timestamp(row.origin_date):
            predictions.append(None)
            reasons.append("annual_observation_after_origin")
            sources.append(None)
            continue
        value, status = lookup.get((row.City, source_date), (None, "no_city_date"))
        if value is not None:
            predictions.append(value)
            reasons.append(None)
            sources.append(source_date.date().isoformat())
        elif status in ("missing", "no_city_date"):
            predictions.append(None)
            reasons.append("missing_annual_observation")
            sources.append(source_date.date().isoformat())
        else:
            predictions.append(None)
            reasons.append(f"invalid_annual_observation_{status}")
            sources.append(source_date.date().isoformat())
    return _prediction_frame(
        samples, _ANNUAL, predictions, reasons, sources=sources
    )


@dataclass(frozen=True)
class CityMonthClimatology:
    """Training-only city/month means plus pooled-month fallback means."""

    policy: str
    horizon_days: int
    city_month_means: dict[tuple[Any, int], float]
    pooled_month_means: dict[int, float]
    training_case_count: int
    training_city_count: int


def fit_city_month_climatology(training_samples: pd.DataFrame) -> CityMonthClimatology:
    """Fit city-month and pooled-month means using training target labels only."""
    policy = str(_single_protocol_value(training_samples, "policy"))
    horizon = int(_single_protocol_value(training_samples, "horizon_days"))
    if "partition" not in training_samples or not training_samples["partition"].eq("train").all():
        raise ValueError("Climatology may only be fitted on train-partition targets")
    _validate_training_dates(training_samples)
    required = {"City", "target_date", "target", "target_valid"}
    missing = required.difference(training_samples.columns)
    if missing:
        raise ValueError(f"Training samples are missing columns: {sorted(missing)}")
    valid = training_samples.loc[training_samples["target_valid"].astype(bool)].copy()
    if valid["target"].isna().any() or not np.isfinite(valid["target"].astype(float)).all():
        raise ValueError("Valid training targets must be finite numeric values")
    valid["target_month"] = pd.to_datetime(valid["target_date"]).dt.month
    city_month = (
        valid.groupby(["City", "target_month"], sort=True)["target"]
        .mean()
        .astype(float)
        .to_dict()
    )
    pooled_month = (
        valid.groupby("target_month", sort=True)["target"]
        .mean()
        .astype(float)
        .to_dict()
    )
    if not pooled_month:
        raise ValueError("No valid training targets are available for climatology")
    return CityMonthClimatology(
        policy=policy,
        horizon_days=horizon,
        city_month_means=city_month,
        pooled_month_means=pooled_month,
        training_case_count=int(len(valid)),
        training_city_count=int(valid["City"].nunique()),
    )


def climatology_predictions(
    climatology: CityMonthClimatology, samples: pd.DataFrame
) -> pd.DataFrame:
    """Predict from frozen city/month means, with pooled-month fallback."""
    if int(_single_protocol_value(samples, "horizon_days")) != climatology.horizon_days:
        raise ValueError("Climatology and prediction horizons do not match")
    if str(_single_protocol_value(samples, "policy")) != climatology.policy:
        raise ValueError("Climatology and prediction policies do not match")
    predictions: list[float | None] = []
    reasons: list[str | None] = []
    sources: list[str | None] = []
    for row in samples.itertuples(index=False):
        month = pd.Timestamp(row.target_date).month
        city_key = (row.City, month)
        if city_key in climatology.city_month_means:
            predictions.append(climatology.city_month_means[city_key])
            reasons.append(None)
            sources.append("city_month")
        elif month in climatology.pooled_month_means:
            predictions.append(climatology.pooled_month_means[month])
            reasons.append(None)
            sources.append("pooled_month_fallback")
        else:
            predictions.append(None)
            reasons.append("no_training_climatology_for_month")
            sources.append(None)
    return _prediction_frame(
        samples, _CLIMATOLOGY, predictions, reasons, sources=sources
    )


def fit_ridge_model(training_samples: pd.DataFrame, alpha: float) -> Pipeline:
    """Fit standardized Ridge on eligible training rows only."""
    validate_feature_schema(PRIMARY_FEATURE_COLUMNS)
    if not math.isfinite(alpha) or alpha <= 0:
        raise ValueError("Ridge alpha must be a finite positive number")
    if "partition" not in training_samples or not training_samples["partition"].eq("train").all():
        raise ValueError("Ridge may only be fitted on train-partition targets")
    _validate_training_dates(training_samples)
    required = {"target", "target_valid", "eligible", *PRIMARY_FEATURE_COLUMNS}
    missing = required.difference(training_samples.columns)
    if missing:
        raise ValueError(f"Ridge training samples are missing columns: {sorted(missing)}")
    fit_rows = training_samples.loc[
        training_samples["eligible"].astype(bool)
        & training_samples["target_valid"].astype(bool)
    ]
    if fit_rows.empty:
        raise ValueError("No eligible training rows are available for Ridge")
    x_train = fit_rows.loc[:, list(PRIMARY_FEATURE_COLUMNS)].astype(float)
    y_train = fit_rows["target"].astype(float)
    if not np.isfinite(x_train.to_numpy()).all() or not np.isfinite(y_train.to_numpy()).all():
        raise ValueError("Ridge training features and labels must be finite")
    model = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("ridge", Ridge(alpha=float(alpha))),
        ]
    )
    model.fit(x_train, y_train)
    return model


def ridge_predictions(model: Pipeline, samples: pd.DataFrame) -> pd.DataFrame:
    """Predict eligible rows; preserve unavailable predictions and reasons."""
    validate_feature_schema(PRIMARY_FEATURE_COLUMNS)
    missing = set(PRIMARY_FEATURE_COLUMNS).difference(samples.columns)
    if missing:
        raise ValueError(f"Ridge prediction samples are missing features: {sorted(missing)}")
    predictions: list[float | None] = []
    reasons: list[str | None] = []
    eligible = samples["eligible"].astype(bool)
    positions = np.flatnonzero(eligible.to_numpy())
    if len(positions):
        features = samples.iloc[positions].loc[:, list(PRIMARY_FEATURE_COLUMNS)].astype(float)
        values = model.predict(features)
        by_position = {int(position): float(value) for position, value in zip(positions, values)}
    else:
        by_position = {}
    for position in range(len(samples)):
        if position in by_position:
            predictions.append(by_position[position])
            reasons.append(None)
        else:
            predictions.append(None)
            reasons.append("missing_or_invalid_primary_feature")
    return _prediction_frame(samples, _RIDGE, predictions, reasons)


def _metric_values(frame: pd.DataFrame) -> dict[str, float | None]:
    if frame.empty:
        return {"count": 0, "mae": None, "rmse": None, "r2": None}
    error = frame["prediction"].astype(float).to_numpy() - frame["target"].astype(float).to_numpy()
    mae = float(np.mean(np.abs(error)))
    rmse = float(np.sqrt(np.mean(np.square(error))))
    target = frame["target"].astype(float).to_numpy()
    r2 = None
    if len(target) >= 2 and not np.all(target == target[0]):
        residual_sum = float(np.sum(np.square(error)))
        total_sum = float(np.sum(np.square(target - np.mean(target))))
        r2 = float(1.0 - residual_sum / total_sum)
    return {"count": int(len(frame)), "mae": mae, "rmse": rmse, "r2": r2}


def _metric_report(frame: pd.DataFrame) -> dict[str, Any]:
    pooled = _metric_values(frame)
    by_city = {
        str(city): _metric_values(group)
        for city, group in frame.groupby("City", sort=True)
    }
    macro: dict[str, float | None] = {}
    for metric in ("mae", "rmse", "r2"):
        values = [
            result[metric]
            for result in by_city.values()
            if result[metric] is not None
        ]
        macro[metric] = float(np.mean(values)) if values else None
    return {
        "pooled": pooled,
        "macro_city": macro,
        "contributing_cities": len(by_city),
        "per_city": by_city,
    }


def evaluate_predictions(
    predictions_by_model: dict[str, pd.DataFrame],
    *,
    partition: str = "validation",
) -> dict[str, Any]:
    """Report native method coverage and paired common-case metrics."""
    if not predictions_by_model:
        raise ValueError("At least one model prediction frame is required")
    native: dict[str, Any] = {}
    common_sets: list[set[str]] = []
    protocol: tuple[str, int] | None = None
    common_frames: dict[str, pd.DataFrame] = {}
    for method, predictions in predictions_by_model.items():
        required = {
            "case_id",
            "City",
            "target",
            "target_valid",
            "prediction",
            "prediction_available",
            "prediction_exclusion_reason",
            "partition",
            "horizon_days",
            "policy",
        }
        missing = required.difference(predictions.columns)
        if missing:
            raise ValueError(f"{method} predictions lack columns: {sorted(missing)}")
        scoped = predictions.loc[predictions["partition"].eq(partition)].copy()
        key = (
            str(_single_protocol_value(scoped, "policy")),
            int(_single_protocol_value(scoped, "horizon_days")),
        )
        if protocol is None:
            protocol = key
        elif protocol != key:
            raise ValueError("Prediction frames must share target policy and horizon")
        if scoped["case_id"].duplicated().any():
            raise ValueError(f"{method} predictions contain duplicate case IDs")
        valid_targets = scoped["target_valid"].astype(bool) & scoped["target"].notna()
        scorable = valid_targets & scoped["prediction_available"].astype(bool)
        scored = scoped.loc[scorable]
        reason_counts = (
            scoped.loc[valid_targets & ~scoped["prediction_available"].astype(bool), "prediction_exclusion_reason"]
            .fillna("unspecified")
            .value_counts()
            .astype(int)
            .to_dict()
        )
        native[method] = {
            "valid_target_cases": int(valid_targets.sum()),
            "predicted_valid_target_cases": int(scorable.sum()),
            "unavailable_valid_target_cases": int((valid_targets & ~scoped["prediction_available"].astype(bool)).sum()),
            "coverage": (
                float(scorable.sum() / valid_targets.sum())
                if valid_targets.any()
                else None
            ),
            "unavailable_reasons": {str(k): int(v) for k, v in reason_counts.items()},
            "metrics": _metric_report(scored),
        }
        common_sets.append(set(scoped.loc[scorable, "case_id"].astype(str)))
        common_frames[method] = scoped
    common_cases = set.intersection(*common_sets) if common_sets else set()
    common_metrics: dict[str, Any] = {}
    for method, scoped in common_frames.items():
        paired = scoped.loc[
            scoped["case_id"].astype(str).isin(common_cases)
            & scoped["target_valid"].astype(bool)
            & scoped["prediction_available"].astype(bool)
        ]
        common_metrics[method] = _metric_report(paired)
    assert protocol is not None
    return {
        "policy": protocol[0],
        "horizon_days": protocol[1],
        "partition": partition,
        "methods": native,
        "common_case_count": len(common_cases),
        "common_case_metrics": common_metrics,
    }


def select_ridge_alpha(
    development_samples: pd.DataFrame,
    *,
    alphas: tuple[float, ...] = RIDGE_ALPHA_CANDIDATES,
) -> dict[str, Any]:
    """Select alpha by mean fold MAE across the fixed expanding folds.

    Equal-weight fold mean is used; exact ties select the larger alpha. The
    final test period is rejected and never used by this function.
    """
    if not alphas or any(not math.isfinite(alpha) or alpha <= 0 for alpha in alphas):
        raise ValueError("Ridge alpha candidates must be finite positive values")
    if len(set(alphas)) != len(alphas):
        raise ValueError("Ridge alpha candidates must be unique")
    if "target_date" not in development_samples:
        raise ValueError("Development samples require target_date")
    dates = pd.to_datetime(development_samples["target_date"], errors="coerce").dt.normalize()
    if dates.isna().any():
        raise ValueError("Development target dates must be valid")
    if dates.max() >= pd.Timestamp("2020-01-01"):
        raise ValueError("Final-test dates cannot be used for Ridge selection")

    rows: list[dict[str, Any]] = []
    folds = expanding_window_folds()
    for alpha in alphas:
        fold_maes: list[float] = []
        for fold in folds:
            train, validation = split_fold(development_samples, fold)
            model = fit_ridge_model(train, float(alpha))
            predictions = ridge_predictions(model, validation)
            scored = predictions.loc[
                predictions["target_valid"].astype(bool)
                & predictions["prediction_available"].astype(bool)
            ]
            if scored.empty:
                raise ValueError(f"No scorable validation rows in {fold['name']}")
            mae = _metric_values(scored)["mae"]
            assert mae is not None
            fold_maes.append(mae)
            rows.append(
                {
                    "alpha": float(alpha),
                    "fold": fold["name"],
                    "validation_cases": int(len(scored)),
                    "mae": mae,
                }
            )
    mean_scores = {
        float(alpha): float(
            np.mean([row["mae"] for row in rows if row["alpha"] == float(alpha)])
        )
        for alpha in alphas
    }
    selected = min(mean_scores, key=lambda alpha: (mean_scores[alpha], -alpha))
    return {
        "selected_alpha": selected,
        "selection_rule": (
            "Minimize equal-weight mean MAE across fold_2017, fold_2018, "
            "and fold_2019; exact ties choose the larger alpha."
        ),
        "fold_scores": rows,
        "mean_mae_by_alpha": mean_scores,
    }


def run_policy_horizon_development(
    samples: pd.DataFrame,
    history: pd.DataFrame,
    *,
    alphas: tuple[float, ...] = RIDGE_ALPHA_CANDIDATES,
) -> dict[str, Any]:
    """Fit baselines on approved training data and report 2019 validation only."""
    policy = str(_single_protocol_value(samples, "policy"))
    horizon = int(_single_protocol_value(samples, "horizon_days"))
    if horizon not in HORIZONS_DAYS:
        raise ValueError(f"Unsupported horizon {horizon}")
    if "partition" not in samples:
        raise ValueError("Samples must be assigned to temporal partitions")
    development = samples.loc[
        samples["partition"].isin(["train", "validation"])
    ].copy()
    training = development.loc[development["partition"].eq("train")].copy()
    validation = development.loc[
        development["partition"].eq("validation")
    ].copy()
    if training.empty or validation.empty:
        raise ValueError("Approved training and validation partitions must be non-empty")

    predictions: dict[str, pd.DataFrame] = {
        _PERSISTENCE: persistence_predictions(validation),
        _ANNUAL: annual_seasonal_naive_predictions(history, validation),
    }
    climatology = fit_city_month_climatology(training)
    predictions[_CLIMATOLOGY] = climatology_predictions(climatology, validation)
    selection = select_ridge_alpha(development, alphas=alphas)
    ridge = fit_ridge_model(training, selection["selected_alpha"])
    predictions[_RIDGE] = ridge_predictions(ridge, validation)
    if horizon != 7:
        predictions[_WEEKLY] = weekly_seasonal_naive_predictions(history, validation)

    return {
        "policy": policy,
        "horizon_days": horizon,
        "train_target_dates": [TRAIN_START, TRAIN_END],
        "validation_target_dates": ["2019-01-01", "2019-12-31"],
        "final_test_scored": False,
        "final_test_used_for_selection": False,
        "climatology_training_cases": climatology.training_case_count,
        "climatology_training_cities": climatology.training_city_count,
        "ridge_selection": selection,
        "validation": evaluate_predictions(predictions, partition="validation"),
    }
