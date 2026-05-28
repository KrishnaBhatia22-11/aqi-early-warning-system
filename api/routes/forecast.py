import hashlib
import random
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
from fastapi import APIRouter, Request
from pydantic import BaseModel
from api.limiter import limiter

router = APIRouter()

_cache: dict = {}
CACHE_TTL = 3600  # seconds

# ── Diurnal profile: 24-hour multiplier for Indian metro cities
# Peaks: 07-09 (morning rush) and 17-19 (evening rush)
# Trough: 02-03 (overnight minimum)
# Midday dip: 12-13 (boundary layer at max height)
_DIURNAL_RAW = [
    0.87, 0.85, 0.83, 0.83, 0.86, 0.92,  # 00–05
    1.05, 1.28, 1.32, 1.20, 1.08, 1.00,  # 06–11
    0.95, 0.93, 0.97, 1.05, 1.15, 1.30,  # 12–17
    1.35, 1.25, 1.10, 1.00, 0.93, 0.89,  # 18–23
]
_diurnal_mean = sum(_DIURNAL_RAW) / 24
DIURNAL = [v / _diurnal_mean for v in _DIURNAL_RAW]

# Monthly seasonal multiplier (India climatology)
SEASONAL = {
    1: 1.25, 2: 1.20, 3: 1.05, 4: 1.05, 5: 1.08,
    6: 0.90, 7: 0.82, 8: 0.78, 9: 0.88, 10: 1.05,
    11: 1.20, 12: 1.35,
}

# Day-of-week multiplier (0=Mon … 6=Sun)
DOW = {0: 1.02, 1: 1.02, 2: 1.02, 3: 1.02, 4: 1.05, 5: 0.92, 6: 0.85}

# Summer 2026 researched baseline AQI — used when WAQI live data is unavailable
CITY_DEFAULTS = {
    "Delhi": 185, "Mumbai": 95, "Kolkata": 140, "Chennai": 75,
    "Bengaluru": 85, "Hyderabad": 90, "Ahmedabad": 130, "Jaipur": 145,
    "Lucknow": 160, "Patna": 175, "Chandigarh": 105, "Amritsar": 120,
    "Guwahati": 95, "Thiruvananthapuram": 55, "Visakhapatnam": 80,
    "Coimbatore": 65, "Kochi": 70, "Bhopal": 120,
}

CITY_NORM = {
    "bangalore": "Bengaluru", "bengalore": "Bengaluru", "bengaluru": "Bengaluru",
    "cochin": "Kochi", "ernakulam": "Kochi",
    "thiruvananthapuram": "Thiruvananthapuram", "trivandrum": "Thiruvananthapuram",
    "vizag": "Visakhapatnam", "visakhapatnam": "Visakhapatnam",
    "delhi": "Delhi", "mumbai": "Mumbai", "kolkata": "Kolkata",
    "chennai": "Chennai", "hyderabad": "Hyderabad", "ahmedabad": "Ahmedabad",
    "jaipur": "Jaipur", "lucknow": "Lucknow", "patna": "Patna",
    "chandigarh": "Chandigarh", "amritsar": "Amritsar", "guwahati": "Guwahati",
    "coimbatore": "Coimbatore", "kochi": "Kochi", "bhopal": "Bhopal",
}


def _cat(aqi: float) -> str:
    if aqi <= 50:  return "Good"
    if aqi <= 100: return "Satisfactory"
    if aqi <= 200: return "Moderate"
    if aqi <= 300: return "Poor"
    if aqi <= 400: return "Very Poor"
    return "Severe"


def _recommendation(peak: float, trend: str) -> str:
    if peak > 400:
        return "Hazardous air quality expected. Stay indoors all day and seal windows."
    if peak > 300:
        if trend == "RISING":
            return "Severe pollution rising throughout the day. Avoid all outdoor exposure and wear an N95 mask."
        return "Very poor air quality forecast. Avoid outdoor activities. N95 mask mandatory if going out."
    if peak > 200:
        if trend == "RISING":
            return "Air quality will worsen significantly. Limit outdoor activities to morning hours only."
        return "Poor air quality expected. Sensitive groups should stay indoors and limit outdoor exertion."
    if peak > 100:
        return "Moderate pollution forecast. Sensitive individuals should avoid prolonged outdoor activities."
    if peak > 50:
        return "Satisfactory air quality ahead. Most activities are safe; sensitive groups should take brief breaks."
    return "Clean air forecast for the next 24 hours. Enjoy outdoor activities freely."


class ForecastRequest(BaseModel):
    city: str
    base_aqi: Optional[float] = None


@router.post("/forecast")
@limiter.limit("20/minute")
def forecast_aqi(req: ForecastRequest, request: Request):
    city_input = req.city.strip()
    norm_city = CITY_NORM.get(city_input.lower(), city_input)
    now = datetime.now()
    now_ts = now.timestamp()

    # Cache key: city + current hour + base_aqi rounded to nearest 10
    base_bucket = round((req.base_aqi or 0) / 10) * 10
    cache_key = f"{norm_city.lower()}_{now.strftime('%Y%m%d%H')}_{base_bucket}"
    entry = _cache.get(cache_key)
    if entry and (now_ts - entry["ts"]) < CACHE_TTL:
        return entry["data"]

    # Determine base AQI and source label
    if req.base_aqi and 1.0 <= req.base_aqi <= 500.0:
        base = float(req.base_aqi)
        base_aqi_source = "live_waqi"
    else:
        base = float(CITY_DEFAULTS.get(norm_city, 150))
        base_aqi_source = "seasonal_estimate"

    seasonal_mult = SEASONAL.get(now.month, 1.0)
    dow_mult = DOW.get(now.weekday(), 1.0)

    # Back-calculate neutral_base so the forecast anchors at base at the current hour
    combined_mult = DIURNAL[now.hour] * seasonal_mult * dow_mult
    neutral_base = max(10.0, base / combined_mult)

    # Reproducible noise: seeded by city + date so same-day calls give same pattern
    seed_int = int(
        hashlib.md5(f"{norm_city.lower()}_{now.strftime('%Y%m%d')}".encode()).hexdigest()[:8], 16
    )
    rng = random.Random(seed_int)

    base_hour_dt = now.replace(minute=0, second=0, microsecond=0)
    items = []

    for i in range(24):
        hour_dt = base_hour_dt + timedelta(hours=i)
        h = hour_dt.hour

        raw = neutral_base * DIURNAL[h] * seasonal_mult * dow_mult
        raw = max(0.0, raw + rng.gauss(0, 0.03 * raw))  # 3% sigma noise

        # Confidence band: ±8% at hour 0, expanding linearly to ±28% at hour 23
        conf_pct = 0.08 + 0.20 * (i / 23)
        upper = min(500.0, raw * (1.0 + conf_pct))
        lower = max(0.0, raw * (1.0 - conf_pct))

        aqi_v = int(round(min(500, max(0, raw))))

        items.append({
            "hour":       hour_dt.strftime("%H:%M"),
            "date_label": hour_dt.strftime("%d %b"),
            "aqi":        aqi_v,
            "upper":      int(round(upper)),
            "lower":      int(round(lower)),
            "category":   _cat(aqi_v),
            "confidence": int(round((1.0 - conf_pct) * 100)),
        })

    vals = [it["aqi"] for it in items]
    peak_i = int(np.argmax(vals))
    low_i  = int(np.argmin(vals))
    peak   = {"hour": items[peak_i]["hour"], "aqi": vals[peak_i], "category": items[peak_i]["category"]}
    low    = {"hour": items[low_i]["hour"],  "aqi": vals[low_i],  "category": items[low_i]["category"]}

    mean_aqi = int(round(sum(vals) / 24))
    diff     = sum(vals[12:]) / 12 - sum(vals[:12]) / 12
    trend    = "RISING" if diff > 10 else ("FALLING" if diff < -10 else "STABLE")

    peak_cat = _cat(peak["aqi"])
    low_cat  = _cat(low["aqi"])
    severity = f"{low_cat} to {peak_cat}" if low_cat != peak_cat else peak_cat

    result = {
        "city":              city_input,
        "generated_at":      now.isoformat(),
        "forecast":          items,
        "peak":              peak,
        "low":               low,
        "trend":             trend,
        "mean_aqi":          mean_aqi,
        "severity_forecast": severity,
        "recommendation":    _recommendation(peak["aqi"], trend),
        "base_aqi_source":   base_aqi_source,
        "base_aqi":          int(round(base)),
    }

    _cache[cache_key] = {"ts": now_ts, "data": result}
    return result
