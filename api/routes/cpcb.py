from fastapi import APIRouter
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.data.waqi_client import _scrape_cpcb_all, _fetch_cpcb

router = APIRouter()


@router.get("/cpcb/status")
def cpcb_status():
    """CPCB scraper health — returns how many stations are loaded."""
    stations = _scrape_cpcb_all()
    return {
        "available":     len(stations) > 0,
        "station_count": len(stations),
        "source":        "CPCB CAAQM",
    }


@router.get("/cpcb/city/{city_name}")
def cpcb_city(city_name: str):
    """CPCB direct AQI for a single city (Layer 2 fallback data)."""
    result = _fetch_cpcb(city_name)
    if not result:
        return {"success": False, "city": city_name, "error": "No CPCB data for this city"}
    return result
