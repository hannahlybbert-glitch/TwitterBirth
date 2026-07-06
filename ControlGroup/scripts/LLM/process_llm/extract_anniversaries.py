# Author: Hannah Lybbert
# Purpose: Filter LLM-classified anniversary tweets down to positive matches
#          (anniversary_flag == 1) for downstream user profiling.

import os

import pandas as pd

TEST_MODE = True

_base = "ControlGroup/data/LLM/seed_tweets/test" if TEST_MODE else "ControlGroup/data/LLM/seed_tweets"
INPUT_PATH  = f"{_base}/anniversary_tweets_classified_test.csv" if TEST_MODE else f"{_base}/anniversary_tweets_classified.csv"
OUTPUT_PATH = f"{_base}/anniversaries_extracted_test.csv" if TEST_MODE else f"{_base}/anniversaries_extracted.csv"

OUTPUT_COLUMNS = ["author_id", "tweet_id", "created_at", "week_start", "text", "like_count"]


def main():
    os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

    df = pd.read_csv(INPUT_PATH)
    extracted = df[df["anniversary_flag"] == 1][OUTPUT_COLUMNS]

    extracted.to_csv(OUTPUT_PATH, index=False)
    print(f"Extracted {len(extracted):,} anniversary tweets (of {len(df):,}) to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
