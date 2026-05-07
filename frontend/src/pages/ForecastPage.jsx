import { useState, useEffect } from "react";
import ForecastChart from "../components/ForecastChart";
import { fetchForecast } from "../utils/api";
import { aqiCategory } from "../utils/aqiCategory";

const FORECAST_CITIES = [
  "Delhi", "Mumbai", "Bengaluru", "Chennai", "Kolkata",
  "Hyderabad", "Ahmedabad", "Jaipur", "Lucknow", "Patna",
  "Chandigarh", "Amritsar", "Guwahati", "Thiruvananthapuram",
  "Visakhapatnam", "Coimbatore", "Kochi", "Bhopal",
];

function trendArrow(prev, curr) {
  if (curr > prev + 5)  return { arrow: "↑", color: "#ef3a4d" };
  if (curr < prev - 5)  return { arrow: "↓", color: "#34d27a" };
  return { arrow: "→", color: "#FFB300" };
}

export default function ForecastPage({ cities }) {
  const [city, setCity]         = useState("Delhi");
  const [data, setData]         = useState(null);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState(null);

  useEffect(() => {
    setData(null);
    setError(null);
    setLoading(true);
    fetchForecast(city)
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [city]);

  const downloadCSV = () => {
    if (!data) return;
    const rows = [
      "Hour,AQI,Upper Bound,Lower Bound,Category",
      ...data.forecast.map(f => `${f.hour},${f.aqi},${f.upper},${f.lower},${f.category}`),
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
      <div className="forecast-hero">
        <div className="mono forecast-eyebrow">PROPHET AI · 24-HOUR FORECAST · UPDATED HOURLY</div>
        <h1 className="display forecast-title">AQI Forecast</h1>
        <p className="forecast-sub">
          Machine-learning time-series forecast for the next 24 hours with confidence intervals.
        </p>
      </div>

      {/* City selector */}
      <div className="forecast-city-bar glass-strong">
        <span className="mono" style={{ color: "var(--orange)", fontSize: 11, letterSpacing: "0.15em", flexShrink: 0 }}>SELECT CITY</span>
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
                  <span className="mono" style={{ marginLeft: 4, color: cat.color, fontSize: 9 }}>{liveCity.aqi}</span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Chart */}
      <div className="forecast-chart-wrap">
        <ForecastChart forecastData={data} loading={loading} error={error} cityName={city} />
      </div>

      {/* 24h table */}
      {data && (
        <div className="forecast-table-wrap glass-strong">
          <div className="panel-header" style={{ marginBottom: 16 }}>
            <span className="mono panel-title">24-HOUR BREAKDOWN · {city.toUpperCase()}</span>
            <button className="btn-ghost" style={{ fontSize: 10, padding: "5px 12px" }} onClick={downloadCSV}>
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
                  <th className="mono">TREND</th>
                </tr>
              </thead>
              <tbody>
                {data.forecast.map((row, i) => {
                  const cat = aqiCategory(row.aqi);
                  const tr  = i > 0 ? trendArrow(data.forecast[i - 1].aqi, row.aqi) : null;
                  return (
                    <tr key={row.hour} className={i % 2 === 0 ? "row-even" : ""}>
                      <td className="mono">{row.hour}</td>
                      <td className="mono" style={{ color: cat.color, fontWeight: 700 }}>{row.aqi}</td>
                      <td className="mono" style={{ color: "rgba(255,255,255,0.4)" }}>{row.upper}</td>
                      <td className="mono" style={{ color: "rgba(255,255,255,0.4)" }}>{row.lower}</td>
                      <td><span className={`badge ${cat.klass}`} style={{ fontSize: 10 }}>{cat.name}</span></td>
                      <td className="mono" style={{ color: tr?.color ?? "transparent", fontSize: 16 }}>{tr?.arrow ?? ""}</td>
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
