# Religion Composition Dataset

**Research question:** How does religious composition affect the treatment of women?

**Unit:** Country-year | **Period:** 2007–2022 | **Countries:** 198 | **Rows:** 3,164 | **Columns:** 20

All 17 numeric columns are min-max normalised to **[0, 1]** (verified — no values outside this range).
**Higher always means MORE religion** — a larger share, more intense practice, or greater institutional embedding.
Missing values are `NaN` — no values are extrapolated or interpolated.

---

## Sub-group 1: Composition — who belongs to each religion

Values only present in **2010 and 2020** (actual survey years). All other years are `NaN`.

| Column | What it measures | Source | Coverage |
|--------|-----------------|--------|----------|
| `pct_unaffiliated_norm` | Religiously unaffiliated share of population | Pew / WRP | 12% |
| `pct_other_norm` | All other religions combined | Pew / WRP | 12% |

---

## Sub-group 2: Religious intensity — how religion is practiced or valued

Survey-based — only present in WVS wave years (typically every 5 years). All other years are `NaN`.

| Column | What it measures | Raw scale | Source | Coverage |
|--------|-----------------|-----------|--------|----------|
| `wvs_imprel_norm` | Mean importance of religion in life | 1–4 | WVS via QoG | 7% |
| `wvs_godimp_norm` | Mean importance of God | 1–10 | WVS via QoG | 7% |
| `wvs_godbel_norm` | Proportion of population who believe in God | 0–1 | WVS via QoG | 6% |
| `wvs_confch_norm` | Mean confidence in the church/mosque/temple | 1–4 | WVS via QoG | 7% |

---

## Sub-group 3: Religious state institutions — religion embedded in law and policy

Annual observed data throughout. Higher = more religion embedded in state structures.

| Column | What it measures | Raw scale | Source | Coverage |
|--------|-----------------|-----------|--------|----------|
| `gri_state_religion_norm` | Official or preferred state religion | 0 / 0.5 / 1 | Pew GRI Q1 | 100% |
| `gri_gov_favour_norm` | Government favouritism toward specific religion(s) | 0–1 | Pew GRI Q2 | 100% |
| `gri_religious_law_norm` | Religious law applied in the legal system | 0–1 | Pew GRI Q3 | 100% |
| `gri_religious_courts_norm` | Government-recognised religious courts exist | 0 / 1 | Pew GRI Q15 | 100% |
| `gri_blasphemy_norm` | Blasphemy laws in effect | 0 / 1 | Pew GRX22 | 81% |
| `gri_apostasy_norm` | Apostasy laws in effect | 0 / 1 | Pew GRX22 | 81% |

---

## Normalisation

    x_norm = (x − min(x)) / (max(x) − min(x))

Applied over all non-null observations in the 2007–2022 panel.

---

## Data sources

| Dataset | Version |
|---------|---------|
| Pew Global Religious Futures | 2010 & 2020 |
| World Religion Project (WRP) | National dataset |
| World Values Survey (WVS) | Via QoG Standard TS Jan 2025 |
| Pew Global Restrictions on Religion | 2007–2022 |
