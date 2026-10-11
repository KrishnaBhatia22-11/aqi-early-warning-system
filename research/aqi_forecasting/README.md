# AQI daily forecasting research utilities

The reviewed manuscript and literature matrix are versioned in
[MANUSCRIPT_DRAFT_v2.md](MANUSCRIPT_DRAFT_v2.md) and
[LITERATURE_MATRIX_v2.md](LITERATURE_MATRIX_v2.md). Experiment verification
and prioritized next steps are in
[EXPERIMENT_REVIEW.md](EXPERIMENT_REVIEW.md) and
[REMAINING_WORK.md](REMAINING_WORK.md).

This package is isolated from the production application. It constructs
auditable direct-horizon forecast samples from the raw city-day CSV, applies
explicit AQI target policies, assigns target-date partitions, and checks
coverage and timestamp invariants. It does not train models or alter existing
data/model artifacts.

From the repository root:

```powershell
python -m research.aqi_forecasting.data_audit
```

Primary samples use exact AQI dates at the forecast origin, origin minus one
calendar day, and origin minus seven calendar days, plus target-date month and
weekday sine/cosine values. Missing targets or lags are not imputed. Target
dates determine partition membership; the approved fixed partitions and
expanding-window folds are in `protocol.py` and `temporal_splits.py`.

`exclude` rejects raw AQI outside `[0, 500]`; `cap` maps values above 500 to 500
and rejects negatives. Both retain raw values/status for audit. The source and
interpretation of this dataset, including values above 500, require independent
verification before scientific claims.

The research package intentionally does not import production API routes,
production model artifacts, the database, or live data clients.

Date parsing accepts mixed date/time string formats and normalizes valid
timezone-naive timestamps to calendar days. Timezone-aware timestamps are
rejected because converting zones could change the daily observation date.
Duplicate city/calendar-day records are reported by the audit and rejected by
sample construction; they are never silently aggregated.

## Baseline development

Run deterministic persistence, annual seasonal-naive, training-only
city/month climatology, weekly seasonal-naive (horizons 1 and 3 only), and
regularized linear baselines with:

```powershell
venv\Scripts\python.exe -m research.aqi_forecasting.run_development
```

The command reports development-fold selection and 2019 validation only. It
does not score the final test period. Ridge alpha is selected by the
equal-weight mean MAE across the fixed 2017, 2018, and 2019 expanding folds;
ties select the larger alpha. The scaler and Ridge estimator are refit on the
2015–2018 training partition using the selected alpha. The reported 2019
validation results are selection data and are not an unbiased final estimate.
At horizon 7, weekly seasonal-naive is identical to persistence and is omitted
as a separate comparator. Prediction tables retain unavailable cases and
reasons; common-case metrics and native method coverage are reported
separately.

### Saving a development run

The command below fits the Ridge baseline and performs development-fold alpha
selection plus 2019 validation. It does not generate final-test predictions
or score the final test period:

```powershell
venv\Scripts\python.exe -m research.aqi_forecasting.run_development
```

Each invocation writes `run_record.json` and `run.log` into a unique
timestamp-and-random-ID directory under `research/aqi_forecasting/results/`.
Use `--output-directory PATH` to select another output root and `--data PATH`
to specify an input CSV. The runner creates a new run directory exclusively
and fails if that run ID already exists; it never replaces an earlier run.
The JSON records data identity, source fingerprint, Git state, runtime,
protocol, fold selection, coverage, and validation metrics. The log records
the command, timestamps, captured output, and path to its associated record.

The corrected runner was executed on 2026-10-10 and saved run
`20261010T101227Z-50924ef9974e`. Its validation/selection metrics are recorded
in that run's JSON and log; they are development results, not an unbiased
final estimate. An earlier record, `20261010T100925Z-52feac852ad6`, was
preserved, but predates the runner's validation-end sample-construction cutoff
and should not be used as the reproducibility reference. Neither run scored
the final test period.

### Data provenance

See [DATA_PROVENANCE.md](DATA_PROVENANCE.md) for the local file checksum,
verified byte match to Kaggle version 12, Kaggle's stated attribution and
license label, and unresolved upstream lineage, rights, and AQI-generation
questions. The Kaggle CC0 label is not treated as proof of upstream CPCB
licensing. Values above 500 remain an unresolved data-methodology issue.

### Python and dependencies

The repository's `runtime.txt` declares Python 3.11. Python 3.11 was not
available in the checked environments; the available research environment is
CPython 3.13.3 with pandas 2.3.3, NumPy 2.4.4, scikit-learn 1.8.0, SciPy
1.17.1, joblib 1.5.3, and threadpoolctl 3.6.0. Compatibility of this pipeline
with Python 3.11 remains unverified. The root `requirements.txt` is
unpinned.

The research-only
[requirements-research-py313.txt](requirements-research-py313.txt) records
the installed direct and relevant transitive dependency versions for the
available Python 3.13 environment. This is a pin set, not a Python-version
compatibility guarantee or a platform-independent lock. For a controlled run,
create a dedicated virtual environment and install this file there; do not
change the global environment. To align with the repository's declared Python
3.11 runtime, first provision Python 3.11 separately and validate the pinned
dependencies and safe test suite in that environment before relying on it.
Run records capture the actual Python/OS and relevant numerical dependency
versions plus the declared runtime.

### Planned author order

The planned author metadata is stored in [AUTHOR_METADATA.json](AUTHOR_METADATA.json):
Poonam Tanwar (mentor, first author), Krishna Bhatia (second author), Prateek
Singh (third author), and Snehaal Mukherjee (fourth author). Emails,
affiliations, academic titles, ORCIDs, and contribution statements remain
unconfirmed and are not inferred.
