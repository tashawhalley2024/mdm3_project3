# Review: Secularism Composite Rebuild

**Date:** 2026-04-16
**Verdict: YES — with downsides**
**Reviewer:** check skill (Cowork session)

---

## Step 1 — The change, precisely

Replace the current headline focal predictor `composite_secularism_norm` (an
equal-weight z-score over 11 inputs: 6 GRI sub-items + v2clrelig_norm
sign-flipped + 4 WVS items) with a new variable `secularism_clean_norm` (an
equal-weight z-score over 7 inputs: 3 "structural" GRI sub-items + 4 WVS items).

Concretely:

**Removed from composite inputs:**
- `gri_apostasy_norm` (treatment: punishes people for leaving religion)
- `gri_blasphemy_norm` (treatment: punishes people for blasphemy)
- `gri_gov_favour_norm` (borderline: government favouritism of religion)
- `v2clrelig_norm` (treatment/freedom: V-Dem religious freedom index)

**Retained in composite inputs:**
- `gri_state_religion_norm` (structural: is there a state religion?)
- `gri_religious_law_norm` (structural: is religious law in the legal system?)
- `gri_religious_courts_norm` (structural: does the state recognise religious courts?)
- `wvs_imprel_norm`, `wvs_godimp_norm`, `wvs_godbel_norm`, `wvs_confch_norm` (behavioural: how religious is the population?)

**Construction method unchanged:** z-score each input, average within dimension,
row-mean across dimensions (with NaN fallback), robust_minmax to [0,1],
sign-align against `gri_state_religion_norm`.

**Dimensions reduced:** from 3 (institutional, attitudinal, behavioural) to 2
(institutional, behavioural). The attitudinal dimension (`v2clrelig_norm`) is
dropped entirely because it is classified as a treatment/freedom variable.

The conceptual rationale: the paper asks "does secularism affect treatment of
women?" If the secularism measure itself contains treatment-of-people variables
(apostasy laws, blasphemy laws, religious freedom), then the regression partly
compares treatment-of-people with treatment-of-women — a circularity that
inflates cross-sectional coefficients and muddies interpretation.

The change would be implemented by modifying `analysis/utils.py`:
`COMPOSITE_INSTITUTIONAL_COLS` (line 49) from 6 items to 3, dropping
`gri_apostasy_norm`, `gri_blasphemy_norm`, `gri_gov_favour_norm`, and removing
`COMPOSITE_ATTITUDINAL_COLS` / `v2clrelig_norm_flipped` from
`_prepare_composite_inputs` (line 75) and `_build_equal_weight` (line 140).
Downstream, `analysis/config.py:FOCAL_PRED` (line 33) would stay pointing at the
same output column name (or be renamed to `secularism_clean_norm`).

The removed items would be preserved as individual sub-item focals in a
decomposition analysis (separate regressions, not in the composite).

---

## Step 2 — Scope: every file, function, and output touched

### Files that define/build the composite
| File | Lines | What |
|---|---|---|
| `analysis/utils.py` | L49-56 | `COMPOSITE_INSTITUTIONAL_COLS` (6 → 3) |
| `analysis/utils.py` | L57 | `COMPOSITE_ATTITUDINAL_COLS` (removed) |
| `analysis/utils.py` | L75-104 | `_prepare_composite_inputs` (11 cols → 7) |
| `analysis/utils.py` | L140-201 | `_build_equal_weight` (3 dims → 2) |
| `analysis/utils.py` | L204-287 | `_build_pca` (11 cols → 7) |
| `analysis/utils.py` | L290-368 | `build_secularism_composite` orchestrator |
| `analysis/config.py` | L33 | `FOCAL_PRED = "composite_secularism_norm"` |
| `analysis/config.py` | L35 | `FOCAL_PRED_PCA` (PCA variant, also affected) |

### Files that consume the composite
| File | Lines | What |
|---|---|---|
| `analysis/run_analysis.py` | L270-305 | `load_and_merge()` calls `build_secularism_composite` 4× |
| `analysis/run_analysis.py` | L3688-3966 | `composite_tier_specs()` runs T1/T2/T4 for composite |
| `analysis/run_analysis.py` | L3998-4006 | `main()` calls `composite_tier_specs` for 5 variants |
| `analysis/run_analysis.py` | L3991-3996 | `main()` T5 loop over `FOCAL_PREDS_T5` |
| `analysis/run_analysis.py` | L3425-3468 | `_apply_mt_corrections` — focal family includes composite |
| `analysis/run_plots.py` | L146-147 | `LABELS_SHORT` display name |
| `analysis/run_plots.py` | L175-191 | Fig 1 scatter: composite vs apostasy |
| `analysis/run_plots.py` | L761-762 | Spec-ladder figure uses composite |
| `analysis/run_plots.py` | L904-944 | Headline comparison figure |
| `analysis/run_plots.py` | L1130-1183 | World choropleth of FOCAL_PRED |
| `analysis/run_plots.py` | L1234-1266 | Within-vs-between decomposition figure |
| `analysis/run_plots.py` | L1370-1384 | Decade-change scatter |
| `tools/build_headline_table.py` | 2 refs | Post-processing for headline_table.csv |
| `verify.py` | 1 ref | Verification script |

### Output files that contain composite values
| File | Description |
|---|---|
| `results/results.csv` | 31 rows with `composite_secularism_norm` |
| `results/headline_table.csv` | 15 rows |
| `results/headline_table.md` | 2 refs |
| `results/rebuild_comparison.csv` | 5 rows (prototype run) |
| `results/spec_ladder.csv` | 1 row |
| `results/placebo.csv` | 5 rows |
| `results/loo_jackknife_summary.csv` | 1 row |
| `results/results_wbl_groups.csv` | 11 rows |

### Documentation
| File | Description |
|---|---|
| `writing/methodology_full.tex` | L61-73: describes the 3-dimension 11-input composite |
| `CLAUDE.md` | L96-110: documents FOCAL_PRED and composite construction |
| `TODO.md` | L57+: open item 2 on secularism predictor rebuild |
| `data/predictors_README.md` | Describes input columns |
| `figures/figure_guide.md` | 2 refs |
| `figures/README.md` | 1 ref |

**Total: 22 files, 108 occurrences** of the string `composite_secularism_norm`.

---

## Step 3 — Downstream blast radius

### CSVs overwritten
All output CSVs listed above would be regenerated by a full `run_analysis.py`
run. They are committed files. Every coefficient, p-value, sample size, and
diagnostic for the composite focal would change. The old composite's numbers
would only be preserved if the code is written to keep both composites (old as
robustness, new as headline).

### Figures that would move
Every figure in `run_plots.py` that uses `FOCAL_PRED` (scatter plots, spec
ladder, choropleth, within-vs-between decomposition, decade-change scatter)
would display different values. At minimum: the cross-section scatter slopes
would be shallower (β halves from ~−0.19 to ~−0.10), the choropleth colour
distribution would shift (different normalisation), and the within-vs-between
bar chart ratios would change.

### Table cells in the write-up
`writing/methodology_full.tex` L61-73 describes the composite as "equal-weighted
z-score composite built across three dimensions" with 11 inputs. This entire
subsection would need rewriting: now 2 dimensions, 7 inputs, and the removed
items need to be framed as "excluded from composite, analysed separately."

The headline table (tab:headline, L195) quotes composite + PCA + apostasy +
courts coefficients. The composite rows would carry different numbers; the
PCA variant would also change (built on 7 inputs not 11).

### Derived statistics
- Bonferroni/BH correction in `_apply_mt_corrections` (L3425): the focal family
  still includes `composite_secularism_norm` — if renamed to `secularism_clean_norm`,
  the mask at L3449 would silently miss it unless updated.
- Oster delta, event study, LOO jackknife, wild bootstrap results for the
  composite focal would all change.
- PCA explained variance ratio would change (fewer inputs → likely higher
  proportion explained by PC1, but different loadings).

---

## Step 4 — Sample and identification implications

### Sample size: UNCHANGED for the composite itself
The composite uses `df.mean(axis=1, skipna=True)` with dimension fallback
(`_build_equal_weight` L172). The institutional dimension (GRI items) has ~100%
coverage; the behavioural dimension (WVS) has ~47% coverage. Dropping 3 GRI
items from the institutional dimension and the attitudinal dimension does NOT
change which rows have at least one dimension observed — every row that had the
old composite will have the new one. So the `dropna(subset=[focal_col])` filter
in all tier functions produces the same sample size.

**Confirmed by rebuild results:** T1 2014 N=166 (both old and new), T2 N=1648
(both old and new).

### Identification: same estimators, same structure
- T1: still OLS with HC3, same cross-sections (2014, 2020).
- T2: still PanelOLS with entity + year FE, clustered by entity.
- T4: still Mundlak RE decomposition.
- T5: still long-difference with HC3.

No change to FE structure, clustering, or SE estimation. The coefficient now
identifies a different quantity (the effect of a 1-unit change in the new
7-input composite rather than the old 11-input composite), but the estimation
strategy is unchanged.

### What changes in the coefficient's interpretation
The old composite β captured: "the combined effect of institutional
entanglement + treatment policies + religious freedom + population religiosity."
The new composite β captures: "the combined effect of structural state-religion
arrangement + population religiosity." These are different quantities. The
coefficient halving (−0.19 → −0.10 in T1) is expected because treatment
variables that mechanically correlate with women's treatment have been removed.

This is the intended change — it eliminates the circularity concern. But it
means old and new composite coefficients are NOT directly comparable in
magnitude; comparing them is comparing different constructs.

---

## Step 5 — Threats to validity

### Circularity / conceptual overlap (IMPROVED)
The old composite included apostasy laws, blasphemy laws, government
favouritism, and V-Dem religious freedom — all of which measure "how the state
treats people on religious grounds." The outcome (`wbl_treatment_index`) measures
"how the state treats women." The overlap is: states that restrict people's
religious freedoms tend to also restrict women's freedoms, partly through the
same legal/institutional machinery. Including both in the regression inflates
the cross-sectional coefficient beyond what "secularism as a state of being"
explains. The new composite eliminates this overlap. **This is the single
strongest argument for the change.**

### Omitted variable bias (WORSE, but by design)
Removing 4 variables from the composite means the new composite captures less
variance in "religiosity." Specifically, v2clrelig_norm (V-Dem religious
freedom) was the highest-coverage, most continuous, and most time-varying input
in the old composite (143 changers, within_sd = 0.051). Dropping it reduces the
composite's information content. Apostasy (12 changers) and blasphemy (69
changers) are less consequential for variation, but government favouritism (63
changers) had meaningful within-country movement.

However, the user's position is well-reasoned: including these as controls
rather than composite inputs is methodologically cleaner. They can appear in the
sub-item decomposition panel instead.

### Loss of the attitudinal dimension (TRADE-OFF)
v2clrelig_norm was the ONLY input in the attitudinal dimension. It was also the
only continuous, high-coverage, expert-coded input (vs the GRI categorical items
and the WVS survey items). Dropping it removes the only "state of affairs as
judged by experts" signal. The remaining composite is: coarse institutional
facts (GRI, mostly {0,1} or {0,0.5,1}) + survey-based population beliefs (WVS,
~47% raw coverage, heavily interpolated).

This is a real cost. The composite is now more dependent on WVS interpolation
artifacts for its behavioural dimension, and its institutional dimension is
very coarse.

### Reduced within-country variation (NEUTRAL to SLIGHTLY WORSE)
New composite within_sd = 0.062; old = 0.038. Wait — the new composite actually
has HIGHER within_sd. This is because the old composite averaged across 3
dimensions including the stable attitudinal one, diluting within-SD. Dropping
the attitudinal dimension (which barely varied) slightly increases within_SD.

But the institutional dimension alone (within_sd = 0.081) and the behavioural
alone (0.017) tell the real story: the GRI structural items change more than
WVS items within countries. The composite's within-SD of 0.062 is driven by the
institutional dimension, not behavioural.

For T2/T4 identification, this is neutral — the within-country null was real
under both composites.

### Multiple testing / researcher degrees of freedom (SLIGHTLY WORSE)
Adding a new composite alongside the old one, plus inst-only and beh-only
variants, expands the number of focal predictors. The current pipeline already
runs 5 composite variants (headline, PCA, real, instonly, covwt) + apostasy +
legacy courts = 7 focals. Replacing the headline composite with a differently-
constructed one adds another researcher degree of freedom. The Bonferroni/BH
corrections in `_apply_mt_corrections` would need updating.

Mitigant: the plan frames the old composite as robustness, not co-headline.
Only one composite would be the "headline." But the paper's history of focal
predictor changes (courts → old composite → new composite) could invite
scepticism about specification search.

### Bad-control / mediator problem (UNCHANGED)
The controls (`v2x_rule_norm`, `v2x_civlib_norm`, `v2x_egal_norm`,
`log_gdppc_norm`) are unchanged. The concerns in TODO.md Item 1 (GDP as
mediator, V-Dem governance as post-treatment) apply equally to the new
composite.

---

## Step 5b — Directional judgement

### The user's theory of the change
"The old composite mixes 'how religious a place is' with 'how people are treated
because of religion.' I want to measure only the first thing and compare it to
treatment of women. Comparing treatment to treatment defeats the purpose."

### Does the theory hold against the code?
**Yes.** Looking at what `COMPOSITE_INSTITUTIONAL_COLS` (utils.py L49-56) actually
contains: `gri_apostasy_norm` is literally "does the country criminalise
apostasy" — that is a treatment/policy variable, not a structural fact about how
religious the state is. Same for `gri_blasphemy_norm`. `v2clrelig_norm` is
explicitly coded by V-Dem as "religious freedom" — a freedom/treatment measure.
`gri_gov_favour_norm` is borderline but leans toward treatment (does the
government favour one religion over others in policy).

The three items retained in the institutional dimension — state religion,
religious law, religious courts — are genuine structural facts about the state's
constitutional arrangement. A country can have a state religion without
criminalising apostasy or blasphemy (e.g., England, Denmark, Norway). These are
plausibly "state of being" rather than "treatment."

The 4 WVS items are clearly "state of being" — they measure population beliefs,
not policies.

### Cross-checking the rebuild results
From `results/rebuild_comparison.csv` (verified against numbers printed by the
analysis script):

- **T1 2014 with_gdp: β = −0.100, p = 0.005.** Still significant, negative,
  interpretable. The cross-section story survives the cleanup.
- **T2 with_gdp: β = +0.024, p = 0.091.** Wrong-signed, marginally significant.
  Within-country null is preserved.
- **T4 Mundlak between: β = −0.119, p = 0.004.** Strongly significant.
  Between-country effect is real.
- **T4 Mundlak within: β = +0.024, p = 0.075.** Wrong-signed. Within null
  preserved.
- **T5 LD 2013-2022: β = +0.053, p = 0.197.** Null. Same story.

The old composite (verified against `results/results.csv`):
- T1 with_gdp 2014: β = −0.194, p = 0.000025
- T2 with_gdp: β = +0.061, p = 0.071
- T4 mundlak_re: β = +0.061, p = 0.058 (this is the within-effect)

The paper's headline story — "secularism matters cross-sectionally but not
within-country" — is **preserved** under the new composite. The cross-section
coefficient halves (from −0.19 to −0.10) but remains significant at the 1%
level. The within-country null remains null.

### Is this forward, backward, or sideways?

**Forward.** The change:
1. Eliminates a genuine conceptual circularity (the strongest single argument).
2. Preserves the paper's headline finding (cross-section significant, within null).
3. Produces a cleaner interpretive story (the between-effect of "how religious a
   place IS" on women's treatment, not the between-effect of "how people are
   treated" on women's treatment).
4. Enables a meaningful sub-item decomposition where treatment variables
   (apostasy, blasphemy, v2clrelig) appear as separate focals rather than being
   baked into the composite.
5. The coefficient halving is a feature — the old number was inflated by circular
   measurement.

The main risk is reviewer scepticism about the specification search (courts →
composite → new composite), but this is addressable with transparent reporting.

---

## Step 6 — Docs-vs-code drift after the change

The following prose would be wrong after implementation:

1. **`writing/methodology_full.tex` L61-73:** "equal-weighted z-score composite
   built across three dimensions" → now 2 dimensions; "11 inputs" → now 7;
   the dimension weighting table (L73) would need a new row.
2. **`writing/methodology_full.tex` L195:** Headline table caption/values would
   have different numbers for composite rows.
3. **`CLAUDE.md` L96-110:** "equal-weight z-score over 6 GRI + v2clrelig
   (sign-flipped) + 4 WVS inputs" → now 3 GRI + 4 WVS. FOCAL_PRED description
   would need updating. Known gotcha about "10 regressors" in T4 Mundlak
   (L67-71) would change (fewer Mundlak _mean terms if GRI_PANEL_COLS shrinks).
4. **`CLAUDE.md` L106-110:** Composite changer count discussion; the within_sd
   and changer-count characteristics change.
5. **`TODO.md` Item 2:** Open item about secularism predictors being "miscast" —
   would become resolved/partially-resolved.
6. **`data/predictors_README.md`:** Would need a note about which items are
   structural vs treatment.
7. **`figures/figure_guide.md` and `figures/README.md`:** Descriptions of
   composite-based figures would need updating.

This is a moderate documentation cost — 7+ files need prose updates. But none of
it is architecturally difficult.

---

## Step 7 — Reversibility and blast containment

- **Code change:** Modifying `COMPOSITE_INSTITUTIONAL_COLS` in `utils.py` is a
  ~3-line edit. Adding back the removed items reverses it cleanly. **High
  reversibility.**
- **Config change:** `FOCAL_PRED` in `config.py` is a single-line string.
  **Trivially reversible.**
- **Output CSVs:** `results/results.csv` and all downstream CSVs would be
  overwritten by a full `run_analysis.py` run. These are committed. A `git
  checkout` recovers the old versions. **Reversible but needs a clean commit
  before the change.**
- **Figures:** All regenerated from `run_plots.py`. Same as CSVs.
  **Reversible.**
- **Prose/LaTeX:** Manual edits to multiple files. Reversible via git but higher
  effort to undo than code changes. **Moderate reversibility.**
- **No data rebuilding:** `data/predictors.csv` is NOT changed. The composite is
  built at runtime by `build_secularism_composite`. No input CSVs are touched.
  **Good containment.**

**Reversibility score: 4/5.** One point off because the documentation churn
across 7+ files makes a clean revert slightly messy. The code/data side is
trivially reversible.

---

## Step 8 — Verdict: YES — with downsides

The change is **forward** on the logic of the project. The circularity concern
is real and the fix is sound. The headline finding survives. The conceptual
framing becomes cleaner. The sub-item decomposition is a net addition.

### Downsides (all named, small, reversible):

1. **Loss of v2clrelig_norm from the composite.** This was the only
   expert-coded, continuous, high-coverage input. The remaining composite is
   coarser (3 categorical GRI items + 4 interpolated WVS items). The composite's
   ability to discriminate between countries in the middle of the distribution
   is reduced.
   - *Mitigant:* v2clrelig appears as a standalone sub-item focal. Its
     information is not lost from the paper, just from the composite.

2. **Coefficient halving.** The headline cross-section effect drops from β≈−0.19
   to β≈−0.10. This is conceptually correct (the inflation was from circular
   measurement), but a reviewer who only sees the final numbers might find
   β=−0.10 less impressive.
   - *Mitigant:* p=0.005 is still strong. The effect size is one standard
     deviation of the new composite → 10 percentage-point change in the women's
     treatment index, which is substantively meaningful.

3. **Specification search optics.** The paper has changed its focal predictor
   twice (courts → 11-input composite → 7-input composite). A sceptical reviewer
   could read this as fishing for the "right" composite.
   - *Mitigant:* The conceptual argument is principled and pre-registered in the
     plan. Reporting the old composite as robustness shows transparency. The
     direction of the change (weaker coefficient, not stronger) argues against
     specification search — you'd search for a stronger result, not a weaker one.

4. **Institutional dimension becomes very coarse.** Three items, two of which are
   binary ({0,1}) and one ternary ({0, 0.5, 1}). The institutional z-score has
   very few distinct values. Combined with WVS dimension-fallback, some
   countries' composite scores are determined almost entirely by which WVS
   interpolation value they got.
   - *Mitigant:* The inst-only and beh-only variants explicitly test whether
     this matters. The rebuild shows the behavioural dimension drives the
     cross-section (β=−0.17, p<0.001) while institutional alone is non-significant
     (β=−0.05, p=0.20). This is an honest finding about which dimension matters.

5. **Bonferroni/BH correction needs updating.** If the composite is renamed, the
   focal family mask in `_apply_mt_corrections` (L3442-3449) will silently miss
   it unless updated.
   - *Mitigant:* Trivial code fix.

All five downsides are: (i) named specifically, (ii) small in magnitude relative
to the conceptual gain, (iii) reversible. Verdict is **YES**.

---

## Step 9 — Self-check pass

- [x] **Every number I quoted is in a file I opened this session.**
  - β=−0.100, p=0.005 (T1 2014 new composite): from rebuild script output,
    verified against `results/rebuild_comparison.csv`.
  - β=−0.194, p=0.000025 (T1 2014 old composite): from `results/results.csv`
    read via bash.
  - β=+0.061, p=0.071 (T2 with_gdp old composite): from `results/results.csv`.
  - β=+0.024, p=0.091 (T2 with_gdp new composite): from rebuild script output.
  - β=−0.119, p=0.004 (T4 Mundlak between new): from rebuild script output.
  - within_sd values: from rebuild script diagnostics output.

- [x] **Every Python identifier I cited is real.**
  - `COMPOSITE_INSTITUTIONAL_COLS` at utils.py L49: confirmed by Read.
  - `COMPOSITE_ATTITUDINAL_COLS` at utils.py L57: confirmed.
  - `_build_equal_weight` at utils.py L140: confirmed.
  - `_prepare_composite_inputs` at utils.py L75: confirmed.
  - `FOCAL_PRED` at config.py L33: confirmed.
  - `_apply_mt_corrections` at run_analysis.py L3425: confirmed.
  - `composite_tier_specs` at run_analysis.py L3688: confirmed.

- [x] **Have I conflated two similarly-named specs?**
  - T2_with_gdp (from `tier2_panel_fe`, GRI decomposition) vs T2_with_gdp (from
    `composite_tier_specs`, composite standalone): these share the same tier tag
    but have different `predictor` column values. I have not conflated them.
  - T4_mundlak_re: this is the within-effect from the Mundlak model. The rebuild
    script separately reports within and between. I cited the between-effect
    (β=−0.119) correctly as T4 Mundlak between, not the within.

- [x] **Counter-argument to my verdict:**
  The strongest counter-argument is: "By removing v2clrelig, you lose the only
  continuous, expert-coded input, making the composite depend heavily on coarse
  GRI binaries and interpolated WVS survey data. The resulting index may be
  *noisier* and *less valid* than the old one, even if conceptually cleaner."
  **My verdict survives this** because: (a) the circularity concern is a
  fundamental validity issue, not a noise issue — a biased but precise estimator
  is worse than an unbiased but noisier one; (b) the sub-item panel preserves
  v2clrelig's information in the paper; (c) the cross-section result still
  reaches p=0.005, so the noise has not killed the signal.

- [x] **Does my verdict match tiebreaker rules?**
  I am not torn. The change is clearly forward. YES is appropriate.

---

## Step 10 — Follow-ups for TODO.md

Regardless of implementation, these items should be tracked:

1. **Update `COMPOSITE_INSTITUTIONAL_COLS` in `analysis/utils.py`** to 3 items;
   remove `COMPOSITE_ATTITUDINAL_COLS`; update `_prepare_composite_inputs` and
   `_build_equal_weight` to 2 dimensions.
2. **Update `_apply_mt_corrections`** focal family set (L3442-3449) if composite
   column is renamed.
3. **Update `CLAUDE.md`** — FOCAL_PRED description (L96-110), Mundlak _mean
   count (L67-71), changer diagnostics (L106-110).
4. **Update `writing/methodology_full.tex`** — §5 composite description (L61-73),
   headline table values (L195+), dimension weighting table.
5. **Update `TODO.md`** — mark Item 2 as resolved with note.
6. **Re-run full `run_analysis.py`** and commit new `results/results.csv`.
7. **Re-run `run_plots.py`** and commit updated figures.
8. **Consider renaming** the output column from `composite_secularism_norm` to
   `secularism_clean_norm` to avoid confusion. If renamed, update all 22 files
   / 108 occurrences.
9. **Report old composite in appendix/robustness** — keep both in the paper for
   transparency.
10. **Address the WVS interpolation dependence** — with v2clrelig gone, the
    behavioural dimension (WVS) is the only non-binary high-variation input.
    The `_real` variant (masking interpolated WVS) becomes even more important
    as a robustness check.

---

## Completeness ledger

### Files opened (with Read tool)
1. `CLAUDE.md` (full read)
2. `TODO.md` (first 100 lines)
3. `analysis/run_analysis.py` L1-120, L120-269, L269-468, L3400-3600, L3688-3768, L3968-4155
4. `analysis/config.py` (full read)
5. `analysis/utils.py` (full read)
6. `writing/PLAN_secularism_rebuild.md` (first 80 lines)
7. `.claude/skills/check/SKILL.md` (full read)

### Greps run
1. `FOCAL_PRED|composite_secularism` in `run_analysis.py` → 60+ matches
2. `composite_secularism|secularism_clean` in `run_plots.py` → 30 matches
3. `composite.secularism|secularism.composite` in `writing/` → 6 files
4. `secularism_clean` in project root → 3 files
5. `composite_secularism_norm` count across project → 108 occurrences in 22 files
6. `def composite_tier_specs` in `run_analysis.py` → L3688
7. `def main|def tier4|def tier5` in `run_analysis.py` → L593, L843, L3968
8. `composite|secularism.*index` in `methodology_full.tex` → 30+ matches

### CSV columns/rows inspected
1. `results/results.csv`: all rows where `predictor == composite_secularism_norm`
   (31 rows). Verified T1, T2, T4, T5 coefficients.
2. `results/rebuild_comparison.csv`: all 60 rows. Verified T1, T2, T4 for new
   and old composites. Cross-checked old composite T1 against results.csv
   (exact match: β=−0.193882).

### Identifiers confirmed to exist
- `COMPOSITE_INSTITUTIONAL_COLS` (utils.py L49)
- `COMPOSITE_ATTITUDINAL_COLS` (utils.py L57)
- `COMPOSITE_BEHAVIOURAL_COLS` (utils.py L58)
- `_prepare_composite_inputs` (utils.py L75)
- `_build_equal_weight` (utils.py L140)
- `_build_pca` (utils.py L204)
- `build_secularism_composite` (utils.py L290)
- `FOCAL_PRED` (config.py L33)
- `FOCAL_PRED_PCA` (config.py L35)
- `FOCAL_PRED_LEGACY` (config.py L36)
- `FOCAL_PREDS_T5` (config.py L40)
- `composite_tier_specs` (run_analysis.py L3688)
- `_apply_mt_corrections` (run_analysis.py L3425)
- `GRI_PANEL_COLS` (run_analysis.py L83)
- `CONTROLS_GDP` (run_analysis.py L94)
