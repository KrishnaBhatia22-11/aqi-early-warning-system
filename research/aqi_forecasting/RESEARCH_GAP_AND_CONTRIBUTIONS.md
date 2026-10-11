# Research Gap and Contributions — Phase 1

**Paper:** “Evaluation of Short-Horizon Daily AQI Forecast Baselines on a
Multi-City Indian Dataset”  
**Scope decision:** Option A — baseline-only. This is a framing document, not
a revised manuscript or a claim of novelty.

## 1. Research landscape and what the reviewed evidence says

AQI forecasting is an established research problem. The literature matrix
identifies India-focused statistical forecasting (seasonal ARIMA and
principal-component regression for Delhi; Prophet described for Delhi and
Bengaluru; SARIMAX), and Delhi-focused recurrent-neural and other machine
learning comparisons. It also includes a nationwide graph-model study for
China and the United States as adjacent spatial-forecasting context, plus
general references on forecasting evaluation and temporally or spatially
structured validation.

Those descriptions are bounded by the evidence actually reviewed:

| Literature evidence | What can be stated | What remains unverified |
|---|---|---|
| [1]–[5] in [LITERATURE_MATRIX_v2.md](LITERATURE_MATRIX_v2.md) | The records and, for several papers, abstracts indicate that statistical and machine-learning AQI forecasting has been studied in Indian settings. | Exact forecast lead, target/AQI construction, input availability at forecast origin, data provenance, temporal split, city holdout, baseline comparability, and many numerical results require full text/supplement review. |
| Reference [3] | DOI/Crossref metadata and a publisher abstract were checked. The abstract describes pollutant trends and SARIMAX AQI forecasting. | Full text, exact target and lead, inputs, split, and tabulated performance were not reviewed. |
| Reference [5] | Bibliographic metadata was checked; an abstract-level metric discrepancy was previously noted. | Full text/tables were unavailable in the prior source check. The MSE/RMSE issue remains unresolved; no corrected number is inferred. |
| [6] | The bibliographic record/abstract describes a graph-based multi-city setting in China and the United States. | This is not evidence of unseen-city generalization in the present dataset or study. |
| [7]–[10] | These provide broad forecasting-validation context; the matrix records the access depth for each. | Detailed methodological recommendations must not be attributed beyond reviewed text. The focused review is not systematic. |

The literature review therefore supports the statement that the broader
problem and multiple method families already exist. It does **not** establish
that the exact combination of design choices below is absent from prior
work.

## 2. Evidence-supported gap: narrowly framed, not a novelty claim

The defensible motivation is an **evaluation and reporting need within this
particular dataset/protocol**, not an asserted literature-wide gap:

> For this hosted multi-city daily AQI artifact, a useful comparison must
> make the target date and forecast origin explicit, use exact city/calendar
> matches for required AQI lags, respect temporal partitions, disclose
> unavailable predictions, compare methods on common eligible cases as well
> as their native coverage, and expose sensitivity to the two predeclared
> treatments of values above the nominal 500 scale.

Why this is a supportable rationale:

- The existing pipeline actually defines target dates, origins, horizons,
  lags, and date availability in
  [forecast_samples.py](forecast_samples.py) and
  [protocol.py](protocol.py).
- [temporal_splits.py](temporal_splits.py) assigns by target date and defines
  the development folds.
- [baselines.py](baselines.py) retains unavailable predictions, computes
  native coverage and common-case metrics, and fits climatology/Ridge within
  their permitted training data.
- [target_policies.py](target_policies.py) expresses separate `exclude` and
  `cap` analyses; neither claims to reconstruct historical AQI generation.
- The saved
  [run_record.json](results/20261010T101227Z-50924ef9974e/run_record.json)
  records development/2019 selection output. The approved folds include 2019
  in Ridge alpha selection, so the reported 2019 comparison is not an
  independent estimate.

This is a **project-specific methodological contribution candidate**. To
describe it as a gap in the field, the authors would need a reproducible
literature search and full-text comparison of comparable target definitions,
leads, input timing, data lineage, split design, and coverage reporting. That
work has not been completed.

## 3. Four distinct claim categories

| Category | Status in this project | Appropriate language |
|---|---|---|
| Established research problem | AQI forecasting appears in multiple reviewed Indian studies and in adjacent spatial forecasting literature. | “AQI forecasting has been studied using statistical and machine-learning approaches.” |
| Methodological design choice | Exact-date joins, target-date partitions, expanding folds, two target policies, coverage denominators, and common-case comparisons are design decisions implemented here. | “We define / apply / report…” Do not call a routine design choice novel without a literature comparison. |
| Project-specific contribution | An auditable implementation and one saved development/2019 selection comparison under the stated protocol, with native coverage and paired metrics. | “This study documents/evaluates these baselines on this hosted artifact under these rules.” Keep the 2019 qualification prominent. |
| Genuinely novel scientific contribution | **Not established.** The search is focused and several sources are abstract-level; the final test is unperformed. | Make no novelty, state-of-the-art, or broad generalization claim. |

## 4. Recommended research questions

Use two active questions. Treat policy differences descriptively because
`exclude` and `cap` induce different transformed outcomes and eligible
populations; they are not a causal treatment contrast.

### RQ1 — Selection-stage baseline profiles

**Question:** What development/model-selection error and native-coverage
profiles are observed for the approved direct-horizon baselines in 2019, by
horizon and target policy, and how do their errors compare on shared eligible
city/date cases?

**Answerability:** The saved run contains 2019 per-method coverage and
common-case MAE/RMSE for the policy/horizon combinations. This is answerable
as a description of the saved selection-stage run only. Because 2019 also
contributes to alpha selection, it cannot answer an independent performance
or generalization question.

### RQ2 — Target-policy sensitivity

**Question:** How do sample eligibility, method coverage, and 2019
selection-stage errors differ descriptively between the predeclared
`exclude` and `cap` policies?

**Answerability:** The run records both policies separately, including
valid-target denominators, prediction availability, and paired metrics.
Interpret these as policy-specific descriptions on different transformed
labels/eligible sets—not as the effect of a scientifically validated
correction or as a paired causal contrast.

### Exclude from active RQs

The existing manuscript's nonlinear-model RQ3 is out of scope under Option A.
It may be retained as a clearly labelled future-work question only if the
authors prefer; it must not appear as answered or as a current objective.
Operational warning efficacy, event detection, false alarms, health impact,
causal effects, unseen-city generalization, and final-test performance are
not answerable from the existing development run and should not be phrased as
current research questions.

## 5. Proposed contribution statements

These are precise contributions to the **study implementation and report**,
not claims of novelty or demonstrated superiority.

| Proposed statement | Supporting implementation/evidence | Qualification |
|---|---|---|
| 1. The study operationalizes direct 1-, 3-, and 7-calendar-day city-level AQI targets with exact-date target and lag construction and an explicit forecast-origin availability check. | [protocol.py](protocol.py), `HORIZONS_DAYS`, `AQI_LAGS_DAYS`, `PRIMARY_FEATURE_COLUMNS`; [forecast_samples.py](forecast_samples.py), `build_forecast_samples`; timestamp and exact-join tests. | Dataset AQI lineage remains unresolved; describe forecasts of the hosted file's AQI field, not a verified reconstruction of CPCB AQI. |
| 2. The study applies target-date training, development, and selection partitions with disjoint expanding development folds, while preserving 2019 as a selection-stage period. | [protocol.py](protocol.py), temporal boundaries; [temporal_splits.py](temporal_splits.py), `assign_partition`, `expanding_window_folds`, `split_fold`; saved run protocol and fold scores. | Do not describe 2019 as an independent test. The locked final period has not been evaluated. |
| 3. The comparison reports native prediction coverage and missingness alongside errors on the common eligible cases. | [baselines.py](baselines.py), prediction/evaluation and common-case metric functions; [coverage.py](coverage.py); saved record `validation.methods`, `common_case_count`, and `common_case_metrics`. | The metrics characterize only the saved 2019 selection-stage run. No statistical significance is established. |
| 4. The run documents policy-specific results under `exclude` and `cap` and records data/run identity and configuration while explicitly flagging values above 500 and unresolved provenance. | [target_policies.py](target_policies.py); [manifest.py](manifest.py); saved `run_record.json`; [DATA_PROVENANCE.md](DATA_PROVENANCE.md). | Kaggle version-12 identity and license label do not resolve upstream rights or historical AQI generation. The saved run's source fingerprint does not archive the exact historical source tree. |

The word “contribution” here means what the project provides and documents.
Whether these items are novel relative to published work remains unknown.

## 6. Claims that must not be made

- “First,” “novel,” “state of the art,” or “fills a field-wide gap” without a
  reproducible literature search and sufficiently comparable full-text
  review.
- Any claim that Ridge or another baseline is superior based on the 2019
  selection-stage metrics; no significance or paired uncertainty analysis
  exists.
- Final-test performance or confirmed generalization; the locked final test
  has not been scored.
- Transfer to unseen cities; temporal periods contain repeated city labels.
- That `exclude` or `cap` is the historically correct AQI calculation.
- That the Kaggle CC0 label establishes rights to upstream CPCB material or
  resolves the dataset's chain of custody.
- That the production AQI calculator generated the historical CSV AQI values.
- That the application's synthetic 24-hour profile or threshold alerts
  provide validated operational early warning.
- Event detection, false-alarm performance, lead-time utility, health benefit,
  causal effect, or operational effectiveness.
- That the saved run is independently reproducible solely from the Git
  revision/fingerprint; the research tree was untracked and the exact
  historical source snapshot is not preserved.

## 7. Conditions on future conclusions

Any performance statement that is intended to generalize beyond the 2019
selection period is conditional on separate approval and a one-time,
predeclared locked-test evaluation. Even such an evaluation would concern
temporal performance on cities represented in training; it would not, by
itself, establish unseen-city transfer, warning-event utility, statistical
superiority, health impact, or operational effectiveness.

Before submission, provenance and rights should be resolved or explicitly
bounded; reference [5]'s MSE/RMSE issue must remain unresolved unless reliable
full text/tables become available; Python 3.11 support or the research
runtime policy must be decided; and author affiliations/contact and
contribution metadata require author confirmation.
