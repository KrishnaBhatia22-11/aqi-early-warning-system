import { useState, useEffect, useCallback, Component } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { fetchHealth, fetchCities } from "./utils/api";
import { CITIES_STATIC } from "./data/index";

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
import ModelComparisonPage from "./pages/ModelComparisonPage";

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

const VALID_PAGES = ["map", "predict", "forecast", "models", "cities", "alerts", "chat", "about", "login", "register", "api"];

function AppInner() {
  const { user } = useAuth();
  const [showIntro, setShowIntro] = useState(() => {
    try { return !sessionStorage.getItem("intro_done"); } catch { return false; }
  });
  const [page, setPage] = useState("map");
  const [cities, setCities] = useState(CITIES_STATIC);
  const [apiOnline, setApiOnline] = useState(false);
  const [lastSync, setLastSync] = useState(null);
  const [zoomCity, setZoomCity] = useState(null);
  const [a11y, setA11y] = useState(false);
  const [citiesInitialCity, setCitiesInitialCity] = useState(null);
  const [alertsInitialCity, setAlertsInitialCity] = useState(null);

  const refreshCities = useCallback(async () => {
    try {
      const data = await fetchCities();
      if (Array.isArray(data) && data.length > 0) {
        setCities(prev =>
          prev.map(c => {
            const live = data.find(d =>
              (d.name ?? d.city ?? "").toLowerCase() === c.name.toLowerCase()
            );
            return live ? { ...c, aqi: live.aqi ?? c.aqi, pollutant: live.pollutant ?? c.pollutant } : c;
          })
        );
      }
      setLastSync(Date.now());
    } catch {
      setLastSync(Date.now());
    }
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
    checkHealth();
    refreshCities();
    const healthInterval = setInterval(checkHealth, 30000);
    const citiesInterval = setInterval(refreshCities, 60000);
    return () => {
      clearInterval(healthInterval);
      clearInterval(citiesInterval);
    };
  }, [checkHealth, refreshCities]);

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
      case "map":      return <HeroMapPage cities={cities} onCitySelect={c => setZoomCity(c)} setPage={navigateTo} />;
      case "predict":  return <PredictorPage />;
      case "forecast": return <ForecastPage cities={cities} />;
      case "models":   return <ModelComparisonPage />;
      case "cities":   return <DashboardPage cities={cities} initialCity={citiesInitialCity} />;
      case "alerts":   return <AlertsPage cities={cities} initialCity={alertsInitialCity} />;
      case "chat":     return <ChatbotPage cities={cities} />;
      case "about":    return <AboutPage />;
      case "login":    return <AuthPage mode="login" setPage={navigateTo} />;
      case "register": return <AuthPage mode="register" setPage={navigateTo} />;
      case "api":      return <ApiPage />;
      default:         return <NotFoundPage setPage={navigateTo} />;
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
          user={user}
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
