# ─────────────────────────────────────────────
# Health Risk Scoring System
# Goes beyond AQI category — tells you exactly
# who is at risk and what they should do.
# This is YOUR custom logic — original thinking.
# ─────────────────────────────────────────────

HEALTH_GROUPS = {
    "children":        "Children (under 12)",
    "elderly":         "Elderly (above 60)",
    "asthma":          "People with Asthma",
    "heart":           "People with Heart Conditions",
    "pregnant":        "Pregnant Women",
    "healthy_adults":  "Healthy Adults",
    "athletes":        "Athletes / Outdoor Workers",
}

# Risk level per group per AQI range
RISK_MATRIX = {
    "Good": {
        "children":       ("Safe",     "Normal outdoor activity fine"),
        "elderly":        ("Safe",     "Normal activity fine"),
        "asthma":         ("Safe",     "Normal activity fine"),
        "heart":          ("Safe",     "Normal activity fine"),
        "pregnant":       ("Safe",     "Normal outdoor activity fine"),
        "healthy_adults": ("Safe",     "Normal activity fine"),
        "athletes":       ("Safe",     "Outdoor training fine"),
    },
    "Satisfactory": {
        "children":       ("Low",      "Outdoor play fine, limit if sensitive"),
        "elderly":        ("Low",      "Light outdoor activity fine"),
        "asthma":         ("Low",      "Keep inhaler handy"),
        "heart":          ("Low",      "Monitor symptoms"),
        "pregnant":       ("Low",      "Short outdoor walks fine"),
        "healthy_adults": ("Safe",     "Normal activity fine"),
        "athletes":       ("Low",      "Outdoor training fine, monitor"),
    },
    "Moderate": {
        "children":       ("Medium",   "Limit prolonged outdoor play"),
        "elderly":        ("Medium",   "Avoid strenuous outdoor activity"),
        "asthma":         ("High",     "Use inhaler before going out"),
        "heart":          ("High",     "Avoid outdoor exertion"),
        "pregnant":       ("Medium",   "Limit outdoor exposure"),
        "healthy_adults": ("Low",      "Sensitive people should take care"),
        "athletes":       ("Medium",   "Move training indoors if possible"),
    },
    "Poor": {
        "children":       ("High",     "Avoid outdoor activity"),
        "elderly":        ("High",     "Stay indoors, keep windows closed"),
        "asthma":         ("Severe",   "Stay indoors, have medication ready"),
        "heart":          ("Severe",   "Stay indoors, consult doctor"),
        "pregnant":       ("High",     "Stay indoors, avoid all exposure"),
        "healthy_adults": ("Medium",   "Reduce prolonged outdoor exertion"),
        "athletes":       ("High",     "Move all training indoors"),
    },
    "Very Poor": {
        "children":       ("Severe",   "Do NOT go outside"),
        "elderly":        ("Severe",   "Do NOT go outside"),
        "asthma":         ("Severe",   "Emergency — stay indoors with medication"),
        "heart":          ("Severe",   "Emergency — stay indoors"),
        "pregnant":       ("Severe",   "Do NOT go outside"),
        "healthy_adults": ("High",     "Avoid all outdoor activity"),
        "athletes":       ("Severe",   "No outdoor activity whatsoever"),
    },
    "Severe": {
        "children":       ("Severe",   "EMERGENCY — do not go outside at all"),
        "elderly":        ("Severe",   "EMERGENCY — do not go outside at all"),
        "asthma":         ("Severe",   "EMERGENCY — have emergency medication ready"),
        "heart":          ("Severe",   "EMERGENCY — seek medical advice"),
        "pregnant":       ("Severe",   "EMERGENCY — do not go outside at all"),
        "healthy_adults": ("Severe",   "Avoid all outdoor exposure"),
        "athletes":       ("Severe",   "EMERGENCY — no outdoor activity"),
    },
}

RISK_COLORS = {
    "Safe":   "#2ecc71",
    "Low":    "#f1c40f",
    "Medium": "#e67e22",
    "High":   "#e74c3c",
    "Severe": "#8e44ad",
}


def get_health_advisory(aqi_category):
    """
    Given an AQI category string, returns full
    health advisory for all population groups.
    """
    if aqi_category not in RISK_MATRIX:
        aqi_category = "Moderate"

    advisory = {}
    for group_key, group_name in HEALTH_GROUPS.items():
        risk_level, advice = RISK_MATRIX[aqi_category][group_key]
        advisory[group_key] = {
            "group":      group_name,
            "risk_level": risk_level,
            "advice":     advice,
            "color":      RISK_COLORS[risk_level],
        }
    return advisory


def get_general_precautions(aqi_category):
    """
    Returns general precautions for any person
    based on the current AQI category.
    """
    precautions = {
        "Good": [
            "Air quality is fine for all activities",
            "Great day for outdoor exercise",
        ],
        "Satisfactory": [
            "Unusually sensitive people should consider limiting outdoor exertion",
            "Most people can carry out normal outdoor activities",
        ],
        "Moderate": [
            "Wear an N95 mask if outdoors for long periods",
            "Keep windows partially closed during peak hours",
            "Sensitive groups should limit outdoor activity",
        ],
        "Poor": [
            "Wear N95 mask outdoors — mandatory for vulnerable groups",
            "Keep all windows and doors closed",
            "Use air purifier indoors if available",
            "Avoid outdoor exercise completely",
            "Drink plenty of water to help lungs",
        ],
        "Very Poor": [
            "Wear N95 mask even for short outdoor trips",
            "All windows and doors must be sealed",
            "Use air purifier on highest setting",
            "Work from home if possible",
            "Seek medical attention if experiencing breathing difficulty",
        ],
        "Severe": [
            "EMERGENCY level — avoid all outdoor exposure",
            "Seal gaps in windows and doors",
            "Do NOT exercise outdoors under any circumstances",
            "Seek immediate medical attention if feeling unwell",
            "Schools and outdoor events should be cancelled",
        ],
    }
    return precautions.get(aqi_category, precautions["Moderate"])