"""Reproducibility metadata for AQI forecasting research runs."""

from __future__ import annotations

import hashlib
import json
import platform
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import subprocess
from typing import Any

import numpy as np
import pandas as pd

from research.aqi_forecasting.protocol import (
    AQI_LAGS_DAYS,
    CALENDAR_FEATURE_COLUMNS,
    HORIZONS_DAYS,
    PRIMARY_FEATURE_COLUMNS,
    TARGET_POLICIES,
    TEST_END,
    TEST_START,
    TRAIN_END,
    TRAIN_START,
    VALIDATION_END,
    VALIDATION_START,
)

_SOURCE_SUFFIXES = {".json", ".md", ".py", ".txt"}
_IGNORED_SOURCE_DIRS = {"__pycache__", ".mypy_cache", ".pytest_cache", "results"}
_VERIFIED_KAGGLE_VERSION_12_SHA256 = (
    "0d84b21c3e4878bbad8df362f2ab05f61ad959538dddf5918e714077ed3c1847"
)


def _package_version(package: str) -> str | None:
    try:
        return version(package)
    except PackageNotFoundError:
        return None


def fingerprint_research_sources(repository_root: str | Path) -> dict[str, Any]:
    """Hash research source files by sorted relative path and exact file bytes."""
    root = Path(repository_root).resolve()
    research_root = root / "research"
    files: list[Path] = []
    if research_root.is_dir():
        for path in research_root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in _SOURCE_SUFFIXES:
                continue
            relative = path.relative_to(research_root)
            if any(part in _IGNORED_SOURCE_DIRS for part in relative.parts):
                continue
            files.append(path)

    relative_paths = sorted(path.relative_to(root).as_posix() for path in files)
    digest = hashlib.sha256()
    for relative_path in relative_paths:
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update((root / Path(relative_path)).read_bytes())
        digest.update(b"\0")
    return {
        "algorithm": "sha256",
        "sha256": digest.hexdigest(),
        "file_count": len(relative_paths),
        "files": relative_paths,
    }


def collect_code_identity(repository_root: str | Path) -> dict[str, Any]:
    """Capture Git identity and research-source fingerprint without modifying Git."""
    root = Path(repository_root).resolve()

    def git(*args: str) -> str | None:
        try:
            result = subprocess.run(
                ["git", "-C", str(root), *args],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            return None
        return result.stdout.strip()

    revision = git("rev-parse", "HEAD")
    status = git("status", "--porcelain=v1", "--untracked-files=all")
    status_lines = status.splitlines() if status is not None else None
    tracked_changes: list[str] | None = None
    untracked_files: list[str] | None = None
    if status_lines is not None:
        tracked_changes = [line for line in status_lines if not line.startswith("??")]
        untracked_files = [line[3:] for line in status_lines if line.startswith("??")]

    return {
        "git_revision": revision,
        "git_revision_status": "known" if revision else "unavailable",
        "working_tree_status": "known" if status_lines is not None else "unavailable",
        "working_tree_clean": not status_lines if status_lines is not None else None,
        "tracked_changes": tracked_changes,
        "untracked_files": untracked_files,
        "research_source_fingerprint": fingerprint_research_sources(root),
    }


def _runtime_metadata() -> dict[str, Any]:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "operating_system": platform.system(),
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "scikit_learn": _package_version("scikit-learn"),
        "scipy": _package_version("scipy"),
        "joblib": _package_version("joblib"),
        "threadpoolctl": _package_version("threadpoolctl"),
        "python_dateutil": _package_version("python-dateutil"),
        "pytz": _package_version("pytz"),
        "tzdata": _package_version("tzdata"),
        "six": _package_version("six"),
    }


def build_manifest(
    data_audit: dict[str, Any],
    *,
    policy: str,
    horizon_days: int,
    coverage: dict[str, Any],
    code_revision: str | None = None,
    revision_checked: bool = False,
    seeds: dict[str, int] | None = None,
    discrepancies: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build protocol metadata without fabricating model metrics."""
    if horizon_days not in HORIZONS_DAYS:
        raise ValueError(f"Unsupported horizon {horizon_days}")
    if policy not in TARGET_POLICIES:
        raise ValueError(f"Unsupported policy {policy!r}")
    if code_revision is not None and not code_revision.strip():
        raise ValueError("code_revision must be a non-empty revision identifier or None")
    revision_status = (
        "known"
        if code_revision is not None
        else "unavailable"
        if revision_checked
        else "not_checked"
    )
    if seeds is not None and any(
        not isinstance(value, int) or isinstance(value, bool) for value in seeds.values()
    ):
        raise ValueError("Seed values must be integers")
    return {
        "study": "daily_aqi_forecasting",
        "stage": "data_and_protocol",
        "model_trained": False,
        "model_metrics": None,
        "data": {
            key: data_audit.get(key)
            for key in (
                "path",
                "file_size_bytes",
                "sha256",
                "rows",
                "columns",
                "column_names",
                "dtypes",
                "date_min",
                "date_max",
                "city_labels",
                "city_count",
                "invalid_date_rows",
                "duplicate_city_date_excess",
            )
        },
        "code_revision": code_revision,
        "code_revision_status": revision_status,
        "environment": {
            **_runtime_metadata(),
        },
        "target_policy": policy,
        "horizon_days": int(horizon_days),
        "supported_horizons_days": list(HORIZONS_DAYS),
        "feature_columns": list(PRIMARY_FEATURE_COLUMNS),
        "aqi_lags_days": list(AQI_LAGS_DAYS),
        "calendar_features": [
            "target month sine/cosine",
            "target weekday sine/cosine (Monday=0)",
        ],
        "split_dates": {
            "train": [TRAIN_START, TRAIN_END],
            "validation": [VALIDATION_START, VALIDATION_END],
            "test": [TEST_START, TEST_END],
        },
        "eligibility": (
            "Valid target and exact policy-valid AQI at origin, origin-1d, origin-7d"
        ),
        "seeds": (
            {"status": "recorded", "values": dict(seeds)}
            if seeds is not None
            else {
                "status": "not_applicable",
                "values": {},
                "reason": "No stochastic model or training operation is represented by this manifest.",
            }
        ),
        "coverage": coverage,
        "discrepancies": (
            {"status": "assessed", "items": discrepancies}
            if discrepancies is not None
            else {"status": "not_assessed", "items": None}
        ),
    }


def build_development_manifest(
    data_audit: dict[str, Any],
    runs: list[dict[str, Any]],
    *,
    repository_root: str | Path,
    run_id: str,
    run_command: str,
    started_at_utc: str,
    completed_at_utc: str,
) -> dict[str, Any]:
    """Build a complete development and 2019 selection run record."""
    if not run_id.strip():
        raise ValueError("run_id must not be empty")
    if not run_command.strip():
        raise ValueError("run_command must not be empty")
    required_run_fields = {
        "policy",
        "horizon_days",
        "case_counts_by_partition",
        "sample_coverage",
        "ridge_selection",
        "validation",
    }
    for index, run in enumerate(runs):
        missing = required_run_fields.difference(run)
        if missing:
            raise ValueError(f"Run {index} is missing fields: {sorted(missing)}")
        if not run["ridge_selection"].get("selection_rule"):
            raise ValueError(f"Run {index} is missing its Ridge selection rule")
    if not runs:
        raise ValueError("A completed development record requires at least one run")
    selection_rules = {
        run["ridge_selection"]["selection_rule"] for run in runs
    }
    if len(selection_rules) != 1:
        raise ValueError("All runs must use the same Ridge selection rule")
    alpha_candidates = sorted(
        {
            float(fold_score["alpha"])
            for run in runs
            for fold_score in run["ridge_selection"].get("fold_scores", [])
        }
    )

    authors_path = Path(__file__).with_name("AUTHOR_METADATA.json")
    author_metadata = json.loads(authors_path.read_text(encoding="utf-8"))
    code_identity = collect_code_identity(repository_root)
    declared_runtime_path = Path(repository_root) / "runtime.txt"
    declared_python = (
        declared_runtime_path.read_text(encoding="utf-8").strip()
        if declared_runtime_path.is_file()
        else None
    )
    local_hash_matches_verified_copy = (
        data_audit.get("sha256") == _VERIFIED_KAGGLE_VERSION_12_SHA256
    )
    data_provenance = (
        {
            "public_artifact": "rohanrao/air-quality-data-in-india",
            "verified_artifact_version": 12,
            "local_file_byte_match_verified": True,
            "dataset_record_license_label": "CC0: Public Domain",
            "upstream_cpcb_lineage_and_rights": "unresolved",
            "historical_aqi_generation_method": "unverified",
            "record_url": (
                "https://www.kaggle.com/datasets/rohanrao/air-quality-data-in-india"
            ),
        }
        if local_hash_matches_verified_copy
        else {
            "public_artifact": None,
            "verified_artifact_version": None,
            "local_file_byte_match_verified": False,
            "dataset_record_license_label": None,
            "upstream_cpcb_lineage_and_rights": "not_verified_for_this_input",
            "historical_aqi_generation_method": "unverified",
            "record_url": None,
        }
    )
    return {
        "study": "daily_aqi_forecasting",
        "stage": "baseline_development_and_2019_selection",
        "status": "completed",
        "run_id": run_id,
        "started_at_utc": started_at_utc,
        "completed_at_utc": completed_at_utc,
        "run_command": run_command,
        "model_fitting_performed": True,
        "final_test_outcomes_used_for_selection": False,
        "final_test_predictions_generated": False,
        "final_test_scoring_performed": False,
        "data": {
            key: data_audit.get(key)
            for key in (
                "path",
                "file_size_bytes",
                "sha256",
                "rows",
                "columns",
                "column_names",
                "dtypes",
                "date_min",
                "date_max",
                "unique_dates",
                "city_labels",
                "city_count",
                "invalid_date_rows",
                "duplicate_city_date_excess",
            )
        },
        "data_provenance": data_provenance,
        "code": code_identity,
        "environment": {
            **_runtime_metadata(),
            "declared_python_runtime": declared_python,
        },
        "authors": author_metadata["authors"],
        "protocol": {
            "horizons_days": list(HORIZONS_DAYS),
            "target_policies": list(TARGET_POLICIES),
            "primary_feature_columns": list(PRIMARY_FEATURE_COLUMNS),
            "aqi_lags_days": list(AQI_LAGS_DAYS),
            "calendar_feature_columns": list(CALENDAR_FEATURE_COLUMNS),
            "train_target_dates": [TRAIN_START, TRAIN_END],
            "validation_and_selection_target_dates": [
                VALIDATION_START,
                VALIDATION_END,
            ],
            "final_test_target_dates_not_scored": [TEST_START, TEST_END],
            "ridge_alpha_candidates": alpha_candidates,
            "ridge_selection_rule": next(iter(selection_rules)),
            "expanding_window_folds": [
                {
                    "name": "fold_2017",
                    "train_target_dates": ["2015-01-01", "2016-12-31"],
                    "validation_target_dates": ["2017-01-01", "2017-12-31"],
                },
                {
                    "name": "fold_2018",
                    "train_target_dates": ["2015-01-01", "2017-12-31"],
                    "validation_target_dates": ["2018-01-01", "2018-12-31"],
                },
                {
                    "name": "fold_2019",
                    "train_target_dates": ["2015-01-01", "2018-12-31"],
                    "validation_target_dates": ["2019-01-01", "2019-12-31"],
                },
            ],
        },
        "runs": runs,
        "reproducibility_notes": {
            "historical_metrics": (
                "Not carried forward; no trusted saved run artifact was available."
            ),
            "research_source_fingerprint_scope": (
                "Sorted Python, Markdown, and JSON files below research/, excluding "
                "cache directories and research/aqi_forecasting/results/."
            ),
        },
    }
