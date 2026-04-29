# Author: Hannah Lybbert
# Created: 03/06/2026
# Purpose: Filter recovered birth detection results, dropping auto-filled sentinel rows from cancelled batches

import os
import pandas as pd

os.chdir("D:/TwitterBirth")

# --- Paths ---
INPUT_PATH  = "Reddit/data/LLM/birth_detection_large_sample.csv"
OUTPUT_PATH = "Reddit/data/LLM/birth_detection_large_sample_clean.csv"

# --- Sentinel values inserted for rows not processed by the LLM (cancelled batch) ---
SENTINEL_CONFIDENCE = 3
SENTINEL_P_FEMALE   = 4
SENTINEL_P_MALE     = 5

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
df = pd.read_csv(INPUT_PATH, encoding="utf-8", low_memory=False)
print(f"Loaded {len(df):,} rows from {INPUT_PATH}")

# ----------------------------------------------------------------
# Drop rows where all three sentinel values are present
# (these were never passed through the LLM — auto-filled on batch cancellation)
# ----------------------------------------------------------------
sentinel_mask = (
    (df["confidence"] == SENTINEL_CONFIDENCE) &
    (df["p_female"]   == SENTINEL_P_FEMALE)   &
    (df["p_male"]     == SENTINEL_P_MALE)
)

n_dropped = sentinel_mask.sum()
df_clean  = df[~sentinel_mask].copy()

print(f"Dropped {n_dropped:,} sentinel rows (confidence={SENTINEL_CONFIDENCE}, p_female={SENTINEL_P_FEMALE}, p_male={SENTINEL_P_MALE})")
print(f"Remaining rows: {len(df_clean):,}")

# ----------------------------------------------------------------
# Save
# ----------------------------------------------------------------
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
df_clean.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
print(f"\nSaved cleaned data to {OUTPUT_PATH}")

# ----------------------------------------------------------------
# Summary
# ----------------------------------------------------------------
print("\n" + "=" * 50)
print("SUMMARY")
print("=" * 50)
print(f"Total rows processed by LLM: {len(df_clean):,}")
print(f"  - Within 14-day window (1):  {(df_clean['birth_flag'] == 1).sum():,}")
print(f"  - Outside window / none (0): {(df_clean['birth_flag'] == 0).sum():,}")
print(f"  - Uncertain (-99):           {(df_clean['birth_flag'] == -99).sum():,}")
