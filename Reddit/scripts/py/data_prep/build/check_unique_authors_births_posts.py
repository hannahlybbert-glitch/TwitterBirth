# Author: Hannah Lybbert
# Created: 2026-04-08
# Updated: 2026-04-08
# Purpose: Check unique birth posts in merged_births_and_posts_FULL.csv and assign true_birth_post

import pandas as pd
from pathlib import Path

ROOT       = Path(__file__).resolve().parents[5]
INPUT_PATH = ROOT / "Reddit/data/intermediate/births_and_posts/merged_births_and_posts_FULL.csv"

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
print("Loading merged_births_and_posts_FULL.csv...")
df = pd.read_csv(INPUT_PATH)
print(f"  Total rows:      {len(df):,}")
print(f"  Unique authors:  {df['author'].nunique():,}")

# ----------------------------------------------------------------
# 1. Check for duplicate ids
# ----------------------------------------------------------------
n_dup_ids = df["id"].duplicated().sum()
print(f"\n  Duplicate ids: {n_dup_ids:,}")
if n_dup_ids > 0:
    dup_authors = df[df["id"].duplicated(keep=False)]["author"].nunique()
    print(f"  Authors with duplicate ids: {dup_authors:,}")

# ----------------------------------------------------------------
# 3. Filter to birth_post == 1
# ----------------------------------------------------------------
births = df[df["birth_post"] == 1].copy()
print(f"\n  Rows with birth_post == 1:  {len(births):,}")
print(f"  Unique authors (birth_post == 1): {births['author'].nunique():,}")
n_dup_birth_ids = births["id"].duplicated().sum()
print(f"  Duplicate ids among birth_post == 1: {n_dup_birth_ids:,}")

# ----------------------------------------------------------------
# 4. Check how many birth posts have days_from == -999
# ----------------------------------------------------------------
n_999 = (births["days_from"] == -999).sum()
print(f"\n  Birth posts with days_from == -999: {n_999:,}")

# ----------------------------------------------------------------
# 5. For authors with multiple birth_post == 1, assign true_birth_post
#    via min abs(days_from)
# ----------------------------------------------------------------
births["_abs_days"] = births["days_from"].abs()

true_birth_ids = (
    births
    .sort_values("_abs_days")
    .drop_duplicates(subset="author", keep="first")
    ["id"]
)

df["true_birth_post"] = df["id"].isin(true_birth_ids).astype(int)

# ----------------------------------------------------------------
# Report
# ----------------------------------------------------------------
n_multi = births.groupby("author").size()
n_authors_multi = (n_multi > 1).sum()
print(f"\n  Authors with multiple birth_post == 1: {n_authors_multi:,}")
print(f"  True birth posts (true_birth_post == 1): {df['true_birth_post'].sum():,}")
print(f"  Unique authors   (true_birth_post == 1): {df[df['true_birth_post']==1]['author'].nunique():,}")
