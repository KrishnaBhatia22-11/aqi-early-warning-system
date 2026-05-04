import os
from dotenv import load_dotenv

load_dotenv()

WAQI_API_KEY   = os.getenv("WAQI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

BASE_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_RAW       = os.path.join(BASE_DIR, "data", "raw", "city_day.csv")
DATA_PROCESSED = os.path.join(BASE_DIR, "data", "processed", "clean_data.csv")
MODEL_DIR      = os.path.join(BASE_DIR, "models")

AQI_CATEGORIES = {
    (0, 50):    "Good",
    (51, 100):  "Satisfactory",
    (101, 200): "Moderate",
    (201, 300): "Poor",
    (301, 400): "Very Poor",
    (401, 500): "Severe",
}

CITY_COORDS = {
    "Delhi":     {"lat": 28.6139, "lon": 77.2090},
    "Mumbai":    {"lat": 19.0760, "lon": 72.8777},
    "Bangalore": {"lat": 12.9716, "lon": 77.5946},
    "Chennai":   {"lat": 13.0827, "lon": 80.2707},
    "Kolkata":   {"lat": 22.5726, "lon": 88.3639},
    "Hyderabad": {"lat": 17.3850, "lon": 78.4867},
    "Ahmedabad": {"lat": 23.0225, "lon": 72.5714},
    "Pune":      {"lat": 18.5204, "lon": 73.8567},
    "Jaipur":    {"lat": 26.9124, "lon": 75.7873},
    "Lucknow":   {"lat": 26.8467, "lon": 80.9462},
}