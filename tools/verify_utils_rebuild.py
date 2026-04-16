"""Verification Checkpoint 1 — see writing/INTEGRATION_INSTRUCTIONS.md."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "analysis"))

import pandas as pd  # noqa: E402

from utils import (  # noqa: E402
    COMPOSITE_INSTITUTIONAL_COLS,
    COMPOSITE_BEHAVIOURAL_COLS,
    build_secularism_composite,
    _prepare_composite_inputs,
)

# Check 1: COMPOSITE_INSTITUTIONAL_COLS has exactly 3 items
assert len(COMPOSITE_INSTITUTIONAL_COLS) == 3, \
    f"Expected 3 institutional cols, got {len(COMPOSITE_INSTITUTIONAL_COLS)}"
assert "gri_apostasy_norm" not in COMPOSITE_INSTITUTIONAL_COLS
assert "gri_blasphemy_norm" not in COMPOSITE_INSTITUTIONAL_COLS
assert "gri_gov_favour_norm" not in COMPOSITE_INSTITUTIONAL_COLS
print("CHECK 1 PASS: COMPOSITE_INSTITUTIONAL_COLS has 3 items")

# Check 2: COMPOSITE_ATTITUDINAL_COLS removed
try:
    from utils import COMPOSITE_ATTITUDINAL_COLS  # noqa: F401
    raise AssertionError("COMPOSITE_ATTITUDINAL_COLS should be removed")
except ImportError:
    print("CHECK 2 PASS: COMPOSITE_ATTITUDINAL_COLS removed")

# Check 3: COMPOSITE_BEHAVIOURAL_COLS unchanged
assert len(COMPOSITE_BEHAVIOURAL_COLS) == 4
print("CHECK 3 PASS: COMPOSITE_BEHAVIOURAL_COLS has 4 items")

# Check 4: Build composite on real data
pred = pd.read_csv(os.path.join(ROOT, "data", "predictors.csv"))
women = pd.read_csv(os.path.join(ROOT, "data", "outcome_wbl.csv"))
df = pred.merge(women, on=["iso3", "year"], how="inner")
df_out = build_secularism_composite(df)

assert "composite_secularism_norm" in df_out.columns
n_obs = df_out["composite_secularism_norm"].notna().sum()
print(f"CHECK 4 PASS: composite built, {n_obs} non-null obs")

# Check 5: _prepare_composite_inputs returns 7 columns
prepared = _prepare_composite_inputs(df)
assert prepared.shape[1] == 7, \
    f"Expected 7 prepared cols, got {prepared.shape[1]}: {list(prepared.columns)}"
assert "v2clrelig_norm_flipped" not in prepared.columns
print(f"CHECK 5 PASS: prepared has 7 cols: {list(prepared.columns)}")

# Check 6: Composite correlates positively with gri_state_religion_norm
corr = df_out["composite_secularism_norm"].corr(df_out["gri_state_religion_norm"])
assert corr > 0, f"Sign alignment failed: corr = {corr}"
print(f"CHECK 6 PASS: composite positively correlated with state_religion (r={corr:.3f})")

# Check 7: Values in [0, 1]
vals = df_out["composite_secularism_norm"].dropna()
assert vals.min() >= 0 and vals.max() <= 1, \
    f"Values out of [0,1]: min={vals.min()}, max={vals.max()}"
print(f"CHECK 7 PASS: values in [0,1], range [{vals.min():.3f}, {vals.max():.3f}]")

print("\n=== ALL UTILS.PY CHECKS PASSED ===")
