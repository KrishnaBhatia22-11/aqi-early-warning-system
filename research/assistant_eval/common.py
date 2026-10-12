"""Shared helpers for the assistant evaluation (API access, fixed protocol constants)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import time
from datetime import datetime, timezone
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = Path(__file__).resolve().parent
API_BASE = "https://aqi-api-y2qs.onrender.com"
CITIES_URL = f"{API_BASE}/api/v1/cities"
CHAT_URL = f"{API_BASE}/api/v1/chat"
PRIMARY_CITIES = ["Delhi", "Mumbai", "Kolkata", "Chennai", "Bengaluru"]
REPLACEMENT_CITIES = ["Hyderabad", "Ahmedabad", "Lucknow", "Patna", "Jaipur"]
MIN_LIVE_CITIES = 20
MIN_COMMIT = "56a68162"
WAIT_BETWEEN_CALLS_S = 7
RATE_LIMIT_WAIT_S = 60


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(*args: str) -> str | None:
    try:
        return subprocess.run(["git", "-C", str(ROOT), *args], check=True, capture_output=True,
                              text=True, encoding="utf-8").stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def has_value(row: dict[str, Any]) -> bool:
    """A city row with an AQI value, whether live or a stored snapshot."""
    aqi = row.get("aqi")
    return bool(row.get("success")) and isinstance(aqi, (int, float)) and aqi > 0


is_live = has_value  # backwards-compatible name used by the first (failed) preflight


def fetch_cities_full(timeout: float = 60) -> tuple[dict[str, Any], float]:
    """Full /cities body (with data_mode / as_of_latest) and latency in seconds."""
    start = time.time()
    response = requests.get(CITIES_URL, timeout=timeout)
    response.raise_for_status()
    return response.json(), time.time() - start


def fetch_cities(timeout: float = 60) -> tuple[list[dict[str, Any]], float]:
    body, latency = fetch_cities_full(timeout)
    return body.get("cities", body.get("data", [])), latency


def city_row(rows: list[dict[str, Any]], city: str) -> dict[str, Any] | None:
    for row in rows:
        if (row.get("city") or row.get("name")) == city:
            return row
    return None
