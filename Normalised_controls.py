import pandas as pd

df = pd.read_csv(r"C:\Users\emyan\mdm3_project3\Controls_raw_dataset.csv")

cols = ["education_index", "Rurality", "Conflict_Scale"]

# Global min-max
global_min = df[cols].min()
global_max = df[cols].max()

# Normalize entire dataset
for col in cols:
    df[col + "_normalized"] = (df[col] - global_min[col]) / (global_max[col] - global_min[col])

# Filter Afghanistan 2013–2016
result = df[(df["country"] == "Afghanistan") & (df["year"].between(2013, 2016))]

print(result)