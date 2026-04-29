# Author: Hannah Lybbert
# Created: 2026-03-25
# Updated: 2026-04-07
# Purpose: Stack treatment and placebo control datasets into a single analysis file

import pandas as pd
from pathlib import Path

ROOT         = Path(__file__).resolve().parents[5]
INPUT_TREAT  = ROOT / "Reddit/data/final/births_and_posts_FULL.csv"
INPUT_PLACEBO = ROOT / "Reddit/data/intermediate/births_and_posts/placebo_births_and_posts.csv"
OUTPUT       = ROOT / "Reddit/data/final/treatment_control_births_posts.csv"

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
treat   = pd.read_csv(INPUT_TREAT)
placebo = pd.read_csv(INPUT_PLACEBO)

print(f"Treatment rows:  {len(treat):,}  ({treat['author'].nunique():,} authors)")
print(f"Control rows:    {len(placebo):,}  ({placebo['author'].nunique():,} authors)")

# ----------------------------------------------------------------
# Stack
# ----------------------------------------------------------------
combined = pd.concat([treat, placebo], ignore_index=True)
combined = combined.sort_values(["treated", "author", "created_utc"]).reset_index(drop=True)

# ----------------------------------------------------------------
# Strip newlines from string columns to prevent CSV import issues
# ----------------------------------------------------------------
str_cols = combined.select_dtypes(include="object").columns
for col in str_cols:
    combined[col] = combined[col].apply(lambda x: x.replace("\n", " ").replace("\r", " ") if isinstance(x, str) else x)

# ----------------------------------------------------------------
# Save
# ----------------------------------------------------------------
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
combined.to_csv(OUTPUT, index=False)

print(f"\nDone. Saved {len(combined):,} rows to {OUTPUT}")
print(f"  Treated   (treated == 1): {(combined['treated'] == 1).sum():,} rows, {treat['author'].nunique():,} authors")
print(f"  Control   (treated == 0): {(combined['treated'] == 0).sum():,} rows, {placebo['author'].nunique():,} authors")
