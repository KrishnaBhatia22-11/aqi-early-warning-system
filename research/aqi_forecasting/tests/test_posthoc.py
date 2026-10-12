import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import numpy as np
import pandas as pd

from research.aqi_forecasting.posthoc import run_posthoc as ph


def _pred_frame(maes: float = 0.0) -> pd.DataFrame:
    """Two common cases for one policy/horizon/model; |y_pred - y_true| averages `maes`."""
    return pd.DataFrame({
        "city": ["A", "B"], "origin_date": ["2020-01-01"] * 2, "target_date": ["2020-01-02"] * 2,
        "horizon": [1, 1], "model": ["persistence"] * 2, "policy": ["exclude"] * 2,
        "y_true": [100.0, 200.0], "y_pred": [100.0 + maes, 200.0 + maes], "in_common_case": [True, True],
        "prediction_available": [True, True], "target_valid": [True, True],
        "case_id": ["a", "b"], "partition": ["test", "test"]})


def _frozen_dir(root: Path, mae: float) -> Path:
    frozen = root / "frozen"
    (frozen / "tables").mkdir(parents=True)
    (frozen / "run_record.json").write_text(json.dumps({"environment": {}, "test_runs": []}), encoding="utf-8")
    pd.DataFrame([{"policy": "exclude", "horizon_days": 1, "method": "persistence",
                   "common_case_count": 2, "mae": mae}]).to_csv(frozen / "tables" / "test_common_case_with_ci.csv", index=False)
    return frozen


class WarningCellTests(unittest.TestCase):
    def test_hand_computed_case(self):
        cell = ph.warning_cell([250, 250, 100, 100, 350], [250, 100, 250, 100, 350], 200)
        self.assertEqual((cell["hits"], cell["misses"], cell["false_alarms"], cell["correct_negatives"]), (2, 1, 1, 1))
        self.assertEqual(cell["events"], 3)
        self.assertAlmostEqual(cell["POD"], 2 / 3)
        self.assertAlmostEqual(cell["FAR"], 1 / 3)
        self.assertAlmostEqual(cell["CSI"], 2 / 4)
        self.assertAlmostEqual(cell["event_base_rate"], 3 / 5)
        self.assertEqual(cell["flag"], "LOW-EVENT-COUNT")

    def test_zero_events(self):
        cell = ph.warning_cell([100, 100], [250, 100], 200)
        self.assertEqual(cell["events"], 0)
        self.assertTrue(math.isnan(cell["POD"]))
        self.assertAlmostEqual(cell["FAR"], 1.0)
        self.assertAlmostEqual(cell["CSI"], 0.0)

    def test_zero_warnings(self):
        cell = ph.warning_cell([250, 100], [100, 100], 200)
        self.assertEqual(cell["warnings_issued"], 0)
        self.assertAlmostEqual(cell["POD"], 0.0)
        self.assertTrue(math.isnan(cell["FAR"]))
        self.assertAlmostEqual(cell["CSI"], 0.0)

    def test_no_events_no_warnings_is_undefined(self):
        cell = ph.warning_cell([100, 100], [100, 100], 200)
        self.assertTrue(math.isnan(cell["CSI"]))

    def test_event_boundary_is_strict(self):
        cell = ph.warning_cell([200, 201], [200, 201], 200)
        self.assertEqual(cell["events"], 1)


class ZoneAndBootstrapTests(unittest.TestCase):
    def test_zone_boundaries(self):
        self.assertEqual([ph.zone_of(v) for v in (0.30, 0.2999, 0.10, 0.0999, 0.0)],
                         ["high", "medium", "medium", "low", "low"])

    def test_weights_follow_frozen_resampling_scheme(self):
        cities = ["a", "b", "c", "d"]
        weights = ph.city_cluster_weights(cities, 50, 20200101)
        rng = np.random.default_rng(20200101)
        draws = rng.integers(0, 4, size=(50, 4))
        expected = np.stack([np.bincount(row, minlength=4) for row in draws]).astype(float)
        np.testing.assert_array_equal(weights, expected)
        self.assertTrue((weights.sum(axis=1) == 4).all())

    def test_perfect_forecaster_has_csi_one(self):
        rows = []
        for city in "ABCDE":
            for y in (250.0, 100.0, 320.0):
                for model in ph.MODEL_ORDER[:1] + ["regularized_linear", "xgboost"]:
                    rows.append({"city": city, "y_true": y, "y_pred": y, "model": model,
                                 "policy": "exclude", "horizon": 1})
        ci, diff = ph.csi_bootstrap(pd.DataFrame(rows), replicates=100)
        self.assertTrue((ci["csi"] == 1.0).all())
        self.assertTrue((ci["ci_lower"] == 1.0).all() and (ci["ci_upper"] == 1.0).all())
        self.assertTrue((diff["csi_difference"] == 0.0).all())

    def test_zone_agreement_table(self):
        rows = []
        for city, share_obs, share_fc in (("A", 4, 4), ("B", 1, 0), ("C", 0, 0)):
            for i in range(10):
                rows.append({"city": city, "y_true": 250.0 if i < share_obs else 100.0,
                             "y_pred": 250.0 if i < share_fc else 100.0,
                             "model": "xgboost", "policy": "exclude", "horizon": 1})
        summary, per_city = ph.zone_tables(pd.DataFrame(rows))
        self.assertEqual(per_city.set_index("city").loc["A", "observed_zone"], "high")
        self.assertEqual(per_city.set_index("city").loc["B", "forecast_zone"], "low")
        self.assertAlmostEqual(summary.loc[0, "exact_zone_agreement"], 2 / 3)


class SafetyTests(unittest.TestCase):
    def test_refuses_to_write_inside_frozen_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            frozen = Path(tmp) / "frozen"
            frozen.mkdir()
            for target in (frozen, frozen / "tables", frozen / "new_dir"):
                with self.assertRaises(PermissionError):
                    ph.ensure_outside_frozen(target, frozen)
            with self.assertRaises(PermissionError):
                ph.run_posthoc(frozen_dir=frozen, out_dir=frozen / "sub")
            self.assertEqual(list(frozen.iterdir()), [])
            self.assertEqual(ph.ensure_outside_frozen(Path(tmp) / "frozen_posthoc", frozen), (Path(tmp) / "frozen_posthoc").resolve())

    def test_real_frozen_directory_is_protected(self):
        frozen = ph.RESULTS_ROOT / ph.FROZEN_RUN_ID
        with self.assertRaises(PermissionError):
            ph.ensure_outside_frozen(frozen / "tables" / "x.csv", frozen)

    def test_gate_failure_writes_only_gate_failed_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            frozen = _frozen_dir(tmp, mae=0.0)
            dataset = tmp / "data.csv"
            dataset.write_text("City,Date\nA,2020-01-01\n", encoding="utf-8")
            out = tmp / "out"
            source = lambda history, record: (_pred_frame(maes=5.0), [])  # MAE 5 != frozen 0
            with self.assertRaises(ph.GateFailed):
                ph.run_posthoc(frozen_dir=frozen, out_dir=out, dataset=dataset, do_preflight=False,
                               prediction_source=source)
            self.assertEqual([p.name for p in out.iterdir()], ["GATE_FAILED.md"])
            self.assertIn("GATE FAILED", (out / "GATE_FAILED.md").read_text(encoding="utf-8"))

    def test_gate_passes_when_numbers_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            frozen = _frozen_dir(Path(tmp), mae=0.0)
            comparison = ph.run_gate(_pred_frame(0.0), frozen / "tables" / "test_common_case_with_ci.csv", Path(tmp) / "o")
            self.assertTrue(comparison["summary"]["passed"])
            self.assertFalse((Path(tmp) / "o").exists())

    def test_gate_catches_count_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            frozen = _frozen_dir(Path(tmp), mae=0.0)
            pred = _pred_frame(0.0).iloc[:1]
            with self.assertRaises(ph.GateFailed):
                ph.run_gate(pred, frozen / "tables" / "test_common_case_with_ci.csv", Path(tmp) / "o")

    def test_main_returns_nonzero_on_gate_failure(self):
        with mock.patch.object(ph, "run_posthoc", side_effect=ph.GateFailed("boom")):
            self.assertEqual(ph.main([]), 1)

    def test_main_returns_nonzero_on_preflight_failure(self):
        with mock.patch.object(ph, "run_posthoc", side_effect=ph.PreflightError("bad env")):
            self.assertEqual(ph.main([]), 1)


if __name__ == "__main__":
    unittest.main()
