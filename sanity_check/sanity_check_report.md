# Sanity Check: Actual (WBL/100) vs Baseline (women_treatment_index)

## Core metrics

| Metric | Value |
|---|---|
| Matched observations | 1,700 |
| Countries | 170 |
| Pearson r | 0.8795 |
| Spearman rho | 0.8869 |
| MAE | 0.0797 |
| RMSE | 0.1036 |
| Mean signed diff (actual - baseline) | +0.0610 |

## Largest positive disagreements (actual above baseline)

| iso3 | year | baseline_value | actual_value | difference_signed |
| --- | --- | --- | --- | --- |
| SAU | 2022 | 0.3329 | 0.7461542951366452 | 0.413254 |
| SAU | 2021 | 0.3343 | 0.7458930744919147 | 0.411593 |
| ERI | 2022 | 0.2924 | 0.6889692868274467 | 0.396569 |
| ERI | 2020 | 0.2983 | 0.6876090453152602 | 0.389309 |
| ERI | 2021 | 0.3055 | 0.6875180231352463 | 0.382018 |

## Largest negative disagreements (actual below baseline)

| iso3 | year | baseline_value | actual_value | difference_signed |
| --- | --- | --- | --- | --- |
| ARE | 2019 | 0.6678 | 0.4174331550740742 | -0.250367 |
| JOR | 2018 | 0.5446 | 0.3608145031703237 | -0.183785 |
| CMR | 2017 | 0.6545 | 0.4759657068880942 | -0.178534 |
| CMR | 2016 | 0.6519 | 0.4751563816545412 | -0.176744 |
| CMR | 2015 | 0.6436 | 0.4742673885605353 | -0.169333 |

## Profile of actual.csv (WBL/100)

| Statistic | Value |
|---|---|
| Observations | 2,178 |
| Countries | 198 |
| Mean | 0.6818 |
| Median | 0.7071 |
| SD | 0.1543 |
| Skewness | -0.6011 (moderately left skewed) |
| Kurtosis | -0.2972 |

## References
See methodology_refs.bib.
