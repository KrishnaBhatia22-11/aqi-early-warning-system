export default function AboutPage() {
  const stats = [
    { n: "10",    l: "Live Stations" },
    { n: "26",    l: "Cities in ML Dataset" },
    { n: "9",     l: "Pollutants Tracked" },
    { n: "0.932", l: "Model R² Score" },
    { n: "21.33", l: "MAE (AQI Units)" },
    { n: "6 yrs", l: "Training Data" },
    { n: "29,531",l: "Dataset Rows" },
    { n: "Free",  l: "Forever" },
  ];

  const stack = [
    { cat: "ML MODEL",  items: ["XGBoost", "Scikit-learn", "SHAP", "MLflow"] },
    { cat: "BACKEND",   items: ["FastAPI", "Python 3.11", "Pydantic", "Uvicorn"] },
    { cat: "FRONTEND",  items: ["React 18", "Vite 5", "Tailwind CSS", "SVG Canvas"] },
    { cat: "INFRA",     items: ["Render (API)", "Vercel (Frontend)", "GitHub Actions"] },
    { cat: "DATA",      items: ["CPCB India", "2015–2020", "Open Government Data"] },
  ];

  return (
    <div className="about-page">
      <section className="about-hero">
        <div className="about-orb" />
        <div className="mono about-eyebrow">MISSION & TRANSPARENCY</div>
        <h1 className="display about-title">About This Project</h1>
        <p className="about-mission">
          India's 1.4 billion people breathe air that is often invisible to them — no real-time alerts,
          no ML forecasts, no accessible dashboard. We built this to change that. Open source, free forever.
        </p>
      </section>

      <section className="about-stats glass-strong">
        <div className="about-stats-grid">
          {stats.map(s => (
            <div key={s.l} className="about-stat">
              <span className="display about-stat-num" style={{ color: "#FF6B00" }}>{s.n}</span>
              <span className="mono about-stat-label">{s.l.toUpperCase()}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="about-story">
        <div className="about-story-inner">
          <div className="glass-strong about-story-card">
            <div className="mono about-section-label">THE PROBLEM</div>
            <h2 className="about-section-title">India's air quality crisis is real</h2>
            <p>
              India has 6 of the world's 10 most polluted cities. PM2.5 levels in Delhi regularly hit
              10–20× WHO limits. Yet most people lack a reliable, free tool to check conditions,
              understand pollutants, and get advance warnings before bad air days arrive.
            </p>
          </div>
          <div className="glass-strong about-story-card">
            <div className="mono about-section-label">OUR APPROACH</div>
            <h2 className="about-section-title">XGBoost + CPCB data</h2>
            <p>
              We trained an XGBoost model on 6 years of Central Pollution Control Board (CPCB) data
              (2015–2020) covering 9 pollutants across 26 cities (29,531 rows). The model achieves
              R²=0.932 — explaining 93.2% of AQI variance. SHAP values make every prediction explainable.
            </p>
          </div>
          <div className="glass-strong about-story-card">
            <div className="mono about-section-label">OPEN SOURCE</div>
            <h2 className="about-section-title">Built in Faridabad, India</h2>
            <p>
              This project is fully open source under the MIT license. The entire codebase — FastAPI
              backend, React frontend, ML training notebooks — is available on GitHub. Contributions,
              issues, and forks are welcome.
            </p>
            <a
              href="https://github.com/KrishnaBhatia22-11/aqi-early-warning-system"
              target="_blank"
              rel="noreferrer"
              className="btn-ghost"
              style={{ display: "inline-block", marginTop: 16 }}
            >
              VIEW ON GITHUB →
            </a>
          </div>
        </div>
      </section>

      <section className="about-team-section" style={{ marginTop: 40 }}>
        <div className="panel-header" style={{ marginBottom: 24 }}>
          <span className="mono panel-title">THE TEAM</span>
        </div>
        <div style={{
          background: "#1a1a1a",
          borderLeft: "4px solid #f97316",
          borderRadius: 12,
          padding: 40,
          display: "flex",
          flexDirection: "row",
          gap: 40,
          flexWrap: "wrap",
        }}>
          {/* Left side */}
          <div style={{ flex: "0 0 35%", minWidth: 220, display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
            <div style={{
              width: 120, height: 120, borderRadius: "50%",
              background: "linear-gradient(135deg, #f97316, #ea580c)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 40, fontWeight: 700, color: "white",
            }}>KB</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: "white", textAlign: "center" }}>Krishna Bhatia</div>
            <div style={{ fontSize: 15, color: "#f97316", textAlign: "center" }}>Full Stack ML Engineer</div>
            <div style={{ fontSize: 13, color: "#888", textAlign: "center" }}>Manav Rachna International Institute of Research and Studies</div>
            <div style={{ fontSize: 13, color: "#888", textAlign: "center" }}>Faridabad, India</div>
          </div>

          {/* Right side */}
          <div style={{ flex: "1 1 200px", display: "flex", flexDirection: "column" }}>
            <div style={{ fontSize: 22, fontWeight: 700, color: "white", marginBottom: 12 }}>
              Built solo. For 1.4 billion Indians.
            </div>
            <p style={{ color: "#aaa", fontSize: 14, lineHeight: 1.7, margin: 0 }}>
              Every line of code in this product — the XGBoost ML model, FastAPI backend, React frontend,
              PostgreSQL database, NASA FIRMS satellite integration, and email alert system — was designed,
              built, and deployed by one person. Built in Faridabad. Free forever.
            </p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, margin: "16px 0" }}>
              {["XGBoost R²=0.932", "53 Indian Cities", "NASA FIRMS Satellite", "2600+ Real DB Readings", "Free Forever"].map(pill => (
                <span key={pill} style={{
                  border: "1px solid #f97316", color: "#f97316",
                  borderRadius: 20, padding: "4px 14px",
                  fontSize: 12, background: "transparent",
                }}>{pill}</span>
              ))}
            </div>
            <div style={{ display: "flex", gap: 16, marginTop: 20, flexWrap: "wrap" }}>
              <a href="https://linkedin.com/in/krishna-bhatia09/" target="_blank" rel="noreferrer" style={{
                display: "flex", alignItems: "center", gap: 6,
                background: "#111", border: "1px solid #f97316", color: "#f97316",
                padding: "8px 16px", borderRadius: 8, fontSize: 13, textDecoration: "none",
              }}>
                <svg width="14" height="14" fill="currentColor" viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
                LinkedIn
              </a>
              <a href="https://github.com/KrishnaBhatia22-11" target="_blank" rel="noreferrer" style={{
                display: "flex", alignItems: "center", gap: 6,
                background: "#111", border: "1px solid #f97316", color: "#f97316",
                padding: "8px 16px", borderRadius: 8, fontSize: 13, textDecoration: "none",
              }}>
                <svg width="14" height="14" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/></svg>
                GitHub
              </a>
              <a href="mailto:krishnabhatia09@gmail.com" style={{
                display: "flex", alignItems: "center", gap: 6,
                background: "#111", border: "1px solid #f97316", color: "#f97316",
                padding: "8px 16px", borderRadius: 8, fontSize: 13, textDecoration: "none",
              }}>
                <svg width="14" height="14" fill="currentColor" viewBox="0 0 24 24"><path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>
                Email
              </a>
            </div>
          </div>
        </div>
      </section>

      <section className="about-stack">
        <div className="panel-header" style={{ marginBottom: 24 }}>
          <span className="mono panel-title">TECHNOLOGY STACK</span>
        </div>
        <div className="stack-grid">
          {stack.map(s => (
            <div key={s.cat} className="glass stack-card">
              <div className="mono stack-cat" style={{ color: "#FF6B00", marginBottom: 12 }}>{s.cat}</div>
              {s.items.map(item => (
                <div key={item} className="mono stack-item">{item}</div>
              ))}
            </div>
          ))}
        </div>
      </section>

      <section className="about-data">
        <div className="glass-strong about-data-card">
          <div className="mono about-section-label">DATA TRANSPARENCY</div>
          <h2 className="about-section-title">Model Card</h2>
          <div className="model-card-grid">
            <div className="mc-row"><span className="mono mc-key">ALGORITHM</span><span className="mc-val">XGBoost Regressor</span></div>
            <div className="mc-row"><span className="mono mc-key">TRAINING DATA</span><span className="mc-val">CPCB, 2015–2020</span></div>
            <div className="mc-row"><span className="mono mc-key">DATASET ROWS</span><span className="mc-val">29,531</span></div>
            <div className="mc-row"><span className="mono mc-key">ML CITIES</span><span className="mc-val">26</span></div>
            <div className="mc-row"><span className="mono mc-key">LIVE STATIONS</span><span className="mc-val">10</span></div>
            <div className="mc-row"><span className="mono mc-key">FEATURES</span><span className="mc-val">PM2.5, PM10, NO, NO2, NOx, NH3, CO, SO2, O3</span></div>
            <div className="mc-row"><span className="mono mc-key">TARGET</span><span className="mc-val">AQI (continuous, 0–500)</span></div>
            <div className="mc-row"><span className="mono mc-key">R² SCORE</span><span className="mc-val" style={{ color: "#34d27a" }}>0.932</span></div>
            <div className="mc-row"><span className="mono mc-key">MAE</span><span className="mc-val">21.33 AQI units</span></div>
            <div className="mc-row"><span className="mono mc-key">EXPLAINABILITY</span><span className="mc-val">SHAP (TreeExplainer)</span></div>
            <div className="mc-row"><span className="mono mc-key">TRACKING</span><span className="mc-val">MLflow</span></div>
          </div>
        </div>
      </section>
    </div>
  );
}
