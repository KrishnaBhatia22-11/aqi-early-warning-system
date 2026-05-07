from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

_POPULATIONS = {
    "delhi":              32_000_000,
    "mumbai":             20_700_000,
    "bengaluru":          13_200_000,
    "bangalore":          13_200_000,
    "chennai":            10_900_000,
    "kolkata":            15_000_000,
    "hyderabad":          10_500_000,
    "ahmedabad":           8_400_000,
    "jaipur":              4_100_000,
    "lucknow":             3_700_000,
    "kanpur":              3_200_000,
    "patna":               2_400_000,
    "bhopal":              2_300_000,
    "pune":                7_400_000,
    "nagpur":              2_900_000,
    "surat":               7_100_000,
    "visakhapatnam":       2_300_000,
    "coimbatore":          2_200_000,
    "kochi":               2_100_000,
    "indore":              3_300_000,
    "chandigarh":          1_200_000,
    "amritsar":            1_300_000,
    "guwahati":            1_100_000,
    "bhubaneswar":         1_000_000,
    "thiruvananthapuram":  1_700_000,
    "varanasi":            1_500_000,
    "ranchi":              1_400_000,
}

_BREATHING = {"child": 0.65, "adult": 0.83, "elderly": 0.70, "athlete": 1.5}

_ADVICE = {
    "Minimal Risk":    "Air quality is satisfactory. Enjoy outdoor activities freely.",
    "Low Risk":        "Sensitive individuals should consider limiting prolonged outdoor exertion.",
    "Moderate Risk":   "Reduce prolonged outdoor exertion. Children and elderly should limit outdoor time.",
    "High Risk":       "Avoid all outdoor exercise. N95 mask mandatory if going outside.",
    "Very High Risk":  "Avoid all outdoor activity. N95 mask mandatory if going outside.",
    "Emergency Level": "Health emergency — stay indoors completely. N95 mask even indoors if no purifier.",
}


class HealthRequest(BaseModel):
    city: str
    aqi: float
    hours_outside: float
    age_group: str = "adult"
    has_condition: bool = False


@router.post("/health/impact")
def calculate_health_impact(req: HealthRequest):
    aqi   = max(0.0, req.aqi)
    hours = max(0.0, req.hours_outside)
    br    = _BREATHING.get(req.age_group.lower(), 0.83)

    # 1. Cigarette equivalent (Berkeley Earth formula)
    cigarettes = round((aqi * hours) / (22 * 24), 1)

    # 2. PM2.5 inhaled
    pm25_conc   = aqi * 0.6
    pm25_inhaled = round(pm25_conc * br * hours, 1)

    # 3. WHO daily limit percentage
    who_pct = min(999, round((pm25_conc * br * hours) / (15 * 24) * 100))

    # 4. Life minutes lost (Harvard SPH)
    base_min    = 0.071 * (aqi / 100)
    minutes_lost = round(base_min * (hours / 24), 1)

    # Sensitive population multiplier
    if req.has_condition:
        cigarettes   = round(cigarettes   * 1.5, 1)
        pm25_inhaled = round(pm25_inhaled * 1.5, 1)
        who_pct      = min(999, round(who_pct * 1.5))
        minutes_lost = round(minutes_lost * 1.5, 1)

    # 5. Risk level
    if   aqi <= 50:  risk = "Minimal Risk"
    elif aqi <= 100: risk = "Low Risk"
    elif aqi <= 200: risk = "Moderate Risk"
    elif aqi <= 300: risk = "High Risk"
    elif aqi <= 400: risk = "Very High Risk"
    else:            risk = "Emergency Level"

    # 6. Population impact
    norm = req.city.lower().strip()
    pop  = _POPULATIONS.get(norm, 0)
    coll = round(cigarettes * pop / 1_000_000, 1)

    mins_per_hour = round(base_min / 24 * 60, 1)
    s_h = "s" if hours != 1 else ""
    s_c = "s" if cigarettes != 1.0 else ""

    return {
        "city":          req.city,
        "aqi":           aqi,
        "hours_outside": hours,
        "personal": {
            "cigarette_equivalent":  cigarettes,
            "pm25_inhaled_ug":       pm25_inhaled,
            "who_limit_percentage":  who_pct,
            "minutes_life_lost":     minutes_lost,
            "risk_level":            risk,
            "advice":                _ADVICE[risk],
        },
        "city_level": {
            "population":                      pop,
            "collective_cigarettes_millions":  coll,
            "people_exposed":                  pop,
        },
        "comparisons": [
            f"Equivalent to smoking {cigarettes} cigarette{s_c}",
            f"{who_pct}% of WHO daily safe limit in just {hours} hour{s_h} outside",
            (f"{pop:,} {req.city} residents breathing this right now"
             if pop else "Millions of residents breathing this air right now"),
            f"Every hour outside costs ~{mins_per_hour} minutes of healthy life",
        ],
    }
