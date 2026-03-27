# Women's Welfare Dataset

**Research question:** Does secularism improve the welfare and treatment of women
relative to men?

**Period:** 2007-2022  |  **Unit:** Country-year  |  **Countries:** 198

This dataset holds the **outcome variables** for the analysis. Secularism
predictors (GRI state institutions, v2clrelig, WVS religiosity, religious
composition shares) are held separately in
`data/secularism_composition/secularism_composition_normalised.csv`.
Join both datasets on `iso3 + year` for analysis.

---

## File

`women_secularism_normalised.csv`

All numeric variables are **robust min-max normalised to [0, 1]** over the
full 2007-2022 panel (1st/99th pct winsorisation applied before scaling).
**Higher always means better for women / more secular** (see direction notes below).
Variables that were originally "higher = worse" have been inverted (1 - x) after normalisation.

---

## Variables

### Identifiers
| Column | Description |
|--------|-------------|
| `iso3` | ISO 3166-1 alpha-3 country code |
| `country` | Country name |
| `year` | Year (2007-2022) |

### Outcome: women's welfare (normalised, higher = better)
| Column | Original variable | Source | Raw scale | Inverted? |
|--------|------------------|--------|-----------|-----------|
| `v2x_gender_norm` | Women's political empowerment index | V-Dem | 0-1 | No |
| `v2x_gencl_norm` | Women's civil liberties | V-Dem | 0-1 | No |
| `v2x_gencs_norm` | Women's civil society participation | V-Dem | 0-1 | No |
| `v2x_genpp_norm` | Women's political participation | V-Dem | 0-1 | No |
| `v2xpe_exlgender_norm` | Political exclusion by gender | V-Dem | 0-1 | **Yes** |
| `v2lgfemleg_norm` | % women in legislature | V-Dem | 0-100 | No |
| `wdi_wombuslawi_norm` | Women, Business & the Law index | World Bank | 0-100 | No |
| `wdi_lifexpf_norm` | Female life expectancy | World Bank | years | No |
| `wdi_lfpf_norm` | Female labour force participation | World Bank | 0-100 | No |
| `wdi_litradf_norm` | Female adult literacy rate | World Bank / UNESCO UIS | 0-100 | No |
| `wdi_homicidesf_norm` | Female homicide rate per 100k | World Bank | >0 | **Yes** |
| `wdi_wip_norm` | Women in parliament % | World Bank | 0-100 | No |
| `wgov_minfem_norm` | % female ministers | QoG/WGOV | 0-100 | No |
| `women_index_n_vars` | Number of outcome vars contributing to composite | -- | 0-13 | -- |
| `women_treatment_index` | **Composite index** -- unweighted mean; requires >=8 of 13 vars | -- | 0-1 | -- |

### Secularism environment (covariates from this dataset)
| Column | Original variable | Source | Raw scale | Inverted? | Interpretation |
|--------|------------------|--------|-----------|-----------|----------------|
| `gri_norm` | Government Restrictions Index | Pew | 0-10 | **Yes** | 1 = fully secular (no restriction) |
| `shi_norm` | Social Hostilities Index | Pew | 0-10 | **Yes** | 1 = no religious hostility |
| `ciri_relfre_norm` | Religious freedom | CIRI | 0-2 | No | 1 = full freedom |

> These measure the state's religious restriction level and societal hostility.
> Detailed secularism predictors (GRI sub-questions, v2clrelig, WVS, pct_*)
> are in the secularism_composition dataset.

### Controls
| Column | Original variable | Source | Raw scale | Inverted? |
|--------|------------------|--------|-----------|-----------|
| `ciri_physint_norm` | Physical integrity rights | CIRI | 0-8 | No |
| `v2x_rule_norm` | Rule of law | V-Dem | 0-1 | No |
| `v2x_civlib_norm` | Civil liberties | V-Dem | 0-1 | No |
| `v2x_egal_norm` | Egalitarian democracy | V-Dem | 0-1 | No |
| `epr_excl_share_norm` | Share of excluded ethnic groups | EPR | 0-1 | **Yes** |

### Auxiliary flags
| Column | Description |
|--------|-------------|
| `epr_excl_2022_ffill` | True if epr_excl_share was forward-filled from 2021 to 2022 |
| `wdi_litradf_source` | Source of literacy rate: "wdi", "uis", or "missing" |

---

## Normalisation method

Robust min-max normalisation: 1st and 99th percentile winsorisation applied
first (clips extreme outliers), then scaled to [0, 1]:

    x_wins = clip(x, p01, p99)
    x_norm = (x_wins - min(x_wins)) / (max(x_wins) - min(x_wins))

For inverted variables:

    x_norm = 1 - (x_wins - min(x_wins)) / (max(x_wins) - min(x_wins))

Missing values are preserved as `NaN` -- they are not imputed.

---

## Composite index threshold

`women_treatment_index` requires at least 8 of 13 outcome variables to be
non-null for the country-year. Rows with fewer than 8 variables present are
coded as NaN rather than averaged from sparse data. The `women_index_n_vars`
column records the actual count of contributing variables.

---

## Data sources

| Dataset | Version | Citation |
|---------|---------|----------|
| V-Dem | CY Core v15 | Coppedge et al. (2024). V-Dem Codebook v15. |
| QoG Standard TS | Jan 2025 | Teorell et al. (2025). The QoG Standard Dataset. |
| Pew GRI/SHI | 2007-2022 | Pew Research Center Global Restrictions on Religion. |
| EPR | EPR-2021 | Cederman, Wimmer & Min (2010). |
| CIRI | via QoG | Cingranelli, Richards & Clay (2014). |
| World Bank WDI | via QoG | World Bank Open Data. |
| UNESCO UIS | optional | UNESCO Institute for Statistics (literacy fallback). |

---

## Known issues

- `wdi_litradf` (female literacy) is sparse -- many country-years missing as WDI
  does not collect literacy annually. UNESCO UIS fills gaps where available.
- `wdi_homicidesf` has moderate missingness in fragile states.
- EPR data ends at 2021; `epr_excl_share_norm` for 2022 is forward-filled from
  2021 (flagged in `epr_excl_2022_ffill`).
- QoG had 96 duplicate (iso3, year) rows (known upstream issue); first occurrence kept.
