# Data Sources

All raw data files are **not included in this repository** due to redistribution restrictions and/or file size. This document lists the original sources so the pipeline can be reproduced.

---

## Primary Sources

### Pew Research Center — Global Restrictions on Religion (GRI)
- **Variables used:** `gri_religious_courts_norm`, `gri_state_religion_norm`, `gri_religious_law_norm`, `gri_blasphemy_norm`, `gri_apostasy_norm`
- **Coverage:** ~197 countries, 2007–2022 (annual)
- **Access:** Pew Research Center dataset portal — requires registration. Dataset: *Global Restrictions on Religion 2007–2022*.
- **Citation:** Pew Research Center (2023). *Global Restrictions on Religion*.

### V-Dem — Varieties of Democracy (CY-Core v15)
- **Variables used:** `v2x_gender`, `v2lgfemleg`, `v2x_gencl`, `v2clrelig`, `v2x_rule`, `v2x_civlib`, `v2x_egal`
- **Coverage:** ~179 countries, 2007–2022
- **Access:** [https://www.v-dem.net/data/the-v-dem-dataset/](https://www.v-dem.net/data/the-v-dem-dataset/) — free download.
- **Citation:** Coppedge, Michael et al. (2024). *V-Dem [Country-Year/Country-Date] Dataset v15*. Varieties of Democracy (V-Dem) Project.

### Quality of Government (QoG) — Standard Time-Series Dataset
- **Variables used:** `wdi_wip`, `wdi_wombuslawi`, `wdi_lfpf`, `wdi_litradf`, `wdi_homicidesf`, `wdi_lifexpf`, `wdi_lifexpm`, `wdi_lfpm`, `wgov_minfem`, `wdi_gdppccon2017`, regional covariates
- **Coverage:** ~196 countries, 2007–2022
- **Access:** [https://www.gu.se/en/quality-government/qog-data](https://www.gu.se/en/quality-government/qog-data) — Jan 2025 version.
- **Citation:** Dahlberg, Stefan et al. (2025). *The Quality of Government Standard Dataset, version Jan25*. University of Gothenburg: The Quality of Government Institute.

### World Bank — Women, Business and the Law (WBL 2024)
- **Variables used:** 10 legal domain scores (mobility, workplace, pay, marriage, parenthood, entrepreneurship, assets, pension, etc.) + overall score
- **Coverage:** ~190 countries, 1971–2024 (historical panel)
- **Access:** [https://wbl.worldbank.org/](https://wbl.worldbank.org/) — free download. File: *WBL2024-1-0-Historical-Panel-Data.xlsx*
- **Citation:** World Bank (2024). *Women, Business and the Law 2024*. Washington, DC: World Bank.

### UNDP — Human Development Report (HDI)
- **Variables used:** Fixed goalposts for life expectancy normalisation (min = 20, max = 85 years)
- **Access:** [https://hdr.undp.org/data-center/human-development-index](https://hdr.undp.org/data-center/human-development-index)
- **Citation:** UNDP (2024). *Human Development Report 2023/2024*. New York: UNDP.

### OECD — Social Institutions and Gender Index (SIGI)
- **Variables used:** SIGI 2019 composite and sub-indices
- **Coverage:** ~120 countries, 2019 (applied ±2 year fill for panel merge)
- **Access:** [https://stats.oecd.org/](https://stats.oecd.org/) — SIGI dataset.
- **Citation:** OECD (2019). *SIGI 2019 Global Report: Transforming Challenges into Opportunities for Gender Equality*. Paris: OECD Publishing.

### Ethnic Power Relations (EPR) Dataset 2021
- **Variables used:** Ethnic group fragmentation controls
- **Coverage:** ~163 countries, 1946–2021
- **Access:** [https://icr.ethz.ch/data/epr/](https://icr.ethz.ch/data/epr/)
- **Citation:** Vogt, Manuel et al. (2015). *Integrating Data on Ethnicity, Geography, and Conflict: The Ethnic Power Relations Data Set Family*. Journal of Conflict Resolution 59(7).

### WHO — World Health Organization
- **Variables used:** Homicide rates (female/male), infant mortality
- **Access:** Obtained via QoG dataset (see above).

### CEDAW Ratification Dates
- **Variables used:** `cedaw_years_since` — years elapsed since country ratified CEDAW
- **Access:** UN Treaty Collection — [https://treaties.un.org/](https://treaties.un.org/)

### La Porta et al. — Legal Origins Classification
- **Variables used:** `lo_english`, `lo_french`, `lo_german`, `lo_scandinavian`, `lo_socialist`
- **Access:** Replication data from La Porta, Lopez-de-Silanes, Shleifer (2008). *The Economic Consequences of Legal Origins*. Journal of Economic Literature 46(2).

### DHS Program — Demographic and Health Surveys
- **Variables used:** Women's attitudes toward domestic violence, violence prevalence (sparse coverage)
- **Access:** [https://dhsprogram.com/](https://dhsprogram.com/) — requires registration.
- **Note:** DHS data was included in the extended dataset (`process_new_datasets.py`) but not used in primary analysis due to sparse coverage.

---

## Processed / Derived Files (in this repo)

| File | Derived from |
|---|---|
| `data/wbl_treatment_index.csv` | WBL 2024 (10 domain scores) + UNDP life expectancy bounds |
| `data/secularism_composition_normalised.csv` | Pew GRI + V-Dem (`v2clrelig`) + QoG (`log_gdppc`) + WVS religiosity |
| `data/gender_gap_panel.csv` | UNDP HDI (GII, GDI) + WEF Global Gender Gap Report (via QoG) |
| `data/women_secularism_normalised.csv` | V-Dem, QoG/WDI, WHO, governance datasets (13-component composite) |

All processed files use **robust min-max normalisation** (1%/99% winsorisation, then scale to [0,1]). Life expectancy uses UNDP HDI fixed goalposts (min = 20, max = 85). See [`DATA_HANDLING_METHODS_LOG.md`](DATA_HANDLING_METHODS_LOG.md) for full decisions.

