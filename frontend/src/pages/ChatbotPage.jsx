import { useState, useRef, useEffect } from "react";
import { aqiCategory } from "../utils/aqiCategory";

const SUGGESTIONS = [
  "What is AQI?",
  "Which city has worst air today?",
  "Is it safe to exercise in Delhi?",
  "What causes PM2.5 pollution?",
  "How accurate is your ML model?",
  "What does AQI 300 mean for my health?",
];

function generateReply(msg, cities) {
  const lower = msg.toLowerCase();
  if (lower.includes("what is aqi") || lower.includes("explain aqi")) {
    return "AQI (Air Quality Index) is a number from 0–500 that tells you how clean or polluted the air is. India uses 9 pollutants to compute it. **0–50** is Good, **51–100** is Satisfactory, **101–200** is Moderate, **201–300** is Poor, **301–400** is Very Poor, and **400+** is Severe.";
  }
  if (lower.includes("worst") || lower.includes("most polluted")) {
    if (cities.length) {
      const worst = [...cities].sort((a, b) => b.aqi - a.aqi)[0];
      const cat = aqiCategory(worst.aqi);
      return `Currently, **${worst.name}** has the worst air quality with AQI **${worst.aqi}** (${cat.name}). Primary pollutant: ${worst.pollutant}.`;
    }
    return "Based on historical data, Delhi and Lucknow frequently top the charts for worst air quality in India, especially during winter months (Nov–Feb).";
  }
  if (lower.includes("exercise") || lower.includes("run") || lower.includes("outdoor")) {
    const delhi = cities.find(c => c.name === "Delhi");
    const aqi = delhi?.aqi ?? 250;
    if (aqi > 300) return `With Delhi's current AQI of **${aqi}** (Very Poor/Severe), outdoor exercise is not recommended. If you must go out, wear an N95 mask and minimize exertion.`;
    if (aqi > 200) return `Delhi's AQI is **${aqi}** (Poor). Limit outdoor exercise to under 30 minutes. Early morning (5–7 AM) tends to be slightly better.`;
    if (aqi > 100) return `Delhi's AQI is **${aqi}** (Moderate). Light exercise is fine; avoid heavy cardio outdoors. Sensitive individuals should be cautious.`;
    return `Delhi's AQI is **${aqi}** — reasonably safe for most outdoor activities. Enjoy your workout!`;
  }
  if (lower.includes("pm2.5") || lower.includes("pm 2.5")) {
    return "PM2.5 are ultra-fine particles (≤2.5 micrometers) that penetrate deep into the lungs and bloodstream. Primary sources in India: vehicular emissions, crop burning, industrial pollution, and construction dust. Long-term exposure is linked to cardiovascular and respiratory disease.";
  }
  if (lower.includes("model") || lower.includes("ml") || lower.includes("accurate") || lower.includes("xgboost")) {
    return "Our model is an **XGBoost regressor** trained on 6 years of CPCB data (2015–2020, 29,531 rows, 26 cities) with **R²=0.932** and **MAE=21.33 AQI units**. It takes 9 pollutant readings as input and outputs a predicted AQI. SHAP values explain which pollutants drive each prediction.";
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
      return `**${best.name}** currently has the cleanest air at AQI **${best.aqi}** (${aqiCategory(best.aqi).name}).`;
    }
    return "Cities in South India — Chennai, Kochi, Coimbatore, Thiruvananthapuram — typically have the cleanest air in India due to sea breeze and less industrial activity.";
  }
  const bestCity = cities.length ? [...cities].sort((a, b) => a.aqi - b.aqi)[0] : null;
  if (bestCity) {
    return `I can answer questions about AQI, city conditions, health advice, and pollutants. Try one of the suggestions below. Currently **${bestCity.name}** has the cleanest air at AQI ${bestCity.aqi}.`;
  }
  return "I can answer questions about air quality, pollutants, health advice, and our ML model. Try one of the suggested questions below!";
}

export default function ChatbotPage({ cities }) {
  const [messages, setMessages] = useState([
    { role: "ai", text: "Hello! I'm AQI Bot. Ask me about air quality, city conditions, health advisories, or how our model works." }
  ]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const threadRef = useRef(null);

  useEffect(() => {
    if (threadRef.current) {
      threadRef.current.scrollTop = threadRef.current.scrollHeight;
    }
  }, [messages, typing]);

  const sendMessage = (text) => {
    if (!text.trim() || typing) return;
    const userMsg = text.trim();
    setMessages(m => [...m, { role: "user", text: userMsg }]);
    setInput("");
    setTyping(true);
    setTimeout(() => {
      const reply = generateReply(userMsg, cities);
      setMessages(m => [...m, { role: "ai", text: reply }]);
      setTyping(false);
    }, 700 + Math.random() * 500);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  return (
    <div className="chatbot-page">
      <div className="chat-hero">
        <div className="mono chat-eyebrow">AI ASSISTANT · LIVE CITY DATA CONTEXT</div>
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
                <div
                  className="chat-bubble"
                  dangerouslySetInnerHTML={{
                    __html: m.text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
                  }}
                />
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
