# Author: Hannah Lybbert
# Created: 2026-03-25
# Updated: 2026-04-03
# Purpose: Clean raw Reddit placebo sample submissions, drop bot/hyper-prolific authors, and save full cleaned dataset

import os
import pandas as pd

os.chdir("D:/TwitterBirth")

# --- Paths ---
INPUT_PATH   = "Reddit/raw/placebo_matched_submissions.csv"
OUTPUT_PQRT  = "Reddit/data/intermediate/cleaned_raw/reddit_placebo_cleaned.parquet"
OUTPUT_CSV   = "Reddit/data/intermediate/cleaned_raw/reddit_placebo_cleaned.csv"

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

# ----------------------------------------------------------------
# 6. Drop top 5% of authors by average posts per month (bots / hyper-prolific)
# ----------------------------------------------------------------
df["_year_month"] = pd.to_datetime(df["created_utc"], unit="s").dt.to_period("M")
monthly_posts     = df.groupby(["author", "_year_month"]).size().reset_index(name="_monthly_posts")
avg_posts_month   = monthly_posts.groupby("author")["_monthly_posts"].mean()
threshold         = avg_posts_month.quantile(0.95)
keep_authors      = avg_posts_month[avg_posts_month <= threshold].index
before            = len(df)
df = df[df["author"].isin(keep_authors)].drop(columns=["_year_month"])
print(f"  After dropping top 5%% posters (>{threshold:.1f} posts/month): {len(df):,}  (removed {before - len(df):,} rows, {df['author'].nunique():,} authors remain)")

# ----------------------------------------------------------------
# 7. Sort by author and created_utc
# ----------------------------------------------------------------
df = df.sort_values(["author", "created_utc"]).reset_index(drop=True)

# ----------------------------------------------------------------
# 7. Save
# ----------------------------------------------------------------
os.makedirs(os.path.dirname(OUTPUT_PQRT), exist_ok=True)
df.to_parquet(OUTPUT_PQRT, index=False)
df.to_csv(OUTPUT_CSV, index=False)
print(f"\nDone. Saved {len(df):,} rows to:")
print(f"  {OUTPUT_PQRT}")
print(f"  {OUTPUT_CSV}")

# ----------------------------------------------------------------
# Summary
# ----------------------------------------------------------------
print("\n" + "=" * 50)
print("SUMMARY")
print("=" * 50)
print(f"Total rows ready for analysis:  {len(df):,}")
print(f"Unique authors:                 {df['author'].nunique():,}")

# Average rows per author
avg_rows = df.groupby("author").size().mean()
print(f"Avg posts per author:           {avg_rows:.2f}")

# Average time span per author (days between first and last post)
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
