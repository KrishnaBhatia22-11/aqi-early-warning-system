import os
import time
import requests
from datetime import datetime, date
from fastapi import APIRouter

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
PUNJAB_CITIES = ["Amritsar", "Chandigarh", "Ludhiana"]
HINDI_BELT    = ["Delhi", "Lucknow", "Kanpur"]
ALL_MONITOR   = PUNJAB_CITIES + HINDI_BELT

CITY_SLUGS = {
    "Amritsar":   "amritsar",
    "Chandigarh": "chandigarh",
    "Ludhiana":   "ludhiana",
    "Delhi":      "delhi",
    "Lucknow":    "lucknow",
    "Kanpur":     "kanpur",
}

# ── Monthly AQI baselines from training data (city_day.csv) ────
CITY_BASELINES = {
    "Delhi":      {1:175,2:150,3:130,4:120,5:115,6:110,7:100,8:105,9:120,10:175,11:210,12:185},
    "Amritsar":   {1:140,2:120,3:105,4:100,5:95, 6:90, 7:85, 8:90, 9:100,10:130,11:160,12:145},
    "Chandigarh": {1:120,2:105,3:92, 4:95, 5:88, 6:80, 7:75, 8:80, 9:90, 10:110,11:140,12:125},
    "Ludhiana":   {1:145,2:125,3:110,4:105,5:100,6:92, 7:88, 8:92, 9:105,10:135,11:165,12:150},
    "Lucknow":    {1:185,2:160,3:140,4:130,5:120,6:115,7:105,8:110,9:125,10:165,11:190,12:180},
    "Kanpur":     {1:195,2:170,3:150,4:140,5:130,6:125,7:115,8:120,9:135,10:175,11:200,12:190},
}
_DEFAULT_BL = {1:140,2:120,3:105,4:100,5:110,6:100,7:95,8:100,9:110,10:140,11:165,12:150}


def _baseline(city, month):
    return CITY_BASELINES.get(city, _DEFAULT_BL).get(month, 110)


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

    # Off-season — find next upcoming season
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


@router.get("/cropburn/status")
def get_cropburn_status():
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

    # Fetch live AQI for all monitored cities
    city_aqi_raw = {c: _fetch_aqi(c) for c in ALL_MONITOR}
    aqi_available = any(v is not None for v in city_aqi_raw.values())

    # Build per-city enriched data
    city_data = {}
    for city, aqi in city_aqi_raw.items():
        if aqi is not None:
            bl  = _baseline(city, month)
            pct = round(((aqi - bl) / bl) * 100)
            city_data[city] = {
                "aqi": aqi,
                "baseline": bl,
                "pct_above_baseline": pct,
                "spiking": aqi > bl * 1.6,
            }
        else:
            city_data[city] = None

    valid = {c: v for c, v in city_data.items() if v is not None}

    punjab_spiking    = [c for c in PUNJAB_CITIES if valid.get(c, {}).get("spiking")]
    all_spiking       = [c for c in ALL_MONITOR   if valid.get(c, {}).get("spiking")]
    delhi_spiking     = valid.get("Delhi", {}).get("spiking", False)
    early_warn_pattern = len(punjab_spiking) >= 2 and not delhi_spiking
    regional_pattern   = len(all_spiking) >= 3

    if valid:
        peak_city = max(valid, key=lambda c: valid[c]["aqi"])
        peak_aqi  = valid[peak_city]["aqi"]
        peak_pct  = valid[peak_city]["pct_above_baseline"]
    else:
        peak_city, peak_aqi, peak_pct = None, 0, 0

    wind_dir     = _wind_dir_delhi()
    wind_from_nw = wind_dir in ("NW", "NNW", "WNW") if wind_dir else False

    # Confidence score
    confidence = 0
    if season_active:             confidence += 40
    if len(punjab_spiking) >= 2:  confidence += 25
    if regional_pattern:          confidence += 20
    if wind_from_nw:              confidence += 15
    confidence = min(confidence, 100)

    if confidence >= 70:   conf_level = "HIGH"
    elif confidence >= 40: conf_level = "MEDIUM"
    elif confidence >= 20: conf_level = "LOW"
    else:                  conf_level = "NONE"

    # Status
    if not season_active or confidence < 20:
        status = "CLEAR"
    elif confidence >= 70:
        status = "EARLY_WARNING" if early_warn_pattern else "ACTIVE_BURN"
    elif confidence >= 40:
        status = "EARLY_WARNING" if early_warn_pattern else "RESIDUAL_SMOKE"
    else:
        status = "CLEAR"

    # Health warning
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

    affected = sorted(
        [c for c in valid if valid[c]["spiking"]],
        key=lambda c: valid[c]["aqi"], reverse=True
    )

    result = {
        "status":           status,
        "confidence":       confidence,
        "confidence_level": conf_level,
        "season":           season["season"],
        "season_active":    season_active,
        "aqi_data_available": aqi_available,
        "detection_signals": {
            "season_active":         season_active,
            "season_name":           season.get("name", ""),
            "season_dates":          season.get("dates", ""),
            "season_crop":           season.get("crop", ""),
            "season_states":         season.get("states", ""),
            "days_into_season":      season.get("days_into", 0),
            "days_remaining":        season.get("days_remaining", 0),
            "next_season":           season.get("next_season"),
            "next_season_start":     season.get("next_season_start"),
            "days_until_next":       season.get("days_until_next"),
            "punjab_cities_spiking": punjab_spiking,
            "north_india_affected":  len(all_spiking),
            "peak_aqi":              peak_aqi,
            "peak_city":             peak_city,
            "baseline_exceeded_pct": peak_pct,
            "wind_direction":        wind_dir,
            "wind_from_nw":          wind_from_nw,
            "early_warning_pattern": early_warn_pattern,
            "regional_pattern":      regional_pattern,
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
        "city_aqi":       city_data,
        "affected_cities": affected,
        "source":         "WAQI live AQI + seasonal calendar + OpenWeatherMap wind",
        "last_updated":   datetime.utcnow().isoformat(),
    }

    _cache[cache_key] = (now, result)
    return result
