# Figure Guide — MDM3 Presentation Companion

> Looking for a plain-English walkthrough for a non-specialist audience? See `presentation_writeup.md` in this folder. That version is rewritten in everyday language with brief layman descriptions of each statistical test and `[insert ... graph here]` markers ready to paste into a Google Doc.

A talking-points companion for each figure in the deck. Each entry has three sections:

- **What it shows** — the concrete contents (axes, elements).
- **Why it's here** — what question it answers in the analysis.
- **What the result means** — the implication for the storyline.

The narrative arc the deck tells: **composite secularism is strongly associated with women's welfare cross-country; within-country over the 2013–2022 panel the signal is null or wrong-signed; figure 03 (between-vs-within hero) shows this geometrically with a quartile staircase and within-country arrows, and figure 12 (Mundlak forest, now in the appendix) is the formal numerical companion. Apostasy laws are the strongest individual sub-item and the only one with a real within-country signal; religious courts is retained as a legacy null.**

Focal predictor and sub-items:
- `composite_secularism_norm` — equal-weighted z-score composite across two dimensions (three *structural* GRI sub-items — state religion, religious law, religious courts; four WVS religious-intensity items), robust min-max scaled to [0,1]. Higher = more religious. Four treatment items (apostasy, blasphemy, gov favouritism, V-Dem religious freedom) were removed from the composite on 2026-04-16 and now appear only as standalone sub-item focals in the decomposition regressions.
- `composite_secularism_pca_norm` — PCA-first-component variant, robustness only.
- `gri_apostasy_norm` — Pew GRI apostasy laws (0/1). Strongest individual sub-item.
- `gri_religious_courts_norm` — Pew GRI religious courts (0/1). Legacy null predictor.

Outcome: `wbl_treatment_index` — composite women's welfare index built by `scoring.py` from World Bank WBL legal-rights data plus de-facto health and political-representation indicators, on a [0,1] scale.

---

## 00_map.png — The composite secularism index, 2020

**What it shows.** A choropleth of the world coloured by each country's `composite_secularism_norm` score in 2020. Light cream = near 0 (most secular). Deep red = near 1 (most religious). Anchor countries labelled. Grey = no data. The colour ramp is continuous; unlike the binary GRI sub-items, the composite varies smoothly.

**Why it's here.** Sets the scene — before any econometrics, viewers should see the geography of the focal predictor. The composite is the variable that carries the headline finding, and its distribution shapes the cross-country reading.

**What the result means.** High composite scores cluster across MENA, Sub-Saharan Africa, South and Central Asia. Low scores sit in Western and Northern Europe, Anglophone North America, and parts of East Asia. The broad geographic pattern lines up with common priors about where institutional secularism and religious practice differ most; the rest of the deck quantifies the association between this spatial pattern and women's welfare.

---

## 01_scatter.png — Bivariate cross-section, 2020

**What it shows.** Two panels, both with the women's treatment index on the y-axis. Left: composite secularism on the x-axis. Right: apostasy on the x-axis. Each point is a country, coloured by region. The line is OLS with 95% CI. Slope (β), p-value and significance stars are annotated.

**Why it's here.** Before introducing fixed effects, panel data, or any controls, *what does the raw cross-sectional correlation look like?* This is the simplest possible question — and the contrast is the visual headline for the deck.

**What the result means.** **Composite panel (left):** downward slope, β ≈ −0.10 in the 2020 cross-section (p = 0.017) under the T1 full-controls spec (rule of law, corruption, education, rurality, political stability, GDP). Countries higher on the composite score systematically lower on women's welfare. **Apostasy panel (right):** same direction, β ≈ −0.12 (p < 0.01) under the same controls; the underlying variable is binary so the dots form two columns. The cross-section reading is consistent across both: more secular countries have better women's welfare, on average.

---

## 02_coefplot.png — Coefficient forest plot, T1 and T2

**What it shows.** Two panels: Tier 1 (cross-sectional OLS, 2020 snapshot, T1 full controls) on the left, Tier 2 (panel fixed effects 2013–2022, country + year FE, clustered SEs, T2 full controls) on the right. Each panel shows coefficients with 95% CIs for the focal composite, the strongest sub-item (apostasy), the legacy sub-item (courts), and the remaining GRI indicators. The control set is rule of law, corruption, education, rurality, political stability, and GDP; GDP is shown last in italic grey as a pure control.

**Why it's here.** The conventional way economists present the headline: cross-section and within-country panel side by side. Two panels because the cross-sectional result and the within-country panel result do not always agree, and the Mundlak decomposition (figure 12) is the natural interpreter of any divergence.

**What the result means.** **Composite:** T1 β = **−0.097 (p = 0.017)**; T2 β = **+0.024 (p = 0.09)**. Significant cross-country signal; within-country mildly positive and marginal under clustered SEs (tightens to p = 0.035 under Driscoll–Kraay HAC with the same point estimate). The sign flip between tiers is the core empirical puzzle and is resolved at figure 03 (geometric) and figure 12 (formal). **Apostasy:** T1 β = −0.119 (p < 0.01); T2 β = −0.018 (p = 0.07, p < 0.01 under DK). Consistent sign across tiers; the only sub-item whose within-country signal survives. **Courts:** T1 β = +0.017 (n.s.); T2 β = −0.007 (n.s.). Null in both. The other GRI variables cluster around zero.

---

## 03_between_within.png — HERO FIGURE — between-country staircase with within-country arrows

**What it shows.** A single panel of the 2013–2022 composite panel (N = 186 countries with ≥3 non-null years). Country-level panel-means are plotted as small region-coloured dots. Behind them, thin grey arrows run from each country's 2013 (composite, women's welfare) point to its 2022 point — showing within-country movement. Overlaid on top, four large navy markers connected by a thick line trace the mean (composite, women's welfare) of each composite quartile Q1 (most secular) → Q4 (most religious). Anchor labels IRN, USA, NOR, IND, SAU, ZAF mark position on the panel-mean dots. A corner annotation quotes the formal T4 Mundlak numbers (β_between = −0.138, p = 0.003; β_within = +0.023, p = 0.12; ratio ≈ 6×, opposite signs) and points to figure 12 for the numerical companion.

**Why it's here.** This is the visual companion to figure 12's formal decomposition. Audiences read geometry faster than forest plots, and the deck's central claim — *the secularism–women's welfare association lives between countries, not within them, over a decade* — is a shape claim. Showing that shape directly, in (composite, welfare) space, makes the claim legible before the econometric machinery that formalises it.

**What the result means.** Two patterns in the same picture. **Between countries:** the quartile line trends down from Q1 to Q4 overall. Q1–Q3 sit at a broadly similar women's-welfare level (~0.66–0.70); Q4 (the most-religious quartile) drops sharply to ~0.57. The structural gap is real but concentrated at the top of the composite distribution — it's a cliff more than a smooth staircase. **Within countries:** the 2013–2022 arrows are short. Most countries barely move on the composite over a decade, and the few that do move do not systematically move toward higher women's welfare. The geometric reading matches the Mundlak numbers: a meaningful between-country effect, a near-zero within-country effect, and the two in opposite directions.

---

## 05_loo_jackknife.png — Leave-one-out stability

**What it shows.** Two columns (composite | apostasy). Top row: a horizontal dot strip — each of 166 small dots is the re-estimated panel-FE coefficient when one country is dropped. Vertical solid line = full-sample baseline; dashed line = zero (sign-flip threshold); shaded band = baseline 95% CI. Bottom row: the 5 countries whose removal changes the coefficient the most.

**Why it's here.** Single-country influence is the classic threat to cross-national panel estimates. The jackknife asks: *if we drop any one country, does the conclusion change?*

**What the result means.** **Composite (left):** the point estimate stays within a narrow band across all 166 single-country drops; no removal flips the sign. The within-country coefficient is small and marginal to begin with, and the jackknife confirms that no single country is driving it in either direction. **Apostasy (right):** 161/166 runs remain significant at p < 0.05; 0 sign flips. The negative within-country effect survives every single-country drop. The bottom-row countries (the most influential individually) are not enough to move the coefficient across the sign-flip line. A clean rebuttal to the "your result is one country" critique for apostasy.

*(Literature: Cooray & Potrafke 2011; Angrist & Pischke 2009.)*

---

## 06_placebo.png — Gendered-mechanism test (apostasy)

**What it shows.** Three bars showing the apostasy coefficient (panel FE, clustered SE) on three outcomes: the women's treatment index (the primary female DV, in red), female life expectancy, and male life expectancy (the placebo).

**Why it's here.** A reviewer's first counter is: *"maybe apostasy proxies for general underdevelopment, and your effect would show up just as strongly on outcomes that have nothing to do with women specifically."* The placebo tests whether male outcomes respond the same way.

**What the result means.** Women's treatment index: β = **−0.018 (p < 0.10)**. Female life expectancy: β ≈ 0 (n.s.). Male life expectancy: β ≈ 0 (n.s.). The effect is concentrated on the *legal* female outcome and absent from biological-style outcomes for either sex. Consistent with a gendered legal-treatment mechanism rather than a generic-underdevelopment proxy. The same placebo run on the composite returns a weaker pattern — the composite's female-outcome coefficient is wrong-signed within country — which is consistent with the composite's within-country signal being noisier than apostasy's.

*Note: female labour-force participation is excluded. FLFP in coercive low-income regimes reflects agricultural compulsion rather than empowerment (Goldin 1995; Mammen & Paxson 2000).*

*(Literature: Seguino 2011; Hakura et al. 2016.)*

---

## 07_spec_ladder.png — Specification stability

**What it shows.** Two panels (composite | apostasy). Each panel stacks 9 specifications: a bivariate baseline, the main FE+GDP spec (highlighted band), and seven sensitivity / subsample variants (CEDAW added, pre-COVID 2013–2019, changers-only, lag L1, lag L2, WEF GGG as alt DV, MENA-only). Coefficients with 95% CIs, colour-coded by significance.

**Why it's here.** "Garden of forking paths" critique: if the result only appears in one specification, it's noise. This figure shows what happens to the focal coefficients under realistic perturbations of the model.

**What the result means.** **Composite (left):** the within-country coefficient stays small and wrong-signed across every panel variant (main, +CEDAW, pre-COVID, changers-only, lagged, MENA-only). The cross-section coefficient (implicit in the bivariate baseline) remains strongly negative throughout. Stability in both the cross-section pattern and the within-country pattern. **Apostasy (right):** Main, +CEDAW, Lag L1, Changers-only are all significantly negative. Pre-COVID and Lag L2 weaken slightly but stay negative. Only MENA-only becomes null (small N). Neither the composite's within-country null nor apostasy's within-country signal is a specification-fragile artefact.

---

## 09_oster_sensitivity.png — Omitted-variable bias robustness (apostasy)

**What it shows.** The Oster (2019) δ statistic plotted against Rmax — the assumed maximum R² that an "ideal" model with all relevant unobservables would achieve, expressed as a multiple of the observed R². The robust region (δ ≥ 1) is shaded green; the threshold δ = 1 is dashed; Oster's two benchmark x-values (1.3× and 2.2×) are vertical dotted lines.

**Why it's here.** All observational estimates are vulnerable to omitted-variable bias. Oster's δ formalises the question "*how strongly correlated with the outcome would unobservables need to be — relative to the observed controls — to drive the apostasy coefficient to zero?*" δ < 1 means weak unobservables would suffice (worry); δ > 1 means stronger-than-controls unobservables would be required (robust).

**What the result means.** δ is well above 1 at Oster's preferred benchmark (Rmax = 2.2×). Unobservables would need to be several times more strongly correlated with women's welfare than the observed controls combined to overturn the apostasy result. Far beyond what is plausible. The strongest single piece of evidence that the apostasy estimate is not driven by an unmodelled confounder.

*Note: A parallel Oster test for the composite within-country coefficient is written to `results/oster_sensitivity.csv`. Its interpretation is weaker because the composite within-country coefficient is already near zero and wrong-signed; the test asks how much bias it would take to move a coefficient to zero, and a coefficient that is already near zero does not benefit from the same framing. We lead with apostasy's Oster result for that reason.*

---

## 10_alt_outcomes.png — Focal-predictor effect across alternative outcomes

**What it shows.** Forest plot: the focal-predictor coefficient (panel FE + GDP) on (i) the primary composite women's treatment index, (ii) the WEF Global Gender Gap Index, (iii) the UNDP GDI, and (iv) the WBL legal rights index. All on a [0,1] scale. Colour-coded by significance.

**Why it's here.** External validity check. The composite index is *our* outcome — would the focal-predictor result look different if we used widely-cited indices built by other organisations?

**What the result means.** The composite's within-country coefficient is small and wrong-signed on the primary composite, the UNDP GDI, and the WBL legal rights index. The WEF Global Gender Gap pulls in the expected cross-sectional direction (negative), but this is against a pre-specified primary outcome; we disclose the WEF pattern rather than adopt it. The within-country null is not an outcome-construction artefact — it holds on the three primary outcomes we pre-specified.

---

## 11_wbl_groups.png — Focal-predictor effect across WBL legal-rights domains

**What it shows.** Forest plot with 11 rows: the focal-predictor coefficient (panel FE + GDP, 2013–2022) on each of the 10 WBL legal-rights group scores produced by `scoring.py` (Assets & Inheritance, Economic Rights, Family & Safety, Health, Mobility, Parenthood, Pay, Pension, Political Representation, Workplace) plus the Overall score at the top.

**Why it's here.** The composite outcome aggregates across many domains. *Could* the focal predictor have a domain-specific effect that washes out in the average — for example, a strong effect on inheritance law swamped by null effects on workplace law?

**What the result means.** No single WBL domain produces a strong within-country coefficient on the focal composite. The within-country null is not an aggregation artefact — it holds at the most granular level we have. The same domain decomposition for courts (shown for comparison in the underlying data) also produces null effects across every domain.

---

## Appendix — 12_mundlak_decomposition.png — formal between-vs-within forest

*Formal coefficient plot of the between-vs-within decomposition. The geometric version (figure 03) is the deck hero; this figure is the numerical companion, kept in the appendix for readers who want the full T4 Mundlak coefficient-and-confidence-interval table.*

**What it shows.** Two panels using the T4 Mundlak random-effects + fixed-effects hybrid (Bell & Jones 2015 framing). **Left:** the within-country effect for each predictor — how a *change* in the predictor within one country relates to a *change* in women's welfare. **Right:** the between-country effect — how a country's *average level* of the predictor relates to its *average level* of women's welfare. The composite row is highlighted. A large between/within ratio annotation sits in the centre.

**Why it's here.** The fixed-effects (T2) result tells you the within-country story; the cross-sectional (T1) result tells you the between-country story; a single Mundlak specification tells you both *side by side* under one model. This is the cleanest way to ask "*is the secularism effect about countries that change, or about countries that differ?*"

**What the result means.** **Composite within-effect:** β ≈ +0.024 (p ≈ 0.07) — small, wrong-signed for the prior. **Composite between-effect:** β ≈ −0.119 (p = 0.004) — negative, correctly signed, significant. The between-to-within ratio in magnitude is roughly **5×**, and the two estimates point in opposite directions. The composite secularism story is cross-national: countries at different points on the secularism spectrum look systematically different on women's welfare, and the structural gap between them is the dominant signal over the 2013–2022 window. This reframes the interpretation: the paper supports the claim that *more secular countries have better women's welfare*, but it does not provide positive evidence that *a country moving toward secularism will see women's welfare improve within a decade*.

**Apostasy in the Mundlak decomposition:** within ≈ −0.018 (p < 0.10), between ≈ −0.126 (p < 0.01); ratio ≈ 7× in magnitude, both correctly signed. Apostasy is the one sub-item whose within-country signal survives and preserves the expected direction. **Courts:** within ≈ 0 (n.s.), between mildly positive and wrong-signed (p ≈ 0.06). Retained as legacy null.

*(Literature: Mundlak 1978; Bell & Jones 2015.)*

---

## 13_long_difference.png — appendix robustness figure

**What it shows.** Two panels for the long-difference regression, which collapses the panel to one observation per country by decade-endpoint subtraction (Δ = value in 2022 − value in 2013). **Left:** forest plot of the coefficient and 95% confidence interval across seven focal variants at 2013→2022 with GDP. Apostasy is greyed (9 changers, flagged invalid under the n_changers ≥ 10 threshold); courts carries a *low-power* warning with 19 changers. **Right:** the decade-change scatter for the headline equal-weight composite — one point per country, coloured by region, with OLS fit and 95% confidence band.

**Why it's here.** The T2 TWFE and T4 Mundlak within coefficients identify off annual movement, a share of which is short-term noise and, for the composite's behavioural dimension, WVS linear-interpolation arithmetic between survey waves. Long-differencing throws away the annual variation and keeps only the endpoint change, so if the within-country null at T2/T4 were driven by noise or interpolation the LD design would recover a sign-correct estimate. Lit precedent: Acemoglu, Johnson, Robinson & Yared 2008; Besley & Persson 2011.

**What the result means.** Composite 2013→2022 with GDP: β = +0.053 (p = 0.17, N = 163) — wrong-signed for the prior, not significant. The within-country null therefore persists at the decade horizon rather than resolving at it: annual noise and WVS interpolation cannot be the binding explanation for the T2/T4 within null.

**Where it lives.** The figure is demoted to Appendix A.2 of `methodology_full.tex` (`\label{sec:ld-details}`) rather than to the main Robustness section. The paper's treatment of long-difference is a single row in tab:headline plus a 2-paragraph §5.8 summary; the figure is reference material for readers who want to verify the point estimates across focal variants. Not on the headline slide deck.

---

## Suggested slide order

If you have ~10 slides:

1. **00 map** — geography of composite secularism (sets the scene).
2. **01 scatter** — raw bivariate contrast (the cross-section headline visually).
3. **02 coefplot** — the formal result, T1 cross-section and T2 panel FE side by side.
4. **03 between_within (HERO)** — the geometric between-vs-within picture. Audiences read geometry faster than forest plots; this is the deck's central visual.
5. **05 LOO** — robustness: not driven by any one country.
6. **07 spec ladder** — robustness: stable across specifications.
7. **09 Oster** — robustness: apostasy survives extreme OVB.
8. **06 placebo** — mechanism: apostasy is gendered, not generic.
9. **10 alt outcomes** — external validity across outcome indices.
10. **11 WBL groups** — domain-by-domain null check on the within-country coefficient.

Figures 12 (Mundlak forest) and 13 (long-difference) are appendix/Q&A figures rather than slides. Pull up figure 12 if a reviewer wants the formal between-vs-within numbers and confidence intervals behind figure 03's geometric version. Pull up figure 13 if a reviewer asks whether the within-country null is an annual-noise or WVS-interpolation artefact. Keeping both off the main deck keeps the 10-slide structural-cross-country story clean.

Closing: the composite secularism–women's welfare association is strong cross-country and small or wrong-signed within-country over a decade; apostasy is the strongest individual sub-item and the only one with a real within-country signal; religious courts is a power-limited null, retained for legacy comparison.
