# Author: Hannah Lybbert
# Created: 2026-04-10
# Updated: 2026-04-10
# Purpose: Stack treatment and matched placebo control datasets into a single analysis file

import pandas as pd
from pathlib import Path

ROOT           = Path(__file__).resolve().parents[5]
INPUT_TREAT    = ROOT / "Reddit/data/final/births_and_posts_FULL.csv"
INPUT_PLACEBO  = ROOT / "Reddit/data/intermediate/births_and_posts/matched_placebo_births_posts.csv"
INPUT_MATCHED  = ROOT / "Reddit/data/intermediate/cleaned_raw/matched_authors_clean.csv"
OUTPUT         = ROOT / "Reddit/data/final/treatment_control_births_posts.csv"

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
treat   = pd.read_csv(INPUT_TREAT)
placebo = pd.read_csv(INPUT_PLACEBO)
matched = pd.read_csv(INPUT_MATCHED)

print(f"Treatment rows:  {len(treat):,}  ({treat['author'].nunique():,} authors)")
print(f"Control rows:    {len(placebo):,}  ({placebo['author'].nunique():,} authors)")

# ----------------------------------------------------------------
# Restrict treatment to authors who have a matched placebo pair
# ----------------------------------------------------------------
matched_treatment_authors = set(matched["treatment_author"].dropna())
before = treat["author"].nunique()
treat  = treat[treat["author"].isin(matched_treatment_authors)]
print(f"\n  Treatment authors with a matched placebo: {treat['author'].nunique():,}  (dropped {before - treat['author'].nunique():,} unmatched)")

# ----------------------------------------------------------------
# Check: how many treatment authors (treated==1, birth_post==1)
# appear as treatment_author in the matched placebo (treated==0, birth_post==1)?
# ----------------------------------------------------------------
treat_birth_authors   = set(treat.loc[treat["birth_post"] == 1, "author"])
placebo_treat_authors = set(placebo.loc[placebo["birth_post"] == 1, "treatment_author"].dropna())
matched               = treat_birth_authors & placebo_treat_authors

print(f"\n--- Match coverage check ---")
print(f"  Treatment authors with birth_post==1:                    {len(treat_birth_authors):,}")
print(f"  Unique treatment_authors in matched placebo birth posts:  {len(placebo_treat_authors):,}")
print(f"  Treatment authors matched to a placebo author:            {len(matched):,}  ({len(matched)/len(treat_birth_authors)*100:.1f}%)")
print(f"  Treatment authors WITHOUT a matched placebo:              {len(treat_birth_authors) - len(matched):,}")

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
