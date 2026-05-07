from datetime import datetime
from typing import List, Optional

import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

# Shared diurnal profile (same as forecast route — Indian metro cities)
_DIURNAL_RAW = [
    0.87, 0.85, 0.83, 0.83, 0.86, 0.92,  # 00–05
    1.05, 1.28, 1.32, 1.20, 1.08, 1.00,  # 06–11
    0.95, 0.93, 0.97, 1.05, 1.15, 1.30,  # 12–17
    1.35, 1.25, 1.10, 1.00, 0.93, 0.89,  # 18–23
]
_diurnal_mean = sum(_DIURNAL_RAW) / 24
DIURNAL = [v / _diurnal_mean for v in _DIURNAL_RAW]

SEASONAL = {
    1: 1.25, 2: 1.20, 3: 1.05, 4: 1.05, 5: 1.08,
    6: 0.90, 7: 0.82, 8: 0.78, 9: 0.88, 10: 1.05,
    11: 1.20, 12: 1.35,
}

# Seasonal daily-average AQI baselines per city
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


def _severity(z_abs: float, delta: Optional[float] = None) -> str:
    if (delta is not None and delta > 100) or z_abs >= 4.5:
        return "CRITICAL"
    if (delta is not None and delta > 70) or z_abs >= 3.5:
        return "HIGH"
    if (delta is not None and delta > 40) or z_abs >= 2.5:
        return "MEDIUM"
    return "LOW"


def _synthetic_window(city: str, n: int = 6) -> list:
    """
    Build n synthetic past readings using the diurnal model anchored to the
    city's typical daily-average AQI for the current season.
    This represents 'normal' so that a spike in current_aqi registers as anomalous.
    """
    norm = CITY_NORM.get(city.lower(), city)
    typical_avg = float(CITY_DEFAULTS.get(norm, 150))
    now = datetime.now()
    s_mult = SEASONAL.get(now.month, 1.0)
    # DIURNAL mean = 1.0 by construction, so neutral_base * s_mult = typical_avg
    neutral_base = typical_avg / s_mult
    readings = []
    for h_back in range(n, 0, -1):
        h = (now.hour - h_back) % 24
        readings.append(round(neutral_base * DIURNAL[h] * s_mult, 1))
    return readings


class AnomalyRequest(BaseModel):
    city: str
    current_aqi: float
    # Chronological list of past readings (most recent last). Optional.
    aqi_history: Optional[List[float]] = None


@router.post("/anomaly/detect")
def detect_anomaly(req: AnomalyRequest):
    city = req.city.strip()
    norm_city = CITY_NORM.get(city.lower(), city)
    current = float(req.current_aqi)

    # Sanitise incoming history
    raw_hist = [float(v) for v in (req.aqi_history or []) if 0 <= v <= 500]

    data_quality = "live"
    if len(raw_hist) < 5:
        # Pad with diurnal-model synthetic readings to reach 6-point window
        synthetic = _synthetic_window(city, n=max(0, 6 - len(raw_hist)))
        history = synthetic + raw_hist
        data_quality = "synthetic" if not raw_hist else "mixed"
    else:
        history = raw_hist
        data_quality = "live"

    # ── RAPID_RISE: AQI jumped >50 points in one polling cycle
    rapid_rise = False
    delta_1h: Optional[float] = None
    if raw_hist:
        delta_1h = current - raw_hist[-1]
        if delta_1h > 50:
            rapid_rise = True

    # ── Z-score on 6-point rolling window
    window = history[-6:]
    if len(window) < 2:
        return {
            "is_anomaly": False, "type": "NORMAL", "severity": "LOW",
            "z_score": 0.0,
            "message": "Insufficient data for anomaly detection.",
            "window_mean": current, "window_std": 0.0,
            "data_quality": data_quality,
        }

    w_mean = float(np.mean(window))
    w_std  = float(np.std(window))
    if w_std < 1.0:
        w_std = max(1.0, w_mean * 0.05)   # floor at 5% of mean

    z = (current - w_mean) / w_std

    # ── Classify
    is_anomaly = False
    atype      = "NORMAL"
    message    = f"{norm_city} air quality is within the normal range."

    if rapid_rise and delta_1h is not None:
        is_anomaly = True
        atype = "RAPID_RISE"
        pct = round(delta_1h / max(1, raw_hist[-1]) * 100)
        message = (
            f"{norm_city} AQI rose {int(delta_1h)} points ({pct}%) in the last reading — "
            f"unusually rapid increase. Check for nearby pollution events."
        )
    elif z >= 2.5:
        is_anomaly = True
        atype = "SPIKE"
        pct = round((current - w_mean) / max(1, w_mean) * 100)
        message = (
            f"{norm_city} AQI spiked {pct}% above the recent average "
            f"({int(w_mean)} → {int(current)}). Possible pollution event or weather inversion."
        )
    elif z <= -2.5:
        is_anomaly = True
        atype = "DROP"
        pct = round((w_mean - current) / max(1, w_mean) * 100)
        message = (
            f"{norm_city} AQI dropped {pct}% below recent levels "
            f"({int(w_mean)} → {int(current)}). Possible sensor issue or sudden rainfall."
        )

    return {
        "is_anomaly": is_anomaly,
        "type":       atype,
        "severity":   _severity(abs(z), delta_1h if rapid_rise else None),
        "z_score":    round(z, 2),
        "message":    message,
        "window_mean": round(w_mean, 1),
        "window_std":  round(w_std, 1),
        "data_quality": data_quality,
    }
