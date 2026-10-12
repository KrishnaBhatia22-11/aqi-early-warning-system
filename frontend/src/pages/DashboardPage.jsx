import { useState, useMemo, useEffect, useRef } from "react";
import SparkLine from "../components/SparkLine";
import { aqiCategory } from "../utils/aqiCategory";
import AnomalyBanner from "../components/AnomalyBanner";
import ShareButton from "../components/ShareButton";
import { detectAnomaly, fetchForecast } from "../utils/api";
import { useCityHistory } from "../utils/useCityHistory";
import { formatAsOf } from "../utils/feed";

function TrendChart({ values, color }) {
  const w = 400, h = 120;
  const min = Math.min(...values), max = Math.max(...values);
  const pts = values.map((v, i) => [
    (i / (values.length - 1)) * w,
    h - ((v - min) / (max - min || 1)) * (h - 16) - 8,
  ]);
  const d = pts.map((p, i) => `${i === 0 ? "M" : "L"}${p[0]} ${p[1]}`).join(" ");
  return (
    <svg viewBox={`0 0 ${w} ${h}`} style={{ width: "100%", height: 120 }} preserveAspectRatio="none">
      <defs>
        <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.4" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={`${d} L ${w} ${h} L 0 ${h} Z`} fill="url(#trendFill)" />
      <path d={d} fill="none" stroke={color} strokeWidth="2" style={{ filter: `drop-shadow(0 0 6px ${color})` }} />
      {pts.map((p, i) => (
        <circle key={i} cx={p[0]} cy={p[1]} r={i === pts.length - 1 ? 5 : 2.5} fill={color} opacity={i === pts.length - 1 ? 1 : 0.5} />
      ))}
    </svg>
  );
}

function CalendarHeatmap({ data }) {
  return (
    <div className="cal-grid">
      {data.map(d => {
        const cat = aqiCategory(d.aqi);
        return (
          <div
            key={d.date}
            className="cal-cell"
            style={{ background: cat.color + "55", border: `1px solid ${cat.color}44` }}
            title={`${d.date}: AQI ${d.aqi}`}
          >
            <span className="mono" style={{ fontSize: 8, color: cat.color }}>{d.aqi}</span>
          </div>
        );
      })}
    </div>
  );
}

export default function DashboardPage({ cities, feed, initialCity }) {
  const [selectedCity, setSelectedCity] = useState(initialCity || cities[0]?.name || null);
  const [forecast, setForecast]         = useState(null);   // { items, peak, low } from /forecast, or { error }
  const [anomaly, setAnomaly]           = useState(null);
  const aqiHistoryRef = useRef({});   // { cityName: number[] } — rolling 12-reading buffer
  const dismissedRef  = useRef(null); // key of last dismissed anomaly — prevents re-flash

  // Clear anomaly when city changes
  useEffect(() => {
    setAnomaly(null);
    dismissedRef.current = null;
  }, [selectedCity]);

  // If a deep-linked ?city= isn't a city we have live data for, fall back to default.
  useEffect(() => {
    if (cities.length && (!selectedCity || !cities.some(c => c.name === selectedCity))) {
      setSelectedCity(cities[0].name);
    }
  }, [cities, selectedCity]);

  // Detect anomaly on every cities refresh
  useEffect(() => {
    const cityData = cities?.find(c => c.name === selectedCity);
    if (!cityData?.aqi) return;

    const curr = cityData.aqi;
    const hist = aqiHistoryRef.current[selectedCity] || [];
    // Append only if value changed (API may return cached)
    if (!hist.length || hist[hist.length - 1] !== curr) {
      aqiHistoryRef.current[selectedCity] = [...hist, curr].slice(-12);
    }

    const histForApi = (aqiHistoryRef.current[selectedCity] || []).slice(0, -1);
    detectAnomaly(selectedCity, curr, histForApi).then(result => {
      if (!result) return;
      if (result.is_anomaly) {
        // Don't re-show an anomaly the user already dismissed for this reading
        const key = `${selectedCity}-${result.type}-${Math.round(result.window_mean / 10) * 10}`;
        if (key !== dismissedRef.current) setAnomaly(result);
      } else {
        setAnomaly(null);
        dismissedRef.current = null; // resolved — clear dismiss lock
      }
    });
  }, [cities, selectedCity]);

  const cityData = useMemo(
    () => cities.find(c => c.name === selectedCity) || cities[0] || null,
    [cities, selectedCity],
  );
  const snapshot = cityData?.data_mode === "snapshot";
  const cat = cityData ? aqiCategory(cityData.aqi) : aqiCategory(0);

  // Real stored history only (daily summaries). No history -> no chart.
  const { points: trendPoints } = useCityHistory(cityData?.name, 7);
  const { points: monthPoints } = useCityHistory(cityData?.name, 30);
  const trend = trendPoints.map(p => p.aqi);

  // 24h modelled forecast from the API, anchored to the AQI shown (live or stored).
  const baseAqi = cityData?.aqi ?? null;
  const baseMode = cityData?.data_mode ?? null;
  const baseAsOf = cityData?.as_of ?? null;
  useEffect(() => {
    if (!cityData || !baseAqi) { setForecast(null); return undefined; }
    let cancelled = false;
    setForecast(null);
    fetchForecast(cityData.name, baseAqi, { dataMode: baseMode, asOf: baseAsOf })
      .then(d => { if (!cancelled) setForecast(d); })
      .catch(e => { if (!cancelled) setForecast({ error: e.message }); });
    return () => { cancelled = true; };
  }, [cityData?.name, baseAqi, baseMode, baseAsOf]);
  const forecastValues = forecast?.forecast?.map(f => f.aqi) ?? [];

  const pollutants = cityData ? [
    ["PM2.5", cityData.pm25, "µg/m³"], ["PM10", cityData.pm10, "µg/m³"], ["NO2", cityData.no2, "µg/m³"],
    ["CO", cityData.co, "mg/m³"], ["SO2", cityData.so2, "µg/m³"], ["O3", cityData.o3, "µg/m³"],
    ...(cityData.nh3 != null ? [["NH3", cityData.nh3, "µg/m³"]] : []),
  ] : [];

  const cityNames = cities.map(c => c.name);

  return (
    <div className="dashboard-page">
      <div className="dashboard-hero">
        <div className="mono dashboard-eyebrow">CITY INTELLIGENCE DASHBOARD{snapshot ? ` · STORED READING AS OF ${formatAsOf(cityData.as_of).toUpperCase()}` : ""}</div>
        <h1 className="display dashboard-title">Air Quality Analytics</h1>
        <div style={{ marginTop: 18, display: "flex", justifyContent: "center" }}>
          <ShareButton city={selectedCity} />
        </div>
      </div>

      <AnomalyBanner
        anomaly={anomaly}
        onDismiss={() => {
          if (anomaly) {
            dismissedRef.current = `${selectedCity}-${anomaly.type}-${Math.round(anomaly.window_mean / 10) * 10}`;
          }
          setAnomaly(null);
        }}
      />

      <div className="dash-city-select-wrap">
        {!cityData && (
          <div className="mono feed-stored-note" style={{ textAlign: "center", padding: 12 }}>
            No live or stored city data available.
          </div>
        )}
        <div className="glass dash-city-bar">
          <span className="mono dash-city-label">SELECT CITY</span>
          <div className="dash-city-pills">
            {cityNames.slice(0, 10).map(name => {
              const c = cities.find(x => x.name === name);
              const cc = c?.aqi ? aqiCategory(c.aqi) : { color: "#6b7280" };
              return (
                <button
                  key={name}
                  className={`city-pill ${selectedCity === name ? "active" : ""}`}
                  style={selectedCity === name ? { borderColor: cc.color, color: cc.color } : {}}
                  onClick={() => setSelectedCity(name)}
                >
                  {name}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <div className="dash-grid">
        <div className="dash-card glass-strong dash-trend">
          <div className="panel-header">
            <span className="mono panel-title">7-DAY TREND (STORED) · {(selectedCity ?? "").toUpperCase()}</span>
            <span className="mono panel-meta" style={{ color: cat.color }}>
              {cityData ? `AQI ${cityData.aqi}${snapshot ? " (STORED)" : ""}` : "—"}
            </span>
          </div>
          {trend.length >= 2 ? (
            <>
              <TrendChart values={trend} color={cat.color} />
              <div className="dash-trend-meta mono">
                {trendPoints.map(p => <span key={p.date}>{p.date.slice(5)}</span>)}
              </div>
            </>
          ) : (
            <div className="mono feed-stored-note" style={{ padding: 16 }}>No stored history for this city yet.</div>
          )}
        </div>

        <div className="dash-card glass-strong dash-donut">
          <div className="panel-header">
            <span className="mono panel-title">POLLUTANT CONCENTRATIONS</span>
            <span className="mono panel-meta">{snapshot ? "STORED" : "CPCB"}</span>
          </div>
          {pollutants.length ? (
            <div className="donut-legend">
              {pollutants.map(([name, value, unit]) => (
                <div className="donut-leg-item" key={name}>
                  <span className="mono donut-leg-name">{name}</span>
                  <span className="mono donut-leg-pct">{Number.isFinite(value) ? `${value} ${unit}` : "—"}</span>
                </div>
              ))}
              {cityData?.dominant_pollutant && (
                <div className="mono feed-stored-note">Dominant pollutant: {cityData.dominant_pollutant}</div>
              )}
            </div>
          ) : (
            <div className="mono feed-stored-note" style={{ padding: 16 }}>No pollutant data.</div>
          )}
        </div>

        <div className="dash-card glass-strong dash-calendar">
          <div className="panel-header">
            <span className="mono panel-title">DAILY AQI · LAST 30 DAYS (STORED)</span>
          </div>
          {monthPoints.length ? (
            <CalendarHeatmap data={monthPoints} />
          ) : (
            <div className="mono feed-stored-note" style={{ padding: 16 }}>No stored history for this city yet.</div>
          )}
        </div>

        <div className="dash-card glass-strong dash-forecast">
          <div className="panel-header">
            <span className="mono panel-title">24H MODELLED FORECAST</span>
            <span className="mono panel-meta">DIURNAL MODEL{snapshot ? " · ANCHORED TO STORED READING" : ""}</span>
          </div>
          {forecastValues.length >= 2 ? (
            <>
              <TrendChart values={forecastValues} color="#FFB300" />
              <div className="mono dash-forecast-badge">
                PEAK: <span style={{ color: "#ef3a4d" }}>{forecast.peak.aqi}</span>
                &nbsp;&nbsp;LOW: <span style={{ color: "#34d27a" }}>{forecast.low.aqi}</span>
              </div>
            </>
          ) : (
            <div className="mono feed-stored-note" style={{ padding: 16 }}>
              {forecast?.error ?? (cityData ? "Loading…" : "Forecast needs a current or stored reading.")}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
