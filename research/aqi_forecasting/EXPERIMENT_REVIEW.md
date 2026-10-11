# Corrected baseline run: independent review

**Review date:** 2026-10-10  
**Reviewed run:** `20261010T101227Z-50924ef9974e`  
**Scope:** The development and 2019 selection portions only. No final-test
prediction, comparison, or score was generated, viewed, or evaluated during
this review.

## Decision summary

The corrected run's reported development/2019 metrics are consistent with
the inspected sample builder, baseline implementations, selection code, and
saved record. The exact target policy and temporal partitions are encoded in
the research protocol. Shared-case metrics use a common city/date/horizon
intersection; native coverage denominators are valid target labels. The
annual seasonal-naïve baseline checks both a history cutoff and a
sample-specific source-date/origin condition.

One boundary claim needs precise wording: **the test-period observations were
not used in selection, prediction generation, metrics, or scoring, but test
rows were physically loaded from the full CSV for checksum/data audit and
date parsing.** The saved run predates the structural handoff correction:
at that time, the full history frame was passed to the baseline entry point,
whose lookup helper truncated by maximum validation origin before
target-policy transformation. The current runner now passes the
2019-12-31-limited history to the baseline entry point. A mocked runner test
verified this handoff for all six policy/horizon calls without fitting a
model. This change does not retroactively rerun or alter the saved artifact.

## Verification checklist

| Check | Finding | Evidence |
|---|---|---|
| Corrected sample-construction cutoff | **Verified.** `run_development()` parses dates, creates `development_history` with `target_date <= VALIDATION_END`, builds samples only from that frame, rejects unexpected partitions, and checks the maximum target date is no later than validation end. | [`run_development.py`](run_development.py), `run_development`; protocol `VALIDATION_END`. The saved record's targets are train/validation only. |
| Approved dates, horizons, and policies | **Verified.** The constants are horizons 1/3/7; policies `exclude`/`cap`; target-date train 2015–2018 and validation 2019; locked test starts 2020-01-01 and ends 2020-07-01. `assign_partition()` uses the target-date column. | [`protocol.py`](protocol.py); [`temporal_splits.py`](temporal_splits.py), `assign_partition`, `expanding_window_folds`, `split_fold`; run record `protocol`. |
| Forecast origins and target-date assignment | **Verified for the implemented direct-horizon samples.** Targets are paired to calendar origin `target_date - horizon`, and the sample builder uses exact city/date joins for lag values; temporal partitioning is by target date. | [`forecast_samples.py`](forecast_samples.py), `build_forecast_samples`; [`temporal_splits.py`](temporal_splits.py), `assign_partition`; tests `test_exact_target_origin_and_lags`, `test_approved_target_date_partitions_and_boundary_origin`, and `test_split_fold_uses_target_dates_and_keeps_sample_ids_disjoint`. |
| Annual seasonal-naïve availability | **Verified.** `_prepare_history()` truncates its lookup to the latest forecast origin in the supplied frame before applying the policy. For each sample, `annual_seasonal_naive_predictions()` also rejects a source date later than that sample's own origin. Prior-year dates are exact; February 29 maps to February 28. | [`baselines.py`](baselines.py), `_prepare_history`, `_previous_year_date`, `annual_seasonal_naive_predictions`; test `test_annual_naive_ignores_history_after_latest_forecast_origin`, plus exact-date/leap-day and missing-history tests. |
| Final-test outcome use | **No scoring or prediction use found; physical input caveat confirmed.** The saved artifact has all three final-test status flags false. `select_ridge_alpha()` rejects any target date at/after 2020-01-01; sample generation ends at 2019-12-31; prediction evaluation is called only for `partition="validation"`. The full file is still read for audit/date parsing. The current runner passes only `development_history` ending 2019-12-31 into `run_policy_horizon_development()`; the saved run itself predates this hardening and is unchanged. | [`run_record.json`](results/20261010T101227Z-50924ef9974e/run_record.json), top-level status and each run's validation output; [`run.log`](results/20261010T101227Z-50924ef9974e/run.log); [`run_development.py`](run_development.py), `run_development`; [`baselines.py`](baselines.py), `select_ridge_alpha`, `run_policy_horizon_development`, `_prepare_history`; `test_development_runner_hands_only_pre_2020_history_to_baselines`. |
| Common-case metrics | **Verified for this run.** All methods receive the same validation sample frame; the evaluator intersects case IDs with valid target and available prediction for every method, then reports each method on that identical set. `common_case_count` matches each per-method paired metric count in the record. | [`baselines.py`](baselines.py), `evaluate_predictions`, `_metric_report`; saved run's `validation.common_case_count` and `validation.common_case_metrics`; test `test_native_coverage_missing_predictions_and_common_case_metrics`. |
| Native coverage and metric denominators | **Verified.** For each method, denominator is valid targets in the requested partition; numerator is valid-target cases with `prediction_available`. MAE/RMSE use that method's valid predicted pairs. R² is null for fewer than two rows or constant targets. | [`baselines.py`](baselines.py), `evaluate_predictions`, `_metric_values`; `validation.methods[*].valid_target_cases`, `predicted_valid_target_cases`, and `coverage`; test `test_native_coverage_missing_predictions_and_common_case_metrics`. |
| Target-policy and feature behavior | **Verified.** Both policy-specific sample sets and outcomes are recorded separately. Ridge consumes the approved seven features, fits `StandardScaler` inside a train-fitted pipeline, and uses eligible valid training rows only. | [`target_policies.py`](target_policies.py); [`protocol.py`](protocol.py), `PRIMARY_FEATURE_COLUMNS`; [`baselines.py`](baselines.py), `fit_ridge_model`; tests in `test_target_policies.py` and the non-model split/schema suite. |
| Alpha selection | **Verified.** Candidates are 0.1, 1.0, and 10.0. Equal-weight mean MAE over expanding folds 2017, 2018, and 2019 is minimized; ties choose the larger alpha. The fold training windows end before their validation windows. Alpha 0.1 was selected for all six policy/horizon configurations. Since 2019 is included in selection, 2019 results are selection-stage, not independent validation. | [`baselines.py`](baselines.py), `select_ridge_alpha`, `fit_ridge_model`; [`temporal_splits.py`](temporal_splits.py), `expanding_window_folds`, `split_fold`; run record `protocol.ridge_selection_rule`, each run's `ridge_selection`; test `test_ridge_selection_uses_disjoint_fixed_folds_and_rejects_test_dates`. |
| Data identity and run identity | **Verified for the saved record.** Artifact records local file path, 2,574,056 bytes, SHA-256, 29,531 rows, 16 columns, 26 cities, date range, Git revision, source fingerprint (SHA-256 `6435c3f1528530fba9dad3cab33a282ebbf0f749a72b8c60664a384f9d594312`, 24 files), command, timestamps, environment, and protocol. The current raw-file SHA-256 independently matches the record. | [`run_record.json`](results/20261010T101227Z-50924ef9974e/run_record.json); [`run.log`](results/20261010T101227Z-50924ef9974e/run.log); [`manifest.py`](manifest.py), `fingerprint_research_sources`, `collect_code_identity`; current `data/raw/city_day.csv` checksum verified read-only. |

## Findings and corrections

### Confirmed limitation: test rows are loaded, though not used for forecasting scores

The saved run is score-isolated by cutoff and partition in the inspected
execution path. However, the literal statement “final-test data were never
read” would be inaccurate. `audit_raw_dataset()` reads the CSV bytes to
compute file identity and inspect the whole data range; `run_development()`
then calls `pd.read_csv()` for all dates. In the saved run, sample
construction used the validation-limited subset, but the full history frame
was handed to `run_policy_horizon_development()`. Annual/weekly functions
truncated lookup history at the latest supplied origin before policy
application; alpha selection rejected test target dates. No evidence
indicates a final-test outcome affected the saved alpha, predictions, or
reported validation metrics.

**Handoff correction implemented; saved run retained.** `run_development()`
continues to audit and load the full CSV, then constructs
`development_history` through `VALIDATION_END`. It now passes that limited
frame to the baseline runner as well as using it for sample construction.
`test_development_runner_hands_only_pre_2020_history_to_baselines` supplies a
synthetic history containing a 2020 row and verifies that all six baseline
calls receive only dates through 2019-12-31. The baseline function is mocked,
so the test fits no estimator and generates no predictions or scores.
Separating raw-byte audit from full-file parsing could further reduce data
exposure but is not required for the corrected baseline handoff. The saved
run and its log were not changed or rerun.

### Reproducibility boundary

The run-time source fingerprint and Git revision are preserved in the
artifact, but the research tree was untracked and the manuscript/literature
files have since changed. The stored fingerprint identifies the snapshot at
execution, not the current tree; a Git commit or archived source snapshot
would be needed to make that source state recoverable. No staging or commit
was performed.

### Test evidence

The previously reported 34-test run intentionally excludes
`test_baselines.py`, which fits/selects forecasting estimators. It therefore
provides evidence for sample construction, policy, split, audit, and run
record invariants, but is not a full rerun of the baseline prediction tests.
For the current handoff correction, `python -m unittest -v
research.aqi_forecasting.tests.test_run_record` passed all 7 tests, including
the new mocked history-boundary regression test; no estimator was fitted.
The baseline-specific unit tests do cover persistence alignment, annual
availability and leap-day behavior, training-only climatology, Ridge
training-only fit, coverage/common cases, and seven-day weekly/persistence
equality; those tests were not rerun for this correction.

### Literature verification alerts

Reference [3]'s bibliographic metadata has now been checked against
Crossref, and its publisher abstract/page was accessible. The full text was
not reviewed, so its detailed methods, split, and results remain
abstract-level/unverified. Reference [5]'s full text and tables remain
unavailable: the Springer PDF endpoint returned HTTP 406, Unpaywall reports
closed access with no repository copy, and the PubMed-indexed endpoint
returned HTTP 403. The previously noted MSE/RMSE discrepancy therefore
remains unresolved; no corrected values are asserted. Multiple AQI studies
were reviewed at abstract level only; no novelty claim is justified from
this search.
