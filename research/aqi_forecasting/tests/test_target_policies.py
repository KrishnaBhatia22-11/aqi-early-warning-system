import pandas as pd
import unittest

from research.aqi_forecasting.target_policies import apply_target_policy


class TargetPolicyTests(unittest.TestCase):
    def test_target_policy_boundaries_and_raw_preservation(self):
        cases = [
            ("exclude", [0, 500, -1, 501, None], [0, 500, None, None, None],
             [True, True, False, False, False], ["valid", "valid", "negative", "above_500", "missing"]),
            ("cap", [0, 500, -1, 501, None], [0, 500, None, 500, None],
             [True, True, False, True, False], ["valid", "valid", "negative", "above_500", "missing"]),
        ]
        for policy, values, expected_values, expected_valid, expected_status in cases:
            with self.subTest(policy=policy):
                source = pd.DataFrame({"AQI": values, "other": list("abcde")})
                original = source.copy(deep=True)
                result, metadata = apply_target_policy(source, policy)
                self.assertTrue(source.equals(original))
                self.assertEqual(result["aqi_raw"].tolist()[:4], values[:4])
                for actual, expected in zip(result["aqi_value"], expected_values):
                    if expected is None:
                        self.assertTrue(pd.isna(actual))
                    else:
                        self.assertEqual(actual, expected)
                self.assertEqual(result["aqi_valid"].tolist(), expected_valid)
                self.assertEqual(result["aqi_status"].tolist(), expected_status)
                self.assertEqual(metadata["policy"], policy)
                self.assertEqual(metadata["above_500_capped"], 1 if policy == "cap" else 0)
                self.assertEqual(metadata["above_500_excluded"], 1 if policy == "exclude" else 0)

    def test_policy_flags_non_numeric_and_infinite_values(self):
        result, metadata = apply_target_policy(
            pd.DataFrame({"AQI": ["bad", float("inf")]}), "exclude"
        )
        self.assertEqual(result["aqi_status"].tolist(), ["non_numeric", "non_finite"])
        self.assertEqual(result["aqi_valid"].tolist(), [False, False])
        self.assertEqual(metadata["valid_targets_or_lags"], 0)

    def test_unknown_policy_and_missing_column_are_explicit_errors(self):
        with self.assertRaisesRegex(ValueError, "Unknown target policy"):
            apply_target_policy(pd.DataFrame({"AQI": [1]}), "silent_clip")
        with self.assertRaisesRegex(KeyError, "source column"):
            apply_target_policy(pd.DataFrame({"value": [1]}), "exclude")


if __name__ == "__main__":
    unittest.main()
