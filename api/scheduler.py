import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone

import resend
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.data.waqi_client import fetch_all_cities
from api.database import AsyncSessionLocal
from api.models import AQIReading, AlertSubscription

resend.api_key = os.environ.get("RESEND_API_KEY", "")

scheduler = AsyncIOScheduler()

_UNSUBSCRIBE_BASE = "https://aqi-api-y2qs.onrender.com/api/v1/alerts/unsubscribe"


def _aqi_category(aqi: float) -> tuple[str, str]:
    """Returns (category_name, hex_color)."""
    if aqi <= 50:   return ("Good",         "#22c55e")
    if aqi <= 100:  return ("Satisfactory",  "#84cc16")
    if aqi <= 200:  return ("Moderate",      "#eab308")
    if aqi <= 300:  return ("Poor",          "#f97316")
    if aqi <= 400:  return ("Very Poor",     "#ef4444")
    return              ("Severe",           "#7c3aed")


def _health_advice(aqi: float) -> str:
    if aqi <= 50:
        return "Air quality is good. Enjoy outdoor activities."
    if aqi <= 100:
        return "Air quality is acceptable. Sensitive individuals should reduce prolonged outdoor exertion."
    if aqi <= 200:
        return "Unhealthy for sensitive groups. People with respiratory or heart conditions should limit outdoor activities."
    if aqi <= 300:
        return "Everyone should reduce prolonged outdoor exertion. Wear a mask when outside."
    if aqi <= 400:
        return "Very unhealthy. Avoid all outdoor activities. Wear an N95 mask if you must go out."
    return "Hazardous. Stay indoors. Seal windows and doors. Use an air purifier if available."


async def save_hourly_snapshot():
    try:
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

    await check_and_fire_alerts()


async def check_and_fire_alerts():
    try:
        now = datetime.now(timezone.utc)
        four_hours_ago = now - timedelta(hours=4)

        async with AsyncSessionLocal() as session:
            subs_result = await session.execute(
                select(AlertSubscription).where(AlertSubscription.active == True)  # noqa: E712
            )
            subs = subs_result.scalars().all()

            for sub in subs:
                # Get the most recent reading for this city
                reading_result = await session.execute(
                    select(AQIReading)
                    .where(AQIReading.city == sub.city)
                    .order_by(AQIReading.timestamp.desc())
                    .limit(1)
                )
                reading = reading_result.scalar_one_or_none()

                if reading is None or reading.aqi < sub.threshold:
                    continue

                # Skip if already fired within the last 4 hours
                if sub.last_fired is not None:
                    last = sub.last_fired
                    # make offset-aware for comparison if needed
                    if last.tzinfo is None:
                        last = last.replace(tzinfo=timezone.utc)
                    if last > four_hours_ago:
                        continue

                # Send the alert email
                category, color = _aqi_category(reading.aqi)
                advice = _health_advice(reading.aqi)
                unsubscribe_url = f"{_UNSUBSCRIBE_BASE}/{sub.token}"

                try:
                    resend.Emails.send({
                        "from": "AQI Alerts <onboarding@resend.dev>",
                        "to": [sub.email],
                        "subject": f"⚠️ {sub.city} AQI Alert — {int(reading.aqi)} right now",
                        "html": f"""
<html>
<body style="font-family:sans-serif;background:#f0f4f8;padding:32px;margin:0">
  <div style="max-width:480px;margin:0 auto;background:#fff;border-radius:12px;
              padding:36px;box-shadow:0 2px 12px rgba(0,0,0,0.08)">
    <h2 style="margin-top:0;color:#111;font-size:20px">⚠️ Air Quality Alert</h2>
    <p style="font-size:16px;color:#555;margin-bottom:8px">{sub.city}</p>
    <div style="font-size:72px;font-weight:700;color:{color};line-height:1;margin:16px 0">
      {int(reading.aqi)}
    </div>
    <p style="font-size:20px;font-weight:600;color:{color};margin:0 0 20px">
      {category}
    </p>
    <p style="font-size:15px;color:#334155;line-height:1.6;
              background:#f8fafc;border-left:4px solid {color};
              padding:12px 16px;border-radius:4px">
      {advice}
    </p>
    <p style="font-size:12px;color:#94a3b8;margin-top:32px;
              border-top:1px solid #e2e8f0;padding-top:16px">
      You set an alert for {sub.city} at AQI {sub.threshold}. &nbsp;
      <a href="{unsubscribe_url}" style="color:#22c55e;text-decoration:none">Unsubscribe</a>
    </p>
  </div>
</body>
</html>""",
                    })
                    print(f"[Alerts] Fired alert → {sub.email} for {sub.city} AQI {reading.aqi}")
                except Exception as mail_err:
                    print(f"[Alerts] Email failed for {sub.email}: {mail_err}")
                    continue

                sub.last_fired = now

            await session.commit()

    except Exception as e:
        print(f"[Alerts] Error in check_and_fire_alerts: {e}")
