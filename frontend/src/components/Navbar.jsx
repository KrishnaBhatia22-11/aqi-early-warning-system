import { useState, useEffect, useRef } from "react";
import { useAuth } from "../context/AuthContext";

const NAV_GROUPS = [
  {
    id: "explore", label: "EXPLORE",
    items: [
      { id: "map",    icon: "🗺", label: "Live Map",       desc: "Real-time AQI across 26 Indian cities" },
      { id: "cities", icon: "🏙", label: "City Dashboard", desc: "Drill into any city's pollution data"   },
    ],
  },
  {
    id: "tools", label: "TOOLS",
    items: [
      { id: "predict",  icon: "🎯", label: "AQI Predictor",  desc: "XGBoost R²=0.932 — predict any pollutant mix" },
      { id: "health",   icon: "❤️", label: "Health Impact",  desc: "What is this air doing to your body?"         },
      { id: "forecast", icon: "📈", label: "24H Forecast",   desc: "Hourly AQI prediction with confidence bands"  },
      { id: "chat",     icon: "🤖", label: "AI Chatbot",     desc: "Ask anything about air quality"               },
      { id: "alerts",   icon: "🔔", label: "Alerts",         desc: "Get notified when AQI crosses your threshold" },
    ],
  },
  {
    id: "data", label: "DATA",
    items: [
      { id: "models", icon: "🧠", label: "Model Intelligence", desc: "How we chose XGBoost over 3 models"      },
      { id: "api",    icon: "🔌", label: "Public API",         desc: "Use our prediction API in your own app" },
    ],
  },
];

export default function Navbar({ page, setPage, apiOnline, a11y, setA11y }) {
  const { user, logout } = useAuth();
  const [scrolled, setScrolled]   = useState(false);
  const [time, setTime]           = useState("");
  const [openGroup, setOpenGroup] = useState(null);
  const [menuOpen, setMenuOpen]   = useState(false);
  const closeTimer = useRef(null);
  const navRef     = useRef(null);

  const activeGroup = NAV_GROUPS.find(g => g.items.some(i => i.id === page))?.id ?? null;

  // Clock
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

  // Scroll
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 80);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // ESC closes all menus
  useEffect(() => {
    const onKey = e => { if (e.key === "Escape") { setOpenGroup(null); setMenuOpen(false); } };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  // Click outside closes dropdown
  useEffect(() => {
    const onClick = e => {
      if (navRef.current && !navRef.current.contains(e.target)) setOpenGroup(null);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  // Lock body scroll when mobile menu open
  useEffect(() => {
    document.body.style.overflow = menuOpen ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [menuOpen]);

  // a11y body class
  useEffect(() => {
    document.body.classList.toggle("a11y-mode", !!a11y);
  }, [a11y]);

  const hoverEnter = id => { clearTimeout(closeTimer.current); setOpenGroup(id); };
  const hoverLeave = ()  => { closeTimer.current = setTimeout(() => setOpenGroup(null), 130); };

  const nav = p => { setPage(p); setOpenGroup(null); setMenuOpen(false); };

  return (
    <>
      <div className={`navbar-float-wrap ${scrolled ? "scrolled" : ""}`} ref={navRef}>
        <div className="navbar-float">

          {/* Logo */}
          <button className="logo logo-btn" onClick={() => nav("map")}>
            <span>AQI</span><span className="bolt">⚡</span>
          </button>

          {/* Desktop dropdown nav */}
          <nav className="nav-center" aria-label="Main navigation">
            {NAV_GROUPS.map(group => (
              <div
                key={group.id}
                className={`nav-group-wrap${openGroup === group.id ? " dd-open" : ""}`}
                onMouseEnter={() => hoverEnter(group.id)}
                onMouseLeave={hoverLeave}
              >
                <button
                  className={`nav-group-btn${activeGroup === group.id ? " active" : ""}`}
                  aria-expanded={openGroup === group.id}
                  aria-haspopup="true"
                >
                  {group.label}
                  <span className="nav-caret" aria-hidden="true">▾</span>
                </button>

                <div className="nav-dropdown" role="menu" aria-label={group.label}>
                  {group.items.map(item => (
                    <button
                      key={item.id}
                      className={`nav-dd-item${page === item.id ? " nav-dd-current" : ""}`}
                      onClick={() => nav(item.id)}
                      role="menuitem"
                    >
                      <span className="nav-dd-icon" aria-hidden="true">{item.icon}</span>
                      <span className="nav-dd-body">
                        <span className="nav-dd-label">{item.label}</span>
                        <span className="nav-dd-desc">{item.desc}</span>
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            ))}

            <button
              className={`nav-group-btn${page === "about" ? " active" : ""}`}
              onClick={() => nav("about")}
            >
              ABOUT
            </button>
          </nav>

          {/* Right side */}
          <div className="nav-right">
            <span className="live-pulse mono">
              <span className={`lp-dot${!apiOnline ? " offline" : ""}`} /> LIVE
            </span>
            <span className="mono nav-time">{time}</span>
            {user ? (
              <>
                <span className="mono nav-user" onClick={() => nav("alerts")}>
                  {(user.name ?? user.email ?? "USER").split(" ")[0].toUpperCase()}
                </span>
                <button
                  className="btn-ghost"
                  style={{ padding: "6px 12px", fontSize: 10 }}
                  onClick={() => { logout(); nav("map"); }}
                >
                  OUT
                </button>
              </>
            ) : (
              <button
                className="btn-ghost"
                style={{ padding: "6px 12px", fontSize: 10 }}
                onClick={() => nav("login")}
              >
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
              className="nav-hamburger"
              onClick={() => setMenuOpen(true)}
              aria-label="Open navigation menu"
            >
              <span /><span /><span />
            </button>
          </div>

        </div>
      </div>

      {/* Mobile full-screen menu */}
      {menuOpen && (
        <div
          className="mobile-nav-overlay"
          onClick={e => { if (e.target === e.currentTarget) setMenuOpen(false); }}
        >
          <div className="mobile-nav-panel">
            <div className="mobile-nav-head">
              <button className="logo logo-btn" onClick={() => nav("map")}>
                <span>AQI</span><span className="bolt">⚡</span>
              </button>
              <button className="mobile-nav-close" onClick={() => setMenuOpen(false)} aria-label="Close menu">
                ✕
              </button>
            </div>

            <div className="mobile-nav-body">
              {NAV_GROUPS.map(group => (
                <div key={group.id} className="mobile-nav-group">
                  <div className="mono mobile-nav-group-label">{group.label}</div>
                  {group.items.map(item => (
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
              ))}
              <div className="mobile-nav-group">
                <button
                  className={`mobile-nav-item${page === "about" ? " current" : ""}`}
                  onClick={() => nav("about")}
                >
                  <span className="mobile-nav-item-icon" aria-hidden="true">ℹ️</span>
                  <span>About</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
