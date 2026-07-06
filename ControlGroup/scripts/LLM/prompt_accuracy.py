"""
Compute accuracy of each LLM prompt variant against the handcoded truth column.

Reads ControlGroup/data/LLM/seed_tweets/test/handcoded.csv, which contains one
row per handcoded tweet plus a trailing totals row (blank tweet_id) that is
dropped before scoring. A prediction of -99 means the prompt did not produce
a usable label for that tweet, and is treated as a negative (0) prediction.
"""

from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "LLM" / "seed_tweets" / "test" / "handcoded.csv"
TRUTH_COL = "handcode"
PRED_COLS = ["full", "mini", "mini_week", "mini_no_week_SO", "mini2"]
MISSING_VALUE = -99


def main():
    df = pd.read_csv(DATA_PATH)
    df = df[df["tweet_id"].notna()]
    df[PRED_COLS] = df[PRED_COLS].replace(MISSING_VALUE, 0)

    print(f"Loaded {len(df)} handcoded tweets from {DATA_PATH}\n")

    for col in PRED_COLS:
        correct = (df[col] == df[TRUTH_COL]).sum()
        accuracy = correct / len(df)

        print(f"{col}:")
        print(f"  accuracy = {accuracy:.3f} ({correct}/{len(df)})\n")


if __name__ == "__main__":
    main()
