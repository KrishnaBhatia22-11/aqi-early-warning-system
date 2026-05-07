import { useState, useEffect, useRef } from "react";
import { calculateHealthImpact } from "../utils/api";

const RISK_COLORS = {
  "Minimal Risk":    "#22c55e",
  "Low Risk":        "#84cc16",
  "Moderate Risk":   "#f59e0b",
  "High Risk":       "#FF6B00",
  "Very High Risk":  "#ef3a4d",
  "Emergency Level": "#c2002a",
};

const RISK_ADVICE = {
  "Minimal Risk":    "Air quality is satisfactory. Enjoy outdoor activities freely.",
  "Low Risk":        "Sensitive individuals should consider limiting prolonged outdoor exertion.",
  "Moderate Risk":   "Reduce prolonged outdoor exertion. Children and elderly should limit outdoor time.",
  "High Risk":       "Avoid all outdoor exercise. N95 mask mandatory if going outside.",
  "Very High Risk":  "Avoid all outdoor activity. N95 mask mandatory if going outside.",
  "Emergency Level": "Health emergency — stay indoors completely. N95 mask even indoors if no purifier.",
};

const ACTION_ITEMS = {
  "Minimal Risk":    ["Safe for most outdoor activities", "Sensitive groups should limit prolonged exertion", "Good day for morning walks", "Keep windows open"],
  "Low Risk":        ["Safe for most outdoor activities", "Sensitive groups should limit prolonged exertion", "Good day for morning walks", "Keep windows open"],
  "Moderate Risk":   ["Reduce prolonged outdoor exertion", "Children and elderly should stay indoors", "Wear a mask if outside more than 1 hour", "Keep air purifier running indoors"],
  "High Risk":       ["Avoid all outdoor exercise", "N95 mask mandatory outside", "Keep all windows closed", "Run air purifier on maximum"],
  "Very High Risk":  ["Health emergency — stay indoors completely", "N95 mask even indoors if no purifier", "Seal window gaps with wet cloth", "Seek medical attention if chest pain or breathlessness"],
  "Emergency Level": ["Health emergency — stay indoors completely", "N95 mask even indoors if no purifier", "Seal window gaps with wet cloth", "Seek medical attention if chest pain or breathlessness"],
};

const CITY_POPULATIONS = {
  Delhi: 32_000_000, Mumbai: 20_700_000, Bengaluru: 13_200_000,
  Chennai: 10_900_000, Kolkata: 15_000_000, Hyderabad: 10_500_000,
  Ahmedabad: 8_400_000, Jaipur: 4_100_000, Lucknow: 3_700_000, Kanpur: 3_200_000,
  Patna: 2_400_000, Bhopal: 2_300_000, Pune: 7_400_000, Nagpur: 2_900_000,
  Surat: 7_100_000, Visakhapatnam: 2_300_000, Coimbatore: 2_200_000,
  Kochi: 2_100_000, Indore: 3_300_000, Chandigarh: 1_200_000,
  Amritsar: 1_300_000, Guwahati: 1_100_000, Bhubaneswar: 1_000_000,
  Thiruvananthapuram: 1_700_000, Varanasi: 1_500_000, Ranchi: 1_400_000,
};

const BREATHING_RATES = { child: 0.65, adult: 0.83, elderly: 0.70, athlete: 1.5 };

const COMP_ICONS = ["🚬", "🛡️", "🫁", "⏳"];

// Client-side fallback — all formulas from spec, no API needed
function computeLocally({ city, aqi, hours_outside, age_group, has_condition }) {
  const br   = BREATHING_RATES[age_group] || 0.83;
  const r1   = v => Math.round(v * 10) / 10;
  const pm25c = aqi * 0.6;

  let cigs  = r1((aqi * hours_outside) / (22 * 24));
  let pm25  = r1(pm25c * br * hours_outside);
  let who   = Math.min(999, Math.round((pm25c * br * hours_outside / (15 * 24)) * 100));
  const bm  = 0.071 * (aqi / 100);
  let mins  = r1(bm * (hours_outside / 24));

  if (has_condition) {
    cigs = r1(cigs * 1.5); pm25 = r1(pm25 * 1.5);
    who  = Math.min(999, Math.round(who * 1.5)); mins = r1(mins * 1.5);
  }

  const risk = aqi <= 50 ? "Minimal Risk" : aqi <= 100 ? "Low Risk" : aqi <= 200 ? "Moderate Risk"
             : aqi <= 300 ? "High Risk" : aqi <= 400 ? "Very High Risk" : "Emergency Level";
  const pop  = CITY_POPULATIONS[city] || 0;

  return {
    city, aqi, hours_outside, _local: true,
    personal: { cigarette_equivalent: cigs, pm25_inhaled_ug: pm25, who_limit_percentage: who, minutes_life_lost: mins, risk_level: risk, advice: RISK_ADVICE[risk] },
    city_level: { population: pop, collective_cigarettes_millions: r1(cigs * pop / 1e6), people_exposed: pop },
    comparisons: [
      `Equivalent to smoking ${cigs} cigarette${cigs !== 1 ? "s" : ""}`,
      `${who}% of WHO daily safe limit in just ${hours_outside} hour${hours_outside !== 1 ? "s" : ""} outside`,
      pop ? `${pop.toLocaleString()} ${city} residents breathing this right now` : "Millions of residents breathing this air right now",
      `Every hour outside costs ~${r1(bm / 24 * 60)} minutes of healthy life`,
    ],
  };
}

// Animated count-up number
function CountUp({ value, decimals = 0, suffix = "", danger = false }) {
  const [cur, setCur] = useState(0);
  useEffect(() => {
    const start = performance.now();
    let raf;
    const tick = ts => {
      const t = Math.min(1, (ts - start) / 1000);
      setCur(value * (1 - Math.pow(1 - t, 3)));
      if (t < 1) raf = requestAnimationFrame(tick); else setCur(value);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [value]);
  const disp = decimals > 0 ? cur.toFixed(decimals) : Math.round(cur);
  return <span className={`hi-number${danger ? " hi-number-danger" : ""}`}>{disp}{suffix}</span>;
}

// Single impact card
function ImpactCard({ cardType, icon, value, decimals, suffix, label, subtext }) {
  return (
    <div className={`impact-card impact-card-${cardType}`}>
      <span className="impact-icon" role="img" aria-hidden="true">{icon}</span>
      <CountUp value={value} decimals={decimals} suffix={suffix} danger={cardType === "who" && value > 100} />
      <div className="impact-label mono">{label}</div>
      <div className="impact-subtext">{subtext}</div>
    </div>
  );
}

export default function HealthImpactPage({ cities = [] }) {
  const [city, setCity]               = useState("Delhi");
  const [liveAqi, setLiveAqi]         = useState(null);
  const [aqiInput, setAqiInput]       = useState("");
  const [hours, setHours]             = useState(2);
  const [ageGroup, setAgeGroup]       = useState("adult");
  const [hasCondition, setHasCond]    = useState(false);
  const [loading, setLoading]         = useState(false);
  const [results, setResults]         = useState(null);
  const resultsRef = useRef(null);
  const shareCardRef = useRef(null);

  const cityNames = cities.length > 0 ? cities.map(c => c.name) : Object.keys(CITY_POPULATIONS);

  // Sync live AQI when city or cities prop changes
  useEffect(() => {
    const found = cities.find(c => c.name?.toLowerCase() === city.toLowerCase());
    setLiveAqi(found?.aqi ?? null);
  }, [city, cities]);

  const effectiveAqi = aqiInput ? Math.max(0, Math.min(500, Number(aqiInput))) : (liveAqi ?? 100);
  const isLive = !aqiInput && !!liveAqi;

  const handleCalculate = async () => {
    setLoading(true);
    setResults(null);
    try {
      const data = await calculateHealthImpact({
        city, aqi: effectiveAqi, hours_outside: hours, age_group: ageGroup, has_condition: hasCondition,
      });
      setResults(data);
    } catch {
      setResults(computeLocally({ city, aqi: effectiveAqi, hours_outside: hours, age_group: ageGroup, has_condition: hasCondition }));
    } finally {
      setLoading(false);
    }
  };

  // Smooth scroll to results after they appear
  useEffect(() => {
    if (results) setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 80);
  }, [results]);

  const handleShare = async () => {
    if (!results || !shareCardRef.current) return;
    try {
      const { default: html2canvas } = await import("html2canvas");
      const canvas = await html2canvas(shareCardRef.current, {
        scale: 2, backgroundColor: "#0a0a14", logging: false, useCORS: true,
      });
      const a = document.createElement("a");
      a.download = `aqi-health-${results.city.toLowerCase()}.png`;
      a.href = canvas.toDataURL("image/png");
      a.click();
    } catch { /* silent — share is non-critical */ }
  };

  const p  = results?.personal;
  const cl = results?.city_level;
  const riskColor = p ? (RISK_COLORS[p.risk_level] ?? "#FF6B00") : "#FF6B00";

  return (
    <div className="health-page">

      {/* ══ HERO ══════════════════════════════════════════════════ */}
      <div className="health-hero">
        <span className="mono health-eyebrow">HEALTH IMPACT CALCULATOR</span>
        <h1 className="display health-title">
          What is this air doing<br />to your body?
        </h1>
        <p className="health-subtitle">
          Enter your city and time spent outside.<br />
          We'll tell you the real cost in human terms.
        </p>
      </div>

      {/* ══ INPUTS ════════════════════════════════════════════════ */}
      <section className="health-input-section">
        <div className="health-input-card glass-strong">
          <div className="health-inputs-grid">

            {/* 1 · City */}
            <div className="health-field">
              <div className="mono health-field-label">CITY</div>
              <div className="health-city-row">
                <select
                  className="health-city-select"
                  value={city}
                  onChange={e => { setCity(e.target.value); setAqiInput(""); }}
                >
                  {cityNames.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
                {isLive && (
                  <span className="health-live-badge">
                    <span className="hlb-dot" />
                    LIVE {liveAqi} AQI
                  </span>
                )}
              </div>
              <div className="health-aqi-row">
                <span className="mono health-sublabel">{isLive ? "Override AQI:" : "AQI:"}</span>
                <input
                  type="number"
                  className="health-aqi-input"
                  placeholder={isLive ? String(liveAqi) : "e.g. 200"}
                  value={aqiInput}
                  min={0} max={500}
                  onChange={e => setAqiInput(e.target.value)}
                />
              </div>
            </div>

            {/* 2 · Hours slider */}
            <div className="health-field">
              <div className="mono health-field-label">HOURS OUTSIDE TODAY</div>
              <div className="health-slider-display">{hours}<span className="health-slider-unit"> hour{hours !== 1 ? "s" : ""}</span></div>
              <input
                type="range"
                className="health-slider"
                min="0.5" max="12" step="0.5"
                value={hours}
                onChange={e => setHours(Number(e.target.value))}
              />
              <div className="health-slider-marks mono">
                {["0.5h", "3h", "6h", "9h", "12h"].map(m => <span key={m}>{m}</span>)}
              </div>
            </div>

            {/* 3 · Age group */}
            <div className="health-field">
              <div className="mono health-field-label">AGE GROUP</div>
              <div className="health-age-pills">
                {[
                  { id: "child",   label: "Child",   note: "Higher breathing rate per body weight" },
                  { id: "adult",   label: "Adult",   note: "" },
                  { id: "elderly", label: "Elderly", note: "" },
                  { id: "athlete", label: "Athlete", note: "Up to 2× more air intake during exercise" },
                ].map(ag => (
                  <button
                    key={ag.id}
                    className={`health-age-pill${ageGroup === ag.id ? " active" : ""}`}
                    onClick={() => setAgeGroup(ag.id)}
                  >
                    {ag.label}
                    {ag.note && <span className="health-age-note">{ag.note}</span>}
                  </button>
                ))}
              </div>
            </div>

            {/* 4 · Health condition toggle */}
            <div className="health-field">
              <div className="mono health-field-label">HEALTH CONDITION</div>
              <button
                className="health-toggle-row"
                onClick={() => setHasCond(v => !v)}
                aria-pressed={hasCondition}
              >
                <span className="health-toggle-text">I have asthma or a heart condition</span>
                <span className={`hi-toggle${hasCondition ? " on" : ""}`} />
              </button>
              {hasCondition && (
                <div className="mono health-condition-note">Risk multiplied ×1.5 for sensitive individuals</div>
              )}
            </div>
          </div>

          <button className="health-calc-btn" onClick={handleCalculate} disabled={loading}>
            {loading
              ? <><span className="health-calc-spin" />CALCULATING…</>
              : "CALCULATE IMPACT"
            }
          </button>
        </div>
      </section>

      {/* ══ RESULTS ═══════════════════════════════════════════════ */}
      {(loading || results) && (
        <section className="health-results" ref={resultsRef}>

          {loading ? (
            // Skeleton while API responds
            <div className="impact-cards-grid">
              {[0, 1, 2, 3].map(i => (
                <div key={i} className="impact-card fc-skel-chart" style={{ animationDelay: `${i * 80}ms` }} />
              ))}
            </div>
          ) : (
            <>
              {results._local && (
                <div className="mono health-local-note">⚠ Estimated locally — backend unavailable</div>
              )}

              {/* 4 Impact cards */}
              <div className="impact-cards-grid">
                <ImpactCard
                  cardType="cig"
                  icon="🚬"
                  value={p.cigarette_equivalent}
                  decimals={1}
                  label="cigarettes smoked"
                  subtext="Equivalent PM2.5 exposure (Berkeley Earth)"
                />
                <ImpactCard
                  cardType="who"
                  icon="🛡️"
                  value={p.who_limit_percentage}
                  decimals={0}
                  suffix="%"
                  label="of WHO daily safe limit"
                  subtext={`In just ${hours} hour${hours !== 1 ? "s" : ""} outside`}
                />
                <ImpactCard
                  cardType="pm"
                  icon="🫁"
                  value={p.pm25_inhaled_ug}
                  decimals={0}
                  suffix="µg"
                  label="of PM2.5 particles inhaled"
                  subtext="Fine particles that reach your bloodstream"
                />
                <ImpactCard
                  cardType="life"
                  icon="⏳"
                  value={p.minutes_life_lost}
                  decimals={1}
                  suffix=" min"
                  label="of healthy life reduced"
                  subtext="Harvard School of Public Health research"
                />
              </div>

              {/* Population banner */}
              {cl.population > 0 && (
                <div className="population-banner glass-strong">
                  <p className="pop-line">
                    Right now,{" "}
                    <strong className="pop-highlight">{cl.population.toLocaleString()}</strong>
                    {" "}people in {results.city} are breathing AQI {Math.round(results.aqi)}.
                  </p>
                  <p className="pop-collective">
                    Collectively, that's equivalent to the city smoking{" "}
                    <strong className="pop-cig-number">{cl.collective_cigarettes_millions}M</strong>
                    {" "}cigarettes today.
                  </p>
                </div>
              )}

              {/* Comparison strips */}
              <div className="comparison-list">
                {results.comparisons.map((c, i) => (
                  <div key={i} className="comparison-item">
                    <span className="comparison-icon" role="img" aria-hidden="true">{COMP_ICONS[i]}</span>
                    <span>{c}</span>
                  </div>
                ))}
              </div>

              {/* Health advisory */}
              <div
                className="health-advisory glass-strong"
                style={{ borderColor: riskColor + "44", boxShadow: `0 0 0 1px ${riskColor}1a, 0 8px 32px ${riskColor}0d` }}
              >
                <div className="advisory-header">
                  <span
                    className="mono advisory-risk-badge"
                    style={{ color: riskColor, borderColor: riskColor + "55", background: riskColor + "14" }}
                  >
                    <span className="advisory-dot" style={{ background: riskColor }} />
                    {p.risk_level.toUpperCase()}
                  </span>
                </div>
                <p className="advisory-advice-text">{p.advice}</p>
                <div className="advisory-actions">
                  {(ACTION_ITEMS[p.risk_level] ?? []).map((item, i) => (
                    <div key={i} className="advisory-action-item">
                      <span className="advisory-bullet" style={{ color: riskColor }}>▸</span>
                      {item}
                    </div>
                  ))}
                </div>
              </div>

              {/* Share */}
              <div className="health-share-row">
                <button className="health-share-btn" onClick={handleShare}>
                  ↗ Share this result
                </button>
              </div>
            </>
          )}
        </section>
      )}

      {/* ══ HIDDEN SHARE CARD (html2canvas target) ════════════════ */}
      {results && (
        <div
          ref={shareCardRef}
          style={{
            position: "fixed", left: "-9999px", top: 0,
            width: "800px", height: "440px",
            background: "#0a0a14",
            padding: "44px 48px",
            fontFamily: "'Courier New', Courier, monospace",
            color: "#ffffff",
            boxSizing: "border-box",
            overflow: "hidden",
          }}
        >
          {/* Header */}
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 28 }}>
            <div style={{ fontSize: 17, fontWeight: 700, letterSpacing: "0.08em" }}>
              AQI<span style={{ color: "#FF6B00" }}>⚡</span>
              <span style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", marginLeft: 10, letterSpacing: "0.12em" }}>HEALTH IMPACT</span>
            </div>
            <div style={{ fontSize: 10, color: "rgba(255,255,255,0.3)", letterSpacing: "0.1em", alignSelf: "flex-end" }}>
              aqi-early-warning-system.vercel.app
            </div>
          </div>

          {/* City + AQI */}
          <div style={{ marginBottom: 24 }}>
            <div style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", letterSpacing: "0.18em", marginBottom: 6 }}>
              {results.city.toUpperCase()} · {p.risk_level.toUpperCase()}
            </div>
            <div style={{ fontSize: 66, fontWeight: 700, letterSpacing: "-0.04em", lineHeight: 1, color: riskColor }}>
              AQI {Math.round(results.aqi)}
            </div>
          </div>

          {/* Three headline stats */}
          <div style={{ display: "flex", gap: 40, marginBottom: 28 }}>
            {[
              { v: p.cigarette_equivalent, s: "", l: "CIGARETTES" },
              { v: p.who_limit_percentage, s: "%", l: "OF WHO LIMIT", c: p.who_limit_percentage > 100 ? "#ef3a4d" : "#f59e0b" },
              { v: `${results.hours_outside}h`, s: "", l: "HOURS OUTSIDE" },
            ].map(({ v, s, l, c }) => (
              <div key={l}>
                <div style={{ fontSize: 42, fontWeight: 700, letterSpacing: "-0.03em", lineHeight: 1, color: c || "#fff" }}>{v}{s}</div>
                <div style={{ fontSize: 10, color: "rgba(255,255,255,0.45)", letterSpacing: "0.12em", marginTop: 4 }}>{l}</div>
              </div>
            ))}
          </div>

          {/* Advice */}
          <div style={{ fontSize: 13, color: "rgba(255,255,255,0.6)", lineHeight: 1.55, borderLeft: `3px solid ${riskColor}`, paddingLeft: 16, maxWidth: 580 }}>
            {p.advice}
          </div>
        </div>
      )}

    </div>
  );
}
