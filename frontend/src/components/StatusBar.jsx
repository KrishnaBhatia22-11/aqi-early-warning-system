import { useState, useEffect } from "react";

import { formatAge } from "../utils/feed";

export default function StatusBar({ apiOnline, feed = null }) {
  const mode = feed?.mode ?? "unknown";
  const [t, setT] = useState(0);
  useEffect(() => {
    const i = setInterval(() => setT(x => x + 1), 1000);
    return () => clearInterval(i);
  }, []);

  return (
    <div className="status-bar mono">
      <span className="sb-item">
        <span className="sb-dot" style={{ background: apiOnline && mode === "live" ? "#34d27a" : "#ef3a4d" }}></span>
        {!apiOnline ? "API OFFLINE"
          : mode === "snapshot" ? `STORED READING: ${formatAge(feed.asOfLatest).toUpperCase()}`
          : mode === "live" ? `LAST SYNC: ${t}s AGO`
          : "NO LIVE DATA"}
      </span>
      <span className="sb-item">XGBOOST R² 0.898 (2020 TEST)</span>
      <span className="sb-item">{mode === "live" && feed?.citiesLive != null ? `${feed.citiesLive} CITIES LIVE` : mode === "snapshot" ? "SHOWING STORED DATA" : "NO LIVE DATA"}</span>
      <span className="sb-item">DATA: 2015–2020</span>
      <span className="sb-item">BUILD v2.1</span>
      <span className="sb-item" style={{ marginLeft: "auto", color: apiOnline && mode === "live" ? "#FF6B00" : "#ef3a4d" }}>
        {apiOnline && mode === "live" ? "● UPLINK STABLE" : apiOnline ? "● FEED DOWN" : "● UPLINK DOWN"}
      </span>
    </div>
  );
}
