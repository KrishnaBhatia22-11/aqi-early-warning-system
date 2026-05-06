import { aqiCategory } from "../utils/aqiCategory";

export default function PredictionHistory({ history, onPick }) {
  if (!history?.length) return null;
  return (
    <div className="glass-strong predict-history">
      <div className="panel-header">
        <span className="panel-title mono">YOUR RECENT PREDICTIONS</span>
        <span className="mono panel-meta">CLICK TO RELOAD</span>
      </div>
      <div className="ph-row">
        {history.slice(0, 5).map((h, i) => {
          const cat = aqiCategory(h.aqi);
          return (
            <button className="ph-card" key={i} onClick={() => onPick?.(h)}>
              <span className="ph-num" style={{ color: cat.color }}>{h.aqi}</span>
              <span className="ph-meta">{cat.name.toUpperCase()}</span>
              <span className="ph-meta" style={{ color: "var(--text-mute)" }}>{h.t}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
