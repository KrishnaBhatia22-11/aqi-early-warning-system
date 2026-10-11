"""Fixed, auditable protocol constants for the daily AQI forecasting study."""

HORIZONS_DAYS = (1, 3, 7)
AQI_LAGS_DAYS = (0, 1, 7)
AQI_MIN = 0.0
AQI_MAX = 500.0

TRAIN_START = "2015-01-01"
TRAIN_END = "2018-12-31"
VALIDATION_START = "2019-01-01"
VALIDATION_END = "2019-12-31"
TEST_START = "2020-01-01"
TEST_END = "2020-07-01"

TARGET_POLICIES = ("exclude", "cap")
PARTITIONS = ("train", "validation", "test")
MIN_CITY_TEST_CASES = 30

LAG_FEATURE_COLUMNS = (
    "aqi_lag_origin",
    "aqi_lag_1d",
    "aqi_lag_7d",
)
CALENDAR_FEATURE_COLUMNS = (
    "target_month_sin",
    "target_month_cos",
    "target_weekday_sin",
    "target_weekday_cos",
)
PRIMARY_FEATURE_COLUMNS = LAG_FEATURE_COLUMNS + CALENDAR_FEATURE_COLUMNS
