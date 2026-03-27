# data/

Analysis-ready, normalised input datasets. No raw source files are included here — see [`docs/sources.md`](../docs/sources.md) for original provenance.

All normalisation uses **robust min-max** (1%/99% winsorisation, then scale to [0,1]) unless otherwise noted. Life expectancy variables use UNDP HDI fixed goalposts (min = 20, max = 85 years).

---

## Dataset Overview

| File | Rows | Countries | Years | Purpose |
|---|---|---|---|---|
| `outcome_wbl.csv` | 2,222 | ~168 | 2013-2022 | **Active** outcome index — WBL legal rights + health |
| `outcome_composite.csv` | 3,164 | ~198 | 2007-2022 | Alternative outcome — 13-component composite |
| `predictors.csv` | 3,164 | ~198 | 2007-2022 | Secularism predictor variables |
| `robustness_outcomes.csv` | 3,164 | ~198 | 2007-2022 | Robustness outcomes (GII, GDI, WEF GGG, gaps) |

---

## File Details

### `outcome_wbl.csv` — Active Outcome Index
- **Source:** World Bank WBL 2024 (10 legal domains) + WDI life expectancy + maternal mortality
- **Key variable:** `wbl_treatment_index` — equal-weight average of normalised domain scores
- **Life expectancy:** normalised using UNDP HDI fixed goalposts
- See `outcome_wbl_README.md` for column-by-column details

### `outcome_composite.csv` — Composite Outcome Index
- **Source:** V-Dem v15 (political/civil rights), QoG/WDI (labour, health, governance), WHO
- **Key variable:** `women_treatment_index` — 13-component composite, equal weights
- **Coverage advantage:** 2007-2022 gives more within-country variation than WBL index
- See `outcome_composite_README.md`

### `predictors.csv` — Predictor Dataset
- **Key variables:**
  - `gri_religious_courts_norm` — **focal predictor** (Pew GRI separate religious courts)
  - `gri_state_religion_norm`, `gri_religious_law_norm`, `gri_blasphemy_norm`, `gri_apostasy_norm`
  - `v2clrelig_norm` — V-Dem religious civil liberties
  - `wvs_imprel_norm`, `wvs_godimp_norm`, `wvs_godbel_norm`, `wvs_confch_norm` — WVS religiosity
  - `log_gdppc_norm` — log GDP per capita (control)
- See `predictors_README.md`

### `robustness_outcomes.csv` — Robustness Outcomes
- **Key variables:** `gii_norm` (Gender Inequality Index), `gdi_norm` (Gender Development Index), `wef_ggg_norm` (WEF Global Gender Gap), `life_exp_gap_norm`, `lfp_gap_norm`
- **Coverage:** GII 80%, GDI 88%, WEF GGG 67% of country-years
- See `robustness_outcomes_README.md`

---

## Interpolation Flags

- `wvs_interpolated = 1` in `predictors.csv` indicates WVS religiosity values were linearly interpolated or forward/back-filled for that country-year.
