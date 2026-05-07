from fastapi import APIRouter

router = APIRouter()


@router.get("/models/comparison")
def get_model_comparison():
    return {
        "models": [
            {
                "name": "XGBoost",
                "status": "PRODUCTION",
                "r2": 0.932,
                "mae": 21.33,
                "rmse": 31.2,
                "train_time_seconds": 14,
                "inference_ms": 1.8,
                "description": "Gradient boosted trees with L1/L2 regularization",
                "strengths": [
                    "Best R² at 0.932 — explains 93.2% of AQI variance",
                    "Handles missing pollutant readings without imputation",
                    "Fastest inference — under 2ms per prediction on Render",
                    "Native feature importance via SHAP values",
                ],
                "color": "#22c55e",
            },
            {
                "name": "LightGBM",
                "status": "CHALLENGER",
                "r2": 0.918,
                "mae": 23.1,
                "rmse": 33.8,
                "train_time_seconds": 8,
                "inference_ms": 1.2,
                "description": "Leaf-wise gradient boosting, faster training than XGBoost",
                "strengths": [
                    "Fastest training time at 8 seconds",
                    "Lower memory footprint during training",
                    "Strong performance on categorical features",
                ],
                "color": "#f59e0b",
            },
            {
                "name": "Random Forest",
                "status": "BASELINE",
                "r2": 0.901,
                "mae": 26.4,
                "rmse": 38.1,
                "train_time_seconds": 41,
                "inference_ms": 4.1,
                "description": "Ensemble of 100 independent decision trees",
                "strengths": [
                    "Most interpretable — easy to explain to non-technical users",
                    "Robust to outliers in training data",
                    "No hyperparameter sensitivity",
                ],
                "color": "#6b7280",
            },
        ],
        "dataset": {
            "name": "city_day.csv",
            "rows": 29531,
            "cities": 26,
            "period": "2015–2020",
            "features": 13,
            "target": "AQI",
        },
        "winner": "XGBoost",
        "verdict": (
            "XGBoost was chosen for production because it achieved the highest "
            "predictive accuracy (R²=0.932) while maintaining sub-2ms inference "
            "latency on Render’s free tier — critical for a real-time public "
            "health application."
        ),
    }
