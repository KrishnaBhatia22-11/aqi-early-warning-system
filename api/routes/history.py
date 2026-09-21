"""
Per-city AQI history.

This used to read WAQI's `forecast.daily.pm25` block and present it as history —
which was never quite what it claimed: those entries are WAQI's own daily PM2.5
summaries, and the PM2.5 average was returned directly in the `aqi` field, so a
US-scale sub-index and a raw µg/m³ concentration were being shown as one number.

Now that CPCB (data.gov.in) is the live source, there is no upstream history to
read at all: the feed publishes the current hour only. The app's own
`aqi_readings` table is the history — the scheduler has been writing an hourly
snapshot per city into it all along — so this endpoint reads that, on the India
CPCB scale, and says plainly when a city has not accumulated readings yet.

/db/history serves the same table in a richer per-reading shape for the Time
Machine; this endpoint keeps its original day-summary shape for API consumers.
"""

import re
import sys
import os
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from api.database import AsyncSessionLocal
from api.models import AQIReading
from src.data.india_aqi import AQI_STANDARD, categorize_aqi

router = APIRouter()

SOURCE_LABEL = "CPCB — Central Pollution Control Board (data.gov.in), via hourly snapshots"

_CITY_RE = re.compile(r'^[A-Za-z][A-Za-z \-]{0,49}$')


@router.get("/history/{city}")
async def get_history(
    city: str,
    days: int = Query(default=7, ge=1, le=30),
):
    if not _CITY_RE.match(city or ""):
        raise HTTPException(
            status_code=400,
            detail="City name may only contain letters, spaces, and hyphens",
        )

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    try:
        async with AsyncSessionLocal() as session:
            rows = (await session.execute(
                select(AQIReading.timestamp, AQIReading.aqi, AQIReading.pm25)
                .where(AQIReading.city == city, AQIReading.timestamp >= cutoff)
                .order_by(AQIReading.timestamp.asc())
            )).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {e}")

    # Fold the hourly snapshots into one entry per day.
    by_day = {}
    for row in rows:
        if row.aqi is None:
            continue
        day = row.timestamp.strftime("%Y-%m-%d")
        bucket = by_day.setdefault(day, {"aqi": [], "pm25": []})
        bucket["aqi"].append(row.aqi)
        if row.pm25 is not None:
            bucket["pm25"].append(row.pm25)

    history_points = [
        {
            "date":     day,
            "aqi":      round(sum(v["aqi"]) / len(v["aqi"])),
            "aqi_min":  round(min(v["aqi"])),
            "aqi_max":  round(max(v["aqi"])),
            "pm25_avg": round(sum(v["pm25"]) / len(v["pm25"]), 1) if v["pm25"] else None,
            "source":   "CPCB",
            "is_forecast": False,
        }
        for day, v in sorted(by_day.items())
    ]

    latest      = rows[-1] if rows else None
    current_aqi = round(latest.aqi) if latest and latest.aqi is not None else None
    current_time = latest.timestamp.isoformat() if latest else ""

    if not history_points:
        return {
            "city": city,
            "message": (
                "No stored readings for this city yet. History is built from the "
                "app's own hourly CPCB snapshots, so it fills in over time."
            ),
            "current_aqi":  current_aqi,
            "current_time": current_time,
            "history": [],
            "source": SOURCE_LABEL,
            "aqi_standard": AQI_STANDARD,
            "data_available": False,
        }

    aqi_values = [p["aqi"] for p in history_points]

    return {
        "city":         city,
        "history":      history_points,
        "current_aqi":  current_aqi,
        "current_time": current_time,
        "current_category": categorize_aqi(current_aqi),
        "summary": {
            "avg_aqi":        round(sum(aqi_values) / len(aqi_values)),
            "max_aqi":        max(aqi_values),
            "min_aqi":        min(aqi_values),
            "days_available": len(history_points),
            "worst_day":      history_points[aqi_values.index(max(aqi_values))]["date"],
            "best_day":       history_points[aqi_values.index(min(aqi_values))]["date"],
        },
        "source":         SOURCE_LABEL,
        "aqi_standard":   AQI_STANDARD,
        "data_available": True,
    }
