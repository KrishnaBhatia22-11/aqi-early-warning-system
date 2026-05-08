import { aqiCategory } from "../utils/aqiCategory";

export default function LiveTicker({ cities }) {
  if (!cities?.length) return null;
  const items = [...cities, ...cities];
  return (
    <div style={{ position: "relative", width: "100%", display: "block" }}>
      <div className="ticker-wrap">
<div className="ticker-track">
          {items.map((c, i) => {
            const cat = aqiCategory(c.aqi);
            return (
              <span className="ticker-item mono" key={i}>
                <span className="ticker-dot" style={{ background: cat.color, boxShadow: `0 0 6px ${cat.color}` }}></span>
                <span className="ticker-city">{c.name.toUpperCase()}</span>
                <span className="ticker-aqi" style={{ color: cat.color }}>{c.aqi}</span>
                <span className="ticker-cat">{cat.name.toUpperCase()}</span>
              </span>
            );
          })}
        </div>
      </div>
    </div>
  );
}
