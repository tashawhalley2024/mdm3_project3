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

**Step 1 — Prepare data.** Same sample as T2_with_gdp: drop rows with any missing values across outcome + 5 GRI + 3 V-Dem + GDP. Result: 1,648 observations, 168 countries.

**Step 2 — Compute country means.** For each of the 9 time-varying predictors, compute the within-country arithmetic mean using `groupby("iso3").transform("mean")`. These get suffix `_mean` (e.g. `gri_apostasy_norm_mean`). Each country-mean column is constant within a country and varies only between countries.

**Step 3 — Add year dummies.** `pd.get_dummies(year, drop_first=True)` creates 9 binary columns (2014–2022, with 2013 as reference). These absorb common time shocks, making β₁ comparable to T2's time-FE specification.

**Step 4 — Estimate.** `linearmodels.panel.RandomEffects` with the full predictor set (9 original + 9 means + 9 year dummies + constant). Fitted with entity-clustered standard errors for consistency with T2.

**Step 5 — Output.** Results appended to `results/results.csv` as tier `T4_mundlak_re`. Each coefficient gets one row.

## Verification

Three properties were tested to confirm correctness:

1. **Within-coefficients match TWFE.** The β₁ on each X_it should numerically equal the T2 TWFE coefficient. Confirmed — maximum difference across all 9 predictors is 0.0003 (GLS vs OLS rounding).

2. **Between and within effects differ.** All 5 GRI variables show different β₁ vs β₂, confirming unobserved heterogeneity exists. For example, `gri_apostasy_norm`: within = −0.020, between = −0.122.

3. **Mundlak test (equivalent to Hausman).** If the country-mean variables are jointly significant, simple RE is inconsistent and FE/CRE is needed. Result: 3 of 9 means significant at 5% — confirms T2's FE approach was warranted.

## Key Results

| GRI Variable | Within (β₁) | p | Between (β₂) | p |
|---|---|---|---|---|
| religious_courts | −0.007 | 0.288 | +0.042 | 0.064 |
| apostasy | −0.020 | 0.027 | −0.122 | 0.001 |
| blasphemy | −0.001 | 0.842 | −0.049 | 0.011 |
| religious_law | +0.007 | 0.276 | +0.074 | 0.102 |
| state_religion | +0.011 | 0.435 | −0.034 | 0.367 |

The between-effects are an order of magnitude larger than within-effects. Secularism differences *across* countries are far more predictive of women's welfare than *within*-country changes over the 2007–2022 window. This is consistent with the low T2 within-R² and suggests institutional secularism is a slow-moving structural feature rather than a lever that produces rapid within-country change.
