# Author: Hannah Lybbert
# Created: 2026-03-30
# Updated: 2026-04-06
# Purpose: Filter birth_detection_2_3M_GPT4o_full.csv to birth_flag == 1 and merge in 2.3M post metadata

import pandas as pd
from pathlib import Path

ROOT        = Path(__file__).resolve().parents[5]
INPUT_LLM   = ROOT / "Reddit/data/LLM/birth_detection_2_3M_GPT4o_full.csv"
INPUT_META  = ROOT / "Reddit/data/intermediate/cleaned_raw/reddit_parenting_2_3M_sample.parquet"
OUTPUT         = ROOT / "Reddit/data/intermediate/llm_births/births_2_3M_sample.csv"
OUTPUT_100     = ROOT / "Reddit/data/intermediate/llm_births/births_2_3M_100_sample.csv"
OUTPUT_AUTHORS = ROOT / "Reddit/data/intermediate/llm_births/authors_2_3M_sample.csv"

# Load and filter to births, then merge metadata
llm    = pd.read_csv(INPUT_LLM)
births = llm[llm["birth_flag"] == 1].drop(columns=["birth_flag"])

meta   = pd.read_parquet(INPUT_META)
births = meta.merge(births, on="id", how="inner")

births = births.sort_values(["author", "created_utc"]).reset_index(drop=True)
births["dup"] = births["author"].duplicated(keep=False).astype(int)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
births.to_csv(OUTPUT, index=False)

# Save 100-row test sample
sample_cols = ["id", "author", "subreddit", "created_utc", "title", "selftext",
               "days_from_birth", "confidence", "p_female", "p_male"]
sample_cols = [c for c in sample_cols if c in births.columns]

sample = births[sample_cols].sample(n=min(100, len(births)), random_state=42).copy()
sample["created_utc"] = pd.to_datetime(sample["created_utc"], unit="s").dt.strftime("%m/%d/%Y")
sample = sample.rename(columns={"created_utc": "created_at"})

OUTPUT_100.parent.mkdir(parents=True, exist_ok=True)
sample.to_csv(OUTPUT_100, index=False)

dup_authors = births.loc[births["dup"] == 1, "author"].nunique()
dup_ids     = births["id"].duplicated().sum()
print(f"Births extracted: {len(births):,} of {len(llm):,} LLM rows")
print(f"Authors with multiple birth posts: {dup_authors:,}")
print(f"Duplicate post IDs: {dup_ids:,}")
print(f"Saved to {OUTPUT}")
print(f"100-row sample saved to {OUTPUT_100}")

# ----------------------------------------------------------------
# Deduplicate to one post per author (closest to birth)
# Priority: (1) valid days_from_birth != -999 over -999
#           (2) among valid, minimum abs(days_from_birth)
#           (3) if all -999, keep latest post (max created_utc)
# ----------------------------------------------------------------
valid   = births[births["days_from_birth"] != -999].copy()
invalid = births[births["days_from_birth"] == -999].copy()

# Among valid rows: keep the one with smallest abs(days_from_birth) per author
valid["_abs_days"] = valid["days_from_birth"].abs()
valid_best = (valid.sort_values("_abs_days")
                   .drop_duplicates(subset="author", keep="first")
                   .drop(columns="_abs_days"))

# Authors with no valid rows: keep the latest post
invalid_only = invalid[~invalid["author"].isin(valid_best["author"])]
invalid_best = (invalid_only.sort_values("created_utc")
                            .drop_duplicates(subset="author", keep="last"))

authors = pd.concat([valid_best, invalid_best], ignore_index=True)
authors = authors.sort_values("author").reset_index(drop=True)

OUTPUT_AUTHORS.parent.mkdir(parents=True, exist_ok=True)
authors.to_csv(OUTPUT_AUTHORS, index=False)
print(f"Authors file saved to {OUTPUT_AUTHORS} ({len(authors):,} unique authors)")
