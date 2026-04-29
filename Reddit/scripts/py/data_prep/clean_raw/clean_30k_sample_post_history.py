# Author: Hannah Lybbert
# Created: 2026-03-19
# Updated: 2026-03-19
# Purpose: Clean raw Reddit births sample submissions and save full cleaned dataset

import os
import re
import pandas as pd

os.chdir("D:/TwitterBirth")

# --- Paths ---
INPUT_PATH  = "Reddit/raw/births_sample_submissions.csv"
OUTPUT_PATH = "Reddit/data/intermediate/cleaned_raw/reddit_30k_post_history_cleaned.csv"

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
print(f"Loading {INPUT_PATH}...")
df = pd.read_csv(INPUT_PATH, encoding="utf-8", low_memory=False)
print(f"  Raw rows: {len(df):,}")

# ----------------------------------------------------------------
# 1. Drop malformed rows — id must be a valid Reddit post ID (4–10 lowercase alphanumeric chars)
# ----------------------------------------------------------------
before = len(df)
valid_id_mask = df["id"].astype(str).str.match(r"^[a-z0-9]{4,10}$")
df = df[valid_id_mask].copy()
print(f"  After dropping malformed rows:         {len(df):,}  (removed {before - len(df):,})")

# ----------------------------------------------------------------
# 2. Drop null IDs — required for LLM batch processing
# ----------------------------------------------------------------
before = len(df)
df = df[df["id"].notna()]
print(f"  After dropping null ids:               {len(df):,}  (removed {before - len(df):,})")

# ----------------------------------------------------------------
# 3. Drop null / [deleted] / [removed] authors
# ----------------------------------------------------------------
before = len(df)
df = df[df["author"].notna() & ~df["author"].str.strip().isin(["[deleted]", "[removed]", ""])]
print(f"  After dropping deleted authors:        {len(df):,}  (removed {before - len(df):,})")

# ----------------------------------------------------------------
# 4. Normalise selftext and title — treat [deleted] / [removed] as empty
# ----------------------------------------------------------------
def clean_text_field(val):
    val = str(val).strip() if pd.notna(val) else ""
    return "" if val in ("[deleted]", "[removed]") else val

df["selftext"] = df["selftext"].apply(clean_text_field)
df["title"]    = df["title"].apply(clean_text_field)

# ----------------------------------------------------------------
# 5. Drop rows where both title and selftext are empty
# ----------------------------------------------------------------
before = len(df)
df = df[~((df["title"] == "") & (df["selftext"] == ""))]
print(f"  After dropping rows with no content:   {len(df):,}  (removed {before - len(df):,})")

# ----------------------------------------------------------------
# 6. Select output columns
# ----------------------------------------------------------------
df = df[["id", "author", "subreddit", "created_utc", "title", "selftext",
         "url", "score", "num_comments", "over_18", "stickied", "locked", "permalink"]].copy()

# ----------------------------------------------------------------
# 7. Save
# ----------------------------------------------------------------
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
print(f"\nDone. Saved {len(df):,} rows to {OUTPUT_PATH}")

# ----------------------------------------------------------------
# Summary
# ----------------------------------------------------------------
print("\n" + "=" * 50)
print("SUMMARY")
print("=" * 50)
print(f"Total rows ready for analysis:  {len(df):,}")
print(f"\nSubreddit breakdown:")
for sub, cnt in df["subreddit"].value_counts().head(15).items():
    print(f"  {sub:35s}: {cnt:7,}")
print(f"\nUnique authors: {df['author'].nunique():,}")
