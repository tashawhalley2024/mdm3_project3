"""Three-way comparison of PCA imputation strategies for the composite.

Reads data/predictors.csv, runs build_secularism_composite under mean,
listwise, and EM imputation, and writes results/pca_loadings_comparison.csv
with PC1 loadings side-by-side plus per-variant explained variance and N.

This is a one-off diagnostic tool, not part of the main pipeline. The paper's
PCA caveat paragraph (§2.2) references the output.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from analysis.utils import (
    _build_pca,
    _prepare_composite_inputs,
)


def main() -> int:
    preds_path = os.path.join(ROOT, "data", "predictors.csv")
    outcome_path = os.path.join(ROOT, "data", "outcome_wbl.csv")
    out_path = os.path.join(ROOT, "results", "pca_loadings_comparison.csv")

    preds = pd.read_csv(preds_path)
    outcome = pd.read_csv(outcome_path)[["iso3", "year"]]
    df = outcome.merge(preds, on=["iso3", "year"], how="left")
    prepared = _prepare_composite_inputs(df)
    sign_anchor = (df["gri_state_religion_norm"]
                   if "gri_state_religion_norm" in df.columns else None)

    rows = []
    meta = {}
    for imputation in ("mean", "listwise", "em"):
        _composite, loadings, expvar, n = _build_pca(
            prepared, imputation=imputation, sign_align_series=sign_anchor,
        )
        meta[imputation] = {"expvar": expvar, "n": n}
        for col, load in loadings.items():
            rows.append({"input": col,
                         "imputation": imputation,
                         "loading": float(load) if pd.notna(load) else np.nan})

    long = pd.DataFrame(rows)
    wide = long.pivot(index="input", columns="imputation", values="loading")
    wide = wide.rename(columns={c: f"loading_{c}" for c in wide.columns})
    wide = wide.reset_index()

    meta_row_expvar = {"input": "_explained_variance_ratio"}
    meta_row_n = {"input": "_n_rows_fit"}
    for imputation in ("mean", "listwise", "em"):
        meta_row_expvar[f"loading_{imputation}"] = meta[imputation]["expvar"]
        meta_row_n[f"loading_{imputation}"] = meta[imputation]["n"]
    meta_df = pd.DataFrame([meta_row_expvar, meta_row_n])

    out = pd.concat([wide, meta_df], ignore_index=True)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    out.to_csv(out_path, index=False, float_format="%.4f")

    print(f"Wrote {out_path} ({len(out)} rows)")
    for imputation, m in meta.items():
        print(f"  {imputation:>9s}: PC1 expvar={m['expvar']:.3f}  N={m['n']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
