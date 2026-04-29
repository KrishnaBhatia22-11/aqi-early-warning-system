import pandas as pd
import numpy as np
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.settings import DATA_RAW, DATA_PROCESSED

# ─────────────────────────────────────────────
# STEP 1 — Load the raw dataset
# ─────────────────────────────────────────────
def load_data():
    print("Loading dataset...")
    df = pd.read_csv(DATA_RAW)
    print(f"Loaded {df.shape[0]} rows and {df.shape[1]} columns")
    return df


# ─────────────────────────────────────────────
# STEP 2 — Drop columns that are too incomplete
# ─────────────────────────────────────────────
def drop_weak_columns(df):
    # Xylene is 61% missing — useless for training
    # Toluene is 27% missing — not a core AQI pollutant
    # Benzene is 19% missing — dropping to keep model clean
    cols_to_drop = ['Xylene', 'Toluene', 'Benzene']
    df = df.drop(columns=cols_to_drop)
    print(f"Dropped columns: {cols_to_drop}")
    return df


# ─────────────────────────────────────────────
# STEP 3 — Drop rows where AQI is missing
# ─────────────────────────────────────────────
def drop_missing_target(df):
    before = len(df)
    df = df.dropna(subset=['AQI'])
    after = len(df)
    print(f"Dropped {before - after} rows with missing AQI")
    return df


# ─────────────────────────────────────────────
# STEP 4 — Cap AQI outliers at 500
# India's official AQI scale only goes to 500.
# Anything above is a sensor error or data issue.
# ─────────────────────────────────────────────
def cap_aqi_outliers(df):
    outliers = (df['AQI'] > 500).sum()
    df['AQI'] = df['AQI'].clip(upper=500)
    print(f"Capped {outliers} AQI outlier rows to 500")
    return df


# ─────────────────────────────────────────────
# STEP 5 — Impute missing values city-wise
# We use each city's own median, not the global
# median. Delhi's PM2.5 is very different from
# Chennai's — a global average would be wrong.
# ─────────────────────────────────────────────
def impute_city_wise(df):
    pollutant_cols = ['PM2.5', 'PM10', 'NO', 'NO2', 'NOx', 'NH3', 'CO', 'SO2', 'O3']

    for col in pollutant_cols:
        # Fill each city's missing values with that city's median
        df[col] = df.groupby('City')[col].transform(
            lambda x: x.fillna(x.median())
        )
        # If a city has ALL values missing for a column, fall back to global median
        df[col] = df[col].fillna(df[col].median())

    print(f"Imputed missing values in: {pollutant_cols}")
    return df


# ─────────────────────────────────────────────
# STEP 6 — Feature engineering
# Extract useful time-based features from Date
# ─────────────────────────────────────────────
def engineer_features(df):
    df['Date'] = pd.to_datetime(df['Date'])
    df['Month']  = df['Date'].dt.month
    df['Year']   = df['Date'].dt.year
    df['Season'] = df['Month'].map({
        12: 'Winter', 1: 'Winter', 2: 'Winter',
        3:  'Spring', 4: 'Spring', 5: 'Spring',
        6:  'Summer', 7: 'Summer', 8: 'Summer',
        9:  'Monsoon',10:'Monsoon',11:'Monsoon'
    })

    # Encode Season as a number so ML model can use it
    season_map = {'Winter': 0, 'Spring': 1, 'Summer': 2, 'Monsoon': 3}
    df['Season_Code'] = df['Season'].map(season_map)

    print("Added features: Month, Year, Season, Season_Code")
    return df


# ─────────────────────────────────────────────
# STEP 7 — Add AQI category column
# ─────────────────────────────────────────────
def add_aqi_category(df):
    def categorize_aqi(aqi):
        if aqi <= 50:   return 'Good'
        if aqi <= 100:  return 'Satisfactory'
        if aqi <= 200:  return 'Moderate'
        if aqi <= 300:  return 'Poor'
        if aqi <= 400:  return 'Very Poor'
        return 'Severe'

    df['AQI_Category'] = df['AQI'].apply(categorize_aqi)
    print("Added AQI_Category column")
    print(df['AQI_Category'].value_counts())
    return df


# ─────────────────────────────────────────────
# STEP 8 — Save the cleaned dataset
# ─────────────────────────────────────────────
def save_processed(df):
    os.makedirs(os.path.dirname(DATA_PROCESSED), exist_ok=True)
    df.to_csv(DATA_PROCESSED, index=False)
    print(f"\nSaved cleaned data to: {DATA_PROCESSED}")
    print(f"Final shape: {df.shape}")


# ─────────────────────────────────────────────
# MAIN — run all steps in order
# ─────────────────────────────────────────────
def run_pipeline():
    print("\n" + "="*50)
    print("  AQI DATA PREPROCESSING PIPELINE")
    print("="*50 + "\n")

    df = load_data()
    df = drop_weak_columns(df)
    df = drop_missing_target(df)
    df = cap_aqi_outliers(df)
    df = impute_city_wise(df)
    df = engineer_features(df)
    df = add_aqi_category(df)
    save_processed(df)

    print("\n" + "="*50)
    print("  PREPROCESSING COMPLETE")
    print("="*50)
    return df


if __name__ == "__main__":
    df = run_pipeline()