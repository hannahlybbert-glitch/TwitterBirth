# Author: Hannah Lybbert
# Purpose: Sum each author's og/qt tweet volume over the 3-year sample window
#          (from get_post_volume.py) and trim authors whose total_sample_tweets
#          is at or above the treatment group's 95th percentile cutoff.
#
# TODO: there is probably more cleaning needed on post_volume.csv before this
# trim (e.g. authors with incomplete/sparse day coverage, duplicate rows) --
# come back to this before running on the full sample.

import os

import pandas as pd

os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

FILTER_NAME = "anniversary"   # must match the value used in get_seed_tweets.py; set "" for default pull
TEST_MODE   = True            # set False for full run

FILTER_CUTOFF = 4752   # treatment group's 95th percentile of total sample (og/qt) tweets; trim >= this

_base_volume = "ControlGroup/data/3_post_volume"
if FILTER_NAME:
    _base_volume = f"{_base_volume}/{FILTER_NAME}"

OUTPUT_DIR = f"{_base_volume}/test" if TEST_MODE else _base_volume

INPUT_PATH   = f"{OUTPUT_DIR}/post_volume.csv" if TEST_MODE else f"{OUTPUT_DIR}/post_volume.parquet"
FILTERED_CSV = f"{OUTPUT_DIR}/post_volume_filtered.csv"


def main():
    if TEST_MODE:
        df = pd.read_csv(INPUT_PATH, dtype={"author_id": str})
    else:
        df = pd.read_parquet(INPUT_PATH)
        df["author_id"] = df["author_id"].astype(str)

    totals = df.groupby("author_id")["original_quote_count"].sum().rename("total_sample_tweets")

    n_total  = len(totals)
    keep_ids = totals[totals < FILTER_CUTOFF].index
    n_final  = len(keep_ids)

    filtered_df = df[df["author_id"].isin(keep_ids)].copy()
    filtered_df.to_csv(FILTERED_CSV, index=False)

    print(f"Filter cutoff: total_sample_tweets < {FILTER_CUTOFF:,}  (treatment group's 95th percentile)")
    print(f"\nSummary:")
    print(f"  Input authors:  {n_total:,}")
    print(f"  Pass trim:      {n_final:,}")
    print(f"\nFiltered volume data saved to {FILTERED_CSV}")


if __name__ == "__main__":
    main()
