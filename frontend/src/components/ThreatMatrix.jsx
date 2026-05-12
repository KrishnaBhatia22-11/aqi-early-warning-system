import { aqiCategory } from "../utils/aqiCategory";

export default function ThreatMatrix({ cities, onCitySelect }) {
  const withData    = cities.filter(c => c.data_available !== false && c.aqi != null);
  const withoutData = cities.filter(c => c.data_available === false || c.aqi == null);

  // Sort: descending AQI, no-data cities at bottom
  const sorted = [
    ...[...withData].sort((a, b) => b.aqi - a.aqi),
    ...withoutData,
  ];

  const max = withData.length ? Math.max(...withData.map(c => c.aqi)) : 500;

  return (
    <div className="threat-panel glass-strong">
      <div className="threat-header">
        <div>
          <span className="panel-title mono">THREAT MATRIX</span>
          <div className="display threat-title">{sorted.length} Cities Ranked</div>
        </div>
        <span className="mono threat-meta">US AQI · DESC</span>
      </div>
      <div className="threat-list">
        {sorted.map((c, i) => {
          const hasData = c.data_available !== false && c.aqi != null;

          if (!hasData) {
            return (
              <button className="threat-row" key={c.name} onClick={() => onCitySelect?.(c)}
                style={{ opacity: 0.45 }}>
                <span className="badge" style={{ width: 80, justifyContent: "center", background: "#1f2937", color: "#6b7280", border: "1px solid #374151" }}>
                  NO DATA
                </span>
                <span className="threat-city">{c.name}</span>
                <span className="threat-bar-wrap" />
                <span className="threat-aqi mono" style={{ color: "#6b7280" }}>—</span>
                <span className="threat-trend" style={{ color: "#6b7280" }}>—</span>
              </button>
            );
          }

          const cat       = aqiCategory(c.aqi);
          const pct       = (c.aqi / max) * 100;
          const trend     = i % 3 === 0 ? "↑" : i % 3 === 1 ? "→" : "↓";
          const trendColor = trend === "↑" ? "#ef3a4d" : trend === "↓" ? "#34d27a" : "#FFB300";
          const stationNote = c.station_count > 1
            ? `${c.station_count} stn`
            : c.primary_station
            ? "1 stn"
            : null;

          return (
            <button className="threat-row" key={c.name} onClick={() => onCitySelect?.(c)}>
              <span className={`badge ${cat.klass}`} style={{ width: 80, justifyContent: "center" }}>
                {cat.name.slice(0, 4).toUpperCase()}
              </span>
              <span className="threat-city">{c.name}</span>
              <span className="threat-bar-wrap">
                <span className="threat-bar" style={{ width: pct + "%", background: cat.color, boxShadow: `0 0 12px ${cat.color}55` }}></span>
              </span>
              <span className="threat-aqi mono" style={{ color: cat.color }}>
                {c.aqi}
                {stationNote && (
                  <span style={{ fontSize: 9, opacity: 0.45, marginLeft: 4 }}>({stationNote})</span>
                )}
              </span>
              <span className="threat-trend" style={{ color: trendColor }}>{trend}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
