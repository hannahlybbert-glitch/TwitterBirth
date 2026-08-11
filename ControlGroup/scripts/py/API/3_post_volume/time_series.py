# Author: Hannah Lybbert
# Purpose: Simple time series of average og/qt tweets per week across all
#          control authors in post_volume_filtered.csv (from filter_volume.py).

import os

import matplotlib.pyplot as plt
import pandas as pd

os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")))

FILTER_NAME = "anniversary"   # must match the value used in get_seed_tweets.py; set "" for default pull
TEST_MODE   = True            # set False for full run

_base_volume = "ControlGroup/data/3_post_volume"
if FILTER_NAME:
    _base_volume = f"{_base_volume}/{FILTER_NAME}"

OUTPUT_DIR   = f"{_base_volume}/test" if TEST_MODE else _base_volume
FILTERED_CSV = f"{OUTPUT_DIR}/post_volume_filtered.csv"

FIGURE_PATH = "ControlGroup/output/volume/control_avg_weekly_tweets.png"


def main():
    df = pd.read_csv(FILTERED_CSV, dtype={"author_id": str})
    df["date"] = pd.to_datetime(df["date"])

    # Week relative to each author's own first observed date (0 = first week in their window)
    start_date = df.groupby("author_id")["date"].transform("min")
    df["week"] = ((df["date"] - start_date).dt.days // 7)

    # Sum tweets per author-week, then average across authors for each week
    weekly_by_author = df.groupby(["author_id", "week"])["original_quote_count"].sum()
    avg_weekly = weekly_by_author.groupby("week").mean()

    print("Average og/qt tweets per week across all control authors:\n")
    print(avg_weekly.to_string())

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(avg_weekly.index, avg_weekly.values)
    ax.set_xlabel("Week in sample")
    ax.set_ylabel("Average og/qt tweets per week")
    ax.set_title("Control group: average weekly tweet volume")
    fig.tight_layout()

    os.makedirs(os.path.dirname(FIGURE_PATH), exist_ok=True)
    fig.savefig(FIGURE_PATH, dpi=150)
    plt.close(fig)

    print(f"\nSaved figure to {FIGURE_PATH}")


if __name__ == "__main__":
    main()
