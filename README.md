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
├── figures/            Publication-quality PNG figures (10 total)
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

Cross-national panel, up to 198 countries, 2007–2022. Focal predictor: `gri_religious_courts_norm` (Pew GRI separate religious courts score, normalised).

### Key Finding

Religious court institutionalisation is associated with significantly lower women's welfare scores:

| Model | Coef | SE | p |
|---|---|---|---|
| T2 Panel FE (no GDP) | −0.011 | 0.004 | 0.002 |
| T2 Panel FE (with GDP) | −0.008 | 0.003 | 0.003 |
| Wild cluster bootstrap | −0.010 | — | 0.012 |
| Driscoll-Kraay HAC | −0.011 | 0.003 | <0.001 |
| WEF GGG external validation | −0.020 | — | 0.036 |

- **LOO jackknife:** 170 country-drop runs — 0 sign flips, 0 non-significant
- **Pre-trend test:** event-study F-test p = 0.881 (no pre-trends)
- **Oster delta:** 8.3 at Rmax = 1.3×R_full (robust to omitted variable bias)
- **Placebo:** courts score on male outcomes ≈ 0 (p = 0.27–0.87), confirming gendered mechanism

### How to run

```bash
python analysis/run_analysis.py    # regressions → results/
python analysis/run_plots.py       # figures → figures/
python analysis/compare_indices.py # index comparison → results/index_comparison.*
python verify.py                   # integrity check
```

---

## Data Sources

| Data | File(s) | Years | Purpose |
|---|---|---|---|
| World Bank WBL 2024 | `data/WBL2024-1-0-Historical-Panel-Data.xlsx` | 2013–2023 | Legal rights (8 groups) |
| WDI adolescent fertility | `data/adolefert/` | 2013–2023 | Health group |
| WDI life expectancy | `data/lifeexp/` | 2013–2023 | Health group |
| WDI maternal mortality | `data/maternalmort/` | 2013–2023 | Health group |
| WDI parliament seats | `data/parliament/` | 2013–2023 | Political representation |
| Pew GRI | `data/predictors.csv` | 2007–2022 | Secularism predictor |
| V-Dem v15, QoG, WHO | `data/outcome_composite.csv` | 2007–2022 | Alternative outcome index |

See [`docs/sources.md`](docs/sources.md) for full provenance.
