import { useState } from "react";
import { predictAQI, fetchCities, fetchHealth } from "../utils/api";

const ENDPOINTS = [
  {
    method: "GET",
    path: "/health",
    desc: "Check if the API is online and get model metadata.",
    response: `{ "status": "healthy", "model": "xgboost", "r2": 0.932 }`,
  },
  {
    method: "GET",
    path: "/cities",
    desc: "Fetch live AQI readings for all 26 monitored Indian cities.",
    response: `[{ "name": "Delhi", "aqi": 287, "category": "Poor", "pollutant": "PM2.5" }, ...]`,
  },
  {
    method: "POST",
    path: "/predict",
    desc: "Predict AQI given 9 pollutant readings. Returns AQI, category, and SHAP values.",
    body: `{
  "PM2.5": 60.0,
  "PM10":  90.0,
  "NO":    12.0,
  "NO2":   40.0,
  "NOx":   52.0,
  "NH3":   18.0,
  "CO":    1.2,
  "SO2":   20.0,
  "O3":    45.0
}`,
    response: `{
  "aqi": 187,
  "category": "Moderate",
  "shap_values": { "PM2.5": 42.1, "PM10": 18.3, ... }
}`,
  },
];

const CODE_EXAMPLES = {
  python: `import requests

BASE = "https://aqi-api-y2qs.onrender.com"

# Predict AQI
response = requests.post(f"{BASE}/predict", json={
    "PM2.5": 60.0, "PM10": 90.0, "NO": 12.0,
    "NO2": 40.0, "NOx": 52.0, "NH3": 18.0,
    "CO": 1.2, "SO2": 20.0, "O3": 45.0
})
print(response.json())
# → { "aqi": 187, "category": "Moderate", ... }`,

  javascript: `const BASE = "https://aqi-api-y2qs.onrender.com";

const res = await fetch(\`\${BASE}/predict\`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    "PM2.5": 60, "PM10": 90, "NO": 12,
    "NO2": 40, "NOx": 52, "NH3": 18,
    "CO": 1.2, "SO2": 20, "O3": 45
  })
});
const data = await res.json();
console.log(data.aqi); // 187`,

  curl: `curl -X POST https://aqi-api-y2qs.onrender.com/predict \\
  -H "Content-Type: application/json" \\
  -d '{
    "PM2.5": 60, "PM10": 90, "NO": 12,
    "NO2": 40, "NOx": 52, "NH3": 18,
    "CO": 1.2, "SO2": 20, "O3": 45
  }'`,
};

export default function ApiPage() {
  const [lang, setLang] = useState("python");
  const [testResult, setTestResult] = useState(null);
  const [testLoading, setTestLoading] = useState(false);
  const [activeEndpoint, setActiveEndpoint] = useState(null);

  const runTest = async (ep) => {
    setTestLoading(true);
    setActiveEndpoint(ep.path);
    setTestResult(null);
    try {
      let result;
      if (ep.path === "/health") result = await fetchHealth();
      else if (ep.path === "/cities") result = await fetchCities();
      else result = await predictAQI({ "PM2.5": 60, PM10: 90, NO: 12, NO2: 40, NOx: 52, NH3: 18, CO: 1.2, SO2: 20, O3: 45 });
      setTestResult({ ok: true, data: result });
    } catch (e) {
      setTestResult({ ok: false, error: e.message });
    } finally {
      setTestLoading(false);
    }
  };

  return (
    <div className="api-page">
      <div className="api-hero">
        <div className="mono api-eyebrow">PUBLIC REST API · OPEN ACCESS · NO KEY REQUIRED</div>
        <h1 className="display api-title">Developer API</h1>
        <p className="api-sub">
          Base URL: <code className="mono" style={{ color: "#FF6B00" }}>https://aqi-api-y2qs.onrender.com</code>
        </p>
        <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
          <a href="https://aqi-api-y2qs.onrender.com/docs" target="_blank" rel="noreferrer" className="btn-primary">
            SWAGGER DOCS →
          </a>
          <a href="https://github.com/KrishnaBhatia22-11/aqi-early-warning-system" target="_blank" rel="noreferrer" className="btn-ghost">
            GITHUB REPO
          </a>
        </div>
      </div>

      <section className="api-endpoints">
        <div className="panel-header" style={{ marginBottom: 24 }}>
          <span className="mono panel-title">ENDPOINTS</span>
        </div>
        <div className="endpoint-list">
          {ENDPOINTS.map(ep => (
            <div key={ep.path} className="glass-strong endpoint-card">
              <div className="endpoint-header">
                <span className={`ep-method mono ep-${ep.method.toLowerCase()}`}>{ep.method}</span>
                <span className="mono ep-path">{ep.path}</span>
                <button
                  className="btn-ghost ep-try"
                  onClick={() => runTest(ep)}
                  disabled={testLoading && activeEndpoint === ep.path}
                >
                  {testLoading && activeEndpoint === ep.path ? "RUNNING…" : "TRY IT →"}
                </button>
              </div>
              <p className="ep-desc">{ep.desc}</p>
              {ep.body && (
                <div className="ep-code-block">
                  <div className="mono ep-code-label">REQUEST BODY</div>
                  <pre className="mono ep-code">{ep.body}</pre>
                </div>
              )}
              <div className="ep-code-block">
                <div className="mono ep-code-label">RESPONSE</div>
                <pre className="mono ep-code">{ep.response}</pre>
              </div>
              {activeEndpoint === ep.path && testResult && (
                <div className={`ep-result ${testResult.ok ? "ok" : "err"}`}>
                  <div className="mono ep-result-label">{testResult.ok ? "✓ LIVE RESPONSE" : "✗ ERROR"}</div>
                  <pre className="mono ep-code">
                    {testResult.ok
                      ? JSON.stringify(Array.isArray(testResult.data) ? testResult.data.slice(0, 3) : testResult.data, null, 2)
                      : testResult.error}
                  </pre>
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      <section className="api-code">
        <div className="panel-header" style={{ marginBottom: 24 }}>
          <span className="mono panel-title">CODE EXAMPLES</span>
        </div>
        <div className="glass-strong code-block-wrap">
          <div className="code-tabs">
            {Object.keys(CODE_EXAMPLES).map(l => (
              <button
                key={l}
                className={`code-tab mono ${lang === l ? "active" : ""}`}
                onClick={() => setLang(l)}
              >
                {l.toUpperCase()}
              </button>
            ))}
          </div>
          <pre className="mono code-example">{CODE_EXAMPLES[lang]}</pre>
        </div>
      </section>

      <section className="api-limits glass-strong">
        <div className="mono panel-title" style={{ marginBottom: 16 }}>RATE LIMITS & TERMS</div>
        <div className="api-limits-grid mono">
          <div className="limit-item"><span className="limit-key">RATE LIMIT</span><span className="limit-val">100 req/min (free)</span></div>
          <div className="limit-item"><span className="limit-key">AUTH</span><span className="limit-val">None required</span></div>
          <div className="limit-item"><span className="limit-key">CORS</span><span className="limit-val">Open (*)</span></div>
          <div className="limit-item"><span className="limit-key">FORMAT</span><span className="limit-val">JSON only</span></div>
          <div className="limit-item"><span className="limit-key">LICENSE</span><span className="limit-val">MIT</span></div>
          <div className="limit-item"><span className="limit-key">SLA</span><span className="limit-val">Best-effort (Render free tier)</span></div>
        </div>
      </section>
    </div>
  );
}
