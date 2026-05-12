import os
from dotenv import load_dotenv

load_dotenv()

WAQI_API_KEY          = os.getenv("WAQI_API_KEY")
GROQ_API_KEY          = os.getenv("GROQ_API_KEY")
OPENWEATHER_API_KEY   = os.getenv("OPENWEATHER_API_KEY")

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
    # ── Metro Tier ──────────────────────────────────────────────
    "Delhi":              {"lat": 28.6139, "lon": 77.2090},
    "Mumbai":             {"lat": 19.0760, "lon": 72.8777},
    "Bengaluru":          {"lat": 12.9716, "lon": 77.5946},
    "Chennai":            {"lat": 13.0827, "lon": 80.2707},
    "Kolkata":            {"lat": 22.5726, "lon": 88.3639},
    "Hyderabad":          {"lat": 17.3850, "lon": 78.4867},
    "Ahmedabad":          {"lat": 23.0225, "lon": 72.5714},
    "Pune":               {"lat": 18.5204, "lon": 73.8567},
    # ── Major Cities ────────────────────────────────────────────
    "Jaipur":             {"lat": 26.9124, "lon": 75.7873},
    "Lucknow":            {"lat": 26.8467, "lon": 80.9462},
    "Kanpur":             {"lat": 26.4499, "lon": 80.3319},
    "Patna":              {"lat": 25.5941, "lon": 85.1376},
    "Bhopal":             {"lat": 23.2599, "lon": 77.4126},
    "Nagpur":             {"lat": 21.1458, "lon": 79.0882},
    "Surat":              {"lat": 21.1702, "lon": 72.8311},
    "Indore":             {"lat": 22.7196, "lon": 75.8577},
    "Visakhapatnam":      {"lat": 17.6868, "lon": 83.2185},
    "Chandigarh":         {"lat": 30.7333, "lon": 76.7794},
    "Coimbatore":         {"lat": 11.0168, "lon": 76.9558},
    "Kochi":              {"lat":  9.9312, "lon": 76.2673},
    # ── Heritage / Tourist ──────────────────────────────────────
    "Agra":               {"lat": 27.1767, "lon": 78.0081},
    "Varanasi":           {"lat": 25.3176, "lon": 82.9739},
    "Amritsar":           {"lat": 31.6340, "lon": 74.8723},
    "Jodhpur":            {"lat": 26.2389, "lon": 73.0243},
    "Udaipur":            {"lat": 24.5854, "lon": 73.7125},
    "Mysuru":             {"lat": 12.2958, "lon": 76.6394},
    "Pondicherry":        {"lat": 11.9416, "lon": 79.8083},
    # ── Industrial Corridors ────────────────────────────────────
    "Ghaziabad":          {"lat": 28.6692, "lon": 77.4538},
    "Noida":              {"lat": 28.5355, "lon": 77.3910},
    "Faridabad":          {"lat": 28.4089, "lon": 77.3178},
    "Gurugram":           {"lat": 28.4595, "lon": 77.0266},
    "Meerut":             {"lat": 28.9845, "lon": 77.7064},
    "Moradabad":          {"lat": 28.8386, "lon": 78.7733},
    "Ludhiana":           {"lat": 30.9010, "lon": 75.8573},
    "Jalandhar":          {"lat": 31.3260, "lon": 75.5762},
    # ── Tier 2 Growing ──────────────────────────────────────────
    "Bhubaneswar":        {"lat": 20.2961, "lon": 85.8245},
    "Guwahati":           {"lat": 26.1445, "lon": 91.7362},
    "Ranchi":             {"lat": 23.3441, "lon": 85.3096},
    "Raipur":             {"lat": 21.2514, "lon": 81.6296},
    "Dehradun":           {"lat": 30.3165, "lon": 78.0322},
    "Shimla":             {"lat": 31.1048, "lon": 77.1734},
    "Jammu":              {"lat": 32.7266, "lon": 74.8570},
    "Srinagar":           {"lat": 34.0837, "lon": 74.7973},
    "Thiruvananthapuram": {"lat":  8.5241, "lon": 76.9366},
    "Madurai":            {"lat":  9.9252, "lon": 78.1198},
    "Vijayawada":         {"lat": 16.5062, "lon": 80.6480},
    "Nashik":             {"lat": 19.9975, "lon": 73.7898},
    "Aurangabad":         {"lat": 19.8762, "lon": 75.3433},
    "Kolhapur":           {"lat": 16.7050, "lon": 74.2433},
    "Solapur":            {"lat": 17.6599, "lon": 75.9064},
    "Warangal":           {"lat": 17.9784, "lon": 79.5941},
    "Guntur":             {"lat": 16.3067, "lon": 80.4365},
    "Tiruchirappalli":    {"lat": 10.7905, "lon": 78.7047},
}
