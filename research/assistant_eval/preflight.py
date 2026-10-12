"""Preflight (snapshot-mode amendment): commit check, wake the API, require >= 20 cities with a value.

Accepts data_mode "live" or "snapshot". Writes preflight.json (and removes any old
PREFLIGHT_FAILED.md) on success; writes PREFLIGHT_FAILED.md and exits non-zero on failure.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time

from research.assistant_eval import common as c

FAILED = c.EVAL_DIR / "PREFLIGHT_FAILED.md"


def fail(reasons: list[str]) -> int:
    FAILED.write_text("# Preflight failed\n\nNo questions were asked.\n\n" + "\n".join(f"- {r}" for r in reasons) + "\n",
                      encoding="utf-8")
    print("PREFLIGHT FAILED:", *reasons, sep="\n  ", file=sys.stderr)
    return 1


def git_ok(*args: str) -> bool:
    return subprocess.run(["git", "-C", str(c.ROOT), *args], capture_output=True).returncode == 0


def choose_cities(rows: list[dict]) -> tuple[list[str], list[dict]]:
    chosen, replacements, spare = [], [], list(c.REPLACEMENT_CITIES)
    for city in c.PRIMARY_CITIES:
        row = c.city_row(rows, city)
        if row is not None and c.has_value(row):
            chosen.append(city)
            continue
        while spare:
            candidate = spare.pop(0)
            row = c.city_row(rows, candidate)
            if row is not None and c.has_value(row):
                chosen.append(candidate)
                replacements.append({"replaced": city, "with": candidate})
                break
        else:
            raise RuntimeError(f"no replacement with a value for {city}")
    return chosen, replacements


def main() -> int:
    head = c.git("rev-parse", "HEAD")
    problems = []
    if c.git("rev-parse", "--abbrev-ref", "HEAD") != "main":
        problems.append("branch is not main")
    if not git_ok("merge-base", "--is-ancestor", c.MIN_COMMIT, "HEAD"):
        problems.append(f"HEAD {head} does not contain {c.MIN_COMMIT}")
    dirty = c.git("status", "--porcelain=v1", "--untracked-files=no")
    if dirty:
        problems.append(f"working tree not clean: {dirty!r}")
    if problems:
        return fail(problems)

    deadline, body, attempts, last_error, with_value = time.time() + 180, None, 0, None, []
    while time.time() < deadline:
        attempts += 1
        try:
            body, _ = c.fetch_cities_full(timeout=60)
            with_value = [r for r in body.get("cities", []) if c.has_value(r)]
            if len(with_value) >= c.MIN_LIVE_CITIES:
                break
        except Exception as error:
            last_error = repr(error)
        time.sleep(15)
    if body is None:
        return fail([f"API did not answer GET /cities within 3 minutes (last error {last_error})"])
    if len(with_value) < c.MIN_LIVE_CITIES:
        return fail([f"only {len(with_value)} of {len(body.get('cities', []))} cities have a value "
                     f"(need {c.MIN_LIVE_CITIES}); data_mode={body.get('data_mode')}"])

    rows = body["cities"]
    chosen, replacements = choose_cities(rows)
    snapshot = {
        "utc": c.utc_now(), "git_head": head, "deployed_commit_claimed": head, "attempts": attempts,
        "data_mode": body.get("data_mode"), "as_of_latest": body.get("as_of_latest"),
        "cities_live": body.get("cities_live"), "cities_snapshot": body.get("cities_snapshot"),
        "cities_with_value": len(with_value), "total_rows": len(rows),
        "chosen_cities": chosen, "replacements": replacements,
        "per_city": {r.get("city"): {k: r.get(k) for k in ("aqi", "category", "data_mode", "as_of", "dominant_pollutant", "station_count")}
                     for r in rows},
    }
    (c.EVAL_DIR / "preflight.json").write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    if FAILED.exists():
        FAILED.unlink()
    print(json.dumps({k: snapshot[k] for k in ("deployed_commit_claimed", "data_mode", "as_of_latest", "cities_with_value", "chosen_cities", "replacements")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
