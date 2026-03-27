# Secularism & Religious Environment Dataset

**Research question:** Does secularism improve the welfare and treatment of women
relative to men?

**Unit:** Country-year | **Period:** 2007-2022 | **Countries:** 198

This dataset holds the **independent variables** (secularism predictors) for the
analysis. The outcome dataset is
`data/women_secularism/women_secularism_normalised.csv`. Join on `iso3 + year`.

All numeric columns are **robust min-max normalised to [0, 1]** (1st/99th pct
winsorisation applied before scaling).
For composition, intensity, and GRI state-institution variables: **higher = more
religion / less secular**. For `v2clrelig_norm`: **higher = more secular freedom**
(direction is reversed -- see Sub-group 3a below).

---

## Sub-group 1: Composition -- who belongs to each religion

Source: Pew Global Religious Futures (2010 & 2020 estimates) with WRP
national dataset as fallback for countries Pew does not cover.
Linear interpolation applied between 2010 and 2020; backward-filled 3 years
(2007-2009) and forward-filled 2 years (2021-2022). Flagged in `pct_interpolated`.

| Column | What it measures |
|--------|-----------------|
| `pct_christian_norm` | Christian share of population |
| `pct_muslim_norm` | Muslim share |
| `pct_hindu_norm` | Hindu share |
| `pct_buddhist_norm` | Buddhist share |
| `pct_jewish_norm` | Jewish share |
| `pct_unaffiliated_norm` | Religiously unaffiliated share |
| `pct_other_norm` | All other religions combined |
| `pct_interpolated` | 0=original data, 1=interpolated/filled, NaN=missing |

---

## Sub-group 2: Religious intensity -- how religion is practiced or valued

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

## Normalisation method

    x_wins = clip(x, p01, p99)   # 1st/99th pct winsorisation
    x_norm = (x_wins - min) / (max - min)

Missing values preserved as NaN -- not imputed.

---

## Data sources

| Dataset | Version | Notes |
|---------|---------|-------|
| Pew Global Religious Futures | 2010 & 2020 | Religious composition % |
| World Religion Project (WRP) | National, ~2010 | Fallback composition |
| World Values Survey (WVS) | Via QoG Jan 2025 | Religious intensity |
| Pew Global Restrictions on Religion | 2007-2022 | State institution sub-questions |
| V-Dem Core | v15, 2007-2022 | Freedom of religion (v2clrelig) |
| World Bank WDI | Via QoG Jan 2025 | GDP per capita |

---

## Join with women's treatment data

```python
import pandas as pd
comp = pd.read_csv("data/secularism_composition/secularism_composition_normalised.csv")
women = pd.read_csv("data/women_secularism/women_secularism_normalised.csv")
merged = women.merge(comp, on=["iso3", "year"], how="left")
```
