import pandas as pd
import numpy as np
import os
import glob

#load the output files that are sorted into the groups

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


id_cols = ['Economy', 'ISO Code', 'Region', 'Income Group', 'Year']

#now all the data is loaded in ill calculate the scores for each indicator in each group and then average them
#output will be a csv file with scores for each group
#input will be a list of weights, as of now the weighting will be equal but i want the option to 
#input weights later on

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

    # Scale each column
    for col in indicator_cols:
        if fixed_bounds and col in fixed_bounds:
            # Fixed reference bounds (e.g. UNDP HDI goalposts) — stable across samples
            lo, hi = fixed_bounds[col]
            df[col] = (df[col] - lo) / (hi - lo)
            df[col] = df[col].clip(0, 1)
        else:
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

    # Weighted average
    df["score"] = sum(df[col] * weights[col] for col in indicator_cols) / weight_sum

    return df[id_cols + ["score"]]














	
assets_score = scoring(assets)
econ_rights_score = scoring(econ_rights)
fam_safety_score = scoring(fam_safety)
# Life expectancy scaled using UNDP HDI fixed goalposts (min=20, max=85)
health_fixed_bounds = {
    "lifeexp_female": (20, 85),
    "lifeexp_total":  (20, 85),
}
health_score = scoring(health, fixed_bounds=health_fixed_bounds)
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

merge_keys = ["Economy", "ISO Code", "Year"]

combined = group_scores[0][1][merge_keys + ["score"]].rename(columns={"score": group_scores[0][0]})
for name, df in group_scores[1:]:
    combined = combined.merge(
        df[merge_keys + ["score"]].rename(columns={"score": name}),
        on=merge_keys,
        how="outer"
    )

score_cols = [name for name, _ in group_scores]
combined["overall_score"] = combined[score_cols].mean(axis=1)

overall = combined[merge_keys + ["overall_score"]].dropna(subset=["overall_score"])
overall = overall.sort_values(["Economy", "Year"]).reset_index(drop=True)
overall.to_csv("output/overall_score.csv", index=False)
print(overall.head(10))
print(f"\nRows: {len(overall)}, Countries: {overall['Economy'].nunique()}, Years: {overall['Year'].nunique()}")