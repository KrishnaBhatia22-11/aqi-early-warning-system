# Prioritized remaining work for a defensible paper

**Status as of 2026-10-10:** No tree model was trained and no final-test
prediction or score was generated during this review. The saved 2019 results
are model-selection results.

## Decision

One nonlinear tree-based comparator would add useful evidence beyond
persistence, seasonal-naïve, climatology, and Ridge: it would test whether
the seven approved AQI/calendar features contain nonlinear interactions that
the linear model cannot express. The smallest reasonable addition is one
scikit-learn `HistGradientBoostingRegressor` family. A second family is not
currently justified: it would add a larger selection burden without a
distinct research question, and the production Random Forest/XGBoost
experiments are not valid direct-horizon comparators because they predict
same-time AQI from contemporaneous pollutant features under a random split.

This tree experiment is **recommended but not required** if the paper is
explicitly scoped as a comparison of the already implemented baselines. It
becomes necessary only if the authors choose to make a claim about nonlinear
tree-based forecasting or broad ML comparisons.

## P0 — Freeze the protocol and source snapshot

Before any new experiment:

1. Keep run `20261010T101227Z-50924ef9974e` and its `run_record.json`/`run.log`
   unchanged. It is the verified development artifact; the older run is
   preserved but predates the validation-end sample cutoff.
2. The current runner now retains the full-file checksum/metadata audit and
   passes only history through 2019-12-31 to its baseline entry point. The
   mocked regression test verifies this handoff; the saved run predates the
   code hardening and remains unchanged. Do not describe the saved artifact as
   having been rerun under the corrected handoff.
3. Capture the exact research source tree (including currently untracked
   files) in an immutable, versioned Git revision or archived source bundle
   before the next model run. The current run's fingerprint is useful
   metadata, but the run-time research snapshot is not recoverable from the
   Git revision alone.
4. Pre-register the decision rule, candidate settings, metrics, coverage
   denominator, common-case definition, and stopping rules before fitting
   another model.

**Gate:** No code change, run, model fit, or final-test access is authorized
by this plan alone.

## P1 — Resolve or bound dataset provenance

Before submission, seek:

1. The upstream CPCB archive or source snapshot matching Kaggle version 12,
   plus retrieval/aggregation lineage for `city_day.csv`.
2. Applicable upstream rights and evidence that the Kaggle CC0 label is
   authorized for the underlying data.
3. The historical AQI calculation, daily aggregation and treatment of values
   501–2049.
4. Evidence about station composition/coverage and missing-value semantics
   behind each city-day record.

If these cannot be resolved, document the uncertainty prominently and
constrain the scientific conclusions to the hosted artifact and the
predeclared `exclude`/`cap` sensitivity analyses. Do not describe either
policy as the true AQI.

## P1 — Complete reference verification

1. Retrieve full texts and supplements for the AQI studies in
   [`LITERATURE_MATRIX_v2.md`](LITERATURE_MATRIX_v2.md).
2. Bibliographic metadata for the 2024 *Journal of Biofuels* reference
   (matrix ref. [3]) has been rechecked against Crossref; its accessible
   publisher abstract is not a substitute for full-text methods/results
   verification.
3. Obtain full text/tables to reconcile the abstract metric pairs for Pande et al. (2024,
   *Environmental Monitoring and Assessment*, matrix ref. [5]) against the
   paper's tables. Springer PDF access returned HTTP 406 and Unpaywall lists
   no repository copy; until accessible, keep the discrepancy explicitly
   unresolved and do not quote corrected values.
4. For each study, record target definition, exact horizon, input timestamps,
   dataset source, temporal and city splits, baseline set, and metric
   denominator before comparing results.
5. Perform a reproducible literature search before claiming a novelty or
   literature gap. Current search is focused and does not establish either.

## P2 — Recommended minimal nonlinear experiment (requires separate approval)

### Model

One direct-horizon `HistGradientBoostingRegressor` per target policy and
horizon, using **exactly** the same seven primary features as Ridge:
`aqi_lag_origin`, `aqi_lag_1d`, `aqi_lag_7d`,
`target_month_sin`, `target_month_cos`, `target_weekday_sin`, and
`target_weekday_cos`. Do not include city ID, pollutant columns, future
measurements, or other features in this experiment.

### Compact, predeclared candidate set

Fix `learning_rate=0.05`, `min_samples_leaf=20`,
`l2_regularization=1.0`, `early_stopping=False`, and `random_state=0`; select
only from:

| Candidate | `max_iter` | `max_leaf_nodes` |
|---|---:|---:|
| A | 100 | 7 |
| B | 100 | 15 |
| C | 250 | 7 |
| D | 250 | 15 |

Use the same eligible training rows as Ridge for each policy/horizon and
training-only fitting. Fit on the expanding-window fold's training partition;
score only that fold's validation partition. Select by equal-weight mean
fold MAE over 2017, 2018, and 2019; exact ties choose the simpler candidate
(fewer leaf nodes, then fewer boosting iterations). Freeze the selected
candidate, fit on 2015–2018, and report 2019 only as development/selection
evaluation. Since 2019 contributes to selection, do not describe its scores
as independent validation.

### Required outputs and controls

- Unit tests for seven-feature schema, policy/horizon identity, train-only
  fitting, disjoint target-date folds, unavailable feature handling, and
  deterministic selection/tie behavior.
- Per policy and horizon: eligible training cases, fold counts and MAEs,
  selected settings, 2019 native coverage and exclusion reasons, and
  common-case MAE/RMSE against every approved baseline.
- Keep both policy results separate. Do not impute missing predictions.
- Use no final-test target or score for feature, model, or hyperparameter
  decisions.
- Do not interpret this as city-wise generalization; all cities remain
  represented across temporal partitions.
- Do not claim superiority from 2019 selection metrics.

**Computational cost:** Four candidates × three expanding folds × six
policy/horizon configurations (72 small tabular fits), plus six final
2015–2018 development fits. The design reuses the existing split and
evaluation machinery and requires no new dependency.

## P3 — Separate final-test stage (requires explicit approval)

After the source snapshot is frozen, provenance is resolved or bounded, and
all method choices are fixed:

1. Reconfirm test-isolation safeguards. The current development runner has a
   tested pre-2020 history handoff, while the saved development artifact
   predates that correction and remains unchanged.
2. Confirm no test predictions or metrics exist in prior outputs.
3. Run the prespecified models once for targets 2020-01-01 through
   2020-07-01 inclusive.
4. Report each policy and horizon separately, including native valid-target
   coverage, missing-prediction reasons, common-case counts, MAE, RMSE, and
   defined/undefined R². Do not tune after viewing results.
5. Keep test results distinct from 2019 model-selection results and avoid
   unsupported claims of superiority.

The final test still evaluates temporal performance on cities seen in
training. It does not evaluate warning-event detection, lead-time utility,
false-alarm burden, causal impact, or unseen-city transfer.

## P4 — Environment and manuscript completion

- The recorded experiment used Python 3.13.3 and pinned research dependencies;
  the repository declares Python 3.11. Either verify the research package in
  Python 3.11 or explicitly define Python 3.13 as the supported research
  runtime. Do not install or upgrade a global environment just to resolve
  this documentation discrepancy.
- After any authorized new experiments, update the abstract and conclusion
  only from the saved artifacts. Complete affiliation/contact metadata with
  author confirmation; do not infer these details.
- Keep the distinction between the production same-time AQI estimator,
  production heuristic/synthetic alert features, and research direct-horizon
  forecasts explicit in every submission version.

## Optional extensions (not required for the current paper)

- City-held-out evaluation, only if the paper asks a zero-shot transfer
  question and a prespecified city-holdout split has adequate eligible data.
- Probabilistic intervals, uncertainty calibration, external meteorology, or
  event-based warning assessment, each as a separately designed study.
- A second tree family only if a distinct scientific question justifies the
  added selection burden. Do not add it merely to increase model count.
