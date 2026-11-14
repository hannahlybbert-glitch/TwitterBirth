# Author: Hannah Lybbert
# Updated: 2026-11-05
# Purpose: Time series of average og/qt tweets per week across control authors in
#          post_volume_filtered.csv (from filter_volume.py), in weeks relative to placebo birth

import os

import matplotlib.pyplot as plt
import pandas as pd

os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

TEST_MODE = False   # set False for full run

_base_profiles = "ControlGroup/data/2_user_profiles"
_base_volume   = "ControlGroup/data/3_post_volume"
_base_figure   = "ControlGroup/output/volume/control_avg_weekly_tweets"

if TEST_MODE:
    PROFILES_CSV = f"{_base_profiles}/profiles_filtered_test.csv"
    FILTERED_CSV = f"{_base_volume}/test_100/post_volume_filtered.csv"
    FIGURE_PATH  = f"{_base_figure}_test.png"
else:
    PROFILES_CSV = f"{_base_profiles}/profiles_filtered.csv"
    FILTERED_CSV = f"{_base_volume}/post_volume_filtered.csv"
    FIGURE_PATH  = f"{_base_figure}.png"


def main():
    df = pd.read_csv(FILTERED_CSV, dtype={"author_id": str})
    df["date"] = pd.to_datetime(df["date"])

    profiles = pd.read_csv(PROFILES_CSV, dtype=str, usecols=["author_id", "date_birth_placebo"])
    profiles = profiles.drop_duplicates(subset="author_id")
    profiles["placebo_day"] = (pd.to_datetime(profiles["date_birth_placebo"], utc=True)
                               .dt.tz_localize(None).dt.normalize())
    df = df.merge(profiles[["author_id", "placebo_day"]], on="author_id", how="left")

    # Week 0 = the 7 days starting on placebo birth; negative = before
    df["week"] = (df["date"] - df["placebo_day"]).dt.days // 7

    # Sum tweets per author-week, then average across authors for each week
    weekly_by_author = df.groupby(["author_id", "week"])["original_quote_count"].sum()
    avg_weekly = weekly_by_author.groupby("week").mean()

    print("Average og/qt tweets per week across control authors (week 0 = placebo birth):\n")
    print(avg_weekly.round(2).to_string())

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(avg_weekly.index, avg_weekly.values)
    ax.axvline(0, color="grey", linestyle="--", linewidth=1)
    ax.set_xlabel("Weeks relative to placebo birth")
    ax.set_ylabel("Average og/qt tweets per week")
    ax.set_title(f"Control group: average weekly tweet volume (n = {df['author_id'].nunique():,})")
    fig.tight_layout()

    os.makedirs(os.path.dirname(FIGURE_PATH), exist_ok=True)
    fig.savefig(FIGURE_PATH, dpi=150)
    plt.close(fig)

    print(f"\nSaved figure to {FIGURE_PATH}")


if __name__ == "__main__":
    main()
