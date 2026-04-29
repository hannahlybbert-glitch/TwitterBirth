# Author: Hannah Lybbert
# Created: 02/09/2026
# Updated: 2026-03-17
# Purpose: Clean raw Reddit data and save full cleaned dataset and large LLM sample

import os
import pandas as pd

os.chdir("D:/TwitterBirth")

# --- Paths ---
INPUT_PATH        = "Reddit/raw/reddit_data_2006_01_to_2018_12.csv"
OUTPUT_PATH       = "Reddit/data/intermediate/cleaned_raw/reddit_cleaned_2006_to_2018.csv"
LARGE_SAMPLE_PATH = "Reddit/data/intermediate/cleaned_raw/reddit_30k_sample.csv"

# --- Optional random sample (set to None to keep all rows) ---
SAMPLE_N    = None
RANDOM_SEED = 42

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
print(f"Loading {INPUT_PATH}...")
df = pd.read_csv(INPUT_PATH, encoding="utf-8", low_memory=False)
print(f"  Raw rows: {len(df):,}")

# ----------------------------------------------------------------
# 1. Drop null / [deleted] / [removed] authors — can't track across time without author
# ----------------------------------------------------------------
before = len(df)
df = df[df["author"].notna() & ~df["author"].str.strip().isin(["[deleted]", "[removed]", ""])]
print(f"  After dropping deleted authors:        {len(df):,}  (removed {before - len(df):,})")

# ----------------------------------------------------------------
# 2. Normalise selftext and title — treat [deleted] / [removed] as empty
# ----------------------------------------------------------------
def clean_text_field(val):
    val = str(val).strip() if pd.notna(val) else ""
    return "" if val in ("[deleted]", "[removed]") else val

df["selftext"] = df["selftext"].apply(clean_text_field)
df["title"]    = df["title"].apply(clean_text_field)

# ----------------------------------------------------------------
# 3. Drop rows where both title and selftext are empty
# ----------------------------------------------------------------
before = len(df)
df = df[~((df["title"] == "") & (df["selftext"] == ""))]
print(f"  After dropping rows with no content:   {len(df):,}  (removed {before - len(df):,})")

# ----------------------------------------------------------------
# 4. Select output columns
# ----------------------------------------------------------------
df = df[["id", "author", "subreddit", "year_month", "title", "selftext"]].copy()

# ----------------------------------------------------------------
# 5. Optional sample
# ----------------------------------------------------------------
if SAMPLE_N is not None and SAMPLE_N < len(df):
    df = df.sample(n=SAMPLE_N, random_state=RANDOM_SEED).reset_index(drop=True)
    print(f"  After sampling {SAMPLE_N:,} rows:             {len(df):,}")

# ----------------------------------------------------------------
# 6. Save
# ----------------------------------------------------------------
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
print(f"\nDone. Saved {len(df):,} rows to {OUTPUT_PATH}")

# ----------------------------------------------------------------
# 7. Save large LLM sample (30,000 rows — ~10% hit rate targets ~3,000 birth announcements)
# ----------------------------------------------------------------
LARGE_SAMPLE_N = 30_000
large_sample = df.sample(n=min(LARGE_SAMPLE_N, len(df)), random_state=RANDOM_SEED).reset_index(drop=True)
large_sample.to_csv(LARGE_SAMPLE_PATH, index=False, encoding="utf-8")
print(f"Large LLM sample ({len(large_sample):,} rows, target {LARGE_SAMPLE_N:,}) saved to {LARGE_SAMPLE_PATH}")

# ----------------------------------------------------------------
# Summary
# ----------------------------------------------------------------
print("\n" + "=" * 50)
print("SUMMARY")
print("=" * 50)
print(f"Total rows ready for analysis:  {len(df):,}")
print(f"\nSubreddit breakdown:")
for sub, cnt in df["subreddit"].value_counts().items():
    print(f"  {sub:35s}: {cnt:7,}")
ym = df["year_month"].dropna()
print(f"\nDate range:  {ym.min()}  to  {ym.max()}")
print(f"Unique authors: {df['author'].nunique():,}")
