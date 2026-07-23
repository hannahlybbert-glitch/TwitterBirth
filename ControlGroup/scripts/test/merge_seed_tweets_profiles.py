# Author: Hannah Lybbert
# Purpose: Merge profiles_filtered.csv (filtered user profiles) with
#          anniversaries_extracted_test.csv (seed tweets) on author_id,
#          keeping only the seed tweet rows whose author is in profiles_filtered.csv.

import os

import pandas as pd

os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

PROFILES_CSV   = "ControlGroup/data/user_profiles/anniversary/test/profiles_filtered.csv"
SEED_TWEETS_CSV = "ControlGroup/data/LLM/seed_tweets/test/anniversaries_extracted_test.csv"
OUTPUT_CSV     = "ControlGroup/data/user_profiles/anniversary/test/seed_tweets_profiles_merged.csv"


def main():
    profiles_df    = pd.read_csv(PROFILES_CSV)
    seed_tweets_df = pd.read_csv(SEED_TWEETS_CSV)

    merged_df = profiles_df.merge(seed_tweets_df, on="author_id", how="left")
    merged_df.to_csv(OUTPUT_CSV, index=False)

    print(f"Profiles:            {len(profiles_df):,}")
    print(f"Seed tweets:         {len(seed_tweets_df):,}")
    print(f"Merged rows:         {len(merged_df):,}")
    print(f"\nMerged file saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
