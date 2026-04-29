import pandas as pd
import numpy as np
import os
import sys
import joblib
import shap
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.settings import DATA_PROCESSED, MODEL_DIR


# ─────────────────────────────────────────────
# STEP 1 — Load model and data
# ─────────────────────────────────────────────
def load_model_and_data():
    model_path   = os.path.join(MODEL_DIR, "best_model.pkl")
    feature_path = os.path.join(MODEL_DIR, "feature_cols.pkl")

    model        = joblib.load(model_path)
    feature_cols = joblib.load(feature_path)

    df = pd.read_csv(DATA_PROCESSED)
    X  = df[feature_cols]

    return model, X, feature_cols


# ─────────────────────────────────────────────
# STEP 2 — Build SHAP explainer
# TreeExplainer works natively with XGBoost
# and Random Forest — very fast, no sampling.
# ─────────────────────────────────────────────
def build_explainer(model, X):
    print("Building SHAP TreeExplainer...")
    explainer   = shap.TreeExplainer(model)

    # Calculate SHAP values for a sample of 500 rows
    # (full dataset takes too long for demonstration)
    X_sample    = X.sample(500, random_state=42)
    shap_values = explainer.shap_values(X_sample)

    print(f"SHAP values calculated for {len(X_sample)} samples")
    return explainer, shap_values, X_sample


# ─────────────────────────────────────────────
# STEP 3 — Global feature importance (summary)
# Shows which features matter most OVERALL
# across all predictions in the dataset.
# ─────────────────────────────────────────────
def plot_summary(shap_values, X_sample):
    print("\nGenerating SHAP summary plot...")
    plt.figure()
    shap.summary_plot(
        shap_values,
        X_sample,
        show=False,
        plot_type="bar"
    )
    plt.title("Global Feature Importance (SHAP)")
    plt.tight_layout()

    path = os.path.join(MODEL_DIR, "shap_summary.png")
    plt.savefig(path, bbox_inches='tight')
    plt.close()
    print(f"Saved: {path}")


# ─────────────────────────────────────────────
# STEP 4 — Beeswarm plot
# Shows not just importance but also direction:
# high PM2.5 = high AQI impact (red dots right)
# low PM2.5  = low AQI impact  (blue dots left)
# ─────────────────────────────────────────────
def plot_beeswarm(shap_values, X_sample):
    print("Generating SHAP beeswarm plot...")
    plt.figure()
    shap.summary_plot(
        shap_values,
        X_sample,
        show=False
    )
    plt.title("SHAP Beeswarm — Feature Impact Direction")
    plt.tight_layout()

    path = os.path.join(MODEL_DIR, "shap_beeswarm.png")
    plt.savefig(path, bbox_inches='tight')
    plt.close()
    print(f"Saved: {path}")


# ─────────────────────────────────────────────
# STEP 5 — Single prediction explanation
# This is the most powerful function for the UI.
# Given one row of pollutant values, it explains
# exactly WHY the model predicted that AQI.
# ─────────────────────────────────────────────
def explain_single_prediction(model, explainer, feature_cols, input_values):
    """
    input_values: dict like {
        'PM2.5': 120, 'PM10': 200, 'NO': 5,
        'NO2': 30, 'NOx': 35, 'NH3': 10,
        'CO': 2.5, 'SO2': 15, 'O3': 40,
        'Month': 12, 'Year': 2024, 'Season_Code': 0
    }
    """
    input_df    = pd.DataFrame([input_values])[feature_cols]
    prediction  = model.predict(input_df)[0]
    shap_vals   = explainer.shap_values(input_df)[0]

    # Build explanation dataframe
    explanation = pd.DataFrame({
        'Feature':    feature_cols,
        'Value':      input_df.iloc[0].values,
        'SHAP_Impact': shap_vals
    }).sort_values('SHAP_Impact', key=abs, ascending=False)

    return prediction, explanation


# ─────────────────────────────────────────────
# STEP 6 — Human readable explanation
# Converts SHAP numbers into plain English.
# This goes directly into the UI and chatbot.
# ─────────────────────────────────────────────
def human_readable_explanation(explanation, predicted_aqi):
    lines = []
    lines.append(f"Predicted AQI: {predicted_aqi:.0f}")
    lines.append("-" * 35)

    for _, row in explanation.head(5).iterrows():
        direction = "pushed AQI UP" if row['SHAP_Impact'] > 0 else "pulled AQI DOWN"
        lines.append(
            f"  {row['Feature']:<12} = {row['Value']:.2f}  →  "
            f"{direction} by {abs(row['SHAP_Impact']):.1f} points"
        )

    return "\n".join(lines)


# ─────────────────────────────────────────────
# STEP 7 — Save explainer for use in API + UI
# ─────────────────────────────────────────────
def save_explainer(explainer):
    import pickle
    path = os.path.join(MODEL_DIR, "shap_explainer.pkl")
    with open(path, 'wb') as f:
        pickle.dump(explainer, f)
    print(f"Explainer saved to: {path}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def run_explainability():
    print("\n" + "="*50)
    print("  SHAP EXPLAINABILITY PIPELINE")
    print("="*50 + "\n")

    model, X, feature_cols = load_model_and_data()
    explainer, shap_values, X_sample = build_explainer(model, X)

    plot_summary(shap_values, X_sample)
    plot_beeswarm(shap_values, X_sample)
    save_explainer(explainer)

    # Test with a sample Delhi winter prediction
    print("\n--- Testing single prediction explanation ---")
    test_input = {
        'PM2.5': 180.0, 'PM10': 250.0, 'NO': 8.0,
        'NO2': 45.0,  'NOx': 50.0,  'NH3': 20.0,
        'CO': 3.5,    'SO2': 18.0,  'O3': 25.0,
        'Month': 12,  'Year': 2024, 'Season_Code': 0
    }

    prediction, explanation = explain_single_prediction(
        model, explainer, feature_cols, test_input
    )

    readable = human_readable_explanation(explanation, prediction)
    print("\n" + readable)

    print("\n" + "="*50)
    print("  SHAP PIPELINE COMPLETE")
    print("="*50)


if __name__ == "__main__":
    run_explainability()