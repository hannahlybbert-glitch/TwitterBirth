# Author: Hannah Lybbert
# Created: 2026-08-27
# Updated: 2026-09-01
# Purpose: Save a three-column file of unique treatment authors, their date_birth,
#          and their post id.

import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]

INPUT  = ROOT / "Reddit/data/final/births_and_posts_FULL.csv"
OUTPUT = ROOT / "Reddit/data/final/treatment_authors.csv"

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
df = pd.read_csv(INPUT, usecols=["id", "author", "date_birth"])
print(f"Loaded {len(df):,} rows, {df['author'].nunique():,} unique authors")

# ----------------------------------------------------------------
# One row per author with their date_birth and post id
# (input is sorted by author, created_utc, so this keeps the earliest post).
# ----------------------------------------------------------------
authors = (
    df.drop_duplicates(subset="author")
      .loc[:, ["author", "date_birth", "id"]]
      .sort_values("author")
      .reset_index(drop=True)
)

authors.to_csv(OUTPUT, index=False)
print(f"Done. Saved {len(authors):,} authors to {OUTPUT}")
