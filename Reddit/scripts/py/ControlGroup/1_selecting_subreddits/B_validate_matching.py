# Author: Hannah Lybbert
# Created: 2026-07-27
# Purpose: For each sampled account, validate how representative their activity is in
#          the subreddit they were pulled from: tenure, avg posts/month in that
#          subreddit, and the share of all their posts that happened there.

import pandas as pd
from pathlib import Path

ROOT               = Path(__file__).resolve().parents[5]
SAMPLED_ACCOUNTS   = ROOT / "Reddit/data/ControlGroup/1_subreddits/sampled_accounts_top_subreddits.csv"
OUTPUT_PATH        = ROOT / "Reddit/data/ControlGroup/1_subreddits/validate_matching.csv"


# ----------------------------------------------------------------
# Placeholder: pull full post history (all subreddits) for the sampled accounts
# ----------------------------------------------------------------
def get_post_history(authors):
    """
    TODO: replace with real pull logic.
    Must return a DataFrame with columns ["author", "subreddit", "created_utc"]
    covering every post (not just in their sampled subreddit) for `authors`.
    """
    raise NotImplementedError("Post history pull not yet implemented")


# ----------------------------------------------------------------
# Load sampled accounts and their full post histories
# ----------------------------------------------------------------
sampled = pd.read_csv(SAMPLED_ACCOUNTS)
print(f"Loaded {len(sampled):,} sampled accounts across {sampled['subreddit'].nunique():,} subreddits")

history = get_post_history(sampled["author"].unique())
history["created_utc"] = pd.to_datetime(history["created_utc"], unit="s")

# ----------------------------------------------------------------
# Metrics, computed per (author, sampled subreddit)
# ----------------------------------------------------------------
total_posts = history.groupby("author").size().rename("total_posts")

in_sub = history.merge(
    sampled[["author", "subreddit"]], on=["author", "subreddit"], how="inner"
)

sub_stats = (
    in_sub.groupby(["author", "subreddit"])["created_utc"]
    .agg(first_post="min", last_post="max", posts_in_subreddit="count")
    .reset_index()
)

sub_stats["subreddit_tenure_days"] = (
    sub_stats["last_post"] - sub_stats["first_post"]
).dt.days
sub_stats["subreddit_tenure_months"] = (sub_stats["subreddit_tenure_days"] / 30.44).clip(lower=1)

sub_stats["avg_posts_per_month_in_subreddit"] = (
    sub_stats["posts_in_subreddit"] / sub_stats["subreddit_tenure_months"]
)

results = sub_stats.merge(total_posts, on="author", how="left")
results["share_posts_in_subreddit"] = results["posts_in_subreddit"] / results["total_posts"]

results = results[[
    "author",
    "subreddit",
    "subreddit_tenure_days",
    "avg_posts_per_month_in_subreddit",
    "share_posts_in_subreddit",
]]

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
results.to_csv(OUTPUT_PATH, index=False)
print(f"Saved validation metrics for {len(results):,} accounts to {OUTPUT_PATH}")
