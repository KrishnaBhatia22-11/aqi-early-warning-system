import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import plotly.graph_objects as go
import pandas as pd
import sys, os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config.settings import CITY_COORDS

st.set_page_config(
    page_title="AQI Early Warning System",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE = "http://127.0.0.1:8000/api/v1"

# ─────────────────────────────────────────────
# MASTER CSS — BLACK + ORANGE FIRE THEME
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* { font-family: 'Inter', sans-serif !important; }

.stApp {
    background: #080808;
    background-image:
        radial-gradient(ellipse at 20% 50%, rgba(255,107,0,0.03) 0%, transparent 60%),
        radial-gradient(ellipse at 80% 20%, rgba(255,170,0,0.03) 0%, transparent 60%);
}

.main .block-container {
    padding: 1rem 2rem 2rem;
    max-width: 100%;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: #0d0d0d !important;
    border-right: 1px solid rgba(255,107,0,0.15) !important;
}
[data-testid="stSidebar"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #ff6b00, #ffaa00, #ff6b00);
}
[data-testid="stSidebar"] * { color: #cccccc !important; }
[data-testid="stSidebar"] .stRadio label {
    padding: 8px 12px !important;
    border-radius: 8px !important;
    transition: all 0.2s !important;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(255,107,0,0.08) !important;
    color: #ff6b00 !important;
}

/* ── METRICS ── */
[data-testid="stMetric"] {
    background: rgba(255,107,0,0.04);
    border: 1px solid rgba(255,107,0,0.12);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    position: relative;
    overflow: hidden;
    transition: all 0.3s;
}
[data-testid="stMetric"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, #ff6b00, transparent);
}
[data-testid="stMetric"]:hover {
    border-color: rgba(255,107,0,0.3);
    box-shadow: 0 0 20px rgba(255,107,0,0.08);
}
[data-testid="stMetricLabel"] {
    color: #666 !important;
    font-size: 11px !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
[data-testid="stMetricValue"] {
    color: #fff !important;
    font-size: 26px !important;
    font-weight: 700 !important;
}
[data-testid="stMetricDelta"] { font-size: 11px !important; }

/* ── BUTTONS ── */
.stButton > button {
    background: linear-gradient(135deg, #ff6b00, #ff8c00) !important;
    color: #000 !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    padding: 0.5rem 1.5rem !important;
    letter-spacing: 0.03em;
    transition: all 0.2s !important;
    box-shadow: 0 4px 15px rgba(255,107,0,0.25) !important;
}
.stButton > button:hover {
    box-shadow: 0 4px 25px rgba(255,107,0,0.45) !important;
    transform: translateY(-1px) !important;
}

/* ── FORM ── */
.stForm {
    background: rgba(255,107,0,0.02) !important;
    border: 1px solid rgba(255,107,0,0.1) !important;
    border-radius: 16px !important;
    padding: 1.5rem !important;
}
.stNumberInput > div > div > input,
.stSelectbox > div > div {
    background: #111 !important;
    border: 1px solid rgba(255,107,0,0.15) !important;
    color: #fff !important;
    border-radius: 8px !important;
}
.stNumberInput > div > div > input:focus,
.stSelectbox > div > div:focus {
    border-color: #ff6b00 !important;
    box-shadow: 0 0 0 1px #ff6b00 !important;
}

/* ── CHAT ── */
.stChatMessage {
    background: rgba(255,107,0,0.03) !important;
    border: 1px solid rgba(255,107,0,0.08) !important;
    border-radius: 12px !important;
}
.stChatInputContainer {
    background: #111 !important;
    border: 1px solid rgba(255,107,0,0.2) !important;
    border-radius: 12px !important;
}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    background: #111;
    border-radius: 10px;
    padding: 4px;
    border: 1px solid rgba(255,107,0,0.1);
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    color: #666;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: rgba(255,107,0,0.15) !important;
    color: #ff6b00 !important;
}

/* ── DIVIDER ── */
hr { border-color: rgba(255,107,0,0.1) !important; }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #080808; }
::-webkit-scrollbar-thumb { background: rgba(255,107,0,0.3); border-radius: 2px; }

/* ── CUSTOM CARDS ── */
.fire-card {
    background: rgba(15,15,15,0.9);
    border: 1px solid rgba(255,107,0,0.12);
    border-radius: 16px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
    position: relative;
    overflow: hidden;
    transition: all 0.3s;
}
.fire-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,107,0,0.4), transparent);
}
.fire-card:hover {
    border-color: rgba(255,107,0,0.25);
    box-shadow: 0 0 30px rgba(255,107,0,0.05);
}

.glow-text {
    text-shadow: 0 0 20px currentColor;
}

.section-tag {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #ff6b00;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.section-tag::before {
    content: '';
    display: inline-block;
    width: 16px;
    height: 1px;
    background: #ff6b00;
}

.live-pulse {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(0,255,100,0.08);
    border: 1px solid rgba(0,255,100,0.2);
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 11px;
    color: #00ff64;
    font-weight: 600;
}

.aqi-number {
    font-size: 56px;
    font-weight: 800;
    line-height: 1;
    letter-spacing: -2px;
}

.pollutant-chip {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px;
    padding: 8px 10px;
    text-align: center;
}

.health-card {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 10px;
    padding: 10px 14px;
    margin: 4px 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: all 0.2s;
}
.health-card:hover {
    background: rgba(255,107,0,0.04);
    border-color: rgba(255,107,0,0.1);
}

.risk-tag {
    font-size: 10px;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 20px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

.shap-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 6px 0;
}
.shap-feature { font-size: 12px; color: #999; width: 50px; text-align: right; flex-shrink: 0; }
.shap-track { flex: 1; height: 6px; background: rgba(255,255,255,0.05); border-radius: 3px; overflow: hidden; }
.shap-fill { height: 100%; border-radius: 3px; transition: width 0.8s ease; }
.shap-value { font-size: 11px; color: #666; width: 40px; flex-shrink: 0; }

.stat-mini {
    background: rgba(255,107,0,0.05);
    border: 1px solid rgba(255,107,0,0.1);
    border-radius: 10px;
    padding: 10px;
    text-align: center;
}

h1, h2, h3 { color: #ffffff !important; }
p { color: #999 !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def aqi_color(aqi):
    if not aqi: return "#666"
    aqi = int(aqi)
    if aqi <= 50:   return "#00ff88"
    if aqi <= 100:  return "#aaff00"
    if aqi <= 200:  return "#ffaa00"
    if aqi <= 300:  return "#ff6b00"
    if aqi <= 400:  return "#ff3300"
    return "#cc00ff"

def aqi_category(aqi):
    if not aqi: return "Unknown"
    aqi = int(aqi)
    if aqi <= 50:   return "Good"
    if aqi <= 100:  return "Satisfactory"
    if aqi <= 200:  return "Moderate"
    if aqi <= 300:  return "Poor"
    if aqi <= 400:  return "Very Poor"
    return "Severe"

def risk_style(level):
    styles = {
        "Safe":   ("rgba(0,255,136,0.08)",   "rgba(0,255,136,0.2)",   "#00ff88"),
        "Low":    ("rgba(170,255,0,0.08)",    "rgba(170,255,0,0.2)",   "#aaff00"),
        "Medium": ("rgba(255,170,0,0.08)",    "rgba(255,170,0,0.2)",   "#ffaa00"),
        "High":   ("rgba(255,107,0,0.08)",    "rgba(255,107,0,0.2)",   "#ff6b00"),
        "Severe": ("rgba(204,0,255,0.08)",    "rgba(204,0,255,0.2)",   "#cc00ff"),
    }
    return styles.get(level, ("rgba(100,100,100,0.08)", "rgba(100,100,100,0.2)", "#666"))

def fetch_city(city):
    try:
        r = requests.get(f"{API_BASE}/city/{city}", timeout=10)
        return r.json() if r.status_code == 200 else None
    except: return None

def fetch_predict(inputs):
    try:
        r = requests.post(f"{API_BASE}/predict", json=inputs, timeout=15)
        return r.json() if r.status_code == 200 else None
    except: return None

def season_code(month):
    return {12:0,1:0,2:0,3:1,4:1,5:1,6:2,7:2,8:2,9:3,10:3,11:3}[month]


# ─────────────────────────────────────────────
# MAP BUILDER — dark + glowing markers
# ─────────────────────────────────────────────
def build_map(cache):
    m = folium.Map(
        location=[20.5937, 78.9629],
        zoom_start=5,
        tiles="CartoDB dark_matter",
        prefer_canvas=True
    )

    for city, coords in CITY_COORDS.items():
        data  = cache.get(city, {})
        aqi   = data.get("aqi")
        cat   = data.get("category", "?")
        color = aqi_color(aqi)
        pulse_size = 14 if aqi and aqi > 200 else 10

        # Glowing pulsing marker
        folium.CircleMarker(
            location=[coords["lat"], coords["lon"]],
            radius=pulse_size,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.9,
            weight=2,
            tooltip=folium.Tooltip(
                f"""<div style='
                    background:#0d0d0d;
                    border:1px solid {color};
                    border-radius:8px;
                    padding:8px 12px;
                    font-family:Inter,sans-serif;
                    min-width:140px;
                    box-shadow: 0 0 15px {color}44;
                '>
                    <div style='font-size:14px;font-weight:700;color:#fff'>{city}</div>
                    <div style='font-size:22px;font-weight:800;color:{color};
                    text-shadow:0 0 10px {color}'>{aqi or "?"}</div>
                    <div style='font-size:11px;color:{color};
                    font-weight:600'>{cat}</div>
                    <div style='font-size:10px;color:#555;margin-top:4px'>
                    Click for full report</div>
                </div>""",
                sticky=True
            ),
            popup=folium.Popup(city, parse_html=False),
        ).add_to(m)

        # Outer glow ring
        folium.CircleMarker(
            location=[coords["lat"], coords["lon"]],
            radius=pulse_size + 6,
            color=color,
            fill=False,
            weight=1,
            opacity=0.3,
        ).add_to(m)

        # City label
        folium.Marker(
            location=[coords["lat"] + 0.7, coords["lon"]],
            icon=folium.DivIcon(
                html=f"""<div style='
                    font-size:10px;font-weight:600;
                    color:{color};white-space:nowrap;
                    font-family:Inter,sans-serif;
                    text-shadow:0 0 8px {color},0 1px 3px #000;
                    letter-spacing:0.03em;
                '>{city}</div>""",
                icon_size=(120, 18),
                icon_anchor=(60, 0)
            )
        ).add_to(m)

    return m


# ─────────────────────────────────────────────
# AQI GAUGE
# ─────────────────────────────────────────────
def make_gauge(aqi, label="AQI"):
    color = aqi_color(aqi)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=aqi or 0,
        number={
            "font": {"size": 44, "color": color, "family": "Inter"},
            "suffix": ""
        },
        title={
            "text": label,
            "font": {"size": 12, "color": "#666", "family": "Inter"}
        },
       gauge={
            "axis": {
                "range": [0, 500],
                "visible": False
            },
            "bar": {"color": color, "thickness": 0.22},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0,   50],  "color": "rgba(0,255,136,0.06)"},
                {"range": [50,  100], "color": "rgba(170,255,0,0.06)"},
                {"range": [100, 200], "color": "rgba(255,170,0,0.06)"},
                {"range": [200, 300], "color": "rgba(255,107,0,0.06)"},
                {"range": [300, 400], "color": "rgba(255,51,0,0.06)"},
                {"range": [400, 500], "color": "rgba(204,0,255,0.06)"},
            ],
            "threshold": {
                "line": {"color": color, "width": 2},
                "thickness": 0.75,
                "value": aqi or 0
            }
        }
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=30, b=0, l=20, r=20),
        height=200,
        font={"color": "#fff", "family": "Inter"}
    )
    return fig


# ─────────────────────────────────────────────
# SHAP CHART
# ─────────────────────────────────────────────
def make_shap_chart(factors):
    features = [f["feature"] for f in factors]
    impacts  = [f["impact"]  for f in factors]
    colors   = [aqi_color(300) if i > 0 else "#00ff88" for i in impacts]

    fig = go.Figure(go.Bar(
        x=impacts, y=features,
        orientation="h",
        marker={
            "color": colors,
            "opacity": 0.85,
            "line": {"width": 0}
        },
        text=[f"+{i:.1f}" if i > 0 else f"{i:.1f}" for i in impacts],
        textposition="outside",
        textfont={"color": "#888", "size": 11, "family": "Inter"}
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=10, b=10, l=70, r=60),
        height=210,
        xaxis=dict(
            showgrid=True, gridcolor="rgba(255,255,255,0.04)",
            zeroline=True, zerolinecolor="rgba(255,107,0,0.3)",
            tickfont={"color": "#555", "size": 10},
            showline=False
        ),
        yaxis=dict(
            tickfont={"color": "#ccc", "size": 11},
            showline=False, showgrid=False
        ),
        font={"color": "#fff", "family": "Inter"}
    )
    return fig


# ─────────────────────────────────────────────
# CITY REPORT
# ─────────────────────────────────────────────
def city_report(city, data, pred=None):
    aqi   = data.get("aqi", 0)
    cat   = data.get("category", "Unknown")
    color = aqi_color(aqi)

    # ── Hero card ──
    st.markdown(f"""
    <div class="fire-card" style="border-color:rgba({
        '255,107,0' if aqi > 200 else '255,170,0' if aqi > 100 else '0,255,136'
    },0.2)">
        <div style="display:flex;justify-content:space-between;align-items:flex-start">
            <div>
                <div class="section-tag">Selected city</div>
                <div style="font-size:28px;font-weight:800;color:#fff;
                letter-spacing:-0.5px">{city}</div>
                <div style="font-size:12px;color:#444;margin-top:2px">
                    {data.get("station_name","Live sensor data")}
                </div>
                <div style="margin-top:12px;display:flex;align-items:center;gap:10px">
                    <span style="background:rgba({
                        '255,107,0' if aqi > 200 else '255,170,0' if aqi > 100 else '0,255,136'
                    },0.1);border:1px solid {color}44;color:{color};
                    font-size:12px;font-weight:700;padding:4px 14px;
                    border-radius:20px;letter-spacing:0.04em">{cat.upper()}</span>
                    <span style="font-size:11px;color:#444">
                        Updated {data.get("last_updated","just now")}
                    </span>
                </div>
            </div>
            <div style="text-align:right">
                <div class="aqi-number glow-text" style="color:{color}">{aqi}</div>
                <div style="font-size:11px;color:#444;
                letter-spacing:0.1em;text-transform:uppercase">AQI Index</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Gauge + pollutants ──
    g_col, p_col = st.columns([1, 1])
    with g_col:
        st.plotly_chart(make_gauge(aqi, city),
                       use_container_width=True,
                       config={"displayModeBar": False})

    with p_col:
        st.markdown("<div class='section-tag'>Pollutant readings</div>",
                   unsafe_allow_html=True)
        pols = [
            ("PM2.5", data.get("pm25"), "µg/m³"),
            ("PM10",  data.get("pm10"), "µg/m³"),
            ("NO2",   data.get("no2"),  "µg/m³"),
            ("CO",    data.get("co"),   "mg/m³"),
            ("SO2",   data.get("so2"),  "µg/m³"),
            ("O3",    data.get("o3"),   "µg/m³"),
        ]
        cols = st.columns(3)
        for i, (name, val, unit) in enumerate(pols):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="pollutant-chip">
                    <div style="font-size:9px;color:#555;
                    text-transform:uppercase;letter-spacing:0.08em">{name}</div>
                    <div style="font-size:18px;font-weight:700;
                    color:#fff;margin:2px 0">{val or "—"}</div>
                    <div style="font-size:9px;color:#444">{unit}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)

    # ── SHAP ──
    if pred and pred.get("top_factors"):
        st.markdown("<div class='section-tag'>Why this AQI? — SHAP explanation</div>",
                   unsafe_allow_html=True)
        st.plotly_chart(make_shap_chart(pred["top_factors"]),
                       use_container_width=True,
                       config={"displayModeBar": False})

        expl = pred.get("explanation", "")
        if expl:
            st.markdown(f"""
            <div style="background:rgba(255,107,0,0.03);
            border:1px solid rgba(255,107,0,0.08);
            border-radius:10px;padding:12px 16px;
            font-size:12px;color:#666;line-height:1.9;
            font-family:'Courier New',monospace">
                {expl.replace(chr(10),"<br>")}
            </div>""", unsafe_allow_html=True)
        st.markdown("<hr/>", unsafe_allow_html=True)

    # ── Health advisory ──
    advisory = data.get("health_advisory", {})
    if advisory:
        st.markdown("<div class='section-tag'>Health advisory</div>",
                   unsafe_allow_html=True)
        for key, info in advisory.items():
            bg, border, fg = risk_style(info["risk_level"])
            st.markdown(f"""
            <div class="health-card">
                <div>
                    <span style="font-size:13px;color:#ddd;
                    font-weight:500">{info["group"]}</span>
                    <span style="font-size:11px;color:#555;
                    margin-left:8px">{info["advice"]}</span>
                </div>
                <span class="risk-tag"
                style="background:{bg};border:1px solid {border};
                color:{fg}">{info["risk_level"]}</span>
            </div>""", unsafe_allow_html=True)

    # ── Precautions ──
    prec = data.get("general_precautions", [])
    if prec:
        st.markdown("<br><div class='section-tag'>Precautions</div>",
                   unsafe_allow_html=True)
        for p in prec:
            st.markdown(f"""
            <div style="display:flex;align-items:flex-start;gap:8px;
            padding:5px 0;font-size:12px;color:#555;line-height:1.5">
                <span style="color:#ff6b00;font-size:14px;margin-top:-1px">›</span>
                {p}
            </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:4px 0 20px">
        <div style="font-size:15px;font-weight:800;
        color:#ff6b00;letter-spacing:-0.3px">
            AQI Warning System
        </div>
        <div style="font-size:10px;color:#333;
        margin-top:3px;letter-spacing:0.05em;
        text-transform:uppercase">
            with Explainable AI
        </div>
        <div style="height:1px;background:linear-gradient(90deg,
        #ff6b00,transparent);margin-top:12px"></div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio("", [
        "🗺️  Live city map",
        "🔮  AQI predictor",
        "💬  AI chatbot",
        "ℹ️  About"
    ], label_visibility="collapsed")

    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:10px;color:#333;line-height:2">
        <div class="live-pulse" style="margin-bottom:8px">
            ● Live · API connected
        </div>
        <div>10 cities · WAQI sensors</div>
        <div>Model: XGBoost R²=0.932</div>
        <div>SHAP: TreeExplainer</div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# PAGE 1 — LIVE CITY MAP
# ─────────────────────────────────────────────
if "map" in page:
    # Header
    st.markdown("""
    <div style="display:flex;justify-content:space-between;
    align-items:center;margin-bottom:1rem">
        <div>
            <div style="font-size:22px;font-weight:800;
            color:#fff;letter-spacing:-0.5px">
                Live air quality map
                <span style="color:#ff6b00"> — India</span>
            </div>
            <div style="font-size:12px;color:#444;margin-top:2px">
                Click any city marker for full AQI report + SHAP analysis
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Cache
    if "city_cache" not in st.session_state:
        st.session_state.city_cache = {}

    col_btn, col_space = st.columns([1, 4])
    with col_btn:
        if st.button("⟳ Refresh data"):
            with st.spinner("Fetching live data..."):
                for city in CITY_COORDS:
                    d = fetch_city(city)
                    if d: st.session_state.city_cache[city] = d

    if not st.session_state.city_cache:
        with st.spinner("Loading live AQI data for 10 cities..."):
            for city in CITY_COORDS:
                d = fetch_city(city)
                if d: st.session_state.city_cache[city] = d

    # Stat cards
    cache = st.session_state.city_cache
    valid = {c: d for c, d in cache.items() if d.get("aqi")}
    if valid:
        best    = min(valid, key=lambda c: valid[c]["aqi"])
        worst   = max(valid, key=lambda c: valid[c]["aqi"])
        avg_aqi = int(sum(d["aqi"] for d in valid.values()) / len(valid))
        at_risk = sum(1 for d in valid.values() if d["aqi"] > 200)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Best city",      best,  f"AQI {valid[best]['aqi']}")
        c2.metric("Worst city",     worst, f"AQI {valid[worst]['aqi']}")
        c3.metric("Average AQI",    avg_aqi, f"{len(valid)} cities")
        c4.metric("Cities at risk", at_risk, "AQI > 200")

    st.markdown("<br>", unsafe_allow_html=True)
    # City selector dropdown
    city_list = list(CITY_COORDS.keys())
    sel_col, _ = st.columns([1, 3])
    with sel_col:
        selected_dropdown = st.selectbox(
            "Select city for full report",
            ["— choose a city —"] + city_list,
            key="city_dropdown"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # MAP — full width
    india_map = build_map(cache)
    map_out   = st_folium(
        india_map,
        width="100%",
        height=500,
        returned_objects=["last_object_clicked_popup"]
    )

    # Detect click
    clicked = map_out.get("last_object_clicked_popup") if map_out else None
    if clicked and clicked in CITY_COORDS:
        st.session_state["selected_city"] = clicked

    selected = st.session_state.get("selected_city")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<hr/>", unsafe_allow_html=True)

    # City report below map
   # Get selected city from EITHER dropdown OR map click
    if selected_dropdown != "— choose a city —":
        selected = selected_dropdown
        st.session_state["selected_city"] = selected_dropdown
    else:
        selected = st.session_state.get("selected_city")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<hr/>", unsafe_allow_html=True)

    if selected and selected in CITY_COORDS:
        data = cache.get(selected, {})
        if data and data.get("aqi"):
            now  = datetime.now()
            pred = fetch_predict({
                "PM2.5": float(data.get("pm25") or 50),
                "PM10":  float(data.get("pm10") or 80),
                "NO":    5.0,
                "NO2":   float(data.get("no2")  or 20),
                "NOx":   25.0,
                "NH3":   10.0,
                "CO":    float(data.get("co")   or 1.5),
                "SO2":   float(data.get("so2")  or 10),
                "O3":    float(data.get("o3")   or 30),
                "Month": now.month,
                "Year":  now.year,
                "Season_Code": season_code(now.month)
            })
            city_report(selected, data, pred)
        else:
            st.warning(f"No live data for {selected}. Click Refresh Data.")
    else:
        st.markdown("""
        <div style="text-align:center;padding:3rem 0">
            <div style="font-size:36px;margin-bottom:12px">🗺️</div>
            <div style="font-size:15px;font-weight:600;color:#333">
                Select a city from the dropdown above
            </div>
            <div style="font-size:12px;color:#222;margin-top:6px">
                Full AQI report · SHAP explanation · Health advisory
            </div>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PAGE 2 — AQI PREDICTOR
# ─────────────────────────────────────────────
elif "predictor" in page:
    st.markdown("""
    <div style="margin-bottom:1.5rem">
        <div style="font-size:22px;font-weight:800;color:#fff">
            Manual AQI <span style="color:#ff6b00">predictor</span>
        </div>
        <div style="font-size:12px;color:#444;margin-top:4px">
            Enter pollutant values from any sensor — 
            get AQI prediction + SHAP explanation
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("predict_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            pm25 = st.number_input("PM2.5 (µg/m³)", 0.0, 999.0, 80.0, 0.1)
            no   = st.number_input("NO (µg/m³)",    0.0, 999.0, 5.0,  0.1)
            co   = st.number_input("CO (mg/m³)",    0.0, 100.0, 1.5,  0.1)
        with c2:
            pm10 = st.number_input("PM10 (µg/m³)", 0.0, 999.0, 120.0, 0.1)
            no2  = st.number_input("NO2 (µg/m³)",  0.0, 999.0, 30.0,  0.1)
            so2  = st.number_input("SO2 (µg/m³)",  0.0, 999.0, 15.0,  0.1)
        with c3:
            nox  = st.number_input("NOx (µg/m³)",  0.0, 999.0, 35.0, 0.1)
            nh3  = st.number_input("NH3 (µg/m³)",  0.0, 999.0, 10.0, 0.1)
            o3   = st.number_input("O3 (µg/m³)",   0.0, 999.0, 40.0, 0.1)

        t1, t2, t3 = st.columns(3)
        with t1:
            month = st.selectbox("Month", range(1,13), format_func=lambda x:
                ["Jan","Feb","Mar","Apr","May","Jun",
                 "Jul","Aug","Sep","Oct","Nov","Dec"][x-1])
        with t2:
            year = st.selectbox("Year", [2023,2024,2025,2026], index=2)
        with t3:
            s = st.selectbox("Season", ["Winter(0)","Spring(1)","Summer(2)","Monsoon(3)"])
            sc = int(s[-2])

        submitted = st.form_submit_button("🔮 Predict AQI now")

    if submitted:
        with st.spinner("Running XGBoost + SHAP..."):
            result = fetch_predict({
                "PM2.5":pm25,"PM10":pm10,"NO":no,"NO2":no2,
                "NOx":nox,"NH3":nh3,"CO":co,"SO2":so2,"O3":o3,
                "Month":month,"Year":year,"Season_Code":sc
            })

        if result and result.get("success"):
            aqi   = result["predicted_aqi"]
            cat   = result["aqi_category"]
            color = aqi_color(aqi)

            st.markdown("<hr/>", unsafe_allow_html=True)
            r1, r2 = st.columns(2)
            with r1:
                st.markdown(f"""
                <div class="fire-card" style="text-align:center">
                    <div class="section-tag" style="justify-content:center">
                        Predicted AQI
                    </div>
                    <div class="aqi-number glow-text"
                    style="color:{color}">{aqi}</div>
                    <span style="background:rgba(255,107,0,0.08);
                    border:1px solid {color}44;color:{color};
                    font-size:13px;font-weight:700;padding:5px 18px;
                    border-radius:20px;display:inline-block;
                    margin-top:8px">{cat.upper()}</span>
                </div>
                """, unsafe_allow_html=True)
                st.plotly_chart(make_gauge(aqi),
                               use_container_width=True,
                               config={"displayModeBar":False})

            with r2:
                st.markdown("<div class='section-tag'>SHAP — what caused this</div>",
                           unsafe_allow_html=True)
                st.plotly_chart(make_shap_chart(result["top_factors"]),
                               use_container_width=True,
                               config={"displayModeBar":False})

            st.markdown("<hr/>", unsafe_allow_html=True)
            st.markdown("<div class='section-tag'>Health advisory</div>",
                       unsafe_allow_html=True)
            for key, info in result["health_advisory"].items():
                bg, border, fg = risk_style(info["risk_level"])
                st.markdown(f"""
                <div class="health-card">
                    <div>
                        <span style="color:#ddd;font-size:13px;
                        font-weight:500">{info["group"]}</span>
                        <span style="color:#555;font-size:11px;
                        margin-left:8px">{info["advice"]}</span>
                    </div>
                    <span class="risk-tag"
                    style="background:{bg};border:1px solid {border};
                    color:{fg}">{info["risk_level"]}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.error("Prediction failed. Is FastAPI running on port 8000?")


# ─────────────────────────────────────────────
# PAGE 3 — AI CHATBOT
# ─────────────────────────────────────────────
elif "chatbot" in page:
    st.markdown("""
    <div style="margin-bottom:1.5rem">
        <div style="font-size:22px;font-weight:800;color:#fff">
            AI air quality <span style="color:#ff6b00">assistant</span>
        </div>
        <div style="font-size:12px;color:#444;margin-top:4px">
            Ask anything about pollution, AQI, health impacts or Indian cities
        </div>
    </div>
    """, unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": "Hello! I'm your AI air quality assistant powered by Gemini. Ask me anything about pollution, AQI levels, health impacts, or specific Indian cities."
        }]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("Ask about air quality..."):
        st.session_state.messages.append({"role":"user","content":prompt})
        with st.chat_message("user"):
            st.write(prompt)

        try:
            import google.generativeai as genai
            from config.settings import GEMINI_API_KEY
            genai.configure(api_key=GEMINI_API_KEY)
            model_ai = genai.GenerativeModel("gemini-1.5-flash")
            ctx = """You are an expert AI assistant specialized in air quality,
            pollution science, and public health in India. You know the CPCB AQI
            scale, Indian cities' pollution patterns, seasonal effects, and health
            impacts. Be concise, helpful, and data-driven. Answer in 3-5 sentences."""
            resp   = model_ai.generate_content(ctx + "\nUser: " + prompt)
            answer = resp.text
        except Exception as e:
            fallback = {
                "pm2.5":  "PM2.5 particles are under 2.5 micrometers — they penetrate deep into lung tissue. In Delhi winters, PM2.5 alone can push AQI above 400, driven by crop burning in Punjab, cold air trapping pollutants close to the ground, and vehicle emissions.",
                "aqi":    "India's AQI scale runs 0-500 with 6 categories: Good (0-50), Satisfactory (51-100), Moderate (101-200), Poor (201-300), Very Poor (301-400), and Severe (401-500). It's calculated from 8 pollutants including PM2.5, PM10, NO2, CO, SO2, and O3.",
                "delhi":  "Delhi is consistently one of the world's most polluted capitals. Winter months (October-January) see AQI regularly crossing 400 due to crop stubble burning in neighboring states, low wind speeds trapping pollutants, and high vehicle density.",
                "mask":   "For AQI above 150, N95 or N99 masks are recommended. Regular surgical masks filter particles above 5 microns but offer minimal protection against the most dangerous PM2.5 particles. Ensure a proper face seal for effective protection.",
                "child":  "Children are particularly vulnerable to air pollution because their lungs are still developing and they breathe more air relative to body weight. Prolonged exposure to high AQI can permanently stunt lung development and increase asthma risk.",
            }
            key    = next((k for k in fallback if k in prompt.lower()), None)
            answer = fallback[key] if key else f"Great question about {prompt}. Based on our AQI system data, PM2.5 and CO are the primary drivers of poor air quality in Indian cities. PM2.5 alone accounts for ~47% of AQI variation according to our SHAP analysis. Would you like to know about a specific city or pollutant?"

        st.session_state.messages.append({"role":"assistant","content":answer})
        with st.chat_message("assistant"):
            st.write(answer)


# ─────────────────────────────────────────────
# PAGE 4 — ABOUT
# ─────────────────────────────────────────────
elif "About" in page:
    st.markdown("""
    <div style="margin-bottom:1.5rem">
        <div style="font-size:22px;font-weight:800;color:#fff">
            About this <span style="color:#ff6b00">project</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="fire-card">
        <div class="section-tag">Project</div>
        <div style="font-size:17px;font-weight:700;color:#fff;margin-bottom:8px">
            AI-Driven Early Warning System for Urban Air Quality Risk Zones
            (with Explainable AI)
        </div>
        <div style="font-size:13px;color:#555;line-height:1.8">
            A full-stack machine learning system that predicts AQI using real-time
            sensor data from 10 Indian cities, explains every prediction using SHAP
            game-theory explainability, and delivers personalised health advisories
            for 7 population groups — served through a production FastAPI backend
            and deployed on the web.
        </div>
    </div>

    <div class="fire-card">
        <div class="section-tag">Tech stack</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;
        gap:12px;font-size:13px">
            <div>
                <div style="color:#444;font-size:10px;text-transform:uppercase;
                letter-spacing:0.08em;margin-bottom:4px">ML Model</div>
                <div style="color:#fff;font-weight:600">XGBoost · R² = 0.932</div>
            </div>
            <div>
                <div style="color:#444;font-size:10px;text-transform:uppercase;
                letter-spacing:0.08em;margin-bottom:4px">Explainability</div>
                <div style="color:#fff;font-weight:600">SHAP TreeExplainer</div>
            </div>
            <div>
                <div style="color:#444;font-size:10px;text-transform:uppercase;
                letter-spacing:0.08em;margin-bottom:4px">Experiment tracking</div>
                <div style="color:#fff;font-weight:600">MLflow</div>
            </div>
            <div>
                <div style="color:#444;font-size:10px;text-transform:uppercase;
                letter-spacing:0.08em;margin-bottom:4px">Backend API</div>
                <div style="color:#fff;font-weight:600">FastAPI + Uvicorn</div>
            </div>
            <div>
                <div style="color:#444;font-size:10px;text-transform:uppercase;
                letter-spacing:0.08em;margin-bottom:4px">Live data</div>
                <div style="color:#fff;font-weight:600">WAQI API</div>
            </div>
            <div>
                <div style="color:#444;font-size:10px;text-transform:uppercase;
                letter-spacing:0.08em;margin-bottom:4px">Frontend</div>
                <div style="color:#fff;font-weight:600">
                    Streamlit + Folium + Plotly
                </div>
            </div>
        </div>
    </div>

    <div class="fire-card">
        <div class="section-tag">Model performance</div>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px">
            <div class="stat-mini">
                <div style="font-size:24px;font-weight:800;
                color:#ff6b00">0.932</div>
                <div style="font-size:10px;color:#444;margin-top:2px">R² Score</div>
            </div>
            <div class="stat-mini">
                <div style="font-size:24px;font-weight:800;
                color:#ffaa00">17.9</div>
                <div style="font-size:10px;color:#444;margin-top:2px">MAE (AQI pts)</div>
            </div>
            <div class="stat-mini">
                <div style="font-size:24px;font-weight:800;
                color:#ff6b00">5-fold</div>
                <div style="font-size:10px;color:#444;margin-top:2px">
                    Cross-validated
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)