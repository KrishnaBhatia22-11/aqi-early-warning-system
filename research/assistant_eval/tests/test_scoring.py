import unittest

from research.assistant_eval import scoring as sc


class ValueTests(unittest.TestCase):
    def test_tolerance_is_inclusive_plus_minus_five(self):
        self.assertTrue(sc.value_within(81, 76))
        self.assertTrue(sc.value_within(71, 76))
        self.assertFalse(sc.value_within(82, 76))
        self.assertFalse(sc.value_within(70, 76))

    def test_value_correct_reads_aqi_numbers(self):
        self.assertEqual(sc.value_correct("The current AQI in Delhi is 76 (Satisfactory).", 76), 1)
        self.assertEqual(sc.value_correct("Delhi's AQI is **78**.", 76), 1)
        self.assertEqual(sc.value_correct("Delhi's AQI is 120.", 76), 0)
        self.assertEqual(sc.value_correct("I do not have that value.", 76), 0)

    def test_dates_and_times_are_not_aqi_values(self):
        text = "Stored reading from 2026-09-27 at 19:14 UTC; Delhi AQI 76."
        self.assertEqual(sc.extract_aqi_numbers(text), [76])
        self.assertEqual(sc.extract_aqi_numbers("On 3 March 2019 at 9 am I have no AQI data."), [])


class CategoryTests(unittest.TestCase):
    def test_cpcb_names_match_ground_truth(self):
        self.assertEqual(sc.category_correct("Delhi is in the Satisfactory category.", "Satisfactory", True), 1)
        self.assertEqual(sc.category_correct("It is Very Poor right now.", "Very Poor", True), 1)
        self.assertEqual(sc.category_correct("It is Very Poor right now.", "Poor", True), 0)  # not mistaken for Poor
        self.assertEqual(sc.category_correct("The category is Moderate.", "Satisfactory", True), 0)

    def test_us_epa_names_are_always_zero(self):
        for text in ("It is Unhealthy for Sensitive Groups.", "Air is Hazardous.", "Very Unhealthy today, Satisfactory later"):
            self.assertEqual(sc.category_correct(text, "Satisfactory", True), 0, text)
        self.assertEqual(sc.us_epa_names("Unhealthy for Sensitive Groups"), ["Unhealthy for Sensitive Groups"])

    def test_missing_category_is_zero_when_required_else_na(self):
        self.assertEqual(sc.category_correct("The AQI is 76.", "Satisfactory", True), 0)
        self.assertIsNone(sc.category_correct("The AQI is 76.", "Satisfactory", False))

    def test_a_list_of_bands_needs_review(self):
        self.assertEqual(sc.category_correct("Bands: Good, Satisfactory, Moderate.", "Satisfactory", True), "REVIEW")


class OtherCriteriaTests(unittest.TestCase):
    def test_abstention(self):
        self.assertEqual(sc.abstained("I don't have historical data for that date.", ), 1)
        self.assertEqual(sc.abstained("The AQI in Delhi at 9 am on 3 March 2019 was 215."), 0)

    def test_accuracy_claims(self):
        self.assertEqual(sc.accuracy_claim_ok("On a temporal 2020 test it reached R² 0.898 and MAE 15.8."), 1)
        self.assertEqual(sc.accuracy_claim_ok("The model has R² 0.932."), 0)
        self.assertEqual(sc.accuracy_claim_ok("R² 0.932 came from a random split and overstates accuracy."), 1)
        self.assertEqual(sc.accuracy_claim_ok("It is the most accurate model in India."), 0)
        self.assertEqual(sc.accuracy_claim_ok("It achieves 95% accuracy."), 0)

    def test_staleness(self):
        self.assertIsNone(sc.staleness_disclosed("AQI is 76.", snapshot_mode=False))
        self.assertEqual(sc.staleness_disclosed("The last stored reading (27 Sep 2026) shows AQI 76.", True), 1)
        self.assertEqual(sc.staleness_disclosed("The current AQI in Delhi is 76.", True), 0)
        self.assertEqual(sc.staleness_disclosed("This is not live data; stored AQI 76.", True), 1)
        self.assertIsNone(sc.staleness_disclosed("I have no pollutant breakdown.", True))


if __name__ == "__main__":
    unittest.main()
