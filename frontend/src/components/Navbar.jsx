import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";

const links = [
  { id: "map",      label: "LIVE MAP"  },
  { id: "predict",  label: "PREDICT"   },
  { id: "forecast", label: "FORECAST"  },
  { id: "models",   label: "MODELS"    },
  { id: "cities",   label: "CITIES"    },
  { id: "alerts",   label: "ALERTS"    },
  { id: "chat",     label: "CHATBOT"   },
  { id: "about",    label: "ABOUT"     },
];

export default function Navbar({ page, setPage, apiOnline }) {
  const { user, logout } = useAuth();
  const [scrolled, setScrolled] = useState(false);
  const [time, setTime] = useState("");
  const [a11y, setA11y] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 80);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    const fmt = () => {
      const d = new Date();
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
    document.body.classList.toggle("a11y-mode", a11y);
  }, [a11y]);

  return (
    <div className={`navbar-float-wrap ${scrolled ? "scrolled" : ""}`}>
      <div className="navbar-float">
        <button className="logo logo-btn" onClick={() => setPage("map")}>
          <span>AQI</span><span className="bolt">⚡</span>
        </button>

        <div className="nav-links">
          {links.map(l => (
            <button
              key={l.id}
              className={page === l.id ? "active" : ""}
              onClick={() => setPage(l.id)}
            >
              {l.label}
            </button>
          ))}
        </div>

        <div className="nav-right">
          <span className="live-pulse mono">
            <span className={`lp-dot ${!apiOnline ? "offline" : ""}`}></span> LIVE
          </span>
          <span className="mono nav-time">{time}</span>
          {user ? (
            <>
              <span
                className="mono"
                style={{ fontSize: 10, color: "var(--orange)", cursor: "pointer" }}
                onClick={() => setPage("alerts")}
              >
                {(user.name ?? user.email ?? "USER").split(" ")[0].toUpperCase()}
              </span>
              <button
                className="btn-ghost"
                style={{ padding: "6px 12px", fontSize: 10 }}
                onClick={() => { logout(); setPage("map"); }}
              >
                OUT
              </button>
            </>
          ) : (
            <button
              className="btn-ghost"
              style={{ padding: "6px 12px", fontSize: 10 }}
              onClick={() => setPage("login")}
            >
              SIGN IN
            </button>
          )}
          <button
            className={`a11y-btn ${a11y ? "on" : ""}`}
            title="High-contrast / colorblind mode"
            onClick={() => setA11y(!a11y)}
          >
            👁
          </button>
        </div>
      </div>
    </div>
  );
}
