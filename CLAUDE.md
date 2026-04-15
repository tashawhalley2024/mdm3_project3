# Project memory — MDM3 Treatment of Women

This file is read at the start of every session. Follow these rules when answering
questions about this repository.

## Golden rule

**Code is the source of truth. Markdown is not.**

The README, docs/*.md, data/*_README.md, and writing/*.tex files in this repo can
and do drift from what the scripts actually do. When the user asks what was done,
how something was computed, what a variable means, or what a model estimates, the
answer MUST be grounded in the Python (and the CSVs those scripts produce), not
in prose documentation. Treat markdown as a hint about where to look, never as
evidence of what the code does.

Never answer a "what did we do" question from memory, from the README, or from the
LaTeX write-up alone. Always open the relevant `.py` file(s) and verify.

## Workflow for any factual question about the project

1. Identify which script(s) would implement the thing being asked about.
   - Scoring / index construction → `data_reading.py`, `scoring.py`, `verify.py`
   - Regressions / econometrics → `analysis/run_analysis.py`
   - Figures and tables → `analysis/run_plots.py`
   - Alternative indices → `analysis/compare_indices.py`
   - Data build (GRI, V-Dem, GDP, composite outcome) → referenced as
     `build_secularism_composition.py` but NOT in this repo; the outputs live in
     `data/predictors.csv` and `data/outcome_*.csv`. Inspect those CSV headers
     with `head -1` when provenance matters.

2. Use `Grep` to locate every site where the concept appears in code, not just
   the first one. Variables are often reused across 10+ functions (e.g.
   `log_gdppc_norm`, `CONTROLS_GDP`, `GRI_PANEL_COLS`).

3. Read enough surrounding code to understand:
   - how the variable/column is constructed or loaded
   - which estimator is called, with which options (cov_type, cluster, FE flags)
   - what sample filter is applied (`dropna(subset=...)`, year restrictions)
   - whether the spec is labelled consistently with how it's described in prose

4. Cross-check against markdown only to flag discrepancies to the user, never to
   override the code.

5. When describing a model, quote the actual Python identifiers (function name,
   line numbers, estimator class, `cov_type`, controls list) so the user can
   audit.

## Known gotchas in this repo

- `log_gdppc_norm` is log(GDP per capita, constant 2015 USD) **robust min-max
  normalised to ~[0,1]**, not plain log GDP. It is pre-built in
  `data/predictors.csv`; `run_analysis.py` only merges it in. Coefficients on it
  are per unit of the normalised scale, not per log-point.
- `CONTROLS = [v2x_rule_norm, v2x_civlib_norm, v2x_egal_norm]` (V-Dem governance).
  `CONTROLS_GDP = CONTROLS + ["log_gdppc_norm"]`. Every "with GDP" spec uses
  `CONTROLS_GDP`; every "no GDP" spec uses `CONTROLS`.
- Sample is filtered per-spec with `dropna(subset=[OUTCOME] + pred_cols)`, so the
  `no_gdp` and `with_gdp` runs are NOT on identical samples — composition effects
  are not separated from the effect of adding the regressor.
- T2 TWFE uses `linearmodels.PanelOLS(..., entity_effects=True, time_effects=True)`
  with `cov_type="clustered", cluster_entity=True`.
- T1 uses `sm.OLS(...).fit(cov_type="HC3")` on 2014 and 2020 cross-sections only.
- T3 System-GMM fails the Roodman bounds check (rho=1.215 > pooled OLS upper
  bound); it is reported in `results/results.csv` but is excluded from
  substantive conclusions. Do not quote T3 coefficients as headline results.
- T4 Mundlak adds `_mean` country-mean regressors for ALL time-varying predictors
  including GDP, via `sub.groupby("iso3")[col].transform("mean")`. As of
  2026-04-15 (Item 2) T4 decomposes **10** regressors (6 GRI + 3 V-Dem +
  `log_gdppc_norm`) after `gri_gov_favour_norm` was added to `GRI_PANEL_COLS`;
  the prior count of 9 referenced in the Mundlak presentation slide is stale.
- **T5 Long-Difference robustness** (Item 3, 2026-04-15; trimmed 2026-04-15
  late-late evening after outside-judgement review).
  `analysis/run_analysis.py:tier5_long_difference` collapses the panel to one
  observation per country by endpoint subtraction and fits
  `sm.OLS(dY ~ 1 + dX + dZ).fit(cov_type="HC3")`. Four windows run:
  2013–2022 (main), 2014–2022 (alt endpoint), 2013–2017 and 2017–2022 (5-yr
  sub-windows). Each window × `{no_gdp, with_gdp}` × 7 focals, plus a
  `_grifull` companion spec for GRI sub-item focals. Three-tier validity:
  `valid=False` if n_changers <10, `valid=True` with `low_power` warning
  if 10–24, `valid=True` no flag if ≥25. Composite 2013→2022 with_gdp:
  β=+0.082 (p=0.28, N=163) — wrong-signed null, corroborates T2/T4 within
  rather than resolving it. Apostasy (9 changers) flagged invalid; courts
  (19) low_power. **The paper treats T5 as a robustness complement to T2/T4
  rather than a fifth tier**: tab:headline shows one "Long-difference
  (2013–2022)" row below T4, §5.8 is a two-paragraph robustness subsection,
  figure 13 lives in Appendix A (`sec:ld-details`), sub-window numbers stay
  in results.csv only. Abstract and §1 describe LD as a robustness
  complement, not a fifth tier.
- **Δ(log_gdppc_norm) in T5** is on the min-max-normalised [0,1] scale, not
  log-points. Coefficients on Δ(log_gdppc_norm) are marginal effects per unit
  of the normalised decade-change, not income elasticities.
- Outcome label depends on which file is being used: `wbl_treatment_index`
  (WBL-based, primary) vs the earlier composite in `data/outcome_composite.csv`.
  Check `OUTCOME` and `WOMEN_PATH` at the top of `run_analysis.py`.
- **`FOCAL_PRED` is `composite_secularism_norm`** (Item 2, 2026-04-15).
  This is an equal-weight z-score over 6 GRI + v2clrelig (sign-flipped) + 4 WVS
  inputs, built at load time inside `analysis/utils.py:build_secularism_composite`
  and attached to `df` inside `run_analysis.py:load_and_merge`. It is NOT stored
  on disk. `FOCAL_PRED_PCA = composite_secularism_pca_norm` is the PCA
  robustness variant (column-mean imputation degenerates PCA toward the
  fully-covered inputs; see caveat in `predictors_README.md` sub-group 4).
  `FOCAL_PRED_LEGACY = gri_religious_courts_norm` is preserved as a robustness
  focal; its outputs land in `results/*_religious_courts.csv`. `FOCAL_PRED_2 =
  gri_apostasy_norm` remains the strongest sub-item focal, also preserved.
- For the composite, **`n_changers` saturates at ≈ `n_clusters`** (continuous
  by construction) and loses diagnostic value; use `within_sd` instead.
  `analysis.log` additionally emits composite changer counts restricted to
  `wvs_interpolated == 0` — that is the real-movement count purged of WVS
  linear-interpolation arithmetic.
- The README's "Current results summary" table is a snapshot and can lag the
  current `results/results.csv`. If a user asks about a specific coefficient,
  read `results/results.csv`, not the README.

## Depth over speed — this is the most important rule

The user has explicitly said: **each question is important, token usage is not a
concern, and an in-depth, careful, correct, insightful answer is always
preferred over a quick win.** Treat every question as if it will be audited.

Concretely, for every non-trivial question:

- Do not stop at the first file that mentions the term. Grep across the whole
  repo, read every call site, and confirm the answer is consistent everywhere it
  appears. Variables like `log_gdppc_norm`, `CONTROLS_GDP`, `FOCAL_PRED`,
  `OUTCOME` show up in 10+ functions — check them all before claiming what the
  code does.
- Read the surrounding function, not just the matching line. An estimator call
  is meaningless without its `cov_type`, cluster argument, FE flags, sample
  filter, and the column list that was actually passed in.
- When the user asks about a number (coefficient, p-value, sample size), open
  `results/results.csv` (or whichever CSV the script writes) and read the
  number. Do not quote the README's summary table — it can lag.
- When the user asks about a methodological choice, give a balanced pros/cons
  review: name the specific threat to validity (omitted-variable bias,
  bad-control/mediator problem, Nickell bias, instrument proliferation, sample
  composition, functional form, interpretation of a rescaled variable, etc.),
  explain how it applies to THIS code, and say whether the current
  implementation handles it or leaves it open. Do not just summarise what the
  script does — critique it.
- Flag discrepancies between what the code does and what the markdown / LaTeX
  claims, and tell the user which is which. Silent agreement with the docs is a
  failure mode.
- Before sending the answer, do a self-check pass: "Is every number I quoted
  actually in a file I read this session? Is every Python identifier I cited
  real? Have I conflated two specs with similar names (e.g. `no_gdp` vs
  `gri_only`, `T2_with_gdp` vs `T4_mundlak_re` within-effect)? Is there a
  counter-argument I should mention?"
- If a question is ambiguous or has multiple defensible interpretations, say so
  and answer the most likely one plus the alternatives — don't pick one
  silently.
- Length is not a virtue in itself; precision and completeness are. Prefer a
  thorough, well-grounded answer that takes many tool calls to produce over a
  short answer that skips verification steps.

If in doubt: open another file. The user would rather wait for a correct,
insightful answer than get a fast wrong one.

## Running todo / think-about list

There is a file `TODO.md` at the repo root that serves as an ongoing list of
open questions, methodological concerns, and follow-ups. When the user asks
about "the todo list", "things to come back to", "open questions", or anything
similar, open `TODO.md` and surface its current contents. When the user flags
something new to think about later, append it to the Open items section of
`TODO.md` rather than only replying in chat. When an open item is resolved,
move it (with a short note on the outcome) to the Resolved / closed section —
do not delete it.

## Clarification — prefer multiple-choice

When clarification is needed, prefer asking as a **multiple-choice question**
with a small number of concrete, distinct options (typically 2–5) rather than an
open-ended "what do you mean?". If an AskUserQuestion-style tool is available,
use it; otherwise list labelled options (A / B / C …) inline and invite the user
to pick one, combine, or add their own.

Use this clarification mechanism fairly freely — whenever the question is
genuinely ambiguous, has multiple defensible interpretations, or a methodological
choice would materially change the answer (e.g. "do you want the `with_gdp` or
`no_gdp` spec?", "T2 TWFE or T4 Mundlak within-effect?", "WBL outcome or
composite outcome?"). It is better to ask than to silently pick a path and
produce a thorough answer to the wrong question.

Do NOT ask when the answer is obvious from context, when the user has already
specified, or when the choice is trivial. Never chain multiple clarifying rounds
if one well-framed multiple-choice question would cover the ambiguity.

## Answer style

- Cite line numbers and function names from the Python when explaining what was
  done.
- Separate "what the code does" from "what the markdown claims" if they diverge,
  and tell the user which is which.
- For methodological judgement questions ("is this defensible?"), give a balanced
  answer grounded in the actual implementation, not in what the docs aspire to.
- Do not invent diagnostics, coefficients, or sample sizes. If a number is not in
  the results CSVs or printed by the script, say so.
