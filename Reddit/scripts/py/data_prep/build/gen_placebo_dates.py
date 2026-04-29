# Author: Hannah Lybbert
# Created: 2026-03-25
# Updated: 2026-04-07
# Purpose: Assign placebo birth dates to control group authors using draws from real days_from distribution

import numpy as np
import pandas as pd
from pathlib import Path

ROOT          = Path(__file__).resolve().parents[5]
INPUT_PLACEBO = ROOT / "Reddit/data/intermediate/cleaned_raw/reddit_placebo_cleaned.csv"
INPUT_TREAT   = ROOT / "Reddit/data/final/births_and_posts_FULL.csv"
OUTPUT        = ROOT / "Reddit/data/intermediate/births_and_posts/placebo_births_and_posts.csv"

RANDOM_SEED = 42

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
placebo = pd.read_csv(INPUT_PLACEBO)
treat   = pd.read_csv(INPUT_TREAT)

print(f"Placebo posts loaded:   {len(placebo):,} ({placebo['author'].nunique():,} authors)")
print(f"Treatment posts loaded: {len(treat):,} ({treat['author'].nunique():,} authors)")

# ----------------------------------------------------------------
# Convert created_utc to datetime
# ----------------------------------------------------------------
placebo["created_utc"] = pd.to_datetime(placebo["created_utc"], unit="s")

# ----------------------------------------------------------------
# Get days_from distribution from real birth posts (exclude -999)
# ----------------------------------------------------------------
days_from_dist = treat.loc[
    (treat["birth_post"] == 1) & (treat["days_from"] != -999), "days_from"
].dropna().values

print(f"Drawing days_from from {len(days_from_dist):,} real birth posts (excluding -999)")

# ----------------------------------------------------------------
# For each placebo author:
#   - draw a random date uniformly from the author's observation window
#     (avoids length-biased sampling from picking a random post)
#   - draw a random days_from from the real distribution
#   - compute date_birth = date_birth_post - days_from
# ----------------------------------------------------------------
rng = np.random.default_rng(RANDOM_SEED)

# Cap draw window so date_birth_post is before BIRTH_CUTOFF,
# ensuring date_birth is at least 18 months before end of sample (Dec 2024)
BIRTH_CUTOFF = pd.Timestamp("2023-07-01")

# ----------------------------------------------------------------
# METHOD 1 (old): draw date_birth_post as a random continuous date
# from the author's observation window, then find the nearest real post.
# Issue: the nearest post may be far from the drawn date, skewing
# months_from_birth for the flagged birth post.
# ----------------------------------------------------------------
# records  = []
# skipped  = 0
# for author, group in placebo.groupby("author"):
#     min_date      = group["created_utc"].min()
#     max_date      = group["created_utc"].max()
#     effective_max = min(max_date, BIRTH_CUTOFF)

#     if effective_max <= min_date:
#         skipped += 1
#         continue

#     date_birth_post = min_date + (effective_max - min_date) * rng.random()
#     days_from       = float(rng.choice(days_from_dist))
#     date_birth      = date_birth_post - pd.to_timedelta(days_from, unit="D")
#     records.append({
#         "author":          author,
#         "date_birth_post": date_birth_post,
#         "days_from":       days_from,
#         "date_birth":      date_birth,
#     })

# placebo_dates = pd.DataFrame(records)
# print(f"Placebo birth dates assigned for {len(placebo_dates):,} authors ({skipped:,} skipped — window entirely after cutoff)")

# ----------------------------------------------------------------
# METHOD 2: draw date_birth_post from the author's actual posts
# (filtered to before BIRTH_CUTOFF), so the flagged birth post IS
# the drawn post with no gap.
# ----------------------------------------------------------------
records  = []
skipped  = 0
for author, group in placebo.groupby("author"):
    eligible = group[group["created_utc"] <= BIRTH_CUTOFF]

    if eligible.empty:
        skipped += 1
        continue

    date_birth_post = eligible["created_utc"].iloc[rng.integers(len(eligible))]
    days_from       = float(rng.choice(days_from_dist))
    date_birth      = date_birth_post - pd.to_timedelta(days_from, unit="D")
    records.append({
        "author":          author,
        "date_birth_post": date_birth_post,
        "days_from":       days_from,
        "date_birth":      date_birth,
    })

placebo_dates = pd.DataFrame(records)
print(f"Placebo birth dates assigned for {len(placebo_dates):,} authors ({skipped:,} skipped — no posts before cutoff)")

# ----------------------------------------------------------------
# Merge placebo birth dates onto all posts
# Drop authors with no valid birth date (entire window after cutoff)
# ----------------------------------------------------------------
placebo = placebo.merge(
    placebo_dates[["author", "date_birth_post", "days_from", "date_birth"]],
    on="author", how="inner"
)
print(f"After dropping authors with no valid birth window: {placebo['author'].nunique():,} authors, {len(placebo):,} posts")

# ----------------------------------------------------------------
# birth_post flag: exact match on date_birth_post (Method 2 — drawn
# directly from actual posts, so the timestamp matches exactly)
# ----------------------------------------------------------------
placebo["birth_post"] = (placebo["created_utc"] == placebo["date_birth_post"]).astype(int)

# ----------------------------------------------------------------
# Time-relative-to-birth variables
# ----------------------------------------------------------------
placebo["days_from_birth"]   = (placebo["created_utc"] - placebo["date_birth"]).dt.days
placebo["weeks_from_birth"]  = placebo["days_from_birth"] // 7
placebo["months_from_birth"] = placebo["days_from_birth"] // 30

# ----------------------------------------------------------------
# Post indicator: 1 if post is on or after placebo birth, 0 if before
# ----------------------------------------------------------------
placebo["post"] = (placebo["days_from_birth"] >= 0).astype(int)

# ----------------------------------------------------------------
# Sample restriction flags
# ----------------------------------------------------------------
author_min = placebo.groupby("author")["months_from_birth"].min()
author_max = placebo.groupby("author")["months_from_birth"].max()
placebo["full_18_pre"]  = placebo["author"].map(author_min <= -18).astype(int)
placebo["one_year_pre"] = placebo["author"].map(author_min <= -12).astype(int)
placebo["full_18_post"] = placebo["author"].map(author_max >= 18).astype(int)

# ----------------------------------------------------------------
# treated flag
# ----------------------------------------------------------------
placebo["treated"] = 0

# ----------------------------------------------------------------
# Sort and save
# ----------------------------------------------------------------
placebo = placebo.sort_values(["author", "created_utc"]).reset_index(drop=True)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
placebo.to_csv(OUTPUT, index=False)

tf = treat.groupby("author")[["full_18_pre", "posted_after_birth", "one_year_pre"]].first()
print(f"\n--- Treatment (births_and_posts_FULL) ---")
print(f"  Unique authors:                                  {treat['author'].nunique():,}")
print(f"  Authors full_18_pre:                             {tf['full_18_pre'].sum():,}")
print(f"  Authors posted_after_birth:                      {tf['posted_after_birth'].sum():,}")
print(f"  Authors full_18_pre & posted_after_birth:        {(tf['full_18_pre'] & tf['posted_after_birth']).sum():,}")
print(f"  Authors one_year_pre:                            {tf['one_year_pre'].sum():,}")

af = placebo.groupby("author")[["full_18_pre", "full_18_post", "one_year_pre"]].first()
print(f"\n--- Placebo (done, saved to {OUTPUT}) ---")
print(f"  Unique authors:                {placebo['author'].nunique():,}")
print(f"  Post-birth posts (post == 1):  {(placebo['post'] == 1).sum():,}")
print(f"  Pre-birth posts  (post == 0):  {(placebo['post'] == 0).sum():,}")
print(f"  Authors full_18_pre:           {af['full_18_pre'].sum():,}")
print(f"  Authors full_18_post:          {af['full_18_post'].sum():,}")
print(f"  Authors one_year_pre:          {af['one_year_pre'].sum():,}")
