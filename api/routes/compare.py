import sys
import os
import time
from typing import Optional
from fastapi import APIRouter, HTTPException

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.data.waqi_client import fetch_city_aqi

router = APIRouter()

_POPULATIONS = {
    "Delhi": 32_000_000, "Mumbai": 20_700_000, "Bengaluru": 13_200_000,
    "Chennai": 10_900_000, "Kolkata": 15_000_000, "Hyderabad": 10_500_000,
    "Ahmedabad": 8_400_000, "Jaipur": 4_100_000, "Lucknow": 3_700_000,
    "Kanpur": 3_200_000, "Patna": 2_400_000, "Bhopal": 2_300_000,
    "Pune": 7_400_000, "Nagpur": 2_900_000, "Surat": 7_100_000,
    "Chandigarh": 1_200_000, "Amritsar": 1_300_000, "Varanasi": 1_500_000,
}

# Seasonal fallback baselines (summer 2026)
_CITY_DEFAULTS = {
    "Delhi": 185, "Mumbai": 95, "Kolkata": 140, "Chennai": 75,
    "Bengaluru": 85, "Hyderabad": 90, "Ahmedabad": 130, "Jaipur": 145,
    "Lucknow": 160, "Patna": 175, "Chandigarh": 105, "Amritsar": 120,
    "Guwahati": 95, "Bhopal": 120, "Pune": 100, "Nagpur": 125,
    "Surat": 115, "Kanpur": 180, "Varanasi": 170,
}

_DOMINANT = {
    "Delhi": "PM2.5", "Mumbai": "NO2", "Kolkata": "PM2.5", "Chennai": "O3",
    "Bengaluru": "NO2", "Hyderabad": "PM2.5", "Ahmedabad": "PM10",
    "Jaipur": "PM10", "Lucknow": "PM2.5", "Patna": "PM2.5",
}

_cache: dict = {}
_CACHE_TTL = 300  # 5 minutes


def _cat(aqi: float) -> str:
    if aqi <= 50:  return "Good"
    if aqi <= 100: return "Satisfactory"
    if aqi <= 200: return "Moderate"
    if aqi <= 300: return "Poor"
    if aqi <= 400: return "Very Poor"
    return "Severe"


def _resolve(city: str) -> dict:
    """Try WAQI; fall back to seasonal default if unavailable."""
    result = fetch_city_aqi(city)
    if result.get("success") and result.get("aqi"):
        return {
            "name":               city,
            "aqi":                int(result["aqi"]),
            "category":           _cat(int(result["aqi"])),
            "dominant_pollutant": _DOMINANT.get(city, "PM2.5"),
            "population":         _POPULATIONS.get(city, 0),
            "source":             "live",
        }
    # Fallback to seasonal default
    aqi = _CITY_DEFAULTS.get(city, 150)
    return {
        "name":               city,
        "aqi":                aqi,
        "category":           _cat(aqi),
        "dominant_pollutant": _DOMINANT.get(city, "PM2.5"),
        "population":         _POPULATIONS.get(city, 0),
        "source":             "estimate",
    }


@router.get("/compare")
def compare_cities(
    city1: str = "Delhi",
    city2: str = "Mumbai",
    aqi1: Optional[float] = None,
    aqi2: Optional[float] = None,
):
    city1 = city1.strip().title()
    city2 = city2.strip().title()

    if city1.lower() == city2.lower():
        raise HTTPException(400, detail="city1 and city2 must be different cities")

    # If caller passes both AQI values already on-screen, skip WAQI fetch entirely
    _provided = aqi1 is not None and aqi2 is not None
    cache_key = f"{city1.lower()}:{city2.lower()}"
    now = time.time()

    if _provided:
        d1 = {
            "name": city1, "aqi": int(aqi1), "category": _cat(int(aqi1)),
            "dominant_pollutant": _DOMINANT.get(city1, "PM2.5"),
            "population": _POPULATIONS.get(city1, 0), "source": "provided",
        }
        d2 = {
            "name": city2, "aqi": int(aqi2), "category": _cat(int(aqi2)),
            "dominant_pollutant": _DOMINANT.get(city2, "PM2.5"),
            "population": _POPULATIONS.get(city2, 0), "source": "provided",
        }
    else:
        if cache_key in _cache:
            ts, data = _cache[cache_key]
            if now - ts < _CACHE_TTL:
                return data

        d1 = _resolve(city1)
        d2 = _resolve(city2)

    v1, v2 = d1["aqi"], d2["aqi"]
    diff = abs(v1 - v2)

    # Insight — always from worse city's perspective
    worse, better = (d1, d2) if v1 >= v2 else (d2, d1)
    pct_worse = round((worse["aqi"] - better["aqi"]) / max(better["aqi"], 1) * 100)

    if pct_worse < 5:
        insight = f"{worse['name']} and {better['name']} have similar air quality right now"
    else:
        insight = f"{worse['name']} air is {pct_worse}% worse than {better['name']} right now"

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
