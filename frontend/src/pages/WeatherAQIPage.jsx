import { useState, useCallback, useEffect, useRef } from "react";
import { fetchWeather, fetchCities } from "../utils/api";

// ── Dark city dropdown (reuses cmp-dd-* CSS) ──────────────────────────────────

function CityDropdown({ value, onChange, cities }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    if (!open) return;
    const onDown = e => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    const onKey  = e => { if (e.key === "Escape") setOpen(false); };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown",   onKey);
    return () => { document.removeEventListener("mousedown", onDown); document.removeEventListener("keydown", onKey); };
  }, [open]);

  return (
    <div className="cmp-dd-wrap wx-dd-wrap" ref={ref}>
      <button
        type="button"
        className={`cmp-dd-trigger${open ? " open" : ""}`}
        onClick={() => setOpen(v => !v)}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <span className="cmp-dd-value">{value}</span>
        <span className="cmp-dd-arrow" aria-hidden="true">▾</span>
      </button>
      {open && (
        <div className="cmp-dd-panel" role="listbox">
          {cities.map(c => (
            <button
              key={c} type="button" role="option" aria-selected={c === value}
              className={`cmp-dd-option${c === value ? " selected" : ""}`}
              onClick={() => { onChange(c); setOpen(false); }}
            >
              <span>{c}</span>
              {c === value && <span className="cmp-dd-check" aria-hidden="true">✓</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Constants ─────────────────────────────────────────────────────────────────

const CITIES = [
  "Delhi", "Mumbai", "Bengaluru", "Chennai", "Kolkata", "Hyderabad",
  "Ahmedabad", "Pune", "Jaipur", "Lucknow", "Kanpur", "Patna",
  "Bhopal", "Nagpur", "Surat", "Indore", "Visakhapatnam", "Chandigarh",
  "Coimbatore", "Kochi", "Agra", "Varanasi", "Amritsar", "Jodhpur",
  "Udaipur", "Mysuru", "Pondicherry", "Ghaziabad", "Noida", "Faridabad",
  "Gurugram", "Meerut", "Moradabad", "Ludhiana", "Jalandhar",
  "Bhubaneswar", "Guwahati", "Ranchi", "Raipur", "Dehradun", "Shimla",
  "Jammu", "Srinagar", "Thiruvananthapuram", "Madurai", "Vijayawada",
  "Nashik", "Aurangabad", "Kolhapur", "Solapur", "Warangal", "Guntur",
  "Tiruchirappalli",
];

const CONDITION_ICON = {
  Clear: "☀️", "Partly Cloudy": "⛅", Cloudy: "☁️",
  Rain: "🌧", Drizzle: "🌦", Thunderstorm: "⛈", Haze: "🌫", Snow: "❄️",
};

// ── Helpers ───────────────────────────────────────────────────────────────────

function aqiColor(aqi) {
  if (!aqi) return "#94a3b8";
  if (aqi <= 50)  return "#22c55e";
  if (aqi <= 100) return "#a3e635";
  if (aqi <= 200) return "#eab308";
  if (aqi <= 300) return "#f97316";
  if (aqi <= 400) return "#ef4444";
  return "#a855f7";
}

function aqiCategory(aqi) {
  if (!aqi) return "—";
  if (aqi <= 50)  return "Good";
  if (aqi <= 100) return "Satisfactory";
  if (aqi <= 200) return "Moderate";
  if (aqi <= 300) return "Poor";
  if (aqi <= 400) return "Very Poor";
  return "Severe";
}

function insightType(text) {
  if (!text) return "stable";
  const t = text.toLowerCase();
  if (t.includes("washing") || t.includes("dispersing")) return "improving";
  if (t.includes("trapping") || t.includes("elevated") || t.includes("ozone")) return "worsening";
  return "stable";
}

function findCityAqi(cities, name) {
  if (!cities || !name) return null;
  const lower = name.toLowerCase();
  return cities.find(c => {
    const cn = (c.name ?? "").toLowerCase();
    return cn === lower
      || (lower === "bangalore" && cn === "bengaluru")
      || (lower === "bengaluru" && cn === "bangalore");
  }) ?? null;
}

// impact: { level, polarity }
// polarity: "worsening" | "improving" | "neutral"
function tempImpact(t) {
  if (t > 38) return { level: "HIGH",     polarity: "worsening" };
  if (t > 28) return { level: "MODERATE", polarity: "worsening" };
  return          { level: "LOW",      polarity: "neutral"   };
}
function humidityImpact(h) {
  if (h > 80) return { level: "HIGH",     polarity: "worsening" };
  if (h > 60) return { level: "MODERATE", polarity: "worsening" };
  return          { level: "LOW",      polarity: "neutral"   };
}
function windImpact(w) {
  if (w > 20) return { level: "HIGH",     polarity: "improving" };
  if (w > 10) return { level: "MODERATE", polarity: "improving" };
  return          { level: "LOW",      polarity: "worsening" };
}
function rainfallImpact(r) {
  if (r > 0) return { level: "HIGH", polarity: "improving" };
  return         { level: "NONE", polarity: "neutral"   };
}

const IMPACT_COLOR = { worsening: "#ef4444", improving: "#22c55e", neutral: "#94a3b8" };

// ── Sub-components ────────────────────────────────────────────────────────────

function ImpactBadge({ level, polarity }) {
  return (
    <span className="wx-impact-badge" style={{ color: IMPACT_COLOR[polarity], borderColor: IMPACT_COLOR[polarity] + "40" }}>
      {level}
    </span>
  );
}

function CorrCard({ icon, title, value, desc, impact }) {
  return (
    <div className="wx-corr-card glass">
      <div className="wx-corr-head">
        <span className="wx-corr-icon">{icon}</span>
        <span className="wx-corr-title mono">{title}</span>
        <ImpactBadge level={impact.level} polarity={impact.polarity} />
      </div>
      <div className="wx-corr-value" style={{ color: IMPACT_COLOR[impact.polarity] }}>{value}</div>
      <p className="wx-corr-desc">{desc}</p>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function WeatherAQIPage() {
  const [city, setCity]       = useState("Delhi");
  const [weather, setWeather] = useState(null);
  const [cityAqi, setCityAqi] = useState(null);
  const [loading, setLoading] = useState(false);
  const [weatherErr, setWeatherErr] = useState(null);
  const [aqiErr, setAqiErr]   = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setWeatherErr(null);
    setAqiErr(null);
    setWeather(null);
    setCityAqi(null);

    const [wRes, cRes] = await Promise.allSettled([
      fetchWeather(city),
      fetchCities(),
    ]);

    if (wRes.status === "fulfilled") setWeather(wRes.value);
    else setWeatherErr(wRes.reason?.message ?? "Weather data unavailable");

    if (cRes.status === "fulfilled") setCityAqi(findCityAqi(cRes.value, city));
    else setAqiErr("AQI data temporarily unavailable");

    setLoading(false);
  }, [city]);

  const hasData    = !loading && (weather || cityAqi);
  const iType      = weather ? insightType(weather.aqi_insight) : "stable";
  const condIcon   = weather ? (CONDITION_ICON[weather.condition] ?? "🌤") : "🌤";

  return (
    <div className="page wx-page">

      {/* Header */}
      <div className="wx-header">
        <div className="mono wx-eyebrow">WEATHER · AQI CORRELATION</div>
        <h1 className="wx-title">How weather affects your air</h1>
        <p className="wx-sub">Real-time weather conditions and their impact on air quality</p>
      </div>

      {/* Controls */}
      <div className="wx-controls">
        <CityDropdown
          value={city}
          onChange={c => { setCity(c); setWeather(null); setCityAqi(null); setWeatherErr(null); setAqiErr(null); }}
          cities={CITIES}
        />
        <button className="wx-load-btn" onClick={load} disabled={loading}>
          {loading ? "Loading…" : "Load Data"}
        </button>
      </div>

      {/* Errors */}
      {(weatherErr || aqiErr) && !loading && (
        <div className="wx-error-row">
          {weatherErr && <div className="wx-error">⚠ {weatherErr}</div>}
          {aqiErr     && <div className="wx-error">⚠ {aqiErr}</div>}
        </div>
      )}

      {/* Loading skeleton */}
      {loading && (
        <div className="wx-skeleton-wrap">
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
            <div className="skeleton" style={{ height: 200, borderRadius: 14 }} />
            <div className="skeleton" style={{ height: 200, borderRadius: 14 }} />
          </div>
          <div className="skeleton" style={{ height: 72, borderRadius: 12, marginBottom: 16 }} />
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <div className="skeleton" style={{ height: 160, borderRadius: 12 }} />
            <div className="skeleton" style={{ height: 160, borderRadius: 12 }} />
            <div className="skeleton" style={{ height: 160, borderRadius: 12 }} />
            <div className="skeleton" style={{ height: 160, borderRadius: 12 }} />
          </div>
        </div>
      )}

      {/* Results */}
      {hasData && (
        <>
          {/* Section 2 — Conditions strip */}
          <div className="wx-cards-row">

            {/* Weather card */}
            {weather ? (
              <div className="wx-card glass">
                <div className="wx-card-top">
                  <div>
                    <div className="wx-city-name">{weather.city}</div>
                    <div className="wx-condition">{condIcon} {weather.condition}</div>
                  </div>
                  <span className="wx-source-badge">● OpenWeatherMap</span>
                </div>
                <div className="wx-temp-big">{weather.temperature}°C</div>
                <div className="wx-feels">Feels like {weather.feels_like}°C</div>
                <div className="wx-metrics-grid">
                  <div className="wx-metric">
                    <span className="wx-metric-icon">💨</span>
                    <div>
                      <div className="wx-metric-val">{weather.wind_speed} km/h {weather.wind_direction}</div>
                      <div className="wx-metric-lbl mono">Wind</div>
                    </div>
                  </div>
                  <div className="wx-metric">
                    <span className="wx-metric-icon">💧</span>
                    <div>
                      <div className="wx-metric-val">{weather.humidity}%</div>
                      <div className="wx-metric-lbl mono">Humidity</div>
                    </div>
                  </div>
                  <div className="wx-metric">
                    <span className="wx-metric-icon">🌧</span>
                    <div>
                      <div className="wx-metric-val">{weather.rainfall_1h} mm</div>
                      <div className="wx-metric-lbl mono">Rainfall (1h)</div>
                    </div>
                  </div>
                  <div className="wx-metric">
                    <span className="wx-metric-icon">👁</span>
                    <div>
                      <div className="wx-metric-val">{weather.condition}</div>
                      <div className="wx-metric-lbl mono">Condition</div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="wx-card wx-card-unavail glass">
                <div className="wx-unavail-msg">⚠ Weather data temporarily unavailable</div>
              </div>
            )}

            {/* AQI card */}
            {cityAqi ? (
              <div className="wx-card glass">
                <div className="wx-card-top">
                  <div>
                    <div className="wx-city-name">{cityAqi.name}</div>
                    <div className="wx-condition">Current Air Quality</div>
                  </div>
                  <span className="wx-source-badge">● WAQI Live</span>
                </div>
                <div className="wx-aqi-big" style={{ color: aqiColor(cityAqi.aqi) }}>
                  {cityAqi.aqi}
                </div>
                <div className="wx-cat-badge" style={{ color: aqiColor(cityAqi.aqi), borderColor: aqiColor(cityAqi.aqi) + "40" }}>
                  {aqiCategory(cityAqi.aqi)}
                </div>
                {cityAqi.pollutant && (
                  <div className="wx-pollutant mono">Dominant: {cityAqi.pollutant}</div>
                )}
              </div>
            ) : (
              <div className="wx-card wx-card-unavail glass">
                <div className="wx-unavail-msg">⚠ AQI data temporarily unavailable</div>
              </div>
            )}
          </div>

          {/* Section 3 — Insight banner */}
          {weather?.aqi_insight && (
            <div className={`wx-insight-banner wx-insight-${iType}`}>
              <span className="wx-insight-icon">
                {iType === "improving" ? "✅" : iType === "worsening" ? "⚠️" : "ℹ️"}
              </span>
              <div className="wx-insight-body">
                <div className="wx-insight-text">{weather.aqi_insight}</div>
                <div className="wx-insight-sub mono">
                  {iType === "improving" && "Air quality expected to improve"}
                  {iType === "worsening" && "Air quality may worsen — take precautions"}
                  {iType === "stable"    && "Conditions stable — no rapid change expected"}
                </div>
              </div>
            </div>
          )}

          {/* Section 4 — Correlation cards (only if weather data available) */}
          {weather && (
            <>
              <div className="wx-section-head">
                <span className="mono wx-eyebrow">WEATHER–AQI CORRELATION</span>
              </div>
              <div className="wx-corr-grid">
                <CorrCard
                  icon="🌡"
                  title="TEMPERATURE"
                  value={`${weather.temperature}°C`}
                  desc="Higher temperatures accelerate chemical reactions that form ground-level ozone (O3). Delhi summers above 40°C see O3 spike 30–40%."
                  impact={tempImpact(weather.temperature)}
                />
                <CorrCard
                  icon="💧"
                  title="HUMIDITY"
                  value={`${weather.humidity}%`}
                  desc="High humidity (>80%) causes PM2.5 particles to absorb water and grow larger, scattering more light and intensifying haze."
                  impact={humidityImpact(weather.humidity)}
                />
                <CorrCard
                  icon="💨"
                  title="WIND SPEED"
                  value={`${weather.wind_speed} km/h`}
                  desc="Wind above 20 km/h disperses pollutants horizontally. Calm conditions allow pollution to accumulate near ground level."
                  impact={windImpact(weather.wind_speed)}
                />
                <CorrCard
                  icon="🌧"
                  title="RAINFALL"
                  value={`${weather.rainfall_1h} mm`}
                  desc="Rain physically washes PM2.5 and PM10 from the atmosphere. Even 1 mm of rain reduces particulate matter by 20–40%."
                  impact={rainfallImpact(weather.rainfall_1h)}
                />
              </div>
            </>
          )}
        </>
      )}

      {/* Empty state */}
      {!loading && !hasData && !weatherErr && !aqiErr && (
        <div className="wx-empty">
          <div style={{ fontSize: 52, marginBottom: 12 }}>🌤</div>
          <div style={{ fontSize: 16, color: "rgba(255,255,255,0.6)", marginBottom: 6 }}>
            Select a city and click Load Data
          </div>
          <div style={{ fontSize: 13, color: "rgba(255,255,255,0.3)" }}>
            Weather + AQI fetched in parallel from OpenWeatherMap and WAQI
          </div>
        </div>
      )}

      {/* Section 5 — Source footer */}
      <div className="wx-source-footer">
        <span>Weather: <strong>OpenWeatherMap</strong> · updated every 10 min</span>
        <span className="wx-sep">·</span>
        <span>AQI: <strong>WAQI — World Air Quality Index</strong> · updated every hour</span>
        <span className="wx-sep">·</span>
        <span>Correlation insights based on atmospheric science research</span>
      </div>

    </div>
  );
}
