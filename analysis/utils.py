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
