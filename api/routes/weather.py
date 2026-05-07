import os
import time
import requests
from fastapi import APIRouter, HTTPException

router = APIRouter()

_cache: dict = {}
_CACHE_TTL = 600  # 10 minutes

_COMPASS = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]


def _wind_dir(degrees: float) -> str:
    return _COMPASS[round(degrees / 22.5) % 16]


def _condition(weather_id: int) -> str:
    if weather_id < 300: return "Thunderstorm"
    if weather_id < 400: return "Drizzle"
    if weather_id < 600: return "Rain"
    if weather_id < 700: return "Snow"
    if weather_id in (741, 721, 731, 751, 761, 762): return "Haze"
    if weather_id < 800: return "Haze"
    if weather_id == 800: return "Clear"
    if weather_id <= 802: return "Partly Cloudy"
    return "Cloudy"


def _insight(humidity: float, wind_kmh: float, rainfall: float, temp: float) -> str:
    if rainfall > 0:
        return "Rainfall washing out particulates — AQI will improve in 1–2 hours"
    if wind_kmh > 20:
        return "Strong winds dispersing pollutants — AQI likely improving"
    if humidity > 80:
        return "High humidity trapping pollutants — expect AQI to worsen"
    if temp > 40:
        return "Heat building ozone — O3 levels elevated"
    return "Stable weather conditions — AQI unlikely to change rapidly"


@router.get("/weather/{city}")
def get_weather(city: str):
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        raise HTTPException(503, detail="Weather service not configured (OPENWEATHER_API_KEY missing)")

    cache_key = city.lower().strip()
    now = time.time()
    if cache_key in _cache:
        ts, data = _cache[cache_key]
        if now - ts < _CACHE_TTL:
            return data

    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city},IN&appid={api_key}&units=metric"
    )

    try:
        resp = requests.get(url, timeout=10)
    except requests.exceptions.Timeout:
        raise HTTPException(504, detail=f"Weather service timed out for '{city}'")
    except requests.exceptions.RequestException as e:
        raise HTTPException(502, detail=f"Weather service error: {e}")

    if resp.status_code == 401:
        raise HTTPException(503, detail="Weather service authentication failed")
    if resp.status_code == 404:
        raise HTTPException(404, detail=f"City '{city}' not found in weather service")
    if resp.status_code != 200:
        raise HTTPException(502, detail=f"Weather service returned HTTP {resp.status_code}")

    raw = resp.json()
    main    = raw.get("main", {})
    wind    = raw.get("wind", {})
    rain    = raw.get("rain", {})
    weather = raw.get("weather", [{}])[0]

    wind_ms   = wind.get("speed", 0.0)
    wind_kmh  = round(wind_ms * 3.6, 1)
    humidity  = main.get("humidity", 0)
    temp      = round(main.get("temp", 0.0))
    feels     = round(main.get("feels_like", 0.0))
    rainfall  = rain.get("1h", 0.0)

    result = {
        "city":          city,
        "temperature":   temp,
        "humidity":      humidity,
        "wind_speed":    wind_kmh,
        "wind_direction": _wind_dir(wind.get("deg", 0.0)),
        "rainfall_1h":   rainfall,
        "condition":     _condition(weather.get("id", 800)),
        "feels_like":    feels,
        "aqi_insight":   _insight(humidity, wind_kmh, rainfall, temp),
        "source":        "OpenWeatherMap",
    }

    _cache[cache_key] = (now, result)
    return result
