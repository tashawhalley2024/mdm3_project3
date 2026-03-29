# data/

Contains both raw data files (read by `data_reading.py`) and analysis-ready normalised CSVs (read by `analysis/` scripts).

---

## Raw Data — WBL Scoring Pipeline

These files are read directly by `data_reading.py` to build the 10 thematic group datasets.

| File / Directory | Source | Years | Contents |
|---|---|---|---|
| `WBL2024-1-0-Historical-Panel-Data.xlsx` | World Bank WBL 2024 | 2013–2023 | Legal rights across 8 domains (mobility, workplace, pay, family, parenthood, economic rights, assets, pension) |
| `adolefert/` | World Bank WDI | 2013–2023 | Adolescent fertility rate — one subdirectory per year |
| `lifeexp/` | World Bank WDI | 2013–2023 | Life expectancy at birth (female + total) — one subdirectory per year |
| `maternalmort/` | World Bank WDI | 2013–2023 | Maternal mortality ratio — one subdirectory per year |
| `parliament/` | World Bank WDI | 2013–2023 | Proportion of seats held by women in national parliaments — one subdirectory per year |
| `religion_composition_normalised.csv` | Pew / WRP | — | Normalised religious composition by country |
| `women_religion_normalised.csv` | — | — | Women-religion interaction index |

Year-by-year directories follow the structure: `<indicator>/<year>/<indicator>/<data>.csv`

---

## Analysis-Ready CSVs — Secularism Regression Analysis

Pre-processed, normalised inputs for the `analysis/` regression scripts. All normalisation uses robust min-max (1%/99% winsorisation, then scale to [0,1]) unless otherwise noted.

| File | Rows | Countries | Years | Purpose |
|---|---|---|---|---|
| `outcome_wbl.csv` | 2,222 | ~168 | 2013–2022 | **Active** outcome index — WBL legal rights + health |
| `outcome_composite.csv` | 3,164 | ~198 | 2007–2022 | Alternative outcome — 13-component composite |
| `predictors.csv` | 3,164 | ~198 | 2007–2022 | Secularism predictor variables |
| `robustness_outcomes.csv` | 3,164 | ~198 | 2007–2022 | Robustness outcomes (GII, GDI, WEF GGG) |

### Key variables

**`outcome_wbl.csv`** — key variable: `wbl_treatment_index`
- Source: World Bank WBL 2024 (10 legal domains) + WDI life expectancy + maternal mortality
- Life expectancy normalised using UNDP HDI fixed goalposts (min=20, max=85)
- See `outcome_wbl_README.md`

**`predictors.csv`** — key variables:
- `gri_religious_courts_norm` — focal predictor (Pew GRI separate religious courts)
- `gri_state_religion_norm`, `gri_religious_law_norm`, `gri_blasphemy_norm`, `gri_apostasy_norm`
- `v2clrelig_norm` — V-Dem religious civil liberties
- `wvs_imprel_norm`, `wvs_godimp_norm`, `wvs_godbel_norm`, `wvs_confch_norm` — WVS religiosity
- `log_gdppc_norm` — log GDP per capita (control)
- `wvs_interpolated = 1` indicates interpolated/filled WVS values
- See `predictors_README.md`

**`robustness_outcomes.csv`** — key variables: `gii_norm`, `gdi_norm`, `wef_ggg_norm`, `life_exp_gap_norm`, `lfp_gap_norm`
- See `robustness_outcomes_README.md`

See [`docs/sources.md`](../docs/sources.md) for full provenance of all datasets.
