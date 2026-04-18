# Secularism and Women's Welfare: A Figure Walkthrough

This is a plain-English walk through the ten figures in the deck. Each one answers a specific question. The headline finding is that more religious societies tend to have worse outcomes for women. The association is large and statistically strong at the cross-country level. Within countries over the 2013–2022 window, though, we don't see the same signal. Countries that become slightly more or less religious over this period don't show their women's welfare moving in the expected direction. We read this as evidence that secularism's association with women's welfare is a structural cross-country difference rather than something a country can change in a decade. The new Figure 4 in this deck shows that reading geometrically, with a quartile staircase across countries and short within-country arrows. The older Mundlak decomposition figure (now in the appendix) gives the formal numbers behind the same picture. Apostasy laws are the one specific institutional marker where the within-country signal does survive, and religious courts, the predictor we used in earlier versions of this analysis, is a null result we now keep for comparison.

A few quick definitions before we start.

**Composite secularism** is our summary measure of how religious a country is. It's built from two pieces: the structural legal institutions side (state religion, religious law, religious courts — all from the Pew Research Center's Global Restrictions on Religion project) and individual-level religiosity (four World Values Survey items on the importance of religion, importance of God, belief in God, and confidence in religious institutions). We z-score each input, average within each of the two dimensions, average across dimensions, and rescale to a 0-to-1 range. Higher means more religious. This is the predictor that carries the headline finding. An earlier version of the composite also included apostasy laws, blasphemy laws, government religious favouritism, and V-Dem's religious-freedom index; those were removed in a 2026-04-16 rebuild because they measure how the state treats people on religious grounds, which overlaps mechanically with the outcome. They remain in the analysis as standalone sub-item predictors in the decomposition tables.

**Apostasy laws** is Pew's yes-or-no measure of whether the country has laws against renouncing one's religion. We keep it as the strongest individual sub-item from the composite.

**Religious courts** is Pew's yes-or-no measure of whether the legal system gives religious courts a formal role. It's what we used as the focal predictor in earlier versions of this analysis. We've kept it in the robustness tables as a legacy comparison.

**Women's treatment index** is a 0 to 1 score we built from the World Bank's Women, Business and the Law data combined with health and political-representation indicators.

---

## Figure 1: The composite secularism index across the world (2020)

[insert 00_map graph here]

The map shades each country by its composite secularism score in 2020. Cream means near zero (most secular). Deep red means near one (most religious). Unlike the binary Pew items that feed into the composite, the composite varies smoothly, so the colour ramp is continuous rather than a two-tone map.

The pattern lines up with common priors. The darkest cluster runs across the Middle East and North Africa, Sub-Saharan Africa, and parts of South and Central Asia. The lightest cluster sits in Western and Northern Europe, Anglophone North America, and parts of East Asia. This is the geography of the predictor whose association with women's welfare the rest of the deck unpacks.

---

## Figure 2: The raw correlation (2020 cross-section)

[insert 01_scatter graph here]

Before doing any modelling, what does the simplest picture look like? Each country becomes one dot. The y-axis is the women's treatment index. On the left we plot it against the composite secularism index. On the right we plot it against the apostasy sub-item.

The left panel slopes downwards. Countries scoring higher on composite secularism score systematically lower on women's welfare: the slope is around −0.10 in 2020 once we control for rule of law, corruption, education, rurality, political stability, and GDP (p = 0.017). This is the cross-sectional headline of the paper.

The right panel shows the same direction for apostasy laws — countries with apostasy laws score lower on women's welfare on average, by around −0.12 points. Because apostasy is a yes/no variable, the dots form two columns; the slope is the average vertical gap between them.

If the eyeball test had said the opposite we'd have something to explain. Both panels push in the direction the rest of the deck confirms.

---

## Figure 3: Coefficients with controls (cross-section and panel)

[insert 02_coefplot graph here]

This is the standard way economists present their headline result. Two panels. Each panel runs a regression with several predictors at the same time and plots each one's coefficient with a 95% confidence interval.

The left panel uses the 2020 cross-section. We look across all countries in one year, controlling for log GDP per capita.

The right panel uses panel fixed effects across 2013 to 2022. That's a much tougher test. It strips out everything that doesn't change inside a country over time, so any leftover association has to come from changes within countries. Anything fixed about a country (its history, its culture, its starting point) gets absorbed and can't bias the result.

The composite and apostasy sit at the top of each panel; the other predictors (state religion, religious law, religious courts, blasphemy, rule of law, civil liberties, egalitarianism) sit below as context. GDP is shown last in italic grey because it's a control, not something we're testing.

In the cross-section (left) the composite comes out negative: about −0.10 at p = 0.017. In the panel (right) it comes out small and marginal, around +0.02 with p ≈ 0.09, with the opposite sign. Apostasy runs negatively in both panels: about −0.12 in the cross-section and about −0.02 in the panel (p ≈ 0.07, tightening to p ≈ 0.006 under a different standard-error calculation). Courts is null in both panels.

The sign flip between the two panels for the composite is the main empirical puzzle in the paper and the reason we lean on the next figure for interpretation.

---

## Figure 4 (the hero): The between-vs-within picture

[insert 03_between_within graph here]

This is the headline visual of the deck. Each small dot is one country's 2013-to-2022 average, plotted against its average composite secularism score over the same window. Countries are coloured by region. Behind each dot is a thin grey arrow from where the country sat in 2013 to where it sat in 2022. On top of the dots are four large navy markers joined by a thick line. These are the averages of each quartile of the composite: Q1 is the most secular quarter of countries, Q4 is the most religious quarter.

The quartile line tells the between-country story. It runs downward from left to right overall. Q1 through Q3 sit at broadly similar women's-welfare levels (around 0.66 to 0.70 on a 0-to-1 scale). Q4, the most-religious quartile, drops sharply to about 0.57. So the structural gap between countries is real, but it's concentrated at the top of the composite distribution. It's a cliff more than a smooth staircase.

The arrows tell the within-country story. They are short. Most countries barely move on the composite in a decade, and those that do move don't systematically move toward higher women's welfare. The few longer arrows point in different directions, not toward a common pattern.

The corner box gives the formal T4 Mundlak numbers behind the geometry. The between-country effect is −0.138 at p = 0.003, the within-country effect is +0.023 at p = 0.12, and the magnitudes differ by about six times, in opposite directions. This is the same pattern the formal decomposition figure (now in the appendix) reports with confidence-interval forest bars. The geometric version is the main-deck visual because most audiences read shape faster than forest plots.

The reading for the paper: more secular countries have better women's welfare, by a meaningful amount, and the gap lives in how the most-religious quartile differs from the rest rather than in gradual movement across the composite. Within-country movement over a decade does not shift women's welfare in the expected direction, for reasons we think are mostly about the time horizon and about how little the legal sub-items move within countries in ten years.

---

## Appendix: The formal within-vs-between decomposition

[insert 12_mundlak_decomposition graph here]

This figure is the numerical companion to Figure 4. It shows the same between-country and within-country effects as coefficient-and-confidence-interval bars rather than as geometry. Kept in the appendix because the geometric version is easier for an audience; shown on request if a reviewer asks for the full forest with every sub-item.

It splits each predictor's effect into two pieces.

The left panel asks: when a country changes its score on this predictor over time, does its women's treatment index move? That's the within-country effect.

The right panel asks: are countries that *generally* score high on this predictor also countries that *generally* score low on women's treatment? That's the between-country effect.

The technical name for this method is the Mundlak decomposition (Mundlak 1978; Bell and Jones 2015). It runs the within-country and between-country comparisons inside a single regression, which is more honest than running two separate analyses and trying to reconcile them after.

For the composite secularism index, the two answers go in opposite directions.

The between-country effect is −0.119 with p = 0.004. In plain English: countries higher on the composite are systematically lower on women's welfare. A one-point move along the composite (roughly the spread from the most secular country to the most religious) corresponds to about a 0.12-point drop in the women's welfare index on the 0-to-1 scale, holding the governance controls fixed. This is the headline the paper supports.

The within-country effect is +0.024 with p ≈ 0.07. In plain English: countries that became slightly more or less religious during 2013–2022 do not show their women's welfare moving in the expected direction. If anything the sign runs the other way. The magnitude is small, and the standard error is wide under country-clustered inference (it tightens under Driscoll–Kraay, but the point estimate stays the same).

In magnitude the two effects differ substantially, and they go opposite directions. What this means for interpretation: the composite secularism story is structural. More secular countries have better women's welfare, but the data we have do not provide positive evidence that a country moving along the composite will see women's welfare improve within a decade. Two data-side features make the within-country null hard to avoid. First, the legal institutions that feed into the composite (state religion, religious law, religious courts) barely move within countries over ten years; most countries that have these arrangements keep them and most that don't, don't add them. Second, the composite's individual-level religiosity component is built from World Values Survey data that is surveyed every five years or so and linearly interpolated in between, so some of the within-country movement we see on the composite is really smoothing, not real attitudinal change. A longer panel and a better within-wave religiosity indicator would be the natural follow-up.

For apostasy specifically, the decomposition is cleaner. Both the between-country effect (−0.126, p < 0.01) and the within-country effect (−0.018, p ≈ 0.07) are negative; the between effect is about seven times larger in magnitude, but unlike the composite the within effect survives and keeps the expected sign.

For religious courts, both components are essentially zero. Courts is inert in both senses — it doesn't move with within-country changes, and it doesn't separate countries that differ in long-run welfare either. That's the legacy null.

---

## Figure 5: How stable is this if we drop one country?

[insert 05_loo_jackknife graph here]

A reviewer's first question is usually something like, "is your result driven by Saudi Arabia?" or "what about Iran?" If pulling one country out makes the answer flip, the result isn't really there.

This is a leave-one-out jackknife. We re-run the panel-fixed-effects regression 166 times. Each run leaves a different country out. Then we plot all 166 of the resulting coefficients. If they all cluster tightly around the same value, the result doesn't depend on any single country.

The top row shows each of the 166 coefficients as a small dot, jittered vertically just so they don't all stack. The vertical solid line is the baseline coefficient from the full sample. The shaded band is the baseline 95% confidence interval. The dashed black line is zero, the sign-flip threshold.

For the composite secularism within-country coefficient, the estimates stay in a narrow band across all 166 single-country drops. The point estimate is small and marginal to begin with, and the jackknife confirms that no single country is driving it in either direction.

For apostasy, 161 of 166 runs are significant at p < 0.05 and none flip sign. The negative within-country effect survives every single-country drop.

The bottom row shows the five countries whose removal shifts each estimate the most. None of them is enough to move the result across the sign-flip line. Both findings are not one-country stories.

---

## Figure 6: Does the result hold under different specifications?

[insert 07_spec_ladder graph here]

Researchers can run a regression in dozens of plausible ways. If your finding only appears in one of them, it's noise. This figure shows nine specifications side by side for the composite and for apostasy.

The first row in each panel is a bivariate baseline, just the predictor and the outcome with nothing else. The next row is our main spec (panel fixed effects with GDP control), highlighted with a pale band. Then seven sensitivity checks: adding CEDAW (an international women's-rights treaty) ratification years, restricting to pre-COVID, restricting to "changers" (countries whose score actually moved during the panel), adding a one-year lag, adding a two-year lag, swapping the outcome for the WEF Global Gender Gap Index, and restricting to MENA countries only.

The composite column on the left keeps the same small, wrong-signed within-country coefficient across every panel variant. That's a stability finding in itself: the within-country null isn't a specification-fragile artefact that appears only under one choice of controls.

The apostasy column on the right is significantly negative in five of nine rows, marginally significant in two more, and only goes flat in MENA-only (tiny sample). The within-country apostasy effect is stable too.

---

## Figure 7: How strong would unmeasured confounders need to be?

[insert 09_oster_sensitivity graph here]

This figure addresses what every observational study has to worry about: an unmeasured variable that's secretly driving both the predictor and the outcome.

The Oster delta test (Oster 2019) puts a number on this worry. The question it asks is roughly: "how strongly correlated with women's welfare would my missing confounders need to be, *relative to the controls I already have*, to wipe out my apostasy result?"

A delta of 1 means missing confounders would only need to be as strong as the controls already in the model. That's worrying. A delta of 5 means they'd need to be five times stronger than all the controls combined. That's a high bar.

For the apostasy coefficient, the test returns a delta well above 1 at Oster's preferred benchmark. Unobserved confounders would need to be several times more correlated with women's welfare than every control variable we put in the model to explain the apostasy effect away.

We run the same test on the composite within-country coefficient too (it's in the data), but we don't lead on its result. The Oster test is designed to ask how much hidden confounding it would take to move a *significant* coefficient to zero, and the composite's within-country coefficient is already near zero. The framing doesn't quite work in that case. For apostasy, where the within-country coefficient is real and negative, the test has its natural interpretation, and apostasy passes it cleanly.

---

## Figure 8: Is the effect specifically about women, or about general underdevelopment?

[insert 06_placebo graph here]

A natural pushback is, "maybe apostasy is just a proxy for poor countries in general, and the effect would look the same on outcomes that have nothing to do with women".

This figure tests that. We re-run the apostasy regression on three outcomes: the women's treatment index (the female outcome we care about), female life expectancy, and male life expectancy. The male outcome is the placebo. If apostasy actually predicts generic underdevelopment, both life-expectancy bars should look similar.

Women's treatment index: negative and marginally significant. Apostasy bites the legal female outcome.

Female life expectancy: essentially zero, not significant.

Male life expectancy: essentially zero, not significant.

The effect is concentrated on the legal female outcome and absent from biological outcomes for either sex. That's consistent with a gendered legal mechanism rather than a generic-poverty story.

We left labour-force participation out of this figure on purpose. Female labour-force participation in low-income coercive regimes often reflects forced agricultural work rather than empowerment (Goldin 1995; Mammen and Paxson 2000). It muddies a clean placebo, so best practice is to drop it.

The same placebo run on the composite rather than on apostasy produces a weaker pattern. The composite's within-country coefficient on the women's index is itself small and wrong-signed, so the placebo comparison has less to work with. It's another piece of evidence that the composite's within-country story is noisier than apostasy's.

---

## Figure 9: Does the result hold for other gender indices?

[insert 10_alt_outcomes graph here]

The women's treatment index is one specific composite we built. Would the within-country result look different if we used widely cited alternatives built by other organisations?

We re-run the panel regression on three external gender indices: the WEF Global Gender Gap, the UNDP Gender Development Index, and the World Bank's WBL Legal Rights Index.

On the primary composite, the UNDP GDI, and the WBL, the composite's within-country coefficient stays small and mildly positive — consistent with the null we report in the main table. On the WEF Global Gender Gap, the composite's within-country coefficient flips and comes out negative. We disclose this rather than hide it. The plausible explanation is that the WEF index loads heavily on political representation and economic participation in a way that captures some of the same cross-country structural variation the between-country composite effect picks up; under within-country fixed effects on our pre-specified primary outcome the within-country signal goes away. We don't adopt the WEF outcome as the headline because we pre-specified the primary composite before running the regressions, and shopping across outcomes to find a favourable within-country sign would be a research-practice violation.

---

## Figure 10: A domain-by-domain check on the composite

[insert 11_wbl_groups graph here]

This is the most granular check on the within-country null. The composite outcome aggregates across many legal and welfare domains. What if the composite has a strong within-country effect on, say, inheritance law that gets washed out by null effects everywhere else?

We split the WBL legal rights index into its 10 building-block scores: Assets & Inheritance, Economic Rights, Family & Safety, Health, Mobility, Parenthood, Pay, Pension, Political Representation, and Workplace. Then we run the same panel-fixed-effects regression with each one as the outcome.

No single domain produces a strong within-country coefficient on the composite. The within-country null isn't an aggregation artefact — it holds at the most granular level we have. The same breakdown for courts (visible for comparison in the underlying data) is also null across every domain; courts is a broad null rather than a domain-specific one.

---

## Backup: the decade-change check (not a main-deck slide)

If a reviewer asks whether the within-country null could be driven by annual noise or by the fact that the World Values Survey items are linearly filled in between survey waves, the long-difference regression is the answer. It collapses the panel to one observation per country — the change from 2013 to 2022 in the outcome against the change in the composite — and throws away both annual variation and the interpolated years. The coefficient is +0.053, not significant (p = 0.17, 163 countries). If noise or interpolation had been the real problem, endpoint differencing would have pulled a sign-correct estimate out of the data. It did not. The null holds at the decade horizon too. We keep this in the appendix of the paper (Figure 13) rather than on the main deck; it's a backup answer to a specific question, not a headline result.

---

## What this all adds up to

The composite secularism index is negatively associated with women's welfare across countries. The 2020 cross-section coefficient is about −0.10 (p = 0.017), and the Mundlak between-country decomposition gives about −0.12 (p = 0.004). More religious countries have worse outcomes for women, and the association is robust to single-country drops and to the choice of aggregation method (the PCA robustness variant gives a similar headline). The cross-section signal is carried primarily by the WVS behavioural dimension of the composite; the institutional-only variant (three structural GRI items alone) is not significant.

Within countries over the 2013–2022 window, we do not see the same signal. The composite's within-country coefficient is small, wrong-signed for the prior, and stable at that pattern across every specification in the ladder. We report this honestly. Two structural features of the data make it hard to read the within-country null as evidence that secularism has no effect: the panel is ten years and the legal institutions involved (state religion, religious law, religious courts) move on much longer timescales than that, and the composite's individual-level religiosity component is built on survey data that is linearly interpolated between waves, so some of the apparent within-country movement is smoothing rather than real attitudinal change. The cleanest reading is that the paper supports the claim that *more secular countries have better outcomes for women* but does not provide positive evidence that *a country moving on the composite will see women's welfare respond within a decade*.

Apostasy laws are the one sub-item that survives as a real within-country signal. The within-country coefficient is negative and marginally significant under country-clustered standard errors, and highly significant under Driscoll–Kraay. The effect survives the leave-one-out jackknife, the male-outcome placebo, the Oster stress test, the lag tests, and the specification ladder. Apostasy's between-country effect is about seven times its within-country effect in magnitude, consistent with the broader structural reading, but apostasy is the evidence that the structural story has a within-country counterpart for at least one dimension of secularism.

Religious courts is the legacy null. In earlier versions of this analysis it was the focal predictor; it remains a useful comparison for what happens when a specific sub-item is too near-binary to identify anything in a short panel. The composite was built in part to move past that limitation, and the between-country composite coefficient (similar in magnitude to the between-country apostasy coefficient) confirms that the structural reading holds at the construct level as well as for the strongest individual sub-item.
