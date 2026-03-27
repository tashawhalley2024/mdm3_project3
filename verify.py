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
    "results/results_wbl.csv",
    "results/index_comparison.csv",
    "results/index_comparison.md",
    "results/event_study.csv",
    "results/loo_jackknife.csv",
    "results/oster_sensitivity.csv",
    "results/placebo.csv",
    "results/spec_ladder.csv",
    "results/README.md",
    # figures/
    "figures/01_scatter.png",
    "figures/02_coefplot.png",
    "figures/03_coefplot_suboutcomes.png",
    "figures/04_trend.png",
    "figures/05_loo_jackknife.png",
    "figures/06_placebo.png",
    "figures/07_spec_ladder.png",
    "figures/08_event_study.png",
    "figures/09_oster_sensitivity.png",
    "figures/10_alt_outcomes.png",
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
            "min_rows": 2200,
            "required_cols": ["iso3", "country", "year", "wbl_treatment_index"],
        },
        "data/predictors.csv": {
            "min_rows": 3100,
            "required_cols": ["iso3", "country", "year",
                              "gri_religious_courts_norm", "gri_state_religion_norm",
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
        composite_path = os.path.join(ROOT, "results/results_composite.csv")
        df_comp = pd.read_csv(composite_path)
        row = df_comp[
            (df_comp["tier"] == "T2_no_gdp") &
            (df_comp["predictor"] == "gri_religious_courts_norm")
        ]
        check(len(row) == 1,
              "composite T2_no_gdp religious_courts row is unique")
        if len(row) == 1:
            coef = float(row.iloc[0]["coef"])
            check(abs(coef - (-0.011020)) < 0.0001,
                  f"T2_no_gdp religious_courts coef = {coef:.6f} (expected ~-0.011020)")
    except Exception as e:
        failures.append(f"FAIL: Key regression check failed: {e}")

except ImportError:
    failures.append("FAIL: pandas not installed -- run: pip install -r requirements.txt")
    print("  SKIP: CSV/regression checks require pandas")

# ── 4. Figure file sizes ───────────────────────────────────────────────────────
print("\n=== 4. Figure file sizes ===")
FIGURES = [
    "figures/01_scatter.png",
    "figures/02_coefplot.png",
    "figures/03_coefplot_suboutcomes.png",
    "figures/04_trend.png",
    "figures/05_loo_jackknife.png",
    "figures/06_placebo.png",
    "figures/07_spec_ladder.png",
    "figures/08_event_study.png",
    "figures/09_oster_sensitivity.png",
    "figures/10_alt_outcomes.png",
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
