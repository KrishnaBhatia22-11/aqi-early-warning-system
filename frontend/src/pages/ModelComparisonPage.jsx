import { useState, useEffect, useRef } from "react";
import { fetchModels } from "../utils/api";

// No hard-coded metrics here: everything shown comes from /models/comparison.
// Metrics are null for models that were not re-evaluated; those render as text, never as 0 or a bar.
const isNum = v => typeof v === "number" && Number.isFinite(v);
const NOT_EVAL = "Not re-evaluated";
const TEST_NOTE = "Temporal test, Jan-Jul 2020 (4,404 rows, 26 cities). Deployed file was not scored on this test.";

// ── Animated count-up metric box (renders nothing when the value is not a number)
function MetricBox({ label, value, decimals = 0, color, suffix = "" }) {
  const [cur, setCur] = useState(0);
  useEffect(() => {
    if (!isNum(value)) return;
    const start = performance.now();
    const dur = 1100;
    let raf;
    const tick = ts => {
      const t = Math.min(1, (ts - start) / dur);
      setCur(value * (1 - Math.pow(1 - t, 3)));
      if (t < 1) raf = requestAnimationFrame(tick);
      else setCur(value);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [value]);

  if (!isNum(value)) return null;
  const display = decimals > 0 ? cur.toFixed(decimals) : Math.round(cur);
  return (
    <div className="model-metric">
      <span className="model-metric-val" style={{ color }}>
        {display}{suffix}
      </span>
      <span className="mono model-metric-label">{label}</span>
    </div>
  );
}

// ── Model card
const PRODUCTION_STATUS = { color: "#22c55e", pulse: true, label: "PRODUCTION" };

function ModelCard({ model, index }) {
  const isProduction = model.status === "PRODUCTION";
  const sc = isProduction
    ? PRODUCTION_STATUS
    : { color: "#6b7280", pulse: false, label: String(model.status ?? "").toUpperCase() };
  const hasMetrics = isNum(model.r2) || isNum(model.mae) || isNum(model.rmse);
  const strengths = model.strengths ?? [];
  return (
    <div
      className={`model-card glass-strong ${isProduction ? "model-card-winner" : ""}`}
      style={{ animationDelay: `${index * 150}ms` }}
    >
      <div className="model-card-header">
        <div style={{ flex: 1, minWidth: 0 }}>
          <h3 className="model-name">{model.name}</h3>
          <p className="model-desc">{model.description}</p>
        </div>
        <div
          className="model-status-badge mono"
          style={{ color: sc.color, borderColor: sc.color + "55", background: sc.color + "14" }}
        >
          <span
            className={`model-status-dot ${sc.pulse ? "model-status-pulsing" : ""}`}
            style={{ background: sc.color }}
          />
          {sc.label}
        </div>
      </div>

      <div className="model-metrics">
        {hasMetrics ? (
          <>
            <MetricBox label="R² SCORE"  value={model.r2}           decimals={3} color="rgba(255,255,255,0.9)" />
            <MetricBox label="MAE (AQI)" value={model.mae}          decimals={1} color="rgba(255,255,255,0.85)" />
            <MetricBox label="RMSE"      value={model.rmse}         decimals={1} color="rgba(255,255,255,0.85)" />
            <MetricBox label="INFERENCE" value={model.inference_ms} decimals={1} color="rgba(255,255,255,0.85)" suffix="ms" />
          </>
        ) : (
          <span className="mono model-metric-label">{NOT_EVAL}</span>
        )}
      </div>

      {strengths.length > 0 && (
        <div className="model-strengths">
          <div className="mono model-strengths-title">STRENGTHS</div>
          {strengths.map((s, i) => (
            <div key={i} className="model-strength-item">{s}</div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Horizontal bar chart (SVG, no libraries). Models without a numeric value get a text row and no bar.
const BAR_W = 560, ML = 116, MR = 100, MT = 12, MB = 30;
const PW = BAR_W - ML - MR; // 344

function BarChart({ models, metricKey, title, subtitle, minVal = 0, maxVal, gridlines = [], winner, visible }) {
  const [prog, setProg] = useState(0);
  const BAR_H  = [36, 28, 28];
  const BAR_GAP = 16;

  useEffect(() => {
    if (!visible) return;
    const start = performance.now();
    let raf;
    const tick = ts => {
      const t = Math.min(1, (ts - start) / 900);
      setProg(1 - Math.pow(1 - t, 3));
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [visible]);

  const range = maxVal - minVal;
  let yPos = MT;
  const bars = models.map((m, i) => {
    const bh = BAR_H[i] ?? 28;
    const cy = yPos;
    yPos += bh + BAR_GAP;
    const has = isNum(m[metricKey]);
    const frac = has ? Math.min(1, Math.max(0, (m[metricKey] - minVal) / range)) : 0;
    return { m, bh, cy, has, fullW: frac * PW };
  });
  const totalH = yPos - BAR_GAP + MB;

  return (
    <div className="chart-card glass-strong">
      <div className="chart-title">{title}</div>
      <div className="mono chart-subtitle">{subtitle}</div>
      <svg
        viewBox={`0 0 ${BAR_W} ${totalH}`}
        className="bar-chart-svg"
        role="img"
        aria-label={title}
      >
        {/* Vertical gridlines + x-axis labels */}
        {gridlines.map(v => {
          const gx = ML + ((v - minVal) / range) * PW;
          return (
            <g key={v}>
              <line x1={gx} y1={MT} x2={gx} y2={totalH - MB}
                stroke="rgba(255,255,255,0.06)" strokeWidth="1" />
              <text x={gx} y={totalH - MB + 16}
                textAnchor="middle" fontFamily="JetBrains Mono" fontSize="9"
                fill="rgba(255,255,255,0.28)">{v}</text>
            </g>
          );
        })}

        {/* Bars */}
        {bars.map(({ m, bh, cy, has, fullW }) => {
          const animW = Math.max(0, fullW * prog);
          const isW   = m.name === winner;
          return (
            <g key={m.name}>
              {/* Model name label */}
              <text
                x={ML - 8} y={cy + bh / 2 + 4}
                textAnchor="end" fontFamily="JetBrains Mono" fontSize="10"
                fill={isW ? m.color : "rgba(255,255,255,0.5)"}
                fontWeight={isW ? "700" : "400"}
              >
                {m.name}
              </text>
              {!has && (
                <text
                  x={ML} y={cy + bh / 2 + 4}
                  fontFamily="JetBrains Mono" fontSize="10" fill="rgba(255,255,255,0.4)"
                >
                  {NOT_EVAL}
                </text>
              )}
              {has && (
                <>
                  {/* Bar track (background) */}
                  <rect x={ML} y={cy} width={PW} height={bh} rx="5"
                    fill="rgba(255,255,255,0.03)" />
                  {/* Animated bar */}
                  <rect x={ML} y={cy} width={animW} height={bh} rx="5"
                    fill={m.color} opacity={isW ? 0.9 : 0.55} />
                  {/* Value label (appears when bar is mostly drawn) */}
                  {prog > 0.5 && (
                    <text
                      x={ML + fullW + 8} y={cy + bh / 2 + 4}
                      fontFamily="JetBrains Mono" fontSize="10"
                      fill="rgba(255,255,255,0.6)"
                    >
                      {m[metricKey]}
                    </text>
                  )}
                  {/* Production badge, appears after animation finishes */}
                  {isW && prog > 0.92 && (
                    <g>
                      <rect
                        x={ML + fullW + 44} y={cy + bh / 2 - 9}
                        width={52} height={18} rx="4"
                        fill={m.color + "1a"} stroke={m.color + "66"} strokeWidth="1"
                      />
                      <text
                        x={ML + fullW + 70} y={cy + bh / 2 + 5}
                        textAnchor="middle" fontFamily="JetBrains Mono"
                        fontSize="8" fontWeight="700" fill={m.color}
                      >
                        LIVE
                      </text>
                    </g>
                  )}
                </>
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
}

// ── Metric explainer card
function ExplainerCard({ icon, title, body }) {
  return (
    <div className="explainer-card glass-strong">
      <span className="explainer-icon" role="img" aria-label={title}>{icon}</span>
      <h4 className="explainer-title">{title}</h4>
      <p className="explainer-body">{body}</p>
    </div>
  );
}

// ── Skeleton while loading
function SkeletonPage() {
  return (
    <div className="models-page">
      <div className="models-hero">
        <div className="fc-skel-line" style={{ width: 220, height: 11, marginBottom: 20 }} />
        <div className="fc-skel-line" style={{ width: 380, height: 52, marginBottom: 16 }} />
        <div className="fc-skel-line" style={{ width: 520, height: 17, marginBottom: 28 }} />
        <div style={{ display: "flex", gap: 12 }}>
          {[130, 140, 130, 150].map((w, i) => (
            <div key={i} className="fc-skel-line" style={{ width: w, height: 36, borderRadius: 999 }} />
          ))}
        </div>
      </div>
      <div style={{ padding: "0 24px 48px", maxWidth: 1400, margin: "0 auto" }}>
        <div className="fc-skel-line" style={{ width: 180, height: 11, marginBottom: 20 }} />
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 20 }}>
          {[0, 1, 2].map(i => (
            <div key={i} className="fc-skel-chart" style={{ height: 320, borderRadius: 14 }} />
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Main page export
export default function ModelComparisonPage() {
  const [data, setData]               = useState(null);
  const [loading, setLoading]         = useState(true);
  const [chartsVisible, setChartsVis] = useState(false);
  const chartsRef = useRef(null);

  useEffect(() => {
    fetchModels()
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  // Fire chart animation when section scrolls into view
  useEffect(() => {
    const el = chartsRef.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setChartsVis(true); obs.disconnect(); } },
      { threshold: 0.15 }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [loading, data]);

  if (loading) return <SkeletonPage />;

  if (!data || !Array.isArray(data.models)) {
    return (
      <div className="models-page">
        <div className="models-hero">
          <h1 className="display models-title">Model Intelligence</h1>
          <p className="models-subtitle">Model evaluation data is temporarily unavailable.</p>
        </div>
      </div>
    );
  }

  const { models, dataset, winner, verdict } = data;
  const prod = models.find(m => m.name === winner) ?? models[0] ?? {};

  return (
    <div className="models-page">

      {/* ══ SECTION 1: Hero ══════════════════════════════════════════ */}
      <div className="models-hero">
        <div className="mono models-eyebrow">MODEL EVALUATION · MODEL INTELLIGENCE</div>
        <h1 className="display models-title">Model Intelligence</h1>
        <p className="models-subtitle">
          How the model behind the AQI predictions performs on data it has not seen.
        </p>
        <p className="mono models-subtitle">{TEST_NOTE}</p>
        {dataset && (
          <div className="models-stat-pills">
            {[
              { icon: "📊", text: `${dataset.rows.toLocaleString()} rows with recorded AQI` },
              { icon: "🏙",  text: `${dataset.cities} Indian cities`                         },
              { icon: "📅", text: `${dataset.period} dataset`                                },
              { icon: "🔢", text: `${dataset.features} input features`                       },
            ].map(p => (
              <div key={p.text} className="models-stat-pill">
                <span>{p.icon}</span>
                <span className="mono">{p.text}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ══ SECTION 2: Model Cards ════════════════════════════════════ */}
      <section className="models-section">
        <div className="mono models-section-label">MODEL COMPARISON</div>
        <div className="models-cards-grid">
          {models.map((m, i) => <ModelCard key={m.name} model={m} index={i} />)}
        </div>
      </section>

      {/* ══ SECTION 3: Visual Benchmarks ════════════════════════════ */}
      <section className="models-section" ref={chartsRef}>
        <div className="mono models-section-label">VISUAL BENCHMARKS</div>
        <div className="models-charts-grid">
          <BarChart
            models={models}
            metricKey="r2"
            title="R² Score (temporal 2020 test)"
            subtitle="HIGHER IS BETTER · MAX = 1.0 · RANGE STARTS AT 0.85"
            minVal={0.85}
            maxVal={1.00}
            gridlines={[0.85, 0.90, 0.95, 1.00]}
            winner={winner}
            visible={chartsVisible}
          />
          <BarChart
            models={models}
            metricKey="mae"
            title="Mean Absolute Error (AQI pts)"
            subtitle="LOWER IS BETTER · UNITS: AQI POINTS"
            minVal={0}
            maxVal={30}
            gridlines={[0, 10, 20, 30]}
            winner={winner}
            visible={chartsVisible}
          />
        </div>
      </section>

      {/* ══ SECTION 4: Metric Explainer ══════════════════════════════ */}
      <section className="models-section">
        <div className="mono models-section-label">WHAT THE METRICS MEAN</div>
        <div className="explainer-grid">
          <ExplainerCard
            icon="🎯"
            title="R² Score"
            body={`Measures how much of AQI variance the model explains. 1.0 = perfect prediction. 0.0 = no better than guessing the mean.${isNum(prod.r2) ? ` ${prod.name} scored ${prod.r2} on the temporal test.` : ""}`}
          />
          <ExplainerCard
            icon="📏"
            title="MAE — Mean Absolute Error"
            body={`Average difference between predicted and actual AQI in real units.${isNum(prod.mae) ? ` ${prod.name} is off by about ${prod.mae} AQI points on average on the temporal test.` : ""}`}
          />
          <ExplainerCard
            icon="〰"
            title="RMSE — Root Mean Square Error"
            body={`Like MAE but penalises large errors more heavily.${isNum(prod.rmse) ? ` ${prod.name} RMSE on the temporal test was ${prod.rmse}.` : ""}`}
          />
        </div>
      </section>

      {/* ══ SECTION 5: Verdict ══════════════════════════════════════ */}
      <section className="models-section models-verdict-section">
        <div className="mono models-section-label">PRODUCTION DECISION</div>
        <div className="verdict-panel glass-strong">
          <h2 className="verdict-title">Where the production model stands</h2>
          {verdict && <blockquote className="verdict-blockquote">"{verdict}"</blockquote>}

          <div className="verdict-reasons">
            {[
              {
                icon: "🧪", title: "Tested on future data",
                body: "Trained on 2015–2018, tuned on 2019, tested on Jan–Jul 2020. An earlier random-split score is not used because it lets neighbouring days leak between train and test.",
              },
              {
                icon: "🧩", title: "Missing Value Tolerance",
                body: "Real-world AQI sensors fail constantly. XGBoost handles NaN inputs natively without imputation, though accuracy drops when PM2.5 or PM10 is missing.",
              },
              {
                icon: "🔍", title: "SHAP Explainability",
                body: "Native SHAP integration means every prediction shows which pollutants drove the result. This is what powers the Predict page's feature chart.",
              },
            ].map(r => (
              <div key={r.title} className="verdict-reason">
                <span className="verdict-reason-icon">{r.icon}</span>
                <div className="verdict-reason-title">{r.title}</div>
                <div className="verdict-reason-body">{r.body}</div>
              </div>
            ))}
          </div>

          <p className="mono verdict-footer">
            {TEST_NOTE}
            {dataset && <>&nbsp;Data: {dataset.name}, {dataset.period}.</>}
          </p>
        </div>
      </section>

    </div>
  );
}
