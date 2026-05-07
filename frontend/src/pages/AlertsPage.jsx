import { useState } from "react";
import { aqiCategory } from "../utils/aqiCategory";

const INITIAL_ALERTS = [
  { id: 1, city: "Delhi", threshold: 200, active: true, triggered: true, lastAqi: 287 },
  { id: 2, city: "Mumbai", threshold: 150, active: true, triggered: false, lastAqi: 92 },
  { id: 3, city: "Lucknow", threshold: 250, active: false, triggered: true, lastAqi: 312 },
];

const CITIES = ["Delhi","Mumbai","Bangalore","Chennai","Kolkata","Hyderabad","Ahmedabad","Pune","Lucknow","Jaipur","Chandigarh","Patna"];

export default function AlertsPage({ cities, initialCity }) {
  const [alerts, setAlerts] = useState(INITIAL_ALERTS);
  const [form, setForm] = useState({ city: initialCity || "Delhi", threshold: 200, email: "" });
  const [saved, setSaved] = useState(false);

  const handleAdd = (e) => {
    e.preventDefault();
    const city = cities.find(c => c.name === form.city);
    setAlerts(a => [
      ...a,
      {
        id: Date.now(),
        city: form.city,
        threshold: Number(form.threshold),
        active: true,
        triggered: city ? city.aqi >= Number(form.threshold) : false,
        lastAqi: city?.aqi ?? 0,
      },
    ]);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const toggleAlert = (id) => {
    setAlerts(a => a.map(al => al.id === id ? { ...al, active: !al.active } : al));
  };

  const removeAlert = (id) => {
    setAlerts(a => a.filter(al => al.id !== id));
  };

  const triggeredCount = alerts.filter(a => a.active && a.triggered).length;

  return (
    <div className="alerts-page">
      <div className="alerts-hero">
        <div className="mono alerts-eyebrow">THRESHOLD ALERTING SYSTEM</div>
        <h1 className="display alerts-title">AQI Alerts</h1>
        <p className="alerts-sub">Get notified when air quality exceeds your threshold.</p>
      </div>

      {triggeredCount > 0 && (
        <div className="alert-banner-active glass-strong">
          <span className="mono" style={{ color: "#ef3a4d" }}>⚠ {triggeredCount} ALERT{triggeredCount > 1 ? "S" : ""} TRIGGERED</span>
          <span className="mono" style={{ color: "rgba(255,255,255,0.5)", fontSize: 12 }}>Cities are exceeding set thresholds right now.</span>
        </div>
      )}

      <div className="alerts-layout">
        <div className="alerts-form glass-strong">
          <div className="panel-header">
            <span className="mono panel-title">CREATE ALERT</span>
          </div>
          <form onSubmit={handleAdd} className="alert-form">
            <div className="form-group">
              <label className="mono form-label">CITY</label>
              <select
                className="form-input"
                value={form.city}
                onChange={e => setForm(f => ({ ...f, city: e.target.value }))}
              >
                {CITIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="mono form-label">AQI THRESHOLD</label>
              <input
                type="range"
                min={50}
                max={500}
                step={10}
                value={form.threshold}
                onChange={e => setForm(f => ({ ...f, threshold: e.target.value }))}
                className="form-range"
              />
              <div className="form-range-val">
                <span className="mono" style={{ color: aqiCategory(form.threshold).color, fontSize: 24, fontWeight: 700 }}>
                  {form.threshold}
                </span>
                <span className={`badge ${aqiCategory(form.threshold).klass}`}>
                  {aqiCategory(form.threshold).name.toUpperCase()}
                </span>
              </div>
            </div>
            <div className="form-group">
              <label className="mono form-label">NOTIFY EMAIL (OPTIONAL)</label>
              <input
                type="email"
                className="form-input"
                placeholder="you@example.com"
                value={form.email}
                onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
              />
            </div>
            <button type="submit" className="btn-primary" style={{ width: "100%" }}>
              {saved ? "✓ ALERT SAVED" : "CREATE ALERT →"}
            </button>
          </form>
        </div>

        <div className="alerts-list">
          <div className="panel-header" style={{ marginBottom: 16 }}>
            <span className="mono panel-title">ACTIVE ALERTS ({alerts.length})</span>
          </div>
          <div className="alert-cards">
            {alerts.map(al => {
              const cat = aqiCategory(al.threshold);
              return (
                <div key={al.id} className={`alert-card glass ${al.triggered && al.active ? "triggered" : ""}`}>
                  <div className="alert-card-top">
                    <div>
                      <span className="mono alert-city">{al.city.toUpperCase()}</span>
                      <div className="alert-threshold-row">
                        <span className="mono" style={{ color: "rgba(255,255,255,0.5)", fontSize: 12 }}>TRIGGER AT</span>
                        <span className="display" style={{ color: cat.color, fontSize: 20, marginLeft: 8 }}>{al.threshold}</span>
                        <span className={`badge ${cat.klass}`} style={{ marginLeft: 8, fontSize: 10 }}>{cat.name.toUpperCase()}</span>
                      </div>
                    </div>
                    <div className="alert-card-actions">
                      <button
                        className={`alert-toggle mono ${al.active ? "on" : "off"}`}
                        onClick={() => toggleAlert(al.id)}
                      >
                        {al.active ? "ON" : "OFF"}
                      </button>
                      <button className="alert-remove" onClick={() => removeAlert(al.id)}>✕</button>
                    </div>
                  </div>
                  {al.triggered && al.active && (
                    <div className="alert-triggered-row mono">
                      <span style={{ color: "#ef3a4d" }}>⚠ TRIGGERED</span>
                      <span style={{ color: "rgba(255,255,255,0.5)" }}>CURRENT: {al.lastAqi} AQI</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
