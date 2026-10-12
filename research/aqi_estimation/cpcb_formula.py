"""CPCB National AQI computed from daily pollutant concentrations.

Breakpoints are the CPCB (2014) table, copied from ``src/data/india_aqi.py`` so
this research package stays independent of production code. Units: ug/m3 for
all pollutants except CO (mg/m3), which is the unit used in ``city_day.csv``.

Approximation: the official method uses 8-hour averages for CO and O3. The
dataset holds only daily means, so those two sub-indices are computed from the
daily mean. Above the top breakpoint the sub-index is capped at 500.

Sub-indices are NOT rounded (the production helper rounds); each band starts
where the previous one ends, matching ``india_aqi.sub_index``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# pollutant -> [(BP_lo, BP_hi, I_lo, I_hi)]
BREAKPOINTS: dict[str, list[tuple[float, float, int, int]]] = {
    "PM2.5": [(0, 30, 0, 50), (30, 60, 51, 100), (60, 90, 101, 200),
              (90, 120, 201, 300), (120, 250, 301, 400), (250, 500, 401, 500)],
    "PM10": [(0, 50, 0, 50), (50, 100, 51, 100), (100, 250, 101, 200),
             (250, 350, 201, 300), (350, 430, 301, 400), (430, 600, 401, 500)],
    "NO2": [(0, 40, 0, 50), (40, 80, 51, 100), (80, 180, 101, 200),
            (180, 280, 201, 300), (280, 400, 301, 400), (400, 500, 401, 500)],
    "O3": [(0, 50, 0, 50), (50, 100, 51, 100), (100, 168, 101, 200),
           (168, 208, 201, 300), (208, 748, 301, 400), (748, 1000, 401, 500)],
    "CO": [(0, 1.0, 0, 50), (1.0, 2.0, 51, 100), (2.0, 10, 101, 200),
           (10, 17, 201, 300), (17, 34, 301, 400), (34, 50, 401, 500)],
    "SO2": [(0, 40, 0, 50), (40, 80, 51, 100), (80, 380, 101, 200),
            (380, 800, 201, 300), (800, 1600, 301, 400), (1600, 2000, 401, 500)],
    "NH3": [(0, 200, 0, 50), (200, 400, 51, 100), (400, 800, 101, 200),
            (800, 1200, 201, 300), (1200, 1800, 301, 400), (1800, 2000, 401, 500)],
}
FORMULA_POLLUTANTS = tuple(BREAKPOINTS)  # fixed order; also the tie-break order
PARTICULATES = ("PM2.5", "PM10")
MIN_POLLUTANTS = 3
AQI_CAP = 500.0


def sub_index(pollutant: str, conc) -> np.ndarray:
    """Vectorised concentration -> sub-index; NaN for missing or negative input."""
    c = np.asarray(conc, dtype=float)
    out = np.full(c.shape, np.nan)
    valid = ~np.isnan(c) & (c >= 0)
    table = BREAKPOINTS[pollutant]
    for bp_lo, bp_hi, i_lo, i_hi in table:
        in_band = valid & (c > bp_lo) & (c <= bp_hi)
        out[in_band] = (i_hi - i_lo) / (bp_hi - bp_lo) * (c[in_band] - bp_lo) + i_lo
    out[valid & (c == 0)] = 0.0
    out[valid & (c > table[-1][1])] = AQI_CAP
    return out


def compute_aqi(frame: pd.DataFrame) -> pd.DataFrame:
    """Sub-indices, n_pollutants, computable flag, AQI and dominant pollutant."""
    subs = pd.DataFrame(
        {p: sub_index(p, frame[p].to_numpy()) for p in FORMULA_POLLUTANTS},
        index=frame.index,
    )
    n_poll = subs.notna().sum(axis=1)
    has_particulate = subs[list(PARTICULATES)].notna().any(axis=1)
    computable = (n_poll >= MIN_POLLUTANTS) & has_particulate
    filled = subs.fillna(-1.0).to_numpy()
    aqi = np.where(computable, filled.max(axis=1), np.nan)
    dominant = np.array(FORMULA_POLLUTANTS, dtype=object)[filled.argmax(axis=1)]
    result = subs.add_prefix("sub_")
    result["n_pollutants"] = n_poll
    result["computable"] = computable
    result["formula_aqi"] = aqi
    result["dominant"] = np.where(computable, dominant, None)
    return result
