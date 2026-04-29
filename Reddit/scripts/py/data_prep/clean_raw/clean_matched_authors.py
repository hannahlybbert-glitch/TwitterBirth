# Author: Hannah Lybbert
# Created: 2026-04-10
# Updated: 2026-04-10
# Purpose: Validate matched_authors.csv — ensure all treatment authors have a placebo author

import pandas as pd
from pathlib import Path

ROOT   = Path(__file__).resolve().parents[5]
INPUT  = ROOT / "Reddit/raw/matched_authors_jul2023.csv"
OUTPUT = ROOT / "Reddit/data/intermediate/cleaned_raw/matched_authors_clean.csv"

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
df = pd.read_csv(INPUT)
print(f"Loaded {len(df):,} rows")

# ----------------------------------------------------------------
# Drop rows where placebo_author is missing
# ----------------------------------------------------------------
before = len(df)
df = df[df["placebo_author"].notna() & ~df["placebo_author"].str.strip().isin(["", "[deleted]", "[removed]"])]
print(f"  After dropping missing placebo_author: {len(df):,}  (removed {before - len(df):,})")

# ----------------------------------------------------------------
# Warn on duplicate treatment or placebo authors
# ----------------------------------------------------------------
dup_treatment = df["treatment_author"].duplicated().sum()
dup_placebo   = df["placebo_author"].duplicated().sum()
if dup_treatment > 0:
    print(f"  WARNING: {dup_treatment:,} duplicate treatment_authors")
if dup_placebo > 0:
    print(f"  WARNING: {dup_placebo:,} duplicate placebo_authors")

# ----------------------------------------------------------------
# Save
# ----------------------------------------------------------------
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUTPUT, index=False)
print(f"\nDone. Saved {len(df):,} rows to {OUTPUT}")
