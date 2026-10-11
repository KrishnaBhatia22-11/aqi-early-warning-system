import math
import unittest

import pandas as pd

from research.aqi_forecasting.forecast_samples import build_forecast_samples
from research.aqi_forecasting.leakage_checks import validate_sample_timestamps


def _fixture():
    dates = pd.date_range("2020-01-01", periods=20, freq="D")
    return pd.DataFrame(
        {
            "City": ["A"] * len(dates) + ["B"] * len(dates),
            "Date": list(dates) * 2,
            "AQI": list(range(10, 30)) + list(range(110, 130)),
            "PM2.5": [999.0] * (2 * len(dates)),
            "AQI_Bucket": ["leak"] * (2 * len(dates)),
        }
    )


class ForecastSampleTests(unittest.TestCase):
    def test_exact_target_origin_and_lags(self):
        for horizon in (1, 3, 7):
            with self.subTest(horizon=horizon):
                samples = build_forecast_samples(_fixture(), horizon, "exclude")
                row = samples.loc[
                    (samples["City"] == "A")
                    & (samples["target_date"] == pd.Timestamp("2020-01-20"))
                ].iloc[0]
                self.assertEqual(
                    row["origin_date"],
                    pd.Timestamp("2020-01-20") - pd.Timedelta(days=horizon),
                )
                self.assertEqual(row["target_raw"], 29)
                self.assertEqual(row["aqi_lag_origin"], 10 + (19 - horizon))
                self.assertEqual(row["aqi_lag_1d"], 10 + (18 - horizon))
                self.assertEqual(row["aqi_lag_7d"], 10 + (12 - horizon))
                self.assertTrue(row["eligible"])
                validate_sample_timestamps(samples)

    def test_missing_calendar_date_is_not_replaced_by_previous_row(self):
        source = _fixture()
        source = source.loc[~((source.City == "A") & (source.Date == "2020-01-10"))]
        samples = build_forecast_samples(source, 1, "exclude")
        row = samples.loc[
            (samples.City == "A") & (samples.target_date == pd.Timestamp("2020-01-12"))
        ].iloc[0]
        self.assertFalse(row["eligible"])
        self.assertIn("missing_one_day_lag", row["exclusion_reasons"])
        self.assertTrue(pd.isna(row["aqi_lag_1d"]))

    def test_missing_target_and_above_500_policy_are_auditable(self):
        source = _fixture()
        source.loc[(source.City == "A") & (source.Date == "2020-01-20"), "AQI"] = 700
        source.loc[(source.City == "B") & (source.Date == "2020-01-20"), "AQI"] = None
        excluded = build_forecast_samples(source, 1, "exclude")
        capped = build_forecast_samples(source, 1, "cap")
        a_ex = excluded.loc[(excluded.City == "A") & excluded.target_date.eq(pd.Timestamp("2020-01-20"))].iloc[0]
        a_cap = capped.loc[(capped.City == "A") & capped.target_date.eq(pd.Timestamp("2020-01-20"))].iloc[0]
        b = capped.loc[(capped.City == "B") & capped.target_date.eq(pd.Timestamp("2020-01-20"))].iloc[0]
        self.assertFalse(a_ex["eligible"])
        self.assertEqual(a_ex["target_status"], "above_500")
        self.assertTrue(a_cap["eligible"])
        self.assertEqual(a_cap["target"], 500)
        self.assertEqual(a_cap["target_raw"], 700)
        self.assertFalse(b["eligible"])
        self.assertIn("missing_target", b["exclusion_reasons"])

    def test_target_date_calendar_features_are_deterministic(self):
        frame = _fixture()
        first = build_forecast_samples(frame, 1, "exclude")
        second = build_forecast_samples(frame, 1, "exclude")
        row = first.loc[first.target_date.eq(pd.Timestamp("2020-01-06"))].iloc[0]
        self.assertAlmostEqual(row["target_month_sin"], 0.0, delta=1e-12)
        self.assertAlmostEqual(row["target_month_cos"], 1.0)
        self.assertAlmostEqual(row["target_weekday_sin"], math.sin(2 * math.pi * 0 / 7))
        self.assertTrue(
            first[["case_id", *first.attrs["feature_columns"]]].equals(
                second[["case_id", *second.attrs["feature_columns"]]]
            )
        )

    def test_duplicate_city_date_and_invalid_date_are_rejected(self):
        source = _fixture()
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            build_forecast_samples(pd.concat([source, source.iloc[[0]]]), 1, "exclude")
        source["Date"] = source["Date"].astype(object)
        source.loc[0, "Date"] = "not-a-date"
        with self.assertRaisesRegex(ValueError, "invalid dates"):
            build_forecast_samples(source, 1, "exclude")

    def test_mixed_date_formats_parse_deterministically_and_timezone_is_rejected(self):
        source = pd.DataFrame(
            {
                "City": ["A", "A"],
                "Date": ["2020-01-01", "2020-01-02 12:30:00"],
                "AQI": [10, 11],
            }
        )
        samples = build_forecast_samples(source, 1, "exclude")
        self.assertEqual(
            samples["target_date"].tolist(),
            [pd.Timestamp("2020-01-01"), pd.Timestamp("2020-01-02")],
        )
        source.loc[0, "Date"] = "2020-01-01T00:00:00+05:30"
        with self.assertRaisesRegex(ValueError, "timezone-naive"):
            build_forecast_samples(source, 1, "exclude")

    def test_timestamp_validator_checks_every_lag_and_does_not_mutate(self):
        samples = build_forecast_samples(_fixture(), 3, "exclude")
        baseline = samples.copy(deep=True)
        validate_sample_timestamps(samples)
        self.assertTrue(samples.equals(baseline))

        future_lag = samples.copy(deep=True)
        future_lag.loc[0, "aqi_lag_1d_date"] = future_lag.loc[0, "origin_date"] + pd.Timedelta(days=1)
        with self.assertRaisesRegex(AssertionError, "required offset"):
            validate_sample_timestamps(future_lag)

        wrong_offset = samples.copy(deep=True)
        wrong_offset.loc[0, "aqi_lag_7d_date"] -= pd.Timedelta(days=1)
        with self.assertRaisesRegex(AssertionError, "required offset"):
            validate_sample_timestamps(wrong_offset)

        stale_max = samples.copy(deep=True)
        stale_max.loc[0, "aqi_lag_1d_date"] = stale_max.loc[0, "origin_date"] + pd.Timedelta(days=1)
        with self.assertRaisesRegex(AssertionError, "required offset"):
            validate_sample_timestamps(stale_max)

        missing_lag_date = samples.copy(deep=True)
        missing_lag_date.loc[0, "aqi_origin_date"] = pd.NaT
        with self.assertRaisesRegex(ValueError, "must be valid"):
            validate_sample_timestamps(missing_lag_date)

    def test_city_values_never_cross_join(self):
        samples = build_forecast_samples(_fixture(), 1, "exclude")
        row_a = samples.loc[(samples.City == "A") & samples.target_date.eq(pd.Timestamp("2020-01-20"))].iloc[0]
        row_b = samples.loc[(samples.City == "B") & samples.target_date.eq(pd.Timestamp("2020-01-20"))].iloc[0]
        self.assertEqual(row_b["aqi_lag_origin"] - row_a["aqi_lag_origin"], 100)


if __name__ == "__main__":
    unittest.main()
