# Author: Hannah Lybbert
# Created: 2026-03-23
# Updated: 2026-03-23# Purpose: Filter birth_detection_parenting_100.csv to birth_flag == 1 and merge in 100-row test sample metadata

import pandas as pd
from pathlib import Path

# Paths relative to project root (D:/TwitterBirth)
ROOT        = Path(__file__).resolve().parents[5]
INPUT_LLM   = ROOT / "Reddit/data/LLM/test_samples/birth_detection_parenting_100.csv"
INPUT_META  = ROOT / "Reddit/data/intermediate/cleaned_raw/test_samples/reddit_parenting_100_sample.csv"
OUTPUT      = ROOT / "Reddit/data/intermediate/llm_births/births_parenting_mini_sample.csv"

# Load and filter to births first, then merge metadata
llm    = pd.read_csv(INPUT_LLM)
births = llm[llm["birth_flag"] == 1].drop(columns=["birth_flag"])

meta   = pd.read_csv(INPUT_META)
births = meta.merge(births, on="id", how="inner")

births = births.rename(columns={
    "days_from_birth": "days_from_mini",
    "confidence":      "confidence_mini",
    "p_female":        "p_female_mini",
    "p_male":          "p_male_mini",
})

births = births.sort_values("author").reset_index(drop=True)
births["dup"] = births["author"].duplicated(keep=False).astype(int)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
births.to_csv(OUTPUT, index=False)

dup_authors = births.loc[births["dup"] == 1, "author"].nunique()
dup_ids     = births["id"].duplicated().sum()
print(f"Births extracted: {len(births):,} of {len(llm):,} LLM rows")
print(f"Authors with multiple birth posts: {dup_authors:,}")
print(f"Duplicate post IDs: {dup_ids:,}")
print(f"Saved to {OUTPUT}")
