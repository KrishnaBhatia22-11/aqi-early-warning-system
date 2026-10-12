import asyncio
import os
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest import mock

os.environ.setdefault("DATABASE_URL", "postgresql://u:p@localhost:5432/db")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api import snapshot as snap
from api.limiter import limiter
from api.routes import anomaly, chat, city, compare, forecast

STORED_AT = datetime(2026, 10, 9, 14, 0, tzinfo=timezone.utc)


def reading(name, aqi, ts=STORED_AT, source="CPCB"):
    return SimpleNamespace(city=name, aqi=aqi, pm25=80.0, pm10=120.0, no2=30.0, co=1.1, so2=9.0, o3=40.0,
                           station_count=4, source=source, timestamp=ts)


def empty_feed():
    """What fetch_all_cities returns while the CPCB feed is down: no-data rows for every city."""
    return [{"success": False, "data_available": False, "no_data": True, "aqi": None, "city": name,
             "lat": 1.0, "lon": 2.0} for name in ("Delhi", "Mumbai", "Chennai", "Kolkata", "Bengaluru", "Pune")]


def live_feed(n=6):
    names = ["Delhi", "Mumbai", "Chennai", "Kolkata", "Bengaluru", "Pune", "Jaipur"][:n]
    return [{"success": True, "data_available": True, "city": name, "aqi": 100 + i * 10, "lat": 1.0, "lon": 2.0,
             "station_count": 3} for i, name in enumerate(names)]


def client(*routers):
    app = FastAPI()
    app.state.limiter = limiter
    for router in routers:
        app.include_router(router, prefix="/api/v1")
    return TestClient(app)


async def _stored(*readings):
    return {r.city: r for r in readings}


class CitiesRouteTests(unittest.TestCase):
    def test_feed_empty_with_stored_rows_returns_snapshot_with_as_of(self):
        stored = {"Delhi": reading("Delhi", 255.0), "Mumbai": reading("Mumbai", 92.0)}
        with mock.patch.object(city, "fetch_all_cities", return_value=empty_feed()), \
             mock.patch.object(snap, "latest_readings", mock.AsyncMock(return_value=stored)):
            body = client(city.router).get("/api/v1/cities").json()
        self.assertEqual(body["data_mode"], "snapshot")
        self.assertTrue(body["fallback_active"])
        self.assertEqual(body["cities_live"], 0)
        self.assertEqual(body["as_of_latest"], STORED_AT.isoformat())
        by_name = {c["city"]: c for c in body["cities"]}
        self.assertEqual(by_name["Delhi"]["aqi"], 255)
        self.assertEqual(by_name["Delhi"]["data_mode"], "snapshot")
        self.assertEqual(by_name["Delhi"]["as_of"], STORED_AT.isoformat())
        self.assertEqual(by_name["Delhi"]["category"], "Poor")
        # a city with no stored reading has no value
        self.assertIsNone(by_name["Chennai"]["aqi"])
        self.assertEqual(by_name["Chennai"]["data_mode"], "none")

    def test_feed_empty_and_no_rows_returns_no_values_and_no_defaults(self):
        with mock.patch.object(city, "fetch_all_cities", return_value=empty_feed()), \
             mock.patch.object(snap, "latest_readings", mock.AsyncMock(return_value={})):
            body = client(city.router).get("/api/v1/cities").json()
        self.assertEqual(body["data_mode"], "unavailable")
        self.assertFalse(body["fallback_active"])
        self.assertTrue(all(c["aqi"] is None for c in body["cities"]))

    def test_live_feed_returns_live_mode_and_skips_the_database(self):
        latest = mock.AsyncMock(return_value={"Delhi": reading("Delhi", 999.0)})
        with mock.patch.object(city, "fetch_all_cities", return_value=live_feed()), \
             mock.patch.object(snap, "latest_readings", latest):
            body = client(city.router).get("/api/v1/cities").json()
        self.assertEqual(body["data_mode"], "live")
        self.assertEqual(body["cities_live"], 6)
        self.assertTrue(all(c["data_mode"] == "live" for c in body["cities"]))
        latest.assert_not_called()

    def test_invalid_stored_values_are_never_served(self):
        bad = {"Delhi": reading("Delhi", 0.0), "Mumbai": reading("Mumbai", 650.0),
               "Chennai": reading("Chennai", 90.0, source="WAQI")}
        rows, summary = snap.merge_live_and_snapshot(empty_feed(), {k: v for k, v in bad.items() if snap._valid_reading(v)})
        self.assertEqual(summary["data_mode"], "unavailable")
        self.assertTrue(all(r["aqi"] is None for r in rows))


class ChatContextTests(unittest.TestCase):
    def test_snapshot_mode_prefixes_stored_readings_and_does_not_say_live(self):
        stored = {"Delhi": reading("Delhi", 255.0)}
        with mock.patch("src.data.cpcb_client.fetch_all_cities", return_value=empty_feed()), \
             mock.patch.object(snap, "latest_readings", mock.AsyncMock(return_value=stored)):
            text = asyncio.run(chat._fetch_cities_ctx())
        self.assertIn(f"LAST STORED CPCB READINGS as of {STORED_AT.isoformat()} (live feed unavailable)", text)
        self.assertNotIn("fetched just now", text)
        self.assertIn("Delhi: 255 AQI (Poor)", text)

    def test_no_data_at_all_tells_the_model_not_to_guess(self):
        with mock.patch("src.data.cpcb_client.fetch_all_cities", return_value=empty_feed()), \
             mock.patch.object(snap, "latest_readings", mock.AsyncMock(return_value={})):
            text = asyncio.run(chat._fetch_cities_ctx())
        self.assertIn("No live or stored CPCB readings", text)
        self.assertNotIn("AQI (", text)

    def test_live_mode_keeps_the_live_header(self):
        with mock.patch("src.data.cpcb_client.fetch_all_cities", return_value=live_feed()):
            text = asyncio.run(chat._fetch_cities_ctx())
        self.assertIn("LIVE CITY AQI (fetched just now)", text)
        self.assertNotIn("LAST STORED", text)


class NoDefaultsTests(unittest.TestCase):
    def test_forecast_without_any_reading_is_503_not_a_default(self):
        with mock.patch.object(snap, "resolve_city_aqi", mock.AsyncMock(return_value=None)):
            response = client(forecast.router).post("/api/v1/forecast", json={"city": "Delhi"})
        self.assertEqual(response.status_code, 503)
        self.assertIn("forecast unavailable", response.json()["detail"])

    def test_forecast_uses_stored_snapshot_and_says_so(self):
        resolved = {"aqi": 200.0, "dominant_pollutant": None, "data_mode": "snapshot", "as_of": STORED_AT.isoformat()}
        with mock.patch.object(snap, "resolve_city_aqi", mock.AsyncMock(return_value=resolved)):
            body = client(forecast.router).post("/api/v1/forecast", json={"city": "Lucknow"}).json()
        self.assertEqual(body["base_aqi_source"], "stored_snapshot")
        self.assertEqual(body["base_as_of"], STORED_AT.isoformat())
        self.assertEqual(body["base_aqi"], 200)

    def test_compare_without_any_reading_is_503(self):
        with mock.patch.object(snap, "resolve_city_aqi", mock.AsyncMock(return_value=None)):
            response = client(compare.router).get("/api/v1/compare?city1=Delhi&city2=Mumbai")
        self.assertEqual(response.status_code, 503)

    def test_compare_snapshot_is_labelled(self):
        resolved = {"aqi": 150.0, "dominant_pollutant": None, "data_mode": "snapshot", "as_of": STORED_AT.isoformat()}
        with mock.patch.object(snap, "resolve_city_aqi", mock.AsyncMock(return_value=resolved)):
            body = client(compare.router).get("/api/v1/compare?city1=Agra&city2=Surat").json()
        self.assertEqual(body["city1"]["source"], "snapshot")
        self.assertEqual(body["city1"]["as_of"], STORED_AT.isoformat())
        self.assertIsNone(body["city1"]["dominant_pollutant"])
        self.assertIn("last stored reading", body["insight"])

    def test_anomaly_without_real_history_is_unavailable_not_synthetic(self):
        body = client(anomaly.router).post("/api/v1/anomaly/detect", json={"city": "Delhi", "current_aqi": 400}).json()
        self.assertFalse(body["available"])
        self.assertFalse(body["is_anomaly"])
        self.assertEqual(body["data_quality"], "none")

    def test_no_default_aqi_dicts_remain(self):
        for module in (forecast, compare, anomaly):
            self.assertFalse(hasattr(module, "CITY_DEFAULTS") or hasattr(module, "_CITY_DEFAULTS"), module.__name__)


class SnapshotSaverTests(unittest.TestCase):
    def _run(self, rows, age):
        from api import scheduler

        session = mock.MagicMock()
        session.add_all = mock.MagicMock()
        session.commit = mock.AsyncMock()
        factory = mock.MagicMock()
        factory.return_value.__aenter__ = mock.AsyncMock(return_value=session)
        factory.return_value.__aexit__ = mock.AsyncMock(return_value=False)
        with mock.patch.object(scheduler, "refresh_cache"), \
             mock.patch.object(scheduler, "fetch_all_cities", return_value=rows), \
             mock.patch.object(scheduler, "cache_status", return_value={"age_seconds": age}), \
             mock.patch.object(scheduler, "AsyncSessionLocal", factory), \
             mock.patch.object(scheduler, "check_and_fire_alerts", mock.AsyncMock()):
            asyncio.run(scheduler.save_hourly_snapshot())
        return session

    def test_empty_feed_writes_nothing(self):
        session = self._run(empty_feed(), age=None)
        session.add_all.assert_not_called()
        session.commit.assert_not_called()

    def test_stale_cache_is_not_restamped_as_a_new_reading(self):
        session = self._run(live_feed(), age=3 * 86400)
        session.add_all.assert_not_called()

    def test_only_valid_readings_are_written(self):
        rows = live_feed(3) + [
            {"success": True, "data_available": True, "city": "Zero", "aqi": 0},
            {"success": True, "data_available": True, "city": "Over", "aqi": 800},
            {"success": True, "data_available": True, "city": "None", "aqi": None},
            {"success": False, "data_available": False, "city": "Gone", "aqi": 120},
        ]
        session = self._run(rows, age=30)
        written = session.add_all.call_args[0][0]
        self.assertEqual(sorted(r.city for r in written), sorted(["Delhi", "Mumbai", "Chennai"]))


if __name__ == "__main__":
    unittest.main()
