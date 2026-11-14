# Author: Hannah Lybbert
# Created: 2026-11-11
# Purpose: Quick look at a partial pull (part_0 post_volume_temp.csv): runs filter_volume.py's
#          checks + trim in memory (nothing saved) and plots time_series.py's weekly average

import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from filter_volume import (FILTER_CUTOFF, check_window, check_coverage,
                           check_daily_counts, summarize_weekly, load_placebo_dates)

os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

# --- Config ---
INPUT_CSV   = "ControlGroup/data/3_post_volume/part_0/post_volume_temp.csv"
FIGURE_PATH     = "ControlGroup/output/volume/control_time_series_TEMP.png"
FIGURE_PATH_LOG = "ControlGroup/output/volume/control_time_series_log_TEMP.png"
WEEK_MIN, WEEK_MAX = -78, 77   # weeks relative to placebo birth; week 78 is partial (~2 days)


def main():
    # --- Load ---
    df = pd.read_csv(INPUT_CSV, dtype={"author_id": str})
    for col in ("date", "begin_date", "end_date"):
        df[col] = pd.to_datetime(df[col])
    print(f"Loaded {len(df):,} rows, {df['author_id'].nunique():,} authors from {INPUT_CSV}")

    # Only authors pulled so far, so Check 1 doesn't count unpulled authors as "no rows"
    placebo = load_placebo_dates()
    placebo = placebo[placebo.index.isin(df["author_id"].unique())]

    # --- Checks (same functions as filter_volume.py) ---
    windows = check_window(df, placebo)
    check_coverage(df, windows)
    check_daily_counts(df)
    weekly = summarize_weekly(df)

    # --- Trim (in memory only) ---
    keep_ids = weekly[weekly < FILTER_CUTOFF].index
    df = df[df["author_id"].isin(keep_ids)].copy()
    print(f"\n--- Trim: og_qt_weekly_sample_tweets < {FILTER_CUTOFF} ---")
    print(f"Input authors: {len(weekly):,}  |  pass trim: {len(keep_ids):,}")
    print("Per-author average weekly tweets after trim:")
    print(weekly[weekly < FILTER_CUTOFF].describe().round(2).to_string())

    # --- Time series (same logic as time_series.py) ---
    placebo_day = placebo.dt.normalize().rename("placebo_day")
    df = df.merge(placebo_day, left_on="author_id", right_index=True, how="left")
    df["week"] = (df["date"] - df["placebo_day"]).dt.days // 7

    df = df[df["week"].between(WEEK_MIN, WEEK_MAX)]

    # One row per author-week, so n = authors in each week
    weekly_by_author = df.groupby(["author_id", "week"])["original_quote_count"].sum()
    n_authors = df["author_id"].nunique()

    plot_weekly(weekly_by_author, "Average og/qt tweets per week",
                "average weekly tweet volume", n_authors, FIGURE_PATH)
    # Log version: log(x + 1) per author-week, then average (as in treatment's original_tweets.do)
    plot_weekly(np.log1p(weekly_by_author), "Average log(og/qt tweets + 1) per week",
                "average log weekly tweet volume", n_authors, FIGURE_PATH_LOG)


def plot_weekly(values, ylabel, title, n_authors, path):
    """Mean and 95% CI across authors for each week; values = one row per author-week."""
    stats = values.groupby("week").agg(["mean", "std", "count"])
    stats["se"] = stats["std"] / stats["count"] ** 0.5
    stats["ci_lower"] = stats["mean"] - 1.96 * stats["se"]
    stats["ci_upper"] = stats["mean"] + 1.96 * stats["se"]
    print(f"\n{ylabel} — mean, 95% CI, and n authors:")
    print(stats[["mean", "ci_lower", "ci_upper", "count"]].round(3).to_string())

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.fill_between(stats.index, stats["ci_lower"], stats["ci_upper"], alpha=0.3, label="95% CI")
    ax.plot(stats.index, stats["mean"], label="Mean")
    ax.legend()
    ax.axvline(0, color="grey", linestyle="--", linewidth=1)
    ax.set_xlabel("Weeks relative to placebo birth")
    ax.set_ylabel(ylabel)
    ax.set_title(f"Control group (partial, part_0): {title} (n = {n_authors:,})")
    fig.tight_layout()

    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved figure to {path}")


if __name__ == "__main__":
    main()
