import requests
import time
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.settings import WAQI_API_KEY, CITY_COORDS

# Simple in-memory cache so we don't hammer the API
# If same city requested within 10 minutes, return cached result
_cache = {}
CACHE_DURATION = 600  # 10 minutes in seconds


# ─────────────────────────────────────────────
# CORE FUNCTION — fetch live AQI for any city
# ─────────────────────────────────────────────
def fetch_city_aqi(city_name):
    """
    Fetches live AQI data from WAQI API for a given city.
    Returns a dict with AQI, pollutants, and status.
    """
    # Check cache first
    now = time.time()
    if city_name in _cache:
        cached_time, cached_data = _cache[city_name]
        if now - cached_time < CACHE_DURATION:
            print(f"[Cache] Returning cached data for {city_name}")
            return cached_data

    # Build API URL
    url = f"https://api.waqi.info/feed/{city_name}/?token={WAQI_API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        data     = response.json()

        if data['status'] != 'ok':
            return {
                "success": False,
                "city":    city_name,
                "error":   f"API returned status: {data['status']}"
            }

        station  = data['data']
        aqi      = station.get('aqi', None)

        # Extract individual pollutant readings if available
        iaqi     = station.get('iaqi', {})
        pm25     = iaqi.get('pm25', {}).get('v', None)
        pm10     = iaqi.get('pm10', {}).get('v', None)
        no2      = iaqi.get('no2',  {}).get('v', None)
        co       = iaqi.get('co',   {}).get('v', None)
        so2      = iaqi.get('so2',  {}).get('v', None)
        o3       = iaqi.get('o3',   {}).get('v', None)

        result = {
            "success":      True,
            "city":         city_name,
            "aqi":          aqi,
            "category":     categorize_aqi(aqi),
            "color":        aqi_color(aqi),
            "pm25":         pm25,
            "pm10":         pm10,
            "no2":          no2,
            "co":           co,
            "so2":          so2,
            "o3":           o3,
            "station_name": station.get('city', {}).get('name', city_name),
            "last_updated": station.get('time', {}).get('s', 'Unknown'),
        }

        # Store in cache
        _cache[city_name] = (now, result)
        return result

    except requests.exceptions.Timeout:
        return {"success": False, "city": city_name, "error": "Request timed out"}
    except Exception as e:
        return {"success": False, "city": city_name, "error": str(e)}


# ─────────────────────────────────────────────
# Fetch AQI for ALL cities on the map at once
# Used to populate the Folium map in the UI
# ─────────────────────────────────────────────
def fetch_all_cities():
    """
    Fetches live AQI for every city in CITY_COORDS.
    Returns a list of result dicts.
    """
    results = []
    for city in CITY_COORDS.keys():
        print(f"Fetching AQI for {city}...")
        result = fetch_city_aqi(city)
        result['lat'] = CITY_COORDS[city]['lat']
        result['lon'] = CITY_COORDS[city]['lon']
        results.append(result)
        time.sleep(0.3)  # small delay to be polite to the API
    return results


# ─────────────────────────────────────────────
# AQI category — India CPCB standard
# ─────────────────────────────────────────────
def categorize_aqi(aqi):
    if aqi is None:
        return "Unknown"
    try:
        aqi = int(aqi)
        if aqi <= 50:   return "Good"
        if aqi <= 100:  return "Satisfactory"
        if aqi <= 200:  return "Moderate"
        if aqi <= 300:  return "Poor"
        if aqi <= 400:  return "Very Poor"
        return "Severe"
    except:
        return "Unknown"


# ─────────────────────────────────────────────
# Color for map markers and UI badges
# ─────────────────────────────────────────────
def aqi_color(aqi):
    if aqi is None:
        return "gray"
    try:
        aqi = int(aqi)
        if aqi <= 50:   return "green"
        if aqi <= 100:  return "lightgreen"
        if aqi <= 200:  return "orange"
        if aqi <= 300:  return "red"
        if aqi <= 400:  return "darkred"
        return "purple"
    except:
        return "gray"