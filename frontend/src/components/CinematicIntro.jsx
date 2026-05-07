import { useState, useEffect, useMemo, useCallback } from "react";
import { INDIA_PATH, CITIES_STATIC } from "../data/index";
import { aqiCategory } from "../utils/aqiCategory";

export default function CinematicIntro({ onDone }) {
  const [stage, setStage] = useState(0);
  const [fading, setFading] = useState(false);

  const finish = useCallback(() => {
    setFading(true);
    setTimeout(onDone, 700);
  }, [onDone]);

  useEffect(() => {
    const timers = [
      setTimeout(() => setStage(1), 2000),
      setTimeout(() => setStage(2), 4000),
      setTimeout(() => setStage(3), 6000),
      setTimeout(finish,            8000),
    ];
    return () => timers.forEach(clearTimeout);
  }, [finish]);

  const stars = useMemo(() => Array.from({ length: 140 }, () => ({
    x: Math.random() * 100, y: Math.random() * 100,
    s: 0.3 + Math.random() * 1.6, d: Math.random() * 4,
  })), []);

  return (
    <div className={`intro-stage ${fading ? "fading" : ""} stage-${stage}`}>
      <div className="intro-stars">
        {stars.map((s, i) => (
          <span key={i} style={{ left: s.x+"%", top: s.y+"%", width: s.s+"px", height: s.s+"px", animationDelay: s.d+"s" }} />
        ))}
      </div>

      <div className="intro-globe-wrap">
        <svg viewBox="0 0 600 600" className="intro-globe">
          <defs>
            <radialGradient id="globeFill" cx="0.35" cy="0.35" r="0.7">
              <stop offset="0%"   stopColor="#1a1a22"/>
              <stop offset="60%"  stopColor="#0a0a14"/>
              <stop offset="100%" stopColor="#02020a"/>
            </radialGradient>
            <radialGradient id="globeAtm" cx="0.5" cy="0.5" r="0.55">
              <stop offset="80%"  stopColor="rgba(255,107,0,0)"/>
              <stop offset="92%"  stopColor="rgba(255,107,0,0.35)"/>
              <stop offset="100%" stopColor="rgba(255,107,0,0)"/>
            </radialGradient>
            <radialGradient id="terminator" cx="0.7" cy="0.5" r="0.7">
              <stop offset="0%"   stopColor="rgba(255,107,0,0.18)"/>
              <stop offset="100%" stopColor="rgba(0,0,0,0)"/>
            </radialGradient>
            <clipPath id="globeClip"><circle cx="300" cy="300" r="220"/></clipPath>
          </defs>
          <circle cx="300" cy="300" r="252" fill="url(#globeAtm)"/>
          <circle cx="300" cy="300" r="220" fill="url(#globeFill)"/>
          <circle cx="300" cy="300" r="220" fill="url(#terminator)"/>
          <g clipPath="url(#globeClip)" stroke="rgba(255,107,0,0.18)" strokeWidth="0.6" fill="none" className="globe-grid">
            {[-60,-30,0,30,60].map(lat => (
              <ellipse key={lat} cx="300" cy={300 - lat * 2.4} rx="220" ry={Math.cos(lat * Math.PI/180) * 18 + 4}/>
            ))}
            {Array.from({length: 12}).map((_, i) => {
              const angle = (i / 12) * Math.PI;
              return <ellipse key={i} cx="300" cy="300" rx={Math.abs(Math.sin(angle)) * 220} ry="220" />;
            })}
          </g>
          <g clipPath="url(#globeClip)" className="globe-land">
            <path d="M 320 220 Q 380 200 430 230 Q 470 260 460 290 Q 440 320 410 330 Q 390 340 380 360 Q 365 390 350 380 Q 335 365 340 340 Q 325 320 315 300 Q 305 270 320 245 Z" fill="rgba(255,107,0,0.25)" stroke="rgba(255,107,0,0.5)" strokeWidth="0.8"/>
            <path d="M 240 290 Q 270 300 275 340 Q 270 380 250 410 Q 235 420 230 400 Q 220 370 225 340 Q 230 310 240 290 Z" fill="rgba(255,107,0,0.18)" stroke="rgba(255,107,0,0.4)" strokeWidth="0.8"/>
            <path d="M 440 380 Q 470 380 480 395 Q 475 410 450 410 Q 435 405 440 380 Z" fill="rgba(255,107,0,0.15)" stroke="rgba(255,107,0,0.3)" strokeWidth="0.8"/>
          </g>
          <g clipPath="url(#globeClip)" className="india-highlight">
            <path d="M 380 270 Q 395 275 400 295 Q 398 320 388 340 Q 380 355 372 340 Q 368 315 372 290 Z" fill="rgba(255,107,0,0.7)" stroke="#FF6B00" strokeWidth="1"/>
            <circle cx="385" cy="305" r="4" fill="#FFB300"/>
          </g>
        </svg>

        {stage >= 2 && (
          <div className="intro-cities">
            {CITIES_STATIC.map((c, i) => {
              const cat = aqiCategory(c.aqi);
              return (
                <span key={c.name} className="intro-city-dot" style={{
                  left: `${(c.x / 600) * 100}%`, top: `${(c.y / 720) * 100}%`,
                  background: cat.color, boxShadow: `0 0 16px ${cat.color}`,
                  animationDelay: `${i * 60}ms`,
                }} />
              );
            })}
          </div>
        )}

        {stage >= 2 && (
          <svg viewBox="0 0 600 720" className="intro-india-outline">
            <path d={INDIA_PATH} fill="none" stroke="#FF6B00" strokeWidth="1.5" style={{ filter: "drop-shadow(0 0 12px rgba(255,107,0,0.6))" }}/>
          </svg>
        )}
      </div>

      <div className="intro-text">
        {stage === 0 && <div className="fade-up"><div className="mono intro-eyebrow">EARTH OBSERVATION · GEO-AQI · 2026</div><div className="display intro-title">Calibrating sensors…</div></div>}
        {stage === 1 && <div className="fade-up"><div className="mono intro-eyebrow" style={{color:"#FF6B00"}}>TARGETING SUBCONTINENT · 22.59°N 79.96°E</div><div className="display intro-title">Locating India.</div></div>}
        {stage === 2 && <div className="fade-up"><div className="mono intro-eyebrow" style={{color:"#FF6B00"}}>ESTABLISHING UPLINK · 26 STATIONS</div><div className="display intro-title">Reading the air.</div></div>}
        {stage === 3 && <div className="fade-up"><div className="mono intro-eyebrow" style={{color:"#34d27a"}}>● ALL SYSTEMS ONLINE</div><div className="display intro-title">Welcome.</div></div>}
      </div>

      <button className="intro-skip mono" onClick={finish}>SKIP INTRO →</button>

      <div className="intro-progress">
        <div className="intro-progress-bar" style={{ width: `${(stage + 1) * 25}%` }}></div>
        <div className="mono intro-progress-meta">
          <span>STAGE {stage + 1} / 4</span>
          <span>{["GEOSYNC","TARGETING","PINGING","RENDERING"][stage]}</span>
        </div>
      </div>

      <span className="intro-reticle tl"></span>
      <span className="intro-reticle tr"></span>
      <span className="intro-reticle bl"></span>
      <span className="intro-reticle br"></span>
    </div>
  );
}
