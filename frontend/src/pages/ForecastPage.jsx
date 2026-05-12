import { useState, useEffect, useRef } from "react";
import ForecastChart from "../components/ForecastChart";
import { fetchForecast, detectAnomaly } from "../utils/api";
import { aqiCategory } from "../utils/aqiCategory";
import AnomalyBanner from "../components/AnomalyBanner";

const FORECAST_CITIES = [
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

export default function ForecastPage({ cities }) {
  const [city, setCity]         = useState("Delhi");
  const [data, setData]         = useState(null);
  const [loading, setLoading]   = useState(false);
  const [slowLoad, setSlowLoad] = useState(false);
  const [error, setError]       = useState(null);

  const [anomaly, setAnomaly]     = useState(null);
  const aqiHistoryRef = useRef({});
  const dismissedRef  = useRef(null);

  // Keep a ref to the latest cities so we read it at fetch-time
  // without re-triggering the forecast effect on every cities poll
  const citiesRef = useRef(cities);
  useEffect(() => { citiesRef.current = cities; }, [cities]);

  // Reset anomaly when selected city changes
  useEffect(() => {
    setAnomaly(null);
    dismissedRef.current = null;
  }, [city]);

  // Detect anomaly on every cities refresh
  useEffect(() => {
    const cityData = cities?.find(c => c.name === city);
    if (!cityData?.aqi) return;

    const curr = cityData.aqi;
    const hist = aqiHistoryRef.current[city] || [];
    if (!hist.length || hist[hist.length - 1] !== curr) {
      aqiHistoryRef.current[city] = [...hist, curr].slice(-12);
    }

    const histForApi = (aqiHistoryRef.current[city] || []).slice(0, -1);
    detectAnomaly(city, curr, histForApi).then(result => {
      if (!result) return;
      if (result.is_anomaly) {
        const key = `${city}-${result.type}-${Math.round(result.window_mean / 10) * 10}`;
        if (key !== dismissedRef.current) setAnomaly(result);
      } else {
        setAnomaly(null);
        dismissedRef.current = null;
      }
    });
  }, [cities, city]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    setData(null);
    setError(null);
    setLoading(true);
    setSlowLoad(false);

    const liveCity = citiesRef.current?.find(x => x.name === city);
    const baseAqi  = liveCity?.aqi ?? null;

    const slowTimer = setTimeout(() => setSlowLoad(true), 3500);

    fetchForecast(city, baseAqi)
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => { setLoading(false); clearTimeout(slowTimer); });

    return () => clearTimeout(slowTimer);
  }, [city]); // eslint-disable-line react-hooks/exhaustive-deps

  const downloadCSV = () => {
    if (!data) return;
    const rows = [
      "Hour,Date,AQI,Upper,Lower,Category,Confidence%",
      ...data.forecast.map(f =>
        `${f.hour},${f.date_label},${f.aqi},${f.upper},${f.lower},${f.category},${f.confidence ?? ""}`
      ),
    ];
    const blob = new Blob([rows.join("\n")], { type: "text/csv" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = `aqi-forecast-${city}-${new Date().toISOString().split("T")[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="forecast-page">
      {/* ── Hero */}
      <div className="forecast-hero">
        <div className="mono forecast-eyebrow">DIURNAL AI MODEL · 24-HOUR FORECAST · UPDATED HOURLY</div>
        <h1 className="display forecast-title">AQI Forecast</h1>
        <p className="forecast-sub">
          Physics-informed model anchored to live WAQI data.
          Peaks at morning rush (07–09) and evening (17–19).
        </p>
      </div>

      {/* ── City selector */}
      <div className="forecast-city-bar glass-strong">
        <span className="mono" style={{ color: "var(--orange)", fontSize: 11, letterSpacing: "0.15em", flexShrink: 0 }}>
          SELECT CITY
        </span>
        <div className="forecast-city-pills">
          {FORECAST_CITIES.map(c => {
            const liveCity = cities?.find(x => x.name === c);
            const cat      = liveCity ? aqiCategory(liveCity.aqi) : null;
            return (
              <button
                key={c}
                className={`city-pill ${city === c ? "active" : ""}`}
                style={city === c && cat ? { borderColor: cat.color, color: cat.color } : {}}
                onClick={() => setCity(c)}
              >
                {c}
                {liveCity && (
                  <span className="mono" style={{ marginLeft: 4, color: cat.color, fontSize: 9 }}>
                    {liveCity.aqi}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      <AnomalyBanner
        anomaly={anomaly}
        onDismiss={() => {
          if (anomaly) {
            dismissedRef.current = `${city}-${anomaly.type}-${Math.round(anomaly.window_mean / 10) * 10}`;
          }
          setAnomaly(null);
        }}
      />

      {/* ── Chart */}
      <div className="forecast-chart-wrap">
        <ForecastChart
          forecastData={data}
          loading={loading}
          slowLoad={slowLoad}
          error={error}
          cityName={city}
        />
      </div>

      {/* ── 24h summary strip */}
      {data && (
        <div className="forecast-summary-strip glass-strong">
          <div className="fss-item">
            <span className="mono fss-label">MEAN AQI</span>
            <span className="mono fss-val" style={{ color: aqiCategory(data.mean_aqi).color }}>
              {data.mean_aqi}
            </span>
          </div>
          <div className="fss-sep" />
          <div className="fss-item">
            <span className="mono fss-label">PEAK AT</span>
            <span className="mono fss-val" style={{ color: "#ef3a4d" }}>{data.peak.hour}</span>
          </div>
          <div className="fss-sep" />
          <div className="fss-item">
            <span className="mono fss-label">CLEANEST AT</span>
            <span className="mono fss-val" style={{ color: "#34d27a" }}>{data.low.hour}</span>
          </div>
          <div className="fss-sep" />
          <div className="fss-item">
            <span className="mono fss-label">TREND</span>
            <span
              className="mono fss-val"
              style={{
                color: data.trend === "RISING" ? "#ef3a4d"
                     : data.trend === "FALLING" ? "#34d27a" : "#FFB300",
              }}
            >
              {data.trend === "RISING" ? "↑" : data.trend === "FALLING" ? "↓" : "→"} {data.trend}
            </span>
          </div>
          <div className="fss-sep" />
          <div className="fss-item">
            <span className="mono fss-label">DATA SOURCE</span>
            <span className={`mono fss-source ${data.base_aqi_source === "live_waqi" ? "live" : "est"}`}>
              {data.base_aqi_source === "live_waqi" ? "● LIVE WAQI" : "◎ SEASONAL EST."}
            </span>
          </div>
        </div>
      )}

      {/* ── 24h breakdown table */}
      {data && (
        <div className="forecast-table-wrap glass-strong">
          <div className="panel-header" style={{ marginBottom: 16 }}>
            <span className="mono panel-title">24-HOUR BREAKDOWN · {city.toUpperCase()}</span>
            <button
              className="btn-ghost"
              style={{ fontSize: 10, padding: "5px 12px" }}
              onClick={downloadCSV}
            >
              ↓ DOWNLOAD CSV
            </button>
          </div>
          <div className="forecast-table-scroll">
            <table className="forecast-table">
              <thead>
                <tr>
                  <th className="mono">HOUR</th>
                  <th className="mono">AQI</th>
                  <th className="mono">UPPER</th>
                  <th className="mono">LOWER</th>
                  <th className="mono">CATEGORY</th>
                  <th className="mono">CONF.</th>
                </tr>
              </thead>
              <tbody>
                {data.forecast.map((row, i) => {
                  const cat = aqiCategory(row.aqi);
                  return (
                    <tr key={row.hour} className={i % 2 === 0 ? "row-even" : ""}>
                      <td className="mono">{row.hour}</td>
                      <td className="mono" style={{ color: cat.color, fontWeight: 700 }}>{row.aqi}</td>
                      <td className="mono" style={{ color: "rgba(255,255,255,0.4)" }}>{row.upper}</td>
                      <td className="mono" style={{ color: "rgba(255,255,255,0.4)" }}>{row.lower}</td>
                      <td>
                        <span className={`badge ${cat.klass}`} style={{ fontSize: 10 }}>{cat.name}</span>
                      </td>
                      <td className="mono" style={{ color: "rgba(255,255,255,0.4)" }}>
                        {row.confidence ?? "—"}%
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
