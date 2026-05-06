export default function AboutPage() {
  const stats = [
    { n: "26", l: "Monitoring Stations" },
    { n: "9", l: "Pollutants Tracked" },
    { n: "0.932", l: "Model R² Score" },
    { n: "21.33", l: "MAE (AQI Units)" },
    { n: "9 yrs", l: "Training Data" },
    { n: "Free", l: "Forever" },
  ];

  const stack = [
    { cat: "ML MODEL", items: ["XGBoost", "Scikit-learn", "SHAP", "MLflow"] },
    { cat: "BACKEND", items: ["FastAPI", "Python 3.11", "Pydantic", "Uvicorn"] },
    { cat: "FRONTEND", items: ["React 18", "Vite 5", "Tailwind CSS", "SVG Canvas"] },
    { cat: "INFRA", items: ["Render (API)", "Vercel (Frontend)", "GitHub Actions"] },
    { cat: "DATA", items: ["CPCB India", "2015–2024", "Open Government Data"] },
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
              We trained an XGBoost model on 9 years of Central Pollution Control Board (CPCB) data
              covering 9 pollutants. The model achieves R²=0.932 — meaning it explains 93.2% of AQI
              variance. SHAP values make every prediction explainable.
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
            <div className="mc-row"><span className="mono mc-key">TRAINING DATA</span><span className="mc-val">CPCB, 2015–2024</span></div>
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
