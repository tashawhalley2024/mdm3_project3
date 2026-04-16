"""Verification Checkpoints 4 and 5 — pipeline output sanity + GRI unchanged.

Run AFTER `python analysis/run_analysis.py` has regenerated results/results.csv.
"""
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

proto = pd.read_csv(os.path.join(ROOT, "results", "rebuild_comparison.csv"))
new = pd.read_csv(os.path.join(ROOT, "results", "results.csv"))
old = pd.read_csv(os.path.join(ROOT, "results", "results_pre_rebuild_backup.csv"))

print("=" * 72)
print("CHECKPOINT 4 — Pipeline output sanity checks")
print("=" * 72)

# CHECK A: T1 2014 composite coefficient matches prototype within tolerance
proto_t1 = proto[(proto["tier"] == "T1_2014_with_gdp") &
                 (proto["predictor"] == "secularism_clean_norm")]
# In the pipeline, T1 rows may be tagged "T1_with_gdp" with a year column
cand = new[
    (new["predictor"] == "composite_secularism_norm")
    & (new["tier"].astype(str).str.contains("T1"))
]
t1_2014 = cand[cand["year"].astype(str) == "2014"]
if len(t1_2014) > 0 and len(proto_t1) > 0:
    proto_beta = float(proto_t1["coef"].iloc[0])
    new_beta = float(t1_2014["coef"].iloc[0])
    diff = abs(proto_beta - new_beta)
    print(f"CHECK A: T1 2014 composite | proto={proto_beta:.4f} "
          f"pipeline={new_beta:.4f} diff={diff:.6f}")
    assert diff < 0.01, \
        f"T1 coefficient mismatch: proto={proto_beta}, pipeline={new_beta}"
    print("         PASS — matches prototype within 0.01")
else:
    print(f"CHECK A: Could not compare — proto rows {len(proto_t1)}, "
          f"pipeline rows {len(t1_2014)} (cand {len(cand)})")
    print(cand[["tier", "year", "predictor", "coef", "pval", "n"]].to_string(index=False))

# CHECK B: All 6 GRI items still present in decomposition
gri_items = [
    "gri_apostasy_norm", "gri_blasphemy_norm", "gri_state_religion_norm",
    "gri_religious_law_norm", "gri_religious_courts_norm", "gri_gov_favour_norm",
]
print("\nCHECK B: GRI decomposition items present")
missing = []
for item in gri_items:
    rows = new[new["predictor"] == item]
    status = f"{len(rows)} rows"
    if len(rows) == 0:
        missing.append(item)
        status = "MISSING"
    print(f"  {item}: {status}")
assert not missing, f"Missing GRI items: {missing}"
print("         PASS — all 6 GRI items present")

# CHECK C: Composite T1 significant at 5%
comp_t1 = new[
    (new["tier"].astype(str).str.contains("T1.*with_gdp", regex=True))
    & (new["predictor"] == "composite_secularism_norm")
]
print("\nCHECK C: Composite T1 significance")
for _, row in comp_t1.iterrows():
    p = float(row["pval"])
    year = row.get("year", "?")
    beta = float(row["coef"])
    print(f"  year={year}: beta={beta:+.4f}, p={p:.4f}")
    assert p < 0.05, f"Composite T1 not significant: p={p}"
print("         PASS — composite cross-section significant at 5%")

# CHECK D: T2 within is wrong-signed or null
comp_t2 = new[
    (new["tier"] == "T2_with_gdp")
    & (new["predictor"] == "composite_secularism_norm")
]
print("\nCHECK D: Composite T2 within-country")
if len(comp_t2) > 0:
    beta = float(comp_t2["coef"].iloc[0])
    p = float(comp_t2["pval"].iloc[0])
    print(f"  T2_with_gdp composite: beta={beta:+.4f}, p={p:.4f}")
    if beta > 0:
        print("         PASS — wrong-signed (null story preserved)")
    elif p > 0.05:
        print("         PASS — non-significant (null story preserved)")
    else:
        print("         WARNING — negative and significant, unexpected")

# CHECK F: Composite sample sizes
print("\nCHECK F: Composite sample sizes")
comp_rows = new[new["predictor"] == "composite_secularism_norm"]
for _, row in comp_rows.head(12).iterrows():
    tier = row["tier"]
    year = row.get("year", "?")
    n = row.get("n", "?")
    print(f"  {tier} (year={year}): N={n}")

print()
print("=" * 72)
print("CHECKPOINT 5 — GRI decomposition coefficients unchanged")
print("=" * 72)

# Compare old vs new: all six GRI items, all tiers (T1, T2, T4)
tiers_to_check = ["T1_no_gdp", "T1_with_gdp", "T2_no_gdp", "T2_with_gdp",
                  "T4_mundlak_re", "T4_mundlak_cre"]
mismatches = []
matches = 0
for item in gri_items:
    for tier in tiers_to_check:
        old_rows = old[(old["tier"] == tier) & (old["predictor"] == item)]
        new_rows = new[(new["tier"] == tier) & (new["predictor"] == item)]
        if len(old_rows) == 0 and len(new_rows) == 0:
            continue
        if len(old_rows) != len(new_rows):
            mismatches.append(
                f"{item} / {tier}: row count old={len(old_rows)} new={len(new_rows)}")
            continue
        # Align by (year if present) to handle T1 2014/2020
        if "year" in old_rows.columns and "year" in new_rows.columns:
            merged_ = pd.merge(
                old_rows[["year", "coef"]].rename(columns={"coef": "old_coef"}),
                new_rows[["year", "coef"]].rename(columns={"coef": "new_coef"}),
                on="year", how="outer",
            )
            for _, r in merged_.iterrows():
                oc = r["old_coef"]
                nc = r["new_coef"]
                if pd.isna(oc) and pd.isna(nc):
                    continue
                if pd.isna(oc) or pd.isna(nc) or abs(oc - nc) > 1e-6:
                    mismatches.append(
                        f"{item} / {tier} / year={r['year']}: "
                        f"old={oc}, new={nc}")
                else:
                    matches += 1
        else:
            oc = float(old_rows["coef"].iloc[0])
            nc = float(new_rows["coef"].iloc[0])
            if abs(oc - nc) > 1e-6:
                mismatches.append(f"{item} / {tier}: old={oc}, new={nc}")
            else:
                matches += 1

print(f"\nMatches: {matches}  Mismatches: {len(mismatches)}")
if mismatches:
    print("\nMISMATCHES:")
    for m in mismatches[:40]:
        print(f"  {m}")
    if len(mismatches) > 40:
        print(f"  ... {len(mismatches) - 40} more")
    print("\nFAIL — GRI decomposition coefficients changed. "
          "Investigate before committing.")
    sys.exit(1)
else:
    print("PASS — all GRI decomposition coefficients identical (< 1e-6).")

# CHECK E: PCA loading count via analysis.log
print("\nCHECK E: PCA loadings line in analysis.log")
log_path = os.path.join(ROOT, "results", "analysis.log")
if os.path.exists(log_path):
    with open(log_path, "r", encoding="utf-8") as f:
        text = f.read()
    if "eleven" in text.lower() or "11-col" in text or "11 inputs" in text:
        print("         WARNING — log still references 11 inputs somewhere")
    else:
        print("         OK — no stale '11 inputs' references")
    # Find first PCA loadings block
    idx = text.find("[build_secularism_composite] PCA")
    if idx != -1:
        snippet = text[idx:idx + 700]
        print("         First PCA loadings block:")
        for line in snippet.splitlines()[:12]:
            print(f"           {line}")

print()
print("=" * 72)
print("ALL PIPELINE VERIFICATION CHECKS COMPLETE")
print("=" * 72)
