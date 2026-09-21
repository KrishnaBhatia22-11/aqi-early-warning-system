import re
import asyncio
import sys
import os

from fastapi import APIRouter, HTTPException, Request
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data.cpcb_client import fetch_city_aqi, fetch_all_cities
from src.analytics.health_score import get_health_advisory, get_general_precautions
from config.settings import CITY_COORDS
from api.limiter import limiter

router = APIRouter()

# ─────────────────────────────────────────────
# /cities no longer fans out
# ─────────────────────────────────────────────
# This endpoint used to open one upstream search plus a station fan-out for each
# of 53 cities, behind a dedicated thread pool, a per-city timeout, a per-request
# semaphore and a global deadline — all of it machinery for surviving 53
# simultaneous network calls on a 512MB box.
#
# The CPCB resource publishes the whole country in a few thousand records, so
# cpcb_client pulls it once and caches it for 15 minutes. Both endpoints here
# now read that one snapshot. There is no fan-out left to bound, so the pool,
# the semaphore and both timeouts are gone with it.
#
# The single remaining concern is the cold path: the very first request after a
# deploy has to wait for that national pull. asyncio.to_thread keeps it off the
# event loop, and _COLD_FETCH_TIMEOUT caps it so a slow upstream degrades to
# no-data markers rather than hanging the whole map to Render's 30s limit.
_COLD_FETCH_TIMEOUT = 25.0

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
async def get_city_aqi(request: Request, city_name: str):
    _validate_city(city_name)
    try:
        try:
            data = await asyncio.wait_for(
                asyncio.to_thread(fetch_city_aqi, city_name),
                timeout=_COLD_FETCH_TIMEOUT,
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=503,
                detail="Live CPCB data is still loading — please retry in a moment",
            )

        if not data or not data.get('success'):
            raise HTTPException(
                status_code=404,
                detail=f"Could not fetch data for {city_name}: {(data or {}).get('error')}"
            )

        # Advisory keys off the CPCB category name, so the advice shown always
        # matches the category shown.
        advisory    = get_health_advisory(data['category'])
        precautions = get_general_precautions(data['category'])

        data = dict(data)
        data['health_advisory']     = advisory
        data['general_precautions'] = precautions

        coords = CITY_COORDS.get(city_name)
        if coords:
            data['lat'] = coords['lat']
            data['lon'] = coords['lon']

        return data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# GET /cities — live data for ALL cities on map
# ─────────────────────────────────────────────
def _no_data_city(city):
    """Placeholder row so a failed city still gets a map marker."""
    return {
        "success":        False,
        "data_available": False,
        "no_data":        True,
        "city":           city,
        "aqi":            None,
        "lat":            CITY_COORDS[city]["lat"],
        "lon":            CITY_COORDS[city]["lon"],
    }


@router.get("/cities")
@limiter.limit("30/minute")
async def get_all_cities(request: Request):
    try:
        try:
            cities_data = await asyncio.wait_for(
                asyncio.to_thread(fetch_all_cities),
                timeout=_COLD_FETCH_TIMEOUT,
            )
        except asyncio.TimeoutError:
            # Still answer with the full set of markers. A map of grey pins that
            # arrives beats a 504 that does not, and the next request will find
            # the cache warm.
            print("[Cities] Cold CPCB fetch exceeded the deadline — returning no-data markers")
            cities_data = []

        if not cities_data:
            cities_data = [_no_data_city(city) for city in CITY_COORDS]
        else:
            # A city the feed does not cover comes back with success=False; give
            # it the explicit no_data flag the frontend keys its grey marker off.
            cities_data = [
                row if row.get("success") else {**row, "no_data": True}
                for row in cities_data
            ]

        return {
            "success": True,
            "count":   len(cities_data),
            "cities":  cities_data,
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
