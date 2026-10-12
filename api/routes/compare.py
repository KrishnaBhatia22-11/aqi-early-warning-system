import sys
import os
import time
from typing import Optional
from fastapi import APIRouter, HTTPException

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from api import snapshot as snap
# India CPCB bands, re-exported from the calculator so this file can never
# drift from the thresholds the AQI numbers were produced with.
from src.data.india_aqi import categorize_aqi as _cat

router = APIRouter()

_POPULATIONS = {
    "Delhi": 32_000_000, "Mumbai": 20_700_000, "Bengaluru": 13_200_000,
    "Chennai": 10_900_000, "Kolkata": 15_000_000, "Hyderabad": 10_500_000,
    "Ahmedabad": 8_400_000, "Jaipur": 4_100_000, "Lucknow": 3_700_000,
    "Kanpur": 3_200_000, "Patna": 2_400_000, "Bhopal": 2_300_000,
    "Pune": 7_400_000, "Nagpur": 2_900_000, "Surat": 7_100_000,
    "Chandigarh": 1_200_000, "Amritsar": 1_300_000, "Varanasi": 1_500_000,
}

_cache: dict = {}
_CACHE_TTL = 300  # 5 minutes


async def _resolve(city: str) -> dict:
    """Live CPCB AQI, else the latest stored reading (labelled), else a 503. No default values."""
    resolved = await snap.resolve_city_aqi(city)
    if resolved is None:
        raise HTTPException(
            status_code=503,
            detail=f"No live or stored CPCB reading for {city}; comparison unavailable",
        )
    aqi = int(round(resolved["aqi"]))
    return {
        "name":               city,
        "aqi":                aqi,
        "category":           _cat(aqi),
        "dominant_pollutant": resolved["dominant_pollutant"],
        "population":         _POPULATIONS.get(city, 0),
        "source":             "live" if resolved["data_mode"] == "live" else "snapshot",
        "as_of":              resolved["as_of"],
    }


@router.get("/compare")
async def compare_cities(
    city1: str = "Delhi",
    city2: str = "Mumbai",
    aqi1: Optional[float] = None,
    aqi2: Optional[float] = None,
):
    city1 = city1.strip().title()
    city2 = city2.strip().title()

    if city1.lower() == city2.lower():
        raise HTTPException(400, detail="city1 and city2 must be different cities")

    # If caller passes both AQI values already on-screen, skip the live fetch entirely
    _provided = aqi1 is not None and aqi2 is not None
    cache_key = f"{city1.lower()}:{city2.lower()}"
    now = time.time()

    if _provided:
        d1 = {
            "name": city1, "aqi": int(aqi1), "category": _cat(int(aqi1)),
            "dominant_pollutant": None,
            "population": _POPULATIONS.get(city1, 0), "source": "provided",
        }
        d2 = {
            "name": city2, "aqi": int(aqi2), "category": _cat(int(aqi2)),
            "dominant_pollutant": None,
            "population": _POPULATIONS.get(city2, 0), "source": "provided",
        }
    else:
        if cache_key in _cache:
            ts, data = _cache[cache_key]
            if now - ts < _CACHE_TTL:
                return data

        d1 = await _resolve(city1)
        d2 = await _resolve(city2)

    v1, v2 = d1["aqi"], d2["aqi"]
    diff = abs(v1 - v2)

    # Insight — always from worse city's perspective
    worse, better = (d1, d2) if v1 >= v2 else (d2, d1)
    pct_worse = round((worse["aqi"] - better["aqi"]) / max(better["aqi"], 1) * 100)

    stored = "snapshot" in (d1["source"], d2["source"])
    when = "at the last stored reading (live feed unavailable)" if stored else "right now"
    if pct_worse < 5:
        insight = f"{worse['name']} and {better['name']} have similar air quality {when}"
    else:
        insight = f"{worse['name']} air is {pct_worse}% worse than {better['name']} {when}"

    # Cigarette equivalent difference per 1 hour outside
    cig1 = worse["aqi"] / (22 * 24)
    cig2 = better["aqi"] / (22 * 24)
    cig_diff = round(abs(cig1 - cig2), 1)
    cig_s = "s" if cig_diff != 1.0 else ""
    cigarette_difference = (
        f"Breathing {worse['name']} air costs {cig_diff} extra "
        f"cigarette{cig_s} vs {better['name']} per hour outside"
    )

    result = {
        "city1":                d1,
        "city2":                d2,
        "difference":           diff,
        "insight":              insight,
        "safer_city":           better["name"],
        "cigarette_difference": cigarette_difference,
    }

    if not _provided:
        _cache[cache_key] = (now, result)
    return result
