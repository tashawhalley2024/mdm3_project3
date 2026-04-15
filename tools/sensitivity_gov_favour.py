"""Empirical sensitivity of the composite to including gri_gov_favour_norm.

One-off diagnostic. Builds a variant of the equal-weight composite with
gri_gov_favour_norm excluded from the institutional dimension, compares
to the main composite at T1 2020 with_gdp and T4 Mundlak (within and
between), and writes results/gov_favour_sensitivity.csv.

Context: gri_gov_favour_norm was in data/predictors.csv from the start
but silently absent from GRI_PANEL_COLS until commit 77417d9 restored it.
This tool quantifies how much the composite's headline coefficients move
when the column is in vs out of the institutional dimension, so the
methodology paper footnote can quote the delta.

This is a pure sensitivity check: the pipeline continues to include
gri_gov_favour_norm. Do not wire the excluded variant into the main
pipeline.

Note: the comparison is valid only if the 6 GRI sub-items share the same
NaN mask in predictors.csv (so main and excluded estimate on identical
country-years). This holds empirically as of the 2026-04-15 Pew GRI
release and is tolerated here. If a future Pew update breaks the
co-missingness, the comparison will silently shift and this script must
be rerun with a same-sample guard.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm
from linearmodels.panel import RandomEffects

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from analysis.utils import (
    COMPOSITE_BEHAVIOURAL_COLS,
    COMPOSITE_INSTITUTIONAL_COLS,
    _zscore_nan,
    robust_minmax,
)

OUTCOME = "wbl_treatment_index"
CONTROLS_GDP = ["v2x_rule_norm", "v2x_civlib_norm", "v2x_egal_norm", "log_gdppc_norm"]


def _build_equal_weight_inline(df: pd.DataFrame, inst_cols: list[str]) -> pd.Series:
    """Inline equal-weight composite over the given institutional cols."""
    if "v2clrelig_norm" in df.columns:
        v_flipped = 1.0 - df["v2clrelig_norm"]
    else:
        v_flipped = pd.Series(np.nan, index=df.index)

    inst_present = [c for c in inst_cols if c in df.columns]
    beh_present = [c for c in COMPOSITE_BEHAVIOURAL_COLS if c in df.columns]

    inst_z = (sum(_zscore_nan(df[c]) for c in inst_present) / len(inst_present)
              if inst_present else pd.Series(np.nan, index=df.index))
    att_z = _zscore_nan(v_flipped)
    beh_z = (sum(_zscore_nan(df[c]) for c in beh_present) / len(beh_present)
             if beh_present else pd.Series(np.nan, index=df.index))

    dims = pd.DataFrame({"inst": inst_z, "att": att_z, "beh": beh_z})
    composite_raw = dims.mean(axis=1, skipna=True)
    composite_norm = robust_minmax(composite_raw)

    if "gri_state_religion_norm" in df.columns:
        tmp = pd.DataFrame({"c": composite_norm,
                            "g": df["gri_state_religion_norm"]}).dropna()
        if len(tmp) > 10 and tmp["c"].corr(tmp["g"]) < 0:
            composite_norm = 1.0 - composite_norm

    return composite_norm


def _t1_2020(df: pd.DataFrame, focal: str) -> dict:
    sub = df[df["year"] == 2020].copy()
    pred_cols = [focal] + CONTROLS_GDP
    s = sub.dropna(subset=[OUTCOME] + pred_cols).copy()
    X = sm.add_constant(s[pred_cols])
    y = s[OUTCOME]
    res = sm.OLS(y, X).fit(cov_type="HC3")
    return {
        "coef": float(res.params[focal]),
        "se": float(res.bse[focal]),
        "pval": float(res.pvalues[focal]),
        "n": int(res.nobs),
    }


def _t4_mundlak(df: pd.DataFrame, focal: str) -> tuple[dict, dict]:
    """Return (within_row, between_row) for the focal under Mundlak RE."""
    pred_cols = [focal] + CONTROLS_GDP
    sub = df[[OUTCOME, "iso3", "year"] + pred_cols].dropna(
        subset=[OUTCOME] + pred_cols).copy()
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
    within = {
        "coef": float(res.params[focal]),
        "se":   float(res.std_errors[focal]),
        "pval": float(res.pvalues[focal]),
        "n":    int(res.nobs),
    }
    mean_col = focal + "_mean"
    between = {
        "coef": float(res.params[mean_col]),
        "se":   float(res.std_errors[mean_col]),
        "pval": float(res.pvalues[mean_col]),
        "n":    int(res.nobs),
    }
    return within, between


def main() -> int:
    preds_path = os.path.join(ROOT, "data", "predictors.csv")
    outcome_path = os.path.join(ROOT, "data", "outcome_wbl.csv")
    aux_path = os.path.join(ROOT, "data", "outcome_composite.csv")
    out_path = os.path.join(ROOT, "results", "gov_favour_sensitivity.csv")

    preds = pd.read_csv(preds_path)
    outcome = pd.read_csv(outcome_path)
    df = outcome.merge(preds, on=["iso3", "year"], how="left")
    aux_cols = [c for c in CONTROLS_GDP if c not in df.columns]
    if aux_cols:
        aux = pd.read_csv(aux_path)[["iso3", "year"] + aux_cols]
        df = df.merge(aux, on=["iso3", "year"], how="left")

    inst_full = list(COMPOSITE_INSTITUTIONAL_COLS)
    inst_excl = [c for c in inst_full if c != "gri_gov_favour_norm"]

    df["composite_main"] = _build_equal_weight_inline(df, inst_full)
    df["composite_excl"] = _build_equal_weight_inline(df, inst_excl)

    def _row(spec, main, excl):
        return {
            "spec": spec,
            "coef_main": main["coef"],
            "coef_excl": excl["coef"],
            "delta_abs": excl["coef"] - main["coef"],
            "delta_pct": 100.0 * (excl["coef"] - main["coef"]) / main["coef"],
            "pval_main": main["pval"],
            "pval_excl": excl["pval"],
            "n": main["n"],
        }

    rows = []
    t1_main = _t1_2020(df, "composite_main")
    t1_excl = _t1_2020(df, "composite_excl")
    rows.append(_row("T1_2020_with_gdp", t1_main, t1_excl))

    w_main, b_main = _t4_mundlak(df, "composite_main")
    w_excl, b_excl = _t4_mundlak(df, "composite_excl")
    rows.append(_row("T4_mundlak_within", w_main, w_excl))
    rows.append(_row("T4_mundlak_between", b_main, b_excl))

    out = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    out.to_csv(out_path, index=False, float_format="%.4f")
    print(f"Wrote {out_path}")
    print(out.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
