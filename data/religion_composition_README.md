# Religion Composition Dataset

**Research question:** How does the religious environment (composition, intensity,
and institutional embedding) shape the treatment of women?

**Unit:** Country-year | **Period:** 2007–2022 | **Countries:** 198 | **Rows:** 3,164 | **Columns:** 20

This dataset is the **independent-variable counterpart** to
`data/women_religion/women_religion_normalised.csv`, which holds the outcome
(treatment-of-women) indicators. Keep them separate and join on `iso3 + year`
for analysis.

All 17 numeric columns are **min-max normalised to [0, 1]** (verified — no values
outside this range). **Higher always means MORE religion** (larger share, more
intense, more institutionally embedded). No values are extrapolated or interpolated —
missing years are `NaN`.

---

## Sub-group 1: Composition — who belongs to each religion

Source: Pew Global Religious Futures (2010 & 2020 estimates) with WRP
national dataset as fallback for countries Pew does not cover.
Values only populated in survey years **2010 and 2020** — all other years NaN.

| Column | What it measures | Coverage |
|--------|-----------------|----------|
| `pct_christian_norm` | Christian share of population | ~12% (2010 & 2020) |
| `pct_muslim_norm` | Muslim share | ~12% |
| `pct_hindu_norm` | Hindu share | ~12% |
| `pct_buddhist_norm` | Buddhist share | ~12% |
| `pct_jewish_norm` | Jewish share | ~12% |
| `pct_unaffiliated_norm` | Religiously unaffiliated share | ~12% |
| `pct_other_norm` | All other religions combined | ~12% |

---

## Sub-group 2: Religious intensity — how religion is practiced or valued

Source: World Values Survey (WVS), accessed via QoG Standard TS Jan 2025.
Survey-based — only available in WVS wave years (typically every 5 years).

| Column | What it measures | Raw scale | Coverage |
|--------|-----------------|-----------|----------|
| `wvs_imprel_norm` | Mean importance of religion in life | 1–4 (higher = more important) | ~7% |
| `wvs_godimp_norm` | Mean importance of God | 1–10 (higher = more important) | ~7% |
| `wvs_godbel_norm` | Proportion of population who believe in God | 0–1 | ~6% |
| `wvs_confch_norm` | Mean confidence in the church/mosque/temple | 1–4 (higher = more confidence) | ~7% |

---

## Sub-group 3: Religious state institutions — religion embedded in law & policy

Source: Pew Global Restrictions on Religion dataset 2007–2022 (sub-questions).
Annual coverage 2007–2022. Higher = more religion embedded in state structures.

| Column | What it measures | Raw scale | Coverage |
|--------|-----------------|-----------|----------|
| `gri_state_religion_norm` | Official or preferred state religion (GRI Q1) | 0/0.5/1 | ~100% |
| `gri_gov_favour_norm` | Government favouritism toward specific religion(s) (GRI Q2) | 0–1 | ~100% |
| `gri_religious_law_norm` | Religious law applied in the legal system (GRI Q3) | 0–1 | ~100% |
| `gri_religious_courts_norm` | Govt-recognised religious courts exist (GRI Q15) | 0/1 | ~100% |
| `gri_blasphemy_norm` | Blasphemy laws in effect (GRX22) | 0/1 | ~81% |
| `gri_apostasy_norm` | Apostasy laws in effect (GRX22) | 0/1 | ~81% |

---

## Normalisation method

    x_norm = (x − min(x)) / (max(x) − min(x))

Applied over all non-null observations in the 2007–2022 panel.
Missing values preserved as NaN — not imputed.

---

## Data sources

| Dataset | Version | Notes |
|---------|---------|-------|
| Pew Global Religious Futures | 2010 & 2020 | Religious composition % |
| World Religion Project (WRP) | National, ~2010 | Fallback composition |
| World Values Survey (WVS) | Via QoG Jan 2025 | Religious intensity |
| Pew Global Restrictions on Religion | 2007–2022 | State institution sub-questions |

---

## Join with women's treatment data

```python
import pandas as pd
comp = pd.read_csv("data/religion_composition/religion_composition_normalised.csv")
women = pd.read_csv("data/women_religion/women_religion_normalised.csv")
merged = women.merge(comp, on=["iso3", "year"], how="left")
```
