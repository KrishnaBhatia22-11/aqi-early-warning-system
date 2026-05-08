import { useState, useEffect, useRef, useCallback } from "react";
import { fetchForecast } from "../utils/api";

const BASE = "https://aqi-api-y2qs.onrender.com";

const ALL_CITIES = [
  "Delhi", "Mumbai", "Kolkata", "Chennai", "Bengaluru", "Hyderabad",
  "Ahmedabad", "Jaipur", "Lucknow", "Patna", "Chandigarh", "Amritsar",
  "Guwahati", "Bhopal", "Pune", "Nagpur", "Surat", "Kanpur", "Varanasi",
  "Coimbatore", "Kochi", "Thiruvananthapuram", "Visakhapatnam", "Ranchi",
  "Bhubaneswar", "Indore",
];

const CAT_COLORS = {
  Good: "#22c55e", Satisfactory: "#84cc16", Moderate: "#f59e0b",
  Poor: "#FF6B00", "Very Poor": "#ef3a4d", Severe: "#c2002a",
};
const CAT_ORDER = ["Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe"];

function catColor(cat) { return CAT_COLORS[cat] ?? "#FF6B00"; }

function catFromAqi(aqi) {
  if (aqi <= 50)  return "Good";
  if (aqi <= 100) return "Satisfactory";
  if (aqi <= 200) return "Moderate";
  if (aqi <= 300) return "Poor";
  if (aqi <= 400) return "Very Poor";
  return "Severe";
}

function healthCalc(aqi, hours = 2) {
  const pm25 = aqi * 0.6;
  const br = 0.83;
  return {
    cigs:     Math.round((aqi * hours) / (22 * 24) * 10) / 10,
    pm25Inh:  Math.round(pm25 * br * hours),
    whoPct:   Math.min(999, Math.round((pm25 * br * hours / (15 * 24)) * 100)),
    minsLost: Math.round(0.071 * (aqi / 100) * (hours / 24) * 10) / 10,
  };
}

function CityDropdown({ value, onChange, cities }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    if (!open) return;
    const onDown = e => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    const onKey  = e => { if (e.key === "Escape") setOpen(false); };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown",   onKey);
    return () => { document.removeEventListener("mousedown", onDown); document.removeEventListener("keydown", onKey); };
  }, [open]);

  return (
    <div className="cmp-dd-wrap" ref={ref}>
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

function CountUp({ value, decimals = 0, suffix = "" }) {
  const [cur, setCur] = useState(0);
  useEffect(() => {
    if (value == null || value === 0) { setCur(0); return; }
    const start = performance.now();
    let raf;
    const tick = ts => {
      const t = Math.min(1, (ts - start) / 900);
      setCur(value * (1 - Math.pow(1 - t, 3)));
      if (t < 1) raf = requestAnimationFrame(tick); else setCur(value);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [value]);
  return <>{decimals > 0 ? cur.toFixed(decimals) : Math.round(cur)}{suffix}</>;
}

function ForecastDualChart({ forecast1, forecast2, name1, name2 }) {
  const W = 800, H = 220;
  const PAD = { t: 20, r: 24, b: 38, l: 48 };
  const pw = W - PAD.l - PAD.r, ph = H - PAD.t - PAD.b;

  const all = [...forecast1, ...forecast2].map(d => d.aqi);
  const lo  = Math.max(0, Math.min(...all) - 20);
  const hi  = Math.max(...all) + 25;

  const sx = i => PAD.l + (i / (forecast1.length - 1)) * pw;
  const sy = v => PAD.t + ph - ((v - lo) / (hi - lo)) * ph;

  function bezierPath(data) {
    const pts = data.map((d, i) => [sx(i), sy(d.aqi)]);
    if (pts.length < 2) return "";
    let d = `M${pts[0][0]},${pts[0][1]}`;
    for (let i = 0; i < pts.length - 1; i++) {
      const cx = (pts[i][0] + pts[i + 1][0]) / 2;
      d += ` C${cx},${pts[i][1]} ${cx},${pts[i + 1][1]} ${pts[i + 1][0]},${pts[i + 1][1]}`;
    }
    return d;
  }

  // Y-axis ticks
  const yTicks = [lo, Math.round(lo + (hi - lo) * 0.5), Math.round(hi)];
  // X labels every 4 hours
  const xLabels = forecast1
    .map((d, i) => ({ d, i }))
    .filter(({ i }) => i % 4 === 0);

  // Find crossings
  const crossings = [];
  for (let i = 0; i < forecast1.length - 1; i++) {
    const d1 = forecast1[i].aqi   - forecast2[i].aqi;
    const d2 = forecast1[i+1].aqi - forecast2[i+1].aqi;
    if (d1 !== 0 && Math.sign(d1) !== Math.sign(d2)) {
      const t       = d1 / (d1 - d2);
      const crossV  = forecast1[i].aqi + t * (forecast1[i+1].aqi - forecast1[i].aqi);
      const rawLabel = forecast1[i].hour_label ?? `${forecast1[i].hour}:00`;
      crossings.push({ x: sx(i + t), y: sy(crossV), label: rawLabel, d1 });
    }
  }

  return (
    <div className="cmp-chart-wrap">
      <div className="cmp-chart-legend">
        <span className="cmp-legend-item">
          <span className="cmp-legend-line" style={{ background: "#FF6B00" }} />
          {name1}
        </span>
        <span className="cmp-legend-item">
          <span className="cmp-legend-line" style={{ background: "#38bdf8" }} />
          {name2}
        </span>
      </div>

      <svg viewBox={`0 0 ${W} ${H}`} className="cmp-fc-svg">
        {/* Grid lines */}
        {yTicks.map(y => (
          <g key={y}>
            <line
              x1={PAD.l} y1={sy(y)} x2={W - PAD.r} y2={sy(y)}
              stroke="rgba(255,255,255,0.06)" strokeWidth={1}
            />
            <text
              x={PAD.l - 6} y={sy(y) + 4}
              textAnchor="end" fill="rgba(255,255,255,0.3)"
              fontSize={9} fontFamily="JetBrains Mono,monospace"
            >
              {y}
            </text>
          </g>
        ))}

        {/* X labels */}
        {xLabels.map(({ d, i }) => {
          const lbl = d.hour_label ? d.hour_label.replace(":00", "") : `${d.hour}h`;
          return (
            <text key={i} x={sx(i)} y={H - 6}
              textAnchor="middle" fill="rgba(255,255,255,0.3)"
              fontSize={9} fontFamily="JetBrains Mono,monospace"
            >
              {lbl}
            </text>
          );
        })}

        {/* City 2 line — cyan */}
        <path d={bezierPath(forecast2)} fill="none" stroke="#38bdf8" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
        {/* City 1 line — orange */}
        <path d={bezierPath(forecast1)} fill="none" stroke="#FF6B00" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round" />

        {/* Crossing markers */}
        {crossings.slice(0, 2).map((c, i) => (
          <g key={i}>
            <circle cx={c.x} cy={c.y} r={5} fill="#fff" stroke="#0a0a14" strokeWidth={2} />
            <text
              x={c.x} y={Math.max(PAD.t + 10, c.y - 10)}
              textAnchor="middle" fill="rgba(255,255,255,0.45)"
              fontSize={9} fontFamily="JetBrains Mono,monospace"
            >
              {c.d1 > 0 ? name2 : name1} lower at {c.label}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}

export default function CityComparisonPage({ cities = [] }) {
  const [city1, setCity1]   = useState("Delhi");
  const [city2, setCity2]   = useState("Mumbai");
  const [data,  setData]    = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]   = useState(null);
  const verdictRef  = useRef(null);
  const shareCardRef = useRef(null);

  const cityList = cities.length > 0
    ? [...new Set([...cities.map(c => c.name), ...ALL_CITIES])]
    : ALL_CITIES;

  const doFetch = useCallback(async (c1, c2, passedAqi1 = null, passedAqi2 = null) => {
    if (c1 === c2) return;
    setLoading(true);
    setError(null);
    try {
      let url = `${BASE}/api/v1/compare?city1=${encodeURIComponent(c1)}&city2=${encodeURIComponent(c2)}`;
      if (passedAqi1 != null && passedAqi2 != null) {
        url += `&aqi1=${passedAqi1}&aqi2=${passedAqi2}`;
      }
      const [compare, fc1, fc2] = await Promise.all([
        fetch(url).then(r => { if (!r.ok) throw new Error("Compare API failed"); return r.json(); }),
        fetchForecast(c1).catch(() => null),
        fetchForecast(c2).catch(() => null),
      ]);
      setData({
        compare,
        forecast1: fc1?.forecast ?? [],
        forecast2: fc2?.forecast ?? [],
      });
    } catch (e) {
      setError(e.message || "Failed to compare cities");
    } finally {
      setLoading(false);
    }
  }, []);

  // Auto-compare on mount (no AQI to pass yet)
  useEffect(() => { doFetch("Delhi", "Mumbai"); }, [doFetch]);

  const handleCompare = () => {
    const liveAqi1 = getLiveAqi(city1);
    const liveAqi2 = getLiveAqi(city2);
    doFetch(city1, city2, liveAqi1, liveAqi2);
  };

  const handleSwap = () => {
    const newC1Aqi = getLiveAqi(city2);
    const newC2Aqi = getLiveAqi(city1);
    setCity1(city2);
    setCity2(city1);
    doFetch(city2, city1, newC1Aqi, newC2Aqi);
  };

  // Scroll into view after results load
  useEffect(() => {
    if (data) setTimeout(() => verdictRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
  }, [data]);

  const handleShare = async () => {
    if (!shareCardRef.current || !data) return;
    try {
      const { default: html2canvas } = await import("html2canvas");
      const canvas = await html2canvas(shareCardRef.current, {
        scale: 2, backgroundColor: "#0a0a14", logging: false, useCORS: true,
      });
      const a = document.createElement("a");
      const n1 = (data.compare?.city1?.name ?? city1).toLowerCase();
      const n2 = (data.compare?.city2?.name ?? city2).toLowerCase();
      a.download = `aqi-compare-${n1}-vs-${n2}.png`;
      a.href = canvas.toDataURL("image/png");
      a.click();
    } catch { /* share is non-critical */ }
  };

  // Derived
  const c1d = data?.compare?.city1;
  const c2d = data?.compare?.city2;
  const diff       = data?.compare?.difference ?? 0;
  const insight    = data?.compare?.insight ?? "";
  const saferCity  = data?.compare?.safer_city ?? "";
  const cigDiff    = data?.compare?.cigarette_difference ?? "";

  const bannerGrad = diff > 200
    ? "linear-gradient(135deg, rgba(194,0,42,0.28) 0%, rgba(239,58,77,0.12) 100%)"
    : diff > 100
    ? "linear-gradient(135deg, rgba(255,107,0,0.28) 0%, rgba(239,154,0,0.12) 100%)"
    : "linear-gradient(135deg, rgba(245,158,11,0.22) 0%, rgba(234,179,8,0.10) 100%)";

  const getMetrics = cd => {
    if (!cd) return null;
    const aqi = cd.aqi;
    return {
      aqi,
      category:    cd.category ?? catFromAqi(aqi),
      pm25:        Math.round(aqi * 0.6),
      pm10:        Math.round(aqi * 1.2),
      no2:         Math.round(aqi * 0.3),
      population:  cd.population ?? 0,
      cigsPerHour: Math.round((aqi / (22 * 24)) * 10) / 10,
    };
  };

  const m1 = getMetrics(c1d);
  const m2 = getMetrics(c2d);
  const h1 = c1d ? healthCalc(c1d.aqi) : null;
  const h2 = c2d ? healthCalc(c2d.aqi) : null;

  // For diff strip: always show savings from worse → better
  const worseIsCity1 = c1d && c2d && c1d.aqi >= c2d.aqi;
  const worseCity  = worseIsCity1 ? c1d : c2d;
  const betterCity = worseIsCity1 ? c2d : c1d;
  const hWorse  = worseIsCity1 ? h1 : h2;
  const hBetter = worseIsCity1 ? h2 : h1;

  // Live AQI badge helper
  const getLiveAqi = (name) => {
    const fromProp = cities.find(c => c.name?.toLowerCase() === name.toLowerCase())?.aqi ?? null;
    const fromData = data?.compare?.city1?.name?.toLowerCase() === name.toLowerCase()
      ? data.compare.city1.aqi
      : data?.compare?.city2?.name?.toLowerCase() === name.toLowerCase()
      ? data.compare.city2.aqi
      : null;
    return fromData ?? fromProp;
  };

  const METRIC_ROWS = m1 && m2 ? [
    {
      key: "aqi", label: "AQI SCORE", lowerBetter: true, delay: 0,
      v1: m1.aqi, v2: m2.aqi,
      render1: () => <span className="cmp-aqi-giant" style={{ color: catColor(m1.category) }}><CountUp value={m1.aqi} /></span>,
      render2: () => <span className="cmp-aqi-giant" style={{ color: catColor(m2.category) }}><CountUp value={m2.aqi} /></span>,
    },
    {
      key: "cat", label: "CATEGORY", lowerBetter: true, delay: 80,
      v1: CAT_ORDER.indexOf(m1.category), v2: CAT_ORDER.indexOf(m2.category),
      render1: () => <span className="cmp-cat-pill" style={{ background: catColor(m1.category) + "22", color: catColor(m1.category), border: `1px solid ${catColor(m1.category)}55` }}>{m1.category}</span>,
      render2: () => <span className="cmp-cat-pill" style={{ background: catColor(m2.category) + "22", color: catColor(m2.category), border: `1px solid ${catColor(m2.category)}55` }}>{m2.category}</span>,
    },
    {
      key: "pm25", label: "PM2.5 µg/m³", lowerBetter: true, delay: 160,
      v1: m1.pm25, v2: m2.pm25,
      render1: () => <CountUp value={m1.pm25} />,
      render2: () => <CountUp value={m2.pm25} />,
    },
    {
      key: "pm10", label: "PM10 µg/m³", lowerBetter: true, delay: 240,
      v1: m1.pm10, v2: m2.pm10,
      render1: () => <CountUp value={m1.pm10} />,
      render2: () => <CountUp value={m2.pm10} />,
    },
    {
      key: "no2", label: "NO₂ µg/m³", lowerBetter: true, delay: 320,
      v1: m1.no2, v2: m2.no2,
      render1: () => <CountUp value={m1.no2} />,
      render2: () => <CountUp value={m2.no2} />,
    },
    {
      key: "pop", label: "POPULATION", lowerBetter: false, delay: 400,
      v1: m1.population, v2: m2.population,
      render1: () => m1.population > 0 ? `${(m1.population / 1e6).toFixed(1)}M people` : "—",
      render2: () => m2.population > 0 ? `${(m2.population / 1e6).toFixed(1)}M people` : "—",
    },
    {
      key: "cigs", label: "CIGARETTES/HR", lowerBetter: true, delay: 480,
      v1: m1.cigsPerHour, v2: m2.cigsPerHour,
      danger: m1.cigsPerHour > 1 || m2.cigsPerHour > 1,
      render1: () => <><CountUp value={m1.cigsPerHour} decimals={1} /> 🚬</>,
      render2: () => <><CountUp value={m2.cigsPerHour} decimals={1} /> 🚬</>,
    },
  ] : [];

  return (
    <div className="cmp-page">

      {/* ══ HERO ══════════════════════════════════════════════════ */}
      <div className="cmp-hero">
        <span className="mono cmp-eyebrow">CITY COMPARISON</span>
        <h1 className="display cmp-title">How does your city stack up?</h1>
        <p className="cmp-subtitle">
          Compare air quality, health impact and forecast between any two Indian cities.
        </p>
      </div>

      {/* ══ SELECTOR ══════════════════════════════════════════════ */}
      <section className="cmp-selector-section">
        <div className="cmp-selector-grid">

          {/* City 1 card */}
          <div className="cmp-city-card glass-strong">
            <span className="mono cmp-city-card-label">CITY 1</span>
            <CityDropdown value={city1} onChange={setCity1} cities={cityList} />
            {(() => {
              const aqi = getLiveAqi(city1);
              if (!aqi) return null;
              const cat = catFromAqi(aqi);
              return (
                <div className="cmp-live-badge">
                  <span className="cmp-live-dot" style={{ background: catColor(cat) }} />
                  <span className="mono cmp-live-text" style={{ color: catColor(cat) }}>LIVE {aqi}</span>
                  <span className="cmp-live-cat" style={{ color: catColor(cat) }}>{cat}</span>
                </div>
              );
            })()}
          </div>

          {/* VS + Swap */}
          <div className="cmp-vs-wrap">
            <div className="cmp-vs-badge">VS</div>
            <button className="cmp-swap-btn" onClick={handleSwap} title="Swap cities" aria-label="Swap city 1 and city 2">
              ⇄
            </button>
          </div>

          {/* City 2 card */}
          <div className="cmp-city-card glass-strong">
            <span className="mono cmp-city-card-label">CITY 2</span>
            <CityDropdown value={city2} onChange={setCity2} cities={cityList} />
            {(() => {
              const aqi = getLiveAqi(city2);
              if (!aqi) return null;
              const cat = catFromAqi(aqi);
              return (
                <div className="cmp-live-badge">
                  <span className="cmp-live-dot" style={{ background: catColor(cat) }} />
                  <span className="mono cmp-live-text" style={{ color: catColor(cat) }}>LIVE {aqi}</span>
                  <span className="cmp-live-cat" style={{ color: catColor(cat) }}>{cat}</span>
                </div>
              );
            })()}
          </div>
        </div>

        <button
          className={`cmp-compare-btn${loading ? " loading" : ""}`}
          onClick={handleCompare}
          disabled={loading || city1 === city2}
        >
          {loading
            ? <><span className="cmp-spin" />LOADING COMPARISON…</>
            : "COMPARE CITIES"
          }
        </button>
        {city1 === city2 && (
          <p className="mono cmp-same-warn">Select two different cities to compare</p>
        )}
      </section>

      {/* ══ LOADING SKELETON ══════════════════════════════════════ */}
      {loading && (
        <div className="cmp-skel-wrap">
          <div className="cmp-skel-banner fc-skel-line" style={{ height: 110, borderRadius: 14 }} />
          {[0, 1, 2, 3, 4].map(i => (
            <div key={i} className="cmp-skel-row fc-skel-line" style={{ animationDelay: `${i * 60}ms` }} />
          ))}
        </div>
      )}

      {/* ══ ERROR ═════════════════════════════════════════════════ */}
      {error && !loading && (
        <div className="cmp-error-wrap">
          <span className="mono cmp-error-text">⚠ {error}</span>
          <button className="cmp-error-retry" onClick={handleCompare}>RETRY</button>
        </div>
      )}

      {/* ══ RESULTS ═══════════════════════════════════════════════ */}
      {data && !loading && (
        <>
          {/* ── SECTION 2 — VERDICT BANNER ────────────────────── */}
          <section className="cmp-verdict-section" ref={verdictRef}>
            <div className="cmp-verdict-banner" style={{ background: bannerGrad }}>
              <div className="cmp-verdict-icon" aria-hidden="true">
                {diff > 200 ? "⚠️" : diff > 100 ? "⚡" : "ℹ️"}
              </div>
              <div className="cmp-verdict-body">
                <p className="cmp-verdict-text">{insight}</p>
                <p className="cmp-verdict-sub">{cigDiff}</p>
              </div>
              {saferCity && (
                <div className="cmp-safer-badge">✓ {saferCity} is safer today</div>
              )}
            </div>
          </section>

          {/* ── SECTION 3 — METRICS GRID ──────────────────────── */}
          {m1 && m2 && (
            <section className="cmp-metrics-section">
              <div className="cmp-metrics-header">
                <div className="cmp-metrics-hcity" style={{ color: catColor(m1.category) }}>
                  {c1d.name}
                </div>
                <div />
                <div className="cmp-metrics-hcity cmp-metrics-hcity-right" style={{ color: catColor(m2.category) }}>
                  {c2d.name}
                </div>
              </div>

              {METRIC_ROWS.map(row => {
                const equal   = row.v1 === row.v2;
                const win1    = !equal && (row.lowerBetter ? row.v1 < row.v2 : row.v1 > row.v2);
                const win2    = !equal && (row.lowerBetter ? row.v2 < row.v1 : row.v2 > row.v1);
                return (
                  <div
                    key={row.key}
                    className={`cmp-metric-row${row.danger ? " cmp-row-danger" : ""}`}
                    style={{ animationDelay: `${row.delay}ms` }}
                  >
                    <div className={`cmp-metric-cell cmp-cell-left${win1 ? " cmp-win" : win2 ? " cmp-lose" : ""}`}>
                      {win1 && <span className="cmp-crown" aria-label="Better">👑</span>}
                      <span className="cmp-metric-val">{row.render1()}</span>
                    </div>
                    <div className="cmp-metric-lbl mono">{row.label}</div>
                    <div className={`cmp-metric-cell cmp-cell-right${win2 ? " cmp-win" : win1 ? " cmp-lose" : ""}`}>
                      <span className="cmp-metric-val">{row.render2()}</span>
                      {win2 && <span className="cmp-crown" aria-label="Better">👑</span>}
                    </div>
                  </div>
                );
              })}
            </section>
          )}

          {/* ── SECTION 4 — FORECAST CHART ────────────────────── */}
          {data.forecast1.length > 0 && data.forecast2.length > 0 && (
            <section className="cmp-forecast-section">
              <div className="cmp-sec-header">
                <h2 className="cmp-sec-title">Next 24 Hours — How will it change?</h2>
                <p className="mono cmp-sec-sub">Based on current readings and diurnal patterns</p>
              </div>
              <div className="glass-strong cmp-fc-card">
                <ForecastDualChart
                  forecast1={data.forecast1}
                  forecast2={data.forecast2}
                  name1={c1d?.name ?? city1}
                  name2={c2d?.name ?? city2}
                />
              </div>
            </section>
          )}

          {/* ── SECTION 5 — HEALTH IMPACT ─────────────────────── */}
          {h1 && h2 && worseCity && betterCity && (
            <section className="cmp-health-section">
              <div className="cmp-sec-header">
                <h2 className="cmp-sec-title">What does the difference cost your body?</h2>
                <p className="mono cmp-sec-sub">Calculated for 2 hours outside · adult breathing rate</p>
              </div>
              <div className="cmp-health-grid">
                {/* City 1 card */}
                <div className="glass-strong cmp-health-card">
                  <div className="cmp-health-city" style={{ color: catColor(m1.category) }}>{c1d.name}</div>
                  {[
                    { icon: "🚬", label: "Cigarettes (2h)", value: h1.cigs.toFixed(1) },
                    { icon: "🛡️", label: "WHO limit",       value: `${h1.whoPct}%`     },
                    { icon: "🫁", label: "PM2.5 inhaled",   value: `${h1.pm25Inh}µg`   },
                    { icon: "⏳", label: "Life mins lost",  value: `${h1.minsLost}min`  },
                  ].map(item => (
                    <div key={item.label} className="cmp-hrow">
                      <span className="cmp-hrow-icon" aria-hidden="true">{item.icon}</span>
                      <span className="mono cmp-hrow-label">{item.label}</span>
                      <span className="cmp-hrow-val">{item.value}</span>
                    </div>
                  ))}
                  <div className="cmp-risk-pill" style={{ background: catColor(m1.category) + "22", color: catColor(m1.category), border: `1px solid ${catColor(m1.category)}44` }}>
                    {m1.category}
                  </div>
                </div>

                {/* Savings strip */}
                <div className="cmp-diff-strip">
                  <div className="mono cmp-diff-header">
                    SWITCH FROM {worseCity.name.toUpperCase()} TO {betterCity.name.toUpperCase()} — SAVE:
                  </div>
                  {[
                    { val: Math.abs(hWorse.cigs - hBetter.cigs).toFixed(1), lbl: "cigarettes per 2 hours" },
                    { val: Math.abs(hWorse.whoPct - hBetter.whoPct),         lbl: "% of WHO daily limit"  },
                    { val: Math.abs(hWorse.pm25Inh - hBetter.pm25Inh),       lbl: "µg of PM2.5 inhaled"   },
                    { val: Math.abs(hWorse.minsLost - hBetter.minsLost).toFixed(1), lbl: "minutes of healthy life" },
                  ].map(item => (
                    <div key={item.lbl} className="cmp-diff-row">
                      <span className="cmp-diff-val">{item.val}</span>
                      <span className="cmp-diff-lbl">{item.lbl}</span>
                    </div>
                  ))}
                </div>

                {/* City 2 card */}
                <div className="glass-strong cmp-health-card">
                  <div className="cmp-health-city" style={{ color: catColor(m2.category) }}>{c2d.name}</div>
                  {[
                    { icon: "🚬", label: "Cigarettes (2h)", value: h2.cigs.toFixed(1) },
                    { icon: "🛡️", label: "WHO limit",       value: `${h2.whoPct}%`     },
                    { icon: "🫁", label: "PM2.5 inhaled",   value: `${h2.pm25Inh}µg`   },
                    { icon: "⏳", label: "Life mins lost",  value: `${h2.minsLost}min`  },
                  ].map(item => (
                    <div key={item.label} className="cmp-hrow">
                      <span className="cmp-hrow-icon" aria-hidden="true">{item.icon}</span>
                      <span className="mono cmp-hrow-label">{item.label}</span>
                      <span className="cmp-hrow-val">{item.value}</span>
                    </div>
                  ))}
                  <div className="cmp-risk-pill" style={{ background: catColor(m2.category) + "22", color: catColor(m2.category), border: `1px solid ${catColor(m2.category)}44` }}>
                    {m2.category}
                  </div>
                </div>
              </div>
            </section>
          )}

          {/* ── SECTION 6 — SHARE ─────────────────────────────── */}
          <section className="cmp-share-section">
            <button className="cmp-share-btn" onClick={handleShare}>
              ↗ Share this comparison
            </button>
          </section>
        </>
      )}

      {/* ══ HIDDEN SHARE CARD (html2canvas target) ════════════════ */}
      {data && c1d && c2d && m1 && m2 && (
        <div
          ref={shareCardRef}
          style={{
            position: "fixed", left: "-9999px", top: 0,
            width: "800px", height: "420px",
            background: "#0a0a14",
            padding: "40px 48px",
            fontFamily: "'Courier New', Courier, monospace",
            color: "#ffffff",
            boxSizing: "border-box",
            overflow: "hidden",
          }}
        >
          {/* Header */}
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 24 }}>
            <div style={{ fontSize: 17, fontWeight: 700, letterSpacing: "0.08em" }}>
              AQI<span style={{ color: "#FF6B00" }}>⚡</span>
              <span style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", marginLeft: 10, letterSpacing: "0.12em" }}>
                CITY COMPARISON
              </span>
            </div>
            <div style={{ fontSize: 10, color: "rgba(255,255,255,0.3)", letterSpacing: "0.1em", alignSelf: "flex-end" }}>
              aqi-early-warning-system.vercel.app
            </div>
          </div>

          {/* Cities */}
          <div style={{ display: "flex", gap: 56, alignItems: "flex-end", marginBottom: 28 }}>
            <div>
              <div style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", letterSpacing: "0.18em", marginBottom: 6 }}>
                {c1d.name.toUpperCase()}
              </div>
              <div style={{ fontSize: 72, fontWeight: 700, letterSpacing: "-0.04em", lineHeight: 1, color: catColor(m1.category) }}>
                {c1d.aqi}
              </div>
              <div style={{ fontSize: 11, color: catColor(m1.category), letterSpacing: "0.12em", marginTop: 5 }}>
                {m1.category.toUpperCase()}
              </div>
            </div>
            <div style={{ fontSize: 28, color: "rgba(255,255,255,0.18)", fontWeight: 700, marginBottom: 8 }}>VS</div>
            <div>
              <div style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", letterSpacing: "0.18em", marginBottom: 6 }}>
                {c2d.name.toUpperCase()}
              </div>
              <div style={{ fontSize: 72, fontWeight: 700, letterSpacing: "-0.04em", lineHeight: 1, color: catColor(m2.category) }}>
                {c2d.aqi}
              </div>
              <div style={{ fontSize: 11, color: catColor(m2.category), letterSpacing: "0.12em", marginTop: 5 }}>
                {m2.category.toUpperCase()}
              </div>
            </div>
          </div>

          {/* Insight */}
          <div style={{ fontSize: 18, fontWeight: 600, color: "#fff", marginBottom: 10, lineHeight: 1.3 }}>
            {insight}
          </div>
          <div style={{ fontSize: 12, color: "rgba(255,255,255,0.45)", marginBottom: 20 }}>
            {cigDiff}
          </div>

          {/* Safer badge */}
          {saferCity && (
            <div style={{
              display: "inline-block",
              background: "rgba(34,197,94,0.12)",
              border: "1px solid rgba(34,197,94,0.4)",
              color: "#22c55e",
              fontSize: 11, padding: "5px 14px",
              borderRadius: 999, letterSpacing: "0.1em",
            }}>
              ✓ {saferCity} is safer today
            </div>
          )}
        </div>
      )}
    </div>
  );
}
