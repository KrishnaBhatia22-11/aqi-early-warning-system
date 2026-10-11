# Evaluation of Short-Horizon Daily AQI Forecast Baselines on a Multi-City Indian Dataset

## Authors

1. **Poonam Tanwar** — mentor; first author. Affiliation and email: [to be confirmed].
2. **Krishna Bhatia** — second author. Affiliation and email: [to be confirmed].
3. **Prateek Singh** — third author. Affiliation and email: [to be confirmed].
4. **Snehaal Mukherjee** — fourth author. Affiliation and email: [to be confirmed].

Academic titles, institutional affiliations, email addresses, ORCID identifiers, funding, acknowledgments, and contribution statements have not been confirmed and are not inferred.

## Abstract

Short-horizon air-quality-index (AQI) forecast comparisons depend on exact target dates, origin-time data availability, temporal model selection, and observation eligibility. This study retrospectively evaluates direct 1-, 3-, and 7-calendar-day predictions of the recorded AQI field in a 29,531-row, 26-city Indian city-day dataset. Five methods are compared: persistence, annual seasonal-naïve, training-only city/month climatology, weekly seasonal-naïve, and standardized Ridge regression. The protocol uses exact-date AQI lags and target-date calendar features, with separate `exclude` and `cap` policies. Target dates in 2015–2018 are used for training, 2019 for development and selection, and 2020-01-01 through 2020-07-01 for a locked test. The saved run selected Ridge alpha 0.1 in all six policy/horizon settings. On 2019 common eligible cases, pooled mean absolute error (MAE) ranged from 22.605 to 51.896 AQI points, and root mean squared error (RMSE) from 34.860 to 76.919 points. These are selection-stage descriptions because 2019 also contributed to alpha selection. The policies use different transformed targets and eligible populations. No locked-test predictions or scores have been generated, and this retrospective comparison does not evaluate operational warning efficacy.

## Index Terms

Air quality index, daily forecasting, time-series validation, forecast coverage, multi-city environmental data, reproducible research.

## I. Introduction

Daily air-quality data do not by themselves define a forecast task. A comparison requires an explicit target date and forecast origin, a statement of which observations are available at that origin, and a temporal design that separates model development from evaluation. In a city-day panel, missing calendar dates and method-specific prediction availability also affect which targets can be forecast and how error summaries should be interpreted.

This study documents a project-specific comparison of direct 1-, 3-, and 7-calendar-day baselines for the recorded `AQI` field. It uses exact city/date joins, target-date partitions, two declared target policies, and both native prediction coverage and paired common-case errors. The purpose is to make the comparison and its eligible cases explicit, not to claim a field-wide research gap, model superiority, or operational value.

Three project components are distinct. The production AQI calculator in `src/data/india_aqi.py` converts pollutant concentrations to sub-indices and an overall value using a Central Pollution Control Board (CPCB)-labelled method. The production model in `src/models/train.py` is a same-time pollutant-to-AQI regression; `api/routes/forecast.py` generates a deterministic 24-hour profile from fixed multipliers and seeded noise, and `api/scheduler.py` compares recent readings with a selected threshold. These application components are not the retrospective direct-horizon experiment reported here, and none is evaluated here as an operational early-warning system. Results in this paper come only from `research/aqi_forecasting/`.

The paper first describes the literature and bounded study questions, then the dataset, task, methods, temporal protocol, and saved development results. It closes with interpretation, limitations, and reproducibility qualifications. The locked final-test period remains unevaluated.

## II. Related Work

### A. AQI forecasting

The reviewed records and abstracts describe Indian AQI forecasting using statistical and machine-learning methods: seasonal ARIMA and principal-component regression for Delhi [1], Prophet for Delhi and Bengaluru [2], SARIMAX [3], and recurrent-neural or other machine-learning comparisons for Delhi [4], [5]. A graph-based nationwide city study provides adjacent spatial-forecasting context [6]. These sources establish that AQI forecasting and multiple method families have been studied; they do not establish novelty for the present protocol.

The evidence depth varies. Reference [1]'s abstract describes statistical methods, while exact forecast lead, data dates, split, and numerical results remain unverified from full text. Reference [2]'s abstract describes its data and use of Prophet, but does not establish exact horizon, data lineage, or a city-holdout design. Reference [3]'s bibliographic metadata and publisher abstract were checked; its full article, detailed methods, and results were not reviewed. Reference [4]'s abstract reports model results that have not been independently checked against full-text tables, and its exact lead, dates, data source, and split remain unresolved. Reference [5]'s full text and relevant table were unavailable; the reported MSE/RMSE concern remains unresolved, and no corrected values are inferred. Reference [6]'s abstract does not by itself establish unseen-city evaluation. These qualifications are consistent with the focused reference review in `LITERATURE_MATRIX_v2.md`.

### B. Forecast evaluation

General literature addresses out-of-sample forecasting evaluation [7], [9] and validation under temporal or spatial structure [8]. The accessible third-edition chapter of *Forecasting: Principles and Practice* describes rolling-origin evaluation [10]. These works provide methodological context; the review does not establish that the present temporal design is novel or optimal, nor does it attribute detailed findings to works whose full text was not reviewed.

### C. Evidence-supported motivation

The reviewed literature does not demonstrate that prior work lacks the combination of exact-date sample construction, temporal partitions, coverage reporting, common-case comparison, and target-policy sensitivity used here. The defensible motivation is narrower: for this hosted dataset and implemented protocol, these choices make the comparison and its limitations explicit. A field-wide gap claim would require a reproducible literature search and full-text comparison of target definitions, leads, input timing, provenance, split design, and coverage reporting; that work has not been completed.

## III. Research Questions and Contributions

### A. Research questions

**RQ1:** What 2019 development/model-selection error and native-coverage profiles are recorded for the specified baselines by horizon and target policy, and how do their errors compare on shared eligible city/date cases?

This question is answerable descriptively from the saved run's validation metrics, denominators, and common-case counts. Because 2019 also contributes to Ridge alpha selection, these results are selection-stage descriptions, not independent final estimates.

**RQ2:** How do eligibility, native prediction coverage, and 2019 selection-stage errors differ descriptively between the `exclude` and `cap` policies?

The saved run reports the two policy-specific populations and results. The policies transform targets differently and induce different eligible cases; their differences are descriptive and not a causal contrast.

These are the only active research questions. The study does not ask or answer questions about nonlinear-model value, warning efficacy, event detection, false alarms, health impacts, causal effects, unseen-city generalization, or final-test performance.

### B. Project-specific contributions

The study documents four implementation and reporting elements without claiming they are novel:

1. Direct calendar-day targets with exact city/date target and lag joins and checks that AQI inputs are available by forecast origin (`protocol.py`, `forecast_samples.py`).
2. Target-date partitions and expanding development folds, with 2019 treated as a selection period (`protocol.py`, `temporal_splits.py`, and the saved run record).
3. Method-specific native prediction coverage alongside errors on common eligible city/date cases (`baselines.py`, `coverage.py`, and the saved validation summaries).
4. Separate `exclude` and `cap` analyses with recorded run/data identity and explicit provenance limitations (`target_policies.py`, `manifest.py`, `DATA_PROVENANCE.md`, and the saved run record).

These are contributions of this project-specific study and report. The available literature review does not establish field-level novelty.

## IV. Dataset and Provenance

### A. Dataset identity

The local comma-separated values (CSV) research input, `data/raw/city_day.csv`, is 2,574,056 bytes and has SHA-256 `0d84b21c3e4878bbad8df362f2ab05f61ad959538dddf5918e714077ed3c1847`. It contains 29,531 rows, 16 columns, 26 city labels, and observed dates from 2015-01-01 through 2020-07-01. Its columns are `City`, `Date`, twelve pollutant fields (`PM2.5`, `PM10`, `NO`, `NO2`, `NOx`, `NH3`, `CO`, `SO2`, `O3`, `Benzene`, `Toluene`, `Xylene`), `AQI`, and `AQI_Bucket`. The local file has 4,681 missing `AQI` values.

The local bytes were previously verified as identical to `city_day.csv` in Kaggle dataset version 12, “Air Quality Data in India (2015–2020)” [12]. Kaggle's record attributes the data to CPCB and displays a CC0: Public Domain license label. This identifies the hosted artifact and records Kaggle's stated attribution and license label; it does not establish the CPCB source snapshot, a complete upstream chain of custody, or the uploader's authority to license upstream material.

### B. Historical AQI values and methodology

The local file contains 543 AQI values above 500, ranging from 501 to 2049; each is labelled `Severe` in the file. CPCB's *National Air Quality Index: Final Report* describes pollutant sub-indices based on concentration breakpoints and an overall AQI based on the maximum sub-index [11]. The current production implementation in `src/data/india_aqi.py` uses a CPCB-labelled calculation bounded at 500. Neither that methodology nor the present application code establishes how the historical CSV's AQI field was generated.

It remains unknown whether values above 500 reflect extrapolation, a different historical calculation, another transformation, or errors. The upstream source snapshot and rights, AQI-generation procedure, aggregation, station coverage, and meaning of missing observations are unresolved. Accordingly, this study forecasts the dataset's recorded AQI field and does not claim to reconstruct historical CPCB AQI.

## V. Forecasting Task and Sample Construction

For city \(c\), forecast-origin date \(t\), and horizon \(h \in \{1,3,7\}\), the response is the policy-transformed AQI on the exact target date \(t+h\), in calendar days. Samples are assigned to partitions by target date. The three AQI predictors are same-city observations at \(t\), \(t-1\), and \(t-7\) calendar days. They are joined using exact city/date keys; a neighboring row does not replace a missing date. The sample builder checks that AQI input timestamps do not exceed the forecast origin.

Four deterministic calendar predictors encode target month and target weekday using sine and cosine terms. The Ridge feature schema therefore contains three AQI lags and four target-date encodings. Pollutant concentrations, city identifiers, and target-derived fields are excluded.

## VI. Target Policies and Forecasting Methods

### A. Target policies

The study uses two separate policies:

* **`exclude`:** raw AQI values outside the inclusive range [0, 500] are invalid as targets or AQI lags.
* **`cap`:** raw AQI values above 500 are mapped to 500; negative and missing values remain invalid.

Raw values and status are retained for audit. These are sensitivity policies, not claims that either treatment is historically correct. Since they produce different target values and eligible populations, results are reported separately and are not interpreted as a causal effect.

### B. Baseline methods

1. **Persistence** predicts the policy-transformed AQI at the exact forecast origin; unavailable inputs remain missing predictions.
2. **Annual seasonal-naïve** uses the same city's exact calendar date one year before the target, only if available by the forecast origin and valid under the policy. February 29 maps to February 28 in the preceding year; no nearby date is substituted.
3. **Training-only city/month climatology** predicts the training-target mean for the same city and target month, falling back to the pooled training mean for that month. It is fitted using training targets only.
4. **Standardized Ridge regression** fits `StandardScaler` and Ridge on the seven approved features, separately by policy and horizon.
5. **Weekly seasonal-naïve** uses the exact same-city value at target date minus seven days, subject to origin availability and policy. It is reported at horizons 1 and 3; at horizon 7 it is identical to persistence.

No tree-based or additional model family was evaluated.

## VII. Experimental Design and Model Selection

### A. Target-date partitions

| Partition | Inclusive target-date interval |
|---|---|
| Training | 2015-01-01–2018-12-31 |
| Development and model selection | 2019-01-01–2019-12-31 |
| Locked final test | 2020-01-01–2020-07-01 |

The expanding development folds train through 2016 and validate in 2017; train through 2017 and validate in 2018; and train through 2018 and validate in 2019. Fold assignment uses target dates. Ridge candidates are \(\alpha \in \{0.1, 1.0, 10.0\}\). Selection minimizes the equal-weight mean validation MAE over the three folds; exact ties favor the larger alpha. Because the 2019 fold contributes to this selection, 2019 metrics are not independent estimates.

### B. Saved-run isolation qualification

The saved run, `20261010T101227Z-50924ef9974e`, was executed before the later runner hardening that limits the baseline history handoff to rows ending 2019-12-31. During the saved run, the full CSV was loaded for audit/date parsing and the full history object was passed to baseline evaluation. The inspected lookup code filters source observations by each forecast origin, Ridge selection excludes targets on or after 2020-01-01, and climatology is fitted only on training targets. The current runner passes only pre-2020 history to the development baseline entry point; a mocked test verifies this handoff. That later code change did not rerun or alter the saved experiment.

The run record states that final-test outcomes were not used for selection, no final-test predictions were generated, and no final-test scoring occurred. Test-period rows were nevertheless present in the full CSV read for audit and date parsing. Thus, “no final-test scoring” does not mean that the test rows were never read.

## VIII. Metrics

For a method and policy/horizon/partition, **native prediction coverage** is the number of available predictions among valid targets divided by the number of valid target labels. The denominator is policy-specific. A method's native error metrics can therefore use a different subset from another method's.

**Common-case metrics** are calculated on the intersection of eligible city/date cases for which every method in that comparison has both a valid target and an available prediction. Methods in a given policy/horizon row are compared on the same cases. MAE and RMSE are reported in AQI points. No inferential test, confidence interval, or uncertainty analysis was performed.

## IX. Reproducibility Record

The structured record and log for run `20261010T101227Z-50924ef9974e` are in `results/20261010T101227Z-50924ef9974e/`. The run started at `2026-10-10T10:12:27.954998+00:00` and completed at `2026-10-10T10:12:40.163426+00:00`. The record's SHA-256 is `a7eac260052a596e1b03848e72a56269e2ce695ead9f6f4326a8d0d6287186c5`; the log's SHA-256 is `f3b94b28ed5e29e75df7bf53d64fbeff75f06582be55c8b5461663000ea00d935`. The record reports Git revision `b3e5a3b0df921c4aff0e4460674e75eedffda5ad` and a 24-file research-source fingerprint of `6435c3f1528530fba9dad3cab33a282ebbf0f749a72b8c60664a384f9d594312`.

The run used CPython 3.13.3 on Windows 11, pandas 2.3.3, NumPy 2.4.4, scikit-learn 1.8.0, SciPy 1.17.1, joblib 1.5.3, and threadpoolctl 3.6.0. The repository declares Python 3.11; compatibility with that version remains unverified. Research files were untracked at execution, and the exact historical source tree is not preserved as an immutable bundle. The recorded source fingerprint therefore identifies the run's recorded source state but does not by itself make that state recoverable.

## X. Results

All results below are from the saved 2019 development/model-selection run. They are not final-test results or independent estimates.

### A. Ridge alpha selection

The following table reports the selected alpha and that candidate's fold MAE in AQI points. The 2019 fold was part of selection.

| Policy | Horizon | Selected \(\alpha\) | 2017 MAE | 2018 MAE | 2019 MAE |
|---|---:|---:|---:|---:|---:|
| exclude | 1 day | 0.1 | 29.099 | 23.442 | 23.360 |
| exclude | 3 days | 0.1 | 41.563 | 34.027 | 35.079 |
| exclude | 7 days | 0.1 | 46.589 | 37.662 | 38.689 |
| cap | 1 day | 0.1 | 30.452 | 25.149 | 25.264 |
| cap | 3 days | 0.1 | 44.808 | 37.282 | 38.161 |
| cap | 7 days | 0.1 | 50.792 | 41.479 | 42.141 |

### B. 2019 common-case errors

Each method entry is pooled **MAE/RMSE in AQI points** over the common eligible cases in its policy/horizon row. The final column is not applicable at seven days because weekly seasonal-naïve then equals persistence.

| Policy | Horizon | Common cases | Persistence | Annual seasonal-naïve | City/month climatology | Ridge | Weekly seasonal-naïve |
|---|---:|---:|---:|---:|---:|---:|---:|
| exclude | 1 day | 4,844 | 22.605 / 36.300 | 48.101 / 69.691 | 43.705 / 60.676 | 22.610 / 34.860 | 41.343 / 63.598 |
| exclude | 3 days | 4,775 | 36.294 / 55.738 | 47.700 / 68.964 | 43.092 / 59.654 | 34.088 / 49.660 | 40.918 / 62.923 |
| exclude | 7 days | 4,824 | 41.102 / 63.088 | 47.779 / 68.990 | 43.603 / 60.488 | 37.717 / 54.397 | — |
| cap | 1 day | 5,223 | 25.008 / 41.499 | 51.896 / 76.852 | 48.690 / 67.712 | 25.091 / 39.545 | 45.356 / 70.459 |
| cap | 3 days | 5,162 | 40.261 / 63.197 | 51.559 / 76.274 | 48.313 / 67.042 | 38.055 / 55.819 | 45.017 / 69.948 |
| cap | 7 days | 5,201 | 45.167 / 70.194 | 51.890 / 76.919 | 48.591 / 67.689 | 42.021 / 60.915 | — |

### C. 2019 native prediction coverage

Entries are available predictions / valid target labels (coverage proportion). Valid-target denominators are 6,915 for `exclude` and 7,071 for `cap` at each horizon.

| Policy | Horizon | Persistence | Annual seasonal-naïve | Climatology | Ridge | Weekly seasonal-naïve |
|---|---:|---:|---:|---:|---:|---:|
| exclude | 1 day | 6,741/6,915 (0.975) | 5,252/6,915 (0.760) | 6,915/6,915 (1.000) | 6,331/6,915 (0.916) | 6,583/6,915 (0.952) |
| exclude | 3 days | 6,642/6,915 (0.961) | 5,252/6,915 (0.760) | 6,915/6,915 (1.000) | 6,264/6,915 (0.906) | 6,583/6,915 (0.952) |
| exclude | 7 days | 6,583/6,915 (0.952) | 5,252/6,915 (0.760) | 6,915/6,915 (1.000) | 6,199/6,915 (0.896) | — |
| cap | 1 day | 6,963/7,071 (0.985) | 5,528/7,071 (0.782) | 7,071/7,071 (1.000) | 6,659/7,071 (0.942) | 6,834/7,071 (0.966) |
| cap | 3 days | 6,889/7,071 (0.974) | 5,528/7,071 (0.782) | 7,071/7,071 (1.000) | 6,601/7,071 (0.934) | 6,834/7,071 (0.966) |
| cap | 7 days | 6,834/7,071 (0.966) | 5,528/7,071 (0.782) | 7,071/7,071 (1.000) | 6,543/7,071 (0.925) | — |

### D. Locked final test

The locked period, 2020-01-01 through 2020-07-01 inclusive, has not been scored. No predictions, metrics, comparisons, or plots for this period are reported.

## XI. Discussion

The 2019 tables document method-specific common-case errors and native coverage under the recorded protocol. The coverage table shows that methods do not produce predictions for identical fractions of valid targets, while the common-case table holds cases constant within each comparison. These descriptive summaries do not establish that one method is superior: the reported period contributed to alpha selection, and no statistical inference or uncertainty analysis was performed.

The `exclude` and `cap` results concern different transformed targets and eligible populations and should be read separately. The annual seasonal-naïve method's exact-date source requirement also results in unavailable predictions; those values are retained as missing rather than imputed. The complete coverage of training-only climatology follows from its pooled-month fallback and is not evidence of short-term predictive accuracy.

The experiment concerns temporal prediction for cities represented in the dataset, not city holdout. It evaluates neither the production calculator and forecast profile nor the alert threshold workflow. A retrospective AQI error comparison does not measure warning lead time, event detection, false alarms, health effects, risk-zone identification, or operational effectiveness.

## XII. Limitations and Threats to Validity

1. **Data provenance and outcome validity:** Kaggle version-12 byte identity and the hosted CC0 label do not establish upstream CPCB lineage, rights, station coverage, aggregation, missingness semantics, or historical AQI generation.
2. **Out-of-range values:** The 543 observations above 500 (501–2049) have unresolved historical interpretation. Neither target policy is validated as the original AQI procedure.
3. **Selection-stage results:** The 2019 fold contributes to Ridge alpha selection; all reported 2019 errors remain selection-stage descriptions.
4. **Historical run versus current code:** The saved run predates current baseline-history handoff hardening. Full-file audit/date parsing included test-period rows, but the record flags no test outcomes used for selection, prediction generation, or scoring. The later mocked handoff test does not change or reproduce the saved run.
5. **Generalization:** The same city labels occur across temporal periods; unseen-city or station-level transfer is not evaluated.
6. **Statistical uncertainty:** No confidence intervals, significance tests, paired inference, or repeated-seed analysis were performed.
7. **Model and application scope:** No tree model or operational warning evaluation is included; health, causal, and public-benefit claims are unsupported.
8. **Literature coverage:** The review is focused and non-systematic. Several sources are represented only by abstracts or bibliographic records, reference [3]'s full text was not reviewed, and reference [5]'s MSE/RMSE concern remains unresolved.
9. **Runtime and source recovery:** The run used Python 3.13.3 while the repository declares Python 3.11; 3.11 compatibility is unverified. The research files were untracked at execution, and the historical source snapshot cannot be recovered from the run fingerprint alone.
10. **Locked test:** The final-test period has not been evaluated; no claim about its performance is possible.

## XIII. Conclusion and Future Work

The saved artifact supports a descriptive account of baseline errors and prediction coverage on the 2019 development/model-selection period under the specified direct-horizon protocol. It does not provide an independent final estimate, establish model superiority, or validate the application as an early-warning system. The data's upstream lineage and rights, historical AQI construction, and runtime compatibility remain unresolved.

Future work could address provenance and full-text literature gaps and, only after separate authorization, perform one predeclared locked-test evaluation. Any operational warning claim would require a separate study of warning definitions, lead time, event detection, false alarms, and actual alert behavior. None of these future analyses is presented as completed.

## XIV. Data and Code Availability

The research package, protocol, implementation, tests, provenance notes, and saved artifacts are under `research/aqi_forecasting/`; the saved run record and log are in `results/20261010T101227Z-50924ef9974e/`. The dataset is at `data/raw/city_day.csv`. The recorded command was `venv\Scripts\python.exe -m research.aqi_forecasting.run_development`; it invokes the development runner and performs model fitting and selection, so it is not a test-only command.

The environment discrepancy and source-recovery limitations are reported in Section IX. The local dataset's byte match to Kaggle version 12 and the hosted record's license label do not resolve upstream rights or historical data lineage.

## XV. References

[1] A. Kumar and P. Goyal, “Forecasting of daily air quality index in Delhi,” *Science of the Total Environment*, vol. 409, no. 24, pp. 5517–5523, 2011, doi: 10.1016/j.scitotenv.2011.08.069.

[2] V. Gupta, S. Kapadia, and C. Bhadane, “Time Series Analysis and Forecasting of Air Quality in India,” in *2023 Fifth International Conference on Electrical, Computer and Communication Technologies*, 2023, pp. 1–5, doi: 10.1109/ICECCT56650.2023.10179673.

[3] Gayatri, Sourabh Anand, and M. K. Satyarthi, “Analysis of air quality of Delhi and AQI forecast using SARIMAX,” *Journal of Biofuels*, vol. 15, no. 1, pp. 1–12, 2024, doi: 10.5958/0976-4763.2024.00001.5.

[4] C. B. Pande, N. L. Kushwaha, O. A. Alawi, S. S. Sammen, L. M. Sidek, Z. M. Yaseen, S. C. Pal, and O. M. Katipoğlu, “Daily scale air quality index forecasting using bidirectional recurrent neural networks: Case study of Delhi, India,” *Environmental Pollution*, vol. 351, Art. no. 124040, 2024, doi: 10.1016/j.envpol.2024.124040.

[5] C. B. Pande, L. Radhadevi, and M. B. Satyanarayana, “Evaluation of machine learning and deep learning models for daily air quality index prediction in Delhi city, India,” *Environmental Monitoring and Assessment*, vol. 196, no. 12, Art. no. 1215, 2024, doi: 10.1007/s10661-024-13351-1. Full text and the relevant metric table were unavailable; the MSE/RMSE concern remains unresolved.

[6] L. Chen et al., “Group-Aware Graph Neural Network for Nationwide City Air Quality Forecasting,” *ACM Transactions on Knowledge Discovery from Data*, vol. 18, no. 3, pp. 1–20, 2024 (online 2023), doi: 10.1145/3631713.

[7] V. Cerqueira, L. Torgo, and I. Mozetič, “Evaluating time series forecasting models: an empirical study on performance estimation methods,” *Machine Learning*, vol. 109, no. 11, pp. 1997–2028, 2020, doi: 10.1007/s10994-020-05910-7.

[8] D. R. Roberts et al., “Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure,” *Ecography*, vol. 40, no. 8, pp. 913–929, 2017, doi: 10.1111/ecog.02881.

[9] L. J. Tashman, “Out-of-sample tests of forecasting accuracy: an analysis and review,” *International Journal of Forecasting*, vol. 16, no. 4, pp. 437–450, 2000, doi: 10.1016/S0169-2070(00)00065-0.

[10] R. J. Hyndman and G. Athanasopoulos, *Forecasting: Principles and Practice*, 3rd ed. Melbourne, Australia: OTexts, 2021, Chapter 5, “The time series cross-validation.” [Online]. Available: https://otexts.com/fpp3/tscv.html.

[11] Central Pollution Control Board, *National Air Quality Index: Final Report*. [Online]. Available: https://airquality.cpcb.gov.in/ccr_docs/FINAL-REPORT_AQI_.pdf. The inspected repository record does not establish an individual author or verified publication date.

[12] Kaggle, “Air Quality Data in India (2015–2020),” dataset by `rohanrao`, version 12. [Online]. Available: https://www.kaggle.com/datasets/rohanrao/air-quality-data-in-india. Kaggle's displayed attribution and CC0 label are hosted-record metadata, not independent proof of upstream CPCB rights.
