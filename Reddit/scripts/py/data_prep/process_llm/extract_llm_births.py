# Author: Hannah Lybbert
# Created: 2026-03-16
# Updated: 2026-03-20
# Purpose: Filter birth_detection_large_sample.csv to birth_flag == 1 and merge in post metadata

import pandas as pd
from pathlib import Path

# Paths relative to project root (D:/TwitterBirth)
ROOT        = Path(__file__).resolve().parents[5]
INPUT_LLM   = ROOT / "Reddit/data/LLM/birth_detection_large_sample.csv"
INPUT_META  = ROOT / "Reddit/data/intermediate/cleaned_raw/reddit_30k_sample.csv"
OUTPUT      = ROOT / "Reddit/data/intermediate/llm_births/births_30k_sample.csv"

# Load and filter to births
llm = pd.read_csv(INPUT_LLM)
births = llm[llm["birth_flag"] == 1].drop(columns=["birth_flag"])

# Merge in post metadata
meta = pd.read_csv(INPUT_META, usecols=["id", "author", "subreddit", "year_month", "title", "selftext"])
births = births.merge(meta, on="id", how="left")

births = births.rename(columns={"days_from_birth": "days_from"})

births = births[["id", "author", "subreddit", "year_month", "title", "selftext",
                 "days_from", "confidence", "p_female", "p_male"]]

# Flag authors with multiple birth posts
births["dup"] = births["author"].duplicated(keep=False).astype(int)

# Sort by author then year_month; assign birth_post == 1 only to the last row per author
births = births.sort_values(["author", "year_month"]).reset_index(drop=True)
births["birth_post"] = (~births.duplicated(subset="author", keep="last")).astype(int)

births.to_csv(OUTPUT, index=False)

dup_authors = births["author"].dropna().duplicated().sum()
dup_ids     = births["id"].duplicated().sum()
print(f"Births extracted: {len(births):,} of {len(llm):,} rows")
print(f"Unique author births: {(births['birth_post'] == 1).sum():,}")
print(f"Authors with multiple birth posts: {dup_authors:,}")
print(f"Duplicate post IDs: {dup_ids:,}")
print(f"Saved to {OUTPUT}")
