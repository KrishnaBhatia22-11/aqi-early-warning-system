from fastapi import APIRouter, HTTPException
import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.data.waqi_client import fetch_city_aqi, fetch_all_cities
from src.analytics.health_score import get_health_advisory, get_general_precautions
from config.settings import CITY_COORDS

router = APIRouter()


# ─────────────────────────────────────────────
# GET /city/{city_name} — live data for one city
# ─────────────────────────────────────────────
@router.get("/city/{city_name}")
def get_city_aqi(city_name: str):
    try:
        data = fetch_city_aqi(city_name)

        if not data['success']:
            raise HTTPException(
                status_code=404,
                detail=f"Could not fetch data for {city_name}: {data.get('error')}"
            )

        # Add health advisory based on live AQI category
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
async def get_all_cities():
    loop = asyncio.get_event_loop()

    async def fetch_one_async(city):
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(None, fetch_city_aqi, city),
                timeout=5.0,
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