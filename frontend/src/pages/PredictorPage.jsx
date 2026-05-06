import { useState, useCallback, useRef } from "react";
import KnobDial from "../components/KnobDial";
import Gauge from "../components/Gauge";
import ShapChart from "../components/ShapChart";
import PredictionHistory from "../components/PredictionHistory";
import { predictAQI } from "../utils/api";
import { aqiCategory } from "../utils/aqiCategory";
import { POLLUTANTS, SHAP_STATIC } from "../data/index";

const DEFAULTS = { "PM2.5": 60, PM10: 90, NO: 12, NO2: 40, NOx: 52, NH3: 18, CO: 1.2, SO2: 20, O3: 45 };

export default function PredictorPage() {
  const [vals, setVals] = useState(DEFAULTS);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);
  const debounceRef = useRef(null);

  const handleKnob = useCallback((name, value) => {
    setVals(prev => {
      const next = { ...prev, [name]: value };
      clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(async () => {
        setLoading(true);
        setError(null);
        try {
          const res = await predictAQI(next);
          setResult(res);
          const cat = aqiCategory(res.aqi);
          setHistory(h => [
            { aqi: res.aqi, t: new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }), vals: next },
            ...h.slice(0, 9),
          ]);
        } catch (e) {
          setError("API unreachable — using local estimate");
          const rough = Math.round(
            next["PM2.5"] * 0.7 + next["PM10"] * 0.3 + next["NO2"] * 0.4 + next["O3"] * 0.2
          );
          setResult({ aqi: Math.min(500, rough), category: aqiCategory(rough).name, shap_values: SHAP_STATIC });
        } finally {
          setLoading(false);
        }
      }, 600);
      return next;
    });
  }, []);

  const handlePick = (h) => {
    setVals(h.vals);
    setResult({ aqi: h.aqi, category: aqiCategory(h.aqi).name, shap_values: SHAP_STATIC });
  };

  const aqi = result?.aqi ?? 0;
  const cat = aqiCategory(aqi);
  const shapData = result?.shap_values ?? SHAP_STATIC;

  return (
    <div className="predict-page">
      <div className="predict-hero">
        <div className="mono predict-eyebrow">ML PREDICTION ENGINE · XGBOOST R²=0.932</div>
        <h1 className="display predict-title">AQI Predictor</h1>
        <p className="predict-sub">Drag the dials to set pollutant levels. Our model predicts the AQI in real time.</p>
      </div>

      <div className="predict-layout">
        <div className="predict-knobs glass-strong">
          <div className="panel-header">
            <span className="mono panel-title">POLLUTANT INPUTS</span>
            <span className="mono panel-meta">{loading ? "COMPUTING…" : error ? "ESTIMATED" : result ? "LIVE" : "DRAG DIALS"}</span>
          </div>
          <div className="knobs-grid">
            {POLLUTANTS.map(p => (
              <KnobDial
                key={p.name}
                label={p.name}
                unit={p.unit}
                min={p.min}
                max={p.max}
                value={vals[p.name] ?? p.default}
                color={p.color}
                onChange={v => handleKnob(p.name, v)}
              />
            ))}
          </div>
          {error && <div className="mono predict-error">{error}</div>}
        </div>

        <div className="predict-result">
          <div className="predict-gauge-wrap glass-strong">
            <div className="panel-header">
              <span className="mono panel-title">AQI READING</span>
              {loading && <span className="mono panel-meta" style={{ color: "#FFB300" }}>⟳ COMPUTING</span>}
            </div>
            <Gauge aqi={aqi} idle={!result} />
            {result && (
              <div className="predict-result-meta">
                <div className="predict-aqi-big" style={{ color: cat.color }}>{aqi}</div>
                <span className={`badge ${cat.klass}`}>{cat.name.toUpperCase()}</span>
                <p className="predict-advice">{getAdvice(aqi)}</p>
              </div>
            )}
          </div>

          <div className="predict-shap glass-strong">
            <div className="panel-header">
              <span className="mono panel-title">AI EXPLAINABILITY (SHAP)</span>
              <span className="mono panel-meta">FEATURE IMPACT</span>
            </div>
            <ShapChart data={shapData} />
          </div>
        </div>
      </div>

      <PredictionHistory history={history} onPick={handlePick} />
    </div>
  );
}

function getAdvice(aqi) {
  if (aqi <= 50)  return "Air is clean. Enjoy outdoor activities freely.";
  if (aqi <= 100) return "Acceptable air quality. Sensitive individuals should be cautious.";
  if (aqi <= 200) return "Moderate pollution. Children and elderly should limit outdoor time.";
  if (aqi <= 300) return "Poor air quality. Everyone may experience health effects.";
  if (aqi <= 400) return "Very poor. Avoid outdoor activities. Use N95 mask if going out.";
  return "Severe hazard. Stay indoors. Emergency conditions.";
}
