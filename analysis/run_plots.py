"""
plot_secularism_women.py
======================
Visualisations for the secularism and gender gap analysis.

Outputs (all saved to data/processed/):
  secularism_women_coefplot.png   – coefficient forest plot (all tiers)
  secularism_women_scatter.png    – 2010 scatter: religious courts score vs women's welfare, coloured by region
  secularism_women_trend.png      – time-trend: high vs low GRI-courts countries

Run from the project root:
  python src/plot_secularism_women.py
"""

import os
import sys
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import statsmodels.api as sm
from scipy import stats

warnings.filterwarnings("ignore")

# ── Import shared config ────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import REGION_MAP, FOCAL_PRED

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Paths ──────────────────────────────────────────────────────────────────────
RESULTS_PATH = os.path.join(ROOT, "results/results.csv")
COMP_PATH    = os.path.join(ROOT, "data/predictors.csv")
WOMEN_PATH   = os.path.join(ROOT, "data/outcome_composite.csv")
OUT_COEF     = os.path.join(ROOT, "figures/02_coefplot.png")
OUT_COEF_SUB = os.path.join(ROOT, "figures/03_coefplot_suboutcomes.png")
OUT_SCATTER  = os.path.join(ROOT, "figures/01_scatter.png")
OUT_TREND    = os.path.join(ROOT, "figures/04_trend.png")
OUT_LOO      = os.path.join(ROOT, "figures/05_loo_jackknife.png")
OUT_PLACEBO  = os.path.join(ROOT, "figures/06_placebo.png")
OUT_SPEC     = os.path.join(ROOT, "figures/07_spec_ladder.png")

LOO_CSV      = os.path.join(ROOT, "results/loo_jackknife.csv")
PLACEBO_CSV  = os.path.join(ROOT, "results/placebo.csv")
RESULTS_CSV  = os.path.join(ROOT, "results/results.csv")
SPEC_CSV     = os.path.join(ROOT, "results/spec_ladder.csv")

# Phase 9 paths
EVENTSTUDY_CSV = os.path.join(ROOT, "results/event_study.csv")
EVENTSTUDY_PNG = os.path.join(ROOT, "figures/08_event_study.png")
OSTER_SENS_CSV = os.path.join(ROOT, "results/oster_sensitivity.csv")
OSTER_SENS_PNG = os.path.join(ROOT, "figures/09_oster_sensitivity.png")

# Phase 10 paths
WBL_RESULTS_CSV = os.path.join(ROOT, "results/results_wbl.csv")
OUT_ALT_OUTCOMES = os.path.join(ROOT, "figures/10_alt_outcomes.png")

# FOCAL_PRED and REGION_MAP imported from src.config above

REGION_COLORS = {
    "Europe":            "#4c72b0",
    "Americas":          "#55a868",
    "MENA":              "#c44e52",
    "Sub-Saharan Africa":"#dd8452",
    "Asia-Pacific":      "#8172b3",
    "Central Asia":      "#937860",
    "Other":             "#999999",
}


def get_region(iso3: str) -> str:
    return REGION_MAP.get(iso3, "Other")


# ── Pretty labels for predictors ───────────────────────────────────────────────
LABELS = {
    "pct_christian_norm":      "% Christian",
    "pct_muslim_norm":         "% Muslim",
    "pct_hindu_norm":          "% Hindu",
    "pct_buddhist_norm":       "% Buddhist",
    "pct_unaffiliated_norm":   "% Unaffiliated",
    "gri_state_religion_norm": "State religion",
    "gri_religious_law_norm":  "Religious law",
    "gri_blasphemy_norm":      "Blasphemy law",
    "gri_apostasy_norm":       "Apostasy law",
    "gri_religious_courts_norm": "Religious courts",
    "v2x_rule_norm":           "Rule of law",
    "v2x_civlib_norm":         "Civil liberties",
    "v2x_egal_norm":           "Egalitarianism",
    "pct_muslim_2010":         "% Muslim (2010)",
    "muslim_x_rellaw":         "Muslim × Rel. law",
    "const":                   "Intercept",
    # GDP
    "log_gdppc_norm":          "GDP p.c. (log, norm)",
}


# ═══════════════════════════════════════════════════════════════════════════════
# 1. COEFFICIENT FOREST PLOT
# ═══════════════════════════════════════════════════════════════════════════════
def plot_coefplot():
    """
    Three-panel forest plot: one panel per tier.
    Rows = predictors, x-axis = coefficient, bars = 95% CI.
    Colour-coded by significance: *** red, ** orange, * yellow, ns grey.
    """
    df = pd.read_csv(RESULTS_PATH)

    # Use GDP-controlled ("with_gdp") versions as the primary display
    tier_order = ["T1_with_gdp", "T2_with_gdp", "T3_with_gdp"]
    tier_labels = {
        "T1_with_gdp": "Tier 1 — Cross-sectional OLS\n(2010 & 2020, GDP-controlled)",
        "T2_with_gdp": "Tier 2 — Panel FE\n(2007-2022, country + year FE, GDP-controlled)",
        "T3_with_gdp": "Tier 3 — Interaction model\n(Muslim x religious law, GDP-controlled)",
    }
    sig_colors = {
        "***": "#c0392b",
        "**":  "#e67e22",
        "*":   "#f1c40f",
        "":    "#95a5a6",
    }

    # Skip intercept and year dummies for display
    skip_patterns = ["const", "yr_"]

    fig, axes = plt.subplots(1, 3, figsize=(16, 7), sharey=False)
    fig.suptitle(
        "Secularism, Governance & Gender Gap: Coefficient Estimates (GDP-controlled)\n"
        "(dots = OLS/FE coefficient, bars = 95% confidence interval)",
        fontsize=12, fontweight="bold", y=1.01,
    )

    for ax, tier in zip(axes, tier_order):
        sub = df[df["tier"] == tier].copy()
        # Remove intercept + year dummies
        sub = sub[~sub["predictor"].apply(
            lambda p: any(p.startswith(s) for s in skip_patterns)
        )]

        rows = []
        for _, row in sub.iterrows():
            label = LABELS.get(row["predictor"], row["predictor"])
            # For T1 append year suffix to distinguish 2010/2020
            if tier.startswith("T1"):
                label = f"{label} ({row['year']})"
            rows.append({
                "label": label,
                "coef": row["coef"],
                "ci95": 1.96 * row["se"],
                "sig": row["sig"],
            })
        plot_rows = pd.DataFrame(rows) if rows else pd.DataFrame(
            columns=["label", "coef", "ci95", "sig"]
        )

        if plot_rows.empty:
            ax.text(0.5, 0.5, "No data", ha="center", va="center",
                    transform=ax.transAxes, fontsize=10)
            ax.set_title(tier_labels[tier], fontsize=9, fontweight="bold")
            continue

        plot_rows = plot_rows.iloc[::-1].reset_index(drop=True)
        ys = np.arange(len(plot_rows))

        for i, row in plot_rows.iterrows():
            color = sig_colors.get(row["sig"], sig_colors[""])
            ax.errorbar(
                row["coef"], i,
                xerr=row["ci95"],
                fmt="o", color=color, ecolor=color,
                markersize=6, capsize=3, linewidth=1.5,
            )

        ax.axvline(0, color="black", linewidth=0.8, linestyle="--", alpha=0.6)
        ax.set_yticks(ys)
        ax.set_yticklabels(plot_rows["label"], fontsize=8)
        ax.set_title(tier_labels[tier], fontsize=9, fontweight="bold")
        ax.set_xlabel("Coefficient", fontsize=8)
        ax.grid(axis="x", alpha=0.3, linewidth=0.5)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    # Shared legend
    legend_handles = [
        mpatches.Patch(color=sig_colors["***"], label="p < 0.01 (***)"),
        mpatches.Patch(color=sig_colors["**"],  label="p < 0.05 (**)"),
        mpatches.Patch(color=sig_colors["*"],   label="p < 0.10 (*)"),
        mpatches.Patch(color=sig_colors[""],    label="Not significant"),
    ]
    fig.legend(handles=legend_handles, loc="lower center", ncol=4,
               fontsize=9, bbox_to_anchor=(0.5, -0.04))

    plt.tight_layout()
    plt.savefig(OUT_COEF, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {OUT_COEF}")


# ═══════════════════════════════════════════════════════════════════════════════
# 1b. SUB-OUTCOME COEFFICIENT PLOT (Phase 3)
# ═══════════════════════════════════════════════════════════════════════════════
def plot_coefplot_suboutcomes():
    """
    Forest plot for the sub-outcome analysis (Phase 3).
    Four rows (one per sub-outcome group), two columns (Tier 1 2010 + Tier 2 panel).
    Religion predictors only — excludes controls for readability.
    """
    df = pd.read_csv(RESULTS_PATH)

    sub_names = ["political", "economic", "physical_safety", "health"]
    sub_labels = {
        "political":       "Political\n(gender, legislature, WiP, ministers)",
        "economic":        "Economic\n(business law, LFPR, literacy)",
        "physical_safety": "Physical safety\n(homicide, civil liberties)",
        "health":          "Health\n(female life expectancy)",
    }
    tier_labels_short = {
        "T1": "Tier 1\n(2010 cross-section)",
        "T2": "Tier 2\n(panel FE)",
    }

    # Religion predictors to show
    rel_preds = [
        "pct_muslim_norm", "pct_christian_norm", "pct_hindu_norm",
        "pct_buddhist_norm", "pct_unaffiliated_norm",
        "gri_state_religion_norm", "gri_religious_law_norm",
        "gri_blasphemy_norm", "gri_apostasy_norm", "gri_religious_courts_norm",
    ]

    sig_colors = {
        "***": "#c0392b", "**": "#e67e22", "*": "#f1c40f", "": "#95a5a6",
    }

    fig, axes = plt.subplots(
        len(sub_names), 2,
        figsize=(14, 4 * len(sub_names)),
        sharey=False,
    )
    fig.suptitle(
        "Religion & Governance Effects by Outcome Dimension (Phase 3: Sub-outcome Analysis)\n"
        "Left = 2010 cross-section; Right = panel FE 2007-2022",
        fontsize=12, fontweight="bold", y=1.01,
    )

    for row_i, sub_name in enumerate(sub_names):
        for col_i, (tier_key, tier_filter) in enumerate([
            ("T1", f"P3_T1_{sub_name}"),
            ("T2", f"P3_T2_{sub_name}"),
        ]):
            ax = axes[row_i, col_i]
            sub = df[df["tier"] == tier_filter].copy()

            # Filter to religion predictors; take 2010 for T1
            if tier_key == "T1":
                sub = sub[sub["year"] == 2010]
            sub = sub[sub["predictor"].isin(rel_preds)]

            if sub.empty:
                ax.text(0.5, 0.5, "No data", ha="center", va="center",
                        transform=ax.transAxes, fontsize=9)
                ax.set_visible(True)
                continue

            sub = sub.iloc[::-1].reset_index(drop=True)
            ys = np.arange(len(sub))

            for i, row in sub.iterrows():
                color = sig_colors.get(row["sig"], sig_colors[""])
                ax.errorbar(
                    row["coef"], i,
                    xerr=1.96 * row["se"],
                    fmt="o", color=color, ecolor=color,
                    markersize=5, capsize=3, linewidth=1.4,
                )

            ax.axvline(0, color="black", linewidth=0.8, linestyle="--", alpha=0.6)
            labels = [LABELS.get(p, p) for p in sub["predictor"]]
            ax.set_yticks(ys)
            ax.set_yticklabels(labels, fontsize=8)
            ax.set_xlabel("Coefficient", fontsize=8)
            ax.grid(axis="x", alpha=0.3, linewidth=0.5)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

            if col_i == 0:
                ax.set_ylabel(sub_labels[sub_name], fontsize=8, fontweight="bold",
                              labelpad=6)
            if row_i == 0:
                ax.set_title(tier_labels_short[tier_key], fontsize=9,
                             fontweight="bold")

    legend_handles = [
        mpatches.Patch(color=sig_colors["***"], label="p < 0.01 (***)"),
        mpatches.Patch(color=sig_colors["**"],  label="p < 0.05 (**)"),
        mpatches.Patch(color=sig_colors["*"],   label="p < 0.10 (*)"),
        mpatches.Patch(color=sig_colors[""],    label="Not significant"),
    ]
    fig.legend(handles=legend_handles, loc="lower center", ncol=4,
               fontsize=9, bbox_to_anchor=(0.5, -0.02))

    plt.tight_layout()
    plt.savefig(OUT_COEF_SUB, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {OUT_COEF_SUB}")


# ═══════════════════════════════════════════════════════════════════════════════
# 2. SCATTER PLOT: pct_muslim vs women_treatment_index (2010)
# ═══════════════════════════════════════════════════════════════════════════════
def plot_scatter(df: pd.DataFrame):
    """
    2010 cross-section scatter: pct_muslim_norm vs women_treatment_index.
    Points coloured by region.
    Two regression lines: raw (bivariate) and adjusted (with controls).
    Outlier country labels.
    """
    OUTCOME  = "women_treatment_index"
    CONTROLS = ["v2x_rule_norm", "v2x_civlib_norm", "v2x_egal_norm"]
    X_VAR    = "pct_muslim_norm"

    cs = df[df["year"] == 2010].copy()
    cs["region"] = cs["iso3"].map(get_region)
    required = [OUTCOME, X_VAR] + CONTROLS + ["iso3", "country", "region"]
    cs = cs[required].dropna()

    fig, ax = plt.subplots(figsize=(10, 7))

    # Scatter — coloured by region
    for region, grp in cs.groupby("region"):
        ax.scatter(
            grp[X_VAR], grp[OUTCOME],
            color=REGION_COLORS.get(region, "#999999"),
            label=region, alpha=0.75, s=45, edgecolors="white", linewidths=0.4,
        )

    # Regression line 1: raw (bivariate)
    x_arr = cs[X_VAR].values
    y_arr = cs[OUTCOME].values
    slope_raw, intercept_raw, r_raw, p_raw, _ = stats.linregress(x_arr, y_arr)
    x_line = np.linspace(x_arr.min(), x_arr.max(), 200)
    ax.plot(x_line, intercept_raw + slope_raw * x_line,
            color="black", linewidth=1.8, linestyle="-",
            label=f"Raw OLS (r={r_raw:.2f}, p={p_raw:.3f})")

    # Regression line 2: partial — residualise on controls then re-fit
    X_ctrl = sm.add_constant(cs[CONTROLS])
    res_x = sm.OLS(cs[X_VAR], X_ctrl).fit().resid
    res_y = sm.OLS(cs[OUTCOME], X_ctrl).fit().resid
    slope_adj, intercept_adj, r_adj, p_adj, _ = stats.linregress(res_x.values, res_y.values)
    # Plot partial regression as a centred line
    x_partial = np.linspace(res_x.min(), res_x.max(), 200)
    # Map residuals back to original x scale for display
    x_plot = x_partial + cs[X_VAR].mean()
    y_plot = intercept_adj + slope_adj * x_partial + cs[OUTCOME].mean()
    ax.plot(x_plot, y_plot,
            color="black", linewidth=1.8, linestyle="--",
            label=f"Adjusted OLS (β={slope_adj:.2f}, p={p_adj:.3f})")

    # Label outliers (top/bottom 8 by residual from raw line)
    cs["_fitted"]  = intercept_raw + slope_raw * cs[X_VAR]
    cs["_resid"]   = cs[OUTCOME] - cs["_fitted"]
    outliers = pd.concat([
        cs.nlargest(5, "_resid"),
        cs.nsmallest(5, "_resid"),
        cs[cs[X_VAR] > 0.7],   # high-Muslim countries
    ]).drop_duplicates("iso3")

    for _, row in outliers.iterrows():
        ax.annotate(
            row["iso3"],
            xy=(row[X_VAR], row[OUTCOME]),
            xytext=(4, 4), textcoords="offset points",
            fontsize=7, color="#333333", alpha=0.9,
        )

    ax.set_xlabel("% Muslim population (normalised, 2010)", fontsize=11)
    ax.set_ylabel("Women's Treatment Index (2010)", fontsize=11)
    ax.set_title(
        "Muslim Population Share vs Women's Treatment (2010 cross-section)\n"
        "Raw correlation (—) and partial correlation controlling for rule of law,\n"
        "civil liberties, and egalitarianism (- -)",
        fontsize=10, fontweight="bold",
    )
    ax.legend(fontsize=8, loc="upper right", framealpha=0.9)
    ax.grid(alpha=0.3, linewidth=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.savefig(OUT_SCATTER, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {OUT_SCATTER}")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. TIME-TREND: high vs low GRI-courts countries
# ═══════════════════════════════════════════════════════════════════════════════
def plot_time_trend(df: pd.DataFrame):
    """
    Average women_treatment_index over 2007–2022 for countries that are
    consistently in the top tercile ('High') vs bottom tercile ('Low') of
    gri_religious_courts_norm (measured in 2010, kept constant as classifier).
    Shows the panel FE finding visually.
    """
    OUTCOME   = "women_treatment_index"
    COURTS    = "gri_religious_courts_norm"

    # Classify countries by 2010 courts score (stable classifier)
    cs2010 = df[df["year"] == 2010][["iso3", COURTS]].dropna()
    q33 = cs2010[COURTS].quantile(0.33)
    q67 = cs2010[COURTS].quantile(0.67)

    low_courts  = cs2010[cs2010[COURTS] <= q33]["iso3"].tolist()
    high_courts = cs2010[cs2010[COURTS] >= q67]["iso3"].tolist()

    trend_low  = (df[df["iso3"].isin(low_courts)]
                  .groupby("year")[OUTCOME].mean())
    trend_high = (df[df["iso3"].isin(high_courts)]
                  .groupby("year")[OUTCOME].mean())
    trend_mid  = (df[~df["iso3"].isin(low_courts + high_courts)]
                  .groupby("year")[OUTCOME].mean())

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(trend_low.index,  trend_low.values,
            color="#4c72b0", linewidth=2.2, marker="o", markersize=5,
            label=f"Low religious courts (n={len(low_courts)} countries)")
    ax.plot(trend_mid.index,  trend_mid.values,
            color="#8172b3", linewidth=1.4, linestyle=":", marker="^", markersize=4,
            label=f"Middle tercile (n={len(df[~df['iso3'].isin(low_courts+high_courts)]['iso3'].unique())} countries)")
    ax.plot(trend_high.index, trend_high.values,
            color="#c44e52", linewidth=2.2, marker="s", markersize=5,
            label=f"High religious courts (n={len(high_courts)} countries)")

    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("Avg Women's Treatment Index", fontsize=11)
    ax.set_title(
        "Women's Treatment Over Time by Religious Court Score\n"
        "(Countries classified by 2010 GRI religious-courts score; "
        "panel FE coefficient = −0.009, p=0.002)",
        fontsize=10, fontweight="bold",
    )
    ax.legend(fontsize=9, framealpha=0.9)
    ax.grid(alpha=0.3, linewidth=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xticks(sorted(df["year"].unique()))
    ax.tick_params(axis="x", rotation=45)

    plt.tight_layout()
    plt.savefig(OUT_TREND, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {OUT_TREND}")


# ═══════════════════════════════════════════════════════════════════════════════
# 4. LEAVE-ONE-OUT JACKKNIFE PLOT
# ═══════════════════════════════════════════════════════════════════════════════
def plot_loo():
    """
    Visualise the LOO jackknife stability of the religious courts coefficient.

    Panel A (left): histogram of the 170 LOO coefficients.
      - Vertical red line = baseline (full-sample) estimate.
      - Shaded band = ±1.96 × baseline SE (95% CI of full-sample estimate).
      - Kernel density overlay.

    Panel B (right): ranked dot plot of the 20 most influential countries.
      - Each dot = LOO coefficient when that country is dropped.
      - Baseline shown as dashed line.
      - Countries labelled.
    """
    import os
    if not os.path.exists(LOO_CSV):
        print(f"  LOO CSV not found ({LOO_CSV}) -- skipping.")
        return

    loo = pd.read_csv(LOO_CSV)
    base_coef = loo["base_coef"].iloc[0]
    base_se   = loo["base_se"].iloc[0]
    ci95_lo   = base_coef - 1.96 * base_se
    ci95_hi   = base_coef + 1.96 * base_se

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle(
        "Leave-One-Out Jackknife: Religious Courts Coefficient\n"
        "(Panel FE, 2007-2022; dependent variable = Women's Treatment Index)",
        fontsize=11, fontweight="bold",
    )

    # ── Panel A: histogram ───────────────────────────────────────────────────
    ax1.hist(loo["coef"].dropna(), bins=30, color="#4c72b0", alpha=0.7,
             edgecolor="white", linewidth=0.5, density=True)

    # KDE overlay
    from scipy.stats import gaussian_kde
    kde_vals = loo["coef"].dropna().values
    kde = gaussian_kde(kde_vals, bw_method="scott")
    x_range = np.linspace(kde_vals.min() - 0.002, kde_vals.max() + 0.002, 300)
    ax1.plot(x_range, kde(x_range), color="#4c72b0", linewidth=2)

    # 95% CI band of baseline estimate
    ax1.axvspan(ci95_lo, ci95_hi, color="#c44e52", alpha=0.12,
                label="Baseline 95% CI")
    # Baseline estimate
    ax1.axvline(base_coef, color="#c44e52", linewidth=2,
                label=f"Baseline: {base_coef:.5f}")
    # Zero line
    ax1.axvline(0, color="black", linewidth=0.8, linestyle="--", alpha=0.5)

    n_total = loo["coef"].notna().sum()
    n_sig   = (loo["pval"] < 0.05).sum()
    ax1.set_xlabel("LOO Coefficient (gri_religious_courts_norm)", fontsize=10)
    ax1.set_ylabel("Density", fontsize=10)
    ax1.set_title(
        f"Distribution of {n_total} LOO estimates\n"
        f"(p<0.05 in {n_sig}/{n_total} runs; 0 sign reversals)",
        fontsize=9,
    )
    ax1.legend(fontsize=8, framealpha=0.9)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    # ── Panel B: ranked influential-country dot plot ──────────────────────────
    top20 = loo.reindex(loo["coef_change"].abs().nlargest(20).index).copy()
    top20 = top20.sort_values("coef")

    colors = ["#c44e52" if c > base_coef else "#4c72b0" for c in top20["coef"]]
    ys = np.arange(len(top20))

    ax2.scatter(top20["coef"], ys, color=colors, s=55, zorder=3)
    for i, (_, row) in enumerate(top20.iterrows()):
        ax2.plot([base_coef, row["coef"]], [i, i],
                 color="#999999", linewidth=0.8, zorder=2)

    ax2.axvline(base_coef, color="#c44e52", linewidth=1.5, linestyle="--",
                label=f"Baseline: {base_coef:.5f}")
    ax2.axvspan(ci95_lo, ci95_hi, color="#c44e52", alpha=0.10)
    ax2.axvline(0, color="black", linewidth=0.8, linestyle=":", alpha=0.5)

    ax2.set_yticks(ys)
    ax2.set_yticklabels(
        [f"{r['iso3']} ({r['country'][:12]})" for _, r in top20.iterrows()],
        fontsize=8,
    )
    ax2.set_xlabel("LOO Coefficient", fontsize=10)
    ax2.set_title("20 Most Influential Countries\n(blue = dropping them weakens effect; "
                  "red = strengthens)", fontsize=9)
    ax2.legend(fontsize=8, framealpha=0.9)
    ax2.grid(axis="x", alpha=0.3, linewidth=0.5)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.savefig(OUT_LOO, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {OUT_LOO}")


# ═══════════════════════════════════════════════════════════════════════════════
# 5. PLACEBO OUTCOME COMPARISON PLOT
# ═══════════════════════════════════════════════════════════════════════════════
def plot_placebo():
    """
    Side-by-side comparison of the religious courts coefficient across
    female DVs (actual outcomes) and male DVs (placebos).

    If the effect is genuinely gendered, the female DVs should show a
    significantly more negative coefficient than the male placebos.
    """
    import os
    if not os.path.exists(PLACEBO_CSV):
        print(f"  Placebo CSV not found ({PLACEBO_CSV}) -- skipping.")
        return

    df = pd.read_csv(PLACEBO_CSV)

    # Human-readable labels
    label_map = {
        "P6_placebo_wdi_lifexpf_norm": "Female life\nexpectancy",
        "P6_placebo_wdi_lfpf_norm":    "Female labour\nforce partic.",
        f"P6_placebo_{LABELS.get('women_treatment_index', 'women_treatment_index')}": "Women's\ntreatment index",
        "P6_placebo_women_treatment_index": "Women's\ntreatment index",
        "P6_placebo_lifexpm_norm":     "Male life\nexpectancy",
        "P6_placebo_lfpm_norm":        "Male labour\nforce partic.",
    }

    # Classify as female or placebo
    female_tiers = [t for t in df["tier"].unique()
                    if any(x in t for x in ["wdi_lifexpf", "wdi_lfpf", "women_treatment"])]
    male_tiers   = [t for t in df["tier"].unique()
                    if any(x in t for x in ["lifexpm", "lfpm_norm"])]

    all_tiers = female_tiers + male_tiers
    sub = df[df["tier"].isin(all_tiers)].copy()

    fig, ax = plt.subplots(figsize=(10, 5))

    x_pos    = np.arange(len(all_tiers))
    colors   = (["#4c72b0"] * len(female_tiers)) + (["#dd8452"] * len(male_tiers))
    ci95     = 1.96 * sub.set_index("tier").loc[all_tiers, "se"].values
    coefs    = sub.set_index("tier").loc[all_tiers, "coef"].values
    pvals    = sub.set_index("tier").loc[all_tiers, "pval"].values

    for i, (tier, coef, ci, pval, color) in enumerate(
        zip(all_tiers, coefs, ci95, pvals, colors)
    ):
        ax.bar(i, coef, color=color, alpha=0.75, width=0.55)
        ax.errorbar(i, coef, yerr=ci, fmt="none", color="black",
                    capsize=5, linewidth=1.5)
        sig = "***" if pval < 0.01 else ("**" if pval < 0.05
              else ("*" if pval < 0.10 else "ns"))
        ax.text(i, coef + (ci + 0.003) * np.sign(coef) if coef >= 0
                else coef - ci - 0.006,
                sig, ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.axhline(0, color="black", linewidth=0.9, linestyle="--", alpha=0.6)

    tick_labels = [label_map.get(t, t.replace("P6_placebo_", "").replace("_norm", ""))
                   for t in all_tiers]
    ax.set_xticks(x_pos)
    ax.set_xticklabels(tick_labels, fontsize=9)
    ax.set_ylabel("Coefficient on Religious Courts\n(Panel FE, clustered SE)", fontsize=10)
    ax.set_title(
        "Placebo Test: Religious Courts Effect on Female vs Male Outcomes\n"
        "(If gender is the mechanism: |female coef| >> |male coef|)",
        fontsize=10, fontweight="bold",
    )

    # Legend patches
    female_patch = mpatches.Patch(color="#4c72b0", alpha=0.75, label="Female outcomes (actual DVs)")
    male_patch   = mpatches.Patch(color="#dd8452", alpha=0.75, label="Male outcomes (placebo DVs)")
    ax.legend(handles=[female_patch, male_patch], fontsize=9, framealpha=0.9)

    # Add divider between female and male groups
    if female_tiers and male_tiers:
        ax.axvline(len(female_tiers) - 0.5, color="gray", linewidth=1.2,
                   linestyle=":", alpha=0.7)
        ax.text(len(female_tiers) - 0.55, ax.get_ylim()[0] * 0.9,
                "Actual DVs", ha="right", fontsize=8, color="gray")
        ax.text(len(female_tiers) - 0.45, ax.get_ylim()[0] * 0.9,
                "Placebo DVs", ha="left", fontsize=8, color="gray")

    ax.grid(axis="y", alpha=0.3, linewidth=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.savefig(OUT_PLACEBO, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {OUT_PLACEBO}")


# ═══════════════════════════════════════════════════════════════════════════════
# 6. SPECIFICATION STABILITY PLOT
# ═══════════════════════════════════════════════════════════════════════════════
def plot_spec_stability():
    """
    Single figure showing the religious courts coefficient across every
    major model specification — the key 'robustness summary' for the paper.

    Specs drawn from two sources:
      (a) secularism_women_spec_stability.csv  — Oster specification ladder
      (b) secularism_women_results.csv         — subsample & robustness tiers

    Layout: horizontal forest plot.  One row per specification.
    Colour: by significance level.  Vertical dashed line at zero.
    Annotated with N obs and delta where available.
    """
    import os
    if not os.path.exists(RESULTS_CSV):
        print(f"  Results CSV not found -- skipping.")
        return

    res = pd.read_csv(RESULTS_CSV)
    focal = res[res["predictor"] == FOCAL_PRED].copy()

    # ── Pull specs in display order ───────────────────────────────────────────
    spec_rows = []

    def _add(label, tier, year_filter=None, note=""):
        sub = focal[focal["tier"] == tier]
        if year_filter is not None:
            sub = sub[sub["year"] == year_filter]
        if sub.empty:
            return
        r = sub.iloc[0]
        spec_rows.append({
            "label": label,
            "coef":  r["coef"],
            "se":    r["se"],
            "pval":  r["pval"],
            "n":     int(r["n"]),
            "note":  note,
            "group": "model",
        })

    # Oster ladder from spec stability CSV (if it exists)
    oster_rows = []
    if os.path.exists(SPEC_CSV):
        ost = pd.read_csv(SPEC_CSV)
        ladder_labels = {
            "Bivariate (courts only)":      "Bivariate (courts only)",
            "+ Other GRI variables":        "+ Other GRI vars",
            "+ Institutional controls":     "+ Institutional controls",
            "+ GDP per capita":             "+ GDP per capita",
            "+ CEDAW years (full model)":   "+ CEDAW years",
        }
        for orig, short in ladder_labels.items():
            row = ost[ost["spec"] == orig]
            if row.empty:
                continue
            r = row.iloc[0]
            delta_col = [c for c in ost.columns if "2p2" in c]
            note = ""
            if delta_col and not np.isnan(r.get(delta_col[0], np.nan)):
                note = f"delta={r[delta_col[0]]:.2f}"
            oster_rows.append({
                "label": short,
                "coef":  r["coef"],
                "se":    r["se"],
                "pval":  r["pval"],
                "n":     int(r["n_obs"]),
                "note":  note,
                "group": "oster",
            })

    # Subsample & sensitivity specs from results CSV
    _add("Panel FE + GDP (main result)",  "T2_with_gdp",     note="")
    _add("Panel FE + CEDAW",              "T2_with_cedaw",    note="")
    _add("Sub-period 2008-2019",          "T2_subperiod_2008_2019", note="pre-COVID")
    _add("Changers only (N~47)",          "T2_changers_only", note="courts moved")
    _add("Non-changers (N~128)",          "T2_nonchangers",   note="courts stable")
    _add("GII as outcome (panel FE)",     "P5_B2_GII_panel_fe", note="alt DV")
    _add("Lagged courts L1 (FE)",         "P4_panel_fe_L1",   note="courts(t-1)")
    _add("Lagged courts L2 (FE)",         "P4_panel_fe_L2",   note="courts(t-2)")
    _add("WEF Global Gender Gap (alt DV)", "P10_wef_panel",   note="external index")
    _add("MENA countries only",            "P10_mena_only",   note="N~19 ctry")

    # Assemble: Oster ladder first (context), then sensitivity specs
    all_rows = oster_rows + spec_rows
    if not all_rows:
        print("  No specs found -- skipping.")
        return

    df_plot = pd.DataFrame(all_rows).reset_index(drop=True)
    df_plot = df_plot.iloc[::-1].reset_index(drop=True)  # flip: top = first spec

    # ── Colour by significance ────────────────────────────────────────────────
    sig_colors = {
        "***": "#c0392b", "**": "#e67e22", "*": "#f1c40f", "": "#95a5a6",
    }
    def _sig(p):
        return "***" if p < 0.01 else ("**" if p < 0.05 else ("*" if p < 0.10 else ""))

    # ── Plot ──────────────────────────────────────────────────────────────────
    n_rows = len(df_plot)
    fig_h  = max(6, n_rows * 0.52 + 2)
    fig, ax = plt.subplots(figsize=(11, fig_h))

    ys = np.arange(n_rows)

    for i, row in df_plot.iterrows():
        sig   = _sig(row["pval"])
        color = sig_colors[sig]
        ci95  = 1.96 * row["se"]

        # Draw CI bar first (behind dot)
        ax.plot([row["coef"] - ci95, row["coef"] + ci95], [i, i],
                color=color, linewidth=2.2, alpha=0.7, solid_capstyle="round")
        # Dot
        ax.scatter(row["coef"], i, color=color, s=70, zorder=4,
                   edgecolors="white", linewidths=0.6)

        # Right-side annotation: N + note
        x_ann = ax.get_xlim()[1] if ax.get_xlim()[1] > 0 else 0.02
        ann = f"N={row['n']:,}"
        if row["note"]:
            ann += f"  [{row['note']}]"
        ax.annotate(ann, xy=(row["coef"] + ci95, i),
                    xytext=(6, 0), textcoords="offset points",
                    fontsize=7, va="center", color="#555555")

    # Divider between Oster ladder and sensitivity specs
    n_oster = len(oster_rows)
    n_sens  = len(spec_rows)
    if n_oster > 0 and n_sens > 0:
        # In the reversed order, sensitivity specs are at bottom (low ys)
        divider_y = n_sens - 0.5
        ax.axhline(divider_y, color="#aaaaaa", linewidth=0.8,
                   linestyle="--", alpha=0.7)
        ax.text(ax.get_xlim()[0] if ax.get_xlim()[0] < 0 else -0.015,
                divider_y + 0.3, "Oster specification ladder",
                fontsize=7, color="#777777", style="italic")
        ax.text(ax.get_xlim()[0] if ax.get_xlim()[0] < 0 else -0.015,
                divider_y - 0.7, "Subsample & sensitivity checks",
                fontsize=7, color="#777777", style="italic")

    ax.axvline(0, color="black", linewidth=0.9, linestyle="--", alpha=0.6)

    ax.set_yticks(ys)
    ax.set_yticklabels(df_plot["label"], fontsize=9)
    ax.set_xlabel("Coefficient on Religious Courts (gri_religious_courts_norm)", fontsize=10)
    ax.set_title(
        "Specification Stability: Religious Courts Effect on Women's Treatment\n"
        "All specifications estimate the same outcome (women_treatment_index) "
        "with panel entity + year fixed effects",
        fontsize=10, fontweight="bold",
    )

    legend_handles = [
        mpatches.Patch(color=sig_colors["***"], label="p < 0.01 (***)"),
        mpatches.Patch(color=sig_colors["**"],  label="p < 0.05 (**)"),
        mpatches.Patch(color=sig_colors["*"],   label="p < 0.10 (*)"),
        mpatches.Patch(color=sig_colors[""],    label="Not significant"),
    ]
    ax.legend(handles=legend_handles, fontsize=8, loc="lower right",
              framealpha=0.9)
    ax.grid(axis="x", alpha=0.3, linewidth=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.savefig(OUT_SPEC, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {OUT_SPEC}")


# ═══════════════════════════════════════════════════════════════════════════════
# 7. EVENT STUDY PLOT (Phase 9)
# ═══════════════════════════════════════════════════════════════════════════════
def plot_event_study():
    """
    Event study: coefficient on each event-time dummy relative to year t=-1.
    Shaded pre-period, annotated pre-trend p-value.
    """
    if not os.path.exists(EVENTSTUDY_CSV):
        print(f"  Event study CSV not found ({EVENTSTUDY_CSV}) -- skipping.")
        return

    es = pd.read_csv(EVENTSTUDY_CSV).sort_values("event_time")

    fig, ax = plt.subplots(figsize=(9, 5))

    # Shade pre-period (t < 0) in light grey
    ax.axvspan(-3.5, -0.5, color="#eeeeee", alpha=0.7, label="Pre-period", zorder=0)

    # Reference lines
    ax.axhline(0, color="black", linewidth=0.9, linestyle="--", alpha=0.6)
    ax.axvline(-0.5, color="#777777", linewidth=1.2, linestyle="--", alpha=0.7,
               label="Event boundary (t=0)")

    # Dots + 95% CI bars
    for _, row in es.iterrows():
        t      = row["event_time"]
        c      = row["coef"]
        se     = row["se"]
        is_ref = (t == -1)
        color  = "#aaaaaa" if is_ref else "#c44e52"
        marker = "D" if is_ref else "o"
        ax.errorbar(
            t, c, yerr=1.96 * se,
            fmt=marker, color=color, ecolor=color,
            markersize=5 if is_ref else 7,
            capsize=4, linewidth=1.5,
            alpha=0.5 if is_ref else 1.0,
            zorder=3,
        )

    # Annotate pre-trend p-value if present
    if "pretrend_p" in es.columns:
        pre_p_vals = es["pretrend_p"].dropna()
        if not pre_p_vals.empty:
            pre_p = float(pre_p_vals.iloc[0])
            ax.annotate(
                f"Pre-trend test: p = {pre_p:.3f}",
                xy=(0.03, 0.96), xycoords="axes fraction",
                fontsize=9, ha="left", va="top",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                          edgecolor="#cccccc", alpha=0.85),
            )

    ax.set_xlabel("Years relative to event (t = 0: first large courts change)", fontsize=10)
    ax.set_ylabel("Coefficient on event-time dummy\n(reference: year t = -1)", fontsize=10)
    ax.set_title(
        "Event Study: Religious Courts Change and Women's Welfare Index\n"
        "(Relative to year before change, 95% CI)",
        fontsize=10, fontweight="bold",
    )
    ax.set_xticks(sorted(es["event_time"].dropna().astype(int).unique()))

    legend_handles = [
        mpatches.Patch(color="#eeeeee", alpha=0.7, label="Pre-period"),
        mlines.Line2D([], [], color="#c44e52", marker="o", markersize=7,
                      label="Post-change estimates"),
        mlines.Line2D([], [], color="#aaaaaa", marker="D", markersize=5,
                      linestyle="none", label="Reference (t=-1, coef=0)"),
    ]
    ax.legend(handles=legend_handles, fontsize=8, framealpha=0.9)
    ax.grid(axis="y", alpha=0.3, linewidth=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.savefig(EVENTSTUDY_PNG, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {EVENTSTUDY_PNG}")


# ═══════════════════════════════════════════════════════════════════════════════
# 8. OSTER DELTA SENSITIVITY PLOT (Phase 9)
# ═══════════════════════════════════════════════════════════════════════════════
def plot_oster_sensitivity():
    """
    Oster (2019) delta as a function of Rmax (expressed as a multiple of R_full).
    Shaded green region where delta >= 1 (robust).
    Vertical reference lines at 1.3x and 2.2x (Oster's benchmarks).
    """
    if not os.path.exists(OSTER_SENS_CSV):
        print(f"  Oster sensitivity CSV not found ({OSTER_SENS_CSV}) -- skipping.")
        return

    df = pd.read_csv(OSTER_SENS_CSV).dropna(subset=["delta"])
    if df.empty:
        print("  Oster sensitivity data empty -- skipping.")
        return

    # Clip delta for display (avoid extreme values from near-zero denominator)
    df["delta_clipped"] = df["delta"].clip(-3, 10)

    fig, ax = plt.subplots(figsize=(9, 5))

    # Shade robust region (delta >= 1)
    robust_mask = df["delta_clipped"] >= 1.0
    if robust_mask.any():
        ax.fill_between(
            df["rmax_mult"],
            df["delta_clipped"].clip(lower=1.0),
            y2=1.0,
            where=robust_mask,
            color="#55a868", alpha=0.18, label="delta >= 1 (robust region)",
        )

    ax.plot(df["rmax_mult"], df["delta_clipped"],
            color="#4c72b0", linewidth=2.2, zorder=3)

    # Robustness threshold
    ax.axhline(1.0, color="#c44e52", linewidth=1.8, linestyle="--",
               label="delta = 1 (robustness threshold)")

    # Oster benchmark lines
    y_top = df["delta_clipped"].max() * 0.95
    for xval, lbl in [(1.3, "1.3x (Oster)"), (2.2, "2.2x (Oster)")]:
        ax.axvline(xval, color="#888888", linewidth=1.2, linestyle=":", alpha=0.8)
        ax.annotate(lbl, xy=(xval + 0.04, y_top),
                    fontsize=8, ha="left", color="#555555")

    ax.set_xlabel("Rmax  (as multiple of within-R\u00b2 from full model)", fontsize=11)
    ax.set_ylabel("Oster delta", fontsize=11)
    ax.set_title(
        "Oster (2019) Delta Sensitivity: Required Unobservable Selection\n"
        "Higher delta = more selection on unobservables needed to nullify the courts result",
        fontsize=10, fontweight="bold",
    )
    ax.legend(fontsize=9, framealpha=0.9)
    ax.grid(alpha=0.3, linewidth=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.savefig(OSTER_SENS_PNG, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {OSTER_SENS_PNG}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def plot_alternative_outcomes():
    """
    Forest plot comparing the courts coefficient across all alternative
    outcome indices — makes the WEF external validation visually prominent.

    Sources:
      - Composite (primary): RESULTS_CSV, tier T2_with_gdp
      - WEF GGG, GDI:        RESULTS_CSV, tiers P10_wef_panel, P10_gdi_panel
      - LFP gap:             RESULTS_CSV, tier P10_gap_lfp
      - WBL index:           WBL_RESULTS_CSV, tier T2_with_gdp
      - GII:                 RESULTS_CSV, tier P5_B2_GII_panel_fe (if present)
    """
    if not os.path.exists(RESULTS_CSV):
        print("  Results CSV not found -- skipping.")
        return

    res   = pd.read_csv(RESULTS_CSV)
    focal = res[res["predictor"] == FOCAL_PRED].copy()

    rows = []

    def _pull(label, tier, csv=None, unit="[0,1]", group="external"):
        src = pd.read_csv(csv) if csv else focal
        if csv:
            src = src[src["predictor"] == FOCAL_PRED]
        sub = src[src["tier"] == tier]
        if sub.empty:
            return
        r = sub.iloc[0]
        rows.append({
            "label": label,
            "coef":  float(r["coef"]),
            "se":    float(r["se"]),
            "pval":  float(r["pval"]),
            "n":     int(r["n"]),
            "unit":  unit,
            "group": group,
        })

    # Primary
    _pull("Composite index (primary)",          "T2_with_gdp",
          unit="[0,1]", group="primary")

    # External independent indices
    _pull("WEF Global Gender Gap Index",        "P10_wef_panel",
          unit="[0,1]", group="external")
    _pull("UNDP GDI",                           "P10_gdi_panel",
          unit="[0,1]", group="external")
    _pull("UNDP GII",                           "P5_B2_GII_panel_fe",
          unit="[0,1]", group="external")

    # Gap outcomes (different unit — note in label)
    _pull("LFP gap (F-M, pp)",                  "P10_gap_lfp",
          unit="pp",   group="gap")

    # WBL legal rights index (from separate CSV)
    if os.path.exists(WBL_RESULTS_CSV):
        wbl_df = pd.read_csv(WBL_RESULTS_CSV)
        wbl_focal = wbl_df[wbl_df["predictor"] == FOCAL_PRED]
        sub = wbl_focal[wbl_focal["tier"] == "T2_with_gdp"]
        if not sub.empty:
            r = sub.iloc[0]
            rows.append({
                "label": "WBL legal rights index",
                "coef":  float(r["coef"]),
                "se":    float(r["se"]),
                "pval":  float(r["pval"]),
                "n":     int(r["n"]),
                "unit":  "[0,1]",
                "group": "external",
            })

    if not rows:
        print("  No alternative outcome data found -- skipping.")
        return

    df_plot = pd.DataFrame(rows)

    # ── Significance ─────────────────────────────────────────────────────────
    sig_colors = {
        "***": "#c0392b", "**": "#e67e22", "*": "#f1c40f", "": "#95a5a6",
    }
    def _sig(p):
        return "***" if p < 0.01 else ("**" if p < 0.05 else ("*" if p < 0.10 else ""))

    # ── Plot ──────────────────────────────────────────────────────────────────
    n_rows = len(df_plot)
    fig, ax = plt.subplots(figsize=(11, max(4, n_rows * 0.65 + 2)))
    ys = np.arange(n_rows)

    for i, row in df_plot.iterrows():
        sig   = _sig(row["pval"])
        color = sig_colors[sig]
        ci95  = 1.96 * row["se"]
        filled = row["group"] == "primary" or sig in ("***", "**", "*")

        ax.plot([row["coef"] - ci95, row["coef"] + ci95], [i, i],
                color=color, linewidth=2.0, alpha=0.75, solid_capstyle="round")
        ax.scatter(row["coef"], i,
                   color=color if filled else "white",
                   edgecolors=color, linewidths=1.5,
                   s=80, zorder=4)

        # Stars + N annotation to the right
        stars = sig if sig else "n.s."
        ann   = f"{stars}  N={row['n']:,}"
        if row["unit"] != "[0,1]":
            ann += f"  [{row['unit']}]"
        ax.annotate(ann, xy=(row["coef"] + ci95, i),
                    xytext=(6, 0), textcoords="offset points",
                    fontsize=8, va="center", color="#555555")

    ax.axvline(0, color="black", linewidth=0.9, linestyle="--", alpha=0.6)
    ax.set_yticks(ys)
    ax.set_yticklabels(df_plot["label"], fontsize=9)
    ax.set_xlabel(
        "Coefficient on Religious Courts (panel FE + GDP)\n"
        "Note: LFP gap is in percentage points; all other outcomes are [0,1] normalised",
        fontsize=9
    )
    ax.set_title(
        "Religious Courts Effect Across Alternative Outcome Indices\n"
        "All panel FE with country + year fixed effects, SEs clustered by country",
        fontsize=10, fontweight="bold",
    )

    legend_handles = [
        mpatches.Patch(color=sig_colors["***"], label="p < 0.01 (***)"),
        mpatches.Patch(color=sig_colors["**"],  label="p < 0.05 (**)"),
        mpatches.Patch(color=sig_colors["*"],   label="p < 0.10 (*)"),
        mpatches.Patch(color=sig_colors[""],    label="Not significant"),
    ]
    ax.legend(handles=legend_handles, fontsize=8, loc="lower right", framealpha=0.9)
    ax.grid(axis="x", alpha=0.3, linewidth=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.savefig(OUT_ALT_OUTCOMES, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {OUT_ALT_OUTCOMES}")


def load_merged() -> pd.DataFrame:
    comp  = pd.read_csv(COMP_PATH)
    women = pd.read_csv(WOMEN_PATH)
    comp_nodupe = comp.drop(columns=["country"], errors="ignore")
    return women.merge(comp_nodupe, on=["iso3", "year"], how="left", suffixes=("", "_comp"))


def main():
    print("=" * 60)
    print("SECULARISM & GENDER GAP — VISUALISATIONS")
    print("=" * 60)

    print("\n[1/4] Coefficient forest plot (main tiers)...")
    plot_coefplot()

    print("\n[2/4] Coefficient forest plot (sub-outcomes)...")
    plot_coefplot_suboutcomes()

    print("\n[3/4] Scatter plot (2010 cross-section)...")
    df = load_merged()
    plot_scatter(df)

    print("\n[4/4] Time-trend (high vs low GRI courts)...")
    plot_time_trend(df)

    print("\n[5/6] LOO jackknife plot...")
    plot_loo()

    print("\n[6/6] Placebo outcome comparison...")
    plot_placebo()

    print("\n[7/7] Specification stability plot...")
    plot_spec_stability()

    print("\n[8/9] Event study plot (Phase 9)...")
    plot_event_study()

    print("\n[9/10] Oster delta sensitivity curve (Phase 9)...")
    plot_oster_sensitivity()

    print("\n[10/10] Alternative outcomes comparison (Phase 10)...")
    plot_alternative_outcomes()

    print("\nDone. All figures saved to data/processed/")


if __name__ == "__main__":
    main()
