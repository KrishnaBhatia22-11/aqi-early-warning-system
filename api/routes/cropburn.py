import os
import time
import requests
from datetime import datetime, date, timedelta, timezone
from fastapi import APIRouter
from sqlalchemy import select, func

from api.database import AsyncSessionLocal
from api.models import AQIReading

router = APIRouter()

WAQI_TOKEN = os.getenv("WAQI_TOKEN", "")
OWM_KEY    = os.getenv("OPENWEATHER_API_KEY", "")

_cache = {}
_CACHE_TTL = 300  # 5 min

# ── Seasonal calendar ──────────────────────────────────────────
SEASONS = {
    "PADDY": {
        "start": (10, 1), "end": (11, 30),
        "name":  "Paddy stubble burning season",
        "dates": "Oct 1 – Nov 30",
        "crop":  "paddy (rice)",
        "states": "Punjab & Haryana",
    },
    "WHEAT": {
        "start": (4, 15), "end": (5, 31),
        "name":  "Wheat stubble burning season",
        "dates": "Apr 15 – May 31",
        "crop":  "wheat",
        "states": "Punjab & Haryana",
    },
}

# ── Monitored cities ───────────────────────────────────────────
PUNJAB_CITIES   = ["Amritsar", "Ludhiana", "Jalandhar", "Chandigarh", "Patiala"]
DOWNWIND_CITIES = ["Delhi", "Lucknow", "Kanpur", "Agra", "Noida", "Ghaziabad"]
ALL_MONITOR     = PUNJAB_CITIES + DOWNWIND_CITIES

CITY_SLUGS = {
    "Amritsar":   "amritsar",
    "Chandigarh": "chandigarh",
    "Ludhiana":   "ludhiana",
    "Jalandhar":  "jalandhar",
    "Patiala":    "patiala",
    "Delhi":      "delhi",
    "Lucknow":    "lucknow",
    "Kanpur":     "kanpur",
    "Agra":       "agra",
    "Noida":      "noida",
    "Ghaziabad":  "ghaziabad",
}


def _season_info(month, day):
    cur = month * 100 + day
    for key, s in SEASONS.items():
        sm, sd = s["start"]
        em, ed = s["end"]
        if sm * 100 + sd <= cur <= em * 100 + ed:
            today_d   = date.today()
            s_start   = date(today_d.year, sm, sd)
            s_end     = date(today_d.year, em, ed)
            into      = max(1, (today_d - s_start).days + 1)
            remaining = max(0, (s_end - today_d).days)
            return {
                "season": key, "active": True,
                "name": s["name"], "dates": s["dates"],
                "crop": s["crop"], "states": s["states"],
                "days_into": into, "days_remaining": remaining,
            }

    today_d  = date.today()
    upcoming = []
    for key, s in SEASONS.items():
        sm, sd = s["start"]
        nxt = date(today_d.year, sm, sd)
        if nxt <= today_d:
            nxt = date(today_d.year + 1, sm, sd)
        upcoming.append((nxt, key, s))
    upcoming.sort()
    nxt_date, nxt_key, nxt_s = upcoming[0]
    return {
        "season": "OFF_SEASON", "active": False,
        "name": "Off season", "dates": "", "crop": "", "states": "",
        "days_into": 0, "days_remaining": 0,
        "next_season":       nxt_key,
        "next_season_name":  nxt_s["name"],
        "next_season_dates": nxt_s["dates"],
        "next_season_start": nxt_date.strftime("%b %d"),
        "days_until_next":   (nxt_date - today_d).days,
    }


def _fetch_aqi(city):
    if not WAQI_TOKEN:
        return None
    slug = CITY_SLUGS.get(city, city.lower())
    try:
        resp = requests.get(
            f"https://api.waqi.info/feed/{slug}/?token={WAQI_TOKEN}",
            timeout=8
        )
        d = resp.json()
        if d.get("status") == "ok":
            aqi = d["data"].get("aqi")
            if isinstance(aqi, (int, float)) and aqi > 0:
                return int(aqi)
    except Exception:
        pass
    return None


def _wind_dir_delhi():
    if not OWM_KEY:
        return None
    try:
        resp = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q=Delhi,IN&appid={OWM_KEY}&units=metric",
            timeout=6
        )
        if resp.status_code == 200:
            deg = resp.json().get("wind", {}).get("deg")
            if deg is not None:
                dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
                        "S","SSW","SW","WSW","W","WNW","NW","NNW"]
                return dirs[round(float(deg) / 22.5) % 16]
    except Exception:
        pass
    return None


async def _query_city_spikes(cities: list):
    """
    Query 24h avg and 7-day avg AQI per city from own DB.
    Returns (dict of city -> spike info, error_str or None).
    Cities with no 24h data are skipped gracefully.
    Falls back to ({}, error) on any DB failure.
    """
    try:
        now        = datetime.now(timezone.utc)
        cutoff_24h = now - timedelta(hours=24)
        cutoff_7d  = now - timedelta(days=7)

        async with AsyncSessionLocal() as session:
            res_24h = await session.execute(
                select(
                    AQIReading.city,
                    func.avg(AQIReading.aqi).label("avg_aqi"),
                    func.count(AQIReading.id).label("cnt"),
                )
                .where(
                    AQIReading.city.in_(cities),
                    AQIReading.timestamp >= cutoff_24h,
                )
                .group_by(AQIReading.city)
            )
            rows_24h = {r.city: {"avg": float(r.avg_aqi), "cnt": r.cnt} for r in res_24h}

            res_7d = await session.execute(
                select(
                    AQIReading.city,
                    func.avg(AQIReading.aqi).label("avg_aqi"),
                    func.count(AQIReading.id).label("cnt"),
                )
                .where(
                    AQIReading.city.in_(cities),
                    AQIReading.timestamp >= cutoff_7d,
                )
                .group_by(AQIReading.city)
            )
            rows_7d = {r.city: {"avg": float(r.avg_aqi), "cnt": r.cnt} for r in res_7d}

        result = {}
        for city in cities:
            d24 = rows_24h.get(city)
            d7d = rows_7d.get(city)
            # Skip cities with no 24h data or no 7-day baseline
            if not d24 or not d7d or d24["cnt"] == 0 or d7d["cnt"] == 0:
                continue
            current_avg  = d24["avg"]
            baseline_avg = d7d["avg"]
            if not baseline_avg or baseline_avg <= 0:
                continue
            pct_above = ((current_avg - baseline_avg) / baseline_avg) * 100
            result[city] = {
                "current_avg":  round(current_avg, 1),
                "baseline_avg": round(baseline_avg, 1),
                "pct_above":    round(pct_above, 1),
                "spiking_20":   pct_above > 20,
                "spiking_15":   pct_above > 15,
            }

        return result, None

    except Exception as e:
        return {}, str(e)


@router.get("/cropburn/status")
async def get_cropburn_status():
    cache_key = "cropburn"
    now = time.time()
    if cache_key in _cache:
        ts, data = _cache[cache_key]
        if now - ts < _CACHE_TTL:
            return data

    today = datetime.utcnow()
    month, day = today.month, today.day

    season        = _season_info(month, day)
    season_active = season["active"]

    # ── Query own DB for spike signals ────────────────────────
    db_data, db_error = await _query_city_spikes(ALL_MONITOR)
    db_available = len(db_data) > 0

    # ── Signal 1: 2+ Punjab cities >20% above 7-day baseline (40 pts) ──
    punjab_spiking = [
        c for c in PUNJAB_CITIES
        if db_data.get(c, {}).get("spiking_20", False)
    ]
    signal1 = len(punjab_spiking) >= 2

    # ── Signal 2: 3+ downwind cities >15% above 7-day baseline (35 pts) ─
    downwind_spiking = [
        c for c in DOWNWIND_CITIES
        if db_data.get(c, {}).get("spiking_15", False)
    ]
    signal2 = len(downwind_spiking) >= 3

    # ── Signal 3: Burning season active (25 pts) ──────────────
    signal3 = season_active

    # ── Confidence: sum of confirmed signals, max 100 ─────────
    confidence = 0
    if signal1: confidence += 40
    if signal2: confidence += 35
    if signal3: confidence += 25
    confidence = min(confidence, 100)

    if confidence >= 70:   conf_level = "HIGH"
    elif confidence >= 40: conf_level = "MEDIUM"
    elif confidence >= 20: conf_level = "LOW"
    else:                  conf_level = "NONE"

    # ── Fetch live WAQI AQI for display ───────────────────────
    city_aqi_raw = {c: _fetch_aqi(c) for c in ALL_MONITOR}
    aqi_available = any(v is not None for v in city_aqi_raw.values())

    city_data = {}
    for city in ALL_MONITOR:
        live_aqi = city_aqi_raw.get(city)
        db_city  = db_data.get(city)
        if live_aqi is not None or db_city:
            city_data[city] = {
                "aqi":              live_aqi,
                "db_current_avg":   db_city["current_avg"]  if db_city else None,
                "db_baseline_avg":  db_city["baseline_avg"] if db_city else None,
                "pct_above_baseline": db_city["pct_above"]  if db_city else None,
                "spiking": (
                    db_city["spiking_20"] if city in PUNJAB_CITIES and db_city else
                    db_city["spiking_15"] if db_city else False
                ),
            }
        else:
            city_data[city] = None

    all_spiking          = punjab_spiking + downwind_spiking
    north_india_affected = len(all_spiking)

    wind_dir     = _wind_dir_delhi()
    wind_from_nw = wind_dir in ("NW", "NNW", "WNW") if wind_dir else False

    early_warn_pattern = len(punjab_spiking) >= 2 and "Delhi" not in downwind_spiking
    regional_pattern   = north_india_affected >= 3

    if not season_active or confidence < 20:
        status = "CLEAR"
    elif confidence >= 70:
        status = "EARLY_WARNING" if early_warn_pattern else "ACTIVE_BURN"
    elif confidence >= 40:
        status = "EARLY_WARNING" if early_warn_pattern else "RESIDUAL_SMOKE"
    else:
        status = "CLEAR"

    HW = {
        "ACTIVE_BURN":    ("CRITICAL",
                           "Crop burning smoke detected across North India",
                           "Stay indoors. Use N95 mask if going outside. Avoid all outdoor exercise."),
        "EARLY_WARNING":  ("HIGH",
                           "Crop burning detected in Punjab — smoke expected to reach downstream cities within 24–48 hours",
                           "Monitor AQI closely. Prepare N95 masks. Limit outdoor exposure."),
        "RESIDUAL_SMOKE": ("MODERATE",
                           "Residual crop burning smoke present. Season winding down.",
                           "Wear a mask outdoors. Avoid prolonged outdoor activity."),
        "CLEAR":          ("LOW",
                           "No crop burning detected. Air quality within seasonal norms.",
                           "No special precautions needed."),
    }
    hw_level, hw_msg, hw_action = HW[status]

    result = {
        "status":             status,
        "confidence":         confidence,
        "confidence_level":   conf_level,
        "season":             season["season"],
        "season_active":      season_active,
        "aqi_data_available": aqi_available,
        "db_data_available":  db_available,
        "db_error":           db_error,
        "detection_signals": {
            "season_active":           season_active,
            "season_name":             season.get("name", ""),
            "season_dates":            season.get("dates", ""),
            "season_crop":             season.get("crop", ""),
            "season_states":           season.get("states", ""),
            "days_into_season":        season.get("days_into", 0),
            "days_remaining":          season.get("days_remaining", 0),
            "next_season":             season.get("next_season"),
            "next_season_start":       season.get("next_season_start"),
            "days_until_next":         season.get("days_until_next"),
            "punjab_cities_spiking":   punjab_spiking,
            "downwind_cities_spiking": downwind_spiking,
            "north_india_affected":    north_india_affected,
            "wind_direction":          wind_dir,
            "wind_from_nw":            wind_from_nw,
            "early_warning_pattern":   early_warn_pattern,
            "regional_pattern":        regional_pattern,
            "signal1_punjab_active":   signal1,
            "signal2_downwind_active": signal2,
            "signal3_season_active":   signal3,
        },
        "health_warning": {
            "level":   hw_level,
            "message": hw_msg,
            "action":  hw_action,
            "vulnerable_groups": [
                {"icon": "👶", "group": "Children",       "advice": "No outdoor school activities"},
                {"icon": "👴", "group": "Elderly",         "advice": "Stay indoors completely"},
                {"icon": "🫁", "group": "Asthma patients", "advice": "Pre-medicate before any outdoor exposure"},
                {"icon": "❤️", "group": "Heart patients",  "advice": "Cancel outdoor exercise"},
                {"icon": "🤰", "group": "Pregnant",        "advice": "Avoid outdoor exposure entirely"},
            ],
        },
        "city_aqi":        city_data,
        "affected_cities": all_spiking,
        "data_source":     "Own DB + WAQI live + seasonal calendar",
        "last_updated":    datetime.utcnow().isoformat(),
    }

    _cache[cache_key] = (now, result)
    return result
