# Evaluation of Short-Horizon Daily AQI Forecast Baselines on a Multi-City Indian Dataset

**Version:** 2.1, 2026-10-10  
**Manuscript status:** Working draft; final-test evaluation is not performed.
The 2019 results are development/model-selection results and must not be
interpreted as an independent final estimate.

## Authors

1. Poonam Tanwar — mentor; first author; affiliation and email: [to be confirmed]
2. Krishna Bhatia — second author; affiliation and email: [to be confirmed]
3. Prateek Singh — third author; affiliation and email: [to be confirmed]
4. Snehaal Mukherjee — fourth author; affiliation and email: [to be confirmed]

Academic titles, ORCIDs, institutions, email addresses, and author
contributions remain unconfirmed. No author details beyond the approved names,
order, and mentor designation are asserted.

## Abstract

Daily city-level air-quality records permit retrospective evaluation of
short-horizon air-quality index (AQI) forecasts, but results depend on exact
target construction, forecast-origin availability, temporal model selection,
and treatment of source values outside the stated AQI scale. This study
evaluates direct 1-, 3-, and 7-calendar-day forecasts on a multi-city Indian
city-day dataset using persistence, annual seasonal-naïve, training-only
city/month climatology, weekly seasonal-naïve, and regularized linear
regression. Models use only approved AQI lags and deterministic target-date
calendar encodings. Two predeclared target policies, `exclude` and `cap`,
address raw values above 500; neither is asserted to recover the unknown
historical AQI-generation procedure. Samples are assigned by target date to
2015–2018 training, 2019 development/model selection, and a locked
2020-01-01–2020-07-01 test period. In the recorded selection run, Ridge
selected alpha 0.1 for all six policy/horizon settings. Its 2019 common-case
MAE/RMSE ranged from 22.610/34.860 to 42.021/60.915, depending on policy and
horizon. Because 2019 also contributes to alpha selection, these metrics are
selection-stage descriptions, not unbiased performance estimates. No
final-test prediction or score has been generated. The experiment evaluates
retrospective AQI prediction; it does not validate warning lead time, event
detection, false-alarm rates, risk-zone identification, or operational
effectiveness.

**Final abstract requirement:** After separate authorization, append a
concise final-test result for every policy and horizon, including evaluation
case count, native coverage, paired common-case MAE/RMSE, and the prespecified
comparison against baselines. Report the locked test exactly once; do not
select or retune methods from those results. If test evaluation is not
authorized or provenance blockers remain unacceptable, retain the explicit
no-test statement above.

## Index Terms

Air quality index, daily forecasting, time-series validation, temporal
leakage, forecast coverage, multi-city environmental data, reproducibility.

## I. Introduction

Retrospective air-quality prediction is not synonymous with an operational
early-warning system. A defensible forecast evaluation must specify the
forecast target, horizon, information available at the forecast origin, and
the split used to estimate performance. Published Indian AQI studies span
statistical forecasting and machine-learning methods, but their titles and
abstracts do not always establish comparable lead times or time-aware
evaluation designs [1]–[5].

This study examines direct forecasts of the `AQI` field in a city-day
dataset at 1-, 3-, and 7-calendar-day horizons. It compares simple,
interpretable baselines with standardized Ridge regression under two
predeclared target policies. The intended scope is a reproducible,
retrospective baseline evaluation—not pollution causality, an atmospheric
process model, a health-impact study, or operational warning efficacy.

The project has three distinct components that must not be conflated:

1. **Production AQI calculation:** `src/data/india_aqi.py` implements a
   CPCB-labelled conversion from pollutant concentrations to sub-indices and
   an overall AQI, with breakpoint interpolation and an upper bound of 500.
   This application code does not establish how the historical CSV's AQI
   values were generated [11].
2. **Production predictive/alert features:** `src/models/train.py` describes
   a random-forest/XGBoost same-time AQI regression using pollutant and
   calendar inputs and a random row split. `api/routes/forecast.py` generates
   a deterministic 24-hour profile from fixed diurnal, seasonal, and
   weekday multipliers plus seeded noise. User alerts compare a recent
   reading with a chosen threshold in `api/scheduler.py`. These application
   behaviors are not the forecasting experiment in this paper and have not
   been validated here for forecast lead time, event detection, or false
   alarms.
3. **Research forecasting experiment:** the isolated
   `research/aqi_forecasting/` package builds direct-horizon samples and
   evaluates explicit baselines under target-date partitions. This is the
   only component from which the results in this manuscript are drawn.

### A. Research questions

- **RQ1:** What 2019 development/model-selection error and native-coverage
  profiles are observed for the approved baselines at each horizon and target
  policy, when comparisons are also paired on shared eligible city/date
  cases?
- **RQ2:** How do eligibility, coverage, and selection-stage errors differ
  between the `exclude` and `cap` target policies?
- **RQ3 (future extension):** Does an explicitly selected nonlinear
  tree-based model add useful evidence beyond these baselines under the same
  seven-feature protocol and leakage controls?

The current temporal experiment includes the same observed cities across
training and validation years. It does not evaluate zero-shot held-out-city
generalization; that claim is outside the results reported here.

## II. Related Work

### A. AQI forecasting and machine learning

India-focused studies include seasonal ARIMA and principal-component
regression for Delhi [1], Prophet across Delhi and Bengaluru [2], SARIMAX
work [3], and recurrent-neural and other machine-learning comparisons for
Delhi [4], [5]. A nationwide graph model provides adjacent evidence on
spatially structured city forecasting outside India [6]. These records show
that AQI forecasting is an established problem area; they do not establish
novelty for the present protocol.

Comparability remains uncertain. Several sources were reviewed at abstract
level, which is insufficient to verify exact forecast leads, predictor
availability at origin, AQI construction, date partitions, or whether
cross-validation respects time. In particular, comparing multiple cities is
not equivalent to testing on a held-out city. Full-text and supplement review
is required before interpreting published metrics against this study.

### B. Forecast evaluation and leakage

Out-of-sample forecasting literature treats split construction and forecast
origins as central to performance estimation [7], [9]. Work on structured
data also explains why dependence across time and space should influence
validation design [8]. A rolling-origin procedure uses only earlier
observations to construct each forecast and can be adapted to multi-step
horizons [10]. These principles motivate the target-date partitions and
expanding development folds used here; they do not make the present protocol
novel.

### C. Contribution boundary

The current contribution, if supported after the locked evaluation, is a
project-specific comparison of exact-calendar direct-horizon baselines that
reports both native coverage and paired common-case metrics, while exposing
the sensitivity to two target policies. The literature review is focused,
not systematic. No state-of-the-art, novelty, or superiority claim is made.
Reference-by-reference verification and unresolved checks appear in
[`LITERATURE_MATRIX_v2.md`](LITERATURE_MATRIX_v2.md).

## III. Research Questions and Candidate Contributions

The questions in Section I-A are answered only to the extent supported by the
saved 2019 selection artifact. Candidate contributions are:

1. Exact city/calendar-date target and lag construction with explicit
   forecast-origin timestamp checks.
2. Paired comparisons on common eligible cases alongside method-specific
   native prediction coverage and unavailable-prediction reasons.
3. A sensitivity comparison of predeclared `exclude` and `cap` treatments
   that preserves the observed raw AQI values.
4. A research package and run record capturing the data checksum, code
   fingerprint, runtime, configuration, folds, and selection-stage metrics.

These are candidate methodological contributions, not evidence of novelty.

## IV. Dataset and Data Provenance

### A. Dataset

The local file `data/raw/city_day.csv` has 29,531 records and 16 columns:
city, date, twelve pollutant fields, AQI, and AQI bucket. It contains 26 city
labels and spans observed dates 2015-01-01 through 2020-07-01. Its SHA-256 is
`0d84b21c3e4878bbad8df362f2ab05f61ad959538dddf5918e714077ed3c1847`; the
corrected run record reports the same checksum and file size of 2,574,056
bytes.

The local bytes match Kaggle's version-12 `city_day.csv` byte-for-byte [12].
Kaggle's dataset record attributes the data to CPCB and displays a CC0
license label. These are hosted-record claims; they do not establish the
underlying CPCB snapshot, chain of custody, or the uploader's authority to
license upstream material.

### B. AQI provenance and values above 500

The local file contains 543 AQI values above 500, ranging from 501 to 2049;
they are labelled “Severe” in the source file. CPCB's National AQI report
defines pollutant sub-index calculations and an overall AQI based on the
maximum sub-index [11]. The current production implementation also caps its
scale at 500. Neither fact proves how the historical CSV AQI field was
calculated. Whether those 543 values are extrapolated indices, another
transformation, or errors is unresolved. Upstream rights, station
composition, aggregation details, and the historical AQI calculation
remain provenance limitations. See
[`DATA_PROVENANCE.md`](DATA_PROVENANCE.md) for the evidence and boundaries.

### C. Target policies

- **exclude:** a raw AQI outside [0, 500] is invalid for the target or AQI
  lag under this policy.
- **cap:** a raw AQI above 500 is mapped to 500; negative values remain
  invalid.

Both policies retain raw values and status for audit. They are sensitivity
policies, not a claim that capping is scientifically correct or that either
policy reconstructs the source computation.

## V. Forecasting Methodology

### A. Forecast target and timing

For city \(c\), origin date \(t\), target date \(t+h\), and
\(h \in \{1,3,7\}\) calendar days, the response is the policy-transformed
city-day AQI on the exact target date. Samples are assigned to partitions by
target date. Required AQI lag features are same-city values at \(t\), \(t-1\),
and \(t-7\) calendar days. Each is joined by exact date; a neighboring row
does not replace a missing date. A timestamp invariant checks that every AQI
feature is available no later than the forecast origin.

Four deterministic predictors encode target month and target weekday as
sine/cosine pairs. The primary model schema is therefore the three AQI lags
plus those four calendar values; pollutant measurements, city identifiers,
and target-derived fields are excluded.

### B. Baseline methods

1. **Persistence:** predicts policy-transformed AQI at the exact forecast
   origin. If unavailable or invalid, the prediction remains missing with an
   exclusion reason.
2. **Annual seasonal-naïve:** uses the same city's AQI on the exact calendar
   date one year before the target, only if the historical observation is
   available by that sample's origin and valid under the policy. February 29
   maps to February 28 of the preceding year. It does not silently substitute
   another nearby date.
3. **Training-only city/month climatology:** predicts the training-label
   mean for the same city and target month. If the city/month estimate is
   absent, it uses the pooled training mean for that month. No validation or
   test target labels are used to fit these means.
4. **Regularized linear regression:** direct-horizon Ridge regression with
   the seven approved features. `StandardScaler` and Ridge are fitted as a
   training-only pipeline. Alpha candidates are 0.1, 1.0, and 10.0.
5. **Weekly seasonal-naïve:** uses exact AQI at target date minus seven
   days, subject to origin availability. It is reported only for horizons 1
   and 3; at horizon 7 it equals persistence by definition.

### C. Metrics and paired comparisons

For each method, native coverage is the number of predictions available for
valid targets divided by the number of valid target labels in the evaluated
partition. Missing predictions are not imputed. MAE and RMSE use only valid
prediction/target pairs. \(R^2\) is undefined for fewer than two observations
or a constant target and is represented as null in that case. Common-case
metrics use the intersection of case IDs for which every method in that
policy/horizon comparison has both a valid target and an available
prediction. All methods receive the same target samples for a run; the
evaluator preserves the same city/date/horizon identifiers.

## VI. Experimental Design and Baselines

### A. Temporal partitions

- Training target dates: 2015-01-01 through 2018-12-31.
- Development/model-selection target dates: 2019-01-01 through 2019-12-31.
- Locked final-test target dates: 2020-01-01 through 2020-07-01, inclusive.

The corrected runner constructs target samples only through the validation
end. Expanding Ridge folds train on 2015 through the year before the fold and
validate in 2017, 2018, or 2019. Alpha is selected by minimizing the
equal-weight mean fold MAE, with exact ties resolved in favor of the larger
alpha. Therefore, 2019 fold scores are part of model selection. The separately
reported 2019 metrics are selection-stage descriptions, not independent
validation estimates.

### B. Executed run and reproducibility record

The corrected run was invoked as:

```powershell
venv\Scripts\python.exe -m research.aqi_forecasting.run_development
```

Run ID `20261010T101227Z-50924ef9974e` is stored at
[`results/20261010T101227Z-50924ef9974e/run_record.json`](results/20261010T101227Z-50924ef9974e/run_record.json)
with associated
[`run.log`](results/20261010T101227Z-50924ef9974e/run.log). The record
stores Git revision `b3e5a3b0df921c4aff0e4460674e75eedffda5ad`, a research
source fingerprint
`6435c3f1528530fba9dad3cab33a282ebbf0f749a72b8c60664a384f9d594312`
(24 files at execution), input checksum, run configuration, alpha/fold
results, counts, and metrics. Research documentation has since changed, so
that fingerprint identifies the run-time snapshot and is not expected to
match the current documentation tree. The research files remain untracked;
the Git revision alone does not archive their content.

The recorded runtime is CPython 3.13.3 on Windows 11 with pandas 2.3.3,
NumPy 2.4.4, scikit-learn 1.8.0, SciPy 1.17.1, joblib 1.5.3, and
threadpoolctl 3.6.0. The repository declares Python 3.11; compatibility
with that version has not been verified. No lengthy migration was performed.

### C. Final-test boundary note

No final-test predictions, model-comparison metrics, or test scores appear in
the corrected run. The code first loads the full CSV for data audit and then
builds samples from rows no later than 2019-12-31. In the saved execution,
the full history object was passed to baseline evaluation; its lookup
preparation filters records by forecast origin before policy transformation,
Ridge selection rejects target dates on or after 2020-01-01, and climatology
fits training targets only. The current runner has since been hardened to
pass only history through 2019-12-31 to the baseline entry point, while
retaining the full-file audit and date parsing. A mocked runner test verifies
this handoff, but the saved run was not rerun and its record and log remain
unchanged. The test-period rows were still read into memory for audit/date
parsing; no claim is made that the test rows were never read.

## VII. Results

### A. Selection process

The selected Ridge alpha was 0.1 for every target-policy/horizon
combination. The following are MAE values for that candidate on the three
selection folds; the 2019 fold is itself used by the selection rule.

| Policy | Horizon | 2017 fold MAE | 2018 fold MAE | 2019 fold MAE |
|---|---:|---:|---:|---:|
| exclude | 1 day | 29.099 | 23.442 | 23.360 |
| exclude | 3 days | 41.563 | 34.027 | 35.079 |
| exclude | 7 days | 46.589 | 37.662 | 38.689 |
| cap | 1 day | 30.452 | 25.149 | 25.264 |
| cap | 3 days | 44.808 | 37.282 | 38.161 |
| cap | 7 days | 50.792 | 41.479 | 42.141 |

### B. 2019 selection-stage common-case errors

Each cell is pooled **MAE / RMSE** in AQI points on the same common eligible
city/date cases for the methods in that row. The weekly comparator is omitted
at seven days because it is identical to persistence. These descriptive
metrics are not independent estimates and do not justify a superiority claim.

| Policy | Horizon | Common cases | Persistence | Annual naïve | City/month climatology | Ridge | Weekly naïve |
|---|---:|---:|---:|---:|---:|---:|---:|
| exclude | 1 day | 4,844 | 22.605 / 36.300 | 48.101 / 69.691 | 43.705 / 60.676 | 22.610 / 34.860 | 41.343 / 63.598 |
| exclude | 3 days | 4,775 | 36.294 / 55.738 | 47.700 / 68.964 | 43.092 / 59.654 | 34.088 / 49.660 | 40.918 / 62.923 |
| exclude | 7 days | 4,824 | 41.102 / 63.088 | 47.779 / 68.990 | 43.603 / 60.488 | 37.717 / 54.397 | — |
| cap | 1 day | 5,223 | 25.008 / 41.499 | 51.896 / 76.852 | 48.690 / 67.712 | 25.091 / 39.545 | 45.356 / 70.459 |
| cap | 3 days | 5,162 | 40.261 / 63.197 | 51.559 / 76.274 | 48.313 / 67.042 | 38.055 / 55.819 | 45.017 / 69.948 |
| cap | 7 days | 5,201 | 45.167 / 70.194 | 51.890 / 76.919 | 48.591 / 67.689 | 42.021 / 60.915 | — |

### C. 2019 native prediction coverage

Coverage is available predictions / valid target labels. Denominators are
6,915 for `exclude` and 7,071 for `cap` for each horizon.

| Policy | Horizon | Persistence | Annual naïve | Climatology | Ridge | Weekly naïve |
|---|---:|---:|---:|---:|---:|---:|
| exclude | 1 day | 6,741/6,915 (0.975) | 5,252/6,915 (0.760) | 6,915/6,915 (1.000) | 6,331/6,915 (0.916) | 6,583/6,915 (0.952) |
| exclude | 3 days | 6,642/6,915 (0.961) | 5,252/6,915 (0.760) | 6,915/6,915 (1.000) | 6,264/6,915 (0.906) | 6,583/6,915 (0.952) |
| exclude | 7 days | 6,583/6,915 (0.952) | 5,252/6,915 (0.760) | 6,915/6,915 (1.000) | 6,199/6,915 (0.896) | — |
| cap | 1 day | 6,963/7,071 (0.985) | 5,528/7,071 (0.782) | 7,071/7,071 (1.000) | 6,659/7,071 (0.942) | 6,834/7,071 (0.966) |
| cap | 3 days | 6,889/7,071 (0.974) | 5,528/7,071 (0.782) | 7,071/7,071 (1.000) | 6,601/7,071 (0.934) | 6,834/7,071 (0.966) |
| cap | 7 days | 6,834/7,071 (0.966) | 5,528/7,071 (0.782) | 7,071/7,071 (1.000) | 6,543/7,071 (0.925) | — |

### D. Locked final evaluation

**Not performed.** The test period remains locked. No final-test prediction,
score, comparison, or result is reported. Completion requires a separately
authorized run, a review of the test-isolation hardening noted in Section
VI-C, and one-time reporting of each target policy and horizon without
post-test tuning.

## VIII. Discussion

The saved run documents an executable development/model-selection comparison
with per-method coverage and paired common-case errors. The resulting
selection-stage numbers vary with horizon and target policy; coverage also
varies by method. These properties are reasons to report coverage with error,
not grounds to declare a best method. In particular, the alpha selection uses
the 2019 fold, so the 2019 Ridge metrics are not independent evidence of
generalization.

The `exclude` and `cap` analyses use different policy-transformed labels and
eligible sets. Their scores must remain separate. Annual seasonal-naïve
coverage is lower than some methods because exact historical-date values may
be missing or policy-invalid; it is not appropriate to fill those predictions
for convenience. The climatology's complete valid-target coverage follows
from its training pooled-month fallback and does not imply that it forecasts
short-term variation well.

This evaluation concerns city/date forecasts on cities represented in the
training period. It does not establish city-wise transfer or station-level
generalization. Nor does an AQI error metric test health advisories, an alert
threshold, warning lead time, event sensitivity, false alarms, or public
benefit. The production dashboard's forecast profile is a separate
fixed-formula application feature, and the production AQI estimator is a
same-time pollutant-to-AQI model; neither is evaluated in the research run.

## IX. Limitations and Threats to Validity

1. **Outcome/source validity:** Kaggle version 12 is an exact byte match, but
   upstream CPCB lineage, licensing authority, station coverage, aggregation,
   and the historical AQI-generation method are unresolved.
2. **Above-scale observations:** 543 values exceed 500 (range 501–2049).
   Exclusion and capping are sensitivity policies; neither is validated as
   the correct interpretation.
3. **Temporal selection:** 2019 contributes to Ridge alpha selection. The
   reported 2019 scores are not an unbiased final estimate.
4. **Input isolation:** the saved run loaded and audited the full CSV and
   passed the full history object to baseline evaluation, whose lookup
   functions filter by forecast origin. The current runner structurally
   limits the baseline handoff to history through 2019-12-31; this correction
   has a mocked regression test but has not been used for a new experiment.
   The full CSV is still read for checksum/metadata audit and date parsing.
5. **City generalization:** train and validation include the same observed
   cities; unseen-city generalization has not been evaluated.
6. **Environment:** the run used Python 3.13.3 although `runtime.txt` declares
   Python 3.11. Compatibility with Python 3.11 remains unverified.
7. **Reproducibility snapshot:** the run record stores a source fingerprint
   and Git revision, but research files were untracked and subsequently
   edited. The fingerprint is an execution-time identity, not a preserved
   immutable source bundle.
8. **Model scope:** the baseline suite does not test nonlinear tree models,
   external meteorology, probabilistic forecasts, or uncertainty calibration.
9. **Evaluation scope:** no final test, statistical uncertainty or paired
   inference, warning-event evaluation, false-alarm analysis, or health
   outcome analysis has been conducted.
10. **Literature coverage:** the source review is limited; several studies
    were checked only at abstract level, and no systematic search was
    performed.

## X. Conclusion and Future Work

The available artifact supports a transparent description of the approved
baseline pipeline and its 2019 development/model-selection results. It does
not support a claim that any method is superior, that the project provides
validated early warning, or that it generalizes to unseen cities. The
conclusion on forecasting performance must remain provisional until the
provenance questions are bounded and an independently locked final evaluation
is separately authorized and completed. The minimum additional experiment
proposal is specified in [`REMAINING_WORK.md`](REMAINING_WORK.md); no
additional model has been trained for this draft.

## References

[1] A. Kumar and P. Goyal, “Forecasting of daily air quality index in Delhi,”
*Science of the Total Environment*, vol. 409, no. 24, pp. 5517–5523, 2011,
doi: 10.1016/j.scitotenv.2011.08.069.

[2] V. Gupta, S. Kapadia, and C. Bhadane, “Time Series Analysis and
Forecasting of Air Quality in India,” in *2023 Fifth International Conference
on Electrical, Computer and Communication Technologies*, 2023, pp. 1–5,
doi: 10.1109/ICECCT56650.2023.10179673.

[3] Gayatri, S. Anand, and M. K. Satyarthi, “Analysis of air quality of Delhi
and AQI forecast using SARIMAX,” *Journal of Biofuels*, vol. 15, no. 1,
pp. 1–12, 2024, doi: 10.5958/0976-4763.2024.00001.5.

[4] C. B. Pande, N. L. Kushwaha, O. A. Alawi, S. S. Sammen, L. M. Sidek,
Z. M. Yaseen, S. C. Pal, and O. M. Katipoğlu, “Daily scale air quality index
forecasting using bidirectional recurrent neural networks: Case study of
Delhi, India,” *Environmental Pollution*, vol. 351, Art. no. 124040, 2024,
doi: 10.1016/j.envpol.2024.124040.

[5] C. B. Pande, L. Radhadevi, and M. B. Satyanarayana, “Evaluation of
machine learning and deep learning models for daily air quality index
prediction in Delhi city, India,” *Environmental Monitoring and Assessment*,
vol. 196, no. 12, Art. no. 1215, 2024,
doi: 10.1007/s10661-024-13351-1.

[6] L. Chen et al., “Group-Aware Graph Neural Network for Nationwide City
Air Quality Forecasting,” *ACM Transactions on Knowledge Discovery from
Data*, vol. 18, no. 3, pp. 1–20, 2024 (online 2023),
doi: 10.1145/3631713.

[7] V. Cerqueira, L. Torgo, and I. Mozetič, “Evaluating time series
forecasting models: an empirical study on performance estimation methods,”
*Machine Learning*, vol. 109, no. 11, pp. 1997–2028, 2020,
doi: 10.1007/s10994-020-05910-7.

[8] D. R. Roberts et al., “Cross-validation strategies for data with temporal,
spatial, hierarchical, or phylogenetic structure,” *Ecography*, vol. 40,
no. 8, pp. 913–929, 2017, doi: 10.1111/ecog.02881.

[9] L. J. Tashman, “Out-of-sample tests of forecasting accuracy: an analysis
and review,” *International Journal of Forecasting*, vol. 16, no. 4,
pp. 437–450, 2000, doi: 10.1016/S0169-2070(00)00065-0.

[10] R. J. Hyndman and G. Athanasopoulos, *Forecasting: Principles and
Practice*, 3rd ed. Melbourne, Australia: OTexts, 2021, Chapter 5, “The time
series cross-validation.” [Online]. Available: https://otexts.com/fpp3/tscv.html.

[11] Central Pollution Control Board, *National Air Quality Index: Final
Report*. [Online]. Available:
https://airquality.cpcb.gov.in/ccr_docs/FINAL-REPORT_AQI_.pdf. [Accessed:
Oct. 10, 2026]. The accessible report metadata reviewed here did not
establish an individual author or publication date.

[12] Kaggle, “Air Quality Data in India (2015–2020),” dataset by
`rohanrao`, version 12. [Online]. Available:
https://www.kaggle.com/datasets/rohanrao/air-quality-data-in-india.
[Accessed: Oct. 10, 2026]. Kaggle's attribution and CC0 label are reported as
hosted-record metadata, not as independent proof of upstream rights.
