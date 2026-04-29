# Author: Hannah Lybbert
# Created: 2026-03-25
# Updated: 2026-03-25
# Purpose: TWFE event study regression: post_count ~ sum_k beta_k*(D_k x Treated) + authorFE + calMonthFE
#
# Install dependency: pip install linearmodels

import pandas as pd
from pathlib import Path
from linearmodels.panel import PanelOLS

ROOT       = Path(__file__).resolve().parents[5]
INPUT_PATH = ROOT / "Reddit/data/intermediate/diff_n_diff/author_month_panel.csv"
OUTPUT_DIR = ROOT / "Reddit/data/intermediate/diff_n_diff"
OUTPUT     = OUTPUT_DIR / "event_study_results.csv"

WINDOW_MIN = -18
WINDOW_MAX =  18
REF_MONTH  = -1    # omitted reference period (last pre-birth month)

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
panel = pd.read_csv(INPUT_PATH)
print(f"Loaded panel: {len(panel):,} rows | {panel['author'].nunique():,} authors")

# ----------------------------------------------------------------
# Create interaction dummies: D_k x Treated for each k != REF_MONTH
# Column naming uses 'm' prefix to avoid issues with negative signs
# ----------------------------------------------------------------
event_months = [m for m in range(WINDOW_MIN, WINDOW_MAX + 1) if m != REF_MONTH]

for m in event_months:
    col = f"Dm{m}_x_treat" if m < 0 else f"D{m}_x_treat"
    panel[col] = (
        ((panel["months_from_birth"] == m) & (panel["treated"] == 1))
        .astype(float)
    )

X_cols = [f"Dm{m}_x_treat" if m < 0 else f"D{m}_x_treat" for m in event_months]

# ----------------------------------------------------------------
# Set panel index: (author, cal_month_id)
# ----------------------------------------------------------------
panel = panel.set_index(["author", "cal_month_id"])

y = panel["post_count"]
X = panel[X_cols]

# ----------------------------------------------------------------
# TWFE regression: author FE + calendar month FE
# Standard errors clustered by author
# ----------------------------------------------------------------
print("Running TWFE regression...")
model = PanelOLS(y, X, entity_effects=True, time_effects=True, drop_absorbed=True)
res   = model.fit(cov_type="clustered", cluster_entity=True)

print(res.summary)

# ----------------------------------------------------------------
# Extract coefficients and save
# Map column names back to month numbers
# ----------------------------------------------------------------
col_to_month = {
    (f"Dm{m}_x_treat" if m < 0 else f"D{m}_x_treat"): m
    for m in event_months
}

results = pd.DataFrame({
    "month":  [col_to_month[c] for c in res.params.index],
    "beta":   res.params.values,
    "se":     res.std_errors.values,
    "ci_low": (res.params - 1.96 * res.std_errors).values,
    "ci_hi":  (res.params + 1.96 * res.std_errors).values,
})

# Insert reference month as zero
ref_row = pd.DataFrame({
    "month": [REF_MONTH], "beta": [0.0], "se": [0.0], "ci_low": [0.0], "ci_hi": [0.0]
})
results = pd.concat([results, ref_row]).sort_values("month").reset_index(drop=True)

results.to_csv(OUTPUT, index=False)
print(f"\nResults saved to {OUTPUT}")
