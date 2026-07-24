# Author: Hannah Lybbert
# Created: 2026-07-24
# Purpose: Find the top subreddits (other than birth subreddits) that treatment users post in

import pandas as pd
from pathlib import Path

ROOT               = Path(__file__).resolve().parents[5]
INPUT_PATH         = ROOT / "Reddit/data/final/births_and_posts_FULL.csv"
BIRTH_SUBS_PATH    = ROOT / "Reddit/data/descriptives/birth_subreddits.csv"
OUTPUT_PATH        = ROOT / "Reddit/data/ControlGroup/1_subreddits/other_treatment_subreddits.csv"
TOP_N              = 20

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
df = pd.read_csv(INPUT_PATH, low_memory=False)
print(f"Loaded {len(df):,} rows, {df['author'].nunique():,} unique treatment users")

birth_subreddits = set(pd.read_csv(BIRTH_SUBS_PATH)["subreddit"])
print(f"Excluding {len(birth_subreddits):,} birth subreddits")

# ----------------------------------------------------------------
# Count unique treatment users per non-birth subreddit
# ----------------------------------------------------------------
other = df[~df["subreddit"].isin(birth_subreddits)]

subreddit_counts = (
    other.groupby("subreddit")["author"]
    .nunique()
    .reset_index(name="active_treatment_users")
    .sort_values("active_treatment_users", ascending=False)
    .head(TOP_N)
)

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
subreddit_counts.to_csv(OUTPUT_PATH, index=False)
print(f"Saved top {TOP_N} subreddits to {OUTPUT_PATH}")
