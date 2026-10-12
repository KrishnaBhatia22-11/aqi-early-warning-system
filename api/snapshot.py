"""Last-known-good fallback: serve the latest STORED CPCB readings when the live feed is down.

The hourly scheduler writes real CPCB readings into ``aqi_readings`` while the feed
works. When the live pull has fewer than ``MIN_LIVE_CITIES`` live cities, the latest
stored reading per city is served instead, always labelled ``data_mode: "snapshot"``
with the reading's own timestamp (``as_of``). Nothing is ever invented: a city with no
stored reading simply has no value.
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional

from sqlalchemy import and_, func, select

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.settings import CITY_COORDS
from src.data.india_aqi import AQI_STANDARD, aqi_color, categorize_aqi

MIN_LIVE_CITIES = 5
SNAPSHOT_SOURCE_LABEL = "Last stored CPCB reading (live feed unavailable)"


def _session_factory():
    from api.database import AsyncSessionLocal

    return AsyncSessionLocal


def iso_utc(ts: Optional[datetime]) -> Optional[str]:
    if ts is None:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc).isoformat()


def is_live_row(row: dict[str, Any]) -> bool:
    aqi = row.get("aqi")
    return bool(row.get("success")) and isinstance(aqi, (int, float)) and aqi > 0


def _valid_reading(reading: Any) -> bool:
    aqi = getattr(reading, "aqi", None)
    return (
        aqi is not None and 0 < aqi <= 500
        and getattr(reading, "source", "CPCB") == "CPCB"
        and getattr(reading, "timestamp", None) is not None
    )


async def latest_readings(session_factory: Optional[Callable] = None) -> dict[str, Any]:
    """Latest stored CPCB reading per city ({city: AQIReading}). Empty on any DB problem."""
    try:
        from api.models import AQIReading

        factory = session_factory or _session_factory()
        latest = (
            select(AQIReading.city.label("city"), func.max(AQIReading.timestamp).label("ts"))
            .where(AQIReading.source == "CPCB", AQIReading.aqi > 0, AQIReading.aqi <= 500)
            .group_by(AQIReading.city)
            .subquery()
        )
        stmt = (
            select(AQIReading)
            .join(latest, and_(AQIReading.city == latest.c.city, AQIReading.timestamp == latest.c.ts))
            .where(AQIReading.source == "CPCB", AQIReading.aqi > 0, AQIReading.aqi <= 500)
        )
        async with factory() as session:
            rows = (await session.execute(stmt)).scalars().all()
    except Exception as error:  # DB down or table missing: no snapshot, never a made-up value
        print(f"[Snapshot] could not read stored readings: {error}")
        return {}
    out: dict[str, Any] = {}
    for reading in rows:
        if _valid_reading(reading):
            out.setdefault(reading.city, reading)
    return out


def snapshot_row(reading: Any, coords: Optional[dict[str, float]] = None) -> dict[str, Any]:
    """Per-city row in the live shape, built only from the stored reading."""
    aqi = float(reading.aqi)
    row = {
        "success": True,
        "data_available": True,
        "city": reading.city,
        "aqi": round(aqi),
        "aqi_standard": AQI_STANDARD,
        "category": categorize_aqi(aqi),
        "color": aqi_color(aqi),
        "pm25": reading.pm25,
        "pm10": reading.pm10,
        "no2": reading.no2,
        "co": reading.co,
        "so2": reading.so2,
        "o3": reading.o3,
        "station_count": reading.station_count,
        "dominant_pollutant": None,
        "source": SNAPSHOT_SOURCE_LABEL,
        "data_mode": "snapshot",
        "as_of": iso_utc(reading.timestamp),
    }
    if coords:
        row["lat"], row["lon"] = coords["lat"], coords["lon"]
    return row


def merge_live_and_snapshot(
    live_rows: list[dict[str, Any]],
    snapshots: dict[str, Any],
    min_live: int = MIN_LIVE_CITIES,
    now: Optional[datetime] = None,
    live_as_of: Optional[str] = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Pure merge. Live rows win; stored readings fill the gaps only when the feed is thin."""
    live_count = sum(1 for r in live_rows if is_live_row(r))
    fallback = live_count < min_live and bool(snapshots)
    rows, snapshot_count = [], 0
    for row in live_rows:
        name = row.get("city") or row.get("name")
        if is_live_row(row):
            rows.append({**row, "data_mode": "live", "as_of": live_as_of})
        elif fallback and name in snapshots:
            rows.append(snapshot_row(snapshots[name], CITY_COORDS.get(name)))
            snapshot_count += 1
        else:
            rows.append({**row, "data_mode": "none", "as_of": None})
    stamps = [r["as_of"] for r in rows if r.get("data_mode") == "snapshot" and r.get("as_of")]
    snapshot_as_of = max(stamps) if stamps else None
    if fallback:
        mode, as_of_latest = "snapshot", snapshot_as_of
    elif live_count:
        mode, as_of_latest = "live", live_as_of
    else:
        mode, as_of_latest = "unavailable", None
    summary = {
        "data_mode": mode,
        "as_of_latest": as_of_latest,
        "cities_live": live_count,
        "cities_snapshot": snapshot_count,
        "fallback_active": fallback,
        "snapshot_as_of": snapshot_as_of,
        "min_live_cities": min_live,
    }
    return rows, summary


async def rows_with_fallback(
    live_rows: list[dict[str, Any]],
    session_factory: Optional[Callable] = None,
    live_as_of: Optional[str] = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    live_count = sum(1 for r in live_rows if is_live_row(r))
    snapshots = await latest_readings(session_factory) if live_count < MIN_LIVE_CITIES else {}
    return merge_live_and_snapshot(live_rows, snapshots, live_as_of=live_as_of)


def live_as_of_iso() -> Optional[str]:
    """When the live cache was last filled from CPCB (None if never)."""
    try:
        from src.data.cpcb_client import cache_status

        age = cache_status().get("age_seconds")
    except Exception:
        return None
    if age is None:
        return None
    return iso_utc(datetime.now(timezone.utc) - timedelta(seconds=age))


async def resolve_city_aqi(city: str, session_factory: Optional[Callable] = None) -> Optional[dict[str, Any]]:
    """Live AQI for one city, else its latest stored reading, else None. Never a default."""
    from src.data.cpcb_client import fetch_city_aqi

    live = await asyncio.to_thread(fetch_city_aqi, city) or {}
    if is_live_row(live):
        return {"aqi": float(live["aqi"]), "dominant_pollutant": live.get("dominant_pollutant"),
                "data_mode": "live", "as_of": live_as_of_iso()}
    stored = (await latest_readings(session_factory)).get(city)
    if stored is not None:
        return {"aqi": float(stored.aqi), "dominant_pollutant": None,
                "data_mode": "snapshot", "as_of": iso_utc(stored.timestamp)}
    return None
