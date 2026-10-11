# Evaluation of Short-Horizon Daily AQI Forecast Baselines on a Multi-City Indian Dataset

## Authors

**Poonam Tanwar** — Mentor; first author  
**Krishna Bhatia** — Second author  
**Prateek Singh** — Third author  
**Snehaal Mukherjee** — Fourth author

Affiliations, email addresses, academic titles, ORCID identifiers, funding, acknowledgments, and author contribution statements have not been confirmed and are intentionally omitted pending author approval.

## Abstract

Short-horizon air-quality-index (AQI) forecast comparisons depend on exact target dates, origin-time data availability, temporal model selection, and observation eligibility. This study retrospectively evaluates direct 1-, 3-, and 7-calendar-day predictions of the recorded AQI field in a 29,531-row, 26-city Indian city-day dataset. Five methods are compared: persistence, annual seasonal-naïve, training-only city/month climatology, weekly seasonal-naïve, and standardized Ridge regression. The protocol uses exact-date AQI lags and target-date calendar features, with separate `exclude` and `cap` policies. Target dates in 2015–2018 are used for training, 2019 for development and selection, and 2020-01-01 through 2020-07-01 for a locked test. The saved run selected Ridge alpha 0.1 in all six policy/horizon settings. On 2019 common eligible cases, pooled mean absolute error (MAE) ranged from 22.605 to 51.896 AQI points and root mean squared error (RMSE) from 34.860 to 76.919 points. These are selection-stage descriptions because 2019 also contributed to alpha selection. The policies use different transformed targets and eligible populations. No locked-test predictions or scores have been generated; the retrospective comparison does not evaluate operational warning efficacy.

## Index Terms

Air quality index, daily forecasting, temporal validation, forecast coverage, multi-city environmental data, reproducible research.

## I. Introduction

Daily air-quality data do not by themselves define a forecast task. A comparison requires an explicit target date and forecast origin, a statement of which observations are available at that origin, and a temporal design that separates model development from evaluation. In a city-day panel, missing calendar dates and method-specific prediction availability also affect which targets can be forecast and how error summaries should be interpreted.

This study documents a project-specific comparison of direct 1-, 3-, and 7-calendar-day baselines for the recorded `AQI` field. It uses exact city/date joins, target-date partitions, two declared target policies, and both native prediction coverage and paired common-case errors. The objective is to make the comparison and the populations underlying its metrics explicit; it is not to establish a field-wide research gap, model superiority, or operational utility.

The repository contains separate production and research components. The production calculator in `src/data/india_aqi.py` converts pollutant concentrations to sub-indices and an overall value using a Central Pollution Control Board (CPCB)-labelled method. The production model in `src/models/train.py` is a same-time pollutant-to-AQI regression. Separately, `api/routes/forecast.py` generates a deterministic 24-hour profile from fixed multipliers and seeded noise, while `api/scheduler.py` compares recent readings with a selected threshold. These application components are not the direct-horizon retrospective experiment evaluated here. Results in this paper come only from `research/aqi_forecasting/`; none of the production features is evaluated as an operational early-warning system.

The paper first summarizes related forecasting and evaluation work and states the study questions. It then describes the dataset, target construction, methods, and temporal design, before presenting the saved development results and their limitations.

## II. Related Work

### A. AQI forecasting

The reviewed records and abstracts describe Indian AQI forecasting using statistical and machine-learning methods: seasonal autoregressive integrated moving average (ARIMA) and principal-component regression for Delhi [1], Prophet for Delhi and Bengaluru [2], seasonal autoregressive integrated moving average with exogenous variables (SARIMAX) [3], and recurrent-neural or other machine-learning comparisons for Delhi [4], [5]. A graph-based nationwide city study provides adjacent spatial-forecasting context [6]. These sources establish that AQI forecasting and multiple method families have been studied; they do not establish novelty for the present protocol.

Evidence depth varies among the cited studies. For [1], the abstract describes statistical methods, but the exact forecast lead, data dates, split, and numerical results have not been verified from full text. The abstract for [2] describes the data and use of Prophet but does not establish the exact horizon, source lineage, or a city-holdout design. The bibliographic metadata and publisher abstract for [3] were checked, but its full article and detailed methods/results were not reviewed. The abstract for [4] reports model results not independently checked against full-text tables; its exact lead, dates, data source, and split remain unresolved. The full text and relevant table for [5] were unavailable, and a reported mean-squared-error (MSE)/RMSE concern remains unresolved; no corrected values are inferred here. The abstract for [6] does not by itself establish unseen-city evaluation. The review is focused and non-systematic; the source-by-source evidence status is summarized in [LITERATURE_MATRIX_v2.md](LITERATURE_MATRIX_v2.md).

### B. Forecast evaluation

General literature addresses out-of-sample forecasting evaluation [7], [9] and validation under temporal or spatial structure [8]. The accessible third-edition chapter of *Forecasting: Principles and Practice* describes rolling-origin evaluation [10]. These references provide methodological context. The available review does not establish that the present temporal design is novel or optimal, and no detailed findings are attributed to works whose full text was not reviewed.

### C. Study motivation and contribution boundary

The reviewed literature does not demonstrate that prior work lacks the combination of exact-date sample construction, temporal partitions, prediction-coverage reporting, common-case comparison, and target-policy sensitivity implemented here. The motivation is narrower: for this hosted dataset and protocol, making those choices explicit improves the interpretability of the reported comparison. A field-wide gap claim would require a reproducible search and full-text comparison of target definitions, forecast leads, input timing, data provenance, split designs, and coverage reporting. That work has not been completed.

## III. Research Questions and Study Contributions

### A. Research questions

**RQ1:** What 2019 development/model-selection error and native-coverage profiles are recorded for the specified baselines by horizon and target policy, and how do their errors compare on shared eligible city/date cases?

This question is answered descriptively from the saved validation metrics, valid-target denominators, and common-case counts. Because 2019 contributes to Ridge alpha selection, these results are selection-stage descriptions rather than independent final estimates.

**RQ2:** How do eligibility, native prediction coverage, and 2019 selection-stage errors differ descriptively between the `exclude` and `cap` policies?

The saved run reports the two policy-specific populations and results. The policies transform targets differently and induce different eligible cases; their differences are descriptive, not a causal contrast.

These are the only active research questions. The study does not ask or answer questions about nonlinear-model value, warning efficacy, event detection, false alarms, health impacts, causal effects, unseen-city generalization, or final-test performance.

### B. Project-specific contributions

This study documents the following implementation and reporting elements without asserting that they are novel:

1. Direct calendar-day targets with exact city/date target and lag joins and checks that AQI input timestamps do not exceed the forecast origin.
2. Target-date partitions and expanding development folds, with 2019 treated as a model-selection period.
3. Method-specific native prediction coverage alongside errors on shared eligible city/date cases.
4. Separate `exclude` and `cap` analyses with run/data identity and explicit provenance limitations.

These statements describe the project-specific implementation and saved development comparison. They are not claims of field-level novelty, state-of-the-art performance, or demonstrated operational effectiveness.

## IV. Dataset and Provenance

### A. Local dataset

The input is `data/raw/city_day.csv`, a comma-separated values (CSV) file of 2,574,056 bytes with SHA-256 `0d84b21c3e4878bbad8df362f2ab05f61ad959538dddf5918e714077ed3c1847`. It contains 29,531 rows, 16 columns, 26 city labels, and observed dates from 2015-01-01 through 2020-07-01. Its columns are `City`, `Date`, twelve pollutant fields (`PM2.5`, `PM10`, `NO`, `NO2`, `NOx`, `NH3`, `CO`, `SO2`, `O3`, `Benzene`, `Toluene`, `Xylene`), `AQI`, and `AQI_Bucket`. There are 4,681 missing values in the `AQI` column.

The local file was previously verified byte-for-byte against `city_day.csv` in Kaggle dataset version 12, “Air Quality Data in India (2015–2020)” [12]. Kaggle's record attributes the data to CPCB and displays a “CC0: Public Domain” license label. This identifies the hosted artifact and records its stated attribution and license label; it does not establish the original CPCB source snapshot, a complete upstream chain of custody, or the uploader's authority to license upstream material.

### B. AQI values and generation uncertainty

The local file contains 543 AQI values above 500, ranging from 501 to 2049; each is labelled `Severe` in the file. CPCB's *National Air Quality Index: Final Report* describes pollutant sub-indices based on concentration breakpoints and an overall AQI based on the maximum sub-index [11]. The current production implementation in `src/data/india_aqi.py` uses a CPCB-labelled calculation bounded at 500. Neither the CPCB methodology reference nor the current application implementation establishes how the historical CSV's `AQI` field was generated.

It remains unknown whether the values above 500 reflect extrapolation, a different historical calculation, another transformation, or data errors. The upstream source snapshot and rights, historical AQI-generation procedure, aggregation, station coverage, and meaning of missing observations remain unresolved. This study therefore forecasts the dataset's recorded AQI field and does not claim to reconstruct historical CPCB AQI. The provenance record and outstanding evidence needs are documented in [DATA_PROVENANCE.md](DATA_PROVENANCE.md).

## V. Forecasting Task and Sample Construction

For city \(c\), forecast-origin date \(t\), and horizon \(h \in \{1,3,7\}\), the target date is \(t+h\) calendar days. The outcome is the policy-transformed `AQI` value for city \(c\) on that exact target date. Samples are assigned to partitions by target date.

The primary model's seven predictors are three same-city AQI observations at \(t\), \(t-1\), and \(t-7\) calendar days, and four deterministic encodings of target month and target weekday. Each AQI lag is retrieved by an exact city/date join; a neighboring row does not substitute for an absent calendar date. The sample builder checks that the input timestamps are no later than the forecast origin. The four calendar features are sine and cosine encodings known from the target date. Pollutant concentrations, city identifiers, and target-derived fields are not included in the Ridge feature schema.

## VI. Target Policies and Forecasting Methods

### A. Target policies

The study uses two distinct policies:

* **`exclude`:** raw AQI values outside the inclusive interval [0, 500] are invalid as targets or AQI lags.
* **`cap`:** raw AQI values above 500 are mapped to 500; negative and missing values remain invalid.

Raw values and statuses are retained for audit. These policies are sensitivity analyses, not claims that either treatment reproduces the historical AQI calculation. Because they produce different transformed targets and eligible populations, their results are reported separately and are not interpreted as a causal effect.

### B. Baseline methods

1. **Persistence** predicts the policy-transformed AQI at the exact forecast origin. If that input is unavailable or invalid, the prediction remains unavailable.
2. **Annual seasonal-naïve** uses the same city's value at the exact calendar date one year before the target, only if it is available by the forecast origin and valid under the policy. February 29 maps to February 28 in the preceding year; no nearby date is substituted.
3. **Training-only city/month climatology** predicts the training-target mean for the same city and target month, with the pooled training mean for that month as fallback. It is fitted using training targets only.
4. **Standardized Ridge regression** fits a `StandardScaler` followed by Ridge regression on the seven approved predictors, separately for each policy/horizon setting.
5. **Weekly seasonal-naïve** uses the exact same-city value at target date minus seven days, subject to origin availability and policy. It is reported at horizons 1 and 3. At horizon 7 it is identical to persistence and is not a distinct comparator.

No tree-based or additional model family was evaluated.

## VII. Experimental Design

### A. Temporal partitions

The approved inclusive target-date partitions are shown in Table I.

**TABLE I. TARGET-DATE PARTITIONS**

| Partition | Inclusive target-date range | Role |
|---|---|---|
| Training | 2015-01-01–2018-12-31 | Fit forecasting methods |
| Development/model selection | 2019-01-01–2019-12-31 | Select Ridge alpha and report development results |
| Locked final test | 2020-01-01–2020-07-01 | Reserved; not scored |

Three expanding development folds are used: training through 2016 with validation in 2017; training through 2017 with validation in 2018; and training through 2018 with validation in 2019. Fold construction and the main partitions use target dates.

### B. Ridge model selection

The candidate Ridge regularization parameters are \(\alpha \in \{0.1, 1.0, 10.0\}\). For each target policy and horizon, selection minimizes the equal-weight mean validation MAE over the 2017, 2018, and 2019 folds. Exact ties are resolved in favor of the larger alpha. The saved run selected \(\alpha=0.1\) in all six policy/horizon settings. Since the 2019 fold participates in selection, all 2019 performance summaries are selection-stage results and are not independent estimates.

### C. Saved-run isolation qualification

The saved run `20261010T101227Z-50924ef9974e` predates a later hardening change that limits the development runner's baseline-history handoff to rows ending 2019-12-31. In the saved run, the full CSV was loaded for the data audit and date parsing, and the full history object was passed to baseline evaluation. The inspected baseline lookup code applies forecast-origin restrictions; Ridge selection rejects targets on or after 2020-01-01; climatology is fitted only on training targets. The current runner passes only pre-2020 history to the development baseline entry point, and a mocked test verifies that handoff. This subsequent change did not rerun or alter the saved experiment.

The saved record states that final-test outcomes were not used for selection, no final-test predictions were generated, and no final-test scoring occurred. Test-period rows were nevertheless present in the full CSV read for audit/date parsing. Thus, absence of final-test scoring must not be conflated with non-access to the test-period rows.

**FIGURE 1 PLACEHOLDER — Forecast protocol and data flow.** Prepare an implementation-grounded schematic showing the city/date AQI series; exact target and lag date joins; origin-time availability check; seven-feature Ridge input; `exclude` and `cap` branches; target-date train, development, and locked-test intervals; and the three expanding development folds. The figure must distinguish the saved run from subsequent history-handoff hardening and must not depict or imply final-test predictions or scores. No figure is generated in this draft.

## VIII. Evaluation Metrics

For method \(m\), policy \(p\), horizon \(h\), and partition \(q\), **native prediction coverage** is

\[
\mathrm{Coverage}_{m,p,h,q} =
\frac{\text{valid-target cases with an available prediction}}
{\text{valid-target cases}}.
\]

Its denominator is the number of valid target labels for that policy, horizon, and partition. The numerator counts the cases for which the method returns an available prediction among those valid targets. Unavailable predictions are not imputed. Consequently, native error summaries may be based on different subsets across methods.

**Common-case metrics** use the intersection of eligible city/date cases for which every method in a given policy/horizon comparison has both a valid target and an available prediction. Each method in a row is therefore evaluated on the same cases. MAE and RMSE are reported in AQI points. The saved analysis reports descriptive point metrics; it does not report inferential tests, confidence intervals, or other uncertainty estimates.

## IX. Run Record and Reproducibility

The saved record and associated log for run `20261010T101227Z-50924ef9974e` are stored in `research/aqi_forecasting/results/20261010T101227Z-50924ef9974e/`. The run started at `2026-10-10T10:12:27.954998+00:00` and completed at `2026-10-10T10:12:40.163426+00:00`. The structured record has SHA-256 `a7eac260052a596e1b03848e72a56269e2ce695ead9f6f4326a8d0d6287186c5`; the log has SHA-256 `f3b94b28ed5e29e75df7bf53d64fbeff75f06582be55c8b5461663000ea00d935`. The record reports Git revision `b3e5a3b0df921c4aff0e4460674e75eedffda5ad` and a 24-file research-source fingerprint `6435c3f1528530fba9dad3cab33a282ebbf0f749a72b8c60664a384f9d594312`.

The saved run used CPython 3.13.3 on Windows 11, pandas 2.3.3, NumPy 2.4.4, scikit-learn 1.8.0, SciPy 1.17.1, joblib 1.5.3, and threadpoolctl 3.6.0. Repository configuration declares Python 3.11, whose compatibility remains unverified. Research files were untracked at execution, and the exact historical source tree is not preserved as an immutable bundle. The recorded fingerprint describes the source state observed during that run; it does not by itself make that source tree recoverable.

## X. Results

All results in this section are from the saved 2019 development/model-selection run. They are selection-stage descriptions, not final-test results or independent performance estimates.

### A. Ridge alpha selection

Table II gives the selected alpha and the selected candidate's fold MAE in AQI points. The 2019 fold participates in the selection rule.

**TABLE II. SELECTED RIDGE ALPHA AND FOLD MAE (AQI POINTS)**

| Policy | Horizon | Selected \(\alpha\) | 2017 fold MAE | 2018 fold MAE | 2019 fold MAE |
|---|---:|---:|---:|---:|---:|
| exclude | 1 day | 0.1 | 29.099 | 23.442 | 23.360 |
| exclude | 3 days | 0.1 | 41.563 | 34.027 | 35.079 |
| exclude | 7 days | 0.1 | 46.589 | 37.662 | 38.689 |
| cap | 1 day | 0.1 | 30.452 | 25.149 | 25.264 |
| cap | 3 days | 0.1 | 44.808 | 37.282 | 38.161 |
| cap | 7 days | 0.1 | 50.792 | 41.479 | 42.141 |

### B. Common-case errors

Table III reports pooled MAE/RMSE in AQI points on the shared eligible cases for all methods in each policy/horizon comparison. The common-case count is shown explicitly. Weekly seasonal-naïve is omitted at seven days because it is identical to persistence at that horizon.

**TABLE III. 2019 SELECTION-STAGE COMMON-CASE MAE/RMSE (AQI POINTS)**

| Policy | Horizon | Common cases | Persistence | Annual seasonal-naïve | City/month climatology | Ridge | Weekly seasonal-naïve |
|---|---:|---:|---:|---:|---:|---:|---:|
| exclude | 1 day | 4,844 | 22.605 / 36.300 | 48.101 / 69.691 | 43.705 / 60.676 | 22.610 / 34.860 | 41.343 / 63.598 |
| exclude | 3 days | 4,775 | 36.294 / 55.738 | 47.700 / 68.964 | 43.092 / 59.654 | 34.088 / 49.660 | 40.918 / 62.923 |
| exclude | 7 days | 4,824 | 41.102 / 63.088 | 47.779 / 68.990 | 43.603 / 60.488 | 37.717 / 54.397 | — |
| cap | 1 day | 5,223 | 25.008 / 41.499 | 51.896 / 76.852 | 48.690 / 67.712 | 25.091 / 39.545 | 45.356 / 70.459 |
| cap | 3 days | 5,162 | 40.261 / 63.197 | 51.559 / 76.274 | 48.313 / 67.042 | 38.055 / 55.819 | 45.017 / 69.948 |
| cap | 7 days | 5,201 | 45.167 / 70.194 | 51.890 / 76.919 | 48.591 / 67.689 | 42.021 / 60.915 | — |

### C. Native prediction coverage

Table IV reports available predictions divided by valid target labels, with the coverage proportion in parentheses. The valid-target denominator is 6,915 for `exclude` and 7,071 for `cap` at each horizon in this run.

**TABLE IV. 2019 SELECTION-STAGE NATIVE PREDICTION COVERAGE**

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

The saved run documents method-specific errors on common eligible cases alongside native coverage. The two summaries answer different descriptive questions: common-case metrics hold the comparison cases constant within each row, whereas native coverage shows the fraction of valid targets for which each method produced a prediction. Neither summary establishes superiority. In particular, 2019 contributes to alpha selection, and the analysis reports no inferential test or uncertainty estimate.

The `exclude` and `cap` results concern different transformed outcomes and eligible populations and should be interpreted separately. The annual seasonal-naïve method's exact-date lookup requirement leaves some valid targets without a prediction; those cases remain unavailable rather than being imputed. The city/month climatology's pooled-month fallback provides predictions for all valid targets in the saved run, but complete coverage is not evidence of low forecast error.

The evaluation uses later dates for cities also represented during training. It does not assess transfer to unseen cities. It also does not evaluate the production AQI calculator, same-time regression, deterministic 24-hour profile, alert thresholds, or alert delivery. Retrospective AQI error metrics do not measure warning lead time, event detection, false alarms, health effects, risk-zone identification, or operational effectiveness.

## XII. Limitations and Threats to Validity

1. **Data provenance and outcome validity:** Byte identity with Kaggle version 12 and the hosted CC0 label do not establish upstream CPCB lineage, legal rights, station coverage, daily aggregation, missingness semantics, or historical AQI generation.
2. **Values above the nominal scale:** The 543 observations above 500 range from 501 to 2049, but their historical interpretation is unresolved. Neither target policy is validated as the original AQI procedure.
3. **Selection-stage results:** The 2019 fold contributes to Ridge alpha selection. All reported 2019 performance figures are therefore selection-stage descriptions.
4. **Historical run and current code:** The saved run predates the current baseline-history handoff hardening. The full CSV, including test-period rows, was read for audit/date parsing, although the saved record marks final-test outcome selection, prediction generation, and scoring as false. The later mocked handoff test does not change or reproduce the saved run.
5. **Generalization:** The same city labels occur in the training and development periods; unseen-city and station-level generalization were not evaluated.
6. **Statistical uncertainty:** No confidence intervals, significance tests, paired inferential analysis, or repeated-seed analysis are reported.
7. **Scope:** The study is baseline-only and does not evaluate nonlinear models, meteorological inputs, uncertainty calibration, operational warnings, health impacts, or causal effects.
8. **Literature coverage:** The review is focused and non-systematic. Several sources are represented only by abstracts or bibliographic records; reference [3]'s full text was not reviewed, and reference [5]'s MSE/RMSE concern remains unresolved.
9. **Runtime and source recovery:** The run used Python 3.13.3, whereas repository configuration declares Python 3.11. Compatibility with Python 3.11 is unverified. Research files were untracked at execution, and the historical source snapshot cannot be reconstructed from its fingerprint alone.
10. **Locked test:** The 2020-01-01–2020-07-01 period remains unevaluated; no claim about its performance is possible.

## XIII. Conclusion and Future Work

The saved development artifact supports a descriptive account of baseline errors and prediction coverage on the 2019 model-selection period under the specified direct-horizon protocol. These results are not independent final estimates because 2019 contributes to Ridge alpha selection. The study does not establish model superiority, unseen-city generalization, or operational early-warning effectiveness.

The data's upstream lineage and rights, historical AQI-generation procedure, and runtime compatibility remain unresolved. Future work may address these evidence gaps and, only after separate authorization, conduct a predeclared evaluation on the locked test. Any operational warning claim would require a distinct evaluation of warning definitions, lead time, event detection, false alarms, and actual alert behavior. None of these future analyses is reported as completed.

## XIV. Data and Code Availability

The research package, protocol, implementation, tests, provenance notes, and saved artifacts are under `research/aqi_forecasting/`. The saved run record and log are in `research/aqi_forecasting/results/20261010T101227Z-50924ef9974e/`; the analyzed dataset is `data/raw/city_day.csv`. The run record captures its command, data identity, runtime, protocol, source fingerprint, and development outputs. The recorded command invokes the development runner and performs model fitting and selection; it is not a test-only command. Data identity and hosted-record information are documented in [DATA_PROVENANCE.md](DATA_PROVENANCE.md), including the limits of the Kaggle attribution and license label.

## References

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
