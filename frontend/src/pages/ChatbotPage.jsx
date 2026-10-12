import { useState, useRef, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import { aqiCategory } from "../utils/aqiCategory";
import { chatWithAI } from "../utils/api";

const SUGGESTIONS = [
  "Is it safe to take my child outside in Delhi today?",
  "Is Punjab crop burning affecting North India right now?",
  "Which city has the worst air quality right now?",
  "Should I wear a mask in Faridabad today?",
  "What will Delhi's AQI be like tonight?",
  "How many cities are in the danger zone right now?",
];

function localReply(msg, cities) {
  const lower = msg.toLowerCase();
  if (lower.includes("what is aqi") || lower.includes("explain aqi")) {
    return "AQI (Air Quality Index) is a number from 0–500 that tells you how clean or polluted the air is. India uses 9 pollutants to compute it. **0–50** is Good, **51–100** is Satisfactory, **101–200** is Moderate, **201–300** is Poor, **301–400** is Very Poor, and **400+** is Severe.";
  }
  if (lower.includes("worst") || lower.includes("most polluted")) {
    if (cities.length) {
      const worst = [...cities].sort((a, b) => b.aqi - a.aqi)[0];
      const cat = aqiCategory(worst.aqi);
      return `${worst.data_mode === "snapshot" ? "At the last stored reading" : "Currently"}, **${worst.name}** has the worst air quality with AQI **${worst.aqi}** (${cat.name}).${worst.dominant_pollutant ? ` Dominant pollutant: ${worst.dominant_pollutant}.` : ""}`;
    }
    return "I have no current city readings to rank right now (the live CPCB feed is unavailable and nothing is stored).";
  }
  if (lower.includes("exercise") || lower.includes("run") || lower.includes("outdoor")) {
    const delhi = cities.find(c => c.name === "Delhi");
    if (delhi?.aqi == null) return "I have no current or stored reading for Delhi, so I can't say whether outdoor exercise is advisable. Please check back when data is available.";
    const aqi = delhi.aqi;
    if (aqi > 300) return `With Delhi's current AQI of **${aqi}** (Very Poor/Severe), outdoor exercise is not recommended. If you must go out, wear an N95 mask and minimize exertion.`;
    if (aqi > 200) return `Delhi's AQI is **${aqi}** (Poor). Limit outdoor exercise to under 30 minutes. Early morning (5–7 AM) tends to be slightly better.`;
    if (aqi > 100) return `Delhi's AQI is **${aqi}** (Moderate). Light exercise is fine; avoid heavy cardio outdoors. Sensitive individuals should be cautious.`;
    return `Delhi's AQI is **${aqi}** — reasonably safe for most outdoor activities. Enjoy your workout!`;
  }
  if (lower.includes("pm2.5") || lower.includes("pm 2.5")) {
    return "PM2.5 are ultra-fine particles (≤2.5 micrometers) that penetrate deep into the lungs and bloodstream. Primary sources in India: vehicular emissions, crop burning, industrial pollution, and construction dust. Long-term exposure is linked to cardiovascular and respiratory disease.";
  }
  if (lower.includes("model") || lower.includes("ml") || lower.includes("accurate") || lower.includes("xgboost")) {
    return "Our model is an **XGBoost regressor** trained on 6 years of CPCB data (2015–2020) On a temporal test (train 2015–2018, tune 2019, test Jan–Jul 2020) an XGBoost model tuned on 2019 reached **R² 0.898** and **MAE 15.8 AQI points**; the CPCB formula computed from daily means scored R² 0.842. It takes 9 pollutant readings plus month, year and season as input and outputs a predicted AQI. SHAP values explain which pollutants drive each prediction.";
  }
  if (lower.includes("300") || lower.includes("health") || lower.includes("safe")) {
    return "AQI **300** is classified as **Very Poor**. At this level: everyone may experience health effects, not just sensitive groups. Avoid prolonged outdoor exposure. Use N95 masks outdoors. Keep windows closed and use air purifiers indoors. Children and elderly should stay inside.";
  }
  if (lower.includes("hello") || lower.includes("hi") || lower.includes("hey")) {
    return "Hello! I'm AQI Bot — your air quality assistant for India. Ask me about current city conditions, health advice, pollutants, or how our ML model works.";
  }
  if (lower.includes("clean") || lower.includes("best") || lower.includes("good air")) {
    if (cities.length) {
      const best = [...cities].sort((a, b) => a.aqi - b.aqi)[0];
      return `**${best.name}** ${best.data_mode === "snapshot" ? "had the cleanest air at the last stored reading" : "currently has the cleanest air"}, AQI **${best.aqi}** (${aqiCategory(best.aqi).name}).`;
    }
    return "I have no current city readings to compare right now (the live CPCB feed is unavailable and nothing is stored).";
  }
  const bestCity = cities.length ? [...cities].sort((a, b) => a.aqi - b.aqi)[0] : null;
  if (bestCity) {
    return `I can answer questions about AQI, city conditions, health advice, and pollutants. Try one of the suggestions below. ${bestCity.data_mode === "snapshot" ? "At the last stored reading" : "Currently"} **${bestCity.name}** has the cleanest air at AQI ${bestCity.aqi}.`;
  }
  return "I can answer questions about air quality, pollutants, health advice, and our ML model. Try one of the suggested questions below!";
}

export default function ChatbotPage({ cities }) {
  const [messages, setMessages] = useState([
    { role: "ai", text: "Hello! I'm AQI Bot. Ask me about air quality, city conditions, health advisories, or how our model works.", source: "local" }
  ]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const threadRef = useRef(null);

  useEffect(() => {
    if (threadRef.current) {
      threadRef.current.scrollTop = threadRef.current.scrollHeight;
    }
  }, [messages, typing]);

  const sendMessage = useCallback(async (text) => {
    if (!text.trim() || typing) return;
    const userMsg = text.trim();

    setMessages(m => [...m, { role: "user", text: userMsg }]);
    setInput("");
    setTyping(true);

    try {
      const historySlice = messages.slice(-6).map(m => ({
        role: m.role === "ai" ? "assistant" : "user",
        content: m.text,
      }));
      const data = await chatWithAI(userMsg, cities, historySlice);
      if (data.source === "error") throw new Error(data.reply);
      setMessages(m => [...m, { role: "ai", text: data.reply, source: "groq" }]);
    } catch {
      const reply = localReply(userMsg, cities);
      setMessages(m => [...m, { role: "ai", text: reply, source: "local" }]);
    } finally {
      setTyping(false);
    }
  }, [typing, messages, cities]);

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  return (
    <div className="chatbot-page">
      <div className="chat-hero">
        <div className="mono chat-eyebrow">AI ASSISTANT · GROQ LLaMA · LIVE CITY DATA CONTEXT</div>
        <h1 className="display chat-title">AQI Chatbot</h1>
      </div>

      <div className="chat-layout">
        <div className="chat-window glass-strong">
          <div className="chat-thread" ref={threadRef}>
            {messages.map((m, i) => (
              <div key={i} className={`chat-msg ${m.role}`}>
                {m.role === "ai" && (
                  <div className="chat-bubble-avatar">🤖</div>
                )}
                <div style={{ display: "flex", flexDirection: "column", gap: 4, alignItems: m.role === "ai" ? "flex-start" : "flex-end" }}>
                  <div className="chat-bubble">
                    {m.role === "ai" ? (
                      <ReactMarkdown
                        components={{
                          p: ({ children }) => <p style={{ margin: "6px 0", lineHeight: 1.7 }}>{children}</p>,
                          ul: ({ children }) => <ul style={{ paddingLeft: 20, margin: "8px 0" }}>{children}</ul>,
                          ol: ({ children }) => <ol style={{ paddingLeft: 20, margin: "8px 0" }}>{children}</ol>,
                          li: ({ children }) => <li style={{ margin: "4px 0", lineHeight: 1.6 }}>{children}</li>,
                          strong: ({ children }) => <strong style={{ color: "white", fontWeight: 700 }}>{children}</strong>,
                          b: ({ children }) => <b style={{ color: "white", fontWeight: 700 }}>{children}</b>,
                          h1: ({ children }) => <h1 style={{ color: "#f97316", margin: "10px 0 6px" }}>{children}</h1>,
                          h2: ({ children }) => <h2 style={{ color: "#f97316", margin: "10px 0 6px" }}>{children}</h2>,
                          h3: ({ children }) => <h3 style={{ color: "#f97316", margin: "10px 0 6px" }}>{children}</h3>,
                        }}
                      >
                        {m.text}
                      </ReactMarkdown>
                    ) : m.text}
                  </div>
                  {m.role === "ai" && m.source && (
                    <span className="mono" style={{ fontSize: 9, color: m.source === "groq" ? "#34d27a" : "rgba(255,255,255,0.25)", letterSpacing: "0.1em" }}>
                      {m.source === "groq" ? "● GROQ AI" : "● LOCAL"}
                    </span>
                  )}
                </div>
              </div>
            ))}
            {typing && (
              <div className="chat-msg ai">
                <div className="chat-bubble-avatar">🤖</div>
                <div className="chat-bubble typing">
                  <span /><span /><span />
                </div>
              </div>
            )}
          </div>

          <div className="chat-suggested">
            {SUGGESTIONS.map(s => (
              <button key={s} className="chip" onClick={() => sendMessage(s)}>
                {s}
              </button>
            ))}
          </div>

          <form className="chat-input-row" onSubmit={handleSubmit}>
            <input
              className="chat-input"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ask about air quality…"
              disabled={typing}
            />
            <button type="submit" className="btn-primary chat-send" disabled={typing || !input.trim()}>
              SEND →
            </button>
          </form>
        </div>

        <div className="chat-sidebar">
          <div className="glass-strong chat-stats">
            <div className="mono panel-title" style={{ marginBottom: 12 }}>LIVE CONTEXT</div>
            {cities.slice(0, 6).map(c => {
              const cat = aqiCategory(c.aqi);
              return (
                <div key={c.name} className="chat-stat-row">
                  <span className="mono" style={{ color: "rgba(255,255,255,0.6)", fontSize: 12 }}>{c.name}</span>
                  <span className="mono" style={{ color: cat.color, fontWeight: 700 }}>{c.aqi}</span>
                </div>
              );
            })}
            {cities.length === 0 && (
              <div className="mono" style={{ color: "var(--text-mute)", fontSize: 11 }}>Loading city data…</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
