#!/usr/bin/env python3
"""
build_headline_table.py
=======================
Builds the one-page headline table most readers actually want: for each focal
predictor (religious courts, apostasy), show coef / SE / p / Bonferroni / BH /
N / n_clusters / n_changers / within-SD / std_coef across the canonical
specifications. Reads results/results.csv (after run_analysis.py has run) and
writes results/headline_table.csv plus a rendered results/headline_table.md.

Usage (from repo root):
    python tools/build_headline_table.py
"""
from __future__ import annotations
import os
import sys
import pandas as pd
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results/results.csv")
OUT_CSV = os.path.join(ROOT, "results/headline_table.csv")
OUT_MD  = os.path.join(ROOT, "results/headline_table.md")

FOCAL_PREDS = [
    # Item 2 (2026-04-15): composite is the new headline; legacy courts
    # and apostasy are preserved as robustness focals; other GRI sub-items
    # appear as secondary rows for completeness.
    "composite_secularism_norm",            # headline: equal-weight z-score
    "composite_secularism_pca_norm",        # robustness: PCA variant
    "gri_apostasy_norm",                    # strongest sub-item
    "gri_religious_courts_norm",            # legacy headline, preserved
    "gri_gov_favour_norm",                  # newly activated in GRI_PANEL_COLS
    "gri_state_religion_norm",
    "gri_religious_law_norm",
    "gri_blasphemy_norm",
]

# Specs that go into the headline table, in order.
# Each entry is (label_for_table, tier_tag, year_filter_or_None,
#                predictor_transform).
# predictor_transform lets us pull e.g. "gri_apostasy_norm_mean" from the
# Mundlak RE spec when reporting the between-effect on gri_apostasy_norm.
HEADLINE_SPECS = [
    ("T1_2014_with_gdp",              "T1_with_gdp",               "2014", None),
    ("T1_2020_with_gdp",              "T1_with_gdp",               "2020", None),
    ("T2_no_gdp",                     "T2_no_gdp",                 "all",  None),
    ("T2_with_gdp",                   "T2_with_gdp",               "all",  None),
    ("T2_no_gdp_samesample",          "T2_no_gdp_samesample",      "all",  None),
    ("T2_with_gdp_samesample",        "T2_with_gdp_samesample",    "all",  None),
    ("T2_with_gdp_dk",                "T2_with_gdp_dk",            "all",  None),
    ("T4_mundlak_within",             "T4_mundlak_re",             "all",  None),
    ("T4_mundlak_between",            "T4_mundlak_re",             "all",  "mean"),
    # Item 2 (Step 7): T4 same-sample (no_gdp mundlak on with_gdp sample)
    ("T4_mundlak_within_samesample",  "T4_mundlak_re_samesample",  "all",  None),
    ("T4_mundlak_between_samesample", "T4_mundlak_re_samesample",  "all",  "mean"),
]


def _safe_fmt(val, fmt: str = "{:.4f}") -> str:
    try:
        if pd.isna(val):
            return ""
        return fmt.format(float(val))
    except Exception:
        return ""


def _sig_from_p(p) -> str:
    try:
        p = float(p)
    except Exception:
        return ""
    if pd.isna(p):
        return ""
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


def main() -> int:
    if not os.path.exists(RESULTS):
        print(f"ERROR: {RESULTS} not found. Run analysis/run_analysis.py first.",
              file=sys.stderr)
        return 1
    df = pd.read_csv(RESULTS)

    # Only valid rows
    if "valid" in df.columns:
        df = df[df["valid"].astype(str).str.lower().isin(("true", "1", "1.0"))].copy()

    # Cast year column to string for robust match (T1 rows use "2014"/"2020")
    if "year" in df.columns:
        df["year"] = df["year"].astype(str)
    rows = []
    for pred in FOCAL_PREDS:
        for label, tier, year_filter, pred_xform in HEADLINE_SPECS:
            # Mundlak between-effect: use "<pred>_mean" as the predictor key
            key = pred + "_mean" if pred_xform == "mean" else pred
            mask = (df["tier"] == tier) & (df["predictor"] == key)
            if year_filter is not None and "year" in df.columns:
                mask &= (df["year"] == str(year_filter))
            r = df[mask]
            if r.empty:
                # The T2_with_gdp_samesample variant is skipped by the estimator
                # when its sample already equals the with_gdp sample. Annotate
                # rather than pretend the row is missing.
                if label == "T2_with_gdp_samesample":
                    rows.append({
                        "predictor": pred, "tier": label,
                        "status": "= T2_with_gdp",
                    })
                else:
                    rows.append({
                        "predictor": pred, "tier": label, "status": "missing",
                    })
                continue
            rr = r.iloc[0]
            rows.append({
                "predictor":   pred,
                "tier":        label,
                "coef":        rr.get("coef"),
                "se":          rr.get("se"),
                "pval":        rr.get("pval"),
                "sig":         _sig_from_p(rr.get("pval")),
                "pval_bonf":   rr.get("pval_bonf"),
                "pval_bh":     rr.get("pval_bh"),
                "std_coef":    rr.get("std_coef"),
                "n":           rr.get("n"),
                "n_clusters":  rr.get("n_clusters"),
                "n_changers":  rr.get("n_changers"),
                "within_sd":   rr.get("within_sd"),
                "se_type":     rr.get("se_type", ""),
            })

    out = pd.DataFrame(rows)
    out.to_csv(OUT_CSV, index=False, float_format="%.6f")
    print(f"Wrote {OUT_CSV} ({len(out)} rows)")

    # Render markdown table, one block per focal predictor
    md = ["# Headline coefficient table\n",
          "Generated by `tools/build_headline_table.py` from "
          "`results/results.csv`. Only rows with `valid==True` are included. "
          "Significance stars are on **raw** p-values; see `pval_bonf` and "
          "`pval_bh` for multiple-testing corrections across the focal family "
          "({composite_secularism_norm, composite_secularism_pca_norm, "
          "gri_apostasy_norm, gri_religious_courts_norm} × "
          "{T2_no_gdp, T2_with_gdp} = 8 tests).\n"]
    for pred in FOCAL_PREDS:
        sub = out[out["predictor"] == pred]
        if sub.empty:
            continue
        md.append(f"\n## `{pred}`\n")
        header = ("| spec | coef | SE | p | sig | p_bonf | p_bh | std_coef | "
                  "N | n_clusters | n_changers | within_sd | SE type |")
        sep    = "|---" * 13 + "|"
        md.append(header)
        md.append(sep)
        for _, r in sub.iterrows():
            if r.get("status") == "missing":
                md.append(f"| {r['tier']} | *missing* | | | | | | | | | | | |")
                continue
            if r.get("status") == "= T2_with_gdp":
                md.append(f"| {r['tier']} | *= T2_with_gdp (by construction)* | | | | | | | | | | | |")
                continue
            md.append("| " + " | ".join([
                str(r["tier"]),
                _safe_fmt(r["coef"], "{:+.4f}"),
                _safe_fmt(r["se"]),
                _safe_fmt(r["pval"]),
                str(r.get("sig", "")),
                _safe_fmt(r.get("pval_bonf")),
                _safe_fmt(r.get("pval_bh")),
                _safe_fmt(r.get("std_coef"), "{:+.3f}"),
                _safe_fmt(r.get("n"), "{:.0f}"),
                _safe_fmt(r.get("n_clusters"), "{:.0f}"),
                _safe_fmt(r.get("n_changers"), "{:.0f}"),
                _safe_fmt(r.get("within_sd"), "{:.4f}"),
                str(r.get("se_type", "")),
            ]) + " |")
    with open(OUT_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(md) + "\n")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
