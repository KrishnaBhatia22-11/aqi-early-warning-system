"""Add the XGBoost comparator, then score the locked 2020 test exactly once.

Stage 1 repeats the frozen development protocol with XGBoost added on the
same footing as Ridge and reports 2019 development results. Stage 2 refits
Ridge, XGBoost, and the city/month climatology on all 2015-2019 targets and
scores the locked test window (2020-01-01 through 2020-07-01) a single time.
Nothing in the protocol, features, lags, partitions, target policies, folds,
or baseline implementations is modified; see
``PROTOCOL_AMENDMENT_XGBOOST.md``.
"""

from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import shlex
import subprocess
import sys
from typing import Any
from uuid import uuid4

import pandas as pd

from research.aqi_forecasting import figures as figure_module
from research.aqi_forecasting.baselines import (
    RIDGE_ALPHA_CANDIDATES,
    annual_seasonal_naive_predictions,
    climatology_predictions,
    evaluate_predictions,
    fit_city_month_climatology,
    fit_ridge_model,
    persistence_predictions,
    ridge_predictions,
    select_ridge_alpha,
    weekly_seasonal_naive_predictions,
)
from research.aqi_forecasting.coverage import coverage_summary
from research.aqi_forecasting.data_audit import audit_raw_dataset
from research.aqi_forecasting.date_utils import parse_calendar_dates
from research.aqi_forecasting.final_test import (
    BOOTSTRAP_CONFIDENCE,
    BOOTSTRAP_REPLICATES,
    BOOTSTRAP_SEED,
    LOCKDOWN_START,
    LOCKDOWN_WINDOW,
    PRE_LOCKDOWN_WINDOW,
    REFIT_END,
    REFIT_PROCEDURE,
    REFIT_START,
    city_cluster_bootstrap,
    common_case_frames,
    fit_refit_climatology,
    fit_refit_ridge,
    fit_refit_xgboost,
    lockdown_split_metrics,
    validate_refit_samples,
)
from research.aqi_forecasting.forecast_samples import build_forecast_samples
from research.aqi_forecasting.leakage_checks import (
    validate_partitions,
    validate_sample_timestamps,
)
from research.aqi_forecasting.manifest import (
    _runtime_metadata,
    collect_code_identity,
)
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
from research.aqi_forecasting.temporal_splits import assign_partition
from research.aqi_forecasting.xgboost_model import (
    XGBOOST_METHOD,
    XGBOOST_SEED,
    config_from_dict,
    fit_xgboost_model,
    select_xgboost_config,
    xgboost_predictions,
)

_RUN_MODULE = "research.aqi_forecasting.run_final_test"
_PERSISTENCE = "persistence"
_ANNUAL = "annual_seasonal_naive"
_WEEKLY = "weekly_seasonal_naive"
_CLIMATOLOGY = "city_month_climatology"
_RIDGE = "regularized_linear"
_TIMESERIES_CITY = "Delhi"
_FIGURE_POLICY = "exclude"
_FIGURE_HORIZON = 1


def _new_run_id(now: datetime | None = None) -> str:
    timestamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{uuid4().hex[:12]}"


def _format_command(arguments: list[str]) -> str:
    if sys.platform == "win32":
        return subprocess.list2cmdline(arguments)
    return shlex.join(arguments)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _case_counts_by_partition(samples: pd.DataFrame, partitions: tuple[str, ...]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for partition in partitions:
        rows = samples.loc[samples["partition"].eq(partition)]
        counts[partition] = {
            "cases": int(len(rows)),
            "valid_targets": int(rows["target_valid"].astype(bool).sum()),
            "eligible_forecasts": int(rows["eligible"].astype(bool).sum()),
        }
    return counts


def development_with_xgboost(
    samples: pd.DataFrame,
    history: pd.DataFrame,
    *,
    alphas: tuple[float, ...] = RIDGE_ALPHA_CANDIDATES,
) -> dict[str, Any]:
    """Repeat the frozen development protocol with XGBoost added."""
    policy = str(samples["policy"].drop_duplicates().iloc[0])
    horizon = int(samples["horizon_days"].drop_duplicates().iloc[0])
    development = samples.loc[samples["partition"].isin(["train", "validation"])].copy()
    training = development.loc[development["partition"].eq("train")].copy()
    validation = development.loc[development["partition"].eq("validation")].copy()
    if training.empty or validation.empty:
        raise ValueError("Approved training and validation partitions must be non-empty")

    predictions: dict[str, pd.DataFrame] = {
        _PERSISTENCE: persistence_predictions(validation),
        _ANNUAL: annual_seasonal_naive_predictions(history, validation),
    }
    climatology = fit_city_month_climatology(training)
    predictions[_CLIMATOLOGY] = climatology_predictions(climatology, validation)
    ridge_selection = select_ridge_alpha(development, alphas=alphas)
    ridge = fit_ridge_model(training, ridge_selection["selected_alpha"])
    predictions[_RIDGE] = ridge_predictions(ridge, validation)
    xgboost_selection = select_xgboost_config(development)
    xgboost = fit_xgboost_model(training, config_from_dict(xgboost_selection["selected_config"]))
    predictions[XGBOOST_METHOD] = xgboost_predictions(xgboost, validation)
    if horizon != 7:
        predictions[_WEEKLY] = weekly_seasonal_naive_predictions(history, validation)

    return {
        "policy": policy,
        "horizon_days": horizon,
        "train_target_dates": [TRAIN_START, TRAIN_END],
        "validation_target_dates": [VALIDATION_START, VALIDATION_END],
        "climatology_training_cases": climatology.training_case_count,
        "climatology_training_cities": climatology.training_city_count,
        "ridge_selection": ridge_selection,
        "xgboost_selection": xgboost_selection,
        "validation": evaluate_predictions(predictions, partition="validation"),
    }


def score_locked_test(
    samples: pd.DataFrame,
    history: pd.DataFrame,
    *,
    ridge_alpha: float,
    xgboost_config: dict[str, Any],
) -> dict[str, Any]:
    """Refit on 2015-2019 targets and score the locked test window once."""
    policy = str(samples["policy"].drop_duplicates().iloc[0])
    horizon = int(samples["horizon_days"].drop_duplicates().iloc[0])
    refit = samples.loc[samples["partition"].isin(["train", "validation"])].copy()
    test = samples.loc[samples["partition"].eq("test")].copy()
    if refit.empty or test.empty:
        raise ValueError("Refit and locked-test partitions must be non-empty")
    validate_refit_samples(refit)
    test_dates = pd.to_datetime(test["target_date"]).dt.normalize()
    if not test_dates.between(TEST_START, TEST_END, inclusive="both").all():
        raise AssertionError("Locked-test rows fall outside the declared test window")

    predictions: dict[str, pd.DataFrame] = {
        _PERSISTENCE: persistence_predictions(test),
        _ANNUAL: annual_seasonal_naive_predictions(history, test),
    }
    climatology = fit_refit_climatology(refit)
    predictions[_CLIMATOLOGY] = climatology_predictions(climatology, test)
    ridge = fit_refit_ridge(refit, float(ridge_alpha))
    predictions[_RIDGE] = ridge_predictions(ridge, test)
    xgboost = fit_refit_xgboost(refit, config_from_dict(xgboost_config))
    predictions[XGBOOST_METHOD] = xgboost_predictions(xgboost, test)
    if horizon != 7:
        predictions[_WEEKLY] = weekly_seasonal_naive_predictions(history, test)

    evaluation = evaluate_predictions(predictions, partition="test")
    paired, common = common_case_frames(predictions, partition="test")
    bootstrap = city_cluster_bootstrap(paired)
    lockdown = lockdown_split_metrics(paired)
    return {
        "policy": policy,
        "horizon_days": horizon,
        "refit_target_dates": [REFIT_START, REFIT_END],
        "refit_procedure": REFIT_PROCEDURE,
        "test_target_dates": [TEST_START, TEST_END],
        "ridge_alpha": float(ridge_alpha),
        "xgboost_config": dict(xgboost_config),
        "refit_case_counts": {
            "cases": int(len(refit)),
            "valid_targets": int(refit["target_valid"].astype(bool).sum()),
            "eligible_forecasts": int(refit["eligible"].astype(bool).sum()),
            "max_target_date": str(pd.to_datetime(refit["target_date"]).max().date()),
        },
        "climatology_refit_cases": climatology.training_case_count,
        "climatology_refit_cities": climatology.training_city_count,
        "test": evaluation,
        "common_case_count": len(common),
        "bootstrap": bootstrap,
        "lockdown_split": lockdown,
        "_paired_frames": paired,
    }


def _dev_fold_rows(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run in runs:
        for score in run["ridge_selection"]["fold_scores"]:
            rows.append(
                {
                    "policy": run["policy"],
                    "horizon_days": run["horizon_days"],
                    "model": _RIDGE,
                    "config": f"alpha={score['alpha']:g}",
                    "selected": bool(
                        float(score["alpha"]) == float(run["ridge_selection"]["selected_alpha"])
                    ),
                    "fold": score["fold"],
                    "validation_cases": score["validation_cases"],
                    "mae": score["mae"],
                }
            )
        for score in run["xgboost_selection"]["fold_scores"]:
            rows.append(
                {
                    "policy": run["policy"],
                    "horizon_days": run["horizon_days"],
                    "model": XGBOOST_METHOD,
                    "config": score["config"],
                    "selected": bool(
                        score["config"] == run["xgboost_selection"]["selected_config_name"]
                    ),
                    "fold": score["fold"],
                    "validation_cases": score["validation_cases"],
                    "mae": score["mae"],
                }
            )
    return rows


def _common_case_rows(runs: list[dict[str, Any]], *, key: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run in runs:
        evaluation = run[key]
        for method, metrics in sorted(evaluation["common_case_metrics"].items()):
            pooled = metrics["pooled"]
            rows.append(
                {
                    "policy": run["policy"],
                    "horizon_days": run["horizon_days"],
                    "method": method,
                    "common_case_count": evaluation["common_case_count"],
                    "cases_scored": pooled["count"],
                    "mae": pooled["mae"],
                    "rmse": pooled["rmse"],
                    "r2": pooled["r2"],
                    "macro_city_mae": metrics["macro_city"]["mae"],
                    "contributing_cities": metrics["contributing_cities"],
                }
            )
    return rows


def _coverage_rows(runs: list[dict[str, Any]], *, key: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run in runs:
        evaluation = run[key]
        for method, native in sorted(evaluation["methods"].items()):
            rows.append(
                {
                    "policy": run["policy"],
                    "horizon_days": run["horizon_days"],
                    "partition": evaluation["partition"],
                    "method": method,
                    "valid_target_cases": native["valid_target_cases"],
                    "predicted_valid_target_cases": native["predicted_valid_target_cases"],
                    "unavailable_valid_target_cases": native["unavailable_valid_target_cases"],
                    "native_coverage": native["coverage"],
                    "unavailable_reasons": json.dumps(
                        native["unavailable_reasons"], sort_keys=True
                    ),
                }
            )
    return rows


def _test_ci_rows(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run in runs:
        evaluation = run["test"]
        bootstrap = run["bootstrap"]
        for method, metrics in sorted(evaluation["common_case_metrics"].items()):
            pooled = metrics["pooled"]
            interval = bootstrap["mae"].get(method, {})
            difference = bootstrap["paired_difference"].get(f"{method}_minus_{_PERSISTENCE}", {})
            rows.append(
                {
                    "policy": run["policy"],
                    "horizon_days": run["horizon_days"],
                    "method": method,
                    "common_case_count": evaluation["common_case_count"],
                    "mae": pooled["mae"],
                    "mae_ci_lower": interval.get("ci_lower"),
                    "mae_ci_upper": interval.get("ci_upper"),
                    "mae_bootstrap_std_error": interval.get("bootstrap_std_error"),
                    "rmse": pooled["rmse"],
                    "macro_city_mae": metrics["macro_city"]["mae"],
                    "mae_minus_persistence": difference.get("mae_difference"),
                    "diff_ci_lower": difference.get("ci_lower"),
                    "diff_ci_upper": difference.get("ci_upper"),
                    "diff_excludes_zero": difference.get("excludes_zero"),
                    "bootstrap_replicates": bootstrap["replicates"],
                    "bootstrap_seed": bootstrap["seed"],
                    "bootstrap_cities": bootstrap["city_count"],
                }
            )
    return rows


def _lockdown_rows(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run in runs:
        lockdown = run["lockdown_split"]
        for method, windows in sorted(lockdown["methods"].items()):
            for window, metrics in windows.items():
                start, end = lockdown["windows"][window]
                rows.append(
                    {
                        "policy": run["policy"],
                        "horizon_days": run["horizon_days"],
                        "method": method,
                        "window": window,
                        "window_start": start,
                        "window_end": end,
                        "common_cases": metrics["count"],
                        "mae": metrics["mae"],
                        "rmse": metrics["rmse"],
                    }
                )
    return rows


def _timeseries_frame(test_runs: list[dict[str, Any]], city: str) -> pd.DataFrame:
    for run in test_runs:
        if run["policy"] != _FIGURE_POLICY or run["horizon_days"] != _FIGURE_HORIZON:
            continue
        paired = run["_paired_frames"]
        reference = paired[_PERSISTENCE]
        rows = reference.loc[reference["City"].astype(str).eq(city), ["case_id", "target_date", "target"]]
        frame = rows.sort_values("target_date").reset_index(drop=True)
        for method in (_PERSISTENCE, _RIDGE, XGBOOST_METHOD):
            method_frame = paired[method]
            lookup = dict(
                zip(
                    method_frame["case_id"].astype(str),
                    method_frame["prediction"].astype(float),
                )
            )
            frame[method] = [lookup[str(case_id)] for case_id in frame["case_id"]]
        return frame
    raise ValueError("No locked-test run matches the figure policy and horizon")


def _write_csv(rows: list[dict[str, Any]], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows)
    frame.to_csv(path, index=False, lineterminator="\n")
    return path


def _build_record(
    *,
    audit: dict[str, Any],
    development_runs: list[dict[str, Any]],
    test_runs: list[dict[str, Any]],
    repository_root: Path,
    run_id: str,
    run_command: str,
    started_at_utc: str,
    completed_at_utc: str,
) -> dict[str, Any]:
    authors_path = Path(__file__).with_name("AUTHOR_METADATA.json")
    author_metadata = json.loads(authors_path.read_text(encoding="utf-8"))
    declared_runtime_path = repository_root / "runtime.txt"
    declared_python = (
        declared_runtime_path.read_text(encoding="utf-8").strip()
        if declared_runtime_path.is_file()
        else None
    )
    alpha_candidates = sorted(
        {
            float(score["alpha"])
            for run in development_runs
            for score in run["ridge_selection"]["fold_scores"]
        }
    )
    return {
        "study": "daily_aqi_forecasting",
        "stage": "xgboost_comparator_and_locked_final_test",
        "status": "completed",
        "run_id": run_id,
        "started_at_utc": started_at_utc,
        "completed_at_utc": completed_at_utc,
        "run_command": run_command,
        "protocol_amendment": "research/aqi_forecasting/PROTOCOL_AMENDMENT_XGBOOST.md",
        "reference_development_run": "20261010T101227Z-50924ef9974e",
        "model_fitting_performed": True,
        "final_test_outcomes_used_for_selection": False,
        "final_test_predictions_generated": True,
        "final_test_scoring_performed": True,
        "final_test_scoring_events": 1,
        "data": {
            key: audit.get(key)
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
        "code": collect_code_identity(repository_root),
        "environment": {
            **_runtime_metadata(),
            "xgboost": _xgboost_version(),
            "matplotlib": _matplotlib_version(),
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
            "validation_and_selection_target_dates": [VALIDATION_START, VALIDATION_END],
            "final_test_target_dates": [TEST_START, TEST_END],
            "ridge_alpha_candidates": alpha_candidates,
            "ridge_selection_rule": development_runs[0]["ridge_selection"]["selection_rule"],
            "xgboost_grid": development_runs[0]["xgboost_selection"]["grid"],
            "xgboost_fixed_hyperparameters": development_runs[0]["xgboost_selection"][
                "fixed_hyperparameters"
            ],
            "xgboost_selection_rule": development_runs[0]["xgboost_selection"]["selection_rule"],
            "xgboost_availability_rule": (
                "Rows with any missing or policy-invalid primary feature are "
                "unavailable; XGBoost native missing-value handling is not used."
            ),
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
            "final_test_refit_procedure": REFIT_PROCEDURE,
            "lockdown_windows": {
                "pre_lockdown": list(PRE_LOCKDOWN_WINDOW),
                "lockdown": list(LOCKDOWN_WINDOW),
                "lockdown_start": LOCKDOWN_START,
            },
            "uncertainty": {
                "method": "city-cluster bootstrap, cities resampled with replacement",
                "replicates": BOOTSTRAP_REPLICATES,
                "seed": BOOTSTRAP_SEED,
                "confidence": BOOTSTRAP_CONFIDENCE,
                "paired_reference": _PERSISTENCE,
            },
        },
        "seeds": {
            "status": "recorded",
            "values": {
                "xgboost_random_state": XGBOOST_SEED,
                "bootstrap_seed": BOOTSTRAP_SEED,
            },
        },
        "development_runs": development_runs,
        "test_runs": test_runs,
        "reproducibility_notes": {
            "saved_development_run_untouched": (
                "Run 20261010T101227Z-50924ef9974e was read only; its tables and "
                "record were not modified."
            ),
            "common_case_intersection": (
                "The 2019 common-case intersection is recomputed with XGBoost "
                "included; XGBoost shares the Ridge availability rule exactly."
            ),
            "research_source_fingerprint_scope": (
                "Sorted Python, Markdown, and JSON files below research/, excluding "
                "cache directories and research/aqi_forecasting/results/. The "
                "fingerprint is computed during the run, so RESULTS_SUMMARY.md, "
                "written after scoring, is not covered by it."
            ),
            "final_test_single_scoring": (
                "The locked test window was constructed, predicted, and scored once "
                "in this run; no tuning or rerun followed."
            ),
        },
    }


def _xgboost_version() -> str | None:
    try:
        import xgboost

        return str(xgboost.__version__)
    except Exception:  # pragma: no cover - environment probe only
        return None


def _matplotlib_version() -> str | None:
    try:
        import matplotlib

        return str(matplotlib.__version__)
    except Exception:  # pragma: no cover - environment probe only
        return None


def run_final_test(
    raw_path: str | Path,
    *,
    output_directory: str | Path,
    run_id: str | None = None,
    run_command: str | None = None,
    started_at_utc: str | None = None,
    summary_path: str | Path | None = None,
) -> dict[str, Any]:
    """Run development with XGBoost, score the locked test once, write outputs."""
    started = datetime.now(timezone.utc)
    run_id = run_id or _new_run_id(started)
    started_at_utc = started_at_utc or started.isoformat()
    repository_root = Path(__file__).resolve().parents[2]

    audit = audit_raw_dataset(raw_path)
    history = pd.read_csv(raw_path)
    dates = parse_calendar_dates(history["Date"], field_name="Date")
    if dates.isna().any():
        raise ValueError("Cannot run with invalid dataset dates")
    development_history = history.loc[dates.le(VALIDATION_END)].copy()

    development_runs: list[dict[str, Any]] = []
    test_runs: list[dict[str, Any]] = []
    for policy in TARGET_POLICIES:
        for horizon in HORIZONS_DAYS:
            print(f"[dev] policy={policy} horizon={horizon}", flush=True)
            development_samples = assign_partition(
                build_forecast_samples(development_history, horizon, policy)
            )
            if development_samples["target_date"].max() > pd.Timestamp(VALIDATION_END):
                raise AssertionError("Development sample construction reached beyond validation")
            validate_sample_timestamps(development_samples)
            validate_partitions(development_samples)
            development = development_with_xgboost(development_samples, development_history)
            development["case_counts_by_partition"] = _case_counts_by_partition(
                development_samples, ("train", "validation")
            )
            development["sample_coverage"] = coverage_summary(development_samples)
            development["data_sha256"] = audit["sha256"]
            development["data_rows"] = audit["rows"]
            development_runs.append(development)

            print(f"[test] policy={policy} horizon={horizon}", flush=True)
            full_samples = assign_partition(build_forecast_samples(history, horizon, policy))
            validate_sample_timestamps(full_samples)
            validate_partitions(full_samples)
            test = score_locked_test(
                full_samples,
                history,
                ridge_alpha=development["ridge_selection"]["selected_alpha"],
                xgboost_config=development["xgboost_selection"]["selected_config"],
            )
            test["case_counts_by_partition"] = _case_counts_by_partition(
                full_samples, ("train", "validation", "test")
            )
            test["sample_coverage"] = coverage_summary(full_samples)
            test_runs.append(test)

    output_root = Path(output_directory)
    output_root.mkdir(parents=True, exist_ok=True)
    run_directory = output_root / run_id
    run_directory.mkdir(exist_ok=False)
    tables = run_directory / "tables"
    figures = run_directory / "figures"

    written: list[Path] = [
        _write_csv(_dev_fold_rows(development_runs), tables / "dev_fold_mae.csv"),
        _write_csv(
            _common_case_rows(development_runs, key="validation"),
            tables / "dev_common_case.csv",
        ),
        _write_csv(
            _coverage_rows(development_runs, key="validation"), tables / "dev_coverage.csv"
        ),
        _write_csv(_test_ci_rows(test_runs), tables / "test_common_case_with_ci.csv"),
        _write_csv(_coverage_rows(test_runs, key="test"), tables / "test_coverage.csv"),
        _write_csv(_lockdown_rows(test_runs), tables / "test_lockdown_split.csv"),
    ]

    timeseries = _timeseries_frame(test_runs, _TIMESERIES_CITY)
    written.append(
        _write_csv(
            timeseries.assign(
                policy=_FIGURE_POLICY, horizon_days=_FIGURE_HORIZON, City=_TIMESERIES_CITY
            ).to_dict(orient="records"),
            tables / "fig_timeseries_delhi_data.csv",
        )
    )

    ci_rows = _test_ci_rows(test_runs)
    dev_vs_test_rows = [
        {
            "policy": row["policy"],
            "horizon_days": row["horizon_days"],
            "method": row["method"],
            "stage": "development_2019",
            "mae": row["mae"],
        }
        for row in _common_case_rows(development_runs, key="validation")
    ] + [
        {
            "policy": row["policy"],
            "horizon_days": row["horizon_days"],
            "method": row["method"],
            "stage": "test_2020",
            "mae": row["mae"],
        }
        for row in ci_rows
    ]
    written.extend(
        [
            figure_module.plot_test_mae_by_horizon(
                [
                    {
                        "policy": row["policy"],
                        "horizon_days": row["horizon_days"],
                        "method": row["method"],
                        "mae": row["mae"],
                        "ci_lower": row["mae_ci_lower"],
                        "ci_upper": row["mae_ci_upper"],
                    }
                    for row in ci_rows
                ],
                figures / "fig_test_mae_by_horizon.png",
                policy=_FIGURE_POLICY,
            ),
            figure_module.plot_dev_vs_test(
                dev_vs_test_rows,
                figures / "fig_dev_vs_test.png",
                policy=_FIGURE_POLICY,
            ),
            figure_module.plot_lockdown(
                _lockdown_rows(test_runs),
                figures / "fig_lockdown.png",
                policy=_FIGURE_POLICY,
                horizon_days=_FIGURE_HORIZON,
            ),
            figure_module.plot_city_timeseries(
                timeseries, figures / "fig_timeseries_delhi.png"
            ),
        ]
    )

    for run in test_runs:
        run.pop("_paired_frames", None)

    completed_at_utc = datetime.now(timezone.utc).isoformat()
    record = _build_record(
        audit=audit,
        development_runs=development_runs,
        test_runs=test_runs,
        repository_root=repository_root,
        run_id=run_id,
        run_command=run_command or _format_command([sys.executable, "-m", _RUN_MODULE]),
        started_at_utc=started_at_utc,
        completed_at_utc=completed_at_utc,
    )

    summary_file = (
        Path(summary_path)
        if summary_path is not None
        else Path(__file__).with_name("RESULTS_SUMMARY.md")
    )
    summary_file.write_text(
        render_results_summary(record, run_directory=run_directory, summary_path=summary_file),
        encoding="utf-8",
        newline="\n",
    )
    written.append(summary_file)

    record["artifacts"] = {
        "run_directory": str(run_directory.resolve()),
        "record_json": str((run_directory / "run_record.json").resolve()),
        "run_log": str((run_directory / "run.log").resolve()),
        "results_summary": str(summary_file.resolve()),
        "sha256": {
            _artifact_key(path, run_directory, repository_root): _sha256_file(path)
            for path in written
        },
    }
    return record


def _artifact_key(path: Path, run_directory: Path, repository_root: Path) -> str:
    resolved = path.resolve()
    for base in (run_directory, repository_root):
        try:
            return resolved.relative_to(base.resolve()).as_posix()
        except ValueError:
            continue
    return resolved.name


def _lookup(scores: dict[Any, float], key: Any) -> float | None:
    """Read a score map whose keys may be floats in memory and strings in JSON."""
    for candidate in (key, str(key), f"{key:g}" if isinstance(key, float) else key):
        if candidate in scores:
            return float(scores[candidate])
    return None


def _format_number(value: Any, digits: int = 3) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "n/a"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int,)):
        return f"{value:,}"
    return f"{float(value):.{digits}f}"


def render_results_summary(
    record: dict[str, Any], *, run_directory: Path, summary_path: Path
) -> str:
    """Render every reported number with the file each one comes from."""
    run_id = record["run_id"]
    tables = f"results/{run_id}/tables"
    lines: list[str] = []
    lines.append("# AQI forecasting results summary")
    lines.append("")
    lines.append(
        "Single-source listing of every number reported for run "
        f"`{run_id}`. Each section names the file it was read from. The locked "
        "2020 test window was scored exactly once, in this run."
    )
    lines.append("")
    lines.append("## Run identity")
    lines.append("")
    lines.append(f"- Run ID: `{run_id}` (`results/{run_id}/run_record.json`)")
    lines.append(f"- Stage: `{record['stage']}`")
    lines.append(f"- Started / completed (UTC): {record['started_at_utc']} / {record['completed_at_utc']}")
    lines.append(f"- Command: `{record['run_command']}`")
    lines.append(
        f"- Input data: `{record['data']['path']}`, {record['data']['rows']:,} rows, "
        f"{record['data']['city_count']} cities, SHA-256 `{record['data']['sha256']}`"
    )
    lines.append(
        f"- Git revision: `{record['code']['git_revision']}`; research source "
        f"fingerprint `{record['code']['research_source_fingerprint']['sha256']}`"
    )
    lines.append(
        f"- Environment: Python {record['environment']['python']}, pandas "
        f"{record['environment']['pandas']}, NumPy {record['environment']['numpy']}, "
        f"scikit-learn {record['environment']['scikit_learn']}, xgboost "
        f"{record['environment']['xgboost']}, matplotlib {record['environment']['matplotlib']}"
    )
    lines.append(
        f"- Reference development run (untouched): `{record['reference_development_run']}`"
    )
    lines.append("")

    lines.append("## Selected configurations")
    lines.append("")
    lines.append(f"Source: `{tables}/dev_fold_mae.csv` and `results/{run_id}/run_record.json`.")
    lines.append("")
    lines.append("| Policy | Horizon | Ridge alpha | XGBoost config | Ridge mean fold MAE | XGBoost mean fold MAE |")
    lines.append("|---|---|---|---|---|---|")
    for run in record["development_runs"]:
        ridge = run["ridge_selection"]
        xgb = run["xgboost_selection"]
        ridge_mean = _lookup(ridge["mean_mae_by_alpha"], ridge["selected_alpha"])
        xgb_mean = _lookup(xgb["mean_mae_by_config"], xgb["selected_config_name"])
        lines.append(
            f"| {run['policy']} | {run['horizon_days']}d | {ridge['selected_alpha']:g} | "
            f"{xgb['selected_config_name']} | {_format_number(ridge_mean)} | "
            f"{_format_number(xgb_mean)} |"
        )
    lines.append("")
    lines.append(
        f"XGBoost grid and fixed hyperparameters: "
        f"`{json.dumps(record['protocol']['xgboost_fixed_hyperparameters'], sort_keys=True)}`; "
        f"selection rule: {record['protocol']['xgboost_selection_rule']}"
    )
    lines.append("")

    lines.append("## 2019 development, common-case metrics (recomputed with XGBoost)")
    lines.append("")
    lines.append(f"Source: `{tables}/dev_common_case.csv`.")
    lines.append("")
    lines.append("| Policy | Horizon | Common cases | Method | MAE | RMSE | Macro-city MAE |")
    lines.append("|---|---|---|---|---|---|---|")
    for run in record["development_runs"]:
        evaluation = run["validation"]
        for method, metrics in sorted(evaluation["common_case_metrics"].items()):
            lines.append(
                f"| {run['policy']} | {run['horizon_days']}d | "
                f"{evaluation['common_case_count']:,} | {method} | "
                f"{_format_number(metrics['pooled']['mae'])} | "
                f"{_format_number(metrics['pooled']['rmse'])} | "
                f"{_format_number(metrics['macro_city']['mae'])} |"
            )
    lines.append("")

    lines.append("## 2019 development, native coverage")
    lines.append("")
    lines.append(f"Source: `{tables}/dev_coverage.csv`.")
    lines.append("")
    lines.append("| Policy | Horizon | Method | Valid targets | Predicted | Native coverage |")
    lines.append("|---|---|---|---|---|---|")
    for run in record["development_runs"]:
        for method, native in sorted(run["validation"]["methods"].items()):
            lines.append(
                f"| {run['policy']} | {run['horizon_days']}d | {method} | "
                f"{native['valid_target_cases']:,} | "
                f"{native['predicted_valid_target_cases']:,} | "
                f"{_format_number(native['coverage'], 4)} |"
            )
    lines.append("")

    lines.append("## Locked 2020 test, native coverage")
    lines.append("")
    lines.append(f"Source: `{tables}/test_coverage.csv`.")
    lines.append("")
    lines.append("| Policy | Horizon | Method | Valid targets | Predicted | Native coverage |")
    lines.append("|---|---|---|---|---|---|")
    for run in record["test_runs"]:
        for method, native in sorted(run["test"]["methods"].items()):
            lines.append(
                f"| {run['policy']} | {run['horizon_days']}d | {method} | "
                f"{native['valid_target_cases']:,} | "
                f"{native['predicted_valid_target_cases']:,} | "
                f"{_format_number(native['coverage'], 4)} |"
            )
    lines.append("")

    lines.append("## Locked 2020 test, common-case metrics with 95% city-cluster CIs")
    lines.append("")
    lines.append(
        f"Source: `{tables}/test_common_case_with_ci.csv`. "
        f"{record['protocol']['uncertainty']['replicates']:,} replicates, seed "
        f"{record['protocol']['uncertainty']['seed']}, cities resampled with replacement."
    )
    lines.append("")
    lines.append(
        "| Policy | Horizon | Common cases | Method | MAE | 95% CI | RMSE | MAE - persistence | 95% CI of difference |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for run in record["test_runs"]:
        evaluation = run["test"]
        bootstrap = run["bootstrap"]
        for method, metrics in sorted(evaluation["common_case_metrics"].items()):
            interval = bootstrap["mae"].get(method, {})
            difference = bootstrap["paired_difference"].get(f"{method}_minus_{_PERSISTENCE}")
            if difference is None:
                difference_text = "reference"
                difference_ci = "reference"
            else:
                difference_text = _format_number(difference["mae_difference"])
                difference_ci = (
                    f"[{_format_number(difference['ci_lower'])}, "
                    f"{_format_number(difference['ci_upper'])}]"
                )
            lines.append(
                f"| {run['policy']} | {run['horizon_days']}d | "
                f"{evaluation['common_case_count']:,} | {method} | "
                f"{_format_number(metrics['pooled']['mae'])} | "
                f"[{_format_number(interval.get('ci_lower'))}, "
                f"{_format_number(interval.get('ci_upper'))}] | "
                f"{_format_number(metrics['pooled']['rmse'])} | {difference_text} | "
                f"{difference_ci} |"
            )
    lines.append("")

    lines.append("## Lockdown sub-analysis")
    lines.append("")
    lines.append(
        f"Source: `{tables}/test_lockdown_split.csv`. India's national lockdown began "
        f"{record['protocol']['lockdown_windows']['lockdown_start']}."
    )
    lines.append("")
    lines.append("| Policy | Horizon | Method | Pre-lockdown MAE (n) | Lockdown MAE (n) |")
    lines.append("|---|---|---|---|---|")
    for run in record["test_runs"]:
        lockdown = run["lockdown_split"]
        for method, windows in sorted(lockdown["methods"].items()):
            pre = windows["pre_lockdown"]
            during = windows["lockdown"]
            lines.append(
                f"| {run['policy']} | {run['horizon_days']}d | {method} | "
                f"{_format_number(pre['mae'])} ({pre['count']:,}) | "
                f"{_format_number(during['mae'])} ({during['count']:,}) |"
            )
    lines.append("")

    lines.append("## Figures")
    lines.append("")
    for name, caption in (
        (
            "fig_test_mae_by_horizon.png",
            "Locked-2020 common-case MAE per method per horizon, exclude policy, "
            "with 95% city-cluster bootstrap CIs. Data: "
            "tables/test_common_case_with_ci.csv.",
        ),
        (
            "fig_dev_vs_test.png",
            "Persistence, Ridge, and XGBoost common-case MAE, 2019 development "
            "versus locked 2020 test, exclude policy. Data: "
            "tables/dev_common_case.csv and tables/test_common_case_with_ci.csv.",
        ),
        (
            "fig_lockdown.png",
            "Common-case MAE before and during the national lockdown, exclude "
            "policy, 1-day horizon. Data: tables/test_lockdown_split.csv.",
        ),
        (
            "fig_timeseries_delhi.png",
            "Delhi observed AQI against 1-day persistence, Ridge, and XGBoost "
            "forecasts over the locked test window, exclude policy. Data: "
            "tables/fig_timeseries_delhi_data.csv.",
        ),
    ):
        lines.append(f"- `results/{run_id}/figures/{name}` — {caption}")
    lines.append("")

    lines.append("## Artifact SHA-256")
    lines.append("")
    lines.append(f"Recorded in `results/{run_id}/run_record.json` under `artifacts.sha256`.")
    lines.append("")
    lines.append(
        "This file is written after the research source fingerprint is computed, "
        "so its own hash is recorded in the run record but it is not covered by "
        "that fingerprint."
    )
    lines.append("")
    return "\n".join(lines)


def persist_final_test_record(
    record: dict[str, Any],
    run_directory: Path,
    *,
    stdout: str = "",
    stderr: str = "",
) -> tuple[Path, Path]:
    """Write the run record and log into the already created run directory."""
    run_id = record.get("run_id")
    if not isinstance(run_id, str) or not run_id or Path(run_id).name != run_id:
        raise ValueError("Record must contain a safe, non-empty run_id")
    if record.get("status") != "completed":
        raise ValueError("Only completed run records may be persisted")
    record_path = run_directory / "run_record.json"
    log_path = run_directory / "run.log"
    with log_path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(f"run_id: {run_id}\n")
        handle.write(f"stage: {record.get('stage', 'unknown')}\n")
        handle.write(f"started_at_utc: {record.get('started_at_utc', 'unknown')}\n")
        handle.write(f"completed_at_utc: {record.get('completed_at_utc', 'unknown')}\n")
        handle.write(f"run_command: {record.get('run_command', 'unknown')}\n")
        handle.write(f"final_test_scoring_events: {record.get('final_test_scoring_events')}\n")
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
        record = run_final_test(
            args.data,
            output_directory=args.output_directory,
            run_id=run_id,
            run_command=command,
            started_at_utc=started.isoformat(),
        )
    run_directory = Path(record["artifacts"]["run_directory"])
    record_path, log_path = persist_final_test_record(
        record,
        run_directory,
        stdout=captured_stdout.getvalue(),
        stderr=captured_stderr.getvalue(),
    )
    print(f"Run ID: {run_id}")
    print(f"Run record: {record_path}")
    print(f"Run log: {log_path}")
    print(f"Results summary: {record['artifacts']['results_summary']}")


if __name__ == "__main__":
    main()
