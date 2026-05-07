from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import predict, city, chat, forecast, anomaly

app = FastAPI(
    title="AI-Driven Early Warning System for Urban Air Quality Risk Zones",
    description="Predicts AQI using ML, explains with SHAP, provides live city data",
    version="1.0.0"
)

# Allow Streamlit frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(predict.router, prefix="/api/v1", tags=["Prediction"])
app.include_router(city.router,    prefix="/api/v1", tags=["City Data"])
app.include_router(chat.router,     prefix="/api/v1", tags=["Chatbot"])
app.include_router(forecast.router, prefix="/api/v1", tags=["Forecast"])
app.include_router(anomaly.router,  prefix="/api/v1", tags=["Anomaly"])


@app.get("/")
def root():
    return {
        "project": "AI-Driven Early Warning System for Urban Air Quality Risk Zones",
        "version": "1.0.0",
        "status":  "running",
        "docs":    "/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}