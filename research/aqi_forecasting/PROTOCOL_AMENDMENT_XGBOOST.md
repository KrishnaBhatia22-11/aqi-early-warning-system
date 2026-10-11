# Protocol amendment: XGBoost comparator and locked final-test procedure

**Status:** declared before any final-test prediction or score was produced.
**Authorized by:** Krishna Bhatia.
**Amends:** the frozen protocol used by development run
`20261010T101227Z-50924ef9974e`.

## What this amendment does and does not change

Unchanged: `protocol.py` constants, the seven primary predictors, the AQI lag
offsets, the exact-date sample construction in `forecast_samples.py`, both
target policies, the target-date partitions, the three expanding-window
folds, and every existing baseline implementation (persistence, annual
seasonal naive, weekly seasonal naive, city/month climatology, Ridge). The
saved run `20261010T101227Z-50924ef9974e` is read-only; its `run_record.json`
and `run.log` are not modified or regenerated, and its tables remain the
reference for the pre-amendment development results.

Added:

1. One gradient-boosted-tree comparator (XGBoost), on the same footing as
   Ridge.
2. A declared refit procedure for the one-time locked final test.
3. A declared uncertainty procedure (city-cluster bootstrap).
4. A declared lockdown sub-analysis of the test window.

## 1. The XGBoost comparator

Implementation: `xgboost_model.py`, using `xgboost.XGBRegressor`.

**Predictors.** Exactly `PRIMARY_FEATURE_COLUMNS`: `aqi_lag_origin`,
`aqi_lag_1d`, `aqi_lag_7d`, `target_month_sin`, `target_month_cos`,
`target_weekday_sin`, `target_weekday_cos`. No city identifier, no
pollutant columns, no future values. The schema is asserted by
`validate_feature_schema` on every fit and predict.

**Sample construction.** The frozen `build_forecast_samples` output, with no
model-specific preprocessing.

**Availability rule.** Identical to Ridge: a row is predicted only when
`eligible` is true, that is, when the target and all three exact AQI lags are
present and policy-valid. Rows with any missing or invalid primary feature
are UNAVAILABLE with reason `missing_or_invalid_primary_feature`. XGBoost's
native NaN handling is deliberately **not** used, so XGBoost native coverage
equals Ridge native coverage and the two models are compared on the same
cases.

**Training partition.** Development fits use the 2015-01-01..2018-12-31
train partition only, enforced by the same partition and date guards the
Ridge fit uses.

**Grid** (4 candidates):

| `max_depth` | `n_estimators` |
|---:|---:|
| 3 | 200 |
| 3 | 500 |
| 6 | 200 |
| 6 | 500 |

**Fixed hyperparameters:** `learning_rate=0.05`, `subsample=0.8`,
`colsample_bytree=1.0`, `objective="reg:squarederror"`,
`tree_method="hist"`, `random_state=0`, `n_jobs=1`. The seed is fixed and
recorded; `n_jobs=1` is set so the fit is reproducible.

**Selection rule.** Per target policy and horizon, minimize the equal-weight
mean validation MAE across `fold_2017`, `fold_2018`, and `fold_2019` — the
same folds and the same equal-weight fold mean used for the Ridge alpha.
Exact ties select the simpler configuration: smaller `max_depth` first, then
fewer trees. Selection never touches any target date on or after
2020-01-01; `select_xgboost_config` raises if it is handed one.

**Development reporting.** 2019 development results are reported in the same
format as the saved run: the fold MAE table, common-case MAE/RMSE, and
native coverage. The common-case intersection is recomputed with XGBoost
included, so all methods' 2019 common-case numbers are reported fresh in
this run's tables rather than copied from the saved run.

## 2. Locked final test — procedure, declared before scoring

**Test targets.** 2020-01-01 through 2020-07-01 inclusive, both target
policies (`exclude`, `cap`), all three horizons (1, 3, 7 days). Scored
exactly once.

**Refit.** Ridge (at its selected alpha), XGBoost (at its selected
configuration), and the city/month climatology are refit on **all** training
and development targets, 2015-01-01 through 2019-12-31 inclusive, then used
to predict the test targets. `validate_refit_samples` rejects any refit row
whose partition is not `train` or `validation` or whose target date falls
outside that window, so no test target can reach a fit. Ridge keeps its
`StandardScaler` + `Ridge` pipeline; XGBoost keeps its selected grid point
and fixed hyperparameters; climatology keeps city/month means with the
pooled-month fallback. Hyperparameters are **not** reselected on the
extended window.

**Baselines.** Persistence, annual seasonal naive, and weekly seasonal naive
(horizons 1 and 3 only) use their normal exact-date, origin-available
lookups, unchanged.

**Reported per policy and horizon.** Native coverage per method,
common-case MAE and RMSE for every method, and the common-case count.

**No post-hoc change.** After the test is scored, nothing is tuned, rerun,
or changed. If a defect is found, the run is reported as broken rather than
silently repaired and rescored.

## 3. Uncertainty — city-cluster bootstrap

Cities are the resampling clusters. Each replicate draws all contributing
cities with replacement and recomputes pooled common-case MAE from the
resampled clusters; 2,000 replicates, seed 20200101, 95 percent percentile
interval. Every method uses the identical city draw within a replicate, so
the paired MAE differences (Ridge − persistence) and (XGBoost − persistence)
are computed on the same resample and reported with their own 95 percent
intervals.

## 4. Lockdown sub-analysis

Common-case MAE per method is additionally reported separately for
2020-01-01..2020-03-24 and 2020-03-25..2020-07-01. India's national lockdown
began on 25 March 2020. This split is descriptive: it is computed from the
same single set of test predictions and involves no refitting, no reselection,
and no additional scoring event.

## 5. Outputs

A new run directory under `results/<run_id>/` with `run_record.json` (SHA-256
hashes of the data file, the research source fingerprint, and every artifact
written), `run.log`, `tables/*.csv`, and `figures/*.png`, plus
`RESULTS_SUMMARY.md` listing every reported number with its source file.
