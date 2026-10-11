import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

from research.aqi_forecasting.manifest import (
    build_development_manifest,
    fingerprint_research_sources,
)
from research.aqi_forecasting.run_development import (
    _RUN_MODULE,
    _format_command,
    persist_run_record,
    run_development,
)


class RunRecordTests(unittest.TestCase):
    def _record_inputs(self, root):
        data_audit = {
            "path": "data/raw/synthetic.csv",
            "file_size_bytes": 100,
            "sha256": "0d84b21c3e4878bbad8df362f2ab05f61ad959538dddf5918e714077ed3c1847",
            "rows": 10,
            "columns": 3,
            "column_names": ["City", "Date", "AQI"],
            "dtypes": {"City": "object", "Date": "object", "AQI": "float64"},
            "date_min": "2015-01-01",
            "date_max": "2020-07-01",
            "unique_dates": 10,
            "city_labels": ["A"],
            "city_count": 1,
            "invalid_date_rows": 0,
            "duplicate_city_date_excess": 0,
        }
        run = {
            "policy": "exclude",
            "horizon_days": 1,
            "case_counts_by_partition": {
                "train": {
                    "cases": 8,
                    "valid_targets": 7,
                    "eligible_forecasts": 6,
                },
                "validation": {
                    "cases": 1,
                    "valid_targets": 1,
                    "eligible_forecasts": 1,
                },
                "test": {
                    "cases": 1,
                    "valid_targets": 1,
                    "eligible_forecasts": 1,
                },
            },
            "sample_coverage": {
                "by_partition": {
                    "train": {"valid_targets": 7, "eligible_forecasts": 6},
                    "validation": {"valid_targets": 1, "eligible_forecasts": 1},
                },
                "exclusion_reason_counts": {"missing_target": 1},
            },
            "ridge_selection": {
                "selected_alpha": 1.0,
                "selection_rule": (
                    "Minimize equal-weight mean MAE across fold_2017, fold_2018, "
                    "and fold_2019; exact ties choose the larger alpha."
                ),
                "fold_scores": [
                    {"alpha": alpha, "fold": "fold_2017", "validation_cases": 2, "mae": 3.0}
                    for alpha in (0.1, 1.0, 10.0)
                ],
            },
            "validation": {
                "policy": "exclude",
                "horizon_days": 1,
                "partition": "validation",
                "common_case_count": 1,
                "methods": {
                    "persistence": {
                        "predicted_valid_target_cases": 1,
                        "coverage": 1.0,
                        "metrics": {"pooled": {"count": 1, "mae": 2.0}},
                    }
                },
            },
        }
        return data_audit, [run]

    def test_source_fingerprint_is_deterministic_and_excludes_run_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "research" / "aqi_forecasting" / "unit.py"
            output = root / "research" / "aqi_forecasting" / "results" / "run.json"
            cache = root / "research" / "aqi_forecasting" / "__pycache__" / "x.py"
            source.parent.mkdir(parents=True)
            source.write_text("VALUE = 1\n", encoding="utf-8")
            output.parent.mkdir()
            output.write_text("first output", encoding="utf-8")
            cache.parent.mkdir()
            cache.write_text("cache", encoding="utf-8")

            first = fingerprint_research_sources(root)
            second = fingerprint_research_sources(root)
            self.assertEqual(first, second)
            self.assertEqual(first["files"], ["research/aqi_forecasting/unit.py"])

            output.write_text("changed output", encoding="utf-8")
            self.assertEqual(first, fingerprint_research_sources(root))
            source.write_text("VALUE = 2\n", encoding="utf-8")
            self.assertNotEqual(first["sha256"], fingerprint_research_sources(root)["sha256"])

    def test_development_manifest_records_protocol_outputs_and_safe_status(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "runtime.txt").write_text("python-3.11\n", encoding="utf-8")
            (root / "research").mkdir()
            data_audit, runs = self._record_inputs(root)
            record = build_development_manifest(
                data_audit,
                runs,
                repository_root=root,
                run_id="synthetic-run",
                run_command="python -m synthetic",
                started_at_utc="2026-10-10T00:00:00+00:00",
                completed_at_utc="2026-10-10T00:00:01+00:00",
            )

        self.assertEqual(record["data"]["sha256"], "0d84b21c3e4878bbad8df362f2ab05f61ad959538dddf5918e714077ed3c1847")
        self.assertEqual(record["protocol"]["horizons_days"], [1, 3, 7])
        self.assertEqual(record["protocol"]["ridge_alpha_candidates"], [0.1, 1.0, 10.0])
        self.assertEqual(record["protocol"]["train_target_dates"], ["2015-01-01", "2018-12-31"])
        self.assertEqual(record["protocol"]["validation_and_selection_target_dates"], ["2019-01-01", "2019-12-31"])
        self.assertTrue(record["final_test_outcomes_used_for_selection"] is False)
        self.assertTrue(record["final_test_predictions_generated"] is False)
        self.assertTrue(record["final_test_scoring_performed"] is False)
        self.assertEqual(record["runs"][0]["ridge_selection"]["selected_alpha"], 1.0)
        self.assertEqual(
            record["runs"][0]["sample_coverage"]["exclusion_reason_counts"],
            {"missing_target": 1},
        )
        self.assertEqual(record["runs"][0]["validation"]["common_case_count"], 1)
        self.assertEqual(record["data_provenance"]["verified_artifact_version"], 12)
        self.assertEqual(record["data_provenance"]["upstream_cpcb_lineage_and_rights"], "unresolved")
        self.assertEqual(record["environment"]["declared_python_runtime"], "python-3.11")
        self.assertEqual(record["reproducibility_notes"]["historical_metrics"], "Not carried forward; no trusted saved run artifact was available.")
        self.assertEqual(
            [author["name"] for author in record["authors"]],
            ["Poonam Tanwar", "Krishna Bhatia", "Prateek Singh", "Snehaal Mukherjee"],
        )
        for author in record["authors"]:
            self.assertEqual(author["email"], "[to be confirmed]")
            self.assertEqual(author["affiliation"], "[to be confirmed]")
            self.assertEqual(author["academic_title"], "[to be confirmed]")
            self.assertEqual(author["orcid"], "[to be confirmed]")

    def test_manifest_does_not_transfer_kaggle_provenance_to_other_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "research").mkdir()
            data_audit, runs = self._record_inputs(root)
            data_audit["sha256"] = "b" * 64
            record = build_development_manifest(
                data_audit,
                runs,
                repository_root=root,
                run_id="other-input",
                run_command="python -m synthetic",
                started_at_utc="start",
                completed_at_utc="end",
            )
        self.assertIsNone(record["data_provenance"]["verified_artifact_version"])
        self.assertFalse(record["data_provenance"]["local_file_byte_match_verified"])

    def test_record_and_log_are_written_once_and_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            record = {
                "run_id": "synthetic-run",
                "stage": "synthetic",
                "status": "completed",
                "started_at_utc": "start",
                "completed_at_utc": "end",
                "run_command": "synthetic command",
                "final_test_scoring_performed": False,
                "runs": [],
            }
            record_path, log_path = persist_run_record(
                record,
                directory,
                stdout="synthetic stdout",
                stderr="synthetic stderr",
            )
            original_json = record_path.read_bytes()
            original_log = log_path.read_bytes()
            parsed = json.loads(original_json)
            self.assertEqual(parsed["artifacts"]["record_json"], str(record_path.resolve()))
            self.assertIn(b"synthetic stdout", original_log)
            self.assertIn(b"synthetic stderr", original_log)

            with self.assertRaises(FileExistsError):
                persist_run_record(record, directory, stdout="replacement")
            self.assertEqual(record_path.read_bytes(), original_json)
            self.assertEqual(log_path.read_bytes(), original_log)

            incomplete = {**record, "run_id": "incomplete-run", "status": "running"}
            with self.assertRaisesRegex(ValueError, "Only completed"):
                persist_run_record(incomplete, directory)

    def test_persistence_rejects_path_like_run_identifiers(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "safe"):
                persist_run_record({"run_id": "../escape"}, directory)

    def test_default_run_command_uses_importable_module_path(self):
        command = _format_command(["python", "-m", _RUN_MODULE])
        self.assertEqual(
            command,
            "python -m research.aqi_forecasting.run_development",
        )

    def test_development_runner_hands_only_pre_2020_history_to_baselines(self):
        raw_path = Path("synthetic-city-day.csv")
        full_history = pd.DataFrame(
            {
                "City": ["A", "A"],
                "Date": ["2019-12-31", "2020-01-01"],
                "AQI": [42.0, 999.0],
            }
        )
        sample_calls = []
        baseline_history_calls = []

        def build_samples(history, horizon, policy):
            sample_calls.append(history.copy())
            return pd.DataFrame(
                {
                    "target_date": [pd.Timestamp("2019-12-31")],
                    "target_valid": [True],
                    "eligible": [True],
                    "partition": ["validation"],
                }
            )

        def run_baselines(samples, history):
            baseline_history_calls.append(history.copy())
            return {"ridge_selection": {"selection_rule": "synthetic"}}

        with (
            patch(
                "research.aqi_forecasting.run_development.audit_raw_dataset",
                return_value={"sha256": "synthetic", "rows": 2},
            ) as audit,
            patch(
                "research.aqi_forecasting.run_development.pd.read_csv",
                return_value=full_history,
            ) as read_csv,
            patch(
                "research.aqi_forecasting.run_development.build_forecast_samples",
                side_effect=build_samples,
            ),
            patch(
                "research.aqi_forecasting.run_development.assign_partition",
                side_effect=lambda samples: samples,
            ),
            patch(
                "research.aqi_forecasting.run_development.run_policy_horizon_development",
                side_effect=run_baselines,
            ),
            patch(
                "research.aqi_forecasting.run_development.coverage_summary",
                return_value={},
            ),
            patch(
                "research.aqi_forecasting.run_development.build_development_manifest",
                return_value={},
            ),
        ):
            run_development(raw_path, run_id="synthetic")

        audit.assert_called_once_with(raw_path)
        read_csv.assert_called_once_with(raw_path)
        self.assertEqual(len(sample_calls), 6)
        self.assertEqual(len(baseline_history_calls), 6)
        for history in sample_calls + baseline_history_calls:
            dates = pd.to_datetime(history["Date"])
            self.assertTrue(dates.le(pd.Timestamp("2019-12-31")).all())
            self.assertFalse(dates.ge(pd.Timestamp("2020-01-01")).any())


if __name__ == "__main__":
    unittest.main()
