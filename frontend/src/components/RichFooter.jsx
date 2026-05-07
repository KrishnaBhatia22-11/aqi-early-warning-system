import { Mail } from "lucide-react";

function LinkedinIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
    </svg>
  );
}

function GithubIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>
    </svg>
  );
}

export default function RichFooter({ setPage }) {
  return (
    <footer className="rich-footer">
      <div className="rich-footer-inner">

        {/* Column 1 — Brand */}
        <div className="rfb-brand">
          <div className="rfb-logo">AQI<span className="bolt">⚡</span></div>
          <p className="rfb-tag">
            Monitoring India's air since 2024.<br />
            Free forever. Open source.<br />
            Built for 1.4 billion Indians.
          </p>
          <div className="rfb-social">
            <a
              href="https://www.linkedin.com/in/krishna-bhatia09/"
              target="_blank" rel="noreferrer"
              className="rfb-social-link rfb-linkedin"
              title="LinkedIn"
              aria-label="LinkedIn profile"
            >
              <LinkedinIcon />
            </a>
            <a
              href="https://github.com/KrishnaBhatia22-11/aqi-early-warning-system"
              target="_blank" rel="noreferrer"
              className="rfb-social-link rfb-github"
              title="GitHub"
              aria-label="GitHub repository"
            >
              <GithubIcon />
            </a>
            <a
              href="mailto:krishnabhatia09@gmail.com"
              className="rfb-social-link rfb-email"
              title="Email"
              aria-label="Send email"
            >
              <Mail size={16} />
            </a>
          </div>
        </div>

        {/* Column 2 — Product */}
        <div>
          <div className="rfb-h">PRODUCT</div>
          <div className="rfb-links">
            <button onClick={() => setPage("map")}>Live Map</button>
            <button onClick={() => setPage("predict")}>AQI Predictor</button>
            <button onClick={() => setPage("health")}>Health Impact</button>
            <button onClick={() => setPage("forecast")}>24H Forecast</button>
            <button onClick={() => setPage("cities")}>City Dashboard</button>
            <button onClick={() => setPage("alerts")}>Alerts</button>
            <button onClick={() => setPage("chat")}>AI Chatbot</button>
          </div>
        </div>

        {/* Column 3 — Developers */}
        <div>
          <div className="rfb-h">DEVELOPERS</div>
          <div className="rfb-links">
            <button onClick={() => setPage("api")}>Public API</button>
            <a
              href="https://github.com/KrishnaBhatia22-11/aqi-early-warning-system"
              target="_blank" rel="noreferrer"
            >
              GitHub Repo
            </a>
            <button onClick={() => setPage("models")}>Model Intelligence</button>
            <button onClick={() => setPage("about")}>About / Team</button>
          </div>
        </div>

      </div>

      {/* Bottom bar */}
      <div className="rfb-bottom">
        <span className="mono">MODEL: XGBoost R²=0.932 · DATA: CPCB 2015–2020 · MAE 21.33</span>
        <span className="rfb-bottom-center">
          Made by Krishna Bhatia ·{" "}
          <a href="mailto:krishnabhatia09@gmail.com" className="rfb-bottom-email">
            krishnabhatia09@gmail.com
          </a>{" "}
          · Manav Rachna International Institute of Research and Studies
        </span>
        <span className="mono">BUILT WITH ❤️ IN FARIDABAD, INDIA · OPEN SOURCE · MIT LICENSE</span>
      </div>
    </footer>
  );
}
