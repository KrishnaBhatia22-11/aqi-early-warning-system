export default function ShapChart({ shap, predicted, idle }) {
  const sorted = [...shap].sort((a, b) => Math.abs(b.value) - Math.abs(a.value));
  const max = Math.max(...sorted.map(s => Math.abs(s.value)), 1);

  return (
    <div className="shap-chart">
      {sorted.map((s, i) => {
        const pct = (Math.abs(s.value) / max) * 100;
        const color = s.value > 0 ? "#ef3a4d" : "#34d27a";
        return (
          <div className="shap-row" key={s.feature} style={{ animationDelay: `${i * 80}ms` }}>
            <div className="shap-feature mono">{s.feature}</div>
            <div className="shap-bar-wrap">
              <div className="shap-axis"></div>
              <div
                className={`shap-bar ${s.value > 0 ? "pos" : "neg"}`}
                style={{
                  width: pct + "%",
                  background: `linear-gradient(${s.value > 0 ? "to right" : "to left"}, ${color}, ${color}aa)`,
                  boxShadow: `0 0 18px ${color}55`,
                }}
              ></div>
            </div>
            <div className="shap-value mono" style={{ color }}>
              {s.value > 0 ? "+" : ""}{s.value.toFixed(1)}
            </div>
          </div>
        );
      })}
      <div className="shap-base mono">
        <span>BASE VALUE: 89.2</span>
        <span>→</span>
        <span style={{ color: idle ? "var(--text-mute)" : "var(--orange)" }}>
          {idle ? "AWAITING PREDICTION…" : `PREDICTED: ${predicted}`}
        </span>
      </div>
    </div>
  );
}
