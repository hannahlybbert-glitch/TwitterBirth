# Author: Hannah Lybbert
# Created: 2026-04-10
# Updated: 2026-04-10
# Purpose: Clean matched placebo submission history — steps 1-5, 7 from clean_placebo_sample_post_history.py (no top-5% drop)

import pandas as pd
from pathlib import Path

ROOT      = Path(__file__).resolve().parents[5]
INPUT     = ROOT / "Reddit/raw/matched_placebo_submissions_jul2023.csv"
OUTPUT    = ROOT / "Reddit/data/intermediate/cleaned_raw/matched_placebo_post_history_clean.csv"
CHUNKSIZE = 100_000

KEEP_COLS = ["id", "author", "subreddit", "created_utc", "title", "selftext",
             "url", "score", "num_comments", "over_18", "stickied", "locked", "permalink"]

def clean_text_field(val):
    val = str(val).strip() if pd.notna(val) else ""
    val = "" if val in ("[deleted]", "[removed]") else val
    return val.replace("\n", " ").replace("\r", " ")

# ----------------------------------------------------------------
# Read in chunks (C engine — no field size limit) and clean row-by-row
# Steps 1-5 are all row-level so they can run per chunk
# ----------------------------------------------------------------
print(f"Loading {INPUT} in chunks of {CHUNKSIZE:,}...")
chunks      = []
raw_rows    = 0
after_auth  = 0
after_id    = 0
after_empty = 0

for chunk in pd.read_csv(INPUT, encoding="utf-8", engine="c",
                          on_bad_lines="warn", chunksize=CHUNKSIZE):
    raw_rows += len(chunk)

    # 1. Drop null / [deleted] / [removed] authors — can't track across time without author
    chunk = chunk[chunk["author"].notna() & ~chunk["author"].str.strip().isin(["[deleted]", "[removed]", ""])]
    after_auth += len(chunk)

    # 2. Drop rows with null id
    chunk = chunk[chunk["id"].notna()]
    after_id += len(chunk)

    # 3. Normalise selftext and title — treat [deleted] / [removed] as empty
    chunk["selftext"] = chunk["selftext"].apply(clean_text_field)
    chunk["title"]    = chunk["title"].apply(clean_text_field)

    # 4. Drop rows where both title and selftext are empty
    chunk = chunk[~((chunk["title"] == "") & (chunk["selftext"] == ""))]
    after_empty += len(chunk)

    # 5. Select output columns
    chunk = chunk[[c for c in KEEP_COLS if c in chunk.columns]].copy()

    chunks.append(chunk)

df = pd.concat(chunks, ignore_index=True)
print(f"  Raw rows:                              {raw_rows:,}")
print(f"  After dropping deleted authors:        {after_auth:,}  (removed {raw_rows - after_auth:,})")
print(f"  After dropping null ids:               {after_id:,}  (removed {after_auth - after_id:,})")
print(f"  After dropping rows with no content:   {after_empty:,}  (removed {after_id - after_empty:,})")

# Step 6 skipped — do not drop top 5% of authors (matched authors are pre-selected; dropping would break pairs)

# ----------------------------------------------------------------
# 7. Sort by author and created_utc
# ----------------------------------------------------------------
print("Sorting...")
df = df.sort_values(["author", "created_utc"]).reset_index(drop=True)

# ----------------------------------------------------------------
# Save
# ----------------------------------------------------------------
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUTPUT, index=False)

# ----------------------------------------------------------------
# Summary
# ----------------------------------------------------------------
print(f"\nDone. Saved {len(df):,} rows to {OUTPUT}")
print("\n" + "=" * 50)
print("SUMMARY")
print("=" * 50)
print(f"Total rows ready for analysis:  {len(df):,}")
print(f"Unique authors:                 {df['author'].nunique():,}")

avg_rows = df.groupby("author").size().mean()
print(f"Avg posts per author:           {avg_rows:.2f}")

author_spans = df.groupby("author")["created_utc"].agg(["min", "max"])
author_spans["span_days"] = (author_spans["max"] - author_spans["min"]) / 86400
avg_span = author_spans["span_days"].mean()
print(f"Avg author time span (days):    {avg_span:.1f}")

print(f"\nTop 25 subreddits by posts:")
top_subs = df["subreddit"].value_counts().head(25).reset_index()
top_subs.columns = ["subreddit", "posts"]
top_subs["pct"] = (top_subs["posts"] / len(df) * 100).round(2)
for _, row in top_subs.iterrows():
    print(f"  {row['subreddit']:35s}: {row['posts']:7,}  ({row['pct']:.2f}%)")
