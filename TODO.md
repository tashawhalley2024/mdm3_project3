# To think about / come back to / to do

Running list of open questions, methodological concerns, and follow-ups for the
MDM3 Treatment of Women project. When the user asks about "the todo list",
"things to come back to", "open questions", or similar, surface this file.

Add new items to the bottom. Mark resolved items with `~~strikethrough~~` and a
short note rather than deleting them, so the audit trail is preserved.

---

## Open items

<!-- Add items here as they come up. Format suggestion:
- [ ] Short title — context / why it matters / where to look.
-->

- [ ] **Discuss with Jyo — write-up on the controls (esp. GDP).** Check that her
  write-up for the controls section does not just describe *what* was controlled
  for (V-Dem rule of law, civil liberties, egalitarianism, and `log_gdppc_norm`)
  but also properly engages with *why this is methodologically contentious*.
  Specifically, make sure she covers:
    - The **bad-control / post-treatment concern** for GDP — GDP per capita is
      plausibly a mediator of secularism's effect on women's welfare (secularism
      → female labour-force participation / property rights / education → GDP),
      so conditioning on GDP partials out part of the causal channel of
      interest. The "with GDP" coefficient is therefore a controlled direct
      effect, not a total effect. This is a live debate in the applied gender /
      institutions literature and should be acknowledged explicitly, not
      glossed over.
    - The **confounder-vs-mediator trade-off** — GDP is simultaneously a major
      omitted-variable-bias risk (richer countries differ on many unobservables)
      AND a mediator, so neither "include" nor "exclude" is obviously correct.
      This is why the code reports both `no_gdp` and `with_gdp` specs, and the
      write-up should frame the pair as bracketing the true effect rather than
      treating `with_gdp` as the single preferred spec.
    - The **interpretation of `log_gdppc_norm`** — it is log GDP per capita
      (constant 2015 USD) robust-min-max normalised to ~[0,1], not plain log
      GDP. Coefficients are "per unit of normalised scale", not per log-point,
      so the usual "a 1 log-unit rise in GDP per capita raises the index by X"
      reading does not apply. Make sure the write-up either explains the
      rescaling or converts back to log-points for interpretability.
    - **Sample composition** — `dropna(subset=[OUTCOME] + pred_cols)` means the
      `no_gdp` and `with_gdp` regressions are estimated on *different* samples,
      so part of the difference between them is compositional, not the pure
      effect of adding the regressor. The write-up should note this or report a
      same-sample comparison.
    - **Functional form** — GDP enters only linearly in log; no quadratic, no
      interaction with region / legal origin / religion. Worth flagging as a
      limitation or addressing with a robustness check.
    - **V-Dem governance controls** — similar bad-control concern (rule of law,
      civil liberties, egalitarianism may themselves be outcomes of secularism),
      so the same discussion applies to `CONTROLS` as well as to GDP.
  Outcome of the conversation: note here whether her draft already addresses
  each bullet, and what (if anything) needs to be added.

- [x] ~~**Secularism predictors are miscast — probably need to replace the data
  source, not just re-spec the model.**~~ **Resolved 2026-04-16** (Item 2
  redux). The composite was rebuilt in `analysis/utils.py` from 11 inputs
  across 3 dimensions to 7 inputs across 2 dimensions (3 structural GRI +
  4 WVS). Four items (`gri_apostasy_norm`, `gri_blasphemy_norm`,
  `gri_gov_favour_norm`, `v2clrelig_norm`) were removed from the composite
  on circularity grounds and now appear as standalone sub-item focals.
  Cross-section result survives: T1 2014 with_gdp β=−0.100 (p=0.005,
  N=166), halved from the prior β=−0.194 as expected. Within-country null
  is preserved. Full audit trail at
  `reviews/2026-04-16_secularism-composite-rebuild.md`. The deeper
  data-source upgrades below (RAS GIR, WRP composition, broader WVS, extra
  V-Dem items) remain possible future work but are out of scope for this
  rebuild. Original audit (2026-04-14) preserved below for reference.

  Audit on 2026-04-14 of
  `data/predictors.csv` (the only secularism file `analysis/run_analysis.py`
  actually reads, via `COMP_PATH` at line 47) revealed several serious problems
  with how "secularism" is operationalised. This is more structural than a
  single-variable fix, so treat it as a data-layer rebuild rather than an
  analysis tweak.

  **What the code actually uses.** `run_analysis.py` defines
  `GRI_PANEL_COLS = [gri_state_religion_norm, gri_religious_law_norm,
  gri_blasphemy_norm, gri_apostasy_norm, gri_religious_courts_norm]` (lines
  63–66) plus `v2clrelig_norm` and the WVS intensity set
  (`wvs_imprel_norm`, `wvs_godimp_norm`, `wvs_godbel_norm`, `wvs_confch_norm`).
  `analysis/config.py` sets `FOCAL_PRED = "gri_religious_courts_norm"` and
  `FOCAL_PRED_2 = "gri_apostasy_norm"` — the two focal predictors of the whole
  analysis are both near-binary.

  **Problem 1 — near-zero within-country variation on the focal predictors.**
  Distinct non-null values per country over 2007–2022 (3,164 rows, 198
  countries, verified by direct read of `data/predictors.csv`):
  `gri_apostasy_norm` changes in only **14 of 198** countries;
  `gri_state_religion_norm` in 32; `gri_religious_courts_norm` (the focal
  predictor!) in 51; `gri_blasphemy_norm` in 81; `gri_religious_law_norm` in
  159. Every two-way FE spec (`T2_*` in `run_analysis.py`) is therefore
  estimated off the movement of a tiny handful of countries. That is why
  `config.py` already labels courts as "the null predictor" in the palette —
  the data can't identify an effect because the regressor barely moves within
  country.

  **Problem 2 — the GRI columns are categorical dressed as continuous.**
  `gri_state_religion_norm` takes only {0, 0.5, 1};
  `gri_religious_courts_norm`, `gri_blasphemy_norm`, `gri_apostasy_norm` are
  all {0, 1}. Robust-min-max on an already-binary item is a cosmetic relabel,
  yet coefficients are read as if the variable were a continuous secularism
  scale. The `_norm` suffix is misleading for these columns.

  **Problem 3 — these are sub-questions, not a secularism construct.** The
  GRI columns pull individual sub-items from the Pew GRI questionnaire (Q1,
  Q2, Q3, Q15, GRX22, GRX22 per `predictors_README.md`). Each captures a
  narrow legalistic aspect of state–religion entanglement (is there an
  apostasy law on the books?). They say nothing about enforcement, social
  dominance of religion, religious schooling, religious party influence, or
  de facto norms — all of which plausibly bear more directly on women's
  treatment than whether a blasphemy statute exists in law.

  **Problem 4 — composition is collected but not used.**
  `data/religion_composition_normalised.csv` contains `pct_unaffiliated_norm`
  and `pct_other_norm` (Pew Global Religious Futures / WRP, observed only in
  2010 and 2020). These columns are **not** merged into `predictors.csv` and
  **not** used by `run_analysis.py`. The composition dimension of secularism
  is therefore absent from the actual regressions despite being collected.

  **Problem 5 — WVS intensity is patchy and partly synthetic.** Coverage of
  the four `wvs_*_norm` columns is ~44% of country-years; gaps between WVS
  waves are filled by within-country linear interpolation (+ ±2yr edge fill),
  flagged in `wvs_interpolated`. Countries like China, DPRK and many
  Sub-Saharan African states have 0 or 1 wave. In a panel FE, most of the
  within-country "variation" on WVS items is interpolator arithmetic, not
  real attitudinal change.

  **Problem 6 — no composite secularism index exists.** The code enters the
  11 religion/secularism columns as parallel univariate predictors rather
  than as a single latent construct. That is defensible as a multi-dimensional
  mapping, but it means the paper cannot cleanly say "secularism raises X";
  it can only say "a particular sub-item of the Pew questionnaire correlates
  with X." The write-up should either (a) build an explicit composite
  (PCA / IRT / equal-weight average across dimensions) or (b) reframe the
  claim as dimension-specific.

  **Problem 7 — `v2clrelig_norm` has opposite orientation.** Per the README
  (line 16 and the Sub-group 3a note), `v2clrelig_norm` is higher = more
  religious freedom (more secular tolerance), whereas every other column is
  higher = more religion / less secular. This is easy to mis-sign when
  combining into an index and should be checked wherever `v2clrelig_norm`
  appears alongside GRI or WVS columns.

  **Problem 8 — doc/code drift around outcome path.**
  `data/predictors_README.md` line 10 and its join example point to
  `data/women_secularism/women_secularism_normalised.csv`, but
  `run_analysis.py` line 49 actually reads `data/outcome_wbl.csv`. Not a
  data-quality issue per se, but it means anyone following the README to
  reproduce will fail. Fix as part of the data-layer rebuild.

  **What to do — options, roughly in order of ambition.**

    - **(A) Replace the state-institution layer with a continuous index.**
      The standard upgrade is Jonathan Fox's **Religion and State (RAS)**
      dataset — RAS-3 (1990–2014) and RAS-4 (extending further). It provides
      a continuous 0–100 **Government Involvement in Religion (GIR)** index
      plus sub-indices (Official GIR, Religious Support, Religious
      Discrimination against minorities, Religious Regulation of the
      majority, Societal-RAS). Annual, continuous, designed exactly for this
      kind of panel work. Replacing the binary GRI sub-items with RAS GIR
      would be the single biggest improvement, because it restores
      within-country variation to the FE specs.

    - **(B) Use the composite Pew GRI score (0–10) and SHI (0–10) rather
      than individual sub-items.** Lower-effort than RAS, keeps the same
      source, but gives a continuous index with real variation. Pew publishes
      the composite scores directly; the current file only has the
      sub-questions.

    - **(C) Add composition properly.** Merge `pct_unaffiliated_norm`,
      `pct_other_norm`, and ideally per-religion shares from the **World
      Religion Project (WRP)** national dataset (annual, 1945–2015, Maoz &
      Henderson) into `predictors.csv`. WRP would fix the two-snapshot
      (2010/2020) limitation and make composition usable in the panel.

    - **(D) Broaden the behavioural religiosity layer.** Add WVS/EVS
      *attendance* and *prayer-frequency* items in addition to
      importance-of-religion. Consider **Barro & McCleary's religion
      dataset** for cross-country religiosity with better historical depth.
      Accept that coverage will remain survey-limited and document it.

    - **(E) Add further V-Dem items beyond `v2clrelig`.** Candidates:
      `v2csrlgcon` (religious organisations' role in civil society),
      `v2mecenefm` (media censorship on religion), and any religion-related
      items in V-Dem's newer modules. V-Dem is already in the pipeline so
      this is low-cost.

    - **(F) Build an explicit composite secularism index.** After assembling
      the richer raw columns, construct one via PCA (or equal-weighted
      z-score average across the three dimensions: institutional, societal,
      behavioural). Report both the composite and the dimension-specific
      results so readers see where the action is.

  **Recommended minimum viable fix.** RAS GIR (institutional, continuous) +
  WRP `pct_unaffiliated` (composition, annual) + retain WVS
  importance-of-religion where available (behavioural). Three qualitatively
  different facets, each with genuine within-country variation, orthogonal
  enough that a composite is meaningful. Then re-run Tier 2 with the RAS GIR
  composite as the focal predictor and report the old GRI sub-item results
  as a robustness appendix rather than the headline.

  **Caveat to flag in the write-up regardless of which fix is taken.** The
  current headline result rests on near-binary regressors with ~14–51
  changer countries; any future spec must report the changer-country count
  alongside N so readers can judge the real identifying sample.

- [ ] **Add / improve a README for the figures folder.** User noted during
  2026-04-14 Stage E review (Claude session) that they want a dedicated README
  for `figures/`. A `figures/README.md` already exists as a minimal figure
  index; user's intent is likely a more substantive overview — possibly
  merging in content from `figure_guide.md` (currently staying local) or
  rewriting so a teammate without prior context can navigate the figure set.
  Clarify scope with user next session.

- [ ] **Low-priority GitHub cleanup candidates (none urgent).**
  Identified 2026-04-15 during a full-sweep audit. None break anything; all
  are cosmetic / organisational. Decide on each if/when time allows.
    - `data/lifeexp/2022/lifeexpfem.zip` and `lifeexptotal.zip` — raw WDI
      downloads (17 KB total) that sit next to their extracted working
      folders. Preserve download provenance. Delete only if the audit trail
      feels redundant.
    - 44 `Metadata.csv` files across `data/adolefert/`, `data/lifeexp/`,
      `data/maternalmort/`, `data/parliament/` year subfolders — auto-generated
      WDI boilerplate (CC BY-4.0 licence blurbs, indicator definitions).
      `data_reading.py` does not read them. Small, harmless noise.
    - Deprecated analysis path: `analysis/compare_indices.py` plus its
      outputs `results/results_composite.csv`, `results/index_comparison.csv`,
      `results/index_comparison.md`. Project memory flags compare_indices.py
      as "consolidated into run_plots.py" but `verify.py` (lines 41, 48,
      50–51, 115, 127, 152) still checks for all of these. Coordinated
      deletion would require editing verify.py to drop the obsolete checks.
      Keeping everything is the zero-risk option.
    - Teammate root-level files `Controls_raw_dataset.csv` and
      `PanelModel_controls_rawdata.csv` (both by lp21110, neither referenced
      by any code, different column widths — PanelModel is a superset). Not
      my stuff to delete; ask lp21110/Jyo if they're still planned for use.
    - `results/results_wbl.csv` — legacy file, but actively used by
      `run_plots.py` line 116 for `10_alt_outcomes.png`. **Do not delete.**
      Flagged only for completeness of the audit.

- [ ] **Add phone push notification when Claude Code finishes a turn
  (Telegram bot route).** Queued 2026-04-15. The local sound hook is
  already live in `~/.claude/settings.json` (`Stop` hook -> PowerShell
  `Media.SoundPlayer` on `C:\Windows\Media\Windows Notify Calendar.wav`).
  Phone side deferred. When resuming: create a Telegram bot via
  `@BotFather`, grab the bot token + chat id (send `/start` to the bot,
  then `curl https://api.telegram.org/bot<TOKEN>/getUpdates` to read the
  chat id), and extend the existing Stop hook command with
  `; curl -s -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" -d "chat_id=<CHATID>&text=Claude finished" >/dev/null 2>&1 || true`.
  Caveat to decide on at that point: `Stop` fires at the end of **every**
  turn, so expect a phone ping on every reply unless we add filtering
  (e.g. only notify if a turn took longer than some threshold, or switch
  to the `Notification` hook which fires on idle / permission prompts).

- [ ] **Iterate further on `writing/methodology_full.tex` — user-flagged
  intent to make additional changes.** Queued 2026-04-15. The 5-iteration
  rewrite (draft → source-verify → self-critique → bib-prune → anti-AI
  voice) produced a full submission-ready 31-page paper with a 15-entry
  curated bibliography, and the user has flagged that they will want
  further targeted edits in upcoming sessions. When the user raises this,
  ask what specifically they want to change before editing — likely
  candidates based on what was discussed during the rewrite session:
    - Section-level expansions (Discussion currently ~3 short subsections
      relative to ~6-subsection Robustness; could earn more length).
    - Adding the moved-from-Conclusion policy reflection into a new
      §6.4 (Interpretation and Scope) — flagged in the self-critique
      agent's report but not applied (judged minor).
    - Re-enabling `\usepackage{microtype}` in the preamble (currently
      commented out at line 12) if user resolves the MiKTeX
      font-expansion bug or switches TeX distribution.
    - Adding teammate Jyo's GDP / controls discussion (cf. open item #1
      above) into the Data section's "with-GDP / no-GDP bracketing"
      framing rather than the current single-sentence treatment.
    - Considering whether to swap GRI sub-items for the RAS GIR composite
      (cf. open item #2) — would change the paper's headline result and
      requires a separate decision before any rewrite.
    - Adding Introduction paragraphs that engage with the secularism
      operationalisation critique from open item #2 as a self-aware
      limitation rather than waiting for the limitations section.
  Preserve the doc structure (9 sections + Appendix), the 15-entry curated
  bibliography (in `references_full.bib`), and the anti-AI writing voice
  unless explicitly told otherwise. Compiled PDF is at
  `writing/methodology_full.pdf` (31 pages, 2.99 MB).

- [ ] **Mundlak slide — fact-check follow-ups (fixes still outstanding).**
  Queued 2026-04-15 after a full fact-check of the presentation slide on the
  Mundlak panel model against `analysis/run_analysis.py` (T4 `tier4_mundlak_re`,
  lines 469–532) and `results/results.csv`. User already edited the slide to
  fix the "religion barely changes over time" phrasing. Remaining items:

    - **Equation vs code mismatch.** Slide shows the demeaned form
      `W_it = β₁(X_it − X̄_i) + β₂X̄_i + λ_t + u_it`; code (line 509,
      `X = sm.add_constant(sub[pred_cols + cmean_cols + yr_cols])`) fits the
      raw-X form `W_it = β₁X_it + β₂X̄_i + λ_t + α_i + u_it` via
      `linearmodels.RandomEffects`. Under the demeaned form β₂ = between
      effect; under the raw-X form β₂ = between − within (Hausman-style
      contrast), not the between itself. Either keep the demeaned equation
      on the slide (simpler but doesn't match the code) or switch to the raw
      form and add the caveat that β₂ is the contrast. Code's own docstring
      at line 476 ("β₂ on X̄_i = between effect") has the same slip and
      could be tightened.

    - **Slide's equation omits α_i.** The code uses RandomEffects so α_i is
      explicitly modelled; Mundlak's contribution is to purge its correlation
      with X̄_i. Slide should either show α_i or state that it is absorbed.

    - **"Outputs two coefficients, within and between" — imprecise under the
      code's parameterisation.** In the raw-X form the two coefficients are
      (within) and (between − within). Reading β₂ as "the between effect"
      directly is only correct after demeaning.

    - **Missing sample / estimator context on the slide.** Worth mentioning:
      N=1,648, 166 countries, 2013–2022; outcome = `wbl_treatment_index`;
      **nine** time-varying regressors get Mundlak-decomposed (5 GRI +
      `v2x_rule_norm`, `v2x_civlib_norm`, `v2x_egal_norm`, `log_gdppc_norm`),
      not just "the secularism variable"; SEs clustered by country
      (`cov_type="clustered", cluster_entity=True`, line 512); year dummies
      include 2014–2022 with 2013 as baseline.

    - **Dual Mundlak in the code.** Both `T4_mundlak_re` (RE, line 471) and
      `T2_mundlak_cre` (pooled OLS with clustered SEs, line 2508) are run and
      land in `results.csv`. Within coefs match to 4 dp; the slide only
      references one estimator implicitly.

    - **Hausman test not reported.** A joint Wald test on all `_mean`
      coefficients = 0 is the Hausman test in Mundlak form. Easy addition to
      `tier4_mundlak_re` and would directly justify choosing Mundlak over RE
      on evidence rather than assumption. Consider adding both to the slide
      and to the code.

    - **"Mundlak solves the RE assumption" — frame carefully.** True that it
      addresses `α_i ⊥ X` (the canonical 1978 motivation). Slide risks
      implying Mundlak also solves Nickell bias, reverse causality,
      time-varying confounders, or measurement error — it does none of these.
      A one-line scope caveat would protect the claim.

    - **Between coefficient ≠ causal.** The significant between effects
      (apostasy_mean β=−0.122, p=0.001; blasphemy_mean β=−0.049, p=0.01) are
      cross-country correlations and carry all the usual OVB concerns (legal
      origin, colonial history, culture). The slide's framing should stop
      short of causal interpretation for the between piece; only the within
      piece inherits FE-style identification.

- [ ] **Minor polish deferred during the five-follow-up pipeline
  (2026-04-15 late evening).** None of these blocked the merge; all
  are one-liners or short cleanup commits for a future session.
    - `analysis/config.py` — add symmetric `FOCAL_PRED_REAL`,
      `FOCAL_PRED_INSTONLY`, `FOCAL_PRED_COVWT` constants so
      `run_analysis.py:3749,3757,3768` stop using bare string literals
      for the new robustness variants. Flagged by blind-agent review of
      followup #1.
    - `requirements.txt` — pin `scikit-learn` to the version used for
      the EM-imputed PCA (`IterativeImputer` is still tagged
      experimental in sklearn, so future silent upgrades could shift
      loadings). Flagged by blind-agent review of followup #3.
    - `analysis/run_analysis.py:load_and_merge` composite-logging loop
      — add a T2-with-GDP-sample-restricted changer count for
      `composite_secularism_real_norm` (not just the panel-wide
      107/198). Current reporting is defensible but the T2 identifying
      sample count is the right quantity for interpreting the real
      variant's within-country coefficient. Flagged by blind-agent
      review of followup #1.
    - Consider a fourth composite weighting variant,
      `composite_secularism_noWVS_norm`, that drops WVS entirely but
      keeps v2clrelig attitudinal at equal weight with GRI
      institutional. Would cleanly separate "v2clrelig carries residual
      within-country movement" from "WVS carries it" in the §2.2
      weight-sensitivity table. Flagged by blind-agent review of
      followup #2.
    - CLAUDE.md documents the T4 Mundlak decomposition as 10
      regressors (as of 2026-04-15), but the Mundlak presentation slide
      mentioned in Item 7 above is still stale at 9. Reconcile when the
      slide is next touched.

- [ ] **Push 13 unpushed commits on local `main` to `origin/main`**
  (target: 2026-04-17). Local `main` is at `0d81d33` and is 13 commits
  ahead of `origin/main` (https://github.com/tashawhalley2024/mdm3_project3):
  Item 2 composite swap, the five composite follow-ups, the four-step
  Item 3 long-difference pipeline, and the two-step Item 3 trim.
  Nothing has gone to GitHub yet. The user will run the push themselves
  in a separate GitBash terminal — `git push origin main` — to keep the
  team repo (tashawhalley2024/mdm3_project3) in sync. Audit-pointer
  branches were deleted locally on 2026-04-16 after the trim landed
  (item2-composite-secularism, item3-long-difference, item3-trim — all
  fully reachable from main, so labels were redundant and deletion lost
  zero work).

---

## Resolved / closed

- **Five-follow-up pipeline on composite_secularism_norm** (resolved
  2026-04-15 late evening). All five blind-agent-surfaced follow-ups
  from the Item 2 + Item 6 commit (`77417d9`) landed as separate
  commits on `item2-composite-secularism`, each ratified by a blind-
  comparison agent with conditions applied before committing:
    - `e7e6a8b` — followup 3: PCA imputation refactor (mean → EM;
      listwise + mean kept as diagnostic in
      `results/pca_loadings_comparison.csv`).
    - `88f74b8` — followup 1: no-WVS-interpolation
      `composite_secularism_real_norm`. Confirms the main composite's
      within-country wrong-signed positive is partly interpolator-
      driven: T2 within drops +0.061 (p=0.07) → +0.027 (p=0.27).
    - `9276f1d` — followup 2: weight sensitivity
      (`_instonly_norm`, `_covwt_norm`). Converging evidence with
      followup 1 that the within-country positive sign is not robust
      to any re-weighting that lowers the WVS share.
    - `18677bc` — followup 5: `gri_gov_favour_norm` footnote +
      `results/gov_favour_sensitivity.csv`.
    - `f618977` — followup 4: wild-cluster bootstrap tier-tag
      unification (`T2_changers_wild_bootstrap` now unsuffixed) and
      headline-table surface; `n_boot` 499 → 1999.
  Plus merge-prep commit `9bad880` that caught 6 stale-label sites in
  `run_plots.py` and regenerated 11_wbl_groups.png with composite
  focal. Fast-forward merged into `main` on the same session. Not
  pushed.

- **Item 3: T5 long-difference tier** (resolved 2026-04-15 after
  same-session discuss-then-execute loop). User picked long-
  difference as the biggest non-data methodological upgrade after
  being presented with four candidates (LD, fractional/beta,
  mediation, de jure/de facto outcome split). Implemented as a new
  `tier5_long_difference` function in `analysis/run_analysis.py`
  with a `_grifull` companion spec for GRI sub-item focals, wired
  into `main()` for 7 focals × 4 windows × 2 control-sets. Four
  commits on branch `item3-long-difference` off `main@9bad880`,
  each ratified by a blind-comparison agent with CONDITIONAL fixes
  applied before committing:
    - Step 1 (`8f28aa8`) — tier5 core + main wiring; fixes: Δ-of-
      normalised-GDP caveat in docstring, three-tier n_changers
      validity (invalid <10, low_power 10–24, valid ≥25), GRI-
      decomposition companion for apostasy + courts focals.
    - Step 2 (`8c5954e`) — headline-table surface; fix: moved T5
      rows between T2 and T4 rather than after wild-bootstrap (fits
      identification-strategy progression T1→T2→T5→T4).
    - Step 3 (`1ea5f08`) — new figure `13_long_difference.png`,
      methodology_full.tex §3.5 + §5.8 + abstract + §6.2 paragraph
      + tab:headline row + 2 new bib entries (AJRY 2008, B-P 2011);
      PDF 35 → 43 pages. Fixes: disambiguate "wrong-signed" (vs
      prior vs vs full-decade), acknowledge 2013–2017 p=0.06
      marginal positive, verify 2014–2022 alt-endpoint number.
    - Step 4 (merge-prep) — drift cleanup across CLAUDE.md,
      docs/robustness_storyline.md, results/README.md, analysis/
      README.md, figures/README.md, figure_guide.md,
      presentation_writeup.md, analysis/config.py (new
      FOCAL_PREDS_T5 constant), verify.py (T5 key-coef assertion).
  Headline empirical result: composite LD 2013→2022 with_gdp
  β = +0.082 (p = 0.28, N = 163, 158 changers). Wrong-signed,
  not significant. Corroborates the T2/T4 within-country null at
  the decade horizon rather than resolving it — rules out "annual
  noise / WVS interpolation" as the binding explanation for the
  short-panel null. Apostasy LD β = −0.042 (correct sign, 9
  changers, invalid). Structural cross-country reading survives.
  Not pushed.

<!-- Move resolved items here with a note on the outcome. -->
