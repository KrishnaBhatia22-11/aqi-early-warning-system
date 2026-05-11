import { useState, useEffect, useRef, useMemo } from "react";
import { useAuth } from "../context/AuthContext";

const PRIMARY_NAV = [
  { id: "map",      label: "LIVE MAP"  },
  { id: "predict",  label: "PREDICT"   },
  { id: "health",   label: "HEALTH"    },
  { id: "forecast", label: "FORECAST"  },
  { id: "cities",   label: "CITIES"    },
  { id: "compare",  label: "COMPARE"   },
  { id: "history",  label: "HISTORY"   },
];

const MORE_ITEMS = [
  { id: "weather", icon: "🌤", label: "Weather & AQI"      },
  { id: "chat",    icon: "🤖", label: "AI Chatbot"         },
  { id: "alerts",  icon: "🔔", label: "Alerts"             },
  { id: "models",  icon: "🧠", label: "Model Intelligence" },
  { id: "api",     icon: "🔌", label: "Public API"         },
  { id: "about",   icon: "ℹ️", label: "About"              },
];

const MOBILE_PRIMARY = [
  { id: "map",      icon: "🗺",  label: "Live Map"           },
  { id: "predict",  icon: "🎯",  label: "AQI Predictor"      },
  { id: "health",   icon: "❤️",  label: "Health Impact"      },
  { id: "forecast", icon: "📈",  label: "24H Forecast"       },
  { id: "cities",   icon: "🏙",  label: "City Dashboard"     },
  { id: "compare",  icon: "🆚",  label: "Compare Cities"     },
  { id: "history",  icon: "📅",  label: "AQI History"        },
];

const MOBILE_MORE = [
  { id: "weather", icon: "🌤",  label: "Weather & AQI"      },
  { id: "chat",    icon: "🤖",  label: "AI Chatbot"         },
  { id: "alerts",  icon: "🔔",  label: "Alerts"             },
  { id: "models",  icon: "🧠",  label: "Model Intelligence" },
  { id: "api",     icon: "🔌",  label: "Public API"         },
  { id: "about",   icon: "ℹ️",  label: "About"              },
];

export default function Navbar({ page, setPage, apiOnline, a11y, setA11y, cities = [] }) {
  const { user, logout } = useAuth();
  const [time, setTime]         = useState("");
  const [moreOpen, setMoreOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const moreRef = useRef(null);

  const { nationalAvg, hazardous } = useMemo(() => {
    const valid = cities.filter(c => c.aqi && typeof c.aqi === "number" && c.aqi > 0);
    if (!valid.length) return { nationalAvg: null, hazardous: 0 };
    const avg = Math.round(valid.reduce((s, c) => s + c.aqi, 0) / valid.length);
    const haz = valid.filter(c => c.aqi > 400).length;
    return { nationalAvg: avg, hazardous: haz };
  }, [cities]);

  useEffect(() => {
    const fmt = () => {
      const d  = new Date();
      const dd = String(d.getDate()).padStart(2, "0");
      const mm = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"][d.getMonth()];
      const yy = d.getFullYear();
      const hh = String(d.getHours()).padStart(2, "0");
      const mn = String(d.getMinutes()).padStart(2, "0");
      setTime(`${dd} ${mm} ${yy} · ${hh}:${mn} IST`);
    };
    fmt();
    const i = setInterval(fmt, 30000);
    return () => clearInterval(i);
  }, []);

  useEffect(() => {
    if (!moreOpen) return;
    const handler = e => {
      if (moreRef.current && !moreRef.current.contains(e.target)) setMoreOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [moreOpen]);

  useEffect(() => {
    const handler = e => {
      if (e.key === "Escape") { setMoreOpen(false); setMenuOpen(false); }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, []);

  useEffect(() => {
    document.body.style.overflow = menuOpen ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [menuOpen]);

  useEffect(() => {
    document.body.classList.toggle("a11y-mode", !!a11y);
  }, [a11y]);

  const nav = p => { setPage(p); setMoreOpen(false); setMenuOpen(false); };
  const isMoreActive = MORE_ITEMS.some(i => i.id === page);

  return (
    <>
      <div className="navbar-wrapper">

        {/* ── Row 1: Brand Bar ── */}
        <div className="navbar-brand-bar">
          <div className="nbb-left">
            <button className="logo-btn nbb-logo-btn" onClick={() => nav("map")}>
              <img src="/logo.svg" alt="AQI India" style={{ height: 26, width: "auto" }} />
            </button>
            <span className="nbb-system-name mono">AQI EARLY WARNING SYSTEM</span>
          </div>

          <div className="nbb-center mono">
            <span className={`nbb-dot${!apiOnline ? " offline" : ""}`} />
            <span className="nbb-live">LIVE</span>
            {nationalAvg !== null && (
              <>
                <span className="nbb-sep">·</span>
                <span className="nbb-stat">NATIONAL AQI <strong>{nationalAvg}</strong></span>
                {hazardous > 0 && (
                  <>
                    <span className="nbb-sep">·</span>
                    <span className="nbb-hazardous">{hazardous} HAZARDOUS</span>
                  </>
                )}
              </>
            )}
            {time && (
              <>
                <span className="nbb-sep">·</span>
                <span className="nbb-time">{time}</span>
              </>
            )}
          </div>

          <div className="nbb-right">
            {user ? (
              <>
                <span className="mono nbb-user" onClick={() => nav("alerts")}>
                  {(user.name ?? user.email ?? "USER").split(" ")[0].toUpperCase()}
                </span>
                <button className="nbb-auth-btn" onClick={() => { logout(); nav("map"); }}>
                  OUT
                </button>
              </>
            ) : (
              <button className="nbb-auth-btn" onClick={() => nav("login")}>
                SIGN IN
              </button>
            )}
            <button
              className={`a11y-btn${a11y ? " on" : ""}`}
              title="High-contrast / colorblind mode"
              onClick={() => setA11y(!a11y)}
            >
              👁
            </button>
            <button
              className="nbb-hamburger"
              onClick={() => setMenuOpen(true)}
              aria-label="Open navigation menu"
            >
              <span /><span /><span />
            </button>
          </div>
        </div>

        {/* ── Row 2: Nav Bar ── */}
        <div className="navbar-nav-bar">
          <nav className="nav-bar-inner" aria-label="Main navigation">
            {PRIMARY_NAV.map(item => (
              <button
                key={item.id}
                className={`nav-item${page === item.id ? " active" : ""}`}
                onClick={() => nav(item.id)}
              >
                {item.label}
              </button>
            ))}

            <div
              className={`nav-more-wrap${moreOpen ? " open" : ""}`}
              ref={moreRef}
              onMouseEnter={() => setMoreOpen(true)}
              onMouseLeave={() => setMoreOpen(false)}
            >
              <button
                className={`nav-item nav-more-btn${isMoreActive ? " active" : ""}`}
                onClick={() => setMoreOpen(v => !v)}
                aria-expanded={moreOpen}
                aria-haspopup="true"
              >
                MORE
                <span className="nav-more-caret" aria-hidden="true">▾</span>
              </button>
              <div className="nav-more-panel" role="menu">
                {MORE_ITEMS.map(item => (
                  <button
                    key={item.id}
                    className={`nav-more-item${page === item.id ? " current" : ""}`}
                    onClick={() => nav(item.id)}
                    role="menuitem"
                  >
                    <span className="nav-more-icon" aria-hidden="true">{item.icon}</span>
                    <span>{item.label}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="nav-status-pills">
              <span className="nav-status-pill">
                <span className="nsp-dot" />
                10 LIVE
              </span>
              <span className="nav-status-pill">R²=0.932</span>
              <span className="nav-status-pill">BUILD v2.1</span>
            </div>
          </nav>
        </div>

      </div>

      {/* ── Mobile Full-Screen Menu ── */}
      {menuOpen && (
        <div
          className="mobile-nav-overlay"
          onClick={e => { if (e.target === e.currentTarget) setMenuOpen(false); }}
        >
          <div className="mobile-nav-panel">
            <div className="mobile-nav-head">
              <button className="logo-btn" onClick={() => nav("map")}>
                <img src="/logo.svg" alt="AQI India" style={{ height: 32, width: "auto" }} />
              </button>
              <button className="mobile-nav-close" onClick={() => setMenuOpen(false)} aria-label="Close menu">
                ✕
              </button>
            </div>
            <div className="mobile-nav-body">
              <div className="mobile-nav-group">
                <div className="mono mobile-nav-group-label">PRIMARY</div>
                {MOBILE_PRIMARY.map(item => (
                  <button
                    key={item.id}
                    className={`mobile-nav-item${page === item.id ? " current" : ""}`}
                    onClick={() => nav(item.id)}
                  >
                    <span className="mobile-nav-item-icon" aria-hidden="true">{item.icon}</span>
                    <span>{item.label}</span>
                  </button>
                ))}
              </div>
              <div className="mobile-nav-group">
                <div className="mono mobile-nav-group-label">MORE</div>
                {MOBILE_MORE.map(item => (
                  <button
                    key={item.id}
                    className={`mobile-nav-item${page === item.id ? " current" : ""}`}
                    onClick={() => nav(item.id)}
                  >
                    <span className="mobile-nav-item-icon" aria-hidden="true">{item.icon}</span>
                    <span>{item.label}</span>
                  </button>
                ))}
              </div>
              {user ? (
                <div className="mobile-nav-group">
                  <div className="mono mobile-nav-group-label">ACCOUNT</div>
                  <button className="mobile-nav-item" onClick={() => nav("alerts")}>
                    <span className="mobile-nav-item-icon">👤</span>
                    <span>{(user.name ?? user.email ?? "USER").split(" ")[0].toUpperCase()}</span>
                  </button>
                  <button className="mobile-nav-item" onClick={() => { logout(); nav("map"); }}>
                    <span className="mobile-nav-item-icon">🚪</span>
                    <span>Sign Out</span>
                  </button>
                </div>
              ) : (
                <div className="mobile-nav-group">
                  <div className="mono mobile-nav-group-label">ACCOUNT</div>
                  <button className="mobile-nav-item" onClick={() => nav("login")}>
                    <span className="mobile-nav-item-icon">🔑</span>
                    <span>Sign In</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
