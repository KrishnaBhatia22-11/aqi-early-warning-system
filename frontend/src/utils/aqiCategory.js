// India CPCB National AQI — the single source of truth for category names,
// colours and badge classes across the app.
//
// These are the official CPCB bands, not the US EPA ones the app used to show.
// The backend computes every AQI with the same bands (src/data/india_aqi.py), so
// a number and its label can never disagree. Two changes from the old table:
// 301–400 is "Very Poor" (it used to say "Severe") and 401–500 is "Severe" (it
// used to say "Hazardous") — CPCB has no "Hazardous" band at all.
export const AQI_STANDARD_LABEL = "India CPCB AQI";

export const AQI_BANDS = [
  { max: 50,  name: "Good",         klass: "good",         color: "#34d27a", range: "0–50" },
  { max: 100, name: "Satisfactory", klass: "satisfactory", color: "#a3d13a", range: "51–100" },
  { max: 200, name: "Moderate",     klass: "moderate",     color: "#f5d142", range: "101–200" },
  { max: 300, name: "Poor",         klass: "poor",         color: "#FF6B00", range: "201–300" },
  { max: 400, name: "Very Poor",    klass: "very-poor",    color: "#ef3a4d", range: "301–400" },
  { max: Infinity, name: "Severe",  klass: "severe",       color: "#7e0023", range: "401–500" },
];

export function aqiCategory(aqi) {
  const band = AQI_BANDS.find((b) => aqi <= b.max) ?? AQI_BANDS[AQI_BANDS.length - 1];
  const { name, klass, color } = band;
  return { name, klass, color };
}

// Category name → colour, for the places that already hold a label from the API
// rather than a number.
export const CAT_COLORS = Object.fromEntries(
  AQI_BANDS.map((b) => [b.name, b.color])
);

export function catColor(name) {
  return CAT_COLORS[name] ?? "#FF6B00";
}
