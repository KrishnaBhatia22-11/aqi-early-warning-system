from typing import List, Optional

import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

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

    # Anomaly detection needs real readings. Nothing is padded or invented: with fewer than
    # 5 real past readings the answer is "not available".
    if len(raw_hist) < 5:
        return {
            "available": False,
            "reason": f"Needs at least 5 real past readings for {norm_city}; got {len(raw_hist)}. "
                      "No history is invented.",
            "is_anomaly": False, "type": "NO_DATA", "severity": "LOW", "z_score": None,
            "message": "Anomaly detection unavailable: not enough real readings.",
            "window_mean": None, "window_std": None, "data_quality": "none",
        }
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
