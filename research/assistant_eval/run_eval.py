"""Run the 30-question assistant evaluation against the deployed API (protocol: PROTOCOL.md).

Refuses to start unless PROTOCOL.md and questions.json are committed and unmodified, so the
protocol is provably frozen before the first chat call.

    venv\\Scripts\\python.exe -m research.assistant_eval.run_eval
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
import platform
import re
import sys
import time

import requests

from research.assistant_eval import common as c
from src.data.india_aqi import categorize_aqi

QUESTIONS = c.EVAL_DIR / "questions.json"
PROTOCOL = c.EVAL_DIR / "PROTOCOL.md"
MAX_RETRIES = 3


def assert_protocol_frozen() -> None:
    for path in (PROTOCOL, QUESTIONS, c.EVAL_DIR / "preflight.json", c.EVAL_DIR / "scoring.py"):
        rel = path.relative_to(c.ROOT).as_posix()
        if not c.git("ls-files", "--error-unmatch", rel):
            raise SystemExit(f"{rel} is not committed; commit the protocol before asking anything")
        if c.git("status", "--porcelain=v1", "--", rel):
            raise SystemExit(f"{rel} has uncommitted changes; the protocol must be frozen")


def model_settings() -> dict:
    code = (c.ROOT / "api" / "routes" / "chat.py").read_text(encoding="utf-8")
    model = re.search(r'model="([^"]+)"', code)
    temperature = re.search(r"temperature=([0-9.]+)", code)
    return {"model": model.group(1) if model else None,
            "temperature": float(temperature.group(1)) if temperature else None}


def ground_truth(city: str) -> dict:
    body, latency = c.fetch_cities_full(timeout=90)
    row = c.city_row(body.get("cities", []), city) or {}
    aqi = row.get("aqi")
    return {
        "utc": c.utc_now(), "city": city, "aqi": aqi,
        "category": categorize_aqi(aqi) if isinstance(aqi, (int, float)) else None,
        "city_data_mode": row.get("data_mode"), "city_as_of": row.get("as_of"),
        "dominant_pollutant": row.get("dominant_pollutant"), "station_count": row.get("station_count"),
        "top_data_mode": body.get("data_mode"), "top_as_of_latest": body.get("as_of_latest"),
        "cities_live": body.get("cities_live"), "cities_snapshot": body.get("cities_snapshot"),
        "latency_s": round(latency, 3),
    }


def ask(question: str) -> dict:
    attempts = []
    for attempt in range(MAX_RETRIES + 1):
        started = c.utc_now()
        t0 = time.time()
        try:
            response = requests.post(c.CHAT_URL, json={"message": question, "cities": [], "history": []}, timeout=120)
            latency = time.time() - t0
            record = {"attempt": attempt + 1, "started_utc": started, "latency_s": round(latency, 3),
                      "http_status": response.status_code}
            if response.status_code == 429 or response.status_code >= 500:
                record["retry_reason"] = f"HTTP {response.status_code}"
                attempts.append(record)
                if attempt < MAX_RETRIES:
                    time.sleep(c.RATE_LIMIT_WAIT_S)
                    continue
                return {"attempts": attempts, "response": None, "failed": True}
            record["response"] = response.json()
            attempts.append(record)
            return {"attempts": attempts, "response": record["response"], "failed": False}
        except Exception as error:  # network error / timeout / bad JSON
            attempts.append({"attempt": attempt + 1, "started_utc": started, "latency_s": round(time.time() - t0, 3),
                             "retry_reason": repr(error)})
            if attempt < MAX_RETRIES:
                time.sleep(c.RATE_LIMIT_WAIT_S)
                continue
            return {"attempts": attempts, "response": None, "failed": True}
    return {"attempts": attempts, "response": None, "failed": True}


def main() -> int:
    assert_protocol_frozen()
    spec = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    questions = spec["questions"]
    started = datetime.now(timezone.utc)
    out = c.EVAL_DIR / "results" / started.strftime("%Y%m%dT%H%M%SZ")
    out.mkdir(parents=True)
    raw_path, truth_path = out / "raw_answers.jsonl", out / "ground_truth.jsonl"

    for index, q in enumerate(questions, start=1):
        truth = ground_truth(q["city"])
        result = ask(q["text"])
        reply = result["response"] or {}
        record = {
            "id": q["id"], "city": q["city"], "type": q["type"], "question": q["text"],
            "request": {"message": q["text"], "cities": [], "history": []},
            "response": result["response"], "source": reply.get("source"),
            "answer_failed": bool(result["failed"] or reply.get("source") != "groq"),
            "retries": max(0, len(result["attempts"]) - 1), "attempts": result["attempts"],
            "truth_fetched_utc": truth["utc"],
        }
        with raw_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        with truth_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"id": q["id"], **truth}, ensure_ascii=False) + "\n")
        print(f"[{index:02d}/{len(questions)}] {q['id']} source={record['source']} retries={record['retries']}", flush=True)
        if index < len(questions):
            time.sleep(c.WAIT_BETWEEN_CALLS_S)

    finished = datetime.now(timezone.utc)
    record = {
        "protocol": "research/assistant_eval/PROTOCOL.md",
        "git_commit": c.git("rev-parse", "HEAD"),
        "deployed_commit_claimed": spec["deployed_commit_claimed"],
        "deployed_commit_note": spec["deployed_commit_note"],
        "api_url": c.API_BASE,
        "model_settings_from_code": model_settings(),
        "python": platform.python_version(),
        "utc_start": started.isoformat(), "utc_end": finished.isoformat(),
        "questions_asked": len(questions),
        "output_file_sha256": {},
    }
    for path in sorted(out.iterdir()):
        record["output_file_sha256"][path.name] = c.sha256_file(path)
    record["protocol_file_sha256"] = {p.name: c.sha256_file(p) for p in (PROTOCOL, QUESTIONS, c.EVAL_DIR / "preflight.json")}
    (out / "run_record.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
