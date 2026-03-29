# Women's Treatment & Secularism Dataset

**Research question:** Does institutional secularism improve the legal treatment and welfare of women?

**Unit:** Country-year | **Period:** 2007–2022 | **Countries:** 198 | **Rows:** 3,164 | **Columns:** 36+

All numeric columns are normalised to **[0, 1]** using **robust min-max** (1%/99% winsorisation
before rescaling). **Higher always means better for women.**
Variables originally coded "higher = worse" have been inverted.
Missing values are `NaN`. The one exception is `cedaw_ratified`, a raw binary flag (0/1) not normalised.

**Exception — life expectancy:** `wdi_lifexpf_norm` is normalised using the UNDP HDI fixed
goalposts (min = 20 years, max = 85 years), not sample-driven min-max. This ensures stability
across samples and consistency with international HDI comparisons.

**Interpolated variables** are flagged with companion columns (`pct_interpolated`,
`wvs_interpolated`, `sigi_interpolated`) so analyses can exclude imputed rows.

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

2019 edition filled ±2 years (covering 2017–2021). All other years remain `NaN`.
A companion flag `sigi_interpolated` = 1 marks rows where values are filled rather than directly observed.

| Column | What it measures | Coverage |
|--------|-----------------|----------|
| `sigi_norm` | Overall SIGI composite | ~20% (2017–2021 via ±2yr fill) |
| `sigi_family_norm` | Discrimination in the family (child marriage, inheritance, parental authority) | ~20% |
| `sigi_physical_norm` | Restricted physical integrity (violence, FGM, reproductive autonomy) | ~20% |
| `sigi_resources_norm` | Restricted access to productive and financial resources | ~20% |
| `sigi_civil_norm` | Restricted civil liberties (freedom of movement, dress codes, political voice) | ~20% |
| `sigi_interpolated` | Flag: 1 if SIGI values are filled (not from exact survey year) | — |

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

**Standard variables** — robust min-max with 1%/99% winsorisation:

    x_clipped = clip(x, percentile_1, percentile_99)
    x_norm = (x_clipped − min(x_clipped)) / (max(x_clipped) − min(x_clipped))

Applied over all non-null observations in the 2007–2022 panel. Winsorisation prevents
outliers from compressing the bulk of observations into a narrow range.

**Life expectancy** — UNDP HDI fixed goalposts:

    x_norm = (x − 20) / (85 − 20)    [clipped to 0–1]

Min = 20 years, max = 85 years. These bounds are externally justified and stable
regardless of sample composition. Source: UNDP Human Development Report Technical Notes (2024).

## Scoring pipeline (WBL-based overall index)

The alternative WBL-based treatment index is produced by a separate pipeline:

```
src/data_reading.py     reads WBL 2024 Excel + health indicators
                        outputs 10 group CSVs (one per WBL legal domain + health group)

src/scoring.py          normalises each group to [0, 1]
                        life expectancy: UNDP HDI fixed bounds (min=20, max=85)
                        computes group score as unweighted mean of indicators within group
                        merges 10 group scores via outer join on ISO Code + Year
                        overall_score = unweighted mean of all 10 group scores

output/overall_score.csv   ISO Code, Economy, Year, overall_score
                           198 countries, 2013–2022
```

Equal weighting across groups is used by default. No theoretical basis exists for
differential weights; equal weights maximise reproducibility and transparency.

---

## Data sources

| Dataset | Version |
|---------|---------|
| V-Dem | CY Core v15 |
| QoG Standard TS | Jan 2025 |
| Pew Global Restrictions on Religion | 2007–2022 |
| EPR | EPR-2021 |
| CIRI | via QoG |
| World Bank WDI | via QoG |
| World Bank WBL | 2024 (1971–2024) |
| UNDP Human Development Reports | 2025 |
| OECD SIGI | 2019 |
| DHS Program | Various years |
