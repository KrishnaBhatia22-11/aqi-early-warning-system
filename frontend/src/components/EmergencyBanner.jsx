import { useState } from "react";
import { aqiCategory } from "../utils/aqiCategory";

export default function EmergencyBanner({ cities }) {
  const [open, setOpen] = useState(true);
  if (!cities || !open) return null;
  const avg = Math.round(cities.reduce((s, c) => s + c.aqi, 0) / cities.length);
  const hazardous = cities.filter(c => c.aqi >= 300).map(c => c.name).slice(0, 3);
  if (avg < 200 || hazardous.length === 0) return null;

  return (
    <div className="emergency-banner">
      <span className="eb-icon">🚨</span>
      <b>SEVERE AIR QUALITY ALERT</b>
      <span className="eb-cities">· {hazardous.join(" · ")} currently hazardous · Check your city now</span>
      <button className="eb-close" onClick={() => setOpen(false)}>DISMISS ✕</button>
    </div>
  );
}
