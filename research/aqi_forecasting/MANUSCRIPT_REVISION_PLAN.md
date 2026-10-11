# Manuscript Revision Plan — Phase 1

**Decision:** Baseline-only paper.  
**Purpose:** Editorial plan for author review; this document does not replace
or revise the manuscript. No protocol, result, citation, or author metadata
is changed by this plan.

## Editorial plan

| Current section | Problem / weakness | Proposed improvement | Evidence needed | Priority | Scientific decision or author confirmation? |
|---|---|---|---|---|---|
| Title and author block | Title names the baseline scope appropriately, but should not imply operational early-warning validation. Author affiliations and contact metadata are incomplete. | Retain the working title unless authors select a venue-driven alternative. Keep the exact approved author order; use placeholders until details are confirmed. | Approved author order; actual confirmed affiliations, emails, titles, ORCIDs, and contribution statements | High | Yes: author metadata and venue formatting |
| Abstract | Current abstract includes selection-stage Ridge results and a clear no-test caveat, but is relatively long and contains a future test requirement that may not belong in a submission abstract. | Structure around context, narrowly stated objective, data artifact/protocol, baseline families, key verified 2019 selection-stage findings, and limitations. Label every 2019 metric as selection-stage. State that no final-test results are available and avoid operational language. Remove editorial workflow text from a submission-ready abstract; preserve the no-test fact until any separately authorized final stage. | Saved `run_record.json`; verified dataset/protocol; final choice on whether paper remains a development-only methods/benchmark report | High | Yes: whether to submit a pre-final-test development paper |
| Introduction — problem statement | The manuscript correctly distinguishes retrospective prediction from early warning, but can more directly motivate why exact targets and availability matter in a daily city panel. | Explain that calendar gaps, unavailable origins/lags, changing eligibility, and different policy-transformed targets can make headline errors incomparable. Frame the need as careful evaluation for this artifact, not proof that the literature ignores these issues. | Existing sample builder, target policies, missingness and coverage summaries; literature full-text review for any comparative claim | High | No, provided claims stay artifact-specific |
| Introduction — motivation | Rationale can overfocus on technical safeguards without stating their practical analytical value. | Emphasize interpretable baselines as reference points and coverage as necessary context: a low error on a restricted subset and a broader-coverage error answer different questions. Do not claim direct public-health/operational utility. | `baselines.py`, coverage and common-case metrics; saved 2019 denominators | High | No |
| Related work / research gap | Current review is explicitly focused and partly abstract-level. It does not establish a field-wide gap or novelty. | Summarize only verified method families and their evidence level. State that exact cross-study comparability is undetermined. Present the study's motivation as a project-specific protocol/reporting contribution, not “first” or “novel.” | Full texts/supplements and a reproducible literature search if making a gap claim; see [LITERATURE_MATRIX_v2.md](LITERATURE_MATRIX_v2.md) | Critical | Yes, if authors seek a novelty claim |
| Objectives | Current framing can conflate broad system aims with the narrower research experiment. | State one objective: describe how the approved baseline set performs on the hosted city-day AQI field under fixed direct horizons, target policies, and temporal-selection rules, with coverage and common-case errors. Explicitly exclude evaluating the deployed application. | `protocol.py`, saved run record | High | No |
| Research questions | Current RQ3 proposes a nonlinear experiment even though the approved choice is Option A. RQ2 could imply a causal contrast between different eligibility/target sets. | Retain two active descriptive RQs: (1) 2019 selection-stage baseline error/coverage by policy and horizon on native and common cases; (2) descriptive differences in eligibility, coverage, and selection-stage errors between `exclude` and `cap`. Remove RQ3 from active questions or clearly label it as future work. | Run record's six development entries and policy-specific denominators; no additional model evidence | High | Yes: authors choose remove vs explicit future-work mention |
| Contribution paragraph | Phrases such as “contribution” can be mistaken for field-level novelty. | Use 3–4 bounded statements: exact-calendar direct-horizon construction and availability rules; temporal selection protocol; native coverage plus common-case errors; policy sensitivity and run/data limitations recorded transparently. Describe these as project-specific study contributions and say novelty is unestablished. | Forecast sample, split, baseline, coverage, manifest, provenance code/docs and saved artifact | High | No, unless authors decide to claim novelty |
| Paper organization | Should direct readers without restating the whole method or promising an unperformed final evaluation. | End the introduction with a short map of sections actually present. Avoid promising a final-test-results section as if results exist; retain a clearly marked pending stage only in working documents if needed. | Current manuscript section structure and Option A decision | Medium | No |
| Dataset and provenance | Kaggle v12 match and displayed CC0 label do not establish upstream CPCB rights, transformation lineage, station aggregation, or AQI construction. | Attribute the analyzed artifact precisely; separate verified local identity, previously documented Kaggle match/metadata, official CPCB methodology context, and unresolved upstream rights/lineage. Explicitly identify 543 values above 500 as a data-quality issue without asserting why they occur. | [DATA_PROVENANCE.md](DATA_PROVENANCE.md); source/archive/license evidence if obtained | Critical | Yes: whether unresolved legal/data validity is acceptable for target venue |
| Methodology and temporal validation | Current design is clear, but language should distinguish what was executed in the saved run from the later runner hardening. | State exact horizon/lag joins, target-date partitions, three expanding folds, policy definitions, and test status. Explain that current code hands only pre-2020 history to baseline evaluation, but the saved run predates that fix; do not imply a rerun. | `protocol.py`, `forecast_samples.py`, `temporal_splits.py`, `run_development.py`, mocked handoff test, saved artifact | High | No |
| Results | 2019 values are selection-stage because 2019 enters alpha selection. Coverage and common-case denominators must remain visible. | Keep the 2019 tables explicitly labelled development/model-selection. Report target policy, horizon, common-case count, valid-target denominator, method coverage, and missing predictions. Do not rank a best method or claim significance. Keep final-test results explicitly absent. | Saved record `ridge_selection`, `validation.methods`, `common_case_count`, and `common_case_metrics`; existing audit cross-check | Critical | Yes: whether to present development-only numbers as paper results |
| Discussion | Interpretations could drift toward superiority or operational relevance. | Discuss observed method/policy-specific error and coverage only. Explain different policy labels/eligible cases and annual-naïve availability. Separate an evaluation result from implications for alerting, health, or deployment. | Saved selection-stage run; target-policy definitions; literature review depth | High | No |
| Limitations and threats to validity | Several material blockers: selected 2019 period, no final test, same cities across temporal splits, uncertain dataset lineage/rights, above-range values, Python mismatch, and unrecoverable historical source snapshot. | Preserve these as explicit limitations. State full test rows were read for audit/date parsing even though the saved record reports no test prediction/scoring use. State current handoff hardening separately from the historical run. | Run record/log hashes, current runner/test, `DATA_PROVENANCE.md`, `runtime.txt`, dependency pins, archive manifest | Critical | Yes: author acceptance of unresolved provenance/runtime limits |
| Conclusion and future work | A conclusion can overstate practical promise before independent evaluation. | Conclude only that the artifact supports an auditable baseline comparison and descriptive 2019 selection-stage results. Future work may include provenance resolution, supported-runtime validation, locked test by separate approval, and warning-event evaluation; none should be implied as completed. | Existing record and listed blockers | Critical | Yes: final-test approval is a separate decision |
| References | Ref. [3] full text is unreviewed; ref. [5] metric discrepancy is unresolved; literature search is non-systematic. | Keep abstract-level qualifiers, do not quote unresolved metric pairs, and do not claim comprehensive coverage. Verify all citation details and source claims before submission. | Publisher/full texts/reliable tables and reproducible search log | High | Yes: access and citation sign-off |
| Production/research distinction throughout | Production same-time pollutant regression, formula-based 24-hour profile, and threshold alerts can be mistaken for the research direct-horizon forecast experiment. | Retain a concise distinction and avoid using application features as evidence of research performance or warning effectiveness. | `src/models/train.py`, `api/routes/forecast.py`, `api/scheduler.py`, `src/data/india_aqi.py` | High | No |

## Abstract and introduction narrative sequence

1. **Problem:** AQI forecasting is established, but a daily city record alone
   does not define a forecast; target date, forecast origin, available
   observations, and the evaluation split matter.
2. **Motivation:** Simple baselines make reference points for short horizons;
   unavailable predictions and policy-specific eligible populations mean
   error without coverage is incomplete.
3. **Study objective:** Evaluate the existing direct-horizon baseline set on
   this hosted multi-city dataset under the fixed seven-feature and temporal
   protocol.
4. **Research questions:** Use the two descriptive questions above. Keep
   `exclude` versus `cap` as sensitivity analyses, not a causal comparison.
5. **Evidence statement:** Any reported 2019 findings are selection-stage
   summaries. The final test remains unevaluated.
6. **Boundary:** This is retrospective AQI prediction, not an evaluation of
   the production 24-hour profile, warnings, event detection, false alarms,
   health outcomes, or risk-zone effectiveness.
7. **Contribution and organization:** Identify the implementation/reporting
   contributions, explicitly disclaim field-level novelty, and briefly map
   the paper's sections.

## Evidence and decision gates before manuscript editing

- Do not edit the manuscript in this phase; the user requested planning
  documents only.
- A final abstract claiming generalization or model ranking requires a
  separately approved locked-test phase after methods are fixed; even then,
  it would not establish unseen-city generalization or operational warning
  efficacy.
- A field-wide novelty or “gap” statement requires a reproducible literature
  search and full-text comparison, not only the present matrix.
- Submission requires a human decision about unresolved upstream data rights
  and lineage, plus author confirmation of affiliations, contact details,
  identifiers, and contributions.
- Do not run the development experiment, fit an estimator, run
  `test_baselines.py`, or access final-test outcome records as part of this
  editorial phase.
