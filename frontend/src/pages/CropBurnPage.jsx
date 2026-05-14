import { useState, useEffect } from "react";
import { fetchCropBurnStatus } from "../utils/api";

// ── Status config ─────────────────────────────────────────────
const STATUS_CFG = {
  ACTIVE_BURN:    { icon: "🔥", label: "ACTIVE BURNING EVENT", color: "#ef4444", bgClass: "cb-hero-bg-active",    pulse: true  },
  EARLY_WARNING:  { icon: "⚠️", label: "EARLY WARNING",        color: "#f59e0b", bgClass: "cb-hero-bg-early",     pulse: true  },
  RESIDUAL_SMOKE: { icon: "🌫",  label: "RESIDUAL SMOKE",       color: "#f97316", bgClass: "cb-hero-bg-residual",  pulse: false },
  CLEAR:          { icon: "✓",  label: "NO BURNING DETECTED",  color: "#22c55e", bgClass: "cb-hero-bg-clear",     pulse: false },
};

const CONF_COLOR = { HIGH: "#ef4444", MEDIUM: "#f59e0b", LOW: "#f97316", NONE: "#22c55e" };

const NASA_LEVEL_COLOR = {
  NONE:     "#94a3b8",
  LOW:      "#eab308",
  MODERATE: "#f97316",
  HIGH:     "#ef4444",
  PEAK:     "#7c3aed",
};

const NASA_LEVEL_DESC = {
  NONE:     "No active crop fires detected by NASA VIIRS satellite in Punjab + Haryana in last 24 hours.",
  LOW:      "Low fire activity detected. Early burning activity beginning.",
  MODERATE: "Moderate burning detected. Smoke likely traveling toward Indo-Gangetic plain.",
  HIGH:     "High fire activity. Significant smoke expected in Delhi, Lucknow, Kanpur within 12–24 hours.",
  PEAK:     "Peak burning season. Severe smoke event imminent for 400 million people.",
};

function aqiColor(aqi) {
  if (!aqi) return "#94a3b8";
  if (aqi <= 50)  return "#22c55e";
  if (aqi <= 100) return "#a3e635";
  if (aqi <= 200) return "#eab308";
  if (aqi <= 300) return "#f97316";
  if (aqi <= 400) return "#ef4444";
  return "#a855f7";
}

// ── Confidence arc meter ──────────────────────────────────────
function ConfidenceMeter({ value, color }) {
  const r = 62, cx = 90, cy = 90;
  const circ    = 2 * Math.PI * r;      // 389.6
  const trackLen = circ * 0.75;         // 270° sweep
  const fillLen  = (value / 100) * trackLen;

  return (
    <svg viewBox="0 0 180 180" style={{ width: 200, height: 200 }}>
      {/* Track arc */}
      <circle
        cx={cx} cy={cy} r={r}
        fill="none"
        stroke="rgba(255,255,255,0.07)"
        strokeWidth="12"
        strokeLinecap="round"
        strokeDasharray={`${trackLen} ${circ - trackLen}`}
        transform={`rotate(135, ${cx}, ${cy})`}
      />
      {/* Value arc */}
      <circle
        cx={cx} cy={cy} r={r}
        fill="none"
        stroke={color}
        strokeWidth="12"
        strokeLinecap="round"
        strokeDasharray={`${fillLen} ${circ - fillLen}`}
        transform={`rotate(135, ${cx}, ${cy})`}
        style={{ filter: `drop-shadow(0 0 8px ${color}80)`, transition: "stroke-dasharray 1.2s ease" }}
      />
      <text x={cx} y={cy - 6} textAnchor="middle" fill={color}
        fontSize="40" fontWeight="700" fontFamily="Space Grotesk, sans-serif">
        {value}
      </text>
      <text x={cx} y={cy + 16} textAnchor="middle" fill="rgba(255,255,255,0.35)"
        fontSize="10" fontFamily="JetBrains Mono, monospace" letterSpacing="0.15em">
        CONFIDENCE
      </text>
    </svg>
  );
}

// ── Signal card ───────────────────────────────────────────────
function SignalCard({ icon, title, status, label: labelProp, children }) {
  const label = labelProp ?? (status === "confirmed" ? "CONFIRMED" : status === "partial" ? "PARTIAL" : "NOT DETECTED");
  return (
    <div className={`cb-signal-card ${status}`}>
      <div className="cb-sig-icon">{icon}</div>
      <div className="cb-sig-head">
        <span className="cb-sig-title mono">{title}</span>
        <span className={`cb-sig-status ${status}`}>{label}</span>
      </div>
      <div className="cb-sig-detail">{children}</div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────
export default function CropBurnPage({ setPage }) {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  useEffect(() => {
    setLoading(true);
    fetchCropBurnStatus()
      .then(d  => { setData(d);            setLoading(false); })
      .catch(e => { setError(e.message);   setLoading(false); });
  }, []);

  const cfg = data ? (STATUS_CFG[data.status] ?? STATUS_CFG.CLEAR) : STATUS_CFG.CLEAR;
  const sig  = data?.detection_signals ?? {};
  const hw   = data?.health_warning ?? {};

  const sortedCities = Object.entries(data?.city_aqi ?? {})
    .filter(([, v]) => v !== null)
    .sort(([, a], [, b]) => b.aqi - a.aqi);

  const VULN = [
    { icon: "👶", group: "Children",       advice: "No outdoor school activities" },
    { icon: "👴", group: "Elderly",         advice: "Stay indoors completely" },
    { icon: "🫁", group: "Asthma patients", advice: "Pre-medicate before any outdoor exposure" },
    { icon: "❤️", group: "Heart patients",  advice: "Cancel outdoor exercise" },
    { icon: "🤰", group: "Pregnant",        advice: "Avoid outdoor exposure entirely" },
  ];

  const TL_STEPS = [
    { icon: "🌾", label: "HARVEST" },
    { icon: "🚜", label: "STUBBLE REMAINS" },
    { icon: "🔥", label: "BURNING BEGINS" },
    { icon: "💨", label: "SMOKE TRAVELS" },
    { icon: "🏙", label: "CITIES CHOKE" },
  ];

  return (
    <div className="page cb-page">

      {/* Page header */}
      <div className="cb-page-header">
        <div className="mono cb-eyebrow">CROP BURNING · EARLY WARNING SYSTEM</div>
        <h1 className="cb-page-title">Stubble Burning Alert</h1>
        <p className="cb-page-sub">
          Real-time detection of crop residue burning across North India.
          400 million people. 48-hour advance warning.
        </p>
      </div>

      {/* Loading skeleton */}
      {loading && (
        <div className="cb-section">
          <div className="skeleton" style={{ height: 320, borderRadius: 16, marginBottom: 20 }} />
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 16, marginBottom: 20 }}>
            {[0,1,2].map(i => <div key={i} className="skeleton" style={{ height: 220, borderRadius: 12 }} />)}
          </div>
          <div className="skeleton" style={{ height: 140, borderRadius: 12 }} />
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div className="cb-section" style={{ textAlign: "center", paddingTop: 80 }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>⚠</div>
          <div style={{ color: "#ef4444", fontSize: 14, marginBottom: 8 }}>Failed to fetch crop burn status</div>
          <div style={{ color: "var(--text-mute)", fontSize: 12, marginBottom: 24 }}>{error}</div>
          <button className="btn-ghost" onClick={() => { setError(null); setLoading(true); fetchCropBurnStatus().then(d => { setData(d); setLoading(false); }).catch(e => { setError(e.message); setLoading(false); }); }}>
            RETRY
          </button>
        </div>
      )}

      {data && !loading && (
        <>

          {/* ── SECTION 1: Status Hero ── */}
          <div className={`cb-hero ${cfg.bgClass}`}>
            <div className="cb-hero-inner">
              <div
                className={`cb-status-badge${cfg.pulse ? " cb-pulse" : ""}`}
                style={{ color: cfg.color, borderColor: cfg.color, background: cfg.color + "12" }}
              >
                {cfg.icon}&nbsp;&nbsp;{cfg.label}
              </div>

              <ConfidenceMeter
                value={data.confidence}
                color={CONF_COLOR[data.confidence_level] ?? "#22c55e"}
              />

              <p style={{ color: "#fff", fontSize: 14, textAlign: "center", maxWidth: 400, margin: "0 auto", opacity: 0.8 }}>
                {data.confidence >= 85 ? "Peak burning. Severe smoke event for 400 million people."
                : data.confidence >= 70 ? "Active burning. Expect smoke in North India within 24hrs."
                : data.confidence >= 50 ? "Early burning activity. Sensitive groups take precautions."
                : data.confidence >= 25 ? "Season active but no burning detected. Stay informed."
                :                         "No crop burning activity detected right now."}
              </p>

              {data.season_active ? (
                <div className="cb-season-strip">
                  🌾&nbsp; {sig.season_name?.toUpperCase()}
                  &nbsp;·&nbsp; {sig.season_dates}
                  &nbsp;·&nbsp; Day {sig.days_into_season} of {(sig.days_into_season ?? 0) + (sig.days_remaining ?? 0)}
                  &nbsp;·&nbsp; {sig.days_remaining} days remaining
                </div>
              ) : (
                <div className="cb-season-strip cb-offseason">
                  📅&nbsp; NEXT BURNING SEASON: {sig.next_season} · {sig.next_season_start}
                  &nbsp;·&nbsp; {sig.days_until_next} days away
                </div>
              )}
            </div>
          </div>

          {/* ── SECTION 2: Detection Signals ── */}
          <div className="cb-section">
            <div className="cb-section-head">
              <div className="mono cb-eyebrow">DETECTION SIGNALS</div>
              <h2 className="cb-section-title">What our system detected</h2>
              <p className="cb-section-sub">Four independent signals confirm or rule out a burning event</p>
            </div>

            <div className="cb-signals-grid">

              {/* Signal 1 — Seasonal Calendar */}
              <SignalCard
                icon="📅"
                title="SEASONAL CALENDAR"
                status={data.season_active ? "confirmed" : "inactive"}
              >
                {data.season_active ? (
                  <>
                    <strong style={{ color: "var(--text)" }}>{sig.season_name}</strong>
                    <div style={{ marginTop: 8 }}>
                      Farmers burning {sig.season_crop} stubble in {sig.season_states} right now.
                      Season runs {sig.season_dates}.
                    </div>
                    <div className="cb-sig-detail-row" style={{ marginTop: 8 }}>
                      <span>Day {sig.days_into_season} into season · {sig.days_remaining} days remaining</span>
                    </div>
                  </>
                ) : (
                  <>
                    No active burning season.{" "}
                    <strong style={{ color: "var(--text)" }}>{sig.next_season} season</strong>{" "}
                    starts {sig.next_season_start} ({sig.days_until_next} days away).
                  </>
                )}
              </SignalCard>

              {/* Signal 2 — Regional AQI Pattern */}
              <SignalCard
                icon="📊"
                title="REGIONAL AQI PATTERN"
                status={
                  !data.aqi_data_available    ? "inactive"
                  : sig.north_india_affected >= 3 ? "confirmed"
                  : sig.north_india_affected >= 1 ? "partial"
                  : "inactive"
                }
              >
                {!data.aqi_data_available ? (
                  "AQI data unavailable — WAQI API not responding. Season calendar still active."
                ) : sortedCities.length === 0 ? (
                  "No live AQI data available for monitored cities."
                ) : (
                  <div className="cb-sig-detail-row">
                    {sortedCities.slice(0, 4).map(([city, d]) => (
                      <span key={city}>
                        <span style={{ color: d.spiking ? "#ef4444" : "rgba(255,255,255,0.25)" }}>●</span>
                        {" "}{city}: <strong style={{ color: aqiColor(d.aqi) }}>{d.aqi}</strong>
                        {" "}
                        <span style={{ color: "var(--text-mute)" }}>
                          ({d.pct_above_baseline > 0 ? "+" : ""}{d.pct_above_baseline}% vs baseline)
                        </span>
                      </span>
                    ))}
                    {sig.north_india_affected > 0 && (
                      <span style={{ marginTop: 6, color: "#ef4444", fontWeight: 600 }}>
                        {sig.north_india_affected} city/cities above 1.6× seasonal baseline
                      </span>
                    )}
                  </div>
                )}
              </SignalCard>

              {/* Signal 3 — Geographic Spread */}
              <SignalCard
                icon="🗺"
                title="GEOGRAPHIC SPREAD"
                status={
                  !data.aqi_data_available    ? "inactive"
                  : sig.regional_pattern       ? "confirmed"
                  : sig.north_india_affected >= 2 ? "partial"
                  : "inactive"
                }
              >
                {!data.aqi_data_available ? (
                  "AQI data unavailable"
                ) : sig.regional_pattern ? (
                  <>
                    <strong style={{ color: "var(--text)" }}>Multi-city event confirmed.</strong>
                    <div style={{ marginTop: 8 }}>
                      {sig.north_india_affected} North Indian cities simultaneously above seasonal
                      baseline — consistent with a regional smoke event, not local pollution.
                    </div>
                    {sig.early_warning_pattern && (
                      <div style={{ marginTop: 8, color: "#f59e0b" }}>
                        ⚠ Punjab spiking ahead of Delhi — smoke front is moving southeast
                      </div>
                    )}
                    {sig.wind_direction && (
                      <div style={{ marginTop: 6, color: "var(--text-dim)", fontSize: 12 }}>
                        Wind: {sig.wind_direction} {sig.wind_from_nw ? "(favourable for smoke transport)" : ""}
                      </div>
                    )}
                  </>
                ) : sig.north_india_affected >= 1 ? (
                  `${sig.north_india_affected} cities above baseline — pattern not yet regional (need 3+). Monitoring.`
                ) : (
                  "No simultaneous multi-city spike detected across North India."
                )}
              </SignalCard>

              {/* Signal 4 — NASA FIRMS Satellite */}
              {(() => {
                const fireLevel = data.nasa_fire_level ?? "NONE";
                const fireCount = data.nasa_fire_count ?? 0;
                const active    = data.signal4_nasa_active ?? false;
                const levelColor = NASA_LEVEL_COLOR[fireLevel] ?? "#94a3b8";
                return (
                  <SignalCard
                    icon="🛰️"
                    title="NASA SATELLITE FIRES"
                    status={active ? "confirmed" : "inactive"}
                    label={active ? "DETECTED" : "NOT DETECTED"}
                  >
                    <div style={{ fontSize: 26, fontWeight: 700, color: levelColor, marginBottom: 6 }}>
                      {fireCount} fire hotspots
                    </div>
                    <span style={{
                      display: "inline-block",
                      padding: "2px 10px",
                      borderRadius: 999,
                      fontSize: 11,
                      fontWeight: 700,
                      letterSpacing: "0.08em",
                      background: levelColor + "22",
                      color: levelColor,
                      border: `1px solid ${levelColor}55`,
                      marginBottom: 10,
                    }}>
                      {fireLevel}
                    </span>
                    <div style={{ color: "var(--text-dim)", fontSize: 13, lineHeight: 1.5 }}>
                      {NASA_LEVEL_DESC[fireLevel] ?? NASA_LEVEL_DESC.NONE}
                    </div>
                    <div style={{ marginTop: 10, color: "var(--text-mute)", fontSize: 11 }}>
                      Source: NASA FIRMS VIIRS · Updates every 3 hours · Covers Punjab + Haryana + W.UP
                    </div>
                  </SignalCard>
                );
              })()}

            </div>
          </div>

          {/* ── SECTION 3: Affected Cities Strip ── */}
          {sortedCities.length > 0 && (
            <div className="cb-section" style={{ paddingTop: 0 }}>
              <div className="cb-section-head">
                <div className="mono cb-eyebrow">LIVE AQI · 6 MONITORED CITIES</div>
                <h2 className="cb-section-title">Cities currently monitored</h2>
              </div>
              <div className="cb-cities-strip">
                {sortedCities.map(([city, d]) => (
                  <div key={city} className={`cb-city-card glass${d.spiking ? " spiking" : ""}`}>
                    <div className="mono cb-city-name">{city.toUpperCase()}</div>
                    <div className="cb-city-aqi" style={{ color: aqiColor(d.aqi) }}>{d.aqi}</div>
                    <div className="mono cb-city-baseline">Baseline: {d.baseline}</div>
                    <div className={`cb-city-spike ${d.pct_above_baseline > 0 ? "up" : "down"}`}>
                      {d.pct_above_baseline > 0 ? "▲" : "▼"} {Math.abs(d.pct_above_baseline)}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── SECTION 4: Health Advisory ── */}
          {hw.level && (
            <div className="cb-health-section">
              <div className="cb-section-head">
                <div className="mono cb-eyebrow">HEALTH ADVISORY</div>
                <h2 className="cb-section-title">What this means for you</h2>
              </div>
              <div className={`cb-health-card ${hw.level}`}>
                <div className={`cb-health-level ${hw.level}`}>{hw.level} RISK</div>
                <div className="cb-health-msg">{hw.message}</div>
                <div className="cb-health-action">{hw.action}</div>
                <div className="cb-vuln-grid">
                  {VULN.map(v => (
                    <div key={v.group} className="cb-vuln-card">
                      <div className="cb-vuln-icon">{v.icon}</div>
                      <div className="cb-vuln-group">{v.group}</div>
                      <div className="cb-vuln-advice">{v.advice}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* ── SECTION 5: Educational ── */}
          <div className="cb-edu-section">
            <div className="mono cb-eyebrow" style={{ marginBottom: 12 }}>THE SCIENCE</div>
            <h2 className="cb-edu-title">Why does this happen every year?</h2>

            <div className="cb-timeline">
              {TL_STEPS.map((step, i) => (
                <div key={i} className="cb-tl-step">
                  <div className="cb-tl-node">
                    <span className="cb-tl-icon">{step.icon}</span>
                    <span className="cb-tl-label mono">{step.label}</span>
                  </div>
                  {i < TL_STEPS.length - 1 && <div className="cb-tl-arrow" />}
                </div>
              ))}
            </div>

            <div className="cb-fact-grid">
              <div className="cb-fact-card glass">
                <div className="cb-fact-icon">📊</div>
                <div className="cb-fact-number">~35 million tonnes of crop residue burned annually in Punjab alone</div>
                <div className="cb-fact-source">SOURCE: CPCB — Central Pollution Control Board</div>
              </div>
              <div className="cb-fact-card glass">
                <div className="cb-fact-icon">💨</div>
                <div className="cb-fact-number">Smoke travels 500–1000 km carried by northwest winds from Punjab to the Indo-Gangetic Plain</div>
                <div className="cb-fact-source">SOURCE: IITM — Indian Institute of Tropical Meteorology</div>
              </div>
              <div className="cb-fact-card glass">
                <div className="cb-fact-icon">🏥</div>
                <div className="cb-fact-number">Crop burning contributes up to 40% of Delhi's PM2.5 concentration in November</div>
                <div className="cb-fact-source">SOURCE: SAFAR India — System of Air Quality and Weather Forecasting</div>
              </div>
            </div>
          </div>

          {/* Source footer */}
          <div className="cb-source-footer">
            {data.data_source ?? "Own DB + WAQI live + seasonal calendar + NASA FIRMS VIIRS satellite"}
            &nbsp;·&nbsp;
            Last updated: {new Date(data.last_updated + "Z").toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata", hour: "2-digit", minute: "2-digit" })} IST
          </div>

        </>
      )}
    </div>
  );
}
