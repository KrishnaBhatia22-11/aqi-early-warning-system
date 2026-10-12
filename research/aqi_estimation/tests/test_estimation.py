import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from research.aqi_estimation import cpcb_formula as cf
from research.aqi_estimation import metrics as mt
from research.aqi_estimation import run_estimation as re_


class FormulaTests(unittest.TestCase):
    def test_known_sub_indices(self):
        self.assertAlmostEqual(cf.sub_index("PM2.5", [45.0])[0], 75.5)
        self.assertEqual(cf.sub_index("PM10", [0.0])[0], 0.0)
        self.assertEqual(cf.sub_index("PM2.5", [1000.0])[0], 500.0)
        self.assertAlmostEqual(cf.sub_index("CO", [1.5])[0], 75.5)
        self.assertTrue(np.isnan(cf.sub_index("NO2", [np.nan, -1.0])).all())

    def test_computability_rule(self):
        frame = pd.DataFrame({p: [np.nan] * 3 for p in cf.FORMULA_POLLUTANTS})
        frame.loc[0, ["PM2.5", "NO2", "SO2"]] = [100, 50, 10]   # ok
        frame.loc[1, ["NO2", "SO2", "CO"]] = [50, 10, 1]        # no particulate
        frame.loc[2, ["PM10", "NO2"]] = [100, 50]               # only 2 pollutants
        out = cf.compute_aqi(frame)
        self.assertEqual(out["computable"].tolist(), [True, False, False])
        self.assertTrue(np.isnan(out.loc[1, "formula_aqi"]))
        self.assertEqual(out.loc[0, "dominant"], "PM2.5")

    def test_max_of_sub_indices(self):
        frame = pd.DataFrame([{**{p: np.nan for p in cf.FORMULA_POLLUTANTS},
                               "PM2.5": 45.0, "PM10": 300.0, "NO2": 10.0}])
        out = cf.compute_aqi(frame)
        self.assertEqual(out.loc[0, "dominant"], "PM10")
        self.assertAlmostEqual(out.loc[0, "formula_aqi"], 201 + (300 - 250) / 100 * 99)


class MetricTests(unittest.TestCase):
    def test_category_boundaries(self):
        self.assertEqual(mt.categorize([0, 50, 50.5, 100, 200, 300, 400, 401, 600]).tolist(),
                         [0, 0, 1, 1, 2, 3, 4, 5, 5])

    def test_event_scores(self):
        s = mt.event_scores([250, 250, 100, 100], [250, 100, 250, 100], 200)
        self.assertEqual((s["hits"], s["misses"], s["false_alarms"]), (1, 1, 1))
        self.assertAlmostEqual(s["POD"], 0.5)
        self.assertAlmostEqual(s["FAR"], 0.5)
        self.assertAlmostEqual(s["CSI"], 1 / 3)

    def test_bootstrap_deterministic_and_brackets(self):
        rng = np.random.default_rng(0)
        cities = np.repeat(list("abcdef"), 50)
        y = rng.uniform(0, 400, 300)
        preds = {"m": y + rng.normal(0, 20, 300)}
        a = mt.cluster_bootstrap(cities, y, preds, reps=300, seed=1)
        b = mt.cluster_bootstrap(cities, y, preds, reps=300, seed=1)
        pd.testing.assert_frame_equal(a, b)
        mae = a[a.metric == "MAE"].iloc[0]
        self.assertLess(mae.ci_low, mae.estimate)
        self.assertGreater(mae.ci_high, mae.estimate)
        self.assertAlmostEqual(mae.estimate, mt.regression_metrics(y, preds["m"])["MAE"])


class PipelineTests(unittest.TestCase):
    def _synthetic(self, path: Path):
        rng = np.random.default_rng(3)
        rows = []
        for city in ["A", "B", "C"]:
            for d in pd.date_range("2015-01-01", "2020-07-01", freq="3D"):
                pm25 = rng.uniform(10, 300)
                rows.append({"City": city, "Date": d.date(), "PM2.5": pm25, "PM10": pm25 * 1.5,
                             "NO": rng.uniform(1, 50), "NO2": rng.uniform(5, 80), "NOx": rng.uniform(5, 90),
                             "NH3": rng.uniform(5, 40), "CO": rng.uniform(0.2, 3), "SO2": rng.uniform(2, 30),
                             "O3": rng.uniform(10, 90), "AQI": min(500, pm25 * 1.6)})
        pd.DataFrame(rows).to_csv(path, index=False)

    def test_end_to_end_and_ledger_blocks_second_scoring(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            self._synthetic(tmp / "city_day.csv")
            cfg = re_.Config(dataset=tmp / "city_day.csv", out_root=tmp / "results", ledger=tmp / "ledger.jsonl",
                             grid={"max_depth": [2, 3], "n_estimators": [20], "learning_rate": [0.1]},
                             reps=50, run_reference=False)
            out = re_.run(cfg)
            record = json.loads((out / "run_record.json").read_text())
            self.assertEqual(record["dataset"]["sha256"], re_.sha256_file(tmp / "city_day.csv"))
            for rel, digest in record["output_file_sha256"].items():
                self.assertEqual(digest, re_.sha256_file(out / rel), rel)
            events = [e["event"] for e in record["scoring_events"]]
            self.assertEqual(events.count("test_scoring_started"), 1)
            self.assertLess(events.index("development_frozen"), events.index("test_scoring_started"))
            preds = pd.read_csv(out / "tables" / "test_predictions_2020.csv", parse_dates=["Date"])
            self.assertTrue((preds["Date"] >= "2020-01-01").all())
            with self.assertRaises(RuntimeError):
                re_.run(cfg)

    def test_development_never_sees_test_rows(self):
        w = re_.Windows()
        df = pd.DataFrame({"Date": pd.to_datetime(["2018-12-31", "2019-12-31", "2020-01-01"])})
        self.assertEqual(len(re_.window(df, w.train_start, w.val_end)), 2)


if __name__ == "__main__":
    unittest.main()
