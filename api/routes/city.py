import re
import asyncio
import sys
import os

from fastapi import APIRouter, HTTPException, Request
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data.waqi_client import fetch_city_aqi, fetch_all_cities
from src.analytics.health_score import get_health_advisory, get_general_precautions
from config.settings import CITY_COORDS
from api.limiter import limiter

router = APIRouter()

# Letters, spaces, hyphens only — max 50 chars — blocks SQL/script injection
_CITY_RE = re.compile(r'^[A-Za-z][A-Za-z \-]{0,49}$')


def _validate_city(name: str):
    if not name or len(name) > 50:
        raise HTTPException(status_code=400, detail="City name must be 1–50 characters")
    if not _CITY_RE.match(name):
        raise HTTPException(
            status_code=400,
            detail="City name may only contain letters, spaces, and hyphens",
        )


# ─────────────────────────────────────────────
# GET /city/{city_name} — live data for one city
# ─────────────────────────────────────────────
@router.get("/city/{city_name}")
@limiter.limit("60/minute")
def get_city_aqi(request: Request, city_name: str):
    _validate_city(city_name)
    try:
        data = fetch_city_aqi(city_name)

        if not data['success']:
            raise HTTPException(
                status_code=404,
                detail=f"Could not fetch data for {city_name}: {data.get('error')}"
            )

        advisory    = get_health_advisory(data['category'])
        precautions = get_general_precautions(data['category'])

        data['health_advisory']     = advisory
        data['general_precautions'] = precautions

        return data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# GET /cities — live data for ALL cities on map
# ─────────────────────────────────────────────
@router.get("/cities")
@limiter.limit("30/minute")
async def get_all_cities(request: Request):
    loop = asyncio.get_event_loop()

    async def fetch_one_async(city):
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(None, fetch_city_aqi, city),
                timeout=10.0,
            )
        except asyncio.TimeoutError:
            result = {"success": False, "data_available": False, "no_data": True,
                      "city": city, "aqi": None}
        if result is None:
            result = {"success": False, "data_available": False, "no_data": True,
                      "city": city, "aqi": None}
        result = dict(result)
        result["lat"] = CITY_COORDS[city]["lat"]
        result["lon"] = CITY_COORDS[city]["lon"]
        return result

    try:
        tasks = [fetch_one_async(city) for city in CITY_COORDS.keys()]
        cities_data = await asyncio.wait_for(asyncio.gather(*tasks), timeout=30.0)
        return {
            "success": True,
            "count":   len(cities_data),
            "cities":  list(cities_data),
        }
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Global timeout: cities endpoint exceeded 30s")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# GET /cities/list — just names and coordinates
# ─────────────────────────────────────────────
@router.get("/cities/list")
def list_cities():
    return {
        "cities": [
            {"name": city, **coords}
            for city, coords in CITY_COORDS.items()
        ]
    }
