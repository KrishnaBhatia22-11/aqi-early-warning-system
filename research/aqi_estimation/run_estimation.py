"""Pollutant -> AQI estimation study ("Model A") with a once-only 2020 test.

Phase 1 (development) sees only rows up to the validation end date: it fits the
models on 2015-2018, selects an XGBoost config on 2019, and freezes the choice
(selection.json, hashed) before any test row is read. Phase 2 (test) scores
2020-01-01..2020-07-01 once; a repo-level ledger refuses a second scoring.

    venv\\Scripts\\python.exe -m research.aqi_estimation.run_estimation
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version

import numpy as np
import pandas as pd

from research.aqi_estimation import cpcb_formula as cf
from research.aqi_estimation import metrics as mt

ROOT = Path(__file__).resolve().parents[2]
POLLUTANTS = ["PM2.5", "PM10", "NO", "NO2", "NOx", "NH3", "CO", "SO2", "O3"]
DEPLOYED_XGB = {"n_estimators": 200, "max_depth": 8, "learning_rate": 0.1, "subsample": 0.8}
GRID = {"max_depth": [3, 5, 8], "n_estimators": [200, 400], "learning_rate": [0.05, 0.1]}
XGB_SEED = 42
BOOTSTRAP_SEED = 20200101
BOOTSTRAP_REPS = 2000
RANDOM_SPLIT_SEED = 42
MASKED = ["PM2.5", "PM10", "NO2", "CO"]
M_DEPLOYED, M_SELECTED, M_LINEAR, M_FORMULA = "xgb_deployed_config", "xgb_selected", "linear", "cpcb_formula"
MODELS = [M_DEPLOYED, M_SELECTED, M_LINEAR, M_FORMULA]
LEDGER = Path(__file__).with_name("SCORING_LEDGER.jsonl")


@dataclass(frozen=True)
class Windows:
    train_start: str = "2015-01-01"
    train_end: str = "2018-12-31"
    val_start: str = "2019-01-01"
    val_end: str = "2019-12-31"
    test_start: str = "2020-01-01"
    test_end: str = "2020-07-01"


@dataclass
class Config:
    dataset: Path = ROOT / "data" / "raw" / "city_day.csv"
    processed: Path = ROOT / "data" / "processed" / "clean_data.csv"
    artifact: Path = ROOT / "models" / "best_model.pkl"
    artifact_features: Path = ROOT / "models" / "feature_cols.pkl"
    out_root: Path = ROOT / "research" / "aqi_estimation" / "results"
    ledger: Path = LEDGER
    windows: Windows = field(default_factory=Windows)
    grid: dict = field(default_factory=lambda: dict(GRID))
    reps: int = BOOTSTRAP_REPS
    run_reference: bool = True
    record_in_ledger: bool = True


# ---------------------------------------------------------------- utilities
def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def git(*args: str) -> str | None:
    try:
        return subprocess.run(["git", "-C", str(ROOT), *args], check=True, capture_output=True,
                              text=True, encoding="utf-8").stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def package_versions() -> dict[str, str | None]:
    out = {"python": sys.version.split()[0]}
    for name in ["numpy", "pandas", "scikit-learn", "scipy", "xgboost", "shap", "matplotlib", "joblib"]:
        try:
            out[name] = version(name)
        except PackageNotFoundError:
            out[name] = None
    return out


class ScoringLog:
    def __init__(self, path: Path):
        self.path, self.events = path, []

    def add(self, event: str, **detail) -> None:
        self.events.append({"utc": utc_now(), "event": event, **detail})
        self.path.write_text(json.dumps(self.events, indent=2), encoding="utf-8")


def claim_test_scoring(ledger: Path, run_id: str, window: str) -> None:
    """Refuse a second scoring of the same test window; otherwise record the claim."""
    if ledger.exists():
        for line in ledger.read_text(encoding="utf-8").splitlines():
            entry = json.loads(line)
            if entry.get("window") == window and entry.get("event") == "test_scoring_started":
                raise RuntimeError(
                    f"Test window {window} was already scored (run {entry['run_id']}); "
                    "refusing to score it again.")
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"event": "test_scoring_started", "window": window,
                                 "run_id": run_id, "utc": utc_now()}) + "\n")


# --------------------------------------------------------------------- data
def load_valid(path: Path) -> tuple[pd.DataFrame, dict]:
    raw = pd.read_csv(path, parse_dates=["Date"])
    if raw.duplicated(["City", "Date"]).any():
        raise ValueError("duplicate City/Date rows")
    valid = raw["AQI"].between(0, 500)
    info = {"raw_rows": int(len(raw)), "missing_aqi": int(raw["AQI"].isna().sum()),
            "aqi_above_500_excluded": int((raw["AQI"] > 500).sum()),
            "aqi_negative_excluded": int((raw["AQI"] < 0).sum()), "valid_rows": int(valid.sum())}
    return raw.loc[valid].sort_values(["Date", "City"]).reset_index(drop=True), info


def window(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    return df[(df["Date"] >= start) & (df["Date"] <= end)].reset_index(drop=True)


def make_xgb(params: dict):
    from xgboost import XGBRegressor

    return XGBRegressor(**params, random_state=XGB_SEED, n_jobs=1, verbosity=0)


class LinearModel:
    """OLS on train-median-imputed pollutants (medians fitted on training rows only)."""

    def fit(self, X: pd.DataFrame, y):
        from sklearn.linear_model import LinearRegression

        self.medians = X.median()
        self.model = LinearRegression().fit(X.fillna(self.medians), y)
        return self

    def predict(self, X: pd.DataFrame):
        return self.model.predict(X.fillna(self.medians))


# -------------------------------------------------------------- development
def develop(train: pd.DataFrame, val: pd.DataFrame, grid: dict, out: Path) -> dict:
    """Fit on train, select on val. Never receives test rows."""
    Xtr, ytr, Xva, yva = train[POLLUTANTS], train["AQI"], val[POLLUTANTS], val["AQI"]
    rows, fitted = [], {}
    combos = [dict(zip(grid, values)) for values in itertools.product(*grid.values())]
    combos.sort(key=lambda c: (c["max_depth"], c["n_estimators"], c["learning_rate"]))
    for combo in combos:
        params = {**combo, "subsample": 0.8}
        model = make_xgb(params).fit(Xtr, ytr)
        m = mt.regression_metrics(yva, model.predict(Xva))
        rows.append({**params, "val_MAE": m["MAE"], "val_RMSE": m["RMSE"], "val_R2": m["R2"]})
        fitted[json.dumps(params, sort_keys=True)] = model
    grid_df = pd.DataFrame(rows)
    best = grid_df.sort_values(["val_MAE"], kind="stable").iloc[0]  # ties -> simplest (sorted order)
    selected = {k: (int(best[k]) if k in ("max_depth", "n_estimators") else float(best[k]))
                for k in ("n_estimators", "max_depth", "learning_rate", "subsample")}
    deployed_model = make_xgb(DEPLOYED_XGB).fit(Xtr, ytr)
    models = {M_DEPLOYED: deployed_model,
              M_SELECTED: fitted[json.dumps(selected, sort_keys=True)],
              M_LINEAR: LinearModel().fit(Xtr, ytr)}
    formula = cf.compute_aqi(val)
    comp = formula["computable"].to_numpy()
    val_rows = []
    for name, model in models.items():
        p = model.predict(Xva)
        val_rows.append({"model": name, "subset": "all_val_rows", **mt.regression_metrics(yva, p)})
        val_rows.append({"model": name, "subset": "formula_computable_rows",
                         **mt.regression_metrics(yva[comp], p[comp])})
    val_rows.append({"model": M_FORMULA, "subset": "formula_computable_rows",
                     **mt.regression_metrics(yva[comp], formula["formula_aqi"].to_numpy()[comp])})
    grid_df.to_csv(out / "tables" / "dev_xgb_grid_2019.csv", index=False)
    pd.DataFrame(val_rows).to_csv(out / "tables" / "dev_validation_2019.csv", index=False)
    for name in (M_DEPLOYED, M_SELECTED):
        models[name].save_model(str(out / "models" / f"{name}.ubj"))
    selection = {"selected_xgb_params": selected, "deployed_xgb_params": DEPLOYED_XGB,
                 "xgb_seed": XGB_SEED, "grid": grid, "selection_metric": "2019 MAE, all rows",
                 "train_rows": int(len(train)), "val_rows": int(len(val)),
                 "linear_train_medians": models[M_LINEAR].medians.to_dict(),
                 "pollutant_features": POLLUTANTS}
    (out / "selection.json").write_text(json.dumps(selection, indent=2), encoding="utf-8")
    return {"models": models, "selection": selection}


# --------------------------------------------------------------------- test
def predict_all(models: dict, frame: pd.DataFrame) -> dict[str, np.ndarray]:
    X = frame[POLLUTANTS]
    preds = {name: np.asarray(m.predict(X), dtype=float) for name, m in models.items()}
    preds[M_FORMULA] = cf.compute_aqi(frame)["formula_aqi"].to_numpy()
    return preds


def score_test(test: pd.DataFrame, models: dict, out: Path, reps: int) -> dict:
    tables = out / "tables"
    y = test["AQI"].to_numpy(dtype=float)
    formula = cf.compute_aqi(test)
    comp = formula["computable"].to_numpy()
    preds = predict_all(models, test)

    # per-row predictions
    row_frame = test[["City", "Date", "AQI"]].rename(columns={"AQI": "recorded_aqi"}).copy()
    for name in MODELS:
        row_frame[f"pred_{name}"] = preds[name]
    row_frame["formula_computable"] = comp
    row_frame["n_pollutants_formula"] = formula["n_pollutants"].to_numpy()
    row_frame["dominant_pollutant"] = formula["dominant"].to_numpy()
    row_frame["recorded_category"] = [mt.CATEGORIES[i] for i in mt.categorize(y)]
    row_frame.to_csv(tables / "test_predictions_2020.csv", index=False)

    # Step 1: metrics, common cases (formula computable) and all rows
    common = {n: preds[n][comp] for n in MODELS}
    boot_common = mt.cluster_bootstrap(
        test["City"].to_numpy()[comp], y[comp], common, reps=reps, seed=BOOTSTRAP_SEED,
        diff_pairs=((M_SELECTED, M_FORMULA), (M_SELECTED, M_LINEAR), (M_LINEAR, M_FORMULA)))
    boot_common.insert(0, "subset", "common_cases_formula_computable")
    allrows = {n: preds[n] for n in MODELS[:3]}
    boot_all = mt.cluster_bootstrap(
        test["City"].to_numpy(), y, allrows, reps=reps, seed=BOOTSTRAP_SEED,
        diff_pairs=((M_SELECTED, M_LINEAR),))
    boot_all.insert(0, "subset", "all_test_rows")
    pd.concat([boot_common, boot_all]).to_csv(tables / "step1_metrics_bootstrap_ci.csv", index=False)

    city_rows = []
    for n in MODELS:
        t = mt.per_city_mae(test["City"].to_numpy()[comp], y[comp], common[n])
        t.insert(0, "model", n)
        city_rows.append(t)
    pd.concat(city_rows).to_csv(tables / "step1_per_city_mae_common.csv", index=False)
    coverage = pd.DataFrame([
        {"model": n, "rows_total": len(test),
         "rows_predicted": int(len(test) if n != M_FORMULA else comp.sum()),
         "coverage": 1.0 if n != M_FORMULA else float(comp.mean())} for n in MODELS])
    coverage.to_csv(tables / "step1_coverage.csv", index=False)

    # Step 2: mask one pollutant at a time
    sel = models[M_SELECTED]
    step2, long_rows = [], []
    for masked in [None] + MASKED:
        masked_frame = test.copy()
        if masked:
            masked_frame[masked] = np.nan
        f2 = cf.compute_aqi(masked_frame)
        c2 = f2["computable"].to_numpy()
        px = np.asarray(sel.predict(masked_frame[POLLUTANTS]), dtype=float)
        pf = f2["formula_aqi"].to_numpy()
        row = {"masked_pollutant": masked or "none", "n_test_rows": len(test),
               "xgb_MAE_all_rows": float(np.mean(np.abs(px - y))),
               "xgb_RMSE_all_rows": float(np.sqrt(np.mean((px - y) ** 2))),
               "formula_computable_rows": int(c2.sum()), "formula_coverage": float(c2.mean())}
        if c2.any():
            row["xgb_MAE_on_formula_computable"] = float(np.mean(np.abs(px[c2] - y[c2])))
            row["formula_MAE"] = float(np.mean(np.abs(pf[c2] - y[c2])))
        step2.append(row)
        long_rows.append(pd.DataFrame({
            "masked_pollutant": masked or "none", "City": test["City"], "Date": test["Date"],
            "recorded_aqi": y, "pred_xgb_selected": px, "pred_cpcb_formula": pf}))
    pd.DataFrame(step2).to_csv(tables / "step2_missing_input_robustness.csv", index=False)
    pd.concat(long_rows).to_csv(tables / "test_predictions_2020_masked.csv", index=False)

    # Step 3: SHAP
    shap_result = explain(test, sel, formula, out)

    # Step 4: categories
    cat_rows, event_rows = [], []
    for n in MODELS:
        cat_rows.append({"model": n, "subset": "common_cases", **mt.category_metrics(y[comp], common[n])})
        mt.confusion(y[comp], common[n]).to_csv(tables / f"step4_confusion_{n}.csv")
        for thr in (200, 300):
            event_rows.append({"model": n, "subset": "common_cases", **mt.event_scores(y[comp], common[n], thr)})
    for n in MODELS[:3]:
        cat_rows.append({"model": n, "subset": "all_test_rows", **mt.category_metrics(y, preds[n])})
        for thr in (200, 300):
            event_rows.append({"model": n, "subset": "all_test_rows", **mt.event_scores(y, preds[n], thr)})
    pd.DataFrame(cat_rows).to_csv(tables / "step4_category_metrics.csv", index=False)
    pd.DataFrame(event_rows).to_csv(tables / "step4_event_scores.csv", index=False)
    plot_confusions(y[comp], common, out)
    plot_scatter(y[comp], common, out)
    return {"n_test": int(len(test)), "n_common": int(comp.sum()), **shap_result}


def explain(test: pd.DataFrame, model, formula: pd.DataFrame, out: Path) -> dict:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import shap

    tables, figures = out / "tables", out / "figures"
    X = test[POLLUTANTS].reset_index(drop=True)
    explainer = shap.TreeExplainer(model)
    sv = explainer.shap_values(X)
    abs_sv = pd.DataFrame(np.abs(sv), columns=POLLUTANTS)
    overall = abs_sv.mean().sort_values(ascending=False).rename("mean_abs_shap").reset_index()
    overall.columns = ["pollutant", "mean_abs_shap"]
    overall["n_rows"] = len(X)
    overall.to_csv(tables / "step3_mean_abs_shap_overall.csv", index=False)
    by_city = abs_sv.assign(City=test["City"].to_numpy()).groupby("City").mean()
    by_city.insert(0, "n_rows", test.groupby("City").size())
    by_city.to_csv(tables / "step3_mean_abs_shap_by_city.csv")

    plt.figure()
    shap.summary_plot(sv, X, show=False)
    plt.savefig(figures / "step3_shap_beeswarm.png", dpi=300, bbox_inches="tight")
    plt.close("all")

    delhi = test.index[test["City"].eq("Delhi")]
    if len(delhi):
        i = int(test.loc[delhi, "AQI"].idxmax())
        exp = shap.Explanation(values=sv[i], base_values=float(np.ravel(explainer.expected_value)[0]),
                               data=X.iloc[i].to_numpy(), feature_names=POLLUTANTS)
        shap.plots.waterfall(exp, show=False)
        plt.title(f"Delhi {test.loc[i, 'Date'].date()} recorded AQI {test.loc[i, 'AQI']:.0f}", pad=38)
        plt.savefig(figures / "step3_shap_waterfall_delhi_max.png", dpi=300, bbox_inches="tight")
        plt.close("all")
        (tables / "step3_waterfall_day.json").write_text(json.dumps(
            {"city": "Delhi", "date": str(test.loc[i, "Date"].date()),
             "recorded_aqi": float(test.loc[i, "AQI"]), "prediction": float(model.predict(X.iloc[[i]])[0])}),
            encoding="utf-8")

    top = np.array(POLLUTANTS, dtype=object)[abs_sv.to_numpy().argmax(axis=1)]
    restricted_cols = [p for p in POLLUTANTS if p in cf.FORMULA_POLLUTANTS]
    top_restricted = np.array(restricted_cols, dtype=object)[abs_sv[restricted_cols].to_numpy().argmax(axis=1)]
    comp = formula["computable"].to_numpy()
    ag = pd.DataFrame({
        "City": test["City"].to_numpy(), "category": [mt.CATEGORIES[i] for i in mt.categorize(test["AQI"])],
        "top_shap": top, "top_shap_formula_pollutants_only": top_restricted,
        "dominant": formula["dominant"].to_numpy()})[comp]
    ag["agree"] = ag["top_shap"] == ag["dominant"]
    ag["agree_restricted"] = ag["top_shap_formula_pollutants_only"] == ag["dominant"]

    def table(groups):
        t = ag.groupby(groups).agg(n=("agree", "size"), agreement=("agree", "mean"),
                                   agreement_restricted=("agree_restricted", "mean")).reset_index()
        return t

    overall_ag = pd.DataFrame([{"n": len(ag), "agreement": ag["agree"].mean(),
                                "agreement_restricted": ag["agree_restricted"].mean()}])
    overall_ag.to_csv(tables / "step3_agreement_overall.csv", index=False)
    table("City").to_csv(tables / "step3_agreement_by_city.csv", index=False)
    cat = table("category")
    cat["category"] = pd.Categorical(cat["category"], mt.CATEGORIES, ordered=True)
    cat.sort_values("category").to_csv(tables / "step3_agreement_by_category.csv", index=False)
    pd.crosstab(ag["dominant"], ag["top_shap"]).to_csv(tables / "step3_dominant_vs_top_shap_crosstab.csv")
    return {"agreement_rows": int(len(ag))}


def plot_confusions(y, common: dict, out: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    names = [M_SELECTED, M_LINEAR, M_FORMULA]
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    for ax, n in zip(axes, names):
        cm = mt.confusion(y, common[n]).to_numpy()
        ax.imshow(cm, cmap="Blues")
        for (r, c), v in np.ndenumerate(cm):
            ax.text(c, r, v, ha="center", va="center", fontsize=8, color="black" if v < cm.max() / 2 else "white")
        ax.set_xticks(range(6), mt.CATEGORIES, rotation=45, ha="right")
        ax.set_yticks(range(6), mt.CATEGORIES)
        ax.set_xlabel("Predicted category")
        ax.set_ylabel("Recorded category")
        ax.set_title(n)
    fig.tight_layout()
    fig.savefig(out / "figures" / "step4_confusion_matrices.png", dpi=300)
    plt.close(fig)


def plot_scatter(y, common: dict, out: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    names = [M_SELECTED, M_LINEAR, M_FORMULA]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), sharex=True, sharey=True)
    for ax, n in zip(axes, names):
        ax.scatter(y, common[n], s=6, alpha=0.4)
        ax.plot([0, 500], [0, 500], "k--", lw=1)
        ax.set_xlabel("Recorded AQI")
        ax.set_title(n)
    axes[0].set_ylabel("Predicted AQI")
    fig.tight_layout()
    fig.savefig(out / "figures" / "step1_pred_vs_recorded.png", dpi=300)
    plt.close(fig)


# ------------------------------------------------------- random-split reference
def random_split_reference(valid: pd.DataFrame, cfg: Config, out: Path) -> pd.DataFrame:
    """Labeled comparison scores under a random 80/20 split (NOT the temporal protocol)."""
    import joblib
    from sklearn.model_selection import train_test_split

    rows = []
    if cfg.processed.exists() and cfg.artifact.exists():
        proc = pd.read_csv(cfg.processed)
        cols = joblib.load(cfg.artifact_features)
        _, Xte, _, yte = train_test_split(proc[cols], proc["AQI"], test_size=0.2, random_state=RANDOM_SPLIT_SEED)
        m = mt.regression_metrics(yte, joblib.load(cfg.artifact).predict(Xte))
        rows.append({"label": "RANDOM-SPLIT: original deployed artifact re-scored on its own random 20% split "
                              "(clean_data.csv: imputed, AQI clipped to 500, features include Year/Month/Season)",
                     "split": "random 80/20 seed 42", **m})
    Xtr, Xte, ytr, yte = train_test_split(valid[POLLUTANTS], valid["AQI"], test_size=0.2, random_state=RANDOM_SPLIT_SEED)
    m = mt.regression_metrics(yte, make_xgb(DEPLOYED_XGB).fit(Xtr, ytr).predict(Xte))
    rows.append({"label": "RANDOM-SPLIT: deployed XGBoost config, 9 pollutant features only, raw NaNs, "
                          "city_day valid AQI 0-500", "split": "random 80/20 seed 42", **m})
    frame = pd.DataFrame(rows)
    frame.to_csv(out / "tables" / "step1_random_split_reference.csv", index=False)
    return frame


# ------------------------------------------------------------------ summary
SUMMARY_NOTES = """\
## Method notes (fixed text)

- Features: 9 pollutants (PM2.5, PM10, NO, NO2, NOx, NH3, CO, SO2, O3). The deployed artifact also used
  Year/Month/Season_Code and train+test-wide median imputation; this study uses neither (raw NaNs,
  XGBoost native handling; linear regression uses training-set medians).
- Rows: city_day.csv with recorded AQI in [0, 500]; rows with AQI > 500 are excluded (the deployed pipeline clipped them to 500).
- Split: train 2015-01-01..2018-12-31, select on 2019, test 2020-01-01..2020-07-01. Models are NOT refit on 2019.
- Formula baseline: CPCB breakpoints on daily means; CO and O3 use daily means, not 8-hour means (approximation).
  Computable only with >=3 of 7 pollutants including PM2.5 or PM10. "Common cases" = rows where it is computable.
- Bootstrap: resample whole cities, 2000 replicates, seed 20200101, percentile 95% CI.
- Category macro-F1 averages over categories present in truth or prediction. Event > threshold: POD=hits/(hits+misses),
  FAR=false alarms/(hits+false alarms), CSI=hits/(hits+misses+false alarms).
- Step 3 agreement: strict compares top-|SHAP| pollutant (any of 9 features) with the formula's dominant pollutant;
  the restricted variant only considers the 7 formula pollutants (NO/NOx excluded) when picking the top SHAP feature.
- Years 2015-2020 data were already used by the separate forecasting study; its results folder is untouched.
"""


def md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    fmt = lambda v: f"{v:.4f}" if isinstance(v, (float, np.floating)) else str(v)
    lines = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(fmt(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(lines)


def write_summary(out: Path, run_id: str) -> None:
    parts = [f"# Results summary — run {run_id}\n",
             "Every table below is rendered directly from the CSV named in its heading (paths relative to this folder).\n",
             SUMMARY_NOTES]
    for csv in sorted((out / "tables").glob("*.csv")):
        if csv.name.startswith("test_predictions"):
            parts.append(f"## tables/{csv.name}\n\nPer-row predictions ({sum(1 for _ in csv.open()) - 1} rows); not inlined.\n")
            continue
        df = pd.read_csv(csv)
        parts.append(f"## tables/{csv.name}\n\n{md_table(df)}\n")
    parts.append("## Figures\n\n" + "\n".join(f"- figures/{p.name}" for p in sorted((out / "figures").glob("*.png"))) + "\n")
    (out / "RESULTS_SUMMARY.md").write_text("\n".join(parts), encoding="utf-8")


# --------------------------------------------------------------------- main
def run(cfg: Config) -> Path:
    short = git("rev-parse", "--short", "HEAD") or "nogit"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{stamp}-{short}"
    out = cfg.out_root / run_id
    for sub in ("tables", "figures", "models"):
        (out / sub).mkdir(parents=True)
    log = ScoringLog(out / "scoring_log.json")
    w = cfg.windows
    log.add("run_started", run_id=run_id, test_window=f"{w.test_start}..{w.test_end}")

    valid, data_info = load_valid(cfg.dataset)
    train, val = window(valid, w.train_start, w.train_end), window(valid, w.val_start, w.val_end)
    dev = develop(train, val, cfg.grid, out)  # test rows are not passed in
    selection_hash = sha256_file(out / "selection.json")
    log.add("development_frozen", selection_sha256=selection_hash,
            selected_xgb_params=dev["selection"]["selected_xgb_params"],
            test_rows_visible_to_development=0)

    window_key = f"{w.test_start}..{w.test_end}"
    if cfg.record_in_ledger:
        claim_test_scoring(cfg.ledger, run_id, window_key)
    log.add("test_scoring_started", window=window_key, ledger_recorded=cfg.record_in_ledger)
    test = window(valid, w.test_start, w.test_end)
    result = score_test(test, dev["models"], out, cfg.reps)
    log.add("test_scoring_finished", rows=result["n_test"], common_rows=result["n_common"])

    if cfg.run_reference:
        ref = random_split_reference(valid, cfg, out)
        log.add("random_split_reference_scored",
                note="labeled comparison only; random split, not the temporal test", rows=len(ref))

    shutil.copy(Path(__file__).with_name("PROVENANCE.md"), out / "PROVENANCE.md") \
        if Path(__file__).with_name("PROVENANCE.md").exists() else None
    write_summary(out, run_id)

    status = git("status", "--porcelain=v1", "--untracked-files=no")
    record = {
        "run_id": run_id,
        "created_utc": utc_now(),
        "dataset": {"path": str(cfg.dataset.relative_to(ROOT)) if cfg.dataset.is_relative_to(ROOT) else str(cfg.dataset),
                    "sha256": sha256_file(cfg.dataset), **data_info},
        "reference_inputs": {
            "clean_data.csv_sha256": sha256_file(cfg.processed) if cfg.processed.exists() else None,
            "best_model.pkl_sha256": sha256_file(cfg.artifact) if cfg.artifact.exists() else None},
        "git": {"commit": git("rev-parse", "HEAD"), "short": short, "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
                "tracked_changes_at_run": status.splitlines() if status is not None else None},
        "package_versions": package_versions(),
        "seeds": {"xgboost": XGB_SEED, "bootstrap": BOOTSTRAP_SEED, "random_split_reference": RANDOM_SPLIT_SEED},
        "windows": w.__dict__, "bootstrap_reps": cfg.reps,
        "selected_xgb_params": dev["selection"]["selected_xgb_params"],
        "selection_sha256": selection_hash,
        "scoring_events": log.events,
        "output_file_sha256": {},
    }
    record_path = out / "run_record.json"
    log.add("outputs_hashed")  # final log entry, written before hashing
    record["scoring_events"] = log.events
    for path in sorted(out.rglob("*")):
        if path.is_file() and path != record_path:
            record["output_file_sha256"][path.relative_to(out).as_posix()] = sha256_file(path)
    record_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", type=Path, default=None,
                        help="dry run: shift every window back (test=2018), write here, never touch the ledger")
    args = parser.parse_args()
    cfg = Config()
    if args.smoke:
        cfg.windows = Windows("2015-01-01", "2016-12-31", "2017-01-01", "2017-12-31", "2018-01-01", "2018-12-31")
        cfg.out_root, cfg.record_in_ledger, cfg.reps = args.smoke, False, 200
    out = run(cfg)
    print(out)
    print(sha256_file(out / "run_record.json"))


if __name__ == "__main__":
    main()
