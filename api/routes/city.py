from fastapi import APIRouter, HTTPException
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
def get_all_cities():
    try:
        cities_data = fetch_all_cities()
        return {
            "success": True,
            "count":   len(cities_data),
            "cities":  cities_data
        }
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