# Author: Hannah Lybbert
# Purpose: Apply Filter A (account age) and Filter B (avg weekly tweets) to
#          profiles_raw.csv (from get_user_profiles.py) and save profiles_filtered.csv.

import os

import pandas as pd
from datetime import date

os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

FILTER_NAME = "anniversary"   # must match the value used in get_user_profiles.py; set "" for default pull
TEST_MODE   = True            # set False for full run

# tweet_count reflects the account's live post count as of when get_user_profiles.py
# pulled it, so avg_weekly_tweets is measured against that pull date, not seed_tweet_date.
REF_DATE = pd.Timestamp(date.today(), tz="UTC")

FILTER_B_PERCENTILE = 0.95   # trim accounts above this percentile of the control's OWN avg_weekly_tweets

_base_profiles = "ControlGroup/data/user_profiles"
if FILTER_NAME:
    _base_profiles = f"{_base_profiles}/{FILTER_NAME}"

OUTPUT_DIR = f"{_base_profiles}/test" if TEST_MODE else _base_profiles

RAW_CSV      = f"{OUTPUT_DIR}/profiles_raw.csv"
FILTERED_CSV = f"{OUTPUT_DIR}/profiles_filtered.csv"


def main():
    df = pd.read_csv(RAW_CSV)

    df["seed_tweet_date"]    = pd.to_datetime(df["seed_tweet_date"], utc=True, errors="coerce")
    df["account_created_at"] = pd.to_datetime(df["account_created_at"], utc=True, errors="coerce")
    df["tweet_count"]        = pd.to_numeric(df["tweet_count"], errors="coerce")
    df["not_found"]          = pd.to_numeric(df["not_found"], errors="coerce").fillna(0).astype(int)

    df["account_age_weeks"] = (REF_DATE - df["account_created_at"]).dt.days / 7
    df["avg_weekly_tweets"] = df["tweet_count"] / df["account_age_weeks"]

    # Filter A: account must exist >= 18 months before seed tweet date
    # 18 months ≈ 548 days (18 × 30.44)
    df["filter_a_pass"] = (
        df["account_created_at"].notna() &
        ((df["seed_tweet_date"] - df["account_created_at"]).dt.days >= 548)
    ).astype(int)

    # Filter B: avg weekly tweets must be <= the control sample's own Nth percentile
    filter_b_cutoff = df["avg_weekly_tweets"].quantile(FILTER_B_PERCENTILE)
    df["filter_b_pass"] = (
        df["avg_weekly_tweets"].notna() &
        (df["avg_weekly_tweets"] <= filter_b_cutoff)
    ).astype(int)

    df.to_csv(RAW_CSV, index=False)

    filtered_df = df[
        (df["not_found"] == 0) &
        (df["filter_a_pass"] == 1) &
        (df["filter_b_pass"] == 1)
    ].copy()
    filtered_df.to_csv(FILTERED_CSV, index=False)

    n_total     = len(df)
    n_not_found = (df["not_found"] == 1).sum()
    n_found     = (df["not_found"] == 0).sum()
    n_after_a   = ((df["not_found"] == 0) & (df["filter_a_pass"] == 1)).sum()
    n_final     = len(filtered_df)

    print(f"Filter B cutoff: avg_weekly_tweets <= {filter_b_cutoff:.2f}  (control's {FILTER_B_PERCENTILE:.0%} percentile)")
    print(f"\nSummary:")
    print(f"  Input authors:          {n_total:,}")
    print(f"  Not found by API:       {n_not_found:,}")
    print(f"  Pass Filter A (age):    {n_after_a:,}  (of {n_found:,} found)")
    print(f"  Pass Filter A + B:      {n_final:,}")
    print(f"\nFiltered profiles saved to {FILTERED_CSV}")


if __name__ == "__main__":
    main()
