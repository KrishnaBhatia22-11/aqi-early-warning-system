import { useRef, useEffect, useState, useCallback } from "react";

// ── SVG layout (viewBox coords — responsive via CSS)
const W = 900, H = 320;
const ML = 54, MR = 24, MT = 28, MB = 44;
const PW = W - ML - MR;   // plot width
const PH = H - MT - MB;   // plot height

// y maps AQI 0-500 → SVG y (top=MT, bottom=MT+PH)
const fy = v => MT + PH * (1 - Math.max(0, Math.min(500, v)) / 500);
const fx = i => ML + (i / 23) * PW;

const AQI_ZONES = [
  { lo: 400, hi: 500, color: "#c2002a" },
  { lo: 300, hi: 400, color: "#ef3a4d" },
  { lo: 200, hi: 300, color: "#FF6B00" },
  { lo: 100, hi: 200, color: "#FFB300" },
  { lo:  50, hi: 100, color: "#a3c94a" },
  { lo:   0, hi:  50, color: "#34d27a" },
];

const Y_TICKS = [0, 100, 200, 300, 400, 500];

function aqiColor(v) {
  if (v <= 50)  return "#34d27a";
  if (v <= 100) return "#a3c94a";
  if (v <= 200) return "#FFB300";
  if (v <= 300) return "#FF6B00";
  if (v <= 400) return "#ef3a4d";
  return "#c2002a";
}

// Catmull-Rom → cubic bezier segments (no leading M — caller provides starting point)
function crSegs(pts, t = 0.35) {
  let d = "";
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)];
    const p1 = pts[i];
    const p2 = pts[i + 1];
    const p3 = pts[Math.min(pts.length - 1, i + 2)];
    const cp1x = p1[0] + (p2[0] - p0[0]) * t;
    const cp1y = p1[1] + (p2[1] - p0[1]) * t;
    const cp2x = p2[0] - (p3[0] - p1[0]) * t;
    const cp2y = p2[1] - (p3[1] - p1[1]) * t;
    d += ` C ${cp1x.toFixed(1)} ${cp1y.toFixed(1)} ${cp2x.toFixed(1)} ${cp2y.toFixed(1)} ${p2[0].toFixed(1)} ${p2[1].toFixed(1)}`;
  }
  return d;
}

// ── Skeleton loader
function Skeleton({ slow }) {
  return (
    <div className="fc-skeleton">
      <div className="fc-skel-row">
        <div>
          <div className="fc-skel-line" style={{ width: 200, height: 10, marginBottom: 8 }} />
          <div className="fc-skel-line" style={{ width: 160, height: 28, marginBottom: 6 }} />
          <div className="fc-skel-line" style={{ width: 180, height: 10 }} />
        </div>
        <div className="fc-skel-badge" />
      </div>
      <div className="fc-skel-chart" />
      <div className="fc-skel-stats">
        {[0, 1, 2].map(i => <div key={i} className="fc-skel-stat" />)}
      </div>
      {slow && (
        <div className="mono fc-skel-wake">⏳ WAKING UP FORECAST ENGINE — RENDER COLD START...</div>
      )}
    </div>
  );
}

export default function ForecastChart({ forecastData, loading, slowLoad, error, cityName }) {
  const svgRef      = useRef(null);
  const clipRectRef = useRef(null);
  const [hoverIdx, setHoverIdx] = useState(null);
  const [peakVis,  setPeakVis]  = useState(false);
  // Stable unique clip-path id per component instance
  const clipId = useRef(`fc-clip-${Math.random().toString(36).slice(2, 8)}`).current;

  // ── Animate clip rect left-to-right on new data
  useEffect(() => {
    if (!forecastData || !clipRectRef.current) return;
    setPeakVis(false);
    clipRectRef.current.setAttribute("width", "0");

    const start = performance.now();
    const dur   = 1500;
    let rafId;

    const animate = now => {
      const t    = Math.min(1, (now - start) / dur);
      const ease = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
      if (clipRectRef.current) {
        clipRectRef.current.setAttribute("width", (ease * PW).toFixed(1));
      }
      if (t < 1) {
        rafId = requestAnimationFrame(animate);
      } else {
        setPeakVis(true);
      }
    };
    rafId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(rafId);
  }, [forecastData]);

  // ── Hover: map clientX → nearest data-point index
  const handleMouseMove = useCallback(e => {
    const svg = svgRef.current;
    if (!svg || !forecastData) return;
    const pt = svg.createSVGPoint();
    pt.x = e.clientX;
    pt.y = e.clientY;
    const { x } = pt.matrixTransform(svg.getScreenCTM().inverse());
    setHoverIdx(Math.max(0, Math.min(23, Math.round(((x - ML) / PW) * 23))));
  }, [forecastData]);

  // ── Render states
  if (loading) return <Skeleton slow={slowLoad} />;

  if (error) {
    return (
      <div className="fc-error glass-strong">
        <div className="mono" style={{ color: "#ef3a4d", fontSize: 11, letterSpacing: "0.15em", marginBottom: 8 }}>
          FORECAST UNAVAILABLE
        </div>
        <div style={{ color: "rgba(255,255,255,0.45)", fontSize: 13 }}>{error}</div>
        <div className="mono" style={{ color: "rgba(255,255,255,0.25)", fontSize: 10, marginTop: 12 }}>
          Render backend may be waking up — please try again in 30 seconds.
        </div>
      </div>
    );
  }

  if (!forecastData) return null;

  const { forecast, peak, low, trend, severity_forecast, recommendation, generated_at, base_aqi_source, mean_aqi } = forecastData;

  // ── Build SVG geometry
  const linePts  = forecast.map((d, i) => [fx(i), fy(d.aqi)]);
  const upperPts = forecast.map((d, i) => [fx(i), fy(d.upper)]);
  // Clamp lower bound to chart floor (fy(0) = MT+PH)
  const lowerPts = forecast.map((d, i) => [fx(i), fy(Math.max(0, d.lower))]);

  // Confidence band: upper curve forward → lower curve backward → close
  const bandPath =
    `M ${upperPts[0][0].toFixed(1)} ${upperPts[0][1].toFixed(1)}` +
    crSegs(upperPts) +
    ` L ${lowerPts[23][0].toFixed(1)} ${lowerPts[23][1].toFixed(1)}` +
    crSegs([...lowerPts].reverse()) +
    " Z";

  // Per-segment colored bezier line
  const lineSegs = forecast.slice(0, 23).map((d, i) => {
    const p0 = linePts[Math.max(0, i - 1)];
    const p1 = linePts[i];
    const p2 = linePts[i + 1];
    const p3 = linePts[Math.min(23, i + 2)];
    const cp1x = p1[0] + (p2[0] - p0[0]) * 0.35;
    const cp1y = p1[1] + (p2[1] - p0[1]) * 0.35;
    const cp2x = p2[0] - (p3[0] - p1[0]) * 0.35;
    const cp2y = p2[1] - (p3[1] - p1[1]) * 0.35;
    return {
      d:     `M ${p1[0].toFixed(1)} ${p1[1].toFixed(1)} C ${cp1x.toFixed(1)} ${cp1y.toFixed(1)} ${cp2x.toFixed(1)} ${cp2y.toFixed(1)} ${p2[0].toFixed(1)} ${p2[1].toFixed(1)}`,
      color: aqiColor((d.aqi + forecast[i + 1].aqi) / 2),
    };
  });

  const peakIdx = forecast.findIndex(f => f.hour === peak.hour && f.aqi === peak.aqi);
  const safeIdx = peakIdx === -1 ? 0 : peakIdx;
  const avgColor = aqiColor(mean_aqi ?? peak.aqi);

  const TREND_CFG = {
    RISING:  { icon: "↑", color: "#ef3a4d", bg: "rgba(239,58,77,0.14)",  border: "rgba(239,58,77,0.4)"  },
    FALLING: { icon: "↓", color: "#34d27a", bg: "rgba(52,210,122,0.12)", border: "rgba(52,210,122,0.4)" },
    STABLE:  { icon: "→", color: "#FFB300", bg: "rgba(255,179,0,0.12)",  border: "rgba(255,179,0,0.4)"  },
  };
  const tc = TREND_CFG[trend] ?? TREND_CFG.STABLE;

  const genTime = (() => {
    try { return new Date(generated_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }); }
    catch { return "—"; }
  })();

  return (
    <div className="fc-wrap glass-strong">
      {/* ── Header */}
      <div className="fc-header">
        <div>
          <div className="mono fc-eyebrow">24H AQI FORECAST · DIURNAL AI MODEL</div>
          <div className="fc-city-name">{cityName ?? forecastData.city}</div>
          <div className="mono fc-meta">Generated {genTime} · Updates hourly</div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 8 }}>
          <div className="fc-trend-badge" style={{ background: tc.bg, borderColor: tc.border }}>
            <span style={{ color: tc.color, fontSize: 18, fontWeight: 700, lineHeight: 1 }}>{tc.icon}</span>
            <span className="mono" style={{ color: tc.color, fontSize: 11, letterSpacing: "0.12em" }}>{trend}</span>
          </div>
          <div className={`fc-source-badge ${base_aqi_source === "live_waqi" ? "live" : "est"}`}>
            <span className="fc-source-dot" />
            <span className="mono">{base_aqi_source === "live_waqi" ? "LIVE WAQI" : "SEASONAL ESTIMATE"}</span>
          </div>
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
          <defs>
            <clipPath id={clipId}>
              {/* Starts at width=0; JS animates to PW */}
              <rect ref={clipRectRef} x={ML} y={0} width={0} height={H} />
            </clipPath>
          </defs>

          {/* AQI zone bands — always visible, 7% opacity */}
          {AQI_ZONES.map(z => (
            <rect
              key={z.lo}
              x={ML} y={fy(z.hi)}
              width={PW}
              height={Math.max(0, fy(z.lo) - fy(z.hi))}
              fill={z.color}
              opacity="0.07"
            />
          ))}

          {/* Y gridlines + labels */}
          {Y_TICKS.map(v => (
            <g key={v}>
              <line
                x1={ML} y1={fy(v)} x2={ML + PW} y2={fy(v)}
                stroke="rgba(255,255,255,0.06)" strokeWidth="1"
              />
              <text
                x={ML - 6} y={fy(v) + 4}
                textAnchor="end"
                fontFamily="JetBrains Mono" fontSize="9"
                fill="rgba(255,255,255,0.28)"
              >
                {v}
              </text>
            </g>
          ))}

          {/* Confidence band — inside clip, revealed left-to-right */}
          <g clipPath={`url(#${clipId})`}>
            <path d={bandPath} fill={avgColor} opacity="0.18" />
          </g>

          {/* Colored line segments — inside clip */}
          <g clipPath={`url(#${clipId})`}>
            {lineSegs.map((seg, i) => (
              <path
                key={i}
                d={seg.d}
                fill="none"
                stroke={seg.color}
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                style={{ filter: `drop-shadow(0 0 4px ${seg.color}88)` }}
              />
            ))}
          </g>

          {/* X-axis labels: every 3 hours */}
          {[0, 3, 6, 9, 12, 15, 18, 21].map(i =>
            forecast[i] ? (
              <text
                key={i}
                x={fx(i)} y={MT + PH + 18}
                textAnchor="middle"
                fontFamily="JetBrains Mono" fontSize="9"
                fill="rgba(255,255,255,0.28)"
              >
                {forecast[i].hour}
              </text>
            ) : null
          )}

          {/* Peak marker — appears after clip animation */}
          {peakVis && (
            <g>
              <circle
                cx={fx(safeIdx)} cy={fy(peak.aqi)} r="6"
                fill="#ef3a4d" stroke="#0a0a0a" strokeWidth="2"
                style={{ filter: "drop-shadow(0 0 10px rgba(239,58,77,0.9))" }}
              />
              <text
                x={fx(safeIdx)} y={fy(peak.aqi) - 12}
                textAnchor={safeIdx > 20 ? "end" : safeIdx < 3 ? "start" : "middle"}
                fontFamily="JetBrains Mono" fontSize="10" fontWeight="700"
                fill="#ef3a4d"
              >
                ▲ {peak.aqi}
              </text>
            </g>
          )}

          {/* Invisible hover capture rect — transparent still receives pointer events */}
          <rect x={ML} y={MT} width={PW} height={PH} fill="transparent" />

          {/* Hover crosshair + tooltip */}
          {hoverIdx !== null && (() => {
            const d   = forecast[hoverIdx];
            if (!d) return null;
            const cx  = fx(hoverIdx);
            const cy  = fy(d.aqi);
            const col = aqiColor(d.aqi);
            const TW  = 138, TH = 80;
            const tx  = hoverIdx > 19 ? cx - TW - 10 : cx + 10;
            const ty  = Math.max(MT + 4, Math.min(MT + PH - TH - 4, cy - TH / 2));
            return (
              <g>
                <line x1={cx} y1={MT} x2={cx} y2={MT + PH}
                  stroke="rgba(255,255,255,0.15)" strokeWidth="1" strokeDasharray="3,3" />
                <circle cx={cx} cy={cy} r="4.5" fill={col} stroke="#0a0a0a" strokeWidth="2" />
                <rect x={tx} y={ty} width={TW} height={TH} rx="6"
                  fill="rgba(8,8,18,0.96)" stroke={col + "55"} strokeWidth="1" />
                <text x={tx + 10} y={ty + 22}
                  fontFamily="JetBrains Mono" fontSize="20" fontWeight="700" fill={col}>{d.aqi}</text>
                <text x={tx + 10} y={ty + 37}
                  fontFamily="JetBrains Mono" fontSize="8.5" fill="rgba(255,255,255,0.45)">{d.category.toUpperCase()}</text>
                <text x={tx + 10} y={ty + 51}
                  fontFamily="JetBrains Mono" fontSize="8.5" fill="rgba(255,107,0,0.75)">
                  {d.hour} · {d.date_label}
                </text>
                <text x={tx + 10} y={ty + 65}
                  fontFamily="JetBrains Mono" fontSize="8" fill="rgba(255,255,255,0.3)">
                  {d.lower}–{d.upper} · {d.confidence ?? "—"}% conf.
                </text>
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
            <div className="mono fc-stat-label">PEAK AQI</div>
            <div className="fc-stat-val" style={{ color: aqiColor(peak.aqi) }}>{peak.aqi}</div>
            <div className="mono fc-stat-sub">{peak.category.toUpperCase()} · {peak.hour}</div>
          </div>
        </div>
        <div className="fc-stat">
          <span className="fc-stat-dot" style={{ background: aqiColor(low.aqi) }} />
          <div>
            <div className="mono fc-stat-label">LOWEST AQI</div>
            <div className="fc-stat-val" style={{ color: aqiColor(low.aqi) }}>{low.aqi}</div>
            <div className="mono fc-stat-sub">{low.category.toUpperCase()} · {low.hour}</div>
          </div>
        </div>
        <div className="fc-stat">
          <span className="fc-stat-dot" style={{ background: "#FFB300" }} />
          <div>
            <div className="mono fc-stat-label">24H RANGE</div>
            <div className="fc-stat-val" style={{ color: "#FFB300", fontSize: 14 }}>{severity_forecast}</div>
            <div className="mono fc-stat-sub">NEXT 24 HOURS</div>
          </div>
        </div>
      </div>

      {/* ── Health recommendation */}
      <div className="fc-recommendation">
        <span className="fc-rec-icon">⚡</span>
        <p className="fc-rec-text">{recommendation}</p>
      </div>
    </div>
  );
}
