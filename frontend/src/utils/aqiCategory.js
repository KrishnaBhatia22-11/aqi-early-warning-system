export function aqiCategory(aqi) {
  if (aqi <= 50)  return { name: "Good",         klass: "good",         color: "#34d27a" };
  if (aqi <= 100) return { name: "Satisfactory", klass: "satisfactory", color: "#f5d142" };
  if (aqi <= 200) return { name: "Moderate",     klass: "moderate",     color: "#FFB300" };
  if (aqi <= 300) return { name: "Poor",         klass: "poor",         color: "#FF6B00" };
  if (aqi <= 400) return { name: "Severe",       klass: "severe",       color: "#ef3a4d" };
  return            { name: "Hazardous",    klass: "hazardous",    color: "#c2002a" };
}
