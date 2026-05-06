import { useState, useEffect, useCallback } from "react";
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

const VALID_PAGES = ["map", "predict", "cities", "alerts", "chat", "about", "login", "register", "api"];

function AppInner() {
  const { user } = useAuth();
  const [showIntro, setShowIntro] = useState(() => !sessionStorage.getItem("intro_done"));
  const [page, setPage] = useState("map");
  const [cities, setCities] = useState(CITIES_STATIC);
  const [apiOnline, setApiOnline] = useState(false);
  const [lastSync, setLastSync] = useState(null);
  const [zoomCity, setZoomCity] = useState(null);
  const [a11y, setA11y] = useState(false);

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
    sessionStorage.setItem("intro_done", "1");
    setShowIntro(false);
  }, []);

  const navigateTo = (p) => {
    setPage(VALID_PAGES.includes(p) ? p : "map");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleCitySelect = (city) => setZoomCity(city);

  const renderPage = () => {
    switch (page) {
      case "map":      return <HeroMapPage cities={cities} onCitySelect={handleCitySelect} setPage={navigateTo} />;
      case "predict":  return <PredictorPage />;
      case "cities":   return <DashboardPage cities={cities} />;
      case "alerts":   return <AlertsPage cities={cities} />;
      case "chat":     return <ChatbotPage cities={cities} />;
      case "about":    return <AboutPage />;
      case "login":    return <AuthPage mode="login" setPage={navigateTo} />;
      case "register": return <AuthPage mode="register" setPage={navigateTo} />;
      case "api":      return <ApiPage />;
      default:         return <NotFoundPage setPage={navigateTo} />;
    }
  };

  const nationalAvg = cities.length
    ? Math.round(cities.reduce((s, c) => s + c.aqi, 0) / cities.length)
    : 0;
  const hazardousCities = cities.filter(c => c.aqi > 300);

  return (
    <>
      {/* Main app always rendered — intro sits on top as a fixed overlay */}
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
          {renderPage()}
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
          />
        )}
      </div>

      {/* Intro overlay — removed from DOM once done */}
      {showIntro && <CinematicIntro onDone={handleIntroDone} />}
    </>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppInner />
    </AuthProvider>
  );
}
