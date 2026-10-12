import { useState, useEffect } from "react";
import IndiaMap from "../components/IndiaMap";
import ThreatMatrix from "../components/ThreatMatrix";
import LiveTicker from "../components/LiveTicker";
import SparkLine from "../components/SparkLine";
import CountUp from "../components/CountUp";
import { aqiCategory } from "../utils/aqiCategory";
import { fetchCropBurnStatus } from "../utils/api";
import { useCityHistory } from "../utils/useCityHistory";
import { formatAsOf, formatAge, totalStations, isLive, isSnapshot } from "../utils/feed";

const HERO_LINES = [
  "India breathes.",
  "Watch it live.",
  "Predict what's next.",
  "Protect your city.",
];

// One featured city: AQI from the API (live or stored) and a sparkline from REAL stored history only.
function FeaturedCard({ city, snapshot }) {
  const { points } = useCityHistory(city.name, 7);
  const c = aqiCategory(city.aqi);
  const values = points.map(p => p.aqi);
  return (
    <div className="spark-card glass">
      <div className="mono spark-city">{city.name.toUpperCase()}</div>
      <div className="spark-aqi" style={{ color: c.color }}>{city.aqi}</div>
      {snapshot && <div className="mono feed-stored-note">STORED · AS OF {formatAsOf(city.as_of)}</div>}
      {values.length >= 2 && <SparkLine values={values} color={c.color} />}
    </div>
  );
}

export default function HeroMapPage({ cities, feed, onCitySelect, setPage, zoomCity, isLoading, isWaking, wakeSeconds, loadError, onRetry }) {
  const [heroIdx, setHeroIdx] = useState(0);
  const [heroFade, setHeroFade] = useState(true);
  const [mapVisible, setMapVisible] = useState(true);
  const [cropBurn, setCropBurn] = useState(null);
  const [bannerDismissed, setBannerDismissed] = useState(false);

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

  useEffect(() => {
    fetchCropBurnStatus().then(setCropBurn).catch(() => {});
  }, []);

  const handleCityClick = (city) => {
    setMapVisible(false);
    onCitySelect(city);
  };

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="skeleton-bar" />
        {isWaking && (
          <div className="wake-banner">
            <div className="wake-spinner">⟳</div>
            <div className="wake-text">
              <span className="wake-title">Connecting to live data engine...</span>
              <span className="wake-sub">Free hosting wakes up in ~45 seconds · {wakeSeconds}s elapsed</span>
            </div>
          </div>
        )}
        <div className="skeleton-stats">
          {[1,2,3,4,5].map(i => (
            <div key={i} className="skeleton-stat">
              <div className="skeleton skeleton-num" />
              <div className="skeleton skeleton-label" />
            </div>
          ))}
        </div>
        <div className="skeleton-ticker">
          <div className="skeleton" style={{ height: "32px", width: "100%" }} />
        </div>
        <div className="skeleton-map-area">
          <div className="skeleton" style={{ height: "500px", borderRadius: "12px" }} />
        </div>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="load-error">
        <div className="load-error-icon">⚠</div>
        <div className="load-error-title">Could not connect to data engine</div>
        <div className="load-error-sub">The server may be temporarily unavailable.</div>
        <button className="load-retry-btn" onClick={() => onRetry()}>Retry</button>
      </div>
    );
  }

  const hasData      = cities.length > 0;
  const snapshotMode = isSnapshot(feed);
  const nationalAvg  = hasData
    ? Math.round(cities.reduce((s, c) => s + (c.aqi ?? 0), 0) / cities.length)
    : null;
  const veryPoorOrWorse = cities.filter(c => c.aqi > 300).length;
  const cleanCities = cities.filter(c => c.aqi <= 100).length;
  const cat = aqiCategory(nationalAvg ?? 0);
  const stations = totalStations(cities);
  const featured = [...cities].sort((a, b) => b.aqi - a.aqi).slice(0, 3);
  const asOfLatest = feed?.asOfLatest ?? null;

  const worstCity    = cities.length ? cities.reduce((a, b) => a.aqi > b.aqi ? a : b) : null;
  const cleanestCity = cities.length ? cities.reduce((a, b) => a.aqi < b.aqi ? a : b) : null;
  const worstCat     = worstCity    ? aqiCategory(worstCity.aqi)    : { color: "#ef3a4d", name: "Severe" };
  const cleanCat     = cleanestCity ? aqiCategory(cleanestCity.aqi) : { color: "#34d27a", name: "Good"   };
  const aboveSafe    = cities.filter(c => c.aqi > 100).length;
  const _d           = new Date();
  const todayLabel   = `${String(_d.getDate()).padStart(2, "0")} ${_d.toLocaleString("en-US", { month: "short" }).toUpperCase()} ${_d.getFullYear()}`;

  const showBanner = cropBurn && cropBurn.status !== "CLEAR" && !bannerDismissed;

  return (
    <div className="hero-map-page">
      {showBanner && (
        <div className="crop-burn-alert-banner">
          <div className="cb-banner-left">
            <span>
              {cropBurn.status === "ACTIVE_BURN" ? "🔥" : "⚠️"}&nbsp;
              CROP BURNING ALERT &nbsp;·&nbsp; {cropBurn.confidence}% confidence
              &nbsp;·&nbsp; {cropBurn.affected_cities?.length || 0} North Indian cities affected
            </span>
            <button className="cb-banner-link" onClick={() => setPage("cropburn")}>
              See full report →
            </button>
          </div>
          <button className="cb-banner-close" onClick={() => setBannerDismissed(true)}>✕</button>
        </div>
      )}
      <section className="dynamic-hero">
        <div className="dh-bg">
          <div className="dh-orb dh-orb-1" />
          <div className="dh-orb dh-orb-2" />
        </div>
        <div className="dh-content">
          <div className="mono dh-eyebrow">
            {isLive(feed) ? `● LIVE · ${cities.length} CITIES${stations ? ` · ${stations} STATIONS` : ""} · INDIA`
              : snapshotMode ? `◌ STORED READINGS · AS OF ${formatAsOf(asOfLatest).toUpperCase()} · NOT LIVE`
              : "○ NO LIVE DATA · INDIA"}
          </div>
          <h1 className="display dh-headline" style={{ opacity: heroFade ? 1 : 0, transition: "opacity 0.4s" }}>
            {HERO_LINES[heroIdx]}
          </h1>
          <p className="dh-sub">
            Air quality data from CPCB via data.gov.in.
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
                {nationalAvg === null ? "—" : <CountUp to={nationalAvg} duration={1200} />}
              </span>
              <span className="mono dh-stat-label">{snapshotMode ? "AVG AQI (STORED)" : "AVG AQI OF CITIES"}</span>
            </div>
            <div className="dh-stat">
              <span className="display dh-stat-num" style={{ color: "#ef3a4d" }}>
                {hasData ? <CountUp to={veryPoorOrWorse} duration={800} /> : "—"}
              </span>
              <span className="mono dh-stat-label">VERY POOR OR WORSE (&gt;300)</span>
            </div>
            <div className="dh-stat">
              <span className="display dh-stat-num" style={{ color: "#34d27a" }}>
                {hasData ? <CountUp to={cleanCities} duration={800} /> : "—"}
              </span>
              <span className="mono dh-stat-label">CLEAN AIR CITIES</span>
            </div>
            <div className="dh-stat">
              <span className="display dh-stat-num" style={{ color: "#FFB300" }}>
                {stations ?? "—"}
              </span>
              <span className="mono dh-stat-label">{snapshotMode ? "STATIONS (STORED)" : "STATIONS"}</span>
            </div>
            <div className="dh-stat">
              <span className="display dh-stat-num" style={{ color: "#3498db" }}>
                {hasData ? <CountUp to={cities.length} duration={600} /> : "—"}
              </span>
              <span className="mono dh-stat-label">{isLive(feed) ? "CITIES LIVE" : "CITIES WITH A VALUE"}</span>
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
              <span className="mono panel-meta" style={{ color: isLive(feed) ? "#34d27a" : "#fbbf24" }}>
                {isLive(feed) ? "● LIVE" : snapshotMode ? `STORED · ${formatAge(asOfLatest).toUpperCase()}` : "NO LIVE DATA"}
              </span>
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
                Very Poor <span className="legend-range">301–400</span>
              </span>
              <span className="legend-item">
                <span className="legend-dot" style={{background:'#7c3aed'}}></span>
                Severe <span className="legend-range">400+</span>
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
              {featured.length === 0 && (
                <div className="spark-card glass">
                  <div className="mono spark-city">LIVE CPCB FEED UNAVAILABLE</div>
                  <div className="mono feed-stored-note">No live or stored values to show.</div>
                </div>
              )}
              {featured.map(city => (
                <FeaturedCard key={city.name} city={city} snapshot={city.data_mode === "snapshot"} />
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── SECTION 2: National Snapshot ── */}
      {cities.length > 0 && (
        <section className="snapshot-section">
          <div className="snapshot-inner">
            <div className="mono snapshot-date">{snapshotMode ? `LAST STORED READINGS — ${formatAsOf(asOfLatest)}` : `TODAY ACROSS INDIA — ${todayLabel}`}</div>
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
                <span className="snap-label">Average of cities</span>
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
              CPCB "Satisfactory" ends at AQI 100. {snapshotMode ? "At the last stored reading" : "Today"}, {aboveSafe} {aboveSafe === 1 ? "city is" : "cities are"} above it.
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
