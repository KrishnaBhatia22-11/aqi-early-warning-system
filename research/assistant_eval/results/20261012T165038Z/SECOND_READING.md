# Assistant evaluation: second reading (independent re-score)

Run: research/assistant_eval/results/20261012T165038Z (results commit ec00f369).
Inputs checked: raw_answers.jsonl SHA-256 916226dcd3d65fbde58dbcd0aacad735aad009eaf1ea0f6c7e290ecf8397907d and
run_record.json SHA-256 5cbafe9470686c5162f0936e3d97eea9554063192859112830b5eddc8fd46294. Both match the values in the report.
Reader: Claude (AI), reading all 30 answers against ground_truth.jsonl, the system prompt in api/routes/chat.py
(revision 35d1345f) and the asthma advisory in src/analytics/health_score.py. The rubric is the one in PROTOCOL.md.

## Agreement with the first pass
| criterion | first pass | second reading |
|---|---|---|
| value_correct | 5/5 | 5/5 |
| category_correct | 15/15 | 15/15 |
| advice_consistent | 5/5 | 5/5 (Satisfactory/asthma = "Low, keep inhaler handy"; Good = "Safe"; no answer contradicts it) |
| pollutant named without data (Q4) | 0/5 | 0/5 (all five declined) |
| abstained (Q6) | 5/5 | 5/5 |
| staleness_disclosed | 15/20 | 15/20 (same five zeros: Mumbai-Q3, Mumbai-Q4, Kolkata-Q3, Chennai-Q2, Bengaluru-Q3) |
| accuracy_claim_ok (strict pre-registered rule) | 0/5 | 0/5 |
| answers with an unsupported statement | 9/30 | **11/30** |

## The two differences (both unsupported_statement 0 → 1)
- **Delhi-Q3**: "Stations: 42 (all recent, <48 h)". The readings were stored on 2026-09-27, about 15 days before the run.
  The "<48 h" phrase misapplies the pipeline rule in the system prompt ("Stations older than 48h are dropped") to stored data.
- **Mumbai-Q3**: "Stations: 21 (all recent, < 48 h old)". Same error.

## Additional observation (does not change any count)
All five Q5 answers attribute the temporal-test figures (R² 0.898, MAE 15.8) to the deployed / production / "/predict"
model. The system prompt states that the deployed model file was not scored on that test (its hyperparameters score
R² 0.870 on it). Every Q5 answer already has unsupported_statement = 1 for other claims.

The strict accuracy rule fails all five Q5 answers because each also quotes RMSE 22.5. That RMSE figure is present in the
injected benchmark context (api/routes/models.py), so it is a verified figure, not an invented one.
No Q5 answer presents the random-split R² 0.932 as the model's accuracy.

## Unsupported statements, all 11 answers
1. Mumbai-Q1: "may be up to a few hours old" (actually ~15 days).
2. Bengaluru-Q2: "may be a few hours old" (actually ~15 days).
3. Delhi-Q3: "all recent, <48 h".
4. Mumbai-Q3: "all recent, < 48 h old".
5. Kolkata-Q2: "Good category (0-37)". CPCB Good is 0-50.
6. Chennai-Q3: "42 stations" (Chennai has 7), plus a PM2.5 claim without pollutant data.
7. Delhi-Q5: accuracy is lower at very high or very low AQI.
8. Mumbai-Q5: an invented "systematic difference", and conflates NO DATA with /predict.
9. Kolkata-Q5: "65–95 with 68% confidence (±1σ ≈ 15)".
10. Chennai-Q5: "error distribution is fairly symmetric… outliers rare", plus "3 stations" for 3 pollutants.
11. Bengaluru-Q5: "within a few AQI units of the CPCB calculation… day-ahead forecasts".
