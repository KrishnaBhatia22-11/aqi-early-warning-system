import re
import asyncio
import sys
import os
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, HTTPException, Request
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data.waqi_client import fetch_city_aqi, fetch_all_cities
from src.analytics.health_score import get_health_advisory, get_general_precautions
from config.settings import CITY_COORDS
from api.limiter import limiter

router = APIRouter()

# ─────────────────────────────────────────────
# Concurrency budget for /cities
# ─────────────────────────────────────────────
# /cities fans out to ~53 cities. Two things used to sink it:
#
#   1. It submitted to asyncio's DEFAULT executor (run_in_executor(None, ...)),
#      which is shared with every other asyncio.to_thread() in the app — the
#      scheduler and /chat both push fetch_all_cities() through it. When they
#      overlap, /cities queues behind them instead of running.
#   2. The per-city asyncio.wait_for() timer started when the coroutine was
#      created, not when the thread actually picked the job up. Cities sitting
#      in the executor queue burned their whole timeout before fetching a byte,
#      and cancelling a run_in_executor future does NOT stop the thread — so the
#      abandoned work kept holding a worker while the endpoint reported no-data.
#
# Fix: a dedicated pool sized for I/O fan-out (these calls are network-bound,
# not CPU-bound) plus a semaphore acquired BEFORE the timer starts.
#
# Sized to share the 512MB box with the warmup and the scheduler: these 8
# threads each fan out to at most _STATION_FETCH_WORKERS more, and every
# resulting request still passes through waqi_client's process-wide gate.
_MAX_CONCURRENT_CITIES = 8

# Matching the semaphore to the pool size means a permit-holder never waits on a
# worker, so the per-city timeout only ever measures real fetch time.
_city_pool = ThreadPoolExecutor(
    max_workers=_MAX_CONCURRENT_CITIES,
    thread_name_prefix="cities",
)

# The semaphore is built PER REQUEST, deliberately not at module level.
#
# A module-level asyncio.Semaphore binds itself to an event loop the first time
# a task actually has to wait on it, and from then on raises
# "is bound to a different event loop" for any other loop. Once that happened,
# every /cities call returned real data for at most _MAX_CONCURRENT_CITIES
# cities — the ones that took the uncontended fast path and never touched the
# loop — and no_data for all the rest, permanently. A per-request semaphore
# cannot outlive its loop, so the failure mode is structurally impossible.
#
# The app-wide ceiling does not depend on this: waqi_client's _waqi_gate is a
# threading primitive, loop-agnostic, and caps real upstream requests process
# wide however many /cities calls overlap.

# Each city may internally do a search call plus a station fan-out, so give it
# more headroom than a single HTTP timeout while staying far under the global cap.
_PER_CITY_TIMEOUT = 15.0

# Leaves room to still serialise a full response inside the 30s budget.
_GLOBAL_TIMEOUT = 25.0

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
    loop = asyncio.get_running_loop()
    cities = list(CITY_COORDS.keys())
    sem = asyncio.Semaphore(_MAX_CONCURRENT_CITIES)

    async def fetch_one_async(city):
        # The try wraps the acquire as well as the fetch. Anything that goes
        # wrong here — upstream error, timeout, or a problem with the lock
        # itself — must cost exactly one city, never escape and take the batch
        # down with it.
        try:
            # Hold a permit for the whole fetch, and only start the clock once
            # we have one — time spent waiting for a turn is not this city's
            # fault.
            async with sem:
                result = await asyncio.wait_for(
                    loop.run_in_executor(_city_pool, fetch_city_aqi, city),
                    timeout=_PER_CITY_TIMEOUT,
                )
        except Exception:
            return _no_data_city(city)

        if not result:
            return _no_data_city(city)

        result = dict(result)
        result["lat"] = CITY_COORDS[city]["lat"]
        result["lon"] = CITY_COORDS[city]["lon"]
        return result

    try:
        tasks = [asyncio.ensure_future(fetch_one_async(city)) for city in cities]

        # asyncio.wait never raises on timeout, so a slow tail degrades to
        # partial data instead of 504-ing the whole map.
        await asyncio.wait(tasks, timeout=_GLOBAL_TIMEOUT)

        cities_data = []
        for city, task in zip(cities, tasks):
            if task.done() and not task.cancelled() and task.exception() is None:
                cities_data.append(task.result())
            else:
                task.cancel()
                cities_data.append(_no_data_city(city))

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
