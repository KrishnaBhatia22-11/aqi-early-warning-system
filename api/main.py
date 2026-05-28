import os
import threading
import time
import requests as _requests

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

from api.routes import predict, city, chat, forecast, anomaly, models, health
from api.routes import weather, compare, history, share, cropburn, cpcb
from api.routes.db import router as db_router
from api.routes.alerts import router as alerts_router
from api.scheduler import scheduler, save_hourly_snapshot
from api.limiter import limiter


# ── Security headers ──────────────────────────────────────────────────────────

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"]  = "nosniff"
        response.headers["X-Frame-Options"]          = "DENY"
        response.headers["X-XSS-Protection"]         = "1; mode=block"
        response.headers["Referrer-Policy"]           = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"]        = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"]   = "default-src 'self'"
        return response


# ── Rate limit exceeded handler ───────────────────────────────────────────────

async def _rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "error":       "Rate limit exceeded",
            "message":     "Too many requests. Please wait before trying again.",
            "retry_after": "60 seconds",
        },
        headers={"Retry-After": "60"},
    )


# ── API key dependency ────────────────────────────────────────────────────────
# Set VALID_API_KEYS on Render as a comma-separated string, e.g. "key1,key2"
# Requests with a valid key are exempt from rate limits (via _has_valid_api_key
# in api/limiter.py) and receive authenticated access status.

def get_api_key(x_api_key: str = Header(None)):
    if x_api_key is None:
        return None  # anonymous access — rate limited
    valid_keys = os.environ.get("VALID_API_KEYS", "")
    if x_api_key in {k.strip() for k in valid_keys.split(",") if k.strip()}:
        return x_api_key  # authenticated — rate limit exempt
    raise HTTPException(status_code=401, detail="Invalid API key")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI-Driven Early Warning System for Urban Air Quality Risk Zones",
    description="Predicts AQI using ML, explains with SHAP, provides live city data",
    version="1.0.0",
)

# Attach limiter state and 429 handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware order: added first = outermost (first to see request, last to see response)
# CORS must be outermost so preflight responses carry the right headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://aqi-early-warning-system.vercel.app",
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(SlowAPIMiddleware)

# ── Routes ────────────────────────────────────────────────────────────────────

app.include_router(predict.router,   prefix="/api/v1", tags=["Prediction"])
app.include_router(city.router,      prefix="/api/v1", tags=["City Data"])
app.include_router(chat.router,      prefix="/api/v1", tags=["Chatbot"])
app.include_router(forecast.router,  prefix="/api/v1", tags=["Forecast"])
app.include_router(anomaly.router,   prefix="/api/v1", tags=["Anomaly"])
app.include_router(models.router,    prefix="/api/v1", tags=["Models"])
app.include_router(health.router,    prefix="/api/v1", tags=["Health"])
app.include_router(weather.router,   prefix="/api/v1", tags=["Weather"])
app.include_router(compare.router,   prefix="/api/v1", tags=["Compare"])
app.include_router(history.router,   prefix="/api/v1", tags=["History"])
app.include_router(share.router,     prefix="/api/v1", tags=["Share"])
app.include_router(cropburn.router,  prefix="/api/v1", tags=["Crop Burn"])
app.include_router(cpcb.router,      prefix="/api/v1", tags=["CPCB"])
app.include_router(db_router,        prefix="/api/v1", tags=["Database"])
app.include_router(alerts_router,    prefix="/api/v1", tags=["Alerts"])


@app.on_event("startup")
async def startup_event():
    import api.models  # noqa: F401 — registers models with Base.metadata
    from api.database import init_db
    await init_db()

    await save_hourly_snapshot()
    scheduler.add_job(save_hourly_snapshot, "interval", minutes=60)
    scheduler.start()


@app.on_event("startup")
async def print_routes():
    for route in app.routes:
        print(route.path)


@app.get("/")
def root():
    return {
        "project": "AI-Driven Early Warning System for Urban Air Quality Risk Zones",
        "version": "1.0.0",
        "status":  "running",
        "docs":    "/docs",
    }


@app.get("/health")
def health_check():
    from datetime import datetime, timezone
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


def _keep_alive():
    """Ping own /health every 14 min so Render never idles the dyno."""
    while True:
        time.sleep(14 * 60)
        try:
            _requests.get("https://aqi-api-y2qs.onrender.com/health", timeout=10)
        except Exception:
            pass


threading.Thread(target=_keep_alive, daemon=True).start()
