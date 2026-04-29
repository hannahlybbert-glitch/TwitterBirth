# Author: Hannah Lybbert
# Created: 2026-03-31
# Updated: 2026-03-31
# Purpose: For each treatment subreddit, find closest control match by avg log posts (-21 to -9) and share of treatment sample

import numpy as np
import pandas as pd
from pathlib import Path

ROOT             = Path(__file__).resolve().parents[5]
INPUT_CTRL_SAMP  = ROOT / "Reddit/raw/placebo_sample_posts.csv"
INPUT_CTRL_HIST  = ROOT / "Reddit/data/intermediate/births_and_posts/placebo_births_and_posts.csv"
INPUT_TREAT      = ROOT / "Reddit/data/final/births_and_posts_22k.csv"
OUTPUT_DIR       = ROOT / "Reddit/output/analysis/placebo"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

WINDOW_MIN  = -21
WINDOW_MAX  = -9


# ----------------------------------------------------------------
# Helper: compute avg log(posts+1) per subreddit over the window
# ----------------------------------------------------------------
def avg_log_posts(post_history, author_subreddit_map):
    """
    Returns a Series indexed by subreddit with the mean log(posts+1)
    per author per month, averaged over the full window.
    """
    months = list(range(WINDOW_MIN, WINDOW_MAX + 1))

    df = post_history.merge(author_subreddit_map, on="author", how="inner")
    df = df[df["subreddit_x"] == df["subreddit_y"]].copy()
    df = df.rename(columns={"subreddit_y": "assigned_subreddit"}).drop(columns=["subreddit_x"])
    df = df[
        (df["months_from_birth"] >= WINDOW_MIN) &
        (df["months_from_birth"] <= WINDOW_MAX)
    ]

    post_counts = (
        df.groupby(["author", "assigned_subreddit", "months_from_birth"])
        .size()
        .reset_index(name="post_count")
    )

    all_combos = (
        author_subreddit_map
        .assign(key=1)
        .merge(pd.DataFrame({"months_from_birth": months, "key": 1}), on="key")
        .drop(columns="key")
        .rename(columns={"subreddit": "assigned_subreddit"})
    )
    panel = all_combos.merge(
        post_counts, on=["author", "assigned_subreddit", "months_from_birth"], how="left"
    )
    panel["post_count"] = panel["post_count"].fillna(0)
    panel["log_posts"]  = np.log(panel["post_count"] + 1)

    return (
        panel.groupby("assigned_subreddit")["log_posts"]
        .mean()
        .rename("avg_log_posts")
    )


# ----------------------------------------------------------------
# Load data
# ----------------------------------------------------------------
print("Loading control data...")
ctrl_sample = pd.read_csv(INPUT_CTRL_SAMP)
ctrl_assign = (
    ctrl_sample.sort_index()
    .groupby("author", sort=False)
    .first()
    .reset_index()[["author", "subreddit"]]
)
ctrl_hist = pd.read_csv(INPUT_CTRL_HIST, low_memory=False)
ctrl_hist["months_from_birth"] = ctrl_hist["months_from_birth"].astype(float)

print("Loading treatment data...")
treat = pd.read_csv(INPUT_TREAT, low_memory=False)
treat_assign = (
    treat[treat["birth_post"] == 1][["author", "subreddit"]]
    .drop_duplicates(subset="author")
    .reset_index(drop=True)
)

# ----------------------------------------------------------------
# Compute averages
# ----------------------------------------------------------------
print("Computing control averages...")
ctrl_avg = avg_log_posts(ctrl_hist, ctrl_assign)

print("Computing treatment averages...")
treat_avg = avg_log_posts(treat, treat_assign)

# ----------------------------------------------------------------
# Treatment sample share per subreddit
# ----------------------------------------------------------------
n_treat_total = len(treat_assign)
treat_share = (
    treat_assign["subreddit"]
    .value_counts()
    .rename("n_authors")
    .to_frame()
    .assign(pct_of_sample=lambda x: (x["n_authors"] / n_treat_total * 100).round(2))
)

# ----------------------------------------------------------------
# Match each treatment subreddit to closest control subreddit(s)
# ----------------------------------------------------------------
TOLERANCE = 1e-6  # treat differences within this as ties

rows = []
for t_sub, t_val in treat_avg.items():
    diffs = (ctrl_avg - t_val).abs().sort_values()
    min_diff = diffs.iloc[0]
    matches = diffs[diffs <= min_diff + TOLERANCE].index.tolist()
    pct = treat_share.loc[t_sub, "pct_of_sample"] if t_sub in treat_share.index else 0.0
    n   = treat_share.loc[t_sub, "n_authors"]     if t_sub in treat_share.index else 0
    rows.append({
        "treatment_subreddit":    t_sub,
        "n_treat_authors":        n,
        "pct_of_treat_sample":    pct,
        "t_avg_log_posts":        round(t_val, 5),
        "ctrl_avg_log_posts":     round(ctrl_avg[matches[0]], 5),
        "abs_diff":               round(min_diff, 5),
        "closest_ctrl_subreddit": "; ".join(matches),
    })

results = (
    pd.DataFrame(rows)
    .sort_values("pct_of_treat_sample", ascending=False)
    .reset_index(drop=True)
)

# ----------------------------------------------------------------
# Output
# ----------------------------------------------------------------
csv_path = OUTPUT_DIR / "subreddit_matching.csv"
results.to_csv(csv_path, index=False)
print(f"\nSaved: {csv_path}")
print(results.to_string(index=False))
