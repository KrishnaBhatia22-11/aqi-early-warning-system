import { createContext, useContext, useState, useEffect } from "react";

const AuthContext = createContext(null);

function makeToken(payload) {
  const header = btoa(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  const body = btoa(JSON.stringify(payload));
  const sig = btoa(`aqi-${payload.email}-${payload.exp}`);
  return `${header}.${body}.${sig}`;
}

function parseToken(token) {
  try {
    const [, body] = token.split(".");
    return JSON.parse(atob(body));
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);

  useEffect(() => {
    const stored = localStorage.getItem("aqi_token");
    if (stored) {
      const payload = parseToken(stored);
      if (payload && payload.exp > Date.now()) {
        setToken(stored);
        setUser({ name: payload.name, email: payload.email, city: payload.city });
      } else {
        localStorage.removeItem("aqi_token");
      }
    }
  }, []);

  const register = ({ name, email, password, city }) => {
    const users = JSON.parse(localStorage.getItem("aqi_users") || "[]");
    if (users.find(u => u.email === email)) {
      throw new Error("Email already registered");
    }
    const newUser = { name, email, password, city };
    users.push(newUser);
    localStorage.setItem("aqi_users", JSON.stringify(users));
    const payload = { name, email, city, exp: Date.now() + 7 * 24 * 60 * 60 * 1000 };
    const tok = makeToken(payload);
    localStorage.setItem("aqi_token", tok);
    setToken(tok);
    setUser({ name, email, city });
  };

  const login = ({ email, password }) => {
    const users = JSON.parse(localStorage.getItem("aqi_users") || "[]");
    const found = users.find(u => u.email === email && u.password === password);
    if (!found) throw new Error("Invalid email or password");
    const payload = { name: found.name, email, city: found.city, exp: Date.now() + 7 * 24 * 60 * 60 * 1000 };
    const tok = makeToken(payload);
    localStorage.setItem("aqi_token", tok);
    setToken(tok);
    setUser({ name: found.name, email, city: found.city });
  };

  const logout = () => {
    localStorage.removeItem("aqi_token");
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, register, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
