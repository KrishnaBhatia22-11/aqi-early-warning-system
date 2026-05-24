import math
import re
import requests
import time
import sys
import os
import statistics
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.settings import WAQI_API_KEY, CITY_COORDS

_cache         = {}
CACHE_DURATION = 900   # 15 minutes
AQI_STANDARD   = "US AQI (EPA)"


# ─────────────────────────────────────────────────────────────────────────────
# Bounding boxes — prevent picking up stations from neighbouring cities
# Format: (lat_min, lat_max, lon_min, lon_max)
# Tight custom boxes for NCR and other densely-packed regions;
# all others fall back to city-centre ± DEFAULT_DELTA degrees.
# ─────────────────────────────────────────────────────────────────────────────
_DEFAULT_DELTA = 0.35  # ≈ 40 km

_BBOX_OVERRIDES = {
    "Delhi":      (28.40, 28.88, 76.84, 77.35),
    "Faridabad":  (28.35, 28.55, 77.25, 77.45),
    "Gurugram":   (28.39, 28.53, 76.95, 77.13),
    "Noida":      (28.45, 28.64, 77.30, 77.52),
    "Ghaziabad":  (28.59, 28.77, 77.35, 77.56),
    "Mumbai":     (18.87, 19.27, 72.77, 73.00),
    "Kolkata":    (22.40, 22.75, 88.20, 88.55),
    "Bengaluru":  (12.82, 13.14, 77.45, 77.75),
    "Chennai":    (12.92, 13.24, 80.13, 80.38),
    "Hyderabad":  (17.25, 17.55, 78.36, 78.60),
    "Ahmedabad":  (22.92, 23.15, 72.43, 72.68),
    "Pune":       (18.43, 18.62, 73.76, 73.97),
}


# Station name substrings to exclude per city — prevents neighbouring-city stations
# from inflating a city's average (e.g. Greater Noida stations in Noida results).
# Applied in BOTH the multi-station and single-station fetch paths, and against the
# actual feed station name (not just the search-result name, which can differ).
_STATION_NAME_BLACKLIST = {
    "Noida":  ["Greater Noida"],
    "Raipur": ["Dehradun", "Doon University"],
}


def _get_bbox(city_name):
    if city_name in _BBOX_OVERRIDES:
        return _BBOX_OVERRIDES[city_name]
    coords = CITY_COORDS.get(city_name)
    if not coords:
        return None
    lat, lon = coords['lat'], coords['lon']
    d = _DEFAULT_DELTA
    return (lat - d, lat + d, lon - d, lon + d)


def _in_bbox(bbox, geo):
    """Return True if geo [lat, lon] falls inside bbox, or if no geo info."""
    if not bbox or not geo or len(geo) < 2:
        return True
    try:
        lat, lon = float(geo[0]), float(geo[1])
        lat_min, lat_max, lon_min, lon_max = bbox
        return lat_min <= lat <= lat_max and lon_min <= lon <= lon_max
    except (TypeError, ValueError):
        return True


# India's geographic bounding box
_INDIA_BBOX = (8.0, 37.5, 68.0, 97.5)  # lat_min, lat_max, lon_min, lon_max


def _in_india(geo):
    """Return True if geo [lat, lon] is within India's bounding box, or if no coords."""
    if not geo or len(geo) < 2:
        return True
    try:
        lat, lon = float(geo[0]), float(geo[1])
        lat_min, lat_max, lon_min, lon_max = _INDIA_BBOX
        return lat_min <= lat <= lat_max and lon_min <= lon <= lon_max
    except (TypeError, ValueError):
        return True


# Short keywords matched as whole words only — prevents "pusa" matching "usa",
# "kukrail" matching "uk", etc.
_FOREIGN_KEYWORDS_WORDS = {
    "japan", "china", "france", "korea", "usa", "uk",
    "germany", "australia", "canada", "russia", "thailand",
    "vietnam", "indonesia", "malaysia", "singapore", "taiwan",
    "italia", "italy", "brazil", "brasil", "pakistan", "bangladesh",
    "prefecture", "province", "spain",
}

# Multi-word / special patterns — safe as substrings (too distinctive to false-positive)
_FOREIGN_KEYWORDS_SUBSTR = [
    "united kingdom", "united states", "hong kong",
    "kochi prefecture", "kochi-ken", "高知",
]


def _is_foreign_name(name):
    """
    Return True if the station name contains a foreign keyword.
    Short single-word keywords are matched as whole words only (word-boundary split)
    so that Indian names like 'Pusa' or 'Kukrail' are never false-positives.
    """
    lower = (name or "").lower()
    if any(s in lower for s in _FOREIGN_KEYWORDS_SUBSTR):
        return True
    tokens = set(re.split(r'[^a-z0-9]+', lower))
    tokens.discard('')
    return bool(tokens & _FOREIGN_KEYWORDS_WORDS)


def _haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km between two lat/lon points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


def _hours_since(r, now_unix):
    """
    Return how many hours ago this station's reading was taken.
    Tries time.v (Unix timestamp) first; falls back to parsing time.s string.
    Returns 0 (treat as fresh) if timestamp is absent or unparseable.
    """
    ts_unix = r.get('time', {}).get('v')
    if ts_unix:
        return (now_unix - ts_unix) / 3600

    ts_str = r.get('time', {}).get('s', '')
    if ts_str:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                ts_dt = datetime.strptime(ts_str, fmt).replace(tzinfo=timezone.utc)
                return (datetime.now(timezone.utc) - ts_dt).total_seconds() / 3600
            except (ValueError, TypeError):
                continue
    return 0


def _result_is_stale(result):
    """
    Return True if result['last_updated'] is more than 48 hours ago.
    Applied after ALL fetch layers so the single-station path is covered too.
    """
    ts = (result or {}).get('last_updated', '')
    if not ts or ts in ('Last hour', 'Unknown', ''):
        return False
    now = datetime.now(timezone.utc)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            ts_dt = datetime.strptime(ts, fmt).replace(tzinfo=timezone.utc)
            return (now - ts_dt).total_seconds() / 3600 > 48
        except (ValueError, TypeError):
            continue
    return False


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def fetch_city_aqi(city_name):
    """
    Three-layer resilient fetch:
      Layer 1 — WAQI multi-station (geo-filtered)
      Layer 2 — CPCB direct scraper
      Layer 3 — Last cached value (never empty)
    """
    now = time.time()

    if city_name in _cache:
        cached_time, cached_data = _cache[city_name]
        if now - cached_time < CACHE_DURATION:
            return cached_data

    result = _fetch_waqi_multi(city_name) or _fetch_cpcb(city_name) or _fetch_waqi_single(city_name)

    if result and result.get('success'):
        # Final staleness gate — applies to ALL layers including single-station fallback.
        # Pune was returning 2021 data via the single-station path which had no staleness check.
        if _result_is_stale(result):
            print(f"[Stale] {city_name}: data from {result.get('last_updated')} is >48h old — discarding")
            result = None
        else:
            _cache[city_name] = (now, result)
            return result

    # Layer 3 — stale cache beats "no data"
    if city_name in _cache:
        _, stale = _cache[city_name]
        out = dict(stale)
        out['source'] = out.get('source', '') + ' (CACHED)'
        return out

    # All layers failed — honest no-data response
    return {
        "success":       False,
        "data_available": False,
        "city":          city_name,
        "aqi":           None,
        "aqi_standard":  AQI_STANDARD,
        "error":         "No monitoring station found for this city",
    }


def fetch_all_cities():
    """
    Fetch all 50+ cities in parallel.
    Always includes no-data cities so the frontend can mark them.
    """
    cities_list = list(CITY_COORDS.keys())

    def fetch_one(city):
        result = fetch_city_aqi(city)
        if result is None:
            result = {"success": False, "data_available": False, "city": city, "aqi": None}
        result = dict(result)
        result['lat'] = CITY_COORDS[city]['lat']
        result['lon'] = CITY_COORDS[city]['lon']
        return result

    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(fetch_one, cities_list))

    return results   # includes no-data cities so frontend can mark them


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 1 — WAQI multi-station average (geo-filtered)
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_waqi_multi(city_name):
    try:
        search_url = f"https://api.waqi.info/search/?token={WAQI_API_KEY}&keyword={city_name}"
        resp = requests.get(search_url, timeout=10)
        data = resp.json()

        if data.get('status') != 'ok' or not data.get('data'):
            return None

        city_lower   = city_name.lower()
        stations_raw = data['data']
        bbox         = _get_bbox(city_name)

        # Filter: station must be inside the city bounding box
        bbox_filtered = [
            s for s in stations_raw
            if _in_bbox(bbox, s.get('station', {}).get('geo', []))
        ]

        # Also try name-based filter in case bbox returns too few
        name_filtered = [
            s for s in stations_raw
            if city_lower in (s.get('station', {}).get('name', '') or '').lower()
        ]

        # Prefer bbox+name overlap; fall back to bbox-only; last resort: name-only
        combined = [s for s in bbox_filtered if s in name_filtered] or bbox_filtered or name_filtered

        # Drop blacklisted station names (e.g. Greater Noida stations from Noida results)
        blacklist = _STATION_NAME_BLACKLIST.get(city_name, [])
        if blacklist:
            combined = [
                s for s in combined
                if not any(bl.lower() in (s.get('station', {}).get('name', '') or '').lower()
                           for bl in blacklist)
            ]

        # Hard cap: never more than 15 stations to keep fetches fast
        relevant = combined[:15]
        if not relevant:
            return None

        relevant_uids = [s['uid'] for s in relevant]
        station_geo_map = {
            s['uid']: s.get('station', {}).get('name', 'Unknown')
            for s in relevant
        }

        # Fetch all stations in parallel
        def fetch_uid(uid):
            try:
                r = requests.get(
                    f"https://api.waqi.info/feed/@{uid}/?token={WAQI_API_KEY}",
                    timeout=8,
                )
                d = r.json()
                if d.get('status') == 'ok':
                    return uid, d['data']
            except Exception:
                pass
            return uid, None

        now_unix = time.time()
        with ThreadPoolExecutor(max_workers=min(len(relevant_uids), 10)) as ex:
            raw_results = list(ex.map(fetch_uid, relevant_uids))

        # Parse with freshness weighting
        station_data = []
        excluded_stations = []
        for uid, r in raw_results:
            if r is None:
                continue
            aqi_raw = r.get('aqi')
            if aqi_raw is None or str(aqi_raw) == '-':
                continue
            try:
                aqi = int(aqi_raw)
            except (ValueError, TypeError):
                continue

            stn_name_raw = r.get('city', {}).get('name') or station_geo_map.get(uid, 'Unknown')
            geo          = r.get('city', {}).get('geo', [])
            ts_str       = r.get('time', {}).get('s', 'Unknown')

            # CHECK 0 — Blacklist re-check against the actual feed name.
            # The pre-fetch blacklist (applied to search-result names) can miss stations
            # whose feed city.name differs from the search-result station.name.
            if any(bl.lower() in (stn_name_raw or '').lower() for bl in blacklist):
                print(f"[Blacklist] Excluded '{stn_name_raw}' from {city_name} — matched blacklist rule")
                excluded_stations.append({'name': stn_name_raw, 'reason': 'blacklisted station name'})
                continue

            # CHECK 1 — Invalid AQI sentinel (999 = sensor malfunction; valid range 1–500)
            if aqi <= 0 or aqi > 500:
                excluded_stations.append({'name': stn_name_raw, 'reason': f'invalid AQI {aqi} (valid range: 1–500)'})
                continue

            # CHECK 2 — Stale data: discard if reading is > 48 hours old.
            # _hours_since() parses time.v (Unix) with time.s string as fallback,
            # so stations that return no Unix timestamp are no longer treated as fresh.
            hours_ago = _hours_since(r, now_unix)
            if hours_ago > 48:
                excluded_stations.append({'name': stn_name_raw, 'reason': f'stale data — last updated {ts_str}'})
                continue

            # CHECK 3 — Foreign station name (e.g. "Kera, Kochi, Kochi Prefecture, Japan")
            if _is_foreign_name(stn_name_raw):
                print(f"Discarded foreign-named station: {stn_name_raw} for city {city_name}")
                excluded_stations.append({'name': stn_name_raw, 'reason': f'foreign station name'})
                continue

            # CHECK 4 & 5 — Coordinate validation (only applied when non-zero coords exist)
            stn_lat, stn_lon = None, None
            if geo and len(geo) >= 2:
                try:
                    stn_lat, stn_lon = float(geo[0]), float(geo[1])
                except (TypeError, ValueError):
                    pass  # Unparseable → no coord checks → keep

            if stn_lat is not None and stn_lon is not None and stn_lat != 0 and stn_lon != 0:
                # CHECK 4 — Outside India bounding box
                if not _in_india([stn_lat, stn_lon]):
                    print(f"Discarded foreign station: {stn_name_raw} at {stn_lat:.4f},{stn_lon:.4f} for city {city_name}")
                    excluded_stations.append({'name': stn_name_raw, 'reason': f'outside India ({stn_lat:.2f},{stn_lon:.2f})'})
                    continue
                # CHECK 5 — Station is > 200 km from the city's known centre
                city_coords = CITY_COORDS.get(city_name)
                if city_coords:
                    dist_km = _haversine_km(city_coords['lat'], city_coords['lon'], stn_lat, stn_lon)
                    if dist_km > 200:
                        print(f"Discarded distant station: {stn_name_raw} at {dist_km:.0f}km from {city_name}")
                        excluded_stations.append({'name': stn_name_raw, 'reason': f'station too far: {dist_km:.0f}km from {city_name}'})
                        continue

            # Freshness weighting for the weighted average
            if hours_ago > 4:
                continue
            elif hours_ago > 2:
                weight = 0.4
            elif hours_ago > 1:
                weight = 0.7
            else:
                weight = 1.0

            iaqi         = r.get('iaqi', {})
            station_name = stn_name_raw
            station_data.append({
                'name':    station_name,
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
            # Return None so fetch_city_aqi falls through to CPCB and single-station layers.
            # A truthy dict here would short-circuit the `or` chain and block all fallbacks.
            if excluded_stations:
                print(f"[WAQI Multi] {city_name}: all {len(excluded_stations)} station(s) filtered out — {[s['reason'] for s in excluded_stations]}")
            return None

        # Remove outliers: |aqi - median| > 100
        if len(station_data) >= 3:
            med = statistics.median(s['aqi'] for s in station_data)
            station_data = [s for s in station_data if abs(s['aqi'] - med) <= 100]

        if not station_data:
            return None

        # Weighted average (after outlier removal)
        total_w  = sum(s['weight'] for s in station_data)
        city_aqi = round(sum(s['aqi'] * s['weight'] for s in station_data) / total_w)

        n             = len(station_data)
        cleanest      = min(station_data, key=lambda s: s['aqi'])
        most_polluted = max(station_data, key=lambda s: s['aqi'])

        if n >= 8:   quality = "HIGH"
        elif n >= 4: quality = "MEDIUM"
        elif n >= 2: quality = "LOW"
        else:        quality = "SINGLE"

        # Best pollutants: freshest station
        best          = max(station_data, key=lambda s: s['weight'])
        primary_stn   = best['name']
        all_stns      = [s['name'] for s in station_data]

        # Compact display label (max 3 names)
        short_names   = [n.split(',')[0] for n in all_stns[:3]]
        display_label = " · ".join(short_names) + ("…" if len(all_stns) > 3 else "")

        return {
            'success':              True,
            'data_available':       True,
            'city':                 city_name,
            'aqi':                  city_aqi,
            'aqi_standard':         AQI_STANDARD,
            'category':             categorize_aqi(city_aqi),
            'color':                aqi_color(city_aqi),
            'pm25':                 best.get('pm25'),
            'pm10':                 best.get('pm10'),
            'no2':                  best.get('no2'),
            'co':                   best.get('co'),
            'so2':                  best.get('so2'),
            'o3':                   best.get('o3'),
            'station_name':         city_name,
            'primary_station':      primary_stn,
            'all_stations_used':    all_stns,
            'station_names_display': f"Avg of: {display_label}",
            'station_count':        n,
            'stations':             sorted(station_data, key=lambda s: s['aqi'], reverse=True),
            'cleanest_area':        cleanest['name'],
            'cleanest_aqi':         cleanest['aqi'],
            'most_polluted_area':   most_polluted['name'],
            'most_polluted_aqi':    most_polluted['aqi'],
            'city_spread':          most_polluted['aqi'] - cleanest['aqi'],
            'data_quality':         quality,
            'excluded_stations':    excluded_stations,
            'source':               f"WAQI — avg of {n} CPCB stations",
            'last_updated':         station_data[0].get('updated', 'Unknown'),
        }

    except Exception as e:
        print(f"[WAQI Multi] {city_name}: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 2 — CPCB direct scraper
# ─────────────────────────────────────────────────────────────────────────────

_cpcb_cache = {'data': [], 'ts': 0}
_CPCB_TTL   = 3600


def _scrape_cpcb_all():
    # CPCB scraper disabled — endpoint changed, needs investigation
    return None


def _fetch_cpcb(city_name):
    try:
        all_stations = _scrape_cpcb_all()
        if not all_stations:
            return None

        city_lower    = city_name.lower()
        city_stations = [
            s for s in all_stations
            if city_lower in str(s.get('city',        '')).lower() or
               city_lower in str(s.get('stationName', '')).lower()
        ]
        if not city_stations:
            return None

        aqis     = []
        stn_names = []
        for s in city_stations:
            raw = s.get('aqi') or s.get('AQI') or s.get('aqiValue')
            if raw:
                try:
                    val = int(float(raw))
                    if 1 <= val <= 500:
                        aqis.append(val)
                        stn_names.append(s.get('stationName', 'CPCB station'))
                except (ValueError, TypeError):
                    pass

        if not aqis:
            return None

        city_aqi = round(sum(aqis) / len(aqis))
        n        = len(aqis)
        return {
            'success':              True,
            'data_available':       True,
            'city':                 city_name,
            'aqi':                  city_aqi,
            'aqi_standard':         AQI_STANDARD,
            'category':             categorize_aqi(city_aqi),
            'color':                aqi_color(city_aqi),
            'pm25':                 None, 'pm10': None, 'no2': None,
            'co':                   None, 'so2':  None, 'o3':  None,
            'station_name':         city_name,
            'primary_station':      stn_names[0] if stn_names else city_name,
            'all_stations_used':    stn_names,
            'station_names_display': f"CPCB avg of {n} station{'s' if n != 1 else ''}",
            'station_count':        n,
            'data_quality':         "HIGH" if n >= 8 else "MEDIUM" if n >= 4 else "LOW" if n >= 2 else "SINGLE",
            'source':               f"CPCB — avg of {n} stations",
            'last_updated':         'Last hour',
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
        stn_name = station.get('city', {}).get('name', city_name)

        # Blacklist check — same rules as multi-station path.
        # Prevents /feed/<city>/ returning a neighbouring-city station as the sole result
        # (e.g. /feed/noida/ resolving to a Greater Noida station).
        _single_blacklist = _STATION_NAME_BLACKLIST.get(city_name, [])
        if any(bl.lower() in (stn_name or '').lower() for bl in _single_blacklist):
            print(f"[Blacklist] Excluded '{stn_name}' from {city_name} — matched blacklist rule")
            return None

        # Apply the same foreign-name and distance guards as the multi-station path.
        # Without this, Kochi fell through to /feed/kochi/ → Japanese station,
        # and Raipur fell through to /feed/raipur/ → Dehradun station.
        if _is_foreign_name(stn_name):
            print(f"[Single] Discarded foreign station: {stn_name} for city {city_name}")
            return None

        station_geo = station.get('city', {}).get('geo', [])
        city_coords = CITY_COORDS.get(city_name)
        if city_coords and station_geo and len(station_geo) >= 2:
            try:
                stn_lat, stn_lon = float(station_geo[0]), float(station_geo[1])
                if stn_lat != 0 and stn_lon != 0:
                    dist_km = _haversine_km(
                        city_coords['lat'], city_coords['lon'], stn_lat, stn_lon
                    )
                    print(f"[Single] {city_name}: station '{stn_name}' is {dist_km:.0f}km away")
                    if dist_km > 300:
                        print(f"[Single] Discarded distant station: {stn_name} at {dist_km:.0f}km from {city_name} (>300km)")
                        return None
            except (TypeError, ValueError):
                pass

        return {
            'success':              True,
            'data_available':       True,
            'city':                 city_name,
            'aqi':                  aqi,
            'aqi_standard':         AQI_STANDARD,
            'category':             categorize_aqi(aqi),
            'color':                aqi_color(aqi),
            'pm25':                 iaqi.get('pm25', {}).get('v'),
            'pm10':                 iaqi.get('pm10', {}).get('v'),
            'no2':                  iaqi.get('no2',  {}).get('v'),
            'co':                   iaqi.get('co',   {}).get('v'),
            'so2':                  iaqi.get('so2',  {}).get('v'),
            'o3':                   iaqi.get('o3',   {}).get('v'),
            'station_name':         stn_name,
            'primary_station':      stn_name,
            'all_stations_used':    [stn_name],
            'station_names_display': stn_name,
            'station_count':        1,
            'data_quality':         'SINGLE',
            'source':               'WAQI — single station',
            'last_updated':         station.get('time', {}).get('s', 'Unknown'),
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
# Background cache warmup
# ─────────────────────────────────────────────────────────────────────────────

def _warmup():
    print("[Cache] Background warmup starting for all cities…")
    fetch_all_cities()
    print("[Cache] Background warmup complete.")

threading.Thread(target=_warmup, daemon=True).start()
