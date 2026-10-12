import asyncio
import unittest
from unittest.mock import patch

from api.routes import chat, predict

CPCB_NAMES = {"Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe"}
US_EPA_NAMES = {"Unhealthy", "Unhealthy for Sensitive Groups", "Very Unhealthy", "Hazardous"}


class ChatCategoryTests(unittest.TestCase):
    def test_chat_and_predict_share_one_cpcb_helper(self):
        self.assertIs(chat.categorize_aqi, predict.categorize_aqi)

    def test_boundaries_are_cpcb_names(self):
        expected = {0: "Good", 50: "Good", 51: "Satisfactory", 100: "Satisfactory", 101: "Moderate",
                    200: "Moderate", 201: "Poor", 300: "Poor", 301: "Very Poor", 400: "Very Poor",
                    401: "Severe", 500: "Severe"}
        for aqi, name in expected.items():
            self.assertEqual(chat.categorize_aqi(aqi), name, aqi)

    def test_live_city_context_uses_cpcb_names(self):
        cities = [{"success": True, "city": n, "name": n, "aqi": a}
                  for n, a in (("A", 150), ("B", 250), ("C", 450), ("D", 60), ("E", 80))]
        with patch("src.data.cpcb_client.fetch_all_cities", return_value=cities):
            text = asyncio.run(chat._fetch_cities_ctx())
        self.assertIn("A: 150 AQI (Moderate)", text)
        self.assertIn("B: 250 AQI (Poor)", text)
        self.assertIn("C: 450 AQI (Severe)", text)
        for bad in US_EPA_NAMES:
            self.assertNotIn(bad, text)

    def test_system_prompt_has_no_stale_accuracy_claims(self):
        for stale in ("0.932 (93.2%", "MAE=21.33", "most accurate", "Live since 2024", "16 CPCB stations", "1500+"):
            self.assertNotIn(stale, chat.SYSTEM_PROMPT)
        self.assertIn("R² 0.898", chat.SYSTEM_PROMPT)


if __name__ == "__main__":
    unittest.main()
