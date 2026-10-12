"""POST-HOC warning / category / risk-zone analysis for the FROZEN forecasting run.

Post-hoc, not pre-registered. The locked 2020 window was already scored by the
frozen run (20261011T163344Z-7eff64974b98); this script re-fits the already
selected configurations, changes no selection, and must reproduce the frozen
common-case MAE exactly (gate) before any new metric is computed.

Predictions come from the frozen code path itself: ``score_locked_test`` is
called unchanged and the full prediction frames it hands to
``evaluate_predictions`` are captured, so nothing is re-implemented.

    venv\\Scripts\\python.exe -m research.aqi_forecasting.posthoc.run_posthoc
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any, Callable
from unittest import mock

import numpy as np
import pandas as pd

from research.aqi_estimation import metrics as est_metrics
from research.aqi_forecasting import run_final_test as frozen_run
from research.aqi_forecasting.baselines import PREDICTION_ID_COLUMNS
from research.aqi_forecasting.final_test import (
    BOOTSTRAP_CONFIDENCE,
    BOOTSTRAP_REPLICATES,
    BOOTSTRAP_SEED,
    LOCKDOWN_WINDOW,
    PRE_LOCKDOWN_WINDOW,
    common_case_frames,
)
from research.aqi_forecasting.date_utils import parse_calendar_dates
from research.aqi_forecasting.forecast_samples import build_forecast_samples
from research.aqi_forecasting.leakage_checks import validate_partitions, validate_sample_timestamps
from research.aqi_forecasting.temporal_splits import assign_partition

ROOT = Path(__file__).resolve().parents[3]
RESULTS_ROOT = ROOT / "research" / "aqi_forecasting" / "results"
FROZEN_RUN_ID = "20261011T163344Z-7eff64974b98"
EXPECTED_DATASET_SHA256 = "0d84b21c3e4878bbad8df362f2ab05f61ad959538dddf5918e714077ed3c1847"
DATASET = ROOT / "data" / "raw" / "city_day.csv"

LABEL = ("post-hoc, not pre-registered; the locked window was already scored by the frozen run; "
         "no selection changed")
GATE_TOLERANCE = 1e-6
THRESHOLDS = (200, 300)
LOW_EVENT_COUNT = 30
ZONE_HIGH, ZONE_MEDIUM = 0.30, 0.10
MODEL_ORDER = ["persistence", "weekly_seasonal_naive", "annual_seasonal_naive",
               "city_month_climatology", "regularized_linear", "xgboost"]
CATEGORY_MODELS = ["persistence", "regularized_linear", "xgboost"]
FIGURE_POLICY = "exclude"


class PreflightError(RuntimeError):
    pass


class GateFailed(RuntimeError):
    pass


# ----------------------------------------------------------------- utilities
def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_outside_frozen(path: Path, frozen_dir: Path) -> Path:
    resolved, frozen = Path(path).resolve(), Path(frozen_dir).resolve()
    if resolved == frozen or frozen in resolved.parents:
        raise PermissionError(f"Refusing to write inside the frozen run directory: {resolved}")
    return resolved


def _git(*args: str) -> str | None:
    try:
        return subprocess.run(["git", "-C", str(ROOT), *args], check=True, capture_output=True,
                              text=True, encoding="utf-8").stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def _versions() -> dict[str, str | None]:
    import sklearn
    import xgboost

    out = {"python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__,
           "scikit_learn": sklearn.__version__, "xgboost": xgboost.__version__}
    for name in ("scipy", "matplotlib"):
        try:
            out[name] = __import__(name).__version__
        except Exception:
            out[name] = None
    return out


# ----------------------------------------------------------------- preflight
def preflight(frozen_record: dict[str, Any], dataset: Path) -> dict[str, Any]:
    problems = []
    status = _git("status", "--porcelain=v1", "--untracked-files=no", "--", "research")
    if status:
        problems.append(f"research/ has uncommitted tracked changes: {status!r}")
    sha = sha256_file(dataset)
    if sha != EXPECTED_DATASET_SHA256:
        problems.append(f"dataset SHA-256 {sha} != expected {EXPECTED_DATASET_SHA256}")
    now, frozen = _versions(), frozen_record["environment"]
    for key in ("python", "scikit_learn", "xgboost"):
        if now[key] != frozen[key]:
            problems.append(f"{key} {now[key]} != frozen {frozen[key]}")
    if problems:
        raise PreflightError("; ".join(problems))
    return {"git_commit": _git("rev-parse", "HEAD"), "dataset_sha256": sha, "versions": now}


# --------------------------------------------------------------- predictions
class _CapturingEvaluate:
    """Wraps the frozen ``evaluate_predictions`` and keeps the frames it receives."""

    def __init__(self, real: Callable):
        self.real, self.captured = real, None

    def __call__(self, predictions_by_model, **kwargs):
        self.captured = predictions_by_model
        return self.real(predictions_by_model, **kwargs)


def generate_predictions(history: pd.DataFrame, frozen_record: dict[str, Any]) -> tuple[pd.DataFrame, list[dict]]:
    dates = parse_calendar_dates(history["Date"], field_name="Date")
    if dates.isna().any():
        raise ValueError("Cannot run with invalid dataset dates")
    frames, run_info = [], []
    for run in frozen_record["test_runs"]:
        policy, horizon = run["policy"], int(run["horizon_days"])
        samples = assign_partition(build_forecast_samples(history, horizon, policy))
        validate_sample_timestamps(samples)
        validate_partitions(samples)
        capture = _CapturingEvaluate(frozen_run.evaluate_predictions)
        with mock.patch.object(frozen_run, "evaluate_predictions", capture):
            result = frozen_run.score_locked_test(
                samples, history, ridge_alpha=run["ridge_alpha"], xgboost_config=run["xgboost_config"])
        predictions = capture.captured
        _, common = common_case_frames(predictions, partition="test")
        if len(common) != result["common_case_count"] or len(common) != run["common_case_count"]:
            raise GateFailed(f"common-case count mismatch for {policy}/h{horizon}")
        for model, frame in predictions.items():
            frame = frame.loc[frame["partition"].eq("test")]
            out = frame.loc[:, list(PREDICTION_ID_COLUMNS)].copy()
            out["model"] = model
            out["y_pred"] = frame["prediction"].astype("Float64").astype("float64").to_numpy()
            out["prediction_available"] = frame["prediction_available"].astype(bool).to_numpy()
            out["in_common_case"] = frame["case_id"].astype(str).isin(common).to_numpy()
            frames.append(out)
        run_info.append({"policy": policy, "horizon_days": horizon, "common_case_count": len(common),
                         "ridge_alpha": run["ridge_alpha"], "xgboost_config": run["xgboost_config"]})
    df = pd.concat(frames, ignore_index=True)
    df = df.rename(columns={"City": "city", "target": "y_true", "horizon_days": "horizon"})
    columns = ["city", "origin_date", "target_date", "horizon", "model", "policy", "y_true", "y_pred",
               "in_common_case", "prediction_available", "target_valid", "case_id", "partition"]
    return df.loc[:, columns], run_info


# ---------------------------------------------------------------------- gate
def compare_to_frozen(pred: pd.DataFrame, frozen_table: Path) -> pd.DataFrame:
    frozen = pd.read_csv(frozen_table)
    rows = []
    common = pred.loc[pred["in_common_case"] & pred["target_valid"].astype(bool)]
    for item in frozen.itertuples(index=False):
        sel = common[(common["policy"] == item.policy) & (common["horizon"] == item.horizon_days)
                     & (common["model"] == item.method)]
        count = int(len(sel))
        mae = float(np.mean(np.abs(sel["y_pred"] - sel["y_true"]))) if count else float("nan")
        rows.append({"policy": item.policy, "horizon_days": item.horizon_days, "model": item.method,
                     "frozen_count": int(item.common_case_count), "posthoc_count": count,
                     "frozen_mae": float(item.mae), "posthoc_mae": mae,
                     "abs_diff": abs(mae - float(item.mae)) if count else float("nan")})
    frame = pd.DataFrame(rows)
    frame["passed"] = (frame["frozen_count"] == frame["posthoc_count"]) & (frame["abs_diff"] <= GATE_TOLERANCE)
    frame["n_models_in_prediction_set"] = pred["model"].nunique()
    return frame


def run_gate(pred: pd.DataFrame, frozen_table: Path, out_dir: Path) -> dict[str, Any]:
    comparison = compare_to_frozen(pred, frozen_table)
    expected_cells = pred.groupby(["policy", "horizon", "model"]).ngroups
    complete = len(comparison) == expected_cells
    passed = bool(comparison["passed"].all()) and complete
    summary = {"passed": passed, "cells_compared": int(len(comparison)),
               "cells_in_posthoc_predictions": int(expected_cells),
               "max_abs_mae_difference": float(comparison["abs_diff"].max()),
               "tolerance": GATE_TOLERANCE, "counts_all_equal": bool(
                   (comparison["frozen_count"] == comparison["posthoc_count"]).all())}
    if not passed:
        out_dir.mkdir(parents=True, exist_ok=True)
        lines = ["# GATE FAILED", "", f"Tolerance {GATE_TOLERANCE}; frozen cells {len(comparison)}, "
                 f"post-hoc cells {expected_cells}.", "", json.dumps(summary, indent=2), "",
                 comparison.to_markdown(index=False) if _has_tabulate() else comparison.to_string(index=False)]
        (out_dir / "GATE_FAILED.md").write_text("\n".join(lines), encoding="utf-8")
        raise GateFailed(f"Gate failed: max |dMAE| = {summary['max_abs_mae_difference']}")
    return {"summary": summary, "comparison": comparison.to_dict(orient="records")}


def _has_tabulate() -> bool:
    try:
        import tabulate  # noqa: F401
        return True
    except ImportError:
        return False


# ------------------------------------------------------------------- metrics
def warning_cell(y, pred, threshold: float) -> dict[str, Any]:
    s = est_metrics.event_scores(y, pred, threshold)
    n = int(len(y))
    return {"threshold": threshold, "n_cases": n, "events": s["events"], "hits": s["hits"],
            "misses": s["misses"], "false_alarms": s["false_alarms"],
            "correct_negatives": n - s["hits"] - s["misses"] - s["false_alarms"],
            "POD": s["POD"], "FAR": s["FAR"], "CSI": s["CSI"],
            "event_base_rate": s["events"] / n if n else float("nan"),
            "warnings_issued": s["hits"] + s["false_alarms"],
            "flag": "LOW-EVENT-COUNT" if s["events"] < LOW_EVENT_COUNT else ""}


def groups(common: pd.DataFrame):
    for (policy, horizon, model), frame in common.groupby(["policy", "horizon", "model"], sort=True):
        yield policy, int(horizon), model, frame


def warning_table(common: pd.DataFrame, extra: dict | None = None) -> pd.DataFrame:
    rows = []
    for policy, horizon, model, frame in groups(common):
        for thr in THRESHOLDS:
            rows.append({"policy": policy, "horizon_days": horizon, "model": model,
                         **warning_cell(frame["y_true"], frame["y_pred"], thr), **(extra or {})})
    return pd.DataFrame(rows)


def city_cluster_weights(cities: list[str], replicates: int, seed: int) -> np.ndarray:
    """Same resampling as ``final_test.city_cluster_bootstrap``: integer draws, bincount weights."""
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(cities), size=(int(replicates), len(cities)))
    weights = np.zeros((int(replicates), len(cities)), dtype="float64")
    for r in range(int(replicates)):
        weights[r] = np.bincount(draws[r], minlength=len(cities)).astype("float64")
    return weights


def _city_counts(frame: pd.DataFrame, cities: list[str], threshold: float) -> np.ndarray:
    obs, fc = frame["y_true"].to_numpy() > threshold, frame["y_pred"].to_numpy() > threshold
    index = {c: i for i, c in enumerate(cities)}
    out = np.zeros((len(cities), 3))
    for city, o, f in zip(frame["city"].astype(str), obs, fc):
        i = index[city]
        out[i, 0] += o and f
        out[i, 1] += o and not f
        out[i, 2] += f and not o
    return out


def _csi(counts: np.ndarray, weights: np.ndarray | None = None) -> np.ndarray | float:
    if weights is None:
        total = counts.sum(axis=0)
        den = total.sum()
        return float(total[0] / den) if den else float("nan")
    num, den = weights @ counts[:, 0], weights @ counts.sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den > 0, num / den, np.nan)


def csi_bootstrap(common: pd.DataFrame, *, replicates=BOOTSTRAP_REPLICATES, seed=BOOTSTRAP_SEED,
                  confidence=BOOTSTRAP_CONFIDENCE) -> tuple[pd.DataFrame, pd.DataFrame]:
    lo_q, hi_q = 100 * (1 - confidence) / 2, 100 * (1 + confidence) / 2
    ci_rows, diff_rows = [], []
    for (policy, horizon), cell in common.groupby(["policy", "horizon"], sort=True):
        cities = sorted(cell["city"].astype(str).unique())
        weights = city_cluster_weights(cities, replicates, seed)
        for thr in THRESHOLDS:
            boots, points = {}, {}
            for model in MODEL_ORDER:
                frame = cell[cell["model"] == model]
                if frame.empty:
                    continue
                counts = _city_counts(frame, cities, thr)
                points[model] = _csi(counts)
                boots[model] = _csi(counts, weights)
                valid = boots[model][~np.isnan(boots[model])]
                ci_rows.append({
                    "policy": policy, "horizon_days": int(horizon), "threshold": thr, "model": model,
                    "csi": points[model],
                    "ci_lower": float(np.percentile(valid, lo_q)) if len(valid) else np.nan,
                    "ci_upper": float(np.percentile(valid, hi_q)) if len(valid) else np.nan,
                    "valid_replicates": int(len(valid)), "replicates": replicates, "seed": seed,
                    "n_cities": len(cities), "events": int(counts[:, 0].sum() + counts[:, 1].sum()),
                    "flag": "LOW-EVENT-COUNT" if counts[:, 0].sum() + counts[:, 1].sum() < LOW_EVENT_COUNT else ""})
            for model in ("regularized_linear", "xgboost"):
                diff = boots[model] - boots["persistence"]
                ok = diff[~np.isnan(diff)]
                diff_rows.append({
                    "policy": policy, "horizon_days": int(horizon), "threshold": thr,
                    "comparison": f"{model}_minus_persistence",
                    "csi_difference": points[model] - points["persistence"],
                    "ci_lower": float(np.percentile(ok, lo_q)) if len(ok) else np.nan,
                    "ci_upper": float(np.percentile(ok, hi_q)) if len(ok) else np.nan,
                    "excludes_zero": bool(len(ok) and (np.percentile(ok, lo_q) > 0 or np.percentile(ok, hi_q) < 0)),
                    "valid_replicates": int(len(ok)), "replicates": replicates, "seed": seed})
    return pd.DataFrame(ci_rows), pd.DataFrame(diff_rows)


def category_tables(common: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, matrices = [], []
    for policy, horizon, model, frame in groups(common):
        if model not in CATEGORY_MODELS:
            continue
        rows.append({"policy": policy, "horizon_days": horizon, "model": model,
                     **est_metrics.category_metrics(frame["y_true"], frame["y_pred"])})
        cm = est_metrics.confusion(frame["y_true"], frame["y_pred"])
        long = cm.reset_index().melt(id_vars="index", var_name="predicted", value_name="count")
        long = long.rename(columns={"index": "observed"})
        long.insert(0, "model", model)
        long.insert(0, "horizon_days", horizon)
        long.insert(0, "policy", policy)
        matrices.append(long)
    return pd.DataFrame(rows), pd.concat(matrices, ignore_index=True)


def zone_of(share: float) -> str:
    if share >= ZONE_HIGH:
        return "high"
    return "medium" if share >= ZONE_MEDIUM else "low"


def zone_tables(common: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    from scipy.stats import spearmanr

    city_rows, summary = [], []
    for policy, horizon, model, frame in groups(common):
        per_city = frame.groupby("city").apply(
            lambda g: pd.Series({"n_days": len(g),
                                 "observed_share_gt200": float((g["y_true"] > 200).mean()),
                                 "forecast_share_gt200": float((g["y_pred"] > 200).mean())}),
            include_groups=False).reset_index()
        per_city["observed_zone"] = per_city["observed_share_gt200"].map(zone_of)
        per_city["forecast_zone"] = per_city["forecast_share_gt200"].map(zone_of)
        per_city["zone_match"] = per_city["observed_zone"] == per_city["forecast_zone"]
        per_city.insert(0, "model", model)
        per_city.insert(0, "horizon_days", horizon)
        per_city.insert(0, "policy", policy)
        city_rows.append(per_city)
        obs, fc = per_city["observed_share_gt200"], per_city["forecast_share_gt200"]
        rho = float("nan") if (obs.nunique() < 2 or fc.nunique() < 2) else float(spearmanr(obs, fc).statistic)
        summary.append({"policy": policy, "horizon_days": horizon, "model": model,
                        "n_cities": len(per_city), "exact_zone_agreement": float(per_city["zone_match"].mean()),
                        "cities_matching": int(per_city["zone_match"].sum()), "spearman_rho": rho,
                        "observed_high": int((per_city["observed_zone"] == "high").sum()),
                        "forecast_high": int((per_city["forecast_zone"] == "high").sum())})
    return pd.DataFrame(summary), pd.concat(city_rows, ignore_index=True)


def lockdown_warning_table(common: pd.DataFrame) -> pd.DataFrame:
    dates = pd.to_datetime(common["target_date"]).dt.normalize()
    parts = []
    for name, (start, end) in (("pre_lockdown", PRE_LOCKDOWN_WINDOW), ("lockdown", LOCKDOWN_WINDOW)):
        window = common[dates.between(start, end, inclusive="both")]
        parts.append(warning_table(window, {"window": name, "window_start": start, "window_end": end}))
    return pd.concat(parts, ignore_index=True)


# ------------------------------------------------------------------- figures
def make_figures(ci: pd.DataFrame, common: pd.DataFrame, out_dir: Path) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig_dir = out_dir / "figures"
    fig_dir.mkdir(exist_ok=True)
    paths = []
    policies = sorted(ci["policy"].unique())
    fig, axes = plt.subplots(1, len(policies), figsize=(7 * len(policies), 4.8), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, policy in zip(axes, policies):
        sub = ci[(ci["policy"] == policy) & (ci["threshold"] == 200)]
        width = 0.13
        for i, model in enumerate(MODEL_ORDER):
            m = sub[sub["model"] == model].sort_values("horizon_days")
            if m.empty:
                continue
            x = np.array([{1: 0, 3: 1, 7: 2}[h] for h in m["horizon_days"]]) + (i - 2.5) * width
            ax.bar(x, m["csi"], width, label=model,
                   yerr=[m["csi"] - m["ci_lower"], m["ci_upper"] - m["csi"]], capsize=2)
        ax.set_xticks([0, 1, 2], ["1 day", "3 days", "7 days"])
        ax.set_title(f"policy={policy} (observed AQI > 200; common cases)")
        ax.set_xlabel("Forecast horizon")
    axes[0].set_ylabel("CSI (95% city-cluster bootstrap CI)")
    axes[0].legend(fontsize=7)
    fig.suptitle("POST-HOC (not pre-registered)", fontsize=9)
    fig.tight_layout()
    p = fig_dir / "fig_csi_gt200_by_horizon_model.png"
    fig.savefig(p, dpi=300)
    plt.close(fig)
    paths.append(p)

    frame = common[(common["policy"] == FIGURE_POLICY) & (common["horizon"] == 1) & (common["model"] == "xgboost")]
    cm = est_metrics.confusion(frame["y_true"], frame["y_pred"]).to_numpy()
    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    ax.imshow(cm, cmap="Blues")
    for (r, c), v in np.ndenumerate(cm):
        ax.text(c, r, v, ha="center", va="center", fontsize=8, color="black" if v < cm.max() / 2 else "white")
    ax.set_xticks(range(6), est_metrics.CATEGORIES, rotation=45, ha="right")
    ax.set_yticks(range(6), est_metrics.CATEGORIES)
    ax.set_xlabel("Forecast category")
    ax.set_ylabel("Observed category")
    ax.set_title(f"XGBoost, 1-day horizon, policy={FIGURE_POLICY} (post-hoc, not pre-registered)", fontsize=9)
    fig.tight_layout()
    p = fig_dir / "fig_confusion_xgboost_h1.png"
    fig.savefig(p, dpi=300)
    plt.close(fig)
    paths.append(p)
    return paths


# ------------------------------------------------------------------- summary
CAVEATS = f"""\
## Status and caveats

- **{LABEL}.**
- The frozen run did not save per-row predictions; they were regenerated by calling the frozen
  `score_locked_test` unchanged and are gated against `tables/test_common_case_with_ci.csv` of the frozen run (see `GATE_PASSED.json`).
- All metrics use common cases only (rows where every model in the policy/horizon cell has a valid prediction), 20 cities contribute.
- Warning = forecast > threshold; event = observed > threshold. POD = hits/(hits+misses), FAR = false alarms/(hits+false alarms),
  CSI = hits/(hits+misses+false alarms); undefined cells are NaN. Cells with fewer than {LOW_EVENT_COUNT} events are flagged LOW-EVENT-COUNT.
- Bootstrap: cities resampled with replacement, {BOOTSTRAP_REPLICATES} replicates, seed {BOOTSTRAP_SEED}, percentile 95% CI, same resampling
  scheme as the frozen run; replicates where a CSI is undefined (no events and no warnings) are dropped and counted in `valid_replicates`.
- Categories: six CPCB bands (<=50, <=100, <=200, <=300, <=400, >400) from `research/aqi_estimation/metrics.py`; macro-F1 averages over
  categories present in truth or forecast.
- Risk zones (defined in this analysis; the estimation study had none): share of common-case test days above 200 per city;
  high >= 30%, medium >= 10% and < 30%, low < 10%.
- Lockdown split reuses the frozen windows (pre-lockdown 2020-01-01..2020-03-24, lockdown 2020-03-25..2020-07-01). The request said
  "warnings (b only)"; this was interpreted as the warning metrics of item (a) per window, without bootstrap intervals.
- Capped policy: observed values above 500 are capped at 500, so categories/events at the top of the scale are affected by that policy.
"""


def md_table(df: pd.DataFrame) -> str:
    fmt = lambda v: f"{v:.4f}" if isinstance(v, (float, np.floating)) else str(v)
    lines = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)]
    lines += ["| " + " | ".join(fmt(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(lines)


def write_summary(out_dir: Path) -> Path:
    parts = [f"# Post-hoc results summary for frozen run {FROZEN_RUN_ID}\n", f"**{LABEL}.**\n", CAVEATS,
             "Every table below is rendered from the CSV named in its heading (paths relative to this folder).\n"]
    for csv in sorted((out_dir / "tables").glob("*.csv")):
        df = pd.read_csv(csv)
        if len(df) > 400:
            parts.append(f"## tables/{csv.name}\n\n{len(df)} rows; not inlined.\n")
        else:
            parts.append(f"## tables/{csv.name}\n\n{md_table(df)}\n")
    parts.append("## Figures\n\n" + "\n".join(f"- figures/{p.name}" for p in sorted((out_dir / "figures").glob("*.png"))) + "\n")
    path = out_dir / "RESULTS_SUMMARY_POSTHOC.md"
    path.write_text("\n".join(parts), encoding="utf-8")
    return path


# ---------------------------------------------------------------------- main
def run_posthoc(
    *,
    frozen_dir: Path = RESULTS_ROOT / FROZEN_RUN_ID,
    out_dir: Path | None = None,
    dataset: Path = DATASET,
    do_preflight: bool = True,
    prediction_source: Callable[[pd.DataFrame, dict], tuple[pd.DataFrame, list[dict]]] = generate_predictions,
    replicates: int = BOOTSTRAP_REPLICATES,
) -> Path:
    frozen_dir = Path(frozen_dir)
    out_dir = ensure_outside_frozen(out_dir or frozen_dir.with_name(frozen_dir.name + "_posthoc"), frozen_dir)
    record_path = frozen_dir / "run_record.json"
    frozen_record = json.loads(record_path.read_text(encoding="utf-8"))
    frozen_table = frozen_dir / "tables" / "test_common_case_with_ci.csv"

    print("[preflight]", flush=True)
    pre = preflight(frozen_record, dataset) if do_preflight else {"skipped": True}
    print("[frozen selected configs]")
    for run in frozen_record["test_runs"]:
        print(f"  {run['policy']}/h{run['horizon_days']}: ridge_alpha={run['ridge_alpha']} xgboost={run['xgboost_config']}")

    print("[predictions]", flush=True)
    history = pd.read_csv(dataset)
    pred, run_info = prediction_source(history, frozen_record)

    print("[gate]", flush=True)
    gate = run_gate(pred, frozen_table, out_dir)  # raises GateFailed and writes only GATE_FAILED.md
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "tables").mkdir(exist_ok=True)

    pred_path = out_dir / "test_predictions_posthoc.csv"
    pred.to_csv(pred_path, index=False, lineterminator="\n")
    pred_sha = sha256_file(pred_path)
    (out_dir / "test_predictions_posthoc.csv.sha256").write_text(f"{pred_sha}  {pred_path.name}\n", encoding="utf-8")
    reread = pd.read_csv(pred_path)
    recheck = compare_to_frozen(reread, frozen_table)
    if not recheck["passed"].all():
        raise GateFailed("Gate failed after CSV round-trip")
    gate["summary"]["csv_roundtrip_max_abs_mae_difference"] = float(recheck["abs_diff"].max())
    (out_dir / "GATE_PASSED.json").write_text(json.dumps({**gate, "label": LABEL}, indent=2), encoding="utf-8")

    common = reread[reread["in_common_case"] & reread["target_valid"].astype(bool)].copy()
    tables = out_dir / "tables"
    warnings = warning_table(common)
    warnings.to_csv(tables / "warnings_gt200_gt300.csv", index=False)
    ci, diff = csi_bootstrap(common, replicates=replicates)
    ci.to_csv(tables / "csi_bootstrap_ci.csv", index=False)
    diff.to_csv(tables / "csi_difference_vs_persistence.csv", index=False)
    cat, conf = category_tables(common)
    cat.to_csv(tables / "category_metrics.csv", index=False)
    conf.to_csv(tables / "category_confusion_matrices.csv", index=False)
    zones, zone_city = zone_tables(common)
    zones.to_csv(tables / "risk_zone_agreement.csv", index=False)
    zone_city.to_csv(tables / "risk_zone_per_city.csv", index=False)
    lockdown = lockdown_warning_table(common)
    lockdown.to_csv(tables / "warnings_lockdown_split.csv", index=False)
    make_figures(ci, common, out_dir)
    write_summary(out_dir)

    record = {
        "label": LABEL,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "frozen_run_id": FROZEN_RUN_ID,
        "inputs": {
            "dataset_sha256": sha256_file(dataset),
            "frozen_run_record_sha256": sha256_file(record_path),
            "frozen_test_common_case_with_ci_sha256": sha256_file(frozen_table),
            "estimation_metrics_py_sha256": sha256_file(Path(est_metrics.__file__)),
        },
        "preflight": pre,
        "environment": _versions(),
        "code": {"git_commit": _git("rev-parse", "HEAD"),
                 "tracked_changes": (_git("status", "--porcelain=v1", "--untracked-files=no") or "").splitlines()},
        "gate": gate["summary"],
        "row_counts": {"prediction_rows": int(len(pred)), "common_case_rows": int(len(common)),
                       "common_case_cells": run_info},
        "settings": {"thresholds": list(THRESHOLDS), "bootstrap_replicates": replicates, "bootstrap_seed": BOOTSTRAP_SEED,
                     "zones": {"high": ZONE_HIGH, "medium": ZONE_MEDIUM}, "low_event_count": LOW_EVENT_COUNT},
        "output_file_sha256": {},
    }
    record_file = out_dir / "POSTHOC_RECORD.json"
    for path in sorted(out_dir.rglob("*")):
        if path.is_file() and path != record_file:
            record["output_file_sha256"][path.relative_to(out_dir).as_posix()] = sha256_file(path)
    record_file.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return out_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        out = run_posthoc(out_dir=args.out_dir)
    except (PreflightError, GateFailed, PermissionError) as error:
        print(f"STOPPED: {error}", file=sys.stderr)
        return 1
    print(out)
    print("predictions sha256:", sha256_file(out / "test_predictions_posthoc.csv"))
    print("POSTHOC_RECORD.json sha256:", sha256_file(out / "POSTHOC_RECORD.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
