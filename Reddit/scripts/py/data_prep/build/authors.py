# Author: Hannah Lybbert
# Created: 2026-08-27
# Updated: 2026-08-27
# Purpose: Save a two-column file of unique treatment authors and their date_birth

import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]

INPUT  = ROOT / "Reddit/data/final/births_and_posts_FULL.csv"
OUTPUT = ROOT / "Reddit/data/final/treatment_authors.csv"

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
df = pd.read_csv(INPUT, usecols=["author", "date_birth"])
print(f"Loaded {len(df):,} rows, {df['author'].nunique():,} unique authors")

# ----------------------------------------------------------------
# One row per author with their date_birth
# ----------------------------------------------------------------
authors = (
    df.drop_duplicates(subset="author")
      .sort_values("author")
      .reset_index(drop=True)
)

authors.to_csv(OUTPUT, index=False)
print(f"Done. Saved {len(authors):,} authors to {OUTPUT}")
