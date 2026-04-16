# Secularism & Religious Environment Dataset

**Research question:** Does secularism improve the welfare and treatment of women
relative to men?

**Unit:** Country-year | **Period:** 2007-2022 | **Countries:** 198

This dataset holds the **independent variables** (secularism predictors) for the
analysis. The outcome dataset is `data/outcome_wbl.csv` (WBL-based treatment
index). Join on `iso3 + year`.

All numeric columns are **robust min-max normalised to [0, 1]** (1st/99th pct
winsorisation applied before scaling).
For composition, intensity, and GRI state-institution variables: **higher = more
religion / less secular**. For `v2clrelig_norm`: **higher = more secular freedom**
(direction is reversed -- see Sub-group 3a below).

---

## Sub-group 0: Religious composition (optional, merged in-memory)

Source: Pew Global Religious Futures / World Religion Project, via
`data/religion_composition_normalised.csv`. These columns are **merged at
load time** inside `analysis/run_analysis.py:load_and_merge` and are NOT
stored in `predictors.csv` itself.

| Column | What it measures |
|--------|-----------------|
| `pct_unaffiliated_norm` | % unaffiliated (Pew GRF), min-max normalised |
| `pct_other_norm` | % adhering to "other" religions, min-max normalised |

**Coverage note**: composition is observed only in **2010 and 2020** (~12%
of country-years). After merging with `outcome_wbl.csv` (2013-2023 coverage),
only 2020 overlaps, so these columns are unusable in the T2/T4 panel
specifications and are kept OUT of `GRI_PANEL_COLS` by default. They are
currently referenced only by the composite secularism builder (see sub-group 4).

---

## Sub-group 1: Religious intensity -- how religious societies are

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

Items are classified here as either **structural** (state-of-being
arrangements for how religion sits inside the state) or **treatment**
(policies that act on individuals on religious grounds). The distinction
is load-bearing: only the structural items enter the composite secularism
index (sub-group 4); the treatment items are retained in the analysis as
**standalone sub-item focals** via `GRI_PANEL_COLS` in the T1/T2/T4
decomposition regressions, but are excluded from the composite to avoid
partial mechanical overlap with the outcome (`wbl_treatment_index`, which
is itself a policy-treatment variable at the country level).

| Column | What it measures | Role |
|--------|-----------------|------|
| `gri_state_religion_norm` | Official or preferred state religion (GRI Q1) | Structural — in composite |
| `gri_religious_law_norm` | Religious law applied in the legal system (GRI Q3) | Structural — in composite |
| `gri_religious_courts_norm` | Govt-recognised religious courts exist (GRI Q15) | Structural — in composite |
| `gri_gov_favour_norm` | Government favouritism toward specific religion(s) (GRI Q2) | Treatment — standalone focal only |
| `gri_blasphemy_norm` | Blasphemy laws in effect (GRX22) | Treatment — standalone focal only |
| `gri_apostasy_norm` | Apostasy laws in effect (GRX22) | Treatment — standalone focal only |

**History**: `gri_gov_favour_norm` (GRI Q2) was present in `predictors.csv`
from the start but silently absent from `GRI_PANEL_COLS` in
pre-`77417d9` analysis versions. It was restored to `GRI_PANEL_COLS` on
2026-04-15 as part of the Item 2 composite rebuild, and added to the
composite's institutional dimension at the same time. On 2026-04-16 the
composite was rebuilt again (Item 2 redux, see
`reviews/2026-04-16_secularism-composite-rebuild.md`) to remove
`gri_gov_favour_norm`, `gri_blasphemy_norm`, `gri_apostasy_norm`, and
`v2clrelig_norm` from the composite on circularity grounds. These four
items stay in the analysis as standalone sub-item focals — only their
role inside the composite has changed.

---

## Sub-group 3a: Secular tolerance -- freedom of religion (V-Dem)

Source: V-Dem Core v15, annual 2007-2022.
**NOTE: direction is OPPOSITE to other vars** -- higher = MORE freedom of religion
(more secular tolerance).

| Column | What it measures | Role |
|--------|-----------------|------|
| `v2clrelig_norm` | Freedom to practise religion (V-Dem v2clrelig) | Treatment — standalone focal only |

`v2clrelig_norm` measures how the state treats individuals on religious
grounds (freedom to practise), which overlaps conceptually with the
outcome (`wbl_treatment_index`, how the state treats women on legal
grounds). As of 2026-04-16 it is therefore excluded from the composite
secularism index and enters the analysis only as a standalone sub-item
focal in the T1/T2 decomposition.

---

## GDP control

`log_gdppc_norm`: log(GDP per capita, constant 2015 USD), robust min-max normalised.
Source: World Bank WDI via QoG Standard TS Jan 2025.
Pre-built here so analysis scripts need not load raw QoG separately.

---

## Sub-group 4: Composite secularism index (derived, in-memory)

Added 2026-04-15 as part of TODO Item 2; rebuilt 2026-04-16 (Item 2
redux, see `reviews/2026-04-16_secularism-composite-rebuild.md`) to
remove treatment items on circularity grounds. Variants are built at
load time by `analysis.utils.build_secularism_composite(df)` and
attached to the working dataframe; they are NOT stored on disk.

| Column | Construction |
|--------|-------------|
| `composite_secularism_norm` | Equal-weight z-score of two dimensions over 7 inputs; primary headline |
| `composite_secularism_pca_norm` | First principal component over the 7 inputs (EM-imputed); robustness variant |
| `composite_secularism_real_norm` | Equal-weight z-score with WVS columns masked to NaN on `wvs_interpolated == 1` rows; robustness variant that purges interpolator arithmetic from the behavioural dimension |
| `composite_secularism_instonly_norm` | Institutional-only variant — z-score mean of the 3 structural GRI items alone |
| `composite_secularism_covwt_norm` | Coverage-weighted variant — each dimension weighted by its panel-wide non-null row fraction |

**Dimensions and orientation** (all set to "higher = more religion / less secular"):
- **Institutional** — 3 *structural* GRI sub-items (state religion,
  religious law, religious courts).
- **Behavioural** — 4 WVS intensity items (imprel, godimp, godbel, confch).

Four items (`gri_apostasy_norm`, `gri_blasphemy_norm`, `gri_gov_favour_norm`,
`v2clrelig_norm`) were previously included in the composite but were
removed on 2026-04-16 because each measures how the state treats people
on religious grounds, which overlaps mechanically with the outcome
(`wbl_treatment_index`) and inflates the cross-sectional coefficient
beyond what ``religiosity as a state of being'' explains. These items
remain in the analysis as standalone sub-item focals via
`GRI_PANEL_COLS` (for the three GRI items) and as a standalone
`v2clrelig_norm` row in the T1/T2 decomposition.

**Equal-weight**: each dimension is z-scored (NaN-aware); the two
z-scores are row-averaged. **Dimension-fallback**: if one dimension is
entirely NaN for a row, the composite equals the observed dimension.
After averaging, the composite is passed through robust_minmax to [0, 1].

**PCA variant**: each input column is imputed, then standardised.
First PC of the 7 standardised columns; sign-aligned so that the loading
on `gri_state_religion_norm` is positive; then robust_minmax to [0, 1].
Three imputation strategies are computed and compared in
`results/pca_loadings_comparison.csv`: column-mean imputation, listwise
deletion (complete-case only), and iterative EM imputation via
sklearn's `IterativeImputer`. EM is the primary variant attached to the
working dataframe as `composite_secularism_pca_norm`. First PC loadings
are highest on the behavioural WVS items and lower on the structural
GRI items, mirroring the equal-weight composite's implicit weighting.
The PCA variant is a cross-check on the equal-weight composite rather
than an independent methodological alternative. Exact explained-variance
ratios and loadings are reported in the analysis log alongside each
pipeline run.

**Diagnostic note for the composite**: `n_changers` saturates at ≈
`n_clusters` because the composite is continuous by construction, so it
loses its discriminating value. `within_sd` becomes the load-bearing
diagnostic for whether the composite has meaningful within-country
variation. The analysis log additionally reports `n_changers` restricted
to `wvs_interpolated == 0` rows — this is the "real movement" count,
purged of WVS interpolator arithmetic.

---

## Normalisation method

    x_wins = clip(x, p01, p99)   # 1st/99th pct winsorisation
    x_norm = (x_wins - min) / (max - min)

Missing values preserved as NaN -- not imputed.

---

## Data sources

| Dataset | Version | Notes |
|---------|---------|-------|
| World Values Survey (WVS) | Via QoG Jan 2025 | Societal religious strength |
| Pew Global Restrictions on Religion | 2007-2022 | State institution sub-questions |
| V-Dem Core | v15, 2007-2022 | Freedom of religion (v2clrelig) |
| World Bank WDI | Via QoG Jan 2025 | GDP per capita |

---

## Join with women's treatment data

```python
import pandas as pd
predictors = pd.read_csv("data/predictors.csv")
outcome    = pd.read_csv("data/outcome_wbl.csv")
merged     = outcome.merge(predictors, on=["iso3", "year"], how="left")
```
