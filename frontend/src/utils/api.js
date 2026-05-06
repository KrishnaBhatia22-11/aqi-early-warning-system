const BASE = "https://aqi-api-y2qs.onrender.com";

export async function fetchHealth() {
  const res = await fetch(`${BASE}/health`);
  if (!res.ok) throw new Error("API offline");
  return res.json();
}

export async function fetchCities() {
  const res = await fetch(`${BASE}/api/v1/cities`);
  if (!res.ok) throw new Error("Failed to fetch cities");
  const data = await res.json();
  // API returns { success, count, cities: [...] }
  return Array.isArray(data) ? data : (data.cities ?? []);
}

export async function predictAQI(values) {
  const now = new Date();
  const month = now.getMonth() + 1;
  const year = now.getFullYear();
  // Season_Code: 0=Winter(Dec-Feb), 1=Spring(Mar-May), 2=Summer(Jun-Aug), 3=Autumn(Sep-Nov)
  const seasonCode = month <= 2 || month === 12 ? 0 : month <= 5 ? 1 : month <= 8 ? 2 : 3;

  const body = {
    "PM2.5":      Number(values["PM2.5"]),
    PM10:         Number(values.PM10),
    NO:           Number(values.NO),
    NO2:          Number(values.NO2),
    NOx:          Number(values.NOx),
    NH3:          Number(values.NH3),
    CO:           Number(values.CO),
    SO2:          Number(values.SO2),
    O3:           Number(values.O3),
    Month:        month,
    Year:         year,
    Season_Code:  seasonCode,
  };

  const res = await fetch(`${BASE}/api/v1/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error("Prediction failed");
  const data = await res.json();

  // Normalize: API returns predicted_aqi / top_factors, frontend expects aqi / shap_values
  const aqi = data.predicted_aqi ?? data.aqi ?? 0;
  const category = data.aqi_category ?? data.category ?? "Unknown";
  const shapValues = (data.top_factors ?? []).map(f => ({
    feature: f.feature,
    value: f.impact ?? f.value ?? 0,
  }));

  return { aqi: Math.round(aqi), category, shap_values: shapValues };
}
