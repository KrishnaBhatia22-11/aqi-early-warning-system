import sys
import os
from datetime import datetime
from fastapi import APIRouter

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.data.waqi_client import fetch_city_aqi

router = APIRouter()

_CITY_DEFAULTS = {
    "Delhi": 185, "Mumbai": 95, "Kolkata": 140, "Chennai": 75,
    "Bengaluru": 85, "Hyderabad": 90, "Ahmedabad": 130, "Jaipur": 145,
    "Lucknow": 160, "Patna": 175, "Chandigarh": 105, "Amritsar": 120,
    "Guwahati": 95, "Bhopal": 120, "Pune": 100, "Nagpur": 125,
    "Surat": 115, "Kanpur": 180, "Varanasi": 170,
    "Coimbatore": 65, "Kochi": 70, "Thiruvananthapuram": 55,
    "Visakhapatnam": 80, "Ranchi": 120, "Bhubaneswar": 110, "Indore": 125,
}

_CATEGORY_COLORS = {
    "Good":         "#22c55e",
    "Satisfactory": "#84cc16",
    "Moderate":     "#f59e0b",
    "Poor":         "#FF6B00",
    "Very Poor":    "#ef4444",
    "Severe":       "#c2002a",
}

_MESSAGES = {
    "Good":         "Air quality is Good today. Enjoy your outdoor activities.",
    "Satisfactory": "Air quality is Satisfactory today. Mostly safe for outdoor activities.",
    "Moderate":     "Air quality is Moderate today. Sensitive groups should limit exertion.",
    "Poor":         "Air quality is Poor today. Avoid prolonged outdoor exposure.",
    "Very Poor":    "Air quality is Very Poor today. Stay indoors if possible.",
    "Severe":       "Air quality is Severe — health emergency. Stay indoors completely.",
}


def _cat(aqi: float) -> str:
    if aqi <= 50:  return "Good"
    if aqi <= 100: return "Satisfactory"
    if aqi <= 200: return "Moderate"
    if aqi <= 300: return "Poor"
    if aqi <= 400: return "Very Poor"
    return "Severe"


@router.get("/share/{city}")
def get_share_card(city: str):
    canon = city.strip().title()
    now   = datetime.now()

    # Try live WAQI data; fall back to seasonal default
    result  = fetch_city_aqi(canon)
    if result.get("success") and result.get("aqi"):
        aqi      = int(result["aqi"])
        pollutant = result.get("dominant_pollutant") or _dominant(result)
        source   = "live"
    else:
        aqi      = _CITY_DEFAULTS.get(canon, 150)
        pollutant = "PM2.5"
        source   = "estimate"

    category = _cat(aqi)
    cigs     = round(aqi / (22 * 24), 1)   # per 1 hour outside

    return {
        "city":                 canon,
        "aqi":                  aqi,
        "category":             category,
        "category_color":       _CATEGORY_COLORS.get(category, "#FF6B00"),
        "date":                 now.strftime("%d %b %Y"),
        "time":                 now.strftime("%H:%M IST"),
        "cigarette_equivalent": cigs,
        "dominant_pollutant":   pollutant,
        "message":              _MESSAGES.get(category, f"{canon} air quality is {category} today."),
        "url":                  "aqi-early-warning-system.vercel.app",
        "source":               source,
    }


def _dominant(result: dict) -> str:
    """Pick the pollutant with the highest reading from WAQI response."""
    candidates = {
        "PM2.5": result.get("pm25") or 0,
        "PM10":  result.get("pm10") or 0,
        "NO2":   result.get("no2")  or 0,
        "O3":    result.get("o3")   or 0,
        "CO":    result.get("co")   or 0,
        "SO2":   result.get("so2")  or 0,
    }
    return max(candidates, key=candidates.get, default="PM2.5")
