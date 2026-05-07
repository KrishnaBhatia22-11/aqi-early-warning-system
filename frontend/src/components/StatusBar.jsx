import { useState, useEffect } from "react";

export default function StatusBar({ apiOnline }) {
  const [t, setT] = useState(0);
  useEffect(() => {
    const i = setInterval(() => setT(x => x + 1), 1000);
    return () => clearInterval(i);
  }, []);

  return (
    <div className="status-bar mono">
      <span className="sb-item">
        <span className="sb-dot" style={{ background: apiOnline ? "#34d27a" : "#ef3a4d" }}></span>
        {apiOnline ? `LAST SYNC: ${t}s AGO` : "API OFFLINE"}
      </span>
      <span className="sb-item">XGBOOST R²=0.932</span>
      <span className="sb-item">26 STATIONS</span>
      <span className="sb-item">DATA: 2015–2024</span>
      <span className="sb-item">BUILD v2.1</span>
      <span className="sb-item" style={{ marginLeft: "auto", color: apiOnline ? "#FF6B00" : "#ef3a4d" }}>
        {apiOnline ? "● UPLINK STABLE" : "● UPLINK DOWN"}
      </span>
    </div>
  );
}
