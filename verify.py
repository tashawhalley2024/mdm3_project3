"""
verify.py
=========
Repository integrity checker for the secularism-women research repo.

Run from the repo root:
    python verify.py

Exit code 0 = all checks passed.
Exit code 1 = one or more checks failed (details printed).
"""

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
failures = []


def check(condition, message):
    if not condition:
        failures.append(f"FAIL: {message}")
    else:
        print(f"  OK: {message}")


# ── 1. Required files ──────────────────────────────────────────────────────────
REQUIRED_FILES = [
    "README.md",
    "requirements.txt",
    ".gitignore",
    # data/
    "data/outcome_wbl.csv",
    "data/outcome_composite.csv",
    "data/predictors.csv",
    "data/robustness_outcomes.csv",
    "data/wbl_group_scores.csv",
    "data/README.md",
    # analysis/
    "analysis/run_analysis.py",
    "analysis/run_plots.py",
    "analysis/compare_indices.py",
    "analysis/sanity_check.py",
    "analysis/utils.py",
    "analysis/config.py",
    "analysis/README.md",
    # results/
    "results/results.csv",
    "results/results_composite.csv",
    "results/index_comparison.csv",
    "results/index_comparison.md",
    "results/event_study.csv",
    "results/loo_jackknife.csv",
    "results/oster_sensitivity.csv",
    "results/placebo.csv",
    "results/spec_ladder.csv",
    "results/headline_table.csv",
    "results/headline_table.md",
    "results/vif_by_spec.csv",
    "results/results_wbl_groups.csv",
    "results/README.md",
    # figures/  (03_coefplot_suboutcomes, 04_trend, 08_event_study deliberately
    # dropped from the presentation set — see figures/README.md)
    "figures/00_map.png",
    "figures/01_scatter.png",
    "figures/02_coefplot.png",
    "figures/05_loo_jackknife.png",
    "figures/06_placebo.png",
    "figures/07_spec_ladder.png",
    "figures/09_oster_sensitivity.png",
    "figures/10_alt_outcomes.png",
    "figures/11_wbl_groups.png",
    "figures/12_mundlak_decomposition.png",
    "figures/README.md",
    # sanity_check/
    "sanity_check/sanity_check_report.md",
    "sanity_check/overlap_comparison.csv",
    "sanity_check/comparison_scatter.png",
    "sanity_check/actual_histogram.png",
    "sanity_check/README.md",
    # docs/
    "docs/methods_log.md",
    "docs/sources.md",
    "docs/mundlak_explanation.md",
    "docs/robustness_storyline.md",
]

print("\n=== 1. Required files ===")
for f in REQUIRED_FILES:
    path = os.path.join(ROOT, f)
    check(os.path.exists(path), f"exists: {f}")

# ── 2. CSV schema checks ───────────────────────────────────────────────────────
print("\n=== 2. CSV schema and row counts ===")

try:
    import pandas as pd

    CSV_CHECKS = {
        "data/outcome_wbl.csv": {
            # WBL panel currently covers 2007-2022 for the subset of economies
            # with at least one non-null legal-rights score (observed 2,057
            # rows as of 2026-04-15); threshold chosen below that so a minor
            # coverage drop doesn't silently flip this check to a pass.
            "min_rows": 2000,
            "required_cols": ["iso3", "country", "year", "wbl_treatment_index"],
        },
        "data/predictors.csv": {
            "min_rows": 3100,
            # Item 2 (2026-04-15): added gri_gov_favour_norm to enforce its
            # presence (it was in the file but silently unused by run_analysis).
            # Composite and composition columns are intentionally NOT checked
            # here — composite is in-memory only, composition is sparse and
            # lives in religion_composition_normalised.csv.
            "required_cols": ["iso3", "country", "year",
                              "gri_religious_courts_norm", "gri_state_religion_norm",
                              "gri_gov_favour_norm",
                              "log_gdppc_norm", "wvs_imprel_norm"],
        },
        "data/outcome_composite.csv": {
            "min_rows": 3100,
            "required_cols": ["iso3", "country", "year"],
        },
        "data/robustness_outcomes.csv": {
            "min_rows": 3100,
            "required_cols": ["iso3", "country", "year", "gii", "gdi"],
        },
        "data/wbl_group_scores.csv": {
            # Written by scoring.py: one row per (iso3, year), with per-group
            # scores + overall_score used by Tier-2 WBL group-wise analyses.
            "min_rows": 2000,
            "required_cols": ["iso3", "year", "assets", "health",
                              "political_rep", "overall_score"],
        },
        "results/results.csv": {
            "min_rows": 320,
            "required_cols": ["tier", "predictor", "coef", "se", "pval", "n"],
        },
        "results/results_composite.csv": {
            "min_rows": 540,
            "required_cols": ["tier", "predictor", "coef", "se", "pval", "n"],
        },
        "results/loo_jackknife.csv": {
            "min_rows": 160,
            "required_cols": ["iso3", "coef", "se", "pval"],
        },
        "results/event_study.csv": {
            "min_rows": 7,
            "required_cols": ["event_time", "coef", "se", "pval"],
        },
        "results/index_comparison.csv": {
            "min_rows": 7,
            "required_cols": ["tier", "coef_composite", "coef_wbl"],
        },
    }

    for rel_path, spec in CSV_CHECKS.items():
        full = os.path.join(ROOT, rel_path)
        if not os.path.exists(full):
            failures.append(f"FAIL: CSV not found for schema check: {rel_path}")
            continue
        try:
            df = pd.read_csv(full)
            row_count = len(df)
            check(row_count >= spec["min_rows"],
                  f"{rel_path}: {row_count:,} rows >= {spec['min_rows']:,}")
            for col in spec["required_cols"]:
                check(col in df.columns,
                      f"{rel_path}: has column '{col}'")
        except Exception as e:
            failures.append(f"FAIL: Could not read {rel_path}: {e}")

    # ── 3. Key regression result ───────────────────────────────────────────────
    print("\n=== 3. Key regression result ===")
    try:
        # Read from results.csv (current pipeline output). The previous source
        # file `results/results_composite.csv` is a stale legacy artefact no
        # longer written by run_analysis.py; verifying against it was silently
        # checking a dead file.
        results_path_main = os.path.join(ROOT, "results/results.csv")
        df_comp = pd.read_csv(results_path_main)
        row = df_comp[
            (df_comp["tier"] == "T2_no_gdp") &
            (df_comp["predictor"] == "gri_religious_courts_norm")
        ]
        check(len(row) == 1,
              "composite T2_no_gdp religious_courts row is unique")
        if len(row) == 1:
            coef = float(row.iloc[0]["coef"])
            check(abs(coef - (-0.009502)) < 0.0001,
                  f"T2_no_gdp religious_courts coef = {coef:.6f} (expected ~-0.009502)")
    except Exception as e:
        failures.append(f"FAIL: Key regression check failed: {e}")

    # ── 3b. T5 long-difference headline (Item 3, 2026-04-15) ───────────────────
    print("\n=== 3b. T5 long-difference headline ===")
    try:
        results_path = os.path.join(ROOT, "results/results.csv")
        df_all = pd.read_csv(results_path)
        t5_row = df_all[
            (df_all["tier"] == "T5_long_diff_2013_2022_with_gdp") &
            (df_all["predictor"] == "composite_secularism_norm")
        ]
        check(len(t5_row) == 1,
              "T5_long_diff_2013_2022_with_gdp composite row is unique")
        if len(t5_row) == 1:
            coef = float(t5_row.iloc[0]["coef"])
            check(abs(coef - 0.053996) < 0.001,
                  f"T5 composite 2013-2022 with_gdp coef = {coef:.6f} (expected ~+0.054)")
            check(bool(t5_row.iloc[0]["valid"]),
                  "T5 composite 2013-2022 with_gdp row is valid (not invalid)")
    except Exception as e:
        failures.append(f"FAIL: T5 key regression check failed: {e}")

except ImportError:
    failures.append("FAIL: pandas not installed -- run: pip install -r requirements.txt")
    print("  SKIP: CSV/regression checks require pandas")

# ── 4. Figure file sizes ───────────────────────────────────────────────────────
print("\n=== 4. Figure file sizes ===")
FIGURES = [
    "figures/00_map.png",
    "figures/01_scatter.png",
    "figures/02_coefplot.png",
    "figures/05_loo_jackknife.png",
    "figures/06_placebo.png",
    "figures/07_spec_ladder.png",
    "figures/09_oster_sensitivity.png",
    "figures/10_alt_outcomes.png",
    "figures/11_wbl_groups.png",
    "figures/12_mundlak_decomposition.png",
    "figures/13_long_difference.png",
]
MIN_PNG_BYTES = 50_000
for fig in FIGURES:
    full = os.path.join(ROOT, fig)
    if os.path.exists(full):
        size = os.path.getsize(full)
        check(size >= MIN_PNG_BYTES,
              f"{fig}: {size:,} bytes")
    else:
        failures.append(f"FAIL: figure missing: {fig}")

# ── 5. READMEs non-trivial ────────────────────────────────────────────────────
print("\n=== 5. READMEs ===")
READMES = [
    "README.md",
    "data/README.md",
    "analysis/README.md",
    "results/README.md",
    "figures/README.md",
    "sanity_check/README.md",
]
for r in READMES:
    full = os.path.join(ROOT, r)
    sz = os.path.getsize(full) if os.path.exists(full) else 0
    check(sz > 100, f"{r}: {sz} bytes")

# ── Final report ───────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
if failures:
    print(f"FAILED -- {len(failures)} check(s) failed:")
    for f in failures:
        print(f"  {f}")
    sys.exit(1)
else:
    print(f"ALL CHECKS PASSED ({len(REQUIRED_FILES)} files, CSV schemas, key coef, figures, READMEs)")
    sys.exit(0)
