# Author: Hannah Lybbert
# Updated: 2026-11-05
# Purpose: Check merged post volume (window length, day coverage, daily counts), summarize
#          weekly tweets, and trim authors at/above treatment's 95th pct weekly rate

import os

import pandas as pd

os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

TEST_MODE = False   # set False for full run

WINDOW_MONTHS   = 18     # months before and after placebo birth
WEEKS_IN_SAMPLE = 156    # weeks in the full 3-year window
FILTER_CUTOFF   = 30.46  # treatment's 95th pct of avg weekly og/qt tweets; trim >= this

_base_profiles = "ControlGroup/data/2_user_profiles"
_base_volume   = "ControlGroup/data/3_post_volume"

if TEST_MODE:
    PROFILES_CSV = f"{_base_profiles}/profiles_filtered_test.csv"
    OUTPUT_DIR   = f"{_base_volume}/test_100"
    INPUT_PATH   = f"{OUTPUT_DIR}/post_volume.csv"
else:
    PROFILES_CSV = f"{_base_profiles}/profiles_filtered.csv"
    OUTPUT_DIR   = _base_volume
    INPUT_PATH   = f"{OUTPUT_DIR}/post_volume.parquet"

FILTERED_CSV = f"{OUTPUT_DIR}/post_volume_filtered.csv"
FILTERED_DTA = f"{OUTPUT_DIR}/post_volume_filtered.dta"

PCTS = [0.25, 0.5, 0.75, 0.9, 0.95, 0.99]


def load_volume():
    if TEST_MODE:
        df = pd.read_csv(INPUT_PATH, dtype={"author_id": str})
    else:
        df = pd.read_parquet(INPUT_PATH)
        df["author_id"] = df["author_id"].astype(str)
    for col in ("date", "begin_date", "end_date"):
        df[col] = pd.to_datetime(df[col])
    return df


def load_placebo_dates():
    profiles = pd.read_csv(PROFILES_CSV, dtype=str, usecols=["author_id", "date_birth_placebo"])
    profiles = profiles.drop_duplicates(subset="author_id").set_index("author_id")
    return pd.to_datetime(profiles["date_birth_placebo"], utc=True).dt.tz_localize(None)


def check_window(df, placebo):
    """Check 1: authors whose window is shorter than 18 months each side of placebo birth."""
    print("\n--- Check 1: window length ---")
    windows = df.groupby("author_id")[["begin_date", "end_date"]].first()

    no_rows = placebo.index.difference(windows.index)
    print(f"Input authors: {len(placebo):,}  |  with volume rows: {len(windows):,}  |  no rows: {len(no_rows):,}")

    # Shortened = begin_date clamped forward to account creation
    expected_begin = (placebo - pd.DateOffset(months=WINDOW_MONTHS)).dt.normalize()
    windows["expected_begin"] = expected_begin.reindex(windows.index)
    windows["window_weeks"]   = (windows["end_date"] - windows["begin_date"]).dt.days / 7
    short = windows[windows["begin_date"] > windows["expected_begin"]]

    print(f"Authors with shortened window (< {WEEKS_IN_SAMPLE} weeks): {len(short):,} of {len(windows):,}")
    if len(short):
        print("Window weeks among shortened authors:")
        print(short["window_weeks"].describe(percentiles=PCTS).round(1).to_string())
    return windows


def check_coverage(df, windows):
    """Check 2: days with data vs. days in each author's window."""
    print("\n--- Check 2: day coverage ---")
    n_dupes = df.duplicated(subset=["author_id", "date"]).sum()
    print(f"Duplicate author-date rows: {n_dupes:,}")

    n_days       = df.groupby("author_id")["date"].nunique()
    window_days  = (windows["end_date"] - windows["begin_date"]).dt.days
    missing_days = (window_days - n_days).clip(lower=0)

    print(f"Authors missing any days in their window: {(missing_days > 0).sum():,} of {len(n_days):,}")
    if (missing_days > 0).any():
        print("Missing days among those authors:")
        print(missing_days[missing_days > 0].describe(percentiles=PCTS).round(1).to_string())


def check_daily_counts(df):
    """Check 3: distribution of daily counts, extreme values, all-zero authors."""
    print("\n--- Check 3: daily counts ---")
    print("Daily og/qt tweets (author-days):")
    print(df["original_quote_count"].describe(percentiles=PCTS).round(2).to_string())

    totals = df.groupby("author_id")["original_quote_count"].sum()
    print(f"\nAuthors with zero tweets across the whole window: {(totals == 0).sum():,} of {len(totals):,}")

    print("\nTop 5 authors by single-day max:")
    print(df.groupby("author_id")["original_quote_count"].max().nlargest(5).to_string())


def summarize_weekly(df):
    """Weekly tweets: per-author average (total / 156) and per author-week."""
    print("\n--- Weekly tweets ---")
    totals = df.groupby("author_id")["original_quote_count"].sum()
    weekly = (totals / WEEKS_IN_SAMPLE).rename("og_qt_weekly_sample_tweets")
    print(f"Per-author average weekly tweets (total / {WEEKS_IN_SAMPLE}):")
    print(weekly.describe(percentiles=PCTS).round(2).to_string())

    # Week 0 = each author's begin_date
    week = (df["date"] - df["begin_date"]).dt.days // 7
    author_weeks = df.groupby(["author_id", week])["original_quote_count"].sum()
    print("\nTweets per author-week:")
    print(author_weeks.describe(percentiles=PCTS).round(2).to_string())
    return weekly


def main():
    df      = load_volume()
    placebo = load_placebo_dates()

    windows = check_window(df, placebo)
    check_coverage(df, windows)
    check_daily_counts(df)
    weekly = summarize_weekly(df)

    # --- Trim ---
    keep_ids    = weekly[weekly < FILTER_CUTOFF].index
    filtered_df = df[df["author_id"].isin(keep_ids)].copy()
    filtered_df.to_csv(FILTERED_CSV, index=False)
    filtered_df.to_stata(FILTERED_DTA, write_index=False)

    print(f"\n--- Trim: og_qt_weekly_sample_tweets < {FILTER_CUTOFF} (treatment 95th pct) ---")
    print(f"Input authors: {len(weekly):,}  |  pass trim: {len(keep_ids):,}")
    print(f"Saved to {FILTERED_CSV}")
    print(f"Saved to {FILTERED_DTA}")


if __name__ == "__main__":
    main()
