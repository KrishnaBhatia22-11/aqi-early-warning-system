# Leakage-Aware Evaluation of Short-Horizon Daily AQI Forecasts Across Indian Cities

> **Versioning note:** The reviewed, expanded manuscript is
> [MANUSCRIPT_DRAFT_v2.md](MANUSCRIPT_DRAFT_v2.md). This original draft is
> retained unchanged as the pre-review version.

**Status:** Structured working draft. The final-test period is locked and has
not been scored. The reported 2019 results below are selection-stage
development results, not an unbiased estimate of final generalization.

## Authors

1. Poonam Tanwar — mentor; first author; affiliation/email: [to be confirmed]
2. Krishna Bhatia — second author; affiliation/email: [to be confirmed]
3. Prateek Singh — third author; affiliation/email: [to be confirmed]
4. Snehaal Mukherjee — fourth author; affiliation/email: [to be confirmed]

Academic titles, ORCIDs, institutional affiliations, email addresses, and
contribution statements are not yet verified and must not be inferred.

## Abstract

**Background:** Daily city-level air-quality records can support evaluation
of short-horizon AQI forecasts, but reported performance depends on target
construction, forecast-origin availability, temporal validation, and the
treatment of out-of-range source values. **Objective:** This study evaluates
direct 1-, 3-, and 7-calendar-day AQI forecasts for cities represented in a
publicly hosted Indian city-day dataset using explicit target policies and
leakage-aware baselines. **Methods:** The research pipeline constructs
city/date samples with exact AQI observations at the forecast origin and
selected prior dates, plus deterministic target-date calendar features.
Persistence, exact-date annual seasonal-naïve, training-only city/month
climatology, and standardized Ridge regression are compared under
exclude/cap treatments of AQI values above the stated 0–500 range. Samples
are assigned by target date to 2015–2018 training, 2019 development and
selection, and a final 2020-01-01 through 2020-07-01 test period. **Results:**
Development-fold and 2019 selection metrics are preserved in the run record;
the 2019 results are not independent because 2019 participates in Ridge
alpha selection. **Final evaluation:** [Reserved. Do not populate until
separate approval and final-test protocol review.] **Conclusion:** [To be
written after the locked final evaluation and provenance questions are
addressed.] This study evaluates AQI prediction, not operational risk-zone
detection or warning effectiveness.

## Index Terms

Air quality index, daily forecasting, temporal validation, urban air quality,
forecast coverage, data provenance, reproducible research.

## I. Introduction

Air-quality forecasting research must define the forecast target and the
information available at the forecast origin. A retrospective daily dataset
does not, by itself, establish that a predictor was available in real time or
that an alert threshold has operational meaning. Prior research includes
daily-scale AQI forecasting for Delhi using bidirectional recurrent neural
networks [1]. Evaluation-method literature emphasizes out-of-sample design
and time-ordered forecast origins [2], [4], [5].

This paper studies direct forecasts of the dataset's city-day AQI field at
three calendar horizons. The research question is deliberately narrower than
the repository's original “early warning” framing: it asks how simple,
auditable forecasting baselines compare under a fixed temporal protocol and
two declared treatments of AQI values above 500. The current implementation
does not identify risk zones, validate a warning threshold, or measure health
or intervention outcomes.

### A. Research questions

- **RQ1:** How do persistence, exact-date annual seasonal-naïve,
  training-only city/month climatology, and regularized linear regression
  compare for 1-, 3-, and 7-day direct forecasts on development/selection
  data, when native coverage and shared-case metrics are both reported?
- **RQ2:** How do observed coverage and forecast errors differ between the
  `exclude` and `cap` target policies?
- **RQ3:** What evidence is required to distinguish temporal interpolation
  across observed cities from generalization to held-out cities?

RQ3 is a future evaluation question; the reported development run does not
establish held-out-city performance.

## II. Related Work

India-focused work spans seasonal ARIMA and principal-component regression,
Prophet, SARIMAX, recurrent neural networks, and other machine-learning
comparisons for Delhi and other cities [1], [8]–[11]. Related spatial work
also studies group-aware graph models for nationwide city forecasting [12].
The available records and abstracts do not establish that their AQI
definitions, exact forecast leads, input availability, or validation designs
are comparable to this study; full-text review is required before making
like-for-like claims. Time-series evaluation research considers how
performance estimates depend on split and forecast-origin procedures [2],
[4]. Work on structured data also motivates explicit treatment of temporal
and spatial dependence [3]. Rolling forecasting-origin validation provides
a time-ordered evaluation framework [5].

The focused source review and access limitations are documented in
[`LITERATURE_MATRIX.md`](LITERATURE_MATRIX.md). This review is not exhaustive,
and no novelty claim is made.

## III. Research Gap and Contributions

### A. Provisional research gap

The defensible gap is a project-specific empirical question, not a claim that
the model or protocol is novel: what coverage and error trade-offs arise when
simple direct AQI forecasting baselines are evaluated on exact calendar
targets with city isolation, time-aware partitions, and explicit handling of
values above 500? Whether this question is distinct from prior literature
remains to be established through a broader full-text literature review.

### B. Contributions to be assessed

Subject to completion of the locked test and provenance work, the study may
contribute:

1. An auditable direct-horizon sample-construction protocol with exact-date
   lag alignment and forecast-origin checks.
2. A paired comparison of simple baseline methods that reports both native
   prediction coverage and metrics on shared eligible cases.
3. A transparent sensitivity analysis for two predeclared treatments of
   out-of-range AQI values.
4. A reproducible research package and run record that records the data
   checksum, source fingerprint, environment, protocol, and selection
   process.

These are candidate contributions, not established novelty claims.

## IV. System Architecture

The research pipeline is isolated in `research/aqi_forecasting/` and reads
the local `data/raw/city_day.csv` input. `data_audit.py` records input
identity and structural checks; `target_policies.py` preserves raw values
while deriving policy-specific values and validity; `forecast_samples.py`
builds exact-calendar targets and AQI lags; `temporal_splits.py` assigns
partitions by target date; `baselines.py` produces predictions and paired
metrics; and `run_development.py` writes a JSON run record and log.

The package does not call the production API, initialize the production
database, or load production model artifacts. Its output is an AQI estimate
for a city/date/horizon; no warning delivery or risk-zone workflow is
evaluated.

## V. Data and Methodology

### A. Data

The local input `data/raw/city_day.csv` contains 29,531 rows and 16 columns,
including city, date, pollutant fields, AQI, and AQI bucket, with 26 city
labels and observed dates from 2015-01-01 through 2020-07-01. The exact
SHA-256 and provenance evidence are recorded in
[`DATA_PROVENANCE.md`](DATA_PROVENANCE.md). The file is byte-identical to
Kaggle dataset version 12's `city_day.csv`; this does not resolve the
upstream CPCB lineage, rights, or historical AQI-generation procedure.

There are 543 observed AQI values above 500, ranging from 501 to 2049. These
values are not assumed to be correct or erroneous. The production AQI
calculation implementation does not establish how the historical CSV values
were generated.

### B. Target, horizon, and samples

For city \(c\), forecast origin \(t\), and horizon \(h \in \{1,3,7\}\)
calendar days, the target is the policy-transformed daily AQI at \(t+h\).
The approved AQI predictors are observations at \(t\), \(t-1\), and \(t-7\)
calendar days. They are joined by exact city/date keys; a neighboring row
does not substitute for a missing calendar date. Four known-at-origin
calendar encodings represent target month and target weekday with sine and
cosine terms.

The `exclude` policy marks raw AQI outside [0, 500] invalid. The `cap` policy
caps values above 500 at 500 and rejects negative values. Both retain the
raw AQI for audit. These are analysis policies rather than a resolution of
the underlying measurement methodology.

### C. Forecast baselines

1. **Persistence:** the transformed AQI at the exact forecast origin, when
   valid and available.
2. **Annual seasonal-naïve:** the same city's observation on the exact
   calendar date one year before the target, only if available by the
   forecast origin and valid under the target policy. February 29 maps to
   the previous February 28; other missing historical dates remain
   unavailable.
3. **Training-only city/month climatology:** the city-by-target-month mean
   of training target labels, with the documented pooled-month fallback for
   cities without a training estimate. No validation or test labels are
   used to fit these statistics.
4. **Regularized linear regression:** a direct-horizon Ridge model using
   only the three AQI lags and four calendar features. Standardization and
   regression are fitted on training data. Candidate alpha values are
   0.1, 1, and 10; selection minimizes equal-weight mean MAE over the
   expanding 2017, 2018, and 2019 folds, with ties resolved toward the
   larger alpha.
5. **Weekly seasonal-naïve:** exact AQI at target date minus seven days is
   evaluated for horizons 1 and 3. At horizon 7, it is identical to
   persistence and is not reported as a separate comparator.

Unavailable predictions are retained with exclusion reasons. Metrics are
computed on valid prediction/target pairs. Each method's native coverage is
reported separately from metrics on the common eligible city/date cases.

### D. Temporal protocol

Samples are partitioned by target date:

- Training targets: 2015-01-01 through 2018-12-31.
- Development/selection targets: 2019-01-01 through 2019-12-31.
- Locked final test targets: 2020-01-01 through 2020-07-01, inclusive.

The fixed expanding folds train through 2016 and validate 2017, train through
2017 and validate 2018, and train through 2018 and validate 2019. Since the
alpha selection rule includes the 2019 fold, the separate 2019 metrics are
selection-stage summaries and must not be described as unbiased validation.
No final-test predictions or metrics are reported in this draft.

## VI. Experimental Setup

The verified development environment for the recorded run was CPython 3.13.3
with pandas 2.3.3, NumPy 2.4.4, scikit-learn 1.8.0, SciPy 1.17.1, joblib
1.5.3, and threadpoolctl 3.6.0. The repository declares Python 3.11, whose
compatibility with this research pipeline remains unverified.

The corrected development command was:

```powershell
venv\Scripts\python.exe -m research.aqi_forecasting.run_development
```

The corresponding run record is
`results/20261010T101227Z-50924ef9974e/run_record.json`; the associated log
is `results/20261010T101227Z-50924ef9974e/run.log`. The earlier run
`20261010T100925Z-52feac852ad6` is preserved but predates the runner's
validation-end sample-construction cutoff and is not the reproducibility
reference.

## VII. Results

### A. Development-fold alpha selection and 2019 selection metrics

In the corrected run, Ridge selected \(\alpha=0.1\) for all six
policy/horizon configurations. The selected alpha's fold MAEs were:

| Policy | Horizon | 2017 fold MAE | 2018 fold MAE | 2019 fold MAE |
|---|---:|---:|---:|---:|
| exclude | 1 day | 29.099 | 23.442 | 23.360 |
| exclude | 3 days | 41.563 | 34.027 | 35.079 |
| exclude | 7 days | 46.589 | 37.662 | 38.689 |
| cap | 1 day | 30.452 | 25.149 | 25.264 |
| cap | 3 days | 44.808 | 37.282 | 38.161 |
| cap | 7 days | 50.792 | 41.479 | 42.141 |

The 2019 fold participates in alpha selection. These values characterize
selection, not an independent model-performance estimate.

### B. 2019 common-case MAE

The table gives pooled MAE on city/date cases with valid predictions from
all methods reported in that row. Values are descriptive selection-stage
results. They do not establish superiority or generalization.

| Policy | Horizon | Common cases | Persistence | Annual naïve | City/month climatology | Ridge | Weekly naïve |
|---|---:|---:|---:|---:|---:|---:|---:|
| exclude | 1 day | 4,844 | 22.605 | 48.101 | 43.705 | 22.610 | 41.343 |
| exclude | 3 days | 4,775 | 36.294 | 47.700 | 43.092 | 34.088 | 40.918 |
| exclude | 7 days | 4,824 | 41.102 | 47.779 | 43.603 | 37.717 | — |
| cap | 1 day | 5,223 | 25.008 | 51.896 | 48.690 | 25.091 | 45.356 |
| cap | 3 days | 5,162 | 40.261 | 51.559 | 48.313 | 38.055 | 45.017 |
| cap | 7 days | 5,201 | 45.167 | 51.890 | 48.591 | 42.021 | — |

The weekly-naïve comparator is omitted at seven days because it equals
persistence by construction.

### C. Native coverage

Coverage below is each method's own fraction of valid 2019 target cases for
which a prediction was available. The complete run record also contains
counts and unavailable-prediction reasons.

| Policy | Horizon | Persistence | Annual naïve | Climatology | Ridge | Weekly naïve |
|---|---:|---:|---:|---:|---:|---:|
| exclude | 1 day | 0.975 | 0.760 | 1.000 | 0.916 | 0.952 |
| exclude | 3 days | 0.961 | 0.760 | 1.000 | 0.906 | 0.952 |
| exclude | 7 days | 0.952 | 0.760 | 1.000 | 0.896 | — |
| cap | 1 day | 0.985 | 0.782 | 1.000 | 0.942 | 0.966 |
| cap | 3 days | 0.974 | 0.782 | 1.000 | 0.934 | 0.966 |
| cap | 7 days | 0.966 | 0.782 | 1.000 | 0.925 | — |

### D. Locked final evaluation

**Not run.** No final-test predictions or scores are included. This section
must remain unpopulated until separate approval and protocol review.

## VIII. Discussion

The corrected development run demonstrates that the pipeline can produce
time-ordered development-fold selection and 2019 descriptive results while
recording coverage and paired cases. The observed 2019 comparisons are not
evidence of a winning method: Ridge alpha selection incorporates 2019, and
the data provenance and above-500 value-generation questions remain open.
Native coverage also differs across methods, so paired metrics should be
interpreted alongside each method's native coverage rather than alone.

The two target policies produce different eligible samples and label
transformations; their scores are not direct comparisons on a single
unmodified target. Any final claim must report each policy and horizon
separately and explain the common-case definition.

## IX. Limitations

1. Kaggle version 12 is the verified byte-identical hosted artifact, but the
   upstream CPCB lineage, rights, and chain of custody are unresolved.
2. The historical process that generated the CSV AQI field, especially the
   543 values above 500, is not established by the production application's
   current AQI code.
3. A city-day aggregate is not a station-level representation, and the
   source does not establish stable station coverage or monitoring changes.
4. No external weather or pollutant forecast inputs are included. The AQI
   lag model is a univariate-history/calendar baseline, not a causal or
   mechanistic atmospheric model.
5. The available Python 3.13.3 run environment differs from the declared
   Python 3.11 runtime; Python 3.11 compatibility remains unverified.
6. 2019 participates in Ridge alpha selection, so 2019 metrics are not an
   independent estimate.
7. No locked final-test analysis, uncertainty intervals, formal paired
   significance analysis, or operational warning evaluation has been
   completed.
8. The limited literature review does not establish novelty or exhaustive
   coverage of the AQI forecasting literature.

## X. Conclusion

**Draft conclusion pending.** The current evidence supports describing an
isolated, auditable pipeline for direct short-horizon AQI baseline evaluation
and its development/selection results. It does not support claims of
final-test performance, operational early warning, risk-zone identification,
or algorithmic superiority. The manuscript should be finalized only after
provenance issues are resolved or explicitly bounded, Python-version
reproducibility is addressed, and the locked final-test stage is separately
authorized and completed.

## References

[1] C. B. Pande, N. L. Kushwaha, O. A. Alawi, S. S. Sammen, L. M. Sidek,
Z. Mundher Yaseen, S. C. Pal, and O. M. Katipoğlu, “Daily scale air quality
index forecasting using bidirectional recurrent neural networks: Case study
of Delhi, India,” *Environmental Pollution*, vol. 351, Art. no. 124040, 2024,
doi: 10.1016/j.envpol.2024.124040.

[2] V. Cerqueira, L. Torgo, and I. Mozetič, “Evaluating time series
forecasting models: an empirical study on performance estimation methods,”
*Machine Learning*, vol. 109, no. 11, pp. 1997–2028, 2020,
doi: 10.1007/s10994-020-05910-7.

[3] D. R. Roberts et al., “Cross-validation strategies for data with temporal,
spatial, hierarchical, or phylogenetic structure,” *Ecography*, vol. 40,
no. 8, pp. 913–929, 2017, doi: 10.1111/ecog.02881.

[4] L. J. Tashman, “Out-of-sample tests of forecasting accuracy: an analysis
and review,” *International Journal of Forecasting*, vol. 16, no. 4,
pp. 437–450, 2000, doi: 10.1016/S0169-2070(00)00065-0.

[5] R. J. Hyndman and G. Athanasopoulos, *Forecasting: Principles and
Practice*, 3rd ed. Melbourne, Australia: OTexts, 2021, Chapter 5. [Online].
Available: https://otexts.com/fpp3/tscv.html.

[6] Central Pollution Control Board, *National Air Quality Index*, final
report. [Online]. Available:
https://airquality.cpcb.gov.in/ccr_docs/FINAL-REPORT_AQI_.pdf. [Accessed:
Oct. 10, 2026]. See the provenance caveat in
[`DATA_PROVENANCE.md`](DATA_PROVENANCE.md).

[7] Kaggle dataset record, “Air Quality Data in India (2015–2020),” version
12, `city_day.csv`. [Online]. Available:
https://www.kaggle.com/datasets/rohanrao/air-quality-data-in-india.
[Accessed: Oct. 10, 2026]. The verified file hash, stated attribution, stated
license label, and unresolved upstream questions are documented in
[`DATA_PROVENANCE.md`](DATA_PROVENANCE.md).

[8] P. Kumar and P. Goyal, “Forecasting of daily air quality index in Delhi,”
*Science of the Total Environment*, vol. 409, no. 24, pp. 5517–5523, 2011,
doi: 10.1016/j.scitotenv.2011.08.069.

[9] S. Gupta, S. Kapadia, and R. Bhadane, “Time Series Analysis and
Forecasting of Air Quality in India,” in *2023 Fifth International Conference
on Electrical, Computer and Communication Technologies*, 2023, pp. 1–5,
doi: 10.1109/ICECCT56650.2023.10179673.

[10] V. Gayatri, S. Anand, and P. Satyarthi, “Analysis of air quality of Delhi
and AQI forecast using SARIMAX,” *Journal of Biofuels*, vol. 15, no. 1,
pp. 1–12, 2024, doi: 10.5958/0976-4763.2024.00001.5.

[11] C. B. Pande et al., “Evaluation of machine learning and deep learning
models for daily air quality index prediction in Delhi city, India,”
*Environmental Monitoring and Assessment*, vol. 196, no. 12, Art. no. 1215,
2024, doi: 10.1007/s10661-024-13351-1.

[12] Y. Chen et al., “Group-Aware Graph Neural Network for Nationwide City
Air Quality Forecasting,” *ACM Transactions on Knowledge Discovery from
Data*, vol. 18, no. 3, pp. 1–20, 2024 (online 2023), doi: 10.1145/3631713.
