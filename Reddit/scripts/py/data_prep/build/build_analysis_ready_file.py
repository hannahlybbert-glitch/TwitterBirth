# Author: Hannah Lybbert
# Created: 2026-03-20
# Updated: 2026-04-14
# Purpose: Build analysis-ready file with time-relative-to-birth variables for Reddit post history

import pandas as pd
from pathlib import Path

ROOT        = Path(__file__).resolve().parents[5]


INPUT_BIRTHS_POSTS = ROOT / "Reddit/data/intermediate/births_and_posts/merged_births_and_posts_FULL.csv"
OUTPUT             = ROOT / "Reddit/data/final/births_and_posts_FULL.csv"

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
# date_birth = created_utc of birth post - days_from
# (days_from > 0: post written after birth; < 0: before birth)
# ----------------------------------------------------------------
birth_posts = df[df["birth_post"] == 1][["author", "created_utc", "days_from"]].copy()
birth_posts["date_birth"]      = birth_posts["created_utc"] - pd.to_timedelta(birth_posts["days_from"], unit="D")
birth_posts["date_birth_post"] = birth_posts["created_utc"]
df = df.merge(birth_posts[["author", "date_birth", "date_birth_post"]], on="author", how="left")

# ----------------------------------------------------------------
# Drop authors whose estimated birth date is after June 2024
# (post-cutoff births have incomplete post-birth histories)
# ----------------------------------------------------------------
before_authors = df["author"].nunique()
before_rows    = len(df)
df = df[df["date_birth"] <= "2023-06-30"]
n_after_date_drop = df["author"].nunique()
dropped_authors   = before_authors - n_after_date_drop
print(f"  Dropped {dropped_authors:,} authors with date_birth after June 2023")
print(f"  Remaining: {n_after_date_drop:,} unique authors ({len(df):,} rows, down from {before_rows:,})")

# ----------------------------------------------------------------
# Time-relative-to-birth variables
# ----------------------------------------------------------------
df["days_from_birth"]   = (df["created_utc"] - df["date_birth"]).dt.days
df["weeks_from_birth"]  = df["days_from_birth"] // 7
df["months_from_birth"] = df["days_from_birth"] // 30

# ----------------------------------------------------------------
# Drop authors in the 99th percentile of lifetime posts (±18 months)
# ----------------------------------------------------------------
lifetime         = (
    df[df["months_from_birth"].between(-18, 18)]
    .groupby("author")
    .size()
    .rename("lifetime_posts")
)
p99_threshold    = lifetime.quantile(0.99)
outlier_authors  = lifetime[lifetime > p99_threshold].index
df               = df[~df["author"].isin(outlier_authors)]
n_after_p99_drop = df["author"].nunique()
print(f"  Dropped {n_after_date_drop - n_after_p99_drop:,} authors above p99 lifetime posts (>{p99_threshold:.0f} posts in ±18 months)")
print(f"  Remaining: {n_after_p99_drop:,} unique authors")

# ----------------------------------------------------------------
# Post indicator: 1 if post is on or after birth, 0 if before
# ----------------------------------------------------------------
df["post"] = (df["days_from_birth"] >= 0).astype(int)

# ----------------------------------------------------------------
# full_18_pre:  1 if author has at least 18 months of pre-birth data
# one_year_pre: 1 if author has at least 12 months of pre-birth data
# full_18_post: 1 if author has at least 18 months of post-birth data
# ----------------------------------------------------------------
author_min = df.groupby("author")["months_from_birth"].min()
author_max = df.groupby("author")["months_from_birth"].max()
df["full_18_pre"]  = df["author"].map(author_min <= -18).astype(int)
df["one_year_pre"] = df["author"].map(author_min <= -12).astype(int)
df["full_18_post"] = df["author"].map(author_max >= 18).astype(int)

# ----------------------------------------------------------------
# female: author-level gender flag derived from birth post
# 1 = likely female (p_female > 50), 0 = likely male (p_male > 50), -99 = ambiguous
# ----------------------------------------------------------------
birth_gender = df[df["birth_post"] == 1][["author", "p_female", "p_male"]].copy()
birth_gender["female"] = -99
birth_gender.loc[birth_gender["p_female"] > 50, "female"] = 1
birth_gender.loc[birth_gender["p_male"]   > 50, "female"] = 0
df = df.merge(birth_gender[["author", "female"]], on="author", how="left")

# ----------------------------------------------------------------
# treated flag
# ----------------------------------------------------------------
df["treated"] = 1

# ----------------------------------------------------------------
# Sort and save
# ----------------------------------------------------------------
df = df.sort_values(["author", "created_utc"]).reset_index(drop=True)

df.to_csv(OUTPUT, index=False)

authors       = df.groupby("author")["female"].first()
author_flags  = df.groupby("author")[["full_18_pre", "full_18_post", "one_year_pre"]].first()
print(f"\nDone. Saved {len(df):,} rows to {OUTPUT}")
print(f"  Post-birth posts  (post == 1): {(df['post'] == 1).sum():,}")
print(f"  Pre-birth posts   (post == 0): {(df['post'] == 0).sum():,}")
print(f"  Authors full_18_pre:           {author_flags['full_18_pre'].sum():,}")
print(f"  Authors full_18_post:          {author_flags['full_18_post'].sum():,}")
print(f"  Authors one_year_pre:          {author_flags['one_year_pre'].sum():,}")
print(f"  Female authors    (female == 1):   {(authors == 1).sum():,}")
print(f"  Male authors      (female == 0):   {(authors == 0).sum():,}")
print(f"  Ambiguous authors (female == -99): {(authors == -99).sum():,}")

n_full18 = int(author_flags["full_18_pre"].sum())
print(f"\n==================================================")
print(f"SAMPLE FUNNEL")
print(f"==================================================")
print(f"  Original (merged_births_and_posts_FULL):    {before_authors:>7,}")
print(f"  After dropping births after June 2023:      {n_after_date_drop:>7,}  (-{before_authors - n_after_date_drop:,})")
print(f"  After dropping p99 lifetime posters:        {n_after_p99_drop:>7,}  (-{n_after_date_drop - n_after_p99_drop:,})")
print(f"  After full_18_pre == 1:                     {n_full18:>7,}  (-{n_after_p99_drop - n_full18:,})")
print(f"=="*25)



