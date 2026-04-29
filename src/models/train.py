import pandas as pd
import numpy as np
import os
import sys
import joblib
import mlflow
import mlflow.sklearn

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.settings import DATA_PROCESSED, MODEL_DIR

# ─────────────────────────────────────────────
# STEP 1 — Load cleaned data
# ─────────────────────────────────────────────
def load_data():
    df = pd.read_csv(DATA_PROCESSED)
    print(f"Loaded cleaned data: {df.shape}")
    return df


# ─────────────────────────────────────────────
# STEP 2 — Prepare features and target
# These are the columns the model learns from.
# We drop City, Date, AQI_Bucket, AQI_Category
# because they are either non-numeric or derived
# from AQI itself (would cause data leakage).
# ─────────────────────────────────────────────
def prepare_features(df):
    feature_cols = [
        'PM2.5', 'PM10', 'NO', 'NO2', 'NOx',
        'NH3', 'CO', 'SO2', 'O3',
        'Month', 'Year', 'Season_Code'
    ]

    X = df[feature_cols]
    y = df['AQI']

    print(f"Features: {feature_cols}")
    print(f"X shape: {X.shape}, y shape: {y.shape}")
    return X, y, feature_cols


# ─────────────────────────────────────────────
# STEP 3 — Split into train and test sets
# 80% training, 20% testing
# random_state=42 means results are reproducible
# ─────────────────────────────────────────────
def split_data(X, y):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"Train size: {X_train.shape[0]}, Test size: {X_test.shape[0]}")
    return X_train, X_test, y_train, y_test


# ─────────────────────────────────────────────
# STEP 4 — Evaluate a trained model
# ─────────────────────────────────────────────
def evaluate_model(model, X_test, y_test):
    predictions = model.predict(X_test)
    mae  = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    r2   = r2_score(y_test, predictions)
    return {
        "MAE":  round(mae, 3),
        "RMSE": round(rmse, 3),
        "R2":   round(r2, 3)
    }, predictions


# ─────────────────────────────────────────────
# STEP 5 — Train Random Forest with MLflow
# MLflow logs every run so you can compare them
# in a dashboard and reproduce any result.
# ─────────────────────────────────────────────
def train_random_forest(X_train, X_test, y_train, y_test):
    print("\n--- Training Random Forest ---")

    params = {
        "n_estimators": 200,
        "max_depth": 15,
        "min_samples_split": 5,
        "random_state": 42,
        "n_jobs": -1
    }

    with mlflow.start_run(run_name="RandomForest"):
        model = RandomForestRegressor(**params)
        model.fit(X_train, y_train)

        metrics, predictions = evaluate_model(model, X_test, y_test)

        # Log everything to MLflow
        mlflow.log_params(params)
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(model, "random_forest_model")

        print(f"Random Forest Results:")
        print(f"  MAE:  {metrics['MAE']}")
        print(f"  RMSE: {metrics['RMSE']}")
        print(f"  R2:   {metrics['R2']}")

    return model, metrics


# ─────────────────────────────────────────────
# STEP 6 — Train XGBoost with MLflow
# ─────────────────────────────────────────────
def train_xgboost(X_train, X_test, y_train, y_test):
    print("\n--- Training XGBoost ---")

    params = {
        "n_estimators": 200,
        "max_depth": 8,
        "learning_rate": 0.1,
        "subsample": 0.8,
        "random_state": 42,
        "n_jobs": -1
    }

    with mlflow.start_run(run_name="XGBoost"):
        model = XGBRegressor(**params, verbosity=0)
        model.fit(X_train, y_train)

        metrics, predictions = evaluate_model(model, X_test, y_test)

        # Log everything to MLflow
        mlflow.log_params(params)
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(model, "xgboost_model")

        print(f"XGBoost Results:")
        print(f"  MAE:  {metrics['MAE']}")
        print(f"  RMSE: {metrics['RMSE']}")
        print(f"  R2:   {metrics['R2']}")

    return model, metrics


# ─────────────────────────────────────────────
# STEP 7 — Save the best model
# Whichever model has lower MAE wins.
# We save it as best_model.pkl for the API
# and Streamlit app to load later.
# ─────────────────────────────────────────────
def save_best_model(rf_model, rf_metrics, xgb_model, xgb_metrics, feature_cols):
    os.makedirs(MODEL_DIR, exist_ok=True)

    if rf_metrics['MAE'] <= xgb_metrics['MAE']:
        best_model = rf_model
        best_name  = "Random Forest"
        best_metrics = rf_metrics
    else:
        best_model = xgb_model
        best_name  = "XGBoost"
        best_metrics = xgb_metrics

    # Save model
    model_path = os.path.join(MODEL_DIR, "best_model.pkl")
    joblib.dump(best_model, model_path)

    # Save feature column list so prediction always uses same features
    feature_path = os.path.join(MODEL_DIR, "feature_cols.pkl")
    joblib.dump(feature_cols, feature_path)

    print(f"\n Best model: {best_name}")
    print(f"  MAE:  {best_metrics['MAE']}")
    print(f"  RMSE: {best_metrics['RMSE']}")
    print(f"  R2:   {best_metrics['R2']}")
    print(f"  Saved to: {model_path}")

    return best_model, best_name


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def run_training():
    print("\n" + "="*50)
    print("  AQI MODEL TRAINING PIPELINE")
    print("="*50 + "\n")

    mlflow.set_experiment("AQI-Prediction")

    df = load_data()
    X, y, feature_cols = prepare_features(df)
    X_train, X_test, y_train, y_test = split_data(X, y)

    rf_model,  rf_metrics  = train_random_forest(X_train, X_test, y_train, y_test)
    xgb_model, xgb_metrics = train_xgboost(X_train, X_test, y_train, y_test)

    best_model, best_name = save_best_model(
        rf_model, rf_metrics,
        xgb_model, xgb_metrics,
        feature_cols
    )

    print("\n" + "="*50)
    print("  TRAINING COMPLETE")
    print("="*50)

    return best_model


if __name__ == "__main__":
    run_training()