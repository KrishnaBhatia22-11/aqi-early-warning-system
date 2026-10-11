"""Run baseline development and 2019 validation without test scoring."""

from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import shlex
import subprocess
import sys
from typing import Any
from uuid import uuid4

import pandas as pd

from research.aqi_forecasting.baselines import run_policy_horizon_development
from research.aqi_forecasting.coverage import coverage_summary
from research.aqi_forecasting.data_audit import audit_raw_dataset
from research.aqi_forecasting.forecast_samples import build_forecast_samples
from research.aqi_forecasting.manifest import build_development_manifest
from research.aqi_forecasting.date_utils import parse_calendar_dates
from research.aqi_forecasting.protocol import HORIZONS_DAYS, TARGET_POLICIES, VALIDATION_END
from research.aqi_forecasting.temporal_splits import assign_partition

_RUN_MODULE = "research.aqi_forecasting.run_development"


def _new_run_id(now: datetime | None = None) -> str:
    timestamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{uuid4().hex[:12]}"


def _format_command(arguments: list[str]) -> str:
    if sys.platform == "win32":
        return subprocess.list2cmdline(arguments)
    return shlex.join(arguments)


def _case_counts_by_partition(samples: pd.DataFrame) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for partition in ("train", "validation"):
        rows = samples.loc[samples["partition"].eq(partition)]
        counts[partition] = {
            "cases": int(len(rows)),
            "valid_targets": int(rows["target_valid"].astype(bool).sum()),
            "eligible_forecasts": int(rows["eligible"].astype(bool).sum()),
        }
    return counts


def run_development(
    raw_path: str | Path,
    *,
    run_id: str | None = None,
    run_command: str | None = None,
    started_at_utc: str | None = None,
) -> dict[str, Any]:
    """Construct approved cases and return development/validation summaries."""
    started = datetime.now(timezone.utc)
    run_id = run_id or _new_run_id(started)
    started_at_utc = started_at_utc or started.isoformat()
    audit = audit_raw_dataset(raw_path)
    history = pd.read_csv(raw_path)
    target_dates = parse_calendar_dates(history["Date"], field_name="Date")
    if target_dates.isna().any():
        raise ValueError("Cannot run development with invalid dataset dates")
    development_history = history.loc[
        target_dates.le(VALIDATION_END)
    ].copy()
    runs: list[dict[str, Any]] = []
    for policy in TARGET_POLICIES:
        for horizon in HORIZONS_DAYS:
            samples = assign_partition(
                build_forecast_samples(development_history, horizon, policy)
            )
            unexpected_partitions = set(samples["partition"].dropna()) - {
                "train",
                "validation",
            }
            if unexpected_partitions:
                raise ValueError(
                    f"Unexpected target-date partitions: {sorted(unexpected_partitions)}"
                )
            if samples.empty or samples["target_date"].max() > pd.Timestamp(VALIDATION_END):
                raise AssertionError("Development sample construction reached beyond validation")
            development_samples = samples.loc[
                samples["partition"].isin(["train", "validation"])
            ].copy()
            result = run_policy_horizon_development(
                development_samples,
                development_history,
            )
            result["case_counts_by_partition"] = _case_counts_by_partition(samples)
            result["sample_coverage"] = coverage_summary(samples)
            result["data_sha256"] = audit["sha256"]
            result["data_rows"] = audit["rows"]
            runs.append(result)
    completed_at_utc = datetime.now(timezone.utc).isoformat()
    repository_root = Path(__file__).resolve().parents[2]
    manifest = build_development_manifest(
        audit,
        runs,
        repository_root=repository_root,
        run_id=run_id,
        run_command=run_command or _format_command([sys.executable, "-m", _RUN_MODULE]),
        started_at_utc=started_at_utc,
        completed_at_utc=completed_at_utc,
    )
    manifest["runs"] = runs
    return manifest


def persist_run_record(
    record: dict[str, Any],
    output_directory: str | Path,
    *,
    stdout: str = "",
    stderr: str = "",
) -> tuple[Path, Path]:
    """Write a JSON record and associated log under a new, exclusive run directory."""
    run_id = record.get("run_id")
    if not isinstance(run_id, str) or not run_id or Path(run_id).name != run_id:
        raise ValueError("Record must contain a safe, non-empty run_id")
    if record.get("status") != "completed":
        raise ValueError("Only completed run records may be persisted")
    output_root = Path(output_directory)
    output_root.mkdir(parents=True, exist_ok=True)
    run_directory = output_root / run_id
    run_directory.mkdir(exist_ok=False)

    record_path = run_directory / "run_record.json"
    log_path = run_directory / "run.log"
    record["artifacts"] = {
        "record_json": str(record_path.resolve()),
        "run_log": str(log_path.resolve()),
    }
    with log_path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(f"run_id: {run_id}\n")
        handle.write(f"stage: {record.get('stage', 'unknown')}\n")
        handle.write(f"started_at_utc: {record.get('started_at_utc', 'unknown')}\n")
        handle.write(f"completed_at_utc: {record.get('completed_at_utc', 'unknown')}\n")
        handle.write(f"run_command: {record.get('run_command', 'unknown')}\n")
        handle.write(f"structured_record: {record_path.resolve()}\n")
        handle.write("\n--- captured stdout ---\n")
        handle.write(stdout)
        if stdout and not stdout.endswith("\n"):
            handle.write("\n")
        handle.write("\n--- captured stderr ---\n")
        handle.write(stderr)
        if stderr and not stderr.endswith("\n"):
            handle.write("\n")
    with record_path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(record, handle, indent=2, allow_nan=False)
        handle.write("\n")
    return record_path, log_path


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data",
        type=Path,
        default=root / "data" / "raw" / "city_day.csv",
        help="Raw city-day CSV (default: repository data/raw/city_day.csv)",
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=Path(__file__).resolve().parent / "results",
        help="Directory for new run-record subdirectories (never overwritten)",
    )
    args = parser.parse_args()

    started = datetime.now(timezone.utc)
    run_id = _new_run_id(started)
    command = _format_command([sys.executable, "-m", _RUN_MODULE, *sys.argv[1:]])
    captured_stdout = io.StringIO()
    captured_stderr = io.StringIO()
    with redirect_stdout(captured_stdout), redirect_stderr(captured_stderr):
        record = run_development(
            args.data,
            run_id=run_id,
            run_command=command,
            started_at_utc=started.isoformat(),
        )
    rendered_record = json.dumps(record, indent=2, allow_nan=False)
    record_path, log_path = persist_run_record(
        record,
        args.output_directory,
        stdout=captured_stdout.getvalue() + rendered_record + "\n",
        stderr=captured_stderr.getvalue(),
    )
    print(rendered_record)
    print(f"Run record: {record_path}", file=sys.stderr)
    print(f"Run log: {log_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
