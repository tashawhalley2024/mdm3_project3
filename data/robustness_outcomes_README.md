# Gender Gap Panel Dataset

**Research question:** Does secularism improve the welfare and treatment of
women relative to men?

**Unit:** Country-year | **Period:** 2007-2022
**Countries:** up to 198 | **Rows:** 3,164

This panel provides the **comparative outcome variables** for the secularism
analysis. Use it alongside `data/secularism_composition/secularism_composition_normalised.csv`
(predictors) and `data/women_secularism/women_secularism_normalised.csv`
(absolute women's welfare outcomes).

All `_norm` columns are min-max scaled to [0, 1] over the 2007-2022 panel.

---

## Gender inequality indices

| Column | Source | Direction | Coverage |
|--------|--------|-----------|----------|
| `gii` / `gii_norm` | UNDP HDR 2025 | Higher = more inequality | ~80% |
| `gdi` / `gdi_norm` | UNDP HDR 2025 | Higher = more gender parity in HDI | ~94% |
| `hdi_f` / `hdi_f_norm` | UNDP HDR 2025 | Female Human Development Index | ~94% |
| `hdi_m` / `hdi_m_norm` | UNDP HDR 2025 | Male Human Development Index | ~94% |
| `hdi_gap` / `hdi_gap_norm` | Computed: hdi_f - hdi_m | Negative = women lower HDI | ~94% |

## WEF Global Gender Gap Index (via QoG)

All sub-indices: 0 = complete inequality, 1 = full parity.

| Column | Sub-index | Coverage |
|--------|-----------|----------|
| `gggi_ggi` / `gggi_ggi_norm` | Overall GGG Index | ~67% |
| `gggi_eas` / `gggi_eas_norm` | Economic Activity & Opportunity | ~67% |
| `gggi_hss` / `gggi_hss_norm` | Health & Survival | ~67% |
| `gggi_pes` / `gggi_pes_norm` | Political Empowerment | ~67% |

## Male welfare variables (QoG / WDI / WHO)

| Column | Measure | Direction |
|--------|---------|-----------|
| `wdi_lifexpm` / `_norm` | Male life expectancy (years) | Higher = better |
| `wdi_lfpmilo15` / `_norm` | Male LFP rate, 15+ ILO (%) | Higher = more participation |
| `wdi_mortm` / `_norm` | Male adult mortality (per 1,000) | Higher = worse |
| `who_homm` / `_norm` | Male homicide rate (per 100,000) | Higher = worse |
| `who_infmortm` / `_norm` | Male infant mortality (per 1,000) | Higher = worse |

## Female welfare variables (QoG / WDI / WHO)

| Column | Measure | Direction |
|--------|---------|-----------|
| `wdi_lifexpf` / `_norm` | Female life expectancy (years) | Higher = better |
| `wdi_lfpfilo15` / `_norm` | Female LFP rate, 15+ ILO (%) | Higher = more participation |
| `wdi_mortf` / `_norm` | Female adult mortality (per 1,000) | Higher = worse |
| `who_homf` / `_norm` | Female homicide rate (per 100,000) | Higher = worse |
| `who_infmortf` / `_norm` | Female infant mortality (per 1,000) | Higher = worse |

## Computed gender gap variables (female - male)

Positive = women better off; negative = women worse off.

| Column | Formula | Typical sign |
|--------|---------|-------------|
| `life_exp_gap` / `_norm` | lifexpf - lifexpm | +6 yrs (women live longer) |
| `lfp_gap` / `_norm` | lfpf - lfpm | Negative (women work less) |
| `mort_gap` / `_norm` | mortf - mortm | Negative (women die less) |
| `infmort_gap` / `_norm` | infmortf - infmortm | Small negative |
| `hom_gap` / `_norm` | homf - homm | Negative (women killed less) |

---

## Data sources

| Dataset | Version | Citation |
|---------|---------|---------|
| UNDP Human Development Reports | 2025 composite time-series | hdr.undp.org |
| WEF Global Gender Gap Report | 2006-2022, via QoG Jan 2025 | weforum.org / qog.gu.se |
| World Development Indicators | Via QoG Jan 2025 | worldbank.org |
| WHO Global Health Observatory | Via QoG Jan 2025 | who.int |

---

## Join with predictors

```python
import pandas as pd
gap    = pd.read_csv("data/processed/gender_gap_panel.csv")
comp   = pd.read_csv("data/secularism_composition/secularism_composition_normalised.csv")
merged = gap.merge(comp, on=["iso3", "year"], how="left")
```
