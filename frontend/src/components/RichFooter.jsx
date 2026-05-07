export default function RichFooter({ setPage }) {
  return (
    <footer className="rich-footer">
      <div className="rich-footer-inner">
        <div>
          <div className="rfb-logo">AQI<span className="bolt">⚡</span></div>
          <p className="rfb-tag">Monitoring India's air since 2024. Free forever. Open source. Built for 1.4 billion Indians.</p>
          <div className="rfb-social">
            <a title="GitHub" href="https://github.com/KrishnaBhatia22-11/aqi-early-warning-system" target="_blank" rel="noreferrer">⌥</a>
            <a title="Twitter / X">𝕏</a>
            <a title="LinkedIn">in</a>
            <a title="Email">✉</a>
          </div>
        </div>
        <div>
          <div className="rfb-h">PRODUCT</div>
          <div className="rfb-links">
            <a onClick={() => setPage("map")}>Live Map</a>
            <a onClick={() => setPage("predict")}>Predictor</a>
            <a onClick={() => setPage("cities")}>City Dashboard</a>
            <a onClick={() => setPage("alerts")}>Alerts</a>
            <a onClick={() => setPage("chat")}>Chatbot</a>
          </div>
        </div>
        <div>
          <div className="rfb-h">DEVELOPERS</div>
          <div className="rfb-links">
            <a onClick={() => setPage("api")}>Public API</a>
            <a href="https://github.com/KrishnaBhatia22-11/aqi-early-warning-system" target="_blank" rel="noreferrer">GitHub Repo</a>
            <a href="https://aqi-api-y2qs.onrender.com/docs" target="_blank" rel="noreferrer">API Docs</a>
            <a onClick={() => setPage("about")}>About / Team</a>
          </div>
        </div>
      </div>
      <div className="rfb-bottom">
        <span>MODEL: XGBOOST R²=0.932 · DATA: CPCB 2015–2020 · MAE 21.33</span>
        <span>BUILT WITH ❤ IN FARIDABAD, INDIA · OPEN SOURCE · MIT LICENSE</span>
      </div>
    </footer>
  );
}
