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


def build_secularism_composite(df: pd.DataFrame) -> pd.DataFrame:
    """Add composite_secularism_norm and composite_secularism_pca_norm to df.

    Three dimensions, all oriented so higher = more religion / less secular:
      institutional: 6 GRI cols (incl. gri_gov_favour_norm)
      attitudinal:   v2clrelig_norm (SIGN-FLIPPED before z-scoring)
      behavioural:   4 WVS cols (imprel, godimp, godbel, confch)

    Equal-weight variant (headline):
      Z-score within each dimension (NaN-aware, skipna). Average the
      available dimension z-scores per row (dimension-fallback: if one
      dimension is entirely NaN for a row, use the mean of the remaining
      two). Pass through robust_minmax to [0, 1].

    PCA variant (robustness):
      Column-mean-impute each input column across its observed values, then
      standardise (z-score each col), then fit PCA(n_components=1) on the
      11-col matrix. Post-hoc sign-align so the loading on
      gri_state_religion_norm is positive. Pass through robust_minmax to
      [0, 1].

      CAVEAT: Column-mean imputation on heterogeneous-coverage inputs
      (WVS coverage ~44% pre-interpolation, GRI 100%) causes imputed
      columns to have lower post-fill variance. The first PC therefore
      loads more heavily on the fully-covered institutional columns,
      degenerating the PCA toward a GRI-weighted average. This is a known
      limitation of the PCA variant; the equal-weight composite is the
      headline for that reason.

    Sign-alignment is verified by asserting
    corr(composite, gri_state_religion_norm) > 0 after robust_minmax; if
    the check fails the composite is flipped and a warning is logged.

    Columns added:
      composite_secularism_norm, composite_secularism_pca_norm
    """
    from sklearn.decomposition import PCA  # lazy import

    out = df.copy()

    # ── 1. Sign-flip v2clrelig so every input is oriented "higher = more religion"
    if "v2clrelig_norm" in out.columns:
        v_flipped = 1.0 - out["v2clrelig_norm"]
    else:
        v_flipped = pd.Series(np.nan, index=out.index)

    # ── 2. Equal-weight z-score composite ───────────────────────────────
    inst_z = sum(_zscore_nan(out[c]) for c in COMPOSITE_INSTITUTIONAL_COLS
                 if c in out.columns) / \
             sum(1 for c in COMPOSITE_INSTITUTIONAL_COLS if c in out.columns)
    att_z  = _zscore_nan(v_flipped)
    beh_z  = sum(_zscore_nan(out[c]) for c in COMPOSITE_BEHAVIOURAL_COLS
                 if c in out.columns) / \
             sum(1 for c in COMPOSITE_BEHAVIOURAL_COLS if c in out.columns)

    # Dimension-fallback: row-average only the non-NaN dimension z-scores
    dims = pd.DataFrame({"inst": inst_z, "att": att_z, "beh": beh_z})
    composite_raw = dims.mean(axis=1, skipna=True)  # pandas skipna handles fallback
    composite_norm = robust_minmax(composite_raw)

    # Sign-align check
    if "gri_state_religion_norm" in out.columns:
        tmp = pd.DataFrame({"c": composite_norm,
                            "g": out["gri_state_religion_norm"]}).dropna()
        if len(tmp) > 10:
            corr_val = tmp["c"].corr(tmp["g"])
            if corr_val < 0:
                print(f"  [build_secularism_composite] WARNING: equal-weight "
                      f"composite had negative corr with gri_state_religion "
                      f"({corr_val:.3f}); flipping sign.")
                composite_norm = 1.0 - composite_norm

    out["composite_secularism_norm"] = composite_norm

    # ── 3. PCA composite (column-mean-impute → standardise → first PC) ──
    pca_cols = (COMPOSITE_INSTITUTIONAL_COLS
                + ["v2clrelig_norm_flipped"]
                + COMPOSITE_BEHAVIOURAL_COLS)
    pca_df = pd.DataFrame(index=out.index)
    for c in COMPOSITE_INSTITUTIONAL_COLS + COMPOSITE_BEHAVIOURAL_COLS:
        if c in out.columns:
            pca_df[c] = out[c]
        else:
            pca_df[c] = np.nan
    pca_df["v2clrelig_norm_flipped"] = v_flipped

    # Column-mean impute
    means = pca_df.mean(axis=0, skipna=True)
    pca_imp = pca_df.fillna(means)

    # Standardise each column (z-score)
    stds = pca_imp.std(axis=0, skipna=False)
    stds_safe = stds.where(stds > 1e-12, 1.0)
    pca_std = (pca_imp - pca_imp.mean(axis=0)) / stds_safe

    try:
        pca = PCA(n_components=1)
        pc1 = pca.fit_transform(pca_std.values).ravel()
        loadings = pd.Series(pca.components_[0], index=pca_std.columns)
    except Exception as e:
        print(f"  [build_secularism_composite] PCA failed: {e}; "
              "writing NaN column")
        out["composite_secularism_pca_norm"] = np.nan
        return out

    # Sign-align: loading on gri_state_religion_norm should be positive
    if "gri_state_religion_norm" in loadings.index and \
            loadings["gri_state_religion_norm"] < 0:
        pc1 = -pc1
        loadings = -loadings

    pc1_series = pd.Series(pc1, index=pca_std.index)
    # Mask rows where ALL original inputs were NaN (nothing to say about them)
    all_nan_mask = pca_df.isna().all(axis=1)
    pc1_series.loc[all_nan_mask] = np.nan

    composite_pca_norm = robust_minmax(pc1_series)

    # Belt-and-braces sign check on the normalised output
    if "gri_state_religion_norm" in out.columns:
        tmp = pd.DataFrame({"c": composite_pca_norm,
                            "g": out["gri_state_religion_norm"]}).dropna()
        if len(tmp) > 10:
            corr_val = tmp["c"].corr(tmp["g"])
            if corr_val < 0:
                print(f"  [build_secularism_composite] WARNING: PCA "
                      f"composite had negative corr with gri_state_religion "
                      f"({corr_val:.3f}); flipping sign.")
                composite_pca_norm = 1.0 - composite_pca_norm

    out["composite_secularism_pca_norm"] = composite_pca_norm

    # Log PCA loadings for audit trail
    print(f"  [build_secularism_composite] PCA first-PC explained variance: "
          f"{pca.explained_variance_ratio_[0]:.3f}")
    print(f"  [build_secularism_composite] PCA loadings:")
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
