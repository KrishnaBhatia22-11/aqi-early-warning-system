import pandas as pd
import numpy as np
import os
import sys
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.settings import DATA_PROCESSED, MODEL_DIR


def load_model_and_data():
    model_path   = os.path.join(MODEL_DIR, "best_model.pkl")
    feature_path = os.path.join(MODEL_DIR, "feature_cols.pkl")

    model        = joblib.load(model_path)
    feature_cols = joblib.load(feature_path)

    df = pd.read_csv(DATA_PROCESSED)
    X  = df[feature_cols]
    y  = df['AQI']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    return model, X_train, X_test, y_train, y_test, feature_cols


def print_metrics(model, X_test, y_test):
    preds = model.predict(X_test)
    mae   = mean_absolute_error(y_test, preds)
    rmse  = np.sqrt(mean_squared_error(y_test, preds))
    r2    = r2_score(y_test, preds)

    print("\n" + "="*40)
    print("  MODEL EVALUATION REPORT")
    print("="*40)
    print(f"  MAE  (avg error in AQI points) : {mae:.2f}")
    print(f"  RMSE (penalises large errors)  : {rmse:.2f}")
    print(f"  R²   (variance explained)      : {r2:.4f}")
    print("="*40)
    return preds


def cross_validate(model, X_train, y_train):
    print("\nRunning 5-fold cross validation...")
    scores = cross_val_score(
        model, X_train, y_train,
        cv=5, scoring='r2', n_jobs=-1
    )
    print(f"  CV R² scores : {[round(s,3) for s in scores]}")
    print(f"  Mean R²      : {scores.mean():.4f}")
    print(f"  Std Dev      : {scores.std():.4f}")
    print("  (Low std dev = model is consistent, not lucky)")


def plot_feature_importance(model, feature_cols):
    importance = model.feature_importances_
    fi_df = pd.DataFrame({
        'Feature':    feature_cols,
        'Importance': importance
    }).sort_values('Importance', ascending=False)

    print("\nFeature Importance:")
    print(fi_df.to_string(index=False))

    plt.figure(figsize=(10, 6))
    sns.barplot(data=fi_df, x='Importance', y='Feature', palette='viridis')
    plt.title('Feature Importance — AQI Prediction Model')
    plt.tight_layout()

    plot_path = os.path.join(MODEL_DIR, "feature_importance.png")
    plt.savefig(plot_path)
    print(f"\nFeature importance plot saved to: {plot_path}")
    plt.show()


def plot_predictions_vs_actual(y_test, preds):
    plt.figure(figsize=(8, 8))
    plt.scatter(y_test, preds, alpha=0.3, color='steelblue', s=10)
    plt.plot([0, 500], [0, 500], 'r--', linewidth=2, label='Perfect prediction')
    plt.xlabel('Actual AQI')
    plt.ylabel('Predicted AQI')
    plt.title('Actual vs Predicted AQI')
    plt.legend()
    plt.tight_layout()

    plot_path = os.path.join(MODEL_DIR, "actual_vs_predicted.png")
    plt.savefig(plot_path)
    print(f"Actual vs Predicted plot saved to: {plot_path}")
    plt.show()


def run_evaluation():
    model, X_train, X_test, y_train, y_test, feature_cols = load_model_and_data()
    preds = print_metrics(model, X_test, y_test)
    cross_validate(model, X_train, y_train)
    plot_feature_importance(model, feature_cols)
    plot_predictions_vs_actual(y_test, preds)
    print("\nEvaluation complete!")


if __name__ == "__main__":
    run_evaluation()