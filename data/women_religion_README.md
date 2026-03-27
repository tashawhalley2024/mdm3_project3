# Women & Religion Dataset

**Research question:** How does religious composition affect the treatment of women?

**Unit:** Country-year | **Period:** 2007–2022 | **Countries:** 198 | **Rows:** 3,164 | **Columns:** 36

All 32 numeric columns are min-max normalised to **[0, 1]** (verified — no values outside this range).
**Higher always means better for women.**
Variables originally coded "higher = worse" have been inverted.
Missing values are `NaN` — no values are extrapolated or interpolated.
The one exception is `cedaw_ratified`, a raw binary flag (0/1) that is not normalised.

---

## Identifiers

| Column | Description |
|--------|-------------|
| `iso3` | ISO 3166-1 alpha-3 country code |
| `country` | Country name |
| `year` | Year (2007–2022) |

---

## Treatment of women — outcome variables (higher = better)

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
| `wdi_litradf_norm` | Female adult literacy rate | World Bank | 21% |
| `wdi_homicidesf_norm` | Female homicide rate per 100k (inverted) | World Bank | 48% |
| `wdi_wip_norm` | Women in parliament % | World Bank | 95% |
| `wgov_minfem_norm` | % of cabinet ministers who are women | WGOV | 86% |
| `women_treatment_index` | Composite — unweighted mean of the 13 columns above | — | 99% |

---

## Religious environment — covariates (higher = less restriction)

Annual observed data throughout.

| Column | What it measures | Source | Coverage |
|--------|-----------------|--------|----------|
| `gri_norm` | Government Restrictions on Religion Index (inverted) | Pew | 100% |
| `shi_norm` | Social Hostilities Index — societal religious conflict (inverted) | Pew | 100% |
| `ciri_relfre_norm` | Religious freedom score | CIRI | 84% |

---

## Controls (higher = better institutions / less exclusion)

Annual observed data throughout.

| Column | What it measures | Source | Coverage |
|--------|-----------------|--------|----------|
| `ciri_physint_norm` | Physical integrity rights | CIRI | 91% |
| `v2x_rule_norm` | Rule of law | V-Dem | 88% |
| `v2x_civlib_norm` | Civil liberties | V-Dem | 88% |
| `v2x_egal_norm` | Egalitarian democracy | V-Dem | 88% |
| `epr_excl_share_norm` | Ethnic group exclusion from power (inverted) | EPR | 77% |

---

## Discriminatory social institutions — SIGI (higher = less discrimination)

Values only present in **2019**. All other years are `NaN`.

| Column | What it measures | Coverage |
|--------|-----------------|----------|
| `sigi_norm` | Overall SIGI composite | 4% |
| `sigi_family_norm` | Discrimination in the family (child marriage, inheritance, parental authority) | 6% |
| `sigi_physical_norm` | Restricted physical integrity (violence, FGM, reproductive autonomy) | 4% |
| `sigi_resources_norm` | Restricted access to productive and financial resources | 4% |
| `sigi_civil_norm` | Restricted civil liberties (freedom of movement, dress codes, political voice) | 4% |

---

## Gender Inequality Index (higher = less inequality)

| Column | What it measures | Source | Coverage |
|--------|-----------------|--------|----------|
| `gii_norm` | UNDP Gender Inequality Index — reproductive health, empowerment, labour market (inverted) | UNDP | 81% |

---

## CEDAW treaty ratification

| Column | What it measures | Coverage |
|--------|-----------------|----------|
| `cedaw_ratified` | 1 if ratified by that year, 0 if not (binary, not normalised) | 96% |
| `cedaw_years_since_norm` | Years since ratification, normalised — higher = ratified longer ago | 96% |

---

## DHS domestic violence indicators (higher = less violence)

Survey-based — only years a DHS survey was conducted in that country. All other years are `NaN`.

| Column | What it measures | Coverage |
|--------|-----------------|----------|
| `dhs_violence_norm` | % of women aged 15–49 who have ever experienced physical violence (inverted) | 3% |
| `dhs_attitude_norm` | % of women who agree wife-beating is justified for at least one reason (inverted) | 4% |

---

## Modelled violence estimate (higher = less violence)

Modelled estimate for **2018 only**. All other years are `NaN`.

| Column | What it measures | Source | Coverage |
|--------|-----------------|--------|----------|
| `wbl_violence_norm` | % of ever-partnered women aged 15–49 subjected to physical and/or sexual violence in the past 12 months (inverted) | World Bank | 5% |

---

## Normalisation

    x_norm = (x − min(x)) / (max(x) − min(x))

Applied over all non-null observations in the 2007–2022 panel.

## Data sources

| Dataset | Version |
|---------|---------|
| V-Dem | CY Core v15 |
| QoG Standard TS | Jan 2025 |
| Pew Global Restrictions on Religion | 2007–2022 |
| EPR | EPR-2021 |
| CIRI | via QoG |
| World Bank WDI | via QoG |
| UNDP Human Development Reports | 2025 |
| OECD SIGI | 2019 |
| DHS Program | Various years |
