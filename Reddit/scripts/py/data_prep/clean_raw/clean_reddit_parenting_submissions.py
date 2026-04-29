# Author: Hannah Lybbert
# Created: 2026-03-18
# Updated: 2026-03-20
# Purpose: Clean raw Reddit parenting submissions and save full cleaned dataset

import os
import pandas as pd

os.chdir("D:/TwitterBirth")

# --- Paths ---
INPUT_PATH  = "Reddit/raw/reddit_parenting_submissions.csv"
OUTPUT_PATH = "Reddit/data/intermediate/cleaned_raw/reddit_parenting_full_cleaned.parquet"

# --- Optional random sample (set to None to keep all rows) ---
SAMPLE_N    = None
RANDOM_SEED = 42

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
print(f"Loading {INPUT_PATH}...")
df = pd.read_csv(INPUT_PATH, encoding="utf-8", engine="python")
print(f"  Raw rows: {len(df):,}")

# ----------------------------------------------------------------
# 1. Drop null / [deleted] / [removed] authors — can't track across time without author
# ----------------------------------------------------------------
before = len(df)
df = df[df["author"].notna() & ~df["author"].str.strip().isin(["[deleted]", "[removed]", ""])]
print(f"  After dropping deleted authors:        {len(df):,}  (removed {before - len(df):,})")

# ----------------------------------------------------------------
# 2. Drop rows with null id — required for LLM batch processing
# ----------------------------------------------------------------
before = len(df)
df = df[df["id"].notna()]
print(f"  After dropping null ids:               {len(df):,}  (removed {before - len(df):,})")

# ----------------------------------------------------------------
# 3. Normalise selftext and title — treat [deleted] / [removed] as empty
# ----------------------------------------------------------------
def clean_text_field(val):
    val = str(val).strip() if pd.notna(val) else ""
    return "" if val in ("[deleted]", "[removed]") else val

df["selftext"] = df["selftext"].apply(clean_text_field)
df["title"]    = df["title"].apply(clean_text_field)

# ----------------------------------------------------------------
# 4. Drop rows where both title and selftext are empty
# ----------------------------------------------------------------
before = len(df)
df = df[~((df["title"] == "") & (df["selftext"] == ""))]
print(f"  After dropping rows with no content:   {len(df):,}  (removed {before - len(df):,})")

# ----------------------------------------------------------------
# 5. Select output columns
# ----------------------------------------------------------------
df = df[["id", "author", "subreddit", "created_utc", "title", "selftext",
         "url", "score", "num_comments", "over_18", "stickied", "locked", "permalink"]].copy()

# ----------------------------------------------------------------
# 6. Optional sample
# ----------------------------------------------------------------
if SAMPLE_N is not None and SAMPLE_N < len(df):
    df = df.sample(n=SAMPLE_N, random_state=RANDOM_SEED).reset_index(drop=True)
    print(f"  After sampling {SAMPLE_N:,} rows:             {len(df):,}")

# ----------------------------------------------------------------
# 7. Save
# ----------------------------------------------------------------
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
df.to_parquet(OUTPUT_PATH, index=False)
print(f"\nDone. Saved {len(df):,} rows to {OUTPUT_PATH}")

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
print(f"\nUnique authors: {df['author'].nunique():,}")
