import hashlib
import random
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()

# Shared constants (mirrors forecast.py)
_DIURNAL_RAW = [
    0.87, 0.85, 0.83, 0.83, 0.86, 0.92,
    1.05, 1.28, 1.32, 1.20, 1.08, 1.00,
    0.95, 0.93, 0.97, 1.05, 1.15, 1.30,
    1.35, 1.25, 1.10, 1.00, 0.93, 0.89,
]
_dm = sum(_DIURNAL_RAW) / 24
_DIURNAL = [v / _dm for v in _DIURNAL_RAW]

_SEASONAL = {
    1: 1.25, 2: 1.20, 3: 1.05, 4: 1.05, 5: 1.08,
    6: 0.90, 7: 0.82, 8: 0.78, 9: 0.88, 10: 1.05,
    11: 1.20, 12: 1.35,
}
_DOW = {0: 1.02, 1: 1.02, 2: 1.02, 3: 1.02, 4: 1.05, 5: 0.92, 6: 0.85}

_CITY_DEFAULTS = {
    "Delhi": 185, "Mumbai": 95, "Kolkata": 140, "Chennai": 75,
    "Bengaluru": 85, "Hyderabad": 90, "Ahmedabad": 130, "Jaipur": 145,
    "Lucknow": 160, "Patna": 175, "Chandigarh": 105, "Amritsar": 120,
    "Guwahati": 95, "Bhopal": 120, "Pune": 100, "Nagpur": 125,
    "Surat": 115, "Kanpur": 180, "Varanasi": 170,
    "Coimbatore": 65, "Kochi": 70, "Thiruvananthapuram": 55,
    "Visakhapatnam": 80, "Ranchi": 120, "Bhubaneswar": 110,
    "Indore": 125,
}

_CITY_NORM = {
    "bangalore": "Bengaluru", "bengalore": "Bengaluru", "bengaluru": "Bengaluru",
    "cochin": "Kochi", "kochi": "Kochi", "trivandrum": "Thiruvananthapuram",
    "vizag": "Visakhapatnam", "delhi": "Delhi", "mumbai": "Mumbai",
    "kolkata": "Kolkata", "chennai": "Chennai", "hyderabad": "Hyderabad",
    "ahmedabad": "Ahmedabad", "jaipur": "Jaipur", "lucknow": "Lucknow",
    "patna": "Patna", "chandigarh": "Chandigarh", "amritsar": "Amritsar",
    "guwahati": "Guwahati", "bhopal": "Bhopal", "pune": "Pune",
    "nagpur": "Nagpur", "surat": "Surat", "kanpur": "Kanpur",
    "varanasi": "Varanasi", "ranchi": "Ranchi", "bhubaneswar": "Bhubaneswar",
    "indore": "Indore", "coimbatore": "Coimbatore",
    "visakhapatnam": "Visakhapatnam", "thiruvananthapuram": "Thiruvananthapuram",
}


def _cat(aqi: float) -> str:
    if aqi <= 50:  return "Good"
    if aqi <= 100: return "Satisfactory"
    if aqi <= 200: return "Moderate"
    if aqi <= 300: return "Poor"
    if aqi <= 400: return "Very Poor"
    return "Severe"


def _daily_aqi(canon_city: str, base: float, date: datetime) -> float:
    """
    Synthetic daily AQI: seasonal × DOW multipliers + seeded noise.
    Uses mean of the 24-hour diurnal profile (= 1.0 by construction)
    so multipliers are applied to the base directly.
    """
    s_mult = _SEASONAL.get(date.month, 1.0)
    d_mult = _DOW.get(date.weekday(), 1.0)

    # Reproducible ±15 % noise seeded by city + date
    seed_str = f"{canon_city.lower()}{date.strftime('%Y%m%d')}"
    seed_int = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed_int)
    noise = 1.0 + (rng.random() - 0.5) * 0.30

    return max(5.0, round(base * s_mult * d_mult * noise))


@router.get("/history/{city}")
def get_history(
    city: str,
    days: int = Query(default=7, ge=1, le=90),
):
    canon = _CITY_NORM.get(city.lower().strip(), city.strip().title())
    base  = _CITY_DEFAULTS.get(canon, 150)

    today   = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    records = []

    for i in range(days, 0, -1):           # oldest → newest
        date = today - timedelta(days=i)
        aqi  = int(_daily_aqi(canon, base, date))
        records.append({
            "date":     date.strftime("%Y-%m-%d"),
            "aqi":      aqi,
            "category": _cat(aqi),
        })

    aqi_vals   = [r["aqi"] for r in records]
    avg        = round(sum(aqi_vals) / len(aqi_vals))
    worst_rec  = max(records, key=lambda r: r["aqi"])
    best_rec   = min(records, key=lambda r: r["aqi"])

    # Trend: compare last-3 vs first-3 daily averages
    first3 = sum(aqi_vals[:3]) / 3
    last3  = sum(aqi_vals[-3:]) / 3
    if last3 > first3 * 1.08:
        trend = "worsening"
    elif last3 < first3 * 0.92:
        trend = "improving"
    else:
        trend = "stable"

    return {
        "city":  canon,
        "days":  days,
        "data":  records,
        "summary": {
            "average":    avg,
            "worst_day":  worst_rec["date"],
            "best_day":   best_rec["date"],
            "worst_aqi":  worst_rec["aqi"],
            "best_aqi":   best_rec["aqi"],
            "trend":      trend,
        },
        "note": "Synthetic historical data — real database planned for Phase 6",
    }
