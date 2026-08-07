# Author: Hannah Lybbert
# Purpose: Drop copy-pasted/templated tweets from the seed tweet candidate pool.
#          Text posted verbatim by more than one author is more likely a spam
#          template than a genuine personal anniversary tweet. Reads
#          candidate_pool.csv (from get_seed_tweets.py) and saves
#          candidate_pool_CLEAN.csv with those rows dropped.

import os

import pandas as pd

os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

FILTER_NAME = "anniversary"   # must match the value used in get_seed_tweets.py; set "" for default pull
TEST_MODE   = True            # set False for full run

_base_dir = f"ControlGroup/data/1_seed_tweets/{FILTER_NAME}"
INPUT_DIR = f"{_base_dir}/test" if TEST_MODE else _base_dir

INPUT_CSV  = f"{INPUT_DIR}/candidate_pool.csv"
OUTPUT_CSV = f"{INPUT_DIR}/candidate_pool_CLEAN.csv"


def main():
    df = pd.read_csv(INPUT_CSV)

    # Strip URLs before comparing — t.co links are unique per tweet, so an
    # otherwise identical copy-pasted tweet won't match on raw text alone.
    df["text_norm"] = (
        df["text"].str.lower()
        .str.replace(r"https?://\S+", "", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )
    dupe_counts = df.groupby("text_norm")["author_id"].nunique()
    copypasta_texts = dupe_counts[dupe_counts > 1].index
    df["is_copypasta"] = df["text_norm"].isin(copypasta_texts)

    n_total     = len(df)
    n_copypasta = int(df["is_copypasta"].sum())
    n_templates = len(copypasta_texts)

    clean_df = df[~df["is_copypasta"]].drop(columns=["text_norm", "is_copypasta"])
    clean_df.to_csv(OUTPUT_CSV, index=False)

    print(f"Input tweets:                  {n_total:,}")
    print(f"Dropped as copypasta:          {n_copypasta:,}  ({n_copypasta / n_total:.1%})")
    print(f"Distinct copypasta templates:  {n_templates:,}")
    print(f"Remaining tweets:              {len(clean_df):,}")
    print(f"\nCleaned pool saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
