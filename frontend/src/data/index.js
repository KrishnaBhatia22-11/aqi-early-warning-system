export const CITIES_STATIC = [
  // ── Metro Tier ──────────────────────────────────────────────────────────────
  { name: "Delhi",           x: 290, y: 195, aqi: 287, pollutant: "PM2.5" },
  { name: "Mumbai",          x: 200, y: 420, aqi: 152, pollutant: "PM10"  },
  { name: "Bengaluru",       x: 282, y: 555, aqi: 98,  pollutant: "NO2"   },
  { name: "Chennai",         x: 332, y: 580, aqi: 45,  pollutant: "O3"    },
  { name: "Kolkata",         x: 442, y: 320, aqi: 218, pollutant: "PM2.5" },
  { name: "Hyderabad",       x: 295, y: 475, aqi: 134, pollutant: "PM2.5" },
  { name: "Ahmedabad",       x: 180, y: 320, aqi: 196, pollutant: "PM10"  },
  { name: "Pune",            x: 220, y: 442, aqi: 116, pollutant: "NO2"   },
  // ── Major Cities ────────────────────────────────────────────────────────────
  { name: "Jaipur",          x: 240, y: 250, aqi: 178, pollutant: "PM10"  },
  { name: "Lucknow",         x: 340, y: 245, aqi: 234, pollutant: "PM2.5" },
  { name: "Kanpur",          x: 322, y: 258, aqi: 312, pollutant: "PM2.5" },
  { name: "Patna",           x: 410, y: 275, aqi: 268, pollutant: "PM2.5" },
  { name: "Bhopal",          x: 270, y: 340, aqi: 142, pollutant: "PM10"  },
  { name: "Nagpur",          x: 295, y: 380, aqi: 168, pollutant: "PM10"  },
  { name: "Surat",           x: 188, y: 360, aqi: 158, pollutant: "PM2.5" },
  { name: "Indore",          x: 240, y: 335, aqi: 154, pollutant: "PM10"  },
  { name: "Visakhapatnam",   x: 380, y: 455, aqi: 86,  pollutant: "O3"    },
  { name: "Chandigarh",      x: 280, y: 165, aqi: 167, pollutant: "PM10"  },
  { name: "Coimbatore",      x: 280, y: 605, aqi: 62,  pollutant: "O3"    },
  { name: "Kochi",           x: 270, y: 625, aqi: 51,  pollutant: "O3"    },
  // ── Heritage / Tourist ──────────────────────────────────────────────────────
  { name: "Agra",            x: 301, y: 228, aqi: 220, pollutant: "PM2.5" },
  { name: "Varanasi",        x: 380, y: 270, aqi: 256, pollutant: "PM2.5" },
  { name: "Amritsar",        x: 252, y: 145, aqi: 245, pollutant: "PM2.5" },
  { name: "Jodhpur",         x: 233, y: 250, aqi: 145, pollutant: "PM10"  },
  { name: "Udaipur",         x: 243, y: 288, aqi: 120, pollutant: "PM10"  },
  { name: "Mysuru",          x: 265, y: 575, aqi: 85,  pollutant: "NO2"   },
  { name: "Pondicherry",     x: 342, y: 590, aqi: 55,  pollutant: "O3"    },
  // ── Industrial Corridors ────────────────────────────────────────────────────
  { name: "Ghaziabad",       x: 308, y: 192, aqi: 310, pollutant: "PM2.5" },
  { name: "Noida",           x: 302, y: 207, aqi: 285, pollutant: "PM2.5" },
  { name: "Faridabad",       x: 285, y: 213, aqi: 295, pollutant: "PM2.5" },
  { name: "Gurugram",        x: 275, y: 207, aqi: 252, pollutant: "PM2.5" },
  { name: "Meerut",          x: 297, y: 186, aqi: 268, pollutant: "PM2.5" },
  { name: "Moradabad",       x: 311, y: 189, aqi: 245, pollutant: "PM2.5" },
  { name: "Ludhiana",        x: 272, y: 142, aqi: 185, pollutant: "PM10"  },
  { name: "Jalandhar",       x: 268, y: 132, aqi: 165, pollutant: "PM10"  },
  // ── Tier 2 Growing ──────────────────────────────────────────────────────────
  { name: "Bhubaneswar",     x: 410, y: 380, aqi: 124, pollutant: "PM2.5" },
  { name: "Guwahati",        x: 510, y: 280, aqi: 188, pollutant: "PM10"  },
  { name: "Ranchi",          x: 400, y: 320, aqi: 145, pollutant: "PM10"  },
  { name: "Raipur",          x: 350, y: 365, aqi: 178, pollutant: "PM10"  },
  { name: "Dehradun",        x: 301, y: 155, aqi: 142, pollutant: "PM10"  },
  { name: "Shimla",          x: 290, y: 137, aqi: 48,  pollutant: "O3"    },
  { name: "Jammu",           x: 258, y: 100, aqi: 155, pollutant: "PM10"  },
  { name: "Srinagar",        x: 257, y: 68,  aqi: 118, pollutant: "PM10"  },
  { name: "Thiruvananthapuram", x: 275, y: 660, aqi: 48, pollutant: "O3"  },
  { name: "Madurai",         x: 303, y: 626, aqi: 95,  pollutant: "NO2"   },
  { name: "Vijayawada",      x: 337, y: 474, aqi: 134, pollutant: "PM2.5" },
  { name: "Nashik",          x: 244, y: 394, aqi: 124, pollutant: "PM10"  },
  { name: "Aurangabad",      x: 265, y: 396, aqi: 148, pollutant: "PM10"  },
  { name: "Kolhapur",        x: 250, y: 470, aqi: 105, pollutant: "PM10"  },
  { name: "Solapur",         x: 273, y: 448, aqi: 138, pollutant: "PM10"  },
  { name: "Warangal",        x: 323, y: 440, aqi: 142, pollutant: "PM2.5" },
  { name: "Guntur",          x: 340, y: 485, aqi: 128, pollutant: "PM2.5" },
  { name: "Tiruchirappalli", x: 310, y: 606, aqi: 88,  pollutant: "O3"    },
];

export const POLLUTANTS = [
  { name: "PM2.5", min: 0, max: 500, unit: "µg/m³", default: 60,  weight: 0.31, color: "#FF6B00" },
  { name: "PM10",  min: 0, max: 600, unit: "µg/m³", default: 90,  weight: 0.22, color: "#FFB300" },
  { name: "NO",    min: 0, max: 200, unit: "µg/m³", default: 12,  weight: 0.06, color: "#34d27a" },
  { name: "NO2",   min: 0, max: 200, unit: "µg/m³", default: 40,  weight: 0.12, color: "#ef3a4d" },
  { name: "NOx",   min: 0, max: 300, unit: "µg/m³", default: 52,  weight: 0.07, color: "#ff8a3d" },
  { name: "NH3",   min: 0, max: 200, unit: "µg/m³", default: 18,  weight: 0.04, color: "#f5d142" },
  { name: "CO",    min: 0, max: 50,  unit: "mg/m³",  default: 1.2, weight: 0.05, color: "#c2002a" },
  { name: "SO2",   min: 0, max: 200, unit: "µg/m³", default: 20,  weight: 0.06, color: "#9b59b6" },
  { name: "O3",    min: 0, max: 300, unit: "µg/m³", default: 45,  weight: 0.07, color: "#3498db" },
];

export const STATIC_SHAP = [
  { feature: "PM2.5", value: +42.5 },
  { feature: "PM10",  value: +28.2 },
  { feature: "NO2",   value: +14.7 },
  { feature: "NOx",   value:  +9.8 },
  { feature: "CO",    value:  +6.5 },
  { feature: "SO2",   value:  +3.2 },
  { feature: "O3",    value:  -8.4 },
  { feature: "NH3",   value:  -5.1 },
  { feature: "NO",    value:  -2.8 },
];

export const TREND_7D = [165, 189, 212, 198, 246, 287, 274];

export const CAL_30 = [
  142,168,189,156,214,245,278,
  256,234,198,187,212,243,287,
  312,298,276,245,218,234,268,
  287,256,234,212,245,287,274,
  298,287,
];

export const POLLUTANT_BREAKDOWN = [
  { name: "PM2.5", pct: 38, color: "#FF6B00" },
  { name: "PM10",  pct: 24, color: "#FFB300" },
  { name: "NO2",   pct: 14, color: "#ef3a4d" },
  { name: "O3",    pct: 10, color: "#34d27a" },
  { name: "CO",    pct: 7,  color: "#ff8a3d" },
  { name: "SO2",   pct: 4,  color: "#c2002a" },
  { name: "Other", pct: 3,  color: "#5b564f" },
];

export const SHAP_STATIC    = STATIC_SHAP;
export const CALENDAR_30D   = CAL_30;

export const INDIA_PATH = "M 248 80 L 282 92 L 318 78 L 348 88 L 378 80 L 408 92 L 442 88 L 472 102 L 498 122 L 510 152 L 528 168 L 540 188 L 532 218 L 514 232 L 502 252 L 488 268 L 466 280 L 448 296 L 432 318 L 418 342 L 414 372 L 408 402 L 414 432 L 408 460 L 396 482 L 382 462 L 370 444 L 360 466 L 348 492 L 340 522 L 332 552 L 322 580 L 308 608 L 296 638 L 286 658 L 278 670 L 268 658 L 264 638 L 268 612 L 274 588 L 274 562 L 268 538 L 258 514 L 248 488 L 234 468 L 220 452 L 204 442 L 188 432 L 178 416 L 174 398 L 178 380 L 178 362 L 168 348 L 158 332 L 152 318 L 158 304 L 168 296 L 174 282 L 168 268 L 156 256 L 144 246 L 138 232 L 142 218 L 154 208 L 162 196 L 168 182 L 174 168 L 184 156 L 198 148 L 212 144 L 224 138 L 238 128 L 246 116 L 246 100 Z M 530 232 L 548 218 L 566 222 L 580 232 L 588 248 L 580 262 L 566 268 L 552 262 L 540 252 L 532 244 Z";
