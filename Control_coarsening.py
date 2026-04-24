import pandas as pd
import numpy as np

# Load data
df = pd.read_csv("Controls_raw_dataset.csv")


# --------------------
# 1. Coarsening rules
# --------------------

def cut_with_missing(series, bins, labels=None, right=False, include_lowest=True, missing_label="Missing"):
    """
    Turn missing values into a category.
    """
    out = pd.cut(
        series,
        bins=bins,
        labels=labels,
        right=right,
        include_lowest=include_lowest
    ).astype("object")
    out[series.isna()] = missing_label
    return out

# V-Dem corruption and liberal democracy
df["cem_v2x_corr"] = cut_with_missing(
    df["v2x_corr"],
    bins=[0, 0.2, 0.4, 0.6, 0.8, 1.000001],
    labels=["0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0"],
    right=False
)

df["cem_v2x_libdem"] = cut_with_missing(
    df["v2x_libdem"],
    bins=[0, 0.2, 0.4, 0.6, 0.8, 1.000001],
    labels=["0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0"],
    right=False
)

# Education index
df["cem_education_index"] = cut_with_missing(
    df["education_index"],
    bins=[0, 5, 8, 11, 20],
    labels=["<5", "5-8", "8-11", "11+"],
    right=False
)

# Rurality
df["cem_rurality"] = cut_with_missing(
    df["Rurality"],
    bins=[0, 20, 40, 60, 80, 100.000001],
    labels=["0-20", "20-40", "40-60", "60-80", "80-100"],
    right=False
)

# Conflict scale
df["cem_conflict_scale"] = np.select(
    [
        df["Conflict_Scale"].isna(),
        df["Conflict_Scale"] == 0,
        (df["Conflict_Scale"] > 0) & (df["Conflict_Scale"] <= 25),
        (df["Conflict_Scale"] > 25) & (df["Conflict_Scale"] <= 50),
        (df["Conflict_Scale"] > 50) & (df["Conflict_Scale"] <= 75),
        (df["Conflict_Scale"] > 75)
    ],
    [
        "Missing",
        "0",
        "0-25",
        "25-50",
        "50-75",
        "75-100"
    ],
    default="Missing"
)

# Range of years to keep tie periods somewhat aligned
df["cem_period"] = pd.cut(
    df["year"],
    bins=[2007, 2012, 2017, 2023],
    labels=["2007-2011", "2012-2016", "2017-2022"],
    right=False
)

controls = ["v2x_corr", "v2x_libdem", "education_index", "Rurality", "Conflict_Scale"]

df = df[df[controls].notna().sum(axis=1) >= 3]

# --------------------------
# 2. Build a CEM stratum id
# --------------------------
cem_vars = [
    "cem_v2x_corr",
    "cem_v2x_libdem",
    "cem_education_index",
    "cem_rurality",
    "cem_conflict_scale",
    "cem_period"
]

df["cem_stratum"] = df[cem_vars].astype(str).agg("|".join, axis=1)

# -------------------------
# 3. Ckeck stratum sizes
# -------------------------
stratum_sizes = (
    df.groupby("cem_stratum")
      .size()
      .reset_index(name="n")
      .sort_values("n", ascending=False)
)

print(stratum_sizes.head(20))
print("\nNumber of strata:", stratum_sizes.shape[0])

# Save coarsened dataset
df.to_csv("Controls_cem_ready.csv", index=False)