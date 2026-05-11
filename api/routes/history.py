from fastapi import APIRouter, HTTPException, Query
import requests
import os
from datetime import datetime

router = APIRouter()

WAQI_TOKEN = os.getenv("WAQI_TOKEN", "")

CITY_SLUGS = {
    "Delhi": "delhi",
    "Mumbai": "mumbai",
    "Bangalore": "bangalore",
    "Chennai": "chennai",
    "Kolkata": "kolkata",
    "Hyderabad": "hyderabad",
    "Ahmedabad": "ahmedabad",
    "Pune": "pune",
    "Jaipur": "jaipur",
    "Lucknow": "lucknow",
    "Kanpur": "kanpur",
    "Patna": "patna",
    "Bhopal": "bhopal",
    "Nagpur": "nagpur",
    "Surat": "surat",
    "Visakhapatnam": "visakhapatnam",
    "Chandigarh": "chandigarh",
    "Indore": "indore",
}


@router.get("/history/{city}")
async def get_history(
    city: str,
    days: int = Query(default=7, ge=1, le=30),
):
    if not WAQI_TOKEN:
        raise HTTPException(status_code=503, detail="WAQI API key not configured")

    slug = CITY_SLUGS.get(city, city.lower())

    try:
        url = f"https://api.waqi.info/feed/{slug}/?token={WAQI_TOKEN}"
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get("status") != "ok":
            raise HTTPException(status_code=404, detail=f"No data available for {city}")

        city_data = data["data"]
        current_aqi = city_data.get("aqi", 0)
        current_time = city_data.get("time", {}).get("s", "")

        forecast = city_data.get("forecast", {})
        daily = forecast.get("daily", {})
        pm25_daily = daily.get("pm25", [])

        history_points = []
        for entry in pm25_daily:
            day = entry.get("day", "")
            avg = entry.get("avg")
            min_val = entry.get("min")
            max_val = entry.get("max")

            if avg is not None:
                aqi_approx = int(avg)
                history_points.append({
                    "date": day,
                    "aqi": min(aqi_approx, 500),
                    "aqi_min": int(min_val) if min_val is not None else None,
                    "aqi_max": int(max_val) if max_val is not None else None,
                    "pm25_avg": avg,
                    "source": "WAQI",
                    "is_forecast": False,
                })

        history_points.sort(key=lambda x: x["date"])

        today = datetime.utcnow().strftime("%Y-%m-%d")
        past_points = [p for p in history_points if p["date"] <= today]

        if not past_points:
            return {
                "city": city,
                "message": "Historical breakdown not available from WAQI for this city. Showing current reading only.",
                "current_aqi": current_aqi,
                "current_time": current_time,
                "history": [],
                "source": "WAQI",
                "data_available": False,
            }

        aqi_values = [p["aqi"] for p in past_points]

        return {
            "city": city,
            "history": past_points,
            "current_aqi": current_aqi,
            "current_time": current_time,
            "summary": {
                "avg_aqi": round(sum(aqi_values) / len(aqi_values)),
                "max_aqi": max(aqi_values),
                "min_aqi": min(aqi_values),
                "days_available": len(past_points),
                "worst_day": past_points[aqi_values.index(max(aqi_values))]["date"],
                "best_day": past_points[aqi_values.index(min(aqi_values))]["date"],
            },
            "source": "WAQI — World Air Quality Index",
            "data_available": True,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")
