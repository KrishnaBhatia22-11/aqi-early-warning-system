import { useRef, useEffect, useState } from "react";

// ── SVG layout constants
const W = 800, H = 280;
const ML = 52, MR = 16, MT = 22, MB = 36;
const PW = W - ML - MR;   // 732
const PH = H - MT - MB;   // 222

const fy = v => MT + PH * (1 - Math.max(0, Math.min(500, v)) / 500);
const fx = i => ML + (i / 23) * PW;

function aqiColor(v) {
  if (v <= 50)  return "#34d27a";
  if (v <= 100) return "#a3c94a";
  if (v <= 200) return "#FFB300";
  if (v <= 300) return "#FF6B00";
  if (v <= 400) return "#ef3a4d";
  return "#c2002a";
}

const ZONES = [
  { lo: 400, hi: 500, fill: "rgba(194,0,42,0.06)"    },
  { lo: 300, hi: 400, fill: "rgba(239,58,77,0.06)"   },
  { lo: 200, hi: 300, fill: "rgba(255,107,0,0.06)"   },
  { lo: 100, hi: 200, fill: "rgba(255,179,0,0.06)"   },
  { lo:  50, hi: 100, fill: "rgba(163,201,74,0.06)"  },
  { lo:   0, hi:  50, fill: "rgba(52,210,122,0.07)"  },
];

const GRIDS = [50, 100, 200, 300, 400];

// ── Skeleton shimmer
function Skeleton() {
  return (
    <div className="fc-skeleton">
      <div className="fc-skel-row">
        <div>
          <div className="fc-skel-line" style={{ width: 220, height: 11, marginBottom: 8 }} />
          <div className="fc-skel-line" style={{ width: 140, height: 24, marginBottom: 6 }} />
          <div className="fc-skel-line" style={{ width: 190, height: 10 }} />
        </div>
        <div className="fc-skel-badge" />
      </div>
      <div className="fc-skel-chart" />
      <div className="fc-skel-stats">
        {[0,1,2].map(i => <div key={i} className="fc-skel-stat" />)}
      </div>
    </div>
  );
}

export default function ForecastChart({ forecastData, loading, error, cityName }) {
  const lineRef   = useRef(null);
  const svgRef    = useRef(null);
  const [hoverIdx, setHoverIdx]     = useState(null);
  const [bandVis,  setBandVis]      = useState(false);
  const [peakVis,  setPeakVis]      = useState(false);

  // ── Animate line via stroke-dashoffset when data arrives
  useEffect(() => {
    const path = lineRef.current;
    if (!path || !forecastData) return;
    setBandVis(false);
    setPeakVis(false);

    const len = path.getTotalLength();
    path.style.transition      = "none";
    path.style.strokeDasharray = `${len}`;
    path.style.strokeDashoffset = `${len}`;
    path.getBoundingClientRect(); // force reflow

    path.style.transition       = "stroke-dashoffset 1.5s cubic-bezier(0.4,0,0.2,1)";
    path.style.strokeDashoffset = "0";

    const t1 = setTimeout(() => setBandVis(true), 300);
    const t2 = setTimeout(() => setPeakVis(true), 1600);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, [forecastData]);

  // ── Hover: SVG coordinate transform
  const handleMouseMove = e => {
    const svg = svgRef.current;
    if (!svg || !forecastData) return;
    const pt = svg.createSVGPoint();
    pt.x = e.clientX; pt.y = e.clientY;
    const { x } = pt.matrixTransform(svg.getScreenCTM().inverse());
    setHoverIdx(Math.max(0, Math.min(23, Math.round((x - ML) / (PW / 23)))));
  };

  if (loading) return <Skeleton />;

  if (error) {
    return (
      <div className="fc-error glass-strong">
        <div className="mono" style={{ color: "#ef3a4d", fontSize: 11, letterSpacing: "0.15em", marginBottom: 8 }}>FORECAST UNAVAILABLE</div>
        <div style={{ color: "rgba(255,255,255,0.45)", fontSize: 13 }}>{error}</div>
        <div className="mono" style={{ color: "rgba(255,255,255,0.25)", fontSize: 10, marginTop: 12 }}>Live data only · Prophet AI offline</div>
      </div>
    );
  }

  if (!forecastData) return null;

  const { forecast, peak, low, trend, severity_forecast, recommendation, generated_at } = forecastData;

  const peakIdx = forecast.findIndex(f => f.hour === peak.hour && f.aqi === peak.aqi);
  const safeIdx = peakIdx === -1 ? 0 : peakIdx;

  // ── Build SVG paths
  const linePts = forecast.map((d, i) => `${i === 0 ? "M" : "L"}${fx(i).toFixed(1)} ${fy(d.aqi).toFixed(1)}`).join(" ");

  const bandTop = forecast.map((d, i) => `${i === 0 ? "M" : "L"}${fx(i).toFixed(1)} ${fy(d.upper).toFixed(1)}`).join(" ");
  const bandBot = forecast.slice().reverse().map((d, i) => `L${fx(23 - i).toFixed(1)} ${fy(d.lower).toFixed(1)}`).join(" ");
  const bandPath = `${bandTop} ${bandBot} Z`;

  // ── Trend badge config
  const TREND_CFG = {
    RISING:  { icon: "↑", color: "#ef3a4d", bg: "rgba(239,58,77,0.14)",  border: "rgba(239,58,77,0.4)",  dot: "pulse-red"   },
    FALLING: { icon: "↓", color: "#34d27a", bg: "rgba(52,210,122,0.12)", border: "rgba(52,210,122,0.4)", dot: "pulse-green" },
    STABLE:  { icon: "→", color: "#FFB300", bg: "rgba(255,179,0,0.12)",  border: "rgba(255,179,0,0.4)",  dot: ""            },
  };
  const tc = TREND_CFG[trend] ?? TREND_CFG.STABLE;

  const genTime = (() => {
    try {
      const d = new Date(generated_at);
      return d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
    } catch { return "—"; }
  })();

  return (
    <div className="fc-wrap glass-strong">
      {/* ── Header */}
      <div className="fc-header">
        <div>
          <div className="mono fc-eyebrow">24H AQI FORECAST · PROPHET AI</div>
          <div className="fc-city-name">{cityName ?? forecastData.city}</div>
          <div className="mono fc-meta">Generated {genTime} · Updates hourly</div>
        </div>
        <div className="fc-trend-badge" style={{ background: tc.bg, borderColor: tc.border }}>
          <span className={`fc-trend-dot ${tc.dot}`} style={{ background: tc.color }} />
          <span style={{ color: tc.color, fontSize: 16, fontWeight: 700 }}>{tc.icon}</span>
          <span className="mono" style={{ color: tc.color, fontSize: 11, letterSpacing: "0.12em" }}>{trend}</span>
        </div>
      </div>

      {/* ── SVG Chart */}
      <div className="fc-svg-wrap">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${W} ${H}`}
          className="fc-svg"
          onMouseMove={handleMouseMove}
          onMouseLeave={() => setHoverIdx(null)}
        >
          {/* Background zones */}
          {ZONES.map(z => (
            <rect
              key={z.lo}
              x={ML} y={fy(z.hi)}
              width={PW} height={fy(z.lo) - fy(z.hi)}
              fill={z.fill}
            />
          ))}

          {/* Gridlines + Y labels */}
          {GRIDS.map(v => (
            <g key={v}>
              <line x1={ML} y1={fy(v)} x2={ML + PW} y2={fy(v)} stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
              <text x={ML - 5} y={fy(v) + 3.5} textAnchor="end" fontFamily="JetBrains Mono" fontSize="9" fill="rgba(255,255,255,0.25)">{v}</text>
            </g>
          ))}

          {/* Confidence band */}
          <path
            d={bandPath}
            fill="rgba(255,107,0,0.09)"
            style={{ opacity: bandVis ? 1 : 0, transition: "opacity 0.5s ease" }}
          />

          {/* "NOW" marker */}
          <line x1={fx(0)} y1={MT} x2={fx(0)} y2={MT + PH} stroke="rgba(255,107,0,0.45)" strokeWidth="1.5" strokeDasharray="4,3" />
          <text x={fx(0) + 4} y={MT + 11} fontFamily="JetBrains Mono" fontSize="9" fill="rgba(255,107,0,0.75)">NOW</text>

          {/* Main AQI line */}
          <path
            ref={lineRef}
            d={linePts}
            fill="none"
            stroke="#FF6B00"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            style={{ filter: "drop-shadow(0 0 6px rgba(255,107,0,0.55))" }}
          />

          {/* Peak marker */}
          {peakVis && (
            <g>
              <circle
                cx={fx(safeIdx)} cy={fy(peak.aqi)} r="6"
                fill="#ef3a4d" stroke="#0a0a0a" strokeWidth="2"
                style={{ filter: "drop-shadow(0 0 10px rgba(239,58,77,0.9))", animation: "pulse-red 1.8s infinite" }}
              />
              <text
                x={fx(safeIdx)} y={fy(peak.aqi) - 12}
                textAnchor={safeIdx > 19 ? "end" : safeIdx < 4 ? "start" : "middle"}
                fontFamily="JetBrains Mono" fontSize="10" fontWeight="700" fill="#ef3a4d"
              >
                ▲ {peak.aqi}
              </text>
            </g>
          )}

          {/* X-axis labels */}
          {[0, 4, 8, 12, 16, 20].map(i => (
            <text key={i} x={fx(i)} y={MT + PH + 18} textAnchor="middle" fontFamily="JetBrains Mono" fontSize="9" fill="rgba(255,255,255,0.3)">
              {forecast[i]?.hour ?? ""}
            </text>
          ))}

          {/* Hover crosshair + tooltip */}
          {hoverIdx !== null && (() => {
            const d   = forecast[hoverIdx];
            const cx  = fx(hoverIdx);
            const cy  = fy(d.aqi);
            const col = aqiColor(d.aqi);
            const TW  = 112, TH = 56;
            const tx  = hoverIdx > 19 ? cx - TW - 8 : cx + 8;
            const ty  = Math.max(MT, Math.min(MT + PH - TH, cy - TH / 2));
            return (
              <g>
                <line x1={cx} y1={MT} x2={cx} y2={MT + PH} stroke="rgba(255,255,255,0.18)" strokeWidth="1" strokeDasharray="3,3" />
                <circle cx={cx} cy={cy} r="4.5" fill={col} stroke="#0a0a0a" strokeWidth="2" />
                <rect x={tx} y={ty} width={TW} height={TH} rx="5" fill="rgba(8,8,18,0.94)" stroke={col + "55"} strokeWidth="1" />
                <text x={tx + 9} y={ty + 20} fontFamily="JetBrains Mono" fontSize="18" fontWeight="700" fill={col}>{d.aqi}</text>
                <text x={tx + 9} y={ty + 34} fontFamily="JetBrains Mono" fontSize="8.5" fill="rgba(255,255,255,0.45)">{d.category.toUpperCase()}</text>
                <text x={tx + 9} y={ty + 47} fontFamily="JetBrains Mono" fontSize="8.5" fill="rgba(255,107,0,0.75)">{d.hour}</text>
              </g>
            );
          })()}
        </svg>
      </div>

      {/* ── Stat cards */}
      <div className="fc-stats">
        <div className="fc-stat">
          <span className="fc-stat-dot" style={{ background: aqiColor(peak.aqi) }} />
          <div>
            <div className="mono fc-stat-label">PEAK</div>
            <div className="fc-stat-val" style={{ color: aqiColor(peak.aqi) }}>{peak.aqi}</div>
            <div className="mono fc-stat-sub">{peak.category.toUpperCase()} · {peak.hour}</div>
          </div>
        </div>
        <div className="fc-stat">
          <span className="fc-stat-dot" style={{ background: aqiColor(low.aqi) }} />
          <div>
            <div className="mono fc-stat-label">LOWEST</div>
            <div className="fc-stat-val" style={{ color: aqiColor(low.aqi) }}>{low.aqi}</div>
            <div className="mono fc-stat-sub">{low.category.toUpperCase()} · {low.hour}</div>
          </div>
        </div>
        <div className="fc-stat">
          <span className="fc-stat-dot" style={{ background: "#FFB300" }} />
          <div>
            <div className="mono fc-stat-label">SEVERITY RANGE</div>
            <div className="fc-stat-val" style={{ color: "#FFB300", fontSize: 14 }}>{severity_forecast}</div>
            <div className="mono fc-stat-sub">NEXT 24 HOURS</div>
          </div>
        </div>
      </div>

      {/* ── Recommendation */}
      <div className="fc-recommendation">
        <span className="fc-rec-icon">⚡</span>
        <p className="fc-rec-text">{recommendation}</p>
      </div>
    </div>
  );
}
