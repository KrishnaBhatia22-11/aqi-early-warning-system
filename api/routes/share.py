"""
Social share cards — live, per-city Open Graph images + share landing pages.

Social crawlers (WhatsApp / Twitter / LinkedIn) do not execute JS, so a shared
city link must resolve to static HTML carrying per-city OG tags, whose og:image
is a real PNG rendered here from the SAME live data the rest of the API serves.

  GET /api/v1/og/{slug}.png   → 1200x630 PNG card (Pillow), 15-min in-memory cache
  GET /api/v1/share/{slug}    → minimal HTML with per-city OG/Twitter tags + redirect

Category thresholds + labels come ONLY from waqi_client.categorize_aqi — this file
never re-defines AQI bands. _CATEGORY_COLORS just maps those category names to a
hex tuned for the dark card.
"""

import io
import os
import re
import sys
import json
import time
import html
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from fastapi import APIRouter
from fastapi.responses import Response, HTMLResponse
from PIL import Image, ImageDraw, ImageFont

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.data.waqi_client import fetch_city_aqi, categorize_aqi
from config.settings import CITY_COORDS

router = APIRouter()

# ── Absolute URLs — social crawlers require absolute og:image / og:url ──────────
BACKEND  = "https://aqi-api-y2qs.onrender.com"
FRONTEND = "https://aqi-early-warning-system.vercel.app"

# ── Card design tokens ──────────────────────────────────────────────────────────
W, H   = 1200, 630
MARGIN = 72
STRIPE = 14
BG     = "#08080a"
INK    = "#f3f1ee"   # near-white text
DIM    = "#9b958c"   # muted text
ACCENT = "#FF6B00"   # site accent (orange)

# Hex per AQI category. Keys MUST match categorize_aqi()'s return values; thresholds
# live solely in categorize_aqi — we never re-derive bands here.
_CATEGORY_COLORS = {
    "Good":         "#22c55e",
    "Satisfactory": "#84cc16",
    "Moderate":     "#f59e0b",
    "Poor":         "#FF6B00",
    "Very Poor":    "#ef4444",
    "Severe":       "#c2002a",
    "Unknown":      DIM,
}

# ── Slug ↔ city ─────────────────────────────────────────────────────────────────
def _slugify(name: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', (name or "").lower()).strip('-')

_SLUG_TO_CITY = {_slugify(c): c for c in CITY_COORDS}

# ── Fonts: prefer bundled Inter (variable), then DejaVu, then PIL default ─────────
_FONTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'fonts')


def _load_font(size: int, bold: bool = False):
    """Bundled Inter (weight axis) → bundled static → PIL default. Never raises."""
    inter = os.path.join(_FONTS_DIR, "InterVariable.ttf")
    if os.path.exists(inter):
        try:
            f = ImageFont.truetype(inter, size)
            try:
                f.set_variation_by_axes([700 if bold else 400])
            except Exception:
                pass  # freetype without variation support → default (regular) instance
            return f
        except Exception:
            pass
    statics = (["Inter-Bold.ttf", "DejaVuSans-Bold.ttf"] if bold
               else ["Inter-Regular.ttf", "DejaVuSans.ttf"])
    for name in statics:
        p = os.path.join(_FONTS_DIR, name)
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    try:
        return ImageFont.load_default(size)
    except Exception:
        return ImageFont.load_default()


def _fit_font(draw, text, max_w, start, bold=False, min_size=28):
    """Shrink font until `text` fits within max_w (keeps long city names on one line)."""
    size = start
    while size > min_size:
        f = _load_font(size, bold=bold)
        if draw.textlength(text, font=f) <= max_w:
            return f
        size -= 4
    return _load_font(min_size, bold=bold)


def _ist_now():
    """IST = UTC+5:30 — computed from UTC so it is correct regardless of server TZ."""
    return datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)


# ── Shared drawing pieces ─────────────────────────────────────────────────────────
def _new_canvas(stripe_color):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, STRIPE, H], fill=stripe_color)
    return img, d


def _draw_footer(d, accent, station_count=None):
    d.line([MARGIN, 542, W - MARGIN, 542], fill="#1c1c22", width=1)
    d.text((MARGIN, 556), "AQI EARLY WARNING SYSTEM",
           font=_load_font(26, bold=True), fill=INK, anchor="la")
    d.text((MARGIN, 592), f"LIVE · {_ist_now():%H:%M} IST",
           font=_load_font(21), fill=accent, anchor="la")
    if station_count:
        try:
            n = int(station_count)
            if n > 0:
                d.text((W - MARGIN, 592), f"{n} station{'s' if n != 1 else ''}",
                       font=_load_font(21), fill=DIM, anchor="ra")
        except (TypeError, ValueError):
            pass


def _draw_chips(d, items, x, y, h=60):
    pad, gap = 22, 16
    lf, vf = _load_font(22), _load_font(26, bold=True)
    for label, value in items:
        lw = d.textlength(label, font=lf)
        vw = d.textlength(value, font=vf)
        w = pad + lw + 12 + vw + pad
        d.rounded_rectangle([x, y, x + w, y + h], radius=14,
                            fill="#15151a", outline="#2a2a31", width=1)
        cy = y + h / 2
        d.text((x + pad, cy), label, font=lf, fill=DIM, anchor="lm")
        d.text((x + pad + lw + 12, cy), value, font=vf, fill=INK, anchor="lm")
        x += w + gap


# ── Card renderers ─────────────────────────────────────────────────────────────
def _render_city(city, data):
    aqi = int(data["aqi"])
    cat = categorize_aqi(aqi)                       # reuse: thresholds + label
    col = _CATEGORY_COLORS.get(cat, ACCENT)
    img, d = _new_canvas(col)

    d.text((MARGIN, 70), "LIVE AIR QUALITY · INDIA",
           font=_load_font(24, bold=True), fill=col, anchor="la")
    cf = _fit_font(d, city, W - 2 * MARGIN, 92, bold=True, min_size=52)
    d.text((MARGIN, 104), city, font=cf, fill=INK, anchor="la")

    bf = _load_font(224, bold=True)
    d.text((MARGIN, 432), str(aqi), font=bf, fill=col, anchor="ls")
    sx = MARGIN + d.textlength(str(aqi), font=bf) + 46
    d.text((sx, 360), "AQI", font=_load_font(30), fill=DIM, anchor="ls")
    catf = _fit_font(d, cat, W - sx - MARGIN, 58, bold=True, min_size=30)
    d.text((sx, 416), cat, font=catf, fill=col, anchor="ls")

    chips = []
    for label, key in (("PM2.5", "pm25"), ("PM10", "pm10"), ("NO2", "no2"), ("O3", "o3")):
        v = data.get(key)
        if v is not None:
            try:
                chips.append((label, str(int(round(float(v))))))
            except (TypeError, ValueError):
                pass
    if chips:
        _draw_chips(d, chips, MARGIN, 472)

    _draw_footer(d, col, station_count=data.get("station_count"))
    return img


def _render_default():
    img, d = _new_canvas(ACCENT)
    d.text((MARGIN, 78), "REAL-TIME · INDIA",
           font=_load_font(26, bold=True), fill=ACCENT, anchor="la")
    hf = _fit_font(d, "India's Air, Live.", W - 2 * MARGIN, 116, bold=True, min_size=60)
    d.text((MARGIN, 150), "India's Air, Live.", font=hf, fill=INK, anchor="la")
    sub = f"Real-time AQI for {len(CITY_COORDS)} cities · Free forever"
    sf = _fit_font(d, sub, W - 2 * MARGIN, 44, min_size=28)
    d.text((MARGIN, 322), sub, font=sf, fill="#d7d2c9", anchor="la")
    d.text((MARGIN, 386), "ML forecasts · Health impact · Anomaly alerts",
           font=_load_font(30), fill=DIM, anchor="la")
    _draw_footer(d, ACCENT)
    return img


def _render_nodata(city):
    gray = "#6b6b73"
    img, d = _new_canvas(gray)
    d.text((MARGIN, 78), "LIVE AIR QUALITY · INDIA",
           font=_load_font(26, bold=True), fill=gray, anchor="la")
    cf = _fit_font(d, city, W - 2 * MARGIN, 100, bold=True, min_size=54)
    d.text((MARGIN, 150), city, font=cf, fill=INK, anchor="la")
    d.text((MARGIN, 330), "Live data unavailable", font=_load_font(46), fill=DIM, anchor="la")
    d.text((MARGIN, 392), "Check back shortly for real-time readings.",
           font=_load_font(28), fill=gray, anchor="la")
    _draw_footer(d, ACCENT)
    return img


def _safe_fallback_png():
    """Absolute last resort so the endpoint NEVER 500s."""
    try:
        img, d = _new_canvas(ACCENT)
        d.text((W / 2, H / 2), "AQI EARLY WARNING SYSTEM",
               font=_load_font(46, bold=True), fill=INK, anchor="mm")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        buf = io.BytesIO()
        Image.new("RGB", (W, H), BG).save(buf, format="PNG")
        return buf.getvalue()


def _generate_png(slug):
    """Render the PNG for a slug. Catches everything → always returns bytes."""
    try:
        if slug == "default":
            img = _render_default()
        else:
            city = _SLUG_TO_CITY.get(slug)
            if not city:
                img = _render_nodata(slug.replace('-', ' ').title() or "Unknown")
            else:
                data = fetch_city_aqi(city)             # reuse — never duplicated
                if data and data.get("success") and data.get("aqi") is not None:
                    img = _render_city(city, data)
                else:
                    img = _render_nodata(city)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as e:
        print(f"[OG] {slug}: {e}")
        return _safe_fallback_png()


# ── In-memory TTL cache so crawlers don't regenerate the image every hit ─────────
_CARD_CACHE = {}     # slug -> (created_ts, png_bytes)
_CARD_TTL   = 900    # 15 minutes


@router.get("/og/{slug}.png")
def og_image(slug: str):
    slug = (slug or "").lower()
    cacheable = slug == "default" or slug in _SLUG_TO_CITY   # don't let random slugs grow the cache
    now = time.time()

    hit = _CARD_CACHE.get(slug)
    if hit and now - hit[0] < _CARD_TTL:
        png = hit[1]
    else:
        png = _generate_png(slug)
        if cacheable:
            _CARD_CACHE[slug] = (now, png)

    return Response(content=png, media_type="image/png",
                    headers={"Cache-Control": "public, max-age=900"})


# ── Per-city share landing — OG tags for crawlers, redirect for humans ───────────
def _share_html(title, desc, image, share_url, redirect):
    t, de = html.escape(title), html.escape(desc)
    im, su, rd = html.escape(image), html.escape(share_url), html.escape(redirect)
    js = json.dumps(redirect)   # safe JS string literal for the <script> redirect
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t}</title>
<meta name="description" content="{de}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="AQI Early Warning System">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{de}">
<meta property="og:url" content="{su}">
<meta property="og:image" content="{im}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{t}">
<meta name="twitter:description" content="{de}">
<meta name="twitter:image" content="{im}">
<meta http-equiv="refresh" content="0; url={rd}">
<script>window.location.replace({js});</script>
</head>
<body style="margin:0;background:#08080a;color:#f3f1ee;font-family:system-ui,-apple-system,sans-serif">
<p style="padding:28px;font-size:15px">Loading live air quality…
<a href="{rd}" style="color:#FF6B00">Continue&nbsp;&rsaquo;</a></p>
</body>
</html>"""


@router.get("/share/{slug}")
def share_landing(slug: str):
    slug = (slug or "").lower()
    city = _SLUG_TO_CITY.get(slug)
    share_url = f"{BACKEND}/api/v1/share/{slug}"

    # Unknown slug → still valid HTML, branded default card, redirect to app root
    if not city:
        return HTMLResponse(
            _share_html(
                title="AQI Early Warning System — India's Air, Live",
                desc="Live, real-time air quality for Indian cities. ML forecasts, health impact, free forever.",
                image=f"{BACKEND}/api/v1/og/default.png",
                share_url=share_url,
                redirect=f"{FRONTEND}/",
            ),
            headers={"Cache-Control": "public, max-age=900"},
        )

    data = fetch_city_aqi(city)
    if data and data.get("success") and data.get("aqi") is not None:
        aqi = int(data["aqi"])
        title = f"{city} AQI: {aqi} — {categorize_aqi(aqi)}"
    else:
        title = f"{city} air quality — live"

    return HTMLResponse(
        _share_html(
            title=title,
            desc=f"Live air quality for {city}. ML forecasts, health impact, free forever.",
            image=f"{BACKEND}/api/v1/og/{slug}.png",
            share_url=share_url,
            redirect=f"{FRONTEND}/cities?city={quote(city)}",
        ),
        headers={"Cache-Control": "public, max-age=900"},
    )
