# Author: Hannah Lybbert
# Created: 2026-03-19
# Updated: 2026-03-25
# Purpose: Merge birth posts with all posts by birth authors; assign birth_post flag

import pandas as pd
from pathlib import Path

# Paths relative to project root (D:/TwitterBirth)
ROOT         = Path(__file__).resolve().parents[5]
INPUT_BIRTHS = ROOT / "Reddit/data/intermediate/llm_births/births_22k_sample.csv"
INPUT_POSTS  = ROOT / "Reddit/data/intermediate/cleaned_raw/reddit_22k_post_history_cleaned.csv"
OUTPUT       = ROOT / "Reddit/data/intermediate/births_and_posts/merged_22k_births_and_posts.csv"

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
births = pd.read_csv(INPUT_BIRTHS)
posts  = pd.read_csv(INPUT_POSTS)

print(f"Birth posts loaded:       {len(births):,}")
print(f"Cleaned posts loaded:     {len(posts):,}")

# ----------------------------------------------------------------
# Filter to shared authors (appear in both files)
# ----------------------------------------------------------------
birth_authors = set(births["author"].dropna().unique())
post_authors  = set(posts["author"].dropna().unique())
shared_authors = birth_authors & post_authors

births_filtered = births[births["author"].isin(shared_authors)].copy()
posts_filtered  = posts[posts["author"].isin(shared_authors)].copy()

print(f"Shared authors:           {len(shared_authors):,}")
print(f"Births for shared authors:{len(births_filtered):,}")
print(f"Posts by shared authors:  {len(posts_filtered):,}")

# ----------------------------------------------------------------
# Assign birth_post flag to post history rows
# Only flag ids matching a birth with birth_post == 1 (latest birth per author)
# ----------------------------------------------------------------
flagged_ids = set(births_filtered[births_filtered["birth_post"] == 1]["id"])
posts_filtered["birth_post"] = posts_filtered["id"].isin(flagged_ids).astype(int)

# ----------------------------------------------------------------
# Merge birth metadata onto matching post history rows
# ----------------------------------------------------------------
birth_meta = births_filtered[["id", "days_from", "confidence", "p_female", "p_male"]]
posts_filtered = posts_filtered.merge(birth_meta, on="id", how="left")

# ----------------------------------------------------------------
# Append births not found in post history
# ----------------------------------------------------------------
unmatched_births = births_filtered[~births_filtered["id"].isin(posts_filtered["id"])].copy()
print(f"Birth posts not in post history: {len(unmatched_births):,}  ({unmatched_births['author'].nunique():,} authors)")

# ----------------------------------------------------------------
# Column order and concat
# ----------------------------------------------------------------
OUTPUT_COLS = ["id", "author", "subreddit", "created_utc", "title", "selftext",
               "url", "score", "num_comments", "over_18", "stickied", "locked", "permalink",
               "days_from", "confidence", "p_female", "p_male", "birth_post"]

merged = pd.concat([
    posts_filtered.reindex(columns=OUTPUT_COLS),
    unmatched_births.reindex(columns=OUTPUT_COLS)
], ignore_index=True)

merged = merged.sort_values(["author", "created_utc"]).reset_index(drop=True)

merged.to_csv(OUTPUT, index=False)

print(f"\nMerge complete. Saved {len(merged):,} rows to {OUTPUT}")
print(f"  Unique authors:              {merged['author'].nunique():,}")
print(f"  Birth posts  (birth_post == 1): {(merged['birth_post'] == 1).sum():,}")
print(f"  Other posts  (birth_post == 0): {(merged['birth_post'] == 0).sum():,}")
