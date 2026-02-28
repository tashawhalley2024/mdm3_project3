# Women & Religion Dataset

**Research question:** How does religious composition affect the treatment of women?

**Unit:** Country-year | **Period:** 2007-2022 | **Countries:** 198 | **Rows:** 3,164 | **Columns:** 43

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
