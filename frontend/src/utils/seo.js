// Single source of truth for SEO: bidirectional page<->URL mapping, per-page
// title/description copy, and dependency-free helpers that sync the document
// <head> (title, meta description, canonical) on navigation. No react-helmet.

export const SITE_URL = "https://aqi-early-warning-system.vercel.app";

// Internal page key -> URL path. Keys are derived from VALID_PAGES in App.jsx.
// The only key that doesn't map 1:1 to its path is `chat` -> /chatbot.
export const PAGE_TO_PATH = {
  map:      "/",
  predict:  "/predict",
  health:   "/health",
  forecast: "/forecast",
  models:   "/models",
  cities:   "/cities",
  compare:  "/compare",
  alerts:   "/alerts",
  chat:     "/chatbot",
  about:    "/about",
  login:    "/login",
  register: "/register",
  api:      "/api",
  history:  "/history",
  weather:  "/weather",
  cropburn: "/cropburn",
};

// Reverse map: URL path -> internal page key.
export const PATH_TO_PAGE = Object.fromEntries(
  Object.entries(PAGE_TO_PATH).map(([page, path]) => [path, page])
);

// Resolve any incoming pathname to an internal page key (or null if unknown).
// Trailing slashes are tolerated so /forecast and /forecast/ both resolve.
export function pathToPage(pathname) {
  const clean = (pathname || "/").replace(/\/+$/, "") || "/";
  return PATH_TO_PAGE[clean] || null;
}

// Internal page key -> URL path, defaulting to home for anything unmapped.
export function pageToPath(page) {
  return PAGE_TO_PATH[page] || "/";
}

// Per-page <title> + <meta name="description">. Honest, keyword-rich copy.
// 37 cities are currently live, so we never overstate coverage.
export const SEO = {
  map: {
    title: "AQI Early Warning System — Live Air Quality for 37 Indian Cities",
    description:
      "Live, real-time Air Quality Index (AQI) for 37 Indian cities. Track PM2.5, PM10 and pollution on an interactive map with ML forecasts — free and real-time.",
  },
  predict: {
    title: "AQI Predictor — ML-Powered Air Quality Prediction | AQI Early Warning",
    description:
      "Predict air quality with a machine-learning model trained on Indian pollution data. Get instant AQI estimates with SHAP explainability — free and real-time.",
  },
  health: {
    title: "Air Quality Health Impact Calculator | AQI Early Warning System",
    description:
      "See how today's air quality affects your health. Personalised AQI risk, PM2.5 exposure and protective advice for 37 Indian cities — free to use.",
  },
  forecast: {
    title: "24-Hour AQI Forecast for Indian Cities | AQI Early Warning System",
    description:
      "ML-powered 24-hour AQI forecast for 37 Indian cities. Plan ahead with hourly air-quality and PM2.5 predictions — free, real-time and updated continuously.",
  },
  models: {
    title: "Model Intelligence — AQI Prediction ML Models | AQI Early Warning",
    description:
      "Explore the machine-learning models behind our AQI forecasts: accuracy metrics, R² scores, feature importance and SHAP explainability for Indian air quality.",
  },
  cities: {
    title: "City Air Quality Dashboard — Live AQI Analytics | AQI Early Warning",
    description:
      "Detailed live air-quality dashboard for Indian cities. Track AQI, PM2.5, PM10, NO2 and trends with rich analytics for 37 cities — free and real-time.",
  },
  compare: {
    title: "Compare Air Quality Across Indian Cities | AQI Early Warning System",
    description:
      "Compare live AQI and PM2.5 pollution side by side across 37 Indian cities. Find the cleanest and most polluted cities in India — free and real-time.",
  },
  alerts: {
    title: "Air Quality Alerts — AQI Email Warnings | AQI Early Warning System",
    description:
      "Get free email alerts when air quality in your city crosses a danger threshold. Set custom AQI warnings for any of 37 Indian cities — real-time monitoring.",
  },
  chat: {
    title: "Air Quality AI Chatbot — Ask About AQI | AQI Early Warning System",
    description:
      "Ask anything about air quality in India. Our AI chatbot explains AQI, PM2.5 health effects and live pollution data for 37 cities — free, instant answers.",
  },
  about: {
    title: "About — How the AQI Early Warning System Works | India Air Quality",
    description:
      "Learn how the AQI Early Warning System uses CPCB and WAQI data, machine learning and SHAP explainability to track and forecast air quality across India.",
  },
  login: {
    title: "Sign In | AQI Early Warning System",
    description:
      "Sign in to the AQI Early Warning System to manage your air-quality alerts and saved Indian cities.",
  },
  register: {
    title: "Create Account | AQI Early Warning System",
    description:
      "Create a free AQI Early Warning System account to set air-quality alerts and track pollution across Indian cities.",
  },
  api: {
    title: "Free Public Air Quality API for India | AQI Early Warning System",
    description:
      "Free public REST API for real-time and historical Indian air-quality data. Access live AQI, PM2.5 and forecasts for 37 cities — open and developer-friendly.",
  },
  history: {
    title: "AQI Time Machine — Historical Air Quality Data | AQI Early Warning",
    description:
      "Travel back through India's air-quality history. Explore historical AQI and PM2.5 trends for 37 cities with the AQI Time Machine — free and real-time.",
  },
  weather: {
    title: "Weather & Air Quality Correlation | AQI Early Warning System",
    description:
      "See how weather drives air quality across India. Explore the link between temperature, wind, humidity and AQI for 37 cities — live data, free to use.",
  },
  cropburn: {
    title: "Stubble Burning Early Warning — North India | AQI Early Warning System",
    description:
      "Track stubble and crop-burning impact on North India's air quality. Early-warning fire and AQI monitoring for the Delhi NCR pollution season — free, real-time.",
  },
};

// Apply per-page SEO to the live document: <title>, meta description and the
// canonical link. Creates the tags if they don't already exist. Safe to call
// on every navigation; no-ops outside a browser.
export function applySeo(page) {
  if (typeof document === "undefined") return;
  const meta = SEO[page] || SEO.map;

  document.title = meta.title;

  let desc = document.querySelector('meta[name="description"]');
  if (!desc) {
    desc = document.createElement("meta");
    desc.setAttribute("name", "description");
    document.head.appendChild(desc);
  }
  desc.setAttribute("content", meta.description);

  let canonical = document.querySelector('link[rel="canonical"]');
  if (!canonical) {
    canonical = document.createElement("link");
    canonical.setAttribute("rel", "canonical");
    document.head.appendChild(canonical);
  }
  canonical.setAttribute("href", SITE_URL + pageToPath(page));
}
