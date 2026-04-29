# Author: Hannah Lybbert
# Created: 2026-04-09
# Updated: 2026-04-09
# Purpose: Build text analysis-ready file: filter sample, drop birth posts, concatenate title + selftext

import pandas as pd
from pathlib import Path

ROOT       = Path(__file__).resolve().parents[5]
INPUT_PATH = ROOT / "Reddit/data/final/births_and_posts_FULL.csv"
OUTPUT_DIR  = ROOT / "Reddit/data/final/text"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH = OUTPUT_DIR / "text_analysis_births_posts.csv"

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
df = pd.read_csv(INPUT_PATH)
print(f"Loaded {len(df):,} rows | {df['author'].nunique():,} unique authors")

# ----------------------------------------------------------------
# Restrict to full_18_pre == 1
# ----------------------------------------------------------------
df = df[df["full_18_pre"] == 1].copy()
print(f"After sample restriction (full_18_pre): {len(df):,} rows | {df['author'].nunique():,} unique authors")

# ----------------------------------------------------------------
# Drop birth posts
# ----------------------------------------------------------------
before = len(df)
df = df[df["birth_post"] != 1].copy()
print(f"Dropped {before - len(df):,} birth posts | {len(df):,} rows remaining")

# ----------------------------------------------------------------
# Ensure id is unique
# ----------------------------------------------------------------
n_dupes = df["id"].duplicated().sum()
if n_dupes > 0:
    print(f"  Warning: {n_dupes:,} duplicate ids found — keeping first occurrence")
    df = df.drop_duplicates(subset="id", keep="first").reset_index(drop=True)
else:
    print(f"  id is unique: no duplicates found")

# ----------------------------------------------------------------
# Create text = title + ". " + selftext
# NaN fields treated as empty string before concatenation
# ----------------------------------------------------------------
title    = df["title"].fillna("").astype(str).str.strip()
selftext = df["selftext"].fillna("").astype(str).str.strip()

df["text"] = title + ". " + selftext
df["text"] = df["text"].str.strip()

# ----------------------------------------------------------------
# Save
# ----------------------------------------------------------------
df.to_csv(OUTPUT_PATH, index=False)
print(f"\nSaved {len(df):,} rows to {OUTPUT_PATH}")

# ----------------------------------------------------------------
# Save 10k random sample
# ----------------------------------------------------------------
RANDOM_SEED = 42
sample_10k = df.sample(n=10_000, random_state=RANDOM_SEED)
output_10k = OUTPUT_DIR / "text_analysis_births_posts_10k.csv"
sample_10k.to_csv(output_10k, index=False)
print(f"Saved 10k random sample to {output_10k}")
