import { useRef, useEffect } from "react";

export default function KnobDial({ label, min, max, unit, color = "#FF6B00", value, onChange, step = 1 }) {
  const dragging = useRef(false);
  const ref = useRef(null);
  const startA = -135, endA = 135;
  const range = endA - startA;
  const pct = (value - min) / (max - min);
  const angle = startA + pct * range;

  const computeFromEvent = (clientX, clientY) => {
    if (!ref.current) return;
    const r = ref.current.getBoundingClientRect();
    const cx = r.left + r.width / 2;
    const cy = r.top + r.height / 2;
    let a = Math.atan2(clientY - cy, clientX - cx) * 180 / Math.PI + 90;
    if (a > 180) a -= 360;
    a = Math.max(startA, Math.min(endA, a));
    const newPct = (a - startA) / range;
    const v = min + newPct * (max - min);
    onChange(Math.round(v / step) * step);
  };

  useEffect(() => {
    const onMove = (e) => {
      if (!dragging.current) return;
      e.preventDefault();
      const x = e.touches ? e.touches[0].clientX : e.clientX;
      const y = e.touches ? e.touches[0].clientY : e.clientY;
      computeFromEvent(x, y);
    };
    const onUp = () => { dragging.current = false; document.body.style.cursor = ""; };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    window.addEventListener("touchmove", onMove, { passive: false });
    window.addEventListener("touchend", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
      window.removeEventListener("touchmove", onMove);
      window.removeEventListener("touchend", onUp);
    };
  }, [min, max, step]);

  const onWheel = (e) => {
    e.preventDefault();
    const wheelStep = unit === "mg/m³" ? 0.1 : (max - min) / 100;
    const dir = e.deltaY > 0 ? -1 : 1;
    onChange(Math.max(min, Math.min(max, value + dir * wheelStep * 5)));
  };

  const handleNumberInput = (e) => {
    const v = parseFloat(e.target.value);
    if (!isNaN(v)) onChange(Math.max(min, Math.min(max, v)));
  };

  const r = 44;
  const aRad = (a) => (a - 90) * Math.PI / 180;
  const arcPath = (from, to) => {
    const a1 = aRad(from), a2 = aRad(to);
    const x1 = 60 + r * Math.cos(a1), y1 = 60 + r * Math.sin(a1);
    const x2 = 60 + r * Math.cos(a2), y2 = 60 + r * Math.sin(a2);
    const large = (to - from) > 180 ? 1 : 0;
    return `M ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2}`;
  };
  const ind = aRad(angle);
  const ix = 60 + (r - 12) * Math.cos(ind);
  const iy = 60 + (r - 12) * Math.sin(ind);
  const id = label.replace(/\./g, "_");

  return (
    <div
      className="knob"
      ref={ref}
      onMouseDown={(e) => { dragging.current = true; document.body.style.cursor = "grabbing"; computeFromEvent(e.clientX, e.clientY); }}
      onTouchStart={(e) => { dragging.current = true; computeFromEvent(e.touches[0].clientX, e.touches[0].clientY); }}
      onWheel={onWheel}
    >
      <svg viewBox="0 0 120 120" className="knob-svg">
        <defs>
          <radialGradient id={`knobBg-${id}`} cx="0.5" cy="0.5" r="0.5">
            <stop offset="0%"   stopColor="rgba(255,107,0,0.06)"/>
            <stop offset="100%" stopColor="rgba(0,0,0,0.4)"/>
          </radialGradient>
        </defs>
        <circle cx="60" cy="60" r="52" fill={`url(#knobBg-${id})`} stroke="rgba(255,107,0,0.25)" strokeWidth="1"/>
        <path d={arcPath(startA, endA)} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="6" strokeLinecap="round"/>
        <path d={arcPath(startA, angle)} fill="none" stroke={color} strokeWidth="6" strokeLinecap="round" style={{ filter: `drop-shadow(0 0 6px ${color}88)` }}/>
        {Array.from({length: 11}).map((_, i) => {
          const a = startA + (i / 10) * range;
          const a1 = aRad(a);
          const x1 = 60 + (r + 4) * Math.cos(a1);
          const y1 = 60 + (r + 4) * Math.sin(a1);
          const x2 = 60 + (r + 8) * Math.cos(a1);
          const y2 = 60 + (r + 8) * Math.sin(a1);
          return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="rgba(255,107,0,0.4)" strokeWidth="1"/>;
        })}
        <line x1="60" y1="60" x2={ix} y2={iy} stroke={color} strokeWidth="2.5" strokeLinecap="round" style={{ filter: `drop-shadow(0 0 4px ${color})` }}/>
        <circle cx="60" cy="60" r="14" fill="#0a0a0a" stroke="rgba(255,107,0,0.5)" strokeWidth="1"/>
        <circle cx="60" cy="60" r="3" fill={color}/>
      </svg>
      <div className="knob-label">
        <span className="mono knob-name">{label}</span>
        <span className="display knob-val">{Number(value).toFixed(unit === "mg/m³" ? 2 : 0)}</span>
        <span className="mono knob-unit">{unit}</span>
      </div>
      <input
        type="number"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={handleNumberInput}
        onMouseDown={e => e.stopPropagation()}
        onTouchStart={e => e.stopPropagation()}
        className="knob-number-input"
      />
    </div>
  );
}
