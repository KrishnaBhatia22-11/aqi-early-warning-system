"""
India CPCB National Air Quality Index.

The official method (CPCB, 2014): every pollutant is converted to a sub-index by
linear interpolation inside its breakpoint band, and the overall AQI is the MAX
of the available sub-indices. The pollutant carrying that max is the "dominant"
pollutant.

    I = ((I_hi - I_lo) / (BP_hi - BP_lo)) * (C - BP_lo) + I_lo

This is NOT the US EPA scale the app used before. The same concentration maps to
a different number on each, so values from the two must never be mixed; anything
produced here is labelled AQI_STANDARD.

─────────────────────────────────────────────────────────────────────────────
WHICH DIRECTION YOU NEED — read this before using either function
─────────────────────────────────────────────────────────────────────────────
Two conversions live here and they are easy to confuse. Confusing them is the
bug that once broke this project (PM2.5 stored as a 0-500 sub-index in a field
that meant µg/m³), so each is named for what it returns:

    sub_index(pollutant, concentration) -> 0-500   forward, from µg/m³ or mg/m³
    concentration(pollutant, sub_index) -> µg/m³   inverse, back to a real unit

The CPCB feed on data.gov.in publishes SUB-INDICES in its `avg_value` field,
despite the field name — verified against the live feed on four independent
checks (see cpcb_client's unit gate). So cpcb_client takes the inverse
direction: it reads sub-indices, maxes them for the AQI, and calls
concentration() to recover the real µg/m³ figures it displays and stores.

Units, when a concentration is involved, are µg/m³ for everything except CO,
which is mg/m³.
"""

AQI_STANDARD = "India CPCB AQI (National)"

# Pollutant → list of (BP_lo, BP_hi, I_lo, I_hi).
#
# Bands are stated by CPCB with integer gaps (…0-30, 31-60…). Using the printed
# lower bound (31) would leave 30.0-31.0 undefined, so each band starts where the
# previous one ends; the sub-index is continuous across the whole range.
BREAKPOINTS = {
    # PM2.5 — µg/m³, 24h average
    "PM2.5": [(0, 30, 0, 50), (30, 60, 51, 100), (60, 90, 101, 200),
              (90, 120, 201, 300), (120, 250, 301, 400), (250, 500, 401, 500)],
    # PM10 — µg/m³, 24h average
    "PM10":  [(0, 50, 0, 50), (50, 100, 51, 100), (100, 250, 101, 200),
              (250, 350, 201, 300), (350, 430, 301, 400), (430, 600, 401, 500)],
    # NO2 — µg/m³, 24h average
    "NO2":   [(0, 40, 0, 50), (40, 80, 51, 100), (80, 180, 101, 200),
              (180, 280, 201, 300), (280, 400, 301, 400), (400, 500, 401, 500)],
    # O3 — µg/m³, 8h average
    "OZONE": [(0, 50, 0, 50), (50, 100, 51, 100), (100, 168, 101, 200),
              (168, 208, 201, 300), (208, 748, 301, 400), (748, 1000, 401, 500)],
    # CO — mg/m³, 8h average
    "CO":    [(0, 1.0, 0, 50), (1.0, 2.0, 51, 100), (2.0, 10, 101, 200),
              (10, 17, 201, 300), (17, 34, 301, 400), (34, 50, 401, 500)],
    # SO2 — µg/m³, 24h average
    "SO2":   [(0, 40, 0, 50), (40, 80, 51, 100), (80, 380, 101, 200),
              (380, 800, 201, 300), (800, 1600, 301, 400), (1600, 2000, 401, 500)],
    # NH3 — µg/m³, 24h average
    "NH3":   [(0, 200, 0, 50), (200, 400, 51, 100), (400, 800, 101, 200),
              (800, 1200, 201, 300), (1200, 1800, 301, 400), (1800, 2000, 401, 500)],
}

# The unit a CONCENTRATION carries for each pollutant — what sub_index() expects
# and what concentration() returns.
UNITS = {
    "PM2.5": "ug/m3", "PM10": "ug/m3", "NO2": "ug/m3",
    "OZONE": "ug/m3", "SO2": "ug/m3", "NH3": "ug/m3",
    "CO": "mg/m3",
}

# The AQI scale runs 0-500 and nothing outside that is a reading.
AQI_MIN, AQI_MAX = 0, 500

# CPCB category bands. Note these are NOT the US EPA names: at 150 the US scale
# says "Unhealthy for sensitive groups", CPCB says "Moderate".
CATEGORIES = [
    (50,  "Good"),
    (100, "Satisfactory"),
    (200, "Moderate"),
    (300, "Poor"),
    (400, "Very Poor"),
    (500, "Severe"),
]

# Hex per category — matches the frontend's band table so the API, the alert
# emails and the OG cards all colour a number the way the map does.
CATEGORY_COLORS = {
    "Good":         "#34d27a",
    "Satisfactory": "#a3d13a",
    "Moderate":     "#f5d142",
    "Poor":         "#FF6B00",
    "Very Poor":    "#ef3a4d",
    "Severe":       "#7e0023",
    "Unknown":      "#94a3b8",
}

# Legacy colour vocabulary — waqi_client returned these bare colour words in the
# `color` field and parts of the app still key off them, so the names are kept
# even though the bands moved to CPCB's.
CATEGORY_COLOR_WORDS = {
    "Good":         "green",
    "Satisfactory": "lightgreen",
    "Moderate":     "yellow",
    "Poor":         "orange",
    "Very Poor":    "red",
    "Severe":       "maroon",
    "Unknown":      "gray",
}

# CPCB will not publish an AQI for a station reporting fewer than three
# pollutants, and one of them must be a particulate — a "clean" AQI computed
# from SO2 alone says nothing about the air anyone is breathing.
MIN_POLLUTANTS = 3
PARTICULATES = ("PM2.5", "PM10")


def sub_index(pollutant, conc):
    """CONCENTRATION → sub-index (0-500), or None if unusable.

    `conc` must be in the unit UNITS names for this pollutant. Values above the
    top breakpoint clamp to 500 (CPCB's scale stops there); negatives and
    non-numbers return None rather than 0, so a broken sensor cannot read as
    clean air.
    """
    table = BREAKPOINTS.get(pollutant)
    if table is None:
        return None
    try:
        c = float(conc)
    except (TypeError, ValueError):
        return None
    if c < 0:
        return None

    for bp_lo, bp_hi, i_lo, i_hi in table:
        if c <= bp_hi:
            if c <= bp_lo:
                return round(i_lo)
            return round(((i_hi - i_lo) / (bp_hi - bp_lo)) * (c - bp_lo) + i_lo)

    return AQI_MAX  # above the top band — CPCB caps the scale at Severe


def concentration(pollutant, index, ndigits=1):
    """SUB-INDEX → concentration, in this pollutant's UNITS entry, or None.

    The exact inverse of sub_index within a band. Sub-index bands are not evenly
    sized in concentration terms, so this is a genuine interpolation, not a
    scale factor: PM2.5 sub-index 150 is ~75 µg/m³ while PM10 sub-index 150 is
    ~174 µg/m³.

    The result is the concentration CPCB derived the published sub-index from,
    so it is a reconstruction, not a raw measurement — precise to about the
    width of one rounding step of the sub-index.

    Not an exact round-trip at the five band boundaries. CPCB's table leaves an
    integer gap there (…0-50, 51-100…), so sub-indices 50 and 51 both sit at the
    same concentration and sub_index(concentration(p, 51)) comes back 50. That
    is the published table's own discontinuity, not a defect here, and it moves
    a displayed concentration by less than a rounding step.
    """
    table = BREAKPOINTS.get(pollutant)
    if table is None:
        return None
    try:
        i = float(index)
    except (TypeError, ValueError):
        return None
    if i < AQI_MIN or i > AQI_MAX:
        return None

    for bp_lo, bp_hi, i_lo, i_hi in table:
        if i <= i_hi:
            if i <= i_lo:
                return round(float(bp_lo), ndigits)
            return round(bp_lo + (i - i_lo) * (bp_hi - bp_lo) / (i_hi - i_lo), ndigits)

    top = table[-1]
    return round(float(top[1]), ndigits)


def categorize_aqi(aqi):
    """CPCB category name for an AQI value."""
    if aqi is None:
        return "Unknown"
    try:
        aqi = float(aqi)
    except (TypeError, ValueError):
        return "Unknown"
    for ceiling, name in CATEGORIES:
        if aqi <= ceiling:
            return name
    return "Severe"


def aqi_color(aqi):
    """Legacy colour word for an AQI value (matches waqi_client's old vocabulary)."""
    return CATEGORY_COLOR_WORDS.get(categorize_aqi(aqi), "gray")


def aqi_hex(aqi):
    """Hex colour for an AQI value."""
    return CATEGORY_COLORS.get(categorize_aqi(aqi), CATEGORY_COLORS["Unknown"])


def aqi_from_sub_indices(sub_indices):
    """Overall AQI from already-computed sub-indices.

    Returns (aqi, dominant_pollutant). `aqi` is None when CPCB's own reporting
    rule is not met — fewer than three usable pollutants, or no particulate
    among them. Callers must treat None as "no AQI", never as 0.
    """
    usable = {}
    for pollutant, value in (sub_indices or {}).items():
        if pollutant not in BREAKPOINTS:
            continue
        try:
            i = float(value)
        except (TypeError, ValueError):
            continue
        if AQI_MIN <= i <= AQI_MAX:
            usable[pollutant] = round(i)

    if len(usable) < MIN_POLLUTANTS:
        return None, None
    if not any(p in usable for p in PARTICULATES):
        return None, None

    dominant = max(usable, key=lambda p: usable[p])
    return usable[dominant], dominant


def compute_aqi(concentrations):
    """CPCB AQI from {pollutant_id: CONCENTRATION}.

    The forward path, for callers that hold real µg/m³ or mg/m³ figures. Reading
    the CPCB feed does NOT go through here — that feed publishes sub-indices, so
    cpcb_client calls aqi_from_sub_indices directly.

    Returns (aqi, dominant_pollutant, sub_indices).
    """
    sub_indices = {}
    for pollutant, value in (concentrations or {}).items():
        si = sub_index(pollutant, value)
        if si is not None:
            sub_indices[pollutant] = si

    aqi, dominant = aqi_from_sub_indices(sub_indices)
    return aqi, dominant, sub_indices
