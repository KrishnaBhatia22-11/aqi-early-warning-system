// Feed state helpers. Everything here is derived from what /api/v1/cities returned;
// nothing is assumed when a field is missing.

export function feedFromResponse(data) {
  return {
    mode: data?.data_mode ?? "unknown",          // "live" | "snapshot" | "unavailable" | "unknown"
    asOfLatest: data?.as_of_latest ?? null,
    citiesLive: Number.isFinite(data?.cities_live) ? data.cities_live : null,
    citiesSnapshot: Number.isFinite(data?.cities_snapshot) ? data.cities_snapshot : null,
  };
}

export function formatAsOf(iso) {
  if (!iso) return "unknown time";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "unknown time";
  return d.toLocaleString(undefined, {
    day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

export function formatAge(iso, now = Date.now()) {
  if (!iso) return "age unknown";
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return "age unknown";
  const minutes = Math.max(0, Math.round((now - t) / 60000));
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 48) return `${hours} hour${hours === 1 ? "" : "s"} ago`;
  const days = Math.round(hours / 24);
  return `${days} days ago`;
}

// Sum of the per-city station counts the API reported; null when none were reported.
export function totalStations(cities) {
  const counts = (cities ?? []).map(c => c.station_count).filter(n => Number.isFinite(n) && n > 0);
  return counts.length ? counts.reduce((a, b) => a + b, 0) : null;
}

export const isSnapshot = feed => feed?.mode === "snapshot";
export const isLive = feed => feed?.mode === "live";
