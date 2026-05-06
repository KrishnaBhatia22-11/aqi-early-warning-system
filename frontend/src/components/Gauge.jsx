import { useState, useEffect } from "react";

export default function Gauge({ value, idle }) {
  const [idleVal, setIdleVal] = useState(value);

  useEffect(() => {
    if (!idle) return;
    let raf;
    const t0 = performance.now();
    const tick = (t) => {
      const dt = (t - t0) / 1000;
      setIdleVal(150 + Math.sin(dt * 1.2) * 90);
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [idle]);

  const v = Math.max(0, Math.min(500, idle ? idleVal : value));
  const startAngle = -120, endAngle = 120;
  const range = endAngle - startAngle;
  const angle = startAngle + (v / 500) * range;
  const cx = 180, cy = 180, r = 130;

  const arc = (from, to, color, width = 14) => {
    const a1 = (from - 90) * Math.PI / 180;
    const a2 = (to   - 90) * Math.PI / 180;
    const x1 = cx + r * Math.cos(a1), y1 = cy + r * Math.sin(a1);
    const x2 = cx + r * Math.cos(a2), y2 = cy + r * Math.sin(a2);
    const large = (to - from) > 180 ? 1 : 0;
    return <path d={`M ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2}`} fill="none" stroke={color} strokeWidth={width} strokeLinecap="round" />;
  };

  const segs = [
    { from: 0,   to: 50,  color: "#34d27a" },
    { from: 50,  to: 100, color: "#f5d142" },
    { from: 100, to: 200, color: "#FFB300" },
    { from: 200, to: 300, color: "#FF6B00" },
    { from: 300, to: 400, color: "#ef3a4d" },
    { from: 400, to: 500, color: "#c2002a" },
  ];
  const aFor = (val) => startAngle + (val / 500) * range;

  const needleLen = r - 18;
  const needleA = (angle - 90) * Math.PI / 180;
  const nx = cx + needleLen * Math.cos(needleA);
  const ny = cy + needleLen * Math.sin(needleA);

  return (
    <div className="gauge-wrap">
      <svg viewBox="0 0 360 280" className="gauge-svg">
        <defs>
          <radialGradient id="gaugeBg" cx="0.5" cy="0.5" r="0.6">
            <stop offset="0%"   stopColor="rgba(255,107,0,0.14)"/>
            <stop offset="70%"  stopColor="rgba(255,107,0,0.02)"/>
            <stop offset="100%" stopColor="rgba(255,107,0,0)"   />
          </radialGradient>
        </defs>
        <circle cx={cx} cy={cy} r={r + 18} fill="url(#gaugeBg)" />
        {arc(startAngle, endAngle, "rgba(255,255,255,0.05)", 14)}
        {segs.map((s, i) => (
          <g key={i}>{arc(aFor(s.from), aFor(s.to), s.color, 14)}</g>
        ))}
        {[0, 50, 100, 200, 300, 400, 500].map(t => {
          const a = (aFor(t) - 90) * Math.PI / 180;
          const x1 = cx + (r - 22) * Math.cos(a), y1 = cy + (r - 22) * Math.sin(a);
          const x2 = cx + (r - 8)  * Math.cos(a), y2 = cy + (r - 8)  * Math.sin(a);
          const lx = cx + (r - 38) * Math.cos(a), ly = cy + (r - 38) * Math.sin(a);
          return (
            <g key={t}>
              <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="rgba(255,255,255,0.4)" strokeWidth="1.5" />
              <text x={lx} y={ly + 3} fontFamily="JetBrains Mono, monospace" fontSize="9" fill="rgba(243,241,238,0.7)" textAnchor="middle">{t}</text>
            </g>
          );
        })}
        <g style={{ transformOrigin: `${cx}px ${cy}px`, transition: "transform 1100ms cubic-bezier(.2,1.4,.4,1)" }}>
          <line x1={cx} y1={cy} x2={nx} y2={ny} stroke="#FF6B00" strokeWidth="3" strokeLinecap="round" style={{ filter: "drop-shadow(0 0 6px rgba(255,107,0,0.8))" }}/>
          <circle cx={cx} cy={cy} r="10" fill="#0a0a0a" stroke="#FF6B00" strokeWidth="2" />
          <circle cx={cx} cy={cy} r="4" fill="#FFB300" />
        </g>
        <text x={cx} y={cy + 70} fontFamily="JetBrains Mono, monospace" fontSize="10" fill="var(--text-mute)" textAnchor="middle">0 ─ 500 INDIA AQI</text>
      </svg>
    </div>
  );
}
