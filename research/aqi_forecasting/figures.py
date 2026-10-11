"""Publication figures for the locked final-test run.

Single-column IEEE width (3.5 in), 300 dpi PNG, white background, serif
type, no titles inside the image (captions belong in the paper). Series
colors are the Okabe-Ito colorblind-safe set; the plotting order was checked
so every adjacent pair clears the CVD separation floor, and hatch texture
plus the companion CSV tables provide the secondary encoding.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

FIGURE_WIDTH_INCHES = 3.5
FIGURE_DPI = 300

# Okabe-Ito; this order is the validated adjacent-pair sequence.
METHOD_ORDER = (
    "persistence",
    "regularized_linear",
    "xgboost",
    "weekly_seasonal_naive",
    "city_month_climatology",
    "annual_seasonal_naive",
)
METHOD_COLORS = {
    "persistence": "#0072B2",
    "regularized_linear": "#D55E00",
    "xgboost": "#009E73",
    "weekly_seasonal_naive": "#56B4E9",
    "city_month_climatology": "#CC79A7",
    "annual_seasonal_naive": "#E69F00",
}
METHOD_HATCHES = {
    "persistence": "",
    "regularized_linear": "//",
    "xgboost": "\\\\",
    "weekly_seasonal_naive": "..",
    "city_month_climatology": "xx",
    "annual_seasonal_naive": "--",
}
METHOD_LABELS = {
    "persistence": "Persistence",
    "regularized_linear": "Ridge",
    "xgboost": "XGBoost",
    "weekly_seasonal_naive": "Weekly naive",
    "city_month_climatology": "Climatology",
    "annual_seasonal_naive": "Annual naive",
}
_INK = "#1a1a1a"
_MUTED = "#595959"


def apply_paper_style() -> None:
    """Set the shared serif, white-background, print-oriented defaults."""
    plt.rcParams.update(
        {
            "figure.dpi": FIGURE_DPI,
            "savefig.dpi": FIGURE_DPI,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.02,
            "font.family": "serif",
            "font.serif": ["DejaVu Serif", "Times New Roman", "Nimbus Roman"],
            "mathtext.fontset": "dejavuserif",
            "font.size": 7.0,
            "axes.labelsize": 7.5,
            "axes.titlesize": 7.5,
            "xtick.labelsize": 6.5,
            "ytick.labelsize": 6.5,
            "legend.fontsize": 6.0,
            "axes.edgecolor": _MUTED,
            "axes.labelcolor": _INK,
            "axes.linewidth": 0.6,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.color": "#d9d9d9",
            "grid.linewidth": 0.4,
            "xtick.color": _MUTED,
            "ytick.color": _MUTED,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "lines.linewidth": 1.0,
            "hatch.linewidth": 0.45,
            "legend.frameon": False,
        }
    )


def _ordered(methods: list[str]) -> list[str]:
    known = [method for method in METHOD_ORDER if method in methods]
    extra = sorted(method for method in methods if method not in METHOD_ORDER)
    return known + extra


def _save(figure: plt.Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, format="png")
    plt.close(figure)
    return path


def plot_test_mae_by_horizon(
    rows: list[dict[str, Any]],
    path: Path,
    *,
    policy: str = "exclude",
) -> Path:
    """Grouped bars: common-case test MAE per method per horizon, 95% CI."""
    apply_paper_style()
    frame = pd.DataFrame(rows)
    frame = frame.loc[frame["policy"].eq(policy)]
    horizons = sorted(frame["horizon_days"].unique())
    methods = _ordered(sorted(frame["method"].unique()))
    figure, axes = plt.subplots(figsize=(FIGURE_WIDTH_INCHES, 2.55))
    group_width = 0.84
    bar_width = group_width / len(methods)
    positions = np.arange(len(horizons), dtype="float64")
    for index, method in enumerate(methods):
        offsets = positions - group_width / 2 + bar_width * (index + 0.5)
        heights: list[float] = []
        lower: list[float] = []
        upper: list[float] = []
        for horizon in horizons:
            match = frame.loc[
                frame["method"].eq(method) & frame["horizon_days"].eq(horizon)
            ]
            if match.empty or pd.isna(match["mae"].iloc[0]):
                heights.append(np.nan)
                lower.append(0.0)
                upper.append(0.0)
                continue
            mae = float(match["mae"].iloc[0])
            heights.append(mae)
            lower.append(max(mae - float(match["ci_lower"].iloc[0]), 0.0))
            upper.append(max(float(match["ci_upper"].iloc[0]) - mae, 0.0))
        axes.bar(
            offsets,
            heights,
            width=bar_width * 0.86,
            color=METHOD_COLORS.get(method, "#777777"),
            hatch=METHOD_HATCHES.get(method, ""),
            edgecolor="white",
            linewidth=0.5,
            label=METHOD_LABELS.get(method, method),
            yerr=[lower, upper],
            error_kw={"elinewidth": 0.6, "capsize": 1.1, "capthick": 0.6, "ecolor": _INK},
        )
    axes.set_xticks(positions)
    axes.set_xticklabels([f"{horizon}-day" for horizon in horizons])
    axes.set_xlabel("Forecast horizon")
    axes.set_ylabel("Common-case MAE (AQI)")
    axes.grid(axis="x", visible=False)
    axes.legend(ncol=3, loc="upper left", bbox_to_anchor=(0.0, 1.22), handlelength=1.4,
                columnspacing=1.0, handletextpad=0.4)
    return _save(figure, path)


def plot_dev_vs_test(
    rows: list[dict[str, Any]],
    path: Path,
    *,
    policy: str = "exclude",
    methods: tuple[str, ...] = ("persistence", "regularized_linear", "xgboost"),
) -> Path:
    """Grouped bars: 2019 development vs 2020 locked-test MAE per method."""
    apply_paper_style()
    frame = pd.DataFrame(rows)
    frame = frame.loc[frame["policy"].eq(policy)]
    horizons = sorted(frame["horizon_days"].unique())
    ordered = _ordered([method for method in methods if method in set(frame["method"])])
    figure, axes = plt.subplots(figsize=(FIGURE_WIDTH_INCHES, 2.45))
    stages = ("development_2019", "test_2020")
    group_width = 0.82
    bar_width = group_width / (len(ordered) * len(stages))
    positions = np.arange(len(horizons), dtype="float64")
    slot = 0
    for method in ordered:
        for stage in stages:
            offsets = positions - group_width / 2 + bar_width * (slot + 0.5)
            heights = []
            for horizon in horizons:
                match = frame.loc[
                    frame["method"].eq(method)
                    & frame["horizon_days"].eq(horizon)
                    & frame["stage"].eq(stage)
                ]
                heights.append(
                    float(match["mae"].iloc[0]) if not match.empty else np.nan
                )
            is_test = stage == "test_2020"
            axes.bar(
                offsets,
                heights,
                width=bar_width * 0.88,
                color=METHOD_COLORS.get(method, "#777777") if is_test else "white",
                edgecolor=METHOD_COLORS.get(method, "#777777") if not is_test else "white",
                hatch="" if is_test else "///",
                linewidth=0.6,
                label=f"{METHOD_LABELS.get(method, method)} ({'2020 test' if is_test else '2019 dev'})",
            )
            slot += 1
    axes.set_xticks(positions)
    axes.set_xticklabels([f"{horizon}-day" for horizon in horizons])
    axes.set_xlabel("Forecast horizon")
    axes.set_ylabel("Common-case MAE (AQI)")
    axes.grid(axis="x", visible=False)
    axes.legend(ncol=2, loc="upper left", bbox_to_anchor=(0.0, 1.30), handlelength=1.4,
                columnspacing=0.8, handletextpad=0.4)
    return _save(figure, path)


def plot_lockdown(
    rows: list[dict[str, Any]],
    path: Path,
    *,
    policy: str = "exclude",
    horizon_days: int = 1,
) -> Path:
    """Grouped bars: pre-lockdown vs lockdown common-case MAE per method."""
    apply_paper_style()
    frame = pd.DataFrame(rows)
    frame = frame.loc[frame["policy"].eq(policy) & frame["horizon_days"].eq(horizon_days)]
    methods = _ordered(sorted(frame["method"].unique()))
    windows = ("pre_lockdown", "lockdown")
    window_labels = {"pre_lockdown": "1 Jan - 24 Mar 2020", "lockdown": "25 Mar - 1 Jul 2020"}
    figure, axes = plt.subplots(figsize=(FIGURE_WIDTH_INCHES, 2.45))
    group_width = 0.76
    bar_width = group_width / len(windows)
    positions = np.arange(len(methods), dtype="float64")
    for index, window in enumerate(windows):
        offsets = positions - group_width / 2 + bar_width * (index + 0.5)
        heights = []
        for method in methods:
            match = frame.loc[frame["method"].eq(method) & frame["window"].eq(window)]
            heights.append(float(match["mae"].iloc[0]) if not match.empty else np.nan)
        axes.bar(
            offsets,
            heights,
            width=bar_width * 0.86,
            color=[METHOD_COLORS.get(method, "#777777") for method in methods],
            hatch="" if window == "pre_lockdown" else "///",
            edgecolor="white",
            linewidth=0.5,
            label=window_labels[window],
        )
    axes.set_xticks(positions)
    axes.set_xticklabels(
        [METHOD_LABELS.get(method, method) for method in methods],
        rotation=30,
        ha="right",
    )
    axes.set_ylabel("Common-case MAE (AQI)")
    axes.grid(axis="x", visible=False)
    handles = [
        plt.Rectangle((0, 0), 1, 1, facecolor="#8c8c8c", edgecolor="white", hatch=""),
        plt.Rectangle((0, 0), 1, 1, facecolor="#8c8c8c", edgecolor="white", hatch="///"),
    ]
    axes.legend(
        handles,
        [window_labels["pre_lockdown"], window_labels["lockdown"]],
        ncol=2,
        loc="upper left",
        bbox_to_anchor=(0.0, 1.16),
        handlelength=1.4,
        handletextpad=0.4,
        columnspacing=1.0,
    )
    return _save(figure, path)


def plot_city_timeseries(
    frame: pd.DataFrame,
    path: Path,
    *,
    methods: tuple[str, ...] = ("persistence", "regularized_linear", "xgboost"),
) -> Path:
    """Observed AQI against 1-day forecasts for one city over the test window."""
    apply_paper_style()
    figure, axes = plt.subplots(figsize=(FIGURE_WIDTH_INCHES, 2.3))
    dates = pd.to_datetime(frame["target_date"])
    axes.plot(
        dates,
        frame["target"].astype(float),
        color=_INK,
        linewidth=1.0,
        label="Observed AQI",
        zorder=5,
    )
    for method in _ordered([method for method in methods if method in frame.columns]):
        axes.plot(
            dates,
            frame[method].astype(float),
            color=METHOD_COLORS.get(method, "#777777"),
            linewidth=0.8,
            alpha=0.9,
            label=METHOD_LABELS.get(method, method),
        )
    axes.axvline(
        pd.Timestamp("2020-03-25"),
        color=_MUTED,
        linewidth=0.7,
        linestyle=(0, (3, 2)),
        zorder=1,
    )
    axes.annotate(
        "lockdown",
        xy=(pd.Timestamp("2020-03-26"), axes.get_ylim()[1]),
        xytext=(2, -7),
        textcoords="offset points",
        color=_MUTED,
        fontsize=5.8,
    )
    axes.set_ylabel("AQI")
    axes.set_xlabel("Target date, 2020")
    axes.grid(axis="x", visible=False)
    axes.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    axes.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    for label in axes.get_xticklabels():
        label.set_rotation(30)
        label.set_horizontalalignment("right")
    axes.legend(ncol=2, loc="upper left", bbox_to_anchor=(0.0, 1.26), handlelength=1.6,
                columnspacing=1.0, handletextpad=0.4)
    return _save(figure, path)


__all__ = [
    "FIGURE_DPI",
    "FIGURE_WIDTH_INCHES",
    "METHOD_COLORS",
    "METHOD_LABELS",
    "METHOD_ORDER",
    "apply_paper_style",
    "plot_city_timeseries",
    "plot_dev_vs_test",
    "plot_lockdown",
    "plot_test_mae_by_horizon",
]
