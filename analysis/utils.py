import hashlib
import os

import numpy as np
import pandas as pd


def linear_slope(x, y) -> float:
    """Return slope of y on x using simple OLS formula (no sklearn)."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    x = x - x.mean()
    denom = (x ** 2).sum()
    if denom == 0:
        return 0.0
    return float((x * y).sum() / denom)


def classify_delta(delta5: float) -> str:
    if delta5 >= 10:
        return "rapid deterioration"
    if delta5 <= -10:
        return "rapid improvement"
    return "stable"


def winsorise(s: pd.Series, lo: float = 0.01, hi: float = 0.99) -> pd.Series:
    """Clip to [lo, hi] quantiles computed on non-null values."""
    q_lo = s.quantile(lo)
    q_hi = s.quantile(hi)
    return s.clip(lower=q_lo, upper=q_hi)


def robust_minmax(s: pd.Series, winsor: bool = True) -> pd.Series:
    """Winsorise then min-max normalise to [0,1]. Missing -> NaN."""
    if winsor:
        s = winsorise(s)
    lo, hi = s.min(), s.max()
    if hi == lo:
        return pd.Series(np.nan, index=s.index)
    return (s - lo) / (hi - lo)


# Dimension memberships for the composite secularism index (Item 2).
# Orientation after construction: higher = more religion / less secular.
# v2clrelig_norm has OPPOSITE orientation in predictors.csv (higher = more
# secular freedom per predictors_README.md sub-group 3a), so it is sign-flipped
# before entering the composite.
COMPOSITE_INSTITUTIONAL_COLS = [
    "gri_state_religion_norm",
    "gri_gov_favour_norm",
    "gri_religious_law_norm",
    "gri_religious_courts_norm",
    "gri_blasphemy_norm",
    "gri_apostasy_norm",
]
COMPOSITE_ATTITUDINAL_COLS = ["v2clrelig_norm"]   # sign-flipped
COMPOSITE_BEHAVIOURAL_COLS = [
    "wvs_imprel_norm",
    "wvs_godimp_norm",
    "wvs_godbel_norm",
    "wvs_confch_norm",
]


def _zscore_nan(s: pd.Series) -> pd.Series:
    """Z-score a Series, skipping NaN for mean/std but preserving NaN rows."""
    mu = s.mean(skipna=True)
    sd = s.std(skipna=True)
    if sd is None or np.isnan(sd) or sd == 0:
        return pd.Series(np.nan, index=s.index)
    return (s - mu) / sd


def _prepare_composite_inputs(
    df: pd.DataFrame,
    *,
    drop_interpolated_wvs: bool = False,
) -> pd.DataFrame:
    """Return the 11-col prepared frame for composite construction.

    v2clrelig is sign-flipped (stored as v2clrelig_norm_flipped). If
    drop_interpolated_wvs is True, the 4 WVS cols are masked to NaN on
    rows where wvs_interpolated == 1.
    """
    if "v2clrelig_norm" in df.columns:
        v_flipped = 1.0 - df["v2clrelig_norm"]
    else:
        v_flipped = pd.Series(np.nan, index=df.index)

    prepared = pd.DataFrame(index=df.index)
    for c in COMPOSITE_INSTITUTIONAL_COLS:
        prepared[c] = df[c] if c in df.columns else np.nan
    prepared["v2clrelig_norm_flipped"] = v_flipped
    for c in COMPOSITE_BEHAVIOURAL_COLS:
        prepared[c] = df[c] if c in df.columns else np.nan

    if drop_interpolated_wvs and "wvs_interpolated" in df.columns:
        mask = df["wvs_interpolated"] == 1
        for c in COMPOSITE_BEHAVIOURAL_COLS:
            if c in prepared.columns:
                prepared.loc[mask, c] = np.nan

    return prepared


def _compute_coverage_weights(df: pd.DataFrame) -> tuple:
    """Panel-wide non-null row fractions per dimension.

    Returns (w_inst, w_att, w_beh). WVS coverage uses wvs_interpolated == 0
    (pre-interpolation wave years only) when that column is present, so the
    coverage variant remains meaningful even when the main composite is
    built post-interpolation.
    """
    inst_cols = [c for c in COMPOSITE_INSTITUTIONAL_COLS if c in df.columns]
    if inst_cols:
        w_inst = float(df[inst_cols].notna().all(axis=1).mean())
    else:
        w_inst = 0.0

    if "v2clrelig_norm" in df.columns:
        w_att = float(df["v2clrelig_norm"].notna().mean())
    else:
        w_att = 0.0

    beh_cols = [c for c in COMPOSITE_BEHAVIOURAL_COLS if c in df.columns]
    if beh_cols:
        beh_observed = df[beh_cols].notna().all(axis=1)
        if "wvs_interpolated" in df.columns:
            beh_real = df["wvs_interpolated"] == 0
            w_beh = float((beh_observed & beh_real).mean())
        else:
            w_beh = float(beh_observed.mean())
    else:
        w_beh = 0.0

    return w_inst, w_att, w_beh


def _build_equal_weight(
    prepared: pd.DataFrame,
    *,
    weighting: str = "equal",
    coverage_weights: tuple = None,
    sign_align_series: pd.Series = None,
) -> pd.Series:
    """Build the equal/instonly/covwt composite from prepared 11-col frame.

    weighting:
      'equal'             -- row-mean of (inst_z, att_z, beh_z), dimension-fallback.
      'institutional_only' -- return inst_z only; att/beh dropped.
      'coverage'          -- weighted sum by coverage_weights (from the
                             original df), renormalised over observed
                             dimensions per row.

    Returns a Series on [0, 1] after robust_minmax, sign-aligned against
    sign_align_series (typically gri_state_religion_norm).
    """
    inst_cols = [c for c in COMPOSITE_INSTITUTIONAL_COLS if c in prepared.columns]
    beh_cols = [c for c in COMPOSITE_BEHAVIOURAL_COLS if c in prepared.columns]

    inst_z = (sum(_zscore_nan(prepared[c]) for c in inst_cols) / len(inst_cols)
              if inst_cols else pd.Series(np.nan, index=prepared.index))
    att_z = (_zscore_nan(prepared["v2clrelig_norm_flipped"])
             if "v2clrelig_norm_flipped" in prepared.columns
             else pd.Series(np.nan, index=prepared.index))
    beh_z = (sum(_zscore_nan(prepared[c]) for c in beh_cols) / len(beh_cols)
             if beh_cols else pd.Series(np.nan, index=prepared.index))

    if weighting == "equal":
        dims = pd.DataFrame({"inst": inst_z, "att": att_z, "beh": beh_z})
        composite_raw = dims.mean(axis=1, skipna=True)
    elif weighting == "institutional_only":
        composite_raw = inst_z
    elif weighting == "coverage":
        if coverage_weights is None:
            raise ValueError("coverage_weights required for weighting='coverage'")
        w_inst, w_att, w_beh = coverage_weights
        dims = pd.DataFrame({"inst": inst_z, "att": att_z, "beh": beh_z})
        weights = pd.Series({"inst": w_inst, "att": w_att, "beh": w_beh})
        dims_mask = dims.notna().astype(float)
        weighted_sum = (dims.fillna(0.0) * weights).sum(axis=1)
        denom = (dims_mask * weights).sum(axis=1)
        composite_raw = weighted_sum / denom.where(denom > 0, np.nan)
    else:
        raise ValueError(f"Unknown weighting: {weighting!r}")

    composite_norm = robust_minmax(composite_raw)

    if sign_align_series is not None:
        tmp = pd.DataFrame({"c": composite_norm,
                            "g": sign_align_series}).dropna()
        if len(tmp) > 10:
            corr_val = tmp["c"].corr(tmp["g"])
            if corr_val < 0:
                print(f"  [build_secularism_composite] WARNING: equal-weight "
                      f"composite (weighting={weighting}) had negative corr "
                      f"with gri_state_religion ({corr_val:.3f}); flipping.")
                composite_norm = 1.0 - composite_norm

    return composite_norm


def _build_pca(
    prepared: pd.DataFrame,
    *,
    imputation: str = "em",
    sign_align_series: pd.Series = None,
    seed: int = 42,
) -> tuple:
    """Build PCA composite from the prepared 11-col frame.

    imputation:
      'mean'     -- column-mean impute (legacy; biased toward high-coverage cols).
      'listwise' -- drop any row with a NaN input; PCA fit on complete cases.
                    Rows outside the complete-case set get NaN in the output.
      'em'       -- sklearn IterativeImputer (EM-style round-robin regression
                    imputation); preserves N while relaxing the mean-imputation
                    variance shrinkage.

    Returns (composite_norm, loadings, explained_variance_ratio, n_used).
    """
    from sklearn.decomposition import PCA

    pca_df = prepared.copy()

    if imputation == "mean":
        means = pca_df.mean(axis=0, skipna=True)
        pca_imp = pca_df.fillna(means)
        fit_idx = pca_imp.index
    elif imputation == "listwise":
        pca_imp = pca_df.dropna()
        fit_idx = pca_imp.index
    elif imputation == "em":
        from sklearn.experimental import enable_iterative_imputer  # noqa: F401
        from sklearn.impute import IterativeImputer
        imp = IterativeImputer(random_state=seed, max_iter=50, sample_posterior=False)
        arr = imp.fit_transform(pca_df.values)
        pca_imp = pd.DataFrame(arr, columns=pca_df.columns, index=pca_df.index)
        fit_idx = pca_imp.index
    else:
        raise ValueError(f"Unknown imputation: {imputation!r}")

    empty = pd.Series(np.nan, index=prepared.index)
    nan_loadings = pd.Series(np.nan, index=pca_df.columns)
    if len(pca_imp) < 10:
        return empty, nan_loadings, float("nan"), len(pca_imp)

    stds = pca_imp.std(axis=0)
    stds_safe = stds.where(stds > 1e-12, 1.0)
    pca_std = (pca_imp - pca_imp.mean(axis=0)) / stds_safe

    try:
        pca = PCA(n_components=1)
        pc1 = pca.fit_transform(pca_std.values).ravel()
        loadings = pd.Series(pca.components_[0], index=pca_std.columns)
        expvar = float(pca.explained_variance_ratio_[0])
    except Exception as e:
        print(f"  [build_secularism_composite] PCA ({imputation}) failed: {e}")
        return empty, nan_loadings, float("nan"), len(pca_imp)

    if ("gri_state_religion_norm" in loadings.index
            and loadings["gri_state_religion_norm"] < 0):
        pc1 = -pc1
        loadings = -loadings

    pc1_series = pd.Series(np.nan, index=prepared.index)
    pc1_series.loc[fit_idx] = pc1

    if imputation != "listwise":
        all_nan_mask = pca_df.isna().all(axis=1)
        pc1_series.loc[all_nan_mask] = np.nan

    composite_pca_norm = robust_minmax(pc1_series)

    if sign_align_series is not None:
        tmp = pd.DataFrame({"c": composite_pca_norm,
                            "g": sign_align_series}).dropna()
        if len(tmp) > 10:
            corr_val = tmp["c"].corr(tmp["g"])
            if corr_val < 0:
                print(f"  [build_secularism_composite] WARNING: PCA composite "
                      f"(imputation={imputation}) had negative corr with "
                      f"gri_state_religion ({corr_val:.3f}); flipping.")
                composite_pca_norm = 1.0 - composite_pca_norm

    return composite_pca_norm, loadings, expvar, len(pca_imp)


def build_secularism_composite(
    df: pd.DataFrame,
    *,
    drop_interpolated_wvs: bool = False,
    weighting: str = "equal",
    pca_imputation: str = "em",
    output_name: str = "composite_secularism_norm",
    pca_output_name: str = "composite_secularism_pca_norm",
    build_pca: bool = True,
) -> pd.DataFrame:
    """Attach composite secularism columns to df.

    Three dimensions, all oriented so higher = more religion / less secular:
      institutional: 6 GRI cols (incl. gri_gov_favour_norm)
      attitudinal:   v2clrelig_norm (SIGN-FLIPPED before z-scoring)
      behavioural:   4 WVS cols (imprel, godimp, godbel, confch)

    Parameters
    ----------
    drop_interpolated_wvs : bool
        If True, mask the 4 WVS cols to NaN on rows with wvs_interpolated == 1
        before building the behavioural dimension. Produces the 'real' variant.
    weighting : {'equal', 'institutional_only', 'coverage'}
        'equal' (default) -- row-mean of the three dimension z-scores, with
        pandas dimension-fallback if one dimension is NaN for a row.
        'institutional_only' -- drop att/beh dimensions; composite = inst_z.
        'coverage' -- weight each dimension by its panel-wide non-null row
        fraction. WVS weight uses pre-interpolation coverage
        (wvs_interpolated == 0), so the variant is meaningful even when the
        main composite is built on post-interpolation WVS.
    pca_imputation : {'mean', 'listwise', 'em'}
        Imputation strategy for the PCA robustness column. 'em' (default) uses
        sklearn IterativeImputer; 'listwise' drops rows with any NaN;
        'mean' is the legacy column-mean imputation kept for comparison.
    output_name : str
        Column name for the equal-weight / instonly / covwt composite.
    pca_output_name : str
        Column name for the PCA composite.
    build_pca : bool
        If False, skip the PCA variant (used for secondary composites).

    Sign-alignment: for each composite, the final Series is verified to
    correlate positively with gri_state_religion_norm on the row intersection;
    if the check fails the Series is flipped and a warning is printed.
    """
    out = df.copy()
    prepared = _prepare_composite_inputs(
        out, drop_interpolated_wvs=drop_interpolated_wvs,
    )
    sign_anchor = (out["gri_state_religion_norm"]
                   if "gri_state_religion_norm" in out.columns else None)

    coverage_weights = None
    if weighting == "coverage":
        coverage_weights = _compute_coverage_weights(out)

    composite_norm = _build_equal_weight(
        prepared,
        weighting=weighting,
        coverage_weights=coverage_weights,
        sign_align_series=sign_anchor,
    )
    out[output_name] = composite_norm

    if build_pca:
        composite_pca_norm, loadings, expvar, n_used = _build_pca(
            prepared, imputation=pca_imputation, sign_align_series=sign_anchor,
        )
        out[pca_output_name] = composite_pca_norm

        if loadings.notna().any():
            print(f"  [build_secularism_composite] PCA ({pca_imputation}) "
                  f"first-PC explained variance: {expvar:.3f} (N={n_used})")
            print(f"  [build_secularism_composite] PCA ({pca_imputation}) "
                  f"loadings:")
            for col, load in loadings.sort_values(ascending=False).items():
                print(f"    {col:40s} {load:+.3f}")

    return out


def within_country_interpolate(
    df: pd.DataFrame,
    group_col: str,
    year_col: str,
    value_cols: list,
    method: str = "linear",
    ffill_limit: int = 3,
    bfill_limit: int = 3,
) -> pd.DataFrame:
    """Linear interpolation within country groups; then ffill/bfill for edges."""
    df = df.copy().sort_values([group_col, year_col])

    def _interp(grp):
        grp = grp.set_index(year_col)
        for col in value_cols:
            if col in grp.columns:
                grp[col] = (
                    grp[col]
                    .interpolate(method=method)
                    .ffill(limit=ffill_limit)
                    .bfill(limit=bfill_limit)
                )
        return grp.reset_index()

    return df.groupby(group_col, group_keys=False).apply(_interp).reset_index(drop=True)


def pipeline_checksum(df: pd.DataFrame, path: str, expected_rows: int = None) -> str:
    """Write SHA-256 of CSV to data/processed/checksums.txt. Assert rows if given."""
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    sha = hashlib.sha256(csv_bytes).hexdigest()
    if expected_rows is not None:
        assert len(df) == expected_rows, (
            f"Row count mismatch for {path}: expected {expected_rows}, got {len(df)}"
        )
    _src_dir = os.path.dirname(os.path.abspath(__file__))
    _root = os.path.dirname(_src_dir)
    checksum_path = os.path.join(_root, "data", "processed", "checksums.txt")
    os.makedirs(os.path.dirname(checksum_path), exist_ok=True)
    with open(checksum_path, "a", encoding="utf-8") as f:
        f.write(f"{os.path.basename(path)}\t{sha}\t{len(df)} rows\n")
    return sha
