# Dataset provenance record

## Local file identity

The research input is `data/raw/city_day.csv`, tracked in this repository.
At the time of verification its SHA-256 was
`0d84b21c3e4878bbad8df362f2ab05f61ad959538dddf5918e714077ed3c1847`.
The file is 2,574,056 bytes and contains 29,531 rows and 16 columns:

`City`, `Date`, `PM2.5`, `PM10`, `NO`, `NO2`, `NOx`, `NH3`, `CO`, `SO2`,
`O3`, `Benzene`, `Toluene`, `Xylene`, `AQI`, and `AQI_Bucket`.

The observed city count is 26, and the observed date range is 2015-01-01
through 2020-07-01. The file contains 543 `AQI` values greater than 500, with
minimum 501 and maximum 2049. All 543 have `AQI_Bucket` equal to `Severe` in
this local file.

## Public artifact match and attribution

On 2026-10-10, the local file's bytes were compared with the `city_day.csv`
inside Kaggle dataset version 12 for [Air Quality Data in India
(2015–2020)](https://www.kaggle.com/datasets/rohanrao/air-quality-data-in-india).
The downloaded version-12 file had the same 2,574,056-byte size and the same
SHA-256; the files were byte-identical.

Kaggle's [dataset metadata API](https://www.kaggle.com/api/v1/datasets/view/rohanrao/air-quality-data-in-india)
identifies the owner as Vopani (`rohanrao`), states that the dataset includes
hourly and daily AQI/air-quality data, attributes public availability to the
Central Pollution Control Board (CPCB), reports version 12 (updated
2020-07-28), and labels the license **CC0: Public Domain**. The
[version-12 file listing](https://www.kaggle.com/api/v1/datasets/list/rohanrao/air-quality-data-in-india?datasetVersionNumber=12)
lists `city_day.csv` at 2,574,056 bytes.

These checks establish the exact match to the Kaggle version-12 artifact and
record Kaggle's stated attribution and license label. They do not establish
the historical CPCB source snapshot, a complete CPCB-to-Kaggle chain of
custody, or that Kaggle's license label resolves rights in upstream CPCB
material. The project should not present the upstream lineage or license as
independently verified.

## AQI methodology and out-of-range values

CPCB's [National Air Quality Index final report](https://airquality.cpcb.gov.in/ccr_docs/FINAL-REPORT_AQI_.pdf)
is the official reference for the Indian National AQI methodology. It
describes pollutant sub-indices based on concentration breakpoints and an
overall AQI determined by the maximum sub-index, across PM2.5, PM10, NO2,
SO2, CO, O3, NH3, and Pb. The
repository's production implementation, [`src/data/india_aqi.py`](../../src/data/india_aqi.py),
contains pollutant breakpoint tables, sub-index interpolation, a maximum of
500, and a function that returns 500 above the top pollutant concentration
band.

That code describes the current application's AQI calculations; it does not
document or prove how the historical CSV's `AQI` values were produced. The
local data's 543 values above 500 (501–2049), each labelled `Severe`, do not
by themselves establish whether the values are extrapolated, calculated by a
different procedure, or erroneous. The Kaggle dataset page links an AQI
calculation tutorial, but the exact transformation that generated these
historical `AQI` values has not been verified in this record.

The forecasting study therefore preserves the two predeclared treatments:
exclude values outside [0, 500] from valid labels/features, or cap values
above 500 at 500 while retaining the raw value for audit. These are explicit
analysis policies, not a conclusion that either treatment is the correct
historical AQI interpretation.

## Remaining verification

- Identify the CPCB source dataset/archive and retrieval or extraction process
  corresponding to the Kaggle copy.
- Verify applicable upstream rights and whether the Kaggle CC0 label applies
  beyond that hosted copy.
- Verify the AQI computation, aggregation, and treatment of values above 500
  used to construct the Kaggle `city_day.csv`.
- Establish whether the historical daily city summaries have consistent
  station coverage and what the missing values represent.
