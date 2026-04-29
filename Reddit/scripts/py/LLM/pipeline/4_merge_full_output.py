# Author: Hannah Lybbert
# Created: 2026-03-26
# Updated: 2026-04-06
# Purpose: Merge all GPT-4o batch outputs into one final combined CSV (run after scripts 1-3 are complete)

import pandas as pd
from pathlib import Path

ROOT      = Path(__file__).resolve().parents[5]
FULL_DIR  = ROOT / "Reddit/data/LLM/pipeline/full_output"
OUTPUT    = ROOT / "Reddit/data/LLM/birth_detection_2_3M_GPT4o_full.csv"

# ----------------------------------------------------------------
# Load all batch outputs
# ----------------------------------------------------------------
full_files = sorted(FULL_DIR.glob("batch_*_full_results.csv"))
print(f"Found {len(full_files)} full output files to merge:")
for f in full_files:
    print(f"  {f.name}")

if not full_files:
    print("No files found — make sure scripts 1-3 have completed.")
    exit()

dfs = []
for f in full_files:
    df = pd.read_csv(f)
    df["source_batch"] = f.stem.replace("_full_results", "")
    dfs.append(df)
    print(f"  Loaded {f.name}: {len(df):,} rows")

# ----------------------------------------------------------------
# Merge and save
# ----------------------------------------------------------------
combined = pd.concat(dfs, ignore_index=True)

n       = len(combined)
n_flag1 = (combined['birth_flag'] == 1).sum()

print(f"\nMerged: {n:,} total rows from {len(full_files)} batches")
print(f"  birth_flag == 1:   {n_flag1:,}  ({n_flag1/n:.1%} of sample)")
print(f"  birth_flag == 0:   {(combined['birth_flag'] == 0).sum():,}")
print(f"  birth_flag == -99: {(combined['birth_flag'] == -99).sum():,}")

positives  = combined[combined['birth_flag'] == 1]
n_female   = (positives['p_female'] > 50).sum()
n_male     = (positives['p_male']   > 50).sum()

print(f"\nGender breakdown (among birth_flag == 1, n={n_flag1:,}):")
print(f"  p_female > 50: {n_female:,}  ({n_female/n_flag1:.1%} of positives)")
print(f"  p_male   > 50: {n_male:,}  ({n_male/n_flag1:.1%} of positives)")

combined.to_csv(OUTPUT, index=False)
print(f"\nSaved to {OUTPUT}")
