# Author: Hannah Lybbert
# Created: 2026-03-20
# Updated: 2026-03-20
# Purpose: Build analysis-ready file with time-relative-to-birth variables for Reddit post history

import pandas as pd
from pathlib import Path

ROOT        = Path(__file__).resolve().parents[5]


INPUT_BIRTHS_POSTS = ROOT / "Reddit/data/intermediate/births_and_posts/merged_30k_births_and_posts.csv"
OUTPUT             = ROOT / "Reddit/data/final/reddit_30k_births_and_posts.csv"

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
df = pd.read_csv(INPUT_BIRTHS_POSTS)
print(f"Loaded {len(df):,} rows, {df['author'].nunique():,} unique authors")

# ----------------------------------------------------------------
# Convert created_utc from Unix timestamp to datetime
# ----------------------------------------------------------------
df["created_utc"] = pd.to_datetime(df["created_utc"], unit="s")

# ----------------------------------------------------------------
# Compute birth date per author
# birth_date = created_utc of birth post - days_from_birth
# (days_from_birth > 0: post written after birth; < 0: before birth)
# ----------------------------------------------------------------
birth_posts = df[df["birth_post"] == 1][["author", "created_utc", "days_from_birth"]].copy()
birth_posts["birth_date"] = (
    birth_posts["created_utc"] - pd.to_timedelta(birth_posts["days_from_birth"], unit="D")
)
df = df.merge(birth_posts[["author", "birth_date"]], on="author", how="left")

# ----------------------------------------------------------------
# Time-relative-to-birth variables
# ----------------------------------------------------------------
df["days_from_birth"]   = (df["created_utc"] - df["birth_date"]).dt.days
df["weeks_from_birth"]  = df["days_from_birth"] // 7
df["months_from_birth"] = df["days_from_birth"] // 30

# ----------------------------------------------------------------
# Post indicator: 1 if post is on or after birth, 0 if before
# ----------------------------------------------------------------
df["post"] = (df["days_from_birth"] >= 0).astype(int)

# ----------------------------------------------------------------
# full_3_years: 1 if author has at least 18 months of pre-birth data
# one_year_pre: 1 if author has at least 12 months of pre-birth data
# ----------------------------------------------------------------
author_min = df.groupby("author")["months_from_birth"].min()
df["full_3_years"] = df["author"].map(author_min <= -18).astype(int)
df["one_year_pre"] = df["author"].map(author_min <= -12).astype(int)

# ----------------------------------------------------------------
# Drop working column and save
# ----------------------------------------------------------------
df = df.drop(columns=["birth_date"])
df = df.sort_values(["author", "created_utc"]).reset_index(drop=True)

df.to_csv(OUTPUT, index=False)

print(f"\nDone. Saved {len(df):,} rows to {OUTPUT}")
print(f"  Post-birth posts  (post == 1): {(df['post'] == 1).sum():,}")
print(f"  Pre-birth posts   (post == 0): {(df['post'] == 0).sum():,}")