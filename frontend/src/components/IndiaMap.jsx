import { useState } from "react";
import { aqiCategory } from "../utils/aqiCategory";
import { INDIA_PATH } from "../data/index";

const INDIA_GRID = [
  "M 220 180 L 320 220 L 420 200",
  "M 200 280 L 320 300 L 440 280",
  "M 200 360 L 300 380 L 410 370",
  "M 220 450 L 310 460",
  "M 250 540 L 310 560",
];

export default function IndiaMap({ cities, selected, onSelect }) {
  const [hover, setHover] = useState(null);

  return (
    <div className="india-map-wrap">
      <svg viewBox="0 0 600 720" preserveAspectRatio="xMidYMid meet" className="india-map">
        <defs>
          <radialGradient id="mapGlow" cx="0.5" cy="0.4" r="0.7">
            <stop offset="0%"   stopColor="rgba(255,107,0,0.18)" />
            <stop offset="60%"  stopColor="rgba(255,107,0,0.04)" />
            <stop offset="100%" stopColor="rgba(255,107,0,0)"    />
          </radialGradient>
          <filter id="dotGlow" x="-200%" y="-200%" width="500%" height="500%">
            <feGaussianBlur stdDeviation="6" />
          </filter>
          <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">
            <path d="M 24 0 L 0 0 0 24" fill="none" stroke="rgba(255,107,0,0.04)" strokeWidth="1"/>
          </pattern>
          <linearGradient id="landFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%"   stopColor="rgba(255,255,255,0.04)" />
            <stop offset="100%" stopColor="rgba(255,107,0,0.06)"   />
          </linearGradient>
        </defs>

        <rect width="600" height="720" fill="url(#grid)" />
        <rect width="600" height="720" fill="url(#mapGlow)" />

        <g stroke="rgba(255,107,0,0.10)" strokeWidth="1" strokeDasharray="2 6">
          <line x1="0" y1="360" x2="600" y2="360" />
          <line x1="300" y1="0"  x2="300" y2="720" />
        </g>

        <path
          d={INDIA_PATH}
          fill="url(#landFill)"
          stroke="rgba(255,107,0,0.45)"
          strokeWidth="1.2"
          style={{ filter: "drop-shadow(0 0 24px rgba(255,107,0,0.18))" }}
        />

        <g stroke="rgba(255,107,0,0.10)" strokeWidth="0.8" fill="none">
          {INDIA_GRID.map((d, i) => <path key={i} d={d} />)}
        </g>

        <g fontFamily="JetBrains Mono, monospace" fontSize="9" fill="rgba(255,107,0,0.4)">
          <text x="14" y="18">28°N</text>
          <text x="14" y="370">20°N</text>
          <text x="14" y="700">8°N</text>
          <text x="568" y="710">92°E</text>
          <text x="280" y="710">78°E</text>
          <text x="100" y="710">68°E</text>
        </g>

        {cities.map((c, i) => {
          const cat = aqiCategory(c.aqi);
          const isSel = selected?.name === c.name;
          const isHov = hover?.name === c.name;
          const r = isSel ? 8 : isHov ? 7 : 5;
          return (
            <g
              key={c.name}
              transform={`translate(${c.x},${c.y})`}
              style={{ cursor: "pointer" }}
              onMouseEnter={() => setHover(c)}
              onMouseLeave={() => setHover(null)}
              onClick={() => onSelect(c)}
            >
              <circle r={r * 3.5} fill={cat.color} opacity="0.18">
                <animate attributeName="r" values={`${r*1.5};${r*4};${r*1.5}`} dur={`${1.6 + (i%3)*0.4}s`} repeatCount="indefinite"/>
                <animate attributeName="opacity" values="0.35;0;0.35" dur={`${1.6 + (i%3)*0.4}s`} repeatCount="indefinite"/>
              </circle>
              <circle r={r*2} fill={cat.color} opacity="0.35" filter="url(#dotGlow)" />
              <circle r={r} fill={cat.color} stroke="#0a0a0a" strokeWidth="1.5" />
              {isSel && (
                <circle r={r + 6} fill="none" stroke={cat.color} strokeWidth="1.2" opacity="0.8">
                  <animate attributeName="r" values={`${r+4};${r+10};${r+4}`} dur="2s" repeatCount="indefinite"/>
                </circle>
              )}
            </g>
          );
        })}

        {hover && (
          <g transform={`translate(${hover.x + 12},${hover.y - 12})`} pointerEvents="none">
            <rect x="0" y="-14" width={hover.name.length * 7 + 50} height="22" rx="6" fill="rgba(15,12,10,0.95)" stroke="rgba(255,107,0,0.5)" strokeWidth="1"/>
            <text x="8" y="1" fontFamily="JetBrains Mono, monospace" fontSize="10" fill="#f3f1ee">
              {hover.name.toUpperCase()}
              <tspan fill={aqiCategory(hover.aqi).color} dx="8">{hover.aqi}</tspan>
            </text>
          </g>
        )}
      </svg>

      <div className="map-legend glass">
        <div className="legend-title">AQI SEVERITY</div>
        {[
          { c:"#34d27a", l:"Good",         r:"0–50"    },
          { c:"#f5d142", l:"Satisfactory", r:"51–100"  },
          { c:"#FFB300", l:"Moderate",     r:"101–200" },
          { c:"#FF6B00", l:"Poor",         r:"201–300" },
          { c:"#ef3a4d", l:"Severe",       r:"301–400" },
          { c:"#c2002a", l:"Hazardous",    r:"400+"    },
        ].map(s => (
          <div key={s.l} className="legend-row">
            <span className="legend-dot" style={{ background: s.c, boxShadow: `0 0 10px ${s.c}` }}></span>
            <span className="legend-l">{s.l}</span>
            <span className="legend-r">{s.r}</span>
          </div>
        ))}
      </div>

      <div className="map-corners">
        <span className="c tl"></span><span className="c tr"></span>
        <span className="c bl"></span><span className="c br"></span>
      </div>

      <div className="map-meta mono">
        <div>LAT 8°N → 36°N</div>
        <div>LON 68°E → 97°E</div>
        <div style={{ color: "var(--orange)" }}>● 26 STATIONS</div>
      </div>
    </div>
  );
}
