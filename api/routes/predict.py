from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import joblib
import numpy as np
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.settings import MODEL_DIR
from src.explainability.shap_explainer import (
    explain_single_prediction,
    human_readable_explanation
)
from src.analytics.health_score import (
    get_health_advisory,
    get_general_precautions
)

router = APIRouter()

# Load model and explainer once at startup
model        = joblib.load(os.path.join(MODEL_DIR, "best_model.pkl"))
feature_cols = joblib.load(os.path.join(MODEL_DIR, "feature_cols.pkl"))

import pickle
with open(os.path.join(MODEL_DIR, "shap_explainer.pkl"), 'rb') as f:
    explainer = pickle.load(f)


# ─────────────────────────────────────────────
# Request schema — what the user sends
# ─────────────────────────────────────────────
class PredictionRequest(BaseModel):
    PM2_5:       float = Field(..., example=120.0, alias="PM2.5")
    PM10:        float = Field(..., example=200.0)
    NO:          float = Field(..., example=5.0)
    NO2:         float = Field(..., example=30.0)
    NOx:         float = Field(..., example=35.0)
    NH3:         float = Field(..., example=10.0)
    CO:          float = Field(..., example=2.5)
    SO2:         float = Field(..., example=15.0)
    O3:          float = Field(..., example=40.0)
    Month:       int   = Field(..., example=12)
    Year:        int   = Field(..., example=2024)
    Season_Code: int   = Field(..., example=0)

    class Config:
        populate_by_name = True


# ─────────────────────────────────────────────
# AQI category helper
# ─────────────────────────────────────────────
def categorize_aqi(aqi):
    if aqi <= 50:   return "Good"
    if aqi <= 100:  return "Satisfactory"
    if aqi <= 200:  return "Moderate"
    if aqi <= 300:  return "Poor"
    if aqi <= 400:  return "Very Poor"
    return "Severe"


# ─────────────────────────────────────────────
# POST /predict — main prediction endpoint
# ─────────────────────────────────────────────
@router.post("/predict")
def predict_aqi(request: PredictionRequest):
    try:
        input_values = {
            'PM2.5':       request.PM2_5,
            'PM10':        request.PM10,
            'NO':          request.NO,
            'NO2':         request.NO2,
            'NOx':         request.NOx,
            'NH3':         request.NH3,
            'CO':          request.CO,
            'SO2':         request.SO2,
            'O3':          request.O3,
            'Month':       request.Month,
            'Year':        request.Year,
            'Season_Code': request.Season_Code,
        }

        # Predict AQI
        prediction, explanation = explain_single_prediction(
            model, explainer, feature_cols, input_values
        )

        predicted_aqi      = round(float(prediction), 1)
        predicted_aqi      = min(predicted_aqi, 500)
        aqi_category       = categorize_aqi(predicted_aqi)
        readable           = human_readable_explanation(explanation, predicted_aqi)
        health_advisory    = get_health_advisory(aqi_category)
        general_precautions = get_general_precautions(aqi_category)

        # Top 5 SHAP factors
        top_factors = []
        for _, row in explanation.head(5).iterrows():
            top_factors.append({
                "feature":    row['Feature'],
                "value":      round(float(row['Value']), 2),
                "impact":     round(float(row['SHAP_Impact']), 2),
                "direction":  "increases AQI" if row['SHAP_Impact'] > 0 else "decreases AQI"
            })

        return {
            "success":            True,
            "predicted_aqi":      predicted_aqi,
            "aqi_category":       aqi_category,
            "explanation":        readable,
            "top_factors":        top_factors,
            "health_advisory":    health_advisory,
            "general_precautions": general_precautions,
            "input_values":       input_values,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))