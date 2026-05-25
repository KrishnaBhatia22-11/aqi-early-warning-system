import { useState, useEffect, useRef } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from "recharts";
import { fetchDbHistory } from "../utils/api";

// ── City Dropdown ─────────────────────────────────────────────────────────────

function CityDropdown({ value, onChange, cities }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    if (!open) return;
    const onDown = e => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    const onKey  = e => { if (e.key === "Escape") setOpen(false); };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown",   onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown",   onKey);
    };
  }, [open]);

  return (
    <div className="cmp-dd-wrap tm-dd-wrap" ref={ref}>
      <button
        type="button"
        className={`cmp-dd-trigger${open ? " open" : ""}`}
        onClick={() => setOpen(v => !v)}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <span className="cmp-dd-value">{value}</span>
        <span className="cmp-dd-arrow" aria-hidden="true">▾</span>
      </button>
      {open && (
        <div className="cmp-dd-panel" role="listbox">
          {cities.map(c => (
            <button
              key={c}
              type="button"
              role="option"
              aria-selected={c === value}
              className={`cmp-dd-option${c === value ? " selected" : ""}`}
              onClick={() => { onChange(c); setOpen(false); }}
            >
              <span>{c}</span>
              {c === value && <span className="cmp-dd-check" aria-hidden="true">✓</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Constants ─────────────────────────────────────────────────────────────────

const CITIES = [
  "Delhi", "Mumbai", "Bengaluru", "Chennai", "Kolkata", "Hyderabad",
  "Ahmedabad", "Pune", "Jaipur", "Lucknow", "Kanpur", "Patna",
  "Bhopal", "Nagpur", "Surat", "Indore", "Visakhapatnam", "Chandigarh",
  "Coimbatore", "Kochi", "Agra", "Varanasi", "Amritsar", "Jodhpur",
  "Udaipur", "Mysuru", "Pondicherry", "Ghaziabad", "Noida", "Faridabad",
  "Gurugram", "Meerut", "Moradabad", "Ludhiana", "Jalandhar",
  "Bhubaneswar", "Guwahati", "Ranchi", "Raipur", "Dehradun", "Shimla",
  "Jammu", "Srinagar", "Thiruvananthapuram", "Madurai", "Vijayawada",
  "Nashik", "Aurangabad", "Kolhapur", "Solapur", "Warangal", "Guntur",
  "Tiruchirappalli",
];

const DAYS_OPTIONS = [1, 3, 7, 12];

// ── Helpers ───────────────────────────────────────────────────────────────────

function aqiColor(aqi) {
  if (!aqi) return "#94a3b8";
  if (aqi <= 50)  return "#10b981";
  if (aqi <= 100) return "#84cc16";
  if (aqi <= 200) return "#f97316";
  if (aqi <= 300) return "#ef4444";
  if (aqi <= 400) return "#7c3aed";
  return "#475569";
}

function aqiCategory(aqi) {
  if (!aqi) return "Unknown";
  if (aqi <= 50)  return "Good";
  if (aqi <= 100) return "Satisfactory";
  if (aqi <= 200) return "Moderate";
  if (aqi <= 300) return "Poor";
  if (aqi <= 400) return "Very Poor";
  return "Severe";
}

function fmtDateTime(isoStr) {
  if (!isoStr) return "";
  const d = new Date(isoStr);
  const months = ["Jan","Feb","Mar","Apr","May","Jun",
                  "Jul","Aug","Sep","Oct","Nov","Dec"];
  return `${months[d.getMonth()]} ${d.getDate()}, ${String(d.getHours()).padStart(2, "0")}:00`;
}

function fmtXTick(isoStr) {
  const d = new Date(isoStr);
  const months = ["Jan","Feb","Mar","Apr","May","Jun",
                  "Jul","Aug","Sep","Oct","Nov","Dec"];
  return `${months[d.getMonth()]} ${d.getDate()}`;
}

// ── Chart ─────────────────────────────────────────────────────────────────────

function renderDot(props) {
  const { cx, cy, payload } = props;
  if (cx == null || cy == null) return null;
  return (
    <circle
      key={`dot-${payload.timestamp}`}
      cx={cx} cy={cy} r={2.5}
      fill={aqiColor(payload.aqi)}
    />
  );
}

function ChartTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d   = payload[0].payload;
  const col = aqiColor(d.aqi);
  return (
    <div style={{
      background: "#0f172a",
      border: `1px solid ${col}`,
      borderRadius: 8,
      padding: "10px 14px",
      minWidth: 160,
    }}>
      <div style={{ color: "rgba(255,255,255,0.45)", fontSize: 11, marginBottom: 4 }}>
        {fmtDateTime(d.timestamp)}
      </div>
      <div style={{ color: col, fontSize: 18, fontWeight: 700, marginBottom: 2 }}>
        AQI {d.aqi}
      </div>
      <div style={{ color: col, fontSize: 11, marginBottom: 6 }}>
        {aqiCategory(d.aqi)}
      </div>
      {d.pm25 != null && (
        <div style={{ color: "rgba(255,255,255,0.5)", fontSize: 11 }}>PM2.5: {d.pm25} µg/m³</div>
      )}
      {d.pm10 != null && (
        <div style={{ color: "rgba(255,255,255,0.5)", fontSize: 11 }}>PM10: {d.pm10} µg/m³</div>
      )}
    </div>
  );
}

function HistoryLineChart({ readings }) {
  const tickInterval = Math.max(1, Math.floor(readings.length / 8));
  return (
    <div className="tm-chart-wrap">
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={readings} margin={{ top: 10, right: 24, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
          <XAxis
            dataKey="timestamp"
            tickFormatter={fmtXTick}
            interval={tickInterval}
            tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }}
            stroke="rgba(255,255,255,0.1)"
          />
          <YAxis
            tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }}
            stroke="rgba(255,255,255,0.1)"
            width={38}
            label={{
              value: "AQI", angle: -90, position: "insideLeft",
              fill: "rgba(255,255,255,0.3)", fontSize: 11, dx: -2,
            }}
          />
          <Tooltip content={<ChartTooltip />} />
          <Line
            type="monotone"
            dataKey="aqi"
            stroke="#f97316"
            strokeWidth={2}
            dot={renderDot}
            activeDot={{ r: 5, fill: "#f97316", stroke: "#fff", strokeWidth: 1 }}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function AQITimeMachinePage() {
  const [city,    setCity]    = useState("Delhi");
  const [days,    setDays]    = useState(7);
  const [result,  setResult]  = useState(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchDbHistory(city, days);
        if (!cancelled) setResult(data);
      } catch (e) {
        if (!cancelled) {
          setError(e.message || "Failed to fetch history");
          setResult(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [city, days]);

  const summary  = result?.summary;
  const readings = result?.readings ?? [];
  const hasData  = readings.length > 0;

  return (
    <div className="page tm-page">

      {/* Header */}
      <div className="tm-header">
        <div className="mono tm-eyebrow">HISTORICAL DATA · DATABASE</div>
        <h1 className="tm-title">AQI Time Machine</h1>
        <p className="tm-sub">
          Real hourly air quality from our database — collected since May 13, 2026.
        </p>
      </div>

      {/* Controls */}
      <div className="tm-controls" style={{ gap: 12, flexWrap: "wrap" }}>
        <CityDropdown
          value={city}
          onChange={c => { setCity(c); setResult(null); }}
          cities={CITIES}
        />
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          {DAYS_OPTIONS.map(d => (
            <button
              key={d}
              type="button"
              onClick={() => setDays(d)}
              style={{
                padding: "7px 16px",
                borderRadius: 8,
                border: `1px solid ${days === d ? "#f97316" : "rgba(255,255,255,0.12)"}`,
                background: days === d ? "rgba(249,115,22,0.15)" : "transparent",
                color: days === d ? "#f97316" : "rgba(255,255,255,0.5)",
                fontSize: 13,
                fontWeight: days === d ? 700 : 400,
                cursor: "pointer",
                transition: "all 0.15s",
              }}
            >{d}d</button>
          ))}
        </div>
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
          <div className="skeleton" style={{ height: 48, borderRadius: 12, marginBottom: 12 }} />
          <div className="skeleton" style={{ height: 280, borderRadius: 12, marginBottom: 12 }} />
          <div className="skeleton" style={{ height: 80, borderRadius: 12 }} />
        </div>
      )}

      {/* Results */}
      {!loading && result && (
        hasData ? (
          <>
            <div className="tm-section-head">
              <span className="mono tm-eyebrow">HOURLY HISTORY</span>
              <span className="tm-data-note">
                {readings.length} readings · last {days} day{days !== 1 ? "s" : ""}
              </span>
            </div>

            <HistoryLineChart readings={readings} />

            {summary && (
              <div className="tm-stats-grid">
                {[
                  {
                    label: "AVG AQI",
                    value: summary.avg_aqi,
                    color: aqiColor(summary.avg_aqi),
                    sub:   aqiCategory(summary.avg_aqi),
                  },
                  {
                    label: "HIGHEST AQI",
                    value: summary.max_aqi,
                    color: aqiColor(summary.max_aqi),
                    sub:   fmtDateTime(summary.max_aqi_time),
                  },
                  {
                    label: "LOWEST AQI",
                    value: summary.min_aqi,
                    color: aqiColor(summary.min_aqi),
                    sub:   fmtDateTime(summary.min_aqi_time),
                  },
                  {
                    label: "HOURS OF DATA",
                    value: summary.total_readings,
                    color: "#94a3b8",
                    sub:   `${days}-day window`,
                  },
                ].map(s => (
                  <div key={s.label} className="tm-stat-box">
                    <div className="mono tm-stat-label">{s.label}</div>
                    <div className="tm-stat-value" style={{ color: s.color }}>{s.value}</div>
                    {s.sub && <div className="tm-stat-sub">{s.sub}</div>}
                  </div>
                ))}
              </div>
            )}
          </>
        ) : (
          <div className="tm-no-data">
            <div className="tm-no-data-icon">📭</div>
            <div className="tm-no-data-msg">No data available for {result.city}</div>
            <div className="tm-no-data-sub">
              No readings found in our database for this city in the last {days} day{days !== 1 ? "s" : ""}.
            </div>
          </div>
        )
      )}

      {/* Source footer */}
      <div className="tm-source-footer">
        <span>Real data from our database.</span>
        <span className="tm-source-sep">·</span>
        <span>Collected hourly since May 13, 2026.</span>
      </div>

    </div>
  );
}
