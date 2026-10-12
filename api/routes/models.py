from fastapi import APIRouter

router = APIRouter()

# Source of every number below:
#   research/aqi_estimation/results/20261012T135944Z-6e220f0c/RESULTS_SUMMARY.md
# Temporal re-evaluation: train 2015-2018, tune on 2019, test 2020-01-01..2020-07-01
# (4,404 rows, 26 cities), 9 pollutant features, rows with recorded AQI in 0-500.
# The old R2=0.932 came from a random row split and is not reported here.


@router.get("/models/comparison")
def get_model_comparison():
    return {
        "models": [
            {
                "name": "XGBoost",
                "status": "PRODUCTION",
                "r2": 0.898,
                "mae": 15.8,
                "rmse": 22.5,
                "train_time_seconds": None,
                "inference_ms": None,
                "description": (
                    "Gradient boosted trees (depth 5, 200 trees, learning rate 0.05, selected on 2019). "
                    "Scores are from a temporal test on Jan–Jul 2020. The deployed model's own "
                    "hyperparameters (depth 8, lr 0.1) scored R² 0.870, MAE 17.9 on the same test; "
                    "the deployed file itself was trained on rows that include 2020, so it was not "
                    "scored on that test."
                ),
                "strengths": [
                    "Beat linear regression on the 2020 test (MAE 15.8 vs 21.1)",
                    "Handles missing pollutant readings natively (no imputation)",
                    "Native feature importance via SHAP values",
                ],
                "color": "#22c55e",
            },
            {
                "name": "LightGBM",
                "status": "NOT RE-EVALUATED",
                "r2": None,
                "mae": None,
                "rmse": None,
                "train_time_seconds": None,
                "inference_ms": None,
                "description": "Not re-evaluated on the temporal test; earlier figures were unverified and were removed.",
                "strengths": [],
                "color": "#f59e0b",
            },
            {
                "name": "Random Forest",
                "status": "NOT RE-EVALUATED",
                "r2": None,
                "mae": None,
                "rmse": None,
                "train_time_seconds": None,
                "inference_ms": None,
                "description": "Not re-evaluated on the temporal test; earlier figures were unverified and were removed.",
                "strengths": [],
                "color": "#6b7280",
            },
        ],
        "dataset": {
            "name": "city_day.csv",
            "rows": 24850,
            "cities": 26,
            "period": "2015–2020",
            "features": 12,
            "target": "AQI",
        },
        "winner": "XGBoost",
        "verdict": (
            "XGBoost is in production. On a temporal test (train 2015–2018, tune on 2019, "
            "test Jan–Jul 2020) the 2019-tuned XGBoost reached R² 0.898 and MAE 15.8 AQI points, "
            "versus R² 0.842 and MAE 18.1 for the CPCB formula computed from daily means and "
            "R² 0.834 and MAE 21.1 for linear regression. The difference from the formula is not "
            "statistically significant (MAE difference −2.2, 95% CI −4.7 to +0.3). The earlier "
            "R² of 0.932 came from a random row split and overstates real-world accuracy."
        ),
    }
