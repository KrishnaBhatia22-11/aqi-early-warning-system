# Provenance of the deployed model's R² = 0.932 ("Model A")

Everything below was verified by reading the code and re-scoring the committed artifact; nothing was retrained.

## Where the number comes from
- Training code: `src/models/train.py` (commit `2ce4e82c`, "Phase 3: ML training complete - XGBoost R2=0.932").
- Artifact: `models/best_model.pkl` = `XGBRegressor(n_estimators=200, max_depth=8, learning_rate=0.1, subsample=0.8, random_state=42)`.
  (Random Forest was also trained; XGBoost won on MAE.) `models/xgb_model.pkl` is a different, later model
  (`models/training_report.txt`: R² 0.6175 on `city_day_combined.csv`, not in the repo) and is NOT the deployed 0.932 model.
- Data: `data/processed/clean_data.csv`, built by `src/data/preprocess.py` from `data/raw/city_day.csv`:
  rows with missing AQI dropped (29,531 → 24,850), AQI **clipped** to 500 (543 raw rows were >500; 545 rows now sit at exactly 500), pollutant NaNs filled with each city's **full-history median** (computed before any split).
- Features (12): PM2.5, PM10, NO, NO2, NOx, NH3, CO, SO2, O3, **Month, Year, Season_Code**.
- Target: recorded `AQI`.
- Split: `train_test_split(test_size=0.2, random_state=42)` — a **random row split**, not temporal. 19,880 train / 4,970 test rows.
- Metric: re-scoring the artifact on that split gives R² = 0.932018, MAE = 17.928, RMSE = 29.500
  (`tables/step1_random_split_reference.csv`). R² matches the claim.

## Discrepancies in repo claims
- README / API text state MAE = 21.33; re-scoring gives MAE 17.93. No MLflow metric file in `mlruns/` contains 21.33.
- README says "trained on 29,531 rows"; 29,531 is the raw row count. The model used 24,850 rows (19,880 for fitting).

## Why 0.932 is not a forecast/estimation guarantee
Random splitting puts neighbouring days of the same city (and same-year rows) in both train and test; median imputation
used test-period rows; `Year` is a feature, which a tree cannot extrapolate to unseen years; 545 target values are
clipped at 500. This study therefore re-evaluates with a date split, no imputation leakage, no calendar features,
and AQI restricted to 0–500.
