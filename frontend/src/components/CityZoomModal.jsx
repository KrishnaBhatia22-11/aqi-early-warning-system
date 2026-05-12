import { useState, useEffect, useCallback } from "react";
import { aqiCategory } from "../utils/aqiCategory";
import CountUp from "./CountUp";
import { TREND_7D } from "../data/index";

function ZpSparkline({ values, color }) {
  const w = 320, h = 80;
  const min = Math.min(...values), max = Math.max(...values);
  const pts = values.map((v, i) => [
    (i / (values.length - 1)) * w,
    h - ((v - min) / (max - min || 1)) * (h - 8) - 4,
  ]);
  const d = pts.map((p, i) => (i === 0 ? "M" : "L") + p[0] + " " + p[1]).join(" ");
  return (
    <svg viewBox={`0 0 ${w} ${h}`} style={{ width: "100%", height: 80 }} preserveAspectRatio="none">
      <defs>
        <linearGradient id="zpFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%"   stopColor={color} stopOpacity="0.5"/>
          <stop offset="100%" stopColor={color} stopOpacity="0"/>
        </linearGradient>
      </defs>
      <path d={`${d} L ${w} ${h} L 0 ${h} Z`} fill="url(#zpFill)"/>
      <path d={d} fill="none" stroke={color} strokeWidth="2" style={{ filter: `drop-shadow(0 0 6px ${color})` }}/>
      {pts.map((p, i) => i === pts.length - 1 && (
        <circle key={i} cx={p[0]} cy={p[1]} r="4" fill={color} stroke="#0a0a0a" strokeWidth="1.5"/>
      ))}
    </svg>
  );
}

function aqiBarColor(aqi) {
  if (aqi <= 50)  return "#22c55e";
  if (aqi <= 100) return "#84cc16";
  if (aqi <= 200) return "#f59e0b";
  if (aqi <= 300) return "#f97316";
  if (aqi <= 400) return "#ef4444";
  return "#a855f7";
}

const QUALITY_STYLE = {
  HIGH:   { color: "#22c55e", label: "HIGH QUALITY" },
  MEDIUM: { color: "#f59e0b", label: "MEDIUM QUALITY" },
  LOW:    { color: "#f97316", label: "LOW QUALITY" },
  SINGLE: { color: "#6b7280", label: "SINGLE STATION" },
};

function StationBreakdown({ city, avgAqi, catColor }) {
  const stations = city.stations?.slice(0, 8) ?? [];
  if (!stations.length) return null;

  const maxAqi    = Math.max(...stations.map(s => s.aqi));
  const quality   = city.data_quality ?? "SINGLE";
  const qStyle    = QUALITY_STYLE[quality] ?? QUALITY_STYLE.SINGLE;
  const chartW    = 220;

  return (
    <div className="zp-station-breakdown">
      <div className="zp-section-title mono" style={{ marginBottom: 10 }}>
        STATION BREAKDOWN
        <span
          className="mono"
          style={{
            marginLeft: 10, fontSize: 10, padding: "2px 8px",
            border: `1px solid ${qStyle.color}`, color: qStyle.color, borderRadius: 2,
          }}
        >
          {qStyle.label}
        </span>
      </div>

      <div className="mono" style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", marginBottom: 10 }}>
        City average from {city.station_count} CPCB station{city.station_count !== 1 ? "s" : ""}
        {city.source ? ` · ${city.source}` : ""}
      </div>

      <svg
        viewBox={`0 0 ${chartW + 160} ${stations.length * 26 + 4}`}
        style={{ width: "100%", maxWidth: 460, display: "block", marginBottom: 12 }}
      >
        {stations.map((s, i) => {
          const barW  = (s.aqi / maxAqi) * chartW;
          const color = aqiBarColor(s.aqi);
          const y     = i * 26 + 2;
          const nameShort = s.name.length > 20 ? s.name.slice(0, 19) + "…" : s.name;
          return (
            <g key={i}>
              <text x="0" y={y + 14} fontSize="9" fontFamily="JetBrains Mono, monospace"
                fill="rgba(255,255,255,0.55)" textAnchor="start">
                {nameShort}
              </text>
              <rect x="130" y={y + 3} width={barW} height="14" rx="2"
                fill={color} opacity="0.85"/>
              <text x={130 + barW + 6} y={y + 14} fontSize="10"
                fontFamily="JetBrains Mono, monospace" fill={color} fontWeight="bold">
                {s.aqi}
              </text>
            </g>
          );
        })}

        {/* City average dashed line */}
        {(() => {
          const lineX = 130 + (avgAqi / maxAqi) * chartW;
          return (
            <line
              x1={lineX} y1="0"
              x2={lineX} y2={stations.length * 26}
              stroke={catColor} strokeWidth="1.5"
              strokeDasharray="4,3" opacity="0.7"
            />
          );
        })()}
      </svg>

      <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
        {city.cleanest_area && (
          <div className="mono" style={{ fontSize: 11 }}>
            <span style={{ color: "#34d27a" }}>CLEANEST</span>
            <span style={{ color: "rgba(255,255,255,0.6)" }}> {city.cleanest_area.split(',')[0]} — </span>
            <span style={{ color: "#34d27a", fontWeight: "bold" }}>{city.cleanest_aqi}</span>
          </div>
        )}
        {city.most_polluted_area && (
          <div className="mono" style={{ fontSize: 11 }}>
            <span style={{ color: "#ef3a4d" }}>WORST</span>
            <span style={{ color: "rgba(255,255,255,0.6)" }}> {city.most_polluted_area.split(',')[0]} — </span>
            <span style={{ color: "#ef3a4d", fontWeight: "bold" }}>{city.most_polluted_aqi}</span>
          </div>
        )}
        {city.city_spread > 0 && (
          <div className="mono" style={{ fontSize: 11, color: "rgba(255,255,255,0.4)" }}>
            SPREAD {city.city_spread} AQI
          </div>
        )}
      </div>
    </div>
  );
}

export default function CityZoomModal({ city, onClose, onPredict, onViewReport, onSetAlert }) {
  const [phase, setPhase] = useState("zooming");
  const [showHint, setShowHint] = useState(true);

  useEffect(() => {
    const t = setTimeout(() => setPhase("loaded"), 1500);
    return () => clearTimeout(t);
  }, []);

  useEffect(() => {
    const t = setTimeout(() => setShowHint(false), 3000);
    return () => clearTimeout(t);
  }, []);

  const handleEsc = useCallback((e) => {
    if (e.key === "Escape") onClose();
  }, [onClose]);

  useEffect(() => {
    window.addEventListener("keydown", handleEsc);
    return () => window.removeEventListener("keydown", handleEsc);
  }, [handleEsc]);

  if (!city) return null;
  const cat = aqiCategory(city.aqi);
  const factor = city.aqi / 200;
  const readings = [
    { name: "PM2.5", val: Math.round(80 * factor),          unit: "µg/m³", crit: city.pollutant === "PM2.5" },
    { name: "PM10",  val: Math.round(120 * factor),         unit: "µg/m³", crit: city.pollutant === "PM10"  },
    { name: "NO",    val: Math.round(5 + 10 * factor),      unit: "µg/m³" },
    { name: "NO2",   val: Math.round(30 * factor),          unit: "µg/m³", crit: city.pollutant === "NO2"   },
    { name: "NOx",   val: Math.round(35 * factor),          unit: "µg/m³" },
    { name: "NH3",   val: Math.round(10 * factor),          unit: "µg/m³" },
    { name: "CO",    val: (1.5 * factor).toFixed(2),        unit: "mg/m³" },
    { name: "SO2",   val: Math.round(15 * factor),          unit: "µg/m³" },
    { name: "O3",    val: Math.round(40 * factor),          unit: "µg/m³", crit: city.pollutant === "O3"    },
  ];
  const trend = TREND_7D.map(v => Math.max(20, v + (city.aqi - 200)));

  const stationLabel = city.station_count > 1
    ? `AVG OF ${city.station_count} CPCB STATIONS`
    : "SINGLE STATION · LIVE";

  return (
    <div className="city-zoom-overlay" onClick={onClose}>
      <div className={`zoom-map phase-${phase}`}>
        <div className="zoom-map-inner">
          <svg viewBox="0 0 800 800" className="street-map">
            <defs>
              <radialGradient id="cityGlow" cx="0.5" cy="0.5" r="0.5">
                <stop offset="0%"   stopColor={cat.color} stopOpacity="0.35"/>
                <stop offset="50%"  stopColor={cat.color} stopOpacity="0.10"/>
                <stop offset="100%" stopColor={cat.color} stopOpacity="0"   />
              </radialGradient>
              <pattern id="streetGrid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255,107,0,0.06)" strokeWidth="1"/>
              </pattern>
              <pattern id="streetGridSm" width="8" height="8" patternUnits="userSpaceOnUse">
                <path d="M 8 0 L 0 0 0 8" fill="none" stroke="rgba(255,107,0,0.025)" strokeWidth="0.5"/>
              </pattern>
            </defs>
            <rect width="800" height="800" fill="url(#streetGridSm)"/>
            <rect width="800" height="800" fill="url(#streetGrid)"/>
            <rect width="800" height="800" fill="url(#cityGlow)"/>
            {[80, 160, 240, 320].map(r => (
              <circle key={r} cx="400" cy="400" r={r} fill="none" stroke="rgba(255,107,0,0.18)" strokeWidth="1.2"/>
            ))}
            {Array.from({length: 12}).map((_, i) => {
              const a = (i * 30 - 15) * Math.PI / 180;
              return <line key={i} x1="400" y1="400" x2={400 + 360*Math.cos(a)} y2={400 + 360*Math.sin(a)} stroke="rgba(255,107,0,0.12)" strokeWidth="1"/>;
            })}
            {Array.from({length: 80}).map((_, i) => {
              const x = (i * 73) % 760 + 20, y = (i * 113) % 760 + 20;
              const w = 8 + (i % 5) * 6, h = 8 + ((i + 2) % 5) * 6;
              return <rect key={i} x={x} y={y} width={w} height={h} fill="rgba(255,107,0,0.05)" stroke="rgba(255,107,0,0.15)" strokeWidth="0.5"/>;
            })}
            <g transform="translate(400, 400)">
              <circle r="60" fill="none" stroke={cat.color} strokeWidth="1" opacity="0.5">
                <animate attributeName="r" values="40;90;40" dur="2s" repeatCount="indefinite"/>
                <animate attributeName="opacity" values="0.6;0;0.6" dur="2s" repeatCount="indefinite"/>
              </circle>
              <circle r="20" fill={cat.color} opacity="0.3"/>
              <circle r="8" fill={cat.color} stroke="#0a0a0a" strokeWidth="2"/>
              <line x1="-30" y1="0" x2="-12" y2="0" stroke={cat.color} strokeWidth="2"/>
              <line x1="12"  y1="0" x2="30"  y2="0" stroke={cat.color} strokeWidth="2"/>
              <line x1="0" y1="-30" x2="0" y2="-12" stroke={cat.color} strokeWidth="2"/>
              <line x1="0" y1="12"  x2="0" y2="30"  stroke={cat.color} strokeWidth="2"/>
            </g>
            <g stroke={cat.color} strokeWidth="2" fill="none">
              <path d="M 30 30 L 30 70 M 30 30 L 70 30"/>
              <path d="M 770 30 L 770 70 M 770 30 L 730 30"/>
              <path d="M 30 770 L 30 730 M 30 770 L 70 770"/>
              <path d="M 770 770 L 770 730 M 770 770 L 730 770"/>
            </g>
            <text x="40" y="790" fontFamily="JetBrains Mono" fontSize="10" fill={cat.color}>28.6139°N · 77.2090°E</text>
            <text x="760" y="790" fontFamily="JetBrains Mono" fontSize="10" fill={cat.color} textAnchor="end">SCALE 1:8000 · ZOOM 18x</text>
          </svg>
        </div>
      </div>

      <div className={`zoom-panel glass-strong phase-${phase}`} onClick={e => e.stopPropagation()}>
        <button className="city-zoom-out-btn" onClick={onClose}>✕ ZOOM OUT</button>
        <div className="zp-top">
          <div>
            <div className="mono zp-eyebrow">{stationLabel} · {city.name.toUpperCase()} · LIVE</div>
            <div className="display zp-name">{city.name}</div>
            {showHint && (
              <div className="zp-hint mono">Press ESC or click ✕ to return to map</div>
            )}
            <div className="mono zp-coords">
              {city.source ?? "WAQI"} · {city.data_quality ?? "LIVE"}
            </div>
          </div>
          <div className="zp-aqi-block" style={{ color: cat.color }}>
            <div className="display zp-aqi-num"><CountUp to={city.aqi} duration={1200}/></div>
            <span className={`badge ${cat.klass}`} style={{ fontSize: 13, padding: "6px 14px" }}>{cat.name.toUpperCase()}</span>
            <div className="mono" style={{ fontSize: 10, color: "rgba(255,255,255,0.35)", marginTop: 4 }}>US AQI (EPA)</div>
          </div>
        </div>

        {/* Station breakdown — only shows when multi-station data is available */}
        <StationBreakdown city={city} avgAqi={city.aqi} catColor={cat.color} />

        <div className="zp-grid">
          <div className="zp-pollutants">
            <div className="zp-section-title mono">POLLUTANT TELEMETRY</div>
            <div className="zp-pol-grid">
              {readings.map(r => (
                <div className={`zp-pol ${r.crit ? "crit" : ""}`} key={r.name}>
                  <span className="mono zp-pol-name">{r.name}</span>
                  <span className="display zp-pol-val">{r.val}<span className="zp-pol-unit">{r.unit}</span></span>
                  {r.crit && <span className="zp-pol-flag mono">TOP DRIVER</span>}
                </div>
              ))}
            </div>
          </div>

          <div className="zp-trend">
            <div className="zp-section-title mono">7-DAY TREND</div>
            <ZpSparkline values={trend} color={cat.color}/>
            <div className="mono zp-trend-meta">
              <span>7d ▲ +28%</span>
              <span style={{ color: cat.color }}>PEAK {Math.max(...trend)}</span>
            </div>
            <div className="zp-driver">
              <span className="mono zp-section-title" style={{ marginBottom: 6 }}>TOP POLLUTANT</span>
              <div className="zp-driver-row">
                <span className="display zp-driver-name" style={{ color: cat.color }}>{city.pollutant}</span>
                <span className="mono zp-driver-pct">38% OF AQI</span>
              </div>
            </div>
          </div>

          <div className="zp-health">
            <div className="zp-section-title mono">HEALTH ADVISORY</div>
            <div className="zp-health-row">
              <div className="zp-health-card"><span>👶</span><b>Children</b><i style={{color:cat.color}}>{city.aqi>200?"AVOID":city.aqi>100?"LIMIT":"OK"}</i></div>
              <div className="zp-health-card"><span>🫁</span><b>Sensitive</b><i style={{color:cat.color}}>{city.aqi>200?"N95":city.aqi>100?"MASK":"OK"}</i></div>
              <div className="zp-health-card"><span>🏃</span><b>Exercise</b><i style={{color:cat.color}}>{city.aqi>200?"NO":city.aqi>100?"EASY":"GO"}</i></div>
            </div>
          </div>
        </div>

        <div className="zp-actions">
          <button className="btn-primary" onClick={onViewReport}>VIEW FULL CITY REPORT →</button>
          <button className="btn-ghost" onClick={onSetAlert}><span>🔔</span> SET ALERT FOR THIS CITY</button>
          <button className="btn-ghost" onClick={onPredict}>PREDICT CUSTOM AQI →</button>
        </div>
      </div>

      <button className="zoom-close" onClick={onClose}>✕ ZOOM OUT</button>
      <div className="zoom-meta mono">
        <div>● ZOOMED · {city.name.toUpperCase()}</div>
        <div>{city.last_updated ? `UPDATED ${city.last_updated}` : "UPDATED 12s AGO"}</div>
      </div>
    </div>
  );
}
