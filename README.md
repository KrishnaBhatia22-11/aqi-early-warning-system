# 🌫️ AQI Early Warning System — India

[![Live Demo](https://img.shields.io/badge/Live-aqi--early--warning--system.vercel.app-orange?style=for-the-badge)](https://aqi-early-warning-system.vercel.app)
[![API](https://img.shields.io/badge/API-Render-46E3B7?style=for-the-badge&logo=render)](https://aqi-api-y2qs.onrender.com/docs)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python)](https://python.org)
[![XGBoost](https://img.shields.io/badge/XGBoost-R²%3D0.932-FF6600?style=for-the-badge)](https://xgboost.readthedocs.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Live%20DB-336791?style=for-the-badge&logo=postgresql)](https://render.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

> Real-time AI-powered air quality monitoring, prediction, and early warning for 53 Indian cities.  
> Built solo. Free forever. For 1.4 billion Indians.

---

## 🚀 Live

| Service | URL |
|---|---|
| 🌐 Web App | https://aqi-early-warning-system.vercel.app |
| ⚡ API | https://aqi-api-y2qs.onrender.com |
| 📖 API Docs | https://aqi-api-y2qs.onrender.com/docs |

---

## ✨ Features

### 🗺️ Live Monitoring
- **53 Indian cities** — real-time AQI from WAQI/CPCB stations
- **Multi-station averaging** — up to 16 stations per city (Delhi), weighted by data freshness
- **Outlier removal** — invalid AQI values, stale data (>48h), and foreign stations automatically filtered
- **India map** — clickable city dots, color-coded by AQI category
- **City drill-down** — all pollutants, station list, cleanest/most polluted area, data quality badge

### 🤖 AI & ML
- **XGBoost prediction** — R²=0.932, trained on 29,531 rows, 26 Indian cities (2015–2020)
- **SHAP explainability** — TreeExplainer shows which pollutant drives each prediction
- **24h forecast** — physics-informed diurnal model anchored to live AQI
- **Anomaly detection** — Z-score spike flagging with city baseline comparison
- **Model comparison** — XGBoost vs LightGBM vs Random Forest benchmarks
- **AI chatbot** — Groq LLaMA 3.1 with live city AQI injected as context on every query

### 🔥 Unique Features
- **Crop burn detector** — 4-signal system combining seasonal calendar, Punjab AQI spike detection, downwind city pattern analysis, and NASA FIRMS VIIRS satellite fire count
- **NASA FIRMS integration** — real satellite fire data, Punjab+Haryana+West UP bounding box, 3-hour cache
- **AQI Time Machine** — 12+ days of real hourly data from PostgreSQL database, Recharts visualization
- **Weather + AQI correlation** — OpenWeatherMap integration, shows how temperature, humidity, wind affect pollution
- **Health impact calculator** — cigarette equivalent, WHO limit %, PM2.5 inhaled, life minutes lost per day, 7 population groups
- **City comparison** — side-by-side AQI with diff calculation
- **Email alerts** — threshold-based, powered by Resend (free tier)
- **PWA** — installable on Android/desktop, works offline

### 🛡️ Security
- Rate limiting per IP via slowapi (30 req/min on cities endpoint)
- Security headers — XSS protection, clickjacking prevention, CSP
- CORS locked to production domain only
- Input validation on all endpoints (SQL injection prevention)
- API key system for developer access
- All secrets in environment variables — nothing hardcoded

---

## 🏗️ Architecture

```
┌─────────────────────┐     ┌─────────────────────┐
│   React + Vite      │────▶│   FastAPI Backend   │
│   Vercel            │◀────│   Render.com        │
└─────────────────────┘     └──────────┬──────────┘
                                        │
         ┌──────────────────────────────┼─────────────────────┐
         ▼                              ▼                     ▼
┌─────────────────┐      ┌─────────────────────┐   ┌──────────────────┐
│  PostgreSQL DB  │      │   WAQI API          │   │  XGBoost Model   │
│  11,000+ rows   │      │   CPCB stations     │   │  R²=0.932        │
│  Hourly cron    │      │   53 cities         │   │  SHAP explainer  │
└─────────────────┘      └─────────────────────┘   └──────────────────┘
         │
┌─────────────────┐      ┌─────────────────────┐
│  NASA FIRMS     │      │  Groq LLaMA 3.1     │
│  VIIRS Satellite│      │  Live AQI context   │
│  Fire detection │      │  injected per query │
└─────────────────┘      └─────────────────────┘
```

---

## 📁 Project Structure

```
aqi-early-warning-system/
├── api/                        # FastAPI backend
│   ├── main.py                 # App entry, middleware, CORS, rate limiting
│   ├── models.py               # SQLAlchemy DB models
│   ├── database.py             # Async PostgreSQL connection
│   ├── scheduler.py            # APScheduler — hourly snapshot of all cities
│   └── routes/
│       ├── city.py             # /cities, /city/{name}
│       ├── predict.py          # /predict (XGBoost)
│       ├── forecast.py         # /forecast (24h diurnal)
│       ├── chat.py             # /chat (Groq LLaMA)
│       ├── alerts.py           # /alerts/subscribe (Resend)
│       ├── db.py               # /db/history, /db/status, /db/audit
│       ├── cropburn.py         # /cropburn/status (NASA FIRMS)
│       ├── weather.py          # /weather/{city} (OpenWeatherMap)
│       ├── health.py           # /health/impact
│       ├── anomaly.py          # /anomaly/detect
│       └── models.py           # /models/comparison
├── config/
│   └── settings.py             # City coordinates, 53 cities config
├── src/data/
│   └── waqi_client.py          # Multi-station fetcher + validator
├── frontend/                   # React + Vite
│   └── src/
│       ├── components/         # 20+ reusable components
│       ├── pages/              # 15 page components
│       └── utils/api.js        # All API calls
├── models/
│   └── xgb_model.pkl           # Trained XGBoost model
├── data/raw/
│   └── city_day.csv            # CPCB 2015-2020 training data
└── requirements.txt
```

---

## 🧠 ML Pipeline

| Item | Detail |
|---|---|
| Dataset | CPCB India city_day.csv — 29,531 rows, 26 cities, 2015–2020 |
| Features | PM2.5, PM10, NO2, CO, SO2, O3, city, month |
| Model | XGBoost Regressor |
| R² Score | **0.932** |
| MAE | 21.33 AQI units |
| CV Mean | 0.931 (5-fold cross-validation) |
| Explainability | SHAP TreeExplainer |
| Tracking | MLflow |
| Also benchmarked | LightGBM, Random Forest |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/cities` | All 53 cities, multi-station averages |
| GET | `/api/v1/city/{city}` | Single city full detail + all stations |
| POST | `/api/v1/predict` | XGBoost AQI prediction from pollutants |
| POST | `/api/v1/forecast` | 24h diurnal AQI forecast |
| POST | `/api/v1/chat` | Groq LLaMA chatbot with live context |
| GET | `/api/v1/cropburn/status` | Crop burning detection (4-signal) |
| GET | `/api/v1/weather/{city}` | OpenWeatherMap weather data |
| GET | `/api/v1/db/history` | Real hourly AQI history from DB |
| GET | `/api/v1/db/status` | Database row count |
| GET | `/api/v1/db/audit` | Data quality audit report |
| POST | `/api/v1/alerts/subscribe` | Email alert subscription |
| POST | `/api/v1/health/impact` | Health impact calculator |
| GET | `/api/v1/compare` | Side-by-side city comparison |
| GET | `/api/v1/anomaly/detect` | Z-score anomaly detection |
| GET | `/api/v1/models/comparison` | ML model benchmarks |
| GET | `/health` | Backend health check |

---

## ⚙️ Local Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL (or Render free tier)
- WAQI API key — [aqicn.org/api](https://aqicn.org/api)
- Groq API key — [console.groq.com](https://console.groq.com)
- NASA FIRMS API key — [firms.modaps.eosdis.nasa.gov](https://firms.modaps.eosdis.nasa.gov)
- Resend API key — [resend.com](https://resend.com)
- OpenWeatherMap API key — [openweathermap.org/api](https://openweathermap.org/api)

### Backend

```bash
git clone https://github.com/KrishnaBhatia22-11/aqi-early-warning-system.git
cd aqi-early-warning-system

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt

# Create .env
DATABASE_URL=your_postgresql_url
WAQI_API_KEY=your_key
GROQ_API_KEY=your_key
NASA_FIRMS_API_KEY=your_key
RESEND_API_KEY=your_key
OPENWEATHER_API_KEY=your_key

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

## 🌐 Deployment

| Platform | Purpose |
|---|---|
| Vercel | React + Vite frontend, auto-deploy from GitHub |
| Render (Web Service) | FastAPI backend + APScheduler |
| Render (PostgreSQL) | Database — 11,000+ hourly readings |

### Render Environment Variables

```
DATABASE_URL
WAQI_API_KEY
GROQ_API_KEY
NASA_FIRMS_API_KEY
RESEND_API_KEY
OPENWEATHER_API_KEY
VALID_API_KEYS
```

---

## 📊 AQI Categories (US EPA)

| AQI Range | Category | Color |
|---|---|---|
| 0–50 | Good | 🟢 |
| 51–100 | Moderate | 🟡 |
| 101–150 | Unhealthy for Sensitive Groups | 🟠 |
| 151–200 | Unhealthy | 🔴 |
| 201–300 | Very Unhealthy | 🟣 |
| 301–500 | Hazardous | ⚫ |

---

## 🛠️ Tech Stack

**ML & Data** — XGBoost · Scikit-learn · SHAP · MLflow · Pandas · NumPy

**Backend** — FastAPI · SQLAlchemy · PostgreSQL · APScheduler · Pydantic · Slowapi · Uvicorn

**Frontend** — React 18 · Vite 5 · Tailwind CSS · Recharts · Leaflet.js

**AI** — Groq LLaMA 3.1 8B Instant · NASA FIRMS VIIRS

**Data Sources** — WAQI API · CPCB India · OpenWeatherMap · Resend

**Infra** — Vercel · Render · GitHub

---

## 👨‍💻 Built By

**Krishna Bhatia** — Full Stack ML Engineer  
Manav Rachna International Institute of Research and Studies, Faridabad, India  
[LinkedIn](https://linkedin.com/in/krishnabhatia) · [GitHub](https://github.com/KrishnaBhatia22-11) · krishnabhatia09@gmail.com

> Every line of code — the XGBoost ML model, FastAPI backend, React frontend,  
> PostgreSQL database, NASA FIRMS satellite integration, and email alert system —  
> was designed, built, and deployed by one person.  
> Built in Faridabad. Free forever.

---

## 📄 License

MIT License — free to use, modify, and distribute.
