import { useState, useMemo } from "react";
import SparkLine from "../components/SparkLine";
import { aqiCategory } from "../utils/aqiCategory";
import { TREND_7D, CALENDAR_30D, POLLUTANT_BREAKDOWN } from "../data/index";

const HOURS = Array.from({ length: 24 }, (_, i) => `${i}:00`);

function DonutChart({ data, total }) {
  const cx = 80, cy = 80, r = 60;
  let offset = -90;
  return (
    <svg viewBox="0 0 160 160" width="160" height="160">
      {data.map((d, i) => {
        const pct = d.value / total;
        const deg = pct * 360;
        const start = offset;
        offset += deg;
        const r1 = (start * Math.PI) / 180;
        const r2 = ((start + deg) * Math.PI) / 180;
        const x1 = cx + r * Math.cos(r1), y1 = cy + r * Math.sin(r1);
        const x2 = cx + r * Math.cos(r2), y2 = cy + r * Math.sin(r2);
        const large = deg > 180 ? 1 : 0;
        return (
          <path
            key={d.name}
            d={`M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2} Z`}
            fill={d.color}
            opacity="0.85"
            stroke="#0a0a0a"
            strokeWidth="1.5"
          />
        );
      })}
      <circle cx={cx} cy={cy} r={r * 0.55} fill="#0a0a0a" />
      <text x={cx} y={cy - 4} textAnchor="middle" fill="#fff" fontFamily="Space Grotesk" fontSize="18" fontWeight="700">{total}</text>
      <text x={cx} y={cy + 14} textAnchor="middle" fill="rgba(255,255,255,0.5)" fontFamily="JetBrains Mono" fontSize="8">AQI</text>
    </svg>
  );
}

function TrendChart({ values, color }) {
  const w = 400, h = 120;
  const min = Math.min(...values), max = Math.max(...values);
  const pts = values.map((v, i) => [
    (i / (values.length - 1)) * w,
    h - ((v - min) / (max - min || 1)) * (h - 16) - 8,
  ]);
  const d = pts.map((p, i) => `${i === 0 ? "M" : "L"}${p[0]} ${p[1]}`).join(" ");
  return (
    <svg viewBox={`0 0 ${w} ${h}`} style={{ width: "100%", height: 120 }} preserveAspectRatio="none">
      <defs>
        <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.4" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={`${d} L ${w} ${h} L 0 ${h} Z`} fill="url(#trendFill)" />
      <path d={d} fill="none" stroke={color} strokeWidth="2" style={{ filter: `drop-shadow(0 0 6px ${color})` }} />
      {pts.map((p, i) => (
        <circle key={i} cx={p[0]} cy={p[1]} r={i === pts.length - 1 ? 5 : 2.5} fill={color} opacity={i === pts.length - 1 ? 1 : 0.5} />
      ))}
    </svg>
  );
}

function CalendarHeatmap({ data }) {
  return (
    <div className="cal-grid">
      {data.map((v, i) => {
        const cat = aqiCategory(v);
        return (
          <div
            key={i}
            className="cal-cell"
            style={{ background: cat.color + "55", border: `1px solid ${cat.color}44` }}
            title={`Day ${i + 1}: AQI ${v}`}
          >
            <span className="mono" style={{ fontSize: 8, color: cat.color }}>{v}</span>
          </div>
        );
      })}
    </div>
  );
}

export default function DashboardPage({ cities, initialCity }) {
  const [selectedCity, setSelectedCity] = useState(initialCity || "Delhi");

  const cityData = useMemo(() => {
    return cities.find(c => c.name === selectedCity) || cities[0] || { name: "Delhi", aqi: 187, pollutant: "PM2.5" };
  }, [cities, selectedCity]);

  const cat = aqiCategory(cityData?.aqi ?? 187);
  const trend = TREND_7D.map(v => Math.max(20, v + ((cityData?.aqi ?? 187) - 200)));
  const forecast72h = Array.from({ length: 24 }, (_, i) => {
    const base = cityData?.aqi ?? 187;
    return Math.max(20, Math.round(base + Math.sin(i * 0.4) * 30 + (Math.random() - 0.5) * 20));
  });

  const donutData = POLLUTANT_BREAKDOWN.map(p => ({ ...p }));
  const donutTotal = cityData?.aqi ?? 187;

  const cityNames = cities.length ? cities.map(c => c.name) : ["Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata"];

  return (
    <div className="dashboard-page">
      <div className="dashboard-hero">
        <div className="mono dashboard-eyebrow">CITY INTELLIGENCE DASHBOARD</div>
        <h1 className="display dashboard-title">Air Quality Analytics</h1>
      </div>

      <div className="dash-city-select-wrap">
        <div className="glass dash-city-bar">
          <span className="mono dash-city-label">SELECT CITY</span>
          <div className="dash-city-pills">
            {cityNames.slice(0, 10).map(name => {
              const c = cities.find(x => x.name === name);
              const cc = aqiCategory(c?.aqi ?? 100);
              return (
                <button
                  key={name}
                  className={`city-pill ${selectedCity === name ? "active" : ""}`}
                  style={selectedCity === name ? { borderColor: cc.color, color: cc.color } : {}}
                  onClick={() => setSelectedCity(name)}
                >
                  {name}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <div className="dash-grid">
        <div className="dash-card glass-strong dash-trend">
          <div className="panel-header">
            <span className="mono panel-title">7-DAY TREND · {selectedCity.toUpperCase()}</span>
            <span className="mono panel-meta" style={{ color: cat.color }}>AQI {cityData?.aqi}</span>
          </div>
          <TrendChart values={trend} color={cat.color} />
          <div className="dash-trend-meta mono">
            {["MON","TUE","WED","THU","FRI","SAT","SUN"].map((d, i) => (
              <span key={d}>{d}</span>
            ))}
          </div>
        </div>

        <div className="dash-card glass-strong dash-donut">
          <div className="panel-header">
            <span className="mono panel-title">POLLUTANT BREAKDOWN</span>
          </div>
          <div className="donut-row">
            <DonutChart data={donutData} total={donutTotal} />
            <div className="donut-legend">
              {donutData.map(d => (
                <div className="donut-leg-item" key={d.name}>
                  <span className="donut-leg-dot" style={{ background: d.color }} />
                  <span className="mono donut-leg-name">{d.name}</span>
                  <span className="mono donut-leg-pct">{d.pct}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="dash-card glass-strong dash-calendar">
          <div className="panel-header">
            <span className="mono panel-title">30-DAY AQI CALENDAR</span>
            <span className="mono panel-meta">MAY 2026</span>
          </div>
          <CalendarHeatmap data={CALENDAR_30D} />
        </div>

        <div className="dash-card glass-strong dash-forecast">
          <div className="panel-header">
            <span className="mono panel-title">72H FORECAST</span>
            <span className="mono panel-meta">NEXT 24 READINGS</span>
          </div>
          <TrendChart values={forecast72h} color="#FFB300" />
          <div className="mono dash-forecast-badge">
            PEAK: <span style={{ color: "#ef3a4d" }}>{Math.max(...forecast72h)}</span>
            &nbsp;&nbsp;LOW: <span style={{ color: "#34d27a" }}>{Math.min(...forecast72h)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
