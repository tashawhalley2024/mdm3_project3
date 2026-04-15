# Robustness Storyline — Presentation Guide

## Narrative Arc

Religious courts (the focal predictor) show **no within-country effect** across any specification. Apostasy laws emerge as the key finding: robustly associated with worse women's welfare, primarily as a **structural cross-country difference** rather than a within-country temporal change.

---

## Core Estimators (4 tiers — all presented)

| Tier | What it does | Key result |
|------|-------------|------------|
| **T1 OLS** (2014 & 2020, HC3 SEs) | Baseline cross-sectional correlation | Apostasy p<0.001; courts n.s. |
| **T2 TWFE** (entity + year FE, clustered SEs) | Within-country identification (annual) | Apostasy p=0.035; courts p=0.312 |
| **T3 System-GMM** (Blundell-Bond) | Dynamic panel with internal instruments | Fails diagnostics (rho=1.215 > OLS bound). Reported for transparency, excluded from conclusions |
| **T4 Mundlak CRE** (within/between decomposition) | Separates structural vs temporal effects | Apostasy between-effect is **6.2x** the within-effect. Courts null in both |

**Takeaway:** The four tiers consistently show courts is null and apostasy is significant. T4 reveals the effect is overwhelmingly cross-national (between-country), not driven by within-country change over time.

**Long-difference robustness complement** (not a separate tier): a decade-change regression (Δoutcome 2013→2022 on Δfocal + Δcontrols, HC3 SEs, one obs per country) is reported alongside T2/T4 to test whether the within-country null could be an artefact of annual noise or WVS interpolator arithmetic. Composite LD β=+0.082 (p=0.28, N=163) — wrong-signed and not significant, same direction as T2/T4 within. Since endpoint differencing throws away annual variation and interpolator contamination by construction, the persistence of the null at the decade horizon rules out both as the binding explanation for the short-panel null. Reported in methodology_full.tex §5.8; underlying rows under `T5_long_diff_*` tiers in results.csv.

---

## Essential Robustness Checks (6 — present these)

### 1. Variance Decomposition
- **Threat:** If courts has almost no within-country variation, TWFE is poorly identified
- **Result:** Only 27% of courts variation is within-country; only 38/168 countries show meaningful changes
- **Literature:** Angrist & Pischke (2009)
- **Why it matters:** Explains why T2 cannot detect a courts effect — there is almost nothing to identify from. Justifies the Mundlak decomposition (T4) as the interpretively central estimator

### 2. Leave-One-Out Jackknife (apostasy)
- **Threat:** Result driven by a single influential country (e.g., Saudi Arabia)
- **Result:** 164/168 runs remain significant at p<0.05; **0 sign flips**
- **Literature:** Cooray & Potrafke (2011), Angrist & Pischke (2009)
- **Why it matters:** Confirms the apostasy finding is not an artifact of any single country's inclusion

### 3. Placebo Outcomes — Male DVs (apostasy)
- **Threat:** Effect reflects general underdevelopment, not a gendered mechanism
- **Result:** Apostasy significantly predicts female treatment index (p=0.035) and female LFP (p=0.023) but NOT male life expectancy (p=0.992) or male LFP (p=0.229)
- **Literature:** Seguino (2011), Hakura et al. (2016)
- **Why it matters:** Establishes a gendered mechanism — apostasy laws constrain women specifically, not general welfare

### 4. Oster Delta (apostasy)
- **Threat:** Omitted variables could explain away the finding
- **Result:** delta = 17.9 at Rmax = 2.2x R_full (far above threshold of 1). Unobservables would need to be **18x more correlated** with the outcome than all observed controls combined
- **Literature:** Oster (2019)
- **Why it matters:** The gold standard for assessing omitted variable bias in observational studies. delta >> 1 means the result is highly robust

### 5. Lagged Predictors (L1, L2)
- **Threat:** Reverse causality — countries that improve women's welfare may subsequently liberalise religious law
- **Result:** L1 and L2 lags of apostasy show contemporaneous effect, not lagged. Reverse-causality test (outcome_t -> courts_t+1) is null
- **Literature:** Bellemare, Masaki & Pepinsky (2017); Ben-Nun Bloom et al. (2016)
- **Why it matters:** Rules out the most obvious reverse-causality story

### 6. Changers-Only Subsample
- **Threat:** FE result driven by noise from ~130 non-changing countries (FE absorbs all their courts variation)
- **Result:** Restricting to ~47 countries with actual courts changes, apostasy remains significant (p<0.01)
- **Literature:** Cooray & Potrafke (2011)
- **Why it matters:** Confirms the effect comes from countries that actually experienced institutional change, not cross-sectional noise

---

## Supporting Evidence (5 — backup/appendix)

| Check | What it shows | Key result |
|-------|--------------|------------|
| **LOO Jackknife (courts)** | Null is stable — no country removal makes courts significant | Stable null, 166/166 runs p>0.05 |
| **Caveat — courts in WEF GGG** | Courts is null in the primary composite + GDI + WBL legal rights, **but turns p=0.037** when the WEF Global Gender Gap is the outcome. Disclose openly: a single external index departs from the null. | Honest robustness disclosure |
| **Reverse causality test** | Outcome does not predict future courts adoption | Null in both directions |
| **WBL group decomposition** | Which legal domains respond to courts? | Courts null across all 10 WBL groups |
| **Regional heterogeneity (MENA)** | Is apostasy effect concentrated by jurisdiction? | Stronger in MENA where religious law has real jurisdiction |
| **Sub-period (2013-2019)** | Is result stable excluding COVID years? | Identical results |

---

## Power Analysis for the Null Courts Result

The T2 panel FE coefficient for religious courts is -0.007 (SE = 0.007).

- **95% CI:** [-0.020, +0.007] — we can rule out effects larger than |0.020| on the 0-1 welfare scale
- **MDE at 80% power:** 0.019 units
- **Within-country variance:** only 27% of total courts variation is within-country
- **Changers:** only 38 of 168 countries show meaningful within-country changes

**Interpretation:** The null finding for religious courts is a combination of (a) a genuinely small or zero within-country effect and (b) limited statistical power due to the slow-moving nature of the variable. The Mundlak between-country effect (+0.042, p=0.064) is marginally non-significant, suggesting courts does not robustly predict women's welfare cross-nationally once other GRI dimensions are controlled.

---

## Checks Dropped from Presentation (and why)

Several robustness checks were computed but are excluded from the presentation because they are either logically misapplied, redundant with existing results, or unsuited to this data structure:

- **Event studies (both predictors):** Designed for sharp policy changes, not slow-moving institutional variables where 73% of variation is between-country. All event-time coefficients are near zero with large standard errors — uninformative by construction.
- **Oster delta/sensitivity for courts:** The Oster test asks "could omitted variables explain a significant result?" Applying it to a non-significant predictor (p=0.584) is logically inverted; the large delta arises mechanically because the coefficient barely changes, not because the result is robust.
- **Wild cluster bootstrap:** Addresses small-cluster bias (<50 clusters). The full sample has ~170 clusters, well above the Cameron et al. (2008) threshold. Redundant with entity-clustered SEs.
- **Driscoll-Kraay SEs:** Produces a smaller SE than entity-clustered (0.003 vs 0.007) because bandwidth=4 does not capture the full within-country autocorrelation of slow-moving GRI variables over 16 years. With N=168 and T=16, cluster-robust is the preferred SE per Cameron & Miller (2015). The DK result for courts (p=0.026) is reported in results/README.md for transparency but is not the primary inference.
- **Redundant Mundlak CRE (Phase 9d):** Identical estimator to T4 using pooled OLS instead of GLS — same results, no added value.

---

## Key Figures for Presentation

| Figure | What to show | File |
|--------|-------------|------|
| Mundlak decomposition | Within vs between effects — apostasy 6.2x ratio | `figures/12_mundlak_decomposition.png` |
| Coefficient forest plot | T1 & T2 coefficients with CIs | `figures/02_coefplot.png` |
| LOO jackknife | Stability of apostasy coefficient | `figures/05_loo_jackknife.png` |
| Placebo outcomes | Female vs male — gendered mechanism | `figures/06_placebo.png` |
| WBL groups | Courts null across all 10 legal domains | `figures/11_wbl_groups.png` |
| World map | Geographic distribution of religious courts | `figures/00_map.png` |
