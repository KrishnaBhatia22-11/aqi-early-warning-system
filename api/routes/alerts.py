import os
import re
import secrets

import resend
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from api.database import AsyncSessionLocal
from api.models import AlertSubscription
from config.settings import CITY_COORDS
from api.limiter import limiter, _has_valid_api_key

resend.api_key = os.environ.get("RESEND_API_KEY", "")  # Render env var: RESEND_API_KEY

router = APIRouter()

_EMAIL_RE     = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
_KNOWN_CITIES = set(CITY_COORDS.keys())
_UNSUBSCRIBE_BASE = "https://aqi-api-y2qs.onrender.com/api/v1/alerts/unsubscribe"


class SubscribeRequest(BaseModel):
    email: str
    city: str
    threshold: int = 150


@router.post("/alerts/subscribe")
@limiter.limit("5/minute", exempt_when=_has_valid_api_key)
async def subscribe(req: SubscribeRequest, request: Request):
    if not _EMAIL_RE.match(req.email):
        return {"success": False, "message": "Invalid email address"}
    if req.city not in _KNOWN_CITIES:
        return {"success": False, "message": f"Unknown city: {req.city}"}
    if not (50 <= req.threshold <= 500):
        return {"success": False, "message": "Threshold must be between 50 and 500"}

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AlertSubscription)
                .where(AlertSubscription.email == req.email)
                .where(AlertSubscription.city == req.city)
            )
            existing = result.scalar_one_or_none()

            if existing:
                existing.threshold = req.threshold
                existing.active = True
                token = existing.token
            else:
                token = secrets.token_urlsafe(32)
                session.add(AlertSubscription(
                    email=req.email,
                    city=req.city,
                    threshold=req.threshold,
                    token=token,
                ))
            await session.commit()

        unsubscribe_url = f"{_UNSUBSCRIBE_BASE}/{token}"
        resend.Emails.send({
            "from": "AQI Alerts <onboarding@resend.dev>",
            "to": [req.email],
            "subject": f"Alert set — {req.city} at AQI {req.threshold}",
            "html": f"""
<html>
<body style="font-family:sans-serif;background:#f0f4f8;padding:32px;margin:0">
  <div style="max-width:480px;margin:0 auto;background:#fff;border-radius:12px;
              padding:36px;box-shadow:0 2px 12px rgba(0,0,0,0.08)">
    <h2 style="color:#22c55e;margin-top:0;font-size:22px">✓ Alert Created</h2>
    <p style="font-size:16px;color:#333;line-height:1.6">
      You will receive an email alert when <strong>{req.city}</strong> AQI crosses
      <strong style="color:#ef4444">{req.threshold}</strong>.
    </p>
    <p style="font-size:13px;color:#94a3b8;margin-top:32px;
              border-top:1px solid #e2e8f0;padding-top:16px">
      Don't want these emails?
      <a href="{unsubscribe_url}" style="color:#22c55e;text-decoration:none">Unsubscribe</a>
    </p>
  </div>
</body>
</html>""",
        })

        return {"success": True, "message": "Alert created"}

    except Exception as e:
        return {"success": False, "message": str(e)}


@router.get("/alerts/unsubscribe/{token}")
async def unsubscribe(token: str):
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AlertSubscription).where(AlertSubscription.token == token)
            )
            sub = result.scalar_one_or_none()
            if not sub:
                return {"success": False, "message": "Token not found"}
            sub.active = False
            await session.commit()
        return {"success": True, "message": "Unsubscribed successfully"}
    except Exception as e:
        return {"success": False, "message": str(e)}
