import pandas as pd
import unittest
import hashlib
from io import BytesIO
from pathlib import Path
import tempfile
from unittest.mock import patch

from research.aqi_forecasting.coverage import common_case_ids, coverage_summary
from research.aqi_forecasting.data_audit import audit_raw_dataset
from research.aqi_forecasting.manifest import build_manifest
from research.aqi_forecasting.forecast_samples import build_forecast_samples
from research.aqi_forecasting.temporal_splits import assign_partition


class AuditManifestTests(unittest.TestCase):
    def test_audit_counts_disjoint_aqi_categories_overall_and_by_partition(self):
        values = [-1, 0, 500, 501, float("nan"), float("-inf"), float("inf")]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "aqi_categories.csv"
            pd.DataFrame(
                {
                    "City": ["A"] * len(values),
                    "Date": pd.date_range("2020-01-01", periods=len(values)),
                    "AQI": values,
                }
            ).to_csv(path, index=False)
            audit = audit_raw_dataset(path)

        expected = {
            "missing": 1,
            "non_numeric": 0,
            "negative": 1,
            "valid_0_to_500": 2,
            "above_500": 1,
            "positive_infinity": 1,
            "negative_infinity": 1,
            "other_non_finite": 0,
        }
        self.assertEqual({key: audit["aqi"][key] for key in expected}, expected)
        partition = audit["target_counts_by_partition"]["test"]
        self.assertEqual({key: partition[key] for key in expected}, expected)
        self.assertEqual(sum(expected.values()), len(values))

    def test_audit_normalizes_daily_duplicates_and_reports_invalid_dates(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "daily_keys.csv"
            pd.DataFrame(
                {
                    "City": ["A", "A", "B", "A"],
                    "Date": [
                        "2020-01-01 00:00",
                        "2020-01-01 12:00",
                        "2020-01-01 00:00",
                        "not-a-date",
                    ],
                    "AQI": [10, 11, 20, 30],
                }
            ).to_csv(path, index=False)
            audit = audit_raw_dataset(path)
        self.assertEqual(audit["invalid_date_rows"], 1)
        self.assertEqual(audit["duplicate_city_date_excess"], 1)
        self.assertEqual(audit["duplicate_city_date_rows"], 2)
        self.assertEqual(
            audit["duplicate_city_day_keys"],
            [{"city": "A", "date": "2020-01-01", "row_count": 2}],
        )
        self.assertEqual(audit["city_coverage"]["B"]["unique_dates"], 1)

    def test_audit_hash_and_parse_use_one_byte_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "changing.csv"
            original = b"City,Date,AQI\nOriginal,2020-01-01,10\n"
            replacement = b"City,Date,AQI\nReplacement,2020-01-01,20\n"
            path.write_bytes(original)
            real_read_csv = pd.read_csv

            def replace_file_then_parse(snapshot, *args, **kwargs):
                self.assertIsInstance(snapshot, BytesIO)
                path.write_bytes(replacement)
                return real_read_csv(snapshot, *args, **kwargs)

            with patch(
                "research.aqi_forecasting.data_audit.pd.read_csv",
                side_effect=replace_file_then_parse,
            ):
                audit = audit_raw_dataset(path)

            self.assertEqual(audit["sha256"], hashlib.sha256(original).hexdigest())
            self.assertEqual(audit["file_size_bytes"], len(original))
            self.assertEqual(audit["city_labels"], ["Original"])
            self.assertNotEqual(audit["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_audit_fails_clearly_on_empty_and_malformed_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.csv"
            path.write_bytes(b"")
            with self.assertRaisesRegex(ValueError, "Could not parse raw CSV snapshot"):
                audit_raw_dataset(path)
            path.write_text('City,Date,AQI\n"A,2020-01-01,10\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Could not parse raw CSV snapshot"):
                audit_raw_dataset(path)

    def test_raw_audit_reports_file_identity_and_panel_gaps(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "city_day.csv"
            pd.DataFrame(
                {
                    "City": ["A", "A", "B"],
                    "Date": ["2020-01-01", "2020-01-03", "2020-01-01"],
                    "AQI": [10, 501, None],
                    "PM2.5": [1.0, None, 2.0],
                }
            ).to_csv(path, index=False)
            audit = audit_raw_dataset(path)
            self.assertEqual(audit["rows"], 3)
            self.assertEqual(audit["duplicate_city_date_excess"], 0)
            self.assertEqual(audit["city_coverage"]["A"]["missing_calendar_dates_within_observed_span"], 1)
            self.assertEqual(audit["aqi"]["above_500"], 1)
            self.assertEqual(audit["aqi"]["missing"], 1)
            self.assertEqual(len(audit["sha256"]), 64)
            self.assertEqual(audit["file_size_bytes"], path.stat().st_size)

    def test_coverage_common_cases_and_manifest_are_result_honest(self):
        frame = pd.DataFrame(
            {
                "City": ["A"] * 15,
                "Date": pd.date_range("2020-01-01", periods=15),
                "AQI": list(range(15, 30)),
            }
        )
        exclude = assign_partition(build_forecast_samples(frame, 1, "exclude"))
        cap = assign_partition(build_forecast_samples(frame, 1, "cap"))
        summary = coverage_summary(exclude)
        self.assertEqual(summary["eligible_forecasts"], len(exclude.loc[exclude["eligible"]]))
        self.assertEqual(
            common_case_ids(exclude, cap),
            set(exclude.loc[exclude["eligible"], "case_id"]),
        )
        audit = {
            "path": "data/raw/city_day.csv",
            "file_size_bytes": 123,
            "sha256": "a" * 64,
            "rows": 15,
            "date_min": "2020-01-01",
            "date_max": "2020-01-15",
            "city_labels": ["A"],
        }
        manifest = build_manifest(audit, policy="exclude", horizon_days=1, coverage=summary)
        self.assertFalse(manifest["model_trained"])
        self.assertIsNone(manifest["model_metrics"])
        self.assertEqual(manifest["target_policy"], "exclude")
        self.assertEqual(manifest["code_revision_status"], "not_checked")
        self.assertEqual(manifest["seeds"]["status"], "not_applicable")
        self.assertEqual(manifest["discrepancies"], {"status": "not_assessed", "items": None})
        self.assertIn("column_names", manifest["data"])

    def test_manifest_revision_seed_and_discrepancy_statuses_are_explicit(self):
        audit = {
            "path": "raw.csv",
            "file_size_bytes": 10,
            "sha256": "0" * 64,
            "rows": 1,
            "columns": 3,
            "column_names": ["City", "Date", "AQI"],
            "dtypes": {"City": "object", "Date": "object", "AQI": "int64"},
            "date_min": "2020-01-01",
            "date_max": "2020-01-01",
            "city_labels": ["A"],
            "city_count": 1,
            "invalid_date_rows": 0,
            "duplicate_city_date_excess": 0,
        }
        kwargs = {"policy": "exclude", "horizon_days": 1, "coverage": {}}
        unavailable = build_manifest(audit, revision_checked=True, **kwargs)
        self.assertEqual(unavailable["code_revision_status"], "unavailable")
        known = build_manifest(
            audit,
            code_revision="abc123",
            seeds={"city_fold": 42},
            discrepancies=[],
            **kwargs,
        )
        self.assertEqual(known["code_revision_status"], "known")
        self.assertEqual(known["seeds"], {"status": "recorded", "values": {"city_fold": 42}})
        self.assertEqual(known["discrepancies"], {"status": "assessed", "items": []})
        self.assertFalse(known["model_trained"])
        self.assertIsNone(known["model_metrics"])

    def test_coverage_summary_names_every_missing_required_column(self):
        frame = pd.DataFrame(
            {
                "City": ["A"],
                "eligible": [True],
                "target_valid": [True],
                "target_status": ["valid"],
                "exclusion_reasons": [()],
                "partition": ["train"],
                "target_date": [pd.Timestamp("2018-01-01")],
                "horizon_days": [1],
                "policy": ["exclude"],
            }
        )
        required_columns = (
            "City",
            "eligible",
            "target_valid",
            "target_status",
            "exclusion_reasons",
            "partition",
            "target_date",
            "horizon_days",
            "policy",
        )
        for column in required_columns:
            with self.subTest(column=column):
                with self.assertRaisesRegex(ValueError, column):
                    coverage_summary(frame.drop(columns=column))
        with self.assertRaisesRegex(ValueError, "boolean values"):
            coverage_summary(frame.assign(target_valid=["yes"]))

    def test_common_case_frames_reject_duplicate_ids_and_horizon_mismatch(self):
        frame = pd.DataFrame(
            {
                "eligible": [True, True],
                "case_id": ["A|2020-01-01|h1", "A|2020-01-01|h1"],
                "City": ["A", "A"],
                "target_date": pd.to_datetime(["2020-01-01", "2020-01-01"]),
                "horizon_days": [1, 1],
                "policy": ["exclude", "exclude"],
            }
        )
        with self.assertRaisesRegex(ValueError, "must be unique"):
            common_case_ids(frame)
        distinct = frame.drop_duplicates("case_id").copy()
        other_horizon = distinct.assign(
            case_id="A|2020-01-01|h3",
            horizon_days=3,
        )
        with self.assertRaisesRegex(ValueError, "same horizon"):
            common_case_ids(distinct, other_horizon)


if __name__ == "__main__":
    unittest.main()
