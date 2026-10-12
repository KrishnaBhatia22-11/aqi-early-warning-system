# Results summary — run 20261012T135944Z-6e220f0c

Every table below is rendered directly from the CSV named in its heading (paths relative to this folder).

## Method notes (fixed text)

- Features: 9 pollutants (PM2.5, PM10, NO, NO2, NOx, NH3, CO, SO2, O3). The deployed artifact also used
  Year/Month/Season_Code and train+test-wide median imputation; this study uses neither (raw NaNs,
  XGBoost native handling; linear regression uses training-set medians).
- Rows: city_day.csv with recorded AQI in [0, 500]; rows with AQI > 500 are excluded (the deployed pipeline clipped them to 500).
- Split: train 2015-01-01..2018-12-31, select on 2019, test 2020-01-01..2020-07-01. Models are NOT refit on 2019.
- Formula baseline: CPCB breakpoints on daily means; CO and O3 use daily means, not 8-hour means (approximation).
  Computable only with >=3 of 7 pollutants including PM2.5 or PM10. "Common cases" = rows where it is computable.
- Bootstrap: resample whole cities, 2000 replicates, seed 20200101, percentile 95% CI.
- Category macro-F1 averages over categories present in truth or prediction. Event > threshold: POD=hits/(hits+misses),
  FAR=false alarms/(hits+false alarms), CSI=hits/(hits+misses+false alarms).
- Step 3 agreement: strict compares top-|SHAP| pollutant (any of 9 features) with the formula's dominant pollutant;
  the restricted variant only considers the 7 formula pollutants (NO/NOx excluded) when picking the top SHAP feature.
- Years 2015-2020 data were already used by the separate forecasting study; its results folder is untouched.

## tables/dev_validation_2019.csv

| model | subset | n | MAE | RMSE | R2 |
|---|---|---|---|---|---|
| xgb_deployed_config | all_val_rows | 6915 | 19.0910 | 28.2843 | 0.9126 |
| xgb_deployed_config | formula_computable_rows | 6905 | 19.0391 | 28.1424 | 0.9135 |
| xgb_selected | all_val_rows | 6915 | 17.4690 | 25.9579 | 0.9264 |
| xgb_selected | formula_computable_rows | 6905 | 17.4157 | 25.7987 | 0.9273 |
| linear | all_val_rows | 6915 | 25.1776 | 36.8421 | 0.8518 |
| linear | formula_computable_rows | 6905 | 25.1158 | 36.7417 | 0.8526 |
| cpcb_formula | formula_computable_rows | 6905 | 20.9536 | 32.1674 | 0.8870 |

## tables/dev_xgb_grid_2019.csv

| max_depth | n_estimators | learning_rate | subsample | val_MAE | val_RMSE | val_R2 |
|---|---|---|---|---|---|---|
| 3 | 200 | 0.0500 | 0.8000 | 18.0656 | 26.6647 | 0.9223 |
| 3 | 200 | 0.1000 | 0.8000 | 18.1384 | 26.8113 | 0.9215 |
| 3 | 400 | 0.0500 | 0.8000 | 18.0807 | 26.4487 | 0.9236 |
| 3 | 400 | 0.1000 | 0.8000 | 18.2774 | 26.9295 | 0.9208 |
| 5 | 200 | 0.0500 | 0.8000 | 17.4690 | 25.9579 | 0.9264 |
| 5 | 200 | 0.1000 | 0.8000 | 18.1811 | 26.7174 | 0.9220 |
| 5 | 400 | 0.0500 | 0.8000 | 17.8194 | 26.2925 | 0.9245 |
| 5 | 400 | 0.1000 | 0.8000 | 18.7283 | 27.2778 | 0.9187 |
| 8 | 200 | 0.0500 | 0.8000 | 18.6256 | 28.1443 | 0.9135 |
| 8 | 200 | 0.1000 | 0.8000 | 19.0910 | 28.2843 | 0.9126 |
| 8 | 400 | 0.0500 | 0.8000 | 19.1402 | 28.5915 | 0.9107 |
| 8 | 400 | 0.1000 | 0.8000 | 19.5448 | 28.7384 | 0.9098 |

## tables/step1_coverage.csv

| model | rows_total | rows_predicted | coverage |
|---|---|---|---|
| xgb_deployed_config | 4404 | 4404 | 1.0000 |
| xgb_selected | 4404 | 4404 | 1.0000 |
| linear | 4404 | 4404 | 1.0000 |
| cpcb_formula | 4404 | 4397 | 0.9984 |

## tables/step1_metrics_bootstrap_ci.csv

| subset | model | metric | estimate | ci_low | ci_high | n_rows | n_cities | reps | seed |
|---|---|---|---|---|---|---|---|---|---|
| common_cases_formula_computable | xgb_deployed_config | MAE | 17.8890 | 15.5653 | 20.4110 | 4397 | 26 | 2000 | 20200101 |
| common_cases_formula_computable | xgb_deployed_config | RMSE | 25.3820 | 21.5740 | 29.4978 | 4397 | 26 | 2000 | 20200101 |
| common_cases_formula_computable | xgb_deployed_config | R2 | 0.8698 | 0.8062 | 0.9017 | 4397 | 26 | 2000 | 20200101 |
| common_cases_formula_computable | xgb_selected | MAE | 15.8334 | 13.8167 | 18.1126 | 4397 | 26 | 2000 | 20200101 |
| common_cases_formula_computable | xgb_selected | RMSE | 22.5108 | 19.1010 | 26.3065 | 4397 | 26 | 2000 | 20200101 |
| common_cases_formula_computable | xgb_selected | R2 | 0.8976 | 0.8607 | 0.9198 | 4397 | 26 | 2000 | 20200101 |
| common_cases_formula_computable | linear | MAE | 21.1390 | 18.8233 | 23.6513 | 4397 | 26 | 2000 | 20200101 |
| common_cases_formula_computable | linear | RMSE | 28.6828 | 24.4464 | 33.4006 | 4397 | 26 | 2000 | 20200101 |
| common_cases_formula_computable | linear | R2 | 0.8338 | 0.7748 | 0.8689 | 4397 | 26 | 2000 | 20200101 |
| common_cases_formula_computable | cpcb_formula | MAE | 18.0673 | 14.8015 | 22.0594 | 4397 | 26 | 2000 | 20200101 |
| common_cases_formula_computable | cpcb_formula | RMSE | 27.9557 | 21.7312 | 34.8422 | 4397 | 26 | 2000 | 20200101 |
| common_cases_formula_computable | cpcb_formula | R2 | 0.8421 | 0.7649 | 0.8982 | 4397 | 26 | 2000 | 20200101 |
| common_cases_formula_computable | xgb_selected minus cpcb_formula | MAE_difference | -2.2339 | -4.7169 | 0.2958 | 4397 | 26 | 2000 | 20200101 |
| common_cases_formula_computable | xgb_selected minus linear | MAE_difference | -5.3056 | -6.6540 | -3.9107 | 4397 | 26 | 2000 | 20200101 |
| common_cases_formula_computable | linear minus cpcb_formula | MAE_difference | 3.0717 | 0.1749 | 5.8479 | 4397 | 26 | 2000 | 20200101 |
| all_test_rows | xgb_deployed_config | MAE | 17.9218 | 15.5992 | 20.4541 | 4404 | 26 | 2000 | 20200101 |
| all_test_rows | xgb_deployed_config | RMSE | 25.4279 | 21.6104 | 29.5286 | 4404 | 26 | 2000 | 20200101 |
| all_test_rows | xgb_deployed_config | R2 | 0.8693 | 0.8054 | 0.9012 | 4404 | 26 | 2000 | 20200101 |
| all_test_rows | xgb_selected | MAE | 15.8691 | 13.8658 | 18.1268 | 4404 | 26 | 2000 | 20200101 |
| all_test_rows | xgb_selected | RMSE | 22.5648 | 19.1810 | 26.3785 | 4404 | 26 | 2000 | 20200101 |
| all_test_rows | xgb_selected | R2 | 0.8970 | 0.8604 | 0.9193 | 4404 | 26 | 2000 | 20200101 |
| all_test_rows | linear | MAE | 21.1850 | 18.8605 | 23.6641 | 4404 | 26 | 2000 | 20200101 |
| all_test_rows | linear | RMSE | 28.7599 | 24.5803 | 33.4659 | 4404 | 26 | 2000 | 20200101 |
| all_test_rows | linear | R2 | 0.8327 | 0.7724 | 0.8683 | 4404 | 26 | 2000 | 20200101 |
| all_test_rows | xgb_selected minus linear | MAE_difference | -5.3159 | -6.6703 | -3.9106 | 4404 | 26 | 2000 | 20200101 |

## tables/step1_per_city_mae_common.csv

| model | City | n | MAE |
|---|---|---|---|
| xgb_deployed_config | Ahmedabad | 159 | 33.9313 |
| xgb_deployed_config | Aizawl | 111 | 29.2718 |
| xgb_deployed_config | Amaravati | 183 | 15.7380 |
| xgb_deployed_config | Amritsar | 173 | 20.0294 |
| xgb_deployed_config | Bengaluru | 183 | 7.1595 |
| xgb_deployed_config | Bhopal | 173 | 17.4271 |
| xgb_deployed_config | Brajrajnagar | 119 | 21.9961 |
| xgb_deployed_config | Chandigarh | 182 | 13.3042 |
| xgb_deployed_config | Chennai | 183 | 15.9720 |
| xgb_deployed_config | Coimbatore | 155 | 17.6126 |
| xgb_deployed_config | Delhi | 183 | 16.0575 |
| xgb_deployed_config | Ernakulam | 152 | 32.3061 |
| xgb_deployed_config | Gurugram | 183 | 16.9672 |
| xgb_deployed_config | Guwahati | 183 | 24.2889 |
| xgb_deployed_config | Hyderabad | 183 | 8.6540 |
| xgb_deployed_config | Jaipur | 183 | 18.1811 |
| xgb_deployed_config | Jorapokhar | 162 | 18.0064 |
| xgb_deployed_config | Kochi | 158 | 22.2675 |
| xgb_deployed_config | Kolkata | 183 | 12.6194 |
| xgb_deployed_config | Lucknow | 183 | 20.2149 |
| xgb_deployed_config | Mumbai | 183 | 9.9106 |
| xgb_deployed_config | Patna | 183 | 21.4054 |
| xgb_deployed_config | Shillong | 142 | 14.6925 |
| xgb_deployed_config | Talcher | 155 | 24.2841 |
| xgb_deployed_config | Thiruvananthapuram | 183 | 11.3818 |
| xgb_deployed_config | Visakhapatnam | 177 | 12.6209 |
| xgb_selected | Ahmedabad | 159 | 34.3135 |
| xgb_selected | Aizawl | 111 | 23.7570 |
| xgb_selected | Amaravati | 183 | 16.6143 |
| xgb_selected | Amritsar | 173 | 17.2292 |
| xgb_selected | Bengaluru | 183 | 6.8503 |
| xgb_selected | Bhopal | 173 | 12.6969 |
| xgb_selected | Brajrajnagar | 119 | 20.7688 |
| xgb_selected | Chandigarh | 182 | 12.0544 |
| xgb_selected | Chennai | 183 | 16.5992 |
| xgb_selected | Coimbatore | 155 | 11.3648 |
| xgb_selected | Delhi | 183 | 15.8302 |
| xgb_selected | Ernakulam | 152 | 9.5619 |
| xgb_selected | Gurugram | 183 | 16.2462 |
| xgb_selected | Guwahati | 183 | 24.6960 |
| xgb_selected | Hyderabad | 183 | 8.9794 |
| xgb_selected | Jaipur | 183 | 14.3424 |
| xgb_selected | Jorapokhar | 162 | 17.8473 |
| xgb_selected | Kochi | 158 | 15.9216 |
| xgb_selected | Kolkata | 183 | 12.7752 |
| xgb_selected | Lucknow | 183 | 20.5433 |
| xgb_selected | Mumbai | 183 | 9.2683 |
| xgb_selected | Patna | 183 | 21.8564 |
| xgb_selected | Shillong | 142 | 15.0719 |
| xgb_selected | Talcher | 155 | 18.1023 |
| xgb_selected | Thiruvananthapuram | 183 | 11.3557 |
| xgb_selected | Visakhapatnam | 177 | 12.7460 |
| linear | Ahmedabad | 159 | 41.7946 |
| linear | Aizawl | 111 | 16.3051 |
| linear | Amaravati | 183 | 25.4166 |
| linear | Amritsar | 173 | 22.7828 |
| linear | Bengaluru | 183 | 14.8883 |
| linear | Bhopal | 173 | 18.3568 |
| linear | Brajrajnagar | 119 | 22.0497 |
| linear | Chandigarh | 182 | 14.4148 |
| linear | Chennai | 183 | 19.8663 |
| linear | Coimbatore | 155 | 20.3113 |
| linear | Delhi | 183 | 20.9223 |
| linear | Ernakulam | 152 | 22.3850 |
| linear | Gurugram | 183 | 19.8530 |
| linear | Guwahati | 183 | 31.6019 |
| linear | Hyderabad | 183 | 18.2293 |
| linear | Jaipur | 183 | 19.2064 |
| linear | Jorapokhar | 162 | 24.6666 |
| linear | Kochi | 158 | 24.2976 |
| linear | Kolkata | 183 | 13.4327 |
| linear | Lucknow | 183 | 30.6688 |
| linear | Mumbai | 183 | 11.2542 |
| linear | Patna | 183 | 21.4299 |
| linear | Shillong | 142 | 18.4762 |
| linear | Talcher | 155 | 24.6899 |
| linear | Thiruvananthapuram | 183 | 17.4759 |
| linear | Visakhapatnam | 177 | 16.5824 |
| cpcb_formula | Ahmedabad | 159 | 57.0052 |
| cpcb_formula | Aizawl | 111 | 6.4647 |
| cpcb_formula | Amaravati | 183 | 8.1261 |
| cpcb_formula | Amritsar | 173 | 11.9685 |
| cpcb_formula | Bengaluru | 183 | 12.2451 |
| cpcb_formula | Bhopal | 173 | 13.3889 |
| cpcb_formula | Brajrajnagar | 119 | 22.6875 |
| cpcb_formula | Chandigarh | 182 | 9.9575 |
| cpcb_formula | Chennai | 183 | 29.1763 |
| cpcb_formula | Coimbatore | 155 | 11.5269 |
| cpcb_formula | Delhi | 183 | 22.2059 |
| cpcb_formula | Ernakulam | 152 | 10.3663 |
| cpcb_formula | Gurugram | 183 | 24.0803 |
| cpcb_formula | Guwahati | 183 | 19.5929 |
| cpcb_formula | Hyderabad | 183 | 7.6234 |
| cpcb_formula | Jaipur | 183 | 15.7156 |
| cpcb_formula | Jorapokhar | 162 | 19.9821 |
| cpcb_formula | Kochi | 158 | 22.5534 |
| cpcb_formula | Kolkata | 183 | 18.3688 |
| cpcb_formula | Lucknow | 183 | 23.5682 |
| cpcb_formula | Mumbai | 183 | 13.1976 |
| cpcb_formula | Patna | 183 | 31.8221 |
| cpcb_formula | Shillong | 142 | 9.9902 |
| cpcb_formula | Talcher | 155 | 22.2851 |
| cpcb_formula | Thiruvananthapuram | 183 | 12.8669 |
| cpcb_formula | Visakhapatnam | 177 | 11.6610 |

## tables/step1_random_split_reference.csv

| label | split | n | MAE | RMSE | R2 |
|---|---|---|---|---|---|
| RANDOM-SPLIT: original deployed artifact re-scored on its own random 20% split (clean_data.csv: imputed, AQI clipped to 500, features include Year/Month/Season) | random 80/20 seed 42 | 4970 | 17.9282 | 29.5003 | 0.9320 |
| RANDOM-SPLIT: deployed XGBoost config, 9 pollutant features only, raw NaNs, city_day valid AQI 0-500 | random 80/20 seed 42 | 4862 | 17.4933 | 28.3854 | 0.9212 |

## tables/step2_missing_input_robustness.csv

| masked_pollutant | n_test_rows | xgb_MAE_all_rows | xgb_RMSE_all_rows | formula_computable_rows | formula_coverage | xgb_MAE_on_formula_computable | formula_MAE |
|---|---|---|---|---|---|---|---|
| none | 4404 | 15.8691 | 22.5648 | 4397 | 0.9984 | 15.8334 | 18.0673 |
| PM2.5 | 4404 | 23.2204 | 38.3841 | 4149 | 0.9421 | 21.0359 | 24.1547 |
| PM10 | 4404 | 20.9695 | 27.4119 | 4339 | 0.9852 | 20.8547 | 26.6668 |
| NO2 | 4404 | 15.7668 | 22.5550 | 4397 | 0.9984 | 15.7310 | 18.1758 |
| CO | 4404 | 18.3805 | 32.5433 | 4391 | 0.9970 | 18.3526 | 21.7567 |

## tables/step3_agreement_by_category.csv

| category | n | agreement | agreement_restricted |
|---|---|---|---|
| Good | 528 | 0.2064 | 0.2064 |
| Satisfactory | 1945 | 0.1686 | 0.1686 |
| Moderate | 1482 | 0.2105 | 0.2200 |
| Poor | 287 | 0.8746 | 0.8850 |
| Very Poor | 134 | 0.9925 | 0.9925 |
| Severe | 21 | 1.0000 | 1.0000 |

## tables/step3_agreement_by_city.csv

| City | n | agreement | agreement_restricted |
|---|---|---|---|
| Ahmedabad | 159 | 0.3459 | 0.3459 |
| Aizawl | 111 | 0.5405 | 0.5405 |
| Amaravati | 183 | 0.1749 | 0.1749 |
| Amritsar | 173 | 0.1965 | 0.1965 |
| Bengaluru | 183 | 0.0601 | 0.0601 |
| Bhopal | 173 | 0.0925 | 0.0925 |
| Brajrajnagar | 119 | 0.3445 | 0.3445 |
| Chandigarh | 182 | 0.0165 | 0.0165 |
| Chennai | 183 | 0.3661 | 0.3661 |
| Coimbatore | 155 | 0.2968 | 0.2968 |
| Delhi | 183 | 0.3825 | 0.3825 |
| Ernakulam | 152 | 0.0658 | 0.0921 |
| Gurugram | 183 | 0.3169 | 0.3169 |
| Guwahati | 183 | 0.6011 | 0.6011 |
| Hyderabad | 183 | 0.0164 | 0.0164 |
| Jaipur | 183 | 0.0219 | 0.0219 |
| Jorapokhar | 162 | 0.2840 | 0.2840 |
| Kochi | 158 | 0.0759 | 0.0949 |
| Kolkata | 183 | 0.2514 | 0.2623 |
| Lucknow | 183 | 0.9016 | 0.9016 |
| Mumbai | 183 | 0.1202 | 0.1366 |
| Patna | 183 | 0.3169 | 0.3443 |
| Shillong | 142 | 0.6268 | 0.6268 |
| Talcher | 155 | 0.3871 | 0.3871 |
| Thiruvananthapuram | 183 | 0.1257 | 0.1257 |
| Visakhapatnam | 177 | 0.0734 | 0.0734 |

## tables/step3_agreement_overall.csv

| n | agreement | agreement_restricted |
|---|---|---|
| 4397 | 0.2625 | 0.2663 |

## tables/step3_dominant_vs_top_shap_crosstab.csv

| dominant | CO | NH3 | NOx | O3 | PM10 | PM2.5 |
|---|---|---|---|---|---|---|
| CO | 50 | 0 | 0 | 0 | 0 | 421 |
| NH3 | 0 | 0 | 0 | 0 | 0 | 2 |
| NO2 | 0 | 0 | 0 | 0 | 0 | 82 |
| O3 | 0 | 0 | 0 | 5 | 0 | 305 |
| PM10 | 1 | 0 | 12 | 1 | 56 | 2230 |
| PM2.5 | 57 | 1 | 30 | 11 | 57 | 1043 |
| SO2 | 0 | 0 | 0 | 0 | 0 | 33 |

## tables/step3_mean_abs_shap_by_city.csv

| City | n_rows | PM2.5 | PM10 | NO | NO2 | NOx | NH3 | CO | SO2 | O3 |
|---|---|---|---|---|---|---|---|---|---|---|
| Ahmedabad | 159 | 43.7671 | 13.4809 | 1.8941 | 1.3362 | 5.8237 | 1.6256 | 49.5290 | 3.5696 | 4.1842 |
| Aizawl | 111 | 50.6327 | 32.8850 | 0.6901 | 3.5746 | 3.8839 | 1.8954 | 17.8866 | 1.8075 | 11.6808 |
| Amaravati | 183 | 52.2380 | 28.1051 | 1.8831 | 1.6854 | 5.9994 | 1.5368 | 13.4055 | 2.0242 | 2.8575 |
| Amritsar | 174 | 48.0601 | 18.6846 | 0.8136 | 1.7426 | 1.7060 | 2.2691 | 11.9195 | 1.2303 | 2.7082 |
| Bengaluru | 183 | 51.8915 | 22.6317 | 1.7728 | 0.9788 | 2.2616 | 2.2400 | 10.9072 | 0.9225 | 2.2022 |
| Bhopal | 173 | 45.4178 | 13.9210 | 1.4349 | 1.2425 | 4.9381 | 2.5663 | 9.9434 | 1.2911 | 11.1770 |
| Brajrajnagar | 121 | 30.5471 | 13.4712 | 1.4730 | 1.5359 | 4.9169 | 1.4035 | 12.1043 | 2.4970 | 5.8903 |
| Chandigarh | 182 | 51.9732 | 21.5754 | 1.5967 | 0.8167 | 6.1032 | 0.9237 | 13.1585 | 1.3158 | 5.2037 |
| Chennai | 183 | 55.9147 | 21.1982 | 0.5770 | 1.8219 | 3.8017 | 1.1172 | 11.1862 | 1.7564 | 3.7917 |
| Coimbatore | 156 | 50.6385 | 30.7817 | 2.8658 | 1.3754 | 3.4694 | 2.1484 | 14.5985 | 0.9861 | 4.8526 |
| Delhi | 183 | 56.2534 | 16.3771 | 0.8566 | 0.4470 | 5.0213 | 1.8120 | 9.0424 | 1.1177 | 2.9128 |
| Ernakulam | 153 | 47.0907 | 26.6736 | 1.7090 | 2.2472 | 7.3128 | 2.6768 | 8.3220 | 2.3011 | 10.0210 |
| Gurugram | 183 | 42.6247 | 13.5847 | 0.9795 | 0.8961 | 4.9283 | 1.6994 | 7.6803 | 1.0188 | 7.5600 |
| Guwahati | 183 | 61.6092 | 21.9278 | 1.5603 | 1.1249 | 8.3370 | 3.4707 | 9.6084 | 0.7958 | 3.1833 |
| Hyderabad | 183 | 48.9141 | 18.9468 | 0.6910 | 0.7945 | 2.3464 | 1.8278 | 13.4972 | 1.6955 | 2.5295 |
| Jaipur | 183 | 45.1308 | 15.2622 | 1.2046 | 0.7248 | 5.3485 | 2.5912 | 11.4290 | 1.2280 | 8.3288 |
| Jorapokhar | 162 | 38.3857 | 16.4930 | 0.9536 | 2.0965 | 2.5813 | 1.1365 | 4.9697 | 1.1994 | 8.3506 |
| Kochi | 158 | 48.2239 | 23.9966 | 2.2849 | 2.6739 | 9.9777 | 1.6118 | 7.3596 | 1.2825 | 7.3839 |
| Kolkata | 183 | 46.3745 | 21.1977 | 1.7547 | 1.1182 | 8.2264 | 1.5499 | 12.1872 | 1.3027 | 3.8817 |
| Lucknow | 183 | 61.4228 | 2.8585 | 1.2609 | 1.4923 | 4.2291 | 2.5932 | 6.5601 | 0.8834 | 1.8427 |
| Mumbai | 183 | 47.3389 | 19.8834 | 0.8173 | 1.2033 | 4.8329 | 1.6710 | 14.0279 | 1.1933 | 3.4126 |
| Patna | 183 | 50.8067 | 16.2437 | 2.4714 | 1.0398 | 8.5207 | 2.1542 | 9.7101 | 0.9810 | 4.1422 |
| Shillong | 142 | 47.5007 | 29.3982 | 3.2622 | 2.9602 | 5.3631 | 3.2073 | 16.2975 | 1.4168 | 5.9896 |
| Talcher | 156 | 57.5113 | 23.0961 | 1.2593 | 2.4567 | 3.3304 | 4.0732 | 6.0779 | 2.5262 | 5.6554 |
| Thiruvananthapuram | 183 | 53.0824 | 28.3564 | 0.6122 | 1.3667 | 2.8432 | 2.0239 | 12.0414 | 1.4102 | 2.7908 |
| Visakhapatnam | 178 | 50.0859 | 19.3416 | 1.6967 | 1.0245 | 2.5675 | 2.0729 | 12.2787 | 1.2533 | 4.3520 |

## tables/step3_mean_abs_shap_overall.csv

| pollutant | mean_abs_shap | n_rows |
|---|---|---|
| PM2.5 | 49.6816 | 4404 |
| PM10 | 20.1407 | 4404 |
| CO | 12.3378 | 4404 |
| O3 | 5.0841 | 4404 |
| NOx | 4.9528 | 4404 |
| NH3 | 2.0662 | 4404 |
| NO2 | 1.4662 | 4404 |
| SO2 | 1.4661 | 4404 |
| NO | 1.4602 | 4404 |

## tables/step4_category_metrics.csv

| model | subset | n | accuracy | within_one | macro_f1 |
|---|---|---|---|---|---|
| xgb_deployed_config | common_cases | 4397 | 0.7398 | 0.9986 | 0.6497 |
| xgb_selected | common_cases | 4397 | 0.7441 | 0.9986 | 0.6361 |
| linear | common_cases | 4397 | 0.6925 | 0.9970 | 0.5883 |
| cpcb_formula | common_cases | 4397 | 0.7364 | 0.9936 | 0.6684 |
| xgb_deployed_config | all_test_rows | 4404 | 0.7393 | 0.9984 | 0.6495 |
| xgb_selected | all_test_rows | 4404 | 0.7436 | 0.9984 | 0.6358 |
| linear | all_test_rows | 4404 | 0.6921 | 0.9968 | 0.5880 |

## tables/step4_confusion_cpcb_formula.csv

| Unnamed: 0 | pred_Good | pred_Satisfactory | pred_Moderate | pred_Poor | pred_Very Poor | pred_Severe |
|---|---|---|---|---|---|---|
| true_Good | 473 | 54 | 1 | 0 | 0 | 0 |
| true_Satisfactory | 396 | 1456 | 90 | 3 | 0 | 0 |
| true_Moderate | 9 | 388 | 1033 | 49 | 3 | 0 |
| true_Poor | 1 | 1 | 75 | 154 | 55 | 1 |
| true_Very Poor | 0 | 0 | 5 | 14 | 115 | 0 |
| true_Severe | 0 | 0 | 0 | 4 | 10 | 7 |

## tables/step4_confusion_linear.csv

| Unnamed: 0 | pred_Good | pred_Satisfactory | pred_Moderate | pred_Poor | pred_Very Poor | pred_Severe |
|---|---|---|---|---|---|---|
| true_Good | 154 | 371 | 3 | 0 | 0 | 0 |
| true_Satisfactory | 14 | 1387 | 544 | 0 | 0 | 0 |
| true_Moderate | 0 | 180 | 1247 | 55 | 0 | 0 |
| true_Poor | 0 | 1 | 83 | 197 | 5 | 1 |
| true_Very Poor | 0 | 0 | 2 | 76 | 52 | 4 |
| true_Severe | 0 | 0 | 1 | 5 | 7 | 8 |

## tables/step4_confusion_xgb_deployed_config.csv

| Unnamed: 0 | pred_Good | pred_Satisfactory | pred_Moderate | pred_Poor | pred_Very Poor | pred_Severe |
|---|---|---|---|---|---|---|
| true_Good | 130 | 397 | 1 | 0 | 0 | 0 |
| true_Satisfactory | 13 | 1525 | 407 | 0 | 0 | 0 |
| true_Moderate | 0 | 120 | 1296 | 66 | 0 | 0 |
| true_Poor | 0 | 0 | 72 | 201 | 13 | 1 |
| true_Very Poor | 0 | 0 | 2 | 39 | 93 | 0 |
| true_Severe | 0 | 0 | 1 | 1 | 11 | 8 |

## tables/step4_confusion_xgb_selected.csv

| Unnamed: 0 | pred_Good | pred_Satisfactory | pred_Moderate | pred_Poor | pred_Very Poor | pred_Severe |
|---|---|---|---|---|---|---|
| true_Good | 63 | 464 | 1 | 0 | 0 | 0 |
| true_Satisfactory | 2 | 1705 | 238 | 0 | 0 | 0 |
| true_Moderate | 0 | 225 | 1198 | 59 | 0 | 0 |
| true_Poor | 0 | 0 | 69 | 203 | 14 | 1 |
| true_Very Poor | 0 | 0 | 1 | 39 | 94 | 0 |
| true_Severe | 0 | 0 | 0 | 3 | 9 | 9 |

## tables/step4_event_scores.csv

| model | subset | threshold | events | hits | misses | false_alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| xgb_deployed_config | common_cases | 200 | 442 | 367 | 75 | 66 | 0.8303 | 0.1524 | 0.7224 |
| xgb_deployed_config | common_cases | 300 | 155 | 112 | 43 | 14 | 0.7226 | 0.1111 | 0.6627 |
| xgb_selected | common_cases | 200 | 442 | 372 | 70 | 59 | 0.8416 | 0.1369 | 0.7425 |
| xgb_selected | common_cases | 300 | 155 | 112 | 43 | 15 | 0.7226 | 0.1181 | 0.6588 |
| linear | common_cases | 200 | 442 | 355 | 87 | 55 | 0.8032 | 0.1341 | 0.7143 |
| linear | common_cases | 300 | 155 | 71 | 84 | 6 | 0.4581 | 0.0779 | 0.4410 |
| cpcb_formula | common_cases | 200 | 442 | 360 | 82 | 55 | 0.8145 | 0.1325 | 0.7243 |
| cpcb_formula | common_cases | 300 | 155 | 132 | 23 | 59 | 0.8516 | 0.3089 | 0.6168 |
| xgb_deployed_config | all_test_rows | 200 | 442 | 367 | 75 | 66 | 0.8303 | 0.1524 | 0.7224 |
| xgb_deployed_config | all_test_rows | 300 | 155 | 112 | 43 | 14 | 0.7226 | 0.1111 | 0.6627 |
| xgb_selected | all_test_rows | 200 | 442 | 372 | 70 | 59 | 0.8416 | 0.1369 | 0.7425 |
| xgb_selected | all_test_rows | 300 | 155 | 112 | 43 | 15 | 0.7226 | 0.1181 | 0.6588 |
| linear | all_test_rows | 200 | 442 | 355 | 87 | 55 | 0.8032 | 0.1341 | 0.7143 |
| linear | all_test_rows | 300 | 155 | 71 | 84 | 6 | 0.4581 | 0.0779 | 0.4410 |

## tables/test_predictions_2020.csv

Per-row predictions (4404 rows); not inlined.

## tables/test_predictions_2020_masked.csv

Per-row predictions (22020 rows); not inlined.

## Figures

- figures/step1_pred_vs_recorded.png
- figures/step3_shap_beeswarm.png
- figures/step3_shap_waterfall_delhi_max.png
- figures/step4_confusion_matrices.png
