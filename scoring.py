import pandas as pd
import numpy as np
import os
import glob


def scoring(group, weights=None, fixed_bounds=None):
    df = group.copy()

    id_cols = ["Economy", "ISO Code", "Region", "Income Group", "Year"]
    indicator_cols = [col for col in df.columns if col not in id_cols]

    # Convert Yes/No → 1/0
    for col in indicator_cols:
        df[col] = df[col].replace({
            "Yes": 1, "No": 0,
            "YES": 1, "NO": 0,
            "True": 1, "False": 0
        })
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Define which variables are "bad"
    negative_vars = [
        "adolescent_fertility",
        "maternal_mortality"
    ]

    # Continuous variables — winsorise at 1/99 percentile before min-max,
    # to match the predictor pipeline (analysis/utils.py:27-41). The other
    # indicator columns in this pipeline are WBL legal binaries for which
    # 1/99 clipping is a no-op; gating by continuous_vars is defensive.
    continuous_vars = [
        "adolescent_fertility",
        "maternal_mortality",
        "lifeexp_female",
        "lifeexp_total",
        "women_parliament_pct",
    ]

    # Scale each column
    for col in indicator_cols:
        if fixed_bounds and col in fixed_bounds:
            # Fixed reference bounds (e.g. UNDP HDI goalposts) — stable across samples
            lo, hi = fixed_bounds[col]
            df[col] = (df[col] - lo) / (hi - lo)
            df[col] = df[col].clip(0, 1)
        else:
            if col in continuous_vars:
                q_lo = df[col].quantile(0.01)
                q_hi = df[col].quantile(0.99)
                df[col] = df[col].clip(lower=q_lo, upper=q_hi)
            # Data-driven min-max
            min_val = df[col].min()
            max_val = df[col].max()
            if pd.notna(min_val) and pd.notna(max_val) and max_val != min_val:
                df[col] = (df[col] - min_val) / (max_val - min_val)

        # Reverse bad variables
        if col in negative_vars:
            df[col] = 1 - df[col]

    # Equal weights if none provided
    if weights is None:
        weights = {col: 1 for col in indicator_cols}

    weight_sum = sum(weights.values())
    if weight_sum == 0:
        raise ValueError(
            "scoring(): sum of weights is 0; cannot compute weighted average. "
            f"Weights passed: {weights}"
        )

    # Weighted average
    df["score"] = sum(df[col] * weights[col] for col in indicator_cols) / weight_sum

    return df[id_cols + ["score"]]


def apply_two_layer_weighting(df, w_dejure: float = 0.5, w_defacto: float = 0.5):
    """Two-layer weighting: de_jure (8 legal groups) and de_facto (2 outcome
    groups), combined with `w_dejure` / `w_defacto` weights (must sum to 1).
    Default 50/50; sensitivity runner can pass other weights.
    """
    if abs((w_dejure + w_defacto) - 1.0) > 1e-9:
        raise ValueError(
            f"Weights must sum to 1 (got {w_dejure}+{w_defacto}={w_dejure+w_defacto})")

    de_jure_cols = [
        "assets",
        "econ_rights",
        "fam_safety",
        "mobility",
        "parenthood",
        "pay",
        "pension",
        "workplace"
    ]

    de_facto_cols = [
        "health",
        "political_rep"
    ]

    # First layer: average groups within each category
    df["de_jure_score"] = df[de_jure_cols].mean(axis=1)
    df["de_facto_score"] = df[de_facto_cols].mean(axis=1)

    # Second layer: combine de jure and de facto with the requested weights
    df["overall_score"] = (
        w_dejure  * df["de_jure_score"] +
        w_defacto * df["de_facto_score"]
    )

    return df


if __name__ == "__main__":
    # load the output files that are sorted into the groups
    assets = pd.read_csv('output/assets_group.csv')
    econ_rights = pd.read_csv('output/economic_rights_group.csv')
    fam_safety = pd.read_csv('output/family_safety_group.csv')
    health = pd.read_csv('output/health_group.csv')
    mobility = pd.read_csv('output/mobility_group.csv')
    parenthood = pd.read_csv('output/parenthood_group.csv')
    pay = pd.read_csv('output/pay_group.csv')
    pension = pd.read_csv('output/pension_group.csv')
    political_rep = pd.read_csv('output/political_representation_group.csv')
    workplace = pd.read_csv('output/workplace_group.csv')

    assets_score = scoring(assets)
    econ_rights_score = scoring(econ_rights)
    fam_safety_score = scoring(fam_safety)
    # All health indicators use data-driven min-max (no fixed bounds)
    health_score = scoring(health)
    mobility_score = scoring(mobility)
    parenthood_score = scoring(parenthood)
    pay_score = scoring(pay)
    pension_score = scoring(pension)
    political_rep_score = scoring(political_rep)
    workplace_score = scoring(workplace)

    # --- Combine all group scores into one overall score ---

    group_scores = [
        ("assets",        assets_score),
        ("econ_rights",   econ_rights_score),
        ("fam_safety",    fam_safety_score),
        ("health",        health_score),
        ("mobility",      mobility_score),
        ("parenthood",    parenthood_score),
        ("pay",           pay_score),
        ("pension",       pension_score),
        ("political_rep", political_rep_score),
        ("workplace",     workplace_score),
    ]

    MIN_GROUPS = 8  # minimum groups with data to receive an overall score

    merge_keys = ["ISO Code", "Year"]

    combined = group_scores[0][1][merge_keys + ["score"]].rename(columns={"score": group_scores[0][0]})
    for name, df in group_scores[1:]:
        combined = combined.merge(
            df[merge_keys + ["score"]].rename(columns={"score": name}),
            on=merge_keys,
            how="outer"
        )

    # Duplicate check and removal
    dupes = combined.duplicated(subset=merge_keys, keep=False)
    if dupes.any():
        print(f"WARNING: {dupes.sum()} duplicate ISO+Year rows found before scoring — keeping first")
        combined = combined.drop_duplicates(subset=merge_keys, keep="first")

    score_cols = [name for name, _ in group_scores]
    combined["n_groups"] = combined[score_cols].notna().sum(axis=1)

    # Apply two-layer weighting (de_jure / de_facto 50/50)
    combined = apply_two_layer_weighting(combined)
    combined.loc[combined["n_groups"] < MIN_GROUPS, "overall_score"] = float("nan")

    overall = combined[merge_keys + ["overall_score"]].dropna(subset=["overall_score"])
    overall = overall.sort_values(merge_keys).reset_index(drop=True)
    overall.to_csv("output/overall_score.csv", index=False)
    print(overall.head(10))
    print(f"\nRows: {len(overall)}, Countries: {overall['ISO Code'].nunique()}, Years: {overall['Year'].nunique()}")

    # Export all group scores + overall to data/ for use in regression analysis
    wbl_groups = combined[merge_keys + score_cols + ["overall_score"]].copy()
    wbl_groups = wbl_groups.rename(columns={"ISO Code": "iso3", "Year": "year"})
    wbl_groups = wbl_groups.dropna(subset=["iso3"])
    wbl_groups.to_csv("data/wbl_group_scores.csv", index=False)
    print(f"\nWBL group scores saved -> data/wbl_group_scores.csv")
    print(f"  Groups: {score_cols}")
    print(f"  Rows: {len(wbl_groups)}, Countries: {wbl_groups['iso3'].nunique()}, Years: {sorted(wbl_groups['year'].unique())}")

    # Export outcome_wbl.csv for regression analysis
    # Get country names from health group (most coverage: 217 countries)
    country_lookup = health[["ISO Code", "Economy"]].drop_duplicates(subset=["ISO Code"]).rename(
        columns={"ISO Code": "iso3", "Economy": "country"}
    )
    outcome = overall.rename(columns={
        "ISO Code": "iso3",
        "Year": "year",
        "overall_score": "wbl_treatment_index"
    })
    outcome = outcome.merge(country_lookup, on="iso3", how="left")
    outcome = outcome[["iso3", "country", "year", "wbl_treatment_index"]]
    outcome = outcome.sort_values(["iso3", "year"]).reset_index(drop=True)
    outcome.to_csv("data/outcome_wbl.csv", index=False)
    print(f"\nOutcome variable saved -> data/outcome_wbl.csv")
    print(f"  Rows: {len(outcome)}, Countries: {outcome['iso3'].nunique()}, Years: {sorted(outcome['year'].unique())}")
