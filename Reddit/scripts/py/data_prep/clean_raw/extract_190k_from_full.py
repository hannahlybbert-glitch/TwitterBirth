# Author: Hannah Lybbert
# Created: 2026-03-26
# Updated: 2026-03-26
# Purpose: Remove 190k sample rows from full cleaned parenting data, saving the complement as a new parquet file

import pandas as pd
from pathlib import Path

ROOT         = Path(__file__).resolve().parents[5]
INPUT_FULL   = ROOT / "Reddit/data/intermediate/cleaned_raw/reddit_parenting_full_cleaned.parquet"
INPUT_190K   = ROOT / "Reddit/data/intermediate/cleaned_raw/reddit_parenting_190k_sample.parquet"
OUTPUT       = ROOT / "Reddit/data/intermediate/cleaned_raw/reddit_parenting_2_3M_sample.parquet"

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
print(f"Loading full cleaned data...")
full = pd.read_parquet(INPUT_FULL)
print(f"  Full dataset:   {len(full):,} rows")

print(f"Loading 190k sample...")
sample_190k = pd.read_parquet(INPUT_190K)
print(f"  190k sample:    {len(sample_190k):,} rows")

# ----------------------------------------------------------------
# Anti-join: remove any row whose id appears in the 190k sample
# ----------------------------------------------------------------
ids_to_remove = set(sample_190k["id"])
complement    = full[~full["id"].isin(ids_to_remove)].reset_index(drop=True)

print(f"\n  Rows removed:   {len(full) - len(complement):,}")
print(f"  Complement:     {len(complement):,} rows")

# Verify no overlap
overlap = complement["id"].isin(ids_to_remove).sum()
print(f"  Overlap check:  {overlap} rows in common (should be 0)")

# Verify union equals full
assert len(complement) + len(sample_190k) == len(full), "Union does not equal full dataset — check for duplicate ids"
print(f"  Union check:    {len(complement):,} + {len(sample_190k):,} = {len(full):,} ✓")

# ----------------------------------------------------------------
# Save
# ----------------------------------------------------------------
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
complement.to_parquet(OUTPUT, index=False)
print(f"\nSaved to {OUTPUT}")
