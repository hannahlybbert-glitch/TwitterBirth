# Author: Hannah Lybbert
# Created: 2026-03-19
# Updated: 2026-04-07
# Purpose: Merge birth posts with all posts by birth authors for both samples; output merged_births_and_posts_FULL.csv

import pandas as pd
from pathlib import Path

ROOT          = Path(__file__).resolve().parents[5]
BIRTHS_DIR    = ROOT / "Reddit/data/intermediate/llm_births"
POSTS_DIR     = ROOT / "Reddit/data/intermediate/cleaned_raw"
OUTPUT_DIR    = ROOT / "Reddit/data/intermediate/births_and_posts"

# ----------------------------------------------------------------
# Input paths
# ----------------------------------------------------------------
INPUT_BIRTHS_22K  = BIRTHS_DIR / "births_22k_sample.csv"
INPUT_POSTS_22K   = POSTS_DIR  / "reddit_22k_post_history_cleaned.csv"
OUTPUT_22K        = OUTPUT_DIR / "merged_22k_births_and_posts.csv"

INPUT_BIRTHS_2_3M = BIRTHS_DIR / "births_2_3M_sample.csv"
INPUT_POSTS_2_3M  = POSTS_DIR  / "reddit_77k_post_history_cleaned.csv"
OUTPUT_2_3M       = OUTPUT_DIR / "merged_77k_births_and_posts.csv"

OUTPUT_FULL       = OUTPUT_DIR / "merged_births_and_posts_FULL.csv"

OUTPUT_COLS = ["id", "author", "subreddit", "created_utc", "title", "selftext",
               "url", "score", "num_comments", "over_18", "stickied", "locked", "permalink",
               "days_from", "confidence", "p_female", "p_male", "birth_post"]

# ----------------------------------------------------------------
# Helper: merge one set of births with its post history
# ----------------------------------------------------------------
def merge_births_and_posts(births_path, posts_path, output_path, label):
    print(f"\n[{label}] Loading...")
    births = pd.read_csv(births_path)
    posts  = pd.read_csv(posts_path)

    print(f"  Birth posts:   {len(births):,}")
    print(f"  Cleaned posts: {len(posts):,}")

    birth_authors  = set(births["author"].dropna().unique())
    post_authors   = set(posts["author"].dropna().unique())
    shared_authors = birth_authors & post_authors

    births_filtered = births[births["author"].isin(shared_authors)].copy()
    posts_filtered  = posts[posts["author"].isin(shared_authors)].copy()

    print(f"  Shared authors:            {len(shared_authors):,}")
    print(f"  Births for shared authors: {len(births_filtered):,}")
    print(f"  Posts by shared authors:   {len(posts_filtered):,}")

    flagged_ids = set(births_filtered[births_filtered["birth_post"] == 1]["id"])
    posts_filtered["birth_post"] = posts_filtered["id"].isin(flagged_ids).astype(int)

    birth_meta     = births_filtered[["id", "days_from", "confidence", "p_female", "p_male"]]
    posts_filtered = posts_filtered.merge(birth_meta, on="id", how="left")

    unmatched_births = births_filtered[~births_filtered["id"].isin(posts_filtered["id"])].copy()
    print(f"  Birth posts not in post history: {len(unmatched_births):,} ({unmatched_births['author'].nunique():,} authors)")
        # Note: these rows represent authors who appear in the births CSV but have no matching records in the post history file
            # So their presence in the births+posts file will just be whatever was in the births file. This means they will
            # likely be dropped after filtering for authors with sufficient pre/post data, but we keep them here for completeness.

    merged = pd.concat([
        posts_filtered.reindex(columns=OUTPUT_COLS),
        unmatched_births.reindex(columns=OUTPUT_COLS)
    ], ignore_index=True)

    merged = merged.sort_values(["author", "created_utc"]).reset_index(drop=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output_path, index=False)

    print(f"  Saved {len(merged):,} rows to {output_path.name}")
    print(f"    Birth posts  (birth_post == 1): {(merged['birth_post'] == 1).sum():,}")
    print(f"    Other posts  (birth_post == 0): {(merged['birth_post'] == 0).sum():,}")

    return merged

# ----------------------------------------------------------------
# Run both merges
# ----------------------------------------------------------------
merged_22k  = merge_births_and_posts(INPUT_BIRTHS_22K,  INPUT_POSTS_22K,  OUTPUT_22K,  "22k")
merged_2_3M = merge_births_and_posts(INPUT_BIRTHS_2_3M, INPUT_POSTS_2_3M, OUTPUT_2_3M, "2.3M")

# ----------------------------------------------------------------
# Combine into FULL output
# ----------------------------------------------------------------
print("\n[FULL] Combining...")
full = pd.concat([merged_22k, merged_2_3M], ignore_index=True)
full = full.sort_values(["author", "created_utc"]).reset_index(drop=True)

# ----------------------------------------------------------------
# De-duplicate ids — keep first instance of any duplicate id
# ----------------------------------------------------------------
before = len(full)
full = full.drop_duplicates(subset="id", keep="first").reset_index(drop=True)
print(f"  Dropped {before - len(full):,} duplicate id rows")
print(f"  Duplicate ids remaining: {full['id'].duplicated().sum():,}")

# ----------------------------------------------------------------
# Re-assign birth_post — for authors with multiple birth_post == 1,
# keep only the one with min abs(days_from); set the rest to 0
# ----------------------------------------------------------------
birth_rows = full[full["birth_post"] == 1].copy()
birth_rows["_abs_days"] = birth_rows["days_from"].abs()
true_birth_ids = (
    birth_rows
    .sort_values("_abs_days")
    .drop_duplicates(subset="author", keep="first")
    ["id"]
)
multi_birth_authors = birth_rows.groupby("author").filter(lambda x: len(x) > 1)["author"].nunique()
print(f"  Authors with multiple birth_post == 1 (before fix): {multi_birth_authors:,}")
full.loc[full["birth_post"] == 1, "birth_post"] = full.loc[full["birth_post"] == 1, "id"].isin(true_birth_ids).astype(int)
multi_birth_after = (full[full["birth_post"] == 1].groupby("author").size() > 1).sum()
print(f"  Authors with multiple birth_post == 1 (after fix):  {multi_birth_after:,}")

full = full.sort_values(["author", "created_utc"]).reset_index(drop=True)
full.to_csv(OUTPUT_FULL, index=False)

print(f"  Merged: {len(full):,} total rows, {full['author'].nunique():,} unique authors")
print(f"  Birth posts  (birth_post == 1): {(full['birth_post'] == 1).sum():,}")
print(f"  Other posts  (birth_post == 0): {(full['birth_post'] == 0).sum():,}")
print(f"\nSaved to {OUTPUT_FULL}")
