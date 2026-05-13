import asyncio
import sys
import os
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.data.waqi_client import fetch_all_cities
from api.database import AsyncSessionLocal
from api.models import AQIReading

scheduler = AsyncIOScheduler()


async def save_hourly_snapshot():
    try:
        # fetch_all_cities is synchronous — run in thread pool to avoid blocking the loop
        cities_data = await asyncio.to_thread(fetch_all_cities)

        rows = []
        for city in cities_data:
            aqi = city.get("aqi")
            if not city.get("data_available", False) or not aqi or aqi == 0:
                continue
            rows.append(AQIReading(
                city=city.get("city") or city.get("name", "Unknown"),
                aqi=float(aqi),
                pm25=city.get("pm25"),
                pm10=city.get("pm10"),
                no2=city.get("no2"),
                co=city.get("co"),
                so2=city.get("so2"),
                o3=city.get("o3"),
                station_count=city.get("station_count"),
                source="WAQI",
            ))

        if rows:
            async with AsyncSessionLocal() as session:
                session.add_all(rows)
                await session.commit()

        ts = datetime.now(timezone.utc).isoformat()
        print(f"[Scheduler] Saved {len(rows)} city readings at {ts}")

    except Exception as e:
        print(f"[Scheduler] Error saving snapshot: {e}")
