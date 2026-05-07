// Shows a dismissable anomaly alert banner — renders nothing for NORMAL status.
const SEVERITY_STYLE = {
  CRITICAL: { bg: "rgba(194,0,42,0.16)",  border: "rgba(194,0,42,0.55)",  color: "#c2002a" },
  HIGH:     { bg: "rgba(239,58,77,0.13)", border: "rgba(239,58,77,0.5)",  color: "#ef3a4d" },
  MEDIUM:   { bg: "rgba(255,107,0,0.12)", border: "rgba(255,107,0,0.45)", color: "#FF6B00" },
  LOW:      { bg: "rgba(255,179,0,0.10)", border: "rgba(255,179,0,0.4)",  color: "#FFB300" },
};

const TYPE_ICON  = { SPIKE: "↑", DROP: "↓", RAPID_RISE: "⚡" };
const TYPE_LABEL = { SPIKE: "AQI SPIKE", DROP: "AQI DROP", RAPID_RISE: "RAPID RISE" };

export default function AnomalyBanner({ anomaly, onDismiss }) {
  if (!anomaly?.is_anomaly || anomaly.type === "NORMAL") return null;

  const s    = SEVERITY_STYLE[anomaly.severity] ?? SEVERITY_STYLE.MEDIUM;
  const icon = TYPE_ICON[anomaly.type]  ?? "⚠";
  const lbl  = TYPE_LABEL[anomaly.type] ?? anomaly.type;

  return (
    <div className="anomaly-banner" style={{ background: s.bg, borderColor: s.border }}>
      <span className="anomaly-pulse-dot" style={{ background: s.color }} />

      <span className="anomaly-icon" style={{ color: s.color }}>{icon}</span>

      <div className="anomaly-body">
        <span className="mono anomaly-type" style={{ color: s.color }}>{lbl}</span>
        <span className="anomaly-msg">{anomaly.message}</span>
      </div>

      <span
        className="mono anomaly-severity-badge"
        style={{ color: s.color, borderColor: s.border, background: s.bg }}
      >
        {anomaly.severity}
      </span>

      {anomaly.data_quality === "synthetic" && (
        <span
          className="mono anomaly-quality"
          title="Anomaly compared against seasonal model baseline — live history not yet accumulated"
        >
          EST
        </span>
      )}

      <button
        className="anomaly-dismiss"
        aria-label="Dismiss anomaly alert"
        onClick={() => {
          console.info("[AnomalyBanner] dismissed:", anomaly.type, anomaly.severity, anomaly.z_score);
          onDismiss?.();
        }}
      >
        ✕
      </button>
    </div>
  );
}
