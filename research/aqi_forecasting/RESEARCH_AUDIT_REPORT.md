# AQI Research Audit Report

**Audit date:** 2026-10-10  
**Scope:** Read-only verification of existing research artifacts, code, claims,
and literature records; one factual manuscript clarification; safe
non-model tests only. No research run was repeated.

## Executive verdict

**Needs corrections before submission; audit package ready for human review.**
The saved development artifact and dataset hashes match the supplied
references, and its reported 2019 common-case metrics match the manuscript
tables after rounding. The 2019 period was used in Ridge alpha selection, so
these numbers are selection-stage evidence, not an independent final
performance estimate. The locked test has not been evaluated.

The research package is currently untracked in Git. Its historical source
fingerprint does not preserve the historical source files, and the recorded
runtime (Python 3.13.3) differs from the repository declaration (Python 3.11).
An immutable archive of the current research source state is provided
separately; it is not the historical run snapshot. Dataset lineage, upstream
rights, historical AQI construction, literature full-text checks, and author
metadata remain unresolved.

## Repository and source inventory

| Item | Observed state |
|---|---|
| Branch / revision | `main`, `b3e5a3b0df921c4aff0e4460674e75eedffda5ad` |
| Tracked working-tree changes | None observed |
| Staged changes | None observed |
| Research files | Untracked under `research/`; preserve them and review before staging |
| Raw dataset | `data/raw/city_day.csv` is tracked; its hash matches the reference |
| Ignored generated files | Research `__pycache__` bytecode is ignored by `.gitignore`; no cleanup performed |
| Source inventory | Research utilities: `baselines.py`, `coverage.py`, `data_audit.py`, `date_utils.py`, `forecast_samples.py`, `leakage_checks.py`, `manifest.py`, `protocol.py`, `run_development.py`, `target_policies.py`, and `temporal_splits.py`; package initializers are also present |
| Tests | `test_audit_manifest.py`, `test_baselines.py`, `test_forecast_samples.py`, `test_run_record.py`, `test_splits_leakage.py`, `test_target_policies.py` |
| Configuration | `runtime.txt` declares Python 3.11; research dependency pins are in `requirements-research-py313.txt` |
| Run outputs | Two unique run directories are present. The older run predates the corrected sample-construction cutoff; the later run is the referenced development artifact. Both are retained. |

The earlier [MANUSCRIPT_DRAFT.md](MANUSCRIPT_DRAFT.md) explicitly retains
the pre-review version and points to [MANUSCRIPT_DRAFT_v2.md](MANUSCRIPT_DRAFT_v2.md)
as the reviewed draft. The same relationship is documented by
[LITERATURE_MATRIX.md](LITERATURE_MATRIX.md) and
[LITERATURE_MATRIX_v2.md](LITERATURE_MATRIX_v2.md). The README points readers
to the v2 files. The filenames are not ambiguous when these notes are
followed, but submission should use only the reviewed v2 manuscript and
matrix.

`runtime.txt`, the research README, and the run record state the Python
version discrepancy. The README's full runner command fits/selects Ridge;
there is no separate checked-in safe-test script. Use only the exact safe
test command reported below when validating the handoff.

## Saved run verification

Run directory:
`results/20261010T101227Z-50924ef9974e/`.

| Check | Result | Evidence |
|---|---|---|
| `run_record.json` expected SHA-256 | **PASS** — `a7eac260052a596e1b03848e72a56269e2ce695ead9f6f4326a8d0d6287186c5` | Read-only `Get-FileHash` |
| `run.log` expected SHA-256 | **PASS** — `f3b94b28ed5e29e75df7bf53d64fbeff75f06582be55c8b5461663000ea00d935` | Read-only `Get-FileHash` |
| Run/log identifiers and timing | **PASS** — both identify run `20261010T101227Z-50924ef9974e`; the log header timestamps and command match the structured record | JSON and log header |
| Dataset identity | **PASS** — 2,574,056 bytes; SHA-256 `0d84b21c3e4878bbad8df362f2ab05f61ad959538dddf5918e714077ed3c1847`; 29,531 rows, 16 columns, 26 cities, 2015-01-01–2020-07-01 | Current file hash and run `data` metadata |
| Protocol and selection | **PASS** — horizons 1/3/7; `exclude`/`cap`; seven primary features; training 2015–2018; 2019 selection; folds 2017/2018/2019; alpha 0.1 selected for all six policy/horizon combinations | Run `protocol` and six run entries; [`protocol.py`](protocol.py) |
| Metrics in manuscript | **PASS, rounded comparison** — all six 2019 common-case MAE/RMSE rows, case counts, and native coverage denominators agree with the saved record to the manuscript's displayed precision | `validation.common_case_metrics`, `common_case_count`, `methods`; manuscript Results tables |
| Final-test flags | **PASS for this record** — final-test outcome use, prediction generation, and scoring flags are all false; run entries have only development/validation summaries | Record status fields; no final-test score data were inspected |
| Run stage | **PASS** — `baseline_development_and_2019_selection`; model fitting occurred for this historical run | Record `stage`, `model_fitting_performed` |
| Historical source identity | **PASS as a recorded identity, not a recoverable source tree** — revision `b3e5a3b0df921c4aff0e4460674e75eedffda5ad`; 24 research source files; fingerprint `6435c3f1528530fba9dad3cab33a282ebbf0f749a72b8c60664a384f9d594312`; code was untracked at execution | Record `code` metadata |
| Source identity at archive time | **PASS** — 30 source files; fingerprint `c9e05ab0970e008bb44bc68eb6d430dbdbd860f7b84cb30be6d765aeee9ceaaf` | `fingerprint_research_sources()` and snapshot manifest |
| Post-audit tree | **PASS as inventoried** — 33 source files; differs from the archive due to this audit's three report files and the manuscript clarification/version update. Python source and test files were not changed in this audit. No self-referential aggregate fingerprint is claimed for the final report state. | Git status, final file inventory, and `fingerprint_research_sources()` algorithm |
| Reproduction of historical run | **NOT ESTABLISHED** — current source differs; no run was repeated | Historical/current fingerprint and untracked state |

The log contains the same run identity/timing/configuration context and the
structured record output. The saved run is not described as reproducible
from the current source merely because the record contains a fingerprint.

### Current source snapshot

A source-only archive was created outside the repository, preserving
repository-relative paths. The archive and manifest include 30 source,
test, and documentation files; the manifest records each included file's
SHA-256 and size. Results directories, saved run records/logs, bytecode
caches, raw data, production code, and files outside `research/` were
excluded. The archive SHA-256 is
`e75d601480d75479fb4710bda9f60698a506489c262794464fbbc22c6161eeaa`.
Archive entry names, count, every entry's SHA-256, and archive SHA-256 match
the manifest.

Archive:
`C:\Users\krish\.copilot\session-state\dea66007-853d-48b3-a0a1-7e1828d66063\files\aqi-research-snapshot\aqi-research-source-20261010T104025Z.zip`

Manifest:
`C:\Users\krish\.copilot\session-state\dea66007-853d-48b3-a0a1-7e1828d66063\files\aqi-research-snapshot\aqi-research-source-20261010T104025Z.manifest.json`

This captures the current research files at archive time, not the historical
24-file execution snapshot. It was created before the present audit reports
and the factual manuscript clarification below.

## Protocol and implementation audit

- [`protocol.py`](protocol.py) defines the approved horizons, target
  policies, feature names, and temporal boundaries.
- [`forecast_samples.py`](forecast_samples.py) constructs exact city/date
  targets and lag joins, adds deterministic target-date encodings, and does
  not substitute nearby dates for missing observations.
- [`temporal_splits.py`](temporal_splits.py) assigns by target date and
  defines fixed expanding development folds.
- [`target_policies.py`](target_policies.py) preserves raw values and
  distinguishes `exclude` from `cap`; neither policy is asserted to recover
  the source's historical AQI process.
- [`baselines.py`](baselines.py) implements persistence, annual exact-date
  naive, training-only city/month climatology with pooled-month fallback,
  Ridge, and weekly naive for horizons 1 and 3. At horizon 7 weekly naive is
  identical to persistence. It computes native coverage and shared-case
  metrics separately.
- [`run_development.py`](run_development.py) audits the full CSV, parses
  dates, restricts sample construction through 2019-12-31, rejects other
  partitions, and uses an exclusive run directory when persisting a run.
  Current code passes the restricted history to baseline evaluation.
- The saved run predates that final history-handoff hardening. Its baseline
  lookup code filtered records by origin; the saved results were not rerun
  after the code change. The full CSV is still read for audit/date parsing,
  so “the test rows were never read” would be false even though no final-test
  outcomes were scored.

## Test and safety evidence

The new handoff regression test in `test_run_record.py` uses a synthetic
2019-12-31 and 2020-01-01 pair. It mocks the audit, sample builder,
partition assignment, coverage, manifest, and baseline runner, then asserts
that all six policy/horizon calls receive dates no later than 2019-12-31.
This cannot fit an estimator.

The safe suite ran only these modules:

```powershell
.\venv\Scripts\python.exe -m unittest -v research.aqi_forecasting.tests.test_run_record research.aqi_forecasting.tests.test_target_policies research.aqi_forecasting.tests.test_forecast_samples research.aqi_forecasting.tests.test_splits_leakage research.aqi_forecasting.tests.test_audit_manifest
```

**Outcome:** **35 tests passed; 0 failed** in 1.542 seconds.
`test_baselines.py` was deliberately not run because it performs estimator
fitting and model-selection checks. No broad test discovery or development
runner was executed.

All 35 executed tests passed:

- `test_run_record`: `test_default_run_command_uses_importable_module_path`,
  `test_development_manifest_records_protocol_outputs_and_safe_status`,
  `test_development_runner_hands_only_pre_2020_history_to_baselines`,
  `test_manifest_does_not_transfer_kaggle_provenance_to_other_inputs`,
  `test_persistence_rejects_path_like_run_identifiers`,
  `test_record_and_log_are_written_once_and_never_overwritten`,
  `test_source_fingerprint_is_deterministic_and_excludes_run_outputs`.
- `test_target_policies`: `test_policy_flags_non_numeric_and_infinite_values`,
  `test_target_policy_boundaries_and_raw_preservation`,
  `test_unknown_policy_and_missing_column_are_explicit_errors`.
- `test_forecast_samples`: `test_city_values_never_cross_join`,
  `test_duplicate_city_date_and_invalid_date_are_rejected`,
  `test_exact_target_origin_and_lags`,
  `test_missing_calendar_date_is_not_replaced_by_previous_row`,
  `test_missing_target_and_above_500_policy_are_auditable`,
  `test_mixed_date_formats_parse_deterministically_and_timezone_is_rejected`,
  `test_target_date_calendar_features_are_deterministic`,
  `test_timestamp_validator_checks_every_lag_and_does_not_mutate`.
- `test_splits_leakage`: `test_approved_target_date_partitions_and_boundary_origin`,
  `test_city_folds_are_deterministic_and_disjoint`,
  `test_expanding_folds_use_only_targets_through_training_cutoff`,
  `test_held_out_coverage_gate_uses_eligible_test_counts_only`,
  `test_partition_invariant_detects_cross_city_mismatch`,
  `test_primary_schema_rejects_pollutant_or_city_identifier`,
  `test_split_fold_rejects_overlapping_or_reversed_ranges`,
  `test_split_fold_uses_target_dates_and_keeps_sample_ids_disjoint`.
- `test_audit_manifest`: `test_audit_counts_disjoint_aqi_categories_overall_and_by_partition`,
  `test_audit_fails_clearly_on_empty_and_malformed_csv`,
  `test_audit_hash_and_parse_use_one_byte_snapshot`,
  `test_audit_normalizes_daily_duplicates_and_reports_invalid_dates`,
  `test_common_case_frames_reject_duplicate_ids_and_horizon_mismatch`,
  `test_coverage_common_cases_and_manifest_are_result_honest`,
  `test_coverage_summary_names_every_missing_required_column`,
  `test_manifest_revision_seed_and_discrepancy_statuses_are_explicit`,
  `test_raw_audit_reports_file_identity_and_panel_gaps`.

Deliberately not run: every test in `test_baselines.py`, including tests
that fit Ridge or execute alpha selection. No tests failed.
Some safe unit fixtures use synthetic 2020 dates or a synthetic `test`
partition to check boundary assignment and invariants. They did not load the
raw dataset's final-test outcomes or produce model predictions/scores for
that period.

## Scientific claim risks and blockers

1. The 2019 scores participated in alpha selection; they are not independent
   test estimates. Do not claim superiority or generalization based on them.
2. Temporal splits retain the observed city labels across years. The results
   do not establish held-out-city or station-level transfer.
3. The existing [DATA_PROVENANCE.md](DATA_PROVENANCE.md) reports 543 AQI
   values above 500 (501–2049). This audit did not re-count raw CSV rows; the
   source lineage, applicable upstream rights, historical AQI calculation,
   aggregation, and station coverage remain unresolved. The Kaggle CC0 label
   is metadata for that hosted record, not proof of upstream CPCB licensing
   authority.
4. The production CPCB-labelled calculator does not establish how the
   historical CSV's `AQI` field was calculated.
5. The production deterministic 24-hour forecast profile and alert thresholds
   have not been evaluated as future AQI forecasts or operational warnings.
6. No statistical uncertainty/paired inference, warning-event detection,
   false-alarm burden, health outcomes, or operational effectiveness were
   evaluated.
7. The full test-period rows remain in the file and were loaded for audit and
   date parsing. The current baseline handoff is structurally restricted to
   pre-2020 history, but the saved run predates this hardening.
8. Python 3.11 is declared; the saved run used Python 3.13.3. Compatibility
   with Python 3.11 is unverified. Do not silently change the environment.
9. The current source archive does not reconstruct the historical run's
   source tree. The manuscript and literature matrix also exist as retained
   original and reviewed v2 files; submit the v2 pair only.

## Literature and external-evidence status

The literature matrix is explicitly a focused, non-systematic review.
Reference [3]'s DOI/Crossref metadata and publisher abstract/page were
checked, but full text and detailed design/results were not reviewed.
Reference [5]'s suspected abstract MSE/RMSE inconsistency remains unresolved;
the full text/table was inaccessible in the previous source check. No
corrected values should be quoted. Other references' metadata and bounded
abstract-level claims are summarized in
[LITERATURE_MATRIX_v2.md](LITERATURE_MATRIX_v2.md); that matrix should not
be read as independent full-text verification for every cited study.

| Ref. | Bibliographic / source check recorded | Full-text and study-design status | Metric / comparison status |
|---|---|---|---|
| [1] | DOI/Crossref metadata and PubMed-indexed abstract recorded as checked | Abstract-level; exact forecast lead, data dates, and split not verified | No numerical metric verified from full text |
| [2] | DOI/Crossref metadata and abstract recorded as checked | Abstract-level; lead, source lineage, split, and unseen-city design unknown | Qualitative abstract wording only; numerical comparisons not verified |
| [3] | DOI/Crossref metadata and publisher article page/abstract checked; Crossref's first-author given-name field is absent, so “Gayatri” is retained as returned | Full article not inspected; exact lead, input timing, and split unknown | No detailed scores verified |
| [4] | DOI/Crossref metadata and PubMed-indexed abstract recorded as checked | Abstract-level; data source, exact lead, input timing, and split unknown | Abstract reports model scores; they are not independently checked against full-text tables |
| [5] | DOI/Crossref metadata recorded as checked; publisher full-text/PDF was unavailable in the earlier access attempt | Full text/table not inspected; input timing and split unknown | Suspected abstract ANN/RF MSE/RMSE inconsistency unresolved; do not infer corrected values |
| [6] | DOI/Crossref record and abstract recorded as checked | Abstract-level; China/U.S. graph setting is adjacent context, not evidence of held-out-city generalization here | No independently reproduced result |
| [7] | DOI/Crossref bibliographic record checked | Full text/results not reviewed for this audit | No detailed recommendation attributed |
| [8] | DOI/Crossref metadata and abstract recorded as checked | Abstract-level structured-data validation context | No AQI performance claim |
| [9] | DOI/Crossref metadata/title recorded as checked | Full text not reviewed for detailed conclusions | No detailed protocol recommendation attributed |
| [10] | Accessible OTexts 3rd-edition chapter inspected | Chapter-level description of rolling-origin evaluation | Methodological support only, not AQI performance evidence |
| [11] | `DATA_PROVENANCE.md` records prior inspection of the official CPCB-hosted report; in this audit the shared PDF page returned no readable text and the local PDF tab reported access forbidden | Existing provenance note reports primary-methodology content; not independently re-read in this audit; author/date metadata not established | Supports the general CPCB method only as documented previously, not historical CSV generation |
| [12] | Kaggle dataset record/version metadata and prior exact byte match to v12 recorded | Hosted data artifact and attribution/license label; upstream chain/authority unresolved | No scientific AQI metric |

Priority evidence / decisions:

| Priority | Outstanding item | Risk |
|---|---|---|
| 1 | CPCB/upstream archive matching this file, extraction/transformation lineage, and applicable rights | Critical legal and outcome-validity risk |
| 2 | Historical handling of AQI >500, daily aggregation, station coverage, and missingness semantics | Critical scientific interpretation risk |
| 3 | Full text/reliable tables for references [3] and [5], especially [5]'s metric reconciliation; full-text methods for other AQI studies | High citation/comparability risk |
| 4 | Author affiliations, emails, titles, ORCIDs, and approved contribution statements | High submission/authorship risk |
| 5 | Supported runtime decision and Python 3.11 compatibility validation in an isolated environment | High reproducibility risk; no migration is authorized here |
| 6 | Human decision on baseline-only scope versus a single optional nonlinear extension, then separate approval for any fitting or locked-test stage | High protocol/governance risk |

No missing author details are inferred. Planned order remains Poonam Tanwar,
Krishna Bhatia, Prateek Singh, and Snehaal Mukherjee.

### Production/research separation observed in code

The manuscript's distinction is supported by the inspected implementation:
[`src/models/train.py`](../../src/models/train.py) uses contemporaneous
pollutant/month/year/season inputs, a random `train_test_split`, and
Random Forest/XGBoost training; it is not the research direct-horizon
comparison. [`api/routes/forecast.py`](../../api/routes/forecast.py)
constructs a 24-hour formula-based profile from diurnal/month/day-of-week
multipliers and seeded noise, using either a supplied base value or a
seasonal estimate. [`api/scheduler.py`](../../api/scheduler.py) checks a
recent reading against a subscription threshold and suppresses repeat alerts
within four hours. These code paths do not establish future-forecast
accuracy, event lead time, detection sensitivity, or false-alarm performance.
[`src/data/india_aqi.py`](../../src/data/india_aqi.py) contains current
pollutant breakpoints and a sub-index cap at 500; it does not show that this
function generated the historical CSV `AQI` column.

## Files changed in this audit

| File | Why / what changed | Change type and evidence | Human approval |
|---|---|---|---|
| `MANUSCRIPT_DRAFT_v2.md` | Clarifies that the saved run used the full-history handoff, while current code has a tested pre-2020 handoff; clarifies that the full CSV was still loaded for audit/date parsing | Factual clarification based on `run_development.py`, the mocked regression test, and saved run's recorded time/source identity | Review required before submission |
| `RESEARCH_AUDIT_REPORT.md` | Adds this inventory, saved-run/data integrity checks, safety evidence, and ranked blockers | New audit record based on inspected files, hashes, run JSON/log, source fingerprint, and executed test command | Review required |
| `CLAIM_EVIDENCE_MATRIX.md` | Maps manuscript claims to evidence and risk | New evidence table based on manuscript, protocol, source files, run artifact, and provenance record | Review required |
| `EXPERIMENT_DECISION_MEMO.md` | Compares baseline-only and one optional nonlinear scope without implementation or fitting | New decision memo; computational fit count is derived from the proposed grid, not measured elapsed time | Author approval required before scope/model work |

The original manuscript and literature files, production application,
dataset, existing run artifacts, and Python environment were not modified.
Nothing was staged, committed, or pushed.
