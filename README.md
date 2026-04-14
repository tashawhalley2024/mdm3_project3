# MDM3 Group Project — Treatment of Women

Cross-national study of women's treatment and welfare, covering 202 countries, 2013–2023.

This repo contains two components:

1. **WBL scoring pipeline** — builds a treatment-of-women index from raw World Bank, WHO, and UN data
2. **Secularism regression analysis** — tests whether institutional secularism improves women's welfare

---

## Repository Structure

```
.
├── data_reading.py     Build 10 thematic group datasets from raw data → output/
├── scoring.py          Score and combine groups → output/overall_score.csv
├── output/             Scored group CSVs + overall_score.csv
├── data/               Raw data files + analysis-ready CSVs
├── analysis/           Regression scripts (secularism analysis)
├── results/            Regression output CSVs and robustness tables
├── figures/            Publication-quality PNG figures
├── writing/            LaTeX methodology write-up + bibliography
├── sanity_check/       Index validation outputs
└── docs/               Data handling log and source references
```

---

## Part 1: WBL Scoring Pipeline

Builds a composite treatment-of-women score (0–1) for each country-year from 10 thematic groups.

### How to run

```bash
pip install -r requirements.txt

python data_reading.py   # reads raw data → output/*_group.csv
python scoring.py        # scores groups → output/overall_score.csv
```

### Output

`output/overall_score.csv` — one row per country-year, columns: `Economy`, `ISO Code`, `Year`, `overall_score`

- **2,222 rows**, 202 countries, 11 years (2013–2023)
- Score range: 0 (lowest welfare) to 1 (highest)

### Thematic groups scored

| Group | Source | Key indicators |
|---|---|---|
| Mobility | WBL 2024 | Freedom of movement, passport, travel |
| Workplace | WBL 2024 | Job access, discrimination law, harassment law |
| Pay | WBL 2024 | Equal pay, night/dangerous/industrial work |
| Family & safety | WBL 2024 | Domestic violence law, divorce, remarriage |
| Parenthood | WBL 2024 | Maternity/paternity leave, dismissal protection |
| Economic rights | WBL 2024 | Credit access, contracts, business registration |
| Assets | WBL 2024 | Property rights, inheritance |
| Pension | WBL 2024 | Retirement age parity, childcare credits |
| Health | WHO/WDI | Adolescent fertility, maternal mortality, life expectancy |
| Political representation | WDI | Women's share of parliamentary seats |

### Scoring method

- Yes/No legal indicators → 1/0
- Continuous indicators → min-max normalised to [0,1]
- Life expectancy: UNDP HDI fixed goalposts (min=20, max=85 years)
- Adverse indicators (maternal mortality, adolescent fertility) → inverted (1 − score)
- Group scores = equal-weight average of indicators
- Overall score = equal-weight average of 10 group scores

---

## Part 2: Secularism Regression Analysis

**Research question:** Does institutional secularism improve the welfare and treatment of women?

Cross-national panel, up to 198 countries, 2007–2022 (WBL outcome available 2013 onwards). Focal predictor: `gri_religious_courts_norm` (Pew GRI religious courts score, normalised). Key finding: `gri_apostasy_norm` is the most consistently significant GRI predictor across all specifications.

### Analysis status

| Tier | Model | Status | Script location |
|---|---|---|---|
| T1 | Cross-sectional OLS (2014 & 2020, HC3 SEs) | **Implemented** | `analysis/run_analysis.py` |
| T2 | Two-way Fixed-Effects panel (country + year FE, clustered SEs, 2007–2022) | **Implemented** | `analysis/run_analysis.py` |
| T3 | System-GMM (Blundell-Bond dynamic panel) | **Implemented** (fails Roodman bounds — see below) | `analysis/run_analysis.py` |
| T4 | Mundlak RE-FE hybrid (between + within decomposition) | **Implemented** | `analysis/run_analysis.py` |

### How to run (current implemented models)

```bash
python analysis/run_analysis.py    # regressions → results/
python analysis/run_plots.py       # figures → figures/
python verify.py                   # integrity check
```

### Current results summary

| Model | gri_religious_courts coef | p-value | gri_apostasy coef | p-value |
|---|---|---|---|---|
| T1 OLS (2020, no GDP) | +0.023 | 0.222 | −0.121 | <0.001 |
| T2 TWFE (no GDP) | −0.007 | 0.289 | −0.018 | 0.033 |
| T2 TWFE (with GDP) | −0.007 | 0.312 | −0.020 | 0.035 |
| T4 Mundlak within | −0.007 | 0.288 | −0.020 | 0.027 |
| T4 Mundlak between | +0.042 | 0.064 | −0.122 | 0.001 |

Robustness checks (implemented):
- LOO jackknife: 166 country-drop runs
- Pre-trend test: event-study F-test
- Oster sensitivity: delta statistic
- Lagged GRI predictors (L1, L2)
- Sub-outcome analysis (political, economic, safety, health)
- Alternative outcomes: SIGI 2019, GII
- Regional heterogeneity
- Legal origins controls
- V-Dem freedom of religion alternative predictor
- Wild cluster bootstrap
- Driscoll-Kraay HAC standard errors
- Mundlak CRE (pooled OLS cross-check of T4)

---

## Part 2 Extensions: T3 System-GMM and T4 Mundlak

Both T3 and T4 are implemented. Both append results to `results/results.csv` in the existing tidy format (`tier, year, predictor, coef, se, pval, n, r2, dv_label, sig`).

The full methodological justification for both models (with literature review and bibliography) is in:
- `writing/methodology_full.tex` — unified LaTeX write-up for all four tiers
- `writing/references_full.bib` — 30-entry bibliography
- `writing/literature_review_gmm.tex` — GMM-specific extended section

### T3: System-GMM (Blundell-Bond 1998)

**Why:** TWFE cannot include a lagged DV (Nickell bias), and the GRI/V-Dem regressors are plausibly endogenous. System-GMM addresses both via internal instruments from lagged values.

**Estimating equation:**

```
W_it = ρ·W_i,t-1 + β·G_it + γ·X_it + α_i + λ_t + ε_it
```

where `W_it` = `wbl_treatment_index`, `G_it` = GRI vector, `X_it` = V-Dem controls + log GDP.

**Implementation:**
- Package: `pydynpd` (`pip install pydynpd`) — purpose-built Blundell-Bond for Python
- Instrument strategy: collapse instrument matrix; lag depth 2 for differenced equation, lag-1 differences for levels equation
- Estimator: two-step GMM with Windmeijer (2005) finite-sample SE correction
- Diagnostics to report: Hansen J-test p-value (instrument validity), AR(1) and AR(2) Arellano-Bond tests (no second-order serial correlation)
- Instrument count must not exceed N≈198; use `collapse=True` in pydynpd

**Closest published template:** Achuo et al. (2024, *Journal of Economics and Development*) — WBL Index as DV, World Governance Indicators as predictors, 142 countries, system-GMM robustness.

**Key constraint:** With T=16 and N=198, instrument proliferation is the main risk. Monitor Hansen p-value — if >0.25, instruments are too many (paradoxically passing).

**Diagnostic outcome:** T3 was implemented but fails the Roodman (2009) bounds check. The GMM autoregressive coefficient (rho = 1.215) exceeds the pooled OLS upper bound (0.982), indicating explosive dynamics inconsistent with a welfare index bounded in [0, 1]. The Hansen J-test p-value (0.83) is suspiciously high, consistent with instrument proliferation despite collapsing. AR(2) p = 0.30 passes. T3 results are reported in `results/results.csv` for transparency but are excluded from substantive conclusions. The T1/T2/T4 estimates constitute the primary evidence.

---

### T4: Mundlak RE-FE Hybrid (Mundlak 1978) — Implemented

**Why:** TWFE discards all between-country variation. The Mundlak model retains it by decomposing each predictor into a within-country deviation and a country mean, yielding two substantively distinct coefficients per variable — the *within effect* (does a country becoming more secular improve welfare?) and the *between effect* (do secular countries structurally have better outcomes?).

**Transformation:** For each time-varying predictor X_it, add its country mean X̄_i as an additional regressor:

```
W_it = β₁·X_it + β₂·X̄_i + u_i + ε_it
```

- `β₁` = within effect (within-country change over time)
- `β₂` = between effect (cross-country structural difference)
- `u_i` = random country effect (GLS, not FE)

**Implementation:** `tier4_mundlak_re()` in `analysis/run_analysis.py`.
- Country means (`_mean` suffix) computed for all 9 time-varying predictors (5 GRI + 3 V-Dem + GDP)
- Estimator: `linearmodels.panel.RandomEffects` with entity-clustered SEs
- Year dummies included to absorb common time shocks
- Results tagged as `T4_mundlak_re` in `results/results.csv`

**Verified properties:**
- Within-coefficients match T2 TWFE to <0.001 absolute difference (confirms correct specification)
- Between and within effects differ for all 5 GRI variables (confirms unobserved heterogeneity; FE warranted)
- 3 of 9 country means significant at 5% (Mundlak test rejects simple RE)

**Key result:** `gri_apostasy_norm` between-effect (β₂ = −0.122, p = 0.001) is roughly 6.2× the within-effect (β₁ = −0.020, p = 0.027). Secularism matters structurally across countries far more than within-country changes over 2007–2022.

---

## Data Sources

| Data | File(s) | Years | Purpose |
|---|---|---|---|
| World Bank WBL 2024 | `data/WBL2024-1-0-Historical-Panel-Data.xlsx` | 2013–2023 | Legal rights (8 groups) |
| WDI adolescent fertility | `data/adolefert/` | 2013–2023 | Health group |
| WDI life expectancy | `data/lifeexp/` | 2013–2023 | Health group |
| WDI maternal mortality | `data/maternalmort/` | 2013–2023 | Health group |
| WDI parliament seats | `data/parliament/` | 2013–2023 | Political representation |
| Pew GRI | `data/predictors.csv` | 2007–2022 | Secularism predictors |
| V-Dem v15, QoG, WHO | `data/outcome_composite.csv` | 2007–2022 | Alternative outcome index |

Analysis-ready merged files:
- `data/outcome_wbl.csv` — outcome variable (`wbl_treatment_index`), ~198 countries, 2007–2022
- `data/predictors.csv` — all GRI predictors + V-Dem controls + `log_gdppc_norm`

See [`docs/sources.md`](docs/sources.md) for full provenance and [`docs/methods_log.md`](docs/methods_log.md) for all data handling decisions.
