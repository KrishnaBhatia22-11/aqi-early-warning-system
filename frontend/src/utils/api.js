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
  if (!res.ok) {
    let detail = "";
    try { detail = (await res.json()).detail ?? ""; } catch {}
    throw new Error(`Prediction failed (${res.status})${detail ? ": " + detail : ""}`);
  }

  const data = await res.json();

  // API returns predicted_aqi / top_factors — throw if missing so caller uses local estimate
  if (data.predicted_aqi == null && data.aqi == null) {
    throw new Error("API returned unexpected response: " + JSON.stringify(data).slice(0, 120));
  }

  const aqi = data.predicted_aqi ?? data.aqi;
  const category = data.aqi_category ?? data.category ?? "Unknown";

  // top_factors[].impact is the SHAP contribution (positive = raises AQI, negative = lowers)
  const shapValues = (data.top_factors ?? []).map(f => ({
    feature: f.feature,
    value: f.impact ?? f.value ?? 0,
  }));

  return { aqi: Math.round(aqi), category, shap_values: shapValues };
}

export async function chatWithAI(message, cities = [], history = []) {
  const res = await fetch(`${BASE}/api/v1/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      cities: cities.map(c => ({ name: c.name, aqi: c.aqi, pollutant: c.pollutant ?? null })),
      history,
    }),
  });
  if (!res.ok) throw new Error("Chat API failed");
  return res.json();
}

export async function fetchModels() {
  const res = await fetch(`${BASE}/api/v1/models/comparison`);
  if (!res.ok) throw new Error("Models API unavailable");
  return res.json();
}

export async function detectAnomaly(city, currentAqi, aqiHistory = []) {
  try {
    const res = await fetch(`${BASE}/api/v1/anomaly/detect`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ city, current_aqi: currentAqi, aqi_history: aqiHistory }),
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function calculateHealthImpact(payload) {
  const res = await fetch(`${BASE}/api/v1/health/impact`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Health API failed");
  return res.json();
}

export async function fetchCompare(city1, city2) {
  const res = await fetch(
    `${BASE}/api/v1/compare?city1=${encodeURIComponent(city1)}&city2=${encodeURIComponent(city2)}`
  );
  if (!res.ok) throw new Error("Compare API failed");
  return res.json();
}

export async function fetchWeather(city) {
  const res = await fetch(`${BASE}/api/v1/weather/${encodeURIComponent(city)}`);
  if (!res.ok) {
    let detail = "Weather data unavailable";
    try { detail = (await res.json()).detail ?? detail; } catch {}
    throw new Error(detail);
  }
  return res.json();
}

export async function fetchHistory(city) {
  const res = await fetch(`${BASE}/api/v1/history/${encodeURIComponent(city)}`);
  if (!res.ok) {
    let detail = "Failed to fetch history";
    try { detail = (await res.json()).detail ?? detail; } catch {}
    throw new Error(detail);
  }
  return res.json();
}

export async function fetchForecast(city, baseAqi = null) {
  const body = { city };
  if (baseAqi !== null && baseAqi > 0) body.base_aqi = baseAqi;
  const res = await fetch(`${BASE}/api/v1/forecast`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = city + " forecast unavailable";
    try { detail = (await res.json()).detail ?? detail; } catch {}
    throw new Error(detail);
  }
  return res.json();
}
