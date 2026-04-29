# Author: Hannah Lybbert
# Created: 2026-03-30
# Updated: 2026-04-07
# Purpose: Filter birth_detection_2_3M_GPT4o_full.csv to birth_flag == 1 and merge in 2.3M post metadata

import pandas as pd
from pathlib import Path

ROOT           = Path(__file__).resolve().parents[5]
INPUT_LLM      = ROOT / "Reddit/data/LLM/birth_detection_2_3M_GPT4o_full.csv"
INPUT_META     = ROOT / "Reddit/data/intermediate/cleaned_raw/reddit_parenting_2_3M_sample.parquet"
OUTPUT         = ROOT / "Reddit/data/intermediate/llm_births/births_2_3M_sample.csv"
OUTPUT_100     = ROOT / "Reddit/data/intermediate/llm_births/births_2_3M_100_sample.csv"
OUTPUT_AUTHORS = ROOT / "Reddit/data/intermediate/llm_births/authors_2_3M_sample.csv"

# Load and filter to births, then merge metadata
llm    = pd.read_csv(INPUT_LLM)
births = llm[llm["birth_flag"] == 1].drop(columns=["birth_flag"])

meta   = pd.read_parquet(INPUT_META)
births = meta.merge(births, on="id", how="inner")

# ----------------------------------------------------------------
# 1. Rename days_from_birth → days_from
# ----------------------------------------------------------------
births = births.rename(columns={"days_from_birth": "days_from"})

# ----------------------------------------------------------------
# 4. Drop rows with days_from outside [-28, 28] (removes -999s and outliers)
# ----------------------------------------------------------------
before = len(births)
births = births[births["days_from"].between(-28, 28)]
print(f"  Dropped {before - len(births):,} rows with days_from outside [-28, 28] (including -999s)")

# ----------------------------------------------------------------
# 2. Assign birth_post: 1 for exactly one post per author (the best
#    candidate birth post), 0 for all others.
#    Priority: (1) valid days_from != -999 over -999
#              (2) among valid, minimum abs(days_from)
#              (3) if all -999, keep latest post (max created_utc)
#    Note: window filter above removes all -999s in practice;
#          criteria (1) and (3) are retained as defensive code.
# ----------------------------------------------------------------
valid   = births[births["days_from"] != -999].copy()
invalid = births[births["days_from"] == -999].copy()

valid["_abs_days"] = valid["days_from"].abs()
valid_best = (valid.sort_values("_abs_days")
                   .drop_duplicates(subset="author", keep="first")
                   .drop(columns="_abs_days"))

invalid_only = invalid[~invalid["author"].isin(valid_best["author"])]
invalid_best = (invalid_only.sort_values("created_utc")
                            .drop_duplicates(subset="author", keep="last"))

n_crit2 = len(valid_best)
n_crit3 = len(invalid_best)

birth_post_ids       = set(valid_best["id"]) | set(invalid_best["id"])
births["birth_post"] = births["id"].isin(birth_post_ids).astype(int)

births = births.sort_values(["author", "created_utc"]).reset_index(drop=True)

# ----------------------------------------------------------------
# 3. Strip newlines from string columns to prevent CSV import issues
# ----------------------------------------------------------------
str_cols = births.select_dtypes(include="object").columns
for col in str_cols:
    births[col] = births[col].apply(lambda x: x.replace("\n", " ").replace("\r", " ") if isinstance(x, str) else x)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
births.to_csv(OUTPUT, index=False)

dup_authors = births.loc[births["birth_post"] == 0, "author"].nunique()
dup_ids     = births["id"].duplicated().sum()
print(f"Births extracted: {len(births):,} of {len(llm):,} LLM rows")
print(f"Unique authors: {births['author'].nunique():,}")
print(f"Authors with multiple birth posts: {dup_authors:,}")
print(f"Duplicate post IDs: {dup_ids:,}")
print(f"  Birth post assigned via criteria (2) — min abs(days_from): {n_crit2:,} authors")
print(f"  Birth post assigned via criteria (3) — all -999, latest post: {n_crit3:,} authors")
print(f"Saved to {OUTPUT}")

# # Save 100-row test sample
# sample_cols = ["id", "author", "subreddit", "created_utc", "title", "selftext",
#                "days_from", "confidence", "p_female", "p_male"]
# sample_cols = [c for c in sample_cols if c in births.columns]

# sample = births[sample_cols].sample(n=min(100, len(births)), random_state=42).copy()
# sample["created_utc"] = pd.to_datetime(sample["created_utc"], unit="s").dt.strftime("%m/%d/%Y")
# sample = sample.rename(columns={"created_utc": "created_at"})

# OUTPUT_100.parent.mkdir(parents=True, exist_ok=True)
# sample.to_csv(OUTPUT_100, index=False)
# print(f"100-row sample saved to {OUTPUT_100}")

# ----------------------------------------------------------------
# Authors file: one row per author (their birth_post == 1 row).
# birth_post == 1 is now assigned above via the three-tier priority
# logic, which replicates the original dedup logic below (now commented).
# ----------------------------------------------------------------
authors = births[births["birth_post"] == 1].copy()
authors = authors.sort_values("author").reset_index(drop=True)

# Original dedup logic (superseded by birth_post assignment above):
# valid   = births[births["days_from"] != -999].copy()
# invalid = births[births["days_from"] == -999].copy()
# valid["_abs_days"] = valid["days_from"].abs()
# valid_best = (valid.sort_values("_abs_days")
#                    .drop_duplicates(subset="author", keep="first")
#                    .drop(columns="_abs_days"))
# invalid_only = invalid[~invalid["author"].isin(valid_best["author"])]
# invalid_best = (invalid_only.sort_values("created_utc")
#                             .drop_duplicates(subset="author", keep="last"))
# authors = pd.concat([valid_best, invalid_best], ignore_index=True)
# authors = authors.sort_values("author").reset_index(drop=True)

OUTPUT_AUTHORS.parent.mkdir(parents=True, exist_ok=True)
authors.to_csv(OUTPUT_AUTHORS, index=False)
print(f"Authors file saved to {OUTPUT_AUTHORS} ({len(authors):,} unique authors)")
