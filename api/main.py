from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import predict, city, chat, forecast, anomaly, models, health
from api.routes import weather, compare, history, share, cropburn, cpcb

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
app.include_router(models.router,   prefix="/api/v1", tags=["Models"])
app.include_router(health.router,   prefix="/api/v1", tags=["Health"])
app.include_router(weather.router,  prefix="/api/v1", tags=["Weather"])
app.include_router(compare.router,  prefix="/api/v1", tags=["Compare"])
app.include_router(history.router,  prefix="/api/v1", tags=["History"])
app.include_router(share.router,    prefix="/api/v1", tags=["Share"])
app.include_router(cropburn.router, prefix="/api/v1", tags=["Crop Burn"])
app.include_router(cpcb.router,    prefix="/api/v1", tags=["CPCB"])


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