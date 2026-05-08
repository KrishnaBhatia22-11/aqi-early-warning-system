import { useState, useEffect } from "react";
import IndiaMap from "../components/IndiaMap";
import ThreatMatrix from "../components/ThreatMatrix";
import LiveTicker from "../components/LiveTicker";
import SparkLine from "../components/SparkLine";
import CountUp from "../components/CountUp";
import { aqiCategory } from "../utils/aqiCategory";

const HERO_LINES = [
  "India breathes.",
  "Watch it live.",
  "Predict what's next.",
  "Protect your city.",
];

const SPARKLINES = {
  delhi:   [210, 230, 195, 240, 260, 245, 255],
  mumbai:  [90,  85,  100, 95,  80,  88,  92 ],
  chennai: [65,  70,  60,  75,  68,  72,  66 ],
};

export default function HeroMapPage({ cities, onCitySelect, setPage }) {
  const [heroIdx, setHeroIdx] = useState(0);
  const [heroFade, setHeroFade] = useState(true);

  useEffect(() => {
    const interval = setInterval(() => {
      setHeroFade(false);
      setTimeout(() => {
        setHeroIdx(i => (i + 1) % HERO_LINES.length);
        setHeroFade(true);
      }, 400);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const nationalAvg = cities.length
    ? Math.round(cities.reduce((s, c) => s + c.aqi, 0) / cities.length)
    : 187;
  const hazardousCities = cities.filter(c => c.aqi > 300).length;
  const cleanCities = cities.filter(c => c.aqi <= 100).length;
  const cat = aqiCategory(nationalAvg);

  return (
    <div className="hero-map-page">
      <section className="dynamic-hero">
        <div className="dh-bg">
          <div className="dh-orb dh-orb-1" />
          <div className="dh-orb dh-orb-2" />
        </div>
        <div className="dh-content">
          <div className="mono dh-eyebrow">● LIVE · {cities.length || 10} LIVE STATIONS · 26 CITIES IN ML DATASET · INDIA</div>
          <h1 className="display dh-headline" style={{ opacity: heroFade ? 1 : 0, transition: "opacity 0.4s" }}>
            {HERO_LINES[heroIdx]}
          </h1>
          <p className="dh-sub">
            Real-time air quality data from across India. ML-powered forecasts. Free forever.
          </p>
          <div className="dh-cta-row">
            <button className="btn-primary" onClick={() => setPage("predict")}>PREDICT MY CITY →</button>
            <button className="btn-ghost" onClick={() => setPage("cities")}>VIEW DASHBOARD</button>
          </div>
        </div>

      </section>

      <div style={{ display: "flex", flexDirection: "column", width: "100%", gap: "0" }}>

        {/* CITIES STRIP — row 1 */}
        <div style={{
          width: "100%",
          overflow: "hidden",
          background: "#0a0f1e",
          borderTop: "1px solid #22c55e20",
          padding: "28px 24px 24px",
        }}>
          <div className="dh-stat-strip">
            <div className="dh-stat">
              <span className="display dh-stat-num" style={{ color: cat.color }}>
                <CountUp to={nationalAvg} duration={1200} />
              </span>
              <span className="mono dh-stat-label">NATIONAL AVG AQI</span>
            </div>
            <div className="dh-stat">
              <span className="display dh-stat-num" style={{ color: "#ef3a4d" }}>
                <CountUp to={hazardousCities} duration={800} />
              </span>
              <span className="mono dh-stat-label">HAZARDOUS CITIES</span>
            </div>
            <div className="dh-stat">
              <span className="display dh-stat-num" style={{ color: "#34d27a" }}>
                <CountUp to={cleanCities} duration={800} />
              </span>
              <span className="mono dh-stat-label">CLEAN AIR CITIES</span>
            </div>
            <div className="dh-stat">
              <span className="display dh-stat-num" style={{ color: "#FFB300" }}>
                <CountUp to={cities.length || 10} duration={600} />
              </span>
              <span className="mono dh-stat-label">LIVE STATIONS</span>
            </div>
            <div className="dh-stat">
              <span className="display dh-stat-num" style={{ color: "#3498db" }}>
                <CountUp to={26} duration={600} />
              </span>
              <span className="mono dh-stat-label">CITIES IN ML DATASET</span>
            </div>
          </div>
        </div>

        {/* LIVE TICKER — row 2, completely separate */}
        <div style={{
          width: "100%",
          overflow: "hidden",
          background: "#060d1a",
          borderTop: "1px solid #ffffff10",
        }}>
          <LiveTicker cities={cities} />
        </div>

      </div>

      <section className="map-section">
        <div className="map-section-inner">
          <div className="map-left">
            <div className="panel-header" style={{ marginBottom: 16 }}>
              <span className="mono panel-title">LIVE AIR QUALITY MAP</span>
              <span className="mono panel-meta" style={{ color: "#34d27a" }}>● LIVE</span>
            </div>
            <IndiaMap cities={cities} onCityClick={onCitySelect} />
          </div>

          <div className="map-right">
            <div className="panel-header" style={{ marginBottom: 16 }}>
              <span className="mono panel-title">THREAT MATRIX</span>
              <span className="mono panel-meta">SORTED BY AQI</span>
            </div>
            <ThreatMatrix cities={cities} onCityClick={onCitySelect} />

            <div className="sparkline-strip">
              {Object.entries(SPARKLINES).map(([city, vals]) => {
                const cityData = cities.find(c => c.name.toLowerCase().includes(city));
                const aqi = cityData?.aqi ?? vals[vals.length - 1];
                const c = aqiCategory(aqi);
                return (
                  <div className="spark-card glass" key={city}>
                    <div className="mono spark-city">{city.toUpperCase()}</div>
                    <div className="spark-aqi" style={{ color: c.color }}>{aqi}</div>
                    <SparkLine values={cityData ? [...vals.slice(0,-1), aqi] : vals} color={c.color} />
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
