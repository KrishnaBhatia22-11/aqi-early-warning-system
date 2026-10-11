# Literature review matrix

> **Versioning note:** The reviewed matrix with per-reference verification
> status is [LITERATURE_MATRIX_v2.md](LITERATURE_MATRIX_v2.md). This original
> matrix is retained unchanged as the pre-review version.

This is a focused, preliminary review for the study design, not a claim of
systematic-review completeness or novelty. Bibliographic metadata were checked
against DOI/Crossref, publisher, or PubMed-indexed records. Most study
descriptions are abstract-level; full methods were not accessible or reviewed
for every item. A “daily” title does not establish an exact one-day-ahead
forecast horizon.

| Source | Topic and inspected evidence | Relevance to this study | Limitations for citation/use |
|---|---|---|---|
| Kumar and Goyal (2011), *Science of the Total Environment*, 409(24), 5517–5523, DOI [10.1016/j.scitotenv.2011.08.069](https://doi.org/10.1016/j.scitotenv.2011.08.069) | PubMed-indexed abstract describes daily AQI for Delhi and seasonal forecasting; models include seasonal ARIMA, principal-component regression, and a combined method. The abstract does not establish the exact lead or split dates. | Foundational India-specific statistical forecasting comparison. | The abstract says AQI used a USEPA method with breakpoint concentrations based on Indian standards; this may differ from CPCB National AQI. No numerical errors or temporal split details were verified. |
| Gupta, Kapadia, and Bhadane (2023), *2023 Fifth International Conference on Electrical, Computer and Communication Technologies*, pp. 1–5, DOI [10.1109/ICECCT56650.2023.10179673](https://doi.org/10.1109/ICECCT56650.2023.10179673) | Retrieved abstract describes daily, weekly, and monthly series, Delhi and Bengaluru, and Prophet. It does not identify the exact forecast horizon or dates. | Provides related Indian city-level AQI forecasting context. | “Highly accurate” is not accompanied by a metric or split design in the retrieved abstract. Comparing two cities does not establish transfer to an unseen city; publisher full text was not reviewed. |
| Gayatri, Anand, and Satyarthi (2024), *Journal of Biofuels*, 15(1), 1–12, DOI [10.5958/0976-4763.2024.00001.5](https://doi.org/10.5958/0976-4763.2024.00001.5) | Publisher abstract describes pollutant trends across Indian cities for 2015–2020 and SARIMAX forecasting of AQI for Delhi or major Indian cities. | Relevant seasonal/exogenous modeling context. | The abstract does not specify exact forecast lead, data source lineage, city assignment, chronological evaluation, or numerical forecast metrics. |
| Pande et al. (2024), *Environmental Pollution*, 351, article 124040, DOI [10.1016/j.envpol.2024.124040](https://doi.org/10.1016/j.envpol.2024.124040) | PubMed-indexed abstract describes daily-scale Delhi AQI and LSTM, Bi-LSTM, Bi-RNN, and Kernel Ridge Regression. It reports Bi-RNN \(R^2=0.954\), RMSE=25.755, and says KRR was weakest. | Directly related India/Delhi neural forecasting comparison. | Exact lead, source data, split dates, rolling-origin design, and naïve baselines were not verified from the abstract. Reported values were not independently reproduced. |
| Pande, Radhadevi, and Satyanarayana (2024), *Environmental Monitoring and Assessment*, 196(12), article 1215, DOI [10.1007/s10661-024-13351-1](https://doi.org/10.1007/s10661-024-13351-1) | PubMed-indexed abstract describes daily AQI prediction in Delhi, six models including XGBoost, ANN, and RF, a test phase, and ten-fold cross-validation. It reports XGBoost test \(R^2=0.99\), RMSE=4.65. | Directly related ML/deep-learning comparison. | The abstract does not establish whether folds respect time or inputs precede targets. It reports ANN/RF MSE and RMSE pairs that are arithmetically inconsistent. The first author overlaps with the preceding study; dataset overlap is unverified. Full tables and methods are needed before comparison. |
| Chen et al. (2024 print; 2023 online), *ACM Transactions on Knowledge Discovery from Data*, 18(3), 1–20, DOI [10.1145/3631713](https://doi.org/10.1145/3631713) | Crossref record and abstract describe a group-aware graph neural network for nationwide city air-quality forecasting on China and U.S. datasets. The abstract does not provide exact lead times or city holdout details. | Adjacent work on spatial and city-group structure. | Nationwide coverage or a graph model does not by itself imply zero-shot held-out-city evaluation. It is not India-specific. |
| Cerqueira, Torgo, and Mozetič (2020), *Machine Learning*, 109(11), 1997–2028, DOI [10.1007/s10994-020-05910-7](https://doi.org/10.1007/s10994-020-05910-7) | DOI/Crossref metadata verify the title, authors, venue, volume, issue, and pages: “Evaluating time series forecasting models: an empirical study on performance estimation methods.” | Relevant to the design and interpretation of time-aware development folds and out-of-sample performance estimation. | Only bibliographic metadata were inspected here; do not claim a particular empirical conclusion from this paper without checking its text. |
| Roberts et al. (2017), *Ecography*, 40(8), 913–929, DOI [10.1111/ecog.02881](https://doi.org/10.1111/ecog.02881) | Crossref metadata and abstract were inspected. The abstract reviews cross-validation under temporal, spatial, hierarchical, and phylogenetic structure and discusses strategically blocked splits. | Motivates treating temporal and city structure explicitly rather than relying on random row-wise splits; supports documenting the target of generalization. | The study is in ecology, not AQI forecasting. Its conclusions are methodological context, not direct evidence about this dataset or this AQI task. |
| Tashman (2000), *International Journal of Forecasting*, 16(4), 437–450, DOI [10.1016/S0169-2070(00)00065-0](https://doi.org/10.1016/S0169-2070(00)00065-0) | DOI/Crossref metadata verify the title: “Out-of-sample tests of forecasting accuracy: an analysis and review.” | Useful framing for the separation of model development, selection, and genuinely out-of-sample evaluation. | Only bibliographic metadata were inspected; cite for its review scope, not for a detailed recommendation unless the full text is reviewed. |
| Hyndman and Athanasopoulos (2021), *Forecasting: Principles and Practice*, 3rd ed., OTexts, Chapter 5, [Time series cross-validation](https://otexts.com/fpp3/tscv.html) | The accessible chapter describes rolling forecasting-origin evaluation in which each forecast is based only on earlier observations, and notes extensions to multi-step errors. | Clear reference for why forecast origins and horizon-specific, time-ordered evaluation matter. | An open textbook rather than a peer-reviewed AQI study. Cite as methodological background, not as evidence of this system's performance. |

## Synthesis and implications

1. Existing Indian AQI forecasting literature includes statistical, Prophet,
   SARIMAX, recurrent-neural, and other ML approaches [1], [6]–[10]. The
   abstract-level summaries do not establish that their data, target
   generation, lead times, partitions, or metrics are comparable to this
   project.
2. The evaluation literature makes temporal dependence and the intended
   prediction target central to split design [2]–[5]. The present study's
   target-date partitions and expanding windows are therefore design choices
   to document and defend, not a contribution by themselves.
3. The current development/2019 results are selection-stage results. The
   Ridge alpha selection uses folds through 2019; consequently, those
   2019 metrics are not a clean, independent estimate of generalization.
4. No novelty claim is supported by this limited search. Before submission,
   the authors should review the full text and supplements for AQI/PM
   forecasting studies in India and comparable multi-city settings, compare
   target definitions and temporal protocols, and search the relevant
   conference/journal proceedings systematically.

## Verified bibliographic records

[1] C. B. Pande, N. L. Kushwaha, O. A. Alawi, S. S. Sammen, L. M. Sidek,
Z. Mundher Yaseen, S. C. Pal, and O. M. Katipoğlu, “Daily scale air quality
index forecasting using bidirectional recurrent neural networks: Case study
of Delhi, India,” *Environmental Pollution*, vol. 351, Art. no. 124040, 2024,
doi: [10.1016/j.envpol.2024.124040](https://doi.org/10.1016/j.envpol.2024.124040).

[2] V. Cerqueira, L. Torgo, and I. Mozetič, “Evaluating time series
forecasting models: an empirical study on performance estimation methods,”
*Machine Learning*, vol. 109, no. 11, pp. 1997–2028, 2020,
doi: [10.1007/s10994-020-05910-7](https://doi.org/10.1007/s10994-020-05910-7).

[3] D. R. Roberts et al., “Cross-validation strategies for data with temporal,
spatial, hierarchical, or phylogenetic structure,” *Ecography*, vol. 40,
no. 8, pp. 913–929, 2017,
doi: [10.1111/ecog.02881](https://doi.org/10.1111/ecog.02881).

[4] L. J. Tashman, “Out-of-sample tests of forecasting accuracy: an analysis
and review,” *International Journal of Forecasting*, vol. 16, no. 4,
pp. 437–450, 2000,
doi: [10.1016/S0169-2070(00)00065-0](https://doi.org/10.1016/S0169-2070(00)00065-0).

[5] R. J. Hyndman and G. Athanasopoulos, *Forecasting: Principles and
Practice*, 3rd ed. Melbourne, Australia: OTexts, 2021, Chapter 5, “The time
series cross-validation.” [Online]. Available:
https://otexts.com/fpp3/tscv.html.

[6] P. Kumar and P. Goyal, “Forecasting of daily air quality index in Delhi,”
*Science of the Total Environment*, vol. 409, no. 24, pp. 5517–5523, 2011,
doi: [10.1016/j.scitotenv.2011.08.069](https://doi.org/10.1016/j.scitotenv.2011.08.069).

[7] S. Gupta, S. Kapadia, and R. Bhadane, “Time Series Analysis and
Forecasting of Air Quality in India,” in *2023 Fifth International Conference
on Electrical, Computer and Communication Technologies*, 2023, pp. 1–5,
doi: [10.1109/ICECCT56650.2023.10179673](https://doi.org/10.1109/ICECCT56650.2023.10179673).

[8] V. Gayatri, S. Anand, and P. Satyarthi, “Analysis of air quality of Delhi
and AQI forecast using SARIMAX,” *Journal of Biofuels*, vol. 15, no. 1,
pp. 1–12, 2024,
doi: [10.5958/0976-4763.2024.00001.5](https://doi.org/10.5958/0976-4763.2024.00001.5).

[9] C. B. Pande et al., “Evaluation of machine learning and deep learning
models for daily air quality index prediction in Delhi city, India,”
*Environmental Monitoring and Assessment*, vol. 196, no. 12, Art. no. 1215,
2024, doi: [10.1007/s10661-024-13351-1](https://doi.org/10.1007/s10661-024-13351-1).

[10] Y. Chen et al., “Group-Aware Graph Neural Network for Nationwide City
Air Quality Forecasting,” *ACM Transactions on Knowledge Discovery from
Data*, vol. 18, no. 3, pp. 1–20, 2024 (online 2023),
doi: [10.1145/3631713](https://doi.org/10.1145/3631713).
