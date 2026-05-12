import { aqiCategory } from "../utils/aqiCategory";

export default function ThreatMatrix({ cities, onCitySelect }) {
  const sorted = [...cities].sort((a, b) => b.aqi - a.aqi);
  const max = Math.max(...sorted.map(c => c.aqi));

  return (
    <div className="threat-panel glass-strong">
      <div className="threat-header">
        <div>
          <span className="panel-title mono">THREAT MATRIX</span>
          <div className="display threat-title">{sorted.length} Cities Ranked</div>
        </div>
        <span className="mono threat-meta">SORTED · DESC</span>
      </div>
      <div className="threat-list">
        {sorted.map((c, i) => {
          const cat = aqiCategory(c.aqi);
          const pct = (c.aqi / max) * 100;
          const trend = i % 3 === 0 ? "↑" : i % 3 === 1 ? "→" : "↓";
          const trendColor = trend === "↑" ? "#ef3a4d" : trend === "↓" ? "#34d27a" : "#FFB300";
          return (
            <button className="threat-row" key={c.name} onClick={() => onCitySelect?.(c)}>
              <span className={`badge ${cat.klass}`} style={{ width: 80, justifyContent: "center" }}>
                {cat.name.slice(0, 4).toUpperCase()}
              </span>
              <span className="threat-city">{c.name}</span>
              <span className="threat-bar-wrap">
                <span className="threat-bar" style={{ width: pct + "%", background: cat.color, boxShadow: `0 0 12px ${cat.color}55` }}></span>
              </span>
              <span className="threat-aqi mono" style={{ color: cat.color }}>{c.aqi}</span>
              <span className="threat-trend" style={{ color: trendColor }}>{trend}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
