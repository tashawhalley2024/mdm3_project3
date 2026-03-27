# Does Institutional Secularism Improve Women's Treatment? — Cross-National Panel Study

**Research question:** Does institutional secularism improve the welfare and treatment of women relative to men?

Cross-national panel covering up to 198 countries, 2007–2022. Focal predictor: `gri_religious_courts_norm` (Pew Global Restrictions on Religion — separate religious courts score, normalised).

---

## Key Finding

Religious court institutionalisation is associated with significantly lower women's welfare scores:

| Model | Coef | SE | p |
|---|---|---|---|
| T2 Panel FE (no GDP) | −0.011 | 0.004 | 0.002 |
| T2 Panel FE (with GDP) | −0.008 | 0.003 | 0.003 |
| Wild cluster bootstrap | −0.010 | — | 0.012 |
| Driscoll-Kraay HAC | −0.011 | 0.003 | <0.001 |
| WEF GGG external validation | −0.020 | — | 0.036 |

- **LOO jackknife:** 170 country-drop runs — 0 sign flips, 0 non-significant results
- **Pre-trend test:** event-study F-test p = 0.881 (no pre-trends; causal interpretation supported)
- **Oster delta:** 8.3 at Rmax = 1.3×R_full (robust to omitted variable bias)
- **Placebo:** courts score on male outcomes ≈ 0 (p = 0.27–0.87), confirming gendered mechanism

Result holds across the **composite index** (2007–2022, 13 components from V-Dem/WDI/governance) and the **WBL index** (2013–2022, World Bank legal rights + health). See [`results/index_comparison.md`](results/index_comparison.md) for full explanation of why significance differs between indices.

---

## Repository Structure

```
.
├── data/           Input datasets (flat, normalised, analysis-ready)
├── analysis/       Python scripts for regression and plotting
├── results/        Regression output CSVs and robustness tables
├── figures/        Publication-quality PNG figures (10 total)
├── sanity_check/   Index validation outputs (WBL vs composite, r = 0.880)
└── docs/           Data handling log and original source references
```

See the README in each subdirectory for details.

---

## How to Run

**Prerequisites:**
```bash
pip install -r requirements.txt
```

**Run from the repo root** (scripts resolve all paths relative to the repo root):

```bash
# 1. Run all regressions (Tiers 1–2, Phases 3–10) — writes to results/
python analysis/analyse_secularism_women.py

# 2. Generate all 10 figures — writes to figures/
python analysis/plot_secularism_women.py

# 3. Compare composite vs WBL index — overwrites results/index_comparison.*
python analysis/compare_indices.py

# 4. Verify repo integrity
python verify.py
```

> Note: some robustness phases (P5 legal origins, P6 male placebo) require raw QoG/legal-origins data that is not included in this repo. Those phases are skipped gracefully if raw files are absent.

---

## Data

| Dataset | File | Rows | Years | Purpose |
|---|---|---|---|---|
| WBL 2024 + health | `data/wbl_treatment_index.csv` | 2,222 | 2013–2022 | **Active** outcome index |
| Composite (13-component) | `data/women_secularism_normalised.csv` | 3,164 | 2007–2022 | Alternative outcome index |
| Secularism predictors | `data/secularism_composition_normalised.csv` | 3,164 | 2007–2022 | GRI vars, V-Dem, GDP |
| Gender gap robustness | `data/gender_gap_panel.csv` | 3,164 | 2007–2022 | GII, GDI, WEF GGG |
| Early composite (group project) | `data/women_religion_normalised.csv` | — | — | Provenance reference |
| Early composition (group project) | `data/religion_composition_normalised.csv` | — | — | Provenance reference |

All input data are normalised and analysis-ready. Raw source files are not included (not redistributable / too large). See [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md) for provenance.

---

## Verification

```bash
python verify.py
```

Checks: all required files exist, CSV schemas, key regression coefficient (β ≈ −0.011020), figure sizes, README completeness. Exit 0 = all pass.

---

## Data Sources

Pew Research Center (GRI), V-Dem v15, QoG Standard TS Jan 2025, World Bank WBL 2024, UNDP HDI, OECD SIGI 2019, EPR 2021, WHO, CEDAW. See [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md).

---

## Related

- Early WBL scoring pipeline: `data/women_religion_normalised.csv` and `data/religion_composition_normalised.csv` are the group-project precursors to the final analysis datasets.
- Data handling decisions: [`docs/DATA_HANDLING_METHODS_LOG.md`](docs/DATA_HANDLING_METHODS_LOG.md)
