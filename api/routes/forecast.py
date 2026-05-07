import os
import sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

router = APIRouter()

# ── Cache: city_key → { ts, data }
_cache: dict = {}
CACHE_TTL = 3600  # 1 hour

DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "raw", "city_day.csv"
)

# Normalise frontend city names to CSV city names
CITY_NORM = {
    "bangalore":         "Bengaluru",
    "bengalore":         "Bengaluru",
    "bengaluru":         "Bengaluru",
    "cochin":            "Kochi",
    "ernakulam":         "Ernakulam",
    "thiruvananthapuram":"Thiruvananthapuram",
    "trivandrum":        "Thiruvananthapuram",
    "vizag":             "Visakhapatnam",
    "visakhapatnam":     "Visakhapatnam",
}


def _cat(aqi: float) -> str:
    if aqi <= 50:   return "Good"
    if aqi <= 100:  return "Satisfactory"
    if aqi <= 200:  return "Moderate"
    if aqi <= 300:  return "Poor"
    if aqi <= 400:  return "Very Poor"
    return "Severe"


def _recommendation(peak: float, trend: str) -> str:
    if peak > 400:
        return "Hazardous air quality expected. Stay indoors all day and seal windows."
    if peak > 300:
        if trend == "RISING":
            return "Severe pollution rising throughout the day. Avoid all outdoor exposure and wear an N95 mask."
        return "Very poor air quality forecast. Avoid outdoor activities. N95 mask mandatory if going out."
    if peak > 200:
        if trend == "RISING":
            return "Air quality will worsen significantly. Limit outdoor activities to morning hours only."
        return "Poor air quality expected. Sensitive groups should stay indoors and limit outdoor exertion."
    if peak > 100:
        return "Moderate pollution forecast. Sensitive individuals should avoid prolonged outdoor activities."
    if peak > 50:
        return "Satisfactory air quality ahead. Most activities are safe; sensitive groups should take brief breaks indoors."
    return "Clean air forecast for the next 24 hours. Enjoy outdoor activities freely."


class ForecastRequest(BaseModel):
    city: str


@router.post("/forecast")
def forecast_aqi(req: ForecastRequest):
    city_input = req.city.strip()
    csv_city = CITY_NORM.get(city_input.lower(), city_input)

    # ── Cache hit
    now_ts = datetime.now().timestamp()
    entry = _cache.get(csv_city.lower())
    if entry and (now_ts - entry["ts"]) < CACHE_TTL:
        return entry["data"]

    # ── Load & filter CSV
    try:
        df = pd.read_csv(DATA_PATH)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Dataset not found on server.")

    city_df = (
        df[df["City"].str.lower() == csv_city.lower()][["Date", "AQI"]]
        .dropna()
        .copy()
    )

    if len(city_df) < 30:
        raise HTTPException(
            status_code=404,
            detail=f"No sufficient data for '{city_input}'. Available cities include Delhi, Mumbai, Bengaluru, Chennai, Kolkata, Hyderabad, Ahmedabad, Jaipur, Lucknow, Patna, Chandigarh, Amritsar, Guwahati, Thiruvananthapuram, Visakhapatnam, Coimbatore, Kochi.",
        )

    city_df["ds"] = pd.to_datetime(city_df["Date"])
    city_df["y"]  = city_df["AQI"].astype(float)
    city_df = city_df[["ds", "y"]].sort_values("ds").drop_duplicates("ds")

    # ── Fit Prophet
    try:
        from prophet import Prophet  # lazy import — slow first time
    except ImportError:
        raise HTTPException(status_code=500, detail="Prophet not installed on server.")

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.3,
        seasonality_prior_scale=10,
    )
    model.fit(city_df)

    # ── 24 hourly future points
    last_date = city_df["ds"].max()
    future_ds = [last_date + timedelta(hours=i + 1) for i in range(24)]
    future    = pd.DataFrame({"ds": future_ds})
    fc        = model.predict(future)

    fc["yhat"]       = fc["yhat"].clip(0, 500)
    fc["yhat_lower"] = fc["yhat_lower"].clip(0, 500)
    fc["yhat_upper"] = fc["yhat_upper"].clip(0, 500)

    # ── Display hours anchored to current clock time
    base = datetime.now().replace(minute=0, second=0, microsecond=0)
    items = []
    for i, (_, row) in enumerate(fc.iterrows()):
        aqi_v = int(round(row["yhat"]))
        items.append({
            "hour":     (base + timedelta(hours=i)).strftime("%H:%M"),
            "aqi":      aqi_v,
            "upper":    int(round(row["yhat_upper"])),
            "lower":    int(round(row["yhat_lower"])),
            "category": _cat(aqi_v),
        })

    vals      = [it["aqi"] for it in items]
    peak_i    = int(np.argmax(vals))
    low_i     = int(np.argmin(vals))
    peak      = {"hour": items[peak_i]["hour"], "aqi": items[peak_i]["aqi"], "category": items[peak_i]["category"]}
    low       = {"hour": items[low_i]["hour"],  "aqi": items[low_i]["aqi"],  "category": items[low_i]["category"]}

    diff  = float(np.mean(vals[12:])) - float(np.mean(vals[:12]))
    trend = "RISING" if diff > 10 else ("FALLING" if diff < -10 else "STABLE")

    peak_cat = _cat(peak["aqi"])
    low_cat  = _cat(low["aqi"])
    severity = f"{low_cat} to {peak_cat}" if low_cat != peak_cat else peak_cat

    result = {
        "city":              city_input,
        "generated_at":      datetime.now().isoformat(),
        "forecast":          items,
        "peak":              peak,
        "low":               low,
        "trend":             trend,
        "severity_forecast": severity,
        "recommendation":    _recommendation(peak["aqi"], trend),
    }

    _cache[csv_city.lower()] = {"ts": now_ts, "data": result}
    return result
