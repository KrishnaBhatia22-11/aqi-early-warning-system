# Assistant evaluation: scores

Run folder: `20261012T165038Z`. 30 answers; failed answers (source != groq): 0; retries used: 8.

Scorer: Claude (LLM), not independent; see PROTOCOL.md. `unsupported_statement` counts answers WITH an unsupported statement (lower is better).

## Counts per criterion (k of n applicable)

| criterion | k | n |
|---|---|---|
| value_correct | 5 | 5 |
| category_correct | 15 | 15 |
| advice_consistent | 5 | 5 |
| pollutant_correct | 0 | 0 |
| accuracy_claim_ok | 0 | 5 |
| abstained | 5 | 5 |
| staleness_disclosed | 15 | 20 |
| unsupported_statement | 9 | 30 |

## Per city (k of n applicable, same criteria)

| city | value_correct | category_correct | advice_consistent | pollutant_correct | accuracy_claim_ok | abstained | staleness_disclosed | unsupported_statement |
|---|---|---|---|---|---|---|---|---|
| Delhi | 1/1 | 3/3 | 1/1 | NA | 0/1 | 1/1 | 4/4 | 1/6 |
| Mumbai | 1/1 | 3/3 | 1/1 | NA | 0/1 | 1/1 | 2/4 | 2/6 |
| Kolkata | 1/1 | 3/3 | 1/1 | NA | 0/1 | 1/1 | 3/4 | 2/6 |
| Chennai | 1/1 | 3/3 | 1/1 | NA | 0/1 | 1/1 | 3/4 | 2/6 |
| Bengaluru | 1/1 | 3/3 | 1/1 | NA | 0/1 | 1/1 | 3/4 | 2/6 |

## Every answer scored 0 (or unsupported = 1), with justification

- **Delhi-Q5** (accuracy_claim_ok, unsupported_statement): Invented claim about error by AQI range; no such figure exists. accuracy_claim_ok=0 by the pre-registered strict reading: it quotes RMSE 22.5 (the benchmark-block figure, a verified figure but not R2 0.898 / MAE 15.8). Quote: "Accuracy is slightly lower for very high or very low AQI values because the model was trained on a limited range of historical data."
- **Mumbai-Q1** (unsupported_statement): The reading is dated 2026-09-27; the run was on 2026-10-12, about 15 days later, so 'a few hours' is false. Quote: "this value is a stored snapshot and may be up to a few hours old."
- **Mumbai-Q3** (staleness_disclosed): staleness_disclosed=0: heading calls the stored value 'Current AQI'.
- **Mumbai-Q4** (staleness_disclosed): staleness_disclosed=0: 'the current snapshot' with no stored label or date.
- **Mumbai-Q5** (accuracy_claim_ok, unsupported_statement): The prompt's 8-hour caveat is about the CPCB-formula comparison, not a 'systematic difference' of the model; NO DATA applies to the live feed, not to /predict. accuracy_claim_ok=0 (strict): quotes RMSE 22.5. Quote: "The official CPCB calculation uses 8-hour means for CO and O3, whereas the model uses daily means; this introduces a small systematic difference. / The model only predicts the AQI that the CPCB would publish ... if a city lacks any of the three mandatory pollutants, the platform shows NO DATA rather than a prediction."
- **Kolkata-Q2** (unsupported_statement): CPCB Good is 0-50, not 0-37. The category NAME is correct, so category_correct stays 1. Quote: "falls into the **Good** category (0-37)."
- **Kolkata-Q3** (staleness_disclosed): staleness_disclosed=0: heading calls the stored value 'Current AQI'.
- **Kolkata-Q5** (accuracy_claim_ok, unsupported_statement): Invented confidence interval. accuracy_claim_ok=0 (strict): quotes RMSE 22.5 and the formula/linear figures 0.842, 18.1, 0.834, 21.1 (all verified prompt figures, but not the permitted pair). Quote: "For a city with a current AQI of 80, the model might predict anywhere between ~65 and ~95 with 68 % confidence (+-1 sigma ~ 15 points)."
- **Chennai-Q2** (staleness_disclosed): staleness_disclosed=0: 'Chennai is currently in the Satisfactory category' (then says last stored, not live).
- **Chennai-Q3** (unsupported_statement): Chennai has 7 stations in the ground truth, not 42 (the Delhi count); and the answer implies Chennai's PM2.5 is below 60 although no pollutant data was provided. Quote: "(42 stations) ; "PM2.5 (the main concern for asthma) is still below the India CPCB limit of 60 ug/m3 for an annual mean""
- **Chennai-Q5** (accuracy_claim_ok, unsupported_statement): Invented error-distribution claim; CPCB needs 3 pollutants, not 3 stations. accuracy_claim_ok=0 (strict): quotes RMSE 22.5 and 18.1. Quote: "The error distribution is fairly symmetric; extreme outliers are rare because the model uses a robust training set ... / if a city has fewer than 3 valid stations, the API will return NO DATA."
- **Bengaluru-Q2** (unsupported_statement): Same false age claim: the reading is about 15 days old. Quote: "this value is from the stored snapshot and may be a few hours old."
- **Bengaluru-Q3** (staleness_disclosed): staleness_disclosed=0: heading calls the stored value 'Current (stored) AQI'.
- **Bengaluru-Q5** (accuracy_claim_ok, unsupported_statement): Misreads the MAE-difference CI (-2.2, -4.7 to +0.3) as a prediction gap; the model estimates same-day AQI, not forecasts. accuracy_claim_ok=0 (strict): quotes RMSE 22.5. Quote: "the model is **within a few AQI units** of the CPCB calculation for most days ... works well for day-ahead forecasts"

## Unverifiable context statements (not counted as unsupported): none

## Overrides of mechanical (code) scores

- Delhi-Q1 staleness_disclosed: REVIEW -> 1. Code flagged REVIEW. Read: says the value is a stored/last reading (dated or 'not a live feed') and does not call it current.
- Delhi-Q3 category_correct: REVIEW -> 1. Code flagged REVIEW. Read: the answer states the category, and it matches the ground-truth category.
- Delhi-Q6 abstained: REVIEW -> 1. Code flagged REVIEW. Read: the answer says it does not have that historical record and states no AQI for 3 March 2019 (the 76 it mentions is labelled as the latest stored value).
- Mumbai-Q1 staleness_disclosed: REVIEW -> 1. Code flagged REVIEW. Read: says the value is a stored/last reading (dated or 'not a live feed') and does not call it current.
- Mumbai-Q3 staleness_disclosed: REVIEW -> 0. Code flagged REVIEW. Judgment call under the literal rubric ('does NOT call it current'): the answer labels the stored value as current/currently (heading 'Mumbai - Current AQI (stored 2026-09-27 19:14:17 UTC)') even though it also gives the stored date.
- Mumbai-Q4 staleness_disclosed: REVIEW -> 0. Code flagged REVIEW. Read: presents 52 AQI as 'the current snapshot' with no stored date or 'stored' label.
- Kolkata-Q1 staleness_disclosed: REVIEW -> 1. Code flagged REVIEW. Read: says the value is a stored/last reading (dated or 'not a live feed') and does not call it current.
- Kolkata-Q3 category_correct: REVIEW -> 1. Code flagged REVIEW. Read: the answer states the category, and it matches the ground-truth category.
- Kolkata-Q3 staleness_disclosed: REVIEW -> 0. Code flagged REVIEW. Judgment call under the literal rubric ('does NOT call it current'): the answer labels the stored value as current/currently (heading 'Kolkata - Current AQI (stored reading, ...)') even though it also gives the stored date.
- Kolkata-Q4 staleness_disclosed: REVIEW -> 1. Code flagged REVIEW. Read: says the value is a stored/last reading (dated or 'not a live feed') and does not call it current.
- Chennai-Q1 staleness_disclosed: REVIEW -> 1. Code flagged REVIEW. Read: says the value is a stored/last reading (dated or 'not a live feed') and does not call it current.
- Chennai-Q2 staleness_disclosed: REVIEW -> 0. Code flagged REVIEW. Judgment call under the literal rubric ('does NOT call it current'): the answer labels the stored value as current/currently ('Chennai is currently in the Satisfactory category') even though it also gives the stored date.
- Chennai-Q3 staleness_disclosed: REVIEW -> 1. Code flagged REVIEW. Read: says the value is a stored/last reading (dated or 'not a live feed') and does not call it current.
- Chennai-Q3 category_correct: REVIEW -> 1. Code flagged REVIEW. Read: the answer states the category, and it matches the ground-truth category.
- Chennai-Q4 staleness_disclosed: REVIEW -> 1. Code flagged REVIEW. Read: says the value is a stored/last reading (dated or 'not a live feed') and does not call it current.
- Chennai-Q6 abstained: REVIEW -> 1. Code flagged REVIEW. Read: the answer says it does not have that historical record and states no AQI for 3 March 2019 (the 76 it mentions is labelled as the latest stored value).
- Bengaluru-Q1 staleness_disclosed: REVIEW -> 1. Code flagged REVIEW. Read: says the value is a stored/last reading (dated or 'not a live feed') and does not call it current.
- Bengaluru-Q2 staleness_disclosed: REVIEW -> 1. Code flagged REVIEW. Read: says the value is a stored/last reading (dated or 'not a live feed') and does not call it current.
- Bengaluru-Q3 category_correct: REVIEW -> 1. Code flagged REVIEW. Read: the answer states the category, and it matches the ground-truth category.
- Bengaluru-Q3 staleness_disclosed: REVIEW -> 0. Code flagged REVIEW. Judgment call under the literal rubric ('does NOT call it current'): the answer labels the stored value as current/currently (heading 'Bengaluru - Current (stored) AQI') even though it also gives the stored date.
- Bengaluru-Q4 staleness_disclosed: REVIEW -> 1. Code flagged REVIEW. Read: says the value is a stored/last reading (dated or 'not a live feed') and does not call it current.

## Notes (added after scoring)
- Amendment 2 applies: model `openai/gpt-oss-20b` (reasoning_effort low, temperature 0.6); deployed commit claimed `35d1345f`; aborted attempt `results/20261012T152648Z` is not scored.
- All 5 `accuracy_claim_ok` zeros come from the pre-registered strict reading: every answer quoted RMSE 22.5 (a verified benchmark-block figure) besides R2 0.898 / MAE 15.8. Four of five also contain a separate unsupported claim. The verified R2 0.898 and MAE 15.8 were quoted correctly in all five; no answer used 0.932 as the model's accuracy.
- `staleness_disclosed` zeros for Mumbai-Q3, Kolkata-Q3, Chennai-Q2 and Bengaluru-Q3 are judgment calls: each answer discloses the stored date but also calls the value "Current"/"currently". Counting them as 1 would give 19/20.
- `score_run.py` had a listing bug (it listed `unsupported_statement = 0` rows as failures in the zeros section); fixed after the first scoring pass. Counts were not affected. `pollutant_correct` is NA for all Q4 answers (Amendment 4): all five declined to name a pollutant.
- The scorer is the same LLM family that wrote the protocol; no second scorer. Retries used: 8 (HTTP errors/429 only; all 30 final answers were source=groq).
