import requests
import time
import sys
import os
import statistics
import threading
from concurrent.futures import ThreadPoolExecutor

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.settings import WAQI_API_KEY, CITY_COORDS

_cache = {}
CACHE_DURATION = 900  # 15 minutes


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def fetch_city_aqi(city_name):
    """
    Three-layer resilient fetch for a single city:
      Layer 1 — WAQI multi-station average
      Layer 2 — CPCB direct scraper
      Layer 3 — Last cached value (never return empty)
    """
    now = time.time()

    # Return fresh cache immediately
    if city_name in _cache:
        cached_time, cached_data = _cache[city_name]
        if now - cached_time < CACHE_DURATION:
            return cached_data

    # Try all layers
    result = _fetch_waqi_multi(city_name) or _fetch_cpcb(city_name) or _fetch_waqi_single(city_name)

    if result and result.get('success'):
        _cache[city_name] = (now, result)
        return result

    # Layer 3 — stale cache is better than nothing
    if city_name in _cache:
        _, stale = _cache[city_name]
        out = dict(stale)
        out['source'] = out.get('source', '') + ' (CACHED)'
        return out

    return {"success": False, "city": city_name, "error": "No data available from any source"}


def fetch_all_cities():
    """
    Fetch all 50+ cities in parallel.
    Returns list of result dicts with lat/lon appended.
    """
    cities_list = list(CITY_COORDS.keys())

    def fetch_one(city):
        result = fetch_city_aqi(city)
        if result:
            result = dict(result)
            result['lat'] = CITY_COORDS[city]['lat']
            result['lon'] = CITY_COORDS[city]['lon']
        return result

    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(fetch_one, cities_list))

    return [r for r in results if r is not None]


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 1 — WAQI multi-station average
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_waqi_multi(city_name):
    """
    Search WAQI for all stations in city, fetch in parallel,
    remove outliers, apply freshness weights, return averaged result.
    """
    try:
        search_url = f"https://api.waqi.info/search/?token={WAQI_API_KEY}&keyword={city_name}"
        resp = requests.get(search_url, timeout=10)
        data = resp.json()

        if data.get('status') != 'ok' or not data.get('data'):
            return None

        city_lower = city_name.lower()
        stations_raw = data['data']

        # Filter stations whose name contains the city name
        relevant_uids = [
            s['uid'] for s in stations_raw
            if city_lower in (s.get('station', {}).get('name', '') or '').lower()
        ]
        # Fallback: accept top results if name filter returned nothing
        if not relevant_uids:
            relevant_uids = [s['uid'] for s in stations_raw[:8]]
        if not relevant_uids:
            return None

        # Fetch all matching stations in parallel
        def fetch_uid(uid):
            try:
                r = requests.get(
                    f"https://api.waqi.info/feed/@{uid}/?token={WAQI_API_KEY}",
                    timeout=8,
                )
                d = r.json()
                if d.get('status') == 'ok':
                    return d['data']
            except Exception:
                pass
            return None

        now_unix = time.time()
        with ThreadPoolExecutor(max_workers=min(len(relevant_uids), 10)) as ex:
            raw_results = list(ex.map(fetch_uid, relevant_uids))

        # Parse station data with freshness weighting
        station_data = []
        for r in raw_results:
            if r is None:
                continue
            aqi_raw = r.get('aqi')
            if aqi_raw is None or str(aqi_raw) == '-':
                continue
            try:
                aqi = int(aqi_raw)
            except (ValueError, TypeError):
                continue
            if aqi <= 0 or aqi > 999:
                continue

            ts = r.get('time', {}).get('v')
            hours_ago = (now_unix - ts) / 3600 if ts else 0

            if hours_ago > 4:
                continue
            elif hours_ago > 2:
                weight = 0.4
            elif hours_ago > 1:
                weight = 0.7
            else:
                weight = 1.0

            iaqi = r.get('iaqi', {})
            station_data.append({
                'name':    r.get('city', {}).get('name', 'Unknown'),
                'aqi':     aqi,
                'weight':  weight,
                'updated': r.get('time', {}).get('s', 'Unknown'),
                'pm25':    iaqi.get('pm25', {}).get('v'),
                'pm10':    iaqi.get('pm10', {}).get('v'),
                'no2':     iaqi.get('no2',  {}).get('v'),
                'co':      iaqi.get('co',   {}).get('v'),
                'so2':     iaqi.get('so2',  {}).get('v'),
                'o3':      iaqi.get('o3',   {}).get('v'),
            })

        if not station_data:
            return None

        # Remove outliers: |aqi - median| > 100
        if len(station_data) >= 3:
            med = statistics.median(s['aqi'] for s in station_data)
            station_data = [s for s in station_data if abs(s['aqi'] - med) <= 100]

        if not station_data:
            return None

        # Weighted average
        total_w  = sum(s['weight'] for s in station_data)
        city_aqi = round(sum(s['aqi'] * s['weight'] for s in station_data) / total_w)

        n              = len(station_data)
        cleanest       = min(station_data, key=lambda s: s['aqi'])
        most_polluted  = max(station_data, key=lambda s: s['aqi'])

        if n >= 8:   quality = "HIGH"
        elif n >= 4: quality = "MEDIUM"
        elif n >= 2: quality = "LOW"
        else:        quality = "SINGLE"

        # Best pollutants: from the freshest station
        best = max(station_data, key=lambda s: s['weight'])

        return {
            'success':             True,
            'city':                city_name,
            'aqi':                 city_aqi,
            'category':            categorize_aqi(city_aqi),
            'color':               aqi_color(city_aqi),
            'pm25':                best.get('pm25'),
            'pm10':                best.get('pm10'),
            'no2':                 best.get('no2'),
            'co':                  best.get('co'),
            'so2':                 best.get('so2'),
            'o3':                  best.get('o3'),
            'station_name':        city_name,
            'station_count':       n,
            'stations':            sorted(station_data, key=lambda s: s['aqi'], reverse=True),
            'cleanest_area':       cleanest['name'],
            'cleanest_aqi':        cleanest['aqi'],
            'most_polluted_area':  most_polluted['name'],
            'most_polluted_aqi':   most_polluted['aqi'],
            'city_spread':         most_polluted['aqi'] - cleanest['aqi'],
            'data_quality':        quality,
            'source':              f"WAQI — average of {n} CPCB stations",
            'last_updated':        station_data[0].get('updated', 'Unknown'),
        }

    except Exception as e:
        print(f"[WAQI Multi] {city_name}: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 2 — CPCB direct scraper
# ─────────────────────────────────────────────────────────────────────────────

_cpcb_cache = {'data': [], 'ts': 0}
_CPCB_TTL   = 3600  # CPCB bulk data cached 1 hour (changes slowly)

def _scrape_cpcb_all():
    """Fetch all-India last-hour station data from CPCB."""
    now = time.time()
    if now - _cpcb_cache['ts'] < _CPCB_TTL and _cpcb_cache['data']:
        return _cpcb_cache['data']
    try:
        resp = requests.post(
            "https://app.cpcbccr.com/caaqm-backend-ui/api/caaqm/getLastHourData",
            json={},
            timeout=15,
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
        )
        raw = resp.json()
        stations = raw if isinstance(raw, list) else raw.get('data', [])
        _cpcb_cache['data'] = stations
        _cpcb_cache['ts']   = now
        return stations
    except Exception as e:
        print(f"[CPCB] Scrape failed: {e}")
        return _cpcb_cache.get('data', [])


def _fetch_cpcb(city_name):
    """Layer 2: CPCB scraper fallback for a single city."""
    try:
        all_stations = _scrape_cpcb_all()
        if not all_stations:
            return None

        city_lower = city_name.lower()
        city_stations = [
            s for s in all_stations
            if city_lower in str(s.get('city',        '')).lower() or
               city_lower in str(s.get('stationName', '')).lower()
        ]
        if not city_stations:
            return None

        aqis = []
        for s in city_stations:
            raw = s.get('aqi') or s.get('AQI') or s.get('aqiValue')
            if raw:
                try:
                    aqis.append(int(float(raw)))
                except (ValueError, TypeError):
                    pass

        if not aqis:
            return None

        city_aqi = round(sum(aqis) / len(aqis))
        n        = len(aqis)

        return {
            'success':       True,
            'city':          city_name,
            'aqi':           city_aqi,
            'category':      categorize_aqi(city_aqi),
            'color':         aqi_color(city_aqi),
            'pm25':          None, 'pm10': None, 'no2': None,
            'co':            None, 'so2':  None, 'o3':  None,
            'station_name':  city_name,
            'station_count': n,
            'data_quality':  "HIGH" if n >= 8 else "MEDIUM" if n >= 4 else "LOW" if n >= 2 else "SINGLE",
            'source':        f"CPCB — average of {n} stations",
            'last_updated':  'Last hour',
        }
    except Exception as e:
        print(f"[CPCB City] {city_name}: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 1 fallback — single-station WAQI (original behaviour)
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_waqi_single(city_name):
    try:
        resp = requests.get(
            f"https://api.waqi.info/feed/{city_name}/?token={WAQI_API_KEY}",
            timeout=10,
        )
        data = resp.json()
        if data.get('status') != 'ok':
            return None

        station = data['data']
        aqi_raw = station.get('aqi')
        if aqi_raw is None or str(aqi_raw) == '-':
            return None

        aqi  = int(aqi_raw)
        iaqi = station.get('iaqi', {})

        return {
            'success':       True,
            'city':          city_name,
            'aqi':           aqi,
            'category':      categorize_aqi(aqi),
            'color':         aqi_color(aqi),
            'pm25':          iaqi.get('pm25', {}).get('v'),
            'pm10':          iaqi.get('pm10', {}).get('v'),
            'no2':           iaqi.get('no2',  {}).get('v'),
            'co':            iaqi.get('co',   {}).get('v'),
            'so2':           iaqi.get('so2',  {}).get('v'),
            'o3':            iaqi.get('o3',   {}).get('v'),
            'station_name':  station.get('city', {}).get('name', city_name),
            'station_count': 1,
            'data_quality':  'SINGLE',
            'source':        'WAQI — single station',
            'last_updated':  station.get('time', {}).get('s', 'Unknown'),
        }
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# AQI helpers
# ─────────────────────────────────────────────────────────────────────────────

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
    except Exception:
        return "Unknown"


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
    except Exception:
        return "gray"


# ─────────────────────────────────────────────────────────────────────────────
# Background cache warmup on module load
# ─────────────────────────────────────────────────────────────────────────────

def _warmup():
    print("[Cache] Background warmup starting for all cities…")
    fetch_all_cities()
    print("[Cache] Background warmup complete.")

threading.Thread(target=_warmup, daemon=True).start()
