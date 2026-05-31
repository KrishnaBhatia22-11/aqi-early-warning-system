import { useState } from "react";

// Mirrors the backend _slugify in api/routes/share.py so the share link resolves.
function slugify(s) {
  return String(s || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

const BACKEND = "https://aqi-api-y2qs.onrender.com";

/**
 * Share the live air quality for a city. The link points at the backend share
 * landing (which unfurls a live OG card on WhatsApp/Twitter/LinkedIn) and then
 * redirects humans into the app. Uses the native share sheet on mobile, with a
 * clipboard + "Link copied" fallback everywhere else. No external UI library.
 */
export default function ShareButton({ city }) {
  const [copied, setCopied] = useState(false);
  const [hover, setHover] = useState(false);

  if (!city) return null;

  const shareUrl = `${BACKEND}/api/v1/share/${slugify(city)}`;
  const shareText = `${city} air quality is live right now — see the forecast:`;

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({ title: `${city} AQI`, text: shareText, url: shareUrl });
      } catch {
        /* user dismissed the native share sheet — nothing to do */
      }
      return;
    }
    try {
      await navigator.clipboard.writeText(`${shareText} ${shareUrl}`);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard unavailable (insecure context) — fail silently */
    }
  };

  const accent = copied ? "#34d27a" : "#FF6B00";

  return (
    <button
      type="button"
      onClick={handleShare}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      title={`Share ${city} air quality`}
      aria-label={`Share ${city} air quality`}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
        padding: "9px 18px",
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: 12,
        letterSpacing: "0.12em",
        textTransform: "uppercase",
        color: copied ? accent : hover ? "#FF6B00" : "#f3f1ee",
        background: copied ? "rgba(52,210,122,0.10)" : "rgba(255,107,0,0.10)",
        border: `1px solid ${copied ? "rgba(52,210,122,0.5)" : hover ? "#FF6B00" : "rgba(255,107,0,0.35)"}`,
        borderRadius: 10,
        cursor: "pointer",
        transition: "all 160ms ease",
        whiteSpace: "nowrap",
      }}
    >
      {copied ? (
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor"
             strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <polyline points="20 6 9 17 4 12" />
        </svg>
      ) : (
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor"
             strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <circle cx="18" cy="5" r="3" />
          <circle cx="6" cy="12" r="3" />
          <circle cx="18" cy="19" r="3" />
          <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
          <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
        </svg>
      )}
      {copied ? "Link copied" : "Share"}
    </button>
  );
}
