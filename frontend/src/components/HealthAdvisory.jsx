const RISK = {
  SAFE:      { label: "SAFE",           bg: "rgba(52,210,122,0.12)",  color: "#6dec9f", border: "rgba(52,210,122,0.35)",  pulse: false },
  LOW:       { label: "LOW",            bg: "rgba(163,201,74,0.12)",  color: "#c1e06a", border: "rgba(163,201,74,0.38)",  pulse: false },
  MEDIUM:    { label: "MEDIUM",         bg: "rgba(255,179,0,0.14)",   color: "#ffd166", border: "rgba(255,179,0,0.45)",   pulse: false },
  HIGH:      { label: "HIGH",           bg: "rgba(255,107,0,0.16)",   color: "#ffb38a", border: "rgba(255,107,0,0.5)",    pulse: false },
  VERY_HIGH: { label: "VERY HIGH",      bg: "rgba(239,58,77,0.18)",   color: "#ff8893", border: "rgba(239,58,77,0.55)",   pulse: false },
  AVOID:     { label: "AVOID OUTDOORS", bg: "rgba(194,0,42,0.22)",    color: "#ff6c79", border: "rgba(194,0,42,0.65)",    pulse: true  },
};

// tiers: 0=Good  1=Satisfactory  2=Moderate  3=Poor  4=Severe  5=Hazardous
const GROUPS = [
  {
    icon: "👶", label: "Children (under 12)",
    tiers: [
      { risk: "LOW",       text: "Can play outside freely. Air is clean and safe." },
      { risk: "LOW",       text: "Unusually sensitive children may limit prolonged exertion." },
      { risk: "MEDIUM",    text: "Limit prolonged outdoor play. Use indoor spaces during peak hours." },
      { risk: "HIGH",      text: "Avoid outdoor activities. Keep windows closed." },
      { risk: "HIGH",      text: "Do not allow outdoor play. Seal windows and doors." },
      { risk: "AVOID",     text: "Keep indoors at all times. Emergency health risk for children." },
    ],
  },
  {
    icon: "👴", label: "Elderly (above 60)",
    tiers: [
      { risk: "LOW",       text: "No restrictions. Enjoy all outdoor activities." },
      { risk: "LOW",       text: "Most can be active outside. Sensitive individuals take note." },
      { risk: "MEDIUM",    text: "Limit prolonged exertion outdoors. Rest indoors frequently." },
      { risk: "HIGH",      text: "Stay indoors. Avoid any outdoor exertion." },
      { risk: "HIGH",      text: "Remain indoors. All outdoor exposure should be avoided." },
      { risk: "AVOID",     text: "Do not go outdoors. Emergency medical risk." },
    ],
  },
  {
    icon: "🫁", label: "Asthma / Respiratory",
    tiers: [
      { risk: "LOW",       text: "No restrictions. Keep inhaler available as usual." },
      { risk: "LOW",       text: "Generally fine. Watch for symptoms during exertion." },
      { risk: "HIGH",      text: "Carry rescue inhaler. Reduce outdoor time significantly." },
      { risk: "VERY_HIGH", text: "Stay indoors. Have rescue medication ready. Seek help if symptoms worsen." },
      { risk: "VERY_HIGH", text: "Stay indoors. Nebulizer ready. Seek immediate help if symptoms spike." },
      { risk: "AVOID",     text: "Maximum indoor precautions. Call doctor immediately if symptoms appear." },
    ],
  },
  {
    icon: "❤️", label: "Heart Conditions",
    tiers: [
      { risk: "LOW",       text: "No restrictions. Normal outdoor activity is fine." },
      { risk: "LOW",       text: "Generally fine. Monitor heart rate during physical activity." },
      { risk: "HIGH",      text: "Reduce physical exertion. Watch for chest pain or breathlessness." },
      { risk: "VERY_HIGH", text: "Stay indoors. Avoid all exertion. Consult doctor if symptoms appear." },
      { risk: "VERY_HIGH", text: "Stay indoors. All physical activity should be avoided." },
      { risk: "AVOID",     text: "Stay indoors. High risk of cardiac events. Seek medical supervision." },
    ],
  },
  {
    icon: "🤰", label: "Pregnant Women",
    tiers: [
      { risk: "LOW",       text: "Clean air. Enjoy outdoor activities as normal." },
      { risk: "LOW",       text: "Acceptable quality. Brief outdoor activities are fine." },
      { risk: "MEDIUM",    text: "Limit outdoor time. Pollution can affect fetal development." },
      { risk: "HIGH",      text: "Stay indoors. Poor air quality is linked to premature birth risk." },
      { risk: "HIGH",      text: "Remain indoors. Use an air purifier in your room." },
      { risk: "AVOID",     text: "Do not go outdoors. Severe risk to maternal and fetal health." },
    ],
  },
  {
    icon: "🚶", label: "Healthy Adults",
    tiers: [
      { risk: "SAFE",      text: "Excellent air quality. No precautions needed." },
      { risk: "SAFE",      text: "No significant concerns. Enjoy outdoor activities freely." },
      { risk: "LOW",       text: "Sensitive individuals should limit prolonged outdoor exertion." },
      { risk: "MEDIUM",    text: "Limit outdoor activities. Use N95 mask if going out." },
      { risk: "HIGH",      text: "Avoid outdoor activity. N95 mask essential if going out." },
      { risk: "AVOID",     text: "Stay indoors. Immediate health effects possible for everyone." },
    ],
  },
  {
    icon: "🏃", label: "Athletes / Outdoor Workers",
    tiers: [
      { risk: "SAFE",      text: "Ideal conditions for training and outdoor work." },
      { risk: "SAFE",      text: "Good conditions. Hydrate well during sessions." },
      { risk: "LOW",       text: "Shorter sessions recommended. Monitor breathing closely." },
      { risk: "MEDIUM",    text: "Move training indoors. Outdoor exercise not recommended." },
      { risk: "HIGH",      text: "All outdoor exercise suspended. Reschedule sessions." },
      { risk: "AVOID",     text: "No outdoor work or training. Severe respiratory risk." },
    ],
  },
];

function getTier(aqi) {
  if (aqi <= 50)  return 0;
  if (aqi <= 100) return 1;
  if (aqi <= 200) return 2;
  if (aqi <= 300) return 3;
  if (aqi <= 400) return 4;
  return 5;
}

export default function HealthAdvisory({ aqi, idle }) {
  const tier = getTier(aqi);

  return (
    <div className="ha-section">
      <div className="ha-panel glass-strong">
        <div className="panel-header">
          <span className="mono panel-title">HEALTH ADVISORY BY GROUP</span>
          <span className="mono panel-meta">
            {idle ? "AWAITING PREDICTION" : `AQI ${aqi} · ${["GOOD","SATISFACTORY","MODERATE","POOR","SEVERE","HAZARDOUS"][tier]}`}
          </span>
        </div>

        <div className="ha-grid">
          {GROUPS.map((g, i) => {
            const { risk, text } = g.tiers[tier];
            const r = RISK[risk];
            return (
              <div
                key={g.label}
                className="ha-row"
                style={{ animationDelay: `${i * 55}ms` }}
              >
                <div className="ha-who">
                  <span className="ha-icon" role="img" aria-label={g.label}>{g.icon}</span>
                  <span className="ha-name mono">{g.label}</span>
                </div>
                <p className="ha-text">{text}</p>
                <span
                  className="ha-badge mono"
                  style={{
                    background: r.bg,
                    color: r.color,
                    borderColor: r.border,
                    animation: r.pulse ? "pulse-red 1.6s infinite" : "none",
                  }}
                >
                  {r.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
