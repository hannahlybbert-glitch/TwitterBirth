# Author: Hannah Lybbert
# Purpose: Apply Filter A (account age) and Filter B (avg weekly tweets) to
#          profiles_raw.csv (from get_user_profiles.py), assign each surviving
#          author a placebo birth date, and save profiles_filtered.csv.
#          Filter B uses a fixed cutoff (FILTER_B_CUTOFF) equal to the treatment
#          group's 95th percentile of avg_weekly_tweets, applied to the control
#          group as well so both groups share the same threshold.

import os

import numpy as np
import pandas as pd
from datetime import date

os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")))

FILTER_NAME = "anniversary"   # must match the value used in get_user_profiles.py; set "" for default pull
TEST_MODE   = True            # set False for full run

# tweet_count reflects the account's live post count as of when get_user_profiles.py
# pulled it, so avg_weekly_tweets is measured against that pull date, not seed_tweet_date.
REF_DATE = pd.Timestamp(date.today(), tz="UTC")

FILTER_B_CUTOFF = 79.94      # treatment group's 95th percentile of avg_weekly_tweets; same cutoff applied to control

# days_from (treatment: date_birth_tweet - date_birth) is trimmed to +/-14 days upstream, so a
# control author's eventual placebo birth date can land up to 14 days earlier than seed_tweet_date.
# Filter A checks the worst case (seed_tweet_date - 14) so that ANY days_from later drawn for a
# surviving author is guaranteed to still keep them >= 18 months old as of their placebo date.
DAYS_FROM_MAX_ABS = 14

DAYS_FROM_SEED = 1234  # reproducibility for the placebo days_from draw
DAYS_FROM_CSV  = "data/final/user_analysis_sample.csv"  # treatment group's days_from distribution

_base_profiles = "ControlGroup/data/2_user_profiles"
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

    # Filter A: account must exist >= 18 months before the worst-case placebo birth date
    # (seed_tweet_date - 14 days). 18 months ≈ 548 days (18 × 30.44)
    worst_case_placebo = df["seed_tweet_date"] - pd.Timedelta(days=DAYS_FROM_MAX_ABS)
    df["filter_a_pass"] = (
        df["account_created_at"].notna() &
        ((worst_case_placebo - df["account_created_at"]).dt.days >= 548)
    ).astype(int)

    # Filter B: avg weekly tweets must be <= the treatment group's 95th percentile cutoff
    df["filter_b_pass"] = (
        df["avg_weekly_tweets"].notna() &
        (df["avg_weekly_tweets"] <= FILTER_B_CUTOFF)
    ).astype(int)

    df.to_csv(RAW_CSV, index=False)

    filtered_df = df[
        (df["not_found"] == 0) &
        (df["filter_a_pass"] == 1) &
        (df["filter_b_pass"] == 1)
    ].copy()

    # Assign each surviving author a placebo birth date by bootstrap-drawing days_from (with
    # replacement) from the treatment group's empirical distribution. Safe to draw only now,
    # after filtering, because Filter A already used the worst-case bound above -- any draw in
    # [-DAYS_FROM_MAX_ABS, DAYS_FROM_MAX_ABS] keeps a surviving author >= 18 months old.
    treatment_days_from = pd.read_csv(DAYS_FROM_CSV, usecols=["days_from"])["days_from"].dropna().to_numpy()
    rng = np.random.default_rng(DAYS_FROM_SEED)
    filtered_df["days_from"] = rng.choice(treatment_days_from, size=len(filtered_df), replace=True)
    filtered_df["date_birth_placebo"] = filtered_df["seed_tweet_date"] - pd.to_timedelta(filtered_df["days_from"], unit="D")

    filtered_df.to_csv(FILTERED_CSV, index=False)

    n_total     = len(df)
    n_not_found = (df["not_found"] == 1).sum()
    n_found     = (df["not_found"] == 0).sum()
    n_after_a   = ((df["not_found"] == 0) & (df["filter_a_pass"] == 1)).sum()
    n_final     = len(filtered_df)

    print(f"Filter B cutoff: avg_weekly_tweets <= {FILTER_B_CUTOFF:.2f}  (treatment group's 95th percentile)")
    print(f"\nSummary:")
    print(f"  Input authors:          {n_total:,}")
    print(f"  Not found by API:       {n_not_found:,}")
    print(f"  Pass Filter A (age):    {n_after_a:,}  (of {n_found:,} found)")
    print(f"  Pass Filter A + B:      {n_final:,}")

    print(f"\nFiltered avg_weekly_tweets:")
    print(f"  Mean:                   {filtered_df['avg_weekly_tweets'].mean():.2f}")
    print(f"  50th percentile:        {filtered_df['avg_weekly_tweets'].quantile(0.50):.2f}")
    print(f"  95th percentile:        {filtered_df['avg_weekly_tweets'].quantile(0.95):.2f}")

    print(f"\nAssigned days_from/date_birth_placebo to all {n_final:,} filtered authors "
          f"(bootstrap draw from {len(treatment_days_from):,} treatment days_from values)")

    print(f"\nFiltered profiles saved to {FILTERED_CSV}")


if __name__ == "__main__":
    main()
