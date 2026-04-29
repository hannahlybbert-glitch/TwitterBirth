# Author: Hannah Lybbert
# Created: 2026-04-10
# Updated: 2026-04-10
# Purpose: Clean matched placebo birth posts — steps 1-5, 7 from clean_placebo_sample_post_history.py (no top-5% drop)

import pandas as pd
from pathlib import Path

ROOT   = Path(__file__).resolve().parents[5]
INPUT  = ROOT / "Reddit/raw/matched_placebo_treatment_posts_jul2023.csv"
OUTPUT = ROOT / "Reddit/data/intermediate/cleaned_raw/matched_placebo_birth_posts_clean.csv"

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
print(f"Loading {INPUT}...")
df = pd.read_csv(INPUT, encoding="utf-8", engine="python")
print(f"  Raw rows: {len(df):,}")

# ----------------------------------------------------------------
# 1. Drop null / [deleted] / [removed] authors
# ----------------------------------------------------------------
before = len(df)
df = df[df["author"].notna() & ~df["author"].str.strip().isin(["[deleted]", "[removed]", ""])]
print(f"  After dropping deleted authors:        {len(df):,}  (removed {before - len(df):,})")

# ----------------------------------------------------------------
# 2. Drop rows with null id
# ----------------------------------------------------------------
before = len(df)
df = df[df["id"].notna()]
print(f"  After dropping null ids:               {len(df):,}  (removed {before - len(df):,})")

# ----------------------------------------------------------------
# 3. Normalise selftext and title — treat [deleted] / [removed] as empty
# ----------------------------------------------------------------
def clean_text_field(val):
    val = str(val).strip() if pd.notna(val) else ""
    val = "" if val in ("[deleted]", "[removed]") else val
    return val.replace("\n", " ").replace("\r", " ")

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

# Step 6 skipped — do not drop top 5% of authors (one post per author; cutoff not meaningful here)

# ----------------------------------------------------------------
# 7. Sort by author and created_utc
# ----------------------------------------------------------------
df = df.sort_values(["author", "created_utc"]).reset_index(drop=True)

# ----------------------------------------------------------------
# Save
# ----------------------------------------------------------------
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUTPUT, index=False)
print(f"\nDone. Saved {len(df):,} rows to {OUTPUT}")
print(f"  Unique authors: {df['author'].nunique():,}")
