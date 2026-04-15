# Secularism & Religious Environment Dataset

**Research question:** Does secularism improve the welfare and treatment of women
relative to men?

**Unit:** Country-year | **Period:** 2007-2022 | **Countries:** 198

This dataset holds the **independent variables** (secularism predictors) for the
analysis. The outcome dataset is `data/outcome_wbl.csv` (WBL-based treatment
index). Join on `iso3 + year`.

All numeric columns are **robust min-max normalised to [0, 1]** (1st/99th pct
winsorisation applied before scaling).
For composition, intensity, and GRI state-institution variables: **higher = more
religion / less secular**. For `v2clrelig_norm`: **higher = more secular freedom**
(direction is reversed -- see Sub-group 3a below).

---

## Sub-group 0: Religious composition (optional, merged in-memory)

Source: Pew Global Religious Futures / World Religion Project, via
`data/religion_composition_normalised.csv`. These columns are **merged at
load time** inside `analysis/run_analysis.py:load_and_merge` and are NOT
stored in `predictors.csv` itself.

| Column | What it measures |
|--------|-----------------|
| `pct_unaffiliated_norm` | % unaffiliated (Pew GRF), min-max normalised |
| `pct_other_norm` | % adhering to "other" religions, min-max normalised |

**Coverage note**: composition is observed only in **2010 and 2020** (~12%
of country-years). After merging with `outcome_wbl.csv` (2013-2023 coverage),
only 2020 overlaps, so these columns are unusable in the T2/T4 panel
specifications and are kept OUT of `GRI_PANEL_COLS` by default. They are
currently referenced only by the composite secularism builder (see sub-group 4).

---

## Sub-group 1: Religious intensity -- how religious societies are

Source: World Values Survey (WVS), accessed via QoG Standard TS Jan 2025.
Survey-based -- only available in WVS wave years (typically every 5 years).
Within-country linear interpolation between wave years; +-2yr edge fill.
Flagged in `wvs_interpolated`.

| Column | What it measures | Raw scale |
|--------|-----------------|-----------|
| `wvs_imprel_norm` | Mean importance of religion in life | 1-4 |
| `wvs_godimp_norm` | Mean importance of God | 1-10 |
| `wvs_godbel_norm` | Proportion who believe in God | 0-1 |
| `wvs_confch_norm` | Mean confidence in the church/mosque/temple | 1-4 |
| `wvs_interpolated` | 0=original data, 1=interpolated/filled, NaN=missing |

---

## Sub-group 3: Religious state institutions -- religion embedded in law & policy

Source: Pew Global Restrictions on Religion dataset 2007-2022 (sub-questions).
Annual coverage 2007-2022. Higher = more religion embedded in state structures.

| Column | What it measures |
|--------|-----------------|
| `gri_state_religion_norm` | Official or preferred state religion (GRI Q1) |
| `gri_gov_favour_norm` | Government favouritism toward specific religion(s) (GRI Q2) |
| `gri_religious_law_norm` | Religious law applied in the legal system (GRI Q3) |
| `gri_religious_courts_norm` | Govt-recognised religious courts exist (GRI Q15) |
| `gri_blasphemy_norm` | Blasphemy laws in effect (GRX22) |
| `gri_apostasy_norm` | Apostasy laws in effect (GRX22) |

---

## Sub-group 3a: Secular tolerance -- freedom of religion (V-Dem)

Source: V-Dem Core v15, annual 2007-2022.
**NOTE: direction is OPPOSITE to other vars** -- higher = MORE freedom of religion
(more secular tolerance).

| Column | What it measures |
|--------|-----------------|
| `v2clrelig_norm` | Freedom to practise religion (V-Dem v2clrelig) |

---

## GDP control

`log_gdppc_norm`: log(GDP per capita, constant 2015 USD), robust min-max normalised.
Source: World Bank WDI via QoG Standard TS Jan 2025.
Pre-built here so analysis scripts need not load raw QoG separately.

---

## Sub-group 4: Composite secularism index (derived, in-memory)

Added 2026-04-15 as part of TODO Item 2. Two variants are built at load
time by `analysis.utils.build_secularism_composite(df)` and attached to
the working dataframe; they are NOT stored on disk.

| Column | Construction |
|--------|-------------|
| `composite_secularism_norm` | Equal-weight z-score of three dimensions; primary headline |
| `composite_secularism_pca_norm` | First principal component over the 11 inputs; robustness variant |

**Dimensions and orientation** (all set to "higher = more religion / less secular"):
- **Institutional** — 6 GRI sub-items (state religion, gov favouritism,
  religious law, religious courts, blasphemy, apostasy).
- **Attitudinal** — `v2clrelig_norm`, **sign-flipped before aggregation**
  because its native orientation in this file is opposite (see Sub-group 3a).
- **Behavioural** — 4 WVS intensity items (imprel, godimp, godbel, confch).

**Equal-weight**: each dimension is z-scored (NaN-aware); the three
z-scores are row-averaged. **Dimension-fallback**: if one dimension is
entirely NaN for a row, the composite uses the mean of the remaining two.
After averaging, the composite is passed through robust_minmax to [0, 1].

**PCA variant**: each input column is mean-imputed, then standardised.
First PC of the 11 standardised columns; sign-aligned so that the loading
on `gri_state_religion_norm` is positive; then robust_minmax to [0, 1].
**Caveat**: column-mean imputation on heterogeneous-coverage inputs (WVS
coverage ~44% after interpolation; GRI coverage 100%) reduces post-fill
variance in imputed columns, so the first PC loads more heavily on the
fully-covered columns. Observed empirically: the PC1 loadings cluster
around 0.3-0.4 for WVS/v2clrelig and 0.07-0.29 for GRI. The PCA variant
is therefore a useful robustness cross-check but is **not** an
independent methodological alternative to the equal-weight composite.

**Diagnostic note for the composite**: `n_changers` saturates at ≈
`n_clusters` because the composite is continuous by construction, so it
loses its discriminating value. `within_sd` becomes the load-bearing
diagnostic for whether the composite has meaningful within-country
variation. The analysis log additionally reports `n_changers` restricted
to `wvs_interpolated == 0` rows — this is the "real movement" count,
purged of WVS interpolator arithmetic.

**New in GRI_PANEL_COLS (2026-04-15)**: `gri_gov_favour_norm` (GRI Q2) —
previously in this file but silently dropped from every regression.
Now active with 4 distinct values and 77/198 changer countries; T4 Mundlak
_mean count goes from 9 to 10 regressors as a result.

---

## Normalisation method

    x_wins = clip(x, p01, p99)   # 1st/99th pct winsorisation
    x_norm = (x_wins - min) / (max - min)

Missing values preserved as NaN -- not imputed.

---

## Data sources

| Dataset | Version | Notes |
|---------|---------|-------|
| World Values Survey (WVS) | Via QoG Jan 2025 | Societal religious strength |
| Pew Global Restrictions on Religion | 2007-2022 | State institution sub-questions |
| V-Dem Core | v15, 2007-2022 | Freedom of religion (v2clrelig) |
| World Bank WDI | Via QoG Jan 2025 | GDP per capita |

---

## Join with women's treatment data

```python
import pandas as pd
predictors = pd.read_csv("data/predictors.csv")
outcome    = pd.read_csv("data/outcome_wbl.csv")
merged     = outcome.merge(predictors, on=["iso3", "year"], how="left")
```
