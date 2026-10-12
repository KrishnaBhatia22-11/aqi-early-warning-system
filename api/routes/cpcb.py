"""
CPCB feed diagnostics.

These used to report on a Layer-2 HTML scraper of the CPCB dashboard, which had
been dead for months (_scrape_cpcb_all returned None unconditionally). CPCB is
now the app's primary and only live source via data.gov.in, so these endpoints
report on that client's cache instead — which is what you actually want to check
when the map looks wrong.
"""

from fastapi import APIRouter
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.data.cpcb_client import cache_status, fetch_city_aqi
from api import snapshot as snap

router = APIRouter()


@router.get("/cpcb/status")
async def cpcb_status():
    """Live-feed health — key present, cache age, how many cities are live, and fallback state."""
    status = cache_status()
    snapshots = await snap.latest_readings() if status["cities_live"] < snap.MIN_LIVE_CITIES else {}
    stamps = [snap.iso_utc(r.timestamp) for r in snapshots.values()]
    snapshot_as_of = max(stamps) if stamps else None
    fallback_active = bool(snapshots)
    if fallback_active:
        data_mode = "snapshot"
    elif status["cities_live"] > 0:
        data_mode = "live"
    else:
        data_mode = "unavailable"
    return {
        "available":     status["cities_live"] > 0,
        "station_count": status["cities_live"],
        "source":        status["source"],
        **status,
        "data_mode":       data_mode,
        "fallback_active": fallback_active,
        "snapshot_as_of":  snapshot_as_of,
        "snapshot_cities": len(snapshots),
    }


@router.get("/cpcb/city/{city_name}")
def cpcb_city(city_name: str):
    """Raw CPCB result for one city, including the stations that were excluded."""
    result = fetch_city_aqi(city_name)
    if not result or not result.get("success"):
        return {"success": False, "city": city_name, "error": "No CPCB data for this city"}
    return result
