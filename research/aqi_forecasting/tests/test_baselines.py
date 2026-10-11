import unittest

import numpy as np
import pandas as pd

from research.aqi_forecasting.baselines import (
    RIDGE_ALPHA_CANDIDATES,
    annual_seasonal_naive_predictions,
    climatology_predictions,
    evaluate_predictions,
    fit_city_month_climatology,
    fit_ridge_model,
    persistence_predictions,
    ridge_predictions,
    select_ridge_alpha,
    weekly_seasonal_naive_predictions,
)
from research.aqi_forecasting.forecast_samples import build_forecast_samples
from research.aqi_forecasting.protocol import PRIMARY_FEATURE_COLUMNS
from research.aqi_forecasting.temporal_splits import assign_partition, split_fold


def _raw_daily(start="2020-01-01", end="2020-01-31", *, city="A"):
    dates = pd.date_range(start, end, freq="D")
    return pd.DataFrame(
        {"City": city, "Date": dates, "AQI": np.arange(10, 10 + len(dates), dtype=float)}
    )


def _prediction_samples(
    *,
    city="A",
    target_date="2020-01-10",
    origin_date="2020-01-09",
    horizon=1,
    policy="exclude",
    target=42.0,
    partition="validation",
):
    return pd.DataFrame(
        {
            "case_id": [f"{city}|{target_date}|h{horizon}"],
            "City": [city],
            "target_date": [pd.Timestamp(target_date)],
            "origin_date": [pd.Timestamp(origin_date)],
            "horizon_days": [horizon],
            "policy": [policy],
            "partition": [partition],
            "target": [target],
            "target_valid": [True],
        }
    )


def _ridge_rows(dates, partition):
    rows = []
    for index, target_date in enumerate(dates):
        features = {
            feature: float(index + feature_index)
            for feature_index, feature in enumerate(PRIMARY_FEATURE_COLUMNS)
        }
        rows.append(
            {
                "case_id": f"A|{target_date.date()}|h1",
                "City": "A",
                "target_date": target_date,
                "origin_date": target_date - pd.Timedelta(days=1),
                "horizon_days": 1,
                "policy": "exclude",
                "partition": partition,
                "target": float(index % 50 + 10),
                "target_valid": True,
                "eligible": True,
                **features,
            }
        )
    return pd.DataFrame(rows)


class BaselineTests(unittest.TestCase):
    def test_persistence_uses_exact_origin_and_reports_missing_observation(self):
        raw = _raw_daily()
        raw.loc[raw.Date.eq(pd.Timestamp("2020-01-09")), "AQI"] = np.nan
        samples = assign_partition(build_forecast_samples(raw, 1, "exclude"))
        predictions = persistence_predictions(samples)
        Jan10 = predictions.loc[predictions.target_date.eq(pd.Timestamp("2020-01-10"))].iloc[0]
        Jan11 = predictions.loc[predictions.target_date.eq(pd.Timestamp("2020-01-11"))].iloc[0]
        self.assertFalse(Jan10.prediction_available)
        self.assertEqual(Jan10.prediction_exclusion_reason, "missing_origin_aqi")
        self.assertEqual(Jan11.prediction, 19.0)
        self.assertEqual(Jan11.origin_date, pd.Timestamp("2020-01-10"))
        self.assertEqual(Jan11.policy, "exclude")
        self.assertEqual(Jan11.horizon_days, 1)

    def test_annual_naive_uses_exact_previous_year_and_february_28_rule(self):
        history = pd.DataFrame(
            {
                "City": ["A", "A", "A"],
                "Date": ["2019-02-28", "2019-03-01", "2020-02-28"],
                "AQI": [280.0, 301.0, 228.0],
            }
        )
        samples = pd.concat(
            [
                _prediction_samples(
                    target_date="2020-02-29", origin_date="2020-02-28", horizon=1
                ),
                _prediction_samples(
                    target_date="2021-02-28", origin_date="2021-02-27", horizon=1
                ),
            ],
            ignore_index=True,
        )
        predictions = annual_seasonal_naive_predictions(history, samples)
        leap = predictions.iloc[0]
        self.assertEqual(leap.prediction, 280.0)
        self.assertEqual(leap.prediction_source, "2019-02-28")
        non_leap = predictions.iloc[1]
        self.assertEqual(non_leap.prediction, 228.0)
        self.assertEqual(non_leap.prediction_source, "2020-02-28")

    def test_annual_naive_keeps_missing_historical_observation_unavailable(self):
        history = pd.DataFrame(
            {"City": ["A"], "Date": ["2019-01-10"], "AQI": [np.nan]}
        )
        samples = _prediction_samples()
        prediction = annual_seasonal_naive_predictions(history, samples).iloc[0]
        self.assertFalse(prediction.prediction_available)
        self.assertEqual(
            prediction.prediction_exclusion_reason, "missing_annual_observation"
        )
        self.assertEqual(prediction.prediction_source, "2019-01-10")

    def test_annual_naive_ignores_history_after_latest_forecast_origin(self):
        history = pd.DataFrame(
            {
                "City": ["A", "A"],
                "Date": ["2019-01-10", "2020-01-11"],
                "AQI": [25.0, 999999.0],
            }
        )
        prediction = annual_seasonal_naive_predictions(
            history, _prediction_samples()
        ).iloc[0]
        self.assertEqual(prediction.prediction, 25.0)

    def test_annual_naive_applies_same_target_policy_to_historical_value(self):
        history = pd.DataFrame(
            {"City": ["A"], "Date": ["2019-01-10"], "AQI": [501.0]}
        )
        cap_sample = _prediction_samples(policy="cap")
        exclude_sample = _prediction_samples(policy="exclude")
        capped = annual_seasonal_naive_predictions(history, cap_sample).iloc[0]
        excluded = annual_seasonal_naive_predictions(history, exclude_sample).iloc[0]
        self.assertEqual(capped.prediction, 500.0)
        self.assertFalse(excluded.prediction_available)
        self.assertEqual(
            excluded.prediction_exclusion_reason,
            "invalid_annual_observation_above_500",
        )

    def test_city_month_climatology_uses_pooled_fallback_for_unseen_city(self):
        train = pd.DataFrame(
            {
                "City": ["A", "A", "B"],
                "target_date": pd.to_datetime(
                    ["2018-01-01", "2018-01-02", "2018-01-03"]
                ),
                "target": [10.0, 20.0, 40.0],
                "target_valid": [True, True, True],
                "partition": ["train"] * 3,
                "policy": ["exclude"] * 3,
                "horizon_days": [1] * 3,
            }
        )
        fitted = fit_city_month_climatology(train)
        cases = pd.concat(
            [
                _prediction_samples(city="A", target_date="2019-01-10"),
                _prediction_samples(city="Z", target_date="2019-01-11"),
            ],
            ignore_index=True,
        )
        predictions = climatology_predictions(fitted, cases)
        self.assertEqual(predictions.iloc[0].prediction, 15.0)
        self.assertEqual(predictions.iloc[0].prediction_source, "city_month")
        self.assertEqual(predictions.iloc[1].prediction, 70.0 / 3.0)
        self.assertEqual(
            predictions.iloc[1].prediction_source, "pooled_month_fallback"
        )
        self.assertEqual(fitted.training_case_count, 3)

    def test_climatology_fit_is_training_only_and_independent_of_other_labels(self):
        train = pd.DataFrame(
            {
                "City": ["A", "B"],
                "target_date": pd.to_datetime(["2018-01-01", "2018-01-02"]),
                "target": [10.0, 30.0],
                "target_valid": [True, True],
                "partition": ["train", "train"],
                "policy": ["exclude", "exclude"],
                "horizon_days": [1, 1],
            }
        )
        validation = pd.DataFrame(
            {
                "City": ["A"],
                "target_date": pd.to_datetime(["2019-01-03"]),
                "target": [9999.0],
                "target_valid": [True],
                "partition": ["validation"],
                "policy": ["exclude"],
                "horizon_days": [1],
            }
        )
        first_fit = fit_city_month_climatology(train)
        changed_validation = validation.assign(target=-100000.0)
        second_fit = fit_city_month_climatology(train.copy())
        self.assertEqual(first_fit.city_month_means, second_fit.city_month_means)
        self.assertEqual(first_fit.pooled_month_means, second_fit.pooled_month_means)
        with self.assertRaisesRegex(ValueError, "train-partition"):
            fit_city_month_climatology(pd.concat([train, changed_validation]))

    def test_ridge_uses_exact_primary_features_and_training_only_scaling(self):
        train = _ridge_rows(
            pd.date_range("2015-01-01", periods=4, freq="D"), "train"
        )
        validation = _ridge_rows(
            pd.date_range("2019-01-01", periods=2, freq="D"), "validation"
        )
        validation.loc[:, list(PRIMARY_FEATURE_COLUMNS)] = 100000.0
        model = fit_ridge_model(train, alpha=1.0)
        expected_means = train.loc[:, list(PRIMARY_FEATURE_COLUMNS)].mean().to_numpy()
        self.assertTrue(
            np.allclose(model.named_steps["scaler"].mean_, expected_means)
        )
        predictions = ridge_predictions(model, validation)
        self.assertTrue(predictions.prediction_available.all())
        self.assertTrue(np.allclose(model.named_steps["scaler"].mean_, expected_means))

    def test_climatology_and_ridge_reject_training_rows_outside_approved_dates(self):
        outside_train = pd.DataFrame(
            {
                "City": ["A"],
                "target_date": [pd.Timestamp("2020-01-01")],
                "target": [10.0],
                "target_valid": [True],
                "partition": ["train"],
                "policy": ["exclude"],
                "horizon_days": [1],
                "eligible": [True],
                **{feature: [1.0] for feature in PRIMARY_FEATURE_COLUMNS},
            }
        )
        with self.assertRaisesRegex(ValueError, "Training targets must fall"):
            fit_city_month_climatology(outside_train)
        with self.assertRaisesRegex(ValueError, "Training targets must fall"):
            fit_ridge_model(outside_train, alpha=1.0)

    def test_ridge_selection_uses_disjoint_fixed_folds_and_rejects_test_dates(self):
        dates = pd.date_range("2015-01-01", "2019-12-31", freq="D")
        train_dates = dates[dates <= pd.Timestamp("2018-12-31")]
        development = pd.concat(
            [
                _ridge_rows(train_dates, "train"),
                _ridge_rows(dates[dates >= pd.Timestamp("2019-01-01")], "validation"),
            ],
            ignore_index=True,
        )
        for fold in (
            {
                "name": "fold_2017",
                "train_start": "2015-01-01",
                "train_end": "2016-12-31",
                "validation_start": "2017-01-01",
                "validation_end": "2017-12-31",
            },
            {
                "name": "fold_2018",
                "train_start": "2015-01-01",
                "train_end": "2017-12-31",
                "validation_start": "2018-01-01",
                "validation_end": "2018-12-31",
            },
        ):
            train, validation = split_fold(development, fold)
            self.assertFalse(set(train.case_id) & set(validation.case_id))
            self.assertLess(train.target_date.max(), validation.target_date.min())
        result = select_ridge_alpha(development, alphas=RIDGE_ALPHA_CANDIDATES)
        self.assertIn(result["selected_alpha"], RIDGE_ALPHA_CANDIDATES)
        self.assertEqual(len(result["fold_scores"]), 9)

        with_test = pd.concat(
            [
                development,
                _ridge_rows(
                    pd.date_range("2020-01-01", periods=1, freq="D"), "test"
                ),
            ],
            ignore_index=True,
        )
        with self.assertRaisesRegex(ValueError, "Final-test dates"):
            select_ridge_alpha(with_test)

    def test_native_coverage_missing_predictions_and_common_case_metrics(self):
        persistence = _prediction_samples()
        persistence["prediction"] = pd.array([20.0], dtype="Float64")
        persistence["prediction_available"] = True
        persistence["prediction_exclusion_reason"] = None
        annual = persistence.copy()
        annual["case_id"] = "A|2020-01-11|h1"
        annual["target"] = 50.0
        annual["prediction"] = pd.array([pd.NA], dtype="Float64")
        annual["prediction_available"] = False
        annual["prediction_exclusion_reason"] = "missing_annual_observation"
        climatology = persistence.copy()
        climatology["prediction"] = pd.array([30.0], dtype="Float64")
        ridge = persistence.copy()
        ridge["prediction"] = pd.array([40.0], dtype="Float64")

        report = evaluate_predictions(
            {
                "persistence": persistence,
                "annual": annual,
                "climatology": climatology,
                "ridge": ridge,
            }
        )
        self.assertEqual(report["common_case_count"], 0)
        self.assertEqual(
            report["methods"]["annual"]["unavailable_reasons"],
            {"missing_annual_observation": 1},
        )
        self.assertEqual(report["methods"]["persistence"]["coverage"], 1.0)

        same_case_annual = annual.assign(
            case_id=persistence.iloc[0].case_id,
            target=persistence.iloc[0].target,
            prediction=pd.array([21.0], dtype="Float64"),
            prediction_available=True,
            prediction_exclusion_reason=None,
        )
        common = evaluate_predictions(
            {
                "persistence": persistence,
                "annual": same_case_annual,
                "climatology": climatology,
                "ridge": ridge,
            }
        )
        self.assertEqual(common["common_case_count"], 1)
        self.assertEqual(
            common["common_case_metrics"]["persistence"]["pooled"]["count"], 1
        )
        self.assertIsNone(
            common["common_case_metrics"]["persistence"]["pooled"]["r2"]
        )

    def test_weekly_naive_equals_persistence_at_seven_day_horizon(self):
        raw = _raw_daily()
        samples = assign_partition(build_forecast_samples(raw, 7, "exclude"))
        persistence = persistence_predictions(samples)
        weekly = weekly_seasonal_naive_predictions(raw, samples)
        available = persistence.prediction_available & weekly.prediction_available
        self.assertTrue(available.any())
        self.assertTrue(
            np.allclose(
                persistence.loc[available, "prediction"].astype(float),
                weekly.loc[available, "prediction"].astype(float),
            )
        )
        self.assertEqual(
            set(persistence.loc[available, "case_id"]),
            set(weekly.loc[available, "case_id"]),
        )


if __name__ == "__main__":
    unittest.main()
