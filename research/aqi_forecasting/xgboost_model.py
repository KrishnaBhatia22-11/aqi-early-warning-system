"""XGBoost comparator fitted on the same footing as the Ridge baseline.

The predictor schema, sample construction, eligibility rule, training
partition, and fold-selection rule are the ones already frozen in
``protocol.py``, ``forecast_samples.py``, and ``temporal_splits.py``. Rows
with any missing or policy-invalid primary feature are UNAVAILABLE; XGBoost's
native missing-value handling is deliberately not used, so native coverage
stays identical to Ridge and the two models remain comparable on the same
cases.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from xgboost import XGBRegressor

from research.aqi_forecasting.baselines import (
    _metric_values,
    _prediction_frame,
    _validate_training_dates,
)
from research.aqi_forecasting.leakage_checks import validate_feature_schema
from research.aqi_forecasting.protocol import PRIMARY_FEATURE_COLUMNS
from research.aqi_forecasting.temporal_splits import expanding_window_folds, split_fold

XGBOOST_METHOD = "xgboost"
XGBOOST_SEED = 0
XGBOOST_LEARNING_RATE = 0.05
XGBOOST_SUBSAMPLE = 0.8
XGBOOST_COLSAMPLE_BYTREE = 1.0
XGBOOST_MAX_DEPTHS = (3, 6)
XGBOOST_N_ESTIMATORS = (200, 500)

XGBOOST_SELECTION_RULE = (
    "Minimize equal-weight mean MAE across fold_2017, fold_2018, and "
    "fold_2019; exact ties choose the smaller max_depth, then the smaller "
    "n_estimators."
)
_UNAVAILABLE_REASON = "missing_or_invalid_primary_feature"


@dataclass(frozen=True)
class XGBoostConfig:
    """One predeclared grid point; every other setting is fixed."""

    max_depth: int
    n_estimators: int

    @property
    def name(self) -> str:
        return f"depth{self.max_depth}_trees{self.n_estimators}"

    def as_dict(self) -> dict[str, Any]:
        return {
            "max_depth": int(self.max_depth),
            "n_estimators": int(self.n_estimators),
            "learning_rate": XGBOOST_LEARNING_RATE,
            "subsample": XGBOOST_SUBSAMPLE,
            "colsample_bytree": XGBOOST_COLSAMPLE_BYTREE,
            "random_state": XGBOOST_SEED,
        }


def xgboost_grid() -> tuple[XGBoostConfig, ...]:
    """Return the predeclared grid in deterministic simple-to-complex order."""
    return tuple(
        XGBoostConfig(max_depth=depth, n_estimators=trees)
        for depth in XGBOOST_MAX_DEPTHS
        for trees in XGBOOST_N_ESTIMATORS
    )


def _new_regressor(config: XGBoostConfig) -> XGBRegressor:
    return XGBRegressor(
        max_depth=int(config.max_depth),
        n_estimators=int(config.n_estimators),
        learning_rate=XGBOOST_LEARNING_RATE,
        subsample=XGBOOST_SUBSAMPLE,
        colsample_bytree=XGBOOST_COLSAMPLE_BYTREE,
        objective="reg:squarederror",
        tree_method="hist",
        random_state=XGBOOST_SEED,
        n_jobs=1,
        verbosity=0,
    )


def eligible_fit_rows(training_samples: pd.DataFrame, *, model_name: str) -> pd.DataFrame:
    """Return the eligible, valid-target rows a model may be fitted on."""
    required = {"target", "target_valid", "eligible", *PRIMARY_FEATURE_COLUMNS}
    missing = required.difference(training_samples.columns)
    if missing:
        raise ValueError(f"{model_name} training samples are missing columns: {sorted(missing)}")
    fit_rows = training_samples.loc[
        training_samples["eligible"].astype(bool)
        & training_samples["target_valid"].astype(bool)
    ]
    if fit_rows.empty:
        raise ValueError(f"No eligible training rows are available for {model_name}")
    x_train = fit_rows.loc[:, list(PRIMARY_FEATURE_COLUMNS)].astype(float)
    y_train = fit_rows["target"].astype(float)
    if not np.isfinite(x_train.to_numpy()).all() or not np.isfinite(y_train.to_numpy()).all():
        raise ValueError(f"{model_name} training features and labels must be finite")
    return fit_rows


def fit_xgboost_model(training_samples: pd.DataFrame, config: XGBoostConfig) -> XGBRegressor:
    """Fit one grid point on eligible 2015-2018 train-partition rows only."""
    validate_feature_schema(PRIMARY_FEATURE_COLUMNS)
    if not isinstance(config, XGBoostConfig):
        raise TypeError("config must be an XGBoostConfig")
    if config.max_depth not in XGBOOST_MAX_DEPTHS or config.n_estimators not in XGBOOST_N_ESTIMATORS:
        raise ValueError(f"Configuration {config.name} is outside the predeclared grid")
    if "partition" not in training_samples or not training_samples["partition"].eq("train").all():
        raise ValueError("XGBoost may only be fitted on train-partition targets")
    _validate_training_dates(training_samples)
    fit_rows = eligible_fit_rows(training_samples, model_name="XGBoost")
    model = _new_regressor(config)
    model.fit(
        fit_rows.loc[:, list(PRIMARY_FEATURE_COLUMNS)].astype(float),
        fit_rows["target"].astype(float),
    )
    return model


def xgboost_predictions(model: XGBRegressor, samples: pd.DataFrame) -> pd.DataFrame:
    """Predict eligible rows only, mirroring ``ridge_predictions`` exactly."""
    validate_feature_schema(PRIMARY_FEATURE_COLUMNS)
    missing = set(PRIMARY_FEATURE_COLUMNS).difference(samples.columns)
    if missing:
        raise ValueError(f"XGBoost prediction samples are missing features: {sorted(missing)}")
    if "eligible" not in samples:
        raise ValueError("XGBoost prediction samples are missing the eligibility flag")
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
            reasons.append(_UNAVAILABLE_REASON)
    return _prediction_frame(samples, XGBOOST_METHOD, predictions, reasons)


def select_xgboost_config(development_samples: pd.DataFrame) -> dict[str, Any]:
    """Select one grid point by mean fold MAE over the frozen expanding folds.

    The equal-weight fold mean is used, exactly as for Ridge alpha. Exact ties
    select the simpler configuration: smaller ``max_depth``, then fewer trees.
    The locked final-test period is rejected and never used here.
    """
    if "target_date" not in development_samples:
        raise ValueError("Development samples require target_date")
    dates = pd.to_datetime(development_samples["target_date"], errors="coerce").dt.normalize()
    if dates.isna().any():
        raise ValueError("Development target dates must be valid")
    if dates.max() >= pd.Timestamp("2020-01-01"):
        raise ValueError("Final-test dates cannot be used for XGBoost selection")

    rows: list[dict[str, Any]] = []
    folds = expanding_window_folds()
    grid = xgboost_grid()
    for config in grid:
        for fold in folds:
            train, validation = split_fold(development_samples, fold)
            model = fit_xgboost_model(train, config)
            predictions = xgboost_predictions(model, validation)
            scored = predictions.loc[
                predictions["target_valid"].astype(bool)
                & predictions["prediction_available"].astype(bool)
            ]
            if scored.empty:
                raise ValueError(f"No scorable validation rows in {fold['name']}")
            mae = _metric_values(scored)["mae"]
            assert mae is not None
            rows.append(
                {
                    "config": config.name,
                    "max_depth": int(config.max_depth),
                    "n_estimators": int(config.n_estimators),
                    "fold": fold["name"],
                    "validation_cases": int(len(scored)),
                    "mae": mae,
                }
            )
    mean_scores = {
        config.name: float(
            np.mean([row["mae"] for row in rows if row["config"] == config.name])
        )
        for config in grid
    }
    by_name = {config.name: config for config in grid}
    selected_name = min(
        mean_scores,
        key=lambda name: (
            mean_scores[name],
            by_name[name].max_depth,
            by_name[name].n_estimators,
        ),
    )
    selected = by_name[selected_name]
    return {
        "selected_config": selected.as_dict(),
        "selected_config_name": selected_name,
        "selection_rule": XGBOOST_SELECTION_RULE,
        "fixed_hyperparameters": {
            "learning_rate": XGBOOST_LEARNING_RATE,
            "subsample": XGBOOST_SUBSAMPLE,
            "colsample_bytree": XGBOOST_COLSAMPLE_BYTREE,
            "objective": "reg:squarederror",
            "tree_method": "hist",
            "random_state": XGBOOST_SEED,
            "n_jobs": 1,
        },
        "grid": [config.as_dict() for config in grid],
        "fold_scores": rows,
        "mean_mae_by_config": mean_scores,
    }


def config_from_dict(payload: dict[str, Any]) -> XGBoostConfig:
    """Rebuild a grid point from a recorded selection payload."""
    return XGBoostConfig(
        max_depth=int(payload["max_depth"]),
        n_estimators=int(payload["n_estimators"]),
    )


__all__ = [
    "XGBOOST_METHOD",
    "XGBOOST_SEED",
    "XGBOOST_SELECTION_RULE",
    "XGBoostConfig",
    "config_from_dict",
    "eligible_fit_rows",
    "fit_xgboost_model",
    "select_xgboost_config",
    "xgboost_grid",
    "xgboost_predictions",
]
