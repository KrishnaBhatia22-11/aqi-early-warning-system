"""Metrics, CPCB categories, and the city-cluster bootstrap."""

from __future__ import annotations

import numpy as np
import pandas as pd

CATEGORIES = ["Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe"]
_EDGES = np.array([50, 100, 200, 300, 400], dtype=float)


def categorize(values) -> np.ndarray:
    """CPCB category index 0..5: <=50, <=100, <=200, <=300, <=400, else Severe."""
    return np.digitize(np.asarray(values, dtype=float), _EDGES, right=True)


def regression_metrics(y, pred) -> dict[str, float]:
    y = np.asarray(y, dtype=float)
    pred = np.asarray(pred, dtype=float)
    err = pred - y
    sse = float(np.sum(err**2))
    sst = float(np.sum((y - y.mean()) ** 2))
    return {
        "n": int(len(y)),
        "MAE": float(np.mean(np.abs(err))),
        "RMSE": float(np.sqrt(sse / len(y))),
        "R2": float(1.0 - sse / sst) if sst > 0 else float("nan"),
    }


def per_city_mae(cities, y, pred) -> pd.DataFrame:
    frame = pd.DataFrame({"City": np.asarray(cities), "ae": np.abs(np.asarray(pred) - np.asarray(y))})
    out = frame.groupby("City")["ae"].agg(["count", "mean"]).reset_index()
    return out.rename(columns={"count": "n", "mean": "MAE"})


def cluster_bootstrap(
    cities,
    y,
    predictions: dict[str, np.ndarray],
    *,
    reps: int,
    seed: int,
    confidence: float = 0.95,
    diff_pairs: tuple[tuple[str, str], ...] = (),
) -> pd.DataFrame:
    """City-cluster percentile bootstrap for MAE, RMSE and R2 (and MAE differences).

    Whole cities are resampled with replacement; metrics are recomputed on the
    pooled resampled rows from per-city sufficient statistics.
    """
    cities = np.asarray(cities)
    y = np.asarray(y, dtype=float)
    names = sorted(set(cities))
    k = len(names)
    idx = np.searchsorted(names, cities)
    n_c = np.bincount(idx, minlength=k).astype(float)
    s_y = np.bincount(idx, weights=y, minlength=k)
    s_yy = np.bincount(idx, weights=y * y, minlength=k)
    stats = {}
    for model, pred in predictions.items():
        err = np.asarray(pred, dtype=float) - y
        stats[model] = (
            np.bincount(idx, weights=np.abs(err), minlength=k),
            np.bincount(idx, weights=err * err, minlength=k),
        )

    rng = np.random.default_rng(seed)
    draws = rng.integers(0, k, size=(reps, k))
    counts = np.stack([np.bincount(row, minlength=k) for row in draws]).astype(float)
    n = counts @ n_c
    sst = counts @ s_yy - (counts @ s_y) ** 2 / n
    lo_q, hi_q = (1 - confidence) / 2 * 100, (1 + confidence) / 2 * 100

    rows = []
    boot_mae = {}
    for model, (sae, sse) in stats.items():
        boot_mae[model] = counts @ sae / n
        boot = {
            "MAE": boot_mae[model],
            "RMSE": np.sqrt(counts @ sse / n),
            "R2": 1.0 - (counts @ sse) / sst,
        }
        point = regression_metrics(y, predictions[model])
        for metric, values in boot.items():
            rows.append({
                "model": model, "metric": metric, "estimate": point[metric],
                "ci_low": float(np.percentile(values, lo_q)),
                "ci_high": float(np.percentile(values, hi_q)),
                "n_rows": point["n"], "n_cities": k, "reps": reps, "seed": seed,
            })
    for a, b in diff_pairs:
        diff = boot_mae[a] - boot_mae[b]
        point = (regression_metrics(y, predictions[a])["MAE"]
                 - regression_metrics(y, predictions[b])["MAE"])
        rows.append({
            "model": f"{a} minus {b}", "metric": "MAE_difference", "estimate": point,
            "ci_low": float(np.percentile(diff, lo_q)), "ci_high": float(np.percentile(diff, hi_q)),
            "n_rows": int(len(y)), "n_cities": k, "reps": reps, "seed": seed,
        })
    return pd.DataFrame(rows)


def category_metrics(y, pred) -> dict[str, float]:
    from sklearn.metrics import f1_score

    ty, tp = categorize(y), categorize(pred)
    labels = sorted(set(ty) | set(tp))
    return {
        "n": int(len(ty)),
        "accuracy": float(np.mean(ty == tp)),
        "within_one": float(np.mean(np.abs(ty - tp) <= 1)),
        "macro_f1": float(f1_score(ty, tp, labels=labels, average="macro", zero_division=0)),
    }


def confusion(y, pred) -> pd.DataFrame:
    ty, tp = categorize(y), categorize(pred)
    matrix = np.zeros((6, 6), dtype=int)
    np.add.at(matrix, (ty, tp), 1)
    return pd.DataFrame(matrix, index=[f"true_{c}" for c in CATEGORIES],
                        columns=[f"pred_{c}" for c in CATEGORIES])


def event_scores(y, pred, threshold: float) -> dict[str, float]:
    """Event = value > threshold. POD=a/(a+c), FAR=b/(a+b), CSI=a/(a+b+c)."""
    obs = np.asarray(y, dtype=float) > threshold
    fc = np.asarray(pred, dtype=float) > threshold
    a = int(np.sum(obs & fc))
    b = int(np.sum(~obs & fc))
    c = int(np.sum(obs & ~fc))

    def div(num, den):
        return float(num / den) if den else float("nan")

    return {
        "threshold": threshold, "events": a + c, "hits": a, "misses": c,
        "false_alarms": b, "POD": div(a, a + c), "FAR": div(b, a + b), "CSI": div(a, a + b + c),
    }
