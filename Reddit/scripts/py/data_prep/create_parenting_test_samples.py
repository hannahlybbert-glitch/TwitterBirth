# Author: Hannah Lybbert
# Created: 2026-03-18
# Updated: 2026-03-23
# Purpose: Create test samples and large LLM sample from cleaned Reddit parenting submissions

import os
import pandas as pd

os.chdir("D:/TwitterBirth")

# --- Paths ---
INPUT_PATH        = "Reddit/data/intermediate/cleaned_raw/reddit_parenting_full_cleaned.parquet"
TEST_PATH         = "Reddit/data/intermediate/cleaned_raw/test_samples/reddit_parenting_100_sample.csv"
SAMPLE_190k_PATH = "Reddit/data/intermediate/cleaned_raw/reddit_parenting_190k_sample.parquet"
SAMPLE_190k_CSV_PATH = "Reddit/data/intermediate/cleaned_raw/reddit_parenting_190k_sample.csv"

# --- Random seed ---
RANDOM_SEED = 42

# Load cleaned data
print(f"Loading {INPUT_PATH}...")
df = pd.read_parquet(INPUT_PATH)
print(f"  Loaded {len(df):,} rows")

# Save a 100-row test sample
os.makedirs(os.path.dirname(TEST_PATH), exist_ok=True)
df.sample(n=100, random_state=RANDOM_SEED)[["id", "author", "subreddit", "title", "selftext"]].to_csv(TEST_PATH, index=False, encoding="utf-8")
print(f"Test sample saved to {TEST_PATH}")

# Save large LLM sample (190,000 rows)
LARGE_SAMPLE_N = 190_000
large_sample = df.sample(n=min(LARGE_SAMPLE_N, len(df)), random_state=RANDOM_SEED).reset_index(drop=True)
large_sample.to_parquet(SAMPLE_190k_PATH, index=False)
print(f"Large LLM sample ({len(large_sample):,} rows, target {LARGE_SAMPLE_N:,}) saved to {SAMPLE_190k_PATH}")
large_sample.to_csv(SAMPLE_190k_CSV_PATH, index=False, encoding="utf-8")
print(f"Large LLM sample also saved as CSV to {SAMPLE_190k_CSV_PATH}")