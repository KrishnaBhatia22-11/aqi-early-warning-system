import pandas as pd
import unittest

from research.aqi_forecasting.forecast_samples import build_forecast_samples
from research.aqi_forecasting.leakage_checks import (
    validate_feature_schema,
    validate_partitions,
    validate_sample_timestamps,
)
from research.aqi_forecasting.protocol import PRIMARY_FEATURE_COLUMNS
from research.aqi_forecasting.temporal_splits import (
    assign_city_folds,
    assign_partition,
    expanding_window_folds,
    held_out_city_split,
    split_fold,
)


class SplitLeakageTests(unittest.TestCase):
    def test_split_fold_rejects_overlapping_or_reversed_ranges(self):
        samples = pd.DataFrame(
            {
                "target_date": pd.to_datetime(
                    ["2018-12-31", "2019-01-01", "2019-01-02"]
                ),
                "case_id": ["a", "b", "c"],
            }
        )
        base = {
            "train_start": "2018-01-01",
            "train_end": "2018-12-31",
            "validation_start": "2019-01-01",
            "validation_end": "2019-12-31",
        }
        overlap = {**base, "train_end": "2019-01-01"}
        with self.assertRaisesRegex(ValueError, "non-overlapping"):
            split_fold(samples, overlap)
        with self.assertRaisesRegex(ValueError, "training date range is reversed"):
            split_fold(samples, {**base, "train_start": "2019-01-01"})
        with self.assertRaisesRegex(ValueError, "validation date range is reversed"):
            split_fold(samples, {**base, "validation_start": "2020-01-01"})
        with self.assertRaisesRegex(ValueError, "valid date"):
            split_fold(samples, {**base, "train_start": "not-a-date"})
        with self.assertRaisesRegex(ValueError, "before the final test"):
            split_fold(
                samples,
                {**base, "validation_end": "2020-01-01"},
            )

    def test_split_fold_uses_target_dates_and_keeps_sample_ids_disjoint(self):
        samples = pd.DataFrame(
            {
                "target_date": pd.to_datetime(
                    ["2018-12-31", "2019-01-01", "2019-01-02"]
                ),
                "origin_date": pd.to_datetime(
                    ["2018-12-24", "2018-12-25", "2018-12-26"]
                ),
                "case_id": ["train", "boundary-validation", "validation"],
            }
        )
        fold = {
            "train_start": "2018-01-01",
            "train_end": "2018-12-31",
            "validation_start": "2019-01-01",
            "validation_end": "2019-12-31",
        }
        training, validation = split_fold(samples, fold)
        self.assertEqual(training["case_id"].tolist(), ["train"])
        self.assertEqual(
            validation["case_id"].tolist(), ["boundary-validation", "validation"]
        )
        self.assertLess(
            samples.loc[samples.case_id.eq("boundary-validation"), "origin_date"].iloc[0],
            pd.Timestamp(fold["validation_start"]),
        )
        self.assertFalse(set(training["case_id"]) & set(validation["case_id"]))

    def test_approved_target_date_partitions_and_boundary_origin(self):
        frame = pd.DataFrame(
            {
                "City": ["A"] * len(pd.date_range("2018-12-20", "2020-07-08")),
                "Date": pd.date_range("2018-12-20", "2020-07-08"),
                "AQI": list(range(len(pd.date_range("2018-12-20", "2020-07-08")))),
            }
        )
        samples = build_forecast_samples(frame, 7, "exclude")
        assigned = assign_partition(samples)
        validate_partitions(assigned)
        validate_sample_timestamps(assigned)
        boundary = assigned.loc[assigned.target_date.eq(pd.Timestamp("2019-01-01"))].iloc[0]
        self.assertEqual(boundary["partition"], "validation")
        self.assertEqual(boundary["origin_date"], pd.Timestamp("2018-12-25"))
        self.assertEqual(assigned.loc[assigned.partition.eq("test"), "target_date"].min(), pd.Timestamp("2020-01-01"))
        self.assertEqual(assigned.loc[assigned.partition.eq("test"), "target_date"].max(), pd.Timestamp("2020-07-01"))

    def test_expanding_folds_use_only_targets_through_training_cutoff(self):
        dates = pd.date_range("2015-01-01", "2020-07-01", freq="D")
        samples = pd.DataFrame({"target_date": dates, "City": "A"})
        folds = expanding_window_folds()
        self.assertEqual(
            [(fold["train_end"], fold["validation_start"], fold["validation_end"]) for fold in folds],
            [
                ("2016-12-31", "2017-01-01", "2017-12-31"),
                ("2017-12-31", "2018-01-01", "2018-12-31"),
                ("2018-12-31", "2019-01-01", "2019-12-31"),
            ],
        )
        for fold in folds:
            train, validation = split_fold(samples, fold)
            self.assertLessEqual(train.target_date.max(), pd.Timestamp(fold["train_end"]))
            self.assertGreaterEqual(validation.target_date.min(), pd.Timestamp(fold["validation_start"]))
            self.assertLessEqual(validation.target_date.max(), pd.Timestamp(fold["validation_end"]))
            self.assertEqual(train.target_date.isin(validation.target_date).sum(), 0)

    def test_primary_schema_rejects_pollutant_or_city_identifier(self):
        validate_feature_schema(PRIMARY_FEATURE_COLUMNS)
        with self.assertRaisesRegex(ValueError, "feature schema"):
            validate_feature_schema([*PRIMARY_FEATURE_COLUMNS, "PM2.5"])

    def test_city_folds_are_deterministic_and_disjoint(self):
        cities = ["A", "B", "C", "D", "E", "F", "G"]
        assignment = assign_city_folds(cities, n_folds=5, seed=19)
        self.assertEqual(assignment, assign_city_folds(cities, n_folds=5, seed=19))
        self.assertEqual(set(assignment), set(cities))
        self.assertEqual(set(assignment.values()), set(range(5)))
        self.assertEqual(len(assignment), len(cities))
        for fold in range(5):
            split = held_out_city_split(pd.DataFrame({"City": cities}), assignment, fold)
            self.assertFalse(set(split["held_out_cities"]) & set(split["training_cities"]))
            self.assertEqual(set(split["held_out_cities"]) | set(split["training_cities"]), set(cities))
        with self.assertRaisesRegex(ValueError, "not present"):
            held_out_city_split(pd.DataFrame({"City": cities}), assignment, 99)
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            held_out_city_split(pd.DataFrame({"City": cities}), {}, 0)
        with self.assertRaisesRegex(ValueError, "non-empty strings"):
            assign_city_folds(["A", ""], n_folds=2)

    def test_held_out_coverage_gate_uses_eligible_test_counts_only(self):
        assignment = {"A": 0, "B": 1}
        samples = pd.DataFrame(
            {
                "City": ["A"] * 31 + ["B"] * 40,
                "eligible": [True] * 30 + [False] + [True] * 40,
                "partition": ["test"] * 71,
            }
        )
        result = held_out_city_split(samples, assignment, 0, minimum_test_cases=30)
        self.assertEqual(result["included_in_macro_summary"], ["A"])
        self.assertEqual(result["test_case_counts"]["A"], 30)

    def test_partition_invariant_detects_cross_city_mismatch(self):
        samples = pd.DataFrame(
            {
                "City": ["A", "B"],
                "target_date": [pd.Timestamp("2019-01-01")] * 2,
                "partition": ["validation", "train"],
                "horizon_days": [1, 1],
                "policy": ["exclude", "exclude"],
            }
        )
        with self.assertRaisesRegex(AssertionError, "different partitions"):
            validate_partitions(samples)


if __name__ == "__main__":
    unittest.main()
