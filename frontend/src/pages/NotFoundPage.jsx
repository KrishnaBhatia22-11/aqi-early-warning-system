export default function NotFoundPage({ setPage }) {
  return (
    <div className="notfound-page">
      <div className="nf-bg">
        <div className="nf-orb" />
      </div>
      <svg viewBox="0 0 300 200" className="nf-gauge-svg">
        <defs>
          <linearGradient id="nfGrad" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#34d27a" />
            <stop offset="50%" stopColor="#FFB300" />
            <stop offset="100%" stopColor="#c2002a" />
          </linearGradient>
        </defs>
        <path d="M 30 160 A 120 120 0 0 1 270 160" fill="none" stroke="rgba(255,107,0,0.15)" strokeWidth="16" strokeLinecap="round" />
        <path d="M 30 160 A 120 120 0 0 1 270 160" fill="none" stroke="url(#nfGrad)" strokeWidth="4" strokeLinecap="round" opacity="0.4" />
        <line x1="150" y1="160" x2="148" y2="60" stroke="#ef3a4d" strokeWidth="2" strokeLinecap="round" opacity="0.6">
          <animateTransform attributeName="transform" type="rotate" from="-90 150 160" to="0 150 160" dur="2s" fill="freeze" />
        </line>
        <circle cx="150" cy="160" r="6" fill="#ef3a4d" />
        <text x="150" y="200" textAnchor="middle" fontFamily="JetBrains Mono" fontSize="11" fill="rgba(255,107,0,0.6)">SENSOR OFFLINE</text>
      </svg>
      <div className="mono nf-code" style={{ color: "#ef3a4d" }}>404</div>
      <h1 className="display nf-title">Page Not Found</h1>
      <p className="nf-sub">The sensor you're looking for has gone offline. Try navigating back.</p>
      <div className="nf-actions">
        <button className="btn-primary" onClick={() => setPage("map")}>← BACK TO MAP</button>
        <button className="btn-ghost" onClick={() => setPage("predict")}>GO TO PREDICTOR</button>
      </div>
    </div>
  );
}
