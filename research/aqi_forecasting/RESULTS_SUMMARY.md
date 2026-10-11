# AQI forecasting results summary

Single-source listing of every number reported for run `20261011T163344Z-7eff64974b98`. Each section names the file it was read from. The locked 2020 test window was scored exactly once, in this run.

## Run identity

- Run ID: `20261011T163344Z-7eff64974b98` (`results/20261011T163344Z-7eff64974b98/run_record.json`)
- Stage: `xgboost_comparator_and_locked_final_test`
- Started / completed (UTC): 2026-10-11T16:33:44.446358+00:00 / 2026-10-11T16:34:44.784711+00:00
- Command: `C:\Users\krish\Desktop\aqi-early-warning-system\venv\Scripts\python.exe -m research.aqi_forecasting.run_final_test`
- Input data: `C:\Users\krish\Desktop\aqi-early-warning-system\data\raw\city_day.csv`, 29,531 rows, 26 cities, SHA-256 `0d84b21c3e4878bbad8df362f2ab05f61ad959538dddf5918e714077ed3c1847`
- Git revision: `cf39c3af7f68264f76d9780d467ab34fabc70712`; research source fingerprint `7ca0a62cc4905882dcfe207e1672226fe34eb1e957cb2bc93b98179062cce1d5`
- Environment: Python 3.13.3, pandas 2.3.3, NumPy 2.4.4, scikit-learn 1.8.0, xgboost 3.2.0, matplotlib 3.10.9
- Reference development run (untouched): `20261010T101227Z-50924ef9974e`

## Selected configurations

Source: `results/20261011T163344Z-7eff64974b98/tables/dev_fold_mae.csv` and `results/20261011T163344Z-7eff64974b98/run_record.json`.

| Policy | Horizon | Ridge alpha | XGBoost config | Ridge mean fold MAE | XGBoost mean fold MAE |
|---|---|---|---|---|---|
| exclude | 1d | 0.1 | depth3_trees200 | 25.300 | 25.821 |
| exclude | 3d | 0.1 | depth3_trees200 | 36.890 | 37.634 |
| exclude | 7d | 0.1 | depth3_trees200 | 40.980 | 41.218 |
| cap | 1d | 0.1 | depth3_trees200 | 26.955 | 27.792 |
| cap | 3d | 0.1 | depth3_trees200 | 40.084 | 41.252 |
| cap | 7d | 0.1 | depth3_trees200 | 44.804 | 45.815 |

XGBoost grid and fixed hyperparameters: `{"colsample_bytree": 1.0, "learning_rate": 0.05, "n_jobs": 1, "objective": "reg:squarederror", "random_state": 0, "subsample": 0.8, "tree_method": "hist"}`; selection rule: Minimize equal-weight mean MAE across fold_2017, fold_2018, and fold_2019; exact ties choose the smaller max_depth, then the smaller n_estimators.

## 2019 development, common-case metrics (recomputed with XGBoost)

Source: `results/20261011T163344Z-7eff64974b98/tables/dev_common_case.csv`.

| Policy | Horizon | Common cases | Method | MAE | RMSE | Macro-city MAE |
|---|---|---|---|---|---|---|
| exclude | 1d | 4,844 | annual_seasonal_naive | 48.101 | 69.691 | 52.236 |
| exclude | 1d | 4,844 | city_month_climatology | 43.705 | 60.676 | 47.728 |
| exclude | 1d | 4,844 | persistence | 22.605 | 36.300 | 23.881 |
| exclude | 1d | 4,844 | regularized_linear | 22.610 | 34.860 | 23.806 |
| exclude | 1d | 4,844 | weekly_seasonal_naive | 41.343 | 63.598 | 43.951 |
| exclude | 1d | 4,844 | xgboost | 22.473 | 34.624 | 23.766 |
| exclude | 3d | 4,775 | annual_seasonal_naive | 47.700 | 68.964 | 52.727 |
| exclude | 3d | 4,775 | city_month_climatology | 43.092 | 59.654 | 46.614 |
| exclude | 3d | 4,775 | persistence | 36.294 | 55.738 | 38.315 |
| exclude | 3d | 4,775 | regularized_linear | 34.088 | 49.660 | 35.799 |
| exclude | 3d | 4,775 | weekly_seasonal_naive | 40.918 | 62.923 | 44.037 |
| exclude | 3d | 4,775 | xgboost | 33.874 | 49.413 | 36.123 |
| exclude | 7d | 4,824 | annual_seasonal_naive | 47.779 | 68.990 | 51.416 |
| exclude | 7d | 4,824 | city_month_climatology | 43.603 | 60.488 | 48.536 |
| exclude | 7d | 4,824 | persistence | 41.102 | 63.088 | 43.136 |
| exclude | 7d | 4,824 | regularized_linear | 37.717 | 54.397 | 39.430 |
| exclude | 7d | 4,824 | xgboost | 37.607 | 54.654 | 39.750 |
| cap | 1d | 5,223 | annual_seasonal_naive | 51.896 | 76.852 | 53.427 |
| cap | 1d | 5,223 | city_month_climatology | 48.690 | 67.712 | 49.304 |
| cap | 1d | 5,223 | persistence | 25.008 | 41.499 | 24.962 |
| cap | 1d | 5,223 | regularized_linear | 25.091 | 39.545 | 25.005 |
| cap | 1d | 5,223 | weekly_seasonal_naive | 45.356 | 70.459 | 45.219 |
| cap | 1d | 5,223 | xgboost | 24.996 | 39.266 | 24.935 |
| cap | 3d | 5,162 | annual_seasonal_naive | 51.559 | 76.274 | 53.008 |
| cap | 3d | 5,162 | city_month_climatology | 48.313 | 67.042 | 48.865 |
| cap | 3d | 5,162 | persistence | 40.261 | 63.197 | 40.349 |
| cap | 3d | 5,162 | regularized_linear | 38.055 | 55.819 | 37.910 |
| cap | 3d | 5,162 | weekly_seasonal_naive | 45.017 | 69.948 | 44.762 |
| cap | 3d | 5,162 | xgboost | 37.729 | 55.490 | 37.751 |
| cap | 7d | 5,201 | annual_seasonal_naive | 51.890 | 76.919 | 53.553 |
| cap | 7d | 5,201 | city_month_climatology | 48.591 | 67.689 | 49.234 |
| cap | 7d | 5,201 | persistence | 45.167 | 70.194 | 45.035 |
| cap | 7d | 5,201 | regularized_linear | 42.021 | 60.915 | 41.698 |
| cap | 7d | 5,201 | xgboost | 41.930 | 61.393 | 41.920 |

## 2019 development, native coverage

Source: `results/20261011T163344Z-7eff64974b98/tables/dev_coverage.csv`.

| Policy | Horizon | Method | Valid targets | Predicted | Native coverage |
|---|---|---|---|---|---|
| exclude | 1d | annual_seasonal_naive | 6,915 | 5,252 | 0.7595 |
| exclude | 1d | city_month_climatology | 6,915 | 6,915 | 1.0000 |
| exclude | 1d | persistence | 6,915 | 6,741 | 0.9748 |
| exclude | 1d | regularized_linear | 6,915 | 6,331 | 0.9155 |
| exclude | 1d | weekly_seasonal_naive | 6,915 | 6,583 | 0.9520 |
| exclude | 1d | xgboost | 6,915 | 6,331 | 0.9155 |
| exclude | 3d | annual_seasonal_naive | 6,915 | 5,252 | 0.7595 |
| exclude | 3d | city_month_climatology | 6,915 | 6,915 | 1.0000 |
| exclude | 3d | persistence | 6,915 | 6,642 | 0.9605 |
| exclude | 3d | regularized_linear | 6,915 | 6,264 | 0.9059 |
| exclude | 3d | weekly_seasonal_naive | 6,915 | 6,583 | 0.9520 |
| exclude | 3d | xgboost | 6,915 | 6,264 | 0.9059 |
| exclude | 7d | annual_seasonal_naive | 6,915 | 5,252 | 0.7595 |
| exclude | 7d | city_month_climatology | 6,915 | 6,915 | 1.0000 |
| exclude | 7d | persistence | 6,915 | 6,583 | 0.9520 |
| exclude | 7d | regularized_linear | 6,915 | 6,199 | 0.8965 |
| exclude | 7d | xgboost | 6,915 | 6,199 | 0.8965 |
| cap | 1d | annual_seasonal_naive | 7,071 | 5,528 | 0.7818 |
| cap | 1d | city_month_climatology | 7,071 | 7,071 | 1.0000 |
| cap | 1d | persistence | 7,071 | 6,963 | 0.9847 |
| cap | 1d | regularized_linear | 7,071 | 6,659 | 0.9417 |
| cap | 1d | weekly_seasonal_naive | 7,071 | 6,834 | 0.9665 |
| cap | 1d | xgboost | 7,071 | 6,659 | 0.9417 |
| cap | 3d | annual_seasonal_naive | 7,071 | 5,528 | 0.7818 |
| cap | 3d | city_month_climatology | 7,071 | 7,071 | 1.0000 |
| cap | 3d | persistence | 7,071 | 6,889 | 0.9743 |
| cap | 3d | regularized_linear | 7,071 | 6,601 | 0.9335 |
| cap | 3d | weekly_seasonal_naive | 7,071 | 6,834 | 0.9665 |
| cap | 3d | xgboost | 7,071 | 6,601 | 0.9335 |
| cap | 7d | annual_seasonal_naive | 7,071 | 5,528 | 0.7818 |
| cap | 7d | city_month_climatology | 7,071 | 7,071 | 1.0000 |
| cap | 7d | persistence | 7,071 | 6,834 | 0.9665 |
| cap | 7d | regularized_linear | 7,071 | 6,543 | 0.9253 |
| cap | 7d | xgboost | 7,071 | 6,543 | 0.9253 |

## Locked 2020 test, native coverage

Source: `results/20261011T163344Z-7eff64974b98/tables/test_coverage.csv`.

| Policy | Horizon | Method | Valid targets | Predicted | Native coverage |
|---|---|---|---|---|---|
| exclude | 1d | annual_seasonal_naive | 4,404 | 3,118 | 0.7080 |
| exclude | 1d | city_month_climatology | 4,404 | 4,404 | 1.0000 |
| exclude | 1d | persistence | 4,404 | 4,330 | 0.9832 |
| exclude | 1d | regularized_linear | 4,404 | 4,120 | 0.9355 |
| exclude | 1d | weekly_seasonal_naive | 4,404 | 4,235 | 0.9616 |
| exclude | 1d | xgboost | 4,404 | 4,120 | 0.9355 |
| exclude | 3d | annual_seasonal_naive | 4,404 | 3,118 | 0.7080 |
| exclude | 3d | city_month_climatology | 4,404 | 4,404 | 1.0000 |
| exclude | 3d | persistence | 4,404 | 4,279 | 0.9716 |
| exclude | 3d | regularized_linear | 4,404 | 4,076 | 0.9255 |
| exclude | 3d | weekly_seasonal_naive | 4,404 | 4,235 | 0.9616 |
| exclude | 3d | xgboost | 4,404 | 4,076 | 0.9255 |
| exclude | 7d | annual_seasonal_naive | 4,404 | 3,118 | 0.7080 |
| exclude | 7d | city_month_climatology | 4,404 | 4,404 | 1.0000 |
| exclude | 7d | persistence | 4,404 | 4,235 | 0.9616 |
| exclude | 7d | regularized_linear | 4,404 | 4,041 | 0.9176 |
| exclude | 7d | xgboost | 4,404 | 4,041 | 0.9176 |
| cap | 1d | annual_seasonal_naive | 4,421 | 3,208 | 0.7256 |
| cap | 1d | city_month_climatology | 4,421 | 4,421 | 1.0000 |
| cap | 1d | persistence | 4,421 | 4,356 | 0.9853 |
| cap | 1d | regularized_linear | 4,421 | 4,163 | 0.9416 |
| cap | 1d | weekly_seasonal_naive | 4,421 | 4,267 | 0.9652 |
| cap | 1d | xgboost | 4,421 | 4,163 | 0.9416 |
| cap | 3d | annual_seasonal_naive | 4,421 | 3,208 | 0.7256 |
| cap | 3d | city_month_climatology | 4,421 | 4,421 | 1.0000 |
| cap | 3d | persistence | 4,421 | 4,309 | 0.9747 |
| cap | 3d | regularized_linear | 4,421 | 4,120 | 0.9319 |
| cap | 3d | weekly_seasonal_naive | 4,421 | 4,267 | 0.9652 |
| cap | 3d | xgboost | 4,421 | 4,120 | 0.9319 |
| cap | 7d | annual_seasonal_naive | 4,421 | 3,208 | 0.7256 |
| cap | 7d | city_month_climatology | 4,421 | 4,421 | 1.0000 |
| cap | 7d | persistence | 4,421 | 4,267 | 0.9652 |
| cap | 7d | regularized_linear | 4,421 | 4,087 | 0.9245 |
| cap | 7d | xgboost | 4,421 | 4,087 | 0.9245 |

## Locked 2020 test, common-case metrics with 95% city-cluster CIs

Source: `results/20261011T163344Z-7eff64974b98/tables/test_common_case_with_ci.csv`. 2,000 replicates, seed 20200101, cities resampled with replacement.

| Policy | Horizon | Common cases | Method | MAE | 95% CI | RMSE | MAE - persistence | 95% CI of difference |
|---|---|---|---|---|---|---|---|---|
| exclude | 1d | 2,955 | annual_seasonal_naive | 59.114 | [47.985, 73.230] | 85.654 | 40.385 | [31.599, 52.005] |
| exclude | 1d | 2,955 | city_month_climatology | 57.504 | [45.470, 70.538] | 75.503 | 38.775 | [29.023, 49.274] |
| exclude | 1d | 2,955 | persistence | 18.728 | [14.941, 22.599] | 31.231 | reference | reference |
| exclude | 1d | 2,955 | regularized_linear | 18.836 | [15.303, 22.454] | 30.023 | 0.108 | [-0.370, 0.574] |
| exclude | 1d | 2,955 | weekly_seasonal_naive | 32.770 | [26.981, 38.729] | 50.954 | 14.042 | [11.624, 16.636] |
| exclude | 1d | 2,955 | xgboost | 19.149 | [15.723, 22.716] | 29.992 | 0.420 | [-0.121, 1.005] |
| exclude | 3d | 2,929 | annual_seasonal_naive | 58.978 | [47.884, 73.359] | 85.636 | 28.179 | [20.594, 39.270] |
| exclude | 3d | 2,929 | city_month_climatology | 57.436 | [45.368, 70.542] | 75.446 | 26.636 | [17.848, 36.089] |
| exclude | 3d | 2,929 | persistence | 30.799 | [24.523, 37.245] | 49.441 | reference | reference |
| exclude | 3d | 2,929 | regularized_linear | 29.014 | [23.851, 34.356] | 43.884 | -1.785 | [-3.022, -0.443] |
| exclude | 3d | 2,929 | weekly_seasonal_naive | 32.942 | [27.127, 39.065] | 51.237 | 2.143 | [0.363, 4.188] |
| exclude | 3d | 2,929 | xgboost | 30.131 | [25.099, 35.323] | 44.207 | -0.668 | [-2.197, 1.013] |
| exclude | 7d | 2,946 | annual_seasonal_naive | 59.048 | [47.885, 73.362] | 85.575 | 26.141 | [18.477, 36.843] |
| exclude | 7d | 2,946 | city_month_climatology | 57.487 | [45.464, 70.660] | 75.482 | 24.581 | [16.129, 33.725] |
| exclude | 7d | 2,946 | persistence | 32.906 | [27.029, 38.930] | 51.186 | reference | reference |
| exclude | 7d | 2,946 | regularized_linear | 30.094 | [25.392, 35.040] | 44.214 | -2.812 | [-4.215, -1.403] |
| exclude | 7d | 2,946 | xgboost | 31.465 | [27.051, 35.984] | 44.386 | -1.441 | [-3.450, 0.600] |
| cap | 1d | 3,057 | annual_seasonal_naive | 64.106 | [49.190, 85.421] | 96.191 | 44.217 | [32.524, 61.513] |
| cap | 1d | 3,057 | city_month_climatology | 62.485 | [47.420, 80.557] | 84.366 | 42.596 | [30.750, 56.797] |
| cap | 1d | 3,057 | persistence | 19.889 | [15.838, 24.701] | 34.215 | reference | reference |
| cap | 1d | 3,057 | regularized_linear | 19.977 | [16.205, 24.443] | 32.873 | 0.089 | [-0.361, 0.553] |
| cap | 1d | 3,057 | weekly_seasonal_naive | 35.198 | [28.689, 43.153] | 56.702 | 15.309 | [12.298, 18.867] |
| cap | 1d | 3,057 | xgboost | 20.396 | [16.761, 24.807] | 33.009 | 0.508 | [-0.049, 1.131] |
| cap | 3d | 3,026 | annual_seasonal_naive | 64.033 | [48.910, 85.952] | 96.268 | 31.212 | [21.358, 46.471] |
| cap | 3d | 3,026 | city_month_climatology | 62.516 | [47.374, 80.602] | 84.396 | 29.694 | [19.392, 41.792] |
| cap | 3d | 3,026 | persistence | 32.822 | [26.118, 40.601] | 54.256 | reference | reference |
| cap | 3d | 3,026 | regularized_linear | 31.087 | [25.499, 37.787] | 48.228 | -1.734 | [-3.005, -0.401] |
| cap | 3d | 3,026 | weekly_seasonal_naive | 35.224 | [28.719, 43.024] | 56.680 | 2.403 | [0.701, 4.349] |
| cap | 3d | 3,026 | xgboost | 32.113 | [26.694, 38.334] | 48.465 | -0.709 | [-2.274, 0.961] |
| cap | 7d | 3,047 | annual_seasonal_naive | 64.224 | [49.034, 86.342] | 96.476 | 28.886 | [19.082, 43.409] |
| cap | 7d | 3,047 | city_month_climatology | 62.555 | [47.318, 80.853] | 84.508 | 27.217 | [17.348, 38.757] |
| cap | 7d | 3,047 | persistence | 35.338 | [28.718, 43.402] | 56.999 | reference | reference |
| cap | 7d | 3,047 | regularized_linear | 32.350 | [26.872, 39.103] | 48.963 | -2.988 | [-4.592, -1.405] |
| cap | 7d | 3,047 | xgboost | 33.787 | [28.559, 39.986] | 49.399 | -1.551 | [-3.815, 0.806] |

## Lockdown sub-analysis

Source: `results/20261011T163344Z-7eff64974b98/tables/test_lockdown_split.csv`. India's national lockdown began 2020-03-25.

| Policy | Horizon | Method | Pre-lockdown MAE (n) | Lockdown MAE (n) |
|---|---|---|---|---|
| exclude | 1d | annual_seasonal_naive | 65.174 (1,330) | 54.153 (1,625) |
| exclude | 1d | city_month_climatology | 61.934 (1,330) | 53.878 (1,625) |
| exclude | 1d | persistence | 26.186 (1,330) | 12.624 (1,625) |
| exclude | 1d | regularized_linear | 26.309 (1,330) | 12.720 (1,625) |
| exclude | 1d | weekly_seasonal_naive | 45.078 (1,330) | 22.696 (1,625) |
| exclude | 1d | xgboost | 26.458 (1,330) | 13.166 (1,625) |
| exclude | 3d | annual_seasonal_naive | 64.500 (1,321) | 54.442 (1,608) |
| exclude | 3d | city_month_climatology | 61.587 (1,321) | 54.025 (1,608) |
| exclude | 3d | persistence | 44.796 (1,321) | 19.301 (1,608) |
| exclude | 3d | regularized_linear | 41.231 (1,321) | 18.978 (1,608) |
| exclude | 3d | weekly_seasonal_naive | 45.403 (1,321) | 22.705 (1,608) |
| exclude | 3d | xgboost | 41.709 (1,321) | 20.621 (1,608) |
| exclude | 7d | annual_seasonal_naive | 64.698 (1,338) | 54.346 (1,608) |
| exclude | 7d | city_month_climatology | 61.322 (1,338) | 54.297 (1,608) |
| exclude | 7d | persistence | 45.205 (1,338) | 22.673 (1,608) |
| exclude | 7d | regularized_linear | 40.650 (1,338) | 21.311 (1,608) |
| exclude | 7d | xgboost | 40.284 (1,338) | 24.126 (1,608) |
| cap | 1d | annual_seasonal_naive | 69.673 (1,405) | 59.372 (1,652) |
| cap | 1d | city_month_climatology | 66.320 (1,405) | 59.223 (1,652) |
| cap | 1d | persistence | 28.440 (1,405) | 12.616 (1,652) |
| cap | 1d | regularized_linear | 28.506 (1,405) | 12.724 (1,652) |
| cap | 1d | weekly_seasonal_naive | 49.514 (1,405) | 23.022 (1,652) |
| cap | 1d | xgboost | 28.802 (1,405) | 13.247 (1,652) |
| cap | 3d | annual_seasonal_naive | 69.159 (1,391) | 59.672 (1,635) |
| cap | 3d | city_month_climatology | 66.195 (1,391) | 59.386 (1,635) |
| cap | 3d | persistence | 48.590 (1,391) | 19.407 (1,635) |
| cap | 3d | regularized_linear | 44.937 (1,391) | 19.304 (1,635) |
| cap | 3d | weekly_seasonal_naive | 49.531 (1,391) | 23.053 (1,635) |
| cap | 3d | xgboost | 45.432 (1,391) | 20.782 (1,635) |
| cap | 7d | annual_seasonal_naive | 69.526 (1,412) | 59.645 (1,635) |
| cap | 7d | city_month_climatology | 65.848 (1,412) | 59.711 (1,635) |
| cap | 7d | persistence | 49.616 (1,412) | 23.007 (1,635) |
| cap | 7d | regularized_linear | 44.587 (1,412) | 21.782 (1,635) |
| cap | 7d | xgboost | 44.531 (1,412) | 24.508 (1,635) |

## Figures

- `results/20261011T163344Z-7eff64974b98/figures/fig_test_mae_by_horizon.png` — Locked-2020 common-case MAE per method per horizon, exclude policy, with 95% city-cluster bootstrap CIs. Data: tables/test_common_case_with_ci.csv.
- `results/20261011T163344Z-7eff64974b98/figures/fig_dev_vs_test.png` — Persistence, Ridge, and XGBoost common-case MAE, 2019 development versus locked 2020 test, exclude policy. Data: tables/dev_common_case.csv and tables/test_common_case_with_ci.csv.
- `results/20261011T163344Z-7eff64974b98/figures/fig_lockdown.png` — Common-case MAE before and during the national lockdown, exclude policy, 1-day horizon. Data: tables/test_lockdown_split.csv.
- `results/20261011T163344Z-7eff64974b98/figures/fig_timeseries_delhi.png` — Delhi observed AQI against 1-day persistence, Ridge, and XGBoost forecasts over the locked test window, exclude policy. Data: tables/fig_timeseries_delhi_data.csv.

## Artifact SHA-256

Recorded in `results/20261011T163344Z-7eff64974b98/run_record.json` under `artifacts.sha256`.

This file is written after the research source fingerprint is computed, so its own hash is recorded in the run record but it is not covered by that fingerprint.
