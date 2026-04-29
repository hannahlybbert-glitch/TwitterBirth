# Author: Hannah Lybbert
# Created: 2026-03-23
# Updated: 2026-03-26
# Purpose: Filter birth_detection_parenting_sample.csv to birth_flag == 1 and merge in 190k post metadata

import pandas as pd
from pathlib import Path

# Paths relative to project root (D:/TwitterBirth)
ROOT        = Path(__file__).resolve().parents[5]
INPUT_LLM   = ROOT / "Reddit/data/LLM/birth_detection_parenting_sample.csv"
INPUT_META  = ROOT / "Reddit/data/intermediate/cleaned_raw/reddit_parenting_190k_sample.csv"
OUTPUT      = ROOT / "Reddit/data/intermediate/llm_births/births_190k_sample.csv"

# Load and filter to births first, then merge metadata
llm    = pd.read_csv(INPUT_LLM)
births = llm[llm["birth_flag"] == 1].drop(columns=["birth_flag"])

meta   = pd.read_csv(INPUT_META)
births = meta.merge(births, on="id", how="inner")

births = births.rename(columns={
    "days_from_birth": "m_days_from",
    "confidence":      "m_confidence",
    "p_female":        "m_p_female",
    "p_male":          "m_p_male",
})

births = births.sort_values(["author", "created_utc"]).reset_index(drop=True)
births["dup"] = births["author"].duplicated(keep=False).astype(int)

OUTPUT_100 = ROOT / "Reddit/data/intermediate/llm_births/births_190k_100_sample.csv"

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
births.to_csv(OUTPUT, index=False)

# Save 100-row test sample (subset of columns)
sample_cols = ["id", "author", "subreddit", "created_utc", "title", "selftext",
               "m_days_from", "m_confidence", "m_p_female", "m_p_male"]
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
