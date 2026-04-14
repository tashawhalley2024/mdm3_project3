# Data Handling Methods Log

**Project:** Does secularism improve the welfare and treatment of women relative to men?
**Scope:** Cross-national panel, up to 198 countries, 2007-2022.
**Last updated:** See git log.

> **Note:** Entries 1–12 reference file paths from a previous pipeline layout
> (`src/extract_women_secularism.py`, `src/build_secularism_composition.py`, etc.)
> that no longer exist in the current repo structure. The actual pipeline files are
> `data_reading.py`, `scoring.py`, and `analysis/run_analysis.py`. The scientific
> justifications in entries 1–12 remain valid — only the file paths are outdated.

This document records every non-trivial data handling decision made in the
analysis pipeline, with scientific justification and implementation details.

---

## 1. Normalisation method

**Decision:** Robust min-max normalisation (1st/99th percentile winsorisation, then scale to [0, 1]).

**Previous method:** Plain min-max — `(x - min) / (max - min)`.

**New method:**
```
x_wins = clip(x, percentile(x, 1), percentile(x, 99))
x_norm = (x_wins - min(x_wins)) / (max(x_wins) - min(x_wins))
```

**Justification:** Plain min-max is highly sensitive to outliers — a single extreme
observation (e.g., a failed state in one year) can compress the entire distribution
into a narrow band. Winsorising to the 1st/99th percentile before scaling preserves
the relative ranking of all but the most extreme values, while preventing outlier
leverage. This is standard practice in composite index construction (OECD 2008,
*Handbook on Constructing Composite Indicators*).

**Implementation:** `utils.robust_minmax(s, winsor=True)`. Applied in:
- `src/extract_women_secularism.py` (all OUTCOME_VARS, SECULAR_ENV_VARS, CONTROL_VARS)
- `src/build_secularism_composition.py` (all composition, intensity, state-institution vars + GDP)
- `src/process_new_datasets.py` (SIGI, GII, CEDAW years_since, DHS)

**What did NOT change:** Direction (inversion for "higher = worse" variables) and
the panel scope (2007-2022) over which normalisation is computed.

---

## 2. Missing data — general policy

**Decision:** Missing values are preserved as `NaN` by default. No global imputation.

**Justification:** Panel fixed-effects models (Tier 2 / Phase 3-7) use listwise deletion
within `linearmodels.PanelOLS`, which correctly handles unbalanced panels. Global
imputation would introduce biased estimates for variables with strong country-level
patterns (e.g., religious composition, SIGI).

**Exceptions (documented separately):** The following variables receive targeted,
scientifically justified interpolation or fill, all flagged in the output data.

---

## 3. Interpolation — religious composition (pct_*)

**Variables:** `pct_unaffiliated`, `pct_other` (normalised versions).

**Source coverage:** Pew Global Religious Futures provides data only in survey
years 2010 and 2020; WRP provides a 2010 cross-section fallback. Without
interpolation, coverage is ~12% of country-years.

**Method:**
1. Linear interpolation between 2010 and 2020 for each country (fills 2011-2019).
2. Backward-fill up to 3 years before 2010 (covers 2007-2009).
3. Forward-fill up to 2 years after 2020 (covers 2021-2022).

**Justification:** Religious composition is an extremely slow-changing demographic
variable. A linear change from 2010 to 2020 is a well-grounded model for the
intervening years (e.g., Hackett et al. 2017, *The Changing Global Religious
Landscape*). Edge-fills are limited to 3 years (pre) and 2 years (post) to avoid
extrapolating too far. Post-2020 fill is limited to 2 years as no 2025 estimate
is available.

**Coverage after interpolation:** Approximately 70% of country-years (up from 12%).

**Flag column:** `pct_interpolated` in `secularism_composition_normalised.csv`.
- `0` = original Pew/WRP survey value
- `1` = linearly interpolated or edge-filled
- `NaN` = no Pew or WRP coverage for this country

**Implementation:** `utils.within_country_interpolate()` called in
`src/build_secularism_composition.py` with `ffill_limit=2, bfill_limit=3`.

---

## 4. Interpolation — WVS religiosity (wvs_*)

**Variables:** `wvs_imprel`, `wvs_godimp`, `wvs_godbel`, `wvs_confch` (normalised).

**Source coverage:** World Values Survey is fielded roughly every 5 years
(waves: ~2005-09, 2010-14, 2017-20). Without interpolation, coverage is ~7%.

**Method:**
1. Linear interpolation between observed wave years within each country.
2. Forward-fill up to 2 years after the most recent observed wave.
3. Backward-fill up to 2 years before the earliest observed wave.

**Justification:** Population religiosity is a slowly-changing cultural variable
that is not expected to jump discontinuously between survey waves. Linear
interpolation between known values is standard in the cross-national panel
literature (e.g., Norris & Inglehart 2004). Edge fills are limited to 2 years
to avoid over-extrapolation; no country should be assigned a WVS value more than
2 years outside the period directly observed for that country.

**Coverage after interpolation:** Approximately 25-30% of country-years.

**Flag column:** `wvs_interpolated` in `secularism_composition_normalised.csv`.
- `0` = original WVS survey value
- `1` = linearly interpolated or edge-filled
- `NaN` = no WVS coverage within +-2 years for this country

**Implementation:** `utils.within_country_interpolate()` called in
`src/build_secularism_composition.py` with `ffill_limit=2, bfill_limit=2`.

---

## 5. Interpolation — SIGI (sigi_*)

**Variables:** `sigi`, `sigi_family`, `sigi_physical`, `sigi_resources`, `sigi_civil`
(normalised; SIGI 2019 edition within the 2007-2022 window).

**Source coverage:** SIGI 2019 provides one cross-section. Without interpolation,
coverage is ~4% of country-years (only year 2019 populated, ~40 countries).

**Method:** Forward-fill 2 years from 2019 (covers 2020-2021) and backward-fill
2 years (covers 2017-2018). This gives 5 years of coverage per country: 2017-2021.

**Justification:** Social institutions measured by SIGI (family law, physical
integrity norms, access to resources) change slowly — rarely by more than
marginal amounts over a 2-year window. A +-2yr neighbourhood fill is more
defensible than either (a) leaving only year 2019 populated or (b) applying the
value to all 16 years. This is consistent with practice in multi-wave panel
imputation (Allison 2002, *Missing Data*).

**Coverage after interpolation:** Approximately 20% of country-years (up from 4%).

**Flag column:** `sigi_interpolated` in `women_secularism_normalised.csv`.
- `0` = original SIGI 2019 survey value
- `1` = filled within +-2yr of 2019
- `NaN` = country not covered by SIGI 2019 or outside the +-2yr window

**Implementation:** `utils.within_country_interpolate()` called in
`src/process_new_datasets.py` with `ffill_limit=2, bfill_limit=2`.

---

## 6. Forward-fill — EPR 2022

**Variable:** `epr_excl_share` (share of ethnic groups politically excluded).

**Issue:** EPR-2021 dataset ends at year 2021; all 2022 values are NaN.

**Method:** Forward-fill `epr_excl_share` by 1 year within each country (fills
2021 value into 2022 where available).

**Justification:** Ethnic exclusion patterns are highly persistent year-to-year —
a 1-year forward fill introduces negligible error compared to leaving ~170
countries missing in 2022. This is explicitly a minimum-intervention fix for a
known data truncation issue.

**Flag column:** `epr_excl_2022_ffill` (boolean) in `women_secularism_normalised.csv`.
- `True` = this row's `epr_excl_share` was filled from the 2021 value
- `False` = original EPR value or already missing before fill

**Implementation:** `src/extract_women_secularism.py`, after loading `phase3_scores.csv`,
using `groupby("iso3")["epr_excl_share"].transform(lambda s: s.ffill(limit=1))`.

---

## 7. Composite index threshold

**Variable:** `women_treatment_index` (unweighted mean of 13 normalised outcome vars).

**Previous method:** `mean(axis=1)` — averaged whatever variables were present,
even if only 1 or 2 were non-null.

**New method:** Require at least 8 of 13 outcome variables to be non-null.
Rows with fewer than 8 variables present are coded as `NaN`.

**Justification:** An unweighted mean computed from 2 of 13 variables would not
represent the same construct as one computed from all 13. The threshold of 8
(>60% of the 13 variables) ensures the composite is substantively meaningful.
Countries with very sparse data (e.g., no V-Dem, no WDI women indicators) receive
NaN rather than a potentially misleading index value. The `women_index_n_vars`
column documents the exact count of contributing variables for each observation.

**Column added:** `women_index_n_vars` — integer count of non-null outcome
variables contributing to the composite for each country-year.

**Coverage impact:** Marginal reduction in the number of rows with a composite
index value (primarily affects very small states and countries with limited WDI
coverage).

**Implementation:** `src/extract_women_secularism.py`, using `apply()` with
`MIN_VARS = 8`.

---

## 8. PCA imputation fix

**Context:** `src/phase2_merge_and_score.py` computes a State Restriction (SR)
and Social Hostility (SH) composite factor using PCA on z-scores of multiple
V-Dem and CIRI indicators.

**Previous method:** Missing z-scores were filled with 0.0 before fitting PCA
(`df[sr_cols].fillna(0.0).to_numpy()`).

**Problem:** Zero-filling for z-scores is biased — a missing value is replaced
with the global mean of the z-score distribution (zero), rather than a
country-specific mean. This causes rows with many missing signals to cluster
near zero in PC1, artificially shrinking within-group variance.

**New method:** Complete-case PCA — two-stage approach:
1. **Estimate loadings** on the subset of rows with ALL signals present
   (complete cases). Requires >=50 complete-case rows; falls back to zero-fill
   if not met.
2. **Score all rows** with >=2 signals using the fitted PC1 weight vector,
   with column-mean imputation for the remaining missing values (unbiased for
   z-score features).

**Justification:** Estimating loadings on complete cases ensures the covariance
structure is not distorted by imputed zeros. Mean imputation for scoring (step 2)
is well-grounded when the mean is close to zero (as for z-scores) and missingness
is scattered. This is the standard two-stage procedure in Dray & Josse (2015),
*missMDA* package documentation.

**Implementation:** `src/phase2_merge_and_score.py`. New helper: `pca1_weight(X)`
returns the PC1 eigenvector without scoring. The SR and SH factors are computed
using the complete-case path with column-mean fallback.

---

## 9. GDP pre-build

**Previous arrangement:** `analyse_secularism_women.py` loaded raw QoG, computed
`log(wdi_gdpcapcon2015)`, and min-max normalised it at analysis time via the
internal `load_gdppc()` function.

**New arrangement:** `build_secularism_composition.py` loads GDP alongside the WVS
variables (same QoG file, same read call), computes `log_gdppc`, normalises with
`robust_minmax()`, and saves `log_gdppc_norm` in
`secularism_composition_normalised.csv`.

**Justification:**
- Single source of truth: the GDP normalisation now uses the same `robust_minmax()`
  function as all other variables, ensuring consistency.
- Analysis scripts no longer need to open raw QoG (reduces coupling and load time).
- The normalisation is computed over the full panel once, not potentially with
  different subsets depending on how the analysis script filters data.

**Column:** `log_gdppc_norm` in `secularism_composition_normalised.csv`.

---

## 10. Configuration centralisation

**Previous arrangement:** `REGION_MAP` (170-country dict) was duplicated in both
`src/analyse_secularism_women.py` and `src/plot_secularism_women.py`, with minor
inconsistencies (Malta in Europe vs. MENA). `FOCAL_PRED` was a hardcoded string in
`plot_secularism_women.py`.

**New arrangement:** `REGION_MAP`, `FOCAL_PRED`, `YEAR_MIN`, `YEAR_MAX` are all
defined once in `src/config.py`. Both analysis and plot scripts import from there.

**Bug fixed:** Malta (MLT) was incorrectly assigned to MENA in the plot script.
The canonical assignment is Europe (Malta is an EU member state). The centralised
`config.py` correctly assigns `MLT: "Europe"`.

**Additional countries added:** The `config.py` REGION_MAP includes the full
Asia-Pacific superset (38 countries), adding Pacific island nations (FSM, KIR,
MHL, NRU, PLW, PRK, SLB, TON, TUV, VUT, WSM) that were missing from the
analyse version.

---

## 11. UNESCO literacy fallback

**Variable:** `wdi_litradf` (female adult literacy rate).

**Issue:** World Bank WDI literacy data is very sparse — collected at irregular
intervals, missing for most country-years.

**Method:** If `data/raw/unesco/uis_literacy_female.csv` exists, load it and fill
gaps in `wdi_litradf` with UNESCO UIS values. The source is documented in the
`wdi_litradf_source` column ("wdi", "uis", or "missing").

**Justification:** UNESCO UIS is the primary global literacy database and
methodologically consistent with WDI literacy. Using UIS as a fallback (not
replacement) is standard practice; WDI itself sources literacy data from UIS in
many cases.

**Column added:** `wdi_litradf_source` in `women_secularism_normalised.csv`.

**Graceful fallback:** If the UNESCO file is absent, the script logs a warning and
continues with WDI-only data. The `wdi_litradf_source` column is still added
(values: "wdi" or "missing").

**Implementation:** `src/extract_women_secularism.py`, after loading QoG.

---

## 12. Pipeline checksums

**Method:** After saving each output CSV, `utils.pipeline_checksum()` computes
the SHA-256 of the DataFrame's CSV content and appends the hash, filename, and
row count to `data/processed/checksums.txt`.

**Justification:** SHA-256 checksums provide:
1. **Reproducibility verification** — re-running the pipeline with the same inputs
   should produce identical checksums.
2. **Data integrity** — detecting accidental file corruption or mid-run overwrites.
3. **Audit trail** — the append-only log shows the history of pipeline runs.

**Format of `checksums.txt`:**
```
women_secularism_normalised.csv    <sha256_hex>    2720 rows
secularism_composition_normalised.csv    <sha256_hex>    2720 rows
```

**Implementation:** `utils.pipeline_checksum(df, path)` in `src/utils.py`.
Called at the end of `extract_women_secularism.py`, `build_secularism_composition.py`,
and `process_new_datasets.py`.

---

## Summary table

| # | Change | File(s) modified | Flag column added |
|---|--------|-----------------|-------------------|
| 1 | Robust min-max (1%/99% winsorisation) | utils.py, extract_*.py, build_*.py, process_*.py | none |
| 2 | General NaN-preserving policy | all | none |
| 3 | pct_* linear interpolation | build_secularism_composition.py | `pct_interpolated` |
| 4 | WVS +-2yr interpolation | build_secularism_composition.py | `wvs_interpolated` |
| 5 | SIGI +-2yr neighbourhood fill | process_new_datasets.py | `sigi_interpolated` |
| 6 | EPR 2022 forward-fill | extract_women_secularism.py | `epr_excl_2022_ffill` |
| 7 | Composite index >=8 var threshold | extract_women_secularism.py | `women_index_n_vars` |
| 8 | Complete-case PCA (mean imputation) | phase2_merge_and_score.py | none |
| 9 | GDP pre-built in comp dataset | build_secularism_composition.py, analyse_*.py | none |
| 10 | REGION_MAP, FOCAL_PRED in config.py | config.py, analyse_*.py, plot_*.py | none |
| 11 | UNESCO literacy fallback | extract_women_secularism.py | `wdi_litradf_source` |
| 12 | SHA-256 pipeline checksums | utils.py, extract_*.py, build_*.py, process_*.py | none |

---

## 13. Planned model: System-GMM (Tier 3)

**Status:** Implemented in `analysis/run_analysis.py` (`tier3_system_gmm()`).

**Decision:** Add Blundell-Bond (1998) system-GMM as a third-tier estimator.

**Justification:** The TWFE model (Tier 2) cannot accommodate a lagged dependent
variable without inducing Nickell (1981) bias (non-negligible at T=16, N≈198), and the
GRI religious institution variables and V-Dem governance controls are plausibly
endogenous with women's welfare. System-GMM resolves both by instrumenting the lagged
DV and endogenous regressors using their own prior lags.

**Estimating equation:**
```
W_it = ρ·W_i,t-1 + β·G_it + γ·X_it + α_i + λ_t + ε_it
```
- `W_it` = `wbl_treatment_index`
- `G_it` = GRI predictors vector (5 variables)
- `X_it` = V-Dem controls + `log_gdppc_norm`
- `α_i`, `λ_t` = country and year fixed effects (absorbed via differencing + year dummies)

**Instrument strategy:**
- Differenced equation: lag 2 of all endogenous variables as instruments
- Levels equation: lag-1 differences as instruments (Blundell-Bond system)
- Collapse instrument matrix (`collapse=True`) — instrument count must not exceed N≈198
- Two-step GMM with Windmeijer (2005) finite-sample SE correction

**Diagnostics to report:**
- Hansen J-statistic (p-value; null = instruments valid; caution if p > 0.25)
- Arellano-Bond AR(1) test (should reject, p < 0.05)
- Arellano-Bond AR(2) test (should NOT reject, p > 0.05 — key validity check)

**Package:** `pydynpd` (`pip install pydynpd`)

**Literature template:** Achuo et al. (2024, *Journal of Economics and Development*),
142-country panel, WBL Index as DV, World Governance Indicators as predictors,
system-GMM robustness specification. Full bibliography in `writing/references_full.bib`.

---

## 14. Planned model: Mundlak RE-FE hybrid (Tier 4)

**Status:** [SUPERSEDED by Entry 15 — now implemented as `tier4_mundlak_re()` in `analysis/run_analysis.py`]

**Decision:** Add the Mundlak (1978) correlated random effects model as a fourth-tier
estimator.

**Justification:** TWFE discards all between-country variation by construction —
it identifies only within-country changes over time. The Mundlak approach retains both
the within and between dimensions, yielding two substantively distinct effects:
(β₁) within — does a country becoming more secular over time improve women's welfare?
(β₂) between — do structurally secular countries have better outcomes than non-secular ones?
These are different theoretical questions. TWFE answers only the first.

**Transformation:** For each time-varying predictor X_it, compute the country mean
X̄_i (average across all years for country i) and add it as an additional regressor:

```
W_it = β₁·X_it + β₂·X̄_i + u_i + ε_it
```

Country means required for: all 5 GRI vars, all 3 V-Dem controls, `log_gdppc_norm`.
Naming convention: suffix `_mean` (e.g. `gri_religious_courts_norm_mean`).

**Key property:** The within coefficient β₁ should equal the TWFE coefficient
numerically. If it does not, this is a sign of a specification error.

**Estimator:** `linearmodels.panel.RandomEffects` (GLS random effects).
- Do NOT demean X_it — keep original values, add X̄_i as separate columns
- Include year dummies
- Entity-clustered standard errors

**Package:** `linearmodels` (already a project dependency)

**Literature references:** Mundlak (1978, *Econometrica*); Bell & Jones (2015,
*Political Science Research and Methods*) for the between/within decomposition
framing. Full bibliography in `writing/references_full.bib`.

---

## 15. Implemented: Mundlak RE-FE hybrid (Tier 4)

**Status:** Implemented in `analysis/run_analysis.py` as `tier4_mundlak_re()`.

**What was done:**
- Added `tier4_mundlak_re()` function using `linearmodels.panel.RandomEffects`
  (GLS random-effects estimator), not pooled OLS
- Country means computed for all 9 time-varying predictors (5 GRI + 3 V-Dem + GDP)
  with suffix `_mean`
- Year dummies included (`pd.get_dummies`, drop_first=True) to absorb common time
  shocks, making within-coefficients comparable to T2 TWFE
- Entity-clustered standard errors for consistency with T2
- Zero-variance mean columns automatically dropped
- Sanity-check print: T4 within-coefficients vs T2 TWFE coefficients
- Results appended to `results/results.csv` as tier `T4_mundlak_re`

**Relationship to existing `phase9_mundlak_cre()`:**
The Phase 9 version uses pooled OLS with country means (valid CRE approach). T4 uses
the proper RE-GLS estimator. Both are retained — Phase 9 serves as a robustness cross-check.

**Interpretation:**
- β₁ on X_it = within-country effect (change in secularism → change in women's welfare)
- β₂ on X̄_i = between-country effect (structurally secular vs non-secular countries)
- If β₁ ≈ T2 TWFE coefficient, the Mundlak specification is consistent

---

## Summary table

| # | Change | File(s) modified | Flag column added |
|---|--------|-----------------|-------------------|
| 1 | Robust min-max (1%/99% winsorisation) | utils.py, extract_*.py, build_*.py, process_*.py | none |
| 2 | General NaN-preserving policy | all | none |
| 3 | pct_* linear interpolation | build_secularism_composition.py | `pct_interpolated` |
| 4 | WVS +-2yr interpolation | build_secularism_composition.py | `wvs_interpolated` |
| 5 | SIGI +-2yr neighbourhood fill | process_new_datasets.py | `sigi_interpolated` |
| 6 | EPR 2022 forward-fill | extract_women_secularism.py | `epr_excl_2022_ffill` |
| 7 | Composite index >=8 var threshold | extract_women_secularism.py | `women_index_n_vars` |
| 8 | Complete-case PCA (mean imputation) | phase2_merge_and_score.py | none |
| 9 | GDP pre-built in comp dataset | build_secularism_composition.py, analyse_*.py | none |
| 10 | REGION_MAP, FOCAL_PRED in config.py | config.py, analyse_*.py, plot_*.py | none |
| 11 | UNESCO literacy fallback | extract_women_secularism.py | `wdi_litradf_source` |
| 12 | SHA-256 pipeline checksums | utils.py, extract_*.py, build_*.py, process_*.py | none |
| 13 | System-GMM (Tier 3) — IMPLEMENTED | analysis/run_analysis.py | `T3_system_gmm` rows |
| 14 | Mundlak RE-FE hybrid (Tier 4) — SUPERSEDED by #15 | analysis/run_analysis.py | none |
| 15 | Mundlak RE-FE hybrid (Tier 4) — IMPLEMENTED | analysis/run_analysis.py | none |

---

## References

- Allison, P.D. (2002). *Missing Data*. Sage.
- Arellano, M. & Bond, S. (1991). Some tests of specification for panel data. *Review of Economic Studies*, 58(2).
- Bell, A. & Jones, K. (2015). Explaining fixed effects: Random effects modelling of time-series cross-sectional and panel data. *Political Science Research and Methods*, 3(1).
- Blundell, R. & Bond, S. (1998). Initial conditions and moment restrictions in dynamic panel data models. *Journal of Econometrics*, 87(1).
- Dray, S. & Josse, J. (2015). Principal component analysis with missing values. *Biometrics*, 71(2).
- Hackett, C. et al. (2017). *The Changing Global Religious Landscape*. Pew Research Center.
- Mundlak, Y. (1978). On the pooling of time series and cross section data. *Econometrica*, 46(1).
- Nickell, S. (1981). Biases in dynamic models with fixed effects. *Econometrica*, 49(6).
- Norris, P. & Inglehart, R. (2004). *Sacred and Secular*. Cambridge University Press.
- OECD (2008). *Handbook on Constructing Composite Indicators*. OECD Publishing.
- Windmeijer, F. (2005). A finite sample correction for the variance of linear efficient two-step GMM estimators. *Journal of Econometrics*, 126(1).
