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

export default function HeroMapPage({ cities, onCitySelect, setPage, zoomCity }) {
  const [heroIdx, setHeroIdx] = useState(0);
  const [heroFade, setHeroFade] = useState(true);
  const [mapVisible, setMapVisible] = useState(true);

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

  useEffect(() => {
    if (!zoomCity) setMapVisible(true);
  }, [zoomCity]);

  const handleCityClick = (city) => {
    setMapVisible(false);
    onCitySelect(city);
  };

  const nationalAvg = cities.length
    ? Math.round(cities.reduce((s, c) => s + c.aqi, 0) / cities.length)
    : 187;
  const hazardousCities = cities.filter(c => c.aqi > 300).length;
  const cleanCities = cities.filter(c => c.aqi <= 100).length;
  const cat = aqiCategory(nationalAvg);

  const worstCity    = cities.length ? cities.reduce((a, b) => a.aqi > b.aqi ? a : b) : null;
  const cleanestCity = cities.length ? cities.reduce((a, b) => a.aqi < b.aqi ? a : b) : null;
  const worstCat     = worstCity    ? aqiCategory(worstCity.aqi)    : { color: "#ef3a4d", name: "Severe" };
  const cleanCat     = cleanestCity ? aqiCategory(cleanestCity.aqi) : { color: "#34d27a", name: "Good"   };
  const aboveSafe    = cities.filter(c => c.aqi > 100).length;
  const _d           = new Date();
  const todayLabel   = `${String(_d.getDate()).padStart(2, "0")} ${_d.toLocaleString("en-US", { month: "short" }).toUpperCase()} ${_d.getFullYear()}`;

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
            <div style={{ display: mapVisible ? "block" : "none" }}>
              <IndiaMap cities={cities} onCityClick={handleCityClick} />
            </div>
            <div className="aqi-legend-strip">
              <span className="legend-item">
                <span className="legend-dot" style={{background:'#22c55e'}}></span>
                Good <span className="legend-range">0–50</span>
              </span>
              <span className="legend-item">
                <span className="legend-dot" style={{background:'#84cc16'}}></span>
                Satisfactory <span className="legend-range">51–100</span>
              </span>
              <span className="legend-item">
                <span className="legend-dot" style={{background:'#eab308'}}></span>
                Moderate <span className="legend-range">101–200</span>
              </span>
              <span className="legend-item">
                <span className="legend-dot" style={{background:'#f97316'}}></span>
                Poor <span className="legend-range">201–300</span>
              </span>
              <span className="legend-item">
                <span className="legend-dot" style={{background:'#ef4444'}}></span>
                Severe <span className="legend-range">301–400</span>
              </span>
              <span className="legend-item">
                <span className="legend-dot" style={{background:'#7c3aed'}}></span>
                Hazardous <span className="legend-range">400+</span>
              </span>
            </div>
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

      {/* ── SECTION 1: Impact Statement ── */}
      <section className="impact-section">
        <div className="impact-inner">
          <div className="impact-grid">
            <div className="impact-stat">
              <div className="impact-num">1.4 Billion</div>
              <div className="impact-label">People in India breathing<br />polluted air daily</div>
              <div className="impact-source">Source: WHO 2024</div>
            </div>
            <div className="impact-divider" />
            <div className="impact-stat">
              <div className="impact-num">7 of 10</div>
              <div className="impact-label">World's most polluted<br />cities are in India</div>
              <div className="impact-source">Source: IQAir 2024</div>
            </div>
            <div className="impact-divider" />
            <div className="impact-stat">
              <div className="impact-num">₹1.5 Lakh Cr</div>
              <div className="impact-label">Annual economic cost<br />of air pollution in India</div>
              <div className="impact-source">Source: World Bank</div>
            </div>
          </div>
        </div>
      </section>

      {/* ── SECTION 2: National Snapshot ── */}
      {cities.length > 0 && (
        <section className="snapshot-section">
          <div className="snapshot-inner">
            <div className="mono snapshot-date">TODAY ACROSS INDIA — {todayLabel}</div>
            <div className="snapshot-pills">
              <div className="snapshot-pill">
                <span className="snap-dot" style={{ background: worstCat.color }} />
                <span className="snap-label">Worst City</span>
                <span className="snap-val" style={{ color: worstCat.color }}>{worstCity.name} {worstCity.aqi}</span>
                <span className="snap-cat" style={{ color: worstCat.color }}>— {worstCat.name}</span>
              </div>
              <div className="snapshot-pill">
                <span className="snap-dot" style={{ background: cleanCat.color }} />
                <span className="snap-label">Cleanest City</span>
                <span className="snap-val" style={{ color: cleanCat.color }}>{cleanestCity.name} {cleanestCity.aqi}</span>
                <span className="snap-cat" style={{ color: cleanCat.color }}>— {cleanCat.name}</span>
              </div>
              <div className="snapshot-pill">
                <span className="snap-dot" style={{ background: cat.color }} />
                <span className="snap-label">National Average</span>
                <span className="snap-val" style={{ color: cat.color }}>{nationalAvg}</span>
                <span className="snap-cat" style={{ color: cat.color }}>— {cat.name}</span>
              </div>
              <div className="snapshot-pill">
                <span className="snap-dot" style={{ background: "#f97316" }} />
                <span className="snap-label">Above Safe Limit</span>
                <span className="snap-val" style={{ color: "#f97316" }}>{aboveSafe} of {cities.length}</span>
                <span className="snap-cat">cities</span>
              </div>
            </div>
            <div className="snapshot-context mono">
              CPCB safe limit is AQI 100. Today, {aboveSafe} {aboveSafe === 1 ? "city is" : "cities are"} above it.
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
