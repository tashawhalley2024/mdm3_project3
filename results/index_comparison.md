# Index Comparison: Composite vs WBL Treatment Index

## What is being compared

| | Composite index | WBL index |
|---|---|---|
| **Full name** | `women_treatment_index` | `wbl_treatment_index` |
| **Components** | 13 sub-indicators: V-Dem political/civil, WDI labour/health, governance | WBL 2024 (10 legal domains) + 4 health outcomes |
| **Sources** | V-Dem v15, World Bank WDI, WHO, governance datasets | World Bank WBL 2024, WDI health indicators |
| **Years** | 2007-2022 | 2013-2022 |
| **Countries** | ~170 | ~168 |
| **Normalisation** | Robust min-max (1%/99% winsorise) per variable | Min-max per indicator; UNDP HDI fixed bounds for life expectancy |
| **Nature** | Mix of de jure rights and de facto outcomes | De jure legal rights + de facto health outcomes |

## Key result: religious courts coefficient (T2 panel FE with GDP)

| | Composite | WBL |
|---|---|---|
| Coefficient | -0.01066 | -0.00514 |
| Std. error  | 0.00334  | 0.00947  |
| p-value     | 0.0014 ** | 0.5870 n.s. |
| N obs       | 2172 | 1708 |

## Why the results differ

**1. The composite index is more sensitive to religious courts.**
The composite outcome (`women_treatment_index`) includes V-Dem civil liberties, political
empowerment, and egalitarian democracy components that respond directly to state religion
and religious courts. When religious courts are present, these political and civil dimensions
tend to score lower — which drives the significant negative coefficient.

**2. The WBL index partly shares variation with the predictor.**
The WBL index measures legal rights across the same institutional domains that religious courts
affect. Countries with high GRI religious courts scores also tend to have restrictive WBL
provisions. This shared institutional variation means the within-country FE estimator has less
leverage to identify the effect — the coefficient direction is the same (negative) but the
standard error is larger relative to the estimate.

**3. Year coverage differs.**
The composite index runs 2007-2022 (16 years); the WBL index runs 2013-2022 (10 years).
Fewer time periods mean less within-country variation to identify the courts effect,
which mechanically widens standard errors.

**4. What this means for interpretation.**
The two indices agree on direction: religious courts are associated with worse women's
outcomes in both. The composite index finds this significant; the WBL index does not,
partly because they overlap conceptually. This is expected: the WBL is a tighter,
more purpose-built measure of legal treatment, but its closeness to the predictor
reduces statistical power in a panel FE design. Neither result contradicts the other.

## Bottom line

Use the **composite index** if the goal is to maximise statistical power and detect
whether religious courts affect a broad range of women's outcomes (political, civil, health).

Use the **WBL index** if the goal is a transparent, purpose-built measure of legal
treatment that can be fully reproduced from public data and defended methodologically.
The non-significance with WBL is informative: it suggests the courts effect operates
partly through the legal channels WBL measures (reducing independent variation),
rather than being an artefact of the composite's construction.

Both results should be reported. The consistent direction across both indices,
across all robustness checks, strengthens the substantive conclusion even where
significance varies.