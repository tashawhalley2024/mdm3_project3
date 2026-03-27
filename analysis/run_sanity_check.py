"""
Sanity check: compare actual.csv (WBL INDEX/100) against baseline.csv
(women_treatment_index). All outputs saved to sanity_check/
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "sanity_check")
os.makedirs(OUT, exist_ok=True)

# ── 1. Load files ─────────────────────────────────────────────────────────────
print("Loading files ...")
baseline = pd.read_csv(os.path.join(OUT, "baseline.csv"))
actual   = pd.read_csv(os.path.join(OUT, "actual.csv"))

print(f"  baseline.csv : {len(baseline):,} rows, {baseline['iso3'].nunique()} countries")
print(f"  actual.csv   : {len(actual):,} rows, {actual['iso3'].nunique()} countries")

# ── 2. Inspect ────────────────────────────────────────────────────────────────
base_dups = baseline.duplicated(subset=["iso3", "year"]).sum()
act_dups  = actual.duplicated(subset=["iso3", "year"]).sum()
print(f"  Duplicates (iso3+year): baseline={base_dups}, actual={act_dups}")

base_in_range = baseline["baseline_value"].between(0, 1).all()
act_in_range  = actual["actual_value"].between(0, 1).all()
print(f"  Values in [0,1]: baseline={base_in_range}, actual={act_in_range}")

# ── 3. Coverage audit ─────────────────────────────────────────────────────────
print("\nBuilding coverage_audit.csv ...")

base_keys = set(zip(baseline["iso3"], baseline["year"]))
act_keys  = set(zip(actual["iso3"],   actual["year"]))
all_keys  = base_keys | act_keys

base_idx = baseline.set_index(["iso3", "year"])
act_idx  = actual.set_index(["iso3", "year"])

audit_rows = []
for iso3, year in sorted(all_keys):
    in_base = (iso3, year) in base_keys
    in_act  = (iso3, year) in act_keys

    base_val = base_idx.loc[(iso3, year), "baseline_value"] if in_base else np.nan
    act_val  = act_idx.loc[(iso3, year), "actual_value"]   if in_act  else np.nan

    base_missing = in_base and pd.isna(base_val)
    act_missing  = in_act  and pd.isna(act_val)

    country = base_idx.loc[(iso3, year), "country"] if in_base else act_idx.loc[(iso3, year), "country"]
    match_status = "iso3_match" if (in_base and in_act) else "one_side_only"
    included = in_base and in_act and not base_missing and not act_missing

    if included:
        reason = ""
    elif not in_base:
        reason = "country-year not in baseline"
    elif not in_act:
        reason = "country-year not in actual"
    elif base_missing:
        reason = "missing baseline value"
    elif act_missing:
        reason = "missing actual value"
    else:
        reason = "other"

    audit_rows.append({
        "iso3": iso3, "country": country, "year": year,
        "present_in_baseline": in_base, "present_in_actual": in_act,
        "baseline_value_missing": base_missing, "actual_value_missing": act_missing,
        "country_match_status": match_status,
        "included_in_strict_overlap": included,
        "exclusion_reason": reason,
    })

audit = pd.DataFrame(audit_rows)
audit.to_csv(os.path.join(OUT, "coverage_audit.csv"), index=False, encoding="utf-8")
print(f"  Total country-years audited: {len(audit):,}")
print(f"  Included in strict overlap : {audit['included_in_strict_overlap'].sum():,}")
print(f"  Excluded                   : {(~audit['included_in_strict_overlap']).sum():,}")

# ── 4. Uncertain country matches ──────────────────────────────────────────────
uncertain = pd.DataFrame(columns=[
    "original_name_baseline", "original_name_actual", "proposed_match",
    "match_reason", "confidence_level", "included_in_strict_overlap"
])
uncertain.to_csv(os.path.join(OUT, "uncertain_country_matches.csv"), index=False, encoding="utf-8")
print("  uncertain_country_matches.csv: 0 uncertain matches (direct iso3 join)")

# ── 5. Build strict overlap ───────────────────────────────────────────────────
print("\nBuilding overlap_comparison.csv ...")
overlap = baseline.merge(actual[["iso3", "year", "actual_value"]], on=["iso3", "year"], how="inner")
overlap = overlap.dropna(subset=["baseline_value", "actual_value"])
overlap["difference_signed"]   = (overlap["actual_value"] - overlap["baseline_value"]).round(6)
overlap["difference_absolute"] = overlap["difference_signed"].abs().round(6)
overlap = overlap.sort_values(["iso3", "year"]).reset_index(drop=True)
overlap.to_csv(os.path.join(OUT, "overlap_comparison.csv"), index=False, encoding="utf-8")
print(f"  Matched rows:      {len(overlap):,}")
print(f"  Matched countries: {overlap['iso3'].nunique()}")

# ── 6. Core metrics ───────────────────────────────────────────────────────────
print("\nComputing core metrics ...")
b = overlap["baseline_value"].values
a = overlap["actual_value"].values

pearson_r,  pearson_p  = stats.pearsonr(b, a)
spearman_r, spearman_p = stats.spearmanr(b, a)
mae         = np.mean(np.abs(a - b))
rmse        = np.sqrt(np.mean((a - b) ** 2))
mean_signed = np.mean(a - b)

print(f"  N matched obs   : {len(overlap):,}")
print(f"  Pearson r       : {pearson_r:.4f}  (p={pearson_p:.2e})")
print(f"  Spearman rho    : {spearman_r:.4f}  (p={spearman_p:.2e})")
print(f"  MAE             : {mae:.4f}")
print(f"  RMSE            : {rmse:.4f}")
print(f"  Mean signed diff: {mean_signed:.4f}  (actual - baseline)")

# ── 7. Year-by-year ───────────────────────────────────────────────────────────
print("\nYear-by-year analysis ...")
yy_rows = []
for year, grp in overlap.groupby("year"):
    bv = grp["baseline_value"].values
    av = grp["actual_value"].values
    nn = len(grp)
    pr, sr = (np.nan, np.nan)
    if nn >= 5:
        pr, _ = stats.pearsonr(bv, av)
        sr, _ = stats.spearmanr(bv, av)
    yy_rows.append({
        "year": year, "n": nn,
        "pearson_r":  round(pr, 4) if not np.isnan(pr) else None,
        "spearman_r": round(sr, 4) if not np.isnan(sr) else None,
        "mae":              round(np.mean(np.abs(av - bv)), 4),
        "mean_signed_diff": round(np.mean(av - bv), 4),
    })
yy = pd.DataFrame(yy_rows)
yy_pearson_range = yy["pearson_r"].max() - yy["pearson_r"].min()
include_yy_plot = yy_pearson_range > 0.1
print(f"  Year pearson range: {yy_pearson_range:.4f} -> year-by-year plot {'included' if include_yy_plot else 'omitted (stable)'}")

# ── 8. Diagnostics ───────────────────────────────────────────────────────────
top5_pos = overlap.nlargest(5,  "difference_signed")[["iso3","country","year","baseline_value","actual_value","difference_signed"]]
top5_neg = overlap.nsmallest(5, "difference_signed")[["iso3","country","year","baseline_value","actual_value","difference_signed"]]

# ── 9. Profile actual ─────────────────────────────────────────────────────────
print("\nProfiling actual.csv ...")
av_all = actual["actual_value"].dropna()
skew_val = float(stats.skew(av_all))
kurt_val  = float(stats.kurtosis(av_all))

if abs(skew_val) < 0.2:
    skew_label = "approximately symmetric"
elif abs(skew_val) < 0.5:
    skew_label = ("mildly right" if skew_val > 0 else "mildly left") + " skewed"
elif abs(skew_val) < 1.0:
    skew_label = ("moderately right" if skew_val > 0 else "moderately left") + " skewed"
else:
    skew_label = ("strongly right" if skew_val > 0 else "strongly left") + " skewed"

profile = {
    "n_obs": len(av_all), "n_countries": actual["iso3"].nunique(),
    "n_years": actual["year"].nunique(),
    "missing_pct": round(actual["actual_value"].isna().mean() * 100, 2),
    "mean":   round(float(av_all.mean()), 4),
    "median": round(float(av_all.median()), 4),
    "std":    round(float(av_all.std()), 4),
    "min":    round(float(av_all.min()), 4),
    "max":    round(float(av_all.max()), 4),
    "q25":    round(float(av_all.quantile(0.25)), 4),
    "q75":    round(float(av_all.quantile(0.75)), 4),
    "skewness": round(skew_val, 4), "skewness_label": skew_label,
    "kurtosis": round(kurt_val, 4),
}
print(f"  Mean={profile['mean']}  Median={profile['median']}  SD={profile['std']}")
print(f"  Skewness={profile['skewness']} ({skew_label})")

# ── 10. Plots ─────────────────────────────────────────────────────────────────
print("\nGenerating plots ...")

# Scatter
fig, ax = plt.subplots(figsize=(6, 6))
ax.scatter(overlap["baseline_value"], overlap["actual_value"],
           alpha=0.25, s=8, color="#2c7bb6", rasterized=True)
ax.plot([0, 1], [0, 1], "k--", lw=1, label="45-degree line")
ax.set_xlabel("Baseline index (women_treatment_index)", fontsize=11)
ax.set_ylabel("Actual index (WBL / 100)", fontsize=11)
ax.set_title("Actual vs Baseline: country-year comparison", fontsize=12)
ax.set_xlim(-0.02, 1.02); ax.set_ylim(-0.02, 1.02)
ax.text(0.05, 0.93,
        f"Pearson r = {pearson_r:.3f}\nSpearman rho = {spearman_r:.3f}\nN = {len(overlap):,}",
        transform=ax.transAxes, fontsize=9, va="top",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))
ax.legend(fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "comparison_scatter.png"), dpi=150)
plt.close()
print("  Saved -> comparison_scatter.png")

# Histogram
fig, ax = plt.subplots(figsize=(7, 4))
ax.hist(av_all, bins=40, color="#2c7bb6", edgecolor="white", linewidth=0.4)
ax.axvline(profile["mean"],   color="red",    lw=1.5, linestyle="--", label=f"Mean ({profile['mean']:.3f})")
ax.axvline(profile["median"], color="orange", lw=1.5, linestyle=":",  label=f"Median ({profile['median']:.3f})")
ax.set_xlabel("Actual value (WBL index / 100)", fontsize=11)
ax.set_ylabel("Count", fontsize=11)
ax.set_title("Distribution of Actual index (WBL / 100), 2007-2022", fontsize=12)
ax.legend(fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "actual_histogram.png"), dpi=150)
plt.close()
print("  Saved -> actual_histogram.png")

if include_yy_plot:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(yy["year"], yy["pearson_r"],  marker="o", color="#2c7bb6", label="Pearson r")
    ax.plot(yy["year"], yy["spearman_r"], marker="s", color="#d7191c", linestyle="--", label="Spearman rho")
    ax.set_xlabel("Year", fontsize=11); ax.set_ylabel("Correlation", fontsize=11)
    ax.set_title("Agreement between actual and baseline by year", fontsize=12)
    ax.legend(fontsize=9); ax.set_ylim(0, 1)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "correlation_by_year.png"), dpi=150)
    plt.close()
    print("  Saved -> correlation_by_year.png")

# ── 11. Report ────────────────────────────────────────────────────────────────
print("\nWriting sanity_check_report.md ...")

def to_md_table(df):
    cols = df.columns.tolist()
    header = "| " + " | ".join(cols) + " |"
    sep    = "| " + " | ".join(["---"] * len(cols)) + " |"
    rows   = ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join([header, sep] + rows)

top5_pos_str = to_md_table(top5_pos[["iso3","year","baseline_value","actual_value","difference_signed"]])
top5_neg_str = to_md_table(top5_neg[["iso3","year","baseline_value","actual_value","difference_signed"]])

report = f"""# Sanity Check: Actual (WBL/100) vs Baseline (women_treatment_index)

## Core metrics

| Metric | Value |
|---|---|
| Matched observations | {len(overlap):,} |
| Countries | {overlap['iso3'].nunique()} |
| Pearson r | {pearson_r:.4f} |
| Spearman rho | {spearman_r:.4f} |
| MAE | {mae:.4f} |
| RMSE | {rmse:.4f} |
| Mean signed diff (actual - baseline) | {mean_signed:+.4f} |

## Largest positive disagreements (actual above baseline)

{top5_pos_str}

## Largest negative disagreements (actual below baseline)

{top5_neg_str}

## Profile of actual.csv (WBL/100)

| Statistic | Value |
|---|---|
| Observations | {profile['n_obs']:,} |
| Countries | {profile['n_countries']} |
| Mean | {profile['mean']} |
| Median | {profile['median']} |
| SD | {profile['std']} |
| Skewness | {profile['skewness']} ({skew_label}) |
| Kurtosis | {profile['kurtosis']} |

## References
See methodology_refs.bib.
"""

with open(os.path.join(OUT, "sanity_check_report.md"), "w", encoding="utf-8") as f:
    f.write(report)
print("  Saved -> sanity_check_report.md")

# ── 12. Summary ───────────────────────────────────────────────────────────────
print("\nDone. All outputs in sanity_check/")
for fname in ["baseline.csv","actual.csv","overlap_comparison.csv","coverage_audit.csv",
              "uncertain_country_matches.csv","sanity_check_report.md",
              "comparison_scatter.png","actual_histogram.png"]:
    exists = "OK" if os.path.exists(os.path.join(OUT, fname)) else "MISSING"
    print(f"  [{exists}] {fname}")
