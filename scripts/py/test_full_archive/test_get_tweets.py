import pandas as pd
from datetime import datetime
import os

# === SETTINGS ===
COUNTS_CSV = "data/raw/tweet_volume_by_user_2013_2017.csv"
ENCODING = "utf-8"

# === LOAD DATA ===
df = pd.read_csv(COUNTS_CSV, encoding=ENCODING)
print(f"Loaded {len(df)} rows from: {COUNTS_CSV}")

# === GROUP + SUM ===
group_cols = ['unique_id', 'author_id', 'user_created_at', 'date_birth', 'begin_date', 'end_date']
numeric_cols = df.select_dtypes(include="number").columns.tolist()

if "date" in df.columns:
    df = df.drop(columns=["date"])

collapsed_df = df.groupby(group_cols, as_index=False)[numeric_cols].sum()
print(f"After grouping: {len(collapsed_df)} unique users")

# === CONVERT DATES ===
collapsed_df["date_birth_dt"] = pd.to_datetime(collapsed_df["date_birth"], errors="coerce")
collapsed_df["user_created_at_dt"] = pd.to_datetime(collapsed_df["user_created_at"], errors="coerce")

# === FILTER 1: PRE-PERIOD >= 546 DAYS ===
collapsed_df["days_pre_period"] = (collapsed_df["date_birth_dt"] - collapsed_df["user_created_at_dt"]).dt.days
print("\n--- Pre-period (days before birth) ---")
print(collapsed_df["days_pre_period"].describe())

pre_period_filtered = collapsed_df[collapsed_df["days_pre_period"] >= 546]
print(f"Users remaining after pre-period filter: {len(pre_period_filtered)}")

# === FILTER 2: TWEET COUNT >= 50 ===
print("\n--- Tweet count ---")
print(pre_period_filtered["tweet_count"].describe())

tweet_count_filtered = pre_period_filtered[pre_period_filtered["tweet_count"] >= 50]
print(f"Users remaining after tweet count filter: {len(tweet_count_filtered)}")

# === FILTER 3: CUMSUM AGAINST QUOTA ===
quota = 1_000_000
tweet_count_filtered = tweet_count_filtered.sort_values("tweet_count")
tweet_count_filtered["cumsum"] = tweet_count_filtered["tweet_count"].cumsum()

final_df = tweet_count_filtered[tweet_count_filtered["cumsum"] <= quota]
print(f"\nUsers remaining after applying quota: {len(final_df)}")

# === OPTIONAL: View example output ===
print("\n--- Sample remaining users ---")
print(final_df[["author_id", "tweet_count", "days_pre_period"]].head())
