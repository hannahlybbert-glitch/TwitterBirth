# Author: Hannah Lybbert
# Created: 2026-03-24
# Updated: 2026-04-07
# Purpose: Filter birth_detection_190k_births_GPT4o.csv to birth_flag == 1 and merge in 190k births metadata

import pandas as pd
from pathlib import Path

# Paths relative to project root (D:/TwitterBirth)
ROOT        = Path(__file__).resolve().parents[5]
INPUT_LLM   = ROOT / "Reddit/data/LLM/birth_detection_190k_births_GPT4o.csv"
INPUT_META  = ROOT / "Reddit/data/intermediate/llm_births/births_190k_sample.csv"
OUTPUT      = ROOT / "Reddit/data/intermediate/llm_births/births_22k_sample.csv"
OUTPUT_100  = ROOT / "Reddit/data/intermediate/cleaned_raw/test_samples/births_22k_100_sample.csv"

RANDOM_SEED = 42

# Load and filter to births first, then merge metadata
llm    = pd.read_csv(INPUT_LLM)
births = llm[llm["birth_flag"] == 1].drop(columns=["birth_flag"])

meta   = pd.read_csv(INPUT_META)
births = meta.merge(births, on="id", how="inner")

births = births.rename(columns={"days_from_birth": "days_from"})

# Drop observations outside plausible birth-post window (also removes -999 sentinels)
before = len(births)
births = births[births["days_from"].between(-28, 28)]
print(f"  Dropped {before - len(births):,} rows with days_from outside [-28, 28] (including -999s)")

# Drop m_ columns (from 190k parenting run) before saving
m_cols = [c for c in births.columns if c.startswith("m_")]
births = births.drop(columns=m_cols)

births = births.sort_values(["author", "created_utc"]).reset_index(drop=True)

# Strip newlines from string columns to prevent CSV import issues in Stata
str_cols = births.select_dtypes(include="object").columns
for col in str_cols:
    births[col] = births[col].apply(lambda x: x.replace("\n", " ").replace("\r", " ") if isinstance(x, str) else x)

# ----------------------------------------------------------------
# Assign birth_post: 1 for exactly one post per author (the best
# candidate birth post), 0 for all others.
# Priority: (1) valid days_from != -999 over -999
#           (2) among valid, minimum abs(days_from)
#           (3) if all -999, keep latest post (max created_utc)
# Note: window filter above removes all -999s in practice;
#       criteria (1) and (3) are retained as defensive code.
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

# Save 100-row test sample (subset of columns)
# sample_cols = ["id", "author", "subreddit", "created_utc", "title", "selftext",
#                "days_from", "confidence", "p_female", "p_male"]
# sample_cols = [c for c in sample_cols if c in births.columns]

# sample = births[sample_cols].sample(n=min(100, len(births)), random_state=RANDOM_SEED).copy()
# sample["created_utc"] = pd.to_datetime(sample["created_utc"], unit="s").dt.strftime("%m/%d/%Y")
# sample = sample.rename(columns={"created_utc": "created_at"})

# OUTPUT_100.parent.mkdir(parents=True, exist_ok=True)
# sample.to_csv(OUTPUT_100, index=False)
# print(f"100-row sample saved to {OUTPUT_100}")
