# 🌫️ AI-Driven Early Warning System for Urban Air Quality Risk Zones

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)](https://aqi-early-warning-system.streamlit.app/)
[![API](https://img.shields.io/badge/API-Render-46E3B7?style=for-the-badge&logo=render)](https://aqi-api-y2qs.onrender.com/docs)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python)](https://python.org)
[![XGBoost](https://img.shields.io/badge/XGBoost-R²%3D0.932-FF6600?style=for-the-badge)](https://xgboost.readthedocs.io)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

> An intelligent AQI prediction and early warning system for Indian cities, powered by XGBoost ML, SHAP Explainable AI, FastAPI, and a Groq-powered AI chatbot.

---

## 🚀 Live Demo

| Service | URL |
|---|---|
| 🌐 Web App | https://aqi-early-warning-system.streamlit.app/ |
| ⚡ FastAPI | https://aqi-api-y2qs.onrender.com |
| 📖 API Docs | https://aqi-api-y2qs.onrender.com/docs |

---

## ✨ Features

- **Live AQI Monitoring** — Real-time data from 10 Indian cities via WAQI API
- **ML Prediction** — XGBoost model with R²=0.932 predicts AQI from 6 pollutants
- **Explainable AI** — SHAP TreeExplainer shows which pollutants drive each prediction
- **Health Advisory** — 7 population groups × 6 AQI categories with tailored guidance
- **AI Chatbot** — Groq LLaMA 3.1 powered assistant for air quality questions
- **MLflow Tracking** — Full experiment tracking with model versioning
- **REST API** — FastAPI backend with 3 endpoints, deployed on Render

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Streamlit UI   │────▶│   FastAPI Backend │────▶│   WAQI API      │
│  (Streamlit     │     │   (Render.com)    │     │   (Live Data)   │
│   Cloud)        │◀────│                  │◀────│                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                       │
         │                       ▼
         │              ┌──────────────────┐
         │              │  XGBoost Model   │
         │              │  + SHAP Explainer│
         │              │  R² = 0.932      │
         │              └──────────────────┘
         │
         ▼
┌─────────────────┐
│  Groq AI        │
│  LLaMA 3.1      │
│  Chatbot        │
└─────────────────┘
```

---

## 📁 Project Structure

```
aqi-early-warning-system/
├── api/                    # FastAPI backend
│   └── main.py             # 3 REST endpoints
├── config/
│   └── settings.py         # Environment config
├── data/
│   ├── raw/                # Raw datasets
│   └── processed/          # Cleaned data
├── models/                 # Trained ML models (.pkl)
├── src/
│   ├── data_preprocessing.py
│   ├── model_training.py
│   └── shap_explainer.py
├── tests/                  # Unit tests
├── streamlit_app.py        # Main UI (4 pages)
├── requirements.txt
└── runtime.txt
```

---

## 🧠 ML Pipeline

| Step | Detail |
|---|---|
| Dataset | CPCB India city_day.csv (2015–2020) |
| Pollutants | PM2.5, PM10, NO2, CO, SO2, O3 |
| Model | XGBoost Regressor |
| R² Score | 0.932 |
| CV Mean | 0.931 (5-fold) |
| Explainability | SHAP TreeExplainer |
| Tracking | MLflow |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check |
| POST | `/api/v1/predict` | Predict AQI from pollutants |
| GET | `/api/v1/cities` | Live AQI for 10 Indian cities |
| GET | `/docs` | Interactive API documentation |

---

## ⚙️ Local Setup

### Prerequisites
- Python 3.11+
- WAQI API key (free at [aqicn.org/api](https://aqicn.org/api))
- Groq API key (free at [console.groq.com](https://console.groq.com))

### Installation

```bash
# Clone the repo
git clone https://github.com/KrishnaBhatia22-11/aqi-early-warning-system.git
cd aqi-early-warning-system

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo WAQI_API_KEY=your_key_here > .env
echo GROQ_API_KEY=your_key_here >> .env
```

### Running

```bash
# Terminal 1 — FastAPI backend
uvicorn api.main:app --reload --port 8000

# Terminal 2 — Streamlit frontend
streamlit run streamlit_app.py
```

Open `http://localhost:8501` in your browser.

---

## 🌐 Deployment

| Platform | Purpose | Config |
|---|---|---|
| Streamlit Cloud | Frontend UI | Connected to GitHub main branch |
| Render.com | FastAPI backend | Free tier, always-on |

### Environment Variables Required

```toml
# Streamlit Cloud Secrets
WAQI_API_KEY = "your_key"
GROQ_API_KEY = "your_key"
```

---

## 📊 AQI Categories (CPCB India)

| AQI Range | Category | Color |
|---|---|---|
| 0–50 | Good | 🟢 |
| 51–100 | Satisfactory | 🟡 |
| 101–200 | Moderate | 🟠 |
| 201–300 | Poor | 🔴 |
| 301–400 | Very Poor | 🟣 |
| 401–500 | Severe | ⚫ |

---

## 🛠️ Tech Stack

**ML & Data** — XGBoost · Scikit-learn · SHAP · MLflow · Pandas · NumPy

**Backend** — FastAPI · Uvicorn · Pydantic · Requests

**Frontend** — Streamlit · Plotly · Folium · Seaborn

**AI Chatbot** — Groq API · LLaMA 3.1 8B Instant

**Deployment** — Streamlit Cloud · Render.com · GitHub

---

## 📄 License

This project is licensed under the MIT License.
