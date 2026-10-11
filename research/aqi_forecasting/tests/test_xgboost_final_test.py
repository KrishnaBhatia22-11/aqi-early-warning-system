import unittest

import numpy as np
import pandas as pd

from research.aqi_forecasting import run_final_test as runner
from research.aqi_forecasting.baselines import fit_ridge_model, ridge_predictions
from research.aqi_forecasting.final_test import (
    LOCKDOWN_WINDOW,
    PRE_LOCKDOWN_WINDOW,
    city_cluster_bootstrap,
    fit_refit_climatology,
    fit_refit_ridge,
    fit_refit_xgboost,
    lockdown_split_metrics,
    validate_refit_samples,
)
from research.aqi_forecasting.forecast_samples import build_forecast_samples
from research.aqi_forecasting.temporal_splits import assign_partition
from research.aqi_forecasting.xgboost_model import (
    XGBOOST_METHOD,
    XGBoostConfig,
    fit_xgboost_model,
    select_xgboost_config,
    xgboost_grid,
    xgboost_predictions,
)

_CITIES = ("Alpha", "Beta", "Gamma")


def _synthetic_history(start="2015-01-01", end="2020-07-01"):
    """Daily AQI for several cities, with deliberate gaps and above-500 values."""
    dates = pd.date_range(start, end, freq="D")
    rng = np.random.default_rng(7)
    frames = []
    for offset, city in enumerate(_CITIES):
        day_of_year = dates.dayofyear.to_numpy(dtype="float64")
        level = (
            140.0
            + 25.0 * offset
            + 70.0 * np.cos(2 * np.pi * (day_of_year - 15.0) / 365.25)
            + rng.normal(0.0, 18.0, size=len(dates))
        )
        values = pd.Series(level, index=range(len(dates)))
        # Deliberate unavailability in every partition: missing blocks and
        # above-500 spikes in training, 2019 validation, and the test window.
        values.iloc[40:47] = np.nan
        values.iloc[500 + offset] = 640.0
        values.iloc[1500:1505] = np.nan
        values.iloc[1600 + offset] = 620.0
        values.iloc[1900 + offset] = np.nan
        values.iloc[1950 + offset] = 710.0
        frames.append(pd.DataFrame({"City": city, "Date": dates, "AQI": values.to_numpy()}))
    return pd.concat(frames, ignore_index=True)


def _samples(history, horizon=1, policy="exclude"):
    return assign_partition(build_forecast_samples(history, horizon, policy))


class XGBoostParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = _synthetic_history()
        cls.samples = _samples(cls.history)
        cls.train = cls.samples.loc[cls.samples["partition"].eq("train")].copy()
        cls.validation = cls.samples.loc[cls.samples["partition"].eq("validation")].copy()

    def test_availability_and_exclusion_reasons_match_ridge_exactly(self):
        ridge = ridge_predictions(fit_ridge_model(self.train, 1.0), self.validation)
        boosted = xgboost_predictions(
            fit_xgboost_model(self.train, XGBoostConfig(3, 200)), self.validation
        )
        self.assertTrue(
            (~self.validation["eligible"].astype(bool)).any(),
            "fixture must contain ineligible rows for the parity check to mean anything",
        )
        pd.testing.assert_series_equal(
            ridge["prediction_available"],
            boosted["prediction_available"],
            check_names=False,
        )
        pd.testing.assert_series_equal(
            ridge["prediction_exclusion_reason"],
            boosted["prediction_exclusion_reason"],
            check_names=False,
        )
        self.assertEqual(
            set(ridge.loc[ridge["prediction_available"], "case_id"]),
            set(boosted.loc[boosted["prediction_available"], "case_id"]),
        )
        self.assertEqual(boosted["method"].drop_duplicates().tolist(), [XGBOOST_METHOD])

    def test_native_nan_handling_is_not_used(self):
        model = fit_xgboost_model(self.train, XGBoostConfig(3, 200))
        ineligible = self.validation.loc[~self.validation["eligible"].astype(bool)]
        self.assertFalse(ineligible.empty)
        predictions = xgboost_predictions(model, ineligible)
        self.assertFalse(predictions["prediction_available"].any())
        self.assertTrue(predictions["prediction"].isna().all())
        self.assertEqual(
            set(predictions["prediction_exclusion_reason"]),
            {"missing_or_invalid_primary_feature"},
        )

    def test_coverage_counts_are_identical_for_both_models(self):
        ridge = ridge_predictions(fit_ridge_model(self.train, 1.0), self.validation)
        boosted = xgboost_predictions(
            fit_xgboost_model(self.train, XGBoostConfig(6, 500)), self.validation
        )
        valid = self.validation["target_valid"].astype(bool)
        self.assertEqual(
            int((valid & ridge["prediction_available"].to_numpy()).sum()),
            int((valid & boosted["prediction_available"].to_numpy()).sum()),
        )

    def test_fit_requires_train_partition_and_training_dates(self):
        with self.assertRaises(ValueError):
            fit_xgboost_model(self.validation, XGBoostConfig(3, 200))
        mislabelled = self.validation.copy()
        mislabelled["partition"] = "train"
        with self.assertRaises(ValueError):
            fit_xgboost_model(mislabelled, XGBoostConfig(3, 200))

    def test_grid_is_the_declared_four_candidates_in_simple_first_order(self):
        self.assertEqual(
            [(config.max_depth, config.n_estimators) for config in xgboost_grid()],
            [(3, 200), (3, 500), (6, 200), (6, 500)],
        )

    def test_off_grid_configuration_is_rejected(self):
        with self.assertRaises(ValueError):
            fit_xgboost_model(self.train, XGBoostConfig(9, 200))

    def test_selection_rejects_locked_test_dates_and_is_deterministic(self):
        full = _samples(_synthetic_history())
        with self.assertRaises(ValueError):
            select_xgboost_config(full)
        development = full.loc[full["partition"].isin(["train", "validation"])].copy()
        first = select_xgboost_config(development)
        second = select_xgboost_config(development)
        self.assertEqual(first["mean_mae_by_config"], second["mean_mae_by_config"])
        self.assertEqual(first["selected_config"], second["selected_config"])
        best = min(first["mean_mae_by_config"].values())
        tied = [
            name
            for name, score in first["mean_mae_by_config"].items()
            if score == best
        ]
        simplest = min(
            tied,
            key=lambda name: (
                int(name.split("_")[0].removeprefix("depth")),
                int(name.split("_")[1].removeprefix("trees")),
            ),
        )
        self.assertEqual(first["selected_config_name"], simplest)


class FinalTestRefitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = _synthetic_history()
        cls.samples = _samples(cls.history)
        cls.refit = cls.samples.loc[
            cls.samples["partition"].isin(["train", "validation"])
        ].copy()
        cls.train = cls.samples.loc[cls.samples["partition"].eq("train")].copy()

    def test_refit_window_rejects_any_locked_test_target(self):
        with self.assertRaises(ValueError):
            validate_refit_samples(self.samples)
        with self.assertRaises(ValueError):
            fit_refit_ridge(self.samples, 1.0)
        with self.assertRaises(ValueError):
            fit_refit_xgboost(self.samples, XGBoostConfig(3, 200))
        with self.assertRaises(ValueError):
            fit_refit_climatology(self.samples)

    def test_refit_window_accepts_exactly_2015_through_2019(self):
        accepted = validate_refit_samples(self.refit)
        dates = pd.to_datetime(accepted["target_date"])
        self.assertEqual(str(dates.min().date()), "2015-01-01")
        self.assertEqual(str(dates.max().date()), "2019-12-31")

    def test_refit_ridge_reproduces_the_baseline_fit_on_train_only_rows(self):
        baseline = fit_ridge_model(self.train, 1.0)
        refit = fit_refit_ridge(self.train, 1.0)
        np.testing.assert_allclose(
            baseline.named_steps["ridge"].coef_, refit.named_steps["ridge"].coef_
        )
        np.testing.assert_allclose(
            baseline.named_steps["ridge"].intercept_, refit.named_steps["ridge"].intercept_
        )

    def test_refit_uses_more_data_than_the_development_fit(self):
        development = fit_refit_ridge(self.train, 1.0)
        extended = fit_refit_ridge(self.refit, 1.0)
        self.assertFalse(
            np.allclose(
                development.named_steps["ridge"].coef_,
                extended.named_steps["ridge"].coef_,
            )
        )


class LockedTestRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = _synthetic_history()
        cls.samples = _samples(cls.history)

    def test_runner_fits_only_on_targets_through_2019(self):
        observed: dict[str, pd.Timestamp] = {}

        def spy(name, wrapped):
            def inner(samples, *args, **kwargs):
                dates = pd.to_datetime(samples["target_date"])
                observed[f"{name}_max"] = dates.max()
                observed[f"{name}_partitions"] = frozenset(
                    samples["partition"].dropna().astype(str)
                )
                return wrapped(samples, *args, **kwargs)

            return inner

        originals = {
            "ridge": runner.fit_refit_ridge,
            "xgboost": runner.fit_refit_xgboost,
            "climatology": runner.fit_refit_climatology,
        }
        for name, wrapped in originals.items():
            setattr(runner, f"fit_refit_{name}", spy(name, wrapped))
        try:
            result = runner.score_locked_test(
                self.samples,
                self.history,
                ridge_alpha=1.0,
                xgboost_config=XGBoostConfig(3, 200).as_dict(),
            )
        finally:
            for name, wrapped in originals.items():
                setattr(runner, f"fit_refit_{name}", wrapped)

        self.assertEqual(
            sorted(observed),
            [
                "climatology_max",
                "climatology_partitions",
                "ridge_max",
                "ridge_partitions",
                "xgboost_max",
                "xgboost_partitions",
            ],
        )
        for name in originals:
            self.assertEqual(
                str(observed[f"{name}_max"].date()),
                "2019-12-31",
                f"{name} refit saw a target after 2019",
            )
            self.assertEqual(observed[f"{name}_partitions"], frozenset({"train", "validation"}))
        self.assertEqual(result["refit_case_counts"]["max_target_date"], "2019-12-31")
        self.assertEqual(result["test_target_dates"], ["2020-01-01", "2020-07-01"])
        self.assertEqual(result["refit_target_dates"], ["2015-01-01", "2019-12-31"])

    def test_scored_test_rows_stay_inside_the_locked_window(self):
        result = runner.score_locked_test(
            self.samples,
            self.history,
            ridge_alpha=1.0,
            xgboost_config=XGBoostConfig(3, 200).as_dict(),
        )
        self.assertEqual(result["test"]["partition"], "test")
        self.assertGreater(result["common_case_count"], 0)
        self.assertIn(XGBOOST_METHOD, result["test"]["common_case_metrics"])
        counts = {
            metrics["pooled"]["count"]
            for metrics in result["test"]["common_case_metrics"].values()
        }
        self.assertEqual(counts, {result["common_case_count"]})

    def test_lockdown_windows_partition_the_test_period_without_overlap(self):
        result = runner.score_locked_test(
            self.samples,
            self.history,
            ridge_alpha=1.0,
            xgboost_config=XGBoostConfig(3, 200).as_dict(),
        )
        lockdown = result["lockdown_split"]
        self.assertEqual(lockdown["windows"]["pre_lockdown"], list(PRE_LOCKDOWN_WINDOW))
        self.assertEqual(lockdown["windows"]["lockdown"], list(LOCKDOWN_WINDOW))
        self.assertEqual(
            lockdown["pre_lockdown_common_cases"] + lockdown["lockdown_common_cases"],
            result["common_case_count"],
        )
        self.assertLess(
            pd.Timestamp(PRE_LOCKDOWN_WINDOW[1]), pd.Timestamp(LOCKDOWN_WINDOW[0])
        )


class BootstrapTests(unittest.TestCase):
    @staticmethod
    def _frames():
        rng = np.random.default_rng(3)
        cities = ["Alpha", "Beta", "Gamma", "Delta"]
        rows = []
        for city_index, city in enumerate(cities):
            for day in range(40):
                rows.append(
                    {
                        "case_id": f"{city}|2020-01-{day + 1:02d}|h1",
                        "City": city,
                        "target_date": pd.Timestamp("2020-01-01") + pd.Timedelta(days=day),
                        "target": 100.0 + city_index * 10 + rng.normal(0, 5),
                    }
                )
        base = pd.DataFrame(rows)
        frames = {}
        for method, bias in (("persistence", 12.0), ("regularized_linear", 8.0), (XGBOOST_METHOD, 6.0)):
            frame = base.copy()
            frame["prediction"] = frame["target"] + bias
            frames[method] = frame.sort_values("case_id").reset_index(drop=True)
        return frames

    def test_bootstrap_is_deterministic_and_brackets_the_point_estimate(self):
        frames = self._frames()
        first = city_cluster_bootstrap(frames, replicates=500, seed=11)
        second = city_cluster_bootstrap(frames, replicates=500, seed=11)
        self.assertEqual(first["mae"], second["mae"])
        self.assertEqual(first["paired_difference"], second["paired_difference"])
        self.assertEqual(first["city_count"], 4)
        for method, interval in first["mae"].items():
            self.assertLessEqual(interval["ci_lower"], interval["mae"], method)
            self.assertLessEqual(interval["mae"], interval["ci_upper"], method)
        self.assertAlmostEqual(first["mae"]["persistence"]["mae"], 12.0, places=6)

    def test_paired_difference_matches_the_difference_of_point_estimates(self):
        frames = self._frames()
        result = city_cluster_bootstrap(frames, replicates=200, seed=5)
        for key, difference in result["paired_difference"].items():
            method = difference["method"]
            expected = result["mae"][method]["mae"] - result["mae"]["persistence"]["mae"]
            self.assertAlmostEqual(difference["mae_difference"], expected, places=9, msg=key)

    def test_mismatched_case_sets_are_rejected(self):
        frames = self._frames()
        frames[XGBOOST_METHOD] = frames[XGBOOST_METHOD].iloc[:-1].copy()
        with self.assertRaises(ValueError):
            city_cluster_bootstrap(frames, replicates=10, seed=1)

    def test_lockdown_split_reports_both_windows_for_every_method(self):
        frames = self._frames()
        split = lockdown_split_metrics(frames)
        self.assertEqual(sorted(split["methods"]), sorted(frames))
        for windows in split["methods"].values():
            self.assertEqual(sorted(windows), ["lockdown", "pre_lockdown"])


if __name__ == "__main__":
    unittest.main()
