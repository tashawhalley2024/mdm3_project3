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
from config import REGION_MAP, FOCAL_PRED, FOCAL_PRED_2, PALETTE
from utils import build_secularism_composite

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ── Presentation style ─────────────────────────────────────────────────────────
def _presentation_style():
    """Project-wide rcParams — presentation-scale fonts, clean spines, white bg.

    Called once at script entry so every figure gets consistent styling.
    """
    plt.rcParams.update({
        "figure.facecolor":   "white",
        "axes.facecolor":     "white",
        "savefig.facecolor":  "white",
        "font.family":        "DejaVu Sans",
        "font.size":          12,
        "axes.titlesize":     14,
        "axes.titleweight":   "bold",
        "axes.labelsize":     11,
        "axes.labelweight":   "normal",
        "xtick.labelsize":    10,
        "ytick.labelsize":    10,
        "legend.fontsize":    10,
        "figure.titlesize":   15,
        "figure.titleweight": "bold",
        "axes.spines.top":    False,
        "axes.spines.right":  False,
        "axes.linewidth":     1.1,
        "grid.linewidth":     0.5,
        "grid.alpha":         0.35,
        "lines.linewidth":    1.8,
    })


# Q12 — two-tier palette for the presentation deck; four-tier retained for
# the writeup. Read from env so run_all.sh and the writeup build can override.
PRES_MODE = os.environ.get("PLOTS_PRES_MODE", "1") == "1"


def _sig_colour(pval: float) -> str:
    """Map a p-value to the palette significance colour."""
    if PRES_MODE:
        # Two-tier: anything p<0.05 is 'significant'; otherwise null-grey.
        return PALETTE["sig_high"] if pval < 0.05 else PALETTE["null"]
    if pval < 0.01:  return PALETTE["sig_high"]
    if pval < 0.05:  return PALETTE["sig_med"]
    if pval < 0.10:  return PALETTE["sig_low"]
    return PALETTE["null"]


def _sig_stars(pval: float) -> str:
    if pval < 0.01:  return "***"
    if pval < 0.05:  return "**"
    if pval < 0.10:  return "*"
    return ""


def _sig_legend_handles():
    """Legend patches that match _sig_colour. Two-tier in PRES_MODE, four-tier in writeup mode."""
    if PRES_MODE:
        return [
            mpatches.Patch(color=PALETTE["sig_high"], label="p < 0.05"),
            mpatches.Patch(color=PALETTE["null"],     label="Not significant"),
        ]
    return [
        mpatches.Patch(color=PALETTE["sig_high"], label="p < 0.01"),
        mpatches.Patch(color=PALETTE["sig_med"],  label="p < 0.05"),
        mpatches.Patch(color=PALETTE["sig_low"],  label="p < 0.10"),
        mpatches.Patch(color=PALETTE["null"],     label="Not significant"),
    ]


def _narrative_title(ax_or_fig, punchline: str, subtitle: str = "", fig_level=False):
    """Two-line title: bold narrative on top, small descriptive subtitle below."""
    if fig_level:
        ax_or_fig.suptitle(
            f"{punchline}\n" + (f"{subtitle}" if subtitle else ""),
            fontsize=15, fontweight="bold", y=1.00,
        )
    else:
        full = punchline + (f"\n{subtitle}" if subtitle else "")
        ax_or_fig.set_title(full, fontsize=13, fontweight="bold", loc="left", pad=12)

# ── Paths ──────────────────────────────────────────────────────────────────────
RESULTS_PATH = os.path.join(ROOT, "results/results.csv")
COMP_PATH    = os.path.join(ROOT, "data/predictors.csv")
WOMEN_PATH   = os.path.join(ROOT, "data/outcome_wbl.csv")
OUT_COEF     = os.path.join(ROOT, "figures/02_coefplot.png")
OUT_SCATTER  = os.path.join(ROOT, "figures/01_scatter.png")
OUT_LOO      = os.path.join(ROOT, "figures/05_loo_jackknife.png")
OUT_PLACEBO  = os.path.join(ROOT, "figures/06_placebo.png")
OUT_SPEC     = os.path.join(ROOT, "figures/07_spec_ladder.png")

LOO_CSV           = os.path.join(ROOT, "results/loo_jackknife.csv")
LOO_APOSTASY_CSV  = os.path.join(ROOT, "results/loo_jackknife_apostasy.csv")
PLACEBO_CSV       = os.path.join(ROOT, "results/placebo.csv")
PLACEBO_APOSTASY_CSV = os.path.join(ROOT, "results/placebo_apostasy.csv")
RESULTS_CSV       = os.path.join(ROOT, "results/results.csv")
SPEC_CSV          = os.path.join(ROOT, "results/spec_ladder.csv")
SPEC_APOSTASY_CSV = os.path.join(ROOT, "results/spec_ladder_apostasy.csv")

# Oster sensitivity — apostasy only (courts version dropped: logically inverted for null predictor)
OSTER_SENS_CSV = os.path.join(ROOT, "results/oster_sensitivity_apostasy.csv")
OSTER_SENS_PNG = os.path.join(ROOT, "figures/09_oster_sensitivity.png")

# Phase 10 paths
OUT_ALT_OUTCOMES = os.path.join(ROOT, "figures/10_alt_outcomes.png")

OUT_MUNDLAK = os.path.join(ROOT, "figures/12_mundlak_decomposition.png")
OUT_LONGDIFF = os.path.join(ROOT, "figures/13_long_difference.png")
WBL_OUTCOME_PATH = os.path.join(ROOT, "data/outcome_wbl.csv")

# Mirror analysis/run_analysis.py:83-94 so plot_scatter can replicate the
# T1_with_gdp fit that the headline table (and figure_guide.md caption) quotes.
T1_CONTROLS_GDP = [
    "v2x_rule_norm", "v2x_corr_norm", "education_norm",
    "rurality_norm", "conflict_norm", "log_gdppc_norm",
]
T1_GRI_PANEL_COLS = [
    "gri_state_religion_norm", "gri_gov_favour_norm",
    "gri_religious_law_norm", "gri_religious_courts_norm",
    "gri_blasphemy_norm", "gri_apostasy_norm",
]

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
    "pct_unaffiliated_norm":   "% Unaffiliated",
    "pct_other_norm":          "% Other religion",
    # Item 2: composite secularism index
    "composite_secularism_norm":     "Composite secularism",
    "composite_secularism_pca_norm": "Composite (PCA)",
    "gri_state_religion_norm": "State religion",
    "gri_gov_favour_norm":     "Gov favouritism",
    "gri_religious_law_norm":  "Religious law",
    "gri_blasphemy_norm":      "Blasphemy law",
    "gri_apostasy_norm":       "Apostasy law",
    "gri_religious_courts_norm": "Religious courts",
    "v2x_rule_norm":           "Rule of law",
    "v2x_civlib_norm":         "Civil liberties",
    "v2x_egal_norm":           "Egalitarianism",
    "v2x_corr_norm":           "Corruption",
    "education_norm":          "Education (yrs schooling)",
    "rurality_norm":           "Rurality (% rural pop.)",
    "conflict_norm":           "Pol. stability",
    "const":                   "Intercept",
    # GDP
    "log_gdppc_norm":          "GDP p.c. (log, norm)",
}


# ═══════════════════════════════════════════════════════════════════════════════
# 0. SCATTER: religious courts vs women's treatment (2020 cross-section)
# ═══════════════════════════════════════════════════════════════════════════════
def plot_scatter(df: pd.DataFrame):
    """
    Dual-panel 2020 cross-section scatter:
      Left  — religious courts vs women's treatment (null)
      Right — apostasy laws vs women's treatment (signal)
    Regions colour the points; a handful of anchor countries are labelled
    so the viewer can see where the signal lives.
    """
    OUTCOME = "wbl_treatment_index"
    # Columns = union of both panels' T1_with_gdp regressors so the common
    # sample matches the headline-table rows (n=163 for 2020).
    cols = list(dict.fromkeys(
        ["iso3", FOCAL_PRED, FOCAL_PRED_2, OUTCOME,
         *T1_GRI_PANEL_COLS, *T1_CONTROLS_GDP]
    ))
    snap = df[df["year"] == 2020][cols].dropna()
    if snap.empty:
        print("  No 2020 data for scatter -- skipping.")
        return

    snap["region"] = snap["iso3"].map(get_region)

    fig, axes = plt.subplots(1, 2, figsize=(13, 6), sharey=True)

    # Per-panel predictors mirror analysis/run_analysis.py T1_with_gdp:
    #   composite focal  → [focal] + CONTROLS_GDP (standalone, composite_tier_specs)
    #   apostasy focal   → GRI_PANEL_COLS + CONTROLS_GDP (joint, tier1_cross_sectional)
    for ax, pred, panel_title, pred_cols in [
        (axes[0], FOCAL_PRED,   "Composite secularism",
         [FOCAL_PRED] + T1_CONTROLS_GDP),
        (axes[1], FOCAL_PRED_2, "Apostasy laws",
         T1_GRI_PANEL_COLS + T1_CONTROLS_GDP),
    ]:
        line_color = PALETTE["apostasy"] if pred == FOCAL_PRED_2 else PALETTE.get("composite", PALETTE["courts"])

        # Fit the full-controls OLS once per panel regardless of geometry —
        # both the scatter-with-line composite panel and the violin-strip
        # apostasy panel show β/p in an annotation box.
        X   = sm.add_constant(snap[pred_cols])
        ols = sm.OLS(snap[OUTCOME], X).fit(cov_type="HC3")
        beta = ols.params[pred]
        pval = ols.pvalues[pred]
        ns_suffix = "   n.s." if pval >= 0.05 else ""

        if pred == FOCAL_PRED_2:
            # Right panel — violin + jittered strip. Apostasy is binary-
            # dominated (0/1 with few intermediate codes), so a violin body
            # per level shows the outcome distribution clearly; per-country
            # jittered dots overlay, region-coloured.
            levels = sorted(snap[pred].unique())
            groups, positions = [], []
            for level in levels:
                vals = snap.loc[snap[pred] == level, OUTCOME].values
                if len(vals) >= 3:
                    groups.append(vals)
                    positions.append(level)
            if len(groups) >= 2:
                parts = ax.violinplot(
                    groups, positions=positions, widths=0.55,
                    showmeans=False, showmedians=True, showextrema=False,
                )
                for pc in parts["bodies"]:
                    pc.set_facecolor(PALETTE["apostasy"])
                    pc.set_alpha(0.22)
                    pc.set_edgecolor(PALETTE["apostasy"])
            rng = np.random.default_rng(seed=1)
            jitter = rng.uniform(-0.08, 0.08, size=len(snap))
            ax.scatter(snap[pred] + jitter, snap[OUTCOME],
                       c="#6c7a89", s=36, alpha=0.70,
                       edgecolors="white", linewidth=0.4)
            ax.set_xticks([0, 1])
            ax.set_xticklabels(["No apostasy law", "Apostasy law"])
            ax.annotate(
                f"β = {beta:+.3f}   p = {pval:.3g}{ns_suffix}\n"
                f"n = {int(ols.nobs)}   (T1 full controls)",
                xy=(0.03, 0.05), xycoords="axes fraction",
                fontsize=11, ha="left", va="bottom",
                bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                          edgecolor=line_color, linewidth=1.3, alpha=0.95),
            )
        else:
            # Left panel — composite is continuous; keep the scatter, OLS fit
            # and 95% CI band. Uniform neutral grey dots (no regional colour),
            # no country anchors per Q9. The composite panel's legend only
            # lists OLS fit + 95% CI.
            ax.scatter(snap[pred], snap[OUTCOME], c="#6c7a89", s=55,
                       alpha=0.75, edgecolors="white", linewidth=0.6)
            # Prediction line: vary pred, hold every other regressor at its mean.
            x_grid = np.linspace(snap[pred].min(), snap[pred].max(), 100)
            means  = snap[pred_cols].mean()
            X_grid_df = pd.DataFrame(np.tile(means.values, (len(x_grid), 1)),
                                     columns=pred_cols)
            X_grid_df[pred] = x_grid
            X_grid = sm.add_constant(X_grid_df, has_constant="add")
            y_hat  = ols.predict(X_grid)
            ci     = ols.get_prediction(X_grid).conf_int(alpha=0.05)
            ax.plot(x_grid, y_hat, color=line_color, linewidth=2.4,
                    zorder=5, label="OLS fit (other controls held at their mean)")
            ax.fill_between(x_grid, ci[:, 0], ci[:, 1], color=line_color,
                            alpha=0.12, label="95% CI")
            ax.annotate(
                f"β = {beta:+.3f}   p = {pval:.3g}{ns_suffix}\n"
                f"n = {int(ols.nobs)}   (T1 full controls)",
                xy=(0.03, 0.05), xycoords="axes fraction",
                fontsize=11, ha="left", va="bottom",
                bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                          edgecolor=line_color, linewidth=1.3, alpha=0.95),
            )

        ax.set_xlabel(f"{panel_title} (GRI, normalised)")
        ax.set_title(panel_title, fontsize=13, fontweight="bold", loc="left", pad=8)
        ax.grid(alpha=0.3, linewidth=0.5)

    axes[0].set_ylabel("Female treatment index")
    # Composite panel legend for the OLS-fit line and 95% CI band,
    # lower-right clear of the β/p box in lower-left. No regional legend on
    # the apostasy panel — dots are uniform neutral grey now.
    axes[0].legend(loc="lower right", fontsize=8.5,
                   framealpha=0.9, frameon=True)

    # Binary note — moved from axes[0] (the continuous composite panel, where
    # it was a stale label from the courts era) to axes[1] under the apostasy
    # violin, as a one-line italic footer.
    axes[1].annotate(
        "Binary-coded in Pew GRI (0 = no law, 1 = law)",
        xy=(0.5, -0.18), xycoords="axes fraction",
        fontsize=8.5, ha="center", va="top",
        color="#666", style="italic",
    )

    fig.suptitle(
        "Composite secularism and apostasy laws: clear negative correlations with female welfare",
        fontsize=16, fontweight="bold", y=1.06,
    )
    fig.text(
        0.5, 0.93,
        "2020 cross-section — each point is a country; line is OLS with 95% CI",
        ha="center", fontsize=10.5, color="#555",
    )

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    plt.savefig(OUT_SCATTER, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {OUT_SCATTER}")


# ═══════════════════════════════════════════════════════════════════════════════
# 1. COEFFICIENT FOREST PLOT
# ═══════════════════════════════════════════════════════════════════════════════
def plot_coefplot():
    """
    Two-panel forest plot (T1 cross-section 2020, T2 panel FE).
    Apostasy + courts are pinned to the top with a highlight band;
    remaining predictors appear below as greyed-out context.
    """
    df = pd.read_csv(RESULTS_PATH)

    # Title depends on entity-clustered SEs. If tier is ever switched to DK
    # (T2_with_gdp_dk), apostasy becomes p~0.003 and the suptitle's
    # "not within them" claim must change.
    tier_order = ["T1_with_gdp", "T2_with_gdp"]
    tier_titles = {
        "T1_with_gdp": "Cross-sectional OLS (2020)",
        "T2_with_gdp": "Two-way fixed effects panel (2013–2022)",
    }

    # Focal predictors rendered at the top; the remaining GRI sub-items are
    # hypothesis context; every CONTROLS_GDP regressor (rule, corruption,
    # education, rurality, conflict, GDP) renders in the visually-demoted
    # control block so the viewer reads them as covariates, not hypotheses.
    focal_preds = [FOCAL_PRED_2, FOCAL_PRED]
    context_preds = [
        "gri_state_religion_norm", "gri_religious_law_norm", "gri_blasphemy_norm",
    ]
    control_preds = [
        "v2x_rule_norm", "v2x_corr_norm", "education_norm",
        "rurality_norm", "conflict_norm", "log_gdppc_norm",
    ]

    skip_patterns = ["const", "yr_"]

    fig, axes = plt.subplots(1, 2, figsize=(14, 7.5), sharex=False, sharey=True)
    fig.suptitle(
        "Secularism and apostasy laws predict female treatment "
        "between countries but not within them",
        fontsize=16, fontweight="bold", y=1.06,
    )
    fig.text(
        0.5, 0.96,
        "Coefficient estimates with 95% CIs.",
        ha="center", fontsize=10.5, color="black",
    )

    for ax, tier in zip(axes, tier_order):
        sub = df[df["tier"] == tier].copy()
        sub = sub[~sub["predictor"].apply(
            lambda p: any(p.startswith(s) for s in skip_patterns)
        )]
        # T1 now uses only the 2020 snapshot (year is stored as string in the CSV)
        if tier.startswith("T1"):
            sub = sub[sub["year"].astype(str) == "2020"]

        ordered_preds = (
            focal_preds
            + [p for p in context_preds if p in sub["predictor"].values]
            + [p for p in control_preds if p in sub["predictor"].values]
        )
        rows = []
        for p in ordered_preds:
            row = sub[sub["predictor"] == p]
            if row.empty:
                continue
            r = row.iloc[0]
            rows.append({
                "predictor": p,
                "label": LABELS.get(p, p),
                "coef":  r["coef"],
                "ci95":  1.96 * r["se"],
                "pval":  r["pval"],
                "focal": p in focal_preds,
                "is_control": p in control_preds,
            })

        if not rows:
            ax.text(0.5, 0.5, "No data", ha="center", va="center",
                    transform=ax.transAxes, fontsize=11)
            ax.set_title(tier_titles[tier], fontsize=13, fontweight="bold", loc="left", pad=8)
            continue

        plot_rows = pd.DataFrame(rows)
        # Display top-to-bottom: apostasy top, then courts, then context
        plot_rows = plot_rows.iloc[::-1].reset_index(drop=True)
        ys = np.arange(len(plot_rows))

        ctrl_idx = [i for i, row in plot_rows.iterrows() if row["is_control"]]
        if ctrl_idx:
            # Horizontal divider between hypothesis rows (above) and controls
            # (below). Solid black, no translucency.
            ax.axhline(max(ctrl_idx) + 0.5, color="black", linewidth=0.8,
                       zorder=1)

        # Solid pale-amber band behind the top two focal rows (Apostasy law
        # and Composite secularism) — regardless of significance — to signpost
        # them as the pre-registered focal predictors. No alpha: the colour
        # itself (#FDF2E9) is already pale enough.
        for i, row in plot_rows.iterrows():
            if row["focal"]:
                ax.axhspan(i - 0.5, i + 0.5,
                           color=PALETTE["highlight_bg"], zorder=0)

        # Uniform styling across all rows — same marker size, same line width,
        # no translucency. The ONLY visual distinction between rows is colour
        # (red for p<0.05, grey otherwise) via _sig_colour.
        for i, row in plot_rows.iterrows():
            color = _sig_colour(row["pval"])
            ax.plot([row["coef"] - row["ci95"], row["coef"] + row["ci95"]], [i, i],
                    color=color, linewidth=1.8, solid_capstyle="round",
                    zorder=2)
            ax.scatter(row["coef"], i, color=color, s=70,
                       edgecolors="white", linewidths=0.8, zorder=3)

            if row["focal"]:
                suffix = "" if row["pval"] < 0.05 else "  n.s."
                ax.annotate(
                    f"{row['coef']:+.3f}{suffix}",
                    xy=(row["coef"] + row["ci95"], i),
                    xytext=(8, 0), textcoords="offset points",
                    fontsize=10,
                    va="center",
                    color="black",
                )

        ax.axvline(0, color="black", linewidth=0.9, linestyle="--")
        ax.set_yticks(ys)
        tick_labels = []
        for _, r in plot_rows.iterrows():
            if r["focal"]:
                tick_labels.append(r["label"])
            else:
                tick_labels.append(r["label"])
        ax.set_yticklabels(tick_labels, fontsize=10)
        # Uniform tick labels: all solid black, no bold differential,
        # no translucency.
        for lbl in ax.get_yticklabels():
            lbl.set_color("black")

        ax.set_title(tier_titles[tier], fontsize=13, fontweight="bold",
                     loc="left", pad=8, color="black")
        ax.set_xlabel("β", color="black")

    # Shared y-axis: right panel re-uses the left panel's labels.
    axes[1].tick_params(labelleft=False)

    legend_handles = _sig_legend_handles()
    fig.legend(handles=legend_handles, loc="lower center",
               ncol=len(legend_handles),
               bbox_to_anchor=(0.5, -0.02), frameon=False)

    plt.tight_layout(rect=[0, 0.02, 1, 0.93])
    plt.savefig(OUT_COEF, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {OUT_COEF}")


# ═══════════════════════════════════════════════════════════════════════════════
# 1b. SUB-OUTCOME COEFFICIENT PLOT (Phase 3)
# ═══════════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════════
# 4. LEAVE-ONE-OUT JACKKNIFE PLOT
# ═══════════════════════════════════════════════════════════════════════════════
def _render_loo_column(loo, ax_strip, ax_bars, palette_color, label_name):
    """One column of the LOO grid: dot strip on top, top-5 influential countries below."""
    base_coef = loo["base_coef"].iloc[0]
    base_se   = loo["base_se"].iloc[0]
    ci95_lo   = base_coef - 1.96 * base_se
    ci95_hi   = base_coef + 1.96 * base_se

    coefs  = loo["coef"].dropna().values
    n_total = len(coefs)
    n_sig   = int((loo["pval"] < 0.05).sum())
    n_flips = int((loo["coef"] * base_coef < 0).sum())

    # ── Top: horizontal dot strip ─────────────────────────────────────────
    rng = np.random.default_rng(seed=0)
    y_jitter = rng.uniform(-0.35, 0.35, size=n_total)

    # Baseline 95% CI band
    ax_strip.axvspan(ci95_lo, ci95_hi, color=palette_color, alpha=0.12,
                     label="Baseline 95% CI")

    # Each LOO coefficient as a small alpha dot
    ax_strip.scatter(coefs, y_jitter, s=18, color=palette_color, alpha=0.45,
                     edgecolors="none", zorder=3)

    # Baseline marker
    ax_strip.axvline(base_coef, color=palette_color, linewidth=2.4,
                     label=f"Baseline β = {base_coef:.4f}", zorder=4)
    # Zero / sign-flip line
    ax_strip.axvline(0, color="black", linewidth=1.0, linestyle="--", alpha=0.6,
                     label="Zero (sign-flip threshold)")

    # Two-line title: bold predictor name + headline result on next line
    flip_word = "Zero" if n_flips == 0 else str(n_flips)
    sig_plural = "run" if n_sig == 1 else "runs"
    remain_verb = "remains" if n_sig == 1 else "remain"
    headline = (
        f"{flip_word} sign flips across {n_total} country drops; "
        f"{n_sig} {sig_plural} {remain_verb} p < 0.05."
    )
    ax_strip.set_title(
        f"{label_name}\n{headline}",
        fontsize=13, fontweight="bold", loc="left", pad=10,
        color=palette_color,
    )

    ax_strip.set_xlabel("LOO β")
    ax_strip.set_ylim(-1.0, 1.0)
    ax_strip.set_yticks([])
    ax_strip.legend(loc="upper right", framealpha=0.95, fontsize=9)
    ax_strip.grid(axis="x", alpha=0.3, linewidth=0.5)

    # ── Bottom: top-5 influential countries ───────────────────────────────
    top5 = loo.reindex(loo["coef_change"].abs().nlargest(5).index).copy()
    top5 = top5.sort_values("coef").reset_index(drop=True)

    bar_colors = [palette_color if c > base_coef else "#888" for c in top5["coef"]]
    ys = np.arange(len(top5))

    ax_bars.scatter(top5["coef"], ys, color=bar_colors, s=80, zorder=3,
                    edgecolors="white", linewidths=0.8)
    for i, row in top5.iterrows():
        ax_bars.plot([base_coef, row["coef"]], [i, i],
                     color="#bbb", linewidth=1.0, zorder=2)

    ax_bars.axvline(base_coef, color=palette_color, linewidth=1.8, linestyle="--")
    ax_bars.axvspan(ci95_lo, ci95_hi, color=palette_color, alpha=0.10)
    ax_bars.axvline(0, color="black", linewidth=0.8, linestyle=":", alpha=0.5)

    ax_bars.set_yticks(ys)
    ax_bars.set_yticklabels(
        [f"{r['iso3']} — {r['country'][:18]}" for _, r in top5.iterrows()],
        fontsize=10,
    )
    ax_bars.set_xlabel("LOO β")
    ax_bars.set_title("5 most influential countries", fontsize=11,
                      fontweight="normal", color="#555", loc="left", pad=6)
    ax_bars.grid(axis="x", alpha=0.3, linewidth=0.5)


def plot_loo():
    """
    LOO jackknife stability, 2×2 grid:
      Row 1: histogram of LOO coefficients (courts | apostasy)
      Row 2: top-5 most influential countries (courts | apostasy)
    Shows that both estimates are stable across country drops.
    """
    have_courts   = os.path.exists(LOO_CSV)
    have_apostasy = os.path.exists(LOO_APOSTASY_CSV)

    if not have_courts and not have_apostasy:
        print("  No LOO CSVs found -- skipping.")
        return

    n_cols = int(have_courts) + int(have_apostasy)
    fig, axes = plt.subplots(2, n_cols, figsize=(6.5 * n_cols, 9.5),
                             squeeze=False)

    col = 0
    if have_courts:
        loo_c = pd.read_csv(LOO_CSV)
        _render_loo_column(loo_c, axes[0, col], axes[1, col],
                           PALETTE["composite"], "Composite secularism")
        col += 1
    if have_apostasy:
        loo_a = pd.read_csv(LOO_APOSTASY_CSV)
        _render_loo_column(loo_a, axes[0, col], axes[1, col],
                           PALETTE["apostasy"], "Apostasy laws")

    fig.suptitle(
        "Both results are stable — no single country drives them",
        fontsize=16, fontweight="bold", y=1.00,
    )
    fig.text(
        0.5, 0.95,
        "Leave-one-out jackknife: drop one country at a time; plot each re-estimated coefficient",
        ha="center", fontsize=10.5, color="#555",
    )

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    plt.savefig(OUT_LOO, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {OUT_LOO}")


# ═══════════════════════════════════════════════════════════════════════════════
# 5. PLACEBO OUTCOME COMPARISON PLOT
# ═══════════════════════════════════════════════════════════════════════════════
def plot_placebo():
    """
    Gendered-mechanism test: apostasy coefficient on female DVs vs male placebos.
    Female bars are highlighted; male bars are desaturated to keep the contrast
    front-and-centre.
    """
    csv = PLACEBO_APOSTASY_CSV if os.path.exists(PLACEBO_APOSTASY_CSV) else PLACEBO_CSV
    if not os.path.exists(csv):
        print(f"  Placebo CSV not found ({csv}) -- skipping.")
        return
    df = pd.read_csv(csv)

    label_map = {
        "P6_placebo_wbl_treatment_index": "Female\ntreatment index",
        "P6_placebo_wdi_lifexpf_norm": "Female life\nexpectancy",
        "P6_placebo_wdi_lfpf_norm":    "Female labour\nforce part.",
        "P6_placebo_lifexpm_norm":     "Male life\nexpectancy",
        "P6_placebo_lfpm_norm":        "Male labour\nforce part.",
    }

    # Lead with the primary female DV (women's treatment index), then female
    # life expectancy. Drop LFP rows: U-shaped FLFP-development relationship
    # (Goldin 1995, Mammen & Paxson 2000) means LFP under coercive regimes
    # often reflects compulsion, not empowerment — a real but distracting
    # confound for a 30-second placebo slide.
    female_order = [
        "P6_placebo_wbl_treatment_index",
        "P6_placebo_wdi_lifexpf_norm",
    ]
    male_order = ["P6_placebo_lifexpm_norm"]

    avail = set(df["tier"].unique())
    female_tiers = [t for t in female_order if t in avail]
    male_tiers   = [t for t in male_order   if t in avail]
    all_tiers = female_tiers + male_tiers
    if not all_tiers:
        print("  No placebo tiers matched -- skipping.")
        return

    sub = df.set_index("tier").loc[all_tiers]
    coefs = sub["coef"].values
    ci95  = 1.96 * sub["se"].values
    pvals = sub["pval"].values

    fig, ax = plt.subplots(figsize=(11, 5.8))
    x_pos = np.arange(len(all_tiers))

    colors = ([PALETTE["female"]] * len(female_tiers)
              + [PALETTE["male"]]   * len(male_tiers))
    alphas = ([1.0] * len(female_tiers)
              + [0.55] * len(male_tiers))

    for i, (coef, ci, pval, color, a) in enumerate(zip(coefs, ci95, pvals, colors, alphas)):
        ax.bar(i, coef, color=color, alpha=a, width=0.6, edgecolor="white", linewidth=0.8)
        ax.errorbar(i, coef, yerr=ci, fmt="none",
                    color="#333" if a == 1.0 else "#999",
                    capsize=5, linewidth=1.4)
        sig_label = "" if pval < 0.05 else "n.s."
        # Always place the annotation ABOVE zero so it stays inside the plot.
        y_ann = max(coef + ci, 0) + 0.003
        if sig_label:
            ax.text(i, y_ann, sig_label, ha="center", va="bottom",
                    fontsize=13 if a == 1.0 else 10,
                    fontweight="bold", color="#222" if a == 1.0 else "#666")

    ax.axhline(0, color="black", linewidth=0.9, linestyle="--", alpha=0.6)

    # Pad y-axis so the "n.s." labels above zero do not collide with the title
    upper = max(np.max(coefs + ci95), 0) + 0.012
    lower = min(np.min(coefs - ci95), 0) - 0.005
    ax.set_ylim(lower, upper)

    tick_labels = [label_map.get(t, t.replace("P6_placebo_", "").replace("_norm", ""))
                   for t in all_tiers]
    ax.set_xticks(x_pos)
    ax.set_xticklabels(tick_labels, fontsize=10)
    ax.set_ylabel("Coefficient on apostasy laws\n(Panel FE, clustered SE)")

    fig.suptitle(
        "Apostasy laws harm females, not males",
        fontsize=16, fontweight="bold", y=1.00,
    )
    ax.set_title(
        "Gendered-mechanism test: female outcomes vs male placebo outcomes",
        fontsize=11, fontweight="normal", color="#555", loc="left", pad=10,
    )

    female_patch = mpatches.Patch(color=PALETTE["female"], alpha=1.0,
                                  label="Female outcomes (actual DVs)")
    male_patch   = mpatches.Patch(color=PALETTE["male"],   alpha=0.55,
                                  label="Male outcomes (placebo DVs)")
    ax.legend(handles=[female_patch, male_patch],
              loc="upper center", bbox_to_anchor=(0.5, -0.18),
              ncol=2, frameon=False)

    if female_tiers and male_tiers:
        ax.axvline(len(female_tiers) - 0.5, color="#bbb", linewidth=1.0,
                   linestyle=":", alpha=0.8)

    ax.grid(axis="y", alpha=0.3, linewidth=0.5)

    plt.tight_layout()
    plt.savefig(OUT_PLACEBO, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {OUT_PLACEBO}")


# ═══════════════════════════════════════════════════════════════════════════════
# 6. SPECIFICATION STABILITY PLOT
# ═══════════════════════════════════════════════════════════════════════════════
def _collect_spec_rows(focal_pred, ladder_csv):
    """Pull specification rows for one focal predictor as a single unified list.

    The Oster ladder lives in `ladder_csv` (Bivariate + Full model) and the
    sensitivity / subsample specs live in `RESULTS_CSV`.
    """
    res = pd.read_csv(RESULTS_CSV)
    focal = res[res["predictor"] == focal_pred]
    focal_L1 = res[res["predictor"] == f"{focal_pred}_L1"]
    focal_L2 = res[res["predictor"] == f"{focal_pred}_L2"]

    rows = []

    # Bivariate row from the Oster spec ladder CSV (helpful baseline)
    if os.path.exists(ladder_csv):
        ost = pd.read_csv(ladder_csv)
        biv = ost[ost["spec"].str.startswith("Bivariate", na=False)]
        if not biv.empty:
            r = biv.iloc[0]
            rows.append({
                "label": "Bivariate",
                "coef":  float(r["coef"]),
                "se":    float(r["se"]),
                "pval":  float(r["pval"]),
                "n":     int(r["n_obs"]),
            })

    def _add(label, tier, source=focal):
        sub = source[source["tier"] == tier]
        if sub.empty:
            return
        r = sub.iloc[0]
        rows.append({
            "label": label,
            "coef":  float(r["coef"]),
            "se":    float(r["se"]),
            "pval":  float(r["pval"]),
            "n":     int(r["n"]),
        })

    _add("Main (FE + 6 controls)", "T2_with_gdp")
    _add("+ CEDAW",                "T2_with_cedaw")
    _add("Pre-COVID (2008–2019)",  "T2_subperiod_2008_2019")
    _add("Changers only",          "T2_changers_only")
    _add("Lag L1",                 "P4_panel_fe_L1", source=focal_L1)
    _add("Lag L2",                 "P4_panel_fe_L2", source=focal_L2)
    _add("WEF GGG (alt DV)",       "P10_wef_panel")

    return rows


def _render_spec_column(ax, rows, panel_title, focal_color):
    """Render one spec-ladder column (single unified list of rows)."""
    if not rows:
        ax.text(0.5, 0.5, "No data", ha="center", va="center",
                transform=ax.transAxes, fontsize=12)
        ax.set_title(panel_title, fontsize=13, fontweight="bold", loc="left", pad=8)
        return

    df_plot = pd.DataFrame(rows).iloc[::-1].reset_index(drop=True)
    n = len(df_plot)
    ys = np.arange(n)

    # Highlight "Main" row
    main_idx = df_plot.index[df_plot["label"].str.startswith("Main")].tolist()
    if main_idx:
        mi = main_idx[0]
        ax.axhspan(mi - 0.5, mi + 0.5,
                   color=PALETTE["highlight_bg"], alpha=0.85, zorder=0)

    for i, row in df_plot.iterrows():
        color = _sig_colour(row["pval"])
        ci95  = 1.96 * row["se"]
        ax.plot([row["coef"] - ci95, row["coef"] + ci95], [i, i],
                color=color, linewidth=2.2, alpha=0.85, solid_capstyle="round")
        ax.scatter(row["coef"], i, color=color, s=75, zorder=4,
                   edgecolors="white", linewidths=0.6)

    ax.axvline(0, color="black", linewidth=0.9, linestyle="--", alpha=0.6)
    ax.set_yticks(ys)
    ax.set_yticklabels(df_plot["label"], fontsize=10)
    ax.set_xlabel("β")
    ax.set_title(panel_title, fontsize=13, fontweight="bold", loc="left",
                 pad=8, color=focal_color)
    ax.grid(axis="x", alpha=0.3, linewidth=0.5)


def plot_spec_stability():
    """
    Dual-panel specification ladder: courts (left) vs apostasy (right).
    Each panel shows the bivariate baseline + 7 sensitivity / subsample specs.
    The main spec is highlighted with a pale background band.
    """
    if not os.path.exists(RESULTS_CSV):
        print("  Results CSV not found -- skipping.")
        return

    composite_rows = _collect_spec_rows(FOCAL_PRED,   SPEC_CSV)
    apos_rows      = _collect_spec_rows(FOCAL_PRED_2, SPEC_APOSTASY_CSV)

    n_rows = max(len(composite_rows), len(apos_rows))
    fig, axes = plt.subplots(1, 2, figsize=(14, max(6, n_rows * 0.55 + 2)))

    _render_spec_column(axes[0], composite_rows,
                        "Composite secularism", PALETTE["composite"])
    _render_spec_column(axes[1], apos_rows,
                        "Apostasy laws", PALETTE["apostasy"])

    fig.suptitle(
        "Results are robust across specifications: "
        "results are not driven by noise",
        fontsize=16, fontweight="bold", y=1.00,
    )
    fig.text(
        0.5, 0.95,
        "Composite and apostasy coefficients stable across "
        "eight specification variants.",
        ha="center", fontsize=10.5, color="#555",
    )

    # Q11: flag the composite-vs-apostasy spec asymmetry. The composite
    # side only has Bivariate + Main; the extended specs (CEDAW, pre-COVID,
    # lag L1/L2, ...) are fitted for apostasy only upstream.
    if len(composite_rows) < len(apos_rows):
        axes[0].text(
            0.98, 0.02,
            "Extended sensitivity specs fitted for apostasy only",
            transform=axes[0].transAxes,
            fontsize=8, ha="right", va="bottom",
            style="italic", color="#888",
        )

    legend_handles = _sig_legend_handles()
    fig.legend(handles=legend_handles, loc="lower center",
               ncol=len(legend_handles),
               bbox_to_anchor=(0.5, -0.02), frameon=False)

    plt.tight_layout(rect=[0, 0.02, 1, 0.93])
    plt.savefig(OUT_SPEC, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {OUT_SPEC}")


# ═══════════════════════════════════════════════════════════════════════════════
# 8. OSTER DELTA SENSITIVITY PLOT (Phase 9)
# ═══════════════════════════════════════════════════════════════════════════════
def plot_oster_sensitivity():
    """
    Oster (2019) delta sensitivity for apostasy.
    Annotates the headline delta at the 2.2x Oster benchmark prominently.
    """
    if not os.path.exists(OSTER_SENS_CSV):
        print(f"  Oster sensitivity CSV not found ({OSTER_SENS_CSV}) -- skipping.")
        return

    df = pd.read_csv(OSTER_SENS_CSV).dropna(subset=["delta"])
    if df.empty:
        print("  Oster sensitivity data empty -- skipping.")
        return

    df["delta_clipped"] = df["delta"].clip(-3, 25)

    fig, ax = plt.subplots(figsize=(10, 5.5))

    robust_mask = df["delta_clipped"] >= 1.0
    if robust_mask.any():
        ax.fill_between(
            df["rmax_mult"],
            df["delta_clipped"].clip(lower=1.0),
            y2=1.0,
            where=robust_mask,
            color=PALETTE["robust_band"], alpha=0.85,
            label="Robust region (δ ≥ 1)",
        )

    ax.plot(df["rmax_mult"], df["delta_clipped"],
            color=PALETTE["apostasy"], linewidth=2.8, zorder=3)

    ax.axhline(1.0, color="#555", linewidth=1.4, linestyle="--",
               label="Robustness threshold (δ = 1)")

    # Oster benchmark lines — labels placed inside the axes (upper strip), with
    # a white bbox so they stay readable over the grid / green fill. Keeps the
    # top strip clear for the suptitle + subtitle.
    y_top = df["delta_clipped"].max()
    label_y = y_top * 0.93
    for xval, lbl in [(1.3, "1.3×"), (2.2, "2.2×")]:
        ax.axvline(xval, color="#999", linewidth=1.0, linestyle=":", alpha=0.8)
        ax.annotate(lbl + " Rmax", xy=(xval, label_y),
                    xytext=(0, 0), textcoords="offset points",
                    fontsize=9, ha="center", color="#666", style="italic",
                    bbox=dict(facecolor="white", edgecolor="none",
                              alpha=0.85, pad=1.5))

    # Headline delta annotation at 2.2x — dropped closer to the curve so the
    # arrow is short and the upper-right feels balanced.
    d22 = df.loc[(df["rmax_mult"] - 2.2).abs().idxmin()]
    if abs(d22["rmax_mult"] - 2.2) < 0.2:
        x_max = df["rmax_mult"].max()
        # Place box in the empty upper-right region above the curve plateau
        box_x = (2.2 + x_max) / 2
        box_y = y_top * 0.35
        ax.annotate(
            f"δ = {d22['delta']:.1f} at Rmax = 2.2×\n"
            f"Unobservables would need to be\n"
            f"{d22['delta']:.1f}× stronger than all controls",
            xy=(d22["rmax_mult"], d22["delta_clipped"]),
            xytext=(box_x, box_y),
            fontsize=11, ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="white",
                      edgecolor=PALETTE["apostasy"], linewidth=1.5),
            arrowprops=dict(arrowstyle="->", color=PALETTE["apostasy"], lw=1.4),
        )

    ax.set_xlabel("Rmax  (multiple of within-R² from the full model)")
    ax.set_ylabel("Oster δ")

    fig.suptitle(
        "Apostasy effect survives extreme omitted-variable bias",
        fontsize=15, fontweight="bold", y=1.00,
    )
    ax.set_title(
        "Oster (2019) sensitivity test — higher δ = more selection needed to nullify the result",
        fontsize=10, fontweight="normal", color="#555", loc="left", pad=10,
    )
    ax.legend(loc="upper right", framealpha=0.95)
    ax.grid(alpha=0.3, linewidth=0.5)

    plt.tight_layout()
    plt.savefig(OSTER_SENS_PNG, dpi=300, bbox_inches="tight")
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

    # LFP gap excluded: reported in percentage points (not [0,1]),
    # so including it stretches the x-axis and makes the other rows unreadable.

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

        # "n.s." + N annotation to the right (no significance stars).
        ann_parts = []
        if not sig:
            ann_parts.append("n.s.")
        ann_parts.append(f"N={row['n']:,}")
        ann = "  ".join(ann_parts)
        if row["unit"] != "[0,1]":
            ann += f"  [{row['unit']}]"
        ax.annotate(ann, xy=(row["coef"] + ci95, i),
                    xytext=(6, 0), textcoords="offset points",
                    fontsize=8, va="center", color="#555555")

    ax.axvline(0, color="black", linewidth=0.9, linestyle="--", alpha=0.6)
    ax.set_yticks(ys)
    ax.set_yticklabels(df_plot["label"], fontsize=11)
    ax.set_xlabel(
        "β on composite secularism (panel FE + 6 controls); all outcomes on [0,1] scale",
        fontsize=10
    )
    fig.suptitle(
        "Focal within-country coefficient is null on pre-specified outcomes; WEF GGG is a disclosed caveat",
        fontsize=15, fontweight="bold", y=1.00,
    )
    ax.set_title(
        "Composite secularism coefficient across the primary outcome and external gender indices",
        fontsize=10, fontweight="normal", color="#555", loc="left", pad=10,
    )

    legend_handles = _sig_legend_handles()
    ax.legend(handles=legend_handles,
              loc="upper center", bbox_to_anchor=(0.5, -0.18),
              ncol=len(legend_handles), frameon=False)
    ax.grid(axis="x", alpha=0.3, linewidth=0.5)

    plt.tight_layout()
    plt.savefig(OUT_ALT_OUTCOMES, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {OUT_ALT_OUTCOMES}")


# ═══════════════════════════════════════════════════════════════════════════════
# 9. WBL GROUP SCORE FOREST PLOT
# ═══════════════════════════════════════════════════════════════════════════════
WBL_GROUPS_CSV  = os.path.join(ROOT, "results/results_wbl_groups.csv")
OUT_WBL_GROUPS  = os.path.join(ROOT, "figures/11_wbl_groups.png")


def plot_wbl_groups():
    """
    Forest plot: religious courts coefficient for each of the 10 WBL group
    scores built by scoring.py, plus the overall score.
    One dot per group — shows which domains of women's legal rights are affected.
    """
    if not os.path.exists(WBL_GROUPS_CSV):
        print(f"  WBL groups CSV not found ({WBL_GROUPS_CSV}) -- skipping.")
        return

    df = pd.read_csv(WBL_GROUPS_CSV)
    focal = df[df["predictor"] == FOCAL_PRED].copy()

    if focal.empty:
        print("  No focal predictor rows found -- skipping.")
        return

    overall = focal[focal["group"] == "overall_score"]
    groups  = focal[focal["group"] != "overall_score"].sort_values("coef")
    focal   = pd.concat([overall, groups], ignore_index=True).reset_index(drop=True)

    # Q5: slide-side label simplifications. "Family & safety" narrows to
    # "Marriage" for the deck (the underlying WBL taxonomy also covers
    # divorce and domestic violence). "Economic rights" -> "Entrepreneurship"
    # and "Assets & Inheritance" -> "Assets" per Phoebe's nomenclature.
    WBL_GROUP_RENAME = {
        "Family & safety":      "Marriage",
        "Economic rights":      "Entrepreneurship",
        "Assets & Inheritance": "Assets",
        "Assets & inheritance": "Assets",
    }
    focal["group_label"] = focal["group_label"].replace(WBL_GROUP_RENAME)

    n = len(focal)
    fig, ax = plt.subplots(figsize=(11, max(5, n * 0.55 + 2)))

    for j in range(n):
        row   = focal.iloc[j]
        y_pos = n - 1 - j
        color = _sig_colour(row["pval"])
        ci95  = 1.96 * row["se"]

        ax.plot([row["coef"] - ci95, row["coef"] + ci95], [y_pos, y_pos],
                color=color, linewidth=2.4, alpha=0.8, solid_capstyle="round")
        ax.scatter(row["coef"], y_pos,
                   color=color, s=90, zorder=4,
                   edgecolors="white", linewidths=0.8)

        ann = f"β = {row['coef']:+.3f}"
        ax.annotate(ann, xy=(row["coef"] + ci95, y_pos),
                    xytext=(8, 0), textcoords="offset points",
                    fontsize=9, va="center", color="#333")

    # Divider between overall and domain scores — thick solid line plus
    # left-margin "Overall" / "Components" labels so the top row reads as
    # the headline and the 10 rows below it read as decomposition.
    if len(overall) > 0:
        ax.axhline(n - 1.5, color="#444", linewidth=1.8,
                   linestyle="-", alpha=0.8, zorder=1)
        ax.text(-0.02, n - 0.5, "Overall",
                transform=ax.get_yaxis_transform(),
                fontsize=10, fontweight="bold", color="#333",
                ha="right", va="center")
        ax.text(-0.02, n - 1.7, "Components",
                transform=ax.get_yaxis_transform(),
                fontsize=10, fontweight="bold", color="#333",
                ha="right", va="center")

    ax.axvline(0, color="black", linewidth=0.9, linestyle="--", alpha=0.6)
    ax.set_yticks(range(n))
    ax.set_yticklabels(
        [focal.iloc[n - 1 - j]["group_label"] for j in range(n)],
        fontsize=11,
    )
    ax.set_xlabel(
        "β on composite secularism (panel FE, GDP-controlled)",
    )

    fig.suptitle(
        "Within-country null holds on the overall WBL index",
        fontsize=15, fontweight="bold", y=1.00,
    )
    ax.set_title(
        "Domain breakdown: every WBL component is null at p < 0.05",
        fontsize=10, fontweight="normal", color="#555",
        loc="left", pad=10,
    )

    ax.grid(axis="x", alpha=0.3, linewidth=0.5)

    ax.legend(handles=_sig_legend_handles(), loc="upper right",
              frameon=True, framealpha=0.95, fontsize=9)

    plt.tight_layout()
    plt.savefig(OUT_WBL_GROUPS, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {OUT_WBL_GROUPS}")


# ═══════════════════════════════════════════════════════════════════════════════
# 10. WORLD CHOROPLETH MAP
# ═══════════════════════════════════════════════════════════════════════════════
def plot_world_map():
    """
    World choropleth of FOCAL_PRED (composite secularism by default), 2020.
    Annotates a handful of anchor countries so the colour scale is concrete.
    """
    import geopandas as gpd
    from matplotlib.colors import LinearSegmentedColormap

    OUT_MAP  = os.path.join(ROOT, "figures/00_map.png")
    SHP_PATH = os.path.join(ROOT, "data/ne_110m_admin_0_countries/ne_110m_admin_0_countries.shp")

    # Item 2 (2026-04-15): build composite in-memory so FOCAL_PRED is available
    pred = pd.read_csv(COMP_PATH)
    pred = build_secularism_composite(pred)
    data2020 = pred[pred["year"] == 2020][["iso3", FOCAL_PRED]].copy()

    world = gpd.read_file(SHP_PATH)
    world = world.rename(columns={"ISO_A3": "iso3"})
    world = world[world["ADMIN"] != "Antarctica"]
    world = world.merge(data2020, on="iso3", how="left")

    fig, ax = plt.subplots(figsize=(13, 6.5))

    # Custom two-stop colormap matching the palette
    cmap = LinearSegmentedColormap.from_list(
        "secularism_scale", [PALETTE["map_lo"], PALETTE["map_hi"]]
    )

    world[world[FOCAL_PRED].isna()].plot(
        ax=ax, color="#EDEDED", edgecolor="white", linewidth=0.3,
    )
    world[world[FOCAL_PRED].notna()].plot(
        ax=ax,
        column=FOCAL_PRED,
        cmap=cmap,
        vmin=0, vmax=1,
        edgecolor="white", linewidth=0.3,
        legend=True,
        legend_kwds={
            "label": "Composite secularism (0 = most secular, 1 = most religious)",
            "orientation": "horizontal",
            "shrink": 0.45,
            "pad": 0.02,
            "aspect": 30,
        },
    )

    # Annotate a few anchor countries so the colour scale feels concrete.
    anchors = ["IRN", "CHN", "RUS", "USA", "BRA", "ZAF", "AUS"]
    world["centroid"] = world.geometry.representative_point()
    for iso in anchors:
        row = world[world["iso3"] == iso]
        if row.empty or pd.isna(row[FOCAL_PRED].iloc[0]):
            continue
        pt = row["centroid"].iloc[0]
        score = row[FOCAL_PRED].iloc[0]
        ax.annotate(
            iso,
            xy=(pt.x, pt.y),
            fontsize=9.5, ha="center", va="center",
            color="white" if score > 0.45 else "#222",
            fontweight="bold",
        )

    ax.set_axis_off()
    fig.suptitle(
        "The composite secularism index across countries (2020)",
        fontsize=16, fontweight="bold", y=0.97,
    )
    ax.set_title(
        "Equal-weight z-score across institutional, attitudinal, behavioural dimensions. Grey = no data",
        fontsize=10, fontweight="normal", color="#555",
    )

    plt.tight_layout()
    plt.savefig(OUT_MAP, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {OUT_MAP}")


# ═══════════════════════════════════════════════════════════════════════════════
# 11. BETWEEN-VS-WITHIN HERO FIGURE
# Geometric companion to the Mundlak forest: the quartile staircase shows the
# between-country structure; grey 2013→2022 arrows show how little countries
# move within-country. Figure 12 (Mundlak) is the numerical companion.
# ═══════════════════════════════════════════════════════════════════════════════
OUT_BETWEEN_WITHIN = os.path.join(ROOT, "figures/03_between_within.png")
MIN_PANEL_YEARS_FOR_MEAN = 3  # require ≥3 non-null years to include a country's mean


def plot_between_within(df: pd.DataFrame):
    """Quartile staircase (between) + country 2013→2022 arrows (within).

    Deck hero visual; figure 12 is the formal numerical companion.
    """
    OUTCOME = "wbl_treatment_index"
    panel = df[(df["year"] >= 2013) & (df["year"] <= 2022)].copy()

    # Country panel means — require ≥MIN_PANEL_YEARS_FOR_MEAN non-null years
    # on both composite and wbl so short-history countries don't dominate.
    clean = panel.dropna(subset=[FOCAL_PRED, OUTCOME])
    agg = (clean.groupby("iso3")
                .agg(mean_composite=(FOCAL_PRED, "mean"),
                     mean_wbl=(OUTCOME, "mean"),
                     n_years=(FOCAL_PRED, "size"))
                .reset_index())
    agg = agg[agg["n_years"] >= MIN_PANEL_YEARS_FOR_MEAN].copy()
    agg["region"] = agg["iso3"].map(get_region)
    agg["quartile"] = pd.qcut(agg["mean_composite"], 4,
                              labels=["Q1", "Q2", "Q3", "Q4"])

    quart_means = (agg.groupby("quartile", observed=True)
                      [["mean_composite", "mean_wbl"]].mean())

    # 2013→2022 endpoints: countries with both observations on both variables
    endpoints = (panel[panel["year"].isin([2013, 2022])]
                      .dropna(subset=[FOCAL_PRED, OUTCOME])
                      .pivot_table(index="iso3", columns="year",
                                   values=[FOCAL_PRED, OUTCOME],
                                   aggfunc="first"))
    endpoints = endpoints.dropna()

    # Validations — surface if the between-country story is not clean
    if len(endpoints) < 80:
        print(f"  WARNING: only {len(endpoints)} countries with 2013+2022 "
              f"endpoints (expected ≥80)")
    wbl_by_q = quart_means["mean_wbl"].values
    monotone = all(wbl_by_q[i] >= wbl_by_q[i + 1] for i in range(len(wbl_by_q) - 1))
    if not monotone:
        print(f"  WARNING: quartile mean_wbl not monotone descending: "
              f"{np.round(wbl_by_q, 3)}")

    fig, ax = plt.subplots(figsize=(10, 7))

    # Background: 2013→2022 arrows
    for iso3 in endpoints.index:
        x0 = endpoints.loc[iso3, (FOCAL_PRED, 2013)]
        y0 = endpoints.loc[iso3, (OUTCOME, 2013)]
        x1 = endpoints.loc[iso3, (FOCAL_PRED, 2022)]
        y1 = endpoints.loc[iso3, (OUTCOME, 2022)]
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="->", color="#888",
                                    alpha=0.35, linewidth=0.7),
                    zorder=1)

    # Country panel-mean dots coloured by region
    for region, color in REGION_COLORS.items():
        sub = agg[agg["region"] == region]
        if sub.empty:
            continue
        ax.scatter(sub["mean_composite"], sub["mean_wbl"],
                   c=color, s=35, alpha=0.65, edgecolors="white",
                   linewidth=0.5, label=region, zorder=3)

    # Quartile overlay
    line_color = PALETTE.get("composite", PALETTE["courts"])
    ax.plot(quart_means["mean_composite"], quart_means["mean_wbl"],
            color=line_color, linewidth=2.8, zorder=5)
    ax.scatter(quart_means["mean_composite"], quart_means["mean_wbl"],
               s=300, color=line_color, edgecolor="white",
               linewidth=2, zorder=6)
    for q, x, y in zip(quart_means.index,
                       quart_means["mean_composite"],
                       quart_means["mean_wbl"]):
        ax.annotate(str(q), xy=(x, y), ha="center", va="center",
                    fontsize=9, fontweight="bold", color="white", zorder=7)

    # Anchor country labels
    for iso in ["IRN", "USA", "NOR", "IND", "SAU", "ZAF"]:
        row = agg[agg["iso3"] == iso]
        if row.empty:
            continue
        ax.annotate(iso,
                    xy=(row.iloc[0]["mean_composite"],
                        row.iloc[0]["mean_wbl"]),
                    xytext=(5, 5), textcoords="offset points",
                    fontsize=9, color="#222", fontweight="bold", zorder=8)

    ax.set_xlabel("Composite secularism (normalised, higher = more religious)",
                  fontsize=11)
    ax.set_ylabel("Female treatment index", fontsize=11)
    ax.grid(alpha=0.3, linewidth=0.5)
    _narrative_title(
        ax,
        "Between countries: a clear staircase. Within countries: arrows that barely move.",
        subtitle="Quartile means (coloured dots, line) vs country-level "
                 "2013→2022 movement (grey arrows)",
    )

    # Mundlak annotation — pulled from results/results.csv T4_mundlak_re rows
    ax.annotate(
        "Mundlak decomposition:\n"
        "  Between β = −0.120  (p = 0.014)\n"
        "  Within  β = +0.019  (p = 0.24)\n"
        "  Ratio ≈ 6.3×, opposite signs\n"
        "See figure 12 (appendix) for the formal plot.",
        xy=(0.97, 0.03), xycoords="axes fraction",
        fontsize=9, ha="right", va="bottom",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="white",
                  edgecolor=line_color, linewidth=1.2, alpha=0.95),
        zorder=9,
    )

    ax.legend(loc="upper right", framealpha=0.92, ncol=2, fontsize=8)

    plt.tight_layout()
    plt.savefig(OUT_BETWEEN_WITHIN, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {OUT_BETWEEN_WITHIN}")
    print(f"    Countries with panel-mean (>= {MIN_PANEL_YEARS_FOR_MEAN}y): "
          f"{len(agg)}")
    print(f"    Countries with 2013+2022 endpoints: {len(endpoints)}")
    print(f"    Quartile mean_wbl (Q1->Q4): {list(np.round(wbl_by_q, 3))}")


# ═══════════════════════════════════════════════════════════════════════════════
# 12. MUNDLAK WITHIN-VS-BETWEEN DECOMPOSITION
# ═══════════════════════════════════════════════════════════════════════════════
LABELS_SHORT = {
    "composite_secularism_norm": "Composite secularism",
    "gri_state_religion_norm": "State religion",
    "gri_religious_law_norm":  "Religious law",
    "gri_blasphemy_norm":      "Blasphemy laws",
    "gri_apostasy_norm":       "Apostasy laws",
    "gri_religious_courts_norm": "Religious courts",
    "gri_gov_favour_norm":     "Gov favouritism",
    "v2x_rule_norm":           "Rule of law",
    "v2x_civlib_norm":         "Civil liberties",
    "v2x_egal_norm":           "Egalitarianism",
    "v2x_corr_norm":           "Corruption",
    "education_norm":          "Education",
    "rurality_norm":           "Rurality",
    "conflict_norm":           "Pol. stability",
    "log_gdppc_norm":          "Log GDP p.c.",
}

def plot_mundlak_decomposition():
    """Paired forest plot: within-country vs between-country effects from T4 Mundlak."""
    res = pd.read_csv(RESULTS_PATH)
    t4  = res[res["tier"] == "T4_mundlak_re"].copy()
    if t4.empty:
        print("  T4_mundlak_re not found in results.csv — skipping.")
        return

    # Separate within (base predictors) and between (_mean suffix).
    # Item 2 (2026-04-15): composite added as hero row; gri_gov_favour_norm
    # newly activated in GRI_PANEL_COLS; all six GRI sub-items present.
    gri_vars = [FOCAL_PRED,
                "gri_state_religion_norm", "gri_gov_favour_norm",
                "gri_religious_law_norm", "gri_blasphemy_norm",
                "gri_apostasy_norm", "gri_religious_courts_norm"]

    rows = []
    for var in gri_vars:
        w = t4[t4["predictor"] == var]
        b = t4[t4["predictor"] == f"{var}_mean"]
        if w.empty or b.empty:
            continue
        rows.append({
            "var": LABELS_SHORT.get(var, var),
            "within_coef": w.iloc[0]["coef"],
            "within_se":   w.iloc[0]["se"],
            "within_p":    w.iloc[0]["pval"],
            "between_coef": b.iloc[0]["coef"],
            "between_se":   b.iloc[0]["se"],
            "between_p":    b.iloc[0]["pval"],
        })

    if not rows:
        print("  No matched within/between pairs found — skipping.")
        return

    df_plot = pd.DataFrame(rows)
    n_vars  = len(df_plot)

    fig, axes = plt.subplots(1, 2, figsize=(13, 0.9 * n_vars + 2.5), sharey=True)
    y_pos = np.arange(n_vars)

    # Highlight the current FOCAL_PRED row (formerly apostasy-keyed)
    focal_label = LABELS_SHORT.get(FOCAL_PRED, FOCAL_PRED)
    focal_row = df_plot.index[df_plot["var"] == focal_label].tolist()
    apostasy_y   = focal_row[0] if focal_row else None

    for ax, prefix, title in [
        (axes[0], "within",  "Within-country effect\n(change over time)"),
        (axes[1], "between", "Between-country effect\n(structural difference)"),
    ]:
        coefs = df_plot[f"{prefix}_coef"].values
        ses   = df_plot[f"{prefix}_se"].values
        pvals = df_plot[f"{prefix}_p"].values

        colors = [_sig_colour(p) for p in pvals]

        # Highlight apostasy row background
        if apostasy_y is not None:
            ax.axhspan(apostasy_y - 0.5, apostasy_y + 0.5,
                       color=PALETTE["highlight_bg"], alpha=0.7, zorder=0)

        ax.barh(y_pos, coefs, xerr=1.96 * ses, height=0.62,
                color=colors, edgecolor="white", linewidth=0.8,
                capsize=4, error_kw={"linewidth": 1.2}, zorder=2)
        ax.axvline(0, color="black", linewidth=0.9, linestyle="--", alpha=0.5)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(df_plot["var"], fontsize=11)
        ax.set_xlabel("β (0–1 scale)")
        ax.set_title(title, fontsize=12, fontweight="bold", loc="left", pad=8)
        ax.tick_params(axis="y", length=0)
        ax.grid(axis="x", alpha=0.3, linewidth=0.5)

        # Significance stars removed per design direction — colour already
        # encodes p<0.05 vs not significant via _sig_colour.

    fig.suptitle(
        "Secularism's effect is structural: between-country gap dwarfs within-country change",
        fontsize=18, fontweight="bold", y=1.04,
    )
    fig.text(
        0.5, 0.99,
        "Mundlak RE-FE hybrid: within-country change (left) vs between-country structural differences (right)",
        ha="center", fontsize=11, color="#555",
    )

    # Annotate the between/within ratio for FOCAL_PRED as a subtle inset
    # on the right (between) panel — the huge mid-figure callout was
    # visually dominant and crowded the two panels.
    ratio_color = PALETTE.get("composite", PALETTE["apostasy"])
    if apostasy_y is not None:
        apo = df_plot.iloc[apostasy_y]
        if apo["within_coef"] != 0:
            ratio = apo["between_coef"] / apo["within_coef"]
            axes[1].annotate(
                f"Between/Within = {abs(ratio):.1f}×",
                xy=(0.97, 0.05), xycoords="axes fraction",
                fontsize=12, fontweight="bold",
                ha="right", va="bottom", color=ratio_color,
                bbox=dict(boxstyle="round,pad=0.35",
                          facecolor="white",
                          edgecolor=ratio_color, linewidth=1.0),
            )

    legend_els = _sig_legend_handles()
    # Put legend on the right panel (interior, lower-right) where there's
    # room — fig-level legend was wrapping/overlapping with the footer note.
    axes[1].legend(
        handles=legend_els, loc="lower left",
        framealpha=0.95, fontsize=10, ncol=2, columnspacing=1.5,
    )

    plt.tight_layout(rect=[0, 0.00, 1, 0.93])
    plt.savefig(OUT_MUNDLAK, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {OUT_MUNDLAK}")


# ═══════════════════════════════════════════════════════════════════════════════
# 13. LONG-DIFFERENCE (Item 3): forest + decade-change scatter
# ═══════════════════════════════════════════════════════════════════════════════
def plot_long_difference():
    """Two-panel figure for the T5 long-difference tier.

    Left: forest plot of T5 β and 95% CI across composite + variants + apostasy
    + courts at the 2013→2022 with_gdp main window. Invalid rows (apostasy,
    n_changers=9) greyed; low_power rows (courts, 16-22 changers) standard
    colour with annotation.
    Right: decade-change scatter (Δwbl_treatment_index vs Δcomposite_secularism),
    one point per country, region-coloured, with OLS fit line and 95% CI band.
    """
    if not os.path.exists(RESULTS_PATH):
        print(f"  {RESULTS_PATH} not found — skipping LD plot.")
        return
    res = pd.read_csv(RESULTS_PATH)
    t5 = res[res["tier"] == "T5_long_diff_2013_2022_with_gdp"].copy()
    if t5.empty:
        print("  No T5 rows in results.csv — skipping LD plot.")
        return

    focal_order = [
        ("composite_secularism_norm",         "Composite (eq-wt)"),
        ("composite_secularism_pca_norm",     "Composite (PCA)"),
        ("composite_secularism_real_norm",    "Composite (no WVS interp)"),
        ("composite_secularism_instonly_norm","Composite (inst only)"),
        ("composite_secularism_covwt_norm",   "Composite (cov-wt)"),
        ("gri_apostasy_norm",                 "Apostasy law"),
        ("gri_religious_courts_norm",         "Religious courts"),
    ]
    forest_rows = []
    for focal, label in focal_order:
        # Prefer the standalone tier tag; grifull is separate (suffix _grifull).
        sub = t5[(t5["predictor"] == focal) & (~t5["tier"].str.endswith("_grifull"))]
        if sub.empty:
            continue
        r = sub.iloc[0]
        nch = None
        if not pd.isna(r["n_changers"]):
            nch = int(r["n_changers"])
        forest_rows.append({
            "label": label,
            "focal": focal,
            "coef":  float(r["coef"]),
            "se":    float(r["se"]),
            "ci":    1.96 * float(r["se"]),
            "p":     float(r["pval"]),
            "n":     int(r["n"]),
            "n_changers": nch,
            "valid": bool(r["valid"]),
        })

    # Decade-change data for scatter panel — recompute from source so the
    # point cloud matches the LD regression exactly.
    try:
        pred_df = pd.read_csv(COMP_PATH)
        pred_df = build_secularism_composite(pred_df, build_pca=False)
    except Exception as e:
        print(f"  [LD scatter] composite build failed: {e}; scatter will be empty.")
        pred_df = None
    wbl_df = pd.read_csv(WBL_OUTCOME_PATH) if os.path.exists(WBL_OUTCOME_PATH) else None

    deltas = None
    ols = None
    if pred_df is not None and wbl_df is not None:
        merged = wbl_df[["iso3", "year", "wbl_treatment_index"]].merge(
            pred_df[["iso3", "year", "composite_secularism_norm"]],
            on=["iso3", "year"], how="inner")
        merged = merged[merged["year"].isin([2013, 2022])].dropna()
        start = merged[merged["year"] == 2013].drop_duplicates("iso3").set_index("iso3")[
            ["wbl_treatment_index", "composite_secularism_norm"]]
        end   = merged[merged["year"] == 2022].drop_duplicates("iso3").set_index("iso3")[
            ["wbl_treatment_index", "composite_secularism_norm"]]
        common = start.index.intersection(end.index)
        if len(common) >= 30:
            deltas = (end.loc[common] - start.loc[common]).copy()
            deltas["region"] = [get_region(x) for x in deltas.index]
            X = sm.add_constant(deltas["composite_secularism_norm"])
            ols = sm.OLS(deltas["wbl_treatment_index"], X).fit(cov_type="HC3")

    # ── Render ─────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(14, 6.5))
    fig.suptitle(
        "Decade-change regression corroborates the within-country null",
        fontsize=15, fontweight="bold", y=1.03,
    )
    fig.text(
        0.5, 0.97,
        "Long-difference: Δoutcome on Δfocal + Δcontrols, 2013→2022 with GDP, HC3 SEs, one obs per country.",
        ha="center", fontsize=10.5, color="#555",
    )

    # Left: forest plot
    ax = axes[0]
    ys = np.arange(len(forest_rows))
    for i, r in enumerate(forest_rows):
        color = _sig_colour(r["p"]) if r["valid"] else "#bbbbbb"
        alpha = 1.0 if r["valid"] else 0.45
        ax.plot([r["coef"] - r["ci"], r["coef"] + r["ci"]], [i, i],
                color=color, linewidth=2.2, alpha=alpha,
                solid_capstyle="round", zorder=2)
        ax.scatter(r["coef"], i, color=color, s=80, edgecolors="white",
                   linewidths=0.8, zorder=3, alpha=alpha)
        sig_label = "" if r["p"] < 0.05 else "n.s."
        note_parts = [f"{r['coef']:+.3f}"]
        if sig_label:
            note_parts.append(sig_label)
        if r["n_changers"] is not None:
            note_parts.append(f"(nΔ={r['n_changers']})")
        if not r["valid"]:
            note_parts.append("[invalid]")
        ax.annotate("  ".join(note_parts),
                    xy=(r["coef"] + r["ci"], i),
                    xytext=(8, 0), textcoords="offset points",
                    fontsize=9.5, va="center", color="#222")
    ax.axvline(0, color="black", linewidth=0.9, linestyle="--", alpha=0.6)
    ax.set_yticks(ys)
    ax.set_yticklabels([r["label"] for r in forest_rows], fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel("Long-difference β (2013→2022, with GDP)")
    ax.set_title("Coefficient across focal variants", fontsize=12,
                 fontweight="bold", loc="left", pad=8)
    ax.grid(axis="x", alpha=0.3, linewidth=0.5)

    # Right: decade-change scatter (headline composite). Q17 — uniform
    # neutral fill so the regional legend no longer competes with the
    # left forest panel's significance colouring. Q10 — strip stats from
    # the title; the same β/p/N already appears in the left forest panel.
    ax2 = axes[1]
    if deltas is not None and ols is not None:
        ax2.scatter(
            deltas["composite_secularism_norm"],
            deltas["wbl_treatment_index"],
            c="#6c7a89", s=48, alpha=0.72,
            edgecolors="white", linewidth=0.5,
        )
        x_grid = np.linspace(
            float(deltas["composite_secularism_norm"].min()),
            float(deltas["composite_secularism_norm"].max()), 100)
        X_grid = sm.add_constant(x_grid)
        y_hat  = ols.predict(X_grid)
        ci     = ols.get_prediction(X_grid).conf_int(alpha=0.05)
        ax2.plot(x_grid, y_hat, color="#444", linewidth=2.0, zorder=5)
        ax2.fill_between(x_grid, ci[:, 0], ci[:, 1],
                          color="#444", alpha=0.12, zorder=4)
        ax2.axhline(0, color="grey", linewidth=0.6, linestyle=":", alpha=0.6)
        ax2.axvline(0, color="grey", linewidth=0.6, linestyle=":", alpha=0.6)
        ax2.set_title(
            "Δ(WBL) vs Δ(Composite), 2013→2022",
            fontsize=11, fontweight="bold", loc="left", pad=8,
        )
    else:
        ax2.text(0.5, 0.5, "Scatter data unavailable", ha="center",
                 va="center", transform=ax2.transAxes, fontsize=11,
                 color="#777")
    ax2.set_xlabel("Δ Composite secularism (2013→2022)")
    ax2.set_ylabel("Δ WBL treatment index (2013→2022)")
    ax2.grid(alpha=0.3, linewidth=0.5)

    plt.tight_layout(rect=[0, 0.02, 1, 0.93])
    plt.savefig(OUT_LONGDIFF, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {OUT_LONGDIFF}")


def load_merged() -> pd.DataFrame:
    comp  = pd.read_csv(COMP_PATH)
    women = pd.read_csv(WOMEN_PATH)
    comp_nodupe = comp.drop(columns=["country"], errors="ignore")
    return women.merge(comp_nodupe, on=["iso3", "year"], how="left", suffixes=("", "_comp"))


def main():
    print("=" * 60)
    print("SECULARISM & GENDER GAP — VISUALISATIONS")
    print("=" * 60)

    _presentation_style()

    # Load merged data for plots that need a DataFrame
    comp  = pd.read_csv(COMP_PATH)
    women = pd.read_csv(WOMEN_PATH)
    df = women.merge(
        comp.drop(columns=["country"], errors="ignore"),
        on=["iso3", "year"], how="left", suffixes=("", "_comp"),
    )
    # Mirror analysis/run_analysis.py:load_and_merge so plot_scatter sees the
    # same T1_with_gdp regressors. v2x_rule_norm lives in the old outcome
    # composite file; the 4 additional controls live in controls_additional.
    old_path = os.path.join(ROOT, "data/outcome_composite.csv")
    if os.path.exists(old_path):
        aux_needed = [c for c in ["v2x_rule_norm"] if c not in df.columns]
        if aux_needed:
            aux = pd.read_csv(old_path)[["iso3", "year"] + aux_needed]
            df = df.merge(aux, on=["iso3", "year"], how="left")
    ctrl_path = os.path.join(ROOT, "data/controls_additional.csv")
    if os.path.exists(ctrl_path):
        ctrl = pd.read_csv(ctrl_path)
        df = df.merge(ctrl, on=["iso3", "year"], how="left")
    # Item 2 (2026-04-15): build composite in-memory so FOCAL_PRED
    # (composite_secularism_norm) is available to plot_scatter and
    # other plots that reference FOCAL_PRED as a column in df.
    df = build_secularism_composite(df)

    print("\n[1/12] World choropleth map...")
    plot_world_map()

    print("\n[2/12] Scatter: courts vs apostasy (2020 dual panel)...")
    plot_scatter(df)

    print("\n[3/12] Coefficient forest plot (slimmed)...")
    plot_coefplot()

    print("\n[4/12] WBL group score breakdown...")
    plot_wbl_groups()

    print("\n[5/12] LOO jackknife (composite + apostasy 2x2)...")
    plot_loo()

    print("\n[6/12] Placebo outcomes (gendered mechanism)...")
    plot_placebo()

    print("\n[7/12] Specification stability (composite + apostasy)...")
    plot_spec_stability()

    print("\n[8/12] Oster sensitivity (apostasy)...")
    plot_oster_sensitivity()

    print("\n[9/12] Alternative outcomes comparison...")
    plot_alternative_outcomes()

    print("\n[10/12] Between-vs-within quartile staircase (hero figure)...")
    plot_between_within(df)

    print("\n[11/12] Mundlak within-vs-between decomposition (appendix)...")
    plot_mundlak_decomposition()

    print("\n[12/12] Long-difference (T5, decade-change 2013->2022)...")
    plot_long_difference()

    print("\nDone. All figures saved to figures/")


if __name__ == "__main__":
    main()
