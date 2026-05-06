const BASE = "https://aqi-api-y2qs.onrender.com";

export async function fetchHealth() {
  const res = await fetch(`${BASE}/health`);
  if (!res.ok) throw new Error("API offline");
  return res.json();
}

export async function fetchCities() {
  const res = await fetch(`${BASE}/cities`);
  if (!res.ok) throw new Error("Failed to fetch cities");
  return res.json();
}

export async function predictAQI(values) {
  const res = await fetch(`${BASE}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(values),
  });
  if (!res.ok) throw new Error("Prediction failed");
  return res.json();
}
