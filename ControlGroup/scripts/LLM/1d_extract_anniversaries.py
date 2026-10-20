# Author: Hannah Lybbert
# Updated: 2026-10-16
# Purpose: Keep LLM-classified anniversary tweets with anniversary_flag == 1 and confidence >= MIN_CONFIDENCE for user profiling

import os

import pandas as pd

TEST_MODE = False

_base = "ControlGroup/data/LLM/seed_tweets/test" if TEST_MODE else "ControlGroup/data/LLM/seed_tweets"
INPUT_PATH  = f"{_base}/anniversary_tweets_classified_test.csv" if TEST_MODE else f"{_base}/anniversary_tweets_RE_classified.csv"
OUTPUT_PATH = f"{_base}/anniversaries_extracted_test.csv" if TEST_MODE else f"{_base}/anniversaries_extracted.csv"

MIN_CONFIDENCE = 90  # chosen from hand-coding in prompt_accuracy.py

OUTPUT_COLUMNS = ["author_id", "tweet_id", "created_at", "week_start", "text", "like_count"]


def main():
    os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

    df = pd.read_csv(INPUT_PATH)
    keep = (df["anniversary_flag"] == 1) & (df["confidence"] >= MIN_CONFIDENCE)
    extracted = df[keep][OUTPUT_COLUMNS]

    extracted.to_csv(OUTPUT_PATH, index=False)
    print(f"Extracted {len(extracted):,} anniversary tweets (of {len(df):,}; "
          f"{(df['anniversary_flag'] == 1).sum():,} flagged, confidence >= {MIN_CONFIDENCE}) to {OUTPUT_PATH}")
    print(f"  unique authors: {extracted['author_id'].nunique():,}")


if __name__ == "__main__":
    main()
