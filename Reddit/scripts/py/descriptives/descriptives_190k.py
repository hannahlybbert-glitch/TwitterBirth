# Author: Hannah Lybbert
# Created: 2026-03-24
# Updated: 2026-03-24
# Purpose: Summary stats on birth posts from the 190k sample

import pandas as pd
from pathlib import Path

ROOT       = Path(__file__).resolve().parents[4]
INPUT_PATH = ROOT / "Reddit/data/intermediate/llm_births/births_22k_sample.csv"

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
df = pd.read_csv(INPUT_PATH)
print(f"Loaded {len(df):,} rows")

# ----------------------------------------------------------------
# days_from_birth (excluding -999)
# ----------------------------------------------------------------
n_999 = (df["days_from_birth"] == -999).sum()
days  = df.loc[df["days_from_birth"] != -999, "days_from_birth"]
print(f"\n--- days_from_birth (excluding -999, n={len(days):,}) ---")
print(f"  Count -999: {n_999:,}")
print(f"  Mean:   {days.mean():.1f}")
print(f"  Median: {days.median():.1f}")
print(f"  Min:    {days.min():.1f}")
print(f"  Max:    {days.max():.1f}")
