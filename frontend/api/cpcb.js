// India relay for the CPCB live feed on data.gov.in.
//
// Since mid-October 2026 api.data.gov.in refuses connections from servers
// outside India: every pull from the Render backend failed with "Connection
// refused" / "No route to host", while the same key worked from a browser in
// India. This function runs in Vercel's Mumbai region (see vercel.json), makes
// the request from an Indian IP, and hands the body back unchanged.
//
// It is not an open proxy: it serves only the one CPCB resource, only GET,
// only a bounded page window, and only to callers presenting the shared token.
// The data.gov.in key lives in this project's environment variables and never
// travels to the caller.
//
// Environment (Vercel → Project → Settings → Environment Variables):
//   DATA_GOV_API_KEY   the data.gov.in key
//   CPCB_RELAY_TOKEN   a long random secret, also set on the Render backend

import { timingSafeEqual } from "node:crypto";

const RESOURCE_ID = "3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69";
const UPSTREAM = `https://api.data.gov.in/resource/${RESOURCE_ID}`;
const MAX_LIMIT = 1000;
const UPSTREAM_TIMEOUT_MS = 25000;

// data.gov.in silently hangs on requests without a browser User-Agent.
const UPSTREAM_HEADERS = {
  "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
    "(KHTML, like Gecko) Chrome/140.0 Safari/537.36",
  Accept: "application/json",
};

function tokenMatches(given, expected) {
  if (typeof given !== "string" || !expected) return false;
  const a = Buffer.from(given);
  const b = Buffer.from(expected);
  return a.length === b.length && timingSafeEqual(a, b);
}

function intParam(raw, fallback) {
  if (raw === undefined || raw === "") return fallback;
  const text = Array.isArray(raw) ? raw[0] : String(raw);
  return /^\d+$/.test(text) ? Number(text) : NaN;
}

export default async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");
  res.setHeader("X-Relay-Region", process.env.VERCEL_REGION || "unknown");

  if (req.method !== "GET") {
    res.setHeader("Allow", "GET");
    return res.status(405).json({ error: "method not allowed" });
  }

  const key = process.env.DATA_GOV_API_KEY;
  const token = process.env.CPCB_RELAY_TOKEN;
  if (!key || !token) {
    return res.status(500).json({ error: "relay not configured" });
  }
  if (!tokenMatches(req.headers["x-relay-token"], token)) {
    return res.status(401).json({ error: "unauthorized" });
  }

  const offset = intParam(req.query.offset, 0);
  const limit = intParam(req.query.limit, MAX_LIMIT);
  if (!Number.isSafeInteger(offset) || !Number.isSafeInteger(limit) || limit < 1 || limit > MAX_LIMIT) {
    return res.status(400).json({ error: "offset and limit must be integers, 1 <= limit <= 1000" });
  }

  const url = new URL(UPSTREAM);
  url.searchParams.set("api-key", key);
  url.searchParams.set("format", "json");
  url.searchParams.set("offset", String(offset));
  url.searchParams.set("limit", String(limit));

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), UPSTREAM_TIMEOUT_MS);
  try {
    const upstream = await fetch(url, { headers: UPSTREAM_HEADERS, signal: controller.signal });
    const body = await upstream.text();
    res.setHeader("Content-Type", upstream.headers.get("content-type") || "application/json");
    return res.status(upstream.status).send(body);
  } catch (error) {
    // Never echo the URL: it carries the key.
    const reason = error && error.name === "AbortError" ? "timeout" : (error && error.name) || "error";
    return res.status(502).json({ error: "data.gov.in unreachable from relay", reason });
  } finally {
    clearTimeout(timer);
  }
}
