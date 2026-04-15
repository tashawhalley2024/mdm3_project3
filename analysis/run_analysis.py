"""
analyse_secularism_women.py
=========================
Research question: Does secularism improve the welfare and treatment of women relative to men?

Two tiers of analysis (core):
  Tier 1 – Cross-sectional OLS (2014 & 2020, institutional secularism predictors)
  Tier 2 – Panel fixed-effects OLS (2013-2023, state-institution predictors)

Extensions (Phases 2–5):
  Phase 2 – GDP per capita control added to all tiers
  Phase 3 – Sub-outcome analysis (political, economic, physical safety, health)
  Phase 4 – Lagged regression (L1, L2 of GRI variables; reverse-causality test)
  Phase 5 – Robustness: SIGI 2019 cross-section, GII annual panel,
             regional heterogeneity

Outputs:
  data/processed/secularism_women_results.csv   – tidy coefficient table (all models)
  data/processed/secularism_women_log.txt       – full console log
"""

import os
import sys
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
from linearmodels.panel import PanelOLS, RandomEffects
from io import StringIO
from scipy import stats

try:
    from pydynpd import regression as pydynpd_reg
    HAS_PYDYNPD = True
except ImportError:
    HAS_PYDYNPD = False

warnings.filterwarnings("ignore")

# ── Reproducibility: fix RNG state for wild bootstrap, etc. ─────────────────────
SEED = 20250415
np.random.seed(SEED)
import random as _py_random
_py_random.seed(SEED)
try:
    _DEFAULT_RNG = np.random.default_rng(SEED)
except Exception:
    _DEFAULT_RNG = None

# ── Import shared config ────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (REGION_MAP, FOCAL_PRED, FOCAL_PRED_2,
                    FOCAL_PRED_PCA, FOCAL_PRED_LEGACY)
from utils import robust_minmax, build_secularism_composite

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Paths ──────────────────────────────────────────────────────────────────────
COMP_PATH   = os.path.join(ROOT, "data/predictors.csv")
WOMEN_PATH  = os.path.join(ROOT, "data/outcome_wbl.csv")
QOG_RAW     = os.path.join(ROOT, "data/raw/qog/qog_std_ts_jan25.csv")   # needed for placebo male vars
OUT_PATH    = os.path.join(ROOT, "results/results.csv")
LOG_PATH    = os.path.join(ROOT, "results/analysis.log")

# Phase 9 outputs
EVENTSTUDY_PATH        = os.path.join(ROOT, "results/event_study.csv")
OSTER_SENS_PATH        = os.path.join(ROOT, "results/oster_sensitivity.csv")
EVENTSTUDY_PATH_APO    = os.path.join(ROOT, "results/event_study_apostasy.csv")
OSTER_SENS_PATH_APO    = os.path.join(ROOT, "results/oster_sensitivity_apostasy.csv")
# Item 2 (2026-04-15): preserve legacy courts outputs and PCA-variant outputs
# with suffixed filenames so the composite-headlined runs do not silently
# overwrite the prior courts results.
EVENTSTUDY_PATH_LEGACY = os.path.join(ROOT, "results/event_study_religious_courts.csv")
OSTER_SENS_PATH_LEGACY = os.path.join(ROOT, "results/oster_sensitivity_religious_courts.csv")
EVENTSTUDY_PATH_PCA    = os.path.join(ROOT, "results/event_study_pca.csv")
OSTER_SENS_PATH_PCA    = os.path.join(ROOT, "results/oster_sensitivity_pca.csv")

# ── Column groups ──────────────────────────────────────────────────────────────
# Item 2 (2026-04-15): added gri_gov_favour_norm (Pew GRI Q2, 77/198 changer
# countries, 4 distinct values — was silently dropped from every regression
# previously). T4 Mundlak _mean count is therefore 10, not 9; update the
# Mundlak presentation slide (see TODO Item 7) to match.
GRI_PANEL_COLS = [
    "gri_state_religion_norm", "gri_gov_favour_norm",
    "gri_religious_law_norm", "gri_religious_courts_norm",
    "gri_blasphemy_norm", "gri_apostasy_norm",
]
# Composition (Item 2 2a): merged in load_and_merge() from
# religion_composition_normalised.csv; observed in 2010 and 2020 only (12%
# coverage), so NOT included in GRI_PANEL_COLS by default — would crash T2
# samples. Available to T1 2020 cross-section and to the composite builder.
COMPOSITION_COLS = ["pct_unaffiliated_norm", "pct_other_norm"]
CONTROLS        = ["v2x_rule_norm", "v2x_civlib_norm", "v2x_egal_norm"]
CONTROLS_GDP    = CONTROLS + ["log_gdppc_norm"]   # Phase 2: GDP-extended controls
OUTCOME         = "wbl_treatment_index"

LO_PATH    = os.path.join(ROOT, "data/raw/legal_origins/legal_origins_laporta.csv")
LO_DUMMIES = ["lo_english", "lo_german", "lo_scandinavian", "lo_socialist"]

# Sub-outcome groups (Phase 3)
SUB_OUTCOMES = {
    "political":       ["v2x_gender_norm", "v2lgfemleg_norm", "wdi_wip_norm", "wgov_minfem_norm"],
    "economic":        ["wdi_wombuslawi_norm", "wdi_lfpf_norm", "wdi_litradf_norm"],
    "physical_safety": ["wdi_homicidesf_norm", "v2x_gencl_norm"],
    "health":          ["wdi_lifexpf_norm"],
}

# ── Utility: significance star ─────────────────────────────────────────────────
def _sig(p):
    try:
        if pd.isna(p):
            return ""
    except Exception:
        pass
    return "***" if p < 0.01 else ("**" if p < 0.05 else ("*" if p < 0.10 else ""))


# ── Panel diagnostics: cluster count, changer count, within-country SD ──────────
def _panel_diagnostics(sub: pd.DataFrame, pred_col: str,
                       entity_col: str = "iso3") -> dict:
    """Return (n_clusters, n_changers, within_sd) for a fitted panel sample.

    `sub` may have (iso3, year) as MultiIndex OR as columns. `pred_col` is the
    column whose within-country variation we measure. Constants and interaction
    regressors that live only in the model matrix (not in `sub`) are skipped.
    """
    try:
        if pred_col not in sub.columns:
            # Try to recover from the index (e.g. after set_index)
            if hasattr(sub, "reset_index"):
                tmp = sub.reset_index()
                if pred_col not in tmp.columns:
                    return {"n_clusters": np.nan, "n_changers": np.nan,
                            "within_sd": np.nan}
                sub = tmp
            else:
                return {"n_clusters": np.nan, "n_changers": np.nan,
                        "within_sd": np.nan}

        if entity_col not in sub.columns:
            # MultiIndex case
            if hasattr(sub.index, "get_level_values") and entity_col in getattr(
                    sub.index, "names", []):
                ent = sub.index.get_level_values(entity_col)
            else:
                return {"n_clusters": np.nan, "n_changers": np.nan,
                        "within_sd": np.nan}
        else:
            ent = sub[entity_col]

        s = sub[pred_col] if pred_col in sub.columns else np.nan
        if not isinstance(s, pd.Series):
            return {"n_clusters": np.nan, "n_changers": np.nan,
                    "within_sd": np.nan}

        tmp = pd.DataFrame({"ent": ent.values, "x": s.values})
        n_clusters = int(tmp["ent"].nunique())
        by_ent = tmp.groupby("ent")["x"]
        # a "changer" cluster has more than one distinct value (within tol)
        n_changers = int((by_ent.nunique(dropna=True) > 1).sum())
        within_sd = float(by_ent.transform(lambda x: x - x.mean()).std(skipna=True))
        return {"n_clusters": n_clusters, "n_changers": n_changers,
                "within_sd": within_sd}
    except Exception:
        return {"n_clusters": np.nan, "n_changers": np.nan, "within_sd": np.nan}


def _std_coef(coef: float, pred_series: pd.Series, out_series: pd.Series) -> float:
    """Standardised coefficient: coef * sd(pred) / sd(outcome) (in-sample SDs)."""
    try:
        sd_x = float(pd.Series(pred_series).astype(float).std(skipna=True))
        sd_y = float(pd.Series(out_series).astype(float).std(skipna=True))
        if sd_y == 0 or np.isnan(sd_x) or np.isnan(sd_y):
            return np.nan
        return float(coef) * sd_x / sd_y
    except Exception:
        return np.nan


def _empty_diag() -> dict:
    return {"n_clusters": np.nan, "n_changers": np.nan, "within_sd": np.nan,
            "std_coef": np.nan, "valid": True, "invalid_reason": ""}


def _preds_for_focal(focal_pred: str, controls: list) -> list:
    """Return pred_cols for a regression focused on `focal_pred`.

    Added 2026-04-15 (Item 2). The existing tier2/tier4/phase functions were
    written under the assumption that `focal_pred` was always one of
    `GRI_PANEL_COLS`. After the composite swap, `focal_pred` may be a
    derived column (composite_secularism_norm or _pca_norm) that is NOT in
    GRI_PANEL_COLS. Feeding GRI_PANEL_COLS + composite to the same
    regression would be severely multicollinear (composite is a linear
    combination of GRI + v2clrelig + WVS), so we swap:

      - focal_pred IS in GRI_PANEL_COLS → keep multi-predictor spec
        (pred_cols = GRI_PANEL_COLS + controls). Used for the GRI
        decomposition the paper has always reported.
      - focal_pred is a composite / derived → use [focal_pred] + controls
        alone (no GRI sub-items). The composite coefficient is then the
        standalone headline effect, not a residual-variation effect.

    This function is called only by phase functions that take
    `focal_pred` as a parameter (LOO, placebo, Oster, event study,
    sensitivity). Tier 1/2/4 core specs keep the multi-predictor form
    unchanged — they produce the GRI decomposition headline that
    build_headline_table collects alongside the composite row.
    """
    if focal_pred in GRI_PANEL_COLS:
        return GRI_PANEL_COLS + controls
    return [focal_pred] + controls


# ═══════════════════════════════════════════════════════════════════════════════
# 1. LOAD & MERGE
# ═══════════════════════════════════════════════════════════════════════════════
def load_and_merge() -> pd.DataFrame:
    comp  = pd.read_csv(COMP_PATH)
    women = pd.read_csv(WOMEN_PATH)
    comp_nodupe = comp.drop(columns=["country"], errors="ignore")
    # log_gdppc_norm is pre-built in the comp dataset (build_secularism_composition.py)
    merged = women.merge(comp_nodupe, on=["iso3", "year"], how="left", suffixes=("", "_comp"))

    # Auxiliary columns that live in the old women_secularism file — merge them in
    # if they are not already present (e.g. when WOMEN_PATH is the WBL-based index)
    aux_cols = [
        "v2x_rule_norm", "v2x_civlib_norm", "v2x_egal_norm",  # V-Dem governance controls
        "cedaw_years_since_norm",                               # Phase 7 CEDAW control
        "wdi_lifexpf_norm", "wdi_lfpf_norm",                   # Phase 6 placebo female DVs
    ]
    needed = [c for c in aux_cols if c not in merged.columns]
    if needed:
        old_path = os.path.join(ROOT, "data/outcome_composite.csv")
        if os.path.exists(old_path):
            aux = pd.read_csv(old_path)[["iso3", "year"] + needed]
            merged = merged.merge(aux, on=["iso3", "year"], how="left")

    print(f"\n{'='*60}")
    print("MERGE VERIFICATION")
    print(f"{'='*60}")
    print(f"  Women rows      : {len(women):,}")
    print(f"  Comp rows       : {len(comp):,}")
    print(f"  Merged rows     : {len(merged):,}")
    print(f"  Countries       : {merged['iso3'].nunique()}")
    print(f"  Years           : {sorted(merged['year'].unique())}")
    if "log_gdppc_norm" in merged.columns:
        print(f"  GDP obs (non-NA): {merged['log_gdppc_norm'].notna().sum():,}")
    else:
        print("  WARNING: log_gdppc_norm not found in comp -- rebuild secularism_composition")

    print(f"  GRI obs (non-NA): {merged['gri_religious_courts_norm'].notna().sum():,}")

    # ── Item 2 (2a): merge in composition (pct_unaffiliated, pct_other) ──
    # Composition is observed in 2010 and 2020 only (~12% coverage); it is
    # kept out of GRI_PANEL_COLS so it does not crash T2 samples. The
    # composite builder consumes it only through the behavioural dimension
    # if/when it becomes available in all years.
    comp_file = os.path.join(ROOT, "data/religion_composition_normalised.csv")
    if os.path.exists(comp_file):
        comp_religion = pd.read_csv(comp_file)[[
            "iso3", "year", "pct_unaffiliated_norm", "pct_other_norm"
        ]]
        merged = merged.merge(comp_religion, on=["iso3", "year"], how="left")
        n_comp = merged["pct_unaffiliated_norm"].notna().sum()
        print(f"  Composition obs (non-NA): {n_comp:,} rows "
              f"(sparse: observed in 2010 & 2020 only)")
    else:
        print(f"  WARNING: {comp_file} not found; composition cols will be missing")

    # ── Item 2 (2b): build composite secularism indices ─────────────────
    # Equal-weight z-score (headline) + PCA variant (robustness). Both
    # oriented so higher = more religious / less secular. See
    # analysis/utils.py:build_secularism_composite for details.
    merged = build_secularism_composite(merged)

    # Follow-up #1: real (no-WVS-interpolation) variant. WVS values are
    # masked to NaN on rows where wvs_interpolated==1 before the behavioural
    # dimension is z-scored, so the composite's within-country variation
    # does not include interpolator arithmetic.
    merged = build_secularism_composite(
        merged,
        drop_interpolated_wvs=True,
        output_name="composite_secularism_real_norm",
        build_pca=False,
    )

    # Follow-up #2: weight-sensitivity variants. Both report the composite
    # under alternate dimension weightings so a reviewer can judge whether
    # the equal-weight choice is load-bearing. 'instonly' drops the V-Dem
    # attitudinal and WVS behavioural dimensions entirely; 'covwt' weights
    # each dimension by its panel-wide non-null row fraction (WVS weight
    # uses pre-interpolation wave-year coverage, so the variant is
    # meaningful even though the main composite is built post-interpolation).
    merged = build_secularism_composite(
        merged,
        weighting="institutional_only",
        output_name="composite_secularism_instonly_norm",
        build_pca=False,
    )
    merged = build_secularism_composite(
        merged,
        weighting="coverage",
        output_name="composite_secularism_covwt_norm",
        build_pca=False,
    )

    # Log composite coverage AND changer counts — raw and WVS-real-only
    # (wvs_interpolated==0). The WVS-real-only count is the meaningful
    # "did anything actually move" diagnostic for the composite's
    # behavioural dimension; raw changer counts are dominated by
    # interpolator arithmetic.
    for col in ["composite_secularism_norm",
                "composite_secularism_pca_norm",
                "composite_secularism_real_norm",
                "composite_secularism_instonly_norm",
                "composite_secularism_covwt_norm"]:
        n_obs = merged[col].notna().sum()
        chg_raw = int((merged.groupby("iso3")[col].nunique(dropna=True) > 1).sum())
        if "wvs_interpolated" in merged.columns:
            real_mask = merged["wvs_interpolated"].fillna(0).astype(float) == 0
            chg_real = int((merged[real_mask].groupby("iso3")[col]
                            .nunique(dropna=True) > 1).sum())
        else:
            chg_real = -1
        print(f"  {col}: N={n_obs:,}, changers raw={chg_raw}/198, "
              f"WVS-real-only={chg_real}/198")

    # Pre-merge legal origins so all phases can use LO dummies without re-loading
    if os.path.exists(LO_PATH):
        lo = pd.read_csv(LO_PATH)[["iso3", "legal_origin"]]
        lo["lo_english"]      = (lo["legal_origin"] == "English").astype(float)
        lo["lo_german"]       = (lo["legal_origin"] == "German").astype(float)
        lo["lo_scandinavian"] = (lo["legal_origin"] == "Scandinavian").astype(float)
        lo["lo_socialist"]    = (lo["legal_origin"] == "Socialist").astype(float)
        merged = merged.merge(lo, on="iso3", how="left")
        for col in LO_DUMMIES:
            merged[col] = merged[col].fillna(0.0)
        earliest_year = int(merged["year"].min())
        n_lo = merged[merged["year"] == earliest_year]["legal_origin"].notna().sum()
        print(f"\n  Legal origins merged: {n_lo} countries ({earliest_year})")
    else:
        print(f"\n  WARNING: {LO_PATH} not found -- LO-based checks will be skipped")

    # Deduplicate: some countries have duplicate iso3-year rows after merge
    n_before = len(merged)
    merged = merged.drop_duplicates(subset=["iso3", "year"], keep="first")
    n_dupes = n_before - len(merged)
    if n_dupes:
        print(f"\n  WARNING: dropped {n_dupes} duplicate (iso3, year) rows")

    return merged


# ═══════════════════════════════════════════════════════════════════════════════
# 2. CORRELATION MATRIX  (earliest-year cross-section)
# ═══════════════════════════════════════════════════════════════════════════════
def correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    earliest_year = int(df["year"].min())
    print(f"\n{'='*60}")
    print(f"STEP 1 – CORRELATION MATRIX ({earliest_year} cross-section)")
    print(f"{'='*60}")

    cs = df[df["year"] == earliest_year].copy()
    rel_vars = GRI_PANEL_COLS + CONTROLS + ["log_gdppc_norm"]
    all_vars = [OUTCOME] + rel_vars
    sub = cs[all_vars].dropna(subset=[OUTCOME])

    print(f"  N = {len(sub)} countries with outcome populated")

    corr = sub[GRI_PANEL_COLS + CONTROLS + ["log_gdppc_norm", OUTCOME]].corr()[[OUTCOME]].rename(
        columns={OUTCOME: "corr_with_outcome"}
    )
    corr = corr.drop(index=OUTCOME)
    corr["abs_corr"] = corr["corr_with_outcome"].abs()
    corr = corr.sort_values("abs_corr", ascending=False)

    print("\n  Correlation of secularism variables with women_treatment_index:")
    print(corr.to_string(float_format="{:.3f}".format))
    return corr


# ═══════════════════════════════════════════════════════════════════════════════
# 3. TIER 1 – CROSS-SECTIONAL OLS  (with & without GDP)
# ═══════════════════════════════════════════════════════════════════════════════
def tier1_cross_sectional(df: pd.DataFrame) -> list[dict]:
    results = []

    for year in [2014, 2020]:
        print(f"\n{'='*60}")
        print(f"STEP 2 – CROSS-SECTIONAL OLS ({year})")
        print(f"{'='*60}")

        sub = df[df["year"] == year].copy()

        lo_available = all(c in df.columns for c in LO_DUMMIES)
        spec_variants = [
            ("no_gdp",  CONTROLS,     []),
            ("with_gdp", CONTROLS_GDP, []),
        ]
        if lo_available:
            spec_variants.append(("with_lo", CONTROLS_GDP, LO_DUMMIES))

        for label, controls, extra_preds in spec_variants:
            pred_cols = GRI_PANEL_COLS + controls + extra_preds
            required  = [OUTCOME] + pred_cols
            s = sub.dropna(subset=required).copy()

            print(f"\n  [{label}] N = {len(s)}")
            if len(s) < 30:
                print("  Too few observations -- skipping.")
                continue

            X = sm.add_constant(s[pred_cols])
            y = s[OUTCOME]
            model = sm.OLS(y, X).fit(cov_type="HC3")
            print(model.summary())

            tier_tag = f"T1_{label}"
            for var in model.params.index:
                results.append({
                    "tier": tier_tag,
                    "year": year,
                    "predictor": var,
                    "coef": model.params[var],
                    "se": model.bse[var],
                    "pval": model.pvalues[var],
                    "n": int(model.nobs),
                    "r2": model.rsquared,
                })

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# 4. TIER 2 – PANEL FIXED-EFFECTS OLS  (with & without GDP)
# ═══════════════════════════════════════════════════════════════════════════════
def tier2_panel_fe(df: pd.DataFrame) -> list[dict]:
    """Tier 2 panel FE OLS with two-way FE.

    Emits, for every spec and every predictor:
      - main result (clustered-by-entity SEs)
      - Driscoll-Kraay HAC variant (tier tag T2_{label}_dk) — addresses spatial
        correlation the entity-cluster SE misses.
      - panel diagnostics (n_clusters, n_changers, within_sd) and std_coef.

    Also re-runs the three GDP-varying specs on the `with_gdp` sample to give a
    same-sample comparison (tier tag T2_{label}_samesample) isolating the effect
    of adding GDP from sample composition.
    """
    results = []

    # First pass to establish the with_gdp sample index (for same-sample variant)
    with_gdp_required = [OUTCOME, "iso3", "year"] + GRI_PANEL_COLS + CONTROLS_GDP
    with_gdp_sub = df[with_gdp_required].dropna(
        subset=[OUTCOME] + GRI_PANEL_COLS + CONTROLS_GDP).copy()
    with_gdp_index = pd.MultiIndex.from_frame(with_gdp_sub[["iso3", "year"]])

    specs = [
        ("gri_only",    []),
        ("gri_gdp",     ["log_gdppc_norm"]),
        ("no_gdp",      CONTROLS),
        ("with_gdp",    CONTROLS_GDP),
    ]

    for label, controls in specs:
        print(f"\n{'='*60}")
        print(f"STEP 3 – PANEL FE [{label}] (country + year FE, 2013-2023)")
        print(f"{'='*60}")

        pred_cols = GRI_PANEL_COLS + controls
        required  = [OUTCOME, "iso3", "year"] + pred_cols
        sub = df[required].dropna(subset=[OUTCOME] + pred_cols).copy()

        print(f"  N = {len(sub):,} obs, {sub['iso3'].nunique()} countries, "
              f"{sub['year'].nunique()} years")

        sub_idx = sub.set_index(["iso3", "year"])
        y = sub_idx[OUTCOME]
        X = sm.add_constant(sub_idx[pred_cols])

        model = PanelOLS(y, X, entity_effects=True, time_effects=True)
        res   = model.fit(cov_type="clustered", cluster_entity=True)
        print(res.summary)

        tier_tag = f"T2_{label}"
        for var in res.params.index:
            # Compute per-predictor diagnostics & std coef (skip for constant)
            if var in pred_cols:
                diag = _panel_diagnostics(sub, var)
                std_c = _std_coef(res.params[var], sub[var], sub[OUTCOME])
            else:
                diag = {"n_clusters": int(sub["iso3"].nunique()),
                        "n_changers": np.nan, "within_sd": np.nan}
                std_c = np.nan
            results.append({
                "tier": tier_tag,
                "year": "all",
                "predictor": var,
                "coef": res.params[var],
                "se": res.std_errors[var],
                "pval": res.pvalues[var],
                "n": res.nobs,
                "r2": res.rsquared,
                "n_clusters": diag["n_clusters"],
                "n_changers": diag["n_changers"],
                "within_sd":  diag["within_sd"],
                "std_coef":   std_c,
                "se_type":    "cluster_entity",
                "valid":      True,
                "invalid_reason": "",
            })

        # ── Driscoll-Kraay HAC variant (bandwidth ≈ T^{1/4} ≈ 2 for T=10) ──
        try:
            res_dk = model.fit(cov_type="kernel", kernel="bartlett", bandwidth=2)
            dk_tag = f"T2_{label}_dk"
            for var in res_dk.params.index:
                if var in pred_cols:
                    diag = _panel_diagnostics(sub, var)
                    std_c = _std_coef(res_dk.params[var], sub[var], sub[OUTCOME])
                else:
                    diag = {"n_clusters": int(sub["iso3"].nunique()),
                            "n_changers": np.nan, "within_sd": np.nan}
                    std_c = np.nan
                results.append({
                    "tier": dk_tag,
                    "year": "all",
                    "predictor": var,
                    "coef": res_dk.params[var],
                    "se": res_dk.std_errors[var],
                    "pval": res_dk.pvalues[var],
                    "n": res_dk.nobs,
                    "r2": res_dk.rsquared,
                    "n_clusters": diag["n_clusters"],
                    "n_changers": diag["n_changers"],
                    "within_sd":  diag["within_sd"],
                    "std_coef":   std_c,
                    "se_type":    "driscoll_kraay_bw2",
                    "valid":      True,
                    "invalid_reason": "",
                })
        except Exception as e:
            print(f"  [DK variant failed for {label}: {e}]")

        # ── Same-sample variant: re-fit on with_gdp sample index ──────────
        try:
            sub_ss = sub.merge(
                with_gdp_sub[["iso3", "year"]], on=["iso3", "year"], how="inner"
            )
            if len(sub_ss) > 0 and len(sub_ss) != len(sub):
                sub_ss_idx = sub_ss.set_index(["iso3", "year"])
                y_ss = sub_ss_idx[OUTCOME]
                X_ss = sm.add_constant(sub_ss_idx[pred_cols])
                res_ss = PanelOLS(
                    y_ss, X_ss, entity_effects=True, time_effects=True
                ).fit(cov_type="clustered", cluster_entity=True)
                ss_tag = f"T2_{label}_samesample"
                print(f"  [same-sample N={res_ss.nobs:,}]")
                for var in res_ss.params.index:
                    if var in pred_cols:
                        diag = _panel_diagnostics(sub_ss, var)
                        std_c = _std_coef(res_ss.params[var], sub_ss[var], sub_ss[OUTCOME])
                    else:
                        diag = {"n_clusters": int(sub_ss["iso3"].nunique()),
                                "n_changers": np.nan, "within_sd": np.nan}
                        std_c = np.nan
                    results.append({
                        "tier": ss_tag,
                        "year": "all",
                        "predictor": var,
                        "coef": res_ss.params[var],
                        "se": res_ss.std_errors[var],
                        "pval": res_ss.pvalues[var],
                        "n": res_ss.nobs,
                        "r2": res_ss.rsquared,
                        "n_clusters": diag["n_clusters"],
                        "n_changers": diag["n_changers"],
                        "within_sd":  diag["within_sd"],
                        "std_coef":   std_c,
                        "se_type":    "cluster_entity",
                        "valid":      True,
                        "invalid_reason": "",
                    })
        except Exception as e:
            print(f"  [same-sample variant failed for {label}: {e}]")

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# 5. TIER 4 – MUNDLAK RE-FE HYBRID  (Mundlak 1978)
# ═══════════════════════════════════════════════════════════════════════════════
def tier4_mundlak_re(df: pd.DataFrame) -> list[dict]:
    """Mundlak (1978) RE-FE hybrid: RandomEffects with country-mean regressors.

    Adds X̄_i (country mean of each time-varying X) as extra regressors.
    β₁ on X_it = within effect (should match T2 TWFE).
    β₂ on X̄_i = between effect.
    """
    print(f"\n{'='*60}")
    print("TIER 4 – MUNDLAK RE-FE HYBRID (RandomEffects + country means)")
    print(f"{'='*60}")

    results = []

    pred_cols = GRI_PANEL_COLS + CONTROLS_GDP
    required  = [OUTCOME, "iso3", "year"] + pred_cols
    sub       = df[required].dropna(subset=[OUTCOME] + pred_cols).copy()

    # Mundlak device: country means of all 9 time-varying predictors
    cmean_cols = []
    for col in pred_cols:
        mc = col + "_mean"
        sub[mc] = sub.groupby("iso3")[col].transform("mean")
        cmean_cols.append(mc)

    # Drop any zero-variance mean columns
    cmean_cols = [c for c in cmean_cols if sub[c].std() > 1e-8]

    # Year dummies to absorb common time shocks (comparable to T2 time FE)
    year_dummies = pd.get_dummies(sub["year"], prefix="yr", drop_first=True).astype(float)
    sub = pd.concat([sub.reset_index(drop=True), year_dummies.reset_index(drop=True)], axis=1)
    yr_cols = list(year_dummies.columns)

    print(f"  N = {len(sub):,} obs, {sub['iso3'].nunique()} countries")
    print(f"  Predictors: {len(pred_cols)} original + {len(cmean_cols)} country means"
          f" + {len(yr_cols)} year dummies")

    # Preserve a non-indexed copy of `sub` for _panel_diagnostics after
    # the MultiIndex is set; the diagnostic function needs iso3 as a column.
    sub_flat = sub.copy()
    # Keep the (iso3, year) keys of the main T4 sample so the samesample
    # variant below can merge against them.
    pan_main_keys = sub_flat[["iso3", "year"]].drop_duplicates().copy()

    sub = sub.set_index(["iso3", "year"])
    y = sub[OUTCOME]
    X = sm.add_constant(sub[pred_cols + cmean_cols + yr_cols])

    model = RandomEffects(y, X)
    res   = model.fit(cov_type="clustered", cluster_entity=True)
    print(res.summary)

    # Sanity check: compare within coefficients to T2
    print("\n  Sanity check -- T4 within coefs (should ~= T2 TWFE):")
    for v in GRI_PANEL_COLS:
        print(f"    {v}: coef={res.params[v]:.5f}  p={res.pvalues[v]:.4f}")

    # Item 2 (Step 6): per-predictor diagnostics wired through so every T4
    # row in results.csv carries n_clusters, n_changers, within_sd, std_coef.
    # _mean predictors inherit diagnostics from their parent time-varying col.
    for var in res.params.index:
        parent = var[:-5] if var.endswith("_mean") else var
        if parent in pred_cols:
            diag = _panel_diagnostics(sub_flat, parent)
            std_c = _std_coef(res.params[var], sub_flat[parent], sub_flat[OUTCOME])
        else:
            diag = {"n_clusters": int(sub_flat["iso3"].nunique()),
                    "n_changers": np.nan, "within_sd": np.nan}
            std_c = np.nan
        results.append({
            "tier":      "T4_mundlak_re",
            "year":      "all",
            "predictor": var,
            "coef":      res.params[var],
            "se":        res.std_errors[var],
            "pval":      res.pvalues[var],
            "n":         res.nobs,
            "r2":        res.rsquared,
            "n_clusters": diag["n_clusters"],
            "n_changers": diag["n_changers"],
            "within_sd":  diag["within_sd"],
            "std_coef":   std_c,
            "se_type":    "cluster_entity",
            "valid":      True,
            "invalid_reason": "",
        })

    # ── Item 2 (Step 7): T4 same-sample variant ────────────────────────
    # Rerun mundlak with pred_cols = GRI + CONTROLS (no log_gdppc) on the
    # SAME sample as the main T4 (with_gdp). Rebuild from df from scratch
    # to avoid duplicate-column issues inherited from the main block.
    try:
        no_gdp_pred_cols = GRI_PANEL_COLS + CONTROLS  # no log_gdppc_norm
        # Rebuild from df using the with_gdp sample rows (same as main T4).
        with_gdp_keys = pan_main_keys  # defined below — (iso3, year) frame
        required_ss = [OUTCOME, "iso3", "year"] + no_gdp_pred_cols
        sub_ss_raw = df[required_ss].dropna(
            subset=[OUTCOME] + no_gdp_pred_cols).copy()
        sub_ss_raw = sub_ss_raw.merge(
            with_gdp_keys, on=["iso3", "year"], how="inner")

        # Mundlak country means on the intersected sample
        cmean_cols_ss = []
        for col in no_gdp_pred_cols:
            mc = col + "_mean"
            sub_ss_raw[mc] = sub_ss_raw.groupby("iso3")[col].transform("mean")
            cmean_cols_ss.append(mc)
        cmean_cols_ss = [c for c in cmean_cols_ss
                         if sub_ss_raw[c].std() > 1e-8]

        yr_ss = pd.get_dummies(sub_ss_raw["year"], prefix="yr",
                                drop_first=True).astype(float)
        yr_cols_ss = list(yr_ss.columns)
        ss_combined = pd.concat(
            [sub_ss_raw.reset_index(drop=True), yr_ss.reset_index(drop=True)],
            axis=1)

        ss_flat = ss_combined.copy()
        ss_indexed = ss_combined.set_index(["iso3", "year"])
        y_ss = ss_indexed[OUTCOME]
        X_ss = sm.add_constant(
            ss_indexed[no_gdp_pred_cols + cmean_cols_ss + yr_cols_ss])
        res_ss = RandomEffects(y_ss, X_ss).fit(
            cov_type="clustered", cluster_entity=True)

        print(f"\n  T4 SAME-SAMPLE no-GDP variant: N={res_ss.nobs:,}, "
              f"{ss_flat['iso3'].nunique()} countries")
        for var in res_ss.params.index:
            parent = var[:-5] if var.endswith("_mean") else var
            if parent in no_gdp_pred_cols:
                diag = _panel_diagnostics(ss_flat, parent)
                std_c = _std_coef(float(res_ss.params[var]),
                                   ss_flat[parent], ss_flat[OUTCOME])
            else:
                diag = {"n_clusters": int(ss_flat["iso3"].nunique()),
                        "n_changers": np.nan, "within_sd": np.nan}
                std_c = np.nan
            results.append({
                "tier":      "T4_mundlak_re_samesample",
                "year":      "all",
                "predictor": var,
                "coef":      float(res_ss.params[var]),
                "se":        float(res_ss.std_errors[var]),
                "pval":      float(res_ss.pvalues[var]),
                "n":         res_ss.nobs,
                "r2":        res_ss.rsquared,
                "n_clusters": diag["n_clusters"],
                "n_changers": diag["n_changers"],
                "within_sd":  diag["within_sd"],
                "std_coef":   std_c,
                "se_type":    "cluster_entity",
                "valid":      True,
                "invalid_reason": "",
            })
    except Exception as e:
        print(f"  [T4 same-sample variant failed: {e}]")

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# 6. TIER 3 – SYSTEM-GMM  (Blundell-Bond 1998)
# ═══════════════════════════════════════════════════════════════════════════════
def tier3_system_gmm(df: pd.DataFrame) -> list[dict]:
    """Blundell-Bond (1998) System-GMM with dynamic panel (lagged DV).

    Estimates: W_it = rho*W_{i,t-1} + beta*G_it + gamma*X_it + alpha_i + lambda_t + e_it
    Two-step GMM with Windmeijer (2005) SE correction, collapsed instruments.
    GRI + V-Dem treated as endogenous (gmm, lags 2:3); GDP as predetermined (iv).
    """
    print(f"\n{'='*60}")
    print("TIER 3 – SYSTEM-GMM (Blundell-Bond 1998)")
    print(f"{'='*60}")

    if not HAS_PYDYNPD:
        print("  SKIPPED: pydynpd not installed (pip install pydynpd)")
        return []

    results = []

    # ── 1. Prepare sample (same predictor set as T2_with_gdp / T4) ──────────
    pred_cols = GRI_PANEL_COLS + CONTROLS_GDP
    required  = [OUTCOME, "iso3", "year"] + pred_cols
    sub       = df[required].dropna(subset=[OUTCOME] + pred_cols).copy()
    # Duplicates already removed in load_and_merge()
    sub = sub.sort_values(["iso3", "year"]).reset_index(drop=True)

    n_obs      = len(sub)
    n_countries = sub["iso3"].nunique()
    n_years    = sub["year"].nunique()
    print(f"  N = {n_obs:,} obs, {n_countries} countries, {n_years} years")

    # ── 2. Build pydynpd command string ─────────────────────────────────────
    # Endogenous: outcome (lagged DV) + 5 GRI = 6 vars
    # V-Dem governance indices are slow-moving → treat as predetermined
    endogenous    = [OUTCOME] + GRI_PANEL_COLS
    predetermined = CONTROLS + ["log_gdppc_norm"]

    dep_and_regs = (f"{OUTCOME} L1.{OUTCOME} "
                    + " ".join(GRI_PANEL_COLS + CONTROLS_GDP))
    gmm_blocks   = " ".join(f"gmm({v}, 2:2)" for v in endogenous)
    iv_blocks    = "iv(" + " ".join(predetermined) + ")" if predetermined else ""
    options      = "collapse timedumm"

    cmd = f"{dep_and_regs} | {gmm_blocks} {iv_blocks} | {options}"
    print(f"\n  Command:\n  {cmd}\n")

    # ── 3. Estimate ─────────────────────────────────────────────────────────
    try:
        result = pydynpd_reg.abond(cmd, sub, ["iso3", "year"])
        m = result.models[0]
    except Exception as e:
        print(f"  ERROR: System-GMM estimation failed: {e}")
        return []

    # ── 4. Diagnostics ──────────────────────────────────────────────────────
    print(f"\n  Observations: {m.num_obs}  |  Groups (N): {m.N}"
          f"  |  Periods (T): {m.T}")

    num_instr = m.num_instruments if hasattr(m, "num_instruments") else None
    if num_instr is not None:
        print(f"  Instrument count: {num_instr}")
        if num_instr > m.N:
            print(f"  *** WARNING: instruments ({num_instr}) > groups ({m.N})"
                  " — Hansen test may be unreliable ***")

    hansen_p = m.hansen.p_value
    ar1_p    = m.AR_list[0].P_value
    ar2_p    = m.AR_list[1].P_value

    hansen_note = ("(OK)" if 0.05 < hansen_p <= 0.25
                   else "(CAUTION: possibly too many instruments)" if hansen_p > 0.25
                   else "(REJECT: instruments invalid)")
    ar1_note = "(OK: expected)" if ar1_p < 0.05 else "(unexpected: no AR(1))"
    ar2_note = ("(OK: no serial correlation)" if ar2_p > 0.05
                else "(PROBLEM: serial correlation in levels)")

    print(f"\n  Hansen J-test:  p = {hansen_p:.4f}  {hansen_note}")
    print(f"  AR(1):          p = {ar1_p:.4f}  {ar1_note}")
    print(f"  AR(2):          p = {ar2_p:.4f}  {ar2_note}")

    # ── 5. Regression table ─────────────────────────────────────────────────
    print(f"\n{m.regression_table.to_string(index=False)}")

    # ── 5b. Roodman (2009) bounds check on lagged DV ───────────────────────
    ldv_rows = m.regression_table[m.regression_table["variable"].str.contains("L1")]
    if not ldv_rows.empty:
        rho_gmm = float(ldv_rows.iloc[0]["coefficient"])

        # OLS upper bound (pooled OLS with lagged DV)
        ols_df = sub.copy()
        ols_df["L1_outcome"] = ols_df.groupby("iso3")[OUTCOME].shift(1)
        ols_df = ols_df.dropna(subset=["L1_outcome"])
        X_ols = sm.add_constant(ols_df[["L1_outcome"]])
        rho_ols = float(sm.OLS(ols_df[OUTCOME], X_ols).fit().params["L1_outcome"])

        # FE lower bound (within estimator with lagged DV)
        fe_df = ols_df.set_index(["iso3", "year"])
        X_fe = sm.add_constant(fe_df[["L1_outcome"]])
        try:
            rho_fe = float(
                PanelOLS(fe_df[OUTCOME], X_fe, entity_effects=True).fit().params["L1_outcome"]
            )
        except Exception:
            rho_fe = np.nan

        in_bounds = (not np.isnan(rho_fe)) and (rho_fe < rho_gmm < rho_ols)
        bounds_note = "(OK: within Roodman bounds)" if in_bounds else "(FAIL: outside Roodman bounds)"

        print(f"\n  Roodman (2009) bounds check:")
        print(f"    rho_FE  = {rho_fe:.4f}  (lower bound)")
        print(f"    rho_GMM = {rho_gmm:.4f}  (estimate)")
        print(f"    rho_OLS = {rho_ols:.4f}  (upper bound)")
        print(f"    {bounds_note}")
    else:
        in_bounds = False

    # ── 5c. Invalidity flag: T3 fails Roodman → mark every row invalid ───────
    t3_valid = bool(in_bounds)
    t3_reason = "" if t3_valid else "roodman_bounds_fail"

    # ── 6. Build results list (per-coefficient rows) ────────────────────────
    # Item 2 (Step 6): per-predictor diagnostics. Cosmetic for T3 since
    # Roodman bounds fail means every row is flagged invalid, but included
    # for cross-tier consistency.
    for _, row in m.regression_table.iterrows():
        var = row["variable"]
        # pydynpd regression_table may have L1. prefixes; strip for diagnostics lookup
        parent = var.split(".")[-1] if "." in str(var) else var
        if parent in pred_cols:
            diag = _panel_diagnostics(sub, parent)
            std_c = _std_coef(row["coefficient"], sub[parent], sub[OUTCOME])
        else:
            diag = {"n_clusters": int(sub["iso3"].nunique()),
                    "n_changers": np.nan, "within_sd": np.nan}
            std_c = np.nan
        results.append({
            "tier":      "T3_system_gmm",
            "year":      "all",
            "predictor": var,
            "coef":      row["coefficient"],
            "se":        row["std_err"],
            "pval":      row["p_value"],
            "n":         m.num_obs,
            "r2":        np.nan,
            "n_clusters": diag["n_clusters"],
            "n_changers": diag["n_changers"],
            "within_sd":  diag["within_sd"],
            "std_coef":   std_c,
            "se_type":    "gmm_windmeijer",
            "valid":     t3_valid,
            "invalid_reason": t3_reason,
        })

    # ── 7. Diagnostic rows (prefixed _ for easy filtering) ──────────────────
    diag_rows = [("_hansen_p", hansen_p),
                  ("_ar1_p",    ar1_p),
                  ("_ar2_p",    ar2_p)]
    if not ldv_rows.empty:
        diag_rows += [("_rho_gmm",       rho_gmm),
                      ("_rho_ols_upper",  rho_ols),
                      ("_rho_fe_lower",   rho_fe)]
    for diag_name, diag_val in diag_rows:
        results.append({
            "tier":      "T3_system_gmm",
            "year":      "all",
            "predictor": diag_name,
            "coef":      diag_val,
            "se":        np.nan,
            "pval":      np.nan,
            "n":         m.num_obs,
            "r2":        np.nan,
            "valid":     t3_valid,
            "invalid_reason": t3_reason,
        })

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 3 – SUB-OUTCOME ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
def _build_sub_index(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    """Row mean of available sub-columns (missing handled by mean of non-NA)."""
    available = [c for c in cols if c in df.columns]
    if not available:
        return pd.Series(np.nan, index=df.index)
    return df[available].mean(axis=1, skipna=True)


def phase3_sub_outcomes(df: pd.DataFrame) -> list[dict]:
    """
    Tier 1 (cross-section) and Tier 2 (panel FE) for each sub-outcome group.
    Controls: CONTROLS_GDP (with GDP).
    """
    results = []

    print(f"\n{'='*60}")
    print("PHASE 3 – SUB-OUTCOME ANALYSIS")
    print(f"{'='*60}")

    # Guard: sub-outcome columns only exist in the old 13-component index
    missing_sub = [c for cols in SUB_OUTCOMES.values() for c in cols if c not in df.columns]
    if missing_sub:
        print("  PHASE 3 skipped: sub-outcome columns not present in current dataset")
        return results

    # Prepare sub-indices
    work = df.copy()
    for name, cols in SUB_OUTCOMES.items():
        work[f"sub_{name}"] = _build_sub_index(work, cols)

    for name in SUB_OUTCOMES:
        sub_outcome = f"sub_{name}"

        # ── Tier 1: cross-section ──────────────────────────────────────────
        print(f"\n  [Phase 3 / Tier 1] outcome = {sub_outcome}")
        pred_cols  = GRI_PANEL_COLS + CONTROLS_GDP

        for year in [2014, 2020]:
            sub = work[work["year"] == year].copy()
            required = [sub_outcome] + pred_cols
            s = sub.dropna(subset=required).copy()
            if len(s) < 25:
                continue

            X = sm.add_constant(s[pred_cols])
            y = s[sub_outcome]
            model = sm.OLS(y, X).fit(cov_type="HC3")
            print(f"    {year}: N={len(s)}, R²={model.rsquared:.3f}")

            for var in model.params.index:
                results.append({
                    "tier": f"P3_T1_{name}",
                    "year": year,
                    "predictor": var,
                    "coef": model.params[var],
                    "se": model.bse[var],
                    "pval": model.pvalues[var],
                    "n": int(model.nobs),
                    "r2": model.rsquared,
                })

        # ── Tier 2: panel FE ────────────────────────────────────────────────
        print(f"  [Phase 3 / Tier 2] outcome = {sub_outcome}")
        pred_cols_fe = GRI_PANEL_COLS + CONTROLS_GDP
        required_fe  = [sub_outcome, "iso3", "year"] + pred_cols_fe
        panel = work[required_fe].dropna(subset=[sub_outcome] + pred_cols_fe).copy()

        if len(panel) < 100:
            print(f"    Too few obs ({len(panel)}) — skipping panel FE.")
            continue

        print(f"    Panel N={len(panel):,}, {panel['iso3'].nunique()} countries")
        panel = panel.set_index(["iso3", "year"])
        y = panel[sub_outcome]
        X = sm.add_constant(panel[pred_cols_fe])

        try:
            model = PanelOLS(y, X, entity_effects=True, time_effects=True)
            res   = model.fit(cov_type="clustered", cluster_entity=True)
            print(res.summary)

            for var in res.params.index:
                results.append({
                    "tier": f"P3_T2_{name}",
                    "year": "all",
                    "predictor": var,
                    "coef": res.params[var],
                    "se": res.std_errors[var],
                    "pval": res.pvalues[var],
                    "n": res.nobs,
                    "r2": res.rsquared,
                })
        except Exception as e:
            print(f"    Panel FE failed: {e}")

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 4 – LAGGED REGRESSION (causal plausibility)
# ═══════════════════════════════════════════════════════════════════════════════
def phase4_lagged(df: pd.DataFrame) -> list[dict]:
    """
    Re-run Tier 2 panel FE with L1 and L2 lags of GRI variables.
    Also run the reverse-causality test: outcome(t) → courts(t+1).
    """
    results = []

    print(f"\n{'='*60}")
    print("PHASE 4 – LAGGED REGRESSION")
    print(f"{'='*60}")

    work = df[["iso3", "year"] + GRI_PANEL_COLS + CONTROLS_GDP + [OUTCOME]].copy()
    work = work.sort_values(["iso3", "year"])

    for lag in [1, 2]:
        print(f"\n  [L{lag}] Lagged GRI predictors -> {OUTCOME}")
        lagged = work[["iso3", "year"] + GRI_PANEL_COLS].copy()
        lagged["year"] = lagged["year"] + lag  # shift year forward by lag
        lagged.columns = (["iso3", "year"] +
                          [f"{c}_L{lag}" for c in GRI_PANEL_COLS])

        merged = work[["iso3", "year"] + CONTROLS_GDP + [OUTCOME]].merge(
            lagged, on=["iso3", "year"], how="inner"
        )

        lag_cols = [f"{c}_L{lag}" for c in GRI_PANEL_COLS]
        pred_cols = lag_cols + CONTROLS_GDP
        required  = [OUTCOME, "iso3", "year"] + pred_cols
        panel = merged[required].dropna().copy()

        print(f"    N = {len(panel):,} obs, {panel['iso3'].nunique()} countries, "
              f"years {panel['year'].min()}–{panel['year'].max()}")

        if len(panel) < 100:
            print("    Too few obs — skipping.")
            continue

        panel = panel.set_index(["iso3", "year"])
        y = panel[OUTCOME]
        X = sm.add_constant(panel[pred_cols])

        try:
            model = PanelOLS(y, X, entity_effects=True, time_effects=True)
            res   = model.fit(cov_type="clustered", cluster_entity=True)
            print(res.summary)

            for var in res.params.index:
                results.append({
                    "tier": f"P4_panel_fe_L{lag}",
                    "year": "all",
                    "predictor": var,
                    "coef": res.params[var],
                    "se": res.std_errors[var],
                    "pval": res.pvalues[var],
                    "n": res.nobs,
                    "r2": res.rsquared,
                })
        except Exception as e:
            print(f"    Panel FE L{lag} failed: {e}")

    # ── Reverse causality: outcome(t) → courts(t+1) ──────────────────────────
    print("\n  [Reverse causality] women_treatment_index(t) -> "
          "gri_religious_courts_norm(t+1)")

    COURTS = "gri_religious_courts_norm"
    rc_now  = work[["iso3", "year", OUTCOME, COURTS] + CONTROLS_GDP].copy()
    rc_lead = work[["iso3", "year", COURTS]].copy()
    rc_lead["year"] = rc_lead["year"] - 1   # lead by 1
    rc_lead = rc_lead.rename(columns={COURTS: f"{COURTS}_lead1"})

    rc = rc_now.merge(rc_lead, on=["iso3", "year"], how="inner")
    rc = rc.dropna(subset=[OUTCOME, f"{COURTS}_lead1"] + CONTROLS_GDP).copy()

    print(f"    N = {len(rc):,} obs")
    if len(rc) >= 100:
        rc = rc.set_index(["iso3", "year"])
        y = rc[f"{COURTS}_lead1"]
        X = sm.add_constant(rc[[OUTCOME] + CONTROLS_GDP])

        try:
            model = PanelOLS(y, X, entity_effects=True, time_effects=True)
            res   = model.fit(cov_type="clustered", cluster_entity=True)
            print(res.summary)

            for var in res.params.index:
                results.append({
                    "tier": "P4_reverse_causality",
                    "year": "all",
                    "predictor": var,
                    "coef": res.params[var],
                    "se": res.std_errors[var],
                    "pval": res.pvalues[var],
                    "n": res.nobs,
                    "r2": res.rsquared,
                })
        except Exception as e:
            print(f"    Reverse causality FE failed: {e}")

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 5 – ROBUSTNESS CHECKS
# ═══════════════════════════════════════════════════════════════════════════════
def phase5_robustness(df: pd.DataFrame) -> list[dict]:
    results = []

    print(f"\n{'='*60}")
    print("PHASE 5 – ROBUSTNESS CHECKS")
    print(f"{'='*60}")

    # ── B1: SIGI 2019 cross-section ────────────────────────────────────────────
    print("\n  [B1] SIGI 2019 as alternative DV (cross-section)")
    sigi_dvs = ["sigi_norm", "sigi_family_norm", "sigi_physical_norm",
                "sigi_resources_norm", "sigi_civil_norm"]
    sigi_dvs_avail = [c for c in sigi_dvs if c in df.columns]

    for dv in sigi_dvs_avail:
        sub = df[df["year"] == 2019].copy()
        pred_cols = GRI_PANEL_COLS + CONTROLS_GDP
        required  = [dv] + pred_cols
        s = sub.dropna(subset=required).copy()
        if len(s) < 25:
            continue

        X = sm.add_constant(s[pred_cols])
        y = s[dv]
        # SIGI is a dis-empowerment index (higher = worse) so note direction
        model = sm.OLS(y, X).fit(cov_type="HC3")
        print(f"    DV={dv}: N={len(s)}, R²={model.rsquared:.3f}")

        for var in model.params.index:
            results.append({
                "tier": f"P5_B1_SIGI_{dv}",
                "year": 2019,
                "predictor": var,
                "coef": model.params[var],
                "se": model.bse[var],
                "pval": model.pvalues[var],
                "n": int(model.nobs),
                "r2": model.rsquared,
            })

    # ── B2: GII annual panel FE ────────────────────────────────────────────────
    print("\n  [B2] GII (Gender Inequality Index) as annual DV in panel FE")
    GII = "gii_norm"
    if GII in df.columns:
        pred_cols = GRI_PANEL_COLS + CONTROLS_GDP
        required  = [GII, "iso3", "year"] + pred_cols
        panel = df[required].dropna(subset=[GII] + pred_cols).copy()
        print(f"    N = {len(panel):,} obs, {panel['iso3'].nunique()} countries")

        if len(panel) >= 100:
            panel = panel.set_index(["iso3", "year"])
            y = panel[GII]
            X = sm.add_constant(panel[pred_cols])
            try:
                model = PanelOLS(y, X, entity_effects=True, time_effects=True)
                res   = model.fit(cov_type="clustered", cluster_entity=True)
                print(res.summary)
                for var in res.params.index:
                    results.append({
                        "tier": "P5_B2_GII_panel_fe",
                        "year": "all",
                        "predictor": var,
                        "coef": res.params[var],
                        "se": res.std_errors[var],
                        "pval": res.pvalues[var],
                        "n": res.nobs,
                        "r2": res.rsquared,
                    })
            except Exception as e:
                print(f"    GII panel FE failed: {e}")
    else:
        print(f"    {GII} not found in dataset — skipping.")

    # ── A4: Regional heterogeneity ────────────────────────────────────────────
    earliest_year = int(df["year"].min())
    print(f"\n  [A4] Regional heterogeneity (Tier 1 by region, {earliest_year})")
    df["region"] = df["iso3"].map(REGION_MAP).fillna("Other")

    pred_cols = GRI_PANEL_COLS + CONTROLS_GDP

    for region in sorted(df["region"].unique()):
        sub = df[(df["year"] == earliest_year) & (df["region"] == region)].copy()
        required = [OUTCOME] + pred_cols
        s = sub.dropna(subset=required).copy()

        print(f"    Region={region}: N={len(s)}", end="")
        if len(s) < 30:
            print(" — too few (< 30), skipping.")
            continue

        # Drop predictors with no variation in this region
        vary_cols = [c for c in pred_cols if s[c].std() > 1e-8]
        X = sm.add_constant(s[vary_cols])
        y = s[OUTCOME]
        model = sm.OLS(y, X).fit(cov_type="HC3")
        print(f", R²={model.rsquared:.3f}")

        for var in model.params.index:
            results.append({
                "tier": f"P5_A4_{region.replace(' ', '_').replace('-', '_')}",
                "year": earliest_year,
                "predictor": var,
                "coef": model.params[var],
                "se": model.bse[var],
                "pval": model.pvalues[var],
                "n": int(model.nobs),
                "r2": model.rsquared,
            })

    # ── B4: v2clrelig_norm (V-Dem freedom of religion) ────────────────────────
    print("\n  [B4] v2clrelig_norm (V-Dem freedom of religion) as secularism predictor")
    CLRELIG = "v2clrelig_norm"
    if CLRELIG in df.columns:
        # (i) Extended spec: v2clrelig alongside standard GRI set
        pred_ext  = GRI_PANEL_COLS + [CLRELIG] + CONTROLS_GDP
        required  = [OUTCOME, "iso3", "year"] + pred_ext
        panel_ext = df[required].dropna(subset=[OUTCOME] + pred_ext).copy()
        print(f"    GRI+clrelig extended: N={len(panel_ext):,} obs, "
              f"{panel_ext['iso3'].nunique()} countries")
        if len(panel_ext) >= 100:
            try:
                pfe = panel_ext.set_index(["iso3", "year"])
                res_ext = PanelOLS(pfe[OUTCOME], sm.add_constant(pfe[pred_ext]),
                                   entity_effects=True, time_effects=True
                                   ).fit(cov_type="clustered", cluster_entity=True)
                for key_v in [FOCAL_PRED_LEGACY, CLRELIG]:
                    if key_v in res_ext.params:
                        c, se, p = (res_ext.params[key_v],
                                    res_ext.std_errors[key_v],
                                    res_ext.pvalues[key_v])
                        print(f"    {key_v}: coef={c:.5f}  p={p:.4f}  {_sig(p)}")
                for var in res_ext.params.index:
                    results.append({
                        "tier":      "P5_B4_clrelig_extended",
                        "year":      "all",
                        "predictor": var,
                        "coef":      res_ext.params[var],
                        "se":        res_ext.std_errors[var],
                        "pval":      res_ext.pvalues[var],
                        "n":         res_ext.nobs,
                        "r2":        float(getattr(res_ext.rsquared, "within", res_ext.rsquared)),
                    })
            except Exception as e:
                print(f"    clrelig extended spec failed: {e}")

        # (ii) Sole secularism predictor -- tests whether freedom-of-religion
        #      effect holds independently of the GRI institutional measures
        pred_sole = [CLRELIG] + CONTROLS_GDP
        required  = [OUTCOME, "iso3", "year"] + pred_sole
        panel_sole = df[required].dropna(subset=[OUTCOME] + pred_sole).copy()
        print(f"    clrelig-only: N={len(panel_sole):,} obs, "
              f"{panel_sole['iso3'].nunique()} countries")
        if len(panel_sole) >= 100:
            try:
                pfe2 = panel_sole.set_index(["iso3", "year"])
                res_sole = PanelOLS(pfe2[OUTCOME], sm.add_constant(pfe2[pred_sole]),
                                    entity_effects=True, time_effects=True
                                    ).fit(cov_type="clustered", cluster_entity=True)
                if CLRELIG in res_sole.params:
                    c, se, p = (res_sole.params[CLRELIG],
                                res_sole.std_errors[CLRELIG],
                                res_sole.pvalues[CLRELIG])
                    print(f"    {CLRELIG} (sole secularism): coef={c:.5f}  p={p:.4f}  {_sig(p)}")
                for var in res_sole.params.index:
                    results.append({
                        "tier":      "P5_B4_clrelig_sole",
                        "year":      "all",
                        "predictor": var,
                        "coef":      res_sole.params[var],
                        "se":        res_sole.std_errors[var],
                        "pval":      res_sole.pvalues[var],
                        "n":         res_sole.nobs,
                        "r2":        float(getattr(res_sole.rsquared, "within", res_sole.rsquared)),
                    })
            except Exception as e:
                print(f"    clrelig-only spec failed: {e}")
    else:
        print(f"    {CLRELIG} not found in dataset -- skipping.")

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 5 — LEGAL ORIGINS ROBUSTNESS  (La Porta et al. 1998, 2008)
# ═══════════════════════════════════════════════════════════════════════════════
def phase5_legal_origins(df: pd.DataFrame) -> list[dict]:
    """
    Test whether the religious courts effect survives controlling for legal family
    (La Porta et al. 1998, 2008).  Legal origin is time-invariant, so it is
    absorbed by country FE in the full panel model.  Two approaches:

      (a) Cross-sectional OLS (2014 & 2020) with legal origin dummies added —
          does the courts coefficient survive?
      (b) Panel FE sub-sample by legal family — does the effect hold within
          English-law vs French-law countries separately?
    """
    print(f"\n{'='*60}")
    print("PHASE 5 (add-on) -- LEGAL ORIGINS ROBUSTNESS  (La Porta et al.)")
    print(f"{'='*60}")
    print("  Legal origin is time-invariant -> absorbed by country FE in Tier 2.")
    print("  Tests: (a) cross-section with LO dummies; (b) panel FE by LO family.")

    if "legal_origin" not in df.columns:
        print(f"  WARNING: legal_origin not in df -- skipping (check {LO_PATH})")
        return []

    earliest_year = int(df["year"].min())
    n_matched = df[df["year"] == earliest_year]["legal_origin"].notna().sum()
    print(f"\n  Legal origin coverage ({earliest_year}): {n_matched} countries")
    print(f"  Distribution:\n" +
          df[df["year"] == earliest_year]["legal_origin"].value_counts().to_string())

    results = []

    # ── (a) Cross-sectional OLS with legal origin dummies ────────────────────
    print("\n  (a) Cross-section with legal origin dummies (French = reference):")
    for year in [2014, 2020]:
        sub = df[df["year"] == year].copy()
        pred_cols = GRI_PANEL_COLS + CONTROLS_GDP + LO_DUMMIES
        required  = [OUTCOME] + pred_cols
        s = sub.dropna(subset=required).copy()

        print(f"\n    Year={year}: N={len(s)}", end="")
        if len(s) < 30:
            print(" -- too few, skipping.")
            continue

        X = sm.add_constant(s[pred_cols])
        y = s[OUTCOME]
        model = sm.OLS(y, X).fit(cov_type="HC3")
        print(f"  R²={model.rsquared:.3f}")

        if FOCAL_PRED_LEGACY in model.params:
            c, se, p = (model.params[FOCAL_PRED_LEGACY],
                        model.bse[FOCAL_PRED_LEGACY],
                        model.pvalues[FOCAL_PRED_LEGACY])
            print(f"    {FOCAL_PRED_LEGACY}: coef={c:.5f}  se={se:.5f}  p={p:.4f}  {_sig(p)}")

        for var in model.params.index:
            results.append({
                "tier":      f"P5_legal_origins_cs_{year}",
                "year":      year,
                "predictor": var,
                "coef":      model.params[var],
                "se":        model.bse[var],
                "pval":      model.pvalues[var],
                "n":         int(model.nobs),
                "r2":        model.rsquared,
            })

    # ── (b) Panel FE sub-samples by legal family ─────────────────────────────
    print("\n  (b) Panel FE sub-samples by legal family (with GDP):")
    pred_cols = GRI_PANEL_COLS + CONTROLS_GDP

    for label, mask in [
        ("English-law",     df["legal_origin"] == "English"),
        ("French-law",      df["legal_origin"] == "French"),
        ("non-English-law", df["legal_origin"] != "English"),
    ]:
        sub = df[mask].copy()
        required = [OUTCOME, "iso3", "year"] + pred_cols
        sub = sub.dropna(subset=required).copy()
        n_ctry = sub["iso3"].nunique()
        print(f"\n    [{label}] N={len(sub):,} obs, {n_ctry} countries", end="")

        if len(sub) < 100 or n_ctry < 15:
            print(" -- too few, skipping.")
            continue

        sub_fe = sub.set_index(["iso3", "year"])
        y  = sub_fe[OUTCOME]
        X  = sm.add_constant(sub_fe[pred_cols])
        try:
            res = PanelOLS(y, X, entity_effects=True, time_effects=True).fit(
                cov_type="clustered", cluster_entity=True
            )
            if FOCAL_PRED_LEGACY in res.params:
                c, se, p = (res.params[FOCAL_PRED_LEGACY],
                            res.std_errors[FOCAL_PRED_LEGACY],
                            res.pvalues[FOCAL_PRED_LEGACY])
                print(f"  courts coef={c:.5f}  se={se:.5f}  p={p:.4f}  {_sig(p)}")
                results.append({
                    "tier":      f"P5_legal_origins_panel_{label.replace(' ', '_')}",
                    "year":      "all",
                    "predictor": FOCAL_PRED_LEGACY,
                    "coef":      c,
                    "se":        se,
                    "pval":      p,
                    "n":         int(res.nobs),
                    "r2":        float(getattr(res.rsquared, 'within', res.rsquared)),
                })
        except Exception as e:
            print(f" -- model failed: {e}")

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# VIF CHECK
# ═══════════════════════════════════════════════════════════════════════════════
def vif_check(df: pd.DataFrame):
    from statsmodels.stats.outliers_influence import variance_inflation_factor

    earliest_year = int(df["year"].min())
    print(f"\n{'='*60}")
    print(f"VIF CHECK — cross-sectional predictors ({earliest_year}, with GDP)")
    print(f"{'='*60}")

    sub = df[df["year"] == earliest_year].copy()
    cols = GRI_PANEL_COLS + CONTROLS_GDP
    sub = sub[cols].dropna()

    if sub.empty:
        print(f"  VIF check skipped: no observations in {earliest_year} cross-section")
        return

    X = sm.add_constant(sub).values
    vif_data = pd.DataFrame({
        "feature": ["const"] + cols,
        "VIF": [variance_inflation_factor(X, i) for i in range(X.shape[1])],
    })
    print(vif_data.to_string(index=False, float_format="{:.2f}".format))


# ── VIF + condition number PER T2 spec (headline diagnostic) ───────────────────
VIF_BY_SPEC_PATH = os.path.join(ROOT, "results/vif_by_spec.csv")


def vif_by_spec(df: pd.DataFrame) -> pd.DataFrame:
    """Compute VIF and design-matrix condition number for each T2 spec.

    Writes results/vif_by_spec.csv.
    """
    from statsmodels.stats.outliers_influence import variance_inflation_factor

    print(f"\n{'='*60}")
    print("VIF BY SPEC  (per-spec multicollinearity diagnostic)")
    print(f"{'='*60}")

    rows = []
    specs = [
        ("T2_gri_only",  GRI_PANEL_COLS),
        ("T2_gri_gdp",   GRI_PANEL_COLS + ["log_gdppc_norm"]),
        ("T2_no_gdp",    GRI_PANEL_COLS + CONTROLS),
        ("T2_with_gdp",  GRI_PANEL_COLS + CONTROLS_GDP),
    ]
    for label, cols in specs:
        sub = df[[OUTCOME] + cols].dropna()
        if sub.empty:
            continue
        X = sm.add_constant(sub[cols]).values
        # design matrix condition number
        try:
            cond_num = float(np.linalg.cond(X))
        except Exception:
            cond_num = np.nan
        for i, feat in enumerate(["const"] + cols):
            try:
                v = float(variance_inflation_factor(X, i))
            except Exception:
                v = np.nan
            rows.append({"spec": label, "feature": feat, "VIF": v,
                         "cond_num": cond_num, "n": len(sub)})
    out = pd.DataFrame(rows)
    out.to_csv(VIF_BY_SPEC_PATH, index=False, float_format="%.4f")
    print(f"  Wrote {VIF_BY_SPEC_PATH} ({len(out)} rows)")
    # print the WORST VIF per spec
    if not out.empty:
        worst = (out[out["feature"] != "const"]
                 .sort_values("VIF", ascending=False)
                 .groupby("spec").head(1)
                 .sort_values("spec"))
        print("\n  Worst-VIF feature per spec:")
        print(worst.to_string(index=False, float_format="{:.2f}".format))
    return out


# ── Robustness: headline T2 excluding interpolated WVS rows ───────────────────
WVS_NOINTERP_PATH = os.path.join(ROOT, "results/robustness_no_wvs_interp.csv")


def robustness_no_wvs_interp(df: pd.DataFrame) -> list[dict]:
    """Re-run T2_no_gdp and T2_with_gdp excluding rows where WVS values were
    linearly interpolated (wvs_interpolated == 1).

    Only meaningful if the current specs actually use WVS regressors, which
    T2_{no_gdp, with_gdp} do NOT — but many heterogeneity / Phase-5 specs do,
    and the focal-outcome panel is still affected via auxiliary columns merged
    from outcome_composite.csv. We report both for transparency.
    """
    print(f"\n{'='*60}")
    print("ROBUSTNESS -- exclude interpolated WVS rows (wvs_interpolated==1)")
    print(f"{'='*60}")

    if "wvs_interpolated" not in df.columns:
        print("  wvs_interpolated column not present; skipping.")
        return []

    mask_real = df["wvs_interpolated"].fillna(0).astype(float) == 0
    df_real = df[mask_real].copy()
    n_lost = len(df) - len(df_real)
    print(f"  Rows kept: {len(df_real):,} / {len(df):,}  "
          f"(dropped {n_lost:,} interpolated rows)")

    results = []
    for label, controls in [
        ("no_gdp",   CONTROLS),
        ("with_gdp", CONTROLS_GDP),
    ]:
        pred_cols = GRI_PANEL_COLS + controls
        sub = df_real[[OUTCOME, "iso3", "year"] + pred_cols].dropna(
            subset=[OUTCOME] + pred_cols).copy()
        if len(sub) < 100:
            print(f"  [{label}] too few obs after filter ({len(sub)}) — skipped")
            continue
        sub_idx = sub.set_index(["iso3", "year"])
        y = sub_idx[OUTCOME]
        X = sm.add_constant(sub_idx[pred_cols])
        try:
            res = PanelOLS(y, X, entity_effects=True, time_effects=True
                           ).fit(cov_type="clustered", cluster_entity=True)
        except Exception as e:
            print(f"  [{label}] fit failed: {e}")
            continue
        tag = f"ROB_no_wvs_interp_{label}"
        for var in res.params.index:
            if var in pred_cols:
                diag = _panel_diagnostics(sub, var)
                std_c = _std_coef(res.params[var], sub[var], sub[OUTCOME])
            else:
                diag = {"n_clusters": int(sub["iso3"].nunique()),
                        "n_changers": np.nan, "within_sd": np.nan}
                std_c = np.nan
            results.append({
                "tier": tag,
                "year": "all",
                "predictor": var,
                "coef": res.params[var],
                "se": res.std_errors[var],
                "pval": res.pvalues[var],
                "n": res.nobs,
                "r2": res.rsquared,
                "n_clusters": diag["n_clusters"],
                "n_changers": diag["n_changers"],
                "within_sd":  diag["within_sd"],
                "std_coef":   std_c,
                "se_type":    "cluster_entity",
                "valid":      True,
                "invalid_reason": "",
            })
    if results:
        pd.DataFrame(results).to_csv(WVS_NOINTERP_PATH, index=False,
                                      float_format="%.6f")
        print(f"  Wrote {WVS_NOINTERP_PATH} ({len(results)} rows)")
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 6 — ADVANCED ROBUSTNESS
# ═══════════════════════════════════════════════════════════════════════════════

LOO_PATH           = os.path.join(ROOT, "results/loo_jackknife.csv")
PLACEBO_PATH       = os.path.join(ROOT, "results/placebo.csv")
LOO_PATH_APO       = os.path.join(ROOT, "results/loo_jackknife_apostasy.csv")
PLACEBO_PATH_APO   = os.path.join(ROOT, "results/placebo_apostasy.csv")
# Item 2 (2026-04-15): preserve legacy courts + PCA robustness outputs
LOO_PATH_LEGACY     = os.path.join(ROOT, "results/loo_jackknife_religious_courts.csv")
PLACEBO_PATH_LEGACY = os.path.join(ROOT, "results/placebo_religious_courts.csv")
LOO_PATH_PCA        = os.path.join(ROOT, "results/loo_jackknife_pca.csv")
PLACEBO_PATH_PCA    = os.path.join(ROOT, "results/placebo_pca.csv")
# FOCAL_PRED imported from config


def phase6_within_variation(df: pd.DataFrame):
    """
    Variance decomposition for every GRI panel variable.

    Reports the fraction of total variance that is within-country (over time)
    vs between-country.  The panel FE estimator is identified solely from
    within-country variation, so a low within-fraction means the FE coefficient
    is estimated from very little actual change.
    """
    print(f"\n{'='*60}")
    print("PHASE 6a -- WITHIN-COUNTRY VARIANCE DECOMPOSITION")
    print(f"{'='*60}")
    print("  Panel FE is identified only from within-country changes.")
    print("  Variables with low within-fraction have thin identifying variation.")
    print()

    rows = []
    for col in GRI_PANEL_COLS + CONTROLS + ["log_gdppc_norm", OUTCOME]:
        sub = df[["iso3", "year", col]].dropna()
        overall_sd = sub[col].std()
        between_sd = sub.groupby("iso3")[col].mean().std()
        # Within SD: SD of (x_it - x_i_bar) across all obs
        sub = sub.copy()
        sub["_dm"] = sub[col] - sub.groupby("iso3")[col].transform("mean")
        within_sd  = sub["_dm"].std()
        n_zero     = (sub.groupby("iso3")[col].std().fillna(0) < 1e-6).sum()
        within_pct = 100 * within_sd / overall_sd if overall_sd > 0 else 0

        rows.append({
            "variable":   col,
            "overall_sd": overall_sd,
            "between_sd": between_sd,
            "within_sd":  within_sd,
            "within_pct": within_pct,
            "n_zero_var": n_zero,
            "n_countries": sub["iso3"].nunique(),
        })
        print(f"  {col:<35s}  within={within_pct:5.1f}%  "
              f"(between SD={between_sd:.3f}, within SD={within_sd:.3f}, "
              f"{n_zero} countries with zero within-variation)")

    return pd.DataFrame(rows)


def phase6_loo_jackknife(df: pd.DataFrame, focal_pred: str = FOCAL_PRED,
                         out_path: str = LOO_PATH) -> pd.DataFrame:
    """
    Leave-one-country-out jackknife for the panel FE model.

    For each of the ~170 countries, drops it from the panel and re-estimates
    Tier 2 (with GDP).  Records the coefficient on FOCAL_PRED (religious courts)
    for each run.

    Key questions:
      - Does the sign ever flip?
      - Does the estimate remain significant across all runs?
      - Which countries are most influential?
    """
    print(f"\n{'='*60}")
    print(f"PHASE 6b -- LEAVE-ONE-OUT JACKKNIFE (panel FE, {focal_pred})")
    print(f"{'='*60}")

    # Item 2 (2026-04-15): focal-pred-aware predictor set. If focal_pred is
    # the composite (not in GRI_PANEL_COLS), use standalone spec to avoid
    # multicollinearity; otherwise keep the GRI decomposition spec.
    pred_cols = _preds_for_focal(focal_pred, CONTROLS_GDP)
    required  = [OUTCOME, "iso3", "year"] + pred_cols
    base = df[required].dropna(subset=[OUTCOME] + pred_cols).copy()

    countries = sorted(base["iso3"].unique())
    print(f"  Running {len(countries)} LOO iterations on N={len(base):,} obs ...")

    # Baseline (full sample) — replicate T2_with_gdp
    pan = base.set_index(["iso3", "year"])
    y_full = pan[OUTCOME]
    X_full = sm.add_constant(pan[pred_cols])
    res_full = PanelOLS(y_full, X_full, entity_effects=True, time_effects=True).fit(
        cov_type="clustered", cluster_entity=True
    )
    base_coef  = res_full.params[focal_pred]
    base_se    = res_full.std_errors[focal_pred]
    base_pval  = res_full.pvalues[focal_pred]
    print(f"\n  Baseline: coef={base_coef:.5f}, se={base_se:.5f}, p={base_pval:.4f}")

    loo_rows = []
    n_sig_flipped = 0    # runs where sign flips vs baseline
    n_insig       = 0    # runs where p >= 0.05

    for iso in countries:
        sub = base[base["iso3"] != iso].copy()
        pan = sub.set_index(["iso3", "year"])
        y = pan[OUTCOME]
        X = sm.add_constant(pan[pred_cols])
        try:
            res = PanelOLS(y, X, entity_effects=True, time_effects=True).fit(
                cov_type="clustered", cluster_entity=True
            )
            coef = res.params[focal_pred]
            se   = res.std_errors[focal_pred]
            pval = res.pvalues[focal_pred]
        except Exception:
            coef, se, pval = np.nan, np.nan, np.nan

        if np.sign(coef) != np.sign(base_coef):
            n_sig_flipped += 1
        if pval >= 0.05:
            n_insig += 1

        # Get country name from df
        name_row = df[df["iso3"] == iso]["country"].dropna()
        name = name_row.iloc[0] if len(name_row) else iso

        loo_rows.append({
            "iso3": iso, "country": name,
            "coef": coef, "se": se, "pval": pval,
            "sig": _sig(pval) if not np.isnan(pval) else "",
            "coef_change": coef - base_coef,
        })

    loo_df = pd.DataFrame(loo_rows).sort_values("coef")

    print(f"\n  LOO summary (N={len(loo_df)} runs):")
    print(f"    Baseline coef       : {base_coef:.5f}")
    print(f"    LOO coef range      : [{loo_df['coef'].min():.5f}, {loo_df['coef'].max():.5f}]")
    print(f"    LOO coef mean (SD)  : {loo_df['coef'].mean():.5f} ({loo_df['coef'].std():.5f})")
    print(f"    Sign flips          : {n_sig_flipped} / {len(loo_df)}")
    print(f"    Runs with p >= 0.05 : {n_insig} / {len(loo_df)}")

    # Most influential countries (largest absolute coef change)
    print(f"\n  Top 10 most influential countries (dropping raises/lowers coef most):")
    top10 = loo_df.reindex(loo_df["coef_change"].abs().nlargest(10).index)
    print(top10[["iso3", "country", "coef", "pval", "coef_change", "sig"]]
          .to_string(index=False, float_format="{:.5f}".format))

    loo_df["base_coef"] = base_coef
    loo_df["base_se"]   = base_se
    loo_df.to_csv(out_path, index=False, float_format="%.6f")
    print(f"\n  LOO results saved -> {out_path}")

    # ── Structured summary + tornado plot ──────────────────────────────────
    try:
        loo_summarise(loo_df, focal_pred=focal_pred, source_path=out_path)
    except Exception as e:
        print(f"  [LOO summarise failed: {e}]")

    return loo_df


def loo_summarise(loo_df: pd.DataFrame, focal_pred: str,
                  source_path: str) -> None:
    """Produce a one-line summary CSV row and a tornado PNG for a LOO run.

    Summary CSV path: results/loo_jackknife_summary.csv  (one row per call,
    appended / overwritten keyed on (focal_pred, source_path)).
    Tornado PNG path: figures/loo_tornado_<focal>.png
    """
    summary_path = os.path.join(ROOT, "results/loo_jackknife_summary.csv")
    fig_dir = os.path.join(ROOT, "figures")
    os.makedirs(fig_dir, exist_ok=True)

    if loo_df.empty or "coef" not in loo_df.columns:
        print("  [LOO summarise: empty df, nothing to do]")
        return
    base_coef = float(loo_df["base_coef"].iloc[0]) if "base_coef" in loo_df else np.nan
    base_se   = float(loo_df["base_se"].iloc[0])   if "base_se"   in loo_df else np.nan
    coef_min  = float(loo_df["coef"].min())
    coef_max  = float(loo_df["coef"].max())
    n_sign_flip = int((np.sign(loo_df["coef"]) != np.sign(base_coef)).sum()) \
        if not np.isnan(base_coef) else np.nan
    n_insig = int((loo_df["pval"] >= 0.05).sum())
    # largest absolute Δ-coef row
    idx_worst = loo_df["coef_change"].abs().idxmax()
    worst_country = loo_df.loc[idx_worst, "country"] if "country" in loo_df else ""
    worst_iso3    = loo_df.loc[idx_worst, "iso3"]    if "iso3" in loo_df    else ""
    worst_delta   = float(loo_df.loc[idx_worst, "coef_change"])
    row = {
        "focal_pred": focal_pred,
        "source": os.path.basename(source_path),
        "n_loo_runs": int(len(loo_df)),
        "base_coef": base_coef,
        "base_se": base_se,
        "coef_min": coef_min,
        "coef_max": coef_max,
        "coef_mean": float(loo_df["coef"].mean()),
        "coef_sd":   float(loo_df["coef"].std()),
        "n_sign_flips": n_sign_flip,
        "n_p_ge_05":   n_insig,
        "worst_country": worst_country,
        "worst_iso3":    worst_iso3,
        "worst_delta":   worst_delta,
    }
    if os.path.exists(summary_path):
        prev = pd.read_csv(summary_path)
        prev = prev[~((prev["focal_pred"] == focal_pred)
                      & (prev["source"] == os.path.basename(source_path)))]
        out = pd.concat([prev, pd.DataFrame([row])], ignore_index=True)
    else:
        out = pd.DataFrame([row])
    out.to_csv(summary_path, index=False, float_format="%.6f")
    print(f"  LOO summary appended -> {summary_path}")

    # Tornado plot: Δcoef per country, sorted
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plot_df = loo_df.copy().sort_values("coef_change")
        labels = plot_df["iso3"].astype(str).values
        deltas = plot_df["coef_change"].astype(float).values
        fig_h = max(4.0, 0.12 * len(plot_df))
        fig, ax = plt.subplots(figsize=(7, fig_h))
        colors = ["#c0392b" if d < 0 else "#2980b9" for d in deltas]
        ax.barh(range(len(plot_df)), deltas, color=colors)
        ax.axvline(0, color="k", lw=0.7)
        ax.set_yticks(range(len(plot_df)))
        ax.set_yticklabels(labels, fontsize=5)
        ax.set_xlabel(f"Δ coef on {focal_pred} (LOO − baseline)")
        ax.set_title(f"LOO jackknife tornado: {focal_pred}\n"
                     f"baseline {base_coef:+.4f}")
        ax.grid(axis="x", ls=":", alpha=0.5)
        fig.tight_layout()
        slug = focal_pred.replace("gri_", "").replace("_norm", "")
        fig_path = os.path.join(fig_dir, f"loo_tornado_{slug}.png")
        fig.savefig(fig_path, dpi=120)
        plt.close(fig)
        print(f"  LOO tornado plot -> {fig_path}")
    except Exception as e:
        print(f"  [tornado plot failed: {e}]")


def phase6_placebo_outcomes(df: pd.DataFrame, focal_pred: str = FOCAL_PRED,
                            placebo_path: str = PLACEBO_PATH) -> list[dict]:
    """
    Placebo test: re-run panel FE with male-equivalent DVs.

    If religious courts predict MALE life expectancy and MALE labour-force
    participation as strongly as female equivalents, the mechanism is not
    specifically gendered -- it just reflects general underdevelopment.
    The null hypothesis for a genuine gender mechanism:
      |coef_female| >> |coef_male|
    """
    print(f"\n{'='*60}")
    print("PHASE 6c -- PLACEBO OUTCOME TEST (male equivalents)")
    print(f"{'='*60}")
    print("  Hypothesis: if effect is gendered, religious courts should")
    print("  predict female outcomes more strongly than male equivalents.")

    # Load male variables from QoG raw
    print("\n  Loading male outcome variables from QoG raw...")
    raw = pd.read_csv(
        QOG_RAW,
        usecols=["ccodealp", "year", "wdi_lifexpm", "wdi_lfpmilo15"],
        low_memory=False,
    )
    raw = raw.rename(columns={
        "ccodealp":    "iso3",
        "wdi_lifexpm": "lifexpm_raw",
        "wdi_lfpmilo15": "lfpm_raw",
    })

    # Robust min-max normalise to match scale of female equivalents
    for col in ["lifexpm_raw", "lfpm_raw"]:
        raw[col.replace("_raw", "_norm")] = robust_minmax(raw[col].where(raw[col] > 0))
    male_df = raw[["iso3", "year", "lifexpm_norm", "lfpm_norm"]].copy()
    df_male = df.merge(male_df, on=["iso3", "year"], how="left")

    print(f"  lifexpm obs: {df_male['lifexpm_norm'].notna().sum():,}")
    print(f"  lfpm obs:    {df_male['lfpm_norm'].notna().sum():,}")

    results = []
    # Item 2 (2026-04-15): focal-pred-aware predictor set
    pred_cols = _preds_for_focal(focal_pred, CONTROLS_GDP)

    # Female equivalents in the dataset (from women_treatment_index components)
    _candidate_female_dvs = {
        "wdi_lifexpf_norm": "Female life expectancy (female DV)",
        "wdi_lfpf_norm":    "Female LFP rate (female DV)",
        OUTCOME:            "Women's treatment index (female DV)",
    }
    female_dvs = {k: v for k, v in _candidate_female_dvs.items() if k in df.columns}
    male_dvs = {
        "lifexpm_norm": "Male life expectancy (placebo DV)",
        "lfpm_norm":    "Male LFP rate (placebo DV)",
    }

    all_dvs = {**female_dvs, **male_dvs}
    dv_source = {**{k: df for k in female_dvs}, **{k: df_male for k in male_dvs}}

    for dv, label in all_dvs.items():
        source = dv_source[dv]
        required = [dv, "iso3", "year"] + pred_cols
        panel = source[required].dropna(subset=[dv] + pred_cols).copy()

        if len(panel) < 100:
            print(f"  {label}: too few obs ({len(panel)}) -- skipping")
            continue

        pan = panel.set_index(["iso3", "year"])
        y = pan[dv]
        X = sm.add_constant(pan[pred_cols])

        try:
            res = PanelOLS(y, X, entity_effects=True, time_effects=True).fit(
                cov_type="clustered", cluster_entity=True
            )
            coef = res.params[focal_pred]
            se   = res.std_errors[focal_pred]
            pval = res.pvalues[focal_pred]
            print(f"  {label:<45s}: {focal_pred} coef={coef:+.5f}  se={se:.5f}  p={pval:.4f}  {_sig(pval)}")

            for var in res.params.index:
                results.append({
                    "tier":      f"P6_placebo_{dv}",
                    "year":      "all",
                    "predictor": var,
                    "dv_label":  label,
                    "coef":      res.params[var],
                    "se":        res.std_errors[var],
                    "pval":      res.pvalues[var],
                    "n":         res.nobs,
                    "r2":        res.rsquared,
                })
        except Exception as e:
            print(f"  {label}: panel FE failed: {e}")

    # Save focal-predictor rows separately for easy plotting
    plac_df = pd.DataFrame(results)
    if not plac_df.empty:
        plac_df["sig"] = plac_df["pval"].apply(_sig)
        focal = plac_df[plac_df["predictor"] == focal_pred].copy()
        focal.to_csv(placebo_path, index=False, float_format="%.6f")
        print(f"\n  Placebo focal results saved -> {placebo_path}")

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 7 — CEDAW CONTROL, SUB-PERIOD / CHANGERS, OSTER DELTA
# ═══════════════════════════════════════════════════════════════════════════════

SPEC_PATH        = os.path.join(ROOT, "results/spec_ladder.csv")
SPEC_PATH_APO    = os.path.join(ROOT, "results/spec_ladder_apostasy.csv")
# Item 2 (2026-04-15): legacy courts + PCA robustness spec ladders
SPEC_PATH_LEGACY = os.path.join(ROOT, "results/spec_ladder_religious_courts.csv")
SPEC_PATH_PCA    = os.path.join(ROOT, "results/spec_ladder_pca.csv")

# Extended controls including CEDAW
CONTROLS_CEDAW = CONTROLS_GDP + ["cedaw_years_since_norm"]


def _run_panel_fe(df: pd.DataFrame, pred_cols: list[str],
                  outcome: str = OUTCOME, label: str = "") -> dict | None:
    """
    Fit a single PanelOLS model and return a result dict for FOCAL_PRED.
    Returns None if insufficient observations.
    """
    required = [outcome, "iso3", "year"] + pred_cols
    sub = df[required].dropna(subset=[outcome] + pred_cols).copy()
    if len(sub) < 100 or sub["iso3"].nunique() < 20:
        print(f"    [{label}] Too few obs ({len(sub)}) -- skipping.")
        return None

    pan = sub.set_index(["iso3", "year"])
    y = pan[outcome]
    X = sm.add_constant(pan[pred_cols])
    try:
        res = PanelOLS(y, X, entity_effects=True, time_effects=True).fit(
            cov_type="clustered", cluster_entity=True
        )
        return {
            "label":  label,
            "coef":   res.params[FOCAL_PRED_LEGACY],
            "se":     res.std_errors[FOCAL_PRED_LEGACY],
            "pval":   res.pvalues[FOCAL_PRED_LEGACY],
            "n_obs":  res.nobs,
            "n_ctry": sub["iso3"].nunique(),
            "r2":     res.rsquared,
        }
    except Exception as e:
        print(f"    [{label}] Panel FE failed: {e}")
        return None


def phase7_cedaw_and_subsamples(df: pd.DataFrame) -> list[dict]:
    """
    Three analyses in one:

    (A) CEDAW control — add cedaw_years_since_norm to all three tiers.
        Tests whether CEDAW ratification confounds the courts finding.

    (B) Sub-period check (2008-2019) — drops 2007 (thin coverage) and the
        COVID years 2020-2022. Panel is already near-balanced within this
        window; tests temporal stability of the main finding.

    (C) Changers-only subsample — restricts to the ~47 countries where
        gri_religious_courts_norm has within-country SD > 0.02, i.e. countries
        that actually changed their religious court score during the panel.
        This is the most direct identification test: among movers, do courts
        changes predict worse outcomes?
    """
    results = []

    print(f"\n{'='*60}")
    print("PHASE 7 -- CEDAW, SUB-PERIOD, AND CHANGERS SUBSAMPLE")
    print(f"{'='*60}")

    # ── (A) CEDAW control ──────────────────────────────────────────────────────
    print("\n  [7A] Adding CEDAW years as control to panel FE")
    pred_cedaw = GRI_PANEL_COLS + CONTROLS_CEDAW
    required   = [OUTCOME, "iso3", "year"] + pred_cedaw
    sub = df[required].dropna(subset=[OUTCOME] + pred_cedaw).copy()
    print(f"       N={len(sub):,} obs, {sub['iso3'].nunique()} countries")

    if len(sub) >= 100:
        pan = sub.set_index(["iso3", "year"])
        y = pan[OUTCOME]
        X = sm.add_constant(pan[pred_cedaw])
        try:
            res = PanelOLS(y, X, entity_effects=True, time_effects=True).fit(
                cov_type="clustered", cluster_entity=True
            )
            print(res.summary)
            courts_r = res.params[FOCAL_PRED_LEGACY]
            courts_p = res.pvalues[FOCAL_PRED_LEGACY]
            cedaw_r  = res.params.get("cedaw_years_since_norm", np.nan)
            cedaw_p  = res.pvalues.get("cedaw_years_since_norm", np.nan)
            print(f"\n  Key result: courts coef={courts_r:.5f} p={courts_p:.4f} {_sig(courts_p)}")
            print(f"  CEDAW years coef={cedaw_r:.5f} p={cedaw_p:.4f} {_sig(cedaw_p)}")
            for var in res.params.index:
                results.append({
                    "tier": "T2_with_cedaw",
                    "year": "all",
                    "predictor": var,
                    "coef": res.params[var],
                    "se":   res.std_errors[var],
                    "pval": res.pvalues[var],
                    "n":    res.nobs,
                    "r2":   res.rsquared,
                })
        except Exception as e:
            print(f"  CEDAW panel FE failed: {e}")

    # Also add CEDAW to T1 cross-section
    earliest_year = int(df["year"].min())
    print(f"\n  [7A-T1] CEDAW in cross-section ({earliest_year})")
    cs = df[df["year"] == earliest_year].copy()
    pred_cs = GRI_PANEL_COLS + CONTROLS_CEDAW
    s = cs.dropna(subset=[OUTCOME] + pred_cs).copy()
    print(f"       N={len(s)}")
    if len(s) >= 30:
        model = sm.OLS(s[OUTCOME], sm.add_constant(s[pred_cs])).fit(cov_type="HC3")
        ced_p = model.pvalues.get("cedaw_years_since_norm", np.nan)
        print(f"  CEDAW coef={model.params.get('cedaw_years_since_norm',np.nan):.5f} p={ced_p:.4f} {_sig(ced_p)}")
        for var in model.params.index:
            results.append({
                "tier": "T1_with_cedaw",
                "year": earliest_year,
                "predictor": var,
                "coef": model.params[var],
                "se":   model.bse[var],
                "pval": model.pvalues[var],
                "n":    int(model.nobs),
                "r2":   model.rsquared,
            })

    # ── (B) Sub-period: 2008-2019 ──────────────────────────────────────────────
    print("\n  [7B] Sub-period panel FE (2013-2019, pre-COVID)")
    sub_period = df[(df["year"] >= 2013) & (df["year"] <= 2019)].copy()
    pred_cols  = GRI_PANEL_COLS + CONTROLS_GDP
    sp_sub     = sub_period[[OUTCOME, "iso3", "year"] + pred_cols].dropna(
        subset=[OUTCOME] + pred_cols
    ).copy()
    print(f"       N={len(sp_sub):,} obs, {sp_sub['iso3'].nunique()} countries, "
          f"years 2013-2019")
    if len(sp_sub) >= 100:
        pan = sp_sub.set_index(["iso3", "year"])
        y = pan[OUTCOME]
        X = sm.add_constant(pan[pred_cols])
        try:
            res = PanelOLS(y, X, entity_effects=True, time_effects=True).fit(
                cov_type="clustered", cluster_entity=True
            )
            print(res.summary)
            courts_r = res.params[FOCAL_PRED_LEGACY]
            courts_p = res.pvalues[FOCAL_PRED_LEGACY]
            print(f"\n  Key result: courts coef={courts_r:.5f} p={courts_p:.4f} {_sig(courts_p)}")
            for var in res.params.index:
                results.append({
                    "tier": "T2_subperiod_2008_2019",
                    "year": "2008-2019",
                    "predictor": var,
                    "coef": res.params[var],
                    "se":   res.std_errors[var],
                    "pval": res.pvalues[var],
                    "n":    res.nobs,
                    "r2":   res.rsquared,
                })
        except Exception as e:
            print(f"  Sub-period panel FE failed: {e}")

    # ── (C) Changers-only subsample ────────────────────────────────────────────
    print("\n  [7C] Changers-only panel FE (countries where courts SD > 0.02)")
    pred_cols = GRI_PANEL_COLS + CONTROLS_GDP
    required  = [OUTCOME, "iso3", "year"] + pred_cols
    base = df[required].dropna(subset=[OUTCOME] + pred_cols).copy()

    courts_sd   = base.groupby("iso3")[FOCAL_PRED_LEGACY].std().fillna(0)
    changers    = courts_sd[courts_sd > 0.02].index.tolist()
    non_changers = courts_sd[courts_sd <= 0.02].index.tolist()

    ch_sub  = base[base["iso3"].isin(changers)].copy()
    nch_sub = base[base["iso3"].isin(non_changers)].copy()

    print(f"       Changers: {len(changers)} countries, {len(ch_sub):,} obs")
    print(f"       Non-changers: {len(non_changers)} countries (excluded -- entity FE")
    print(f"       absorbs all within-country courts variation for non-movers)")

    for sub_name, sub_data, tier_tag in [
        ("changers", ch_sub, "T2_changers_only"),
    ]:
        if len(sub_data) < 100 or sub_data["iso3"].nunique() < 10:
            print(f"  {sub_name}: too few obs -- skipping")
            continue
        pan = sub_data.set_index(["iso3", "year"])
        y = pan[OUTCOME]
        X = sm.add_constant(pan[pred_cols])
        try:
            res = PanelOLS(y, X, entity_effects=True, time_effects=True).fit(
                cov_type="clustered", cluster_entity=True
            )
            print(res.summary)
            courts_r = res.params[FOCAL_PRED_LEGACY]
            courts_p = res.pvalues[FOCAL_PRED_LEGACY]
            print(f"\n  [{sub_name}] courts coef={courts_r:.5f} p={courts_p:.4f} {_sig(courts_p)}")
            for var in res.params.index:
                results.append({
                    "tier": tier_tag,
                    "year": "all",
                    "predictor": var,
                    "coef": res.params[var],
                    "se":   res.std_errors[var],
                    "pval": res.pvalues[var],
                    "n":    res.nobs,
                    "r2":   res.rsquared,
                })
        except Exception as e:
            print(f"  {sub_name} panel FE failed: {e}")

    return results


def phase7_oster_delta(df: pd.DataFrame, focal_pred: str = FOCAL_PRED,
                       out_path: str = SPEC_PATH) -> pd.DataFrame:
    """
    Oster (2019) coefficient stability test for the religious courts finding.

    Compares two panel FE models on a common estimation sample:
      Restricted: courts only (bivariate) + entity/year FE
      Full:       courts + all controls (GRI vars, institutions, GDP) + entity/year FE

    Computes delta = the ratio of selection on unobservables to selection on
    observables required to fully explain away the courts coefficient.
    Threshold: delta >= 1 means robust.

    Formula:
      delta = beta_full * (R_full - R_restricted) /
              ((beta_restricted - beta_full) * (Rmax - R_full))

    Two Rmax values are reported:
      Rmax = min(2.2 * R_full, 1)   -- Oster's recommended default
      Rmax = 1.0                     -- most conservative bound

    Note: Rmax = 1.0 is implausible for panel FE with entity effects, where
    the maximum achievable within-R² is far below 1.  Rmax = 2.2*R_full is
    the appropriate benchmark for this design.
    """
    print(f"\n{'='*60}")
    print("PHASE 7 -- OSTER (2019) COEFFICIENT STABILITY")
    print(f"{'='*60}")
    print("  Comparing: bivariate (courts only) vs full model (GDP-controlled)")
    print("  Common estimation sample used for both models.")
    print("  Null: beta* = 0.  Threshold: delta >= 1 means robust.")
    print()

    # Establish common sample: rows non-missing for ALL variables in full model.
    # Item 2 (2026-04-15): focal-pred-aware full spec. For composite focal,
    # full_preds = [composite] + CONTROLS_GDP (standalone headline); for
    # GRI-item focal, full_preds = GRI_PANEL_COLS + CONTROLS_GDP (includes focal).
    full_preds = _preds_for_focal(focal_pred, CONTROLS_GDP)
    required   = [OUTCOME, "iso3", "year"] + full_preds
    base = df[required].dropna(subset=[OUTCOME] + full_preds).copy()
    print(f"  Common sample: N={len(base):,} obs, {base['iso3'].nunique()} countries")

    results = []
    for spec_label, pred_cols in [
        (f"Bivariate ({focal_pred})", [focal_pred]),
        ("Full model (GDP-controlled)", full_preds),
    ]:
        pan = base.set_index(["iso3", "year"])
        y = pan[OUTCOME]
        X = sm.add_constant(pan[pred_cols])
        try:
            res = PanelOLS(y, X, entity_effects=True, time_effects=True).fit(
                cov_type="clustered", cluster_entity=True
            )
        except Exception as e:
            print(f"  [{spec_label}] failed: {e}")
            continue
        results.append({
            "spec":  spec_label,
            "coef":  res.params[focal_pred],
            "se":    res.std_errors[focal_pred],
            "pval":  res.pvalues[focal_pred],
            "r2":    res.rsquared,
            "n_obs": res.nobs,
        })
        print(f"  {spec_label}: coef={res.params[focal_pred]:.5f}  "
              f"se={res.std_errors[focal_pred]:.5f}  p={res.pvalues[focal_pred]:.4f}  "
              f"within-R2={res.rsquared:.4f}")

    oster_df = pd.DataFrame(results)

    if len(oster_df) == 2:
        beta_r = oster_df.iloc[0]["coef"]   # bivariate
        R_r    = oster_df.iloc[0]["r2"]
        beta_f = oster_df.iloc[1]["coef"]   # full
        R_f    = oster_df.iloc[1]["r2"]

        print()
        for rmax_label, Rmax in [
            ("Rmax = 2.2 x R_full (recommended)", min(2.2 * R_f, 1.0)),
            ("Rmax = 1.0 (conservative bound)",   1.0),
        ]:
            denom = (beta_r - beta_f) * (Rmax - R_f)
            if abs(denom) > 1e-10 and abs(R_f - R_r) > 1e-10:
                delta = beta_f * (R_f - R_r) / denom
                if delta < 0:
                    verdict = "ROBUST (negative delta: coefficient strengthens with controls)"
                elif delta > 50:
                    verdict = (f"CAUTION (delta = {delta:.1f}; beta barely changes "
                               "with controls, ratio is numerically unstable)")
                elif delta >= 1:
                    verdict = "ROBUST (delta >= 1)"
                else:
                    verdict = "not robust (delta < 1)"
                print(f"  {rmax_label}: delta = {delta:.3f}  ->  {verdict}")
                oster_df.loc[1, f"delta_{rmax_label[:10].replace(' ','_')}"] = delta
            else:
                print(f"  {rmax_label}: delta = undefined")

    return oster_df


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 8 — COUNTRY-SPECIFIC LINEAR TIME TRENDS + LO INTERACTION
# ═══════════════════════════════════════════════════════════════════════════════

def _detrend_within_country(df: pd.DataFrame, cols: list,
                             group_col: str = "iso3",
                             year_col:  str = "year") -> pd.DataFrame:
    """Remove within-country linear time trends from specified columns.

    For each country regresses col_it on (1, year_c) and returns residuals
    as col+'_dt'.  Countries with < 3 non-missing obs are centred by mean only.
    Equivalent to the Frisch-Waugh partial-out of country-specific linear trends
    before running panel FE.
    """
    df = df.copy()
    yr_mean = df[year_col].mean()
    df["_yr_c"] = df[year_col] - yr_mean

    for col in cols:
        dt_col = col + "_dt"
        df[dt_col] = np.nan
        for iso3, grp in df.groupby(group_col):
            idx  = grp.index
            yr   = grp["_yr_c"].values
            vals = grp[col].values
            mask = ~np.isnan(vals)
            if mask.sum() >= 3:
                X_fit = np.column_stack([np.ones(mask.sum()), yr[mask]])
                b, _, _, _ = np.linalg.lstsq(X_fit, vals[mask], rcond=None)
                resids = np.full(len(vals), np.nan)
                resids[mask] = vals[mask] - (b[0] + b[1] * yr[mask])
                df.loc[idx, dt_col] = resids
            elif mask.sum() >= 1:
                resids = np.full(len(vals), np.nan)
                resids[mask] = vals[mask] - vals[mask].mean()
                df.loc[idx, dt_col] = resids

    return df.drop(columns=["_yr_c"])


def phase8_country_trends(df: pd.DataFrame) -> list[dict]:
    """Panel FE with country-specific linear time trends.

    Partials out within-country linear year trends from outcome and all
    predictors (Frisch-Waugh theorem) before running two-way panel FE.
    The courts coefficient is then identified purely from non-linear
    within-country variation -- i.e. it cannot be explained by a country
    that is simultaneously secularising and improving women's outcomes
    along a simple linear path.  This is the most demanding robustness
    check for the parallel-trends / confounding critique.
    """
    print(f"\n{'='*60}")
    print("PHASE 8a -- COUNTRY-SPECIFIC LINEAR TIME TRENDS")
    print(f"{'='*60}")
    print("  Frisch-Waugh partial-out of within-country linear year trends.")
    print("  Coefficient identified from non-linear within-country variation only.")

    results   = []
    pred_cols = GRI_PANEL_COLS + CONTROLS_GDP
    required  = [OUTCOME, "iso3", "year"] + pred_cols
    sub = df[required].dropna(subset=[OUTCOME] + pred_cols).copy()
    print(f"  N = {len(sub):,} obs, {sub['iso3'].nunique()} countries (before detrending)")

    sub_dt     = _detrend_within_country(sub, [OUTCOME] + pred_cols)
    dt_outcome = OUTCOME + "_dt"
    dt_preds   = [c + "_dt" for c in pred_cols]
    name_map   = dict(zip(dt_preds, pred_cols))

    sub_dt = sub_dt.dropna(subset=[dt_outcome] + dt_preds)
    n_ctry = sub_dt["iso3"].nunique()
    print(f"  N = {len(sub_dt):,} obs after detrending, {n_ctry} countries")

    if len(sub_dt) < 100:
        print("  Too few observations -- skipping.")
        return results

    try:
        sub_dt_fe = sub_dt.set_index(["iso3", "year"])
        y = sub_dt_fe[dt_outcome]
        X = sm.add_constant(sub_dt_fe[dt_preds])
        res = PanelOLS(y, X, entity_effects=True, time_effects=True).fit(
            cov_type="clustered", cluster_entity=True
        )
        focal_dt = FOCAL_PRED_LEGACY + "_dt"
        if focal_dt in res.params:
            c, se, p = res.params[focal_dt], res.std_errors[focal_dt], res.pvalues[focal_dt]
            print(f"\n  {FOCAL_PRED_LEGACY}: coef={c:.5f}  se={se:.5f}  p={p:.4f}  {_sig(p)}")
        print(res.summary)

        for var in res.params.index:
            results.append({
                "tier":      "P8a_country_linear_trends",
                "year":      "all",
                "predictor": name_map.get(var, var),
                "coef":      res.params[var],
                "se":        res.std_errors[var],
                "pval":      res.pvalues[var],
                "n":         res.nobs,
                "r2":        float(getattr(res.rsquared, "within", res.rsquared)),
            })
    except Exception as e:
        print(f"  Country trends FE failed: {e}")

    return results


def phase8_lo_interaction(df: pd.DataFrame) -> list[dict]:
    """Panel FE with legal origin x courts interaction.

    legal_origin is time-invariant, so lo_english and lo_socialist are absorbed
    by entity fixed effects.  But courts_norm x lo_english IS time-varying
    (because courts changes within countries) and IS identified in panel FE.
    The interaction coefficient tests whether the within-country effect of
    religious courts differs between English-law and French/civil-law countries.
    """
    if "legal_origin" not in df.columns:
        print("  WARNING: legal_origin not in df -- skipping LO interaction")
        return []

    print(f"\n{'='*60}")
    print("PHASE 8b -- LEGAL ORIGIN x COURTS INTERACTION (Panel FE)")
    print(f"{'='*60}")
    print("  lo_* absorbed by entity FE; courts x lo_* is time-varying -> identified.")

    results   = []
    pred_cols = GRI_PANEL_COLS + CONTROLS_GDP
    required  = [OUTCOME, "iso3", "year", "lo_english", "lo_socialist"] + pred_cols
    sub = df[required].dropna(subset=[OUTCOME] + pred_cols).copy()

    sub["courts_x_english"]   = sub[FOCAL_PRED_LEGACY] * sub["lo_english"]
    sub["courts_x_socialist"] = sub[FOCAL_PRED_LEGACY] * sub["lo_socialist"]
    interaction_cols = ["courts_x_english", "courts_x_socialist"]
    full_preds       = pred_cols + interaction_cols

    print(f"  N={len(sub):,} obs, {sub['iso3'].nunique()} countries")

    try:
        sub_fe = sub.set_index(["iso3", "year"])
        y = sub_fe[OUTCOME]
        X = sm.add_constant(sub_fe[full_preds])
        res = PanelOLS(y, X, entity_effects=True, time_effects=True).fit(
            cov_type="clustered", cluster_entity=True
        )
        print(res.summary)
        print("\n  Key interaction terms:")
        for var in [FOCAL_PRED_LEGACY] + interaction_cols:
            if var in res.params:
                c, se, p = res.params[var], res.std_errors[var], res.pvalues[var]
                print(f"    {var:<35s} coef={c:.5f}  se={se:.5f}  p={p:.4f}  {_sig(p)}")

        for var in res.params.index:
            results.append({
                "tier":      "P8b_lo_interaction",
                "year":      "all",
                "predictor": var,
                "coef":      res.params[var],
                "se":        res.std_errors[var],
                "pval":      res.pvalues[var],
                "n":         res.nobs,
                "r2":        float(getattr(res.rsquared, "within", res.rsquared)),
            })
    except Exception as e:
        print(f"  LO interaction panel FE failed: {e}")

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 9 — METHODOLOGICAL IMPROVEMENTS
# ═══════════════════════════════════════════════════════════════════════════════

def _clustered_se(X: np.ndarray, e: np.ndarray, clusters: np.ndarray) -> np.ndarray:
    """CR1 clustered sandwich standard errors (no constant column required).

    Parameters
    ----------
    X        : (n, k) design matrix (already demeaned; no constant)
    e        : (n,) residual vector
    clusters : (n,) cluster labels (entity identifiers)

    Returns
    -------
    (k,) array of standard errors.
    """
    n, k = X.shape
    cluster_labels = np.unique(clusters)
    G = len(cluster_labels)
    try:
        XtX_inv = np.linalg.inv(X.T @ X)
    except np.linalg.LinAlgError:
        warnings.warn(
            "_clustered_se: X'X is singular; using pseudo-inverse. "
            "Clustered SEs may be unreliable.",
            RuntimeWarning,
            stacklevel=2,
        )
        XtX_inv = np.linalg.pinv(X.T @ X)
    meat = np.zeros((k, k))
    for g in cluster_labels:
        mask    = clusters == g
        score_g = X[mask].T @ e[mask]   # k-vector: sum of X_i * e_i for cluster g
        meat   += np.outer(score_g, score_g)
    adj = (G / (G - 1)) if G > 1 else 1.0
    V   = XtX_inv @ meat @ XtX_inv * adj
    diag = np.diag(V)
    return np.sqrt(np.where(diag > 0, diag, 0.0))


def _two_way_demean(
    df: pd.DataFrame,
    outcome: str,
    pred_cols: list[str],
) -> pd.DataFrame:
    """Two-way (entity + time) within-transformation.

    For each column c:
        c_dm = c - entity_mean(c) - time_mean(c) + grand_mean(c)

    Requires 'iso3' and 'year' as plain columns (not index).
    Returns a copy of df with outcome and pred_cols replaced by their
    demeaned counterparts.
    """
    df = df.copy()
    for c in [outcome] + pred_cols:
        if c not in df.columns:
            continue
        entity_mean = df.groupby("iso3")[c].transform("mean")
        time_mean   = df.groupby("year")[c].transform("mean")
        grand_mean  = df[c].mean()
        df[c] = df[c] - entity_mean - time_mean + grand_mean
    return df


def phase9_event_study(df: pd.DataFrame, focal_pred: str = FOCAL_PRED,
                       out_path: str = EVENTSTUDY_PATH) -> list[dict]:
    """Pre-trend and post-change event study for the religious courts finding.

    Uses all countries: non-changers act as control group.
    Event-time dummies capture the effect in each year relative to the
    year before the largest within-country courts change (reference = t=-1).
    Pre-trend F-test: joint significance of et_{-3} and et_{-2}.
    """
    print(f"\n{'='*60}")
    print("PHASE 9a -- EVENT STUDY (pre-trend test for changers)")
    print(f"{'='*60}")

    # Sample: all rows with non-missing outcome + CONTROLS_GDP
    required = [OUTCOME, "iso3", "year"] + CONTROLS_GDP
    base = df[required + [focal_pred]].dropna(subset=[OUTCOME] + CONTROLS_GDP).copy()

    # Identify changers from full predictor data
    pred_data = base[["iso3", "year", focal_pred]].dropna()
    pred_sd   = pred_data.groupby("iso3")[focal_pred].std().fillna(0)
    changers  = pred_sd[pred_sd > 0.02].index
    print(f"  Changers ({focal_pred} SD > 0.02): {len(changers)} countries")

    # Find event year (year of largest absolute first-difference) per changer
    event_years: dict[str, int] = {}
    for iso3, grp in pred_data[pred_data["iso3"].isin(changers)].groupby("iso3"):
        grp    = grp.sort_values("year")
        diffs  = grp[focal_pred].diff().abs()
        if diffs.notna().any() and diffs.max() > 0:
            event_years[iso3] = int(grp.loc[diffs.idxmax(), "year"])
    print(f"  Event years identified: {len(event_years)} changers")

    # Compute relative year
    base["rel_year"] = np.nan
    for iso3, ev_yr in event_years.items():
        mask = base["iso3"] == iso3
        base.loc[mask, "rel_year"] = base.loc[mask, "year"] - ev_yr

    # Build event-time dummies (k = -3, -2, 0, 1, 2, 3; omit k=-1 as reference)
    k_vals  = [-3, -2, 0, 1, 2, 3]
    et_cols = []
    for k in k_vals:
        col = f"et_{k}"           # e.g. "et_-3", "et_0", "et_1"
        base[col] = (
            base["iso3"].isin(changers) & (base["rel_year"] == k)
        ).astype(float)
        if base[col].sum() > 0:   # retain only if at least one 1
            et_cols.append(col)
    # Ensure NaN rel_year rows (non-changers + out-of-window changers) have 0 dummies
    base[et_cols] = base[et_cols].fillna(0)

    print(f"  Event-time dummies retained: {et_cols}")
    if not et_cols:
        print("  No event-time dummies with variation -- skipping.")
        return []

    all_preds = et_cols + CONTROLS_GDP
    sub = base.dropna(subset=[OUTCOME] + CONTROLS_GDP).copy()
    sub[et_cols] = sub[et_cols].fillna(0)
    print(f"  N = {len(sub):,} obs, {sub['iso3'].nunique()} countries")

    try:
        pan = sub.set_index(["iso3", "year"])
        y   = pan[OUTCOME]
        X   = sm.add_constant(pan[all_preds])
        res = PanelOLS(y, X, entity_effects=True, time_effects=True).fit(
            cov_type="clustered", cluster_entity=True
        )
        print(res.summary)

        # Pre-trend joint test (chi-squared Wald)
        pre_vars   = [v for v in et_cols if v in ("et_-3", "et_-2")]
        p_pretrend = np.nan
        if len(pre_vars) >= 1 and all(v in res.params.index for v in pre_vars):
            coef_pre  = res.params[pre_vars].values
            cov_pre   = res.cov.loc[pre_vars, pre_vars].values
            try:
                wald_stat  = float(coef_pre @ np.linalg.inv(cov_pre) @ coef_pre)
                p_pretrend = float(1.0 - stats.chi2.cdf(wald_stat, df=len(pre_vars)))
                verdict    = ("No evidence of pre-trends" if p_pretrend > 0.05
                              else "WARNING: pre-trends detected")
                print(f"\n  Pre-trend joint test (k={pre_vars}): "
                      f"chi2={wald_stat:.3f}, p={p_pretrend:.4f}  --> {verdict}")
            except np.linalg.LinAlgError:
                print("  Pre-trend test: singular covariance -- skipping.")

        # Save event-study CSV (include reference k=-1 at coef=0)
        es_rows = []
        for col in et_cols:
            if col in res.params.index:
                k_val = int(col.replace("et_", ""))
                es_rows.append({
                    "event_time": k_val,
                    "coef": float(res.params[col]),
                    "se":   float(res.std_errors[col]),
                    "pval": float(res.pvalues[col]),
                    "sig":  _sig(float(res.pvalues[col])),
                    "pretrend_p": p_pretrend,
                })
        es_rows.append({
            "event_time": -1, "coef": 0.0, "se": 0.0, "pval": 1.0,
            "sig": "", "pretrend_p": p_pretrend,
        })
        es_df = pd.DataFrame(es_rows).sort_values("event_time")
        es_df.to_csv(out_path, index=False, float_format="%.6f")
        print(f"\n  Event study saved -> {out_path}")

        results = []
        for col in et_cols:
            if col in res.params.index:
                results.append({
                    "tier":      "P9_event_study",
                    "year":      "all",
                    "predictor": col,
                    "coef":      float(res.params[col]),
                    "se":        float(res.std_errors[col]),
                    "pval":      float(res.pvalues[col]),
                    "n":         res.nobs,
                    "r2":        float(res.rsquared),
                })
        return results

    except Exception as exc:
        print(f"  Event study failed: {exc}")
        return []


def phase9_wild_bootstrap(
    df: pd.DataFrame,
    n_boot: int = 499,
    seed: int = 42,
    focal_pred: str = FOCAL_PRED,
) -> list[dict]:
    """Wild cluster bootstrap p-value for the changers-only PanelOLS.

    Addresses the small-cluster problem (~47 clusters) using Rademacher weights.
    Null DGP: residuals from the model excluding FOCAL_PRED, scrambled by entity.
    """
    print(f"\n{'='*60}")
    print("PHASE 9b -- WILD CLUSTER BOOTSTRAP (changers subsample)")
    print(f"{'='*60}")

    rng       = np.random.default_rng(seed)
    # Item 2 (2026-04-15): focal-pred-aware predictor set
    pred_cols = _preds_for_focal(focal_pred, CONTROLS_GDP)
    required  = [OUTCOME, "iso3", "year"] + pred_cols
    base = df[required].dropna(subset=[OUTCOME] + pred_cols).copy()

    courts_sd  = base.groupby("iso3")[focal_pred].std().fillna(0)
    changers   = courts_sd[courts_sd > 0.02].index
    ch         = base[base["iso3"].isin(changers)].copy()
    n_changers = ch["iso3"].nunique()
    print(f"  Changers: {n_changers} countries, {len(ch):,} obs")

    if len(ch) < 50 or n_changers < 5:
        print("  Too few changers for wild bootstrap -- skipping.")
        return []

    # Two-way demeaning (equivalent to country + year FE)
    ch_dm   = _two_way_demean(ch, OUTCOME, pred_cols)
    ch_dm   = ch_dm.dropna(subset=[OUTCOME] + pred_cols)

    entities  = ch_dm["iso3"].values
    y_dm      = ch_dm[OUTCOME].values
    X_dm      = ch_dm[pred_cols].values          # (n, k), no constant

    focal_idx = pred_cols.index(focal_pred)
    null_idx  = [i for i in range(len(pred_cols)) if i != focal_idx]
    X_null_dm = X_dm[:, null_idx]

    # Fit null and full models via lstsq
    beta_null, _, _, _ = np.linalg.lstsq(X_null_dm, y_dm, rcond=None)
    resid_null = y_dm - X_null_dm @ beta_null

    beta_full, _, _, _ = np.linalg.lstsq(X_dm, y_dm, rcond=None)
    resid_full = y_dm - X_dm @ beta_full

    se_obs = _clustered_se(X_dm, resid_full, entities)
    if se_obs[focal_idx] <= 0:
        print("  SE = 0 for focal predictor -- skipping bootstrap.")
        return []
    t_obs = beta_full[focal_idx] / se_obs[focal_idx]
    print(f"  Observed t-stat (demeaned OLS): {t_obs:.4f}")
    print(f"  Running {n_boot} bootstrap iterations ...")

    unique_ents = np.unique(entities)
    t_boots: list[float] = []
    for _ in range(n_boot):
        # Rademacher weights: one per entity, +1 or -1 with equal probability
        w_e   = rng.choice([-1.0, 1.0], size=len(unique_ents))
        w_map = dict(zip(unique_ents, w_e))
        w_arr = np.array([w_map[e] for e in entities])

        y_boot = X_null_dm @ beta_null + resid_null * w_arr
        beta_b, _, _, _ = np.linalg.lstsq(X_dm, y_boot, rcond=None)
        resid_b = y_boot - X_dm @ beta_b
        se_b    = _clustered_se(X_dm, resid_b, entities)
        if se_b[focal_idx] > 0:
            t_boots.append(abs(beta_b[focal_idx] / se_b[focal_idx]))

    p_wild = float(np.mean(np.array(t_boots) >= abs(t_obs))) if t_boots else np.nan
    print(f"  Wild bootstrap p-value: {p_wild:.4f}  (n_valid_boots={len(t_boots)})")

    tier_suffix = "" if focal_pred == FOCAL_PRED else f"_{focal_pred.replace('gri_','').replace('_norm','')}"
    return [{
        "tier":      f"T2_changers_wild_bootstrap{tier_suffix}",
        "year":      "all",
        "predictor": focal_pred,
        "coef":      float(beta_full[focal_idx]),
        "se":        float(se_obs[focal_idx]),
        "pval":      float(p_wild),
        "n":         int(len(ch_dm)),
        "r2":        np.nan,
    }]


def phase9_driscoll_kraay(df: pd.DataFrame) -> list[dict]:
    """Re-run T2 with Driscoll-Kraay kernel HAC SEs (bandwidth=4).

    Robust to both serial correlation and spatial correlation across countries.
    Bandwidth of 4 years covers typical autocorrelation in the GRI panel.
    """
    print(f"\n{'='*60}")
    print("PHASE 9c -- DRISCOLL-KRAAY HAC SE  (bandwidth=4)")
    print(f"{'='*60}")

    pred_cols = GRI_PANEL_COLS + CONTROLS_GDP
    required  = [OUTCOME, "iso3", "year"] + pred_cols
    sub = df[required].dropna(subset=[OUTCOME] + pred_cols).copy()
    print(f"  N = {len(sub):,} obs, {sub['iso3'].nunique()} countries")

    results = []
    try:
        pan    = sub.set_index(["iso3", "year"])
        y      = pan[OUTCOME]
        X      = sm.add_constant(pan[pred_cols])
        model  = PanelOLS(y, X, entity_effects=True, time_effects=True)
        res_dk = model.fit(cov_type="kernel", bandwidth=4)

        c  = res_dk.params[FOCAL_PRED_LEGACY]
        se = res_dk.std_errors[FOCAL_PRED_LEGACY]
        p  = res_dk.pvalues[FOCAL_PRED_LEGACY]
        print(f"  DK (bandwidth=4): courts coef={c:.5f}  se={se:.5f}  p={p:.4f}  {_sig(p)}")
        print(res_dk.summary)

        # Item 2 (Step 6): per-predictor diagnostics
        for var in res_dk.params.index:
            if var in pred_cols:
                diag = _panel_diagnostics(sub, var)
                std_c = _std_coef(float(res_dk.params[var]), sub[var], sub[OUTCOME])
            else:
                diag = {"n_clusters": int(sub["iso3"].nunique()),
                        "n_changers": np.nan, "within_sd": np.nan}
                std_c = np.nan
            results.append({
                "tier":      "T2_driscoll_kraay",
                "year":      "all",
                "predictor": var,
                "coef":      float(res_dk.params[var]),
                "se":        float(res_dk.std_errors[var]),
                "pval":      float(res_dk.pvalues[var]),
                "n":         res_dk.nobs,
                "r2":        float(res_dk.rsquared),
                "n_clusters": diag["n_clusters"],
                "n_changers": diag["n_changers"],
                "within_sd":  diag["within_sd"],
                "std_coef":   std_c,
                "se_type":    "driscoll_kraay_bw4",
                "valid":      True,
                "invalid_reason": "",
            })
    except Exception as exc:
        print(f"  Driscoll-Kraay failed: {exc}")

    return results


def phase9_mundlak_cre(df: pd.DataFrame) -> list[dict]:
    """Correlated Random Effects (Mundlak 1978) for the Tier 2 panel model.

    Adds country means of all time-varying predictors (Mundlak device) so
    pooled OLS is consistent under correlated random effects, equivalent to FE.
    """
    print(f"\n{'='*60}")
    print("PHASE 9d -- MUNDLAK CRE  (Tier 2 GRI model + country means)")
    print(f"{'='*60}")

    pred_cols = GRI_PANEL_COLS + CONTROLS_GDP
    required  = [OUTCOME, "iso3", "year"] + pred_cols
    sub       = df[required].dropna(subset=[OUTCOME] + pred_cols).copy()

    year_dummies = pd.get_dummies(sub["year"], prefix="yr", drop_first=True).astype(float)
    sub = pd.concat([sub.reset_index(drop=True), year_dummies.reset_index(drop=True)], axis=1)

    # Mundlak device: within-group means of all time-varying predictors
    cmean_cols = []
    for col in pred_cols:
        cmean = col + "_cmean"
        sub[cmean] = sub.groupby("iso3")[col].transform("mean")
        cmean_cols.append(cmean)

    # Final predictor list (drop zero-variance columns)
    base_preds  = pred_cols + list(year_dummies.columns)
    final_preds = [c for c in base_preds + cmean_cols
                   if c in sub.columns and sub[c].std() > 1e-8]

    print(f"  N = {len(sub):,} obs, {sub['iso3'].nunique()} countries")
    print(f"  Predictors: {len(final_preds)}  (incl. {len(cmean_cols)} country means)")

    results = []
    try:
        X     = sm.add_constant(sub[final_preds])
        y     = sub[OUTCOME]
        model = sm.OLS(y, X).fit(
            cov_type="cluster",
            cov_kwds={"groups": sub["iso3"]},
        )
        print(model.summary(slim=True))

        key_vars = [v for v in GRI_PANEL_COLS if v in model.params.index]
        print("\n  Key Mundlak CRE estimates:")
        for v in key_vars:
            print(f"    {v}: coef={model.params[v]:.5f}  "
                  f"p={model.pvalues[v]:.4f}  {_sig(model.pvalues[v])}")

        # Item 2 (Step 6): per-predictor diagnostics. _cmean predictors
        # (this function's naming, note the trailing _cmean not _mean)
        # inherit diagnostics from their parent time-varying col.
        for var in model.params.index:
            parent = var[:-6] if var.endswith("_cmean") else var
            if parent in pred_cols:
                diag = _panel_diagnostics(sub, parent)
                std_c = _std_coef(float(model.params[var]), sub[parent], sub[OUTCOME])
            else:
                diag = {"n_clusters": int(sub["iso3"].nunique()),
                        "n_changers": np.nan, "within_sd": np.nan}
                std_c = np.nan
            results.append({
                "tier":      "T2_mundlak_cre",
                "year":      "all",
                "predictor": var,
                "coef":      model.params[var],
                "se":        model.bse[var],
                "pval":      model.pvalues[var],
                "n":         int(model.nobs),
                "r2":        model.rsquared,
                "n_clusters": diag["n_clusters"],
                "n_changers": diag["n_changers"],
                "within_sd":  diag["within_sd"],
                "std_coef":   std_c,
                "se_type":    "cluster_entity",
                "valid":      True,
                "invalid_reason": "",
            })
    except Exception as exc:
        print(f"  Mundlak CRE failed: {exc}")

    return results


def phase9_male_composite_placebo(df: pd.DataFrame) -> list[dict]:
    """Symmetric placebo: 3-component male welfare composite index.

    Components (from QoG): male life expectancy, male LFP, male homicides
    (inverted so higher = better).  Requires >= 2 non-missing vars per row.
    Tests whether courts predicts a male composite as strongly as the
    13-component female index (expectation: male effect is smaller / zero).
    """
    print(f"\n{'='*60}")
    print("PHASE 9e -- MALE COMPOSITE WELFARE INDEX (symmetric placebo)")
    print(f"{'='*60}")

    male_var_map = {
        "wdi_lifexpm":   "lifexpm_raw",
        "wdi_lfpmilo15": "lfpm_raw",
        "wdi_homicidesm": "homicidesm_raw",
    }
    usecols_try = ["ccodealp", "year"] + list(male_var_map.keys())
    try:
        raw = pd.read_csv(QOG_RAW, usecols=usecols_try, low_memory=False)
    except ValueError:
        # wdi_homicidesm may not exist in older QoG releases
        usecols_try = ["ccodealp", "year", "wdi_lifexpm", "wdi_lfpmilo15"]
        raw = pd.read_csv(QOG_RAW, usecols=usecols_try, low_memory=False)

    raw = raw.rename(columns={"ccodealp": "iso3"})

    available_norm: list[str] = []
    for raw_col, alias in male_var_map.items():
        if raw_col not in raw.columns:
            continue
        vals = raw[raw_col].where(raw[raw_col] > 0)
        if raw_col == "wdi_homicidesm":
            raw["homicidesm_inv_norm"] = 1.0 - robust_minmax(vals)
            available_norm.append("homicidesm_inv_norm")
        elif raw_col == "wdi_lifexpm":
            raw["lifexpm_norm"] = robust_minmax(vals)
            available_norm.append("lifexpm_norm")
        elif raw_col == "wdi_lfpmilo15":
            raw["lfpm_norm"] = robust_minmax(vals)
            available_norm.append("lfpm_norm")

    print(f"  Male welfare components available: {available_norm}")
    if not available_norm:
        print("  No male welfare vars found in QoG -- skipping.")
        return []

    raw["n_male_vars"] = raw[available_norm].notna().sum(axis=1)
    raw["male_welfare_index"] = np.where(
        raw["n_male_vars"] >= 2,
        raw[available_norm].mean(axis=1, skipna=True),
        np.nan,
    )
    male_df = raw[["iso3", "year", "male_welfare_index"]].copy()
    df_m    = df.merge(male_df, on=["iso3", "year"], how="left")
    print(f"  Male welfare index: {df_m['male_welfare_index'].notna().sum():,} obs matched")

    pred_cols = GRI_PANEL_COLS + CONTROLS_GDP
    required  = ["male_welfare_index", "iso3", "year"] + pred_cols
    panel     = df_m[required].dropna(subset=["male_welfare_index"] + pred_cols).copy()
    if len(panel) < 100:
        print(f"  Too few obs ({len(panel)}) -- skipping.")
        return []

    results: list[dict] = []
    try:
        pan = panel.set_index(["iso3", "year"])
        y   = pan["male_welfare_index"]
        X   = sm.add_constant(pan[pred_cols])
        res = PanelOLS(y, X, entity_effects=True, time_effects=True).fit(
            cov_type="clustered", cluster_entity=True
        )
        c  = float(res.params[FOCAL_PRED_LEGACY])
        se = float(res.std_errors[FOCAL_PRED_LEGACY])
        p  = float(res.pvalues[FOCAL_PRED_LEGACY])
        print(f"  Male composite (placebo DV): courts coef={c:+.5f}  "
              f"se={se:.5f}  p={p:.4f}  {_sig(p)}")
        print(res.summary)

        for var in res.params.index:
            results.append({
                "tier":      "P9_male_composite_placebo",
                "year":      "all",
                "predictor": var,
                "dv_label":  "Male welfare index (placebo DV)",
                "coef":      float(res.params[var]),
                "se":        float(res.std_errors[var]),
                "pval":      float(res.pvalues[var]),
                "n":         res.nobs,
                "r2":        float(res.rsquared),
            })

        # Append focal row to PLACEBO_PATH (for plot_placebo to pick up)
        if os.path.exists(PLACEBO_PATH):
            plac_existing = pd.read_csv(PLACEBO_PATH)
            already_there = (
                (plac_existing.get("tier", "") == "P9_male_composite_placebo") &
                (plac_existing.get("predictor", "") == FOCAL_PRED_LEGACY)
            ).any()
            if not already_there:
                new_row = pd.DataFrame([{
                    "tier":     "P9_male_composite_placebo",
                    "year":     "all",
                    "predictor": FOCAL_PRED_LEGACY,
                    "dv_label": "Male welfare index (placebo DV)",
                    "coef": c, "se": se, "pval": p,
                    "n": res.nobs, "r2": float(res.rsquared),
                    "sig": _sig(p),
                }])
                updated = pd.concat([plac_existing, new_row], ignore_index=True)
                updated.to_csv(PLACEBO_PATH, index=False, float_format="%.6f")
                print(f"  Focal row appended to {PLACEBO_PATH}")

    except Exception as exc:
        print(f"  Male composite placebo failed: {exc}")

    return results


def phase9_oster_sensitivity(df: pd.DataFrame, focal_pred: str = FOCAL_PRED,
                              out_path: str = OSTER_SENS_PATH) -> pd.DataFrame:
    """Oster (2019) delta sensitivity curve across a range of Rmax values.

    Uses the same common sample as phase7_oster_delta.
    Computes delta for Rmax_mult in [0.8, 3.0] x R_full, skipping Rmax <= R_full.
    Reports the multiplier at which delta first falls below 1.0.

    Returns a DataFrame with columns ['rmax_mult', 'rmax_val', 'delta'].
    """
    print(f"\n{'='*60}")
    print("PHASE 9f -- OSTER DELTA SENSITIVITY CURVE")
    print(f"{'='*60}")

    # Item 2 (2026-04-15): focal-pred-aware full spec
    full_preds = _preds_for_focal(focal_pred, CONTROLS_GDP)
    required   = [OUTCOME, "iso3", "year"] + full_preds
    base = df[required].dropna(subset=[OUTCOME] + full_preds).copy()
    print(f"  Common sample: N={len(base):,} obs, {base['iso3'].nunique()} countries")

    fitted: dict[str, dict] = {}
    for spec_label, pred_cols in [
        ("bivariate", [focal_pred]),
        ("full",      full_preds),
    ]:
        pan = base.set_index(["iso3", "year"])
        y   = pan[OUTCOME]
        X   = sm.add_constant(pan[pred_cols])
        try:
            res = PanelOLS(y, X, entity_effects=True, time_effects=True).fit(
                cov_type="clustered", cluster_entity=True
            )
            fitted[spec_label] = {
                "coef": float(res.params[focal_pred]),
                "r2":   float(res.rsquared),
            }
            print(f"  [{spec_label}] coef={fitted[spec_label]['coef']:.5f}  "
                  f"R2={fitted[spec_label]['r2']:.4f}")
        except Exception as exc:
            print(f"  [{spec_label}] failed: {exc}")

    if len(fitted) < 2:
        print("  Cannot compute Oster sensitivity -- returning empty DataFrame.")
        return pd.DataFrame()

    beta_r, R_r = fitted["bivariate"]["coef"], fitted["bivariate"]["r2"]
    beta_f, R_f = fitted["full"]["coef"],      fitted["full"]["r2"]

    rows = []
    for mult_raw in np.arange(0.8, 3.15, 0.1):
        mult = round(float(mult_raw), 2)
        Rmax = mult * R_f
        if Rmax <= R_f:
            rows.append({"rmax_mult": mult, "rmax_val": Rmax, "delta": np.nan})
            continue
        denom = (beta_r - beta_f) * (Rmax - R_f)
        if abs(denom) > 1e-10 and abs(R_f - R_r) > 1e-10:
            delta = beta_f * (R_f - R_r) / denom
        else:
            delta = np.nan
        rows.append({"rmax_mult": mult, "rmax_val": Rmax, "delta": delta})

    sens_df = pd.DataFrame(rows)
    valid   = sens_df.dropna(subset=["delta"])
    below_1 = valid[valid["delta"] < 1.0]
    if not below_1.empty:
        print(f"\n  Delta first < 1.0 at Rmax_mult = {below_1.iloc[0]['rmax_mult']:.1f}x R_full")
    else:
        print(f"\n  Delta >= 1.0 for all Rmax tested (result is robust across range)")

    return sens_df


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 10 – REGIONAL HETEROGENEITY
# ═══════════════════════════════════════════════════════════════════════════════
def phase10_regional_heterogeneity(df: pd.DataFrame) -> list[dict]:
    """
    Tests whether the courts effect is concentrated in MENA or is globally distributed.
    Three approaches:
      P10_courts_x_mena  - pooled OLS with country+year dummies and courts x mena interaction
      P10_mena_only      - panel FE restricted to MENA countries
      P10_non_mena_only  - panel FE restricted to non-MENA countries
    """
    results = []

    print(f"\n{'='*60}")
    print("PHASE 10 -- REGIONAL HETEROGENEITY (MENA vs non-MENA)")
    print(f"{'='*60}")

    COURTS = FOCAL_PRED_LEGACY
    mena_iso3 = {iso for iso, region in REGION_MAP.items() if region == "MENA"}

    work = df[["iso3", "year"] + GRI_PANEL_COLS + CONTROLS_GDP + [OUTCOME]].dropna().copy()
    work["mena"] = work["iso3"].isin(mena_iso3).astype(int)
    work["courts_x_mena"] = work[COURTS] * work["mena"]

    # ── A: Interaction model (PanelOLS with courts x mena) ────────────────────
    # mena is time-invariant so entity FE absorbs it; courts_x_mena = courts * mena
    # varies within-entity for MENA countries only. PanelOLS identifies:
    #   beta_courts       = within-country courts effect for non-MENA
    #   beta_courts_x_mena = additional MENA premium (MENA effect = sum of both)
    print(f"\n  [A] Interaction: courts x mena (PanelOLS + entity/time FE)")
    panel_a = work[["iso3", "year"] + GRI_PANEL_COLS + CONTROLS_GDP +
                   ["courts_x_mena", OUTCOME]].dropna().copy()
    print(f"    N = {len(panel_a):,} obs, {panel_a['iso3'].nunique()} countries")

    try:
        panel_a_idx = panel_a.set_index(["iso3", "year"])
        pred_cols_a = GRI_PANEL_COLS + CONTROLS_GDP + ["courts_x_mena"]
        y_a = panel_a_idx[OUTCOME]
        X_a = sm.add_constant(panel_a_idx[pred_cols_a])
        mod_a = PanelOLS(y_a, X_a, entity_effects=True, time_effects=True)
        res_a = mod_a.fit(cov_type="clustered", cluster_entity=True)
        for var in pred_cols_a:
            if var in res_a.params.index:
                results.append({
                    "tier": "P10_courts_x_mena",
                    "year": "all",
                    "predictor": var,
                    "coef": res_a.params[var],
                    "se": res_a.std_errors[var],
                    "pval": res_a.pvalues[var],
                    "n": res_a.nobs,
                    "r2": res_a.rsquared,
                })
        c_main = res_a.params.get(COURTS, float("nan"))
        c_int  = res_a.params.get("courts_x_mena", float("nan"))
        p_int  = res_a.pvalues.get("courts_x_mena", float("nan"))
        print(f"    courts (non-MENA baseline): {c_main:.4f}")
        print(f"    courts x mena interaction:  {c_int:.4f}  (p={p_int:.3f})")
        print(f"    MENA total effect:          {c_main + c_int:.4f}")
    except Exception as e:
        print(f"    Interaction model failed: {e}")

    # ── B: Stratified panel FE ─────────────────────────────────────────────────
    for label, mask in [("mena_only", work["mena"] == 1),
                        ("non_mena_only", work["mena"] == 0)]:
        sub = work[mask].copy()
        print(f"\n  [{label}]  N = {len(sub):,} obs, {sub['iso3'].nunique()} countries")

        if len(sub) < 100 or sub["iso3"].nunique() < 5:
            print(f"    Too few obs/countries -- skipping {label}.")
            continue

        panel_b = sub[["iso3", "year"] + GRI_PANEL_COLS + CONTROLS_GDP + [OUTCOME]].dropna()
        panel_b = panel_b.set_index(["iso3", "year"])
        y_b = panel_b[OUTCOME]
        X_b = sm.add_constant(panel_b[GRI_PANEL_COLS + CONTROLS_GDP])

        try:
            model_b = PanelOLS(y_b, X_b, entity_effects=True, time_effects=True)
            res_b   = model_b.fit(cov_type="clustered", cluster_entity=True)
            for var in res_b.params.index:
                results.append({
                    "tier": f"P10_{label}",
                    "year": "all",
                    "predictor": var,
                    "coef": res_b.params[var],
                    "se": res_b.std_errors[var],
                    "pval": res_b.pvalues[var],
                    "n": res_b.nobs,
                    "r2": res_b.rsquared,
                })
            c_val = res_b.params.get(COURTS, float("nan"))
            p_val = res_b.pvalues.get(COURTS, float("nan"))
            print(f"    courts coef = {c_val:.4f}  (p={p_val:.3f})")
        except Exception as e:
            print(f"    Panel FE failed for {label}: {e}")

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 10 – GENDER GAP AND ALTERNATIVE EXTERNAL OUTCOMES
# ═══════════════════════════════════════════════════════════════════════════════
GENDER_GAP_PATH = os.path.join(ROOT, "data/robustness_outcomes.csv")

def phase10_gender_gap_outcomes(df: pd.DataFrame) -> list[dict]:
    """
    Tests courts on:
      - GDI  (Gender Development Index, UNDP)            -> P10_gdi_panel
      - WEF GGG (Global Gender Gap Index)                -> P10_wef_panel
      - life_exp_gap (female - male life expectancy)     -> P10_gap_lifeexp
      - lfp_gap      (female - male LFP rate)            -> P10_gap_lfp
    All panel FE with country + year FE, clustered SEs, focal predictor + GDP only.
    """
    results = []

    print(f"\n{'='*60}")
    print("PHASE 10 -- GENDER GAP & ALTERNATIVE EXTERNAL OUTCOMES")
    print(f"{'='*60}")

    if not os.path.exists(GENDER_GAP_PATH):
        print(f"  gender_gap_panel.csv not found at {GENDER_GAP_PATH} -- skipping.")
        return results

    gap = pd.read_csv(GENDER_GAP_PATH)
    COURTS = FOCAL_PRED_LEGACY

    # Normalise GDI and WEF GGG with robust_minmax
    for col in ["gdi", "gggi_ggi"]:
        if col in gap.columns:
            gap[col + "_norm"] = robust_minmax(gap[col])

    # Merge with secularism predictors from main df
    pred_df = df[["iso3", "year", COURTS, "log_gdppc_norm"]].dropna().copy()
    merged  = gap.merge(pred_df, on=["iso3", "year"], how="inner")

    outcomes = [
        ("gdi_norm",       "P10_gdi_panel",    "GDI (Gender Development Index)"),
        ("gggi_ggi_norm",  "P10_wef_panel",    "WEF Global Gender Gap Index"),
        ("life_exp_gap",   "P10_gap_lifeexp",  "Life expectancy gap (F - M, years)"),
        ("lfp_gap",        "P10_gap_lfp",      "LFP gap (F - M, pp)"),
    ]

    for outcome_col, tier_name, label in outcomes:
        if outcome_col not in merged.columns:
            print(f"  [{tier_name}] column '{outcome_col}' not found -- skipping.")
            continue

        sub = merged[["iso3", "year", outcome_col, COURTS, "log_gdppc_norm"]].dropna()
        n   = len(sub)
        nc  = sub["iso3"].nunique()
        print(f"\n  [{tier_name}] {label}")
        print(f"    N = {n:,} obs, {nc} countries")

        if n < 500:
            print(f"    Too few obs (< 500) -- skipping.")
            continue

        panel = sub.set_index(["iso3", "year"])
        y = panel[outcome_col]
        X = sm.add_constant(panel[[COURTS, "log_gdppc_norm"]])

        try:
            model = PanelOLS(y, X, entity_effects=True, time_effects=True)
            res   = model.fit(cov_type="clustered", cluster_entity=True)
            for var in res.params.index:
                results.append({
                    "tier": tier_name,
                    "year": "all",
                    "predictor": var,
                    "coef": res.params[var],
                    "se": res.std_errors[var],
                    "pval": res.pvalues[var],
                    "n": res.nobs,
                    "r2": res.rsquared,
                })
            c_val = res.params.get(COURTS, float("nan"))
            p_val = res.pvalues.get(COURTS, float("nan"))
            print(f"    courts coef = {c_val:.5f}  (p={p_val:.3f})  within-R2={res.rsquared:.3f}")
        except Exception as e:
            print(f"    Panel FE failed: {e}")

    return results



# ═══════════════════════════════════════════════════════════════════════════════
# SAVE RESULTS
# ═══════════════════════════════════════════════════════════════════════════════
def _apply_mt_corrections(out: pd.DataFrame) -> pd.DataFrame:
    """Apply Bonferroni + Benjamini-Hochberg corrections to the focal family.

    Item 2 (2026-04-15): focal family redefined post-composite.
    Primary headline family = { composite_secularism_norm,
                                composite_secularism_pca_norm,
                                gri_apostasy_norm,
                                gri_religious_courts_norm }  ×
                              { T2_no_gdp, T2_with_gdp }.
    = 8 tests in the Bonferroni denominator. GRI sub-items other than
    apostasy + legacy courts are NOT counted in the headline denominator
    (their coefficients still appear in results.csv; they're just not
    part of the headline-family correction).
    Corrections applied *within* family. Non-family rows get NaN.
    """
    out["pval_bonf"] = np.nan
    out["pval_bh"] = np.nan
    focal_preds = {
        "composite_secularism_norm",
        "composite_secularism_pca_norm",
        "gri_apostasy_norm",
        "gri_religious_courts_norm",
    }
    focal_tiers = {"T2_no_gdp", "T2_with_gdp"}
    mask = out["tier"].isin(focal_tiers) & out["predictor"].isin(focal_preds)
    if mask.sum() == 0:
        return out
    pvals = out.loc[mask, "pval"].astype(float).values
    m_tests = len(pvals)
    # Bonferroni
    out.loc[mask, "pval_bonf"] = np.minimum(pvals * m_tests, 1.0)
    # Benjamini-Hochberg FDR
    order = np.argsort(pvals)
    ranked = np.empty_like(pvals)
    ranked[order] = np.arange(1, m_tests + 1)
    bh = pvals * m_tests / ranked
    # Enforce monotonicity
    bh_sorted = bh[order]
    for i in range(len(bh_sorted) - 2, -1, -1):
        bh_sorted[i] = min(bh_sorted[i], bh_sorted[i + 1])
    bh_monotone = np.empty_like(bh)
    bh_monotone[order] = np.minimum(bh_sorted, 1.0)
    out.loc[mask, "pval_bh"] = bh_monotone
    return out


def _attach_interpretation(out: pd.DataFrame) -> pd.DataFrame:
    """Short plain-English interpretation per row (best-effort, focal rows)."""
    def _fmt(row):
        try:
            if pd.isna(row.get("coef")):
                return ""
            pred = str(row.get("predictor", ""))
            coef = float(row["coef"])
            if pred in GRI_PANEL_COLS:
                direction = "decreases" if coef < 0 else "increases"
                return (f"moving {pred} from 0 to 1 {direction} the outcome "
                        f"by {abs(coef):.4f} (index units)")
            if pred == "log_gdppc_norm":
                return (f"1-unit change in normalised log-GDP associates with "
                        f"{coef:+.4f} in the outcome (normalised scale)")
            return ""
        except Exception:
            return ""
    out["interpretation"] = out.apply(_fmt, axis=1)
    return out


def save_results(all_results: list[dict]):
    out = pd.DataFrame(all_results)

    # ── Schema normalisation: every row gets the enhanced columns ──────────
    for col, default in [
        ("n_clusters", np.nan), ("n_changers", np.nan), ("within_sd", np.nan),
        ("std_coef", np.nan), ("se_type", ""), ("valid", True),
        ("invalid_reason", ""),
    ]:
        if col not in out.columns:
            out[col] = default
        else:
            out[col] = out[col].fillna(default) if col in ("se_type", "invalid_reason") else out[col]
    out["valid"] = out["valid"].fillna(True)

    out["sig"] = out["pval"].apply(_sig)
    out = _apply_mt_corrections(out)
    out = _attach_interpretation(out)

    # Order columns sensibly
    lead = ["tier", "year", "predictor", "coef", "se", "pval", "sig",
            "pval_bonf", "pval_bh", "std_coef", "n", "r2",
            "n_clusters", "n_changers", "within_sd", "se_type",
            "valid", "invalid_reason", "interpretation"]
    rest = [c for c in out.columns if c not in lead]
    out = out[[c for c in lead if c in out.columns] + rest]

    out.to_csv(OUT_PATH, index=False, float_format="%.6f")
    print(f"\n  Results saved -> {OUT_PATH}")
    print(f"  Rows: {len(out)}  |  Invalid (e.g. T3 Roodman fail): "
          f"{(~out['valid'].astype(bool)).sum()}")
    # Summary: significant findings only (valid rows only)
    sig_rows = out[(out["sig"] != "") & (out["valid"].astype(bool))].copy()
    print(f"\n  Significant VALID results ({len(sig_rows)} predictors with p<0.10):")
    print(sig_rows[["tier", "year", "predictor", "coef", "pval", "pval_bh",
                    "sig", "n", "n_changers"]]
          .sort_values("pval")
          .to_string(index=False, float_format="{:.4f}".format))


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN  — tee output to log file
# ═══════════════════════════════════════════════════════════════════════════════
class _Tee:
    """Write to both stdout and a file."""
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            f.write(obj)
    def flush(self):
        for f in self.files:
            f.flush()


# ═══════════════════════════════════════════════════════════════════════════════
# WBL GROUP SCORE ANALYSIS — scoring pipeline as outcomes
# ═══════════════════════════════════════════════════════════════════════════════
WBL_GROUPS_PATH = os.path.join(ROOT, "data/wbl_group_scores.csv")
WBL_GROUPS_RESULTS_PATH = os.path.join(ROOT, "results/results_wbl_groups.csv")

WBL_GROUP_LABELS = {
    "assets":       "Assets & inheritance",
    "econ_rights":  "Economic rights",
    "fam_safety":   "Family & safety",
    "health":       "Health",
    "mobility":     "Mobility",
    "parenthood":   "Parenthood",
    "pay":          "Pay",
    "pension":      "Pension",
    "political_rep":"Political representation",
    "workplace":    "Workplace",
    "overall_score":"Overall score",
}


def phase_wbl_groups() -> pd.DataFrame:
    """
    Panel FE regression of religious courts → each of the 10 WBL group scores
    built by scoring.py (plus the overall score).

    Uses predictors.csv for the religion and control variables.
    Overlap period: 2013–2022 (WBL covers 2013-2023; GRI covers up to 2022).
    """
    print(f"\n{'='*60}")
    print("WBL GROUP SCORE ANALYSIS")
    print(f"  Outcomes: 10 WBL group scores + overall (from scoring.py)")
    print(f"{'='*60}")

    if not os.path.exists(WBL_GROUPS_PATH):
        print(f"  ERROR: {WBL_GROUPS_PATH} not found -- run scoring.py first")
        return pd.DataFrame()

    wbl = pd.read_csv(WBL_GROUPS_PATH)
    pred = pd.read_csv(COMP_PATH)
    pred = pred.drop(columns=["country"], errors="ignore")

    merged = wbl.merge(pred, on=["iso3", "year"], how="inner")

    # Pull in governance controls from outcome_composite if not already present
    ctrl_path = os.path.join(ROOT, "data/outcome_composite.csv")
    if os.path.exists(ctrl_path):
        ctrl_cols = ["iso3", "year"] + [c for c in CONTROLS if c not in merged.columns]
        if len(ctrl_cols) > 2:
            ctrl = pd.read_csv(ctrl_path)[ctrl_cols]
            merged = merged.merge(ctrl, on=["iso3", "year"], how="left")

    # Overlap period: GRI goes to 2022, WBL starts 2013
    merged = merged[(merged["year"] >= 2013) & (merged["year"] <= 2022)]

    print(f"  Merged: {len(merged):,} obs, {merged['iso3'].nunique()} countries, "
          f"years {sorted(merged['year'].unique())}")

    group_cols = [g for g in WBL_GROUP_LABELS if g in merged.columns]
    pred_cols  = GRI_PANEL_COLS + CONTROLS_GDP

    rows = []
    for group in group_cols:
        required = [group, "iso3", "year"] + pred_cols
        sub = merged[required].dropna(subset=[group] + pred_cols).copy()

        print(f"\n  [{group}] N={len(sub):,} obs, {sub['iso3'].nunique()} countries")
        if sub["iso3"].nunique() < 20 or len(sub) < 50:
            print("    Too few obs — skipping.")
            continue

        try:
            panel = sub.set_index(["iso3", "year"])
            y = panel[group]
            X = sm.add_constant(panel[pred_cols])
            res = PanelOLS(y, X, entity_effects=True, time_effects=True
                           ).fit(cov_type="clustered", cluster_entity=True)

            if FOCAL_PRED_LEGACY in res.params:
                c, se, p = (res.params[FOCAL_PRED_LEGACY],
                            res.std_errors[FOCAL_PRED_LEGACY],
                            res.pvalues[FOCAL_PRED_LEGACY])
                print(f"    {FOCAL_PRED_LEGACY}: coef={c:.5f}  se={se:.5f}  p={p:.4f}  {_sig(p)}")

            for var in res.params.index:
                rows.append({
                    "group":      group,
                    "group_label": WBL_GROUP_LABELS.get(group, group),
                    "predictor":  var,
                    "coef":       res.params[var],
                    "se":         res.std_errors[var],
                    "pval":       res.pvalues[var],
                    "sig":        _sig(res.pvalues[var]),
                    "n":          res.nobs,
                    "r2":         float(getattr(res.rsquared, "within", res.rsquared)),
                })
        except Exception as e:
            print(f"    Model failed: {e}")

    df_out = pd.DataFrame(rows)
    if not df_out.empty:
        df_out.to_csv(WBL_GROUPS_RESULTS_PATH, index=False, float_format="%.6f")
        print(f"\n  Saved -> {WBL_GROUPS_RESULTS_PATH}")
    return df_out


def composite_tier_specs(df: pd.DataFrame, focal_col: str) -> list[dict]:
    """Item 2 (2026-04-15): standalone composite regressions under canonical tier tags.

    tier2_panel_fe and tier4_mundlak_re are hardcoded to GRI_PANEL_COLS as the
    multi-predictor decomposition spec — that is by design (they report
    coefficients for every GRI sub-item). The composite is NOT in GRI_PANEL_COLS
    and would not appear in those regressions, so without this function the
    headline table for composite would be all "missing".

    This function fits PanelOLS with `[focal_col] + CONTROLS_GDP` (or _no_gdp
    variant) as a STANDALONE focal regression, and emits rows with the same
    tier tags that tier2_panel_fe / tier4_mundlak_re use. The composite
    coefficient then lives under T2_no_gdp / T2_with_gdp / T4_mundlak_re /
    etc. alongside the GRI rows, with `predictor = focal_col`.

    Methodologically: these are the composite-as-headline estimates that the
    paper should quote. The GRI-panel versions in tier2_panel_fe remain as
    the decomposition reference.
    """
    print(f"\n{'='*60}")
    print(f"COMPOSITE TIER SPECS -- standalone regressions for {focal_col}")
    print(f"{'='*60}")

    if focal_col not in df.columns:
        print(f"  {focal_col} not in df; skipping.")
        return []

    results = []

    # ── T1: cross-sectional OLS with HC3 SEs on composite (2014, 2020) ────
    for year in [2014, 2020]:
        sub = df[df["year"] == year].copy()
        for label, controls in [("no_gdp", CONTROLS), ("with_gdp", CONTROLS_GDP)]:
            pred_cols = [focal_col] + controls
            s = sub.dropna(subset=[OUTCOME] + pred_cols).copy()
            if len(s) < 30:
                continue
            try:
                X = sm.add_constant(s[pred_cols])
                y = s[OUTCOME]
                model = sm.OLS(y, X).fit(cov_type="HC3")
                results.append({
                    "tier": f"T1_{label}",
                    "year": year,
                    "predictor": focal_col,
                    "coef": float(model.params[focal_col]),
                    "se":   float(model.bse[focal_col]),
                    "pval": float(model.pvalues[focal_col]),
                    "n":    int(model.nobs),
                    "r2":   float(model.rsquared),
                    "se_type": "HC3",
                })
            except Exception as e:
                print(f"  [T1_{label} {year}] failed: {e}")

    # ── T2: panel FE with clustered SEs + DK variant + samesample ─────────
    # Replicate the with_gdp_index logic for samesample variants.
    with_gdp_required = [OUTCOME, "iso3", "year", focal_col] + CONTROLS_GDP
    with_gdp_sub = df[with_gdp_required].dropna(
        subset=[OUTCOME, focal_col] + CONTROLS_GDP).copy()

    specs = [
        ("gri_only",  []),
        ("gri_gdp",   ["log_gdppc_norm"]),
        ("no_gdp",    CONTROLS),
        ("with_gdp",  CONTROLS_GDP),
    ]
    for label, controls in specs:
        pred_cols = [focal_col] + controls
        sub = df[[OUTCOME, "iso3", "year"] + pred_cols].dropna(
            subset=[OUTCOME] + pred_cols).copy()
        if len(sub) < 50:
            continue
        try:
            pan = sub.set_index(["iso3", "year"])
            y = pan[OUTCOME]
            X = sm.add_constant(pan[pred_cols])
            model = PanelOLS(y, X, entity_effects=True, time_effects=True)
            res = model.fit(cov_type="clustered", cluster_entity=True)
            diag = _panel_diagnostics(sub, focal_col)
            std_c = _std_coef(float(res.params[focal_col]), sub[focal_col], sub[OUTCOME])
            results.append({
                "tier": f"T2_{label}",
                "year": "all",
                "predictor": focal_col,
                "coef": float(res.params[focal_col]),
                "se":   float(res.std_errors[focal_col]),
                "pval": float(res.pvalues[focal_col]),
                "n":    int(res.nobs),
                "r2":   float(res.rsquared),
                "n_clusters": diag["n_clusters"],
                "n_changers": diag["n_changers"],
                "within_sd":  diag["within_sd"],
                "std_coef":   std_c,
                "se_type":    "cluster_entity",
                "valid":      True,
                "invalid_reason": "",
            })
            # DK variant
            try:
                res_dk = model.fit(cov_type="kernel", kernel="bartlett", bandwidth=2)
                results.append({
                    "tier": f"T2_{label}_dk",
                    "year": "all",
                    "predictor": focal_col,
                    "coef": float(res_dk.params[focal_col]),
                    "se":   float(res_dk.std_errors[focal_col]),
                    "pval": float(res_dk.pvalues[focal_col]),
                    "n":    int(res_dk.nobs),
                    "r2":   float(res_dk.rsquared),
                    "n_clusters": diag["n_clusters"],
                    "n_changers": diag["n_changers"],
                    "within_sd":  diag["within_sd"],
                    "std_coef":   std_c,
                    "se_type":    "driscoll_kraay_bw2",
                    "valid":      True,
                    "invalid_reason": "",
                })
            except Exception:
                pass
            # Samesample (intersect with with_gdp_sub sample)
            try:
                sub_ss = sub.merge(
                    with_gdp_sub[["iso3", "year"]], on=["iso3", "year"], how="inner")
                if len(sub_ss) > 0 and len(sub_ss) != len(sub):
                    pan_ss = sub_ss.set_index(["iso3", "year"])
                    y_ss = pan_ss[OUTCOME]
                    X_ss = sm.add_constant(pan_ss[pred_cols])
                    res_ss = PanelOLS(
                        y_ss, X_ss, entity_effects=True, time_effects=True
                    ).fit(cov_type="clustered", cluster_entity=True)
                    diag_ss = _panel_diagnostics(sub_ss, focal_col)
                    std_c_ss = _std_coef(float(res_ss.params[focal_col]),
                                          sub_ss[focal_col], sub_ss[OUTCOME])
                    results.append({
                        "tier": f"T2_{label}_samesample",
                        "year": "all",
                        "predictor": focal_col,
                        "coef": float(res_ss.params[focal_col]),
                        "se":   float(res_ss.std_errors[focal_col]),
                        "pval": float(res_ss.pvalues[focal_col]),
                        "n":    int(res_ss.nobs),
                        "r2":   float(res_ss.rsquared),
                        "n_clusters": diag_ss["n_clusters"],
                        "n_changers": diag_ss["n_changers"],
                        "within_sd":  diag_ss["within_sd"],
                        "std_coef":   std_c_ss,
                        "se_type":    "cluster_entity",
                        "valid":      True,
                        "invalid_reason": "",
                    })
            except Exception as e:
                print(f"  [T2_{label}_samesample] failed: {e}")
        except Exception as e:
            print(f"  [T2_{label}] failed: {e}")

    # ── T4: Mundlak RE with composite standalone + _mean ──────────────────
    pred_cols = [focal_col] + CONTROLS_GDP
    sub = df[[OUTCOME, "iso3", "year"] + pred_cols].dropna(
        subset=[OUTCOME] + pred_cols).copy()
    if len(sub) >= 50:
        try:
            mean_cols = []
            for c in pred_cols:
                mc = c + "_mean"
                sub[mc] = sub.groupby("iso3")[c].transform("mean")
                mean_cols.append(mc)
            mean_cols = [c for c in mean_cols if sub[c].std() > 1e-8]
            yr = pd.get_dummies(sub["year"], prefix="yr", drop_first=True).astype(float)
            sub_f = pd.concat([sub.reset_index(drop=True),
                               yr.reset_index(drop=True)], axis=1)
            yr_cols = list(yr.columns)
            pan = sub_f.set_index(["iso3", "year"])
            y = pan[OUTCOME]
            X = sm.add_constant(pan[pred_cols + mean_cols + yr_cols])
            res = RandomEffects(y, X).fit(cov_type="clustered", cluster_entity=True)
            diag = _panel_diagnostics(sub_f, focal_col)
            std_c = _std_coef(float(res.params[focal_col]),
                              sub_f[focal_col], sub_f[OUTCOME])
            # Within (focal) row
            results.append({
                "tier": "T4_mundlak_re",
                "year": "all",
                "predictor": focal_col,
                "coef": float(res.params[focal_col]),
                "se":   float(res.std_errors[focal_col]),
                "pval": float(res.pvalues[focal_col]),
                "n":    int(res.nobs),
                "r2":   float(res.rsquared),
                "n_clusters": diag["n_clusters"],
                "n_changers": diag["n_changers"],
                "within_sd":  diag["within_sd"],
                "std_coef":   std_c,
                "se_type":    "cluster_entity",
                "valid":      True,
                "invalid_reason": "",
            })
            # Between (mean) row
            mean_col = focal_col + "_mean"
            if mean_col in res.params.index:
                results.append({
                    "tier": "T4_mundlak_re",
                    "year": "all",
                    "predictor": mean_col,
                    "coef": float(res.params[mean_col]),
                    "se":   float(res.std_errors[mean_col]),
                    "pval": float(res.pvalues[mean_col]),
                    "n":    int(res.nobs),
                    "r2":   float(res.rsquared),
                    "n_clusters": diag["n_clusters"],
                    "n_changers": diag["n_changers"],
                    "within_sd":  diag["within_sd"],
                    "std_coef":   np.nan,
                    "se_type":    "cluster_entity",
                    "valid":      True,
                    "invalid_reason": "",
                })
        except Exception as e:
            print(f"  [T4_mundlak_re composite] failed: {e}")

    print(f"  Emitted {len(results)} composite rows for {focal_col}")
    return results


def phase_power_analysis(df: pd.DataFrame) -> None:
    """Power analysis for the null religious courts result.

    Computes: 95% CI for the T2_with_gdp courts coefficient,
    minimum detectable effect (MDE) at 80% power, and within-country
    variance share of the focal predictor.
    """
    print(f"\n{'='*60}")
    print("POWER ANALYSIS — NULL RESULT DIAGNOSTICS (religious courts)")
    print(f"{'='*60}")

    pred_cols = GRI_PANEL_COLS + CONTROLS_GDP
    required  = [OUTCOME, "iso3", "year"] + pred_cols
    base = df[required].dropna(subset=[OUTCOME] + pred_cols).copy()

    pan = base.set_index(["iso3", "year"])
    y = pan[OUTCOME]
    X = sm.add_constant(pan[pred_cols])
    res = PanelOLS(y, X, entity_effects=True, time_effects=True).fit(
        cov_type="clustered", cluster_entity=True
    )

    coef = res.params[FOCAL_PRED_LEGACY]
    se   = res.std_errors[FOCAL_PRED_LEGACY]
    ci_lo = coef - 1.96 * se
    ci_hi = coef + 1.96 * se

    # MDE at 80% power (two-sided, alpha=0.05): MDE = (z_alpha/2 + z_beta) * SE = 2.8 * SE
    mde = 2.8 * se

    # Within-country variance share of FOCAL_PRED
    courts = base.groupby("iso3")[FOCAL_PRED_LEGACY]
    overall_var = base[FOCAL_PRED_LEGACY].var()
    within_var  = courts.transform(lambda x: x - x.mean()).var()
    within_pct  = (within_var / overall_var * 100) if overall_var > 0 else 0

    n_countries = base["iso3"].nunique()
    n_changers  = (courts.std().fillna(0) > 0.02).sum()

    print(f"\n  T2_with_gdp results for {FOCAL_PRED_LEGACY}:")
    print(f"    Coefficient:  {coef:.5f}")
    print(f"    SE (clustered): {se:.5f}")
    print(f"    95% CI:       [{ci_lo:.4f}, {ci_hi:.4f}]")
    print(f"    MDE (80% power, alpha=0.05): {mde:.4f}")
    print(f"\n  Identifying variation:")
    print(f"    Overall variance: {overall_var:.6f}")
    print(f"    Within-country variance: {within_var:.6f} ({within_pct:.1f}% of total)")
    print(f"    Countries with courts SD > 0.02: {n_changers} / {n_countries}")
    print(f"\n  Interpretation:")
    print(f"    The data can rule out effects on women's welfare larger than")
    print(f"    |{max(abs(ci_lo), abs(ci_hi)):.3f}| units (on the 0-1 scale) in either direction.")
    print(f"    The minimum detectable effect at 80% power is {mde:.3f} units.")
    print(f"    Only {within_pct:.1f}% of courts variation is within-country,")
    print(f"    and only {n_changers}/{n_countries} countries show meaningful changes.")


def main():
    with open(LOG_PATH, "w", encoding="utf-8") as log_file:
        tee = _Tee(sys.stdout, log_file)
        old_stdout = sys.stdout
        sys.stdout = tee

        try:
            df = load_and_merge()
            correlation_matrix(df)

            all_results = []

            # Core tiers (with & without GDP, Phase 2)
            all_results.extend(tier1_cross_sectional(df))
            all_results.extend(tier2_panel_fe(df))
            all_results.extend(tier4_mundlak_re(df))
            all_results.extend(tier3_system_gmm(df))

            # Item 2 (2026-04-15): composite tier specs — standalone PanelOLS
            # with composite as focal. Emits rows under the same tier tags as
            # tier2_panel_fe / tier4_mundlak_re so the headline table picks them
            # up alongside the GRI decomposition rows. Both composite variants.
            all_results.extend(composite_tier_specs(df, FOCAL_PRED))
            all_results.extend(composite_tier_specs(df, FOCAL_PRED_PCA))
            all_results.extend(composite_tier_specs(df, "composite_secularism_real_norm"))
            all_results.extend(composite_tier_specs(df, "composite_secularism_instonly_norm"))
            all_results.extend(composite_tier_specs(df, "composite_secularism_covwt_norm"))

            vif_check(df)
            vif_by_spec(df)
            phase_power_analysis(df)

            # Robustness: exclude interpolated WVS rows
            all_results.extend(robustness_no_wvs_interp(df))

            # Phase 3: Sub-outcome
            all_results.extend(phase3_sub_outcomes(df))

            # Phase 4: Lagged
            all_results.extend(phase4_lagged(df))

            # Phase 5: Robustness
            all_results.extend(phase5_robustness(df))
            all_results.extend(phase5_legal_origins(df))

            # Phase 6: Advanced robustness
            phase6_within_variation(df)
            loo_df = phase6_loo_jackknife(df)
            all_results.extend(phase6_placebo_outcomes(df))

            # Phase 6 (apostasy): repeat LOO + placebo for significant predictor
            print(f"\n{'='*60}")
            print("PHASE 6 (APOSTASY) -- ROBUSTNESS FOR gri_apostasy_norm")
            print(f"{'='*60}")
            phase6_loo_jackknife(df, focal_pred=FOCAL_PRED_2, out_path=LOO_PATH_APO)
            all_results.extend(phase6_placebo_outcomes(df, focal_pred=FOCAL_PRED_2,
                                                       placebo_path=PLACEBO_PATH_APO))

            # Phase 6 (Item 2 robustness): legacy courts + PCA composite
            print(f"\n{'='*60}")
            print("PHASE 6 (LEGACY COURTS) -- ROBUSTNESS FOR gri_religious_courts_norm")
            print(f"{'='*60}")
            phase6_loo_jackknife(df, focal_pred=FOCAL_PRED_LEGACY,
                                 out_path=LOO_PATH_LEGACY)
            all_results.extend(phase6_placebo_outcomes(df, focal_pred=FOCAL_PRED_LEGACY,
                                                       placebo_path=PLACEBO_PATH_LEGACY))

            print(f"\n{'='*60}")
            print("PHASE 6 (PCA COMPOSITE) -- ROBUSTNESS FOR composite_secularism_pca_norm")
            print(f"{'='*60}")
            phase6_loo_jackknife(df, focal_pred=FOCAL_PRED_PCA,
                                 out_path=LOO_PATH_PCA)
            all_results.extend(phase6_placebo_outcomes(df, focal_pred=FOCAL_PRED_PCA,
                                                       placebo_path=PLACEBO_PATH_PCA))

            # Phase 7: CEDAW, sub-period/changers, Oster delta
            all_results.extend(phase7_cedaw_and_subsamples(df))
            oster_df = phase7_oster_delta(df)
            oster_df_apo = phase7_oster_delta(df, focal_pred=FOCAL_PRED_2,
                                              out_path=SPEC_PATH_APO)
            oster_df_legacy = phase7_oster_delta(df, focal_pred=FOCAL_PRED_LEGACY,
                                                 out_path=SPEC_PATH_LEGACY)
            oster_df_pca = phase7_oster_delta(df, focal_pred=FOCAL_PRED_PCA,
                                              out_path=SPEC_PATH_PCA)

            # Phase 8: Country-specific linear time trends + LO interaction
            all_results.extend(phase8_country_trends(df))
            all_results.extend(phase8_lo_interaction(df))

            # Phase 9: Methodological improvements
            print(f"\n{'='*60}")
            print("PHASE 9 -- METHODOLOGICAL IMPROVEMENTS")
            print(f"{'='*60}")
            all_results.extend(phase9_event_study(df))
            all_results.extend(phase9_event_study(df, focal_pred=FOCAL_PRED_2,
                                                   out_path=EVENTSTUDY_PATH_APO))
            all_results.extend(phase9_event_study(df, focal_pred=FOCAL_PRED_LEGACY,
                                                   out_path=EVENTSTUDY_PATH_LEGACY))
            all_results.extend(phase9_event_study(df, focal_pred=FOCAL_PRED_PCA,
                                                   out_path=EVENTSTUDY_PATH_PCA))
            all_results.extend(phase9_wild_bootstrap(df))
            all_results.extend(phase9_wild_bootstrap(df, focal_pred=FOCAL_PRED_2))
            all_results.extend(phase9_wild_bootstrap(
                df, focal_pred="composite_secularism_real_norm"))
            all_results.extend(phase9_driscoll_kraay(df))
            all_results.extend(phase9_mundlak_cre(df))
            all_results.extend(phase9_male_composite_placebo(df))
            oster_sens_df = phase9_oster_sensitivity(df)
            if not oster_sens_df.empty:
                oster_sens_df.to_csv(OSTER_SENS_PATH, index=False, float_format="%.6f")
                print(f"  Oster sensitivity saved -> {OSTER_SENS_PATH}")

            oster_sens_df_apo = phase9_oster_sensitivity(df, focal_pred=FOCAL_PRED_2,
                                                          out_path=OSTER_SENS_PATH_APO)
            if not oster_sens_df_apo.empty:
                oster_sens_df_apo.to_csv(OSTER_SENS_PATH_APO, index=False, float_format="%.6f")
                print(f"  Oster sensitivity (apostasy) saved -> {OSTER_SENS_PATH_APO}")

            oster_sens_df_legacy = phase9_oster_sensitivity(df, focal_pred=FOCAL_PRED_LEGACY,
                                                             out_path=OSTER_SENS_PATH_LEGACY)
            if not oster_sens_df_legacy.empty:
                oster_sens_df_legacy.to_csv(OSTER_SENS_PATH_LEGACY, index=False, float_format="%.6f")
                print(f"  Oster sensitivity (legacy courts) saved -> {OSTER_SENS_PATH_LEGACY}")

            oster_sens_df_pca = phase9_oster_sensitivity(df, focal_pred=FOCAL_PRED_PCA,
                                                          out_path=OSTER_SENS_PATH_PCA)
            if not oster_sens_df_pca.empty:
                oster_sens_df_pca.to_csv(OSTER_SENS_PATH_PCA, index=False, float_format="%.6f")
                print(f"  Oster sensitivity (PCA) saved -> {OSTER_SENS_PATH_PCA}")

            if not oster_df.empty:
                oster_df.to_csv(SPEC_PATH, index=False, float_format="%.6f")
                print(f"\n  Oster spec table saved -> {SPEC_PATH}")
            if not oster_df_apo.empty:
                oster_df_apo.to_csv(SPEC_PATH_APO, index=False, float_format="%.6f")
                print(f"  Oster spec table (apostasy) saved -> {SPEC_PATH_APO}")
            if oster_df_legacy is not None and not oster_df_legacy.empty:
                oster_df_legacy.to_csv(SPEC_PATH_LEGACY, index=False, float_format="%.6f")
                print(f"  Oster spec table (legacy courts) saved -> {SPEC_PATH_LEGACY}")
            if oster_df_pca is not None and not oster_df_pca.empty:
                oster_df_pca.to_csv(SPEC_PATH_PCA, index=False, float_format="%.6f")
                print(f"  Oster spec table (PCA) saved -> {SPEC_PATH_PCA}")

            # Phase 10: Regional heterogeneity + alternative external outcomes
            print(f"\n{'='*60}")
            print("PHASE 10 -- REGIONAL HETEROGENEITY & GENDER GAP OUTCOMES")
            print(f"{'='*60}")
            all_results.extend(phase10_regional_heterogeneity(df))
            all_results.extend(phase10_gender_gap_outcomes(df))

            # WBL group score analysis (scoring pipeline)
            phase_wbl_groups()

            print(f"\n{'='*60}")
            print("RESULTS SUMMARY")
            print(f"{'='*60}")
            save_results(all_results)

            # Build headline table (post-processing on results.csv)
            try:
                import subprocess
                subprocess.run([sys.executable,
                                os.path.join(ROOT, "tools/build_headline_table.py")],
                               check=False)
            except Exception as e:
                print(f"  [headline table build failed: {e}]")

        finally:
            sys.stdout = old_stdout

    print(f"Log saved -> {LOG_PATH}")


if __name__ == "__main__":
    main()
