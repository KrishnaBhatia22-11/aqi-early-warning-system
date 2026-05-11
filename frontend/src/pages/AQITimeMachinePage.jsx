import { useState, useCallback } from "react";
import { fetchHistory } from "../utils/api";

const CITIES = [
  "Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata",
  "Hyderabad", "Ahmedabad", "Pune", "Jaipur", "Lucknow",
  "Kanpur", "Patna", "Bhopal", "Nagpur", "Surat",
  "Visakhapatnam", "Chandigarh", "Indore",
];

function aqiColor(aqi) {
  if (aqi <= 50)  return "#22c55e";
  if (aqi <= 100) return "#a3e635";
  if (aqi <= 200) return "#eab308";
  if (aqi <= 300) return "#f97316";
  if (aqi <= 400) return "#ef4444";
  return "#a855f7";
}

function aqiCategory(aqi) {
  if (aqi <= 50)  return "Good";
  if (aqi <= 100) return "Satisfactory";
  if (aqi <= 200) return "Moderate";
  if (aqi <= 300) return "Poor";
  if (aqi <= 400) return "Very Poor";
  return "Severe";
}

function fmtDate(dateStr) {
  if (!dateStr) return "";
  const parts = dateStr.split("-");
  if (parts.length < 3) return dateStr;
  const months = ["Jan","Feb","Mar","Apr","May","Jun",
                  "Jul","Aug","Sep","Oct","Nov","Dec"];
  const m = parseInt(parts[1], 10);
  const d = parseInt(parts[2], 10);
  if (isNaN(m) || m < 1 || m > 12) return dateStr;
  return `${months[m - 1]} ${d}`;
}

// ── SVG Bar Chart ──────────────────────────────────────────────────────────────

function HistoryChart({ data }) {
  const [hovered, setHovered] = useState(null);

  if (!data || data.length === 0) return null;

  const padL = 48, padT = 20, padR = 20, padB = 56;
  const chartW = 660;
  const chartH = 180;
  const totalW = chartW + padL + padR;
  const totalH = chartH + padT + padB;
  const n = data.length;
  const barSlot = chartW / n;
  const barW = Math.min(64, Math.max(10, barSlot * 0.68));
  const maxAqi = 500;
  const yScale = (v) => chartH - (v / maxAqi) * chartH;
  const gridLines = [100, 200, 300, 400];

  return (
    <div className="tm-chart-wrap">
      <svg viewBox={`0 0 ${totalW} ${totalH}`} style={{ width: "100%", overflow: "visible" }}>

        {/* Grid lines + Y labels */}
        {gridLines.map(v => (
          <g key={v}>
            <line
              x1={padL} y1={padT + yScale(v)}
              x2={padL + chartW} y2={padT + yScale(v)}
              stroke="rgba(255,255,255,0.06)" strokeWidth="1"
            />
            <text
              x={padL - 6} y={padT + yScale(v) + 4}
              textAnchor="end" fontSize="10"
              fill="rgba(255,255,255,0.35)"
            >{v}</text>
          </g>
        ))}

        {/* Y axis label */}
        <text
          x={12} y={padT + chartH / 2}
          textAnchor="middle" fontSize="9" fill="rgba(255,255,255,0.3)"
          transform={`rotate(-90, 12, ${padT + chartH / 2})`}
        >AQI</text>

        {/* Bars + date labels */}
        {data.map((pt, i) => {
          const bx = padL + i * barSlot + (barSlot - barW) / 2;
          const rawH = (pt.aqi / maxAqi) * chartH;
          const barH = Math.max(2, rawH);
          const by = padT + chartH - barH;
          const col = aqiColor(pt.aqi);
          const isHov = hovered === i;
          const labelX = padL + i * barSlot + barSlot / 2;
          const labelY = padT + chartH + 14;

          return (
            <g
              key={pt.date}
              onMouseEnter={() => setHovered(i)}
              onMouseLeave={() => setHovered(null)}
              style={{ cursor: "pointer" }}
            >
              <rect
                x={bx} y={by} width={barW} height={barH}
                fill={col} opacity={isHov ? 1 : 0.72} rx="3"
              />
              {isHov && (
                <text
                  x={bx + barW / 2} y={by - 6}
                  textAnchor="middle" fontSize="11"
                  fontWeight="700" fill={col}
                >{pt.aqi}</text>
              )}
              <text
                x={labelX} y={labelY}
                textAnchor="end" fontSize="9"
                fill="rgba(255,255,255,0.45)"
                transform={`rotate(-45, ${labelX}, ${labelY})`}
              >{fmtDate(pt.date)}</text>
            </g>
          );
        })}

        {/* Hover tooltip */}
        {hovered !== null && (() => {
          const pt = data[hovered];
          const col = aqiColor(pt.aqi);
          const barH = Math.max(2, (pt.aqi / maxAqi) * chartH);
          const barTopY = padT + chartH - barH;
          const boxW = 120;
          const boxH = pt.pm25_avg != null ? 50 : 36;
          const cx = padL + hovered * barSlot + barSlot / 2;
          const bx = Math.min(Math.max(cx - boxW / 2, padL), padL + chartW - boxW);
          const by = Math.max(boxH + 8, barTopY - 10);
          return (
            <g pointerEvents="none">
              <rect
                x={bx} y={by - boxH} width={boxW} height={boxH}
                fill="#0f1f3d" stroke={col} strokeWidth="1"
                rx="4" opacity="0.97"
              />
              <text x={bx + 8} y={by - boxH + 13} fontSize="9" fill={col} fontWeight="700">
                {pt.date}
              </text>
              <text x={bx + 8} y={by - boxH + 27} fontSize="11" fill="#fff" fontWeight="700">
                AQI {pt.aqi} · {aqiCategory(pt.aqi)}
              </text>
              {pt.pm25_avg != null && (
                <text x={bx + 8} y={by - boxH + 41} fontSize="9" fill="rgba(255,255,255,0.5)">
                  PM2.5 avg: {pt.pm25_avg}
                </text>
              )}
            </g>
          );
        })()}
      </svg>
    </div>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────────

export default function AQITimeMachinePage() {
  const [city, setCity] = useState("Delhi");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchHistory(city);
      setResult(data);
    } catch (e) {
      setError(e.message || "Failed to fetch history");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }, [city]);

  return (
    <div className="page tm-page">

      {/* Header */}
      <div className="tm-header">
        <div className="mono tm-eyebrow">HISTORICAL DATA · WAQI</div>
        <h1 className="tm-title">AQI Time Machine</h1>
        <p className="tm-sub">
          Real air quality history direct from WAQI. No synthetic data — ever.
        </p>
      </div>

      {/* Controls */}
      <div className="tm-controls">
        <select
          className="tm-select"
          value={city}
          onChange={e => { setCity(e.target.value); setResult(null); setError(null); }}
        >
          {CITIES.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <button className="tm-load-btn" onClick={load} disabled={loading}>
          {loading ? "Loading…" : "Load Data"}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="tm-error">
          <span>⚠ {error}</span>
        </div>
      )}

      {/* Loading skeleton */}
      {loading && (
        <div className="tm-skeleton-wrap">
          <div className="skeleton" style={{ height: 80, borderRadius: 12, marginBottom: 12 }} />
          <div className="skeleton" style={{ height: 260, borderRadius: 12, marginBottom: 12 }} />
          <div className="skeleton" style={{ height: 80, borderRadius: 12 }} />
        </div>
      )}

      {/* Results */}
      {!loading && result && (
        <>
          {/* Current reading */}
          <div className="tm-current-card">
            <div className="tm-current-left">
              <div className="mono tm-eyebrow" style={{ color: "#22c55e", marginBottom: 4 }}>
                CURRENT READING
              </div>
              <div className="tm-aqi-big" style={{ color: aqiColor(result.current_aqi) }}>
                {result.current_aqi}
              </div>
              <div className="tm-cat" style={{ color: aqiColor(result.current_aqi) }}>
                {aqiCategory(result.current_aqi)}
              </div>
            </div>
            <div className="tm-current-right">
              <span className="tm-live-badge">● WAQI Live</span>
              {result.current_time && (
                <div className="mono" style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", marginTop: 6 }}>
                  Updated: {result.current_time}
                </div>
              )}
              <div className="mono" style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", marginTop: 4 }}>
                {result.city}
              </div>
            </div>
          </div>

          {/* Historical chart or honest no-data message */}
          {result.data_available ? (
            <>
              <div className="tm-section-head">
                <span className="mono tm-eyebrow">DAILY HISTORY</span>
                <span className="tm-data-note">{result.history.length} days · WAQI pm25 forecast data</span>
              </div>

              <HistoryChart data={result.history} />

              {/* Summary stats */}
              <div className="tm-stats-grid">
                {[
                  {
                    label: "AVG AQI",
                    value: result.summary.avg_aqi,
                    color: aqiColor(result.summary.avg_aqi),
                  },
                  {
                    label: "WORST DAY",
                    value: fmtDate(result.summary.worst_day),
                    sub: `AQI ${result.summary.max_aqi}`,
                    color: aqiColor(result.summary.max_aqi),
                  },
                  {
                    label: "BEST DAY",
                    value: fmtDate(result.summary.best_day),
                    sub: `AQI ${result.summary.min_aqi}`,
                    color: aqiColor(result.summary.min_aqi),
                  },
                  {
                    label: "DAYS OF DATA",
                    value: result.summary.days_available,
                    color: "#94a3b8",
                  },
                ].map(s => (
                  <div key={s.label} className="tm-stat-box">
                    <div className="mono tm-stat-label">{s.label}</div>
                    <div className="tm-stat-value" style={{ color: s.color }}>{s.value}</div>
                    {s.sub && <div className="tm-stat-sub">{s.sub}</div>}
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="tm-no-data">
              <div className="tm-no-data-icon">📭</div>
              <div className="tm-no-data-msg">
                Historical daily breakdown not available for {result.city} from WAQI.
              </div>
              <div className="tm-no-data-sub">
                Showing current reading only. WAQI historical coverage varies by city and monitoring station.
              </div>
            </div>
          )}
        </>
      )}

      {/* Empty state before first load */}
      {!loading && !result && !error && (
        <div className="tm-empty">
          <div style={{ fontSize: 52, marginBottom: 12 }}>📅</div>
          <div style={{ fontSize: 16, color: "rgba(255,255,255,0.6)", marginBottom: 6 }}>
            Select a city and click Load Data
          </div>
          <div style={{ fontSize: 13, color: "rgba(255,255,255,0.3)" }}>
            Real data from WAQI only — no synthetic generation
          </div>
        </div>
      )}

      {/* Source attribution — always visible */}
      <div className="tm-source-footer">
        <span>Data source: <strong>WAQI — World Air Quality Index</strong></span>
        <span className="tm-source-sep">·</span>
        <a
          href="https://waqi.info"
          target="_blank"
          rel="noreferrer"
          className="tm-source-link"
        >waqi.info</a>
        <span className="tm-source-sep">·</span>
        <span>Updated every hour</span>
        <span className="tm-source-sep">·</span>
        <span>Historical data availability varies by city and station</span>
      </div>

    </div>
  );
}
