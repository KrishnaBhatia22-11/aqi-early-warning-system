import os
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()


class CityCtx(BaseModel):
    name: str
    aqi: int
    pollutant: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    cities: List[CityCtx] = []
    history: List[dict] = []


SYSTEM_PROMPT = (
    "You are AQI Bot, an AI assistant for India's AQI Early Warning System. "
    "You help users understand air quality, health impacts, and pollution sources. "
    "Be concise (2–3 sentences), factual, and friendly. "
    "Use **bold** for key terms. "
    "The system uses an XGBoost model (R²=0.932, MAE=21.33) trained on CPCB data 2015–2020 for 26 cities."
)


@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    groq_key = os.environ.get("GROQ_API_KEY", "")

    city_lines = "\n".join(
        f"- {c.name}: AQI {c.aqi}" + (f" (primary pollutant: {c.pollutant})" if c.pollutant else "")
        for c in req.cities[:12]
    )
    system = SYSTEM_PROMPT + (
        f"\n\nCurrent live AQI readings:\n{city_lines}" if city_lines else ""
    )

    if not groq_key:
        return {
            "reply": "Groq AI is not configured on this server. Set the GROQ_API_KEY environment variable on Render to enable real AI responses.",
            "source": "error",
        }

    try:
        from groq import Groq
        client = Groq(api_key=groq_key)

        messages = [{"role": "system", "content": system}]
        for h in req.history[-6:]:
            role = h.get("role")
            content = h.get("content") or h.get("text", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": req.message})

        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            max_tokens=250,
            temperature=0.6,
        )
        reply = resp.choices[0].message.content.strip()
        return {"reply": reply, "source": "groq"}

    except Exception as e:
        return {
            "reply": "AI is temporarily unavailable. Please try again in a moment.",
            "source": "error",
            "detail": str(e),
        }
