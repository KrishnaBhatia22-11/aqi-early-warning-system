"""
Live air-quality data from the official CPCB feed on data.gov.in.

This replaces waqi_client as the app's only live source. WAQI's CPCB mirror
froze on 2026-06-23 for every city except Delhi; the government resource this
module reads is the same monitoring network at first hand, and it is current.

DESIGN — one national pull, grouped locally.
The old client fanned out one HTTP search plus up to fifteen station feeds PER
CITY, 53 cities deep, and spent most of its code budget keeping that burst from
exhausting Render's 512MB box. This resource publishes the WHOLE country in a
few thousand records, so the entire app is served by one paged fetch behind a
15-minute cache. No fan-out, no per-city timeouts, no concurrency budget.

The feed returns ONE record per pollutant per station:

    {"country": "India", "state": "Delhi", "city": "Delhi",
     "station": "Alipur, Delhi - DPCC", "last_update": "21-09-2026 18:00:00",
     "latitude": "...", "longitude": "...",
     "pollutant_id": "PM2.5", "min_value": "68", "max_value": "107",
     "avg_value": "83"}

so grouping runs records → city → station → {pollutant: sub-index}, and each
station's dict goes through india_aqi.aqi_from_sub_indices. Why sub-index and
not concentration, when the field is called avg_value: see THE UNIT GATE below.
It is the single most important thing in this file.

The public shape — fetch_city_aqi / fetch_all_cities and every key they return —
is deliberately identical to waqi_client's, because /city, /cities, /compare,
/share, /chat, the scheduler and the frontend all read those exact keys.
"""

import math
import os
import sys
import time
import threading
import requests
from datetime import datetime, timedelta, timezone

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.settings import DATA_GOV_API_KEY, CITY_COORDS
from src.data.india_aqi import (
    AQI_STANDARD,
    AQI_MAX,
    UNITS,
    aqi_from_sub_indices,
    concentration,
    categorize_aqi,
    aqi_color,
)

RESOURCE_ID = "3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69"
BASE_URL    = f"https://api.data.gov.in/resource/{RESOURCE_ID}"

SOURCE_LABEL = "CPCB — Central Pollution Control Board (data.gov.in)"

CACHE_DURATION = 900   # 15 minutes, matching the old client's TTL

# data.gov.in silently hangs on requests without a browser User-Agent — the
# connection is accepted and then never answered, so it surfaces as a read
# timeout rather than a 403. Do not remove this header.
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/140.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

_PAGE_LIMIT   = 1000   # the API's own ceiling; a restricted key may return fewer
_HTTP_TIMEOUT = 45
_RETRIES      = 3

# The national resource is ~3.5k records, so a full key needs four pages. A
# rate-restricted key (data.gov.in's public sample key, for one) caps every
# response at 10 rows no matter what `limit` asks for, and then the same pull
# needs hundreds. The page cap is set high enough to finish in that case; the
# deadline is what actually stops a runaway, because pages are what cost time,
# not records.
_MAX_PAGES        = 400
_FETCH_DEADLINE_S = 120

# India Standard Time. CPCB stamps `last_update` in local wall-clock time with no
# offset, so it MUST be attached explicitly — read as UTC, an 18:00 IST reading
# looks 5.5 hours in the future and every freshness calculation is wrong.
IST = timezone(timedelta(hours=5, minutes=30))

# Reuse waqi_client's honest-data rule: a station whose newest reading is older
# than this is dropped entirely rather than shown as if it were current. This is
# what made the WAQI freeze visible as NO DATA instead of as stale numbers, and
# it is the guarantee worth keeping most.
_MAX_AGE_HOURS = 48

# Carried over from waqi_client: a station further than this from the city's
# known centre is not that city's station.
#
# CPCB's `city` field is clean, but it is not unique — India has an Aurangabad
# in Maharashtra AND one in Bihar, a Hamirpur in HP and UP, and so on. Matching
# on the name alone would average two cities 1,000km apart into one reading.
# Every record carries lat/lon, so the check is free.
_MAX_STATION_DISTANCE_KM = 200

# Feed values are sub-indices, so the only physically meaningful range is the
# AQI scale itself. Anything outside it is a broken sensor, not dirty air — and
# that includes CPCB's 999 malfunction sentinel, which the old client rejected
# the same way when it arrived as an AQI.
_JUNK_SENTINELS = {999.0}


# ──────────────────────────────────────────────────────────────────────────────
# THE UNIT GATE — avg_value is a SUB-INDEX, not a concentration
# ──────────────────────────────────────────────────────────────────────────────
# Despite the field name, `avg_value` carries each pollutant's CPCB sub-index
# (0-500), already computed by CPCB. It does NOT carry µg/m³ or mg/m³.
#
# This project was once broken by exactly this confusion in the other direction
# — PM2.5 stored as a 0-500 sub-index in a field that meant µg/m³ — so the
# question was settled against the live feed rather than assumed. Four
# independent checks on Delhi, 45 stations, 2026-09-21 18:00 IST, all agree:
#
#   1. AQI, read as concentrations ...... 392  (Very Poor)   — wrong
#      AQI, read as sub-indices ......... 167  (Moderate)    — matches the
#      CPCB and WAQI dashboards, which had Delhi at ~140-160 that day.
#
#   2. PM10:PM2.5 ratio. Indian urban air runs 1.8-2.5.
#      As concentrations ... 0.92  — a ratio that essentially never occurs.
#      As sub-indices ...... 2.31  — textbook.
#
#   3. CO. Delhi runs 0.5-2.5 mg/m³. Median raw value 42.
#      As mg/m³ ............ 42 mg/m³, a fatal-exposure figure, city-wide.
#      As a sub-index ...... 0.84 mg/m³.
#
#   4. NH3. Delhi runs 15-60 µg/m³. Median raw value 5.
#      As µg/m³ ............ 5, far below anything Delhi records.
#      As a sub-index ...... 20 µg/m³.
#
# Check 1 is the one that matters for shipping: reading these as concentrations
# produces a number that looks entirely plausible — a bad Delhi day — and is
# wrong by 225 points.
#
# So the pipeline runs INVERSE to the obvious direction: sub-indices are maxed
# straight into the AQI, and india_aqi.concentration() reconstructs the real
# µg/m³ figures for the pm25/pm10/... fields the frontend charts and the
# database store. Those fields now hold genuine concentrations for the first
# time; under WAQI they held US EPA sub-indices.
#
# Every pollutant participates in the AQI, CO included — on the sub-index
# reading its values are physically sensible, so there is nothing to exclude.
#
# If a future feed change reintroduces doubt, re-run the four checks above
# before trusting a number out of this module.
_EXCLUDED_FROM_AQI = set()

# Canonical pollutant → the key the rest of the app expects on a result dict.
# The canonical names are india_aqi's BREAKPOINTS keys.
_POLLUTANT_FIELD = {
    "PM2.5": "pm25",
    "PM10":  "pm10",
    "NO2":   "no2",
    "CO":    "co",
    "SO2":   "so2",
    "OZONE": "o3",
    "NH3":   "nh3",
}

# Upper-cased feed pollutant_id → canonical name. The feed says "OZONE" and
# "PM2.5" today; the spellings below are accepted too so a cosmetic change
# upstream drops a pollutant's spelling rather than the pollutant.
_POLLUTANT_ALIASES = {name: name for name in _POLLUTANT_FIELD}
_POLLUTANT_ALIASES.update({
    "PM25":   "PM2.5",
    "PM 2.5": "PM2.5",
    "PM 10":  "PM10",
    "O3":     "OZONE",
    "NO_2":   "NO2",
    "SO_2":   "SO2",
})


# ────────────────────────────────────────────────────────────────────────────
# City name map — the app's names → the feed's `city` field
# ────────────────────────────────────────────────────────────────────────────
# The feed's `city` is clean ("Mumbai"); it is the `station` field that carries
# the agency suffixes ("Bandra, Mumbai - MPCB"). So most of CITY_COORDS matches
# the feed after nothing more than case/punctuation folding.
#
# All 53 of the app's cities were probed against the live feed on 2026-09-21.
# 45 resolved, and exactly ONE needed a different spelling:
#
#     Pondicherry → Puducherry
#
# Every other rename the app might have expected — Bengaluru, Mysuru, Gurugram,
# Visakhapatnam, Thiruvananthapuram, and Aurangabad — CPCB publishes under the
# name the app already uses. Those entries are kept anyway, second in their
# list, as no-cost insurance for the day CPCB migrates: a miss on the first
# candidate is a dict lookup, not a request.
#
# The 8 with no CPCB presence at all (Coimbatore, Kochi, Ranchi, Shimla, Jammu,
# Madurai, Warangal, Tiruchirappalli) are honest NO_DATA. Do not invent aliases
# for them — they have no stations in this feed, and a name that happens to
# match somewhere else in India would be worse than an empty marker. The
# distance guard above is the backstop if one ever does.
_CITY_ALIASES = {
    # Verified: the feed's name differs from the app's.
    "Pondicherry":        ["Puducherry", "Pondicherry"],

    # Verified: the app's own name works today. The second entry is the
    # renamed/alternate form, held in reserve.
    "Bengaluru":          ["Bengaluru", "Bangalore"],
    "Mysuru":             ["Mysuru", "Mysore"],
    "Gurugram":           ["Gurugram", "Gurgaon"],
    "Visakhapatnam":      ["Visakhapatnam", "Vishakhapatnam"],
    "Thiruvananthapuram": ["Thiruvananthapuram", "Trivandrum"],
    "Aurangabad":         ["Aurangabad", "Chhatrapati Sambhajinagar"],
}


def _normalise(name):
    """Fold a city name for matching — case, spaces and punctuation removed."""
    return "".join(ch for ch in (name or "").lower() if ch.isalnum())


def _candidates(app_city):
    """Feed city names to try for one of the app's cities, best first."""
    return _CITY_ALIASES.get(app_city, [app_city])


# ─────────────────────────────────────────────────────────────────────────────
# Fetch
# ─────────────────────────────────────────────────────────────────────────────

def _get_page(offset, limit=_PAGE_LIMIT):
    """One page of the resource. Returns the decoded body, or None."""
    params = {
        "api-key": DATA_GOV_API_KEY,
        "format":  "json",
        "limit":   limit,
        "offset":  offset,
    }
    for attempt in range(_RETRIES):
        try:
            resp = requests.get(
                BASE_URL, params=params, headers=_HEADERS, timeout=_HTTP_TIMEOUT
            )
            if resp.status_code == 200:
                return resp.json()
            # 429 (quota) and 5xx are worth another try; a 4xx is not.
            if resp.status_code != 429 and resp.status_code < 500:
                print(f"[CPCB] offset={offset} HTTP {resp.status_code} — not retrying")
                return None
            print(f"[CPCB] offset={offset} HTTP {resp.status_code} — retry {attempt + 1}/{_RETRIES}")
        except Exception as e:
            print(f"[CPCB] offset={offset} {type(e).__name__}: {e} — retry {attempt + 1}/{_RETRIES}")
        time.sleep(2 * (attempt + 1))
    return None


def fetch_all_records():
    """Page through the whole national resource.

    Returns (records, complete). `complete` is True only when the feed's own
    `total` was reached — a partial pull is reported rather than passed off as
    the whole country, because a truncated pull looks exactly like half of
    India going offline and would otherwise blank the map silently.

    Advances by however many records actually came back rather than by the
    requested limit, since a restricted key can cap a page well below it.
    """
    if not DATA_GOV_API_KEY:
        print("[CPCB] DATA_GOV_API_KEY is not set — cannot fetch live data")
        return [], False

    records, offset, total = [], 0, None
    started = time.time()
    pages = 0

    for _ in range(_MAX_PAGES):
        if time.time() - started > _FETCH_DEADLINE_S:
            print(f"[CPCB] Fetch deadline hit after {pages} page(s)")
            break

        body = _get_page(offset)
        if body is None:
            break

        page = body.get("records") or []
        if total is None:
            try:
                total = int(body.get("total") or 0)
            except (TypeError, ValueError):
                total = 0
            if page and len(page) < _PAGE_LIMIT and total > len(page):
                print(
                    f"[CPCB] Key is capped at {len(page)} records/page — "
                    f"{total} records will need ~{-(-total // len(page))} requests"
                )

        if not page:
            break

        records.extend(page)
        offset += len(page)
        pages += 1

        if total and offset >= total:
            break

    complete = bool(total) and len(records) >= total
    print(
        f"[CPCB] Fetched {len(records)}/{total} records in {pages} page(s), "
        f"{time.time() - started:.1f}s — {'complete' if complete else 'PARTIAL'}"
    )
    return records, complete


# ─────────────────────────────────────────────────────────────────────────────
# Clean & validate
# ─────────────────────────────────────────────────────────────────────────────

def _clean_value(pollutant, raw):
    """Parse one avg_value into a sub-index, or None if it must not be trusted.

    Rejects the feed's "NA", blanks, non-numbers, negatives, the 999 malfunction
    sentinel, and anything outside the 0-500 AQI scale.
    """
    if raw is None:
        return None
    text = str(raw).strip()
    if not text or text.upper() in ("NA", "N/A", "-", "NULL", "NONE"):
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    if value in _JUNK_SENTINELS:
        return None
    if value < 0 or value > AQI_MAX:
        return None
    return value


def _coord(raw):
    """Parse a latitude/longitude string, or None. 0/0 is the null island."""
    try:
        value = float(str(raw).strip())
    except (TypeError, ValueError):
        return None
    return None if value == 0 else value


def _parse_timestamp(raw):
    """Parse CPCB's "DD-MM-YYYY HH:MM:SS" into an IST-aware datetime, or None."""
    text = (raw or "").strip()
    if not text:
        return None
    for fmt in ("%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=IST)
        except ValueError:
            continue
    return None


def _haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km between two lat/lon points."""
    radius = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return 2 * radius * math.asin(math.sqrt(a))


def _distance_from_city(app_city, entry):
    """km from the app's city centre to this station, or None if uncheckable.

    None means "cannot prove it is wrong" — a station with no usable
    coordinates is kept, exactly as the old client kept one whose geo was
    missing, because dropping unverifiable stations loses more than it saves.
    """
    coords = CITY_COORDS.get(app_city)
    if not coords or entry["lat"] is None or entry["lon"] is None:
        return None
    return _haversine_km(coords["lat"], coords["lon"], entry["lat"], entry["lon"])


def _is_stale(ts):
    """True if this reading is older than the staleness cutoff.

    A reading stamped in the future is a clock problem upstream, not staleness,
    so it passes here and is caught (or not) by the plausibility checks instead.
    """
    if ts is None:
        return True   # no usable timestamp — cannot prove freshness, so drop it
    return (datetime.now(timezone.utc) - ts).total_seconds() / 3600 > _MAX_AGE_HOURS


# ─────────────────────────────────────────────────────────────────────────────
# Group records → cities
# ─────────────────────────────────────────────────────────────────────────────

def _group_stations(records):
    """Fold flat pollutant records into {normalised_city: {station: {...}}}.

    Each station accumulates its pollutant SUB-INDICES (see THE UNIT GATE) plus
    the newest timestamp seen across them. Nothing is dropped for staleness here
    — that happens in _build_city once a station is whole, so a single old
    pollutant row cannot silently take the station's other readings with it.
    """
    cities = {}

    for rec in records:
        city_raw = (rec.get("city") or "").strip()
        station  = (rec.get("station") or "").strip()
        if not city_raw or not station:
            continue

        pollutant = _POLLUTANT_ALIASES.get(
            (rec.get("pollutant_id") or "").strip().upper()
        )
        if pollutant is None:
            continue

        value = _clean_value(pollutant, rec.get("avg_value"))
        ts    = _parse_timestamp(rec.get("last_update"))

        bucket = cities.setdefault(_normalise(city_raw), {})
        entry  = bucket.setdefault(station, {
            "name":         station,
            "city_raw":     city_raw,
            "state":        (rec.get("state") or "").strip(),
            "lat":          _coord(rec.get("latitude")),
            "lon":          _coord(rec.get("longitude")),
            "sub_indices":  {},
            "updated":      None,
        })

        if value is not None:
            entry["sub_indices"][pollutant] = value
        if ts is not None and (entry["updated"] is None or ts > entry["updated"]):
            entry["updated"] = ts

    return cities


def _station_result(entry):
    """Compute one station's AQI, or None if CPCB's reporting rule is not met.

    The feed's values are already sub-indices, so the AQI is their maximum — no
    forward conversion happens anywhere in this path. The pm25/pm10/... fields
    are the INVERSE conversion: real concentrations reconstructed from those
    sub-indices, because that is what the health calculators, the pollutant
    charts and the aqi_readings table all mean by those names.
    """
    scoring = {
        p: v for p, v in entry["sub_indices"].items()
        if p not in _EXCLUDED_FROM_AQI
    }
    aqi, dominant = aqi_from_sub_indices(scoring)
    if aqi is None:
        return None

    station = {
        "name":     entry["name"],
        "aqi":      aqi,
        "weight":   1.0,   # every CPCB station shares the same reporting hour
        "updated":  entry["updated"].strftime("%Y-%m-%dT%H:%M:%S") if entry["updated"] else "Unknown",
        "dominant_pollutant": dominant,
    }

    for pollutant, field in _POLLUTANT_FIELD.items():
        si = entry["sub_indices"].get(pollutant)
        station[field] = concentration(pollutant, si) if si is not None else None
        # Keep the raw sub-index too — it is what CPCB actually published, and
        # it is the only way to tell which pollutant drove the AQI.
        station[field + "_sub_index"] = round(si) if si is not None else None

    return station


def _build_city(app_city, station_entries):
    """Assemble one city result in waqi_client's exact output shape."""
    stations, excluded = [], []

    for entry in station_entries.values():
        distance = _distance_from_city(app_city, entry)
        if distance is not None and distance > _MAX_STATION_DISTANCE_KM:
            excluded.append({
                "name":   entry["name"],
                "reason": f"{distance:.0f}km from {app_city} — different city of the same name",
            })
            continue

        if _is_stale(entry["updated"]):
            stamp = entry["updated"].strftime("%Y-%m-%d %H:%M") if entry["updated"] else "no timestamp"
            excluded.append({"name": entry["name"], "reason": f"stale data — last updated {stamp}"})
            continue

        result = _station_result(entry)
        if result is None:
            have = sorted(entry["sub_indices"])
            excluded.append({
                "name":   entry["name"],
                "reason": f"insufficient pollutants for CPCB AQI (have: {', '.join(have) or 'none'})",
            })
            continue

        stations.append(result)

    if not stations:
        return None

    # Drop stations far from the city's median, exactly as the old client did —
    # one stuck sensor should not drag a whole city's headline number.
    if len(stations) >= 3:
        ordered = sorted(s["aqi"] for s in stations)
        mid     = len(ordered) // 2
        median  = ordered[mid] if len(ordered) % 2 else (ordered[mid - 1] + ordered[mid]) / 2
        kept, dropped = [], []
        for s in stations:
            (kept if abs(s["aqi"] - median) <= 100 else dropped).append(s)
        if kept:   # never let the filter empty a city out entirely
            for s in dropped:
                excluded.append({
                    "name":   s["name"],
                    "reason": f"outlier — AQI {s['aqi']} vs city median {median:.0f}",
                })
            stations = kept

    n        = len(stations)
    city_aqi = round(sum(s["aqi"] for s in stations) / n)

    cleanest      = min(stations, key=lambda s: s["aqi"])
    most_polluted = max(stations, key=lambda s: s["aqi"])

    if   n >= 8: quality = "HIGH"
    elif n >= 4: quality = "MEDIUM"
    elif n >= 2: quality = "LOW"
    else:        quality = "SINGLE"

    # Representative pollutants come from ONE station, not from an average of
    # concentrations across stations — averaging those would produce a pollutant
    # mix no station ever measured.
    #
    # Freshest first, as the old client did. Then the station reporting the most
    # pollutants: CPCB stations routinely return NA for several, and picking on
    # AQI alone kept landing on a station with three readings and four blanks,
    # so a city's headline showed "PM10: —" while a neighbouring station had it.
    # Worst reading breaks the remaining ties, since that is the one the health
    # advice should be written against.
    def _primary_rank(s):
        reported = sum(
            1 for field in _POLLUTANT_FIELD.values() if s.get(field) is not None
        )
        return (s["updated"], reported, s["aqi"])

    primary = max(stations, key=_primary_rank)

    all_stns      = [s["name"] for s in stations]
    short_names   = [name.split(",")[0] for name in all_stns[:3]]
    display_label = " · ".join(short_names) + ("…" if len(all_stns) > 3 else "")

    newest = max((s["updated"] for s in stations if s["updated"] != "Unknown"), default="Unknown")

    return {
        "success":               True,
        "data_available":        True,
        "city":                  app_city,
        "aqi":                   city_aqi,
        "aqi_standard":          AQI_STANDARD,
        "category":              categorize_aqi(city_aqi),
        "color":                 aqi_color(city_aqi),
        # Concentrations, reconstructed from CPCB's sub-indices: µg/m³ for all
        # of these except co, which is mg/m³. Under WAQI these same fields held
        # US EPA sub-indices, so historical rows are not comparable to new ones.
        "pm25":                  primary.get("pm25"),
        "pm10":                  primary.get("pm10"),
        "no2":                   primary.get("no2"),
        "co":                    primary.get("co"),
        "so2":                   primary.get("so2"),
        "o3":                    primary.get("o3"),
        "nh3":                   primary.get("nh3"),
        "pollutant_units":       dict(UNITS),
        "dominant_pollutant":    primary.get("dominant_pollutant"),
        "station_name":          app_city,
        "primary_station":       primary["name"],
        "all_stations_used":     all_stns,
        "station_names_display": f"Avg of: {display_label}",
        "station_count":         n,
        "stations":              sorted(stations, key=lambda s: s["aqi"], reverse=True),
        "cleanest_area":         cleanest["name"],
        "cleanest_aqi":          cleanest["aqi"],
        "most_polluted_area":    most_polluted["name"],
        "most_polluted_aqi":     most_polluted["aqi"],
        "city_spread":           most_polluted["aqi"] - cleanest["aqi"],
        "data_quality":          quality,
        "excluded_stations":     excluded,
        "source":                SOURCE_LABEL,
        "last_updated":          newest,
    }


def _no_data(app_city):
    """The honest empty result — same shape the old client returned on failure."""
    return {
        "success":        False,
        "data_available": False,
        "city":           app_city,
        "aqi":            None,
        "aqi_standard":   AQI_STANDARD,
        "error":          "No monitoring station found for this city",
    }


def build_city_map(records):
    """Turn raw national records into {app_city_name: result} for all 53 cities."""
    grouped = _group_stations(records)
    out = {}

    for app_city in CITY_COORDS:
        result = None
        for candidate in _candidates(app_city):
            entries = grouped.get(_normalise(candidate))
            if entries:
                result = _build_city(app_city, entries)
                if result:
                    break
        out[app_city] = result or _no_data(app_city)

    live = sum(1 for r in out.values() if r.get("success"))
    print(f"[CPCB] Built {live}/{len(out)} cities with live data")
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Cache — one national pull serves every endpoint
# ─────────────────────────────────────────────────────────────────────────────

_cache      = {"data": None, "ts": 0.0, "complete": False}
_cache_lock = threading.Lock()   # only one thread ever refreshes

# How long a caller will wait for a refresh that another thread is already
# doing. Callers do NOT queue behind it past this point — see _get_cached.
_LOCK_WAIT_S = 20


def _live_count(snapshot):
    return sum(1 for r in (snapshot or {}).values() if r.get("success"))


def _fresh():
    """True if the cache holds a snapshot that is still inside its TTL."""
    return (
        _cache["data"] is not None
        and time.time() - _cache["ts"] < CACHE_DURATION
    )


def _get_cached(force=False):
    """Return {city: result}, refreshing if the TTL has expired.

    On a failed refresh the previous snapshot is kept and served — a transient
    upstream error should not blank the map. Serving it is safe indefinitely:
    every station in it carries its own timestamp and _build_city already
    rejected anything older than the staleness cutoff, so a stale snapshot goes
    honestly empty rather than quietly wrong.
    """
    if not force and _fresh():
        return _cache["data"]

    # Wait for an in-progress refresh, but never indefinitely.
    #
    # Cancelling an asyncio.to_thread future does not stop the thread, so a
    # request that times out at the endpoint leaves its worker here holding the
    # line. On a cold start a burst of requests would park the whole default
    # executor on this lock for the length of one national pull. Bounding the
    # wait means a caller that cannot be served quickly returns whatever is
    # known — the previous snapshot, or nothing, which renders as honest
    # no-data markers — instead of occupying a thread.
    if not _cache_lock.acquire(timeout=_LOCK_WAIT_S):
        print("[CPCB] Refresh already in progress — serving what is cached")
        return _cache["data"] or {}

    try:
        # The other thread may have finished refreshing while this one waited.
        if not force and _fresh():
            return _cache["data"]

        try:
            records, complete = fetch_all_records()
        except Exception as e:
            print(f"[CPCB] Refresh failed: {e}")
            records, complete = [], False

        if not records:
            if _cache["data"] is not None:
                print("[CPCB] Refresh returned nothing — serving previous snapshot")
                return _cache["data"]
            return {}

        built = build_city_map(records)

        # A partial pull covers whichever slice of the country paged in first,
        # so it can lose cities that are genuinely reporting. Only let one
        # replace a good snapshot if it is not actually worse.
        if not complete and _cache["data"] is not None:
            if _live_count(built) < _live_count(_cache["data"]):
                print(
                    f"[CPCB] Partial refresh ({_live_count(built)} live cities) is worse "
                    f"than the cached snapshot ({_live_count(_cache['data'])}) — keeping it"
                )
                # Do not touch _cache["ts"]: the TTL stays expired so the next
                # caller retries instead of waiting out a full 15 minutes.
                return _cache["data"]

        _cache["data"]     = built
        _cache["ts"]       = time.time()
        _cache["complete"] = complete
        return built
    finally:
        _cache_lock.release()


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API — same names and same output shape as waqi_client
# ─────────────────────────────────────────────────────────────────────────────

def fetch_city_aqi(city_name):
    """Live CPCB AQI for one city. Never raises; returns the no-data shape instead.

    The result is a shallow copy of the cached entry, so a caller that adds
    fields to it (/city attaches health_advisory and coordinates) cannot write
    those into the shared snapshot every other endpoint reads.
    """
    try:
        cities = _get_cached()
    except Exception as e:
        print(f"[CPCB] {city_name}: {e}")
        return _no_data(city_name)

    result = cities.get(city_name)
    if result:
        return dict(result)

    # Fall back to a normalised match so a caller's spelling ("bengaluru",
    # "New Delhi ") still finds the city the cache built under CITY_COORDS' name.
    for candidate in _candidates(city_name):
        wanted = _normalise(candidate)
        for known, known_result in cities.items():
            if _normalise(known) == wanted:
                return dict(known_result)

    return _no_data(city_name)


def fetch_all_cities():
    """Live CPCB AQI for every city in CITY_COORDS, with coordinates attached.

    No-data cities are included so the map can mark them, which is what the old
    client did and what the frontend still expects.
    """
    try:
        cities = _get_cached()
    except Exception as e:
        print(f"[CPCB] fetch_all_cities failed: {e}")
        cities = {}

    out = []
    for city, coords in CITY_COORDS.items():
        result = dict(cities.get(city) or _no_data(city))
        result["lat"] = coords["lat"]
        result["lon"] = coords["lon"]
        out.append(result)
    return out


def refresh_cache():
    """Force a refresh. Used by the scheduler so the hourly snapshot is not a
    replay of a cache entry it already wrote."""
    return _get_cached(force=True)


def cache_status():
    """Diagnostics for /cpcb/status."""
    data = _cache["data"] or {}
    live = sum(1 for r in data.values() if r.get("success"))
    return {
        "cached":        _cache["data"] is not None,
        "age_seconds":   round(time.time() - _cache["ts"]) if _cache["ts"] else None,
        "ttl_seconds":   CACHE_DURATION,
        "cities_total":  len(data),
        "cities_live":   live,
        "last_pull_complete": _cache["complete"],
        "aqi_standard":  AQI_STANDARD,
        "source":        SOURCE_LABEL,
        "key_present":   bool(DATA_GOV_API_KEY),
        "excluded_from_aqi": sorted(_EXCLUDED_FROM_AQI),
        "feed_values_are":   "CPCB sub-indices (0-500), inverted to concentrations for display",
        "pollutant_units":   dict(UNITS),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Warmup
# ─────────────────────────────────────────────────────────────────────────────

def _warmup():
    """Fill the cache once, off the request path. Never raises."""
    try:
        cities = _get_cached(force=True)
        live = sum(1 for r in cities.values() if r.get("success"))
        print(f"[CPCB] Warmup complete — {live}/{len(cities)} cities live")
    except Exception as e:
        print(f"[CPCB] Warmup aborted: {e}")


def start_warmup():
    """Kick the warmup off on a daemon thread. Never blocks the caller.

    One HTTP page or four, not 53 cities' worth of fan-out — the burst that used
    to have to be rationed across the whole process no longer exists.
    """
    thread = threading.Thread(target=_warmup, name="cpcb-warmup", daemon=True)
    thread.start()
    return thread
