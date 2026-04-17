# Mundlak RE-FE Hybrid: How It Was Implemented

## The Problem T4 Solves

T2 (Two-Way Fixed Effects) controls for all time-invariant country characteristics by demeaning — subtracting each country's average from every observation. This eliminates confounding from things like legal tradition or colonial history, but it also **throws away all between-country variation**. The only variation left is *within*-country changes over time.

For slow-moving variables like institutional secularism (GRI scores barely change year to year within a country), this means T2 is trying to identify an effect from very little signal — which is why the within-R² is only 0.005.

The Mundlak (1978) approach keeps both dimensions: it estimates a **within effect** (does a country becoming more secular over time see improved women's welfare?) and a **between effect** (do structurally secular countries have better outcomes than non-secular ones?).

## The Mundlak Device

For every time-varying predictor X_it, compute the country mean:

```
X̄_i = (1/T_i) * Σ_t X_it
```

Then estimate a Random Effects model with both X_it and X̄_i as regressors:

```
W_it = β₁·X_it + β₂·X̄_i + year_dummies + u_i + ε_it
```

- **β₁** = within effect (same interpretation as TWFE)
- **β₂** = between effect (cross-country structural differences)
- **u_i** = random country effect (GLS)

The key mathematical property: including X̄_i in a Random Effects model makes the RE estimator consistent even when u_i is correlated with X_it — which is exactly the condition that normally makes RE biased and FE necessary. The country means "absorb" the correlation.

## What the Code Does

**Function:** `tier4_mundlak_re()` in `analysis/run_analysis.py`

**Step 1 — Prepare data.** Same sample as T2_with_gdp: drop rows with any missing values across outcome + 6 GRI + 5 controls + GDP. Result: 1,639 observations, 166 countries.

**Step 2 — Compute country means.** For each of the 12 time-varying predictors, compute the within-country arithmetic mean using `groupby("iso3").transform("mean")`. These get suffix `_mean` (e.g. `gri_apostasy_norm_mean`). Each country-mean column is constant within a country and varies only between countries.

**Step 3 — Add year dummies.** `pd.get_dummies(year, drop_first=True)` creates 9 binary columns (2014–2022, with 2013 as reference). These absorb common time shocks, making β₁ comparable to T2's time-FE specification.

**Step 4 — Estimate.** `linearmodels.panel.RandomEffects` with the full predictor set (12 original + 12 means + 9 year dummies + constant). Fitted with entity-clustered standard errors for consistency with T2.

**Step 5 — Output.** Results appended to `results/results.csv` as tier `T4_mundlak_re`. Each coefficient gets one row.

## Verification

Three properties were tested to confirm correctness:

1. **Within-coefficients match TWFE.** The β₁ on each X_it should numerically equal the T2 TWFE coefficient. Confirmed — maximum difference across all 12 predictors is within GLS vs OLS rounding.

2. **Between and within effects differ.** GRI variables show different β₁ vs β₂, confirming unobserved heterogeneity exists.

3. **Mundlak test (equivalent to Hausman).** If the country-mean variables are jointly significant, simple RE is inconsistent and FE/CRE is needed — confirms T2's FE approach was warranted.

## Key Results

Current coefficients for every predictor (within β₁ and between β₂, p-values, sample sizes) live in `results/results.csv` under `tier == "T4_mundlak_re"`. The headline pattern is that between-effects are substantially larger than within-effects and often opposite in sign: secularism differences *across* countries are more predictive of women's welfare than *within*-country changes over the 2013–2022 window. This is consistent with the low T2 within-R² and suggests institutional secularism is a slow-moving structural feature rather than a lever that produces rapid within-country change.
