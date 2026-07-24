# Author: Hannah Lybbert
# Created: 2026-07-24
# Purpose: Count how many birth posts come from each subreddit

import pandas as pd
from pathlib import Path

ROOT       = Path(__file__).resolve().parents[4]
INPUT_PATH = ROOT / "Reddit/data/final/births_and_posts_FULL.csv"
OUTPUT_PATH = ROOT / "Reddit/data/descriptives/birth_subreddits.csv"

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
df = pd.read_csv(INPUT_PATH, low_memory=False)
print(f"Loaded {len(df):,} rows")

births = df[df["birth_post"] == 1]
print(f"Found {len(births):,} birth posts across {births['subreddit'].nunique():,} subreddits")

# ----------------------------------------------------------------
# Count birth posts per subreddit
# ----------------------------------------------------------------
subreddit_counts = (
    births.groupby("subreddit")
    .size()
    .reset_index(name="birth_post_count")
    .sort_values("birth_post_count", ascending=False)
)

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
subreddit_counts.to_csv(OUTPUT_PATH, index=False)
print(f"Saved to {OUTPUT_PATH}")
