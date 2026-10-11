# Experiment Decision Memo

**Decision requested:** Choose between a baseline-only paper and a paper that
adds one nonlinear tree family. No model was implemented, fitted, tuned, or
scored for this memo.

## Recommendation

**Recommend Option A: baseline-only.** It is the smallest defensible scope
for the already implemented study and directly supports questions about
simple, interpretable forecast baselines, coverage, shared eligible cases,
and sensitivity to the two declared target policies. The saved 2019 results
remain selection-stage evidence, not an independent estimate. A separately
authorized, one-time evaluation on the locked period is still required
before making confirmatory performance claims or asserting superiority.

Option B can be scientifically useful if the authors explicitly want to test
whether nonlinear interactions among the same seven features add value.
However, adding a model does not resolve the source-provenance, runtime,
2019-selection, or final-test limitations. It adds model-selection degrees
of freedom and implementation/testing burden without answering a distinct
question unless that nonlinear comparison is itself a planned research
question.

## Scope comparison

| Dimension | Option A — baseline-only | Option B — baselines plus one nonlinear model |
|---|---|---|
| Scientific value | Clear and interpretable benchmark of persistence, annual exact-date naive, training-only climatology, weekly naive at horizons 1/3, and Ridge; emphasizes coverage and policy sensitivity | Tests whether a single nonlinear learner can exploit interactions in the approved AQI/calendar predictors beyond linear Ridge and simple baselines |
| Research question | Keep RQ1/RQ2: development/selection-stage baseline profiles and differences between `exclude`/`cap` | Add a bounded question: whether a predeclared nonlinear candidate selected on the existing folds changes development/selection results versus baselines; reserve performance claims for the separately authorized final test |
| Feature fairness | Existing seven-feature Ridge versus deterministic baselines | Use exactly the same seven primary features for HistGradientBoostingRegressor; no city ID, pollutants, or future values |
| Hyperparameter selection | Existing Ridge alpha rule: equal-weight fold MAE on 2017/2018/2019; alpha tie selects larger value | Candidate grid below; equal-weight mean fold MAE on those same three folds; ties choose fewer leaves, then fewer iterations; 2019 remains selection-stage |
| Computational burden | Historical experiments already run; no new fits in this decision task | Four candidates × three folds × six policy/horizon configurations = **72 selection fits**, plus six selected-model fits on 2015–2018 if performing 2019 development evaluation: **78 planned fits**. Actual runtime is unknown and was not benchmarked. |
| Implementation effort | No new estimator implementation; mostly evidence curation and eventual separately authorized final evaluation | Planning estimate: approximately 1–2 focused engineering days for implementation, reproducibility metadata, and synthetic tests; excludes any literature/provenance work and is not a measured commitment |
| Required tests | Safe test subset and later authorized baseline/model evaluation checks | Seven-feature schema; train-only fitting; disjoint expanding folds; deterministic candidate selection and tie handling; policy/horizon identity; missing-feature behavior, exclusion reasons, and coverage; common-case comparison; no post-2019 history handoff; repeated deterministic settings |
| Main risks | 2019 used for selection; no independent result until locked evaluation; simple baseline scope may be less broad than some venues expect | Added complexity and selection burden; 2019 is not independent; no automatic superiority; tuning leakage/incorrect tie rule; missing features/coverage comparability; small gain may not justify model |
| Effect on paper | Keeps the paper focused on auditable baselines; claims remain modest | Expands Methods/Results/RQ and increases experiment documentation; paper must distinguish nonlinear model selection from final evaluation |

## Option B — proposed specification, not authorization

One direct-horizon `HistGradientBoostingRegressor` per policy/horizon with
the exact seven approved inputs:

| `max_iter` | `max_leaf_nodes` |
|---:|---:|
| 100 | 7 |
| 100 | 15 |
| 250 | 7 |
| 250 | 15 |

Fixed settings: `learning_rate=0.05`, `min_samples_leaf=20`,
`l2_regularization=1.0`, `early_stopping=False`, `random_state=0`.
Selection: equal-weight mean MAE across the existing expanding validation
folds for 2017, 2018, and 2019; exact ties prefer fewer leaf nodes, then
fewer iterations. Do not alter folds, features, eligibility, policies, or
locked test boundaries. If later authorized, report 2019 strictly as
selection-stage evaluation and assess models on common eligible cases while
also reporting native coverage.

These are proposed settings only. No code, predictions, scores, or candidate
selection results have been created.

## Decision gate

Option A is recommended unless the authors specifically need a nonlinear
model question for the intended publication. Before either future fitting
stage, freeze a versioned source snapshot, resolve or explicitly bound data
rights/provenance and Python support, and obtain human approval. Any locked
test evaluation requires its own explicit approval and must occur only after
all method choices are frozen.

The current v2.1 manuscript already labels RQ3 as a future nonlinear
extension. If Option A is selected, retain that only as clearly deferred
future work or remove it from the active research questions after author
approval; do not write it as a question answered by the current results.
