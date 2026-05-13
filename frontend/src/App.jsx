import { useState, useEffect, useCallback, useRef, Component } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { fetchHealth } from "./utils/api";

import CinematicIntro from "./components/CinematicIntro";
import Navbar from "./components/Navbar";
import StatusBar from "./components/StatusBar";
import EmergencyBanner from "./components/EmergencyBanner";
import HelpFAB from "./components/HelpFAB";
import RichFooter from "./components/RichFooter";
import CityZoomModal from "./components/CityZoomModal";

import HeroMapPage from "./pages/HeroMapPage";
import PredictorPage from "./pages/PredictorPage";
import DashboardPage from "./pages/DashboardPage";
import AlertsPage from "./pages/AlertsPage";
import ChatbotPage from "./pages/ChatbotPage";
import AboutPage from "./pages/AboutPage";
import AuthPage from "./pages/AuthPage";
import ApiPage from "./pages/ApiPage";
import NotFoundPage from "./pages/NotFoundPage";
import ForecastPage from "./pages/ForecastPage";
import AQITimeMachinePage from "./pages/AQITimeMachinePage";
import WeatherAQIPage from "./pages/WeatherAQIPage";
import ModelComparisonPage from "./pages/ModelComparisonPage";
import HealthImpactPage from "./pages/HealthImpactPage";
import CityComparisonPage from "./pages/CityComparisonPage";
import CropBurnPage from "./pages/CropBurnPage";

// ── Error Boundaries ─────────────────────────────────────────────────────────

class IntroBoundary extends Component {
  constructor(props) { super(props); this.state = { crashed: false }; }
  static getDerivedStateFromError() { return { crashed: true }; }
  componentDidCatch() { this.props.onDone?.(); }
  render() { return this.state.crashed ? null : this.props.children; }
}

class PageBoundary extends Component {
  constructor(props) { super(props); this.state = { crashed: false, msg: "" }; }
  static getDerivedStateFromError(e) { return { crashed: true, msg: e?.message || String(e) }; }
  render() {
    if (this.state.crashed) {
      return (
        <div style={{ padding: "60px 24px", textAlign: "center", fontFamily: "monospace" }}>
          <div style={{ color: "#ef3a4d", fontSize: 20, marginBottom: 12 }}>⚠ PAGE ERROR</div>
          <div style={{ color: "rgba(255,255,255,0.5)", fontSize: 12, maxWidth: 480, margin: "0 auto 20px" }}>
            {this.state.msg}
          </div>
          <button
            onClick={() => this.setState({ crashed: false, msg: "" })}
            style={{ padding: "8px 20px", background: "#FF6B00", color: "#000", border: "none", borderRadius: 4, cursor: "pointer", fontFamily: "monospace" }}
          >
            RETRY
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

class AppBoundary extends Component {
  constructor(props) { super(props); this.state = { crashed: false, msg: "" }; }
  static getDerivedStateFromError(e) { return { crashed: true, msg: e?.message || String(e) }; }
  componentDidCatch(err, info) { console.error("[AppBoundary]", err, info?.componentStack); }
  render() {
    if (this.state.crashed) {
      return (
        <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", background: "#0a0a14", color: "#fff", fontFamily: "monospace", gap: 16, padding: 24, textAlign: "center" }}>
          <div style={{ color: "#FF6B00", fontSize: 32 }}>⚠</div>
          <div style={{ fontSize: 14, letterSpacing: "0.1em" }}>RENDER ERROR</div>
          <div style={{ fontSize: 12, color: "#ef3a4d", maxWidth: 520, wordBreak: "break-word" }}>
            {this.state.msg}
          </div>
          <button
            onClick={() => window.location.reload()}
            style={{ marginTop: 8, padding: "10px 24px", background: "#FF6B00", color: "#000", border: "none", borderRadius: 6, cursor: "pointer", fontFamily: "monospace", fontWeight: 700 }}
          >
            RELOAD APP
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

// ── Main App ──────────────────────────────────────────────────────────────────

const VALID_PAGES = ["map", "predict", "health", "forecast", "models", "cities", "compare", "alerts", "chat", "about", "login", "register", "api", "history", "weather", "cropburn"];

function AppInner() {
  const { user } = useAuth();
  const [showIntro, setShowIntro] = useState(() => {
    try { return !sessionStorage.getItem("intro_done"); } catch { return false; }
  });
  const [page, setPage] = useState("map");
  const [cities, setCities] = useState([]);
  const [apiOnline, setApiOnline] = useState(false);
  const [lastSync, setLastSync] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [wakeSeconds, setWakeSeconds] = useState(0);
  const [isWaking, setIsWaking] = useState(false);
  const [zoomCity, setZoomCity] = useState(null);
  const [a11y, setA11y] = useState(false);
  const [citiesInitialCity, setCitiesInitialCity] = useState(null);
  const [alertsInitialCity, setAlertsInitialCity] = useState(null);
  const [installPrompt, setInstallPrompt] = useState(null);
  const [showInstall, setShowInstall] = useState(false);

  const fetchCitiesRef = useRef(null);
  const fetchCities = useCallback(async (attempt = 1) => {
    setIsLoading(true);
    setLoadError(false);
    const wakeTimer = setTimeout(() => setIsWaking(true), 4000);
    try {
      const res = await fetch(
        "https://aqi-api-y2qs.onrender.com/api/v1/cities",
        { signal: AbortSignal.timeout(120000) }
      );
      clearTimeout(wakeTimer);
      const data = await res.json();
      setCities(data.cities.filter(c => c.data_available !== false));
      setIsLoading(false);
      setIsWaking(false);
      setLastSync(Date.now());
    } catch (e) {
      clearTimeout(wakeTimer);
      if (attempt < 3) {
        setTimeout(() => fetchCitiesRef.current(attempt + 1), 5000);
      } else {
        setIsLoading(false);
        setIsWaking(false);
        setLoadError(true);
      }
    }
  }, []);
  fetchCitiesRef.current = fetchCities;

  const refreshCities = useCallback(async () => {
    try {
      const res = await fetch("https://aqi-api-y2qs.onrender.com/api/v1/cities");
      const data = await res.json();
      setCities(data.cities.filter(c => c.data_available !== false));
      setLastSync(Date.now());
    } catch {}
  }, []);

  const checkHealth = useCallback(async () => {
    try {
      await fetchHealth();
      setApiOnline(true);
    } catch {
      setApiOnline(false);
    }
  }, []);

  useEffect(() => {
    if (!isWaking) { setWakeSeconds(0); return; }
    const interval = setInterval(() => setWakeSeconds(s => s + 1), 1000);
    return () => clearInterval(interval);
  }, [isWaking]);

  useEffect(() => {
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      setInstallPrompt(e);
      setShowInstall(true);
    });
    window.addEventListener('appinstalled', () => {
      setShowInstall(false);
    });
  }, []);

  const handleInstall = async () => {
    if (!installPrompt) return;
    installPrompt.prompt();
    await installPrompt.userChoice;
    setShowInstall(false);
    setInstallPrompt(null);
  };

  useEffect(() => {
    checkHealth();
    fetchCities();
    const healthInterval = setInterval(checkHealth, 30000);
    const citiesInterval = setInterval(refreshCities, 60000);
    return () => {
      clearInterval(healthInterval);
      clearInterval(citiesInterval);
    };
  }, [checkHealth, fetchCities, refreshCities]);

  const handleIntroDone = useCallback(() => {
    try { sessionStorage.setItem("intro_done", "1"); } catch {}
    setShowIntro(false);
  }, []);

  const navigateTo = (p) => {
    setPage(VALID_PAGES.includes(p) ? p : "map");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const renderPage = () => {
    switch (page) {
      case "map":      return <HeroMapPage cities={cities} onCitySelect={c => setZoomCity(c)} setPage={navigateTo} zoomCity={zoomCity} isLoading={isLoading} isWaking={isWaking} wakeSeconds={wakeSeconds} loadError={loadError} onRetry={fetchCities} />;
      case "predict":  return <PredictorPage />;
      case "health":   return <HealthImpactPage cities={cities} />;
      case "forecast": return <ForecastPage cities={cities} />;
      case "models":   return <ModelComparisonPage />;
      case "cities":   return <DashboardPage cities={cities} initialCity={citiesInitialCity} />;
      case "compare":  return <CityComparisonPage cities={cities} />;
      case "alerts":   return <AlertsPage cities={cities} initialCity={alertsInitialCity} />;
      case "chat":     return <ChatbotPage cities={cities} />;
      case "about":    return <AboutPage />;
      case "login":    return <AuthPage mode="login" setPage={navigateTo} />;
      case "register": return <AuthPage mode="register" setPage={navigateTo} />;
      case "api":      return <ApiPage />;
      case "history":  return <AQITimeMachinePage />;
      case "weather":   return <WeatherAQIPage />;
      case "cropburn":  return <CropBurnPage setPage={navigateTo} />;
      default:          return <NotFoundPage setPage={navigateTo} />;
    }
  };

  return (
    <>
      <div className={`app-root ${a11y ? "a11y-mode" : ""}`}>
        <EmergencyBanner cities={cities} />
        <Navbar
          page={page}
          setPage={navigateTo}
          apiOnline={apiOnline}
          cities={cities}
          a11y={a11y}
          setA11y={setA11y}
        />
        <main className="main-content">
          <PageBoundary key={page}>
            {renderPage()}
          </PageBoundary>
        </main>
        {page !== "login" && page !== "register" && (
          <RichFooter setPage={navigateTo} />
        )}
        <StatusBar apiOnline={apiOnline} lastSync={lastSync} />
        <HelpFAB />
        {zoomCity && (
          <CityZoomModal
            city={zoomCity}
            onClose={() => setZoomCity(null)}
            onPredict={() => { setZoomCity(null); navigateTo("predict"); }}
            onViewReport={() => { setCitiesInitialCity(zoomCity?.name ?? null); setZoomCity(null); navigateTo("cities"); }}
            onSetAlert={() => { setAlertsInitialCity(zoomCity?.name ?? null); setZoomCity(null); navigateTo("alerts"); }}
          />
        )}
        {showInstall && (
          <div className="pwa-install-banner">
            <span>📱 Install AQI India on your phone</span>
            <button onClick={handleInstall}>Install</button>
            <button onClick={() => setShowInstall(false)}>✕</button>
          </div>
        )}
      </div>

      {showIntro && (
        <IntroBoundary onDone={handleIntroDone}>
          <CinematicIntro onDone={handleIntroDone} />
        </IntroBoundary>
      )}
    </>
  );
}

export default function App() {
  return (
    <AppBoundary>
      <AuthProvider>
        <AppInner />
      </AuthProvider>
    </AppBoundary>
  );
}
