# data/

Analysis-ready, normalised input datasets. No raw source files are included here — see [`docs/DATA_SOURCES.md`](../docs/DATA_SOURCES.md) for original provenance.

All normalisation uses **robust min-max** (1%/99% winsorisation, then scale to [0,1]) unless otherwise noted. Life expectancy variables use UNDP HDI fixed goalposts (min = 20, max = 85 years).

---

## Dataset Overview

| File | Rows | Countries | Years | Purpose |
|---|---|---|---|---|
| `wbl_treatment_index.csv` | 2,222 | ~168 | 2013-2022 | **Active** outcome index -- WBL legal rights + health |
| `women_secularism_normalised.csv` | 3,164 | ~198 | 2007-2022 | Alternative outcome -- 13-component composite |
| `secularism_composition_normalised.csv` | 3,164 | ~198 | 2007-2022 | Secularism predictor variables |
| `gender_gap_panel.csv` | 3,164 | ~198 | 2007-2022 | Robustness outcomes (GII, GDI, WEF GGG, gaps) |

---

## File Details

### `wbl_treatment_index.csv` -- Active Outcome Index
- **Source:** World Bank WBL 2024 (10 legal domains) + WDI life expectancy + maternal mortality
- **Key variable:** `wbl_treatment_index` -- equal-weight average of normalised domain scores
- **Life expectancy:** normalised using UNDP HDI fixed goalposts
- See `wbl_treatment_index_README.md` for column-by-column details

### `women_secularism_normalised.csv` -- Composite Outcome Index
- **Source:** V-Dem v15 (political/civil rights), QoG/WDI (labour, health, governance), WHO
- **Key variable:** `women_treatment_index` -- 13-component composite, equal weights
- **Coverage advantage:** 2007-2022 gives more within-country variation than WBL index
- See `women_secularism_README.md`

### `secularism_composition_normalised.csv` -- Predictor Dataset
- **Key variables:**
  - `gri_religious_courts_norm` -- **focal predictor** (Pew GRI separate religious courts)
  - `gri_state_religion_norm`, `gri_religious_law_norm`, `gri_blasphemy_norm`, `gri_apostasy_norm`
  - `v2clrelig_norm` -- V-Dem religious civil liberties
  - `log_gdppc_norm` -- log GDP per capita (control)
  - `pct_muslim_norm` -- Muslim population share (WRP, interpolated)
  - `pct_interpolated` flag -- 1 if religious composition was linearly interpolated
- See `secularism_composition_README.md`

### `gender_gap_panel.csv` -- Robustness Outcomes
- **Key variables:** `gii_norm` (Gender Inequality Index), `gdi_norm` (Gender Development Index), `wef_ggg_norm` (WEF Global Gender Gap), `life_exp_gap_norm`, `lfp_gap_norm`
- **Coverage:** GII 80%, GDI 88%, WEF GGG 67% of country-years
- See `gender_gap_panel_README.md`

---

## Interpolation Flags

- `wvs_interpolated = 1` in `secularism_composition_normalised.csv` indicates WVS religiosity values were linearly interpolated or forward/back-filled for that country-year.

---

<!-- Original group project README preserved below for provenance -->

## Original group project dataset description

---

## Files

### `women_religion_normalised.csv`

The main analysis dataset. All 29+ numeric columns are min-max normalised to **[0, 1]**
(verified — no values outside this range). Missing values are `NaN`, not imputed.
**Higher always means better for women, or a larger share of that religion.**
Variables originally coded "higher = worse" have been inverted.

**No values are extrapolated or interpolated.** Variables are only populated in the
years the source data was actually collected — all other years are `NaN`.

#### Identifiers

| Column | Description |
|--------|-------------|
| `iso3` | ISO 3166-1 alpha-3 country code |
| `country` | Country name |
| `year` | Year (2007-2022) |

#### Treatment of women — outcome variables (higher = better)

Annual observed data throughout.

| Column | What it measures | Source | Coverage |
|--------|-----------------|--------|----------|
| `v2x_gender_norm` | Women's political empowerment index | V-Dem | 88% |
| `v2x_gencl_norm` | Women's civil liberties | V-Dem | 88% |
| `v2x_gencs_norm` | Women's civil society participation | V-Dem | 88% |
| `v2x_genpp_norm` | Women's political participation | V-Dem | 88% |
| `v2xpe_exlgender_norm` | Political exclusion by gender (inverted) | V-Dem | 88% |
| `v2lgfemleg_norm` | % women in national legislature | V-Dem | 86% |
| `wdi_wombuslawi_norm` | Women, Business & the Law index | World Bank | 93% |
| `wdi_lifexpf_norm` | Female life expectancy | World Bank | 95% |
| `wdi_lfpf_norm` | Female labour force participation rate | World Bank | 89% |
| `wdi_litradf_norm` | Female adult literacy rate | World Bank | **21% — sparse** |
| `wdi_homicidesf_norm` | Female homicide rate per 100k (inverted) | World Bank | **48% — sparse** |
| `wdi_wip_norm` | Women in parliament % | World Bank | 95% |
| `wgov_minfem_norm` | % of cabinet ministers who are women | WGOV | 86% |
| `women_treatment_index` | Composite — unweighted mean of the 13 columns above | — | 99% |

#### Religious composition — independent variables (higher = larger share)

Sourced from Pew Religious Composition Dataset. Values only present in actual
survey years: **2010 and 2020**. All other years are `NaN`.

| Column | What it measures | Coverage |
|--------|-----------------|----------|
| `pct_christian_norm` | Christian share of population | 12% (years 2010 & 2020 only) |
| `pct_muslim_norm` | Muslim share of population | 12% |
| `pct_hindu_norm` | Hindu share of population | 12% |
| `pct_buddhist_norm` | Buddhist share of population | 12% |
| `pct_jewish_norm` | Jewish share of population | 12% |
| `pct_unaffiliated_norm` | Religiously unaffiliated share | 12% |
| `pct_other_norm` | All other religions combined | 12% |

#### Religious environment — covariates (higher = less restriction)

Annual observed data throughout.

| Column | What it measures | Source | Coverage |
|--------|-----------------|--------|----------|
| `gri_norm` | Government Restrictions on Religion Index (inverted) | Pew | 100% |
| `shi_norm` | Social Hostilities Index — societal religious conflict (inverted) | Pew | 100% |
| `ciri_relfre_norm` | Religious freedom score | CIRI | 84% |

#### Controls (higher = better institutions / less exclusion)

Annual observed data throughout.

| Column | What it measures | Source | Coverage |
|--------|-----------------|--------|----------|
| `ciri_physint_norm` | Physical integrity rights | CIRI | 91% |
| `v2x_rule_norm` | Rule of law | V-Dem | 88% |
| `v2x_civlib_norm` | Civil liberties | V-Dem | 88% |
| `v2x_egal_norm` | Egalitarian democracy | V-Dem | 88% |
| `epr_excl_share_norm` | Ethnic group exclusion from power (inverted) | EPR | 77% |

#### Discriminatory social institutions — SIGI (higher = less discrimination)

Values only present in actual edition year: **2019** (within the 2007-2022 window).
The 2023 edition falls outside the window. All other years are `NaN`.

| Column | What it measures | Coverage |
|--------|-----------------|----------|
| `sigi_norm` | Overall SIGI composite | 4% (year 2019 only) |
| `sigi_family_norm` | Discrimination in the family (child marriage, inheritance, parental authority) | 6% |
| `sigi_physical_norm` | Restricted physical integrity (violence, FGM, reproductive autonomy) | 4% |
| `sigi_resources_norm` | Restricted access to productive and financial resources | 4% |
| `sigi_civil_norm` | Restricted civil liberties (freedom of movement, dress codes, political voice) | 4% |

#### Gender Inequality Index (higher = less inequality)

Annual observed data 1990-2023 from UNDP Human Development Reports.

| Column | What it measures | Coverage |
|--------|-----------------|----------|
| `gii_norm` | UNDP Gender Inequality Index — reproductive health, empowerment, labour market (inverted) | 81% |

#### CEDAW treaty ratification

Whether each country had ratified the UN women's rights convention by that year.
Source: World Politics Data Lab.

| Column | What it measures | Coverage |
|--------|-----------------|----------|
| `cedaw_ratified` | 1 if ratified by that year, 0 if not (binary, not normalised) | 96% |
| `cedaw_years_since_norm` | Years since ratification, normalised. Higher = ratified longer | 96% |

#### DHS domestic violence indicators (higher = better / less violence)

Survey-based — only years a DHS survey was conducted in that country
(typically every 5-7 years). All other years are `NaN`.

| Column | What it measures | Coverage |
|--------|-----------------|----------|
| `dhs_violence_norm` | % of women aged 15-49 who have ever experienced physical violence (inverted) | 3% |
| `dhs_attitude_norm` | % of women who agree wife-beating is justified for at least one reason (inverted) | 4% |

#### Modelled violence estimate — WHO/World Bank (higher = less violence)

Modelled cross-national estimate for **year 2018 only**. All other years are `NaN`.
Source: World Bank Gender Portal (via collaborator dataset).

| Column | What it measures | Coverage |
|--------|-----------------|----------|
| `wbl_violence_norm` | % of ever-partnered women aged 15-49 subjected to physical and/or sexual violence in the past 12 months (modelled estimate, inverted) | **5% (year 2018 only)** |

---

### `README.md`

This file.
