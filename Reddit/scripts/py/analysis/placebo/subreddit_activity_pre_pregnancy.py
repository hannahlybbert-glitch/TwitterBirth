# Author: Hannah Lybbert
# Created: 2026-03-27
# Updated: 2026-03-27
# Purpose: Compute log avg posts/month per subreddit during months -21 to -9 for treatment and control groups

import numpy as np
import pandas as pd
from pathlib import Path

ROOT         = Path(__file__).resolve().parents[5]
INPUT_TREAT  = ROOT / "Reddit/data/final/births_and_posts_22k.csv"
INPUT_CTRL   = ROOT / "Reddit/data/intermediate/births_and_posts/placebo_births_and_posts.csv"
OUTPUT_DIR   = ROOT / "Reddit/output/analysis/placebo"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH        = OUTPUT_DIR / "subreddit_activity_pre_pregnancy.csv"
OUTPUT_PATH_WINDOW = OUTPUT_DIR / "subreddit_activity_pre_pregnancy_window_sample.csv"

WINDOW_MIN    = -21
WINDOW_MAX    = -9
WINDOW_MONTHS = 13   # fixed denominator: months -21 through -9 inclusive
SAMPLE_MIN    = 100  # minimum authors required in both groups to include a subreddit

# ----------------------------------------------------------------
# Helper: compute log(avg posts/month) per subreddit for one group
# ----------------------------------------------------------------
def subreddit_log_activity(df, col_name, sample="ever"):
    """
    For each subreddit, compute log(avg posts/month + 1) during months -21 to -9.

    sample="ever"   : include all authors who ever posted in the subreddit (anywhere in data);
                      authors with 0 posts in the window contribute 0 to the average.
    sample="window" : include only authors who posted in the subreddit at least once
                      during the -21 to -9 window; no zeros by construction.
    """
    # Posts in the window
    window = df[
        (df["months_from_birth"] >= WINDOW_MIN) &
        (df["months_from_birth"] <= WINDOW_MAX)
    ]
    window_counts = (
        window.groupby(["author", "subreddit"])
        .size()
        .reset_index(name="post_count")
    )

    if sample == "ever":
        # All (author, subreddit) pairs observed anywhere in the data
        ever_posted = df[["author", "subreddit"]].drop_duplicates()
        # Merge: authors with 0 posts in window get post_count = 0
        author_sub = ever_posted.merge(window_counts, on=["author", "subreddit"], how="left")
        author_sub["post_count"] = author_sub["post_count"].fillna(0)
    else:
        # Only authors who posted in the subreddit during the window (no zeros)
        author_sub = window_counts.copy()

    # Posts per month using fixed window length
    author_sub["posts_per_month"] = author_sub["post_count"] / WINDOW_MONTHS

    # Average across authors per subreddit, then log(x+1); also count authors
    sub_avg = author_sub.groupby("subreddit").agg(
        avg_posts_per_month = ("posts_per_month", "mean"),
        author_count        = ("author", "count"),
    ).reset_index()
    sub_avg[col_name]                                    = np.log(sub_avg["avg_posts_per_month"] + 1)
    sub_avg[col_name.replace("_avg", "_sample")]         = sub_avg["author_count"]
    sub_avg[col_name.replace("_avg", "_avg_posts")]      = sub_avg["avg_posts_per_month"].round(2)

    return sub_avg[["subreddit", col_name, col_name.replace("_avg", "_sample"), col_name.replace("_avg", "_avg_posts")]]

# ----------------------------------------------------------------
# Helper: filter to subreddits meeting minimum sample in both groups
# ----------------------------------------------------------------
def filter_by_sample(treat_sub, ctrl_sub):
    """
    Independently filter each side: keep subreddits where
    treatment_sample >= SAMPLE_MIN for treatment, and
    control_sample >= SAMPLE_MIN for control.
    """
    return (
        treat_sub[treat_sub["treatment_sample"] >= SAMPLE_MIN].copy(),
        ctrl_sub[ctrl_sub["control_sample"]     >= SAMPLE_MIN].copy(),
    )

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
treat = pd.read_csv(INPUT_TREAT)
ctrl  = pd.read_csv(INPUT_CTRL, low_memory=False)

print(f"Treatment: {len(treat):,} posts | {treat['author'].nunique():,} authors")
print(f"Control:   {len(ctrl):,} posts  | {ctrl['author'].nunique():,} authors")

# ----------------------------------------------------------------
# Compute per-group subreddit activity
# ----------------------------------------------------------------
treat_sub = subreddit_log_activity(treat, "treatment_avg")
ctrl_sub  = subreddit_log_activity(ctrl,  "control_avg")

print(f"\nTreatment unique subreddits: {len(treat_sub):,}")
print(f"Control unique subreddits:   {len(ctrl_sub):,}")

# ----------------------------------------------------------------
# Build independent sorted columns (no join on subreddit)
# ----------------------------------------------------------------
treat_sub, ctrl_sub = filter_by_sample(treat_sub, ctrl_sub)
print(f"After sample filter (>={SAMPLE_MIN}): {len(treat_sub):,} subreddits")

treat_sub["treatment_avg"] = treat_sub["treatment_avg"].round(2)
ctrl_sub["control_avg"]   = ctrl_sub["control_avg"].round(2)

treat_sorted = treat_sub.sort_values("treatment_avg", ascending=False).reset_index(drop=True)
ctrl_sorted  = ctrl_sub.sort_values("control_avg",   ascending=False).reset_index(drop=True)

treat_sorted = treat_sorted.rename(columns={
    "subreddit":       "t_subreddit",
    "treatment_avg":   "t_ln_postpermonth",
    "treatment_sample": "t_sample_cnt",
    "treatment_avg_posts": "t_avg_postperauthor_month",
})
ctrl_sorted = ctrl_sorted.rename(columns={
    "subreddit":     "c_subreddit",
    "control_avg":   "c_ln_postpermonth",
    "control_sample": "c_sample_cnt",
    "control_avg_posts": "c_avg_postperauthor_month",
})

treat_sorted = treat_sorted[["t_subreddit", "t_ln_postpermonth", "t_sample_cnt", "t_avg_postperauthor_month"]]
ctrl_sorted  = ctrl_sorted[["c_subreddit",  "c_ln_postpermonth", "c_sample_cnt", "c_avg_postperauthor_month"]]

result = pd.concat([treat_sorted, ctrl_sorted], axis=1)

print(f"\nTreatment subreddits: {treat_sorted['t_subreddit'].notna().sum():,}")
print(f"Control subreddits:   {ctrl_sorted['c_subreddit'].notna().sum():,}")

# ----------------------------------------------------------------
# Save
# ----------------------------------------------------------------
result.to_csv(OUTPUT_PATH, index=False)
print(f"\nSaved to {OUTPUT_PATH}")
print(result.head(20).to_string())

# ----------------------------------------------------------------
# Window-sample version: only authors who posted in subreddit
# during -21 to -9 (no zeros)
# ----------------------------------------------------------------
print(f"\n--- Window sample (posted in subreddit during -21 to -9) ---")
treat_sub_w = subreddit_log_activity(treat, "treatment_avg", sample="window")
ctrl_sub_w  = subreddit_log_activity(ctrl,  "control_avg",  sample="window")

print(f"Treatment unique subreddits: {len(treat_sub_w):,}")
print(f"Control unique subreddits:   {len(ctrl_sub_w):,}")

treat_sub_w, ctrl_sub_w = filter_by_sample(treat_sub_w, ctrl_sub_w)
print(f"After sample filter (>={SAMPLE_MIN}): {len(treat_sub_w):,} subreddits")

treat_sub_w["treatment_avg"] = treat_sub_w["treatment_avg"].round(2)
ctrl_sub_w["control_avg"]    = ctrl_sub_w["control_avg"].round(2)

treat_sorted_w = treat_sub_w.sort_values("treatment_avg", ascending=False).reset_index(drop=True)
ctrl_sorted_w  = ctrl_sub_w.sort_values("control_avg",   ascending=False).reset_index(drop=True)

treat_sorted_w = treat_sorted_w.rename(columns={
    "subreddit":           "t_subreddit",
    "treatment_avg":       "t_ln_postpermonth",
    "treatment_sample":    "t_sample_cnt",
    "treatment_avg_posts": "t_avg_postperauthor_month",
})
ctrl_sorted_w = ctrl_sorted_w.rename(columns={
    "subreddit":         "c_subreddit",
    "control_avg":       "c_ln_postpermonth",
    "control_sample":    "c_sample_cnt",
    "control_avg_posts": "c_avg_postperauthor_month",
})

treat_sorted_w = treat_sorted_w[["t_subreddit", "t_ln_postpermonth", "t_sample_cnt", "t_avg_postperauthor_month"]]
ctrl_sorted_w  = ctrl_sorted_w[["c_subreddit",  "c_ln_postpermonth", "c_sample_cnt", "c_avg_postperauthor_month"]]

result_w = pd.concat([treat_sorted_w, ctrl_sorted_w], axis=1)

result_w.to_csv(OUTPUT_PATH_WINDOW, index=False)
print(f"Saved to {OUTPUT_PATH_WINDOW}")
print(result_w.head(20).to_string())
