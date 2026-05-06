import { useState } from "react";
import { useAuth } from "../context/AuthContext";

export default function AuthPage({ mode = "login", setPage }) {
  const { login, register } = useAuth();
  const [isLogin, setIsLogin] = useState(mode === "login");
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (isLogin) {
        login({ email: form.email, password: form.password });
      } else {
        if (!form.name.trim()) { setError("Name is required"); setLoading(false); return; }
        if (form.password.length < 6) { setError("Password must be at least 6 characters"); setLoading(false); return; }
        register({ name: form.name, email: form.email, password: form.password });
      }
      setPage("map");
    } catch (err) {
      setError(err.message || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-bg">
        <div className="auth-orb auth-orb-1" />
        <div className="auth-orb auth-orb-2" />
      </div>

      <div className="auth-card glass-strong">
        <div className="auth-logo">AQI<span style={{ color: "#FF6B00" }}>⚡</span></div>
        <div className="mono auth-eyebrow">EARLY WARNING SYSTEM</div>

        <div className="auth-tabs">
          <button
            className={`auth-tab ${isLogin ? "active" : ""}`}
            onClick={() => { setIsLogin(true); setError(""); }}
          >
            SIGN IN
          </button>
          <button
            className={`auth-tab ${!isLogin ? "active" : ""}`}
            onClick={() => { setIsLogin(false); setError(""); }}
          >
            REGISTER
          </button>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {!isLogin && (
            <div className="form-group">
              <label className="mono form-label">FULL NAME</label>
              <input
                type="text"
                className="form-input"
                placeholder="Krishna Bhatia"
                value={form.name}
                onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              />
            </div>
          )}

          <div className="form-group">
            <label className="mono form-label">EMAIL ADDRESS</label>
            <input
              type="email"
              className="form-input"
              placeholder="you@example.com"
              value={form.email}
              onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
              required
            />
          </div>

          <div className="form-group">
            <label className="mono form-label">PASSWORD</label>
            <input
              type="password"
              className="form-input"
              placeholder={isLogin ? "Enter password" : "Min. 6 characters"}
              value={form.password}
              onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
              required
            />
          </div>

          {error && <div className="auth-error mono">{error}</div>}

          <button type="submit" className="btn-primary auth-submit" disabled={loading}>
            {loading ? "AUTHENTICATING…" : isLogin ? "SIGN IN →" : "CREATE ACCOUNT →"}
          </button>
        </form>

        <div className="auth-footer-text mono">
          {isLogin ? (
            <>No account? <button className="auth-link" onClick={() => { setIsLogin(false); setError(""); }}>Register free</button></>
          ) : (
            <>Already have an account? <button className="auth-link" onClick={() => { setIsLogin(true); setError(""); }}>Sign in</button></>
          )}
        </div>

        <div className="auth-skip-row">
          <button className="auth-link mono" onClick={() => setPage("map")}>
            SKIP — CONTINUE WITHOUT ACCOUNT →
          </button>
        </div>

        <div className="auth-disclaimer mono">
          Credentials stored locally in browser. No server-side auth required.
        </div>
      </div>
    </div>
  );
}
