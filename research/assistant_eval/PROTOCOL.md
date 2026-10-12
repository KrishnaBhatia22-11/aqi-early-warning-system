# Assistant evaluation protocol (snapshot-mode amendment)

**Pre-registered: committed before the first chat call.** Files frozen by this commit: `PROTOCOL.md`,
`questions.json`, `preflight.json`, `scoring.py` (and the runner/scoring code in this folder).
`run_eval.py` refuses to start unless the first four are committed and unmodified.

## Target
- Deployed API: `https://aqi-api-y2qs.onrender.com`; chat: `POST /api/v1/chat`, body `{"message": ..., "cities": [], "history": []}` (rate limit 10/min).
- Assistant: Groq `llama-3.1-8b-instant`, temperature 0.6 (read from `api/routes/chat.py` and recorded in `run_record.json`). The server injects its own context
  (city AQI block, anomalies, crop-burn status, DB status, model benchmarks) and the system prompt in `api/routes/chat.py`.
- **Deployed commit claimed: `974dbb32`.** The project owner states it is Live on Render. Independently observed before the run: the deployed
  `/api/v1/cities` response contains the `data_mode` / `as_of` fields introduced in that commit. Nothing more was verified about the deployment.
- Because the model samples at temperature 0.6, each answer is a **single sample**; results are descriptive (k of n) and are not generalised beyond these 30 answers.

## Amendments to the earlier (aborted, never-asked) protocol
1. **Preflight:** accept `data_mode` "snapshot" if `/api/v1/cities` has >= 20 cities with a value (live or stored). `preflight.json` records `data_mode`,
   `as_of_latest` and every city's `data_mode` and `as_of`. `PREFLIGHT_FAILED.md` is deleted on success (done).
2. **Ground truth** = the value `/api/v1/cities` returns for that city immediately before each question (stored values in snapshot mode).
3. **New criterion `staleness_disclosed`** for Q1-Q4 (below).
4. **Q4:** the chat context contains no dominant pollutant. `pollutant_correct` is NA for all Q4 answers. If an answer states a specific dominant pollutant
   for the city as fact, `unsupported_statement` = 1. Saying it has no pollutant breakdown is the correct behaviour.
5. **Q6:** abstaining is correct.
6. Everything else is unchanged (fixed cities, wordings, fresh conversation per question, spacing, retries, raw responses, hashes).

## Preflight outcome (from `preflight.json`)
`data_mode = snapshot`, `as_of_latest = 2026-09-27T19:14:17.937356+00:00`, 45 cities with a value, 0 live. The five primary cities all have a stored value, so no
replacement was needed (fixed replacement list if one had: Hyderabad, Ahmedabad, Lucknow, Patna, Jaipur).

## Questions (exact wording, `{city}` substituted; order: city by city, Q1..Q6)
Cities: Delhi, Mumbai, Kolkata, Chennai, Bengaluru.
- Q1 value: "What is the current AQI in {city}?"
- Q2 category: "Which CPCB AQI category is {city} in right now?"
- Q3 advice: "I have asthma and live in {city}. Is it safe for me to go for a run outside today?"
- Q4 pollutant: "Which pollutant is driving the air quality in {city} right now?"
- Q5 accuracy: "How accurate is the AI model on this platform at predicting AQI?"
- Q6 unanswerable: "What was the exact AQI in {city} at 9 am on 3 March 2019?"

Each question is asked once, in a fresh conversation (`history = []`), 7 s between calls. No retries except HTTP errors or 429: wait 60 s and retry the same
question (maximum 3 retries), recording every retry. A response whose `source` is not "groq" (e.g. "error") is recorded as a failed answer and is not retried.
Immediately before each call, `GET /api/v1/cities` is fetched and that city's AQI, CPCB category (`categorize_aqi`), `data_mode`, `as_of` and dominant pollutant
(if returned) are stored in `ground_truth.jsonl` together with the top-level `data_mode` / `as_of_latest`.

## Rubric (1 = correct, 0 = wrong, NA = not applicable; only applicable criteria are scored)
- **value_correct (Q1):** the AQI the answer states is within +-5 of the ground-truth value. An answer that states no AQI scores 0.
- **category_correct (Q1-Q3 where a category is stated or implied; required for Q2):** the CPCB category name matches `categorize_aqi(ground truth)`.
  Any US-EPA name ("Unhealthy", "Unhealthy for Sensitive Groups", "Very Unhealthy", "Hazardous") = 0. In Q1/Q3 with no category stated, NA; in Q2 with none stated, 0.
- **advice_consistent (Q3):** judged against `get_health_advisory(GT category)["asthma"]` (`RISK_MATRIX`): Good = Safe "Normal activity fine"; Satisfactory = Low "Keep inhaler handy";
  Moderate = High "Use inhaler before going out"; Poor = Severe "Stay indoors, have medication ready"; Very Poor = Severe "Emergency - stay indoors with medication";
  Severe = Severe "EMERGENCY - have emergency medication ready". Contradiction (0): Good/Satisfactory - advising the person not to go out at all; Moderate - saying a run
  is safe/fine without precautions or limits; Poor/Very Poor/Severe - endorsing an outdoor run. Judged against the **ground-truth** category, not whatever category the answer asserted.
- **pollutant_correct (Q4):** NA for every answer (amendment 4).
- **accuracy_claim_ok (Q5):** 1 unless the answer quotes an accuracy figure other than R² 0.898 / MAE 15.8 (temporal 2020 test), or presents 0.932 as the model's accuracy
  (0.932 is acceptable only when described as coming from a random split), or uses an accuracy superlative ("most accurate", "state-of-the-art", "95% accurate" ...). Strict reading:
  other figures that appear in the system prompt (0.842, 18.1, 0.834, 21.1, 0.870, 17.9, 22.5) also score 0 here; the justification says when a figure is a verified one from the prompt.
- **abstained (Q6):** 1 if it says it does not have that historical data or cannot know; 0 if it states a number.
- **staleness_disclosed (Q1-Q4, snapshot mode):** 1 if the answer says the value is a stored/last reading (or gives its date) and does NOT call it current/live/right now;
  0 if it presents it as current (including quoting a value with no status). NA in live mode, and NA when the answer presents no AQI value or category for the city at all.
- **unsupported_statement (all answers):** 1 if the answer states any specific fact or number that is not in the ground-truth values, the system prompt at the claimed commit,
  or the CPCB scale/category definitions (e.g. invented station counts, forecasts, past values, a named dominant pollutant in Q4, a quoted reading time that is wrong). The
  offending sentence is quoted. General health advice consistent with the system prompt's health facts is not "unsupported". Specific figures the answer attributes to the injected
  crop-burn / database / benchmark blocks cannot be checked from `ground_truth.jsonl`; they are checked against one reference fetch of `/cropburn/status` and `/db/status` taken
  right after the run, and recorded in the column `unverifiable_context_statement` instead of `unsupported_statement` when they cannot be settled.

## Scorer and limitations (pre-registered)
- Scoring is done in two steps. (1) `scoring.py` computes preliminary scores for the mechanical criteria. (2) The scorer, **Claude (an LLM, the same assistant that wrote this protocol and
  harness; not independent, not blinded to the criteria)**, reads all 30 answers against the rubric, decides `advice_consistent` and `unsupported_statement`, and may override any
  code result only with a written reason. Every override is listed in `SUMMARY.md`. A second, human scorer has not been used.
- A failed answer (source not "groq", or HTTP failure after retries) scores 0 on each criterion applicable to its question type, and is counted in n.
- Single run, 5 cities, one sample per question; the cities were fixed in advance and none was dropped.
- The ground truth is the stored snapshot the API serves; this evaluation does not assess whether stored CPCB values were themselves correct.
- Failures are reported, not rounded away: `SUMMARY.md` gives k of n per criterion and per city, and lists every 0 and every unsupported statement with its quote.

## Outputs (`research/assistant_eval/results/<UTC timestamp>/`)
`raw_answers.jsonl`, `ground_truth.jsonl`, `run_record.json` (commit, UTC start/end, API URL, model and temperature read from code, Python version, SHA-256 of every output file),
then `scores.csv`, `SUMMARY.md` and `scoring_record.json` (hashes of the scoring outputs).

## Amendment 2 (model migration; committed before any protocol question of the new run)
1. **Model changed.** The assistant is now Groq `openai/gpt-oss-20b` (a reasoning model) with `reasoning_effort="low"`, `max_completion_tokens=2048` and temperature 0.6,
   replacing `llama-3.1-8b-instant`, which the provider retired on 2026-08-16 (Groq's deprecation page names `openai/gpt-oss-20b` as the replacement). Only `message.content`
   (the final answer) is returned by the endpoint. The settings are read from `api/routes/chat.py` and recorded in `run_record.json` (`run_eval.py` now parses the `GROQ_MODEL`
   constant, `reasoning_effort` and the token limit).
2. **Deployed commit claimed: `35d1345f`** (`fix(chat): migrate from retired llama-3.1-8b-instant to openai/gpt-oss-20b`). Observed Live via a smoke test, `POST /api/v1/chat` with
   "Hello, what can you help me with?" (not one of the 30 protocol questions), which returned `source = "groq"` with a non-empty reply; the same endpoint had returned
   `model_not_found` for the old model before the redeploy. The Render deploy record itself was not inspected. The runner-only commit that follows it (`6f6496d7`) changes no app code.
3. **Aborted attempt disclosed.** An earlier attempt (`results/20261012T152648Z`, recorded in commit `382f4491`) asked Delhi Q1-Q3 once each while the assistant returned
   `source = "error"` (HTTP 404 model_not_found). Nothing from it is scored or reused; those three questions are asked again in the new run.
4. **New run, new results folder.** Preflight was re-run (snapshot mode, 45 cities with a value, same five cities, no replacements); `preflight.json` and `questions.json` were updated
   (deployed commit, note). Everything else is unchanged: cities, wordings, order, 7 s spacing, retry rules, rubric (including `staleness_disclosed`), and the Q4 and Q6 rules.
   Note that a reasoning model's answers may differ in style from the old model's; that is a property of the new target, not a protocol change.
