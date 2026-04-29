# Author: Hannah Lybbert
# Created: 2026-04-03
# Updated: 2026-04-03
# Purpose: Quick diagnostic checks on cleaned placebo data — subreddit distribution and author concentration

import pandas as pd
from pathlib import Path

ROOT       = Path(__file__).resolve().parents[5]
INPUT_PATH = ROOT / "Reddit/data/intermediate/cleaned_raw/reddit_placebo_cleaned.csv"

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
print(f"Loading {INPUT_PATH.name}...")
df = pd.read_csv(INPUT_PATH, low_memory=False)
print(f"  Rows: {len(df):,} | Authors: {df['author'].nunique():,}")

# ----------------------------------------------------------------
# Top 25 subreddits by posts
# ----------------------------------------------------------------
print(f"\nTop 25 subreddits by posts:")
top_subs = df["subreddit"].value_counts().head(25).reset_index()
top_subs.columns = ["subreddit", "posts"]
top_subs["pct"] = (top_subs["posts"] / len(df) * 100).round(2)
for _, row in top_subs.iterrows():
    print(f"  {row['subreddit']:35s}: {row['posts']:7,}  ({row['pct']:.2f}%)")

# ----------------------------------------------------------------
# Author concentration in top 25 subreddits
# Flags subreddits inflated by a small number of prolific authors
# ----------------------------------------------------------------
print(f"\nAuthor concentration in top 25 subreddits:")
print(f"  {'Subreddit':<35} {'Total':>7}  {'Top author':>10}  {'Top 3':>7}  {'Top author name'}")
print(f"  {'-'*85}")
for sub in top_subs["subreddit"]:
    sub_df        = df[df["subreddit"] == sub]
    total         = len(sub_df)
    author_counts = sub_df["author"].value_counts()
    top1_pct      = author_counts.iloc[0] / total * 100
    top3_pct      = author_counts.iloc[:3].sum() / total * 100
    top_author    = author_counts.index[0]
    print(f"  {sub:<35} {total:>7,}  {top1_pct:>9.1f}%  {top3_pct:>6.1f}%  {top_author}")
