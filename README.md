# 🌫️ AQI Early Warning System — India

[![Live Demo](https://img.shields.io/badge/Live-aqi--early--warning--system.vercel.app-orange?style=for-the-badge)](https://aqi-early-warning-system.vercel.app)
[![API](https://img.shields.io/badge/API-Render-46E3B7?style=for-the-badge&logo=render)](https://aqi-api-y2qs.onrender.com/docs)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python)](https://python.org)
[![XGBoost](https://img.shields.io/badge/XGBoost-R²%3D0.932-FF6600?style=for-the-badge)](https://xgboost.readthedocs.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16K%2B%20rows-336791?style=for-the-badge&logo=postgresql)](https://render.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

> Real-time AI-powered air quality monitoring, prediction, and early warning for 37 Indian cities.  

---

## 🌐 Live

| Service | URL |
|---|---|
| Web App | https://aqi-early-warning-system.vercel.app |
| API | https://aqi-api-y2qs.onrender.com |
| API Docs (Swagger) | https://aqi-api-y2qs.onrender.com/docs |

---

## Why This Exists

7 of the world's 10 most polluted cities are in India. PM2.5 in Delhi regularly hits 10–20× the WHO safe limit. Yet most Indians have no reliable, free tool to check real-time conditions, understand which pollutant is causing harm, or get advance warnings before bad air days arrive.

This project was built to change that. One student, one laptop, Faridabad.

---

## What Makes This Different

- **Real data only** — live CPCB station readings via WAQI API, multi-station averaged, bad sensors filtered
- **NASA satellite** — actual FIRMS VIIRS fire detection for crop burning alerts, not estimates
- **XGBoost + SHAP** — every prediction is explainable, showing exactly which pollutant drives the AQI
- **Real database** — 16,000+ hourly readings collected since May 13, 2026, growing every hour
- **Honest** — cities with no WAQI coverage are shown as NO_DATA, never faked

---

## Features

### Live Monitoring
- 37 Indian cities with real CPCB data from 200+ stations
- Multi-station averaging — up to 15 stations per city (Delhi), weighted by data freshness
- Bad sensor filtering — stations reporting impossible PM values (≥500 µg/m³) automatically excluded
- India map — clickable city dots, color-coded by AQI category (Leaflet.js)
- Threat Matrix — all cities ranked by AQI in real time
- Live ticker — scrolling city AQI feed across the top

### AI & ML
- XGBoost prediction — R²=0.932, MAE=21.33, trained on 29,531 rows across 26 Indian cities (2015–2020)
- SHAP TreeExplainer — shows which pollutant drives each prediction
- 24h diurnal forecast — physics-informed model anchored to live AQI, peaks at morning rush (07–09) and evening (17–19)
- Anomaly detection — Z-score spike flagging with city baseline comparison
- Model benchmarks — XGBoost vs LightGBM vs Random Forest, side by side
- AI chatbot — Groq LLaMA 3.1 8B Instant with live city AQI injected as context per query

### Unique Features
- **Crop Burn Detector** — 4-signal system: seasonal calendar + Punjab AQI spike + downwind city pattern + NASA FIRMS VIIRS satellite fire count
- **AQI Time Machine** — 16,000+ real hourly readings from PostgreSQL, Recharts visualization, 1d/3d/7d/12d selector
- **Health Impact Calculator** — cigarette equivalent, WHO limit %, PM2.5 inhaled (mg), life minutes lost per day, across 7 population groups
- **Weather + AQI Correlation** — OpenWeatherMap integration showing how temperature, humidity, wind speed, and rainfall affect pollution
- **City Intelligence Dashboard** — 7-day trend, pollutant breakdown (pie), 30-day AQI calendar heatmap, 72h forecast chart
- **City Comparison** — side-by-side AQI, pollutants, population, cigarette equivalent diff
- **Email Alerts** — threshold-based alerts via Resend, 3000/month free tier
- **PWA** — installable on Android/desktop, works offline

### Security
- Rate limiting per IP via slowapi (30 req/min on /cities, 10 req/min on /chat)
- Security headers — XSS protection, clickjacking prevention, Content Security Policy
- CORS locked to production Vercel domain only
- SQL injection prevention on all endpoints
- All secrets in Render environment variables — nothing hardcoded

---

## Architecture

```
┌─────────────────────┐       ┌─────────────────────┐
│   React 18 + Vite   │──────▶│   FastAPI Backend   │
│   Vercel            │◀──────│   Render.com        │
└─────────────────────┘       └──────────┬──────────┘
                                          │
         ┌────────────────────────────────┼──────────────────────┐
         ▼                                ▼                      ▼
┌─────────────────┐        ┌─────────────────────┐   ┌──────────────────┐
│  PostgreSQL DB  │        │   WAQI API          │   │  XGBoost Model   │
│  16,000+ rows   │        │   CPCB stations     │   │  R²=0.932        │
│  Hourly cron    │        │   37 live cities    │   │  SHAP explainer  │
└─────────────────┘        └─────────────────────┘   └──────────────────┘
         │
┌─────────────────┐        ┌─────────────────────┐
│  NASA FIRMS     │        │  Groq LLaMA 3.1     │
│  VIIRS Satellite│        │  Live AQI context   │
│  Fire detection │        │  injected per query │
└─────────────────┘        └─────────────────────┘
```

---

## City Coverage

**37 cities with live CPCB data:**

Delhi (15 stn) · Mumbai (11 stn) · Bengaluru (5 stn) · Chennai (6 stn) · Kolkata (7 stn) · Hyderabad (4 stn) · Ahmedabad (6 stn) · Jaipur (3 stn) · Lucknow (6 stn) · Kanpur (2 stn) · Patna (5 stn) · Bhopal (2 stn) · Nagpur (1 stn) · Indore (1 stn) · Visakhapatnam (1 stn) · Chandigarh (3 stn) · Coimbatore (1 stn) · Agra (4 stn) · Varanasi (4 stn) · Amritsar (1 stn) · Jodhpur (1 stn) · Udaipur (1 stn) · Mysuru (1 stn) · Pondicherry (1 stn) · Ghaziabad (3 stn) · Noida (4 stn) · Faridabad (2 stn) · Gurugram (1 stn) · Meerut (3 stn) · Moradabad (6 stn) · Ludhiana (1 stn) · Jalandhar (1 stn) · Guwahati (1 stn) · Srinagar (1 stn) · Thiruvananthapuram (1 stn) · Dehradun (1 stn) · Nashik (1 stn)

**16 cities honestly shown as NO_DATA** (no WAQI/CPCB station coverage):
Pune · Surat · Kochi · Bhubaneswar · Ranchi · Raipur · Shimla · Jammu · Madurai · Vijayawada · Aurangabad · Kolhapur · Solapur · Warangal · Guntur · Tiruchirappalli

---

## ML Pipeline

| Item | Detail |
|---|---|
| Dataset | CPCB India city_day.csv — 29,531 rows, 26 cities, 2015–2020 |
| Features | PM2.5, PM10, NO, NO2, NOx, NH3, CO, SO2, O3, Benzene, Toluene, Xylene, City, Month |
| Model | XGBoost Regressor |
| R² Score | **0.932** |
| MAE | **21.33 AQI units** |
| CV | 5-fold cross-validation mean R²=0.931 |
| Explainability | SHAP TreeExplainer |
| Tracking | MLflow |
| Benchmarked | XGBoost · LightGBM · Random Forest |

---

## API Endpoints (16 total)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/cities` | All 37 live cities, multi-station averaged AQI |
| GET | `/api/v1/city/{city}` | Single city — all pollutants, all stations |
| POST | `/api/v1/predict` | XGBoost AQI prediction + SHAP values |
| POST | `/api/v1/forecast` | 24h diurnal AQI forecast |
| POST | `/api/v1/chat` | Groq LLaMA chatbot with live AQI context |
| GET | `/api/v1/cropburn/status` | Crop burning 4-signal detection |
| GET | `/api/v1/weather/{city}` | Weather + AQI correlation data |
| GET | `/api/v1/db/history` | Real hourly AQI from PostgreSQL |
| GET | `/api/v1/db/status` | Database row count |
| GET | `/api/v1/db/audit` | Full data quality audit report |
| GET | `/api/v1/db/cleanup` | Remove bad/invalid rows (admin) |
| POST | `/api/v1/alerts/subscribe` | Email alert subscription |
| POST | `/api/v1/health/impact` | Health impact calculator |
| GET | `/api/v1/compare` | Side-by-side city comparison |
| GET | `/api/v1/anomaly/detect` | Z-score anomaly detection |
| GET | `/api/v1/models/comparison` | ML model benchmark results |
| GET | `/health` | Backend health check |

---

## Pages (15 total)

| Route | Page |
|---|---|
| `/` | Live Map — India map, 37 cities, Threat Matrix |
| `/predict` | AQI Predictor — XGBoost dials + SHAP chart |
| `/health` | Health Impact Calculator |
| `/forecast` | 24h Diurnal Forecast |
| `/cities` | City Intelligence Dashboard |
| `/compare` | Side-by-side City Comparison |
| `/history` | AQI Time Machine — real DB data |
| `/weather` | Weather + AQI Correlation |
| `/cropburn` | Crop Burning Early Warning |
| `/chatbot` | Groq LLaMA Chatbot |
| `/alerts` | Email Threshold Alerts |
| `/models` | ML Model Benchmarks |
| `/about` | About + Mission |
| `/api` | Public API Documentation |

---

## Database

| Item | Detail |
|---|---|
| Engine | PostgreSQL on Render (free tier) |
| Table | `aqi_readings` |
| Rows | 16,122 (as of May 30, 2026) |
| Coverage | May 13, 2026 → present |
| Frequency | Every 60 minutes via APScheduler |
| Columns | city, aqi, pm25, pm10, no2, co, so2, o3, station_name, timestamp |
| Validation | Rows with impossible pollutant values automatically flagged and removed |

---

## Project Structure

```
aqi-early-warning-system/
├── api/                        # FastAPI backend
│   ├── main.py                 # App entry, CORS, rate limiting, security headers
│   ├── models.py               # SQLAlchemy ORM models
│   ├── database.py             # Async PostgreSQL connection pool
│   ├── scheduler.py            # APScheduler — hourly city snapshots
│   └── routes/
│       ├── city.py             # /cities, /city/{name}
│       ├── predict.py          # /predict (XGBoost + SHAP)
│       ├── forecast.py         # /forecast (24h diurnal)
│       ├── chat.py             # /chat (Groq LLaMA)
│       ├── alerts.py           # /alerts/subscribe (Resend)
│       ├── db.py               # /db/history, /db/status, /db/audit, /db/cleanup
│       ├── cropburn.py         # /cropburn/status (NASA FIRMS)
│       ├── weather.py          # /weather/{city} (OpenWeatherMap)
│       ├── health.py           # /health/impact
│       ├── anomaly.py          # /anomaly/detect
│       └── models_routes.py    # /models/comparison
├── config/
│   └── settings.py             # 37 cities config, coordinates, station lists
├── src/data/
│   └── waqi_client.py          # Multi-station fetcher, bad sensor filter, averaging
├── frontend/                   # React 18 + Vite 5
│   └── src/
│       ├── components/         # Navbar, Map, Charts, Cards, Ticker, etc.
│       ├── pages/              # 14 page components
│       └── utils/api.js        # Centralized API calls
├── models/
│   └── xgb_model.pkl           # Trained XGBoost model (binary)
├── data/raw/
│   └── city_day.csv            # CPCB training data (not used at runtime)
├── requirements.txt
└── README.md
```

---

## Local Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL database
- API keys: WAQI · Groq · NASA FIRMS · Resend · OpenWeatherMap

### Backend

```bash
git clone https://github.com/KrishnaBhatia22-11/aqi-early-warning-system.git
cd aqi-early-warning-system

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
```

Create `.env` in root:
```
DATABASE_URL=your_postgresql_url
WAQI_API_KEY=your_key
GROQ_API_KEY=your_key
NASA_FIRMS_API_KEY=your_key
RESEND_API_KEY=your_key
OPENWEATHER_API_KEY=your_key
```

```bash
uvicorn api.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`

---

## Deployment

| Platform | Purpose |
|---|---|
| Vercel | React + Vite frontend, auto-deploy from GitHub main |
| Render (Web Service) | FastAPI backend + APScheduler hourly cron |
| Render (PostgreSQL) | Live database — 16,000+ hourly readings |

---

## AQI Scale (India CPCB)

| AQI | Category |
|---|---|
| 0–50 | Good 🟢 |
| 51–100 | Satisfactory 🟡 |
| 101–200 | Moderate 🟠 |
| 201–300 | Poor 🔴 |
| 301–400 | Very Poor 🟣 |
| 401–500 | Severe ⚫ |

---

## Tech Stack

**ML** — XGBoost · Scikit-learn · SHAP · MLflow · Pandas · NumPy

**Backend** — FastAPI · SQLAlchemy · PostgreSQL · APScheduler · Slowapi · Pydantic · Uvicorn

**Frontend** — React 18 · Vite 5 · Tailwind CSS · Recharts · Leaflet.js

**AI** — Groq LLaMA 3.1 8B Instant

**Data Sources** — WAQI API · CPCB India · NASA FIRMS VIIRS · OpenWeatherMap · Resend

**Infra** — Vercel · Render · GitHub

---

## Built By

**Krishna Bhatia**  
B.Tech CSE, 6th Semester  
Manav Rachna International Institute of Research and Studies, Faridabad, India

[LinkedIn](https://linkedin.com/in/krishna-bhatia09/) · [GitHub](https://github.com/KrishnaBhatia22-11) · krishnabhatia09@gmail.com

> Every line of code — the XGBoost ML model, FastAPI backend, React frontend,  
> PostgreSQL database, NASA FIRMS satellite integration, SHAP explainability,  
> and email alert system — was built and deployed solo.  
> Built in Faridabad. Free forever. No ads. No paywall. Ever.

---

## License

MIT — free to use, modify, and distribute with attribution.
