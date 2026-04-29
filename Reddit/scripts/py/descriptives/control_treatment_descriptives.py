# Author: Hannah Lybbert
# Created: 2026-04-03
# Updated: 2026-04-03
# Purpose: Descriptive stats comparing treatment and control groups — subreddits and posting activity

import pandas as pd
from pathlib import Path

ROOT       = Path(__file__).resolve().parents[4]
INPUT      = ROOT / "Reddit/data/final/treatment_control_births_posts.csv"
OUTPUT_DIR = ROOT / "Reddit/output/descriptives"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
df = pd.read_csv(INPUT, low_memory=False, encoding="latin-1")
df["created_utc"] = pd.to_datetime(df["created_utc"], unit="s", errors="coerce")

print(f"Loaded {len(df):,} rows | {df['author'].nunique():,} authors")
print(f"  Treatment posts: {(df['treated'] == 1).sum():,} | authors: {df[df['treated'] == 1]['author'].nunique():,}")
print(f"  Control posts:   {(df['treated'] == 0).sum():,} | authors: {df[df['treated'] == 0]['author'].nunique():,}")

# ----------------------------------------------------------------
# Top 25 subreddits by posts — treatment vs control
# ----------------------------------------------------------------
for treated, label in [(1, "Treatment"), (0, "Control")]:
    sub_counts = (
        df[df["treated"] == treated]["subreddit"]
        .value_counts()
        .head(25)
        .reset_index()
    )
    sub_counts.columns = ["subreddit", "posts"]
    sub_counts["pct"] = (sub_counts["posts"] / sub_counts["posts"].sum() * 100).round(2)

    print(f"\n--- Top 25 Subreddits by Posts — {label} ---")
    print(sub_counts.to_string(index=False))

# ----------------------------------------------------------------
# Average posts per author per month — quantiles, treatment vs control
# ----------------------------------------------------------------
df["year_month"] = df["created_utc"].dt.to_period("M")

print(f"\n--- Avg Posts per Author per Month — Quantiles ---")
for treated, label in [(1, "Treatment"), (0, "Control")]:
    grp = df[df["treated"] == treated]

    # posts per author per month
    monthly = (
        grp.groupby(["author", "year_month"])
        .size()
        .reset_index(name="posts")
    )

    # average across months per author
    avg_per_author = monthly.groupby("author")["posts"].mean()

    quantiles = avg_per_author.quantile([0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99])

    print(f"\n  {label} (n authors = {avg_per_author.shape[0]:,})")
    print(f"  {'Percentile':<15} {'Avg posts/month':>15}")
    print(f"  {'-'*32}")
    for q, v in quantiles.items():
        print(f"  {int(q*100):>3d}th pct       {v:>15.2f}")
    print(f"  {'Mean':<15} {avg_per_author.mean():>15.2f}")
    print(f"  {'Std dev':<15} {avg_per_author.std():>15.2f}")
