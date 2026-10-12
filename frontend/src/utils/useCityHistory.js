import { useEffect, useState } from "react";
import { fetchHistory } from "./api";

// Real stored history for one city (daily AQI summaries from /api/v1/history/{city}).
// Returns an empty list when the city has no stored readings or the request fails;
// callers hide their chart in that case. Nothing is ever filled in.
export function useCityHistory(city, days = 7) {
  const [state, setState] = useState({ points: [], loading: Boolean(city) });

  useEffect(() => {
    if (!city) { setState({ points: [], loading: false }); return undefined; }
    let cancelled = false;
    setState(s => ({ ...s, loading: true }));
    fetchHistory(city, days)
      .then(d => {
        if (cancelled) return;
        const points = d?.data_available === false ? [] : (d?.history ?? [])
          .filter(p => Number.isFinite(p?.aqi))
          .map(p => ({ date: p.date, aqi: p.aqi }));
        setState({ points, loading: false });
      })
      .catch(() => { if (!cancelled) setState({ points: [], loading: false }); });
    return () => { cancelled = true; };
  }, [city, days]);

  return state;
}
