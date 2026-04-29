# Author: Hannah Lybbert
# Created: 2026-03-18
# Updated: 2026-03-18
# Purpose: Create small test samples from cleaned Reddit data for LLM prompt testing and validation

import os
import pandas as pd

os.chdir("D:/TwitterBirth")

# --- Paths ---
INPUT_PATH       = "Reddit/data/intermediate/cleaned_raw/reddit_cleaned_2006_to_2018.csv"
TEST_PATH        = "Reddit/data/intermediate/cleaned_raw/test_samples/reddit_test_100_sample.csv"
MINI_TEST_PATH   = "Reddit/data/intermediate/cleaned_raw/test_samples/reddit_mini_20_test_sample.csv"
SECOND_TEST_PATH = "Reddit/data/intermediate/cleaned_raw/test_samples/reddit_2nd_test_100_sample.csv"

# --- Random seeds ---
RANDOM_SEED = 42
SECOND_SEED = 99

# Load cleaned data
print(f"Loading {INPUT_PATH}...")
df = pd.read_csv(INPUT_PATH, encoding="utf-8", low_memory=False)
print(f"  Loaded {len(df):,} rows")

# Save a 100-row test sample for LLM testing
os.makedirs(os.path.dirname(TEST_PATH), exist_ok=True)
df.sample(n=100, random_state=RANDOM_SEED).to_csv(TEST_PATH, index=False, encoding="utf-8")
print(f"Test sample saved to {TEST_PATH}")

# Save a 20-row mini test sample for prompt iteration
df.sample(n=20, random_state=RANDOM_SEED).to_csv(MINI_TEST_PATH, index=False, encoding="utf-8")
print(f"Mini test sample saved to {MINI_TEST_PATH}")

# Save a second 100-row test sample for LLM testing (different seed for variety)
df.sample(n=100, random_state=SECOND_SEED).to_csv(SECOND_TEST_PATH, index=False, encoding="utf-8")
print(f"Second test sample saved to {SECOND_TEST_PATH}")
