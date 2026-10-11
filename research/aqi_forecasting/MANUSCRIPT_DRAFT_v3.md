# Evaluation of Short-Horizon Daily AQI Forecast Baselines on a Multi-City Indian Dataset

**Manuscript status:** Integrated working draft based on the saved development/model-selection run. The locked final-test evaluation has not been performed. Results below are selection-stage descriptions only.

## Authors

1. **Poonam Tanwar** — mentor; first author. Affiliation and email: [to be confirmed].
2. **Krishna Bhatia** — second author. Affiliation and email: [to be confirmed].
3. **Prateek Singh** — third author. Affiliation and email: [to be confirmed].
4. **Snehaal Mukherjee** — fourth author. Affiliation and email: [to be confirmed].

Academic titles, institutional affiliations, email addresses, ORCID identifiers, funding, and contribution statements require author confirmation and are not inferred here.

## Abstract

Evaluation of short-horizon air-quality forecasts depends on the precise definition of forecast origin and target date, the information available at prediction time, the temporal selection procedure, and the handling of incomplete or out-of-range observations. This study reports a retrospective comparison of direct 1-, 3-, and 7-calendar-day forecasts of the `AQI` field in a hosted multi-city Indian city-day dataset. It compares persistence, annual seasonal-naïve, training-only city/month climatology, weekly seasonal-naïve, and standardized Ridge regression under two predeclared target policies (`exclude` and `cap`). Samples use exact city/calendar-date joins, three AQI lags, and four deterministic target-date calendar encodings. Target dates from 2015–2018 are assigned to training, 2019 to development and model selection, and 2020-01-01 through 2020-07-01 to a locked test period. In the saved development run, Ridge alpha 0.1 was selected for all six policy/horizon combinations. On 2019 common eligible cases, pooled MAE ranged from 22.605 to 51.896 and pooled RMSE from 34.860 to 76.919 across methods and settings; native prediction coverage also varied by method. These values are descriptive selection-stage results because 2019 contributes to alpha selection and must not be interpreted as independent final estimates. The `exclude` and `cap` settings use different transformed labels and eligible populations. No locked-test predictions or scores have been generated. The experiment concerns retrospective AQI-field forecasting and does not evaluate operational warning lead time, event detection, false alarms, health outcomes, risk-zone identification, or effectiveness.

**Completion requirement:** If a separately authorized locked-test evaluation is later performed, revise this abstract with the predeclared test-period case counts, native coverage, and common-case MAE/RMSE for every policy and horizon. Report the test once without post-test tuning. Until then, retain the explicit statement that final-test evaluation is pending.

## Index Terms

Air quality index, daily forecasting, time-series validation, temporal leakage, forecast coverage, multi-city environmental data, reproducible research.

## I. Introduction

Daily AQI forecasting is an established environmental-data problem, but an evaluation result is meaningful only relative to a specified forecast horizon, information set, target definition, and evaluation design. A nominally “daily” study does not by itself establish a one-day-ahead forecast, and a multi-city dataset does not by itself establish generalization to cities excluded from training. Temporal dependence, missing records, and method-specific prediction availability can also make comparisons misleading if their handling is not made explicit.

This paper examines direct city-level predictions of the `AQI` field at 1-, 3-, and 7-calendar-day horizons in a hosted Indian city-day dataset. Its purpose is to document and compare a small set of forecasting baselines under exact calendar-date sample construction, target-date partitions, two declared treatments of AQI values above the nominal 500 scale, and explicit reporting of both native coverage and paired common-case errors. Such reporting is useful because an error value alone does not reveal how many valid targets a method could actually predict, while native errors can be calculated over different subsets when observations are unavailable.

The scope is retrospective forecasting, not an operational early-warning evaluation. The study does not evaluate alert delivery, warning lead time, event sensitivity, false-alarm burden, health benefit, or risk-zone identification. Nor does the study claim novelty, state-of-the-art performance, statistical superiority, causal effects, or generalization to unseen cities.

The project contains distinct production and research components:

1. **Production AQI calculation.** `src/data/india_aqi.py` implements a CPCB-labelled conversion from pollutant concentrations to sub-indices and an overall AQI, including breakpoint interpolation and an upper bound of 500. This current implementation does not establish how the historical CSV's `AQI` values were generated.
2. **Production predictive and alert features.** `src/models/train.py` describes same-time AQI regression from pollutant/calendar inputs with a random row split. `api/routes/forecast.py` produces a deterministic 24-hour forecast profile using fixed diurnal, seasonal, and weekday multipliers plus seeded noise; `api/scheduler.py` compares a recent reading with a selected alert threshold. None of these application behaviors is evaluated as a future-AQI forecast or validated warning system in this study.
3. **Research forecasting experiment.** `research/aqi_forecasting/` implements the direct-horizon sample construction, temporal protocol, baseline comparisons, coverage accounting, and run record from which the results reported here are drawn.

The manuscript makes a deliberately bounded contribution claim: it documents a project-specific implementation and saved development/model-selection comparison under explicit date, eligibility, coverage, and target-policy rules. Whether those design choices are novel relative to the wider literature has not been established.

## II. Related Work

### A. AQI forecasting

The reviewed literature identifies Indian AQI forecasting studies using statistical and machine-learning approaches, including seasonal ARIMA and principal-component regression for Delhi [1], Prophet as described for Delhi and Bengaluru [2], SARIMAX [3], and recurrent-neural or other machine-learning comparisons for Delhi [4], [5]. A nationwide graph-based study provides adjacent context for spatially structured city forecasting outside India [6]. This literature establishes that AQI forecasting and a variety of model families are existing research topics; it does not establish novelty for the present experiment.

The depth of evidence is uneven. For several AQI papers the available evidence reviewed for this study was limited to bibliographic records or abstracts. Abstract-level descriptions do not verify exact forecast leads, data lineage, AQI construction, predictor availability at forecast origin, temporal partitions, or whether reported metrics are comparable with the present protocol. Reference [5] has an unresolved concern about the correspondence of reported MSE and RMSE values; the full text and relevant table were not available, so this paper does not repeat or “correct” those figures. Reference [3]'s bibliographic metadata and publisher abstract have been checked, but its full methods and results have not been verified. The evidence depth and outstanding checks for each source are recorded in `LITERATURE_MATRIX_v2.md`.

### B. Forecast evaluation and temporal validation

Forecast-evaluation research treats out-of-sample design as central to assessing forecasting methods [7], [9]. Work on structured data discusses the implications of temporal and spatial dependence for cross-validation [8]. The accessible third-edition chapter of *Forecasting: Principles and Practice* describes rolling-origin evaluation [10]. These sources motivate explicit chronological partitions and expanding development folds; they are not cited as evidence that the present design is novel or optimal for every use.

### C. Position of this study

The evidence supports an evaluation rationale specific to this dataset and implementation: exact city/date construction, temporal selection, method-specific coverage, common-case errors, and sensitivity to the declared `exclude` and `cap` policies should be visible together. It does not support a claim that prior studies have failed to address these issues collectively. The literature review is focused rather than systematic, and comparable full-text protocol review remains incomplete.

## III. Evidence-Supported Research Gap

AQI forecasting is established, and the reviewed sources cover statistical, machine-learning, and spatially structured approaches. The current literature review does not establish that exact-date target and lag construction, target-date temporal partitions, method-specific coverage, common-case comparisons, and sensitivity to the two declared target policies are absent from prior studies. The defensible motivation is narrower: for this hosted dataset and implemented protocol, these choices make the comparison and its limitations explicit.

This is a project-specific evaluation and reporting rationale, not a field-wide gap or a novelty claim. Establishing a broader gap would require a reproducible literature search and full-text comparison of target definitions, forecast leads, input timing, data provenance, split design, and coverage reporting. That work has not been completed.

## IV. Research Questions and Contributions

### A. Research questions

**RQ1:** What 2019 development/model-selection error and native-coverage profiles are recorded for the specified direct-horizon baselines by horizon and target policy, and how do their errors compare on shared eligible city/date cases?

**Answerability:** The saved run records policy/horizon-specific native coverage, valid-target denominators, and common-case MAE/RMSE. The answer is descriptive of that selection-stage run only; it is not an independent performance estimate because the 2019 fold contributed to Ridge alpha selection.

**RQ2:** How do target eligibility, native prediction coverage, and 2019 selection-stage errors differ descriptively between the `exclude` and `cap` target policies?

**Answerability:** The run records each policy separately. Since the policies transform targets differently and induce different eligible populations, differences are descriptive and are not a causal or paired treatment effect.

Questions about warning efficacy, event detection, false alarms, health impacts, causal effects, unseen-city generalization, nonlinear model value, and final-test performance are outside the active research questions and are not answered by the current evidence.

### B. Project-specific contributions

The study provides the following implementation and reporting contributions, without asserting that they are novel:

1. It operationalizes direct 1-, 3-, and 7-calendar-day targets with exact city/date joins for targets and AQI lags and explicit checks that AQI input timestamps are no later than the forecast origin. Evidence: `protocol.py`, `forecast_samples.py`, and their sample-construction tests.
2. It applies target-date partitions and expanding development folds while treating 2019 as a model-selection period rather than an independent test. Evidence: `protocol.py`, `temporal_splits.py`, and the saved run configuration and fold records.
3. It reports both method-specific native prediction coverage and common-case errors calculated on shared eligible city/date cases. Evidence: `baselines.py`, `coverage.py`, and the saved `validation.methods` and `validation.common_case_metrics` records.
4. It documents policy-specific analyses and records data/run identity and configuration while retaining explicit provenance caveats. Evidence: `target_policies.py`, `manifest.py`, the saved run record, and `DATA_PROVENANCE.md`.

These are contributions of the implemented study package and its report, not claims of field-wide novelty, model superiority, or operational efficacy.

## V. System Context and Scope

The research methods forecast the hosted dataset's city-day `AQI` field. They are not the production pollutant-to-AQI estimator and do not call the production forecast-profile or alert workflow. In particular, results in this paper must not be described as validation of an application “early-warning system.” Such a claim would require, at minimum, an explicit warning-event definition, prospective information constraints, warning lead-time analysis, detection and false-alarm measures, and evaluation of the actual delivered alert behavior.

The research experiment is retrospective. City labels are present in both training and development periods; city-wise or unseen-city transfer is not tested. The evaluation is therefore limited to the temporal and city composition represented by this dataset and protocol.

## VI. Dataset and Provenance

### A. Local dataset

The research input is `data/raw/city_day.csv`. Its verified identity in the provenance record is 2,574,056 bytes with SHA-256 `0d84b21c3e4878bbad8df362f2ab05f61ad959538dddf5918e714077ed3c1847`. The file has 29,531 rows and 16 columns: `City`, `Date`, twelve pollutant fields (`PM2.5`, `PM10`, `NO`, `NO2`, `NOx`, `NH3`, `CO`, `SO2`, `O3`, `Benzene`, `Toluene`, `Xylene`), `AQI`, and `AQI_Bucket`. It contains 26 city labels and observed dates from 2015-01-01 through 2020-07-01.

The local file has been verified byte-for-byte against `city_day.csv` in Kaggle dataset version 12, “Air Quality Data in India (2015–2020),” attributed on Kaggle to `rohanrao`/Vopani. The Kaggle dataset record displays a CC0: Public Domain license label and attributes public availability to CPCB. These establish the hosted record's stated attribution and license label, not the upstream CPCB chain of custody or the uploader's authority to license upstream material.

### B. AQI values and provenance limitations

The local file contains 543 AQI values above 500, in the observed range 501–2049; all 543 are labelled `Severe` in the source file. CPCB's *National Air Quality Index: Final Report* describes pollutant sub-index calculations and an overall AQI based on the maximum sub-index [11]. The production implementation in `src/data/india_aqi.py` applies a current CPCB-labelled calculation bounded at 500. Neither the official methodology reference nor the production implementation establishes how the historical CSV's AQI field was generated.

It remains unresolved whether the values above 500 result from extrapolation, a different historical calculation, another transformation, or data errors. Upstream source snapshots, station coverage, daily aggregation, missingness semantics, historical AQI generation, and applicable upstream rights have not been fully established. Accordingly, the study forecasts the dataset's recorded AQI field and does not assert that it reconstructs the official historical CPCB AQI.

### C. Data source and reproducibility qualification

The local file's checksum and metadata are recorded in `DATA_PROVENANCE.md` and the saved `run_record.json`. A matching checksum establishes byte identity with the identified hosted artifact, not scientific validity of the AQI values or legal resolution of upstream rights. The run's source fingerprint identifies the research source files observed at execution time, but the historical source tree is not preserved as an immutable bundle; research files were untracked and changed after the run.

## VII. Forecasting Task and Sample Construction

For city \(c\), forecast-origin date \(t\), and horizon \(h \in \{1,3,7\}\), the target is the policy-transformed AQI on the exact target date \(t+h\), measured in calendar days. The target date and forecast origin are therefore distinct. Samples are assigned to data partitions by target date.

The three AQI inputs are same-city values at \(t\), \(t-1\), and \(t-7\) calendar days. Each is retrieved using an exact city/calendar-date key. A neighboring row is not used as a replacement when an expected calendar date is absent. The sample builder checks the availability timestamp of AQI inputs against the forecast origin. Four deterministic, known-at-origin calendar features encode target month and target weekday using sine and cosine terms. No pollutant concentration, city identifier, or target-derived field is part of the seven-feature Ridge schema.

Samples use dates in the local dataset and the approved protocol. The saved development run reports target dates in 2019; the locked test window is not used in this manuscript's results.

## VIII. Target Policies and Feature Set

Two separate target policies are analyzed:

* **`exclude`:** a raw AQI outside the inclusive range [0, 500] is invalid for a target or AQI lag.
* **`cap`:** a raw AQI above 500 is mapped to 500, while negative values and missing values remain invalid.

Raw values and their status are retained for audit. These policies are predeclared sensitivity analyses; neither is claimed to recover or validate the historical AQI-generation procedure. Because they result in different transformed outcomes and eligible populations, their results are presented separately. A numerical difference between policies cannot be interpreted as the causal effect of correcting AQI.

The predictor schema comprises AQI at the forecast origin and at one and seven calendar days before origin, joined by exact city/date keys, together with sine/cosine encodings of target month and target weekday. Pollutant concentration fields, city identifiers, and target-derived fields are excluded from the seven-feature Ridge input.

## IX. Forecasting Baselines

The saved comparison includes the following methods:

1. **Persistence:** predicts the policy-transformed AQI at the exact forecast origin. If the value is missing or invalid, no prediction is imputed.
2. **Annual seasonal-naïve:** retrieves the same city's AQI at the exact calendar date one year before the target, provided that source observation is available by the sample's forecast origin and valid under the policy. February 29 maps to February 28 in the preceding year. No nearby-date substitute is used.
3. **Training-only city/month climatology:** predicts the mean training target for that city and target month. If a city/month estimate is unavailable, it uses the pooled training mean for the month. The climatology is fitted from training target labels only.
4. **Standardized Ridge regression:** fits a `StandardScaler` followed by Ridge regression separately by policy and horizon. The seven approved predictors are the three AQI lags and four target-date calendar encodings.
5. **Weekly seasonal-naïve:** predicts from the exact same-city AQI value at target date minus seven days, subject to forecast-origin availability and target policy. It is reported for horizons 1 and 3. At a seven-day horizon it is identical to persistence and is not a distinct comparator.

No tree-based or other new model family is evaluated in this draft.

## X. Experimental Design and Model Selection

### A. Temporal partitions

The approved inclusive target-date periods are:

| Partition | Target-date range |
|---|---|
| Training | 2015-01-01–2018-12-31 |
| Development/model selection | 2019-01-01–2019-12-31 |
| Locked final test | 2020-01-01–2020-07-01 |

The expanding development folds train through 2016 and validate on 2017; train through 2017 and validate on 2018; and train through 2018 and validate on 2019. Fold train and validation periods are chronologically separated and are assigned by target date.

### B. Ridge selection

Candidate Ridge alpha values are 0.1, 1.0, and 10.0. For each target policy and horizon, selection minimizes the equal-weight mean validation MAE across the three expanding folds; exact ties are resolved in favor of the larger alpha. The saved run selected alpha 0.1 in all six settings. Since the 2019 fold is part of this selection process, neither its fold metric nor the separately reported 2019 baseline comparisons are an independent final estimate.

### C. Isolation and interpretation of the saved run

The corrected run is identified as `20261010T101227Z-50924ef9974e` and is stored under `results/20261010T101227Z-50924ef9974e/`. It predates a subsequent hardening change that restricts the runner's baseline-history input to rows ending 2019-12-31. At execution, the full CSV was read for audit/date parsing and the full history object was handed to baseline evaluation; the inspected baseline lookup code filters source observations by forecast origin, Ridge selection rejects targets on or after 2020-01-01, and climatology is trained only on training targets. The current runner now passes only pre-2020 history to the development baseline entry point, and a mocked regression test verifies this handoff. The saved run was not rerun after that code change and its record and log remain unchanged.

The record states that final-test outcomes were not used for selection and that no final-test scoring occurred. The test-period rows were nevertheless present in the CSV read for the full-file audit. This manuscript does not claim those rows were never read; it reports no final-test prediction, metric, score, or plot.

## XI. Evaluation Metrics and Reporting

For each method, **native prediction coverage** is the number of available predictions among valid targets divided by the number of valid target labels in that policy/horizon/partition. The denominator is policy-specific. Missing predictions are preserved as unavailable rather than imputed. Native error metrics describe each method's available valid prediction/target pairs and can therefore have different sample sets.

**Common-case metrics** are computed on the intersection of eligible city/date cases for which each compared method has both a valid target and an available prediction. All methods in a policy/horizon comparison are thus evaluated on identical cases in this paired descriptive table. MAE and RMSE are reported in the dataset's AQI units. No inferential statistical test or uncertainty interval is reported.

## XII. Run Record and Reproducibility

The saved run has identifier `20261010T101227Z-50924ef9974e` and resides in `results/20261010T101227Z-50924ef9974e/`. Its `run_record.json` and `run.log` record the invocation, timestamp, dataset identity, Git revision, research-source fingerprint, runtime, protocol configuration, selection outputs, and validation metrics. The record identifies Git revision `b3e5a3b0df921c4aff0e4460674e75eedffda5ad` and the execution-time research-source fingerprint `6435c3f1528530fba9dad3cab33a282ebbf0f749a72b8c60664a384f9d594312` over 24 files. The recorded command was `venv\Scripts\python.exe -m research.aqi_forecasting.run_development`; executing it fits/selects Ridge and is not a test-only command.

The run used CPython 3.13.3 on Windows with pandas 2.3.3, NumPy 2.4.4, scikit-learn 1.8.0, SciPy 1.17.1, joblib 1.5.3, and threadpoolctl 3.6.0. The repository declares Python 3.11, whose compatibility remains unverified. The run's fingerprint describes the research source files at execution time, but those files were untracked and the exact historical source bundle is not preserved. The saved record and log are retained; they were not overwritten or regenerated for this draft.

## XIII. Results

All numbers in this section are from the saved 2019 development/model-selection run. They are selection-stage results and not final-test estimates.

### A. Ridge alpha-selection fold errors

The table gives the selected alpha and the selected candidate's fold-level MAE. The 2019 fold participates in model selection.

| Policy | Horizon | Selected alpha | 2017 fold MAE | 2018 fold MAE | 2019 fold MAE |
|---|---:|---:|---:|---:|---:|
| exclude | 1 day | 0.1 | 29.099 | 23.442 | 23.360 |
| exclude | 3 days | 0.1 | 41.563 | 34.027 | 35.079 |
| exclude | 7 days | 0.1 | 46.589 | 37.662 | 38.689 |
| cap | 1 day | 0.1 | 30.452 | 25.149 | 25.264 |
| cap | 3 days | 0.1 | 44.808 | 37.282 | 38.161 |
| cap | 7 days | 0.1 | 50.792 | 41.479 | 42.141 |

### B. 2019 common-case errors

Each method entry is pooled MAE/RMSE on the common eligible city/date cases for the methods in that policy/horizon comparison. Values are in AQI units. Weekly seasonal-naïve is omitted at seven days because it is identical to persistence.

| Policy | Horizon | Common cases | Persistence | Annual seasonal-naïve | City/month climatology | Ridge | Weekly seasonal-naïve |
|---|---:|---:|---:|---:|---:|---:|---:|
| exclude | 1 day | 4,844 | 22.605 / 36.300 | 48.101 / 69.691 | 43.705 / 60.676 | 22.610 / 34.860 | 41.343 / 63.598 |
| exclude | 3 days | 4,775 | 36.294 / 55.738 | 47.700 / 68.964 | 43.092 / 59.654 | 34.088 / 49.660 | 40.918 / 62.923 |
| exclude | 7 days | 4,824 | 41.102 / 63.088 | 47.779 / 68.990 | 43.603 / 60.488 | 37.717 / 54.397 | — |
| cap | 1 day | 5,223 | 25.008 / 41.499 | 51.896 / 76.852 | 48.690 / 67.712 | 25.091 / 39.545 | 45.356 / 70.459 |
| cap | 3 days | 5,162 | 40.261 / 63.197 | 51.559 / 76.274 | 48.313 / 67.042 | 38.055 / 55.819 | 45.017 / 69.948 |
| cap | 7 days | 5,201 | 45.167 / 70.194 | 51.890 / 76.919 | 48.591 / 67.689 | 42.021 / 60.915 | — |

### C. 2019 native prediction coverage

Each entry is available predictions / valid target labels (coverage proportion). Each policy/horizon has the same valid-target denominator within that policy in this saved run. The annual seasonal-naïve baseline has lower native coverage because its exact historical-date source may be missing or policy-invalid. The climatology fallback supplies a prediction for every valid target, which does not imply low forecast error.

| Policy | Horizon | Persistence | Annual seasonal-naïve | Climatology | Ridge | Weekly seasonal-naïve |
|---|---:|---:|---:|---:|---:|---:|
| exclude | 1 day | 6,741/6,915 (0.975) | 5,252/6,915 (0.760) | 6,915/6,915 (1.000) | 6,331/6,915 (0.916) | 6,583/6,915 (0.952) |
| exclude | 3 days | 6,642/6,915 (0.961) | 5,252/6,915 (0.760) | 6,915/6,915 (1.000) | 6,264/6,915 (0.906) | 6,583/6,915 (0.952) |
| exclude | 7 days | 6,583/6,915 (0.952) | 5,252/6,915 (0.760) | 6,915/6,915 (1.000) | 6,199/6,915 (0.896) | — |
| cap | 1 day | 6,963/7,071 (0.985) | 5,528/7,071 (0.782) | 7,071/7,071 (1.000) | 6,659/7,071 (0.942) | 6,834/7,071 (0.966) |
| cap | 3 days | 6,889/7,071 (0.974) | 5,528/7,071 (0.782) | 7,071/7,071 (1.000) | 6,601/7,071 (0.934) | 6,834/7,071 (0.966) |
| cap | 7 days | 6,834/7,071 (0.966) | 5,528/7,071 (0.782) | 7,071/7,071 (1.000) | 6,543/7,071 (0.925) | — |

### D. Locked final-test results

**Not evaluated.** The locked period is 2020-01-01 through 2020-07-01 inclusive. No final-test predictions, error metrics, scores, comparisons, or plots are reported.

## XIV. Discussion

The saved run shows why both common-case errors and native prediction coverage are relevant to baseline reporting. Common-case evaluation holds the city/date comparison set fixed across methods, while native coverage makes visible how often each method can produce a prediction among policy-valid targets. Neither view alone fully characterizes operational usability, and the present study does not measure warning utility.

Across the recorded settings, common-case errors and coverage vary with horizon and target policy. These are descriptive properties of this saved selection-stage run. Ridge alpha selection includes 2019; consequently, the 2019 values do not provide independent evidence of generalization or establish that any baseline is superior. No statistical uncertainty or paired significance analysis was performed.

The `exclude` and `cap` analyses should not be treated as a controlled comparison of a single common outcome: each applies a different target transformation and yields a different eligible population. Results are therefore reported separately. In particular, the lower coverage of annual seasonal-naïve follows from its exact-date historical lookup requirement and should not be hidden through imputation.

The experiment includes cities represented during training and evaluates target dates in a later period. It does not test unseen-city transfer. It also does not evaluate the production application's AQI calculator, its synthetic 24-hour profile, its alert thresholds, or alert delivery. Forecasting error on a retrospective CSV target cannot on its own establish warning lead time, event detection, false-alarm rate, public-health benefit, or operational effectiveness.

## XV. Limitations and Threats to Validity

1. **Outcome validity and provenance:** The local bytes match Kaggle version 12, but upstream CPCB lineage, chain of custody, applicable rights, station composition, daily aggregation, missingness meaning, and historical AQI generation are unresolved.
2. **Values above the nominal scale:** The 543 observations above 500 range from 501 to 2049. `exclude` and `cap` are sensitivity policies, not validated reconstructions of historical AQI.
3. **Selection dependence:** The 2019 fold contributes to Ridge alpha selection. All reported 2019 comparisons are therefore selection-stage descriptions, not independent final performance estimates.
4. **Saved-run versus current-code distinction:** The saved run predates the current runner's pre-2020 history handoff hardening. The full dataset was read for audit/date parsing in the historical run. The current mocked test verifies input handoff but does not retroactively change the saved run or rerun its results.
5. **City generalization:** The train and development periods contain recurring city labels. No held-out-city or unseen-city generalization experiment was performed.
6. **Coverage and metric uncertainty:** Methods have different native prediction coverage. Common-case metrics address differing case sets for the displayed paired comparisons, but no uncertainty intervals, statistical tests, or repeated-seed analysis are provided.
7. **Model scope:** The comparison is baseline-only. It does not evaluate tree models, external meteorology, probabilistic forecasts, calibrated uncertainty, or warning-event detection.
8. **Literature scope:** The review is focused and non-systematic. Several sources are represented by abstracts or bibliographic metadata rather than full-text study-design review. Reference [5]'s MSE/RMSE concern remains unresolved.
9. **Runtime reproducibility:** The saved run used CPython 3.13.3 on Windows, while the repository declares Python 3.11. Python 3.11 compatibility is unverified. No environment migration is claimed.
10. **Historical source snapshot:** The run record stores a revision and deterministic research-source fingerprint, but the research files were untracked and the exact historical source bundle is not preserved. The current source fingerprint is not a substitute for that snapshot.
11. **Operational interpretation:** Warning delivery, lead time, event detection, false alarms, health outcomes, and public benefit were not measured. The study is not validation of an operational early-warning system.
12. **Locked-test status:** The final-test period remains unevaluated. No conclusions about final-test performance are possible.

## XVI. Conclusion and Future Work

This manuscript reports a saved development/model-selection comparison of direct short-horizon AQI-field forecasting baselines under explicit date construction, temporal folds, target policies, coverage denominators, and common-case metrics. The 2019 results are selection-stage descriptions because 2019 participates in Ridge alpha selection. They do not establish model superiority, independent generalization, or final-test performance.

The evidence supports a project-specific account of how baseline errors and prediction availability are reported under the implemented protocol. It does not establish a field-wide research gap or novelty. The local dataset's upstream lineage, rights, and historical AQI-generation procedure remain unresolved, and Python 3.11 compatibility has not been verified.

Future work requires author decisions about provenance and runtime constraints; review of the relevant full texts, especially reference [5]; and, only after separate authorization, one predeclared locked-test evaluation. Any operational early-warning claim would require a distinct evaluation of warning definitions, lead time, event detection, false alarms, and actual alert behavior. None of those future analyses is reported as completed here.

## XVII. Data and Code Availability

The research protocol, implementation, tests, provenance record, and saved run artifacts are in `research/aqi_forecasting/`. The saved run's structured record and associated log are in `results/20261010T101227Z-50924ef9974e/`.

The dataset is locally available at `data/raw/city_day.csv`; its hosted version-12 match and provenance limitations are documented in `DATA_PROVENANCE.md`. Dataset hosting metadata and its displayed CC0 label do not resolve upstream CPCB rights. Repository materials declare Python 3.11, whereas the saved run used Python 3.13.3; compatibility with Python 3.11 remains unverified. No claim of a fully supported or independently reproduced environment is made.

## XVIII. References

[1] A. Kumar and P. Goyal, “Forecasting of daily air quality index in Delhi,” *Science of the Total Environment*, vol. 409, no. 24, pp. 5517–5523, 2011, doi: 10.1016/j.scitotenv.2011.08.069.

[2] V. Gupta, S. Kapadia, and C. Bhadane, “Time Series Analysis and Forecasting of Air Quality in India,” in *2023 Fifth International Conference on Electrical, Computer and Communication Technologies*, 2023, pp. 1–5, doi: 10.1109/ICECCT56650.2023.10179673.

[3] Gayatri, S. Anand, and M. K. Satyarthi, “Analysis of air quality of Delhi and AQI forecast using SARIMAX,” *Journal of Biofuels*, vol. 15, no. 1, pp. 1–12, 2024, doi: 10.5958/0976-4763.2024.00001.5.

[4] C. B. Pande, N. L. Kushwaha, O. A. Alawi, S. S. Sammen, L. M. Sidek, Z. M. Yaseen, S. C. Pal, and O. M. Katipoğlu, “Daily scale air quality index forecasting using bidirectional recurrent neural networks: Case study of Delhi, India,” *Environmental Pollution*, vol. 351, Art. no. 124040, 2024, doi: 10.1016/j.envpol.2024.124040.

[5] C. B. Pande, L. Radhadevi, and M. B. Satyanarayana, “Evaluation of machine learning and deep learning models for daily air quality index prediction in Delhi city, India,” *Environmental Monitoring and Assessment*, vol. 196, no. 12, Art. no. 1215, 2024, doi: 10.1007/s10661-024-13351-1. The full text and relevant metric table were unavailable for this review; the reported MSE/RMSE issue remains unresolved.

[6] L. Chen et al., “Group-Aware Graph Neural Network for Nationwide City Air Quality Forecasting,” *ACM Transactions on Knowledge Discovery from Data*, vol. 18, no. 3, pp. 1–20, 2024 (online 2023), doi: 10.1145/3631713.

[7] V. Cerqueira, L. Torgo, and I. Mozetič, “Evaluating time series forecasting models: an empirical study on performance estimation methods,” *Machine Learning*, vol. 109, no. 11, pp. 1997–2028, 2020, doi: 10.1007/s10994-020-05910-7.

[8] D. R. Roberts et al., “Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure,” *Ecography*, vol. 40, no. 8, pp. 913–929, 2017, doi: 10.1111/ecog.02881.

[9] L. J. Tashman, “Out-of-sample tests of forecasting accuracy: an analysis and review,” *International Journal of Forecasting*, vol. 16, no. 4, pp. 437–450, 2000, doi: 10.1016/S0169-2070(00)00065-0.

[10] R. J. Hyndman and G. Athanasopoulos, *Forecasting: Principles and Practice*, 3rd ed. Melbourne, Australia: OTexts, 2021, Chapter 5, “The time series cross-validation.” [Online]. Available: https://otexts.com/fpp3/tscv.html.

[11] Central Pollution Control Board, *National Air Quality Index: Final Report*. [Online]. Available: https://airquality.cpcb.gov.in/ccr_docs/FINAL-REPORT_AQI_.pdf. [Accessed: Oct. 10, 2026]. The available report record does not establish an individual author or publication date.

[12] Kaggle, “Air Quality Data in India (2015–2020),” dataset by `rohanrao`, version 12. [Online]. Available: https://www.kaggle.com/datasets/rohanrao/air-quality-data-in-india. [Accessed: Oct. 10, 2026]. The attribution and CC0 label cited here are hosted-record metadata, not independent proof of upstream CPCB rights.
