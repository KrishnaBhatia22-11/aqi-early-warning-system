import asyncio
import os
import re
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from api.limiter import limiter
from src.data.india_aqi import categorize_aqi  # single CPCB category helper (shared with predict)

_HTML_RE       = re.compile(r'<[^>]+>')
_SUSPICION_RE  = re.compile(
    r'(<script|javascript:|on\w+\s*=|eval\s*\(|exec\s*\(|__import__|DROP\s+TABLE|'
    r'SELECT\s+\*|INSERT\s+INTO|UNION\s+SELECT)',
    re.IGNORECASE,
)

router = APIRouter()

SUGGESTED_QUESTIONS = [
    "What is Delhi's AQI right now?",
    "Is it safe to exercise in Mumbai today?",
    "Is crop burning happening right now?",
    "Which city has the worst air quality today?",
    "What does AQI 150 mean for my health?",
    "How does your ML model work?",
    "Which cities are in the database?",
    "What is PM2.5 and why does it matter?",
]

SYSTEM_PROMPT = """
You are AQI Bot — the official AI assistant of the AQI
Early Warning System (aqi-early-warning-system.vercel.app).
You are a knowledgeable air quality specialist for India.
Built by Krishna Bhatia, Full Stack ML Engineer,
Manav Rachna International Institute of Research and
Studies, Faridabad.

ABOUT THIS PRODUCT:
- Real-time air quality for Indian cities, from the official CPCB feed
- Free to use — built for Indians
- Built in Faridabad

TECH STACK:
- ML Model: XGBoost regressor (see ML MODEL DETAILS for honest accuracy figures)
- Trained on city_day.csv (2015-2020, 26 cities)
- Backend: FastAPI on Render
- Frontend: React + Tailwind + Vite on Vercel
- Database: PostgreSQL — stores AQI readings
- AI Chatbot: Groq LLaMA (that's you)
- Live AQI: official CPCB feed (data.gov.in), multi-station averaging, India CPCB National AQI
- Weather: OpenWeatherMap API
- Satellite fires: NASA FIRMS VIIRS satellite
- Auth: JWT in sessionStorage
- PWA: Installable, works offline

PAGES AND FEATURES:
/ — Homepage with real India map and live city AQI
/predict — XGBoost AQI predictor with input dials
/health — Health Impact Calculator:
  cigarette equivalent, WHO limit %, PM2.5 inhaled,
  life minutes lost per day
/forecast — 24-hour AQI forecast using physics-informed
  diurnal model
/cities — City Intelligence Dashboard — all covered cities
/compare — Compare any two cities side by side
/history — AQI Time Machine — historical data
/weather — Weather + AQI correlation page
/cropburn — Crop Burning Early Warning System:
  4 signals: seasonal calendar, Punjab AQI spike detection,
  downwind city pattern, NASA FIRMS satellite fires
  Wheat season: Apr 15 - May 31 (Punjab + Haryana)
  Paddy season: Oct 1 - Nov 30 (Punjab + Haryana)
/chatbot — That's you
/alerts — AQI Threshold Alerts with email notifications
/models — Model Intelligence: model evaluation figures
/about — About page
/api — Public API documentation

DATA ARCHITECTURE:
- Indian cities covered: use the live city list injected below; do not quote a fixed count
- Multi-station averaging with outlier removal (station counts are in the live data)
- Stations older than 48h are dropped, never shown as current
- Every reading shows station count and data quality
- NEVER shows fake or synthetic data
- Database: readings are saved on a schedule; the live reading count is injected below
- Scheduler saves every covered city every 60 minutes
- AQI standard: India CPCB National AQI (NOT US EPA)

CROP BURNING SYSTEM:
- Signal 1: Punjab cities AQI spike vs 7-day DB baseline
- Signal 2: Downwind cities (Delhi, Lucknow, Kanpur) spike
- Signal 3: Seasonal calendar (CPCB + IMD data)
- Signal 4: NASA FIRMS VIIRS satellite fire count
- Bounding box: Punjab + Haryana + Western UP
- 3-hour cache on satellite data
- Confidence 0-100: 25=season only, 65+=active burning,
  85+=peak event

AQI CATEGORIES (India CPCB National AQI — the ONLY scale this app uses):
0-50: Good — green
51-100: Satisfactory — light green
101-200: Moderate — yellow
201-300: Poor — orange
301-400: Very Poor — red
401-500: Severe — maroon

Never describe these numbers on the US EPA scale. The same concentration gives a
different number on each scale, so a US category name against a CPCB value would
be wrong. CPCB has no "Hazardous" or "Unhealthy for Sensitive Groups" band.
The AQI is the MAXIMUM of the per-pollutant sub-indices, not an average, and
CPCB requires at least 3 pollutants including PM2.5 or PM10 before publishing
one — which is why some cities honestly show NO DATA.

HEALTH FACTS YOU KNOW:
- 1 cigarette = ~22 μg/m³ PM2.5 exposure over 24h
- WHO safe limit: 15 μg/m³ annual mean PM2.5
- India's NAAQS limit: 60 μg/m³ annual mean PM2.5
- Delhi average PM2.5 in winter: 150-300 μg/m³
- Crop burning contributes up to 40% of Delhi PM2.5
  in November (SAFAR India)
- Smoke travels 500-1000 km from Punjab to Delhi
- ~35 million tonnes of crop residue burned annually
  in Punjab alone (CPCB)

ML MODEL DETAILS (state ONLY these figures; never invent accuracy numbers):
- Algorithm: XGBoost regressor estimating AQI from same-day pollutant readings
- Features (12): PM2.5, PM10, NO, NO2, NOx, NH3, CO, SO2, O3, Month, Year, Season_Code
- Training data: city_day.csv, 2015-2020
- Model file: best_model.pkl
- The headline "R²=0.932" that older text quotes came from a RANDOM row split, where
  neighbouring days of a city sit in both train and test. It overstates real accuracy.
  Do not present it as the model's accuracy.
- Honest evaluation (temporal test: train 2015-2018, tune on 2019, test Jan-Jul 2020,
  4,404 rows, 26 cities, pollutant-only features):
  XGBoost tuned on 2019: R² 0.898, MAE 15.8 AQI points
  The CPCB formula computed from daily means: R² 0.842, MAE 18.1
  Linear regression: R² 0.834, MAE 21.1
  XGBoost vs the formula: MAE difference -2.2, 95% CI -4.7 to +0.3 — not statistically significant.
- Caveats to mention when asked: the CPCB formula here uses daily means (the official method
  uses 8-hour means for CO and O3); the deployed model file itself was trained on rows that include
  2020, so it was not scored on that test; LightGBM and Random Forest were not re-evaluated.
- Do not make superlative accuracy claims about the model or the platform.

BACKEND API ROUTES:
POST /api/v1/predict — XGBoost prediction
GET  /api/v1/cities — live cities with multi-station data
GET  /api/v1/weather/{city} — OpenWeatherMap data
POST /api/v1/forecast — 24H diurnal forecast
POST /api/v1/health/impact — health calculator
GET  /api/v1/compare — city comparison
GET  /api/v1/history/{city} — historical data
GET  /api/v1/cropburn/status — burning detector
GET  /api/v1/anomaly/detect — Z-score spike detection
GET  /api/v1/models/comparison — ML benchmarks
POST /api/v1/chat — this endpoint (you)
GET  /api/v1/db/status — database health
GET  /api/v1/db/latest — most recent readings
GET  /api/v1/alerts/subscribe — email alert signup

PRODUCT PRINCIPLES:
1. REAL DATA ONLY — never show fake/synthetic data
2. HONEST LABELLING — every number shows its source
3. CAREFUL — multi-station averages not single sensor
4. TRUSTWORTHY — show confidence, show limitations
5. ACTIONABLE — every AQI reading has health advice
6. FREE FOREVER — public health tool, not paywall
7. INDIA FIRST — Indian cities, Indian standards

YOUR PERSONALITY:
- You are a specialist, not a generic AI
- You speak with authority about Indian air quality
- You give specific actionable health advice
- You cite real data from this product
- You can speak in Hindi if the user writes in Hindi
- You never say "I don't have real-time data" because
  you always have it — it's injected below
- You are warm, helpful, and care about people's health
- Keep answers concise but complete
- Use bullet points for lists
- Always mention the live AQI numbers when relevant
- If someone asks about a city, give their current AQI
  from the live data below

LIVE DATA IS INJECTED BELOW THIS LINE.
Always use this data to answer questions.
This data was fetched seconds ago from our own backend.
"""


# ── Individual context fetchers ───────────────────────────────

async def _fetch_cities_ctx() -> str:
    try:
        import sys as _sys
        import os as _os
        _sys.path.append(_os.path.join(_os.path.dirname(__file__), '..', '..'))
        from src.data.cpcb_client import fetch_all_cities
        from api.routes.anomaly import detect_anomaly, AnomalyRequest

        cities = await asyncio.to_thread(fetch_all_cities)
        if not cities:
            return ""

        valid = sorted(
            [c for c in cities if isinstance(c.get("aqi"), (int, float)) and c["aqi"] > 0],
            key=lambda x: x["aqi"],
            reverse=True,
        )

        lines = ["=== LIVE CITY AQI (fetched just now) ==="]
        for c in valid:
            name   = c.get("name") or c.get("city", "Unknown")
            aqi    = int(c["aqi"])
            cat    = categorize_aqi(aqi)
            sc     = c.get("station_count")
            sc_str = f" — {sc} stations" if sc else ""
            lines.append(f"{name}: {aqi} AQI ({cat}){sc_str}")

        # Anomaly detection for top cities
        anomalies = []
        for c in valid[:10]:
            try:
                name = c.get("name") or c.get("city", "")
                aqi  = float(c["aqi"])
                result = await asyncio.to_thread(
                    detect_anomaly,
                    AnomalyRequest(city=name, current_aqi=aqi)
                )
                if result.get("is_anomaly"):
                    anomalies.append(
                        f"{name} ({int(aqi)} AQI): {result.get('type', 'SPIKE')} — "
                        f"{result.get('message', '')}"
                    )
            except Exception:
                pass

        lines.append("")
        lines.append("=== ANOMALIES ===")
        if anomalies:
            lines.extend(anomalies)
        else:
            lines.append("None detected")

        return "\n".join(lines)

    except Exception as e:
        return f"=== LIVE CITY AQI ===\nUnavailable ({e})"


async def _fetch_cropburn_ctx() -> str:
    try:
        from api.routes.cropburn import get_cropburn_status
        d   = await get_cropburn_status()
        sig = d.get("detection_signals", {})

        lines = ["=== CROP BURNING STATUS ==="]
        lines.append(f"Status: {d.get('status', 'UNKNOWN')}")
        lines.append(
            f"Confidence: {d.get('confidence', 0)}% "
            f"({d.get('confidence_level', 'NONE')})"
        )
        lines.append(
            f"NASA fires in Punjab+Haryana: "
            f"{d.get('nasa_fire_count', 0)} ({d.get('nasa_fire_level', 'NONE')})"
        )
        punjab   = sig.get("punjab_cities_spiking", [])
        downwind = sig.get("downwind_cities_spiking", [])
        lines.append(f"Punjab cities spiking: {', '.join(punjab) if punjab else 'none'}")
        lines.append(f"Downwind cities spiking: {', '.join(downwind) if downwind else 'none'}")
        if d.get("season_active"):
            lines.append(
                f"Season: {sig.get('season_name', '')} — "
                f"Day {sig.get('days_into_season', 0)}, "
                f"{sig.get('days_remaining', 0)} days remaining"
            )
        else:
            lines.append(
                f"Off season. Next: {sig.get('next_season', '')} "
                f"in {sig.get('days_until_next', '?')} days"
            )
        return "\n".join(lines)

    except Exception as e:
        return f"=== CROP BURNING STATUS ===\nUnavailable ({e})"


async def _fetch_db_ctx() -> str:
    try:
        from sqlalchemy import text
        from api.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            row_count = (
                await session.execute(text("SELECT COUNT(*) FROM aqi_readings"))
            ).scalar()
            last_ts = (
                await session.execute(text("SELECT MAX(timestamp) FROM aqi_readings"))
            ).scalar()
        lines = ["=== DATABASE ==="]
        lines.append(f"Total readings stored: {row_count}")
        if last_ts:
            lines.append(f"Last snapshot: {last_ts}")
        return "\n".join(lines)

    except Exception as e:
        return f"=== DATABASE ===\nUnavailable ({e})"


async def _fetch_models_ctx() -> str:
    try:
        from api.routes.models import get_model_comparison
        d     = await asyncio.to_thread(get_model_comparison)
        lines = ["=== ML MODEL BENCHMARKS ==="]
        for m in d.get("models", []):
            if m.get("r2") is None:
                lines.append(f"{m['name']} ({m['status']}): no verified figures")
                continue
            lines.append(
                f"{m['name']} ({m['status']}): temporal 2020 test "
                f"R²={m['r2']}, MAE={m['mae']}, RMSE={m['rmse']}"
            )
        lines.append(f"In production: {d.get('winner', 'XGBoost')}")
        lines.append(f"Dataset: {d['dataset']['rows']:,} rows, "
                     f"{d['dataset']['cities']} cities, "
                     f"{d['dataset']['period']}")
        return "\n".join(lines)

    except Exception as e:
        return f"=== ML MODEL BENCHMARKS ===\nUnavailable ({e})"


async def get_live_context() -> str:
    results = await asyncio.gather(
        _fetch_cities_ctx(),
        _fetch_cropburn_ctx(),
        _fetch_db_ctx(),
        _fetch_models_ctx(),
        return_exceptions=True,
    )
    parts = [r for r in results if isinstance(r, str) and r.strip()]
    return "\n\n".join(parts) if parts else "Live data temporarily unavailable."


# ── Request / response models ─────────────────────────────────

class CityCtx(BaseModel):
    name: str
    aqi: int
    pollutant: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    cities: List[CityCtx] = []
    history: List[dict] = []


# ── Route ─────────────────────────────────────────────────────

@router.post("/chat")
@limiter.limit("10/minute")
async def chat_endpoint(req: ChatRequest, request: Request):
    message = _HTML_RE.sub("", req.message).strip()
    if len(message) > 500:
        raise HTTPException(status_code=400, detail="Message must be 500 characters or fewer")
    if _SUSPICION_RE.search(message):
        raise HTTPException(status_code=400, detail="Message contains disallowed content")

    groq_key = os.environ.get("GROQ_API_KEY", "")

    if not groq_key:
        return {
            "reply": (
                "Groq AI is not configured on this server. "
                "Set the GROQ_API_KEY environment variable on Render to enable real AI responses."
            ),
            "source": "error",
            "suggested_questions": SUGGESTED_QUESTIONS,
        }

    try:
        live_context = await get_live_context()
        full_system  = SYSTEM_PROMPT + "\n\nLIVE DATA RIGHT NOW:\n" + live_context

        from groq import Groq
        client = Groq(api_key=groq_key)

        messages = [{"role": "system", "content": full_system}]
        for h in req.history[-6:]:
            role    = h.get("role")
            content = h.get("content") or h.get("text", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": message})

        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            max_tokens=2048,
            temperature=0.6,
        )
        reply = resp.choices[0].message.content.strip()
        return {
            "reply": reply,
            "source": "groq",
            "suggested_questions": SUGGESTED_QUESTIONS,
        }

    except Exception as e:
        return {
            "reply": "AI is temporarily unavailable. Please try again in a moment.",
            "source": "error",
            "detail": str(e),
            "suggested_questions": SUGGESTED_QUESTIONS,
        }
